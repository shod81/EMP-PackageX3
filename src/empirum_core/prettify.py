"""Lightweight Setup.inf prettifier (spacing / blank lines between sections)."""

from __future__ import annotations

from empirum_core.ast.model import (
    CommentLine,
    Document,
    KeyValueLine,
    LineNode,
    RawLine,
    Section,
    needs_section_gap,
)
from empirum_core.parser.work import recompute_spans
from empirum_core.serializer.serialize import serialize_document


def prettify_document(document: Document, *, blank_between_sections: bool = True) -> Document:
    """Return a new document with trimmed KV spacing and optional section gaps.

    Untouched raw preservation is cleared only for KeyValue lines we normalize.
    """
    new = Document(
        encoding_name=document.encoding_name,
        newline=document.newline,
        has_bom=document.has_bom,
        preamble=_normalize_lines(document.preamble),
        sections=[],
    )
    for index, section in enumerate(document.sections):
        new_section = Section(
            name=section.name,
            header_raw=section.header_raw,
            lines=_normalize_lines(section.lines),
        )
        if (
            blank_between_sections
            and index > 0
            and needs_section_gap(new.sections[-1])
        ):
            new.sections[-1].lines.append(RawLine(text=""))
        new.sections.append(new_section)
    # Inserted blank lines shift everything after them – keep spans truthful.
    recompute_spans(new)
    return new


def prettify_text(text: str) -> str:
    from empirum_core.parser.lexer import lex_text

    normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
    doc = lex_text(normalized)
    pretty = prettify_document(doc)
    return serialize_document(pretty)


def _normalize_lines(lines: list[LineNode]) -> list[LineNode]:
    out: list[LineNode] = []
    for node in lines:
        if isinstance(node, KeyValueLine):
            value = node.value.strip() if not node.value.startswith(" ") else node.value
            out.append(
                KeyValueLine(
                    key=node.key.strip(),
                    value=value,
                    preserve_raw=False,
                    raw=None,
                    span=node.span,
                )
            )
        elif isinstance(node, CommentLine):
            out.append(CommentLine(text=node.text.rstrip(), raw=None, span=node.span))
        elif isinstance(node, RawLine):
            out.append(RawLine(text=node.text.rstrip(), span=node.span))
        else:
            out.append(node)
    collapsed: list[LineNode] = []
    blank = False
    for node in out:
        is_blank = isinstance(node, RawLine) and node.text == ""
        if is_blank and blank:
            continue
        blank = is_blank
        collapsed.append(node)
    return collapsed
