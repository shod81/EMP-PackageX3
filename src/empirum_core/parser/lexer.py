"""Stage-1 section lexer for Empirum Setup.inf.

Tolerant: never aborts on unknown lines; preserves them as RawLine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from empirum_core.ast.model import (
    CommentLine,
    Document,
    KeyValueLine,
    LineNode,
    RawLine,
    Section,
    SourceSpan,
)
from empirum_core.parser.encoding import DetectedEncoding, decode_bytes

_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
# Key = value; key may contain spaces rarely – Empirum typically uses Token=Value
_KV_RE = re.compile(r"^([^=;\r\n]+?)=(.*)$")
# Split on CR/LF only. str.splitlines() would also break on \v, \f, \x1c-\x1e,
# \x85, \u2028 and \u2029 – those are content characters for roundtrip fidelity.
_LINE_BREAK_RE = re.compile(r"\r\n|\n|\r")


class LexerError(ValueError):
    """Hard failures: undecodable bytes or unencodable text (see encoding)."""


def _split_lines(text: str) -> list[str]:
    """Split like str.splitlines(), but ONLY on CRLF/LF/CR line breaks."""
    if not text:
        return []
    parts = _LINE_BREAK_RE.split(text)
    if len(parts) > 1 and parts[-1] == "":
        parts.pop()  # trailing newline, not an extra empty line
    return parts


@dataclass(frozen=True, slots=True)
class LexResult:
    document: Document
    encoding: DetectedEncoding


def lex_document(data: bytes, *, encoding: DetectedEncoding | None = None) -> LexResult:
    text, detected = decode_bytes(data, encoding)
    newline = "\r\n" if "\r\n" in text else ("\n" if "\n" in text else "\r\n")
    # Roundtrip contract: mixed line endings are normalized to document.newline
    # on serialize; an explicit empty trailing line survives as RawLine("").
    lines = _split_lines(text)
    doc = Document(
        encoding_name=detected.name,
        newline=newline,
        has_bom=detected.has_bom,
    )

    current: Section | None = None
    for idx, line in enumerate(lines, start=1):
        span = SourceSpan(idx, idx)
        section_match = _SECTION_RE.match(line)
        if section_match:
            name = section_match.group(1)
            current = Section(name=name, header_raw=name, span=span)
            doc.sections.append(current)
            continue

        node = _classify_line(line, span)
        if current is None:
            doc.preamble.append(node)
        else:
            current.lines.append(node)

    # Fix section spans to cover their body
    for section in doc.sections:
        if section.lines:
            assert section.span is not None
            last = section.lines[-1].span
            if last is not None:
                section.span = SourceSpan(section.span.start_line, last.end_line)

    return LexResult(document=doc, encoding=detected)


def lex_text(text: str, *, encoding_name: str = "cp1252", newline: str = "\r\n") -> Document:
    """Lex an already-decoded string (tests / in-memory edits).

    Line endings are normalized to `newline` on serialize; mixed CR/LF input
    is therefore unified. Raises LexerError if the text contains characters
    that cannot be represented in `encoding_name`.
    """
    text = text.lstrip("\ufeff\xef\xbb\xbf")
    try:
        data = text.encode(encoding_name)
    except UnicodeEncodeError as exc:
        raise LexerError(
            f"Text enthält Zeichen, die mit {encoding_name} nicht darstellbar sind: {exc}"
        ) from exc
    result = lex_document(data)
    result.document.newline = newline
    result.document.encoding_name = encoding_name
    return result.document


def _classify_line(line: str, span: SourceSpan) -> LineNode:
    stripped = line.lstrip()
    if stripped.startswith(";"):
        # Keep indentation in raw; comment text after first ';'
        first = line.index(";")
        return CommentLine(text=line[first + 1 :], span=span, raw=line)

    kv = _KV_RE.match(line)
    if kv and not line.lstrip().startswith("="):
        key = kv.group(1).rstrip()
        # Only treat as KV when key looks like an identifier / Empirum token
        if key and not key.startswith(" ") and _looks_like_key(key):
            return KeyValueLine(
                key=key,
                value=kv.group(2),
                span=span,
                raw=line,
                preserve_raw=True,
            )

    return RawLine(text=line, span=span)


def _looks_like_key(key: str) -> bool:
    """Reject pure paths or quoted strings as keys.

    Empirum-Paket-Standard allows spaces in keys (e.g. ``Command line options``).
    """
    if key.startswith('"') or key.startswith("'"):
        return False
    if len(key) > 120:
        return False
    stripped = key.strip()
    if not stripped or "\\" in stripped or "/" in stripped:
        return False
    # Alphanumeric / . _ - and spaces (standard SetupInfo keys)
    return bool(re.match(r"^[\w.\-]+(?:\s+[\w.\-]+)*$", stripped, flags=re.UNICODE))
