from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_update_file_index_stores_index_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            (source / "View.h").write_text("class BView {};", encoding="utf-8")

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                settings = dict(connection.execute("SELECT key, value FROM settings").fetchall())

            self.assertEqual(str(source), settings["source_path"])
            self.assertEqual("1", settings["header_count"])
            self.assertIn("last_indexed_at", settings)

    def test_update_file_index_keeps_running_after_parser_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            (source / "Broken.h").write_text("BROKEN", encoding="utf-8")
            (source / "View.h").write_text("class BView {};", encoding="utf-8")

            def parse_or_raise(source_text: str):
                if "BROKEN" in source_text:
                    raise ValueError("parser failed")
                return []

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                with patch("haiku_atlas.file_index.parse_header_symbols", parse_or_raise):
                    result = update_file_index(connection, source)
                files = connection.execute("SELECT path FROM files ORDER BY path").fetchall()

            self.assertEqual(["Broken.h", "View.h"], list(result.new))
            self.assertEqual("Broken.h", result.errors[0].path)
            self.assertEqual("parser failed", result.errors[0].message)
            self.assertEqual([("View.h",)], files)

    def test_full_index_rebuilds_existing_headers(self) -> None:
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

            self.assertEqual(("View.h",), result.new)

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

    def test_update_file_index_assigns_kits_from_header_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            (source / "os" / "interface").mkdir(parents=True)
            (source / "os" / "interface" / "View.h").write_text(
                "class BView : public BHandler {};",
                encoding="utf-8",
            )

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                rows = connection.execute(
                    """
                    SELECT symbols.qualified_name, kits.name, kits.display_name
                    FROM symbols
                    JOIN kits ON kits.id = symbols.kit_id
                    """
                ).fetchall()

            self.assertEqual([("BView", "interface", "Interface Kit")], rows)

    def test_update_file_index_stores_public_methods_as_child_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            (source / "View.h").write_text(
                """
                class BView : public BHandler {
                public:
                    BView(BRect frame);
                    virtual void Draw(BRect update);
                private:
                    void PrivateHook();
                };
                """,
                encoding="utf-8",
            )

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                symbols = connection.execute(
                    """
                    SELECT child.kind, child.qualified_name, parent.qualified_name
                    FROM symbols child
                    LEFT JOIN symbols parent ON parent.id = child.parent_id
                    ORDER BY child.qualified_name
                    """
                ).fetchall()
                relations = connection.execute(
                    """
                    SELECT relation_type, target_text
                    FROM relations
                    WHERE relation_type = 'contains'
                    ORDER BY target_text
                    """
                ).fetchall()

            self.assertEqual(
                [
                    ("class", "BView", None),
                    ("constructor", "BView::BView", "BView"),
                    ("method", "BView::Draw", "BView"),
                ],
                symbols,
            )
            self.assertEqual(
                [("contains", "BView::BView"), ("contains", "BView::Draw")],
                relations,
            )

    def test_update_file_index_stores_source_context_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            (source / "Message.h").write_text(
                """
                class BMessage {
                public:
                    // Replying
                    status_t SendReply(uint32 command);
                };
                """,
                encoding="utf-8",
            )

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                docs = connection.execute(
                    """
                    SELECT docs.source, docs.body
                    FROM docs
                    JOIN symbols ON symbols.id = docs.symbol_id
                    WHERE symbols.qualified_name = 'BMessage::SendReply'
                    """
                ).fetchall()

            self.assertEqual([("source_context", "Replying")], docs)

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

    def test_full_reindex_rebuilds_symbol_names_without_broken_relations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            source.mkdir()
            header = source / "View.h"
            header.write_text("class BView : public BHandler {};", encoding="utf-8")

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                update_file_index(connection, source)
                header.write_text("class BView : public BHandler { public: void Draw(); };", encoding="utf-8")
                update_file_index(connection, source, full=True)
                relations = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM relations
                    JOIN symbols ON symbols.id = relations.source_symbol_id
                    WHERE symbols.qualified_name = 'BView'
                    """
                ).fetchone()[0]

            self.assertGreater(relations, 0)

    def test_full_reindex_removes_stale_kits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "source"
            (source / "os" / "interface").mkdir(parents=True)
            (source / "os" / "interface" / "View.h").write_text(
                "class BView {};",
                encoding="utf-8",
            )

            initialize_database(db_path)
            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    "INSERT INTO kits (name, display_name) VALUES ('stale', 'Stale Kit')"
                )
                update_file_index(connection, source, full=True)
                kit_names = [
                    row[0]
                    for row in connection.execute("SELECT name FROM kits ORDER BY name")
                ]

            self.assertEqual(["interface"], kit_names)


if __name__ == "__main__":
    unittest.main()
