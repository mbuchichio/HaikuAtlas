from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from haiku_atlas.db import initialize_database
from haiku_atlas.file_index import update_file_index
from haiku_atlas.web import _route


class WebTests(unittest.TestCase):
    def test_web_home_lists_kits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = self._indexed_connection(Path(directory))
            try:
                status, body = _route(connection, "/", {})
            finally:
                connection.close()

        self.assertEqual(200, status)
        self.assertIn("Haiku Atlas", body)
        self.assertIn("Interface Kit", body)
        self.assertIn("data-recent-section", body)
        self.assertIn("haiku-atlas:recent", body)

    def test_web_search_links_to_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = self._indexed_connection(Path(directory))
            try:
                status, body = _route(connection, "/search", {"q": ["View"]})
            finally:
                connection.close()

        self.assertEqual(200, status)
        self.assertIn("/symbol/BView", body)
        self.assertIn("BView", body)

    def test_web_kit_groups_top_level_symbols_by_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = self._indexed_connection(Path(directory))
            try:
                status, body = _route(connection, "/kit/interface", {})
            finally:
                connection.close()

        self.assertEqual(200, status)
        self.assertIn("Classes", body)
        self.assertIn("Structs", body)
        self.assertIn("Enums", body)
        self.assertLess(body.index("Classes"), body.index("Structs"))
        self.assertLess(body.index("Structs"), body.index("Enums"))

    def test_web_symbol_shows_detail_and_methods(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = self._indexed_connection(Path(directory))
            try:
                status, body = _route(connection, "/symbol/BView", {})
            finally:
                connection.close()

        self.assertEqual(200, status)
        self.assertIn("BView", body)
        self.assertIn("Constructors", body)
        self.assertIn("Destructors", body)
        self.assertIn("Methods", body)
        self.assertLess(body.index("Constructors"), body.index("Destructors"))
        self.assertLess(body.index("Destructors"), body.index("Methods"))
        self.assertIn("/symbol/BView%3A%3ADraw", body)
        self.assertIn("virtual void Draw(BRect update);", body)
        self.assertIn("Drawing", body)
        self.assertIn('class="method-row"', body)
        self.assertNotIn('class="pill"', body)
        self.assertIn('data-recent-title="BView"', body)
        self.assertIn('data-recent-url="/symbol/BView"', body)
        self.assertIn("os/interface/View.h:1", body)

    def _indexed_connection(self, root: Path) -> sqlite3.Connection:
        db_path = root / "atlas.sqlite3"
        source = root / "headers"
        (source / "os" / "interface").mkdir(parents=True)
        (source / "os" / "interface" / "View.h").write_text(
            """class BView : public BHandler {
            public:
                BView(BRect frame);
                virtual ~BView();
                // Drawing
                virtual void Draw(BRect update);
            };

            struct rgb_color {};

            enum orientation {};
            """,
            encoding="utf-8",
        )
        initialize_database(db_path)
        connection = sqlite3.connect(db_path)
        update_file_index(connection, source)
        return connection


if __name__ == "__main__":
    unittest.main()
