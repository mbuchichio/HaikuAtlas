from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from haiku_atlas.db import initialize_database
from haiku_atlas.file_index import scan_header_files, update_file_index


class FileIndexTests(unittest.TestCase):
    def test_scan_header_files_returns_relative_header_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "headers" / "os" / "interface").mkdir(parents=True)
            (root / "headers" / "os" / "interface" / "View.h").write_text(
                "class BView {};",
                encoding="utf-8",
            )
            (root / "README.md").write_text("not a header", encoding="utf-8")

            headers = scan_header_files(root)

        self.assertEqual(["headers/os/interface/View.h"], [header.path for header in headers])

    def test_update_file_index_tracks_new_unchanged_changed_and_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            header = source / "View.h"
            header.write_text("class BView {};", encoding="utf-8")

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                first = update_file_index(connection, source)
                second = update_file_index(connection, source)

                header.write_text("class BView { void Draw(); };", encoding="utf-8")
                third = update_file_index(connection, source)

                header.unlink()
                fourth = update_file_index(connection, source)

            self.assertEqual(("View.h",), first.new)
            self.assertEqual(("View.h",), second.unchanged)
            self.assertEqual(("View.h",), third.changed)
            self.assertEqual(("View.h",), fourth.deleted)

    def test_full_index_marks_existing_headers_changed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            (source / "View.h").write_text("class BView {};", encoding="utf-8")

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                result = update_file_index(connection, source, full=True)

            self.assertEqual(("View.h",), result.changed)

    def test_update_file_index_stores_symbols_and_relations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            (source / "View.h").write_text(
                """
                class BView : public BHandler {
                };

                struct rgb_color {
                };

                enum orientation {
                };
                """,
                encoding="utf-8",
            )

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                symbols = connection.execute(
                    "SELECT kind, name FROM symbols ORDER BY kind, name"
                ).fetchall()
                relations = connection.execute(
                    "SELECT relation_type, target_text FROM relations ORDER BY relation_type, target_text"
                ).fetchall()

            self.assertEqual(
                [("class", "BView"), ("enum", "orientation"), ("struct", "rgb_color")],
                symbols,
            )
            self.assertIn(("defined_in", "View.h"), relations)
            self.assertIn(("inherits", "BHandler"), relations)

    def test_update_file_index_removes_symbols_for_deleted_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            header = source / "View.h"
            header.write_text("class BView {};", encoding="utf-8")

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                header.unlink()
                update_file_index(connection, source)
                count = connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]

            self.assertEqual(0, count)


if __name__ == "__main__":
    unittest.main()
