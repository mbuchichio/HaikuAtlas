# Changelog

All notable changes to Haiku Atlas are documented here.

## 2026-05-01 - v0 Validation Checkpoint

### Added

- Added `atlas setup` to download Haiku, build the index, and open Atlas.
- Added local web UI as the default `atlas` experience.
- Added Linux shell wrappers and Windows `.bat` wrappers.
- Added SQLite indexer for Haiku headers.
- Added search, kit browsing, symbol detail pages, and source context labels.
- Added parser support for public methods, constructors, destructors, multiline
  signatures, export macros, and truncated declarations.
- Added v0 release docs for usage, index format, changelog, and roadmap.
- Documented cross-platform validation notes for Linux and Windows.
- Added web index controls for choosing a source path and running incremental or
  full reindexing from the local UI.

### Fixed

- Closed SQLite connections explicitly with `contextlib.closing` so Windows can
  release database files immediately after CLI, setup, web, and test operations.
- Updated direct SQLite test helpers to close connections explicitly, preventing
  `TemporaryDirectory` cleanup failures on Windows.
- Display `midi2` as `MIDI2 Kit` so it no longer appears as a duplicate
  `MIDI Kit` in kit lists.
- Parse class and struct definitions whose opening brace is on the following
  line, fixing missing MIDI2 classes such as `BMidiEndpoint` and `BMidiRoster`.

### Validated

- Windows `.bat` flow against `sources\haiku`:
  - `atlas-indexer.bat sources\haiku`
  - `atlas-indexer.bat`
  - `atlas.bat status`
  - `atlas.bat search BView`
  - `atlas.bat show BMessage::SendReply`
  - `atlas.bat web --host 127.0.0.1 --port 8766 --no-open`
- Current local index reports 2627 headers, 13 kits, and 17826 symbols.
- Canonical v0 nodes resolve with public methods: `BApplication`, `BWindow`,
  `BView`, and `BMessage`.
- Unit suite passes on Windows: 72 tests.
