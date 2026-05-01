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

Pending validation on a Windows machine with Python 3.10+.

    atlas-indexer.bat C:\path\to\haiku
    atlas-indexer.bat
    atlas.bat status
    atlas.bat search BView
    atlas.bat show BMessage::SendReply
    atlas.bat

Expected:

    indexer scans the same headers into db\haiku-atlas.sqlite3
    atlas-indexer.bat without SOURCE rebuilds the stored source path
    atlas.bat opens the local web UI
    search finds BView
    show prints BMessage::SendReply
