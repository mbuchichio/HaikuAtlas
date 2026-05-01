from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from haiku_atlas.cli.indexer import main as indexer_main
from haiku_atlas.cli.query import main as query_main


class CliTests(unittest.TestCase):
    def test_indexer_bootstrap_initializes_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"
            output = StringIO()

            with redirect_stdout(output):
                result = indexer_main(["--db", str(db_path)])

            self.assertEqual(0, result)
            self.assertTrue(db_path.exists())
            self.assertIn("initialized", output.getvalue())

    def test_query_search_placeholder_initializes_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"
            output = StringIO()

            with redirect_stdout(output):
                result = query_main(["--db", str(db_path), "search", "BView"])

            self.assertEqual(0, result)
            self.assertTrue(db_path.exists())
            self.assertIn("BView", output.getvalue())

    def test_query_dump_commands_read_empty_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"

            for command in ("dump-symbols", "dump-kits"):
                output = StringIO()
                with redirect_stdout(output):
                    result = query_main(["--db", str(db_path), command])

                self.assertEqual(0, result)
                self.assertEqual("", output.getvalue())


if __name__ == "__main__":
    unittest.main()
