"""Editor find bar tests: widget behavior, find logic, shortcuts wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

_SAMPLE = (
    "[SetupInfo]\r\n"
    "Method=MSI\r\n"
    "Description=Demo\r\n"
    "\r\n"
    "[Set:Product]\r\n"
    "CallHidden setup.exe /S\r\n"
    "CallHidden msiexec /I a.msi\r\n"
    "Echo callhidden lowercase\r\n"
)


def _window(tmp_path: Path):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    inf = tmp_path / "Setup.inf"
    inf.write_bytes(_SAMPLE.replace("\r\n", "\r\n").encode("cp1252"))
    window = MainWindow()
    window.load_file_at_startup(inf)
    return window


def test_find_bar_open_and_signals() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.find_bar import FindBar

    app = QApplication.instance() or QApplication([])
    _ = app

    bar = FindBar()
    received: list[tuple[str, bool, bool]] = []
    bar.search_requested.connect(lambda t, c, b: received.append((t, c, b)))

    assert bar.isHidden()
    bar.open_with("CallHidden")
    assert not bar.isHidden()
    assert bar.term() == "CallHidden"
    assert received and received[-1] == ("CallHidden", False, False)

    bar._case.setChecked(True)
    assert received[-1] == ("CallHidden", True, False)

    bar.search(backward=True)
    assert received[-1] == ("CallHidden", True, True)

    bar.dismiss()
    assert bar.isHidden()


def test_find_finds_and_selects(tmp_path: Path) -> None:
    window = _window(tmp_path)
    window.open_find()
    assert window._find_bar.is_open()

    window._find_bar.set_term("CallHidden")
    # M-5: live typing is debounced – an explicit search is the immediate path.
    window._find_bar.search()
    assert window._editor.textCursor().selectedText() == "CallHidden"

    # forward search continues after the current selection ...
    window._find("CallHidden", False, False)
    assert window._editor.textCursor().selectedText() == "CallHidden"
    # ... also matches the lowercase occurrence (case-insensitive) ...
    window._find("CallHidden", False, False)
    assert window._editor.textCursor().selectedText() == "callhidden"
    # ... and wraps back to the first hit
    window._find("CallHidden", False, False)
    assert window._editor.textCursor().selectedText() == "CallHidden"


def test_find_wraps_around(tmp_path: Path) -> None:
    window = _window(tmp_path)
    # jump to end of document
    cursor = window._editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    window._editor.setTextCursor(cursor)

    assert window._find("SetupInfo", case_sensitive=False, backward=False) is True
    selected = window._editor.textCursor().selectedText()
    assert selected == "SetupInfo"  # wrapped to the first occurrence


def test_find_case_sensitivity_and_status(tmp_path: Path) -> None:
    window = _window(tmp_path)

    # sample has lowercase 'callhidden' in the Echo line only
    assert window._find("callhidden", case_sensitive=True, backward=False) is True
    assert window._count_matches("callhidden", case_sensitive=True) == 1
    assert window._count_matches("CallHidden", case_sensitive=True) == 2
    assert window._count_matches("callhidden", case_sensitive=False) == 3

    window._on_search_requested("nichtda", False, False)
    assert "nicht gefunden" in window._find_bar._status.text()

    window._on_search_requested("CallHidden", False, False)
    assert "3 Treffer" in window._find_bar._status.text()


def test_find_next_action_reuses_bar(tmp_path: Path) -> None:
    window = _window(tmp_path)
    window.open_find()
    window._find_bar.set_term("CallHidden")
    window._find_next_action()  # uses bar term, no reopen needed
    assert window._editor.textCursor().selectedText() == "CallHidden"

    # Esc closes via _close -> editor regains focus callback
    window._find_bar.dismiss()
    assert window._find_bar.isHidden()

    # M-5: F3 with a closed bar reuses the last term instead of reopening an
    # empty search bar.
    window._find_next_action()
    assert window._find_bar.isHidden()
    assert window._editor.textCursor().selectedText() == "CallHidden"


def test_f3_on_closed_bar_reports_result_in_status_bar(tmp_path: Path) -> None:
    """F3 on a closed bar reuses the term – and says what it found."""
    window = _window(tmp_path)
    window.open_find()
    window._find_bar.set_term("CallHidden")
    window._find_bar.search()
    window._find_bar.dismiss()
    window.statusBar().clearMessage()

    window._find_next_action()
    assert window._find_bar.isHidden()  # no empty bar popping up
    message = window.statusBar().currentMessage()
    assert "CallHidden" in message
    assert "3 Treffer" in message


def test_live_search_is_debounced() -> None:
    """M-5: typing must not run a full-document search on every keystroke."""
    pytest.importorskip("PySide6")
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.find_bar import FindBar

    app = QApplication.instance() or QApplication([])
    _ = app

    bar = FindBar()
    received: list[tuple[str, bool, bool]] = []
    bar.search_requested.connect(lambda t, c, b: received.append((t, c, b)))

    bar.open_with("Call")
    assert received == [("Call", False, False)]  # opening searches exactly once
    bar.set_term("CallH")  # live typing -> deferred
    assert received == [("Call", False, False)]
    QTest.qWait(250)
    assert received.count(("CallH", False, False)) == 1

    # Enter flushes immediately and cancels the pending debounce
    bar.set_term("CallHidden")
    bar._term.returnPressed.emit()
    assert received[-1] == ("CallHidden", False, False)
    QTest.qWait(250)
    assert received.count(("CallHidden", False, False)) == 1

    # A closed bar never emits afterwards
    bar.set_term("Late")
    bar.dismiss()
    QTest.qWait(250)
    assert all(term != "Late" for term, _c, _b in received)


def test_find_wrap_hint_in_status(tmp_path: Path) -> None:
    window = _window(tmp_path)
    window.open_find()
    cursor = window._editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    window._editor.setTextCursor(cursor)

    window._on_search_requested("SetupInfo", False, False)
    status = window._find_bar._status.text()
    assert "1 Treffer" in status  # single set_status: count survives
    assert "umgebrochen" in status  # wrap-around is reported


def test_escape_closes_find_bar(tmp_path: Path) -> None:
    """M-5: Esc closes the bar from the editor and from the window itself."""
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    window = _window(tmp_path)
    esc = QKeyEvent(
        QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier
    )

    window.open_find()
    QApplication.sendEvent(window._editor, esc)  # focus is in the editor
    assert window._find_bar.isHidden()

    window.open_find()
    QApplication.sendEvent(window, esc)  # anywhere else in the window
    assert window._find_bar.isHidden()
