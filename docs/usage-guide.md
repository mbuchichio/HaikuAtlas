# Usage guide

## Fast start

    ./atlas setup

Atlas asks before downloading the Haiku repository into `sources/haiku`, builds
the local SQLite index, and opens the browser UI.

## Existing Haiku checkout

    ./atlas-indexer /path/to/haiku
    ./atlas

Atlas stores the resolved header path in `db/haiku-atlas.sqlite3`. After that:

    ./atlas-indexer

rebuilds the last indexed source.

## Installed SDK headers

    ./atlas-indexer /boot/system/develop/headers
    ./atlas

## Useful commands

    ./atlas                 open the browser UI
    ./atlas status          show index metadata
    ./atlas search BView    search symbols
    ./atlas show BView      show a symbol in the terminal
    ./atlas web --no-open   run the web UI without opening a browser

## Windows

Use the `.bat` wrappers from the repository root:

    atlas.bat setup
    atlas.bat
    atlas-indexer.bat

## Data directories

    db/                     generated SQLite index
    sources/                downloaded Haiku source tree

Both directories are ignored by git.
