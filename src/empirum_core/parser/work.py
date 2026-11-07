"""Semantic helpers over lexed Setup.inf lines (WORK / command view)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from empirum_core.ast.model import (
    Document,
    KeyValueLine,
    LineNode,
    RawLine,
    Section,
    SourceSpan,
)
from empirum_core.setupinf_contract import SETUPINF_FUNCTIONS, SETUPINF_PREDICATES

# Empirum refs: #Set/#Shell/#Reg/#Ini/#Security:Name[, FLAGS], #Bare, Then/Else
_HASH_TYPED_RE = re.compile(
    r"(?<![#\w\\/\"'])#(?P<kind>Set|Shell|Reg|Ini|Security)\s*:\s*(?P<name>[^\s,\]]+)",
    re.IGNORECASE,
)
_HASH_BARE_RE = re.compile(
    r"(?<![#\w\\/\"'])#(?!(?:Set|Shell|Reg|Ini|Security)\s*:)(?P<name>[A-Za-z_][\w]*)",
    re.IGNORECASE,
)
_THEN_SET_RE = re.compile(
    r'\b(?:Then|Else)\s+(?P<q>"?)Set\s*:\s*(?P<name>[^"\s]+)(?P=q)',
    re.IGNORECASE,
)
_THEN_BARE_RE = re.compile(
    r'\b(?:Then|Else)\s+"(?P<name>[A-Za-z_][\w]*)"',
    re.IGNORECASE,
)
_IF_KV_RE = re.compile(r"^If$", re.IGNORECASE)
# Catalog-derived If/function names for the VAL-002 quoting check. Legacy
# alias names (non-existent in the 26.1.0 interpreter, flagged by VAL-026)
# stay listed so VAL-002 still reports the quoting error next to the rename.
_LEGACY_FUNC_NAMES = (
    "FileExists",
    "DirExists",
    "RegKeyExists",
    "RegValueExists",
    "DoesDirExist",
    "DoesRegValueExist",
    "ServiceExists",
    "ProcessExists",
    "FileVersion",
    "FileSize",
)
_FUNC_NAME_ALTERNATION = "|".join(
    re.escape(name)
    for name in dict.fromkeys((*SETUPINF_PREDICATES, *SETUPINF_FUNCTIONS, *_LEGACY_FUNC_NAMES))
)
_FUNC_PRED_RE = re.compile(
    r'^\s*"(?P<fn>' + _FUNC_NAME_ALTERNATION + r')\s*\(',
    re.IGNORECASE,
)
_HARDCODED_PF_RE = re.compile(
    r'(?i)([A-Z]:\\)?Program Files(?: \(x86\))?\\',
)


@dataclass(frozen=True, slots=True)
class SectionRef:
    kind: str  # Set | Shell
    name: str
    line: int
    source: str


@dataclass(frozen=True, slots=True)
class LocatedLine:
    section: Section | None
    node: LineNode
    line_no: int
    text: str


def iter_located(document: Document) -> list[LocatedLine]:
    out: list[LocatedLine] = []
    for node in document.preamble:
        out.append(
            LocatedLine(
                section=None,
                node=node,
                line_no=_line_no(node),
                text=_node_text(node),
            )
        )
    for section in document.sections:
        for node in section.lines:
            out.append(
                LocatedLine(
                    section=section,
                    node=node,
                    line_no=_line_no(node),
                    text=_node_text(node),
                )
            )
    return out


def find_section_refs_in_text(text: str, line: int = 0) -> list[SectionRef]:
    refs: list[SectionRef] = []
    for match in _HASH_TYPED_RE.finditer(text):
        refs.append(
            SectionRef(
                kind=match.group("kind"),
                name=match.group("name").rstrip(","),
                line=line,
                source=text,
            )
        )
    for match in _HASH_BARE_RE.finditer(text):
        refs.append(
            SectionRef(
                kind="",
                name=match.group("name"),
                line=line,
                source=text,
            )
        )
    for match in _THEN_SET_RE.finditer(text):
        refs.append(
            SectionRef(
                kind="Set",
                name=match.group("name").rstrip(","),
                line=line,
                source=text,
            )
        )
    for match in _THEN_BARE_RE.finditer(text):
        # Skip Then "Set:…" already covered by _THEN_SET_RE
        if match.group("name").casefold() == "set":
            continue
        refs.append(
            SectionRef(
                kind="",
                name=match.group("name"),
                line=line,
                source=text,
            )
        )
    return refs


def find_section_refs(document: Document) -> list[SectionRef]:
    """All section references in ACTIVE lines (commented-out code is ignored)."""
    refs: list[SectionRef] = []
    for loc in iter_located(document):
        if loc.text.lstrip().startswith(";"):
            continue
        refs.extend(find_section_refs_in_text(loc.text, loc.line_no))
    return refs


def recompute_spans(document: Document) -> None:
    """Re-assign 1-based line spans after structural edits (insert/remove lines).

    Mirrors the lexer's layout: preamble lines, then per section one header
    line followed by its body lines.
    """
    line = 0
    for node in document.preamble:
        line += 1
        node.span = SourceSpan(line, line)
    for section in document.sections:
        line += 1
        start = line
        for node in section.lines:
            line += 1
            node.span = SourceSpan(line, line)
        section.span = SourceSpan(start, line)


def section_names(document: Document) -> set[str]:
    return {s.name.casefold() for s in document.sections}


def resolve_section_ref(ref: SectionRef, known: set[str]) -> str | None:
    """Return matching section name (casefolded) for standard-style refs, or None.

    `#Set:Product` resolves to `[Set:Product]` or `[Product]`.
    `#Installation` resolves to `[Installation]`.
    """
    bare = ref.name.strip().rstrip(",").split(",", 1)[0].strip()
    if not bare:
        return None
    candidates: list[str] = [bare.casefold()]
    if ref.kind:
        candidates.insert(0, f"{ref.kind}:{bare}".casefold())
    else:
        candidates.extend(
            [
                f"Set:{bare}".casefold(),
                f"Shell:{bare}".casefold(),
                f"Reg:{bare}".casefold(),
                f"Ini:{bare}".casefold(),
                f"Security:{bare}".casefold(),
            ]
        )
    for cand in candidates:
        if cand in known:
            return cand
    return None


def section_ref_exists(ref: SectionRef, known: set[str]) -> bool:
    return resolve_section_ref(ref, known) is not None


def preferred_stub_section(ref: SectionRef) -> str:
    bare = ref.name.strip().rstrip(",").split(",", 1)[0].strip() or "Missing"
    if ref.kind:
        return f"{ref.kind}:{bare}"
    return bare


def is_uninstall_error_section(name: str) -> bool:
    n = name.casefold()
    if n.startswith("-") and "error" in n:
        return True
    return "uninstall" in n and "error" in n


def kv_pairs(document: Document) -> list[tuple[Section | None, KeyValueLine]]:
    pairs: list[tuple[Section | None, KeyValueLine]] = []
    for loc in iter_located(document):
        if isinstance(loc.node, KeyValueLine):
            pairs.append((loc.section, loc.node))
    return pairs


def if_predicate_is_quoted_function(value: str) -> bool:
    """True when If-value wraps a function predicate in quotes (VAL-002)."""
    return bool(_FUNC_PRED_RE.match(value))


def looks_like_if_key(key: str) -> bool:
    return bool(_IF_KV_RE.match(key))


def has_hardcoded_program_files(text: str) -> bool:
    if "%programfiles" in text.casefold():
        return False
    return bool(_HARDCODED_PF_RE.search(text))


def _node_text(node: LineNode) -> str:
    if isinstance(node, KeyValueLine):
        return node.raw if node.raw is not None else f"{node.key}={node.value}"
    if isinstance(node, RawLine):
        return node.text
    return node.raw if node.raw is not None else f";{node.text}"


def _line_no(node: LineNode) -> int:
    return node.span.start_line if node.span is not None else 0
