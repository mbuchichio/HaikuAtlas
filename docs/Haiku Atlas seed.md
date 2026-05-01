# Spec - Haiku API Atlas

## 0. Idea

Haiku API Atlas is a CLI/index-first tool for exploring the Haiku API as a navigable structure, not only as textual documentation. It builds a local SQLite atlas that can later feed a decoupled UI.

The main unit is not a page, but a node:

- Kit
- Class
- Struct
- Enum
- Method
- Constant
- Header
- Subsystem
- Example

The project combines two functions:

- 70% structural explorer
- 30% documentation reader

Goal: help someone understand the Haiku API, architecture, and source-code location without manually jumping between headers, online docs, repositories, and loose searches.

## 1. Design Principle

### 1.1 Guiding Phrase

> A symbol is a place.  
> The documentation is what you see when you arrive there.

### 1.2 It Is Not

It is not only:

- an HTML browser
- a Zeal/Dash clone
- a static documentation viewer
- a perfect C++ parser
- a complete IDE

### 1.3 It Is

It is:

- an atlas of the API
- a hierarchical browser for kits/classes/members
- a node reader
- an orientation tool for contributors
- a map between docs, headers, and implementation

## 2. Target Users

### 2.1 New Contributor

Wants to answer:

- Which class should I use?
- Where is it defined?
- What does it inherit from?
- Which methods does it have?
- Where is it implemented?
- Which examples exist?

### 2.2 Haiku App Developer

Wants to quickly navigate the public API:

- Application Kit
- Interface Kit
- Storage Kit
- Media Kit
- Support Kit
- Locale Kit
- Network Kit

### 2.3 Advanced Contributor

Wants to jump between:

- public header
- source implementation
- existing docs
- relationships between classes
- recent changes

## 3. Main UI

### 3.1 Base Layout

Two panels:

```text
+------------------------------+---------------------------------------------+
| Browser                      | Node Reader                                 |
|                              |                                             |
| Kits                         | BView                                       |
|  > Application Kit           |                                             |
|  > Interface Kit             | Kit: Interface Kit                          |
|      BView                   | Kind: Class                                 |
|      BWindow                 | Inherits: BHandler                          |
|      BBitmap                 | Header: headers/os/interface/View.h         |
|  > Storage Kit               | Source: src/kits/interface/View.cpp         |
|  > Media Kit                 |                                             |
|                              | Methods                                     |
| Search: [ BView________ ]    |   Draw(BRect update)                        |
|                              |   MouseDown(BPoint where)                   |
|                              |   AttachedToWindow()                        |
|                              |                                             |
|                              | Related                                     |
|                              |   BWindow, BRegion, BBitmap, app_server     |
+------------------------------+---------------------------------------------+
```

### 3.2 Browser Panel

The browser can switch views:

- By Kit
- By Class
- By Inheritance
- By Header Path
- By Subsystem
- Search Results
- Recently Viewed
- Bookmarks

Recommended initial view:

- Application Kit
- Interface Kit
- Storage Kit
- Support Kit
- Media Kit
- Translation Kit
- Locale Kit
- Network Kit
- Game Kit
- Kernel / Drivers

### 3.3 Node Reader

The right panel changes according to node type.

#### Class Node

Shows:

- Name
- Kind
- Kit
- Header path
- Source path
- Inheritance
- Public methods
- Protected methods
- Related constants/enums
- Related classes
- Docs/comment block
- Examples

#### Method Node

Shows:

- Signature
- Owning class
- Declared in
- Implemented in
- Return type
- Parameters
- Overrides / overridden by
- Docs/comment block
- Examples

#### Kit Node

Shows:

- Kit name
- Summary
- Main classes
- Common patterns
- Headers
- Subsystem relation

#### Header Node

Shows:

- Path
- Kit
- Declared symbols
- Includes
- Last indexed
- Open file action

## 4. Data Model

### 4.1 Nodes

Every navigable element is a node.

```text
SymbolNode
  id
  kind
  name
  qualified_name
  display_name
  file_id
  line_start
  line_end
  parent_id
  kit_id
```

Initial types:

- kit
- header
- class
- struct
- enum
- method
- constructor
- destructor
- field
- constant
- typedef
- namespace
- subsystem

### 4.2 Relations

Relations are as important as nodes.

```text
Relation
  id
  from_symbol_id
  relation_type
  to_symbol_id
```

Types:

- declares
- contains
- inherits
- implements
- returns
- takes_parameter
- uses
- related_to
- defined_in
- implemented_in
- belongs_to_kit

### 4.3 Files

```text
FileRecord
  id
  path
  role
  mtime
  size
  sha256_optional
  last_indexed_at
```

Roles:

- public_header
- private_header
- source
- example
- doc

## 5. Indexer

### 5.1 Goal

The indexer turns headers/source/docs into a navigable index.

```text
public headers
  -> indexer
  -> api-index.sqlite
  -> browser + node reader
```

### 5.2 Do Not Reparse Everything Every Time

The API does not change constantly, so the index can be persistent.

On startup:

- scan files
- compare mtime + size
- reindex changed files
- reuse cache for unchanged files

### 5.3 Change Detection Strategy

For each file:

- path
- mtime
- size
- optional sha256

Rules:

- if the file is new: index it
- if mtime/size changed: reindex it
- if the file disappeared: remove symbols
- if nothing changed: use cache

sha256 remains an option for strict mode.

### 5.4 Disposable Index

Fundamental rule:

> The index is cache, not a source of truth.

If it breaks:

- delete api-index.sqlite
- rebuild

## 6. Parser

### 6.1 Phase 1 - Heuristic Parser

For v0, avoid libclang.

The initial parser detects:

- class BView : public BHandler
- struct rgb_color
- enum orientation
- public/protected/private sections
- simple method signatures
- constructors/destructors
- typedefs
- constants
- nearby comments

Advantages:

- simple
- fast
- no heavy dependencies
- enough for navigation

Accepted disadvantages:

- does not understand all C++
- may fail with macros
- may miss rare cases

### 6.2 Phase 2 - Improved Parser

Later:

- ClangProvider
- Doxygen/XML provider
- prebuilt docs provider

The project should be designed with a provider interface:

```text
ISymbolProvider
  HeaderHeuristicProvider
  ClangProvider
  CachedJsonProvider
  DoxygenProvider
```

This lets the initial parser be replaced without destroying the app.

## 7. Storage

### 7.1 SQLite Recommended

Base:

- api-index.sqlite

Minimal tables:

```sql
files(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  role TEXT,
  mtime INTEGER,
  size INTEGER,
  sha256 TEXT,
  last_indexed_at INTEGER
);

symbols(
  id INTEGER PRIMARY KEY,
  kind TEXT,
  name TEXT,
  qualified_name TEXT,
  display_name TEXT,
  file_id INTEGER,
  line_start INTEGER,
  line_end INTEGER,
  parent_id INTEGER,
  kit_id INTEGER
);

relations(
  id INTEGER PRIMARY KEY,
  from_symbol_id INTEGER,
  relation_type TEXT,
  to_symbol_id INTEGER
);

docs(
  id INTEGER PRIMARY KEY,
  symbol_id INTEGER,
  source TEXT,
  body TEXT
);
```

### 7.2 Indexes

```sql
CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_qualified ON symbols(qualified_name);
CREATE INDEX idx_symbols_kind ON symbols(kind);
CREATE INDEX idx_rel_from ON relations(from_symbol_id);
CREATE INDEX idx_rel_to ON relations(to_symbol_id);
```

## 8. Project Layout

Own repository:

```text
haiku-api-atlas/
  README.md
  src/
    haiku_atlas/
      cli/
        indexer.py
        query.py
      db.py
      scanner.py
      parser.py
      model.py
      providers.py

  data/
    schema.sql

  docs/
    design.md
    parser-notes.md
    roadmap.md

  tests/
    fixtures/
      simple_class.h
      inheritance.h
      enum_method.h
```

## 9. Usage Modes

### 9.1 User Mode

For someone who only wants to inspect the API:

- use an included or generated index
- search class
- read node

### 9.2 Contributor Mode

For someone with a local Haiku repo:

- select Haiku repo path
- index headers
- open nodes
- jump to header/source
- detect changes after git pull

### 9.3 Installed SDK Mode

For a tool installed inside Haiku:

- use /boot/system/develop/headers
- use /boot/system/develop/documentation if it exists

### 9.4 Source Tree Mode

For contributors:

- use ~/haiku/headers
- use ~/haiku/src
- use ~/haiku/docs

## 10. MVP v0

### Goal

A CLI-first atlas that indexes public Haiku API classes and exposes them through query commands.

### Includes

- public header scanning
- grouping by kit
- class/struct detection
- simple inheritance detection
- public method detection
- name search
- query output with basic details
- persistent SQLite cache
- incremental reindex by mtime/size

### Does Not Include

- perfect C++ parser
- visual inheritance graph
- complete Doxygen support
- semantic search
- external editor integration
- perfect source implementation linking

### Success Criteria

- run atlas-indexer
- select repo/SDK path
- index without crashing
- see Application Kit / Interface Kit
- open BApplication, BWindow, BView, BMessage
- see main methods
- search by name
- rerun queries instantly using cache

## 11. v1

Improvements:

- nearby comments extracted from headers
- source path guessing
- examples finder
- bookmarks
- recent nodes
- better search
- inherited members
- header path mode

Examples finder:

Search in:

- src/apps
- src/tests
- src/preferences
- src/demos

Relation:

- example_uses_symbol

## 12. v2

Advanced exploration:

- visual inheritance graph
- related classes
- used by
- method override tree
- diff between API versions
- contributor mode: where to edit docs
- open in external editor
- export JSON index

## 13. UI Behavior

### 13.1 Search

Global search:

- BView
- view
- Draw
- BMessage

Grouped results:

- Classes
- Methods
- Headers
- Enums

### 13.2 Breadcrumb

The Node Reader shows:

- Interface Kit > BView > Draw(BRect)

### 13.3 Navigation History

- Back
- Forward
- Recently viewed

### 13.4 Bookmarks

Local bookmarks:

- BApplication
- BWindow
- BView
- BMessage
- BBitmap
- BPath
- BEntry

## 14. Technical Risks

### 14.1 C++ Parsing

Risk:

- complex headers
- macros
- #ifdef
- multiline signatures
- templates

Mitigation:

- heuristic good enough for MVP
- fail softly
- show raw declaration when it does not understand
- design replaceable provider

### 14.2 Source Linking

Risk:

- header declaration does not map 1:1 to implementation
- overloads
- inline methods
- generated code

Mitigation:

- v0 header only
- v1 source guess
- v2 source index

### 14.3 Scope Creep

Risk:

- ending up building an IDE

Mitigation:

- do not edit code
- do not compile
- no debugger
- no LSP initially

## 15. Explicit Non-Goals

- It is not an IDE.
- It is not a replacement for official documentation.
- It does not try to parse all C++ perfectly in v0.
- It does not require an internet connection.
- It does not depend on AI.
- It does not modify the Haiku repo.

## 16. Implementation Philosophy

### 16.1 Simple First

First:

- headers -> symbols -> tree -> node

Then:

- docs
- examples
- source links
- graphs

### 16.2 CLI-First, UI-Later

Start with a portable CLI and SQLite index:

- Python 3.10+
- SQLite
- atlas-indexer
- atlas

The UI stays decoupled. It can later become a TUI, a local web UI, or a native Haiku UI without forcing a rewrite of the indexer.

### 16.3 Separate Indexer and UI

```text
atlas-indexer
  -> generates api-index.sqlite

atlas / future UI
  -> consumes api-index.sqlite
```

This makes it possible to debug the parser without opening the UI.

## 17. CLI Surface

### atlas-indexer

Usage:

```bash
atlas-indexer --sdk /boot/system/develop/headers --out api-index.sqlite
```

Or:

```bash
atlas-indexer --haiku-source /boot/home/haiku --out api-index.sqlite
```

Options:

- --full
- --incremental
- --strict-hash
- --dump-symbols
- --dump-kits
- --verbose

### atlas

Usage:

```bash
atlas search BView
atlas show BView
atlas dump-symbols
```

## 18. First Canonical Nodes to Test

- BApplication
- BLooper
- BHandler
- BMessage
- BMessenger
- BWindow
- BView
- BBitmap
- BRect
- BPoint
- BRegion
- BFile
- BEntry
- BPath
- BDirectory
- BNode
- BMediaNode
- BBuffer
- BParameterWeb

If these work, the app already starts to become useful.

## 19. Ideal UX for a Class Node

BView example:

```text
BView
Class - Interface Kit

Declared in:
  headers/os/interface/View.h

Implemented in:
  src/kits/interface/View.cpp

Inherits:
  BHandler

Inherited by:
  BButton
  BControl
  BTextView
  ...

Common lifecycle:
  AttachedToWindow()
  Draw(BRect update)
  MouseDown(BPoint where)
  FrameResized(float width, float height)

Public methods:
  Draw(BRect update)
  Invalidate()
  SetViewColor(rgb_color)
  SetHighColor(rgb_color)
  FillRect(BRect rect)
  StrokeLine(BPoint start, BPoint end)

Related:
  BWindow
  BBitmap
  BRegion
  app_server
```

## 20. Open Questions

- Should the index include private headers?
- Should it point to the full source tree or only to the installed SDK?
- Which UI should consume the SQLite index first: TUI, local web, or native Haiku?
- SQLite or JSON for v0?
- Should existing docs be integrated, or only structure?
- Final name: Haiku Atlas, API Atlas, BeMap, ClassTracker

## 21. Suggested Roadmap

### Week 1 - Minimal Indexer

- scan headers
- detect class/struct
- detect kit by path
- write SQLite/JSON
- CLI dump

### Week 2 - Minimal Query Layer

- atlas search
- atlas show
- dump symbols
- dump kits
- load index
- class name -> show details

### Week 3 - Methods + Search

- parse public methods
- search box
- method list
- header line references

### Week 4 - Polish

- cache invalidation
- recent nodes
- bookmarks
- basic docs extraction
- experimental hpkg package

## 22. Tentative Name

Favorites:

- Haiku Atlas
- API Atlas
- BeMap
- ClassTracker
- KitExplorer

My vote: Haiku Atlas.

Because it does not promise perfect documentation. It promises something more interesting:

> cartography of the system.
