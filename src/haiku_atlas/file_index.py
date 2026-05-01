"""Header file scanning and incremental file metadata indexing."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path

from haiku_atlas.parser import ParsedSymbol, parse_header_symbols

HEADER_EXTENSIONS = {".h", ".hpp"}


@dataclass(frozen=True)
class HeaderFile:
    path: str
    mtime: float
    size: int


@dataclass(frozen=True)
class FileIndexResult:
    scanned: int
    new: tuple[str, ...]
    changed: tuple[str, ...]
    deleted: tuple[str, ...]
    unchanged: tuple[str, ...]


def scan_header_files(source_root: Path) -> list[HeaderFile]:
    """Return header files under source_root with paths relative to that root."""
    root = source_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_root}")

    headers: list[HeaderFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in HEADER_EXTENSIONS:
            continue

        stat = path.stat()
        headers.append(
            HeaderFile(
                path=path.relative_to(root).as_posix(),
                mtime=stat.st_mtime,
                size=stat.st_size,
            )
        )
    return headers


def update_file_index(
    connection: sqlite3.Connection,
    source_root: Path,
    *,
    full: bool = False,
) -> FileIndexResult:
    """Scan headers and update file metadata in SQLite."""
    connection.execute("PRAGMA foreign_keys = ON")
    headers = scan_header_files(source_root)
    scanned_by_path = {header.path: header for header in headers}

    existing_rows = connection.execute("SELECT path, mtime, size FROM files").fetchall()
    existing_by_path = {path: (mtime, size) for path, mtime, size in existing_rows}

    new: list[str] = []
    changed: list[str] = []
    unchanged: list[str] = []

    for header in headers:
        existing = existing_by_path.get(header.path)
        if existing is None:
            new.append(header.path)
        elif full or existing != (header.mtime, header.size):
            changed.append(header.path)
        else:
            unchanged.append(header.path)

    deleted = sorted(set(existing_by_path) - set(scanned_by_path))

    for path in deleted:
        file_id = _get_file_id(connection, path)
        if file_id is not None:
            _delete_file_symbols(connection, file_id)
        connection.execute("DELETE FROM files WHERE path = ?", (path,))

    for path in (*new, *changed):
        header = scanned_by_path[path]
        connection.execute(
            """
            INSERT INTO files (path, mtime, size, last_indexed_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(path) DO UPDATE SET
                mtime = excluded.mtime,
                size = excluded.size,
                last_indexed_at = CURRENT_TIMESTAMP
            """,
            (header.path, header.mtime, header.size),
        )
        file_id = _get_file_id(connection, header.path)
        if file_id is None:
            continue

        _delete_file_symbols(connection, file_id)
        header_source = (source_root / header.path).read_text(encoding="utf-8", errors="replace")
        for symbol in parse_header_symbols(header_source):
            _insert_symbol(connection, file_id, header.path, symbol)

    return FileIndexResult(
        scanned=len(headers),
        new=tuple(new),
        changed=tuple(changed),
        deleted=tuple(deleted),
        unchanged=tuple(unchanged),
    )


def _get_file_id(connection: sqlite3.Connection, path: str) -> int | None:
    row = connection.execute("SELECT id FROM files WHERE path = ?", (path,)).fetchone()
    if row is None:
        return None
    return int(row[0])


def _delete_file_symbols(connection: sqlite3.Connection, file_id: int) -> None:
    connection.execute(
        """
        DELETE FROM relations
        WHERE source_symbol_id IN (SELECT id FROM symbols WHERE file_id = ?)
           OR target_symbol_id IN (SELECT id FROM symbols WHERE file_id = ?)
        """,
        (file_id, file_id),
    )
    connection.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))


def _insert_symbol(
    connection: sqlite3.Connection,
    file_id: int,
    file_path: str,
    symbol: ParsedSymbol,
) -> None:
    cursor = connection.execute(
        """
        INSERT INTO symbols (
            kind,
            name,
            qualified_name,
            display_name,
            file_id,
            line_start,
            line_end,
            raw_declaration
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(qualified_name) DO UPDATE SET
            kind = excluded.kind,
            name = excluded.name,
            display_name = excluded.display_name,
            file_id = excluded.file_id,
            line_start = excluded.line_start,
            line_end = excluded.line_end,
            raw_declaration = excluded.raw_declaration
        """,
        (
            symbol.kind,
            symbol.name,
            symbol.qualified_name,
            symbol.name,
            file_id,
            symbol.line_start,
            symbol.line_end,
            symbol.raw_declaration,
        ),
    )
    symbol_id = cursor.lastrowid
    if symbol_id == 0:
        row = connection.execute(
            "SELECT id FROM symbols WHERE qualified_name = ?",
            (symbol.qualified_name,),
        ).fetchone()
        if row is None:
            return
        symbol_id = int(row[0])

    _insert_relation(connection, symbol_id, "defined_in", file_path)
    for base in symbol.inherits:
        _insert_relation(connection, symbol_id, "inherits", base)


def _insert_relation(
    connection: sqlite3.Connection,
    source_symbol_id: int,
    relation_type: str,
    target_text: str,
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO relations (source_symbol_id, relation_type, target_text)
        VALUES (?, ?, ?)
        """,
        (source_symbol_id, relation_type, target_text),
    )
