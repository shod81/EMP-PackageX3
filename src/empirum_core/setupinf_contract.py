"""Canonical Empirum package-standard Setup.inf section and key contracts.

Aligned with:
- Referenzvorlagen des Paket-Standards (MSI / Unattend / Skripte / Links)
- Empirum Setup.inf Quick Reference
- System_Prompt_Empirum_Setup.inf
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

# Always present in generated packages (empty sections allowed / commentary OK).
STANDARD_SECTIONS: tuple[str, ...] = (
    "SetupInfo",
    "VarDefInfo",
    "Setup",
    "Requirements",
    "Application",
    "Strings:07",
    "Strings:09",
    "SysStrings:07",
    "SysStrings:09",
    "Environment",
    "Encryption",
    "Disks",
    "Options",
    "Processes",
    "Installer",
    "Product",
    "Set:Product",
    "Set:Deinstallation",
    "Reg:OnUninstallProduct",
    "Reg:Product",
    "Ini:Product",
    "Security:Product",
    "Shell:Product",
    "RebootRequired",
    "Set:InstallationError",
    "Set:ReinstallationError",
    "Set:DeInstallationError",
)

# MSI install CallHidden flags (Quick Reference / System Prompt).
MSI_INSTALL_FLAGS: tuple[str, ...] = (
    'ALLUSERS="1"',
    "REBOOT=REALLYSUPPRESS",
    "ARPSYSTEMCOMPONENT=1",
    "/qn",
)

# Official [Reg:*] type constants of the Empirum Setup.inf reference
# (Legacy-Help Section 29, verified against the 26.1.0 interpreter, K-03). Single
# source of truth for the .reg importer (parser/reg_parser.py), the wizard
# and VAL-027.
SETUPINF_REG_TYPES: Mapping[str, str] = MappingProxyType(
    {
        "REG_SZ": "0x00000000",
        "REG_BINARY": "0x00000001",
        "REG_MULTI_SZ": "0x00010000",
        "REG_DWORD": "0x00010001",
        "REG_EXPAND_SZ": "0x00020000",
        "REG_NONE": "0x00020001",
        "REG_QWORD": "0x00040001",
        "REG_BINARY_SZ": "0x10000001",
    }
)

# Additive behaviour flags that may be OR-ed onto a [Reg:*] type constant
# (Legacy-Help A.2.6): +0x2 write-only-if-absent, +0x8 append
# data instead of replace, +0x10 create empty key. A trailing '\'
# continues the value on the next line.
SETUPINF_REG_EXTRA_FLAGS: tuple[tuple[str, str], ...] = (
    (
        "+0x2",
        "Nur schreiben, wenn Wert noch nicht vorhanden; bei Deinstallation nur bei "
        "Wertgleichheit löschen",
    ),
    ("+0x8", "Daten an vorhandenen Wert anhängen statt ersetzen"),
    ("+0x10", "Leeren Registry-Schlüssel anlegen"),
)

# Setup.inf command vocabulary (command style; lines may carry a '-' uninstall
# prefix). Sources: System_Prompt_Empirum_Setup.inf §6 table, field-verified
# commands (MD) and the verified 26.1.0 interpreter command table.
# Completer, snippets and VAL-019 derive from this list.
#
# Verification against the Empirum 26.1.0 interpreter: 
# `CheckLanAdministrator` and `Run` do NOT exist as commands — unknown commands
# are executed as a program start fallback (SETUP_ERR_UNRECOGNIZABLE). Usage
# is flagged by VAL-026. Short/long forms (MD/MkDir, CD/ChDir, RD/RmDir,
# Del/Erase, Ren/Rename) are both real and therefore both listed.
SETUPINF_COMMANDS: tuple[str, ...] = (
    "Abort",
    "AbortReboot",
    "AbortSilent",
    "AddEventSource",
    "AddMeter",
    "AddMonitor",
    "AddPort",
    "AddPrinter",
    "AddPrinterConnection",
    "AddPrinterDriver",
    "AddPrintProcessor",
    "AddPrintProvider",
    "AddService",
    "Append",
    "AskKillProcesses",
    "Beep",
    "Call",
    "CallHidden",
    "CallRunAs",
    "CallRunAsHidden",
    "CD",
    "ChDir",
    "CloseWindow",
    "Copy",
    "DDE",
    "Decrement",
    "DeleteAllPrinters",
    "DeleteMonitor",
    "DeletePort",
    "DeletePrinter",
    "DeletePrinterConnection",
    "DeletePrinterDriver",
    "DeletePrintProcessor",
    "DeletePrintProvider",
    "DeleteService",
    "DeleteXml",
    "Del",
    "DelTree",
    "Divide",
    "Echo",
    "EmptyClipboard",
    "EndIf",
    "Erase",
    "ErrorLogMsg",
    "Exit",
    "For",
    "If",
    "Increment",
    "KillProcess",
    "MD",
    "MkDir",
    "Multiply",
    "Next",
    "PlaySound",
    "Prompt",
    "RD",
    "RegAsm",
    "Rem",
    "Rename",
    "Ren",
    "ReplaceEnv",
    "ReplaceRegValue",
    "ReplaceTextFile",
    "ReplaceVars",
    "ReadXmlNode",
    "ReadXmlText",
    "RmDir",
    "Set",
    "SetReboot",
    "ShowPicture",
    "Sleep",
    "SplashDialogOff",
    "SplashDialogOn",
    "SplashDialogText",
    "StartService",
    "StopService",
    "SystemShutdown",
    "UpdateXml",
    "Unrar",
    "Unzip",
    "WaitUntilFileExists",
    "WaitUntilProcessExists",
    "WaitUntilRegKeyExists",
    "WaitWhileProcessExists",
)

# If-predicates (not line-start commands; used inside If … Then … EndIf).
# Verified function table of the Empirum 26.1.0 interpreter: these
# five Does* predicates are the ONLY existing ones. Former alias entries
# (DirExists, FileExists, ProcessExists, RegKeyExists, RegValueExists,
# ServiceExists, DoesDirExist, DoesServiceExist, DoesRegValueExist) do not
# exist and are flagged by VAL-026.
SETUPINF_PREDICATES: tuple[str, ...] = (
    "DoesFileExist",
    "DoesPathExist",
    "DoesProcessExist",
    "DoesRegKeyExist",
    "DoesTextInFileExist",
)

# Functions usable on the right-hand side of Set … and inside If expressions
# (verified function table 26.1.0).
SETUPINF_FUNCTIONS: tuple[str, ...] = (
    "BitAnd",
    "BitOr",
    "BitXOr",
    "FileSize",
    "FileVersion",
    "GetClipboardText",
    "GetDCName",
    "GetDiskFreeSpace",
    "GetDiskFreeSpaceKB",
    "GetDotNetPatchLevel",
    "GetIP",
    "GetNIC",
    "GetNICs",
    "GetUninstallKeyName",
    "HexToString",
    "IsDotNetVersionAvailable",
    "Left",
    "Len",
    "Lowercase",
    "Mid",
    "ReadTextFile",
    "RemoveFromLeft",
    "RemoveFromRight",
    "Right",
    "StringToHex",
    "Tokenize",
    "Uppercase",
)

# Copy flags of the [Installer]/[Options] file lists (Legacy-Help Section 24
# flags table, CF-001..024). DELETE/DONTDELETE/ADMIN/CLIENT/MACHINE as
# section-call flags live in FLAG_DOCS, not here.
SETUPINF_COPYFLAGS: tuple[str, ...] = (
    "APPEND",
    "BACKUP",
    "CASCADED",
    "CHECKRTVERSION",
    "CREATE",
    "DONTREPLACE",
    "EXPAND",
    "HIDDEN",
    "KEEPEXISTING",
    "LOCALAPP",
    "NODATEWARNING",
    "RDONLY",
    "REGASM",
    "REGISTER",
    "REPLACEOLDER",
    "REPLACEVARS",
    "SERVICE",
    "SERVICE_AUTO_START",
    "SETUPHOOK",
    "SETUSERINFO",
    "SHARED",
    "SHAREDDLL",
    "SYSTEM",
)

# Setup.exe call switches (Legacy-Help SETUP_Aufruf.htm, SW-001..019).
SETUPINF_SWITCHES: tuple[str, ...] = (
    "/?",
    "/A",
    "/AS",
    "/AW",
    "/B<Datei>",
    "/C",
    "/D",
    "/E[+]<Datei>",
    "/F",
    "/L",
    "/M",
    "/N",
    "/O+/-<Option>",
    "/P<Verzeichnis>",
    "/R",
    "/S0",
    "/S1",
    "/S2",
    "/S3",
    "/S4",
    "/T0",
    "/T1",
    "/U",
    "/X<Flag>",
)

# Verified uninstall semantics (OP-008, Legacy-Help): commands that run in
# BOTH directions even without a '-' prefix …
SETUPINF_ALWAYS_BOTH_COMMANDS: tuple[str, ...] = (
    "AddMeter",
    "Beep",
    "CD",
    "ChDir",
    "Rem",
    "ReplaceEnv",
    "Set",
)

# … and commands the interpreter automatically reverses on /U (undo log),
# so they need no '-' mirror line (OP-008: Copy, MD, MkDir, Ren, Rename).
SETUPINF_AUTO_REVERSED_COMMANDS: tuple[str, ...] = (
    "Copy",
    "MD",
    "MkDir",
    "Ren",
    "Rename",
)

# ---------------------------------------------------------------------------
# Klasse 1 — undokumentierte Befehle: im Interpreter 26.1.0 vorhanden, in der
# gesamten offiziellen Hilfe nicht dokumentiert.
# Gated behind the 'undocumented_commands' feature flag: no Matrix42 safety
# net, semantics partly unclear (Extract). Do NOT add to SETUPINF_COMMANDS.
# ---------------------------------------------------------------------------
SETUPINF_COMMANDS_UNDOCUMENTED: tuple[str, ...] = (
    "BlockInput",
    "CollapseEnv",
    "Extract",
    "RenDir",
)

# Undocumented variables (variable table): %DstDir% (used by Matrix42's
# own OutlookSignatur.inf), the New-Folder known-folder family and internal
# system paths, plus service-context variables.
SETUPINF_VARIABLES_UNDOCUMENTED: tuple[str, ...] = (
    "%CalledFromService%",
    "%CommonOEMLinks%",
    "%Contacts%",
    "%CurrentFqdnUser%",
    "%Downloads%",
    "%DstDir%",
    "%LocalizedResourcesDir%",
    "%LocalAppDataLow%",
    "%MediaPathUnexpanded%",
    "%OriginalImages%",
    "%PhotoAlbums%",
    "%Playlists%",
    "%PrintProcessorDir%",
    "%PrinterDriverDir%",
    "%Public%",
    "%QuickLaunch%",
    "%ResourcesDir%",
    "%SavedGames%",
    "%SavedSearches%",
    "%SharedDir%",
    "%SidebarDefaultParts%",
    "%SidebarParts%",
    "%System16%",
    "%UserProfiles%",
)

# Undocumented $-groups for [Security:] ACL accounts (group table).
SETUPINF_DOLLAR_GROUPS_UNDOCUMENTED: tuple[str, ...] = (
    "%$AuthenticatedUser%",
    "%$Batch%",
    "%$LocalCertsvcDCOMAccessGroup%",
    "%$CreatorOwner%",
    "%$Dialup%",
    "%$DomainAdmin%",
    "%$DomainGuest%",
    "%$LocalIUsers%",
    "%$Interactive%",
    "%$Local%",
    "%$LocalAccountOps%",
    "%$LocalBackupOps%",
    "%$LocalDCOMUsers%",
    "%$LocalPowerUsers%",
    "%$LocalPrintOps%",
    "%$LocalRASServers%",
    "%$LocalRemoteDesktopUsers%",
    "%$LocalReplicator%",
    "%$LocalSystem%",
    "%$LocalSystemOps%",
    "%$LocalTSLicenseServers%",
    "%$Network%",
    "%$SID%",
    "%$Service%",
)

# Undocumented [Application]/[SetupInfo] keys (serial/demo mechanics, behaviour
# switches).
SETUPINF_KEYS_UNDOCUMENTED: tuple[str, ...] = (
    "CheckSerialProc",
    "ForceOnceDate",
    "PatchSerialProc",
    "ProductIDLength",
    "SerialDLL",
    "SetupExtIsUnicode",
    "UseProductID",
    "UseProductIDPerOption",
    "UserText",
    "UseRegSvr",
    "WarnRegistry",
)

# Undocumented Setup.exe switches with unclear semantics — documented
# here for completeness only; do not generate.
SETUPINF_SWITCHES_UNDOCUMENTED: tuple[str, ...] = (
    "/SX",
    '/Y:"<Datei>"',
)

# Admin-oriented grouping for the structured Empirum help UI. Commands not
# listed in any group are appended by the help tree under a residual group.
SETUPINF_COMMAND_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Ausführung",
        (
            "Call",
            "CallHidden",
            "CallRunAs",
            "CallRunAsHidden",
            "Sleep",
            "AddMeter",
            "Exit",
        ),
    ),
    (
        "Dateioperationen",
        (
            "Copy",
            "Del",
            "Erase",
            "DelTree",
            "MD",
            "MkDir",
            "RD",
            "RmDir",
            "CD",
            "ChDir",
            "Ren",
            "Rename",
            "Append",
        ),
    ),
    (
        "Prozesse & Fenster",
        (
            "KillProcess",
            "AskKillProcesses",
            "CloseWindow",
            "WaitUntilProcessExists",
            "WaitWhileProcessExists",
        ),
    ),
    ("Variablen & Rechnen", ("Set", "ReplaceEnv", "Increment", "Decrement", "Multiply", "Divide")),
    (
        "Kontrolle",
        ("If", "EndIf", "For", "Next", "Rem", "Prompt"),
    ),
    (
        "Fehler & Reboot",
        (
            "Echo", "ErrorLogMsg", "Abort", "AbortReboot", "AbortSilent", "SetReboot",
            "SystemShutdown",
        ),
    ),
    (
        "Registry & Dienste",
        (
            "RegAsm", "AddService", "DeleteService", "StartService", "StopService",
            "AddEventSource", "ReplaceRegValue",
        ),
    ),
    ("Archive & Entpacken", ("Unzip", "Unrar")),
    (
        "Text, XML & INI",
        ("ReplaceVars", "ReplaceTextFile", "ReadXmlNode", "ReadXmlText", "UpdateXml", "DeleteXml"),
    ),
    (
        "Drucker",
        (
            "AddPrinter",
            "AddPrinterConnection",
            "AddPrinterDriver",
            "AddMonitor",
            "AddPort",
            "AddPrintProcessor",
            "AddPrintProvider",
            "DeletePrinter",
            "DeletePrinterConnection",
            "DeletePrinterDriver",
            "DeleteMonitor",
            "DeletePort",
            "DeletePrintProcessor",
            "DeletePrintProvider",
            "DeleteAllPrinters",
        ),
    ),
    (
        "Dialoge & UI",
        (
            "Beep", "PlaySound", "ShowPicture", "SplashDialogOn", "SplashDialogText",
            "SplashDialogOff", "EmptyClipboard",
        ),
    ),
    ("Warten", ("WaitUntilFileExists", "WaitUntilRegKeyExists")),
    ("Legacy", ("DDE",)),
)

# Built-in variables documented in the reference (tables and examples) plus
# the Legacy-Help Section 12 list (verified, class 2).
# %Dst% / %PackageDir% remain deliberately absent (0 reference hits); the
# undocumented New-Folder family (Contacts, Downloads, QuickLaunch, …) is gated
# behind the undocumented-commands feature flag instead.
SETUPINF_VARIABLES: tuple[str, ...] = (
    "%$DomainUsers%",
    "%$Everyone%",
    "%$LocalAdmins%",
    "%Accessories%",
    "%AdminTools%",
    "%App%",
    "%AppData%",
    "%AppPaths%",
    "%ApplicationDir%",
    "%CDBurnArea%",
    "%CLRDir%",
    "%Client%",
    "%ClientSrcDir%",
    "%CommonAppData%",
    "%CommonDesktop%",
    "%CommonFilesDir%",
    "%CommonFilesDirx86%",
    "%CommonPrograms%",
    "%CommonStartMenu%",
    "%CommonStartup%",
    "%Company%",
    "%ComputerName%",
    "%Cookies%",
    "%Data%",
    "%DeveloperName%",
    "%Desktop%",
    "%DomainName%",
    "%EmpirumServer%",
    "%ErrorLevel%",
    "%ExactSysTime%",
    "%Favorites%",
    "%Fonts%",
    "%Games%",
    "%History%",
    "%InstalledRevision%",
    "%InstalledVersion%",
    "%InternetCache%",
    "%IsLaptop%",
    "%LocalAppData%",
    "%LongSysTime%",
    "%MediaPath%",
    "%Multimedia%",
    "%MyMusic%",
    "%MyPictures%",
    "%MyVideo%",
    "%NetHood%",
    "%Option%",
    "%OptionName%",
    "%OptionText%",
    "%OS.BuildNumber%",
    "%OS.CSDVersion%",
    "%OS.DisplayString%",
    "%OS.MajorVersion%",
    "%OS.MinorVersion%",
    "%OS.Name%",
    "%OS.PlatformId%",
    "%OS.ProductType%",
    "%OS.ServicePackMajor%",
    "%OS.SuiteMask%",
    "%Personal%",
    "%PrintEnvironment%",
    "%PrintHood%",
    "%PrintServer%",
    "%ProgramFiles%",
    "%ProgramFiles(x86)%",
    "%ProgramFilesDir%",
    "%ProgramFilesDirx86%",
    "%ProgramFilesSys%",
    "%Programs%",
    "%ProductName%",
    "%Recent%",
    "%Sendto%",
    "%SetupBits%",
    "%SetupInf%",
    "%SetupInfFileName%",
    "%SetupInfPathName%",
    "%SetupInfServerName%",
    "%Src%",
    "%Startup%",
    "%SysDate%",
    "%SysTime%",
    "%System%",
    "%SystemTools%",
    "%Templates%",
    "%Temp%",
    "%User%",
    "%UserDesktop%",
    "%UserDomain%",
    "%UserProfile%",
    "%UserPrograms%",
    "%UserStartup%",
    "%Version%",
    "%WinDir%",
    "%Windows%",
    "%WindowsBits%",
    "%WindowsName%",
    "%WindowsUser%",
    "%WindowsVersion%",
    "%WriteableSystem%",
)

# [Application] keys required for Empirum identity + package-standard conventions.
APPLICATION_KEYS: tuple[str, ...] = (
    "ProductName",
    "ProductNameShort",
    "DeveloperName",
    "DeveloperNameShort",
    "Version",
    "Revision",
    "UserKeyName",
    "MachineKeyName",
    "UninstallKeyName",
    "UninstallDisplayName",
    "UninstallString",
    "ReinstallString",
    "UninstallDisplayIcon",
    "UninstallOptions",
    "HideUninstall",
    "ReinstallMode",
    "SrcDir",
    "ApplicationDir",
    "SetupInfDir",
    "DataDir",
    "AskUninstallOld",
    "ShellLinks",
    "CommonShellLinks",
    "CreateUnresolvableShellLinks",
    "UseStringSection",
    "UseSysStringSection",
    "Reboot",
    "PreventExternalReboot",
    "StartServicesOnReboot",
    "CallTimeOut",
    "AbortAfterCallTimeOut",
    "DisableCancelButton",
    "ShowEndMessage",
    "EndMessage",
)

# Canonical [Product] GOSUB block in standard order. This is the single source of
# truth shared by the wizard templates and the standard skeleton repair
# (empirum_core.skeleton_repair) so a repaired package uninstalls in the same order
# as a generated one. ``Shell:Product`` is deliberately absent: it auto-runs
# via ShellLinks=1 and an extra #Shell ref would duplicate links (VAL-005).
PRODUCT_REFS: tuple[tuple[str, str], ...] = (
    ("Set:Product", "#Set:Product, DONTDELETE"),
    ("Reg:OnUninstallProduct", "#Reg:OnUninstallProduct, DELETE"),
    ("Reg:Product", "#Reg:Product, DONTDELETE"),
    ("Ini:Product", "#Ini:Product, DONTDELETE"),
    ("Security:Product", "#Security:Product"),
    ("Set:Deinstallation", "#Set:Deinstallation, DELETE"),
)

# User part contract: section name and the canonical
# [Product] call. Offered by completer/snippets and emitted by the templates
# as soon as a package has user-context commands; deliberately NOT part of
# STANDARD_SECTIONS (VAL-012 must not demand a user part in every package).
USER_PART_SECTION = "Set:Client"
USER_PART_SECTIONS: tuple[str, ...] = (USER_PART_SECTION,)
USER_PART_PRODUCT_REF: tuple[str, str] = (
    USER_PART_SECTION,
    "#Set:Client, CLIENT",
)


def product_refs_for(
    *,
    user_part: bool = False,
    reg_machine_only: bool = True,
) -> tuple[tuple[str, str], ...]:
    """Standard [Product] refs resolved for the machine/user context contract.

    User parts: when the package has a real user part, every
    machine entry gains the ``MACHINE`` flag so the installer runs it exactly
    once per machine even under ``/AW``, and the ``#Set:Client, CLIENT`` ref is
    appended last. ``#Reg:Product`` keeps its unflagged form (runs in both the
    machine and the user pass) when the registry holds HKCU entries — a
    ``MACHINE`` flag would silently skip the per-user values there (VAL-006
    chain / VAL-034). Without a user part the plain standard refs are returned
    unchanged: packages whose ``/AW`` results only from HKCU/profile-variable
    detection intentionally keep their [Set:Product] content running in the
    user pass too.
    """
    if not user_part:
        return PRODUCT_REFS
    out: list[tuple[str, str]] = []
    for target, ref in PRODUCT_REFS:
        if target == "Reg:Product" and not reg_machine_only:
            out.append((target, ref))
            continue
        out.append((target, f"{ref}, MACHINE"))
    out.append(USER_PART_PRODUCT_REF)
    return tuple(out)

# Canonical bodies of the three standard error handlers ('-' prefix = runs only in
# the uninstall path, mirroring the reference command style). Shared by the
# templates and the skeleton repair so a repaired package aborts like a
# reference package. ``[RebootRequired]`` is intentionally NOT included: the template
# body (``SetReboot 1``) would turn a structural repair into a forced reboot.
ERROR_SECTION_BODIES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "Set:InstallationError": ("ErrorLogMsg %ErrorLogMessage%", "Abort %ErrorText%"),
        "Set:ReinstallationError": ("ErrorLogMsg %ErrorLogMessage%", "Abort %ErrorText%"),
        "Set:DeInstallationError": ("-ErrorLogMsg %ErrorLogMessage%", "-Abort %ErrorText%"),
    }
)
