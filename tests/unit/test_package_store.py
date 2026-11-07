"""Tests for Empirum PackageStore deploy."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from empirum_services.package_store import (
    DeployMode,
    PackageStoreError,
    _ensure_within_store,
    build_destination,
    deploy_to_package_store,
    expand_empirum_path,
    plan_deploy,
    validate_package_dir,
)


def _make_package(root: Path, name: str = "DemoApp_1.2.3") -> Path:
    pkg = root / name
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Files").mkdir(parents=True)
    (pkg / "Install" / "Setup.inf").write_text("[Setup]\nProductName=Demo\n", encoding="utf-8")
    (pkg / "Files" / "payload.exe").write_bytes(b"MZ")
    return pkg


def test_expand_empirum_server_token() -> None:
    out = expand_empirum_path(
        r"\\%EmpirumServer%\Configurator$\PackageStore",
        empirum_server="emp-srv01",
        environ={},
    )
    assert out == r"\\emp-srv01\Configurator$\PackageStore"


def test_validate_and_build_destination(tmp_path: Path) -> None:
    pkg = _make_package(tmp_path)
    layout = validate_package_dir(pkg)
    assert layout.setup_inf.name == "Setup.inf"
    dest = build_destination(
        tmp_path / "PackageStore",
        package_dir=pkg,
        manufacturer="Acme",
        mode=DeployMode.VENDOR_PRODUCT_VERSION,
    )
    assert dest == tmp_path / "PackageStore" / "Acme" / "DemoApp" / "1.2.3"


def test_deploy_copy_and_overwrite(tmp_path: Path) -> None:
    pkg = _make_package(tmp_path / "src")
    store = tmp_path / "PackageStore"
    dry = deploy_to_package_store(
        pkg,
        store,
        manufacturer="Acme",
        dry_run=True,
    )
    assert dry.dry_run is True
    assert "DemoApp" in str(dry.destination)

    result = deploy_to_package_store(
        pkg,
        store,
        manufacturer="Acme",
        dry_run=False,
    )
    assert result.copied_files >= 2
    assert (result.destination / "Install" / "Setup.inf").is_file()

    with pytest.raises(PackageStoreError, match="existiert"):
        deploy_to_package_store(pkg, store, manufacturer="Acme", dry_run=False)

    again = deploy_to_package_store(
        pkg, store, manufacturer="Acme", overwrite=True, dry_run=False
    )
    assert again.copied_files >= 2


def test_plan_flat_mode(tmp_path: Path) -> None:
    pkg = _make_package(tmp_path)
    plan = plan_deploy(
        pkg,
        tmp_path / "Store",
        mode=DeployMode.FLAT,
        require_free_target=False,
    )
    assert plan.destination.name == "DemoApp_1.2.3"


def test_validate_rejects_incomplete(tmp_path: Path) -> None:
    bad = tmp_path / "Broken"
    bad.mkdir()
    with pytest.raises(PackageStoreError):
        validate_package_dir(bad)


def test_build_destination_blocks_traversal_segments(tmp_path: Path) -> None:
    pkg = _make_package(tmp_path)
    dest = build_destination(
        tmp_path / "Store",
        package_dir=pkg,
        manufacturer="..",
        product="..",
        version="1.0.",
        mode=DeployMode.VENDOR_PRODUCT_VERSION,
    )
    assert ".." not in dest.parts
    assert dest == tmp_path / "Store" / "Vendor" / "Package" / "1.0"


def test_build_destination_replaces_reserved_names(tmp_path: Path) -> None:
    pkg = _make_package(tmp_path)
    dest = build_destination(
        tmp_path / "Store",
        package_dir=pkg,
        manufacturer="CON",
        version="NUL",
        mode=DeployMode.VENDOR_PRODUCT_VERSION,
    )
    upper_parts = {p.upper() for p in dest.parts}
    assert "CON" not in upper_parts
    assert "NUL" not in upper_parts
    assert dest.parts[-3] == "Vendor"


def test_ensure_within_store_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(PackageStoreError, match="außerhalb"):
        _ensure_within_store(tmp_path / "Store" / ".." / "Elsewhere", tmp_path / "Store")
    _ensure_within_store(tmp_path / "Store" / "Vendor" / "App" / "1.0", tmp_path / "Store")


def test_deploy_overwrite_readonly_target(tmp_path: Path) -> None:
    pkg = _make_package(tmp_path / "src")
    store = tmp_path / "PackageStore"
    first = deploy_to_package_store(pkg, store, manufacturer="Acme", dry_run=False)
    os.chmod(first.destination / "Install" / "Setup.inf", stat.S_IREAD)
    again = deploy_to_package_store(
        pkg, store, manufacturer="Acme", overwrite=True, dry_run=False
    )
    assert (again.destination / "Install" / "Setup.inf").is_file()


def test_expand_empirum_path_uses_provided_environ() -> None:
    out = expand_empirum_path(r"\\%DepotServer%\Share", environ={"DepotServer": "srv99"})
    assert out == r"\\srv99\Share"


def test_expand_empirum_path_leaves_unknown_tokens() -> None:
    out = expand_empirum_path(r"\\%UnknownVar%\Share", environ={})
    assert out == r"\\%UnknownVar%\Share"


def test_readiness_error_not_masked_by_warn_item(tmp_path: Path) -> None:
    """Regression: PKG-008 (warn) must not mask VAL-012 errors -> deploy blocked."""
    from empirum_services.package_readiness import (
        ReadinessLevel,
        check_package_readiness,
    )

    pkg = _make_package(tmp_path)
    inf = pkg / "Install" / "Setup.inf"
    inf.write_text(
        "[SetupInfo]\r\nMethod=MSI\r\nCommand line options=/S2 /AW\r\n\r\n"
        "[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n\r\n"
        "[Set:Product]\r\nEcho ok\r\n",
        encoding="cp1252",
    )
    report = check_package_readiness(pkg)
    assert report.level == ReadinessLevel.FAIL
    assert report.ok_to_deploy is False
    assert any(d.code == "VAL-012" for d in report.diagnostics)
