"""CLI for querying a Haiku Atlas index."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from haiku_atlas.db import DEFAULT_DB_PATH, initialize_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas-query")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"SQLite index path (default: {DEFAULT_DB_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search indexed symbols by name.")
    search.add_argument("term", help="Name fragment to search for.")

    show = subparsers.add_parser("show", help="Show one indexed symbol.")
    show.add_argument("name", help="Symbol name to display.")

    subparsers.add_parser("dump-symbols", help="Print all indexed symbols.")
    subparsers.add_parser("dump-kits", help="Print all indexed kits.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    initialize_database(args.db)

    if args.command == "search":
        print(f"atlas-query: search is not implemented yet for {args.term!r}")
        return 0

    if args.command == "show":
        print(f"atlas-query: show is not implemented yet for {args.name!r}")
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
