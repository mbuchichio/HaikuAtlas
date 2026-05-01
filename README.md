# Haiku API Atlas

Haiku API Atlas is a local explorer for the Haiku API. The v0 starts as a
Python CLI that builds a SQLite index from Haiku headers and later feeds a
separate UI.

## Requirements

- Python 3.10+
- SQLite support from the Python standard library

## Quick Start

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
atlas-indexer --db data/haiku-atlas.sqlite3
atlas-query --db data/haiku-atlas.sqlite3 search BView
```

On Haiku, use the Python command that exists on your system. For example:

```sh
python3.10 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Current Commands

- `atlas-indexer --full PATH`
- `atlas-indexer --incremental PATH`
- `atlas-query search NAME`
- `atlas-query show NAME`
- `atlas-query dump-symbols`
- `atlas-query dump-kits`

The indexer and query commands currently initialize the database and expose the
CLI shape. Header scanning and search implementation come next.

## Project Notes

- [Spec / seed](docs/Haiku%20Atlas%20seed.md)
- [Implementation plan](docs/Haiku%20Atlas%20implementation%20plan.md)

## Tests

The smoke tests use only the Python standard library:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
```
