"""Standard skeleton repair: core + on-disk service + editor/deploy wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from empirum_core.ast.model import RawLine, Section
from empirum_core.linter import lint_document
from empirum_core.parser.lexer import lex_text
from empirum_core.prettify import prettify_text
from empirum_core.serializer.serialize import serialize_document
from empirum_core.skeleton_repair import add_missing_standard_sections, missing_standard_sections

# Converted-package pattern: package-shaped but
# missing Reg:/Ini:/Security:/Shell: standard sections; Set-refs already called.
_CONVERTED_SAMPLE = (
    "[SetupInfo]\r\nMethod=MSI\r\nCommand line options=/S2 /AW\r\n\r\n"
    "[VarDefInfo]\r\n\r\n"
    "[Setup]\r\nVersion=14.2\r\n\r\n"
    "[Requirements]\r\n\r\n"
    "[Application]\r\nProductName=X\r\n\r\n"
    "[Strings:07]\r\nEndMessageDesc=Fertig!\r\n\r\n"
    "[Strings:09]\r\nEndMessageDesc=Done!\r\n\r\n"
    "[SysStrings:07]\r\nUsers=Benutzer\r\n\r\n"
    "[SysStrings:09]\r\nUsers=Users\r\n\r\n"
    "[Environment]\r\nCommonSetupDir=%CommonFilesDir%\\Setup%SetupBits%\r\n\r\n"
    "[Encryption]\r\n\r\n"
    "[Disks]\r\n1=%Disk1%\r\n\r\n"
    "[Options]\r\nProduct=%ProductName%, COPYALWAYS, Product, \"%ProductDesc%\"\r\n\r\n"
    "[Processes]\r\n\r\n"
    "[Installer]\r\n1:%SetupInfDir%\\Setup.inf, , ALWAYS, 0\r\n\r\n"
    "[Product]\r\n"
    "#Set:Product, DONTDELETE\r\n"
    "#Set:Deinstallation, DELETE\r\n"
    "#Set:Client, CLIENT\r\n"
    "\r\n"
    "[RebootRequired]\r\nSetReboot 0\r\n-SetReboot 0\r\n\r\n"
    "[Set:Product]\r\nEcho ok\r\n"
    "\r\n"
    "[Set:Deinstallation]\r\n-Del %AppData%\\x\r\n\r\n"
    "[Set:Client]\r\nEcho user part\r\n\r\n"
    "[Set:InstallationError]\r\nErrorLogMsg %ErrorLogMessage%\r\nAbort\r\n\r\n"
    "[Set:ReinstallationError]\r\nErrorLogMsg %ErrorLogMessage%\r\nAbort\r\n\r\n"
    "[Set:DeInstallationError]\r\n-ErrorLogMsg %ErrorLogMessage%\r\n-Abort\r\n"
)


def _is_blank(node: object) -> bool:
    """True for the separator blank line the section appender inserts."""
    return isinstance(node, RawLine) and node.text == ""


def _body(section: Section) -> list[str]:
    """Section body texts, ignoring separator blank lines."""
    return [node.text for node in section.lines if not _is_blank(node)]


def _doc(text: str):
    return lex_text(text)


@pytest.fixture(autouse=True)
def _hermetic_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M-3: repair WAL backups go to the user profile – keep tests out of it."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))


def test_missing_standard_sections_on_converted_pattern() -> None:
    missing = missing_standard_sections(_doc(_CONVERTED_SAMPLE))
    assert set(missing) == {
        "Reg:OnUninstallProduct",
        "Reg:Product",
        "Ini:Product",
        "Security:Product",
        "Shell:Product",
    }


def test_add_missing_sections_and_refs_canonical() -> None:
    doc = _doc(_CONVERTED_SAMPLE)
    repair = add_missing_standard_sections(doc)
    assert set(repair.added_sections) == {
        "Reg:OnUninstallProduct",
        "Reg:Product",
        "Ini:Product",
        "Security:Product",
        "Shell:Product",
    }
    # Set-refs already exist -> not duplicated; 4 new refs + none for Shell
    assert repair.added_refs == [
        "#Reg:OnUninstallProduct, DELETE",
        "#Reg:Product, DONTDELETE",
        "#Ini:Product, DONTDELETE",
        "#Security:Product",
    ]
    product = doc.section("Product")
    assert product is not None
    texts = [getattr(n, "text", "") for n in product.lines]
    assert texts.count("#Reg:Product, DONTDELETE") == 1
    # sections appended in canonical standard order at document end
    names = [s.name for s in doc.sections]
    assert names[-5:] == [
        "Reg:OnUninstallProduct",
        "Reg:Product",
        "Ini:Product",
        "Security:Product",
        "Shell:Product",
    ]


def test_repair_is_idempotent() -> None:
    doc = _doc(_CONVERTED_SAMPLE)
    add_missing_standard_sections(doc)
    second = add_missing_standard_sections(doc)
    assert second.added_sections == []
    assert second.added_refs == []


def test_repair_recognizes_case_insensitive_existing() -> None:
    doc = _doc(
        _CONVERTED_SAMPLE
        + "[REG:PRODUCT]\r\n\r\n[shell:product]\r\n\r\n"
        "[Product]\r\n#security:product\r\n"
    )
    repair = add_missing_standard_sections(doc)
    assert "Reg:Product" not in repair.added_sections
    assert "Shell:Product" not in repair.added_sections
    assert all("Security" not in r for r in repair.added_refs)


def test_commented_ref_does_not_count() -> None:
    doc = _doc(_CONVERTED_SAMPLE + "[Product]\r\n; #Reg:Product, DONTDELETE\r\n")
    repair = add_missing_standard_sections(doc)
    assert "#Reg:Product, DONTDELETE" in repair.added_refs


def test_wizard_templates_need_no_repair() -> None:
    """Gate: wizard output is standard-complete - repair must add nothing."""
    from empirum_core.inspect import PackageMetadata
    from empirum_core.templates import render_template

    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.0",
        manufacturer="Acme",
        package_type="MSI",
        source_path=r"C:\tmp\Demo.msi",
    )
    for kind in ("msi", "exe", "script", "links"):
        doc = render_template(kind, meta)
        assert missing_standard_sections(doc) == [], kind
        repair = add_missing_standard_sections(doc)
        assert repair.added_sections == [] and repair.added_refs == []


def test_repaired_converted_document_lints_without_val001() -> None:
    doc = _doc(_CONVERTED_SAMPLE)
    add_missing_standard_sections(doc)
    codes = {d.code for d in lint_document(doc)}
    assert "VAL-001" not in codes  # all new refs resolve
    assert "VAL-012" not in codes  # skeleton complete


# Slim document without the three error handlers: the repair must create them
# with the canonical standard bodies instead of empty stubs.
_MINIMAL_SAMPLE = (
    "[SetupInfo]\r\nMethod=MSI\r\n\r\n"
    "[Application]\r\nProductName=X\r\n\r\n"
    "[Product]\r\n#Set:Product, DONTDELETE\r\n\r\n"
    "[Set:Product]\r\nEcho ok\r\n\r\n"
    "[Set:Deinstallation]\r\nEcho bye\r\n"
)


def test_missing_error_handlers_get_canonical_bodies() -> None:
    doc = _doc(_MINIMAL_SAMPLE)
    repair = add_missing_standard_sections(doc)
    assert {
        "Set:InstallationError",
        "Set:ReinstallationError",
        "Set:DeInstallationError",
    } <= set(repair.added_sections)

    install = doc.section("Set:InstallationError")
    assert install is not None
    assert _body(install) == [
        "ErrorLogMsg %ErrorLogMessage%",
        "Abort %ErrorText%",
    ]
    reinstall = doc.section("Set:ReinstallationError")
    assert reinstall is not None
    assert _body(reinstall) == [
        "ErrorLogMsg %ErrorLogMessage%",
        "Abort %ErrorText%",
    ]
    deinstall = doc.section("Set:DeInstallationError")
    assert deinstall is not None
    assert _body(deinstall) == [
        "-ErrorLogMsg %ErrorLogMessage%",
        "-Abort %ErrorText%",
    ]

    # The appended block is separated by exactly one blank line; like prettify,
    # the separator belongs to the previous section's lines.
    deinstall_set = doc.section("Set:Deinstallation")
    assert deinstall_set is not None
    assert _is_blank(deinstall_set.lines[-1])

    # A repair must never turn into a forced reboot -> [RebootRequired] stays
    # empty, and non-handler stubs stay behavior-neutral (empty) as well.
    reboot = doc.section("RebootRequired")
    assert reboot is not None and reboot.lines == []
    shell = doc.section("Shell:Product")
    assert shell is not None and shell.lines == []


def test_repaired_output_is_already_prettified() -> None:
    """A repair emits canonical text – a Prettify pass must not change it.

    Both appenders (repair and the editor quick fix) keep the one-blank-line
    section gap, so the visible result matches a reference package right away.
    """
    doc = _doc(_MINIMAL_SAMPLE)
    add_missing_standard_sections(doc)
    text = serialize_document(doc)
    assert "\r\n\r\n[VarDefInfo]" in text  # gap before the appended block
    assert prettify_text(text) == text


def test_canonical_deinstall_ref_is_appended_last() -> None:
    """M-2: a repaired package gets the template's ref order. Uninstall runs
    bottom-up, so ``#Set:Deinstallation`` must be the last [Product] call."""
    from empirum_core.setupinf_contract import PRODUCT_REFS

    doc = _doc(
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n"
        "[Application]\r\nProductName=X\r\n\r\n"
        "[Product]\r\n#Set:Product, DONTDELETE\r\n\r\n"
        "[Set:Product]\r\nEcho ok\r\n\r\n"
        "[Set:Deinstallation]\r\nEcho bye\r\n"
    )
    repair = add_missing_standard_sections(doc)
    assert repair.added_refs[-1] == "#Set:Deinstallation, DELETE"
    expected = [ref for _target, ref in PRODUCT_REFS]
    product = doc.section("Product")
    assert product is not None
    texts = [getattr(n, "text", "") for n in product.lines]
    assert [line for line in texts if line in expected] == expected


# -- service (disk repair) ---------------------------------------------------


def _make_package(root: Path) -> Path:
    pkg = root / "B_Migrated_1.0"
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Files").mkdir(parents=True)
    (pkg / "Install" / "Setup.inf").write_text(_CONVERTED_SAMPLE, encoding="cp1252")
    (pkg / "Files" / "payload.exe").write_bytes(b"MZ")
    return pkg


def test_service_repair_preserves_encoding_and_backs_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from empirum_services.package_readiness import (
        check_package_readiness,
        default_repair_backup_dir,
        repair_missing_standard_sections,
    )

    # Hermetic: M-3 moves the WAL backup to the user profile.
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    pkg = _make_package(tmp_path)
    inf = pkg / "Install" / "Setup.inf"
    before = inf.read_bytes()

    result = repair_missing_standard_sections(pkg)
    assert set(result.added_sections) == {
        "Reg:OnUninstallProduct",
        "Reg:Product",
        "Ini:Product",
        "Security:Product",
        "Shell:Product",
    }
    assert result.backup_path is not None and result.backup_path.is_file()
    assert result.backup_path.read_bytes() == before
    # M-3: backup lives outside the package -> nothing extra gets deployed.
    assert result.backup_path.parent == default_repair_backup_dir(pkg)
    assert not list(pkg.rglob(".emp_packagex3_bak"))

    after = inf.read_bytes()
    assert not after.startswith(b"\xef\xbb\xbf")  # cp1252 stays cp1252, no BOM
    assert "für" not in after.decode("cp1252") or "Installation für" in after.decode(
        "cp1252"
    )
    assert b"\r\n" in after

    report = check_package_readiness(pkg)
    assert not any(d.code == "VAL-012" for d in report.diagnostics)
    # The slim sample has no [Application] identity -> VAL-013 errors remain
    # (expected); VAL-012 specifically is resolved by the repair.
    remaining_errors = [
        d.code for d in report.diagnostics if d.severity.value == "error"
    ]
    assert set(remaining_errors) <= {"VAL-013"}


def test_service_repair_idempotent_on_second_call(tmp_path: Path) -> None:
    from empirum_services.package_readiness import repair_missing_standard_sections

    pkg = _make_package(tmp_path)
    repair_missing_standard_sections(pkg)
    second = repair_missing_standard_sections(pkg)
    assert second.added_sections == [] and second.added_refs == []
    assert second.backup_path is None  # nothing written -> no backup


def test_service_repair_strips_utf8_bom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from empirum_services.package_readiness import (
        check_package_readiness,
        repair_missing_standard_sections,
    )

    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    pkg = tmp_path / "BOM_Pkg"
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Files").mkdir(parents=True)
    inf = pkg / "Install" / "Setup.inf"
    inf.write_bytes(b"\xef\xbb\xbf" + _CONVERTED_SAMPLE.encode("utf-8"))

    # Before repair: readiness reports PKG-009 FAIL and VAL-030
    report_before = check_package_readiness(pkg)
    assert any(item.code == "PKG-009" for item in report_before.items)

    result = repair_missing_standard_sections(pkg)
    assert result.bom_stripped is True
    after = inf.read_bytes()
    assert not after.startswith(b"\xef\xbb\xbf")
    assert after.startswith(b"[SetupInfo]")

    # After repair: PKG-009 is resolved
    report_after = check_package_readiness(pkg)
    assert not any(item.code == "PKG-009" for item in report_after.items)


def test_readiness_flags_invalid_cp1252_bytes(tmp_path: Path) -> None:
    from empirum_services.package_readiness import check_package_readiness

    pkg = tmp_path / "BadCP1252_Pkg"
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Files").mkdir(parents=True)
    inf = pkg / "Install" / "Setup.inf"
    # 0x81 is undefined in CP1252
    inf.write_bytes(b"[SetupInfo]\r\nProductName=Test\x81\r\n")
    report = check_package_readiness(pkg)
    assert any(item.code == "PKG-011" for item in report.items)


# -- UI wiring ----------------------------------------------------------------


def test_deploy_dialog_offers_repair_on_val012(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QMessageBox

    from emp_packagex3.ui.package_store_dialog import PackageStoreDeployDialog

    app = QApplication.instance() or QApplication([])
    _ = app

    pkg = _make_package(tmp_path)

    class _StubBoxes:
        StandardButton = QMessageBox.StandardButton

        @staticmethod
        def question(*args: object, **kwargs: object) -> QMessageBox.StandardButton:
            return QMessageBox.StandardButton.Yes

        @staticmethod
        def warning(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def information(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def critical(*args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("emp_packagex3.ui.package_store_dialog.QMessageBox", _StubBoxes)

    dlg = PackageStoreDeployDialog(package_dir=pkg, store_root=r"\\srv\Store$")
    assert dlg._repair_btn.isHidden()  # not checked yet

    dlg._run_readiness()  # fails with VAL-012 -> button becomes visible
    assert not dlg._repair_btn.isHidden()

    dlg._repair_btn.click()  # confirm stubbed to Yes -> repairs disk
    assert (pkg / "Install" / "Setup.inf").read_text(encoding="cp1252").count(
        "[Reg:Product]"
    ) == 1
    assert dlg._repair_btn.isHidden()  # re-check: no more VAL-012


def test_editor_action_adds_sections(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app

    class _StubBoxes:
        @staticmethod
        def information(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def warning(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def critical(*args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("emp_packagex3.app.QMessageBox", _StubBoxes)

    window = MainWindow()
    window.load_file_at_startup(_make_package(tmp_path) / "Install" / "Setup.inf")
    window.run_skeleton_repair()
    text = window._editor.toPlainText()
    assert "[Reg:Product]" in text
    assert "#Reg:Product, DONTDELETE" in text


def _stub_boxes(monkeypatch: pytest.MonkeyPatch) -> None:
    class _StubBoxes:
        @staticmethod
        def information(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def warning(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def critical(*args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("emp_packagex3.app.QMessageBox", _StubBoxes)


def _handler_diag(window) -> object:
    return next(
        d
        for d in window._diags
        if any(f.section_name == "Set:DeInstallationError" for f in d.quick_fixes)
    )


def test_editor_quickfix_inserts_missing_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M-4: Ctrl+. applies the VAL-012 fix (was dead code before)."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_boxes(monkeypatch)

    window = MainWindow()
    window.load_file_at_startup(_make_package(tmp_path) / "Install" / "Setup.inf")
    assert any(d.code == "VAL-012" for d in window._diags)
    window.apply_first_quickfix()
    text = window._editor.toPlainText()
    # First missing section in standard order for the converted sample.
    assert "[Reg:OnUninstallProduct]" in text
    assert not any(d.code == "VAL-012" and "[Reg:OnUninstallProduct]" in d.message
                   for d in window._diags)


def test_editor_quickfix_inserts_handler_with_canonical_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M-4: applying the handler fix brings the Abort body, not an empty stub."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_boxes(monkeypatch)

    inf = tmp_path / "Install" / "Setup.inf"
    inf.parent.mkdir(parents=True)
    inf.write_text(_MINIMAL_SAMPLE, encoding="cp1252")

    window = MainWindow()
    window.load_file_at_startup(inf)
    window._apply_insert_section_fix_for(_handler_diag(window))
    text = window._editor.toPlainText()
    assert "[Set:DeInstallationError]" in text
    assert "-ErrorLogMsg %ErrorLogMessage%" in text
    assert "-Abort %ErrorText%" in text
    assert not any(
        f.section_name == "Set:DeInstallationError"
        for d in window._diags
        for f in d.quick_fixes
    )


def test_editor_quickfix_section_insert_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_boxes(monkeypatch)

    window = MainWindow()
    window.load_file_at_startup(_make_package(tmp_path) / "Install" / "Setup.inf")
    diag = next(d for d in window._diags if d.code == "VAL-012")
    fix = next(f for f in diag.quick_fixes if f.note == "insert_section")
    assert window._apply_section_fix(fix) is True
    once = window._editor.toPlainText()
    assert window._apply_section_fix(fix) is False  # already present
    assert window._editor.toPlainText() == once


# A sample the prettifier really rewrites (trailing spaces) – keeps the F-3
# assertion below non-vacuous.
_PRETTY_NEEDED = "[SetupInfo]\r\nMethod=MSI   \r\n\r\n[Set:Product]\r\nEcho ok\r\n"


def test_editor_quickfix_marks_document_dirty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-2: an applied fix is an unsaved change (``*`` + save prompt on close)."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_boxes(monkeypatch)

    window = MainWindow()
    window.load_file_at_startup(_make_package(tmp_path) / "Install" / "Setup.inf")
    assert window._dirty is False
    window.apply_first_quickfix()
    assert window._dirty is True
    assert window.isWindowModified()


def test_editor_ctx_menu_quickfix_keeps_typed_edit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-1: the context-menu path must flush an edit still inside the debounce."""
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QTextCursor
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_boxes(monkeypatch)

    window = MainWindow()
    inf = tmp_path / "Install" / "Setup.inf"
    inf.parent.mkdir(parents=True)
    inf.write_bytes(_MINIMAL_SAMPLE.encode("cp1252"))  # handlers are missing here
    window.load_file_at_startup(inf)
    diag = _handler_diag(window)

    # Typed a moment ago: the debounced sync/lint has not run yet.
    window._editor.moveCursor(QTextCursor.MoveOperation.End)
    window._editor.insertPlainText("\r\n;TYPED\r\n")
    assert window._lint_timer.isActive()
    assert window._dirty is False

    window._apply_insert_section_fix_for(diag)

    text = window._editor.toPlainText()
    assert ";TYPED" in text  # lost without the flush (F-1)
    assert text.count("[Set:DeInstallationError]") == 1
    assert window._dirty is True


def test_editor_repair_marks_dirty_but_noop_prettify_does_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-3: only a real rewrite raises ``*`` – F7/save stay silent."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_boxes(monkeypatch)

    window = MainWindow()
    window.load_file_at_startup(_make_package(tmp_path) / "Install" / "Setup.inf")

    # A flush without an edit (F7 „Prüfen“) must not fake unsaved changes.
    window.run_lint()
    assert window._dirty is False
    assert not window.isWindowModified()

    window.run_skeleton_repair()
    assert "[Reg:Product]" in window._editor.toPlainText()
    assert window._dirty is True

    # Prettify only raises the flag when it really rewrites the document.
    clean = MainWindow()
    inf = tmp_path / "Pretty" / "Install" / "Setup.inf"
    inf.parent.mkdir(parents=True)
    inf.write_bytes(_PRETTY_NEEDED.encode("cp1252"))
    clean.load_file_at_startup(inf)
    assert clean._dirty is False
    clean.run_prettify()
    assert clean._sync.text != _PRETTY_NEEDED  # the sample is un-pretty
    assert clean._dirty is True
    assert clean.isWindowModified()

    again = MainWindow()
    inf.write_bytes(clean._sync.text.encode("cp1252"))  # store the pretty result
    again.load_file_at_startup(inf)  # now already pretty -> no-op
    again.run_prettify()
    assert again._dirty is False
