"""CLI for building or updating a Haiku Atlas index."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from haiku_atlas.db import DEFAULT_DB_PATH, initialize_database
from haiku_atlas.file_index import update_file_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas-indexer")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"SQLite index path (default: {DEFAULT_DB_PATH})",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true", help="Run a full index pass.")
    mode.add_argument("--incremental", action="store_true", help="Run an incremental index pass.")

    source_mode = parser.add_mutually_exclusive_group()
    source_mode.add_argument(
        "--sdk",
        type=Path,
        help="Path to an installed Haiku SDK header root, such as /boot/system/develop/headers.",
    )
    source_mode.add_argument(
        "--haiku-source",
        type=Path,
        help="Path to a full Haiku source checkout. The indexer scans its headers/ directory.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help="Path to a header root. Prefer --sdk or --haiku-source for clarity.",
    )
    return parser


def resolve_source_path(args: argparse.Namespace) -> Path | None:
    if args.sdk is not None:
        return args.sdk
    if args.haiku_source is not None:
        return args.haiku_source / "headers"
    return args.source


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    initialize_database(args.db)

    mode = "full" if args.full else "incremental" if args.incremental else "bootstrap"
    source_path = resolve_source_path(args)
    source = str(source_path) if source_path else "(not set)"

    if source_path is None:
        print(f"atlas-indexer: initialized {args.db} [{mode}] source={source}")
        return 0

    with sqlite3.connect(args.db) as connection:
        result = update_file_index(connection, source_path, full=args.full)

    print(
        "atlas-indexer: "
        f"{mode} scanned={result.scanned} "
        f"new={len(result.new)} changed={len(result.changed)} "
        f"deleted={len(result.deleted)} unchanged={len(result.unchanged)} "
        f"db={args.db} source={source}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
