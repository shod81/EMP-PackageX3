"""VisualPanels workflow classification."""

from __future__ import annotations

import pytest

from emp_packagex3.ui.panels import _workflow_role, _workflow_section, _workflow_steps
from empirum_core.ast.model import KeyValueLine, RawLine, Section
from empirum_core.parser.lexer import lex_text


def test_workflow_section_matches_standard_and_legacy() -> None:
    assert _workflow_section("Product")
    assert _workflow_section("Set:Product")
    assert _workflow_section("Set:Deinstallation")
    assert _workflow_section("Set:InstallationError")
    assert _workflow_section("Set_Install")
    assert _workflow_section("Set_Uninstall")
    assert _workflow_section("InstallMSI")
    assert _workflow_section("RepairMSI")
    assert _workflow_section("Uninstall_x64")
    assert _workflow_section("Deinstall_x86")
    assert _workflow_section("RebootRequired")
    assert _workflow_section("Installation")
    assert _workflow_section("Repair")
    assert not _workflow_section("Application")
    assert not _workflow_section("SetupInfo")
    assert not _workflow_section("Environment")
    assert not _workflow_section("Reg:Product")
    assert not _workflow_section("Shell:Product")
    assert not _workflow_section("Installer")
    assert not _workflow_section("Options")


def test_workflow_steps_from_standard_raw_commands() -> None:
    section = Section(
        name="Set:Product",
        lines=[
            RawLine(text="AddMeter -1"),
            RawLine(text="; comment only"),
            RawLine(text='CallHidden MsiExec /I "%Src%\\Files\\a.msi" /qn'),
            RawLine(text='If "%ErrorLevel%" == "3010" Then "RebootRequired" EndIf'),
            RawLine(text="#InstallMSI"),
            KeyValueLine(key="Sleep", value="3000"),
        ],
    )
    steps = _workflow_steps(section)
    kinds = [k for k, _ in steps]
    assert "AddMeter" in kinds
    assert "CallHidden" in kinds
    assert "If" in kinds
    assert "→ Sektion" in kinds
    assert "Sleep" in kinds
    assert len(steps) == 5


def test_workflow_role_labels() -> None:
    assert "Einstieg" in _workflow_role("Product")
    assert "Installation" in _workflow_role("Set:Product")
    assert "Deinstallation" in _workflow_role("Set:Deinstallation")
    assert "Reboot" in _workflow_role("RebootRequired")
    assert "Fehler" in _workflow_role("Set:InstallationError")


def test_visual_panels_workflow_lists_standard_flow() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.panels import VisualPanels

    app = QApplication.instance() or QApplication([])
    _ = app
    text = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n"
        "[Application]\r\nProductName=Demo\r\n\r\n"
        "[Product]\r\n"
        "#Set:Product, DONTDELETE\r\n"
        "#Set:Deinstallation, DELETE\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "AddMeter -1\r\n"
        'CallHidden MsiExec /I "%Src%\\Files\\a.msi" /qn\r\n'
        "\r\n"
        "[InstallMSI]\r\n"
        "AddMeter -1\r\n"
        "\r\n"
        "[Set:Deinstallation]\r\n"
        "-AddMeter -1\r\n"
        "\r\n"
        "[RebootRequired]\r\n"
        "SetReboot 1\r\n"
        "\r\n"
        "[Reg:Product]\r\n"
        "\r\n"
    )
    doc = lex_text(text)
    panels = VisualPanels()
    panels.set_document(doc)
    tree = panels._workflow  # noqa: SLF001
    names = [tree.topLevelItem(i).text(0) for i in range(tree.topLevelItemCount())]
    assert any("[Product]" in n for n in names)
    assert any("[Set:Product]" in n for n in names)
    assert any("[InstallMSI]" in n for n in names)
    assert any("[Set:Deinstallation]" in n for n in names)
    assert any("[RebootRequired]" in n for n in names)
    assert not any("[Reg:Product]" in n for n in names)
    assert not any("[Application]" in n for n in names)
    set_product = next(
        tree.topLevelItem(i)
        for i in range(tree.topLevelItemCount())
        if "[Set:Product]" in tree.topLevelItem(i).text(0)
    )
    child_cmds = {set_product.child(i).text(0) for i in range(set_product.childCount())}
    assert "CallHidden" in child_cmds or "AddMeter" in child_cmds


def test_shell_link_add_writes_standard_syntax() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.panels import VisualPanels

    app = QApplication.instance() or QApplication([])
    _ = app
    doc = lex_text(
        "[Application]\r\nProductName=X\r\n\r\n"
        "[Shell:Product]\r\n"
        '"%CommonDesktop%\\Existing", "%ProgramFiles%\\App\\a.exe"\r\n'
    )
    panels = VisualPanels()
    panels.set_document(doc)
    panels._shell_name.setText("Demo")
    panels._shell_path.setText(r"%ProgramFiles%\Demo\demo.exe")
    panels._add_shell_link()

    section = doc.section("Shell:Product")
    assert section is not None
    texts = [n.text for n in section.lines if hasattr(n, "text")]
    assert '"%CommonDesktop%\\Existing", "%ProgramFiles%\\App\\a.exe"' in texts
    assert '"%CommonDesktop%\\Demo", "%ProgramFiles%\\Demo\\demo.exe"' in texts
    app_section = doc.section("Application")
    assert app_section is not None
    app_keys = {
        n.key: n.value for n in app_section.lines if isinstance(n, KeyValueLine)
    }
    assert app_keys.get("ShellLinks") == "1"
    assert app_keys.get("CommonShellLinks") == "1"
    # The non-reference CreateLinks/LinkName dialect is no longer generated
    assert doc.section("CreateLinks") is None


def test_shell_link_add_destination_choice() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.ui.panels import VisualPanels

    app = QApplication.instance() or QApplication([])
    _ = app
    doc = lex_text("[Application]\r\nProductName=X\r\n\r\n[Shell:Product]\r\n")
    panels = VisualPanels()
    panels.set_document(doc)

    # Default stays CommonDesktop (previous fixed behaviour)
    assert panels._shell_dest.currentData() == "%CommonDesktop%"

    # Common Programs: name may carry a subfolder path (Vendor\App)
    panels._shell_dest.setCurrentIndex(1)
    panels._shell_name.setText(r"Vendor\DemoStart")
    panels._shell_path.setText(r"%ProgramFiles%\Demo\demo.exe")
    panels._add_shell_link()

    # CommonDesktop via the combo box
    panels._shell_dest.setCurrentIndex(0)
    panels._shell_name.setText("DemoDesktop")
    panels._shell_path.setText(r"%ProgramFiles%\Demo\demo.exe")
    panels._add_shell_link()

    section = doc.section("Shell:Product")
    assert section is not None
    texts = [n.text for n in section.lines if hasattr(n, "text")]
    assert '"%CommonPrograms%\\Vendor\\DemoStart", "%ProgramFiles%\\Demo\\demo.exe"' in texts
    assert '"%CommonDesktop%\\DemoDesktop", "%ProgramFiles%\\Demo\\demo.exe"' in texts


def test_workflow_role_labels_uninstall_and_error() -> None:
    assert "Deinstallation" in _workflow_role("Uninstall")
    assert "Deinstallation" in _workflow_role("Uninstall_x64")
    assert "Deinstallation" in _workflow_role("Set_Uninstall")
    assert "Deinstallation" in _workflow_role("Set:Deinstallation")
    assert "Fehlerpfad" in _workflow_role("Error_Uninstall")
    assert "Fehlerpfad" in _workflow_role("Set:DeInstallationError")
