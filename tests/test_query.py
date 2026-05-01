from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from haiku_atlas.db import initialize_database
from haiku_atlas.query import list_kits


class QueryTests(unittest.TestCase):
    def test_list_kits_uses_canonical_display_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"
            initialize_database(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                with connection:
                    connection.execute(
                        "INSERT INTO kits (name, display_name) VALUES ('midi2', 'MIDI Kit')"
                    )
                kits = list_kits(connection)

        self.assertEqual("MIDI2 Kit", kits[0].display_name)


if __name__ == "__main__":
    unittest.main()
