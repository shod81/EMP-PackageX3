from __future__ import annotations

from pathlib import Path

import pytest

from empirum_core.inspect import RegistryEntrySpec
from empirum_core.parser.reg_parser import (
    REG_TYPE_HEX,
    decode_hex_utf16,
    format_reg_entry_empirum,
    normalize_root,
    parse_reg_content,
    parse_reg_file,
    reg_has_hkcu,
    unescape_reg_string,
)


def test_normalize_root() -> None:
    assert normalize_root("HKEY_LOCAL_MACHINE") == "HKLM"
    assert normalize_root("HKEY_CURRENT_USER") == "HKCU"
    assert normalize_root("HKEY_CLASSES_ROOT") == "HKCR"
    assert normalize_root("HKEY_USERS") == "HKU"
    assert normalize_root("HKEY_CURRENT_CONFIG") == "HKCC"
    assert normalize_root("HKLM") == "HKLM"
    assert normalize_root("hkcu") == "HKCU"
    assert normalize_root("CUSTOM_ROOT") == "CUSTOM_ROOT"


def test_unescape_reg_string() -> None:
    assert unescape_reg_string(r'C:\\Program Files\\App') == r"C:\Program Files\App"
    assert unescape_reg_string(r'Line1\nLine2') == "Line1\nLine2"
    assert unescape_reg_string(r'Quote\"Inside') == 'Quote"Inside'
    assert unescape_reg_string(r"Simple") == "Simple"


def test_decode_hex_utf16() -> None:
    # "Test" in utf-16 le hex: 54,00,65,00,73,00,74,00,00,00
    hex_str = "54,00,65,00,73,00,74,00,00,00"
    assert decode_hex_utf16(hex_str) == "Test"

    # Odd hex or invalid fallback
    assert decode_hex_utf16("54,00,zz") == "54,00,zz"


def test_format_reg_entry_empirum() -> None:
    # REG_SZ with value_name
    spec1 = RegistryEntrySpec(
        root="HKLM",
        key_path=r"Software\Acme\Tool",
        value_name="Path",
        reg_type="REG_SZ",
        value_data=r"C:\Acme\Tool",
        delete_on_uninstall=False,
    )
    assert (
        format_reg_entry_empirum(spec1)
        == r'HKLM,"Software\Acme\Tool","Path",0x00000000,"C:\Acme\Tool"'
    )

    # Default / unnamed value
    spec_def = RegistryEntrySpec(
        root="HKLM",
        key_path=r"Software\Acme\Tool",
        value_name="",
        reg_type="REG_SZ",
        value_data="DefaultVal",
    )
    exp_def = 'HKLM,"Software\\Acme\\Tool",,0x00000000,"DefaultVal"'
    assert format_reg_entry_empirum(spec_def) == exp_def

    # REG_DWORD integer
    spec_dw = RegistryEntrySpec(
        root="HKCU",
        key_path=r"Software\Acme",
        value_name="Enabled",
        reg_type="REG_DWORD",
        value_data="1",
        delete_on_uninstall=True,
    )
    assert format_reg_entry_empirum(spec_dw) == '-HKCU,"Software\\Acme","Enabled",0x00010001,1'

    # REG_DWORD hex format
    spec_dw_hex = RegistryEntrySpec(
        root="HKCU",
        key_path=r"Software\Acme",
        value_name="Count",
        reg_type="REG_DWORD",
        value_data="0x00000010",
    )
    assert format_reg_entry_empirum(spec_dw_hex) == 'HKCU,"Software\\Acme","Count",0x00010001,16'

    # REG_EXPAND_SZ
    spec_exp = RegistryEntrySpec(
        root="HKLM",
        key_path=r"Software\Acme",
        value_name="Exp",
        reg_type="REG_EXPAND_SZ",
        value_data="%ProgramFiles%",
    )
    exp_exp = 'HKLM,"Software\\Acme","Exp",0x00020000,"%ProgramFiles%"'
    assert format_reg_entry_empirum(spec_exp) == exp_exp

    # REG_MULTI_SZ
    spec_multi = RegistryEntrySpec(
        root="HKLM",
        key_path=r"Software\Acme",
        value_name="Multi",
        reg_type="REG_MULTI_SZ",
        value_data="A\0B",
    )
    exp_multi = 'HKLM,"Software\\Acme","Multi",0x00010000,"A\\0B"'
    assert format_reg_entry_empirum(spec_multi) == exp_multi

    # REG_BINARY
    spec_bin = RegistryEntrySpec(
        root="HKLM",
        key_path=r"Software\Acme",
        value_name="Bin",
        reg_type="REG_BINARY",
        value_data="01,02,03",
    )
    assert format_reg_entry_empirum(spec_bin) == 'HKLM,"Software\\Acme","Bin",0x00000001,"01,02,03"'


def test_parse_reg_content_valid() -> None:
    sample = """Windows Registry Editor Version 5.00

; A comment line
[HKEY_LOCAL_MACHINE\\Software\\Vendor\\App]
"InstallDir"="C:\\\\Program Files\\\\App"
"Installed"=dword:00000001
@="DefaultAppName"
"Expandable"=hex(2):25,00,50,00,41,00,54,00,48,00,25,00,00,00
"MultiStr"=hex(7):61,00,00,00,62,00,00,00,00,00
"Binary"=hex:de,ad,be,ef

[HKEY_CURRENT_USER\\Software\\Vendor\\App\\Settings]
"Theme"="Dark"
"""
    entries = parse_reg_content(sample)
    assert len(entries) == 7

    # HKLM InstallDir
    e0 = entries[0]
    assert e0.root == "HKLM"
    assert e0.key_path == r"Software\Vendor\App"
    assert e0.value_name == "InstallDir"
    assert e0.reg_type == "REG_SZ"
    assert e0.value_data == r"C:\Program Files\App"

    # dword
    e1 = entries[1]
    assert e1.value_name == "Installed"
    assert e1.reg_type == "REG_DWORD"
    assert e1.value_data == "1"

    # default @
    e2 = entries[2]
    assert e2.value_name == ""
    assert e2.value_data == "DefaultAppName"

    # hex(2) -> REG_EXPAND_SZ
    e3 = entries[3]
    assert e3.value_name == "Expandable"
    assert e3.reg_type == "REG_EXPAND_SZ"
    assert e3.value_data == "%PATH%"

    # hex(7) -> REG_MULTI_SZ
    e4 = entries[4]
    assert e4.value_name == "MultiStr"
    assert e4.reg_type == "REG_MULTI_SZ"

    # hex -> REG_BINARY
    e5 = entries[5]
    assert e5.value_name == "Binary"
    assert e5.reg_type == "REG_BINARY"
    assert "de,ad,be,ef" in e5.value_data

    # HKCU Theme
    e6 = entries[6]
    assert e6.root == "HKCU"
    assert e6.value_name == "Theme"
    assert e6.value_data == "Dark"


def test_parse_reg_content_multiline_and_raw_hex() -> None:
    sample = """Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\Software\\Test]
"LongHex"=hex:01,02,03,\\
  04,05,06,\\
  07,08
"UnknownHex"=hex(99):aa,bb
"""
    entries = parse_reg_content(sample)
    assert len(entries) == 2
    assert entries[0].reg_type == "REG_BINARY"
    assert "01,02,03,04,05,06,07,08" in entries[0].value_data
    assert entries[1].reg_type == "REG_BINARY"


def test_parse_reg_content_header_validation() -> None:
    with pytest.raises(ValueError, match="Keine gültige Windows .reg Datei"):
        parse_reg_content("Invalid file without header\n[HKLM\\Key]")


def test_parse_reg_file_utf16le_and_utf8(tmp_path: Path) -> None:
    reg_text = """Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Test]
"UserPref"="Active"
"""
    # UTF-16 LE with BOM
    f_utf16 = tmp_path / "utf16.reg"
    f_utf16.write_bytes(reg_text.encode("utf-16"))
    assert reg_has_hkcu(f_utf16) is True
    entries_16 = parse_reg_file(f_utf16)
    assert len(entries_16) == 1
    assert entries_16[0].root == "HKCU"
    assert entries_16[0].value_data == "Active"

    # UTF-8 with BOM
    f_utf8 = tmp_path / "utf8.reg"
    f_utf8.write_bytes(b"\xef\xbb\xbf" + reg_text.encode("utf-8"))
    assert reg_has_hkcu(f_utf8) is True
    entries_8 = parse_reg_file(f_utf8)
    assert len(entries_8) == 1

    # Non-existent file
    with pytest.raises(ValueError, match="nicht gefunden"):
        parse_reg_file(tmp_path / "does_not_exist.reg")


def test_reg_has_hkcu_false(tmp_path: Path) -> None:
    f_hklm = tmp_path / "machine_only.reg"
    f_hklm.write_text(
        "Windows Registry Editor Version 5.00\n\n"
        "[HKEY_LOCAL_MACHINE\\Software\\Test]\n\"A\"=\"B\"\n",
        encoding="utf-8",
    )
    assert reg_has_hkcu(f_hklm) is False
    assert reg_has_hkcu(tmp_path / "not_there.reg") is False


def test_format_and_parse_qword() -> None:
    # 1. Format
    spec = RegistryEntrySpec(
        root="HKLM",
        key_path=r"System\CurrentControlSet\Services\bfs",
        value_name="Start",
        reg_type="REG_QWORD",
        value_data="4",
        delete_on_uninstall=False,
    )
    formatted = format_reg_entry_empirum(spec)
    # K-03: official 26.1.0 type constant (former PackagerX value 0x00010004 was wrong)
    assert formatted == r'HKLM,"System\CurrentControlSet\Services\bfs","Start",0x00040001,4'

    # 2. Parse qword: and hex(b):
    reg_text = (
        "Windows Registry Editor Version 5.00\r\n\r\n"
        "[HKEY_LOCAL_MACHINE\\Software\\Test]\r\n"
        '"Val1"=qword:0000000000000004\r\n'
        '"Val2"=hex(b):02,00,00,00,00,00,00,00\r\n'
    )
    entries = parse_reg_content(reg_text)
    assert len(entries) == 2
    assert entries[0].reg_type == "REG_QWORD"
    assert entries[0].value_data == "4"
    assert entries[1].reg_type == "REG_QWORD"
    assert entries[1].value_data == "2"


def test_reg_type_hex_matches_official_contract() -> None:
    # Single source of truth: setupinf_contract.SETUPINF_REG_TYPES (K-03)
    from empirum_core.setupinf_contract import SETUPINF_REG_TYPES

    for name, code in SETUPINF_REG_TYPES.items():
        assert REG_TYPE_HEX[name] == code
    assert SETUPINF_REG_TYPES["REG_BINARY"] == "0x00000001"
    assert SETUPINF_REG_TYPES["REG_MULTI_SZ"] == "0x00010000"
    assert SETUPINF_REG_TYPES["REG_QWORD"] == "0x00040001"
    assert SETUPINF_REG_TYPES["REG_NONE"] == "0x00020001"
    assert SETUPINF_REG_TYPES["REG_BINARY_SZ"] == "0x10000001"


def test_format_reg_none_and_binary_sz() -> None:
    none_spec = RegistryEntrySpec(
        root="HKLM",
        key_path=r"Software\Test",
        value_name="Empty",
        reg_type="REG_NONE",
        value_data="",
        delete_on_uninstall=False,
    )
    assert (
        format_reg_entry_empirum(none_spec)
        == 'HKLM,"Software\\Test","Empty",0x00020001,""'
    )

    bsz_spec = RegistryEntrySpec(
        root="HKCU",
        key_path=r"Software\Test",
        value_name="Blob",
        reg_type="REG_BINARY_SZ",
        value_data="01,02,03",
        delete_on_uninstall=False,
    )
    assert (
        format_reg_entry_empirum(bsz_spec)
        == 'HKCU,"Software\\Test","Blob",0x10000001,"01,02,03"'
    )
