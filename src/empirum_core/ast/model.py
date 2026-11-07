"""Typed AST for Empirum Setup.inf documents.

The AST is the single source of truth. Unknown content is preserved as RawLine
nodes so round-trips stay byte-identical for untouched lines.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """1-based line span in the original file (inclusive)."""

    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError(f"invalid span: {self.start_line}-{self.end_line}")


@dataclass(slots=True)
class CommentLine:
    text: str  # without leading ';', may be empty
    span: SourceSpan | None = None
    raw: str | None = None  # original line including CRLF semantics marker


@dataclass(slots=True)
class KeyValueLine:
    key: str
    value: str
    span: SourceSpan | None = None
    raw: str | None = None
    # When True, serializer emits the exact raw line (untouched).
    preserve_raw: bool = True


@dataclass(slots=True)
class RawLine:
    """Unknown or non-key-value content preserved verbatim (without trailing newline)."""

    text: str
    span: SourceSpan | None = None


LineNode = CommentLine | KeyValueLine | RawLine


@dataclass(slots=True)
class Section:
    name: str
    lines: list[LineNode] = field(default_factory=list)
    span: SourceSpan | None = None
    # Exact header text without brackets, as seen (case preserved).
    header_raw: str | None = None

    @property
    def header(self) -> str:
        return self.header_raw if self.header_raw is not None else self.name


@dataclass(slots=True)
class Document:
    """Complete Setup.inf document."""

    sections: list[Section] = field(default_factory=list)
    # Lines before the first section header (rare, but field files exist).
    preamble: list[LineNode] = field(default_factory=list)
    encoding_name: str = "cp1252"
    newline: str = "\r\n"
    has_bom: bool = False

    def iter_lines(self) -> Iterator[LineNode]:
        yield from self.preamble
        for section in self.sections:
            yield from section.lines

    def section(self, name: str) -> Section | None:
        wanted = name.casefold()
        for section in self.sections:
            if section.name.casefold() == wanted:
                return section
        return None

    def structural_hash(self) -> str:
        """Stable hash over normalized structure (ignores raw/span)."""
        parts: list[str] = []
        for node in self.preamble:
            parts.append(_node_fingerprint(node))
        for section in self.sections:
            parts.append(f"[section:{section.name.casefold()}]")
            for node in section.lines:
                parts.append(_node_fingerprint(node))
        digest = sha256("\n".join(parts).encode("utf-8")).hexdigest()
        return digest


def needs_section_gap(previous: Section) -> bool:
    """True when a blank line must precede the next section header.

    The same rule the prettifier applies (``empirum_core.prettify``), kept here
    so newly appended sections are separated exactly like prettified ones: a
    repaired or quick-fixed document must not need a second Prettify pass.
    """
    if not previous.lines:
        return False
    last = previous.lines[-1]
    return not (isinstance(last, RawLine) and last.text == "")


def append_section(document: Document, section: Section) -> Section:
    """Append ``section`` at the document end, keeping the one-blank-line gap.

    Returns the appended section so callers can keep using it by name.
    """
    if document.sections and needs_section_gap(document.sections[-1]):
        document.sections[-1].lines.append(RawLine(text=""))
    document.sections.append(section)
    return section


def _node_fingerprint(node: LineNode) -> str:
    if isinstance(node, CommentLine):
        return f"comment:{node.text}"
    if isinstance(node, KeyValueLine):
        return f"kv:{node.key}={node.value}"
    return f"raw:{node.text}"
