"""Tooltip-mode helpers."""

from __future__ import annotations

import pytest

from emp_packagex3.ui.tooltip_mode import FIELD_TIPS, MENU_TIPS, tip_text


def test_menu_catalog_covers_core_actions() -> None:
    for key in (
        "file.open",
        "tools.wizard",
        "tools.packagestore",
        "help.tooltip_mode",
        "help.command_reference",
        "edit.prettify",
    ):
        assert key in MENU_TIPS
        assert len(MENU_TIPS[key]) > 10
    assert "settings.tooltip_mode" in FIELD_TIPS


def test_fast_wake_delay_constant() -> None:
    from emp_packagex3.ui.tooltip_mode import TIP_WAKE_MS

    assert TIP_WAKE_MS <= 200


def test_bind_and_read_tip() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QApplication, QWidget

    from emp_packagex3.ui.tooltip_mode import bind_action, bind_tip

    app = QApplication.instance() or QApplication([])
    _ = app
    widget = QWidget()
    bind_tip(widget, "Hello admin")
    assert tip_text(widget) == "Hello admin"
    act = QAction("X")
    bind_action(act, "file.open")
    assert tip_text(act) == MENU_TIPS["file.open"]


def test_settings_dialog_binds_all_field_tips() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QLabel,
        QLineEdit,
        QTextEdit,
        QWidget,
    )

    from emp_packagex3.settings import AppSettings
    from emp_packagex3.ui.settings_dialog import SettingsDialog
    from emp_packagex3.ui.tooltip_mode import TIP_PROP, apply_tooltip_mode

    app = QApplication.instance() or QApplication([])
    _ = app
    dlg = SettingsDialog(AppSettings(tooltip_mode=True))
    apply_tooltip_mode(dlg, True)
    tipped = [w for w in dlg.findChildren(QWidget) if w.property(TIP_PROP)]
    assert len(tipped) >= 14
    inputs = (
        list(dlg.findChildren(QLineEdit))
        + list(dlg.findChildren(QTextEdit))
        + list(dlg.findChildren(QCheckBox))
        + list(dlg.findChildren(QComboBox))
    )
    for w in inputs:
        assert w.toolTip(), f"missing tooltip on {type(w).__name__}"
    labeled = [w for w in dlg.findChildren(QLabel) if w.property(TIP_PROP)]
    assert len(labeled) >= 6
