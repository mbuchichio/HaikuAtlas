# Haiku API Atlas

Haiku API Atlas is a local explorer for the Haiku API. It indexes Haiku headers
into SQLite, then lets you browse kits, classes, methods, and source context
through a local web UI or terminal commands.

## Quick Start

```sh
./atlas setup
```

`setup` asks before downloading Haiku into `sources/haiku`, builds
`db/haiku-atlas.sqlite3`, and opens the local web UI.

With an existing Haiku checkout:

```sh
./atlas-indexer /path/to/haiku
./atlas
```

On Windows, use the `.bat` wrappers:

```bat
atlas-indexer.bat C:\path\to\haiku
atlas.bat
```

## Commands

```sh
./atlas                 # open the local web UI
./atlas status
./atlas search BView
./atlas show BMessage::SendReply
./atlas kits
./atlas kit interface
./atlas-indexer SOURCE
```

## Documentation

- [Usage guide](docs/usage-guide.md)
- [CLI reference](docs/cli-reference)
- [Index format v0](docs/index-format-v0.md)
- [Changelog](docs/changelog.md)
- [v1 roadmap](docs/v1-roadmap.md)

Historical planning notes:

- [Spec / seed](docs/Haiku%20Atlas%20seed.md)
- [Implementation plan](docs/Haiku%20Atlas%20implementation%20plan.md)

## License

MIT. See [LICENSE](LICENSE).

## Tests

The smoke tests use only the Python standard library:

```sh
PYTHONPATH=src python -m unittest discover -s tests
```
