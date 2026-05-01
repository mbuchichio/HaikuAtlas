"""SQLite database setup for Haiku Atlas."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "schema.sql"
DEFAULT_DB_PATH = Path("data") / "haiku-atlas.sqlite3"


def initialize_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create the SQLite database and apply the v0 schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as connection:
        connection.executescript(schema)

