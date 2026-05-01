"""Bootstrap helpers for fetching and indexing the Haiku source tree."""

from __future__ import annotations

from pathlib import Path
from contextlib import closing
import shutil
import sqlite3
import subprocess

from haiku_atlas.db import DEFAULT_DB_PATH, initialize_database
from haiku_atlas.file_index import update_file_index

HAIKU_REPOSITORY_URL = "https://github.com/haiku/haiku.git"
DEFAULT_SOURCE_PATH = Path("sources") / "haiku"


def setup_haiku_source(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    source_path: Path = DEFAULT_SOURCE_PATH,
    assume_yes: bool = False,
) -> int:
    source_path = source_path.expanduser()
    if not source_path.exists():
        if not _confirm_download(source_path, assume_yes):
            print("atlas setup: canceled")
            return 1
        _clone_haiku_source(source_path)
    elif not (source_path / "headers").is_dir():
        print(f"atlas setup: source exists but has no headers directory: {source_path}")
        return 1

    initialize_database(db_path)
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            result = update_file_index(connection, source_path / "headers", full=True)

    print(
        "atlas setup: "
        f"indexed scanned={result.scanned} "
        f"symbols source={source_path / 'headers'} db={db_path}"
    )
    return 0


def _confirm_download(source_path: Path, assume_yes: bool) -> bool:
    if assume_yes:
        return True

    print(f"atlas setup: clone Haiku source from {HAIKU_REPOSITORY_URL}")
    print(f"atlas setup: destination {source_path}")
    answer = input("Download now? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def _clone_haiku_source(source_path: Path) -> None:
    if shutil.which("git") is None:
        raise RuntimeError("git not found; install git or clone Haiku manually")

    source_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", HAIKU_REPOSITORY_URL, str(source_path)],
        check=True,
    )
