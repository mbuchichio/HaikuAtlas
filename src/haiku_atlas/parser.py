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
ACCESS_PATTERN = re.compile(r"^\s*(public|protected|private)\s*:\s*$")
METHOD_PATTERN = re.compile(
    r"^\s*"
    r"(?:(?:virtual|static|inline|explicit|friend)\s+)*"
    r"(?:(?P<return_type>[A-Za-z_][\w:<>,~*&\s]*?)\s+)?"
    r"(?P<name>~?[A-Za-z_]\w*)"
    r"\s*\([^;{}]*\)"
    r"\s*(?:const\s*)?(?:override\s*)?(?:=\s*0\s*)?"
    r"[;{]"
)


@dataclass(frozen=True)
class ParsedSymbol:
    kind: str
    name: str
    qualified_name: str
    line_start: int
    line_end: int
    raw_declaration: str
    inherits: tuple[str, ...] = ()
    parent_qualified_name: str | None = None


def parse_header_symbols(source: str) -> list[ParsedSymbol]:
    """Detect class, struct, enum, and simple public method declarations."""
    symbols: list[ParsedSymbol] = []
    current_type: ParsedSymbol | None = None
    current_access: str | None = None
    type_brace_depth = 0

    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "*")):
            continue

        if current_type is not None:
            access_match = ACCESS_PATTERN.match(line)
            if access_match:
                current_access = access_match.group(1)
                type_brace_depth += _brace_delta(line)
                if type_brace_depth <= 0:
                    current_type = None
                    current_access = None
                continue

            if current_access == "public":
                method = _parse_method(line, line_number, current_type)
                if method is not None:
                    symbols.append(method)

            type_brace_depth += _brace_delta(line)
            if type_brace_depth <= 0:
                current_type = None
                current_access = None
            continue

        type_match = TYPE_PATTERN.match(line)
        if type_match and _is_definition_or_inherited_declaration(type_match):
            kind = type_match.group(1)
            name = type_match.group(2)
            bases = _parse_bases(type_match.group("bases") or "")
            symbol = ParsedSymbol(
                kind=kind,
                name=name,
                qualified_name=name,
                line_start=line_number,
                line_end=line_number,
                raw_declaration=stripped,
                inherits=bases,
            )
            symbols.append(symbol)
            type_brace_depth = _brace_delta(line)
            if type_match.group("body") == "{" and type_brace_depth > 0:
                current_type = symbol
                current_access = "public" if kind == "struct" else "private"
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


def _brace_delta(line: str) -> int:
    return line.count("{") - line.count("}")


def _parse_method(
    line: str,
    line_number: int,
    parent: ParsedSymbol,
) -> ParsedSymbol | None:
    stripped = line.strip()
    if stripped.startswith(("typedef ", "using ", "return ")):
        return None

    match = METHOD_PATTERN.match(line)
    if match is None:
        return None

    name = match.group("name")
    if name == parent.name:
        kind = "constructor"
    elif name == f"~{parent.name}":
        kind = "destructor"
    else:
        kind = "method"

    return ParsedSymbol(
        kind=kind,
        name=name,
        qualified_name=f"{parent.qualified_name}::{name}",
        line_start=line_number,
        line_end=line_number,
        raw_declaration=stripped,
        parent_qualified_name=parent.qualified_name,
    )
