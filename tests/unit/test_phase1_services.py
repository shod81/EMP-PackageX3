from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

from empirum_core.inspect import PackageMetadata
from empirum_core.linter import lint_document
from empirum_core.simulator import SimMode, simulate
from empirum_core.templates import render_template
from empirum_services.creator.generator import generate_package
from empirum_services.editor.sync import EditOrigin, SyncController
from empirum_services.runner import (
    RunnerConfig,
    RunnerSafetyError,
    assert_safe_target,
    build_command,
    run_package,
)


def test_msi_template_lint_clean_enough() -> None:
    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.2.3",
        manufacturer="Hodrius",
        package_type="MSI",
        source_path=r"C:\tmp\Demo.msi",
    )
    doc = render_template("msi", meta)
    errors = [d for d in lint_document(doc) if d.severity.value == "error"]
    assert errors == []


def test_generate_package_writes_cp1252_no_bom_and_structure(tmp_path: Path) -> None:
    meta = PackageMetadata(
        product_name="ScriptDemo",
        manufacturer="Acme",
        package_type="Script",
    )
    result = generate_package(meta, tmp_path, kind="Script", copy_source=False)
    assert result.setup_inf.is_file()
    assert (result.package_dir / "Files").is_dir()
    raw = result.setup_inf.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.startswith(b"[SetupInfo]")
    text = raw.decode("cp1252")
    assert "[Installer]" in text
    assert "SetupInfDir=Install" in text
    assert "SrcDir=.." in text
    assert not any(d.severity.value == "error" for d in result.diagnostics)


def test_generate_package_encodes_umlauts_as_single_byte_cp1252(tmp_path: Path) -> None:
    meta = PackageMetadata(
        product_name="Büro & Test",
        manufacturer="Hödrius",
        package_type="Script",
    )
    result = generate_package(meta, tmp_path, kind="Script", copy_source=False)
    raw = result.setup_inf.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    # 'ü' in CP1252 is 0xFC, not UTF-8 multi-byte 0xC3 0xBC
    assert b"\xfc" in raw
    assert b"\xc3\xbc" not in raw
    # 'ö' in CP1252 is 0xF6, not UTF-8 multi-byte 0xC3 0xB6
    assert b"\xf6" in raw
    assert b"\xc3\xb6" not in raw
    text = raw.decode("cp1252")
    assert "Büro & Test" in text
    assert "Hödrius" in text
    assert not any(d.severity.value == "error" for d in result.diagnostics)


def test_sync_controller_roundtrip_code() -> None:
    sync = SyncController()
    text = "[SetupInfo]\r\nProductName=X\r\n"
    state = sync.apply_code_edit(text)
    assert state is not None
    assert state.last_origin == EditOrigin.CODE
    assert sync.document.section("SetupInfo") is not None
    v = sync.version
    assert sync.apply_code_edit("nope", expected_version=v - 1) is None


def test_simulator_finds_uninstall_gap() -> None:
    from empirum_core.parser.lexer import lex_text

    doc = lex_text(
        "[Set_Install]\r\nCall=msiexec /i a.msi\r\nIf=%ErrorLevel%\r\n"
    )
    report = simulate(doc, SimMode.INSTALL)
    assert any("Set_Uninstall" in g for g in report.gaps)


def test_runner_blocks_non_whitelist(tmp_path: Path) -> None:
    cfg = RunnerConfig(allowed_roots=(tmp_path / "allowed",), require_vm_marker=True)
    with pytest.raises(RunnerSafetyError):
        assert_safe_target(tmp_path / "other" / "pkg", cfg)


def test_runner_requires_marker(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    pkg = root / "pkg"
    pkg.mkdir(parents=True)
    cfg = RunnerConfig(allowed_roots=(root,), require_vm_marker=True)
    with pytest.raises(RunnerSafetyError):
        assert_safe_target(pkg, cfg)
    (root / ".emp_packagex3_vm").write_text("ok", encoding="utf-8")
    assert assert_safe_target(pkg, cfg) == pkg.resolve()


def test_runner_dry_run(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    pkg = root / "pkg"
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Install" / "Setup.inf").write_text("[SetupInfo]\r\n", encoding="utf-8")
    (root / ".emp_packagex3_vm").write_text("ok", encoding="utf-8")
    cfg = RunnerConfig(
        allowed_roots=(root,), require_vm_marker=True, setup_exe=Path("Setup.exe")
    )
    result = run_package(pkg, config=cfg, dry_run=True)
    assert result.returncode == 0
    assert "Setup.inf" in result.command[1]


def test_pe_inspector_on_python_exe() -> None:
    from empirum_infra.inspectors.pe import inspect_pe

    cand = Path(sys.executable)
    if not cand.is_file():
        pytest.skip("no PE sample")
    meta = inspect_pe(cand)
    assert meta.package_type == "EXE"
    assert meta.architecture in {"x86", "x64", "ARM64", "ARM", "Unknown"}


def test_runner_mode_validation() -> None:
    root = Path(tempfile.mkdtemp())
    pkg = root / "pkg"
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Install" / "Setup.inf").write_text("[SetupInfo]\r\n", encoding="utf-8")
    with pytest.raises(ValueError, match="install"):
        build_command(pkg, mode="unknown")


def test_runner_default_exe_path_expanded(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(tempfile.mkdtemp())
    pkg = root / "pkg"
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Install" / "Setup.inf").write_text("[SetupInfo]\r\n", encoding="utf-8")
    monkeypatch.delenv("EMPIRUM_SETUP_EXE", raising=False)
    monkeypatch.setenv("CommonFilesDir", r"C:\Program Files\Common Files")
    cmd = build_command(pkg)
    assert cmd[0] == r"C:\Program Files\Common Files\Setup64\Setup.exe"


def test_runner_config_has_timeout() -> None:
    cfg = RunnerConfig(allowed_roots=(Path("C:/x"),))
    assert cfg.timeout_seconds > 0


def test_pe_inspector_degrades_on_corrupt_exe(tmp_path: Path) -> None:
    from empirum_infra.inspectors.pe import inspect_pe

    bogus = tmp_path / "notreally.exe"
    bogus.write_bytes(b"definitely not a PE file")
    meta = inspect_pe(bogus)
    assert meta.properties.get("inspector_error")
    assert meta.architecture == "Unknown"
    assert meta.product_name == "notreally"


def test_msi_architecture_unknown_on_backend_error(tmp_path: Path) -> None:
    from empirum_infra.inspectors.msi import inspect_msi

    class FailingBackend:
        def read_properties(self, path: Path) -> dict[str, str]:
            raise RuntimeError("boom")

    meta = inspect_msi(tmp_path / "x.msi", backend=FailingBackend())
    assert meta.architecture == "Unknown"
    assert meta.properties.get("inspector_error") == "boom"


def test_msi_template_mapping_case_insensitive(tmp_path: Path) -> None:
    from empirum_infra.inspectors.msi import DictMsiBackend, inspect_msi

    msi = tmp_path / "Demo.msi"
    msi.write_bytes(b"D0CF11E0")
    backend = DictMsiBackend({"demo": {"ProductName": "Demo", "Template": "intel;64"}})
    meta = inspect_msi(msi, backend=backend)
    assert meta.architecture == "x64"
    backend32 = DictMsiBackend({"demo": {"ProductName": "Demo", "Template": "INTEL"}})
    assert inspect_msi(msi, backend=backend32).architecture == "x86"


def test_generate_package_sanitizes_version(tmp_path: Path) -> None:
    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.0\\..\\evil",
        manufacturer="M",
        package_type="Script",
    )
    result = generate_package(meta, tmp_path)
    assert result.package_dir.parent == tmp_path
    assert ".." not in result.package_dir.parts


def test_generate_package_warns_on_missing_source(tmp_path: Path) -> None:
    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.0",
        manufacturer="M",
        package_type="Script",
        source_path=str(tmp_path / "missing.cmd"),
    )
    result = generate_package(meta, tmp_path)
    assert any("Quell-Installer" in w for w in result.warnings)


def test_generate_package_backs_up_existing_setup_inf(tmp_path: Path) -> None:
    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.0",
        manufacturer="M",
        package_type="Script",
    )
    first = generate_package(meta, tmp_path)
    second = generate_package(meta, tmp_path)
    assert first.setup_inf.is_file()
    assert second.warnings == []
    bak_dir = first.setup_inf.parent / ".emp_packagex3_bak"
    backups = list(bak_dir.glob("Setup.inf.*.bak")) if bak_dir.is_dir() else []
    assert backups, "regeneration must keep a WAL backup of the previous Setup.inf"
