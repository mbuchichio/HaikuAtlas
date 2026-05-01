# Changelog

All notable changes to Haiku Atlas are documented here.

## 2026-05-01 - v0 Validation Checkpoint

### Added

- Documented the Windows `.bat` validation flow in `docs/cross-platform-validation.md`.
- Added the v0 validation checkpoint to the implementation plan.

### Fixed

- Closed SQLite connections explicitly with `contextlib.closing` so Windows can release database files immediately after CLI, setup, web, and test operations.
- Updated direct SQLite test helpers to close connections explicitly, preventing `TemporaryDirectory` cleanup failures on Windows.

### Validated

- Windows `.bat` flow against `sources\haiku`:
  - `atlas-indexer.bat sources\haiku`
  - `atlas-indexer.bat`
  - `atlas.bat status`
  - `atlas.bat search BView`
  - `atlas.bat show BMessage::SendReply`
  - `atlas.bat web --host 127.0.0.1 --port 8766 --no-open`
- Current local index reports 2627 headers, 13 kits, and 17826 symbols.
- Canonical v0 nodes resolve with public methods: `BApplication`, `BWindow`, `BView`, and `BMessage`.
- Unit suite passes on Windows: 72 tests.

