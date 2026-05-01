"""Small heuristic parser for Haiku C/C++ headers."""

from __future__ import annotations

from dataclasses import dataclass
import re

TYPE_PATTERN = re.compile(
    r"^\s*(class|struct)\s+([A-Za-z_]\w*)(?:\s*:\s*(?P<bases>[^{;]+))?\s*(?P<body>[{;]?)"
)
ENUM_PATTERN = re.compile(
    r"^\s*enum(?:\s+class)?\s+([A-Za-z_]\w*)\s*(?P<body>[{;]?)"
)
BASE_PATTERN = re.compile(r"(?:public|protected|private)?\s*([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)")


@dataclass(frozen=True)
class ParsedSymbol:
    kind: str
    name: str
    qualified_name: str
    line_start: int
    line_end: int
    raw_declaration: str
    inherits: tuple[str, ...] = ()


def parse_header_symbols(source: str) -> list[ParsedSymbol]:
    """Detect class, struct, and enum declarations from one header."""
    symbols: list[ParsedSymbol] = []

    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "*")):
            continue

        type_match = TYPE_PATTERN.match(line)
        if type_match and _is_definition_or_inherited_declaration(type_match):
            kind = type_match.group(1)
            name = type_match.group(2)
            bases = _parse_bases(type_match.group("bases") or "")
            symbols.append(
                ParsedSymbol(
                    kind=kind,
                    name=name,
                    qualified_name=name,
                    line_start=line_number,
                    line_end=line_number,
                    raw_declaration=stripped,
                    inherits=bases,
                )
            )
            continue

        enum_match = ENUM_PATTERN.match(line)
        if enum_match and enum_match.group("body") != ";":
            name = enum_match.group(1)
            symbols.append(
                ParsedSymbol(
                    kind="enum",
                    name=name,
                    qualified_name=name,
                    line_start=line_number,
                    line_end=line_number,
                    raw_declaration=stripped,
                )
            )

    return symbols


def _is_definition_or_inherited_declaration(match: re.Match[str]) -> bool:
    return match.group("body") == "{" or match.group("bases") is not None


def _parse_bases(raw_bases: str) -> tuple[str, ...]:
    bases: list[str] = []
    for base in raw_bases.split(","):
        match = BASE_PATTERN.fullmatch(base.strip())
        if match:
            bases.append(match.group(1))
    return tuple(bases)

