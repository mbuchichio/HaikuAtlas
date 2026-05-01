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
./atlas setup
```

`setup` asks before downloading the Haiku source tree into `sources/haiku`,
indexes it, then opens Atlas.

For a Haiku source checkout on Linux:

```sh
./atlas-indexer ~/src/haiku
./atlas
```

After the first index, `./atlas-indexer` rebuilds the last source path.

On Windows, run the `.bat` wrappers from the repository root:

```bat
atlas-indexer.bat C:\path\to\haiku
atlas.bat web
```

## Current Commands

- `./atlas-indexer SOURCE`
- `./atlas-indexer`
- `./atlas-indexer --full SOURCE`
- `./atlas`
- `./atlas setup`
- `./atlas search NAME`
- `./atlas show NAME`
- `./atlas web`
- `./atlas help`
- `./atlas dump-symbols`
- `./atlas dump-kits`

The indexer currently scans `.h` and `.hpp` files, stores file metadata,
detects new, changed, deleted, and unchanged files, and extracts simple
class/struct/enum symbols plus public methods. The query CLI can search symbols
and show basic symbol details.

## Project Notes

- [CLI reference](docs/cli-reference)
- [Usage guide](docs/usage-guide.md)
- [Index format v0](docs/index-format-v0.md)
- [Changelog](docs/changelog.md)
- [Cross-platform validation](docs/cross-platform-validation.md)
- [v1 roadmap](docs/v1-roadmap.md)
- [Spec / seed](docs/Haiku%20Atlas%20seed.md)
- [Implementation plan](docs/Haiku%20Atlas%20implementation%20plan.md)

## License

MIT. See [LICENSE](LICENSE).

## Tests

The smoke tests use only the Python standard library:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
```
