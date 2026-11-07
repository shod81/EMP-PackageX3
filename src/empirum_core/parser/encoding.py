"""Encoding detection for Empirum Setup.inf files (CP1252 / UTF-8)."""

from __future__ import annotations

from dataclasses import dataclass

UTF8_BOM = b"\xef\xbb\xbf"
UTF16_LE_BOM = b"\xff\xfe"
UTF16_BE_BOM = b"\xfe\xff"


@dataclass(frozen=True, slots=True)
class DetectedEncoding:
    name: str  # "utf-8" | "cp1252"
    has_bom: bool
    ambiguous: bool = False


def detect_encoding(data: bytes) -> DetectedEncoding:
    """Detect encoding with BOM preference, then UTF-8 validity, else CP1252.

    Ambiguous files (valid as both UTF-8 and typical CP1252) are flagged so the
    editor can open read-only until the user picks an encoding (plan R-02).
    """
    if data.startswith(UTF8_BOM):
        return DetectedEncoding(name="utf-8", has_bom=True, ambiguous=False)
    if data.startswith(UTF16_LE_BOM):
        return DetectedEncoding(name="utf-16-le", has_bom=True, ambiguous=False)
    if data.startswith(UTF16_BE_BOM):
        return DetectedEncoding(name="utf-16-be", has_bom=True, ambiguous=False)

    utf8_ok = False
    try:
        data.decode("utf-8")
        utf8_ok = True
    except UnicodeDecodeError:
        utf8_ok = False

    if not utf8_ok:
        return DetectedEncoding(name="cp1252", has_bom=False, ambiguous=False)

    # Valid UTF-8. Prefer UTF-8 when high bytes form valid multi-byte sequences;
    # pure ASCII is reported as cp1252 (Empirum field default) without ambiguity.
    if _looks_like_utf8_multibyte(data):
        # Could still be coincidental; mark ambiguous only if also "latin1-ish"
        ambiguous = _has_non_ascii(data)
        return DetectedEncoding(name="utf-8", has_bom=False, ambiguous=ambiguous)

    return DetectedEncoding(name="cp1252", has_bom=False, ambiguous=False)


def decode_bytes(
    data: bytes,
    encoding: DetectedEncoding | None = None,
) -> tuple[str, DetectedEncoding]:
    detected = encoding or detect_encoding(data)
    if detected.has_bom:
        bom_len = len(UTF8_BOM) if data.startswith(UTF8_BOM) else 2
        payload = data[bom_len:]
    else:
        payload = data
    text = payload.decode(detected.name, errors="strict")
    text = text.lstrip("\ufeff\xef\xbb\xbf")
    return text, detected


def encode_text(text: str, encoding_name: str, *, has_bom: bool = False) -> bytes:
    body = text.encode(encoding_name)
    if has_bom:
        if encoding_name.lower().replace("-", "") != "utf8":
            raise ValueError("BOM ist nur für UTF-8 gültig (cp1252 ohne BOM speichern)")
        return UTF8_BOM + body
    return body


def _has_non_ascii(data: bytes) -> bool:
    return any(b > 127 for b in data)


def _looks_like_utf8_multibyte(data: bytes) -> bool:
    """True if data contains valid UTF-8 multi-byte sequences."""
    i = 0
    found = False
    while i < len(data):
        b = data[i]
        if b < 0x80:
            i += 1
            continue
        if 0xC2 <= b <= 0xDF:
            if i + 1 >= len(data) or not (0x80 <= data[i + 1] <= 0xBF):
                return False
            found = True
            i += 2
        elif 0xE0 <= b <= 0xEF:
            if i + 2 >= len(data):
                return False
            if not (0x80 <= data[i + 1] <= 0xBF and 0x80 <= data[i + 2] <= 0xBF):
                return False
            found = True
            i += 3
        elif 0xF0 <= b <= 0xF4:
            if i + 3 >= len(data):
                return False
            if not all(0x80 <= data[i + j] <= 0xBF for j in (1, 2, 3)):
                return False
            found = True
            i += 4
        else:
            return False
    return found
