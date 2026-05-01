from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from haiku_atlas.db import initialize_database
from haiku_atlas.setup import setup_haiku_source


class SetupTests(unittest.TestCase):
    def test_setup_cancels_without_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with patch("builtins.input", return_value="n"), redirect_stdout(StringIO()):
                result = setup_haiku_source(
                    db_path=root / "atlas.sqlite3",
                    source_path=root / "haiku",
                )

        self.assertEqual(1, result)

    def test_setup_indexes_existing_source_without_clone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "haiku"
            headers = source / "headers"
            headers.mkdir(parents=True)
            (headers / "View.h").write_text("class BView {};", encoding="utf-8")

            with patch("haiku_atlas.setup._clone_haiku_source") as clone, redirect_stdout(StringIO()):
                result = setup_haiku_source(db_path=db_path, source_path=source)

            self.assertEqual(0, result)
            clone.assert_not_called()
            with sqlite3.connect(db_path) as connection:
                settings = dict(connection.execute("SELECT key, value FROM settings").fetchall())

            self.assertEqual(str(headers), settings["source_path"])

    def test_setup_clones_when_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "haiku"

            def fake_clone(path: Path) -> None:
                headers = path / "headers"
                headers.mkdir(parents=True)
                (headers / "View.h").write_text("class BView {};", encoding="utf-8")

            initialize_database(db_path)
            with (
                patch("haiku_atlas.setup._clone_haiku_source", fake_clone),
                redirect_stdout(StringIO()),
            ):
                result = setup_haiku_source(
                    db_path=db_path,
                    source_path=source,
                    assume_yes=True,
                )

        self.assertEqual(0, result)


if __name__ == "__main__":
    unittest.main()
