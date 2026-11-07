"""Simulator coverage for install/uninstall flows and gap analysis."""

from __future__ import annotations

from empirum_core.parser.lexer import lex_text
from empirum_core.simulator import SimMode, simulate


def test_simulate_install_walks_hash_refs() -> None:
    doc = lex_text(
        "[Set_Install]\r\n"
        "Echo=start\r\n"
        "#Set:Phase2\r\n"
        "\r\n"
        "[Phase2]\r\n"
        "Echo=phase2\r\n"
        "\r\n"
        "[Set_Uninstall]\r\n"
        "Echo=gone\r\n"
    )
    report = simulate(doc, SimMode.INSTALL)
    commands = [a.command for a in report.actions]
    assert "Echo" in commands
    assert any(a.section == "Phase2" for a in report.actions)


def test_simulate_uninstall_entry() -> None:
    # OP-008: ohne '-' laufen im Uninstall nur die Immer-Befehle (Set, …)
    doc = lex_text(
        "[Set_Uninstall]\r\n"
        "-Echo=removing\r\n"
        "-DelTree=%Dst%\r\n"
    )
    report = simulate(doc, SimMode.UNINSTALL)
    assert report.mode == SimMode.UNINSTALL
    assert any(a.command in ("DelTree", "-DelTree") for a in report.actions)
    assert any(a.command in ("Echo", "-Echo") for a in report.actions)


def test_simulate_missing_install_section() -> None:
    doc = lex_text("[SetupInfo]\r\nProductName=X\r\n")
    report = simulate(doc, SimMode.INSTALL)
    assert report.gaps


def test_simulate_state_tracking_variables_files_registry() -> None:
    text = (
        "[Application]\r\n"
        "ProductName=SuperTool\r\n"
        "DeveloperName=AcmeCorp\r\n"
        "Version=2.5\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Product, DONTDELETE\r\n"
        "#Reg:Product, DONTDELETE\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Set CustomFolder = %ProgramFiles%\\Acme\\Tools\r\n"
        "ReplaceEnv CustomFolder\r\n"
        'MD "%CustomFolder%"\r\n'
        'KillProcess "oldtool.exe"\r\n'
        "AskKillProcesses 60, ToolApp\r\n"
        "SetReboot 1\r\n"
        "\r\n"
        "[Reg:Product]\r\n"
        'HKLM,"SOFTWARE\\AcmeCorp\\SuperTool","Installed",0x00010001,"1"\r\n'
        '-HKLM,"SOFTWARE\\AcmeCorp\\Legacy"\r\n'
        "\r\n"
        "[Set:Deinstallation]\r\n"
        '-DelTree "%CustomFolder%"\r\n'
    )
    doc = lex_text(text)
    report = simulate(doc, SimMode.INSTALL)

    # Variables populated & expanded
    assert report.final_state.variables.get("ProductName") == "SuperTool"
    assert report.final_state.variables.get("DeveloperName") == "AcmeCorp"
    assert "CustomFolder" in report.final_state.variables
    assert "C:\\Program Files\\Acme\\Tools" in report.final_state.variables["CustomFolder"]

    # Files / Dirs tracked
    assert any("Acme\\Tools" in f for f in report.final_state.files)

    # Processes tracked
    assert "oldtool.exe" in report.final_state.terminated_processes
    assert "ToolApp" in report.final_state.terminated_processes

    # Reboot requested
    assert report.final_state.reboot_requested is True

    # Registry tracked
    assert "HKLM\\SOFTWARE\\AcmeCorp\\SuperTool" in report.final_state.reg_keys

def test_simulate_uninstall_reverse_execution_order() -> None:
    """Setup.exe /U executes sections and actions in reverse order (bottom-up)."""
    text = (
        "[Set:Deinstallation]\r\n"
        '-DelTree "C:\\Program Files (x86)\\Acme\\DemoApp"\r\n'
        '-Del "%CommonStartMenu%\\Start Menu\\DemoApp.lnk"\r\n'
        '-KillProcess "DemoApp.exe"\r\n'
    )
    doc = lex_text(text)
    report = simulate(doc, SimMode.UNINSTALL)
    commands = [a.command for a in report.actions]
    assert commands == ["KillProcess", "Del", "DelTree"]


def test_simulate_uninstall_op008_line_filter() -> None:
    """Verified OP-008: at /U only '-'-lines run, plus the always-both commands;
    Copy/MD without '-' are auto-reversed by the interpreter instead."""
    text = (
        "[Set:Deinstallation]\r\n"
        'Del "%App%\\install-only.txt"\r\n'       # install-only: skipped at /U
        'Set Note = uninstall-run\r\n'            # Set: immer auch bei /U
        "AddMeter -1\r\n"                          # AddMeter: immer auch bei /U
        'MD "%App%\\auto"\r\n'                     # auto-reversed (undo log)
        '-Del "%App%\\real-uninstall.txt"\r\n'     # '-'-Zeile: läuft bei /U
    )
    doc = lex_text(text)
    report = simulate(doc, SimMode.UNINSTALL)
    commands = [a.command for a in report.actions]
    # Install-only line without '-' is skipped at /U
    assert commands.count("Del") == 1
    # Always-both commands run without '-'
    assert any(c.startswith("Set") for c in commands)
    assert "AddMeter" in commands
    # Auto-reversed command is annotated as interpreter undo
    auto = next(a for a in report.actions if a.command == "MD")
    assert "automatisch rückgängig" in auto.detail


def test_simulate_install_skips_delete_refs() -> None:
    text = (
        "[Product]\r\n"
        "#Set:Product, DONTDELETE\r\n"
        "#Set:Deinstallation, DELETE\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Echo=install\r\n"
        "\r\n"
        "[Set:Deinstallation]\r\n"
        '-DelTree "%App%"\r\n'
    )
    doc = lex_text(text)
    install = simulate(doc, SimMode.INSTALL)
    assert not any(a.section == "Set:Deinstallation" for a in install.actions)
    uninstall = simulate(doc, SimMode.UNINSTALL)
    assert any(a.section == "Set:Deinstallation" for a in uninstall.actions)
    assert not any(a.section == "Set:Product" for a in uninstall.actions)


def test_simulate_new_command_state_effects() -> None:
    text = (
        "[Set:Product]\r\n"
        'MkDir "%App%\\logs"\r\n'
        "Set Zaehler = 5\r\n"
        "Increment (Zaehler)\r\n"
        "Divide (Zaehler, 2)\r\n"
        'Rename "%App%\\old.cfg" "%App%\\new.cfg"\r\n'
        'AddService MeinDienst, 0x10, 2, 1\r\n'
        'StartService MeinDienst\r\n'
        'StopService MeinDienst\r\n'
        'DeleteService MeinDienst\r\n'
        'SystemShutdown %ShutdownTextDesc%, 1, 0, -1, 1\r\n'
        'KillProcess app.exe, 30, 1\r\n'
    )
    doc = lex_text(text)
    report = simulate(doc, SimMode.INSTALL)
    state = report.final_state
    assert any("logs" in f for f in state.files)
    assert state.variables.get("Zaehler") == "3"  # (5+1)/2
    assert any("new.cfg" in f for f in state.files)
    assert not any("old.cfg" in f for f in state.files)
    assert "MeinDienst" not in state.services  # deleted again
    assert state.shutdown_requested is True
    assert "app.exe" in state.terminated_processes


def test_simulate_undocumented_collapseenv_and_rendir() -> None:
    """Klasse-1 commands: CollapseEnv resolves deferred expressions, RenDir moves dirs."""
    text = (
        "[Environment]\r\n"
        "Basis=C:\\Program Files\\Vendor\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Set X = %Basis%\\App\r\n"
        "CollapseEnv X\r\n"
        'MD "%Basis%\\old"\r\n'
        'RenDir "%Basis%\\old" "%Basis%\\new"\r\n'
    )
    doc = lex_text(text)
    report = simulate(doc, SimMode.INSTALL)
    state = report.final_state
    assert state.variables.get("X") == r"C:\Program Files\Vendor\App"
    assert any(f.endswith("\\new") for f in state.files)
    assert not any(f.endswith("\\old") for f in state.files)

