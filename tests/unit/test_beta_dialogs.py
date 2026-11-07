"""Dialog regressions: logging reconfigure, error mask prefill, encoding BOM."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest


def test_setup_logging_switches_log_dir(tmp_path: Path) -> None:
    from emp_packagex3.logging_setup import setup_logging

    logger = logging.getLogger("emp_packagex3")
    first = setup_logging(debug=False, log_dir=tmp_path / "one")
    second = setup_logging(debug=False, log_dir=tmp_path / "two")
    assert first == tmp_path / "one"
    assert second == tmp_path / "two"
    file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1
    assert Path(file_handlers[0].baseFilename).parent == tmp_path / "two"
    assert (tmp_path / "two" / "emp-packagex3.log").is_file()


def test_error_reboot_prefills_and_writes_standard_sections() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.error_reboot import ErrorRebootDialog
    from empirum_core.parser.lexer import lex_text

    app = QApplication.instance() or QApplication([])
    _ = app
    doc = lex_text(
        "[Application]\r\nReboot=0\r\n\r\n"
        "[Set:InstallationError]\r\n"
        "ErrorLogMsg Eigene Meldung\r\n"
        "Abort Kundentext\r\n"
    )
    dlg = ErrorRebootDialog(doc)
    # Reboot=0 stays unchecked; command-style texts are prefilled
    assert dlg._reboot.isChecked() is False
    assert dlg._abort.text() == "Kundentext"
    assert dlg._err.text() == "Eigene Meldung"

    dlg._abort.setText("Neuer Text")
    result = dlg.apply()
    install_err = result.section("Set:InstallationError")
    assert install_err is not None
    lines = [n.text for n in install_err.lines if hasattr(n, "text")]
    assert "Abort Neuer Text" in lines
    assert "ErrorLogMsg Eigene Meldung" in lines
    deinstall_err = result.section("Set:DeInstallationError")
    assert deinstall_err is not None
    deLines = [n.text for n in deinstall_err.lines if hasattr(n, "text")]
    assert "-Abort Neuer Text" in deLines
    assert "-ErrorLogMsg Eigene Meldung" in deLines
    # Legacy KV error sections are not generated anymore
    assert result.section("Error_Install") is None
    assert result.section("Error_Uninstall") is None


def test_encoding_dialog_preserves_bom_choice() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.encoding_dialog import EncodingChoiceDialog
    from empirum_core.parser.encoding import DetectedEncoding

    app = QApplication.instance() or QApplication([])
    _ = app
    dlg = EncodingChoiceDialog(DetectedEncoding(name="utf-8", has_bom=True, ambiguous=True))
    assert dlg.chosen().has_bom is True  # BOM roundtrip preserved by default
    dlg2 = EncodingChoiceDialog(DetectedEncoding(name="utf-8", has_bom=False, ambiguous=True))
    assert dlg2.chosen().name == "utf-8"
    assert dlg2.chosen().has_bom is False


def test_settings_and_wizard_dialogs_follow_dark_theme() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.settings import AppSettings
    from emp_packagex3.ui.settings_dialog import SettingsDialog
    from emp_packagex3.wizard.creator import CreatorWizard

    app = QApplication.instance() or QApplication([])
    _ = app
    settings = AppSettings(theme="dark")
    dlg = SettingsDialog(settings)
    assert "#1b2429" in dlg.styleSheet()  # dark dialog background
    light = SettingsDialog(AppSettings(theme="light"))
    assert "#f7f9fa" in light.styleSheet()

    wiz = CreatorWizard(theme="dark")
    assert "#1b2429" in wiz.styleSheet()
