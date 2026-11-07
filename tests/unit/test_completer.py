"""Completer inserts the selected completion into the editor (review S8a)."""

from __future__ import annotations

import pytest


def test_completer_word_list_is_sane() -> None:
    pytest.importorskip("PySide6")
    from emp_packagex3.ui.completer import SECTIONS, SET_TARGETS
    from empirum_core.setupinf_contract import STANDARD_SECTIONS, USER_PART_SECTIONS

    assert "#Set:SetupInfo" not in SET_TARGETS
    assert "#Set:Product" in SET_TARGETS
    assert "#Set:Client, CLIENT" in SET_TARGETS  # user part
    assert "[Product]" in [f"[{s}]" for s in SECTIONS]
    # M-1: the popup offers exactly the standard catalog (plus the
    # user-part section), no legacy names.
    assert set(SECTIONS) == set(STANDARD_SECTIONS) | set(USER_PART_SECTIONS)
    for legacy in ("Set_Install", "Set_Uninstall", "Error_Install", "Error_Uninstall"):
        assert legacy not in SECTIONS


def test_completer_undocumented_gating() -> None:
    pytest.importorskip("PySide6")
    from emp_packagex3.ui.completer import completer_words

    off = completer_words(undocumented=False)
    assert "CollapseEnv" not in off
    assert "%DstDir%" not in off
    # Documented class-2 extension commands ARE offered without the flag
    assert "WaitUntilRegKeyExists" in off
    assert "DoesPathExist" in off
    assert "SHAREDDLL" in off  # copy flags offered

    on = completer_words(undocumented=True)
    assert "CollapseEnv" in on
    assert "Extract" in on
    assert "RenDir" in on
    assert "BlockInput" in on
    assert "%DstDir%" in on


def test_completer_refresh_swaps_words() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QStringListModel
    from PySide6.QtWidgets import QApplication, QPlainTextEdit

    from emp_packagex3.ui.completer import attach_completer, refresh_completer

    app = QApplication.instance() or QApplication([])
    _ = app
    editor = QPlainTextEdit()
    completer = attach_completer(editor, undocumented=False)
    model = completer.model()
    assert isinstance(model, QStringListModel)
    assert "CollapseEnv" not in model.stringList()

    refresh_completer(completer, undocumented=True)
    assert "CollapseEnv" in model.stringList()


def test_completer_activated_inserts_completion() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QTextCursor
    from PySide6.QtWidgets import QApplication, QPlainTextEdit

    from emp_packagex3.ui.completer import attach_completer

    app = QApplication.instance() or QApplication([])
    _ = app
    editor = QPlainTextEdit()
    completer = attach_completer(editor)
    editor.setPlainText("Cal")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    completer.setCompletionPrefix("Cal")
    completer.activated[str].emit("CallHidden")  # type: ignore[attr-defined]
    assert editor.toPlainText() == "CallHidden"


def test_completer_context_set_prefix() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QTextCursor
    from PySide6.QtWidgets import QApplication, QPlainTextEdit

    from emp_packagex3.ui.completer import attach_completer

    app = QApplication.instance() or QApplication([])
    _ = app
    editor = QPlainTextEdit()
    completer = attach_completer(editor)
    editor.setPlainText("#Set:Prod")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    completer.setCompletionPrefix("#Set:Prod")
    completer.activated[str].emit("#Set:Product")  # type: ignore[attr-defined]
    assert editor.toPlainText() == "#Set:Product"
