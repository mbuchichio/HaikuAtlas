"""CLI for building or updating a Haiku Atlas index."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from haiku_atlas.db import DEFAULT_DB_PATH, initialize_database
from haiku_atlas.cli.help import read_cli_reference
from haiku_atlas.file_index import FileIndexError, update_file_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas-indexer")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=argparse.SUPPRESS,
    )

    parser.add_argument("--full", action="store_true", help="Force a full reindex.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    source_mode = parser.add_mutually_exclusive_group()
    source_mode.add_argument(
        "--sdk",
        type=Path,
        help=argparse.SUPPRESS,
    )
    source_mode.add_argument(
        "--haiku-source",
        type=Path,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help="Header root or Haiku source checkout.",
    )
    return parser


def resolve_source_path(args: argparse.Namespace) -> Path | None:
    if args.sdk is not None:
        return args.sdk
    if args.haiku_source is not None:
        return args.haiku_source / "headers"
    if args.source is None:
        return None
    source_headers = args.source / "headers"
    if source_headers.is_dir():
        return source_headers
    return args.source


def main(argv: list[str] | None = None) -> int:
    effective_argv = sys.argv[1:] if argv is None else argv
    if effective_argv == ["help"]:
        print(read_cli_reference(), end="")
        return 0

    args = build_parser().parse_args(effective_argv)
    initialize_database(args.db)

    source_path = resolve_source_path(args)
    mode = "full" if args.full else "incremental" if source_path is not None else "bootstrap"
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
        f"{_error_summary(result.errors)}"
        f"db={args.db} source={source}"
    )
    if args.verbose:
        _print_verbose_paths("new", result.new)
        _print_verbose_paths("changed", result.changed)
        _print_verbose_paths("deleted", result.deleted)
        _print_verbose_errors(result.errors)
    return 0


def _error_summary(errors: tuple[FileIndexError, ...]) -> str:
    if not errors:
        return ""
    return f"errors={len(errors)} "


def _print_verbose_paths(label: str, paths: tuple[str, ...]) -> None:
    if not paths:
        return

    print(label)
    for path in paths:
        print(f"  {path}")


def _print_verbose_errors(errors: tuple[FileIndexError, ...]) -> None:
    if not errors:
        return

    print("errors")
    for error in errors:
        print(f"  {error.path}: {error.message}")


if __name__ == "__main__":
    raise SystemExit(main())
