"""CLI for building or updating a Haiku Atlas index."""

from __future__ import annotations

import argparse
from pathlib import Path

from haiku_atlas.db import DEFAULT_DB_PATH, initialize_database


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

    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help="Path to a Haiku source tree or installed header root.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    initialize_database(args.db)

    mode = "full" if args.full else "incremental" if args.incremental else "bootstrap"
    source = str(args.source) if args.source else "(not set)"
    print(f"atlas-indexer: initialized {args.db} [{mode}] source={source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

