# Empirum / Paket-Standard Setup.inf alignment

EMP-PackageX3 templates and structure checks follow the package-standard reference templates plus the
Empirum Setup.inf Quick Reference and System Prompt
(`docs/reference/`).

Canonical lists live in `empirum_core.setupinf_contract`
(`STANDARD_SECTIONS`, `APPLICATION_KEYS`, `MSI_INSTALL_FLAGS`,
`SETUPINF_COMMANDS`, `SETUPINF_VARIABLES`) und die gemeinsamen
Struktur-Konstanten
`PRODUCT_REFS` (kanonische `[Product]`-Reihenfolge) sowie
`ERROR_SECTION_BODIES` (Bodies der drei Fehler-Handler). Templates,
Completer, Snippets, VAL-012/019/020/021 und `empirum_core.skeleton_repair` leiten
sich daraus ab – keine Einträge ohne Referenz-Beleg.

Wichtig: Der Completer bietet genau `STANDARD_SECTIONS` an (keine
Altnamen wie `[Set_Install]`), und der VAL-012-QuickFix fügt dieselbe Sektion
ein, die auch die Reparatur anlegen würde – inklusive kanonischem Abort-Block
bei den Fehler-Handlern.

Fehlende Standardsektionen repariert `empirum_core.skeleton_repair`
(kanonische `[Product]`-Refs in Vorlagen-Reihenfolge: `#Reg:OnUninstallProduct`
vor `#Set:Deinstallation`, damit generierte und reparierte Pakete beim
Uninstall identisch ablaufen; die drei Fehler-Handler entstehen mit dem
Abort-Block, alle übrigen Sektionen als leere Stubs, `[RebootRequired]`
bewusst ohne `SetReboot`; Werkzeuge-Menü bzw. PackageStore-Dialog).

## Package folder (must)

```
<Paket>/
  Install/
    Setup.inf     # SetupInfDir=Install
  Files/          # payload; referenced as %Src%\Files\…
```

- `SrcDir=..` (package root = parent of `Install`)
- Windows-1252 (ANSI) without BOM + CRLF on generate (UTF-8 still loadable)

## Generated Setup.inf (standard skeleton)

Every kind (**msi** | **exe**/Unattend | **script** | **links**) always emits
all `STANDARD_SECTIONS`, including nice-to-have stubs:

`SetupInfo`, `VarDefInfo`, `Setup` (`Version=14.2`), `Requirements`,
`Application` (full identity + `$Matrix42Packages$` keys), `Strings:07/09`,
`SysStrings:07/09`, `Environment` (logs, `CommonSetupDir`, Machine/UserValues
paths + VM_/VU_ comments), `Encryption`, `Disks`, `Options`, `Processes`
(placeholder for `AskKillProcesses`), `Installer`, `Product` (+
`Set:Product` / `Set:Deinstallation`), empty `Reg:` / `Ini:` / `Security:` /
`Shell:Product`, `RebootRequired`, error sections.

Unattend/EXE/Script/Links also include `#Set:AppActive` + `[Set:AppActive]`
(`AskKillProcesses` placeholders for EXE).

MSI install: `CallHidden MsiExec /I … ALLUSERS="1" REBOOT=REALLYSUPPRESS
ARPSYSTEMCOMPONENT=1 /qn`, ErrorLevel 3010 → `RebootRequired`, registry
success check, `-` uninstall lines + `Sleep 3000`.

## Linter

| IDs | Role |
|-----|------|
| VAL-001…011 | Pitfalls (dangling refs, DelTree `\`, ShellLinks duplex, HKCU/`/AW`, …) |
| VAL-012 | Alle `STANDARD_SECTIONS` müssen existieren (QuickFix hängt die Sektion direkt an – Fehler-Handler mit kanonischem Abort-Block) |
| VAL-013 | Alle `APPLICATION_KEYS` |
| VAL-014 | `[Setup] Version` |
| VAL-015 | SrcDir / SetupInfDir / CommonSetupDir |
| VAL-016 | MSI `/I` Flags (`ALLUSERS`, `REBOOT=REALLYSUPPRESS`, `ARPSYSTEMCOMPONENT`, `/qn`) |
| VAL-017 | INFO: `/AW` in SetupInfo → Depot-Befehl ebenfalls `/AW` |
| VAL-018 | INFO: `-HK…` in `[Reg:…]` löscht erst bei Deinstallation; Install → `reg.exe` |

VAL-006 warnt bei HKCU / `VU_` / `AskKillProcesses` ohne `/AW` (inkl. Standard-Key
`Command line options`).

Paketprüfung vor Deploy: `empirum_services.package_readiness.check_package_readiness`
(Struktur + Lint). Simulator startet im Paket-Standard auf `[Product]` bzw. `[Set:Deinstallation]`.

## Still manual / environment-specific

- Depot “Befehl” must match `/AW` when used (VU_ / User part)
- Relative `..\..\..\..\User\Setup.exe` paths depend on Empirum depot layout
- Fill `[Processes]` APP* entries before shipping AskKillProcesses
- EV signing, live Empirum **25.4** Probeimport
