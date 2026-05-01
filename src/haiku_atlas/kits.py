"""Kit inference from Haiku header paths."""

from __future__ import annotations

KIT_DISPLAY_NAMES = {
    "app": "Application Kit",
    "device": "Device Kit",
    "game": "Game Kit",
    "interface": "Interface Kit",
    "locale": "Locale Kit",
    "mail": "Mail Kit",
    "media": "Media Kit",
    "midi": "MIDI Kit",
    "midi2": "MIDI2 Kit",
    "net": "Network Kit",
    "storage": "Storage Kit",
    "support": "Support Kit",
    "translation": "Translation Kit",
}

AGGREGATE_HEADER_KITS = {
    "AppKit.h": "app",
    "DeviceKit.h": "device",
    "GameKit.h": "game",
    "InterfaceKit.h": "interface",
    "LocaleKit.h": "locale",
    "MailKit.h": "mail",
    "MediaKit.h": "media",
    "MidiKit.h": "midi",
    "NetworkKit.h": "net",
    "NetKit.h": "net",
    "StorageKit.h": "storage",
    "SupportKit.h": "support",
    "TranslationKit.h": "translation",
}


def infer_kit_name(file_path: str) -> str | None:
    parts = file_path.split("/")
    if len(parts) < 2:
        return None

    if parts[0] == "os":
        if len(parts) >= 3 and parts[1] in KIT_DISPLAY_NAMES:
            return parts[1]
        return AGGREGATE_HEADER_KITS.get(parts[1])

    if parts[0] == "private" and len(parts) >= 3:
        if parts[1] in KIT_DISPLAY_NAMES:
            return parts[1]

    return None


def kit_display_name(name: str) -> str:
    return KIT_DISPLAY_NAMES.get(name, f"{name.title()} Kit")
