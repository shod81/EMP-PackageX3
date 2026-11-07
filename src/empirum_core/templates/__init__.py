"""Standard-aligned Empirum Setup.inf templates (parametrized text → AST).

Derived from the Matrix42 package conventions documented in the project
knowledge base (Setup.inf-Vorlagen MSI / Unattend / Skripte / Links):
required sections, Application identity keys, Installer copy block,
SrcDir/SetupInfDir path contract, DONTDELETE/DELETE Product flow,
REBOOT=REALLYSUPPRESS + ErrorLevel 3010 handling.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from empirum_core.ast.model import Document
from empirum_core.inspect import PackageMetadata, ShellLinkSpec
from empirum_core.parser.lexer import lex_text
from empirum_core.parser.reg_parser import (
    format_reg_entry_empirum,
    reg_has_hkcu,
)
from empirum_core.setupinf_contract import (
    ERROR_SECTION_BODIES,
    USER_PART_SECTION,
    product_refs_for,
)

_TEMPLATE_KINDS = ("msi", "exe", "script", "links")



def _sanitize(value: str) -> str:
    """Neutralize line/section injection from foreign metadata values."""
    return re.sub(r"[\r\n\t]+", " ", value).strip()


def _sanitize_meta(meta: PackageMetadata) -> PackageMetadata:
    return replace(
        meta,
        product_name=_sanitize(meta.product_name),
        product_version=_sanitize(meta.product_version),
        manufacturer=_sanitize(meta.manufacturer),
        product_code=_sanitize(meta.product_code),
        properties={k: _sanitize(v) for k, v in meta.properties.items()},
        folder_copies=[
            replace(
                fc,
                folder_name=_sanitize(fc.folder_name),
                target_path=_sanitize(fc.target_path),
                xcopy_flags=_sanitize(fc.xcopy_flags),
            )
            for fc in meta.folder_copies
        ],
        registry_entries=[
            replace(
                re_entry,
                key_path=_sanitize(re_entry.key_path),
                value_name=_sanitize(re_entry.value_name),
                value_data=_sanitize(re_entry.value_data),
            )
            for re_entry in meta.registry_entries
        ],
        reg_files=[
            replace(
                rf,
                file_name=_sanitize(rf.file_name),
                target_subfolder=_sanitize(rf.target_subfolder),
            )
            for rf in meta.reg_files
        ],
        shell_links=[
            replace(
                sl,
                name=_sanitize(sl.name),
                subfolder=_sanitize(sl.subfolder),
                target=_sanitize(sl.target),
                arguments=_sanitize(sl.arguments),
                working_dir=_sanitize(sl.working_dir),
                description=_sanitize(sl.description),
                icon_file=_sanitize(sl.icon_file),
            )
            for sl in meta.shell_links
        ],
    )



def render_template(kind: str, meta: PackageMetadata) -> Document:
    kind_l = kind.casefold()
    meta = _sanitize_meta(meta)
    if kind_l == "msi":
        text = _msi_template(meta)
    elif kind_l in {"exe", "unattend", "unattended"}:
        text = _exe_template(meta)
    elif kind_l == "script":
        text = _script_template(meta)
    elif kind_l in {"links", "link"}:
        text = _links_template(meta)
    else:
        raise ValueError(
            f"Unbekannter Vorlagentyp {kind!r} (erlaubt: {'/'.join(_TEMPLATE_KINDS)})"
        )
    doc = lex_text(text, encoding_name="cp1252", newline="\r\n")
    doc.encoding_name = "cp1252"
    doc.has_bom = False
    doc.newline = "\r\n"
    return doc


def _short(value: str, limit: int = 8) -> str:
    cleaned = "".join(c for c in value.upper() if c.isalnum())
    return (cleaned or "PKG")[:limit]


def _src_leaf(meta: PackageMetadata) -> str:
    if meta.source_path:
        return Path(meta.source_path).name
    return "setup.bin"


def _platform(meta: PackageMetadata) -> str:
    arch = (meta.architecture or "*").strip()
    if arch.casefold() in {"any", "arm64", ""}:
        return "*"
    return arch


def silent_args_for(meta: PackageMetadata) -> str:
    """Public helper: resolve EXE silent switches for UI / templates."""
    return _silent_exe_args(meta)


def _silent_exe_args(meta: PackageMetadata) -> str:
    custom = (meta.properties.get("silent_args") or "").strip()
    if custom:
        return custom
    kind = (meta.exe_kind or "").casefold()
    if kind == "nsis":
        return "/S"
    if kind == "inno":
        return "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART"
    if kind in {"installshield", "is"}:
        return "/s /sms"
    return "/quiet /norestart"


def _kill_process_entries(meta: PackageMetadata) -> list[tuple[str, str, str]]:
    """Parse kill_processes property: exe|Display|ABORT;exe2|Name|CONTINUE."""
    raw = (meta.properties.get("kill_processes") or "").strip()
    if not raw:
        return []
    out: list[tuple[str, str, str]] = []
    for i, chunk in enumerate(raw.split(";"), start=1):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split("|")]
        exe = parts[0] if parts else f"app{i}.exe"
        label = parts[1] if len(parts) > 1 and parts[1] else Path(exe).stem
        mode = parts[2] if len(parts) > 2 and parts[2] else "ABORT"
        out.append((exe, label, mode.upper()))
    return out


def _processes_block(meta: PackageMetadata) -> str:
    entries = _kill_process_entries(meta)
    lines = ["[Processes]\r\n"]
    if not entries:
        lines.append(
            "; Prozesse für AskKillProcesses (Unattend/EXE) – Platzhalter anpassen:\r\n"
        )
        lines.append(
            "; APP1=NamederExe01, AnzeigenamefürEndanwender01, KILLPROCESS ABORT\r\n"
        )
    else:
        for idx, (exe, label, mode) in enumerate(entries, start=1):
            lines.append(
                f"APP{idx}={exe}, {label}, KILLPROCESS {mode}\r\n"
            )
    lines.append("\r\n")
    return "".join(lines)


def _app_active_block(meta: PackageMetadata) -> str:
    entries = _kill_process_entries(meta)
    if not entries:
        return (
            "[Set:AppActive]\r\n"
            "; AskKillProcesses – APP1/APP2 in [Processes] hinterlegen, dann aktivieren:\r\n"
            ";AskKillProcesses 300,APP1, APP2\r\n"
            ";-AskKillProcesses 300,APP1, APP2\r\n"
            "\r\n"
        )
    ids = ",".join(f"APP{i}" for i in range(1, len(entries) + 1))
    return (
        "[Set:AppActive]\r\n"
        f"AskKillProcesses 300,{ids}\r\n"
        f"-AskKillProcesses 300,{ids}\r\n"
        "\r\n"
    )


def _has_hkcu(meta: PackageMetadata) -> bool:
    """True when [Reg:Product] receives HKCU entries (directly or via .reg)."""
    if any(e.root.upper() == "HKCU" for e in meta.registry_entries):
        return True
    return any(
        rf.local_source_path and reg_has_hkcu(rf.local_source_path)
        for rf in meta.reg_files
    )


def _standard_header(meta: PackageMetadata, *, method: str, cmdline: str = "/S2") -> str:
    name = meta.product_name or "Package"
    ver = meta.product_version or "1.0.0"
    mfr = meta.manufacturer or "Unknown"
    rev = meta.properties.get("revision", "0")
    name_s = _short(name)
    mfr_s = _short(mfr)
    platform = _platform(meta)
    has_hkcu = _has_hkcu(meta)
    # /AW (Also-for-User) chain (VAL-006): a real user part
    # ([Set:Client]) OR HKCU registry OR the manual property forces the
    # user pass; without /AW Setup.exe runs as SYSTEM only and HKCU values
    # would silently land in the system profile.
    needs_aw = (
        meta.has_user_part
        or has_hkcu
        or meta.properties.get("needs_aw", "").strip().lower() in {"1", "true", "yes"}
    )
    if needs_aw and "/AW" not in cmdline.upper():
        cmdline = f"{cmdline} /AW".strip()
    if _kill_process_entries(meta) and "/AW" not in cmdline.upper():
        # AskKillProcesses is interactive → user part recommended
        cmdline = f"{cmdline} /AW".strip()


    product_code_line = ""
    if meta.product_code.strip():
        product_code_line = f"V_ProductCode={meta.product_code.strip()}\r\n"

    display = name
    if meta.product_code.strip():
        # Prefer ARP DisplayName wildcard; keep ProductCode for reference
        display = f"{name}*"

    return (
        "[SetupInfo]\r\n"
        "Author=\r\n"
        "CreationDate=\r\n"
        "InventoryID=\r\n"
        f"Description={name}\r\n"
        f"Method={method}\r\n"
        "Tested on=\r\n"
        "Dependencies=\r\n"
        f"Command line options={cmdline}\r\n"
        "Last Change=\r\n"
        "Build=0\r\n"
        "\r\n"
        "[VarDefInfo]\r\n"
        "; <Variable>, <Type: 0=Computer 1=User>, <Allow NULL values: 0=No 1=Yes>\r\n"
        "\r\n"
        "[Setup]\r\n"
        "Version=14.2\r\n"
        "ShowCaption=1\r\n"
        "BlockInput=0\r\n"
        f"Platform={platform}\r\n"
        "\r\n"
        "[Requirements]\r\n"
        "\r\n"
        "[Application]\r\n"
        f"ProductName={name}\r\n"
        f"ProductNameShort={name_s}\r\n"
        f"DeveloperName={mfr}\r\n"
        f"DeveloperNameShort={mfr_s}\r\n"
        f"Version={ver}\r\n"
        f"Revision={rev}\r\n"
        "SetupName=%ProductName% %Version% %SetupWizard%\r\n"
        'Text1="%ProductName% %Version%",         Arial,           30, , 2170F3, 4,    , LEFT BOLD ITALIC\r\n'
        'Text2="%DeveloperName%",                 Arial,           24, , 2170F3, 4,    , LEFT BOLD ITALIC\r\n'
        'Text8="%Company%",                       Arial,           18, , 2170F3, 4,  10, RIGHT BOLD ITALIC\r\n'
        'Text9="%InstallationFor% %WindowsUser%", Arial,           16, , 2170F3, 4, -18, BOTTOM ITALIC LEFT\r\n'
        "BackgroundColor=EFEFEF,000000\r\n"
        "CopyDialogRect=0%, 0%, 100%, 100%, HCENTER VCENTER\r\n"
        "UserKeyName=$Matrix42Packages$\\%DeveloperName%\\%ProductName%\r\n"
        "MachineKeyName=$Matrix42Packages$\\%DeveloperName%\\%ProductName%\\%Version%\r\n"
        "UninstallKeyName=Matrix42 - %DeveloperName% %ProductName% %Version%\r\n"
        "UninstallDisplayName=Matrix42 - %DeveloperName% %ProductName% %Version%\r\n"
        "UninstallString=%ReinstallString% /U\r\n"
        'ReinstallString="%CommonSetupDir%\\Setup.exe" "%App%\\%SetupInfDir%\\Setup.inf"\r\n'
        'UninstallDisplayIcon="%ApplicationDir%\\%SetupInfDir%\\Setup.ico",0\r\n'
        "UninstallOptions=NOMODIFY SYSTEMCOMPONENT\r\n"
        "HideUninstall=1\r\n"
        "ReinstallMode=1\r\n"
        "SrcDir=..\r\n"
        "ApplicationDir=%CommonAppData%\\$Matrix42Scripts$\\%DeveloperName%\\%ProductName%\\%Version%\r\n"
        "SetupInfDir=Install\r\n"
        "DataDir=%Personal%\r\n"
        "AskUninstallOld=1\r\n"
        "ShellLinks=1\r\n"
        "CommonShellLinks=1\r\n"
        "CreateUnresolvableShellLinks=1\r\n"
        "UseStringSection=Strings:09\r\n"
        "UseSysStringSection=SysStrings:09\r\n"
        "DateWarning=1\r\n"
        "SizeWarning=0\r\n"
        "Reboot=0\r\n"
        "PreventExternalReboot=1\r\n"
        "StartServicesOnReboot=0\r\n"
        "CallTimeOut=3600\r\n"
        "AbortAfterCallTimeOut=1\r\n"
        "DisableCancelButton=1\r\n"
        "ShowEndMessage=1\r\n"
        "EndMessage=%EndMessageDesc%\r\n"
        "\r\n"
        "[Strings:07]\r\n"
        "Disk1=Installationsmedium 1\r\n"
        "EndMessageDesc=Die Installation wurde erfolgreich abgeschlossen!\r\n"
        "ErrorLogMessage=Die Installation/Deinstallation wurde mit einer Fehlermeldung abgebrochen!\r\n"
        "InstallationFor=Installation für:\r\n"
        "InstallerDesc=Dienstprogramm zum Installieren einzelner Komponenten.\r\n"
        "InstallerName=Installationsprogramm\r\n"
        "SetupWizard=Installations-Assistent\r\n"
        "Uninstallation=deinstallieren\r\n"
        "ErrorText=Fehler\r\n"
        "CallingText=beim Aufruf von\r\n"
        f"ProductDesc={name}\r\n"
        "\r\n"
        "[Strings:09]\r\n"
        "Disk1=Installation media 1\r\n"
        "EndMessageDesc=Installation was completed successfully!\r\n"
        "ErrorLogMessage=The installation/uninstallation aborted with an error message!\r\n"
        "InstallationFor=Installation for:\r\n"
        "InstallerDesc=Service program to install single components.\r\n"
        "InstallerName=Setup program\r\n"
        "SetupWizard=Installation Wizard\r\n"
        "Uninstallation=Uninstallation\r\n"
        "ErrorText=Error\r\n"
        "CallingText=launching\r\n"
        f"ProductDesc={name}\r\n"
        "\r\n"
        "[SysStrings:07]\r\n"
        "Users=Benutzer\r\n"
        "\r\n"
        "[SysStrings:09]\r\n"
        "Users=Users\r\n"
        "\r\n"
        "[Environment]\r\n"
        "V_LogFileInstall=%Temp%\\Install_%ProductName%.%Version%.%Revision%.log\r\n"
        "V_LogFileUninstall=%Temp%\\Uninstall_%ProductName%.%Version%.%Revision%.log\r\n"
        "MSILogFileInstall=%Temp%\\MSI_Install_%ProductName%.%Version%.%Revision%.log\r\n"
        "MSILogFileUninstall=%Temp%\\MSI_Uninstall_%ProductName%.%Version%.%Revision%.log\r\n"
        "CommonSetupDir=%CommonFilesDir%\\Setup%SetupBits%\r\n"
        "V_MachineValuesPath=\\\\%EmpirumServer%\\Values$\\MachineValues\\%DomainName%\r\n"
        'V_UserValuesPath=%HKLM,"Software\\matrix42\\Software Depot","HomeServer"%\\Values$\\UserValues\\%UserDomain%\r\n'
        f"V_DisplayName={display}\r\n"
        f"{product_code_line}"
        "\r\n"
        "; Maschinenabhängige Variablen (VM_) – ReplaceEnv in [Product] nicht vergessen\r\n"
        ";VM_<Variable>=%%%V_MachineValuesPath%\\%ComputerName%.ini,%ComputerName%,<Variable>%%\r\n"
        "; Userabhängige Variablen (VU_) – benötigen /AW in SetupInfo und Depot\r\n"
        ";VU_<Variable>=%%%V_UserValuesPath%\\%WindowsUser%.ini,%WindowsUser%,<Variable>%%\r\n"
        "\r\n"
        "[Encryption]\r\n"
        "\r\n"
        "[Disks]\r\n"
        "1=%Disk1%\r\n"
        "\r\n"
        "[Options]\r\n"
        'Installer=%InstallerName%, COPYALWAYS, Installer, "%InstallerDesc%"\r\n'
        'Product=%ProductName%,   COPYALWAYS, Product,   "%ProductDesc%"\r\n'
        "\r\n"
        + _processes_block(meta)
        + "[Installer]\r\n"
        "1:..\\..\\..\\..\\User\\Setup.exe, %CommonSetupDir%, OPTIONAL USEFILENAME DIRECTORY NOSIZEWARNING SETUP, 0\r\n"
        "1:..\\..\\..\\..\\User\\SetupDeu.chm, %CommonSetupDir%, OPTIONAL USEFILENAME DIRECTORY NOSIZEWARNING SETUP, 0\r\n"
        "1:..\\..\\..\\..\\User\\SetupEnu.chm, %CommonSetupDir%, OPTIONAL USEFILENAME DIRECTORY NOSIZEWARNING SETUP, 0\r\n"
        "1:%Temp%\\Setup64.exe, %CommonSetupDir%\\Setup.exe, OPTIONAL ALWAYS NOSIZEWARNING SETUP WINDOWS64, 0\r\n"
        "1:..\\..\\..\\..\\User\\Setup64.exe, %CommonSetupDir%\\Setup.exe, OPTIONAL ALWAYS NOSIZEWARNING SETUP WINDOWS64, 0\r\n"
        "1:%SetupInfDir%\\Setup.inf, , ALWAYS, 0\r\n"
        "1:%SetupInfDir%\\Setup.ico, , OPTIONAL, 0\r\n"
        "; 1:%SetupInfDir%\\Logo.bmp, , NORMAL, 0\r\n"
        "\r\n"
    )


def _format_shell_link(link: ShellLinkSpec) -> str:
    if link.destination.casefold() == "common_desktop":
        shortcut = f'"%CommonDesktop%\\{link.name.strip()}"'
    else:
        sub = f"{link.subfolder.strip()}\\" if link.subfolder.strip() else ""
        shortcut = f'"%CommonPrograms%\\{sub}{link.name.strip()}"'
    target = f'"{link.target.strip()}"' if link.target.strip() else '""'
    args = f'"{link.arguments.strip()}"' if link.arguments.strip() else ""
    wdir = f'"{link.working_dir.strip()}"' if link.working_dir.strip() else ""
    desc = f'"{link.description.strip()}"' if link.description.strip() else ""
    icon = f'"{link.icon_file.strip()}"' if link.icon_file.strip() else ""
    idx = str(link.icon_index) if link.icon_file.strip() else ""
    state = str(link.window_state) if link.window_state != 1 else ""
    parts = [shortcut, target, args, wdir, desc, icon, idx, state]
    while len(parts) > 2 and parts[-1] == "":
        parts.pop()
    return ", ".join(parts) + "\r\n"


def _custom_install_steps(meta: PackageMetadata) -> str:
    lines: list[str] = []
    if meta.folder_copies:
        lines.append("; Zusätzliche Ordner kopieren (cmd /c xcopy für zuverlässige Ausführung in Empirum)\r\n")
        for fc in meta.folder_copies:
            flags = fc.xcopy_flags.strip() or "/S /H /E /V /Y"
            lines.append(
                f'CallHidden cmd.exe /c xcopy "%Src%\\Files\\{fc.folder_name}" "{fc.target_path}" {flags}\r\n'
            )
            lines.append('If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf\r\n')
    if meta.reg_files:
        reg_imports = [rf for rf in meta.reg_files if rf.import_mode == "reg_exe"]
        if reg_imports:
            lines.append("; Registry-Dateien importieren\r\n")
            for rf in reg_imports:
                sub = f"{rf.target_subfolder}\\" if rf.target_subfolder.strip() else ""
                lines.append(
                    f'CallHidden cmd.exe /c reg.exe import "%Src%\\Files\\{sub}{rf.file_name}"\r\n'
                )
                lines.append('If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf\r\n')
    return "".join(lines)


def _custom_uninstall_steps(meta: PackageMetadata) -> str:
    lines: list[str] = []
    if meta.folder_copies:
        cleanup = [fc for fc in meta.folder_copies if fc.delete_on_uninstall]
        if cleanup:
            lines.append("; Bereinigung kopierter Ordner bei Deinstallation\r\n")
            for fc in cleanup:
                lines.append(f'-DelTree "{fc.target_path}"\r\n')
    return "".join(lines)


def _error_sections(meta: PackageMetadata | None = None) -> str:
    reg_lines = ["[Reg:Product]\r\n"]
    if meta and meta.registry_entries:
        for entry in meta.registry_entries:
            reg_lines.append(format_reg_entry_empirum(entry) + "\r\n")
    reg_lines.append("\r\n")

    shell_lines = ["[Shell:Product]\r\n"]
    if meta and meta.shell_links:
        for sl in meta.shell_links:
            shell_lines.append(_format_shell_link(sl))
    shell_lines.append("\r\n")

    # [RebootRequired] keeps the template-only SetReboot body: the skeleton
    # repair deliberately leaves it empty (no forced reboot).
    error_blocks = "".join(
        f"[{name}]\r\n" + "".join(f"{line}\r\n" for line in body) + "\r\n"
        for name, body in ERROR_SECTION_BODIES.items()
    )
    return (
        "[RebootRequired]\r\n"
        "SetReboot 1\r\n"
        "-SetReboot 1\r\n"
        "\r\n"
        + error_blocks
        + "[Reg:OnUninstallProduct]\r\n"
        "\r\n"
        + "".join(reg_lines)
        + "[Ini:Product]\r\n"
        "\r\n"
        "[Security:Product]\r\n"
        "\r\n"
        + "".join(shell_lines)
    )


def _msi_template(meta: PackageMetadata) -> str:
    src = _src_leaf(meta)
    user_part = meta.has_user_part
    body = (
        _product_refs(
            with_app_active=False,
            user_part=user_part,
            reg_machine_only=not _has_hkcu(meta),
        )
        + "[Set:Product]\r\n"
        "AddMeter -1\r\n"
        "Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)\r\n"
        "Set MSIGUID_X86 = GetUninstallKeyName (%V_DisplayName%,x86)\r\n"
        "ReplaceEnv MSIGUID_X64\r\n"
        "ReplaceEnv MSIGUID_X86\r\n"
        'If DoesRegKeyExist ("HKLM,SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%MSIGUID_X64%,UnInstallString") == "1" | DoesRegKeyExist ("HKLM,SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%MSIGUID_X86%,UnInstallString") == "1" Then "RepairMSI" Else "InstallMSI" EndIf\r\n'
        "\r\n"
        "[RepairMSI]\r\n"
        'If "%MSIGUID_X64%" <> "" Then "Reinstall_x64" EndIf\r\n'
        'If "%MSIGUID_X86%" <> "" Then "Reinstall_x86" EndIf\r\n'
        "#InstallMSI\r\n"
        "\r\n"
        "[Reinstall_x64]\r\n"
        'CallHidden MsiExec /X %MSIGUID_X64% REBOOT=REALLYSUPPRESS /qn /L*v "%MSILogFileUninstall%"\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        'If DoesRegKeyExist ("HKLM,SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%MSIGUID_X64%,UnInstallString") == "1" Then "Set:ReinstallationError" EndIf\r\n'
        'Del "%MSILogFileUninstall%"\r\n'
        "\r\n"
        "[Reinstall_x86]\r\n"
        'CallHidden MsiExec /X %MSIGUID_X86% REBOOT=REALLYSUPPRESS /qn /L*v "%MSILogFileUninstall%"\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        'If DoesRegKeyExist ("HKLM,SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%MSIGUID_X86%,UnInstallString") == "1" Then "Set:ReinstallationError" EndIf\r\n'
        'Del "%MSILogFileUninstall%"\r\n'
        "\r\n"
        "[InstallMSI]\r\n"
        "AddMeter -1\r\n"
        f'CallHidden MsiExec /I "%Src%\\Files\\{src}" ALLUSERS="1" REBOOT=REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn /L*v "%MSILogFileInstall%"\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        "Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)\r\n"
        "Set MSIGUID_X86 = GetUninstallKeyName (%V_DisplayName%,x86)\r\n"
        "ReplaceEnv MSIGUID_X64\r\n"
        "ReplaceEnv MSIGUID_X86\r\n"
        'If DoesRegKeyExist ("HKLM,SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%MSIGUID_X64%,UnInstallString") == "0" & DoesRegKeyExist ("HKLM,SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%MSIGUID_X86%,UnInstallString") == "0" Then "Set:InstallationError" EndIf\r\n'
        'Del "%MSILogFileInstall%"\r\n'
        + _custom_install_steps(meta)
        + "\r\n"
        "[Set:Deinstallation]\r\n"
        'If "%MSIGUID_X64%" <> "" Then "Uninstall_x64" EndIf\r\n'
        'If "%MSIGUID_X86%" <> "" Then "Uninstall_x86" EndIf\r\n'
        + _custom_uninstall_steps(meta)
        + "-ReplaceEnv MSIGUID_X64\r\n"
        "-ReplaceEnv MSIGUID_X86\r\n"
        "-Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)\r\n"
        "-Set MSIGUID_X86 = GetUninstallKeyName (%V_DisplayName%,x86)\r\n"
        "-AddMeter -1\r\n"
        "\r\n"
        "[Uninstall_x64]\r\n"
        '-CallHidden MsiExec /X %MSIGUID_X64% REBOOT=REALLYSUPPRESS /qn /L*v "%MSILogFileUninstall%"\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        "Sleep 3000\r\n"
        '-Del "%MSILogFileUninstall%"\r\n'
        "\r\n"
        "[Uninstall_x86]\r\n"
        '-CallHidden MsiExec /X %MSIGUID_X86% REBOOT=REALLYSUPPRESS /qn /L*v "%MSILogFileUninstall%"\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        "Sleep 3000\r\n"
        '-Del "%MSILogFileUninstall%"\r\n'
        "\r\n"
    )
    return (
        _standard_header(meta, method="MSI", cmdline="/S2")
        + body
        + _user_part_block(meta)
        + _error_sections(meta)
    )


def _product_refs(
    *,
    with_app_active: bool = False,
    user_part: bool = False,
    reg_machine_only: bool = True,
) -> str:
    """Standard [Product] GOSUB block (install top→bottom, uninstall bottom→top).

    Refs come from ``setupinf_contract.product_refs_for`` (single source of
    truth, shared with the standard skeleton repair). With a user part the machine
    entries carry the ``MACHINE`` flag and ``#Set:Client, CLIENT`` closes the
    block.
    """
    lines = ["[Product]\r\n"]
    if with_app_active:
        lines.append("#Set:AppActive, DONTDELETE\r\n")
    lines.extend(
        f"{ref}\r\n"
        for _target, ref in product_refs_for(
            user_part=user_part, reg_machine_only=reg_machine_only
        )
    )
    if with_app_active:
        lines.append("#Set:AppActive, DELETE\r\n")
    lines.append("\r\n")
    return "".join(lines)


# Call-style statements need the 3010/0 ErrorLevel pair right below them
# (VAL-008); user-supplied commands get it appended automatically unless the
# next line already checks %ErrorLevel% itself.
_CALL_LIKE_RE = re.compile(r"(?i)^-?(call|callhidden|callrunas|callrunashidden)\b")
_ERRORLEVEL_RE = re.compile(r'(?i)^-?if\s+"?%errorlevel%')


def _user_part_block(meta: PackageMetadata) -> str:
    """[Set:Client] body for user-context commands (per-user context).

    Empty string for pure machine packages — the section is only emitted when
    there is a real user part, and it is never emitted twice (single block,
    merged commands).
    """
    commands = [c.strip() for c in meta.user_context_commands if c.strip()]
    if not commands:
        return ""
    lines = [
        f"[{USER_PART_SECTION}]\r\n"
        "; Benutzerteil (User-Part) – läuft nur im Benutzerkontext (/AW + CLIENT-Flag);\r\n"
        "; %AppData%/%Desktop%/HKCU zeigen hier auf den angemeldeten Benutzer\r\n"
    ]
    for i, cmd in enumerate(commands):
        # A '[' line would inject a section header into the block – neutralize.
        lines.append(f";{cmd}\r\n" if cmd.startswith("[") else f"{cmd}\r\n")
        following = commands[i + 1] if i + 1 < len(commands) else ""
        if _CALL_LIKE_RE.match(cmd) and not _ERRORLEVEL_RE.match(following):
            lines.append('If "%ErrorLevel%" == "3010" Then "RebootRequired" EndIf\r\n')
            lines.append('If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf\r\n')
    lines.append("\r\n")
    return "".join(lines)


def _exe_template(meta: PackageMetadata) -> str:
    src = _src_leaf(meta)
    silent = _silent_exe_args(meta)
    body = (
        _product_refs(
            with_app_active=True,
            user_part=meta.has_user_part,
            reg_machine_only=not _has_hkcu(meta),
        )
        + _app_active_block(meta)
        + "[Set:Product]\r\n"
        "AddMeter -1\r\n"
        "Set GUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)\r\n"
        "Set GUID_X86 = GetUninstallKeyName (%V_DisplayName%,x86)\r\n"
        "ReplaceEnv GUID_X64\r\n"
        "ReplaceEnv GUID_X86\r\n"
        'If DoesRegKeyExist ("HKLM,SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%GUID_X64%,UnInstallString") == "1" | DoesRegKeyExist ("HKLM,SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%GUID_X86%,UnInstallString") == "1" Then "Repair" Else "Installation" EndIf\r\n'
        "\r\n"
        "[Repair]\r\n"
        "#Installation\r\n"
        "\r\n"
        "[Installation]\r\n"
        f'CallHidden "%Src%\\Files\\{src}" {silent}\r\n'
        'If "%ErrorLevel%" == "3010" Then "RebootRequired" EndIf\r\n'
        'If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf\r\n'
        "Sleep 3000\r\n"
        + _custom_install_steps(meta)
        + "\r\n"
        "[Set:Deinstallation]\r\n"
        "-AddMeter -1\r\n"
        'If "%GUID_X64%" <> "" Then "Deinstall_x64" EndIf\r\n'
        'If "%GUID_X86%" <> "" Then "Deinstall_x86" EndIf\r\n'
        + _custom_uninstall_steps(meta)
        + "-ReplaceEnv GUID_X64\r\n"
        "-ReplaceEnv GUID_X86\r\n"
        "-Set GUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)\r\n"
        "-Set GUID_X86 = GetUninstallKeyName (%V_DisplayName%,x86)\r\n"
        "\r\n"
        "[Deinstall_x64]\r\n"
        "Set V_UNINSTALLSTRING=%%HKLM,SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%GUID_X64%,UnInstallString%%\r\n"
        "ReplaceEnv V_UNINSTALLSTRING\r\n"
        "-CallHidden %V_UNINSTALLSTRING%\r\n"
        "Sleep 3000\r\n"
        "\r\n"
        "[Deinstall_x86]\r\n"
        "Set V_UNINSTALLSTRING=%%HKLM,SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\%GUID_X86%,UnInstallString%%\r\n"
        "ReplaceEnv V_UNINSTALLSTRING\r\n"
        "-CallHidden %V_UNINSTALLSTRING%\r\n"
        "Sleep 3000\r\n"
        "\r\n"
    )
    return (
        _standard_header(meta, method="Unattend", cmdline="/S2")
        + body
        + _user_part_block(meta)
        + _error_sections(meta)
    )


def _script_template(meta: PackageMetadata) -> str:
    body = (
        _product_refs(
            with_app_active=True,
            user_part=meta.has_user_part,
            reg_machine_only=not _has_hkcu(meta),
        )
        + _app_active_block(meta)
        + "[Set:Product]\r\n"
        "AddMeter -1\r\n"
        'CallHidden "%Src%\\Files\\install.cmd"\r\n'
        'If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf\r\n'
        "Sleep 3000\r\n"
        + _custom_install_steps(meta)
        + "\r\n"
        "[Set:Deinstallation]\r\n"
        "-AddMeter -1\r\n"
        '-CallHidden "%Src%\\Files\\uninstall.cmd"\r\n'
        'If "%ErrorLevel%" != "0" Then "Set:DeInstallationError" EndIf\r\n'
        "Sleep 3000\r\n"
        + _custom_uninstall_steps(meta)
        + "\r\n"
    )
    return (
        _standard_header(meta, method="Unattend", cmdline="/S2")
        + body
        + _user_part_block(meta)
        + _error_sections(meta)
    )


def _links_template(meta: PackageMetadata) -> str:
    name = meta.product_name or "LinksPackage"
    # ShellLinks=1 auto-runs [Shell:Product] – do NOT also #Shell:Product (VAL-005).
    body = (
        _product_refs(
            with_app_active=True,
            user_part=meta.has_user_part,
            reg_machine_only=not _has_hkcu(meta),
        )
        + _app_active_block(meta)
        + "[Set:Product]\r\n"
        "AddMeter -1\r\n"
        "Echo Creating shell links for %ProductName%\r\n"
        + _custom_install_steps(meta)
        + "\r\n"
        "[Set:Deinstallation]\r\n"
        "-AddMeter -1\r\n"
        "-Echo Removing shell links for %ProductName%\r\n"
        + _custom_uninstall_steps(meta)
        + "\r\n"
    )
    if not meta.shell_links:
        # Use classic default single link line if no custom links were added
        errors = (
            "[RebootRequired]\r\n"
            "SetReboot 1\r\n"
            "-SetReboot 1\r\n"
            "\r\n"
            "[Set:InstallationError]\r\n"
            "ErrorLogMsg %ErrorLogMessage%\r\n"
            "Abort %ErrorText%\r\n"
            "\r\n"
            "[Set:ReinstallationError]\r\n"
            "ErrorLogMsg %ErrorLogMessage%\r\n"
            "Abort %ErrorText%\r\n"
            "\r\n"
            "[Set:DeInstallationError]\r\n"
            "-ErrorLogMsg %ErrorLogMessage%\r\n"
            "-Abort %ErrorText%\r\n"
            "\r\n"
            "[Reg:OnUninstallProduct]\r\n"
            "\r\n"
            "[Reg:Product]\r\n"
            "\r\n"
            "[Ini:Product]\r\n"
            "\r\n"
            "[Security:Product]\r\n"
            "\r\n"
            "[Shell:Product]\r\n"
            # %CommonPrograms% is the documented Start Menu\Programs variable
            # (%CommonStartMenu% has 0 reference hits).
            f"%CommonPrograms%\\{name},%Src%\\Files\\app.exe,,,,%Src%\\Files\\app.exe,,,\r\n"
        )
        return (
            _standard_header(meta, method="Unattend", cmdline="/S2")
            + body
            + _user_part_block(meta)
            + errors
        )

    return (
        _standard_header(meta, method="Unattend", cmdline="/S2")
        + body
        + _user_part_block(meta)
        + _error_sections(meta)
    )

