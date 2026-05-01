from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from haiku_atlas.cli.indexer import main as indexer_main
from haiku_atlas.cli.query import main as query_main


class CliTests(unittest.TestCase):
    def test_indexer_help_prints_cli_reference(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            result = indexer_main(["help"])

        self.assertEqual(0, result)
        self.assertIn("Haiku Atlas CLI Reference", output.getvalue())
        self.assertIn("atlas-indexer", output.getvalue())

    def test_query_help_prints_cli_reference(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            result = query_main(["help"])

        self.assertEqual(0, result)
        self.assertIn("Haiku Atlas CLI Reference", output.getvalue())
        self.assertIn("atlas-query", output.getvalue())

    def test_indexer_bootstrap_initializes_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"
            output = StringIO()

            with redirect_stdout(output):
                result = indexer_main(["--db", str(db_path)])

            self.assertEqual(0, result)
            self.assertTrue(db_path.exists())
            self.assertIn("initialized", output.getvalue())

    def test_query_search_initializes_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"
            output = StringIO()

            with redirect_stdout(output):
                result = query_main(["--db", str(db_path), "search", "BView"])

            self.assertEqual(0, result)
            self.assertTrue(db_path.exists())
            self.assertEqual("", output.getvalue())

    def test_query_dump_commands_read_empty_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"

            for command in ("dump-symbols", "dump-kits"):
                output = StringIO()
                with redirect_stdout(output):
                    result = query_main(["--db", str(db_path), command])

                self.assertEqual(0, result)
                self.assertEqual("", output.getvalue())

    def test_indexer_incremental_scans_source_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "headers"
            source.mkdir()
            (source / "View.h").write_text("class BView {};", encoding="utf-8")
            output = StringIO()

            with redirect_stdout(output):
                result = indexer_main(["--db", str(db_path), "--incremental", str(source)])

            self.assertEqual(0, result)
            self.assertIn("scanned=1", output.getvalue())
            self.assertIn("new=1", output.getvalue())

    def test_indexer_sdk_option_scans_header_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            sdk = root / "develop" / "headers"
            sdk.mkdir(parents=True)
            (sdk / "Application.h").write_text("class BApplication {};", encoding="utf-8")
            output = StringIO()

            with redirect_stdout(output):
                result = indexer_main(["--db", str(db_path), "--sdk", str(sdk)])

            self.assertEqual(0, result)
            self.assertIn("scanned=1", output.getvalue())
            self.assertIn(f"source={sdk}", output.getvalue())

    def test_indexer_haiku_source_option_scans_headers_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            haiku_source = root / "haiku"
            headers = haiku_source / "headers"
            headers.mkdir(parents=True)
            (headers / "View.h").write_text("class BView {};", encoding="utf-8")
            output = StringIO()

            with redirect_stdout(output):
                result = indexer_main(
                    ["--db", str(db_path), "--haiku-source", str(haiku_source)]
                )

            self.assertEqual(0, result)
            self.assertIn("scanned=1", output.getvalue())
            self.assertIn(f"source={headers}", output.getvalue())

    def test_indexer_then_dump_symbols_prints_parsed_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "headers"
            source.mkdir()
            (source / "View.h").write_text("class BView : public BHandler {};", encoding="utf-8")

            with redirect_stdout(StringIO()):
                indexer_main(["--db", str(db_path), "--incremental", str(source)])

            output = StringIO()
            with redirect_stdout(output):
                result = query_main(["--db", str(db_path), "dump-symbols"])

            self.assertEqual(0, result)
            self.assertIn("class\tBView", output.getvalue())

    def test_query_search_prints_matching_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "headers"
            source.mkdir()
            (source / "View.h").write_text("class BView : public BHandler {};", encoding="utf-8")

            with redirect_stdout(StringIO()):
                indexer_main(["--db", str(db_path), "--incremental", str(source)])

            output = StringIO()
            with redirect_stdout(output):
                result = query_main(["--db", str(db_path), "search", "View"])

            self.assertEqual(0, result)
            self.assertIn("class\tBView\tView.h:1", output.getvalue())

    def test_query_show_prints_symbol_detail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "headers"
            source.mkdir()
            (source / "View.h").write_text("class BView : public BHandler {};", encoding="utf-8")

            with redirect_stdout(StringIO()):
                indexer_main(["--db", str(db_path), "--incremental", str(source)])

            output = StringIO()
            with redirect_stdout(output):
                result = query_main(["--db", str(db_path), "show", "BView"])

            self.assertEqual(0, result)
            self.assertIn("BView", output.getvalue())
            self.assertIn("Kind: class", output.getvalue())
            self.assertIn("Header: View.h:1", output.getvalue())
            self.assertIn("inherits: BHandler", output.getvalue())

    def test_query_search_and_show_include_public_methods(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "atlas.sqlite3"
            source = root / "headers"
            source.mkdir()
            (source / "View.h").write_text(
                """
                class BView : public BHandler {
                public:
                    virtual void Draw(BRect update);
                };
                """,
                encoding="utf-8",
            )

            with redirect_stdout(StringIO()):
                indexer_main(["--db", str(db_path), "--incremental", str(source)])

            search_output = StringIO()
            with redirect_stdout(search_output):
                search_result = query_main(["--db", str(db_path), "search", "Draw"])

            show_output = StringIO()
            with redirect_stdout(show_output):
                show_result = query_main(["--db", str(db_path), "show", "BView::Draw"])

            self.assertEqual(0, search_result)
            self.assertIn("method\tBView::Draw", search_output.getvalue())
            self.assertEqual(0, show_result)
            self.assertIn("Kind: method", show_output.getvalue())
            self.assertIn("Declaration: virtual void Draw(BRect update);", show_output.getvalue())

    def test_query_show_returns_error_for_missing_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "atlas.sqlite3"
            output = StringIO()

            with redirect_stdout(output):
                result = query_main(["--db", str(db_path), "show", "Missing"])

            self.assertEqual(1, result)
            self.assertIn("symbol not found", output.getvalue())


if __name__ == "__main__":
    unittest.main()
