"""CLI for querying a Haiku Atlas index."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from haiku_atlas.cli.help import read_cli_reference
from haiku_atlas.db import DEFAULT_DB_PATH, initialize_database
from haiku_atlas.query import get_symbol_page, search_symbols

MAX_METHODS_SHOWN = 40


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

    subparsers.add_parser("help", help="Print the long Haiku Atlas CLI reference.")
    subparsers.add_parser("dump-symbols", help="Print all indexed symbols.")
    subparsers.add_parser("dump-kits", help="Print all indexed kits.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "help":
        print(read_cli_reference(), end="")
        return 0

    initialize_database(args.db)

    if args.command == "search":
        with sqlite3.connect(args.db) as connection:
            results = search_symbols(connection, args.term)
        for result in results:
            location = ""
            if result.file_path:
                location = f"\t{result.file_path}"
                if result.line_start is not None:
                    location += f":{result.line_start}"
            print(f"{result.kind}\t{result.qualified_name}{location}")
        return 0

    if args.command == "show":
        with sqlite3.connect(args.db) as connection:
            page = get_symbol_page(connection, args.name)
        if page is None:
            print(f"atlas: symbol not found: {args.name}")
            return 1

        detail = page.detail
        print(detail.display_name)
        print(detail.kind)
        if detail.qualified_name != detail.display_name:
            print(detail.qualified_name)
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

    if args.command == "dump-symbols":
        with sqlite3.connect(args.db) as connection:
            rows = connection.execute(
                "SELECT kind, qualified_name FROM symbols ORDER BY qualified_name"
            )
            for kind, qualified_name in rows:
                print(f"{kind}\t{qualified_name}")
        return 0

    if args.command == "dump-kits":
        with sqlite3.connect(args.db) as connection:
            rows = connection.execute("SELECT name, display_name FROM kits ORDER BY name")
            for name, display_name in rows:
                print(f"{name}\t{display_name}")
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
