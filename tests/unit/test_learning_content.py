"""Learning content sanity + execution order + learning center rendering."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from emp_packagex3.learning_content import (
    COMMAND_DOCS,
    COURSE_CHAPTERS,
    VAL_DOCS,
    lookup_section,
)
from empirum_core.linter import builtin_rules
from empirum_core.setupinf_contract import SETUPINF_COMMANDS, STANDARD_SECTIONS


def test_every_catalog_command_has_docs() -> None:
    missing = [cmd for cmd in SETUPINF_COMMANDS if cmd.casefold() not in
               {k.casefold() for k in COMMAND_DOCS}]
    assert missing == [], f"COMMAND_DOCS fehlt: {missing}"


def test_every_catalog_variable_has_docs() -> None:
    from emp_packagex3.learning_content import lookup_variable
    from empirum_core.setupinf_contract import SETUPINF_VARIABLES
    missing = [var for var in SETUPINF_VARIABLES if lookup_variable(var) is None]
    assert missing == [], f"VARIABLE_DOCS fehlt: {missing}"


def test_every_standard_section_has_reference_entry() -> None:
    def resolve(name: str) -> bool:
        if lookup_section(name) is not None:
            return True
        # pattern families: strip the concrete name after the colon
        if ":" in name:
            prefix = name.split(":", 1)[0] + ":"
            return lookup_section(prefix + "X") is not None
        return False

    missing = [s for s in STANDARD_SECTIONS if not resolve(s)]
    assert missing == [], f"SECTION_REFERENCE fehlt: {missing}"


def test_every_val_code_has_docs() -> None:
    codes = {rule.code for rule in builtin_rules()}
    assert codes == set(VAL_DOCS), f"VAL_DOCS vs. Regeln: {codes ^ set(VAL_DOCS)}"


def test_course_chapters_complete_and_nonempty() -> None:
    numbers = [c.number for c in COURSE_CHAPTERS]
    assert numbers == list(range(1, 9))
    for chapter in COURSE_CHAPTERS:
        assert chapter.intro and chapter.key_rule and chapter.example
        assert 2 <= len(chapter.quiz) <= 3
        for q in chapter.quiz:
            assert q.question.endswith("?") or q.question.startswith(
                ("Welche", "Was", "Wo", "Warum", "Wie")
            )


def test_lookup_section_families() -> None:
    assert lookup_section("Product").name == "Product"
    assert lookup_section("Shell:Product").name == "Shell:<Name>"
    assert lookup_section("Set:Anything").name == "Set:<Name>"
    assert lookup_section("Reg:OnUninstallProduct").name == "Reg:OnUninstall<Name>"
    assert lookup_section("Strings:09").name.startswith("Strings:")
    assert lookup_section("GanzUnbekannt") is None


def test_learning_center_rendering() -> None:
    pytest.importorskip("PySide6")
    from emp_packagex3.ui.learning_center import (
        render_all_commands_html,
        render_all_sections_html,
        render_chapter_html,
        render_full_export_html,
        render_overview_html,
        render_val_docs_html,
    )

    overview = render_overview_html(term="Benutzerteil")
    assert "Benutzerteil" in overview and "<b>" in overview
    chapter = render_chapter_html(COURSE_CHAPTERS[2], term="DONTDELETE")
    assert "Kapitel 3" in chapter and "Merksatz" in chapter and "Selbsttest" in chapter
    assert "DONTDELETE" in chapter
    assert render_all_sections_html().count("<h2>") >= 20
    assert render_all_commands_html().count("<h2>") >= 20
    assert "VAL-021" in render_val_docs_html()
    full = render_full_export_html()
    assert full.startswith("<html>") and full.count("<h1>") >= 12


def test_learning_center_dialog_smoke() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.learning_center import LearningCenterDialog

    app = QApplication.instance() or QApplication([])
    _ = app
    dlg = LearningCenterDialog()
    assert dlg._toc.count() > 30
    # Chapter navigation renders content
    dlg._toc.setCurrentRow(3)
    assert "Kapitel" in dlg._browser.toPlainText()
    # Deterministic command lookup by data key
    target_row = -1
    for row in range(dlg._toc.count()):
        if str(dlg._toc.item(row).data(0x0100) or "") == "command:CallHidden":
            target_row = row
            break
    assert target_row >= 0
    dlg._search.setText("unsichtbar")
    dlg._toc.setCurrentRow(target_row)
    assert "CallHidden" in dlg._browser.toPlainText()
    assert "unsichtbar" in dlg._browser.toPlainText()  # Treffer hervorgehoben


_SAMPLE = (
    "[Application]\r\n"
    "ProductName=X\r\n"
    "ShellLinks=1\r\n"
    "\r\n"
    "[Product]\r\n"
    "#Set:Install, DONTDELETE\r\n"
    "#Reg:OnUninstall, DELETE\r\n"
    "#Set:Cleanup, DELETE\r\n"
    "\r\n"
    "[Set:Install]\r\n"
    "AddMeter -1\r\n"
    'CallHidden setup.exe /S\r\n'
    'If %ErrorLevel% == "0" Then "OK" EndIf\r\n'
    "-DelTree \"%Temp%\\leftover\"\r\n"
    "\r\n"
    "[Set:Cleanup]\r\n"
    "-Del \"%App%\\file.dat\"\r\n"
    "Echo never-on-uninstall\r\n"
    "\r\n"
    "[Reg:OnUninstall]\r\n"
    'HKLM,"Software\\X","",0x00000000,1\r\n'
    "\r\n"
    "[Shell:Product]\r\n"
    '"%CommonDesktop%\\X", "%ProgramFiles%\\X\\x.exe"\r\n'
)


def _doc():
    from empirum_core.parser.lexer import lex_text

    return lex_text(_SAMPLE)


def test_execution_order_install() -> None:
    from emp_packagex3.execution_logic import execution_steps

    steps = execution_steps(_doc(), uninstall=False)
    texts = [s.text for s in steps]
    # DONTDELETE runs, DELETE skipped, '-'-Zeilen übersprungen
    assert "#Set:Install, DONTDELETE" in texts
    assert not any("OnUninstall" in t or "#Set:Cleanup" in t for t in texts)
    assert not any(t.startswith("-") for t in texts)
    assert any("CallHidden" in t for t in texts)
    # Shell:Product automatisch zuletzt
    assert steps[-1].kind == "shell-auto"
    assert steps[-1].section == "Shell:Product"
    assert [s.order for s in steps] == list(range(1, len(steps) + 1))


def test_execution_order_uninstall() -> None:
    from emp_packagex3.execution_logic import execution_steps

    steps = execution_steps(_doc(), uninstall=True)
    texts = [s.text for s in steps]
    # Shell zuerst, dann bottom-up: DELETE-Refs laufen, DONTDELETE gar nicht
    assert steps[0].kind == "shell-auto"
    assert any("Cleanup" in t for t in texts)
    assert not any("Set:Install" in t for t in texts)
    cleanup = next(i for i, s in enumerate(steps) if "Cleanup" in s.text)
    onuninstall = next(i for i, s in enumerate(steps) if "OnUninstall" in s.text)
    assert cleanup < onuninstall  # bottom-up: letzter Ref zuerst
    # Nur '-'-Zeilen (und If/#) laufen; Echo ohne '-' fällt raus
    assert not any(t.startswith("Echo") for t in texts)
    assert any(t.startswith('-Del "') for t in texts)
    assert not any(t.startswith("-DelTree") for t in texts)  # install-only Sektion


def test_execution_notes_from_command_docs() -> None:
    from emp_packagex3.execution_logic import execution_steps

    steps = execution_steps(_doc(), uninstall=False)
    call = next(s for s in steps if "CallHidden" in s.text)
    assert call.note  # Kurzbedeutung aus COMMAND_DOCS


@given(mode=st.booleans())
def test_execution_ordering_always_dense(mode: bool) -> None:
    from emp_packagex3.execution_logic import execution_steps

    steps = execution_steps(_doc(), uninstall=mode)
    assert [s.order for s in steps] == list(range(1, len(steps) + 1))
