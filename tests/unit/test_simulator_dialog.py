"""Simulator dialog tests: export format, tree, filter, jump, wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from empirum_core.parser.lexer import lex_text
from empirum_core.simulator import SimMode

_SAMPLE = (
    "[Application]\r\nProductName=X\r\n\r\n"
    "[Product]\r\n"
    "#Set:Install, DONTDELETE\r\n"
    "#Set:Deinstallation, DELETE\r\n"
    "\r\n"
    "[Set:Install]\r\n"
    "AddMeter -1\r\n"
    'CallHidden setup.exe /S\r\n'
    'If %ErrorLevel% == "0" Then "OK" EndIf\r\n'
    "\r\n"
    "[Set:Deinstallation]\r\n"
    '-Del "%App%\\file.dat"\r\n'
    "\r\n"
)


def _doc():
    return lex_text(_SAMPLE)


# -- pure export --------------------------------------------------------------


def test_format_simulator_report_structure() -> None:
    from emp_packagex3.ui.simulator_dialog import format_simulator_report
    from empirum_core.simulator import simulate

    report = simulate(_doc(), SimMode.INSTALL)
    text = format_simulator_report(report, package=r"C:\pkg", app_version="9.9.9")
    assert text.startswith("EMP-PackageX3 Simulator-Report")
    assert "Modus: Installation" in text
    assert "App-Version: 9.9.9" in text
    assert "[Set:Install]" in text
    assert "CallHidden" in text
    assert text.endswith("\n")


def test_format_simulator_report_includes_gaps_and_state() -> None:
    from emp_packagex3.ui.simulator_dialog import format_simulator_report
    from empirum_core.simulator import simulate

    # Install mode: setup.exe has no uninstall counterpart -> gap reported
    report = simulate(_doc(), SimMode.INSTALL)
    text = format_simulator_report(report)
    assert "--- Lücken ---" in text or "--- Luecken ---" in text
    assert "Aktionen:" in text


def test_format_simulator_report_empty() -> None:
    from emp_packagex3.ui.simulator_dialog import format_simulator_report
    from empirum_core.simulator import simulate

    empty = lex_text("[Application]\r\nProductName=X\r\n")
    report = simulate(empty, SimMode.INSTALL)
    text = format_simulator_report(report)
    assert "Aktionen: 0" in text


# -- Qt dialog ----------------------------------------------------------------


def test_simulator_dialog_tree_and_jump(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.simulator_dialog import SimulatorDialog

    app = QApplication.instance() or QApplication([])
    _ = app

    jumped: list[int] = []
    dlg = SimulatorDialog(
        document=_doc(),
        mode=SimMode.INSTALL,
        on_jump=jumped.append,
        theme="light",
    )
    assert not dlg.isModal()
    assert "Installation" in dlg.windowTitle()

    # Section groups in walk order with all actions (no 40-cap)
    top_texts = [
        dlg._tree.topLevelItem(i).text(0) for i in range(dlg._tree.topLevelItemCount())
    ]
    assert "[Product]" in top_texts
    assert "[Set:Install]" in top_texts

    # Jump: activate a leaf with a line number
    for i in range(dlg._tree.topLevelItemCount()):
        group = dlg._tree.topLevelItem(i)
        if group.text(0) == "[Set:Install]":
            leaf = group.child(1)  # CallHidden row
            line = leaf.data(0, 0x0100)
            assert isinstance(line, int) and line > 0
            dlg._on_item_activated(leaf, 0)
            assert jumped == [line]
            break
    else:  # pragma: no cover
        pytest.fail("Set:Install group not found")


def test_simulator_dialog_mode_toggle_and_gaps() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.simulator_dialog import SimulatorDialog

    app = QApplication.instance() or QApplication([])
    _ = app

    dlg = SimulatorDialog(
        document=_doc(), mode=SimMode.INSTALL, on_jump=lambda line: None, theme="dark"
    )
    assert "#1b2429" in dlg.styleSheet()  # themed
    # OP-008: install skips the DELETE ref (#Set:Deinstallation) -> 5 actions
    assert "5 Aktionen" in dlg._stats_label.text()

    dlg._btn_deinstall.click()  # re-simulates in uninstall mode
    assert "Deinstallation" in dlg.windowTitle()
    assert "1 Aktionen" in dlg._stats_label.text()

    # Filter hides non-matching children
    dlg._filter.setText("Del")
    visible = []
    for i in range(dlg._tree.topLevelItemCount()):
        group = dlg._tree.topLevelItem(i)
        for c in range(group.childCount()):
            if not group.child(c).isHidden():
                visible.append(group.child(c).text(1))
    assert visible and all("Del" in v for v in visible)


def test_simulator_dialog_missing_entry_shows_gaps() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.simulator_dialog import SimulatorDialog

    app = QApplication.instance() or QApplication([])
    _ = app

    doc = lex_text("[Application]\r\nProductName=X\r\n")
    dlg = SimulatorDialog(
        document=doc, mode=SimMode.INSTALL, on_jump=lambda line: None, theme="light"
    )
    assert dlg._gap_banner.text()  # entry section missing -> banner
    top_texts = [
        dlg._tree.topLevelItem(i).text(0) for i in range(dlg._tree.topLevelItemCount())
    ]
    assert any("Lücken" in t for t in top_texts)


# -- app wiring ---------------------------------------------------------------


def test_run_simulator_opens_nonmodal_and_reuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow
    from empirum_core.simulator import SimMode as _SimMode

    app = QApplication.instance() or QApplication([])
    _ = app

    window = MainWindow()
    window.run_simulator(_SimMode.INSTALL)
    dlg1 = window._sim_dialog
    assert dlg1 is not None and dlg1.isVisible()
    assert dlg1.isModal() is False

    window.run_simulator(_SimMode.UNINSTALL)  # reuse, not a second window
    dlg2 = window._sim_dialog
    assert dlg2 is dlg1
    assert "Deinstallation" in dlg2.windowTitle()
    dlg1.close()
