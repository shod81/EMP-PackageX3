"""Serialize AST documents with round-trip guarantees for untouched lines."""

from __future__ import annotations

from empirum_core.ast.model import (
    CommentLine,
    Document,
    KeyValueLine,
    LineNode,
    RawLine,
    Section,
)
from empirum_core.parser.encoding import encode_text
from empirum_core.parser.lexer import LexerError
from empirum_core.quoting.quote import Quoter


def serialize_document(document: Document) -> str:
    """Serialize to text using document.newline. Untouched KV/comment keep raw."""
    parts: list[str] = []
    for node in document.preamble:
        parts.append(_serialize_line(node))
    for index, section in enumerate(document.sections):
        if parts and parts[-1] != "":
            # Section headers follow previous content; blank lines are explicit RawLines
            pass
        parts.append(f"[{section.header}]")
        for node in section.lines:
            parts.append(_serialize_line(node))
        # No automatic blank line between sections — only what's in the AST
        _ = index
    # Empirum files typically end with a newline
    body = document.newline.join(parts)
    if body and not body.endswith(("\r\n", "\n")):
        body += document.newline
    elif not body:
        body = ""
    else:
        # join doesn't add trailing newline after last element
        body += document.newline
    return body


def serialize_to_bytes(document: Document) -> bytes:
    text = serialize_document(document)
    try:
        return encode_text(text, document.encoding_name, has_bom=document.has_bom)
    except UnicodeEncodeError as exc:
        raise LexerError(
            f"Dokument enthält Zeichen, die mit {document.encoding_name} "
            f"nicht darstellbar sind: {exc}"
        ) from exc


def _serialize_line(node: LineNode) -> str:
    if isinstance(node, CommentLine):
        if node.raw is not None:
            return node.raw
        return f";{node.text}"
    if isinstance(node, KeyValueLine):
        if node.preserve_raw and node.raw is not None:
            return node.raw
        return Quoter.q_key_value(node.key, node.value)
    if isinstance(node, RawLine):
        return node.text
    # Defensive only: LineNode is a closed union, so this is unreachable unless a
    # new node type is added. Marked no-cover so the blanket coverage exclusion
    # for "raise TypeError" could be dropped (L-5).
    raise TypeError(f"unknown line node: {type(node)!r}")  # pragma: no cover


def touch_key_value(section: Section, key: str, value: str) -> KeyValueLine | None:
    """Update first matching key and clear preserve_raw so quoting is reapplied."""
    wanted = key.casefold()
    for node in section.lines:
        if isinstance(node, KeyValueLine) and node.key.casefold() == wanted:
            node.value = value
            node.preserve_raw = False
            node.raw = None
            return node
    return None
