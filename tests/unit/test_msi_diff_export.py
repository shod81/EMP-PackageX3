from __future__ import annotations

from pathlib import Path

from empirum_core.diffing import unified_inf_diff
from empirum_core.linter import Diagnostic, Severity
from empirum_infra.inspectors.msi import DictMsiBackend, inspect_msi, set_msi_backend
from empirum_services.diagnostics_export import format_diagnostics_report


def test_msi_dict_backend_fixture() -> None:
    backend = DictMsiBackend(
        {
            "demo": {
                "ProductName": "Demo MSI",
                "ProductVersion": "9.8.7",
                "Manufacturer": "Hodrius",
                "Template": "Intel;64",
            }
        }
    )
    set_msi_backend(backend)
    try:
        meta = inspect_msi(Path("C:/fake/Demo.msi"))
        assert meta.product_name == "Demo MSI"
        assert meta.product_version == "9.8.7"
        assert meta.architecture == "x64"
        assert meta.package_type == "MSI"
    finally:
        set_msi_backend(None)


def test_unified_diff_detects_change() -> None:
    a = "[SetupInfo]\nProductName=A\n"
    b = "[SetupInfo]\nProductName=B\n"
    diff = unified_inf_diff(a, b)
    assert "-ProductName=A" in diff
    assert "+ProductName=B" in diff


def test_diagnostics_export_format() -> None:
    text = format_diagnostics_report(
        [
            Diagnostic(
                code="VAL-003",
                severity=Severity.ERROR,
                message="backslash",
                line=4,
            )
        ],
        package="X",
        app_version="0.4.0",
    )
    assert "VAL-003" in text
    assert "Z4" in text
