from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from haiku_atlas.db import initialize_database


class DatabaseTests(unittest.TestCase):
    def test_initialize_database_creates_core_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"

            initialize_database(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }

        self.assertLessEqual(
            {"files", "kits", "symbols", "relations", "docs", "settings", "schema_migrations"},
            tables,
        )


if __name__ == "__main__":
    unittest.main()
