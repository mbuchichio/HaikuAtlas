"""Read-side queries for a Haiku Atlas SQLite index."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class SearchResult:
    kind: str
    qualified_name: str
    kit_display_name: str | None
    file_path: str | None
    line_start: int | None


@dataclass(frozen=True)
class KitSummary:
    name: str
    display_name: str
    symbol_count: int
    top_level_symbol_count: int = 0


@dataclass(frozen=True)
class SymbolDetail:
    kind: str
    name: str
    qualified_name: str
    display_name: str
    kit_display_name: str | None
    file_path: str | None
    line_start: int | None
    line_end: int | None
    raw_declaration: str | None
    relations: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class SymbolPage:
    detail: SymbolDetail
    inherits: tuple[str, ...]
    methods: tuple[str, ...]
    other_relations: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class KitSymbol:
    kind: str
    qualified_name: str
    file_path: str | None
    line_start: int | None


@dataclass(frozen=True)
class IndexStatus:
    source_path: str | None
    last_indexed_at: str | None
    header_count: int
    kit_count: int
    symbol_count: int
    database_path: str | None = None


def get_index_status(connection: sqlite3.Connection) -> IndexStatus:
    settings = dict(connection.execute("SELECT key, value FROM settings").fetchall())
    header_count = _count_rows(connection, "files")
    kit_count = _count_rows(connection, "kits")
    symbol_count = _count_rows(connection, "symbols")
    return IndexStatus(
        source_path=settings.get("source_path"),
        last_indexed_at=settings.get("last_indexed_at"),
        header_count=header_count,
        kit_count=kit_count,
        symbol_count=symbol_count,
    )


def _count_rows(connection: sqlite3.Connection, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0])


def list_kits(connection: sqlite3.Connection) -> list[KitSummary]:
    rows = connection.execute(
        """
        SELECT
            kits.name,
            kits.display_name,
            COUNT(symbols.id) AS symbol_count,
            SUM(
                CASE
                    WHEN symbols.parent_id IS NULL
                     AND symbols.kind IN ('class', 'struct', 'enum')
                    THEN 1
                    ELSE 0
                END
            ) AS top_level_symbol_count
        FROM kits
        LEFT JOIN symbols ON symbols.kit_id = kits.id
        GROUP BY kits.id
        ORDER BY kits.display_name
        """
    ).fetchall()
    return [
        KitSummary(
            name=name,
            display_name=display_name,
            symbol_count=symbol_count,
            top_level_symbol_count=top_level_symbol_count or 0,
        )
        for name, display_name, symbol_count, top_level_symbol_count in rows
    ]


def list_kit_symbols(
    connection: sqlite3.Connection,
    kit_name: str,
    *,
    limit: int = 80,
) -> tuple[KitSummary, tuple[KitSymbol, ...]] | None:
    kit_row = connection.execute(
        """
        SELECT
            kits.id,
            kits.name,
            kits.display_name,
            COUNT(symbols.id) AS symbol_count,
            SUM(
                CASE
                    WHEN symbols.parent_id IS NULL
                     AND symbols.kind IN ('class', 'struct', 'enum')
                    THEN 1
                    ELSE 0
                END
            ) AS top_level_symbol_count
        FROM kits
        LEFT JOIN symbols ON symbols.kit_id = kits.id
        WHERE kits.name = ? OR kits.display_name = ?
        GROUP BY kits.id
        """,
        (kit_name, kit_name),
    ).fetchone()
    if kit_row is None:
        return None

    kit_id, name, display_name, symbol_count, top_level_symbol_count = kit_row
    rows = connection.execute(
        """
        SELECT symbols.kind, symbols.qualified_name, files.path, symbols.line_start
        FROM symbols
        LEFT JOIN files ON files.id = symbols.file_id
        WHERE symbols.kit_id = ?
          AND symbols.parent_id IS NULL
          AND symbols.kind IN ('class', 'struct', 'enum')
        ORDER BY symbols.kind, symbols.qualified_name
        LIMIT ?
        """,
        (kit_id, limit),
    ).fetchall()
    symbols = tuple(
        KitSymbol(
            kind=kind,
            qualified_name=qualified_name,
            file_path=file_path,
            line_start=line_start,
        )
        for kind, qualified_name, file_path, line_start in rows
    )
    return (
        KitSummary(
            name=name,
            display_name=display_name,
            symbol_count=symbol_count,
            top_level_symbol_count=top_level_symbol_count or 0,
        ),
        symbols,
    )


def search_symbols(connection: sqlite3.Connection, term: str, *, limit: int = 20) -> list[SearchResult]:
    """Search symbols by name with exact/prefix/contains ranking."""
    pattern = f"%{term}%"
    rows = connection.execute(
        """
        SELECT s.kind, s.qualified_name, k.display_name, f.path, s.line_start
        FROM symbols s
        LEFT JOIN files f ON f.id = s.file_id
        LEFT JOIN kits k ON k.id = s.kit_id
        WHERE s.name LIKE ? OR s.qualified_name LIKE ?
        ORDER BY
            CASE
                WHEN s.name = ? THEN 0
                WHEN s.qualified_name = ? THEN 1
                WHEN s.name LIKE ? THEN 2
                ELSE 3
            END,
            s.qualified_name
        LIMIT ?
        """,
        (pattern, pattern, term, term, f"{term}%", limit),
    )
    return [
        SearchResult(
            kind=kind,
            qualified_name=qualified_name,
            kit_display_name=kit_display_name,
            file_path=file_path,
            line_start=line_start,
        )
        for kind, qualified_name, kit_display_name, file_path, line_start in rows
    ]


def get_symbol_detail(connection: sqlite3.Connection, name: str) -> SymbolDetail | None:
    """Return one symbol by exact name or qualified name."""
    row = connection.execute(
        """
        SELECT
            s.id,
            s.kind,
            s.name,
            s.qualified_name,
            s.display_name,
            k.display_name,
            f.path,
            s.line_start,
            s.line_end,
            s.raw_declaration
        FROM symbols s
        LEFT JOIN files f ON f.id = s.file_id
        LEFT JOIN kits k ON k.id = s.kit_id
        WHERE s.qualified_name = ? OR s.name = ?
        ORDER BY
            CASE
                WHEN s.qualified_name = ? THEN 0
                ELSE 1
            END,
            s.qualified_name
        LIMIT 1
        """,
        (name, name, name),
    ).fetchone()
    if row is None:
        return None

    (
        symbol_id,
        kind,
        symbol_name,
        qualified_name,
        display_name,
        kit_display,
        file_path,
        line_start,
        line_end,
        raw,
    ) = row
    relation_rows = connection.execute(
        """
        SELECT relation_type, COALESCE(target_text, target.qualified_name)
        FROM relations
        LEFT JOIN symbols target ON target.id = relations.target_symbol_id
        WHERE source_symbol_id = ?
        ORDER BY relation_type, target_text
        """,
        (symbol_id,),
    ).fetchall()
    relations = tuple((relation_type, target or "") for relation_type, target in relation_rows)

    return SymbolDetail(
        kind=kind,
        name=symbol_name,
        qualified_name=qualified_name,
        display_name=display_name,
        kit_display_name=kit_display,
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        raw_declaration=raw,
        relations=relations,
    )


def get_symbol_page(connection: sqlite3.Connection, name: str) -> SymbolPage | None:
    """Return display-oriented symbol information for CLI/UI consumers."""
    detail = get_symbol_detail(connection, name)
    if detail is None:
        return None

    inherits: list[str] = []
    methods: list[str] = []
    other_relations: list[tuple[str, str]] = []

    for relation_type, target in detail.relations:
        if relation_type == "inherits":
            inherits.append(target)
        elif relation_type == "contains":
            methods.append(target)
        elif relation_type != "defined_in":
            other_relations.append((relation_type, target))

    return SymbolPage(
        detail=detail,
        inherits=tuple(inherits),
        methods=tuple(methods),
        other_relations=tuple(other_relations),
    )
