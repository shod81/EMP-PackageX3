"""Parser package exports."""

from empirum_core.parser.encoding import (
    DetectedEncoding,
    decode_bytes,
    detect_encoding,
    encode_text,
)
from empirum_core.parser.lexer import LexerError, LexResult, lex_document, lex_text
from empirum_core.parser.reg_parser import (
    format_reg_entry_empirum,
    parse_reg_file,
    reg_has_hkcu,
)

__all__ = [
    "DetectedEncoding",
    "LexResult",
    "LexerError",
    "decode_bytes",
    "detect_encoding",
    "encode_text",
    "format_reg_entry_empirum",
    "lex_document",
    "lex_text",
    "parse_reg_file",
    "reg_has_hkcu",
]

