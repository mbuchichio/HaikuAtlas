"""Long-form CLI help loaded from the project docs."""

from __future__ import annotations

from pathlib import Path

CLI_REFERENCE_PATH = Path(__file__).resolve().parents[3] / "docs" / "cli-reference"


def read_cli_reference() -> str:
    return CLI_REFERENCE_PATH.read_text(encoding="utf-8")

