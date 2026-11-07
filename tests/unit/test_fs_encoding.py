from __future__ import annotations

from pathlib import Path

from empirum_infra.fs_safe import write_bytes_with_backup
from empirum_services.editor.sync import SyncController


def test_write_bytes_with_backup_creates_bak(tmp_path: Path) -> None:
    target = tmp_path / "Setup.inf"
    target.write_bytes(b"old\r\n")
    result = write_bytes_with_backup(target, b"new\r\n")
    assert target.read_bytes() == b"new\r\n"
    assert result.backup_path is not None
    assert result.backup_path.read_bytes() == b"old\r\n"


def test_write_bytes_first_time_no_backup(tmp_path: Path) -> None:
    target = tmp_path / "Setup.inf"
    result = write_bytes_with_backup(target, b"fresh\r\n")
    assert result.backup_path is None
    assert target.read_bytes() == b"fresh\r\n"


def test_sync_marks_ambiguous_utf8_readonly() -> None:
    sync = SyncController()
    # Valid UTF-8 multi-byte without BOM → ambiguous per detector
    data = "ProductName=Café\r\n".encode()
    # Wrap as minimal inf
    payload = b"[SetupInfo]\r\n" + data
    sync.load_bytes(payload)
    if sync.encoding_ambiguous:
        assert sync.read_only is True
        sync.set_encoding("utf-8")
        assert sync.read_only is False
        assert sync.document.encoding_name == "utf-8"


def test_backup_collision_within_same_second(tmp_path: Path) -> None:
    target = tmp_path / "f.inf"
    target.write_bytes(b"v1\r\n")
    first = write_bytes_with_backup(target, b"v2\r\n")
    second = write_bytes_with_backup(target, b"v3\r\n")
    assert first.backup_path is not None
    assert second.backup_path is not None
    assert first.backup_path != second.backup_path
    assert second.backup_path.is_file()
    assert target.read_bytes() == b"v3\r\n"


def test_bom_stripping_on_decode_and_lex() -> None:
    from empirum_core.parser.encoding import decode_bytes
    from empirum_core.parser.lexer import lex_text

    # 1. UTF-8 BOM decoded properly
    raw_utf8 = b"\xef\xbb\xbf[SetupInfo]\r\nProductName=Test\r\n"
    text, detected = decode_bytes(raw_utf8)
    assert not text.startswith(("\ufeff", "\xef\xbb\xbf"))
    assert text.startswith("[SetupInfo]")

    # 2. lex_text with leading Unicode BOM or mis-decoded Latin1 BOM residue
    doc1 = lex_text("\ufeff[SetupInfo]\r\nProductName=Test\r\n")
    assert doc1.sections[0].name == "SetupInfo"
    assert len(doc1.preamble) == 0

    doc2 = lex_text("\xef\xbb\xbf[SetupInfo]\r\nProductName=Test\r\n")
    assert doc2.sections[0].name == "SetupInfo"
    assert len(doc2.preamble) == 0
