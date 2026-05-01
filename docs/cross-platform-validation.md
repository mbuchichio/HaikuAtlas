# Cross-platform validation

This checklist keeps the v0 flow reproducible across Linux and Windows.

## Linux

Validated on 2026-05-01 with `/home/mario/Dev/haiku`.

    ./atlas-indexer /home/mario/Dev/haiku
    ./atlas-indexer
    ./atlas status
    ./atlas search BView
    ./atlas show BMessage::SendReply
    ./atlas

Expected:

    indexer scans 2627 headers
    atlas-indexer without SOURCE rebuilds the stored source path
    atlas opens the local web UI
    search finds BView
    show prints BMessage::SendReply

## Windows

Validated on 2026-05-01 with `sources\haiku` on Windows and Python 3.12.

    atlas-indexer.bat C:\path\to\haiku
    atlas-indexer.bat
    atlas.bat status
    atlas.bat search BView
    atlas.bat show BMessage::SendReply
    atlas.bat web --host 127.0.0.1 --port 8766 --no-open

Observed:

    indexer scans 2627 headers into db\haiku-atlas.sqlite3
    atlas-indexer.bat without SOURCE rebuilds the stored source path
    atlas.bat status reports 2627 headers, 13 kits, 17826 symbols
    search finds BView
    show prints BMessage::SendReply
    web UI responds with HTTP 200 and renders Haiku Atlas
