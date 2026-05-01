# Haiku API Atlas - Implementation Plan

This document keeps the operational plan separate from the spec/seed.

## 1. Base Decisions

- [x] Confirm v0 stack: Python 3.10+, SQLite, CLI-first, decoupled UI.
- [ ] Confirm v0 scope: heuristic parser, incremental index, name search.
- [x] Define input policy: installed SDK, full source tree, or both.
- [x] Lock project name and binary names (atlas-indexer, atlas).

## 2. Week 1 - Project Bootstrap

- [x] Create folder structure (src/, data/, tests/, docs/).
- [x] Create pyproject.toml with basic tooling (formatter, linter, test).
- [x] Define base CLI commands (index, dump-symbols, dump-kits, search).
- [x] Add data/schema.sql with files, symbols, relations, docs tables.
- [x] Implement DB initialization and schema migration on startup.
- [x] Document quick setup in README.

## 3. Week 2 - Minimal Functional Indexer

- [x] Implement header file scanning (.h, .hpp) from a configured path.
- [x] Persist file metadata (path, mtime, size, last_indexed_at).
- [x] Implement incremental detection (new/changed/deleted/unchanged).
- [x] Implement heuristic parser for class, struct, enum.
- [x] Store symbols and minimal relations (inherits, defined_in).
- [x] Expose atlas-indexer --full and atlas-indexer --incremental.
- [x] Validate with fixtures and readable console dumps.

## 4. Week 3 - Public Methods and Search

- [x] Detect public/protected/private sections per class.
- [x] Extract simple signatures for public methods and constructors/destructors.
- [x] Store methods in symbols and contains relations.
- [x] Implement name search (class/method) with simple ranking.
- [x] Add atlas search "BView".
- [x] Add atlas show "BView" for node detail.

## 5. Week 4 - Quality and DX

- [x] Add configurable logging (--verbose) for the indexer.
- [x] Add error handling and soft parser failures (raw declaration).
- [ ] Cover edge cases: macros, multiline signatures, incomplete headers.
- [ ] Add regression tests with real Haiku API fixtures.
- [ ] Measure baseline performance (full and incremental index time).
- [ ] Define v0 performance acceptance thresholds.

## 6. Week 5 - Minimal Cross-Platform UI

- [ ] Choose v0 frontend (TUI or local web) that consumes SQLite.
- [ ] Show kit browser and node detail panel.
- [ ] Implement search box connected to atlas/SQL queries.
- [ ] Implement basic history (back/forward/recent).
- [ ] Validate on Linux and Windows with the same index.

## 7. Week 6 - v0 Release

- [ ] Freeze SQLite index format v0.
- [ ] Write usage guide for SDK mode and source tree mode.
- [ ] Generate binaries/packages for Linux and Windows.
- [ ] Run end-to-end smoke test in a clean environment.
- [ ] Publish changelog and v1 roadmap.

## 8. Definition of Done (v0)

- [ ] Indexes headers from a real Haiku tree without crashing.
- [ ] Finds canonical nodes (BApplication, BWindow, BView, BMessage).
- [ ] Shows main public methods per class.
- [ ] Incremental reindex reuses cache and reduces runtime.
- [ ] Works on Linux and Windows with the same CLI flow.

## 9. Post-v0 Backlog

- [ ] Extract nearby comments as docs per node.
- [ ] Source path guessing and implementation indexing.
- [ ] Examples finder (example_uses_symbol).
- [ ] Persistent bookmarks and recently viewed nodes.
- [ ] Alternative provider using Clang or Doxygen.
