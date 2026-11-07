"""User-Parts: per-user context, CLIENT/MACHINE flags, /AW chain.

Covers the user-part contract: templates emit [Set:Client]
with the CLIENT flag and MACHINE-flagged machine entries, [SetupInfo] gains
/AW, and the linter enforces the reverse direction (VAL-006), user-context
routing (VAL-032), duplicate sections (VAL-033) and the Reg/HKCU flag trap
(VAL-034). Machine packages must stay byte-comparable to the plain standard form.
"""

from __future__ import annotations

from empirum_core.inspect import PackageMetadata, RegistryEntrySpec
from empirum_core.linter import Severity, lint_document
from empirum_core.parser.lexer import lex_text
from empirum_core.serializer.serialize import serialize_to_bytes
from empirum_core.setupinf_contract import (
    PRODUCT_REFS,
    USER_PART_PRODUCT_REF,
    product_refs_for,
)
from empirum_core.skeleton_repair import add_missing_standard_sections
from empirum_core.templates import render_template


def _meta(**kwargs) -> PackageMetadata:
    base = dict(
        product_name="Demo",
        product_version="1.2.3",
        manufacturer="Hodrius",
        source_path=r"C:\tmp\Demo.msi",
    )
    base.update(kwargs)
    return PackageMetadata(**base)


def _codes(text: str) -> set[str]:
    normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return {d.code for d in lint_document(lex_text(normalized))}


def _diags(text: str, code: str):
    normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return [d for d in lint_document(lex_text(normalized)) if d.code == code]


# --- Contract ---------------------------------------------------------------


def test_contract_machine_refs_unchanged_without_user_part() -> None:
    assert product_refs_for() == PRODUCT_REFS
    assert product_refs_for(user_part=False, reg_machine_only=False) == PRODUCT_REFS


def test_contract_user_part_flags() -> None:
    refs = product_refs_for(user_part=True)
    assert refs[0] == ("Set:Product", "#Set:Product, DONTDELETE, MACHINE")
    assert refs[-1] == USER_PART_PRODUCT_REF == ("Set:Client", "#Set:Client, CLIENT")
    # every machine entry carries MACHINE, appended comma-separated, unquoted
    for _target, ref in refs[:-1]:
        assert ref.endswith(", MACHINE"), ref
        assert '"' not in ref
    # client ref is last (machine part first, then the user pass)


def test_contract_hkcu_registry_stays_unflagged() -> None:
    refs = product_refs_for(user_part=True, reg_machine_only=False)
    reg = [ref for target, ref in refs if target == "Reg:Product"]
    assert reg == ["#Reg:Product, DONTDELETE"]
    assert ("Set:Client", "#Set:Client, CLIENT") in refs


# --- Templates --------------------------------------------------------------


def _product_lines(doc) -> list[str]:
    """Active call lines of the [Product] section(s), in order."""
    out: list[str] = []
    for section in doc.sections:
        if section.name.casefold() != "product":
            continue
        for node in section.lines:
            text = getattr(node, "text", None)
            if text and text.startswith("#"):
                out.append(text)
    return out


def test_template_user_part_emits_client_section_and_flags() -> None:
    meta = _meta(
        user_context_commands=[
            r'CallHidden "%Src%\Files\usersetup.exe"',
            r"MD %AppData%\Vendor\AppConfig",
        ]
    )
    doc = render_template("msi", meta)
    text = serialize_to_bytes(doc).decode("cp1252")

    assert "Command line options=/S2 /AW\r\n" in text
    lines = _product_lines(doc)
    assert "#Set:Product, DONTDELETE, MACHINE" in lines
    assert "#Set:Deinstallation, DELETE, MACHINE" in lines
    assert "#Reg:Product, DONTDELETE, MACHINE" in lines
    assert lines[-1] == "#Set:Client, CLIENT"

    client = doc.section("Set:Client")
    assert client is not None
    body = [n.text for n in client.lines if n.text]
    assert r'CallHidden "%Src%\Files\usersetup.exe"' in body
    # Call-like user commands get the 3010/0 ErrorLevel pair (VAL-008)
    i = body.index(r'CallHidden "%Src%\Files\usersetup.exe"')
    assert body[i + 1] == 'If "%ErrorLevel%" == "3010" Then "RebootRequired" EndIf'
    assert body[i + 2] == 'If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf'
    # non-Call commands get no pair
    assert r"MD %AppData%\Vendor\AppConfig" in body


def test_template_user_part_exactly_one_client_section() -> None:
    meta = _meta(user_context_commands=["Echo user part"])
    for kind in ("msi", "exe", "script", "links"):
        doc = render_template(kind, meta)
        names = [s.name.casefold() for s in doc.sections]
        assert names.count("set:client") == 1, kind
        assert "Command line options=/S2 /AW\r\n" in serialize_to_bytes(doc).decode(
            "cp1252"
        ), kind


def test_template_machine_package_stays_unflagged() -> None:
    meta = _meta()
    doc = render_template("msi", meta)
    text = serialize_to_bytes(doc).decode("cp1252")
    assert "Command line options=/S2\r\n" in text
    assert "MACHINE" not in text
    assert "#Set:Client" not in text
    assert doc.section("Set:Client") is None


def test_template_hkcu_with_user_part_keeps_reg_ref_unflagged() -> None:
    meta = _meta(user_context_commands=["Echo user part"])
    meta.registry_entries.append(
        RegistryEntrySpec(
            root="HKCU",
            key_path=r"Software\Vendor\App",
            value_name="Flag",
            value_data="1",
        )
    )
    doc = render_template("msi", meta)
    lines = _product_lines(doc)
    assert "#Reg:Product, DONTDELETE" in lines
    assert "#Reg:Product, DONTDELETE, MACHINE" not in lines
    assert "#Set:Product, DONTDELETE, MACHINE" in lines
    assert "Command line options=/S2 /AW\r\n" in serialize_to_bytes(doc).decode("cp1252")


def test_user_part_templates_lint_without_errors() -> None:
    meta = _meta(
        user_context_commands=[
            r'CallHidden "%Src%\Files\usersetup.exe"',
            r"MD %AppData%\Vendor\AppConfig",
        ]
    )
    for kind in ("msi", "exe", "script", "links"):
        diags = lint_document(render_template(kind, meta))
        errors = [d for d in diags if d.severity == Severity.ERROR]
        assert errors == [], (kind, [(d.code, d.message) for d in errors])
        # the new user-part rules must stay silent on generated packages
        assert not [d for d in diags if d.code in {"VAL-032", "VAL-033", "VAL-034"}], kind


def test_user_part_commands_with_own_errorlevel_get_no_double_pair() -> None:
    meta = _meta(
        user_context_commands=[
            "CallHidden usersetup.exe",
            'If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf',
        ]
    )
    doc = render_template("script", meta)
    body = [n.text for n in doc.section("Set:Client").lines if n.text]
    assert body.count('If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf') == 1


# --- Linter: VAL-006 counter direction --------------------------------------


def test_val_006_client_section_without_aw_is_error() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Product, DONTDELETE, MACHINE\r\n"
        "#Set:Client, CLIENT\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Echo ok\r\n"
        "\r\n"
        "[Set:Client]\r\n"
        "Echo user\r\n"
    )
    diags = _diags(text, "VAL-006")
    assert len(diags) == 1
    assert diags[0].severity == Severity.ERROR
    assert any(f.replacement_line == "Command line options=/S2 /AW" for f in diags[0].quick_fixes)


def test_val_006_client_section_with_aw_clean() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2 /AW\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Client, CLIENT\r\n"
        "\r\n"
        "[Set:Client]\r\n"
        "Echo user\r\n"
    )
    assert "VAL-006" not in _codes(text)


def test_val_006_hkcu_only_stays_warning() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2\r\n"
        "\r\n"
        "[Reg:Product]\r\n"
        'HKCU,"Software\\Vendor","Value","1"\r\n'
    )
    diags = _diags(text, "VAL-006")
    assert len(diags) == 1
    assert diags[0].severity == Severity.WARNING


# --- Linter: VAL-032 user-context routing ------------------------------------


def test_val_032_user_command_outside_client_section() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2 /AW\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Product, DONTDELETE, MACHINE\r\n"
        "#Set:Client, CLIENT\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        r"MD %AppData%\Vendor\Config" + "\r\n"
        "\r\n"
        "[Set:Client]\r\n"
        r"MD %AppData%\Vendor\User" + "\r\n"
    )
    diags = _diags(text, "VAL-032")
    assert len(diags) == 1
    assert diags[0].severity == Severity.ERROR
    assert diags[0].line is not None and diags[0].line > 8  # the Set:Product line


def test_val_032_hkcu_write_outside_client_section() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2 /AW\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Client, CLIENT\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        'CallHidden reg.exe add "HKCU\\Software\\Vendor" /v Flag /d 1 /f\r\n'
    )
    diags = _diags(text, "VAL-032")
    assert len(diags) == 1
    assert "HKCU" in diags[0].message


def test_val_032_client_flagged_custom_section_counts_as_client_scope() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2 /AW\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Product, DONTDELETE, MACHINE\r\n"
        "#Set:UserConfig, CLIENT\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Echo machine\r\n"
        "\r\n"
        "[Set:UserConfig]\r\n"
        r"MD %AppData%\Vendor\User" + "\r\n"
    )
    assert "VAL-032" not in _codes(text)


def test_val_032_silent_without_user_part() -> None:
    """No real user part: profile-var commands may run in both passes."""
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Product, DONTDELETE\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        r"MD %AppData%\Vendor\Config" + "\r\n"
    )
    assert "VAL-032" not in _codes(text)


def test_val_032_uninstall_sections_exempt() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2 /AW\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Client, CLIENT\r\n"
        "\r\n"
        "[Set:Deinstallation]\r\n"
        r"-MD %AppData%\Vendor\Config" + "\r\n"
        "-DelTree xyz" + "\r\n"
    )
    assert "VAL-032" not in _codes(text)


# --- Linter: VAL-033 duplicate [Set:Client] ----------------------------------


def test_val_033_duplicate_client_sections() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2 /AW\r\n"
        "\r\n"
        "[Set:Client]\r\n"
        "Echo one\r\n"
        "\r\n"
        "[Set:Client]\r\n"
        "Echo two\r\n"
    )
    diags = _diags(text, "VAL-033")
    assert len(diags) == 1
    assert diags[0].severity == Severity.ERROR


def test_val_033_single_client_section_clean() -> None:
    text = "[Set:Client]\r\nEcho one\r\n"
    assert "VAL-033" not in _codes(text)


# --- Linter: VAL-034 MACHINE on HKCU registry -------------------------------


def test_val_034_machine_flag_on_hkcu_registry() -> None:
    text = (
        "[Product]\r\n"
        "#Reg:Product, DONTDELETE, MACHINE\r\n"
        "\r\n"
        "[Reg:Product]\r\n"
        'HKCU,"Software\\Vendor","Value","1"\r\n'
    )
    diags = _diags(text, "VAL-034")
    assert len(diags) == 1
    assert diags[0].severity == Severity.WARNING
    fix = diags[0].quick_fixes[0]
    assert fix.replacement_line == "#Reg:Product, DONTDELETE"


def test_val_034_machine_flag_ok_without_hkcu() -> None:
    text = (
        "[Product]\r\n"
        "#Reg:Product, DONTDELETE, MACHINE\r\n"
        "\r\n"
        "[Reg:Product]\r\n"
        'HKLM,"Software\\Vendor","Value","1"\r\n'
    )
    assert "VAL-034" not in _codes(text)


def test_val_034_unflagged_hkcu_registry_clean() -> None:
    text = (
        "[Product]\r\n"
        "#Reg:Product, DONTDELETE\r\n"
        "\r\n"
        "[Reg:Product]\r\n"
        'HKCU,"Software\\Vendor","Value","1"\r\n'
    )
    assert "VAL-034" not in _codes(text)


# --- skeleton repair --------------------------------------------------------------


def test_repair_wires_missing_client_call() -> None:
    text = (
        "[SetupInfo]\r\n"
        "Command line options=/S2 /AW\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Set:Product, DONTDELETE\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Echo ok\r\n"
        "\r\n"
        "[Set:Client]\r\n"
        "Echo user\r\n"
    )
    doc = lex_text(text)
    repair = add_missing_standard_sections(doc)
    assert "#Set:Client, CLIENT" in repair.added_refs
    lines = [
        n.text for s in doc.sections if s.name.casefold() == "product" for n in s.lines
    ]
    assert "#Set:Client, CLIENT" in lines
    # idempotent: a second repair adds nothing
    repair2 = add_missing_standard_sections(doc)
    assert "#Set:Client, CLIENT" not in repair2.added_refs


def test_repair_never_creates_client_section() -> None:
    doc = lex_text("[SetupInfo]\r\nCommand line options=/S2\r\n")
    add_missing_standard_sections(doc)
    assert doc.section("Set:Client") is None


# --- Wizard / UI -------------------------------------------------------------


def test_wizard_collects_user_part() -> None:
    import pytest

    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.wizard.creator import CreatorWizard

    app = QApplication.instance() or QApplication([])
    _ = app
    wizard = CreatorWizard()
    wizard._user_part.setChecked(True)
    wizard._user_commands.setPlainText(
        'CallHidden usersetup.exe\nMD %AppData%\\Vendor\\Config\n\n'
    )
    wizard._collect()
    assert wizard._meta.has_user_part
    assert wizard._meta.user_context_commands == [
        "CallHidden usersetup.exe",
        r"MD %AppData%\Vendor\Config",
    ]

    wizard._user_part.setChecked(False)
    wizard._collect()
    assert not wizard._meta.has_user_part
    assert wizard._meta.user_context_commands == []
