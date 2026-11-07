"""Setup.inf command reference / Empirum help dialog."""

from __future__ import annotations

import pytest

from emp_packagex3.learning_content import (
    COMMAND_DOCS,
    FUNCTION_DOCS,
    PREDICATE_DOCS,
    lookup_predicate,
)
from emp_packagex3.ui.command_reference import (
    command_matches,
    iter_command_docs,
)
from emp_packagex3.ui.empirum_help import render_hub_overview_html, topic_matches
from empirum_core.setupinf_contract import (
    SETUPINF_COMMANDS,
    SETUPINF_FUNCTIONS,
    SETUPINF_PREDICATES,
)


def test_iter_command_docs_covers_catalog() -> None:
    docs = iter_command_docs()
    names = [d.name for d in docs]
    assert names == list(SETUPINF_COMMANDS)
    assert "MD" in names
    # K-01 / §8.3: proven non-existent commands must never return to the catalog
    assert "CheckLanAdministrator" not in names
    assert "Run" not in names


def test_reference_table_core_commands_documented() -> None:
    """Kap. 6 Ausführungs-Befehle from System_Prompt (plus control words)."""
    core = {
        "Call",
        "CallHidden",
        "Sleep",
        "AddMeter",
        "KillProcess",
        "AskKillProcesses",
        "Del",
        "DelTree",
        "Copy",
        "Echo",
        "Set",
        "ReplaceEnv",
        "ErrorLogMsg",
        "Abort",
        "Exit",
        "SetReboot",
        "If",
        "EndIf",
        "For",
        "Next",
    }
    catalog = {c.casefold() for c in SETUPINF_COMMANDS}
    missing = [c for c in core if c.casefold() not in catalog]
    assert missing == []


def test_predicates_and_functions_documented() -> None:
    for name in SETUPINF_PREDICATES:
        assert name in PREDICATE_DOCS, name
    for name in SETUPINF_FUNCTIONS:
        assert name in FUNCTION_DOCS, name
    assert lookup_predicate("DoesRegKeyExist") is not None
    assert lookup_predicate("doesfileexist") is not None


def test_command_matches_search() -> None:
    doc = COMMAND_DOCS["CallHidden"]
    assert command_matches(doc, "msiexec")
    assert command_matches(doc, "CALLHIDDEN")
    assert not command_matches(doc, "AskKillProcessesXYZ")


def test_overview_html() -> None:
    html = render_hub_overview_html()
    assert "Setup.inf-Hilfe" in html
    assert "Prädikate" in html
    assert str(len(SETUPINF_COMMANDS)) in html


def test_overview_notes_undocumented_commands() -> None:
    """Die Übersichtsseite benennt immer, welche Einträge nicht dokumentiert sind."""
    from empirum_core.setupinf_contract import SETUPINF_COMMANDS_UNDOCUMENTED

    html = render_hub_overview_html()
    assert "Nicht dokumentierte Befehle" in html
    for name in SETUPINF_COMMANDS_UNDOCUMENTED:
        assert name in html, name
    # Auch ohne Feature-Flag steht der Hinweis auf die Aktivierung dabei
    assert "Feature-Flag" in html
    assert "Undokumentiert (26.1.0)" in html

    on_html = render_hub_overview_html(undocumented=True)
    assert "Feature-Flag ist aktiv" in on_html
    assert "(undok.)" in on_html


def test_topic_matches_predicate() -> None:
    assert topic_matches("predicate", "DoesRegKeyExist", "registry")
    assert topic_matches("function", "GetUninstallKeyName", "GUID")


def test_topic_matches_variable() -> None:
    assert topic_matches("variable", "%AppData%", "roaming")
    assert topic_matches("variable", "%ErrorLevel%", "returncode")
    assert topic_matches("variable", "%Src%", "quelle")


def test_empirum_help_dialog_search() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.empirum_help import EmpirumHelpDialog

    app = QApplication.instance() or QApplication([])
    _ = app
    dlg = EmpirumHelpDialog(tooltip_mode=False)
    dlg._search.setText("DoesRegKeyExist")
    html = dlg._browser.toHtml()
    assert "DoesRegKeyExist" in html or dlg._tree.topLevelItemCount() > 0
    dlg._search.setText("GetUninstallKeyName")
    dlg._select_initial("function:GetUninstallKeyName")
    assert "GetUninstallKeyName" in dlg._browser.toHtml()


def test_command_reference_dialog_opens_help() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.command_reference import CommandReferenceDialog

    app = QApplication.instance() or QApplication([])
    _ = app
    dlg = CommandReferenceDialog(tooltip_mode=False, initial_command="Sleep")
    assert "Sleep" in dlg._browser.toHtml()


def test_help_tree_undocumented_gating() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.empirum_help import EmpirumHelpDialog

    app = QApplication.instance() or QApplication([])
    _ = app

    def tree_labels(dialog) -> list[str]:
        return [
            dialog._tree.topLevelItem(i).text(0)
            for i in range(dialog._tree.topLevelItemCount())
        ]

    # Default: class-1 group hidden
    off = EmpirumHelpDialog(tooltip_mode=False)
    assert not any("Undokumentiert" in label for label in tree_labels(off))

    # Flag on: gated group visible, secret commands listed
    on = EmpirumHelpDialog(tooltip_mode=False, undocumented=True)
    assert any("Undokumentiert" in label for label in tree_labels(on))
    undoc_root = next(
        on._tree.topLevelItem(i)
        for i in range(on._tree.topLevelItemCount())
        if "Undokumentiert" in on._tree.topLevelItem(i).text(0)
    )
    child_labels = [undoc_root.child(i).text(0) for i in range(undoc_root.childCount())]
    # Einträge sind zusätzlich mit „(undok.)“ gekennzeichnet
    assert "CollapseEnv (undok.)" in child_labels
    assert "%DstDir% (undok.)" in child_labels


def _all_tree_labels(item) -> list[str]:
    labels = [item.text(0)]
    for i in range(item.childCount()):
        labels.extend(_all_tree_labels(item.child(i)))
    return labels


def test_undoc_detail_pages_carry_warning_badge() -> None:
    """Detailseiten undokumentierter Befehle/Variablen zeigen die Warnbox."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.empirum_help import EmpirumHelpDialog

    app = QApplication.instance() or QApplication([])
    _ = app
    dlg = EmpirumHelpDialog(tooltip_mode=False, undocumented=True)

    dlg._select_initial("command:CollapseEnv")
    assert "UNDOKUMENTIERT" in dlg._browser.toHtml()

    dlg._select_initial("variable:%DstDir%")
    assert "UNDOKUMENTIERT" in dlg._browser.toHtml()

    # Suchtreffer bleiben über das Suffix als undokumentiert erkennbar
    dlg._search.setText("Env")
    all_labels = _all_tree_labels(dlg._tree.invisibleRootItem())
    assert "CollapseEnv (undok.)" in all_labels
    assert "ReplaceEnv" in all_labels

    # Übersicht im Dialog (Flag an) nennt den undokumentierten Bereich
    dlg._search.clear()
    assert "Nicht dokumentierte Befehle" in dlg._browser.toHtml()
