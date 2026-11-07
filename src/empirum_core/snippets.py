"""Insertable Empirum snippets (IntelliSense 1.0 scope).

All snippets use standard command style: `If … Then "…" EndIf` single-line and
`Sleep 3000` (no `If=`/`Sleep=` key-value forms – not in the reference).
"""

from __future__ import annotations

SNIPPETS: dict[str, str] = {
    "errorlevel-block": (
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        'If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf\r\n'
    ),
    "uninstall-error-pair": (
        "[Set:DeInstallationError]\r\n"
        "-ErrorLogMsg Deinstallation fehlgeschlagen\r\n"
        "-Abort Deinstallation fehlgeschlagen – Details siehe Log\r\n"
    ),
    "msi-install": (
        'CallHidden MsiExec /I "%Src%\\Files\\setup.msi" '
        'ALLUSERS="1" REBOOT=REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        "Sleep 3000\r\n"
    ),
    "msi-dynamic-reinstall": (
        "; Dynamische MSI-GUID-Erkennung (x64/x86) via GetUninstallKeyName:\r\n"
        "Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)\r\n"
        "Set MSIGUID_X86 = GetUninstallKeyName (%V_DisplayName%,x86)\r\n"
        "ReplaceEnv MSIGUID_X64\r\n"
        "ReplaceEnv MSIGUID_X86\r\n"
        'If DoesRegKeyExist ("HKLM,SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\'
        'Uninstall\\%MSIGUID_X64%,UnInstallString") == "1" | '
        'DoesRegKeyExist ("HKLM,SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\'
        'Uninstall\\%MSIGUID_X86%,UnInstallString") == "1" '
        'Then "RepairMSI" Else "InstallMSI" EndIf\r\n'
    ),
    "reboot-safe": ("Reboot=0\r\n"),
    # Install-time registry delete (Empirum: '-' in [Reg:…] runs only on uninstall)
    "reg-delete-install": (
        '; Registry während Installation löschen (nicht -HKLM in [Reg:Product]):\r\n'
        'CallHidden reg.exe delete "HKLM\\Software\\Hersteller\\AltProdukt" /f\r\n'
        '; Optional einzelner Wert:\r\n'
        ';CallHidden reg.exe delete "HKLM\\Software\\Hersteller\\Produkt" /v "ObsoleteValue" /f\r\n'
    ),
    # Registry value read inside an If condition (%Root,SubKey,ValueName%)
    "reg-condition-query": (
        '; Registry-Wert in Bedingung prüfen (%Root,SubKey,ValueName%):\r\n'
        'If "%HKLM,SYSTEM\\CurrentControlSet\\Services\\ServiceName,Start%" == "2" '
        'Then "Set:ChangeService" EndIf\r\n'
    ),
    # Conditional registry modification via reg.exe (procedural in Set: section)
    "reg-modify-procedural": (
        '; Bedingte/prozedurale Registry-Änderung via reg.exe (nicht in [Reg:Product]):\r\n'
        '[Set:ChangeService]\r\n'
        'CallHidden reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\ServiceName" '
        '/v Start /t REG_DWORD /d 4 /f\r\n'
    ),
    # Uninstall registry restore (revert instead of delete for services/system settings)
    "reg-restore-uninstall": (
        '; Originalwert bei Deinstallation wiederherstellen (statt Löschen via [Reg:Product]):\r\n'
        '[Set:Deinstallation]\r\n'
        '-CallHidden reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\ServiceName" '
        '/v Start /t REG_DWORD /d 2 /f\r\n'
    ),
    # User part: per-user commands run in [Set:Client] with the
    # CLIENT flag; /AW in [SetupInfo] and the depot command is mandatory.
    "user-part": (
        "[Set:Client]\r\n"
        "; Benutzerteil – läuft nur im Benutzerkontext (/AW + CLIENT-Flag)\r\n"
        'CallHidden "%Src%\\Files\\usersetup.exe"\r\n'
        'If "%ErrorLevel%" == "3010" Then "RebootRequired" EndIf\r\n'
        'If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf\r\n'
        'MD "%AppData%\\Vendor\\AppConfig"\r\n'
    ),
    "user-part-product-ref": (
        "; In [Product] einfügen – Maschineneinträge erhalten zusätzlich MACHINE:\r\n"
        "#Set:Product, DONTDELETE, MACHINE\r\n"
        "#Set:Deinstallation, DELETE, MACHINE\r\n"
        "#Set:Client, CLIENT\r\n"
    ),
}


def snippet_names() -> list[str]:
    return sorted(SNIPPETS)


def get_snippet(name: str) -> str:
    return SNIPPETS[name]
