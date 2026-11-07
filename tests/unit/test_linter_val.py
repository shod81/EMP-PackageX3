"""Fixtures and tests for VAL-001..VAL-016."""

from __future__ import annotations

from empirum_core.linter import Severity, lint_document
from empirum_core.parser.lexer import lex_text
from empirum_core.setupinf_contract import STANDARD_SECTIONS


def _codes(text: str) -> set[str]:
    normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
    doc = lex_text(normalized)
    return {d.code for d in lint_document(doc)}


def test_val_001_dangling_section_ref() -> None:
    text = "[Product]\r\n#Set:MissingPart\r\n"
    diags = lint_document(lex_text(text))
    assert any(d.code == "VAL-001" for d in diags)
    assert diags[0].quick_fixes


def test_val_001_ok_when_section_exists() -> None:
    text = "[Product]\r\n#Set:Install\r\n\r\n[Install]\r\nEcho=ok\r\n"
    assert "VAL-001" not in _codes(text)


def test_val_001_standard_set_with_flags() -> None:
    text = (
        "[Product]\r\n"
        "#Set:Product, DONTDELETE\r\n"
        "#Set:Deinstallation, DELETE\r\n"
        "#Reg:Product, DONTDELETE\r\n"
        "\r\n"
        "[Set:Product]\r\nEcho=ok\r\n"
        "\r\n"
        "[Set:Deinstallation]\r\n-Echo=bye\r\n"
        "\r\n"
        "[Reg:Product]\r\n"
    )
    assert "VAL-001" not in _codes(text)


def test_val_001_bare_hash_and_then_target() -> None:
    text = (
        "[Set:Product]\r\n"
        "#InstallMSI\r\n"
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        "\r\n"
        "[InstallMSI]\r\nEcho=i\r\n"
        "\r\n"
        "[RebootRequired]\r\nSetReboot 1\r\n"
    )
    assert "VAL-001" not in _codes(text)


def test_val_002_quoted_predicate() -> None:
    text = '[Set_Install]\r\nIf="FileExists("%App%\\x")"\r\n'
    assert "VAL-002" in _codes(text)


def test_val_002_ok_unquoted() -> None:
    text = '[Set_Install]\r\nIf=FileExists("%App%\\x")\r\n'
    assert "VAL-002" not in _codes(text)


def test_val_003_deltree_backslash() -> None:
    text = "[Set_Uninstall]\r\nDelTree=%Dst%\\App\\\r\n"
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-003"]
    assert diags
    assert diags[0].quick_fixes[0].replacement_line == "DelTree=%Dst%\\App"


def test_val_004_missing_prefix() -> None:
    text = "[Error_Uninstall]\r\nAbort=fail\r\n"
    assert "VAL-004" in _codes(text)


def test_val_004_ok_with_prefix() -> None:
    text = "[Error_Uninstall]\r\n--Abort=fail\r\n"
    assert "VAL-004" not in _codes(text)


def test_val_005_duplicate_shellinks() -> None:
    text = (
        "[Application]\r\nShellLinks=1\r\n\r\n"
        "[Product]\r\n#Shell:CreateLinks\r\n\r\n"
        "[CreateLinks]\r\nLinkName=X\r\n"
    )
    assert "VAL-005" in _codes(text)


def test_val_006_hkcu_without_aw() -> None:
    text = "[SetupInfo]\r\nProductName=X\r\n\r\n[Set_Registry]\r\nRoot=HKCU\r\n"
    assert "VAL-006" in _codes(text)


def test_val_006_askkill_without_aw() -> None:
    text = (
        "[SetupInfo]\r\nCommand line options=/S2\r\n\r\n"
        "[Set:AppActive]\r\nAskKillProcesses 300,APP1\r\n"
    )
    assert "VAL-006" in _codes(text)


def test_val_017_aw_depot_reminder() -> None:
    text = (
        "[SetupInfo]\r\nMethod=MSI\r\nCommand line options=/S2 /AW\r\n\r\n"
        "[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n"
    )
    assert "VAL-017" in _codes(text)


def test_val_018_reg_minus_is_uninstall_time() -> None:
    text = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n"
        "[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n\r\n"
        "[Reg:Product]\r\n"
        '-HKLM,"Software\\Old\\Product"\r\n'
    )
    assert "VAL-018" in _codes(text)


def test_val_007_dangerous_root() -> None:
    text = "[Set_Uninstall]\r\n-HKLM,SOFTWARE\\Microsoft\r\n"
    assert "VAL-007" in _codes(text)


def test_val_008_missing_errorlevel() -> None:
    text = "[Set_Install]\r\nCall=msiexec /i setup.msi\r\nEcho=done\r\n"
    assert "VAL-008" in _codes(text)


def test_val_009_reboot() -> None:
    text = "[Application]\r\nReboot=1\r\n"
    assert "VAL-009" in _codes(text)


def test_val_010_hardcoded_path() -> None:
    text = "[Set_Install]\r\nDst=C:\\Program Files\\Demo\r\n"
    assert "VAL-010" in _codes(text)


def test_val_011_missing_sleep() -> None:
    text = "[Set_Uninstall]\r\nCall=msiexec /x setup.msi\r\nDelTree=%Dst%\r\n"
    assert "VAL-011" in _codes(text)


def test_val_011_ok_with_sleep() -> None:
    text = (
        "[Set_Uninstall]\r\nCall=msiexec /x setup.msi\r\nSleep=3000\r\nDelTree=%Dst%\r\n"
    )
    assert "VAL-011" not in _codes(text)


def test_val_012_missing_sections() -> None:
    text = "[SetupInfo]\r\nDescription=X\r\n\r\n[Application]\r\nProductName=X\r\n"
    assert "VAL-012" in _codes(text)


def test_val_012_quickfix_is_applicable() -> None:
    """M-4: the VAL-012 fix names its target section and carries the body."""
    text = "[SetupInfo]\r\nDescription=X\r\n\r\n[Application]\r\nProductName=X\r\n"
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-012"]
    assert diags
    fixes = {}
    for d in diags:
        fix = d.quick_fixes[0]
        assert fix.note == "insert_section"
        assert fix.section_name and fix.section_name in STANDARD_SECTIONS
        fixes[fix.section_name] = fix
    # Plain stub: header only (inserting it yields an empty section).
    assert fixes["Set:Product"].replacement_line == "[Set:Product]"
    # Error handler: canonical Abort block travels with the fix.
    assert fixes["Set:InstallationError"].replacement_line == (
        "[Set:InstallationError]\r\n"
        "ErrorLogMsg %ErrorLogMessage%\r\n"
        "Abort %ErrorText%"
    )
    assert fixes["Set:DeInstallationError"].replacement_line == (
        "[Set:DeInstallationError]\r\n"
        "-ErrorLogMsg %ErrorLogMessage%\r\n"
        "-Abort %ErrorText%"
    )


def test_clean_fragment_skips_structure_rules() -> None:
    """Fragments without SetupInfo/Setup/Application are editor scratch – no VAL-012."""
    text = "[Set_Install]\r\nEcho=ok\r\n"
    assert "VAL-012" not in _codes(text)


def test_clean_package_has_no_errors() -> None:
    from empirum_core.inspect import PackageMetadata
    from empirum_core.templates import render_template

    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.0",
        manufacturer="Acme",
        package_type="MSI",
        source_path=r"C:\tmp\Demo.msi",
    )
    diags = lint_document(render_template("msi", meta))
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert errors == []


def test_val_016_msi_flags() -> None:
    text = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n"
        "[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n"
        "\r\n"
        "[InstallMSI]\r\n"
        'CallHidden MsiExec /I "%Src%\\Files\\x.msi" /qn\r\n'
    )
    assert "VAL-016" in _codes(text)


def test_builtin_rule_count() -> None:
    from empirum_core.linter import builtin_rules

    # VAL-001..031 + user-part rules VAL-032..034
    assert len(builtin_rules()) == 34


def test_val_019_flags_undocumented_command() -> None:
    text = "[Set:Product]\r\nFrobnicate /all\r\nEcho ok\r\n"
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-019"]
    assert len(diags) == 1
    assert "Frobnicate" in diags[0].message


def test_val_019_clean_for_reference_commands() -> None:
    text = (
        "[Set:Product]\r\n"
        "AddMeter -1\r\n"
        'CallHidden MsiExec /I "%Src%\\Files\\a.msi" /qn\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        "Sleep 3000\r\n"
        "-Del \"%Temp%\\x.log\"\r\n"
    )
    assert "VAL-019" not in _codes(text)


def test_val_020_if_then_requires_endif() -> None:
    bad = '[Set:Product]\r\nIf %ErrorLevel% == "3010" Then "RebootRequired"\r\n'
    assert "VAL-020" in _codes(bad)
    good = '[Set:Product]\r\nIf %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
    assert "VAL-020" not in _codes(good)
    legacy_no_then = "[Set_Install]\r\nIf=%ErrorLevel%\r\n"
    assert "VAL-020" not in _codes(legacy_no_then)


def test_val_021_flags_undefined_variable() -> None:
    text = "[Set:Product]\r\nEcho %UnknownVar%\r\n"
    assert "VAL-021" in _codes(text)


def test_val_021_accepts_builtin_and_document_defined() -> None:
    text = (
        "[Application]\r\nProductName=X\r\n\r\n"
        "[Environment]\r\nV_Custom=1\r\n\r\n"
        "[Strings:09]\r\nLabel=Text\r\n\r\n"
        "[Set:Product]\r\n"
        "Set MSIGUID_X64 = GetUninstallKeyName (%ProductName%,x64)\r\n"
        "Echo %ProductName% %V_Custom% %Label% %MSIGUID_X64% %Temp%\r\n"
    )
    assert "VAL-021" not in _codes(text)


def test_val_015_accepts_quoted_srcdir_and_setupinfdir() -> None:
    text = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nSrcDir=\"..\"\r\nSetupInfDir=\"Install\"\r\n"
    )
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-015"]
    assert all("SrcDir" not in d.message for d in diags)
    assert all("SetupInfDir" not in d.message for d in diags)


def test_fresh_templates_do_not_trigger_val_006() -> None:
    """S3: comment placeholders must not count as active user-part features."""
    from empirum_core.inspect import PackageMetadata
    from empirum_core.templates import render_template

    meta = PackageMetadata(
        product_name="Demo",
        product_version="1.0",
        manufacturer="Acme",
        package_type="MSI",
        source_path=r"C:\tmp\Demo.msi",
    )
    for kind in ("msi", "exe", "script", "links"):
        diags = lint_document(render_template(kind, meta))
        assert not any(d.code == "VAL-006" for d in diags), kind


def test_val_001_ignores_commented_refs() -> None:
    text = "[Product]\r\n; #Set:OldStuff\r\n"
    assert "VAL-001" not in _codes(text)


def test_val_006_still_fires_for_active_hkcu() -> None:
    text = "[SetupInfo]\r\nProductName=X\r\n\r\n[Set_Registry]\r\nRoot=HKCU\r\n"
    assert "VAL-006" in _codes(text)


def test_val_016_ignores_commented_msiexec() -> None:
    text = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n\r\n"
        "[Set:Product]\r\n; CallHidden MsiExec /I x.msi /qn ALLUSERS=1\r\n"
    )
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-016"]
    # The commented call must not count as install line: no flag diagnostics
    # from it – only the legitimate "no active MsiExec" warning may appear.
    assert not any("empfohlene Flags" in d.message for d in diags)


def test_val_007_dangerous_root_quoted() -> None:
    text = '[Set_Uninstall]\r\n-HKLM,"SOFTWARE\\Microsoft\\"\r\n'
    assert "VAL-007" in _codes(text)


def test_val_008_recognizes_rawline_callhidden_style() -> None:
    text = "[Set_Install]\r\nCallHidden setup.exe /S\r\nEcho=done\r\n"
    assert "VAL-008" in _codes(text)


def test_val_011_call_if_sleep_pattern_ok() -> None:
    text = (
        "[Set_Uninstall]\r\nCall=msiexec /x setup.msi\r\nIf=%ErrorLevel%\r\n"
        "Sleep=3000\r\nDelTree=%Dst%\r\n"
    )
    assert "VAL-011" not in _codes(text)


def test_val_011_rawline_msiexec_with_sleep() -> None:
    text = (
        '[Set_Uninstall]\r\n-CallHidden MsiExec /X setup.msi /qn\r\n'
        '-Sleep 3000\r\n-DelTree "%Dst%"\r\n'
    )
    assert "VAL-011" not in _codes(text)


def test_val_011_still_warns_without_sleep() -> None:
    text = "[Set_Uninstall]\r\nCall=msiexec /x setup.msi\r\nDelTree=%Dst%\r\n"
    assert "VAL-011" in _codes(text)


def test_val_010_quickfix_uses_defined_variables() -> None:
    text = (
        "[Set_Install]\r\nDst=C:\\Program Files\\Demo\r\n"
        "X=C:\\Program Files (x86)\\D2\r\n"
    )
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-010"]
    fixes = [d.quick_fixes[0].replacement_line or "" for d in diags]
    assert any(f == r"Dst=%ProgramFiles%\Demo" for f in fixes)
    assert any(f == r"X=%ProgramFiles(x86)%\D2" for f in fixes)
    assert not any("ProgramFilesSys" in f for f in fixes)


def test_val_006_quickfix_preserves_legacy_cmdline_key() -> None:
    text = (
        "[SetupInfo]\r\nCmdLine=/S2\r\n\r\n[Set_Registry]\r\nRoot=HKCU\r\n"
    )
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-006"]
    assert diags
    assert diags[0].quick_fixes[0].replacement_line == "CmdLine=/S2 /AW"


def test_val_006_awx_does_not_suppress() -> None:
    text = "[SetupInfo]\r\nCommand line options=/S2 /AWX\r\n\r\n[Set_Registry]\r\nRoot=HKCU\r\n"
    assert "VAL-006" in _codes(text)


def test_val_017_requires_real_aw() -> None:
    base = (
        "[SetupInfo]\r\nMethod=MSI\r\nCommand line options=/S2 {opt}\r\n\r\n"
        "[Setup]\r\nVersion=14.2\r\n\r\n[Application]\r\nProductName=X\r\n"
    )
    assert "VAL-017" in _codes(base.format(opt="/AW"))
    assert "VAL-017" not in _codes(base.format(opt="/AWX"))


def test_val_005_detects_quoted_shelllinks() -> None:
    text = (
        '[Application]\r\nShellLinks="1"\r\n\r\n'
        "[Product]\r\n#Shell:CreateLinks\r\n\r\n"
        "[CreateLinks]\r\nLinkName=X\r\n"
    )
    assert "VAL-005" in _codes(text)


def test_val_002_quickfix_only_when_effective() -> None:
    text = '[Set_Install]\r\nIf="FileExists(%App%\\x)" extra\r\n'
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-002"]
    assert diags
    fix = diags[0].quick_fixes[0].replacement_line
    assert fix is not None and fix.startswith('If=FileExists(')


def test_val_001_dedups_repeated_refs_on_one_line() -> None:
    text = "[Product]\r\n#Set:Missing then #Set:Missing\r\n"
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-001"]
    assert len(diags) == 1


def test_val_016_recognizes_msiexec_exe_form() -> None:
    text = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n\r\n"
        '[Set:Product]\r\nCallHidden MsiExec.exe /I"%Src%\\Files\\x.msi" /qn\r\n'
    )
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-016"]
    # must be the flags warning on the call line, not "ohne MsiExec /I"
    assert diags and "empfohlene Flags" in diags[0].message
    assert diags[0].line is not None

    good = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n\r\n"
        "[Set:Product]\r\n"
        'CallHidden MsiExec.exe /I"%Src%\\Files\\x.msi" ALLUSERS="1" '
        'REBOOT=REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn\r\n'
    )
    assert not [d for d in lint_document(lex_text(good)) if d.code == "VAL-016"]


def test_val_021_accepts_documented_appdata() -> None:
    text = (
        "[Set:Product]\r\n"
        'CallHidden xcopy.exe "%Src%\\Files\\Dir" "%AppData%\\Dir" /S /E /Y\r\n'
        "-Del %LocalAppData%\\Cache\\x.dat\r\n"
    )
    assert "VAL-021" not in _codes(text)


def test_val_019_accepts_md_directory_command() -> None:
    """MD (Verzeichnis anlegen) is field-standard - no VAL-019 warning."""
    text = (
        "[Set:Product]\r\n"
        "MD C:\\adflow_generic\\\r\n"
        "MD C:\\adflow_generic\\bin\r\n"
        "MD C:\\adflow_generic\\config\r\n"
        "Echo done\r\n"
    )
    assert "VAL-019" not in _codes(text)


def test_val_008_taskkill_exempt() -> None:
    text = (
        "[Set:Product]\r\n"
        'CallHidden cmd.exe /c taskkill /F /IM "ax.exe"\r\n'
        'Call taskkill.exe /F /IM "notepad.exe"\r\n'
        "Echo done\r\n"
    )
    assert "VAL-008" not in _codes(text)


def test_val_013_shortnames_severity_info() -> None:
    from empirum_core.setupinf_contract import APPLICATION_KEYS

    lines = ["[Application]"]
    for key in APPLICATION_KEYS:
        if key.casefold() not in {"productnameshort", "developernameshort"}:
            lines.append(f"{key}=DummyValue")
    text = "\r\n".join(lines) + "\r\n"

    doc = lex_text(text)
    diags = [d for d in lint_document(doc) if d.code == "VAL-013"]

    assert len(diags) == 2
    assert all(d.severity == Severity.INFO for d in diags)
    assert any("ProductNameShort" in d.message for d in diags)
    assert any("DeveloperNameShort" in d.message for d in diags)

    text_missing_prod = "[Application]\r\nDeveloperName=Hodrius\r\n"
    doc_missing = lex_text(text_missing_prod)
    errors = [
        d
        for d in lint_document(doc_missing)
        if d.code == "VAL-013" and d.severity == Severity.ERROR
    ]
    assert any("ProductName" in d.message for d in errors)


def test_val_022_flags_procedural_commands_in_reg_sections() -> None:
    bad1 = (
        "[Reg:Product]\r\n"
        'If "%HKLM,SYSTEM\\CurrentControlSet\\Services\\bfs,Start%" == "2" '
        'Then "Set:Then_1" EndIf\r\n'
    )
    assert "VAL-022" in _codes(bad1)

    bad2 = (
        "[Reg:Product]\r\n"
        'CallHidden reg.exe add "HKLM\\Software\\Test" /v Start /t REG_DWORD /d 4 /f\r\n'
    )
    assert "VAL-022" in _codes(bad2)

    bad3 = (
        "[Reg:OnUninstallProduct]\r\n"
        'RegModifyDWord "HKLM\\Software\\Test" Start 2\r\n'
    )
    assert "VAL-022" in _codes(bad3)

    good = (
        "[Reg:Product]\r\n"
        '; Normal comment is allowed\r\n'
        'HKLM,"Software\\Acme\\Tool","Path",0x00000000,"C:\\Acme\\Tool"\r\n'
        '-HKLM,"Software\\Acme\\OldTool"\r\n'
    )
    assert "VAL-022" not in _codes(good)


def test_val_007_flags_system_services_deletion() -> None:
    text = '[Set_Uninstall]\r\n-HKLM,"SYSTEM\\CurrentControlSet\\Services\\bfs\\Start"\r\n'
    assert "VAL-007" in _codes(text)
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-007"]
    assert any("Services" in d.message for d in diags)


def test_val_021_accepts_vardefinfo_variables() -> None:
    text = (
        "[VarDefInfo]\r\n"
        "VM_CustomPath, STRING, 0\r\n"
        "VU_ConfigKey = 1\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        'Echo "%VM_CustomPath% %VU_ConfigKey%"\r\n'
    )
    assert "VAL-021" not in _codes(text)


def test_val_023_flags_missing_replaceenv() -> None:
    bad = (
        "[Set:Product]\r\n"
        "Set MSIGUID = GetUninstallKeyName (%ProductName%, x64)\r\n"
        'CallHidden MsiExec /X "%MSIGUID%" /qn\r\n'
    )
    assert "VAL-023" in _codes(bad)
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-023"]
    assert any("MSIGUID" in d.message for d in diags)

    bad_reg = (
        "[Set:Product]\r\n"
        'Set RegPath = "%HKLM,Software\\Vendor\\App,InstallDir%"\r\n'
        'Echo "%RegPath%"\r\n'
    )
    assert "VAL-023" in _codes(bad_reg)


def test_val_023_accepts_when_replaceenv_present() -> None:
    good = (
        "[Set:Product]\r\n"
        "Set MSIGUID = GetUninstallKeyName (%ProductName%, x64)\r\n"
        "ReplaceEnv MSIGUID\r\n"
        'CallHidden MsiExec /X "%MSIGUID%" /qn\r\n'
    )
    assert "VAL-023" not in _codes(good)


def test_val_024_flags_abort_without_errorlogmsg() -> None:
    bad = (
        "[Set:InstallError]\r\n"
        'Abort "Fehler bei der Installation"\r\n'
    )
    assert "VAL-024" in _codes(bad)
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-024"]
    assert any("ErrorLogMsg" in d.message for d in diags)


def test_val_024_accepts_abort_with_preceding_errorlogmsg() -> None:
    good = (
        "[Set:InstallError]\r\n"
        'ErrorLogMsg "Fehlercode: %ErrorLevel%"\r\n'
        'Abort "Fehler bei der Installation"\r\n'
    )
    assert "VAL-024" not in _codes(good)


def test_val_025_flags_sleep_equal_syntax_with_quickfix() -> None:
    bad1 = "[Set:Product]\r\nSleep=3000\r\n"
    assert "VAL-025" in _codes(bad1)
    diags = [d for d in lint_document(lex_text(bad1)) if d.code == "VAL-025"]
    assert len(diags) == 1
    assert diags[0].severity == Severity.ERROR
    assert diags[0].quick_fixes
    assert diags[0].quick_fixes[0].replacement_line == "Sleep 3000"

    bad2 = "[Set:Product]\r\n-Sleep = 2000\r\n"
    assert "VAL-025" in _codes(bad2)
    diags2 = [d for d in lint_document(lex_text(bad2)) if d.code == "VAL-025"]
    assert diags2[0].quick_fixes[0].replacement_line == "-Sleep 2000"


def test_val_025_accepts_valid_sleep_syntax() -> None:
    good = "[Set:Product]\r\nSleep 3000\r\n-Sleep 1500\r\n"
    assert "VAL-025" not in _codes(good)


def test_val_026_flags_run_command_with_callhidden_fix() -> None:
    bad = '[Set:Product]\r\nRun "%App%\\tools\\register_bg.exe"\r\n'
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-026"]
    assert diags
    assert diags[0].severity == Severity.ERROR
    assert diags[0].quick_fixes
    assert diags[0].quick_fixes[0].replacement_line == (
        'CallHidden "%App%\\tools\\register_bg.exe"'
    )
    # VAL-019 must not double-flag the proven non-existent command
    assert "VAL-019" not in _codes(bad)


def test_val_026_flags_checklanadministrator_with_delete_fix() -> None:
    bad = "[Set:Product]\r\nCheckLanAdministrator\r\n"
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-026"]
    assert diags
    assert diags[0].quick_fixes[0].note == "delete_line"


def test_val_026_flags_alias_predicates_with_rename_fix() -> None:
    bad = (
        "[Set:Product]\r\n"
        'If FileExists ("%App%\\app.exe") == "1" Then "Set:OK" EndIf\r\n'
        "\r\n"
        "[Set:OK]\r\nEcho ok\r\n"
    )
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-026"]
    assert diags
    assert diags[0].quick_fixes[0].replacement_line == (
        'If DoesFileExist ("%App%\\app.exe") == "1" Then "Set:OK" EndIf'
    )


def test_val_026_flags_regvalue_and_service_predicates() -> None:
    bad = (
        "[Set:Product]\r\n"
        'If RegValueExists ("HKLM,SOFTWARE\\Vendor,License") == "1" Then "Set:OK" EndIf\r\n'
        'If ServiceExists ("Spooler") == "1" Then "Set:OK" EndIf\r\n'
        "\r\n"
        "[Set:OK]\r\nEcho ok\r\n"
    )
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-026"]
    assert len(diags) == 2
    reg_diag = next(d for d in diags if "RegValueExists" in d.message)
    assert "DoesRegKeyExist" in reg_diag.message
    svc_diag = next(d for d in diags if "ServiceExists" in d.message)
    assert "CurrentControlSet" in svc_diag.message
    assert svc_diag.quick_fixes[0].note == "manual"


def test_val_026_flags_predicates_in_requirements_section() -> None:
    bad = "[Requirements]\r\nFileExists(\"%App%\\app.exe\")\r\n"
    assert "VAL-026" in _codes(bad)


def test_val_026_accepts_verified_predicates_and_commands() -> None:
    good = (
        "[Set:Product]\r\n"
        'If DoesPathExist ("%App%") == "1" Then "Set:OK" EndIf\r\n'
        'If DoesTextInFileExist ("Liz", "%App%\\config.ini") == "1" Then "Set:OK" EndIf\r\n'
        'CallHidden MsiExec /I "%Src%\\setup.msi" /qn\r\n'
        "\r\n"
        "[Set:OK]\r\nEcho ok\r\n"
    )
    assert "VAL-026" not in _codes(good)


def test_val_027_flags_old_qword_constant_with_quickfix() -> None:
    bad = '[Reg:Product]\r\nHKLM,"Software\\Vendor","Start",0x00010004,4\r\n'
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-027"]
    assert diags
    assert diags[0].severity == Severity.WARNING
    assert diags[0].quick_fixes
    assert diags[0].quick_fixes[0].replacement_line == (
        'HKLM,"Software\\Vendor","Start",0x00040001,4'
    )


def test_val_027_accepts_official_codes_and_additive_flags() -> None:
    good = (
        "[Reg:Product]\r\n"
        'HKLM,"Software\\Vendor","SZ",0x00000000,"1"\r\n'
        'HKLM,"Software\\Vendor","DW",0x00010001,1\r\n'
        'HKLM,"Software\\Vendor","QW",0x00040001,4\r\n'
        'HKLM,"Software\\Vendor","None",0x00020001,""\r\n'
        'HKLM,"Software\\Vendor","BinSz",0x10000001,"01,02"\r\n'
        'HKLM,"Software\\Vendor","OnlyIfAbsent",0x00010002,1\r\n'
        'HKLM,"Software\\Vendor","Append",0x00000008,"x"\r\n'
        'HKLM,"Software\\Vendor","EmptyKey",0x00000010,""\r\n'
        'HKLM,"Software\\Vendor","QuotedHex",0x00000001,"0x00FF"\r\n'
    )
    assert "VAL-027" not in _codes(good)


def test_val_027_flags_garbage_code_without_quickfix() -> None:
    bad = '[Reg:Product]\r\nHKLM,"Software\\Vendor","V",0x12345678,1\r\n'
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-027"]
    assert diags
    assert not diags[0].quick_fixes


def test_val_028_flags_prompt_in_silent_package() -> None:
    bad = (
        "[SetupInfo]\r\n"
        "Command line options=/S1\r\n"
        "\r\n"
        "[Prompts]\r\n"
        "RebootNow=Sofort neu starten?, JA/NEIN, NEIN\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Prompt RebootNow\r\n"
        "AskKillProcesses 60, AppProc\r\n"
    )
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-028"]
    assert len(diags) == 2
    assert diags[0].severity == Severity.WARNING


def test_val_028_accepts_prompt_at_visible_silent_level() -> None:
    good = (
        "[SetupInfo]\r\n"
        "Command line options=/S2\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Prompt RebootNow\r\n"
    )
    assert "VAL-028" not in _codes(good)


def test_val_029_flags_abortsilent_success_semantics() -> None:
    bad = "[Set:Product]\r\nAbortSilent \"überspringe Altlast\"\r\n"
    diags = [d for d in lint_document(lex_text(bad)) if d.code == "VAL-029"]
    assert diags
    assert "Success" in diags[0].message

    good = "[Set:Product]\r\nAbort \"Fehler\"\r\n"
    assert "VAL-029" not in _codes(good)


def test_undocumented_commands_feature_flag_gates_val_019_and_021() -> None:
    from empirum_core.linter import LintOptions

    text = (
        "[Environment]\r\n"
        "Reg=4100\r\n"
        "\r\n"
        "[Set:Product]\r\n"
        "Set X = HexToString (\"%Reg%\", 1)\r\n"
        "CollapseEnv X\r\n"
        'Echo Ziel: %DstDir%\r\n'
    )
    doc = lex_text(text)

    # Flag off (default): secret command/variable are flagged as unknown
    codes_off = {d.code for d in lint_document(doc)}
    assert "VAL-019" in codes_off
    assert "VAL-021" in codes_off

    # Flag on: both count as known
    codes_on = {
        d.code
        for d in lint_document(doc, options=LintOptions(undocumented_commands=True))
    }
    assert "VAL-019" not in codes_on
    assert "VAL-021" not in codes_on


def test_val_030_utf8_bom_error() -> None:
    doc = lex_text("[SetupInfo]\r\nProductName=Test\r\n")
    doc.has_bom = True
    diags = lint_document(doc)
    val30 = [d for d in diags if d.code == "VAL-030"]
    assert len(val30) == 1
    assert val30[0].severity == Severity.ERROR
    assert "BOM" in val30[0].message
    assert any(f.note == "strip_bom_and_set_cp1252" for f in val30[0].quick_fixes)


def test_val_030_mojibake_bom_residue() -> None:
    doc = lex_text("[SetupInfo]\r\nProductName=Test\r\n")
    doc.sections[0].header_raw = "ï»¿[SetupInfo]"
    diags = lint_document(doc)
    val30 = [d for d in diags if d.code == "VAL-030"]
    assert len(val30) == 1
    assert val30[0].severity == Severity.ERROR


def test_val_031_utf8_encoding_declaration_warning() -> None:
    doc = lex_text("[SetupInfo]\r\nProductName=Test\r\n", encoding_name="utf-8")
    doc.has_bom = False
    diags = lint_document(doc)
    val31 = [d for d in diags if d.code == "VAL-031"]
    assert len(val31) == 1
    assert val31[0].severity == Severity.WARNING
    assert "utf-8" in val31[0].message
    assert any(f.note == "set_cp1252" for f in val31[0].quick_fixes)


def test_val_031_non_cp1252_character_error() -> None:
    from empirum_core.ast.model import RawLine

    doc = lex_text("[Set:Product]\r\n", encoding_name="cp1252")
    doc.sections[0].lines.append(RawLine(text="Echo Pfeil: ➔", span=None))
    diags = lint_document(doc)
    val31_errors = [d for d in diags if d.code == "VAL-031" and d.severity == Severity.ERROR]
    assert len(val31_errors) == 1
    assert "U+2794" in val31_errors[0].message


def test_val_030_and_031_cp1252_clean() -> None:
    doc = lex_text("[SetupInfo]\r\nProductName=Büro\r\n", encoding_name="cp1252")
    doc.has_bom = False
    diags = lint_document(doc)
    assert not any(d.code in {"VAL-030", "VAL-031"} for d in diags)



