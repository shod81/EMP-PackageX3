"""Global crash hook: unhandled exceptions land in the log + feedback offer.

Without this, an unhandled exception in the windowed EXE (no console,
PySide6 routes slot errors to sys.excepthook) disappears silently - the
single worst case for beta feedback. The hook logs the full traceback,
offers the feedback ZIP and then chains to the previous excepthook.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from emp_packagex3.logging_setup import get_logger

log = get_logger("emp_packagex3.crash")

_offer_busy = False


def install_crash_hook() -> None:
    """Route unhandled exceptions to the app log and offer a feedback ZIP."""
    previous_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb) -> None:  # type: ignore[no-untyped-def]
        log.critical(
            "Unbehandelte Ausnahme:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
        _offer_feedback(exc_value)
        # Chain to the previous hook so console development stays visible.
        previous_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


def _offer_feedback(exc: BaseException) -> None:
    """Offer the feedback ZIP once per crash; never raise from the hook."""
    global _offer_busy
    if _offer_busy:
        return
    _offer_busy = True
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        if QApplication.instance() is None:
            return  # headless context (tests/CLI) - logging already happened
        answer = QMessageBox.question(
            None,
            "EMP-PackageX3 – unerwarteter Fehler",
            "Es ist ein unerwarteter Fehler aufgetreten:\n"
            f"{type(exc).__name__}: {exc}\n\n"
            "Details wurden ins Log geschrieben.\n\n"
            "Jetzt ein Feedback-Paket (Logs) für den Support erstellen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        path = create_feedback_archive()
        QMessageBox.information(
            None,
            "Feedback-Paket erstellt",
            f"ZIP erstellt:\n{path}\n\nBitte als GitHub-Issue anhaengen:\nhttps://github.com/shod81/EMP-PackageX3/issues",
        )
    except Exception:  # noqa: BLE001 - the hook itself must never crash
        log.exception("feedback offer after crash failed")
    finally:
        _offer_busy = False


def create_feedback_archive() -> Path:
    """Create the feedback ZIP without UI (Documents, timestamped name)."""
    from datetime import UTC, datetime
    from pathlib import Path

    from emp_packagex3 import __version__
    from emp_packagex3.feedback import create_feedback_zip
    from emp_packagex3.logging_setup import default_log_dir
    from emp_packagex3.settings import load_settings

    settings = load_settings()
    log_dir = (
        Path(settings.log_dir) if settings.log_dir.strip() else default_log_dir()
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = Path.home() / "Documents" / f"EMP-PackageX3-Crash-{__version__}-{stamp}.zip"
    return create_feedback_zip(dest, log_dir=log_dir)
