"""EMP-PackageX3 – Empirum package tooling domain core.

Copyright (c) 2026 Stefan Hodrius / Hodrius Systems. MIT License.
"""

from empirum_core.ast.model import (
    CommentLine,
    Document,
    KeyValueLine,
    RawLine,
    Section,
    SourceSpan,
)
from empirum_core.linter import Diagnostic, Severity, lint_document
from empirum_core.parser.encoding import DetectedEncoding, decode_bytes, detect_encoding
from empirum_core.parser.lexer import LexerError, lex_document
from empirum_core.quoting.quote import Quoter
from empirum_core.serializer.serialize import serialize_document

__all__ = [
    "CommentLine",
    "DetectedEncoding",
    "Diagnostic",
    "Document",
    "KeyValueLine",
    "LexerError",
    "Quoter",
    "RawLine",
    "Section",
    "Severity",
    "SourceSpan",
    "decode_bytes",
    "detect_encoding",
    "lex_document",
    "lint_document",
    "serialize_document",
]

__version__ = "0.1.0"
