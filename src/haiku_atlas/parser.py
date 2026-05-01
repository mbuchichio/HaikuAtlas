"""Small heuristic parser for Haiku C/C++ headers."""

from __future__ import annotations

from dataclasses import dataclass
import re

TYPE_PATTERN = re.compile(
    r"^\s*(class|struct)\s+"
    r"(?:(?:[A-Z_]\w*|__declspec\([^)]*\))\s+)*"
    r"([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)"
    r"(?:\s*:\s*(?P<bases>[^{;]+))?\s*(?P<body>[{;]?)"
)
ENUM_PATTERN = re.compile(
    r"^\s*enum(?:\s+class)?\s+([A-Za-z_]\w*)\s*(?P<body>[{;]?)"
)
BASE_PATTERN = re.compile(r"(?:public|protected|private)?\s*([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)")
ACCESS_PATTERN = re.compile(r"^\s*(public|protected|private)\s*:\s*$")
METHOD_START_PATTERN = re.compile(
    r"^\s*"
    r"(?:(?:virtual|static|inline|explicit|friend)\s+)*"
    r"(?:(?:[A-Z_]\w*|__declspec\([^)]*\))\s+)*"
    r"(?:[A-Za-z_][\w:<>,~*&\s]*?\s+)?"
    r"~?[A-Za-z_]\w*"
    r"\s*\("
)
METHOD_PATTERN = re.compile(
    r"^\s*"
    r"(?:(?:virtual|static|inline|explicit|friend)\s+)*"
    r"(?:(?:[A-Z_]\w*|__declspec\([^)]*\))\s+)*"
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
    source_context: str | None = None


def parse_header_symbols(source: str) -> list[ParsedSymbol]:
    """Detect class, struct, enum, and simple public method declarations."""
    symbols: list[ParsedSymbol] = []
    current_type: ParsedSymbol | None = None
    current_access: str | None = None
    type_brace_depth = 0
    pending_method_lines: list[str] = []
    pending_method_start = 0
    pending_type_match: re.Match[str] | None = None
    pending_type_line = 0
    current_section: str | None = None

    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if current_type is not None and stripped.startswith("//"):
            section = _parse_section_comment(stripped)
            if section:
                current_section = section
            continue

        if not stripped or stripped.startswith(("#", "*")):
            continue

        if pending_type_match is not None:
            if stripped == "{":
                symbol = _symbol_from_type_match(pending_type_match, pending_type_line)
                symbols.append(symbol)
                type_brace_depth = _brace_delta(line)
                if type_brace_depth > 0:
                    current_type = symbol
                    current_access = "public" if symbol.kind == "struct" else "private"
                    current_section = None
                pending_type_match = None
                pending_type_line = 0
                continue
            pending_type_match = None
            pending_type_line = 0

        if current_type is not None:
            access_match = ACCESS_PATTERN.match(line)
            if access_match:
                pending_method_lines = []
                pending_method_start = 0
                current_access = access_match.group(1)
                type_brace_depth += _brace_delta(line)
                if type_brace_depth <= 0:
                    current_type = None
                    current_access = None
                continue

            if current_access == "public":
                if pending_method_lines and _looks_like_method_start(line):
                    pending_method_lines = []
                    pending_method_start = 0
                if not pending_method_lines:
                    pending_method_start = line_number
                pending_method_lines.append(line)
                if _declaration_is_complete(line):
                    declaration = " ".join(pending_method_lines)
                    method = _parse_method(
                        declaration,
                        pending_method_start,
                        line_number,
                        current_type,
                        current_section,
                    )
                    if method is not None:
                        symbols.append(method)
                    pending_method_lines = []
                    pending_method_start = 0

            type_brace_depth += _brace_delta(line)
            if type_brace_depth <= 0:
                current_type = None
                current_access = None
                pending_method_lines = []
                pending_method_start = 0
                current_section = None
            continue

        type_match = TYPE_PATTERN.match(line)
        if type_match and _is_definition_or_inherited_declaration(type_match):
            symbol = _symbol_from_type_match(type_match, line_number)
            symbols.append(symbol)
            type_brace_depth = _brace_delta(line)
            if type_match.group("body") == "{" and type_brace_depth > 0:
                current_type = symbol
                current_access = "public" if symbol.kind == "struct" else "private"
                current_section = None
            continue
        if type_match and _could_be_multiline_type_definition(type_match):
            pending_type_match = type_match
            pending_type_line = line_number
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
                    raw_declaration=_normalize_declaration(stripped),
                )
            )

    return symbols


def _is_definition_or_inherited_declaration(match: re.Match[str]) -> bool:
    return match.group("body") == "{"


def _could_be_multiline_type_definition(match: re.Match[str]) -> bool:
    return match.group("body") == "" and not match.string.rstrip().endswith(";")


def _symbol_from_type_match(match: re.Match[str], line_number: int) -> ParsedSymbol:
    kind = match.group(1)
    qualified_name = match.group(2)
    name = qualified_name.rsplit("::", 1)[-1]
    bases = _parse_bases(match.group("bases") or "")
    return ParsedSymbol(
        kind=kind,
        name=name,
        qualified_name=qualified_name,
        line_start=line_number,
        line_end=line_number,
        raw_declaration=_normalize_declaration(match.string.strip()),
        inherits=bases,
    )


def _parse_bases(raw_bases: str) -> tuple[str, ...]:
    bases: list[str] = []
    for base in raw_bases.split(","):
        match = BASE_PATTERN.fullmatch(base.strip())
        if match:
            bases.append(match.group(1))
    return tuple(bases)


def _brace_delta(line: str) -> int:
    return line.count("{") - line.count("}")


def _declaration_is_complete(line: str) -> bool:
    return ";" in line or "{" in line


def _looks_like_method_start(line: str) -> bool:
    return METHOD_START_PATTERN.match(line) is not None


def _parse_section_comment(stripped_line: str) -> str | None:
    text = stripped_line.removeprefix("//").strip()
    if not text:
        return None
    if text.startswith(("#", "NOTE:", "TODO", "FIXME")):
        return None
    if len(text) > 80:
        return None
    return text.rstrip(".")


def _parse_method(
    line: str,
    line_start: int,
    line_end: int,
    parent: ParsedSymbol,
    source_context: str | None,
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
        line_start=line_start,
        line_end=line_end,
        raw_declaration=_normalize_declaration(stripped),
        parent_qualified_name=parent.qualified_name,
        source_context=source_context,
    )


def _normalize_declaration(declaration: str) -> str:
    normalized = " ".join(declaration.strip().split())
    normalized = re.sub(r"\s+([,;()])", r"\1", normalized)
    normalized = re.sub(r"([({])\s+", r"\1", normalized)
    return normalized
