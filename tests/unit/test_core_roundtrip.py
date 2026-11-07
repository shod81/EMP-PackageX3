from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from empirum_core.ast.model import (
    CommentLine,
    Document,
    KeyValueLine,
    RawLine,
    Section,
    SourceSpan,
)
from empirum_core.parser.encoding import detect_encoding, encode_text
from empirum_core.parser.lexer import lex_document, lex_text
from empirum_core.quoting.quote import Quoter
from empirum_core.serializer.serialize import (
    serialize_document,
    serialize_to_bytes,
    touch_key_value,
)

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "testdata" / "golden"


def _golden_files() -> list[Path]:
    files = sorted(GOLDEN_DIR.glob("*.inf"))
    assert len(files) >= 10, f"expected >=10 golden files, found {len(files)}"
    return files


@pytest.mark.parametrize("path", _golden_files(), ids=lambda p: p.name)
def test_golden_roundtrip_byte_identical(path: Path) -> None:
    original = path.read_bytes()
    result = lex_document(original)
    again = serialize_to_bytes(result.document)
    assert again == original


@pytest.mark.parametrize("path", _golden_files(), ids=lambda p: p.name)
def test_golden_idempotent_second_pass(path: Path) -> None:
    original = path.read_bytes()
    first = serialize_to_bytes(lex_document(original).document)
    second = serialize_to_bytes(lex_document(first).document)
    assert first == second


def test_lexer_classifies_sections_and_comments() -> None:
    data = (
        b"; head\r\n"
        b"[SetupInfo]\r\n"
        b"ProductName=Demo\r\n"
        b"#Shell:X\r\n"
    )
    doc = lex_document(data).document
    assert len(doc.preamble) == 1
    assert isinstance(doc.preamble[0], CommentLine)
    assert doc.section("SetupInfo") is not None
    assert isinstance(doc.sections[0].lines[1], RawLine)


def test_lex_text_and_iter_lines() -> None:
    doc = lex_text("[A]\r\nK=V\r\n;c\r\n", encoding_name="cp1252")
    assert doc.section("a") is not None
    assert doc.section("missing") is None
    nodes = list(doc.iter_lines())
    assert len(nodes) == 2


def test_encoding_utf8_bom() -> None:
    raw = encode_text("ä\r\n", "utf-8", has_bom=True)
    detected = detect_encoding(raw)
    assert detected.name == "utf-8"
    assert detected.has_bom is True


def test_encoding_utf8_multibyte_without_bom() -> None:
    raw = "Café".encode()
    detected = detect_encoding(raw)
    assert detected.name == "utf-8"
    assert detected.ambiguous is True


def test_encoding_ascii_defaults_cp1252() -> None:
    detected = detect_encoding(b"Hello=World\r\n")
    assert detected.name == "cp1252"
    assert detected.ambiguous is False


def test_encoding_cp1252_umlauts() -> None:
    raw = "Büro".encode("cp1252")
    detected = detect_encoding(raw)
    assert detected.name == "cp1252"


def test_invalid_span_raises() -> None:
    with pytest.raises(ValueError):
        SourceSpan(0, 1)


def test_touch_key_value_writes_literal_value() -> None:
    kv = KeyValueLine(
        key="ProductName",
        value="A",
        preserve_raw=True,
        raw="ProductName=A",
    )
    doc = Document(sections=[Section(name="SetupInfo", lines=[kv])])
    touch_key_value(doc.sections[0], "ProductName", "A B")
    text = serialize_document(doc)
    assert "ProductName=A B" in text
    assert touch_key_value(doc.sections[0], "Missing", "x") is None


def test_quoter_helpers() -> None:
    # Dedicated field contexts keep INI-style quoting …
    assert Quoter.q_path(r"C:\Program Files\App") == '"C:\\Program Files\\App"'
    assert Quoter.q_reg_field("Installed") == "Installed"
    assert Quoter.q_value('"already"') == '"already"'
    # … but Key=Value values are literal (literal-value rule): never quoted,
    # never unescaped – the interpreter has no quote-stripping layer.
    assert Quoter.q_value("b c") == "b c"
    assert Quoter.q_value('%HKLM,"K","V"%\\x') == '%HKLM,"K","V"%\\x'
    assert Quoter.q_key_value("A", "b c") == "A=b c"
    assert Quoter.unquote('"a""b"') == '"a""b"'
    # Tolerant comparison helper (read-only checks, canonical quoted form).
    assert Quoter.strip_optional_quotes('"1"') == "1"
    assert Quoter.strip_optional_quotes('"a""b"') == 'a""b'
    assert Quoter.strip_optional_quotes("plain") == "plain"


def test_serialize_comment_without_raw() -> None:
    doc = Document(
        sections=[
            Section(
                name="S",
                lines=[CommentLine(text=" note", raw=None)],
            )
        ]
    )
    text = serialize_document(doc)
    assert "; note" in text


def test_structural_hash_includes_comments_and_raw() -> None:
    doc = Document(
        preamble=[CommentLine(text="p")],
        sections=[
            Section(
                name="S",
                lines=[RawLine(text="!!!"), KeyValueLine(key="K", value="V")],
            )
        ],
    )
    assert len(doc.structural_hash()) == 64


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=40))
@settings(max_examples=50)
def test_quoter_kv_identity(value: str) -> None:
    # Setup.inf Key=Value values round-trip through the Quoter unchanged.
    assert Quoter.q_value(value) == value
    assert Quoter.unquote(value) == value
    assert Quoter.q_key_value("K", value) == f"K={value}"


_safe_text = st.text(min_size=1, max_size=12).filter(
    lambda s: "=" not in s and "[" not in s
)


@given(st.lists(_safe_text, max_size=5))
@settings(max_examples=40)
def test_structural_hash_stable(keys: list[str]) -> None:
    lines = [
        KeyValueLine(key=f"K{i}", value=k, preserve_raw=False) for i, k in enumerate(keys)
    ]
    doc_a = Document(sections=[Section(name="S", lines=list(lines))])
    doc_b = Document(sections=[Section(name="S", lines=list(lines))])
    assert doc_a.structural_hash() == doc_b.structural_hash()


def test_roundtrip_preserves_unicode_line_break_chars() -> None:
    """S1: \\v/\\f/\\x1c-\\x1e/\\x85/\\u2028/\\u2029 are content, not line breaks."""
    # cp1252-representable control characters
    data = "[Product]\r\nCall=a\x0cb=c\r\nKey=\x1dz\r\n".encode("cp1252")
    doc = lex_document(data).document
    assert serialize_to_bytes(doc) == data
    # NEL / LINE SEPARATOR only roundtrip in UTF-8 documents (multibyte content)
    utf8 = "[Product]\r\nEcho=x\x85y\r\nKey=\u2028z\r\n".encode("utf-8")
    doc_utf8 = lex_document(utf8).document
    assert doc_utf8.encoding_name == "utf-8"
    assert serialize_to_bytes(doc_utf8) == utf8


def test_roundtrip_cr_only_normalizes_to_crlf() -> None:
    # CR-only separators are normalized to the document newline (CRLF default).
    data = b"[A]\rK=1\rJ=2"
    out = serialize_to_bytes(lex_document(data).document)
    assert out == b"[A]\r\nK=1\r\nJ=2\r\n"


def test_roundtrip_empty_file() -> None:
    assert serialize_to_bytes(lex_document(b"").document) == b""


def test_lex_text_lexer_error_type() -> None:
    from empirum_core.parser.lexer import LexerError

    with pytest.raises(LexerError):
        lex_text("K=\u2603\r\n", encoding_name="cp1252")


def test_serialize_to_bytes_raises_lexer_error_for_unencodable() -> None:
    from empirum_core.parser.lexer import LexerError

    doc = lex_text("[A]\r\nK=1\r\n", encoding_name="cp1252")
    doc.sections[0].lines[0].value = "\u2603"  # type: ignore[index]
    doc.sections[0].lines[0].preserve_raw = False  # type: ignore[index]
    with pytest.raises(LexerError):
        serialize_to_bytes(doc)


def test_encode_text_bom_only_for_utf8() -> None:
    with pytest.raises(ValueError, match="BOM"):
        encode_text("x\r\n", "cp1252", has_bom=True)


def test_prettify_recomputes_spans() -> None:
    from empirum_core.prettify import prettify_document

    doc = lex_text("[SetupInfo]\r\nA=1\r\n[B]\r\nDelTree=%Dst%\\x\r\n[C]\r\nD=2\r\n")
    pretty = prettify_document(doc)
    deltree = pretty.section("B")
    assert deltree is not None
    node = deltree.lines[0]
    assert node.span is not None
    serialized = serialize_document(pretty)
    expected_line = serialized.split("\r\n").index("DelTree=%Dst%\\x") + 1
    assert node.span.start_line == expected_line
