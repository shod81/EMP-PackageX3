"""MSI property reading with injectable backend (COM or fixture/mock)."""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Protocol

from empirum_core.inspect import PackageMetadata

_PROPS = (
    "ProductName",
    "ProductVersion",
    "Manufacturer",
    "ProductCode",
    "UpgradeCode",
    "ARPPRODUCTICON",
)


class MsiPropertyBackend(Protocol):
    def read_properties(self, path: Path) -> dict[str, str]: ...


class ComMsiBackend:
    """Live Windows Installer COM backend."""

    def read_properties(self, path: Path) -> dict[str, str]:
        import comtypes.client

        installer = comtypes.client.CreateObject("WindowsInstaller.Installer")
        database = installer.OpenDatabase(str(path), 0)
        try:
            result: dict[str, str] = {}
            for prop in _PROPS:
                value = _query_property(database, prop)
                if value:
                    result[prop] = value
            try:
                summary = database.SummaryInformation(0)
                template = summary.Property(7)
                if template:
                    result["Template"] = str(template)
            except Exception:
                pass
            return result
        finally:
            # Release MSI handles eagerly; comtypes would only free them on GC.
            del database
            del installer


class DictMsiBackend:
    """Fixture backend: maps filename stem → property dict."""

    def __init__(self, catalog: dict[str, dict[str, str]]) -> None:
        self._catalog = catalog

    def read_properties(self, path: Path) -> dict[str, str]:
        key = path.stem.casefold()
        if key not in self._catalog:
            raise FileNotFoundError(f"No MSI fixture for {path.name}")
        return dict(self._catalog[key])


_default_backend: MsiPropertyBackend | None = None


def set_msi_backend(backend: MsiPropertyBackend | None) -> None:
    global _default_backend
    _default_backend = backend


def inspect_msi(path: str | Path, *, backend: MsiPropertyBackend | None = None) -> PackageMetadata:
    file_path = Path(path)
    # Unknown until proven by the Template field or backend success.
    meta = PackageMetadata(
        package_type="MSI",
        source_path=str(file_path.resolve()),
        architecture="Unknown",
    )
    active = backend or _default_backend or ComMsiBackend()
    try:
        props = active.read_properties(file_path)
    except Exception as exc:
        meta.properties["inspector_error"] = str(exc)
        meta.product_name = file_path.stem
        return meta

    meta.product_name = props.get("ProductName", file_path.stem)
    meta.product_version = props.get("ProductVersion", "")
    meta.manufacturer = props.get("Manufacturer", "")
    meta.product_code = props.get("ProductCode", "")
    meta.upgrade_code = props.get("UpgradeCode", "")
    meta.properties.update(props)
    template = props.get("Template", "")
    low = template.lower()
    if "x64" in low or "intel;64" in low:
        meta.architecture = "x64"
    elif "arm64" in low:
        meta.architecture = "ARM64"
    elif "intel64" in low:
        meta.architecture = "IA64"  # Itanium – not x64
    elif "intel" in low:
        meta.architecture = "x86"
    return meta


def _query_property(database: object, name: str) -> str:
    view = database.OpenView(  # type: ignore[attr-defined]
        f"SELECT `Value` FROM `Property` WHERE `Property`='{name}'"
    )
    try:
        view.Execute(None)
        record = view.Fetch()
        if record is None:
            return ""
        return str(record.StringData(1))
    finally:
        with contextlib.suppress(Exception):
            view.Close()
