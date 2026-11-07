"""Crash hook and editor hover help regressions."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _restore_excepthook():
    """Keep sys.excepthook pristine across tests."""
    saved = sys.excepthook
    yield
    sys.excepthook = saved


def test_crash_hook_logs_chains_and_offers(monkeypatch: pytest.MonkeyPatch) -> None:
    from emp_packagex3 import crash_hook

    offered: list[BaseException] = []
    chained: list[tuple] = []
    monkeypatch.setattr(crash_hook, "_offer_feedback", offered.append)
    monkeypatch.setattr(sys, "excepthook", lambda *args: chained.append(args))

    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    collector = _Collector(level=logging.ERROR)
    logger = logging.getLogger("emp_packagex3.crash")
    logger.addHandler(collector)
    try:
        crash_hook.install_crash_hook()
        assert sys.excepthook is not None
        try:
            raise ValueError("beta boom")
        except ValueError:
            sys.excepthook(*sys.exc_info())
    finally:
        logger.removeHandler(collector)

    assert offered and isinstance(offered[0], ValueError)
    assert len(chained) == 1  # previous hook chained
    assert any(r.levelno >= logging.CRITICAL for r in records)
    assert any("beta boom" in r.getMessage() for r in records)


def test_crash_hook_busy_flag_prevents_recursion(monkeypatch: pytest.MonkeyPatch) -> None:
    from emp_packagex3 import crash_hook

    crash_hook._offer_busy = True  # simulate an offer already in progress
    try:
        crash_hook._offer_feedback(ValueError("second"))  # must return silently
    finally:
        crash_hook._offer_busy = False


def test_create_feedback_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from emp_packagex3 import crash_hook
    from emp_packagex3.settings import AppSettings

    monkeypatch.setattr(
        "emp_packagex3.settings.load_settings",
        lambda *a, **k: AppSettings(log_dir=str(tmp_path / "logs")),
    )
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "emp-packagex3.log").write_text("log line\n", encoding="utf-8")

    dest = crash_hook.create_feedback_archive()
    assert dest.is_file()
    assert dest.name.startswith("EMP-PackageX3-Crash-")
    assert dest.parent == Path.home() / "Documents"


# -- editor hover (issue: tooltip flicker between keyword and general tip) ----


def test_hover_help_lookup() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app

    window = MainWindow()

    section_html = window._hover_help_for("[Reg:Product]", "Reg")
    assert section_html is not None and "<b>[Reg:&lt;Name&gt;]" in section_html or "Reg:" in (
        section_html or ""
    )

    command_html = window._hover_help_for("CallHidden setup.exe /S", "CallHidden")
    assert command_html is not None and "CallHidden" in command_html
    assert "Uninstall:" in command_html

    assert window._hover_help_for("Echo hallo", "hallo") is None
    assert window._hover_help_for("", "") is None


def test_hover_state_transitions_suppress_and_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app

    inf = tmp_path / "Setup.inf"
    inf.write_bytes(b"[SetupInfo]\r\nProductName=Demo\r\n")
    window = MainWindow()
    general_tip = window._editor.toolTip()
    assert general_tip  # learning tip bound to the editor

    html = window._hover_help_for("CallHidden setup.exe /S", "CallHidden")
    window._hover_state = html
    window._editor.setToolTip("")  # suppressed over keyword (as the handler does)

    # Leaving the keyword restores the general tip (handler path)
    window._hover_state = None
    window._editor.setToolTip(
        __import__("emp_packagex3.ui.tooltip_mode", fromlist=["tip_text"]).tip_text(
            window._editor
        )
    )
    assert window._editor.toolTip() == general_tip
