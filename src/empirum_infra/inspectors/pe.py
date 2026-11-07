"""PE / EXE inspection via pefile (no Qt)."""

from __future__ import annotations

import contextlib
from pathlib import Path

import pefile

from empirum_core.inspect import PackageMetadata

_MACHINE = {
    0x014C: "x86",
    0x8664: "x64",
    0xAA64: "ARM64",
    0x01C4: "ARM",
}

_SIGNATURES: list[tuple[bytes, str]] = [
    (b"Inno Setup Setup Data", "Inno"),
    (b"NullsoftInst", "NSIS"),
    (b"InstallShield", "InstallShield"),
    (b"Advanced Installer", "AdvancedInstaller"),
]

_SIGNATURE_CHUNK = 1 << 16


def inspect_pe(path: str | Path) -> PackageMetadata:
    file_path = Path(path)
    try:
        data = file_path.read_bytes()
        pe = pefile.PE(data=data, fast_load=True)
    except (pefile.PEFormatError, OSError, ValueError) as exc:
        # Degrade like the MSI inspector instead of crashing the wizard.
        return PackageMetadata(
            package_type="EXE",
            architecture="Unknown",
            source_path=str(file_path.resolve()),
            product_name=file_path.stem,
            properties={"inspector_error": f"PE-Inspektion fehlgeschlagen: {exc}"},
        )
    with contextlib.suppress(Exception):
        pe.parse_data_directories(
            directories=[
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"],
            ]
        )

    arch = _MACHINE.get(pe.FILE_HEADER.Machine, "Unknown")
    meta = PackageMetadata(
        package_type="EXE",
        architecture=arch,
        source_path=str(file_path.resolve()),
        exe_kind=_detect_kind(data),
    )
    _fill_version_info(pe, meta)
    if not meta.product_name:
        meta.product_name = file_path.stem
    return meta


def _detect_kind(data: bytes) -> str:
    """Installer signature scan in bounded windows (needle-length overlap)."""
    overlap = max(len(needle) for needle, _ in _SIGNATURES) - 1
    for offset in range(0, len(data), _SIGNATURE_CHUNK):
        window = data[offset : offset + _SIGNATURE_CHUNK + overlap]
        for needle, label in _SIGNATURES:
            if needle in window:
                return label
    return "Generic"


def _fill_version_info(pe: pefile.PE, meta: PackageMetadata) -> None:
    with contextlib.suppress(Exception):
        if not hasattr(pe, "FileInfo"):
            pe.parse_data_directories(
                directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
            )
    try:
        file_info = getattr(pe, "FileInfo", None)
        if not file_info:
            return
        for entry in file_info:
            for info in getattr(entry, "StringTable", []) or []:
                entries = {
                    k.decode(errors="ignore"): v.decode(errors="ignore")
                    for k, v in info.entries.items()
                }
                meta.product_name = entries.get("ProductName") or meta.product_name
                meta.product_version = entries.get("ProductVersion") or meta.product_version
                meta.manufacturer = entries.get("CompanyName") or meta.manufacturer
                meta.properties.update(entries)
    except Exception:
        return
