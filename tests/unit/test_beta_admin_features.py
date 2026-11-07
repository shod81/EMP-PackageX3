"""Simulator standard entry + package readiness."""

from __future__ import annotations

from pathlib import Path

from empirum_core.inspect import PackageMetadata
from empirum_core.simulator import SimMode, simulate
from empirum_core.templates import render_template, silent_args_for
from empirum_services.package_readiness import ReadinessLevel, check_package_readiness


def test_simulate_standard_product_walks_set_product() -> None:
    doc = render_template(
        "msi",
        PackageMetadata(
            product_name="Demo",
            product_version="1.0",
            manufacturer="Acme",
            package_type="MSI",
            source_path=r"C:\tmp\Demo.msi",
            product_code="{AAA}",
        ),
    )
    report = simulate(doc, SimMode.INSTALL)
    assert report.entry_section == "Product"
    sections = {a.section for a in report.actions}
    assert "Set:Product" in sections or any("InstallMSI" in s for s in sections)
    assert any(a.command in {"CallHidden", "ref", "AddMeter", "If"} for a in report.actions)


def test_simulate_standard_uninstall_entry() -> None:
    doc = render_template(
        "msi",
        PackageMetadata(
            product_name="Demo",
            product_version="1.0",
            manufacturer="Acme",
            source_path=r"C:\tmp\Demo.msi",
        ),
    )
    report = simulate(doc, SimMode.UNINSTALL)
    assert report.entry_section in {"Set:Deinstallation", "Product"}
    assert report.actions


def test_silent_args_custom_and_presets() -> None:
    meta = PackageMetadata(exe_kind="NSIS")
    assert silent_args_for(meta) == "/S"
    meta.properties["silent_args"] = "/custom"
    assert silent_args_for(meta) == "/custom"


def test_processes_in_exe_template() -> None:
    meta = PackageMetadata(
        product_name="App",
        product_version="1",
        manufacturer="V",
        package_type="EXE",
        source_path=r"C:\a.exe",
        exe_kind="NSIS",
        properties={"kill_processes": "app.exe|App|ABORT"},
    )
    doc = render_template("exe", meta)
    blob = "\n".join(
        getattr(n, "text", "") or f"{getattr(n,'key','')}={getattr(n,'value','')}"
        for s in doc.sections
        for n in s.lines
    )
    assert "APP1=app.exe" in blob
    assert "AskKillProcesses 300,APP1" in blob
    assert "/AW" in blob


def test_package_readiness_ok(tmp_path: Path) -> None:
    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.0",
        manufacturer="Acme",
        source_path=r"C:\tmp\Demo.msi",
    )
    from empirum_services.creator.generator import generate_package

    result = generate_package(meta, tmp_path, kind="msi", copy_source=False)
    # Ensure Files exists for readiness
    (result.package_dir / "Files").mkdir(exist_ok=True)
    report = check_package_readiness(result.package_dir)
    assert report.ok_to_deploy
    assert report.level in {ReadinessLevel.OK, ReadinessLevel.WARN}


def test_package_readiness_missing_layout(tmp_path: Path) -> None:
    report = check_package_readiness(tmp_path / "empty")
    assert report.level == ReadinessLevel.FAIL
    assert any(i.code == "PKG-001" for i in report.items)


def test_feedback_zip(tmp_path: Path) -> None:
    from emp_packagex3.feedback import create_feedback_zip

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "emp-packagex3.log").write_text("hello\n", encoding="utf-8")
    zip_path = create_feedback_zip(tmp_path / "fb.zip", log_dir=log_dir, extra_note="test")
    assert zip_path.is_file()
    import zipfile

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert "README.txt" in names
        assert "logs/emp-packagex3.log" in names
