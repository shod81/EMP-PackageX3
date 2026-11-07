"""Windows .reg file parser for converting .reg entries to Empirum [Reg:Product] lines."""

from __future__ import annotations

import re
from pathlib import Path

from empirum_core.inspect import RegistryEntrySpec
from empirum_core.setupinf_contract import SETUPINF_REG_TYPES

# K-03: single source of truth is setupinf_contract.SETUPINF_REG_TYPES (official
# Legacy-Help/26.1.0 type table). Kept as a plain dict for callers that
# mutate/iterate; the former hardcoded copy drifted (REG_QWORD 0x00010004).
REG_TYPE_HEX: dict[str, str] = dict(SETUPINF_REG_TYPES)

_ROOT_MAP: dict[str, str] = {
    "hkey_local_machine": "HKLM",
    "hklm": "HKLM",
    "hkey_current_user": "HKCU",
    "hkcu": "HKCU",
    "hkey_classes_root": "HKCR",
    "hkcr": "HKCR",
    "hkey_users": "HKU",
    "hku": "HKU",
    "hkey_current_config": "HKCC",
    "hkcc": "HKCC",
}


def normalize_root(root: str) -> str:
    """Normalize a registry root string (e.g. HKEY_LOCAL_MACHINE -> HKLM)."""
    return _ROOT_MAP.get(root.strip().casefold(), root.strip().upper())


def unescape_reg_string(val: str) -> str:
    """Unescape backslashes, quotes, and newlines in registry string literals."""
    return val.replace(r"\\", "\\").replace(r'\"', '"').replace(r"\n", "\n")


def decode_hex_utf16(raw_hex: str) -> str:
    """Decode comma-separated hex bytes into a UTF-16LE string."""
    parts = [p.strip() for p in raw_hex.split(",") if p.strip()]
    try:
        data_bytes = bytes(int(p, 16) for p in parts)
        decoded = data_bytes.decode("utf-16le", errors="replace")
        return decoded.rstrip("\x00")
    except Exception:
        return raw_hex


def decode_reg_bytes(raw: bytes) -> str:
    """Decode raw .reg bytes handling UTF-16 LE (BOM / null bytes), UTF-8, and ANSI."""
    if raw.startswith(b"\xff\xfe") or b"\x00" in raw[:128]:
        try:
            return raw.decode("utf-16").lstrip("\ufeff\xef\xbb\xbf")
        except UnicodeDecodeError:
            pass
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc).lstrip("\ufeff\xef\xbb\xbf")
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").lstrip("\ufeff\xef\xbb\xbf")


def parse_reg_content(text: str) -> list[RegistryEntrySpec]:
    """Parse text content of a Windows .reg file into RegistryEntrySpec items."""
    text = text.lstrip("\ufeff\xef\xbb\xbf")
    lines = _unfold_lines(text)
    has_header = any(
        line.strip().startswith("Windows Registry Editor") or line.strip().startswith("REGEDIT4")
        for line in lines
    )
    if not has_header:
        raise ValueError(
            "Keine gültige Windows .reg Datei "
            "(Header 'Windows Registry Editor Version 5.00' fehlt)."
        )

    entries: list[RegistryEntrySpec] = []
    current_root = "HKLM"
    current_path = ""

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if line.startswith("Windows Registry Editor") or line.startswith("REGEDIT4"):
            continue

        # Section header: [HKEY_...] or [-HKEY_...]
        if line.startswith("[") and line.endswith("]"):
            sec = line[1:-1].strip()
            delete_key = False
            if sec.startswith("-"):
                delete_key = True
                sec = sec[1:].strip()
            root, path = _split_root_path(sec)
            current_root = root
            current_path = path
            if delete_key:
                entries.append(
                    RegistryEntrySpec(
                        root=current_root,
                        key_path=current_path,
                        value_name="",
                        reg_type="REG_SZ",
                        value_data="",
                        delete_on_uninstall=True,
                    )
                )
            continue

        if not current_path:
            continue

        entry = _parse_reg_value(line, current_root, current_path)
        if entry is not None:
            entries.append(entry)

    return entries


def parse_reg_file(source: str | Path | bytes) -> list[RegistryEntrySpec]:
    """Parse a Windows .reg file or text into a list of RegistryEntrySpec objects."""
    if isinstance(source, bytes):
        text = decode_reg_bytes(source)
    elif isinstance(source, Path):
        if not source.is_file():
            raise ValueError(f"Registry-Datei '{source}' nicht gefunden.")
        text = decode_reg_bytes(source.read_bytes())
    else:
        src_str = str(source)
        if "\n" not in src_str and ("\\" in src_str or "/" in src_str or src_str.endswith(".reg")):
            p = Path(src_str)
            if not p.is_file():
                raise ValueError(f"Registry-Datei '{source}' nicht gefunden.")
            text = decode_reg_bytes(p.read_bytes())
        else:
            text = src_str

    return parse_reg_content(text)


def _unfold_lines(text: str) -> list[str]:
    """Merge lines terminated by backslash in .reg multi-line values."""
    raw_lines = text.splitlines()
    unfolded: list[str] = []
    buf = ""
    for line in raw_lines:
        line_clean = line.rstrip()
        if line_clean.endswith("\\"):
            buf += line_clean[:-1]
        else:
            buf += line
            unfolded.append(buf)
            buf = ""
    if buf:
        unfolded.append(buf)
    return unfolded


def _split_root_path(header: str) -> tuple[str, str]:
    parts = header.split("\\", 1)
    canonical_root = normalize_root(parts[0])
    key_path = parts[1].strip() if len(parts) > 1 else ""
    return canonical_root, key_path


def _parse_reg_value(line: str, root: str, key_path: str) -> RegistryEntrySpec | None:
    # Matches: "ValueName"=... or @=...
    eq_idx = line.find("=")
    if eq_idx == -1:
        return None
    name_part = line[:eq_idx].strip()
    val_part = line[eq_idx + 1:].strip()

    if name_part == "@":
        val_name = ""
    elif name_part.startswith('"') and name_part.endswith('"'):
        val_name = unescape_reg_string(name_part[1:-1])
    else:
        val_name = name_part

    # Deletion of value: "Value"=-
    if val_part == "-":
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_SZ",
            value_data="",
            delete_on_uninstall=True,
        )

    # String value: "..."
    if val_part.startswith('"') and val_part.endswith('"'):
        content = unescape_reg_string(val_part[1:-1])
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_SZ",
            value_data=content,
        )

    # DWORD: dword:00000001
    if val_part.lower().startswith("dword:"):
        hex_val = val_part[6:].strip()
        try:
            dec_val = str(int(hex_val, 16))
        except ValueError:
            dec_val = hex_val
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_DWORD",
            value_data=dec_val,
        )

    # QWORD: qword:0000000000000001 or hex(b):
    if val_part.lower().startswith("qword:"):
        hex_val = val_part[6:].strip()
        try:
            dec_val = str(int(hex_val, 16))
        except ValueError:
            dec_val = hex_val
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_QWORD",
            value_data=dec_val,
        )

    if val_part.lower().startswith("hex(b):"):
        raw_hex = val_part[7:].strip()
        parts = [p.strip() for p in raw_hex.split(",") if p.strip()]
        try:
            val_bytes = bytes(int(p, 16) for p in parts)
            dec_val = str(int.from_bytes(val_bytes, byteorder="little"))
        except Exception:
            dec_val = raw_hex
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_QWORD",
            value_data=dec_val,
        )

    # hex(2): REG_EXPAND_SZ (UTF-16LE bytes)
    if val_part.lower().startswith("hex(2):"):
        raw_hex = val_part[7:].strip()
        decoded = decode_hex_utf16(raw_hex)
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_EXPAND_SZ",
            value_data=decoded,
        )

    # hex(7): REG_MULTI_SZ
    if val_part.lower().startswith("hex(7):"):
        raw_hex = val_part[7:].strip()
        decoded = decode_hex_utf16(raw_hex)
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_MULTI_SZ",
            value_data=decoded,
        )

    # hex: or hex(N): REG_BINARY (e.g. hex(1):, hex(99):)
    if val_part.lower().startswith("hex:") or re.match(r"^hex\([0-9a-fA-F]+\):", val_part.lower()):
        colon_idx = val_part.find(":")
        raw_hex = val_part[colon_idx + 1:].strip()
        cleaned_hex = re.sub(r"\s+", "", raw_hex)
        return RegistryEntrySpec(
            root=root,
            key_path=key_path,
            value_name=val_name,
            reg_type="REG_BINARY",
            value_data=cleaned_hex,
        )

    # Fallback to REG_SZ
    return RegistryEntrySpec(
        root=root,
        key_path=key_path,
        value_name=val_name,
        reg_type="REG_SZ",
        value_data=val_part,
    )


def reg_has_hkcu(source: str | Path | bytes | list[RegistryEntrySpec]) -> bool:
    """Return True if any entry points to HKCU / HKEY_CURRENT_USER."""
    if isinstance(source, list):
        return any(e.root.upper() == "HKCU" for e in source)
    try:
        specs = parse_reg_file(source)
        return any(e.root.upper() == "HKCU" for e in specs)
    except Exception:
        return False


def format_reg_entry_empirum(entry: RegistryEntrySpec) -> str:
    """Format a RegistryEntrySpec into a canonical Empirum Setup.inf [Reg:Product] line."""
    type_code = REG_TYPE_HEX.get(entry.reg_type.upper(), "0x00000000")
    prefix = "-" if entry.delete_on_uninstall else ""

    # Delete key syntax: -HKLM,"Software\Path"
    if entry.delete_on_uninstall and not entry.value_name and not entry.value_data:
        return f'{prefix}{entry.root},"{entry.key_path}"'

    val_quoted = f'"{entry.value_name}"' if entry.value_name else ""
    if entry.reg_type.upper() in ("REG_DWORD", "REG_QWORD"):
        try:
            val_num = int(entry.value_data, 0)
            return f'{prefix}{entry.root},"{entry.key_path}",{val_quoted},{type_code},{val_num}'
        except ValueError:
            pass
    data_str = entry.value_data.replace('"', '""').replace("\0", r"\0")
    return f'{prefix}{entry.root},"{entry.key_path}",{val_quoted},{type_code},"{data_str}"'


__all__ = [
    "REG_TYPE_HEX",
    "decode_hex_utf16",
    "decode_reg_bytes",
    "format_reg_entry_empirum",
    "normalize_root",
    "parse_reg_content",
    "parse_reg_file",
    "reg_has_hkcu",
    "unescape_reg_string",
]
