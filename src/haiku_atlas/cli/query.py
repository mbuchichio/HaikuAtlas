"""CLI for querying a Haiku Atlas index."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from haiku_atlas.cli.help import read_cli_reference
from haiku_atlas.db import DEFAULT_DB_PATH, initialize_database
from haiku_atlas.kits import kit_display_name
from haiku_atlas.query import (
    get_index_status,
    get_symbol_page,
    list_kit_symbols,
    list_kits,
    search_symbols,
)
from haiku_atlas.setup import DEFAULT_SOURCE_PATH, setup_haiku_source
from haiku_atlas.web import serve

MAX_METHODS_SHOWN = 40
MAX_KIT_SYMBOLS_SHOWN = 80


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=argparse.SUPPRESS,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search indexed symbols by name.")
    search.add_argument("term", help="Name fragment to search for.")

    show = subparsers.add_parser("show", help="Show one indexed symbol.")
    show.add_argument("name", help="Symbol name to display.")

    subparsers.add_parser("status", help="Show index status.")
    subparsers.add_parser("kits", help="List indexed kits.")

    kit = subparsers.add_parser("kit", help="List top-level symbols in one kit.")
    kit.add_argument("name", help="Kit name, such as interface or 'Interface Kit'.")

    web = subparsers.add_parser("web", help="Start the local web UI.")
    web.add_argument("--host", default="127.0.0.1", help=argparse.SUPPRESS)
    web.add_argument("--port", type=int, default=8765, help=argparse.SUPPRESS)
    web.add_argument("--no-open", action="store_true", help=argparse.SUPPRESS)

    setup = subparsers.add_parser("setup", help="Download and index Haiku source.")
    setup.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH, help=argparse.SUPPRESS)
    setup.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    setup.add_argument("--no-open", action="store_true", help=argparse.SUPPRESS)

    subparsers.add_parser("help", help="Print the long Haiku Atlas CLI reference.")
    subparsers.add_parser("dump-symbols", help="Print all indexed symbols.")
    subparsers.add_parser("dump-kits", help="Print all indexed kits.")

    return parser


def main(argv: list[str] | None = None) -> int:
    effective_argv = sys.argv[1:] if argv is None else argv
    if not effective_argv:
        effective_argv = ["web"]
    args = build_parser().parse_args(effective_argv)

    if args.command == "help":
        print(read_cli_reference(), end="")
        return 0

    initialize_database(args.db)

    if args.command == "search":
        with closing(sqlite3.connect(args.db)) as connection:
            results = search_symbols(connection, args.term)
        for result in results:
            location = ""
            if result.file_path:
                location = f"\t{result.file_path}"
                if result.line_start is not None:
                    location += f":{result.line_start}"
            kit = f"\t{result.kit_display_name}" if result.kit_display_name else ""
            print(f"{result.kind}\t{result.qualified_name}{kit}{location}")
        return 0

    if args.command == "show":
        with closing(sqlite3.connect(args.db)) as connection:
            page = get_symbol_page(connection, args.name)
        if page is None:
            print(f"atlas: symbol not found: {args.name}")
            return 1

        detail = page.detail
        print(detail.display_name)
        print(detail.kind)
        if detail.qualified_name != detail.display_name:
            print(detail.qualified_name)
        if detail.kit_display_name:
            print(detail.kit_display_name)
        if detail.file_path:
            location = detail.file_path
            if detail.line_start is not None:
                location += f":{detail.line_start}"
            print(location)
        if page.inherits:
            print("inherits " + ", ".join(page.inherits))
        if detail.raw_declaration:
            print("")
            print(detail.raw_declaration)
        if page.methods:
            print("")
            print("methods")
            for method in page.methods[:MAX_METHODS_SHOWN]:
                print(f"  {method}")
            hidden_methods = len(page.methods) - MAX_METHODS_SHOWN
            if hidden_methods > 0:
                print(f"  ... {hidden_methods} more")
        if page.other_relations:
            print("")
            print("relations")
            for relation_type, target in page.other_relations:
                print(f"  {relation_type}: {target}")
        return 0

    if args.command == "status":
        with closing(sqlite3.connect(args.db)) as connection:
            status = get_index_status(connection)
        print(f"database\t{args.db}")
        if status.source_path:
            print(f"source\t{status.source_path}")
        if status.last_indexed_at:
            print(f"indexed\t{status.last_indexed_at}")
        print(f"headers\t{status.header_count}")
        print(f"kits\t{status.kit_count}")
        print(f"symbols\t{status.symbol_count}")
        return 0

    if args.command == "kits":
        with closing(sqlite3.connect(args.db)) as connection:
            kits = list_kits(connection)
        if not kits:
            print("no kits indexed")
            print("run: ./atlas-indexer /path/to/haiku")
            return 0
        for kit in kits:
            print(f"{kit.name}\t{kit.display_name}\t{kit.symbol_count}")
        return 0

    if args.command == "kit":
        with closing(sqlite3.connect(args.db)) as connection:
            result = list_kit_symbols(connection, args.name, limit=MAX_KIT_SYMBOLS_SHOWN)
        if result is None:
            print(f"atlas: kit not found: {args.name}")
            return 1

        kit, symbols = result
        print(kit.display_name)
        print(f"{kit.symbol_count} symbols")
        if symbols:
            print("")
            for symbol in symbols:
                location = ""
                if symbol.file_path:
                    location = f"\t{symbol.file_path}"
                    if symbol.line_start is not None:
                        location += f":{symbol.line_start}"
                print(f"{symbol.kind}\t{symbol.qualified_name}{location}")
            hidden_symbols = kit.top_level_symbol_count - len(symbols)
            if hidden_symbols > 0:
                print(f"... {hidden_symbols} more")
        return 0

    if args.command == "web":
        serve(args.db, host=args.host, port=args.port, open_browser=not args.no_open)
        return 0

    if args.command == "setup":
        result = setup_haiku_source(
            db_path=args.db,
            source_path=args.source,
            assume_yes=args.yes,
        )
        if result == 0 and not args.no_open:
            serve(args.db)
        return result

    if args.command == "dump-symbols":
        with closing(sqlite3.connect(args.db)) as connection:
            rows = connection.execute(
                "SELECT kind, qualified_name FROM symbols ORDER BY qualified_name"
            ).fetchall()
        for kind, qualified_name in rows:
            print(f"{kind}\t{qualified_name}")
        return 0

    if args.command == "dump-kits":
        with closing(sqlite3.connect(args.db)) as connection:
            rows = connection.execute("SELECT name FROM kits ORDER BY name").fetchall()
        for (name,) in rows:
            print(f"{name}\t{kit_display_name(name)}")
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
