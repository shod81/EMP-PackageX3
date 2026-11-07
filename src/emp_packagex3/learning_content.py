"""Setup.inf learning content („Akademie") – didaktisch, systemorientiert.

Alle Texte sind aus der projekteigenen Referenz
(docs/reference/System_Prompt_Empirum_Setup.inf.md) und den mitgelieferten
Referenztemplates destilliert. Rein datenbasiert, offline- und frozen-fähig.
"""

from __future__ import annotations

from dataclasses import dataclass

# Default file name for the learning center HTML export.
CHAPTER_EXPORT_NAME = "Setupinf-Schnellkurs.html"


@dataclass(frozen=True, slots=True)
class SectionDoc:
    name: str  # Anzeigemuster, z. B. "Set:<Name>"
    meaning: str
    when_needed: str
    standard_section: bool
    example: str
    reference: str


@dataclass(frozen=True, slots=True)
class CommandDoc:
    name: str
    syntax: str
    semantics: str
    uninstall: str
    example: str
    pitfall: str


@dataclass(frozen=True, slots=True)
class PredicateDoc:
    name: str
    syntax: str
    semantics: str
    example: str
    pitfall: str
    alias_of: str = ""


@dataclass(frozen=True, slots=True)
class FunctionDoc:
    name: str
    syntax: str
    semantics: str
    example: str
    pitfall: str


@dataclass(frozen=True, slots=True)
class FlagDoc:
    name: str
    syntax: str
    semantics: str
    example: str
    pitfall: str


@dataclass(frozen=True, slots=True)
class VariableDoc:
    name: str  # Anzeigemuster, z. B. "%App%"
    category: str  # z. B. "Verzeichnis", "Metadaten", "System", "Ablaufsteuerung"
    meaning: str
    example_value: str
    usage: str
    pitfall: str


@dataclass(frozen=True, slots=True)
class QuizItem:
    question: str
    answer: str


@dataclass(frozen=True, slots=True)
class Chapter:
    number: int
    title: str
    intro: tuple[str, ...]
    key_rule: str
    example: str
    quiz: tuple[QuizItem, ...]


@dataclass(frozen=True, slots=True)
class ValDoc:
    code: str
    severity: str
    cause: str
    remedy: str
    reference: str


# --------------------------------------------------------------------------
# Sektions-Referenz (alle Sektionstypen, Referenz Kapitel 3)
# --------------------------------------------------------------------------

SECTION_REFERENCE: dict[str, SectionDoc] = {
    "SetupInfo": SectionDoc(
        name="SetupInfo",
        meaning="Steuert das Verhalten des Setup.exe-Aufrufs: Silent-Optionen, "
        "Paket-Metadaten für das Depot.",
        when_needed="Immer. Hier stehen Command line options (/S1 /S2 /U /AW) "
        "und Beschreibung/Methodik für den Paketierer.",
        standard_section=True,
        example="[SetupInfo]\r\nDescription=DemoApp 1.0\r\nMethod=MSI\r\n"
        "Command line options=/S2 /AW",
        reference="Kap. 3 – [SetupInfo]",
    ),
    "VarDefInfo": SectionDoc(
        name="VarDefInfo",
        meaning="Deklariert Variablen-Typen: Computer (VM_) oder Benutzer (VU_), "
        "inkl. NULL-Werte-Erlaubnis.",
        when_needed="Sobald VM_/VU_-Variablen aus MachineValues/UserValues-INIs "
        "genutzt werden (mit /AW für VU_).",
        standard_section=True,
        example="[VarDefInfo]\r\n; <Variable>, <Type: 0=Computer 1=User>, "
        "<Allow NULL: 0=No 1=Yes>",
        reference="Kap. 3 – [VarDefInfo]",
    ),
    "Setup": SectionDoc(
        name="Setup",
        meaning="Dialekt-/Verhaltensversion der Setup.inf und Fenster-/Plattform-"
        "Einstellungen für den Setup-Assistenten.",
        when_needed="Immer; Version=14.2 ist der aktuelle Dialekt (nicht die "
        "Empirum-Produktversion).",
        standard_section=True,
        example="[Setup]\r\nVersion=14.2\r\nShowCaption=1\r\nPlatform=x64",
        reference="Kap. 3 – [Setup], Kap. 12",
    ),
    "Requirements": SectionDoc(
        name="Requirements",
        meaning="Vorbedingungen für die Installation (OS, Service Packs, "
        "Abhängigkeiten), geprüft vor dem Start.",
        when_needed="Bei Paketen mit harten Voraussetzungen oder Abhängigkeiten.",
        standard_section=True,
        example="[Requirements]",
        reference="Kap. 3 – [Requirements]",
    ),
    "Application": SectionDoc(
        name="Application",
        meaning="Identität des Pakets im Empirum-Register: Namen, Version, "
        "Uninstall-Strings, Pfade (SrcDir/SetupInfDir/ApplicationDir), "
        "Verhalten (Reboot, ShellLinks, Timeouts).",
        when_needed="Immer – die Identität steuert Software-Register, ARP und "
        "Reparatur.",
        standard_section=True,
        example="[Application]\r\nProductName=DemoApp\r\nVersion=1.0\r\n"
        "SrcDir=..\r\nSetupInfDir=Install\r\nReboot=0",
        reference="Kap. 3 – [Application]",
    ),
    "Strings:07": SectionDoc(
        name="Strings:07 / Strings:09",
        meaning="Lokalisierungstexte je Sprachkode (07=deutsch, 09=englisch); "
        "Einbindung über UseStringSection.",
        when_needed="Immer im Paket-Standard; jedes %TextVar% in Dialogen/Logs kommt hierher.",
        standard_section=True,
        example="[Strings:07]\r\nEndMessageDesc=Die Installation wurde "
        "erfolgreich abgeschlossen!",
        reference="Kap. 3 – [Strings]",
    ),
    "SysStrings:07": SectionDoc(
        name="SysStrings:07 / SysStrings:09",
        meaning="Wie Strings, aber systemsprachabhängig statt benutzerbezogen.",
        when_needed="Wenn Texte unabhängig von der Benutzer-, aber abhängig von "
        "der Systemsprache sein sollen.",
        standard_section=True,
        example="[SysStrings:07]\r\nUsers=Benutzer",
        reference="Kap. 3 – [SysStrings]",
    ),
    "Environment": SectionDoc(
        name="Environment",
        meaning="Definiert Paketvariablen (V_…), Pfade (CommonSetupDir) und "
        "Logdatei-Namen; wird vor der Abarbeitung substituiert.",
        when_needed="Immer im Paket-Standard – zentrale Stelle für Log-Pfade, DisplayName, "
        "MSI-GUID-Halter (V_ProductCode).",
        standard_section=True,
        example="[Environment]\r\nV_LogFileInstall=%Temp%\\Install_%ProductName%.log\r\n"
        "CommonSetupDir=%CommonFilesDir%\\Setup%SetupBits%",
        reference="Kap. 3 – [Environment], Kap. 4",
    ),
    "Encryption": SectionDoc(
        name="Encryption",
        meaning="Optionale Entschlüsselungsinformation für verschlüsselte "
        "Paketbestandteile.",
        when_needed="Nur bei verschlüsselten Paketen (selten).",
        standard_section=True,
        example="[Encryption]",
        reference="Kap. 3 – [Encryption]",
    ),
    "Disks": SectionDoc(
        name="Disks",
        meaning="Medien-/Quelllaufwerke der Paketdateien.",
        when_needed="Immer (Standard-Stub mit Disk1).",
        standard_section=True,
        example="[Disks]\r\n1=Installationsmedium 1",
        reference="Kap. 3 – [Disks]",
    ),
    "Options": SectionDoc(
        name="Options",
        meaning="Auswahloptionen des Setup-Assistenten; verbindet Anzeigename "
        "mit Sektionen und Copy-Flags (COPYALWAYS).",
        when_needed="Immer im Paket-Standard (Installer/Product-Optionen).",
        standard_section=True,
        example="[Options]\r\nProduct=%ProductName%, COPYALWAYS, Product, "
        '"%ProductDesc%"',
        reference="Kap. 3 – [Options]",
    ),
    "Processes": SectionDoc(
        name="Processes",
        meaning="Benannte Prozesse für AskKillProcesses: EXE-Name, Anzeigename, "
        "KILLPROCESS-Modus (ABORT/CONTINUE).",
        when_needed="Bei laufenden Apps vor Installation (Unattend-EXE, Office-"
        "Addins …). Benötigt /AW für den Benutzerteil-Dialog.",
        standard_section=True,
        example="[Processes]\r\nAPP1=app.exe, DemoApp, KILLPROCESS ABORT",
        reference="Kap. 10 – Prozessmanagement",
    ),
    "Installer": SectionDoc(
        name="Installer",
        meaning="Datei-Kopierliste des Maschinenteils: Quelle → Ziel mit Flags "
        "(ALWAYS/OPTIONAL, DIRECTORY, WINDOWS64 …).",
        when_needed="Immer im Paket-Standard – kopiert Setup.inf/Setup.ico in das "
        "Anwendungsverzeichnis (%App%\\%SetupInfDir%).",
        standard_section=True,
        example="[Installer]\r\n1:%SetupInfDir%\\Setup.inf, , ALWAYS, 0",
        reference="Kap. 8 – Installer",
    ),
    "Product": SectionDoc(
        name="Product",
        meaning="Das Hauptprogramm: Einstiegspunkt der Ablaufsteuerung. #Aufrufe "
        "mit Flags (DONTDELETE/DELETE/MACHINE/CLIENT) regieren Install und "
        "Uninstall.",
        when_needed="Immer – hier wird die Logik des Pakets orchestriert.",
        standard_section=True,
        example="[Product]\r\n#Set:Product, DONTDELETE\r\n"
        "#Set:Deinstallation, DELETE",
        reference="Kap. 3 – [Product], Kap. 5",
    ),
    "Set:<Name>": SectionDoc(
        name="Set:<Name>",
        meaning="Benutzerdefinierte Ausführungssektion (Unterprogramm): Beflehe "
        "Dateien, MSI, Skripte; bei Uninstall laufen '-'-Zeilen rückwärts.",
        when_needed="Für jeden logischen Schritt (Install, Deinstallation, "
        "Fehlerpfade, AppActive …).",
        standard_section=True,
        example="[Set:Product]\r\nAddMeter -1\r\n"
        'CallHidden MsiExec /I "%Src%\\Files\\setup.msi" /qn\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf',
        reference="Kap. 3 – [Set:], Kap. 5",
    ),
    "Reg:<Name>": SectionDoc(
        name="Reg:<Name>",
        meaning="Registry-Sektion: schreibt Werte (Install), löscht sie bei "
        "Uninstall; '-'-Zeilen wirken umgekehrt (nur Uninstall).",
        when_needed="Für HKLM/HKCU-Schreiber; Restore-Werte gehören in "
        "Reg:OnUninstall…",
        standard_section=True,
        example='[Reg:Product]\r\nHKLM,"Software\\Hersteller\\App","Version",'
        "0x00000000,2",
        reference="Kap. 7 – Registry",
    ),
    "Reg:OnUninstall<Name>": SectionDoc(
        name="Reg:OnUninstall<Name>",
        meaning="Registry-Werte, die bei der Deinstallation gesetzt werden "
        "(Restore statt Löschen); Aufruf mit Flag DELETE.",
        when_needed="Wenn ein Schlüssel beim Entfernen einen definierten "
        "Rücksetzwert erhalten soll.",
        standard_section=True,
        example='[Reg:OnUninstallProduct]\r\nHKLM,"Software\\Hersteller\\App",'
        '"Version",0x00000000,1',
        reference="Kap. 5 – Reg:OnUninstall",
    ),
    "Shell:<Name>": SectionDoc(
        name="Shell:<Name>",
        meaning="Verknüpfungen als kommaseparierte Felder (Ziel, Programm, "
        "Parameter, Icon …). Läuft bei Install automatisch zuletzt, bei "
        "Uninstall zuerst (ShellLinks=1).",
        when_needed="Für Desktop-/Startmenü-Verknüpfungen; CommonShellLinks=1 "
        "für alle Benutzer.",
        standard_section=True,
        example='[Shell:Product]\r\n"%CommonDesktop%\\DemoApp", '
        '"%ProgramFiles%\\Demo\\app.exe"',
        reference="Kap. 9 – Verknüpfungen",
    ),
    "Ini:<Name>": SectionDoc(
        name="Ini:<Name>",
        meaning="INI-Datei-Einträge (Sektion/Schlüssel/Wert), die bei Uninstall "
        "zurückgenommen werden.",
        when_needed="Für Alt-Applikationen mit INI-Konfiguration.",
        standard_section=True,
        example="[Ini:Product]",
        reference="Kap. 3 – [Ini:]",
    ),
    "Security:<Name>": SectionDoc(
        name="Security:<Name>",
        meaning="NTFS-Berechtigungen auf Dateien/Registrierung; Abarbeitung "
        "unabhängig vom '-'-Präfix.",
        when_needed="Wenn Ordner/Keys spezielle ACLs brauchen.",
        standard_section=True,
        example="[Security:Product]",
        reference="Kap. 3 – [Security:]",
    ),
    "RebootRequired": SectionDoc(
        name="RebootRequired",
        meaning="Sammelsektion für den Reboot-Pfad: SetReboot 1 nach "
        "ErrorLevel 3010 (und Rücknahme mit '-SetReboot 1').",
        when_needed="Immer im Paket-Standard – Ziel der 3010-Verzweigung.",
        standard_section=True,
        example='[RebootRequired]\r\nSetReboot 1\r\n-SetReboot 1\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf',
        reference="Kap. 11 – Reboot",
    ),
    "Bat:<Name>": SectionDoc(
        name="Bat:<Name>",
        meaning="Erzeugt/ändert BAT-/Textdateien zeilenweise (Append-Stil).",
        when_needed="Legacy-Hilfsmittel für Autoexec/Profile-Anpassungen.",
        standard_section=False,
        example="[Bat:Config]",
        reference="Kap. 3 – [Bat:]",
    ),
    "ODBC<Component>:<Name>": SectionDoc(
        name="ODBC<Component>:<Name>",
        meaning="ODBC-Datenquellen- und Treiber-Konfiguration.",
        when_needed="Nur für Applikationen mit ODBC-Anbindung.",
        standard_section=False,
        example="[ODBCDriver:App]",
        reference="Kap. 3 – [ODBC…]",
    ),
    "Config.sys:<Name>": SectionDoc(
        name="Config.sys:<Name>",
        meaning="Einträge für Config.sys (DOS-Ära; Wartung legacy).",
        when_needed="Praktisch nicht mehr.",
        standard_section=False,
        example="[Config.sys:Legacy]",
        reference="Kap. 3 – [Config.sys:]",
    ),
    "IP<Component>:<Name>": SectionDoc(
        name="IP<Component>:<Name>",
        meaning="IP-/Netzwerkkomponenten-Konfiguration.",
        when_needed="Spezialfall Netzwerkkomponenten.",
        standard_section=False,
        example="[IPTcp:Cfg]",
        reference="Kap. 3 – [IP…]",
    ),
    # ------------------------------------------------------------------
    # Verifizierte Erweiterung 
    # ------------------------------------------------------------------
    "Admin": SectionDoc(
        name="[Admin]",
        meaning="Installationsart Administrator: steuert Admin-Setup-Verhalten (Keys z. B. Reboot, "
        "InstallAtLast, AdminSetup).",
        when_needed="Bei Admin-Installationen (/A-Varianten) mit abweichendem Verhalten.",
        standard_section=False,
        example="[Admin]\r\nReboot=0",
        reference="Erw. Referenz 26.1.0 – Installationsarten",
    ),
    "Client": SectionDoc(
        name="[Client]",
        meaning="Installationsart Client (Benutzerteil-Konfiguration, ClientPath/AppPath-Logik).",
        when_needed="Bei Admin-/Workstation-Setups mit Client-Anteil.",
        standard_section=False,
        example="[Client]",
        reference="Erw. Referenz 26.1.0 – Installationsarten",
    ),
    "Workstation": SectionDoc(
        name="[Workstation]",
        meaning="Installationsart Workstation (Server-/Workstation-Paar von /AS//AW).",
        when_needed="Bei Workstation-Installationen.",
        standard_section=False,
        example="[Workstation]",
        reference="Erw. Referenz 26.1.0 – Installationsarten",
    ),
    "Prompts": SectionDoc(
        name="[Prompts]",
        meaning="Definition interaktiver Abfragen für den 'Prompt'-Befehl: Frage, Typ (z. B. JA/NEIN, "
        "EINGABE) und Default-Antwort; Silent-Schalter (/S…) übersteuern mit dem Default.",
        when_needed="Wenn der Paketierer vor Installationsschritten interaktiv entscheiden lässt.",
        standard_section=False,
        example="[Prompts]\r\nRebootNow=Sofort neu starten?, JA/NEIN, NEIN",
        reference="Erw. Referenz 26.1.0 – Prompt",
    ),
    "Services": SectionDoc(
        name="[Services]",
        meaning="Dienstedefinition mit Win32-CreateService-Parametern: <Name>=<Anzeigename>,<Typ>,"
        "<Starttyp>,<Fehlerkontrolle>,<Ladegruppe>,<Abhängigkeiten ;getrennt>,<Konto>,<Passwort>"
        "[,<EventSource>][,<Startparameter>]. SERVICE_AUTO_START startet sofort.",
        when_needed="Wenn eine EXE des Pakets als Windows-Dienst laufen soll (alternativ AddService-"
        "Befehl oder SERVICE-Copyflag).",
        standard_section=False,
        example="[Services]\r\nSvc1=Mein Dienst,0x10,2,1,,;HKLM\\Software\\MeinDienst,LocalSystem,,,"
        "MeinEventSource",
        reference="Erw. Referenz 26.1.0 – Dienste",
    ),
    "EventSources": SectionDoc(
        name="[EventSources]",
        meaning="Ereignisquellen für das Windows-Ereignisprotokoll (deklarative Alternative zum "
        "AddEventSource-Befehl).",
        when_needed="Wenn die Anwendung EventLog-Einträge schreiben soll.",
        standard_section=False,
        example="[EventSources]\r\n1=MeineApp",
        reference="Erw. Referenz 26.1.0 – EventSources",
    ),
    "UserKeyNames": SectionDoc(
        name="[UserKeyNames]",
        meaning="Zusätzliche Uninstall-Key-Namen, unter denen alte Installationen im Software-Register "
        "gesucht werden.",
        when_needed="Bei Herstellerwechsel/umbenannten Paketen, um Altversionen sauber zu finden.",
        standard_section=False,
        example="[UserKeyNames]\r\n1=OldVendor\\OldApp",
        reference="Erw. Referenz 26.1.0 – UserKeyNames",
    ),
    "OptionDependencies": SectionDoc(
        name="[OptionDependencies]",
        meaning="Abhängigkeiten zwischen [Options]-Einträgen (Option A erfordert Option B).",
        when_needed="Bei Mehr-Optionen-Paketen mit logischen Abhängigkeiten.",
        standard_section=False,
        example="[OptionDependencies]\r\nAPI=Core",
        reference="Erw. Referenz 26.1.0 – Optionen",
    ),
    "OptionGroups": SectionDoc(
        name="[OptionGroups]",
        meaning="Gruppierung von Optionen im Optionsdialog des Setup-Assistenten.",
        when_needed="Bei vielen Optionen für übersichtliche Dialoge.",
        standard_section=False,
        example="[OptionGroups]",
        reference="Erw. Referenz 26.1.0 – Optionen",
    ),
    "Icons": SectionDoc(
        name="[Icons]",
        meaning="Icon-Definitionen (Datei, Index, Transparenzfarbe) für den Setup-Assistenten; "
        "feldverifiziert im Agent-Paket 2604.2.2: 'Product = <Datei>, <Index>, <Transparenz>, ICON'.",
        when_needed="Für eigenes Branding des Assistenten.",
        standard_section=False,
        example="[Icons]\r\nProduct = %Src%\\Files\\app.ico, 0, 0xFF00FF, ICON",
        reference="Erw. Referenz 26.1.0 – Icons",
    ),
    "%Option%": SectionDoc(
        name="[%Option%]",
        meaning="Gemeinsame Sektion für WILDCARD-Optionen: Der Platzhalter [%Option%] wird für jede "
        "gewählte Option ausgeführt; einzelne Optionen können zusätzlich eigene Sektionen "
        "[<Optionsname>] haben.",
        when_needed="Bei vielen Optionen mit gemeinsamer Grundlogik.",
        standard_section=False,
        example="[%Option%]\r\nEcho Verarbeite Option %Option%",
        reference="Erw. Referenz 26.1.0 – Optionen",
    ),
    "Win.ini:<Name>": SectionDoc(
        name="Win.ini:<Name>",
        meaning="Historische typisierte Sektion für Win.ini-Einträge.",
        when_needed="Legacy (16-Bit-Ära).",
        standard_section=False,
        example="[Win.ini:Legacy]",
        reference="Kap. 3 – typisierte Sektionen",
    ),
    "System.ini:<Name>": SectionDoc(
        name="System.ini:<Name>",
        meaning="Historische typisierte Sektion für System.ini-Einträge.",
        when_needed="Legacy (16-Bit-Ära).",
        standard_section=False,
        example="[System.ini:Legacy]",
        reference="Kap. 3 – typisierte Sektionen",
    ),
    "Autoexec.bat:<Name>": SectionDoc(
        name="Autoexec.bat:<Name>",
        meaning="Historische typisierte Sektion für Autoexec.bat-Anpassungen.",
        when_needed="Legacy (DOS-Ära).",
        standard_section=False,
        example="[Autoexec.bat:Legacy]",
        reference="Kap. 3 – typisierte Sektionen",
    ),
}


def lookup_section(
    section_name: str,
    reference: dict[str, SectionDoc] | None = None,
) -> SectionDoc | None:
    """Resolve a concrete section name ('Shell:Product') to its SectionDoc.

    Exact hit first, then pattern families (Set:/Reg:/Shell:/Ini:/Security:
    with or without the 'OnUninstall' infix).
    """
    ref = reference if reference is not None else SECTION_REFERENCE
    direct = section_name.casefold()
    hits = {key.casefold(): key for key in ref}
    if direct in hits:
        return ref[hits[direct]]
    for prefix, doc_key in (
        ("reg:onuninstall", "Reg:OnUninstall<Name>"),
        ("reg:", "Reg:<Name>"),
        ("set:", "Set:<Name>"),
        ("shell:", "Shell:<Name>"),
        ("ini:", "Ini:<Name>"),
        ("security:", "Security:<Name>"),
        ("strings:", "Strings:07"),
        ("sysstrings:", "SysStrings:07"),
    ):
        if direct.startswith(prefix):
            return ref.get(doc_key)
    return None


# --------------------------------------------------------------------------
# [Security:]-DSL (Legacy-Help Section 43, 268 Zeilen – verifiziert gegen den Interpreter)
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SecurityOpDoc:
    op: str  # z. B. "LocalUser.Add"
    syntax: str
    semantics: str
    example: str
    pitfall: str


SECURITY_DSL_DOCS: dict[str, SecurityOpDoc] = {
    "LocalUser.Add": SecurityOpDoc(
        op="LocalUser.Add",
        syntax="LocalUser.Add ('<Name>','<Passwort>','<Kommentar>',PRIV_USER,'<Voller Name>',"
        "'<Profil>',[<Flags>])",
        semantics="Legt ein lokales Benutzerkonto an. Konstanten: PRIV_GUEST, PRIV_USER, PRIV_ADMIN; "
        "Flag DONT_EXPIRE_PASSWD setzt 'Passwort läuft nie ab'.",
        example="LocalUser.Add ('svcApp','<verschlüsselt>','Servicekonto',PRIV_USER,'',"
        "'',DONT_EXPIRE_PASSWD)",
        pitfall="Passwörter ab INF-Version 6.5 Setup-verschlüsselt (EmpCrypt.exe) angeben.",
    ),
    "LocalUser.Mod": SecurityOpDoc(
        op="LocalUser.Mod",
        syntax="LocalUser.Mod ('<Name>', …)",
        semantics="Ändert Eigenschaften eines bestehenden lokalen Kontos (Kommentar, Vollname, "
        "Profil, Flags).",
        example="LocalUser.Mod ('svcApp','', 'Neuer Kommentar',PRIV_USER,'','')",
        pitfall="Leere Parameter (Kommas!) müssen stehen bleiben.",
    ),
    "LocalUser.Del": SecurityOpDoc(
        op="LocalUser.Del",
        syntax="LocalUser.Del ('<Name>')",
        semantics="Löscht ein lokales Benutzerkonto.",
        example="LocalUser.Del ('svcApp')",
        pitfall="Profile des Kontos werden NICHT mitgelöscht.",
    ),
    "LocalGroup.Add": SecurityOpDoc(
        op="LocalGroup.Add",
        syntax="LocalGroup.Add ('<Name>','<Kommentar>')",
        semantics="Legt eine lokale Gruppe an.",
        example="LocalGroup.Add ('AppAdmins','Admins der App')",
        pitfall="—",
    ),
    "LocalGroup.Del": SecurityOpDoc(
        op="LocalGroup.Del",
        syntax="LocalGroup.Del ('<Name>')",
        semantics="Löscht eine lokale Gruppe.",
        example="LocalGroup.Del ('AppAdmins')",
        pitfall="Nur leere Gruppen zuverlässig löschbar.",
    ),
    "LocalGroup.AddMember": SecurityOpDoc(
        op="LocalGroup.AddMember",
        syntax="LocalGroup.AddMember ('<Gruppe>','<Mitglied>')",
        semantics="Fügt ein Mitglied (Benutzer oder Gruppe) in eine lokale Gruppe ein.",
        example="LocalGroup.AddMember ('AppAdmins','%UserDomain%\\%User%')",
        pitfall="Mitglied voll qualifiziert (Domäne\\Name) angeben.",
    ),
    "LocalGroup.DelMember": SecurityOpDoc(
        op="LocalGroup.DelMember",
        syntax="LocalGroup.DelMember ('<Gruppe>','<Mitglied>')",
        semantics="Entfernt ein Mitglied aus einer lokalen Gruppe.",
        example="LocalGroup.DelMember ('AppAdmins','CORP\\svcAlt')",
        pitfall="—",
    ),
    "Privilege.Add": SecurityOpDoc(
        op="Privilege.Add",
        syntax="Privilege.Add ('<Privileg>','<Konto>')",
        semantics="Gewährt einem Konto ein Systemprivileg, z. B. 'SeServiceLogonRight' (Anmelden "
        "als Dienst).",
        example="Privilege.Add ('SeServiceLogonRight','CORP\\svcApp')",
        pitfall="Privilegnamen exakt (Se*-Nomenklatur) angeben.",
    ),
    "Privilege.Del": SecurityOpDoc(
        op="Privilege.Del",
        syntax="Privilege.Del ('<Privileg>','<Konto>')",
        semantics="Entzieht einem Konto ein Systemprivileg.",
        example="Privilege.Del ('SeServiceLogonRight','CORP\\svcAlt')",
        pitfall="—",
    ),
    "FileDacl.Add": SecurityOpDoc(
        op="FileDacl.Add",
        syntax='FileDacl.Add ("<Pfad>", <Konto>, SET, <Rechte>, <Vererbung>)',
        semantics="Setzt NTFS-Berechtigungen auf Dateien/Ordner. Rechte u. a. READ, CHANGE, ALL; "
        "Vererbung z. B. SUB_CONTAINERS_AND_OBJECTS_INHERIT (verifiziertes Binary-Beispiel).",
        example='FileDacl.Add ("%App%", %$Everyone%, SET, READ, SUB_CONTAINERS_AND_OBJECTS_INHERIT)',
        pitfall="Konten über die %$…%-Gruppenvariablen (lokalisiert) referenzieren.",
    ),
    "FileDacl.Del": SecurityOpDoc(
        op="FileDacl.Del",
        syntax='FileDacl.Del ("<Pfad>", <Konto>)',
        semantics="Entfernt explizite ACEs eines Kontos von der Datei/Ordner-ACL.",
        example='FileDacl.Del ("%App%", %$Everyone%)',
        pitfall="Geerbte ACEs werden nicht entfernt.",
    ),
    "FileDaclEx.Add": SecurityOpDoc(
        op="FileDaclEx.Add",
        syntax='FileDaclEx.Add (…erweiterte ACE-Parameter…)',
        semantics="Erweiterte Variante von FileDacl.Add mit detaillierter ACE-Steuerung "
        "(Zugriffsmaske statt Sammelrechte).",
        example='FileDaclEx.Add ("%App%\\data", %$DomainUsers%, SET, 0x1FFFF, '
        "SUB_CONTAINERS_AND_OBJECTS_INHERIT)",
        pitfall="Bitmaske der Zugriffsrechte exakt angeben.",
    ),
    "RegDacl.Add": SecurityOpDoc(
        op="RegDacl.Add",
        syntax='RegDacl.Add (HKEY_LOCAL_MACHINE, "<Key>", <Konto>, SET, <Rechte>, <Vererbung>)',
        semantics="Setzt Registry-Berechtigungen (verifiziertes Binary-Beispiel mit ALL und "
        "SUB_CONTAINERS_AND_OBJECTS_INHERIT).",
        example='RegDacl.Add (HKEY_LOCAL_MACHINE, "Software\\Vendor\\App", %$Everyone%, SET, READ, '
        "SUB_CONTAINERS_AND_OBJECTS_INHERIT)",
        pitfall="Root als Konstante (HKEY_LOCAL_MACHINE), nicht als String 'HKLM'.",
    ),
    "RegDacl.Del": SecurityOpDoc(
        op="RegDacl.Del",
        syntax='RegDacl.Del (HKEY_LOCAL_MACHINE, "<Key>", <Konto>)',
        semantics="Entfernt explizite ACEs eines Kontos aus der Registry-ACL.",
        example='RegDacl.Del (HKEY_LOCAL_MACHINE, "Software\\Vendor\\App", %$Everyone%)',
        pitfall="—",
    ),
    "NetShare.Add": SecurityOpDoc(
        op="NetShare.Add",
        syntax='NetShare.Add ("<Pfad>","<ShareName>","<Kommentar>")',
        semantics="Erstellt eine Freigabe (SMB-Share) für einen Ordner.",
        example='NetShare.Add ("%App%\\public","AppPublic$","Public der App")',
        pitfall="Dollar-Suffix versteckt die Freigabe in der Netzwerkumgebung.",
    ),
    "NetShare.Del": SecurityOpDoc(
        op="NetShare.Del",
        syntax='NetShare.Del ("<ShareName>")',
        semantics="Entfernt eine Freigabe (der Ordner bleibt erhalten).",
        example='NetShare.Del ("AppPublic$")',
        pitfall="—",
    ),
    "NetShareDacl.Add": SecurityOpDoc(
        op="NetShareDacl.Add",
        syntax='NetShareDacl.Add ("<ShareName>", <Konto>, SET, <Rechte>)',
        semantics="Setzt die Freigabe-Berechtigungen (Share-ACL) – getrennt von der NTFS-ACL.",
        example='NetShareDacl.Add ("AppPublic$", %$DomainUsers%, SET, READ)',
        pitfall="Effektive Rechte = Schnittmenge aus Share- und NTFS-ACL.",
    ),
    "PrinterDacl": SecurityOpDoc(
        op="PrinterDacl(.Add/.Del)",
        syntax='PrinterDacl.Add ("<Drucker>", <Konto>, SET, <Rechte>)',
        semantics="Setzt Drucker-Berechtigungen (Print-ACL) – Teil der dokumentierten Security-DSL.",
        example='PrinterDacl.Add ("Kassendrucker", %$Everyone%, SET, READ)',
        pitfall="—",
    ),
    "NetDomain.Join": SecurityOpDoc(
        op="NetDomain.Join",
        syntax="NetDomain.Join ('<Domäne>','<Konto>','<Passwort>')",
        semantics="Tritt der Maschine einer Domäne bei (vollständige DSL-Operation, Legacy-Help "
        "Section 43).",
        example="NetDomain.Join ('CORP','CORP\\svcJoiner','<verschlüsselt>')",
        pitfall="Benötigt Domänen-Join-Rechte; Passwort verschlüsselt; Reboot erforderlich.",
    ),
    "NetDomain.Unjoin": SecurityOpDoc(
        op="NetDomain.Unjoin",
        syntax="NetDomain.Unjoin ('<Konto>','<Passwort>')",
        semantics="Entfernt die Maschine aus der Domäne (in Arbeitsgruppe).",
        example="NetDomain.Unjoin ('CORP\\svcJoiner','<verschlüsselt>')",
        pitfall="Computerkonto in der Domäne wird ggf. deaktiviert zurückgelassen.",
    ),
}

# Kontext der [Security:]-Abarbeitung : Referenzzähler unter
# HKLM\Software\UsageCount\Setup; Konstanten PRIV_GUEST/PRIV_USER/PRIV_ADMIN,
# DONT_EXPIRE_PASSWD, ACE-Vererbungsflags.
SECURITY_DSL_CONSTANTS: tuple[tuple[str, str], ...] = (
    ("PRIV_GUEST", "Kontotyp Gast für LocalUser.Add"),
    ("PRIV_USER", "Kontotyp Standardbenutzer für LocalUser.Add"),
    ("PRIV_ADMIN", "Kontotyp Administrator für LocalUser.Add"),
    ("DONT_EXPIRE_PASSWD", "Passwort läuft nie ab (LocalUser-Flag)"),
    ("SET", "ACL-Modus: Rechte setzen (statt akkumulieren)"),
    ("READ / CHANGE / ALL", "Sammelrechte für Dacl-Operationen"),
    ("SUB_CONTAINERS_AND_OBJECTS_INHERIT", "ACE-Vererbung auf Unterordner und Objekte"),
    ("UsageCount", "Referenzzähler der [Security:]-Ops unter HKLM\\Software\\UsageCount\\Setup"),
)


def lookup_security_op(op_name: str) -> SecurityOpDoc | None:
    return SECURITY_DSL_DOCS.get(op_name.casefold().replace(" ", "")) or next(
        (doc for key, doc in SECURITY_DSL_DOCS.items() if key.casefold() == op_name.casefold()),
        None,
    )


# --------------------------------------------------------------------------
# Befehls-Referenz (Referenz Kapitel 5/6/8-11; '-' = Uninstall-Präfix)
# --------------------------------------------------------------------------

COMMAND_DOCS: dict[str, CommandDoc] = {
    "AddMeter": CommandDoc(
        name="AddMeter",
        syntax="AddMeter <Wert>  ·  -AddMeter <Wert>",
        semantics="Steuert oder reserviert Zeilen im Fortschrittsbalken des Empirum Setup-Assistenten. "
        "Der Standardaufruf 'AddMeter -1' reserviert im Maschinenteil einen Teilschritt für die Abarbeitung "
        "externer Installer (MSI, Unattended Setup), sodass der Balken während längerer Teilschritte nicht "
        "springt oder auf 0 % stehen bleibt.",
        uninstall="Bekommt im Deinstallationspfad das Minuszeichen: '-AddMeter -1' (gibt den Teilschritt bei "
        "der Deinstallation wieder frei und hält den Fortschrittsbalken synchron).",
        example="[Product]\r\nAddMeter -1\r\n#Set:Product, DONTDELETE\r\n"
        "#Set:Deinstallation, DELETE\r\n-AddMeter -1",
        pitfall="Ohne 'AddMeter -1' springt der Fortschrittsbalken des UEM-Agenten oft unregelmäßig "
        "von 0 % direkt auf 100 %. 'AddMeter' ist primär im interaktiven/Fortschritts-Modus sichtbar, "
        "gehört aber als Best Practice fest in jeden Hauptablauf.",
    ),
    "Abort": CommandDoc(
        name="Abort",
        syntax="Abort [<Fehlertext>]  ·  -Abort [<Fehlertext>]",
        semantics="Bricht die Paketverarbeitung sofort ab und meldet dem Empirum-Agenten den Status "
        "'Failure' (Fehlgeschlagen). Trägt den optionalen Fehlertext ins lokale Setup-Log ein und stoppt "
        "die weitere Ausführung aller nachfolgenden Sektionen.",
        uninstall="In Deinstallations-Fehlersektionen mit führendem Minus: '-Abort %ErrorText%'.",
        example="[Set:InstallationError]\r\nErrorLogMsg %ErrorLogMessage%\r\n"
        "Abort %ErrorText%",
        pitfall="Niemals 'Abort' ohne vorheriges 'ErrorLogMsg' aufrufen! Während 'Abort' den Prozess stoppt, "
        "sorgt 'ErrorLogMsg' für den dauerhaften Eintrag im 'SetupErrorLog' des Empirum-Servers/Depots. "
        "Nach 'Abort' finden keine nachfolgenden Aufräumarbeiten statt.",
    ),
    "AskKillProcesses": CommandDoc(
        name="AskKillProcesses",
        syntax="AskKillProcesses <TimeoutInSekunden>, <ProzessAlias1>[, <ProzessAlias2> ...]",
        semantics="Zeigt dem interaktiv angemeldeten Benutzer einen Dialog mit Countdown, in dem er "
        "aufgefordert wird, die gelisteten blockierenden Prozesse (definiert in der Sektion [Processes]) "
        "selbst zu schließen. Nach Ablauf des Timeouts greift der dort definierte Modus ('KILLPROCESS CONTINUE' "
        "für erzwungenes Beenden oder 'KILLPROCESS ABORT' für Paketabbruch).",
        uninstall="Mit führendem Minus für den Deinstallationslauf: '-AskKillProcesses 300, AppProc'.",
        example="[Processes]\r\nAppProc = acroread.exe, Adobe Acrobat Reader, KILLPROCESS CONTINUE\r\n\r\n"
        "[Set:Product]\r\nAskKillProcesses 300, AppProc",
        pitfall="Da der Befehl eine Benutzerinteraktion darstellt, setzt er eine interaktive Sitzung "
        "voraus (/AW oder sichtbare Ausführung). Läuft das Paket rein silent als SYSTEM ohne angemeldeten "
        "Benutzer, kann der Dialog hängen oder das Timeout ungeprüft ablaufen. Bei 'KILLPROCESS CONTINUE' "
        "droht Datenverlust durch erzwungene Prozessbeendigung.",
    ),
    "Call": CommandDoc(
        name="Call",
        syntax="Call <Programm> [Parameter]  ·  -Call <Programm> [Parameter]",
        semantics="Führt ein externes Programm synchron mit sichtbarem Konsolen- bzw. Anwendungsfenster aus "
        "und blockiert die Setup.exe, bis der Prozess beendet ist. Weist nach Beendigung der Variablen "
        "%ErrorLevel% den Rückgabecode (Exit-Code) des Prozesses zu.",
        uninstall="Mit führendem '-' für den Deinstallationspfad: '-Call \"%App%\\uninstall.exe\" /S'.",
        example='Call "%Src%\\Files\\helper.exe" /arg1\r\n'
        'If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf',
        pitfall="Öffnet ein sichtbares Konsolen-/Befehlsfenster, das Anwender irritieren kann! Für automatisierte "
        "Softwareverteilung im Depot ist fast immer 'CallHidden' die richtige Wahl. Pfade mit Leerzeichen müssen "
        "stets mit '\"%...%\"' gequotet werden.",
    ),
    "CallHidden": CommandDoc(
        name="CallHidden",
        syntax="CallHidden <Programm> [Parameter]  ·  -CallHidden <Programm> [Parameter]",
        semantics="Startet ein externes Programm unsichtbar und synchron mit komplett verstecktem Konsolenfenster (SW_HIDE) "
        "und wartet auf dessen Beendigung. Weist %ErrorLevel% den Rückgabecode des aufgerufenen Prozesses zu. "
        "Der universelle Standard für MSI- (MsiExec.exe), Unattended-EXE- und PowerShell-/CMD-Aufrufe.",
        uninstall="Mit '-' für Deinstallationsaufrufe: '-CallHidden MsiExec /X %V_ProductCode% /qn REBOOT=REALLYSUPPRESS'.",
        example='CallHidden MsiExec /I "%Src%\\Files\\setup.msi" ALLUSERS="1" REBOOT=REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        'If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf',
        pitfall="Pfade mit Leerzeichen zwingend in Anführungszeichen setzen! Unmittelbar nach dem Aufruf muss "
        "%ErrorLevel% geprüft werden, da nachfolgende Befehle den Returncode überschreiben. Bei MSI-Installationen "
        "sind 0 und 3010 (Reboot erforderlich) reguläre Erfolgs-Codes.",
    ),
    "Copy": CommandDoc(
        name="Copy",
        syntax="Copy <Quelle>, <Ziel>[, Flags]  ·  -Copy <Quelle>, <Ziel>",
        semantics="Kopiert eine Datei zur Laufzeit von der Quelle zum Ziel. Unterstützt Empirum-Pfade "
        "wie %Src%, %App%, %ProgramFiles% oder %AppData%. Erweiterte Form (verifiziert, "
        "xcopy-artig): 'Copy <Quelle> <Ziel> [/S] [/D] [/EXCLUDE:<Datei>]' – /S rekursiv, "
        "/D nur neuere Dateien, /EXCLUDE schließt Muster aus.",
        uninstall="Wird bei der Deinstallation automatisch rückgängig gemacht (Interpreter-Undo-Log); "
        "eine zusätzliche '-'-Spiegelzeile ist nicht nötig.",
        example='Copy "%Src%\\Files\\settings.json", "%App%\\settings.json"',
        pitfall="Für das Ausrollen großer statischer Dateisammlungen ist die Sektion [Installer] vorzuziehen, "
        "da sie Prüfsummen, automatische Ordnererstellung und Paketkomprimierung bietet. Dateipfade immer quoten. "
        "Bei der erweiterten Form werden Argumente per Leerzeichen (nicht Komma) getrennt.",
    ),
    "Del": CommandDoc(
        name="Del",
        syntax="Del <Dateipfad>  ·  -Del <Dateipfad>",
        semantics="Löscht eine einzelne Datei dauerhaft vom Dateisystem.",
        uninstall="Mit führendem '-': '-Del \"%CommonDesktop%\\App.lnk\"' entfernt die Datei bei der Deinstallation.",
        example='Del "%Temp%\\install_temp.log"\r\n-Del "%CommonDesktop%\\%ProductName%.lnk"',
        pitfall="Pfade immer in Anführungszeichen fassen ('\"%Path%\"'). 'Del' kann keine ganzen Ordnerbäume "
        "löschen – dafür ist 'DelTree' zuständig. Wildcards (*.*) sollten vermieden werden.",
    ),
    "DelTree": CommandDoc(
        name="DelTree",
        syntax="DelTree <Verzeichnispfad>  ·  -DelTree <Verzeichnispfad>",
        semantics="Löscht ein Verzeichnis rekursiv mit allen darin enthaltenen Dateien und Unterverzeichnissen. "
        "De-facto-Standard zur Bereinigung des Installationsverzeichnisses bei der Deinstallation.",
        uninstall="Mit führendem Minus: '-DelTree \"%App%\"'.",
        example='-DelTree "%App%"\r\n-DelTree "%CommonPrograms%\\%DeveloperName%"',
        pitfall="NIEMALS mit abschließendem Backslash angeben (z. B. 'DelTree \"%App%\\\"' erzeugt VAL-003, "
        "da die Empirum-Engine den Backslash oft als Syntaxfehler interpretiert)! Niemals auf Stammordner wie "
        "%ProgramFiles%, C:\\ oder Systemordner anwenden (VAL-007).",
    ),
    "Echo": CommandDoc(
        name="Echo",
        syntax="Echo <Text>  ·  -Echo <Text>",
        semantics="Schreibt eine Textzeile in die Protokolldatei der Installation zur Statuskontrolle "
        "und Diagnose im Empirum Management Center.",
        uninstall="Mit '-' für Meldungen im Deinstallationslauf: '-Echo Deinstallation von %ProductName% beendet'.",
        example="Echo [Setup] Starte Installation von %ProductName% %Version%...",
        pitfall="'Echo' setzt keine Fehlercodes zurück und ersetzt keine strukturierte Fehlerbehandlung mit "
        "'ErrorLogMsg' und 'Abort'.",
    ),
    "EndIf": CommandDoc(
        name="EndIf",
        syntax='If <Bedingung> Then "<Sektion>" [Else "<Sektion>"] EndIf',
        semantics="Terminiert die einzeilige Empirum If-Kontrollstruktur. In der Setup.inf-Spezifikation "
        "MUSS die gesamte Verzweigung in einer einzelnen Zeile formuliert sein.",
        uninstall="Kontrollstrukturen erhalten kein '-'.",
        example='If %ErrorLevel% == "3010" Then "RebootRequired" EndIf',
        pitfall="Ein 'Then' ohne zugehöriges 'EndIf' in derselben Zeile ist ein fataler Syntaxfehler (VAL-020). "
        "Mehrzeilige If-Blöcke wie in Visual Basic oder PowerShell werden von Empirum nicht unterstützt!",
    ),
    "ErrorLogMsg": CommandDoc(
        name="ErrorLogMsg",
        syntax="ErrorLogMsg <Meldung>  ·  -ErrorLogMsg <Meldung>",
        semantics="Protokolliert eine formatierte Fehlermeldung mit Fehlercode und Kontext im SetupErrorLog "
        "des Empirum-Systems. Bricht das Skript nicht selbstständig ab.",
        uninstall="Mit '-' in Deinstallations-Fehlersektionen: '-ErrorLogMsg %ErrorLogMessage%'.",
        example="[Set:InstallationError]\r\nErrorLogMsg %ErrorLogMessage% (Returncode: %ErrorLevel%)\r\n"
        "Abort %ErrorText%",
        pitfall="Immer in Kombination mit 'Abort' verwenden, um einen sichtbaren Paketfehler im Management Center "
        "zu erzeugen. Ohne 'Abort' läuft das Skript trotz protokollierter Fehlermeldung weiter.",
    ),
    "Exit": CommandDoc(
        name="Exit",
        syntax="Exit",
        semantics="Beendet die Ausführung der aktuellen Sektion oder der gesamten Setup.inf vorzeitig mit "
        "Erfolgsstatus (Success).",
        uninstall="Kontrollanweisung; erhält kein '-'.",
        example='[Set:CheckRequirements]\r\nIf DoesFileExist ("%App%\\installed.flag") == "1" Then "Set:SkipAll" EndIf\r\n\r\n'
        "[Set:SkipAll]\r\nEcho Anwendung bereits vorhanden, überspringe...\r\nExit",
        pitfall="Wenn 'Exit' in einer per '#' aufgerufenen Sektion steht, bricht es die Ausführung ab. "
        "Bei unbedachtem Einsatz können nachfolgende Schritte in [Product] (z. B. Registry, Verknüpfungen) "
        "unbemerkt übersprungen werden.",
    ),
    "For": CommandDoc(
        name="For",
        syntax="For <Variable>, <Start>, <Ende>[, <Schrittweite>], <Zielsektion>",
        semantics="Führt eine Zählschleife aus. In jedem Durchlauf wird die angegebene Zielsektion ausgeführt, "
        "wobei der Zähler über '%<Variable>%' (z. B. '%Counter%') abrufbar ist. Bei der Deinstallation führt die "
        "Setup.exe die Schleife automatisch rückwärts aus!",
        uninstall="Bekommt kein '-'; die Setup.exe kehrt die Zählrichtung bei Deinstallation selbstständig von "
        "<Ende> nach <Start> um.",
        example="[Set:Installation]\r\nFor counter, 1, 5, , EchoCounter\r\n\r\n"
        "[EchoCounter]\r\nEcho Installation Schritt %Counter%\r\n-Echo Deinstallation Schritt %Counter%",
        pitfall="Soll die Zählrichtung bei der Installation absteigend sein, muss eine negative Schrittweite "
        "angegeben werden ('For counter, 5, 1, -1, EchoCounter'). Keine komplex verschachtelten Schleifen bauen.",
    ),
    "If": CommandDoc(
        name="If",
        syntax='If <Bedingung> Then "<Sektion>" [Else "<Sektion>"] EndIf',
        semantics="Bedingte Verzweigung zu benannten Untersektionen (GOSUB-Prinzip). Unterstützt Vergleiche "
        "von Variablen (%ErrorLevel% == \"0\") sowie Prädikatsfunktionen (DoesRegKeyExist(...) == \"1\", "
        "DoesFileExist(...) == \"1\"). Kehrt nach Beendigung der Zielsektion hinter das EndIf zurück.",
        uninstall="Kontrollzeilen erhalten kein '-'.",
        example='If DoesRegKeyExist ("%RegUninstallKey%") == "1" Then "Set:Repair" Else "Set:Install" EndIf\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf',
        pitfall="Hinter 'Then' und 'Else' dürfen AUSSCHLIESSLICH Sektionsnamen in Anführungszeichen stehen – "
        "keine Direktbefehle! Vergleichswerte müssen in Anführungszeichen stehen (\"0\", \"1\"). "
        "Funktionsprädikate selbst nicht zusätzlich in Anführungszeichen fassen (VAL-002).",
    ),
    "KillProcess": CommandDoc(
        name="KillProcess",
        syntax="KillProcess <Prozessname>[, <Timeout>[, <Abfrage>]]  ·  -KillProcess <Prozessname>",
        semantics="Beendet sofort und ohne Rückfrage einen laufenden Windows-Prozess anhand seines "
            "Dateinamens (entspricht taskkill.exe /F /IM <Prozessname>). Erweiterte, dokumentierte Form: "
            "optionale Parameter <Timeout> (Sekunden warten) und <Abfrage>; im Prozessnamen sind "
            "Wildcards erlaubt.",
        uninstall="Mit '-' bei Deinstallation: '-KillProcess app.exe'.",
        example="KillProcess acroread.exe\r\nKillProcess app*.exe, 30, 1",
        pitfall="Harte Terminierung – Anwender verlieren ungespeicherte Daten. Für interaktive Applikationen "
        "ist 'AskKillProcesses' die empfohlene, anwenderfreundliche Alternative. Wildcards mit Bedacht "
        "einsetzen ('*' beendet alle passenden Prozesse!).",
    ),
    "MD": CommandDoc(
        name="MD",
        syntax="MD <Verzeichnispfad>",
        semantics="Erstellt ein Verzeichnis (Make Directory) inklusive aller notwendigen übergeordneten "
        "Ordnerstrukturen, falls diese noch nicht existieren. Lange Form: 'MkDir'.",
        uninstall="Wird bei der Deinstallation automatisch rückgängig gemacht (Interpreter-Undo-Log, "
        "verifizierte Semantik) – eine '-MD'-Spiegelzeile ist nicht nötig.",
        example='MD "%ProgramData%\\Vendor\\AppName\\Config"\r\nMD "%App%\\bin"',
        pitfall="Trailing-Backslashes sind bei 'MD' im Unterschied zu 'DelTree' unkritisch. Verzeichnisse, die "
        "über [Installer]/Copy-Flags (CASCADED) angelegt wurden, bereinigt ebenfalls der Uninstall-Lauf.",
    ),
    "Next": CommandDoc(
        name="Next",
        syntax="Next  (Schleifenende zu For …)",
        semantics="Schließt optional einen Schleifenblock ab, falls dieser mehrzeilig ohne Zielsektion "
        "formuliert wurde.",
        uninstall="Ohne '-'.",
        example="For i, 1, 3, , StepSection\r\n\r\n[StepSection]\r\nEcho Schritt %i%",
        pitfall="Empirum-Best-Practice ist der Aufruf über eine Zielsektion ('For Var,1,5,,Sektion'). Ein "
        "unvollständiges oder unpassendes 'Next' führt zu Syntaxfehlern.",
    ),
    "ReplaceEnv": CommandDoc(
        name="ReplaceEnv",
        syntax="ReplaceEnv <Variablenname>  ·  -ReplaceEnv <Variablenname>",
        semantics="Expandiert den aktuellen Wert einer Variablen und löst indirekte Referenzen, "
        "Registry-Abfragen (%HKLM,...%) oder Maschinen-/Benutzerwerte (VM_*, VU_*) sofort auf.",
        uninstall="Mit '-' für die Deinstallationsphase: '-ReplaceEnv MSIGUID_X64'.",
        example="Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%, x64)\r\n"
        "ReplaceEnv MSIGUID_X64\r\n"
        'If "%MSIGUID_X64%" != "" Then "Set:UninstallOld" EndIf',
        pitfall="Ohne 'ReplaceEnv' bleibt die Variable unaufgelöst und enthält den Literal-Ausdruck oder "
        "ist leer. Unbedingt nach 'Set' mit Funktions- oder Registry-Zuweisung ausführen!",
    ),
    "Set": CommandDoc(
        name="Set",
        syntax="Set <Variable> = <Wert/Ausdruck>  ·  -Set <Variable> = <Wert>",
        semantics="Weist einer Variablen einen Wert, einen Pfad, eine Umgebungsvariable oder das Ergebnis "
        "einer Funktion (z. B. GetUninstallKeyName) zu.",
        uninstall="Mit '-': '-Set Variable = ...' für Deinstallationszuweisungen.",
        example="Set V_LogFile = %Temp%\\Setup_%ProductName%.log\r\n"
        "Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%, x64)\r\n"
        "ReplaceEnv MSIGUID_X64",
        pitfall="Bei dynamischen Zuweisungen und Funktionen muss unmittelbar danach 'ReplaceEnv <Variable>' "
        "aufgerufen werden.",
    ),
    "SetReboot": CommandDoc(
        name="SetReboot",
        syntax="SetReboot <Modus>  ·  -SetReboot <Modus>",
        semantics="Setzt eine kontrollierte Reboot-Anforderung für das Paket an die Empirum-Engine "
        "('1' = Reboot anfordern). Standardziel für den Returncode 3010 nach MSI- und Treiber-Setups.",
        uninstall="Mit '-': '-SetReboot 1' fordert einen Neustart nach der Deinstallation an.",
        example="[RebootRequired]\r\nSetReboot 1\r\n-SetReboot 1",
        pitfall="Niemals statisch 'Reboot=1' in [Application] setzen, wenn der Neustart nur im Bedarfsfall "
        "erforderlich ist (VAL-009). Stattdessen nach der Installation per 'If %ErrorLevel% == \"3010\" "
        "Then \"RebootRequired\" EndIf' dynamisch 'SetReboot 1' triggern.",
    ),
    "Sleep": CommandDoc(
        name="Sleep",
        syntax="Sleep <Millisekunden>",
        semantics="Pausiert die Ausführung der Setup.exe für die angegebene Zeitspanne in Millisekunden "
        "(z. B. 'Sleep 3000' = 3 Sekunden). Typisch nach MSI-Installationen oder Deinstallationen, um dem System "
        "Zeit zum Freigeben von Dateihandles und Beenden von Hilfsprozessen zu geben.",
        uninstall="Läuft in beiden Richtungen gleichermaßen; erhält kein '-'.",
        example="Sleep 3000",
        pitfall="Strikte Befehlssyntax: 'Sleep 3000' (Command-Style mit Leerzeichen), NICHT 'Sleep=3000' schreiben! "
        "Nicht als Ersatz für saubere Prozessprüfungen missbrauchen.",
    ),
    # ------------------------------------------------------------------
    # Klasse 1 – undokumentierte Befehle (verifiziert 26.1.0, in der gesamten
    # offiziellen Hilfe nicht vorhanden; nur hinter Feature-Flag sichtbar).
    # ------------------------------------------------------------------
    "CollapseEnv": CommandDoc(
        name="CollapseEnv",
        syntax="CollapseEnv <Variable>",
        semantics="⚠ UNDOKUMENTIERT (Klasse 1): Wertet einen in der Variable gespeicherten "
        "Funktionsausdruck aus (verzögerte Auswertung). Top-Fund der Verifikation: "
        "voll funktionsfähig und von Matrix42 selbst in PSTBackupInfo.inf genutzt – "
        "Beispielkette: 'Set X=HexToString(\"%Reg%\",1)' → 'CollapseEnv X' → Ergebnis.",
        uninstall="Ohne '-'; Auswertungsphase.",
        example='Set X = HexToString ("%Reg%", 1)\r\nCollapseEnv X',
        pitfall="Kein offizieller Support, kein Sicherheitsnetz. Nur einsetzen, wenn das "
        "Verhalten gegen den Zielinterpreter 26.1.0 verifiziert wurde.",
    ),
    "Extract": CommandDoc(
        name="Extract",
        syntax="Extract <…>  (Parameter offen)",
        semantics="⚠ UNDOKUMENTIERT (Klasse 1): Entpackt Dateien aus der Setup.cab des Pakets. "
        "Befehlstabelle und 'Setup.cab'-String sind verifiziert; die genaue "
        "Parametersignatur ist ungeklärt.",
        uninstall="Unbekannt.",
        example="; Parameter offen – nicht ohne Verifikation einsetzen",
        pitfall="Semantik offen: Es existiert keine dokumentierte Parameterliste. Setup.cab "
        "trägt die Sonderfall-Disknummer 0. Nicht generieren, nur manuell prüfen.",
    ),
    "RenDir": CommandDoc(
        name="RenDir",
        syntax="RenDir <Alt> <Neu>",
        semantics="⚠ UNDOKUMENTIERT (Klasse 1): Benennt ein Verzeichnis um (verifizierte "
        "Befehlstabelle, keine Doku).",
        uninstall="Unbekannt (vermutlich analog Rename automatisch rückgängig).",
        example='RenDir "%App%\\old" "%App%\\new"',
        pitfall="Kein offizieller Support. Für dokumentierte Pfade 'Rename' für Dateien "
        "verwenden; Verzeichnisse besser über Kopie + DelTree abbilden.",
    ),
    "BlockInput": CommandDoc(
        name="BlockInput",
        syntax="BlockInput <0|1>",
        semantics="⚠ UNDOKUMENTIERT (Klasse 1): Sperrt die Benutzereingabe als Befehlsform "
        "(1 = Sperre an, 0 = auf). Dokumentiert ist nur der [Setup]-Key BlockInput=; "
        "im Paket-User-Ordner existiert sogar eine BlockInput.exe.",
        uninstall="Ohne '-'.",
        example="BlockInput 1\r\n… kritische Schritte …\r\nBlockInput 0",
        pitfall="Blockiert die Eingabe des angemeldeten Benutzers – bei Absturz zwischen "
        "an/aus bleibt die Sperre ggf. bestehen! Kein offizieller Support.",
    ),
    # ------------------------------------------------------------------
    # Verifizierte Erweiterung (Legacy-Help + Interpreter 26.1.0)
    # ------------------------------------------------------------------
    "AbortReboot": CommandDoc(
        name="AbortReboot",
        syntax="AbortReboot [<Text>]",
        semantics="Bricht die Paketverarbeitung ab und fordert zugleich einen Neustart an – "
        "Kombination aus Abort und Reboot-Anforderung für Fehlerfälle, die erst nach einem "
        "Neustart sauber wiederholbar sind.",
        uninstall="Mit führendem '-' in Deinstallations-Fehlersektionen.",
        example='[Set:InstallationError]\r\nErrorLogMsg %ErrorLogMessage%\r\nAbortReboot %ErrorText%',
        pitfall="Der Neustart wird auch im Fehlerfall gezogen – nachfolgende Aufräumschritte entfallen. "
        "Wie 'Abort' niemals ohne vorheriges 'ErrorLogMsg' verwenden.",
    ),
    "AbortSilent": CommandDoc(
        name="AbortSilent",
        syntax="AbortSilent [<Text>]",
        semantics="Bricht die Verarbeitung still (ohne Fehlerdialog) ab und schreibt LastError ins "
        "SwDepot-Log. Achtung, dokumentierte Sondersemantik: meldet dem Depot 'Success' und führt "
        "den Benutzerteil trotzdem aus!",
        uninstall="Mit führendem '-' im Deinstallationspfad.",
        example='AbortSilent "Vorbedingung nicht erfüllt – Überspringe %ProductName%"',
        pitfall="Nicht für echte Fehler verwenden: Das Paket erscheint im Software-Depot als ERFOLGREICH, "
        "obwohl der Maschinenteil abgebrochen wurde. Nur für bewusstes, still Überspringen gedacht.",
    ),
    "AddEventSource": CommandDoc(
        name="AddEventSource",
        syntax="AddEventSource <Name>",
        semantics="Registriert eine Ereignisquelle im Windows-Ereignisprotokoll, damit die Anwendung "
        "Einträge unter Application/<Name> schreiben kann. Deklarative Alternative: Sektion "
        "[EventSources].",
        uninstall="Erfolgt über die zugehörige Uninstall-Logik der [EventSources]-Sektion; als einzelner "
        "Befehl keine automatische Rücknahme.",
        example='AddEventSource "%ProductName%"',
        pitfall="Der Name muss zur MessageDLL/Registry der Anwendung passen, sonst schlägt das Schreiben "
        "von Ereignissen später fehl.",
    ),
    "AddMonitor": CommandDoc(
        name="AddMonitor",
        syntax="AddMonitor <Name>, <DLL>[, <Umgebung>]",
        semantics="Installiert einen Druckmonitor (Language Monitor) für den Druckspooler – Teil der "
        "Druckerverwaltungs-Befehlsfamilie (Legacy-Help Section 25).",
        uninstall="Gegenstück 'DeleteMonitor' in der Deinstallationssektion aufrufen.",
        example='AddMonitor "MyMon", "mymon.dll"',
        pitfall="Nur für Treiberpakete mit eigenem Monitor nötig; die DLL muss bereits kopiert sein.",
    ),
    "AddPort": CommandDoc(
        name="AddPort",
        syntax="AddPort <Name>[, <Host>]  ·  -AddPort <Name>",
        semantics="Legt einen Druckport an (z. B. Local Port oder TCP/IP-Port) – Teil der "
        "Druckerverwaltungs-Befehlsfamilie.",
        uninstall="Gegenstück 'DeletePort' in der Deinstallationssektion.",
        example='AddPort "LPT3:"',
        pitfall="Ports, die andere Drucker mitnutzen, dürfen bei Deinstallation nicht entfernt werden.",
    ),
    "AddPrinter": CommandDoc(
        name="AddPrinter",
        syntax="AddPrinter <Name>, <Treiber>, <Port>[, <Beschreibung>, …]  (16 Parameter, Legacy-Help Section 25)",
        semantics="Installiert einen Drucker mit Treiber, Port und Standardeinstellungen. Die vollständige "
        "16-parametrige Signatur ist in der Legacy-Hilfe 'Drucker-Befehle' dokumentiert.",
        uninstall="Mit '-' bzw. Gegenstück 'DeletePrinter' im Deinstallationspfad.",
        example='AddPrinter "Kassendrucker", "Generic / Text Only", "LPT1:"',
        pitfall="Treiber und Port müssen VOR dem Drucker existieren (AddPrinterDriver, AddPort). "
        "Reihenfolge in der Deinstallation exakt umgekehrt aufbauen.",
    ),
    "AddPrinterConnection": CommandDoc(
        name="AddPrinterConnection",
        syntax="AddPrinterConnection \\\\<Server>\\<Drucker>",
        semantics="Verbindet den aktuellen Benutzer mit einem freigegebenen Netzdrucker (per-user "
        "Verbindung).",
        uninstall="Gegenstück 'DeletePrinterConnection' – typischerweise im Benutzerteil (/AW).",
        example='AddPrinterConnection "\\\\PRINT01\\Etage1"',
        pitfall="Per-user-Verbindung: im Maschinenteil (SYSTEM) wirkungslos – CLIENT-Flag bzw. /AW nötig.",
    ),
    "AddPrinterDriver": CommandDoc(
        name="AddPrinterDriver",
        syntax="AddPrinterDriver <Name>, <Umgebung>, <Pfad>[, …]",
        semantics="Installiert einen Druckertreiber in den Treiberspeicher (maschinenweit).",
        uninstall="Gegenstück 'DeletePrinterDriver' in der Deinstallationssektion.",
        example='AddPrinterDriver "Generic / Text Only", "Windows x64", "%Src%\\Driver"',
        pitfall="Architektur (Umgebung) muss zur Zielplattform passen; treiberalte Pakete benötigen "
        "ggf. beide Varianten (x86/x64).",
    ),
    "AddPrintProcessor": CommandDoc(
        name="AddPrintProcessor",
        syntax="AddPrintProcessor <Name>, <DLL>[, <Umgebung>]",
        semantics="Registriert einen Druckprozessor (Render-Pipeline) für den Spooler.",
        uninstall="Gegenstück 'DeletePrintProcessor'.",
        example='AddPrintProcessor "MyProc", "myproc.dll"',
        pitfall="Reines Spezialwerkzeug für Treiberpakete.",
    ),
    "AddPrintProvider": CommandDoc(
        name="AddPrintProvider",
        syntax="AddPrintProvider <Name>, <DLL>[, …]",
        semantics="Registriert einen Druckprovider (Port-Monitor-DLL des Spoolers).",
        uninstall="Gegenstück 'DeletePrintProvider'.",
        example='AddPrintProvider "MyProv", "myprov.dll"',
        pitfall="Reines Spezialwerkzeug; Fehler hier legen den kompletten Spooler lahm.",
    ),
    "AddService": CommandDoc(
        name="AddService",
        syntax="AddService <Parameter>  (CreateService-Parameter)",
        semantics="Legt einen Windows-Dienst an (Win32 CreateService-Parameter). Alternativen: Sektion "
        "[Services] oder das SERVICE-Copyflag in [Installer] – SERVICE_AUTO_START startet sofort.",
        uninstall="Gegenstück 'DeleteService' in der Deinstallationssektion.",
        example="[Services]\r\nSvc1=Mein Dienst,0x10,2,1,,;HKLM\\Software\\MeinDienst,,",
        pitfall="Dienstpasswörter ab Setup.inf-Version 6.5 nur verschlüsselt (EmpCrypt.exe). Bevorzugt "
        "[Services]-Sektion statt Einzelbefehl verwenden.",
    ),
    "Append": CommandDoc(
        name="Append",
        syntax="Append <Quelle> <Ziel>",
        semantics="Hängt den Inhalt der Quelldatei an die Zieldatei an (ohne die Zieldatei zu ersetzen).",
        uninstall="Keine automatische Rücknahme – Rückbau ggf. über eigene Deinstallationslogik.",
        example='Append "%Src%\\Files\\add.cfg", "%App%\\config.cfg"',
        pitfall="Zieldatei muss existieren; ansonsten vorher per Copy anlegen.",
    ),
    "Beep": CommandDoc(
        name="Beep",
        syntax="Beep [0-4]",
        semantics="Gibt einen akustischen Signalton (Varianten 0–4) aus. Läuft als einer der wenigen "
        "Befehle IMMER auch bei der Deinstallation – auch ohne '-'.",
        uninstall="Ohne '-' in beiden Richtungen aktiv (verifizierte Semantik).",
        example="Beep 1",
        pitfall="Bei silenten Verteilungen (/S0-/S1) ohne sichtbaren Dialog bleibt nur der Ton – "
        "überspringen oder abhängig vom Silent-Level verzweigen.",
    ),
    "CallRunAs": CommandDoc(
        name="CallRunAs",
        syntax='CallRunAs /U:<Konto> /P:<Passwort> "<Programm>" [Parameter]',
        semantics="Startet ein Programm wartend unter einem anderen Benutzerkonto (RunAs). Passwörter "
        "müssen ab Setup.inf-Version 6.5 Setup-verschlüsselt angegeben werden (EmpCrypt.exe).",
        uninstall="Mit führendem '-' für Deinstallationsaufrufe.",
        example='CallRunAs /U:CORP\\svcInstaller /P:<verschlüsselt> "%Src%\\Files\\agent.exe" /S',
        pitfall="Klartext-Passwörter werden ab INF-Version 6.5 abgelehnt. Konto braucht 'Log on as a "
        "batch job'-Rechte; Fehlercodes wie ErrorLevel auswerten.",
    ),
    "CallRunAsHidden": CommandDoc(
        name="CallRunAsHidden",
        syntax='CallRunAsHidden /U:<Konto> /P:<Passwort> "<Programm>" [Parameter]',
        semantics="Wie 'CallRunAs', aber mit komplett verstecktem Fenster – Standard für automatisierte "
        "RunAs-Aufrufe im Softwarepaket.",
        uninstall="Mit führendem '-' für Deinstallationsaufrufe.",
        example='CallRunAsHidden /U:CORP\\svcInstaller /P:<verschlüsselt> "reg.exe" add …',
        pitfall="Gleiche Verschlüsselungspflicht wie CallRunAs; %ErrorLevel% unmittelbar danach prüfen.",
    ),
    "CD": CommandDoc(
        name="CD",
        syntax="CD <Pfad>  ·  ChDir <Pfad>",
        semantics="Wechselt das Arbeitsverzeichnis für nachfolgende Programmstarts (Call/CallHidden). "
        "Läuft IMMER auch bei der Deinstallation – auch ohne '-'.",
        uninstall="Ohne '-' in beiden Richtungen aktiv (verifizierte Semantik).",
        example='CD "%TEMP%"',
        pitfall="Wirkt nur auf relative Pfade nachfolgender Aufrufe; absolute Pfade ignorieren das "
        "Arbeitsverzeichnis.",
    ),
    "ChDir": CommandDoc(
        name="ChDir",
        syntax="ChDir <Pfad>  ·  CD <Pfad>",
        semantics="Lange Form von 'CD': wechselt das Arbeitsverzeichnis. Läuft immer auch bei der "
        "Deinstallation – auch ohne '-'.",
        uninstall="Ohne '-' in beiden Richtungen aktiv.",
        example='ChDir "%App%\\bin"',
        pitfall="Siehe 'CD'.",
    ),
    "CloseWindow": CommandDoc(
        name="CloseWindow",
        syntax="CloseWindow <Titel>[, <Flags>[, <Timeout>[, <Prompt>]]]",
        semantics="Schließt ein Fenster anhand des Titels (Wildcards erlaubt). Flags: CLOSEWINDOW "
        "(freundlich), DESTROYWINDOW, QUERYCLOSEWINDOW (rückfragen) und KILLPROCESS, jeweils "
        "kombinierbar mit CONTINUE/ABORT für das weitere Verhalten.",
        uninstall="Mit führendem '-' im Deinstallationspfad.",
        example='CloseWindow "Unbenannt - Editor*", QUERYCLOSEWINDOW, 30, 1',
        pitfall="Wildcards im Titel können fremde Fenster treffen; im Silent-Modus übernimmt der "
        "CONTINUE/ABORT-Modus die Entscheidung statt des Benutzers.",
    ),
    "DDE": CommandDoc(
        name="DDE",
        syntax="DDE <…>",
        semantics="Historische DDE-Steuerung des Windows 3.x/9x-Program-Managers (Gruppen/Icons). "
        "Nur für Legacy-Pakete aus der Vor-NT-Ära relevant.",
        uninstall="Keine Relevanz.",
        example="; nur Legacy",
        pitfall="In modernen Umgebungen nicht verwenden; funktioniert nicht mit dem Windows-95-Programm-"
        "Manager-losen Shells.",
    ),
    "Decrement": CommandDoc(
        name="Decrement",
        syntax="Decrement (<Variable>[, n])",
        semantics="Vermindert eine Variable um n (Standard 1). Arbeitet auch direkt auf Registry-Werten "
        "('%HKLM,…%'-Notation) und INI-Werten ('%Datei,Sektion,Key%').",
        uninstall="Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.",
        example="Decrement (Zaehler, 1)",
        pitfall="Nicht-numerische Inhalte führen zu Laufzeitfehlern; bei Registry-Zielen stellt "
        "Decrement sicher, dass der Wert numerisch ist.",
    ),
    "Divide": CommandDoc(
        name="Divide",
        syntax="Divide (<Variable>, n)",
        semantics="Dividiert eine Variable durch n. Arbeitet auch direkt auf Registry- und INI-Werten.",
        uninstall="Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.",
        example="Divide (GroesseKB, 1024)",
        pitfall="Division durch 0 bricht das Paket ab; Ergebnisse sind ganzzahlig.",
    ),
    "DeleteAllPrinters": CommandDoc(
        name="DeleteAllPrinters",
        syntax="DeleteAllPrinters",
        semantics="Entfernt alle auf dem System eingerichteten Drucker – radikales Gegenstück der "
        "Druckerfamilie, z. B. für kioskartige Setups.",
        uninstall="Nur in Deinstallations-/Aufräum-Szenarien verwenden.",
        example="-DeleteAllPrinters",
        pitfall="Entfernt auch nutzerdefinierte und Netzdrucker – in normalen Paketen DURCHAUS tabu!",
    ),
    "DeleteMonitor": CommandDoc(
        name="DeleteMonitor",
        syntax="DeleteMonitor <Name>[, <Umgebung>]",
        semantics="Entfernt einen Druckmonitor – Gegenstück zu 'AddMonitor'.",
        uninstall="Typischerweise mit '-' in der Deinstallationssektion.",
        example='-DeleteMonitor "MyMon"',
        pitfall="Nur entfernen, wenn kein Drucker den Monitor mehr nutzt.",
    ),
    "DeletePort": CommandDoc(
        name="DeletePort",
        syntax="DeletePort <Name>",
        semantics="Entfernt einen Druckport – Gegenstück zu 'AddPort'.",
        uninstall="Typischerweise mit '-' in der Deinstallationssektion.",
        example='-DeletePort "LPT3:"',
        pitfall="Standardports (LPT1:, COM1:, FILE:) dürfen nie gelöscht werden.",
    ),
    "DeletePrinter": CommandDoc(
        name="DeletePrinter",
        syntax="DeletePrinter <Name>",
        semantics="Entfernt einen Drucker – Gegenstück zu 'AddPrinter'.",
        uninstall="Typischerweise mit '-' in der Deinstallationssektion.",
        example='-DeletePrinter "Kassendrucker"',
        pitfall="Zuerst Drucker, dann Treiber, dann Ports/Monitore löschen (umgekehrte Installationsreihenfolge).",
    ),
    "DeletePrinterConnection": CommandDoc(
        name="DeletePrinterConnection",
        syntax="DeletePrinterConnection \\\\<Server>\\<Drucker>",
        semantics="Entfernt eine per-user Netzdrucker-Verbindung – Gegenstück zu 'AddPrinterConnection'.",
        uninstall="Im Benutzerteil (/AW) der Deinstallation.",
        example='-DeletePrinterConnection "\\\\PRINT01\\Etage1"',
        pitfall="Per-user-Operation – im Maschinenteil wirkungslos.",
    ),
    "DeletePrinterDriver": CommandDoc(
        name="DeletePrinterDriver",
        syntax="DeletePrinterDriver <Name>[, <Umgebung>]",
        semantics="Entfernt einen Druckertreiber – Gegenstück zu 'AddPrinterDriver'.",
        uninstall="Typischerweise mit '-' in der Deinstallationssektion.",
        example='-DeletePrinterDriver "Generic / Text Only"',
        pitfall="Treiber, die noch von anderen Druckern verwendet werden, lassen sich nicht entfernen.",
    ),
    "DeletePrintProcessor": CommandDoc(
        name="DeletePrintProcessor",
        syntax="DeletePrintProcessor <Name>[, <Umgebung>]",
        semantics="Entfernt einen Druckprozessor – Gegenstück zu 'AddPrintProcessor'.",
        uninstall="Typischerweise mit '-' in der Deinstallationssektion.",
        example='-DeletePrintProcessor "MyProc"',
        pitfall="Nur entfernen, wenn kein Drucker den Prozessor mehr referenziert.",
    ),
    "DeletePrintProvider": CommandDoc(
        name="DeletePrintProvider",
        syntax="DeletePrintProvider <Name>",
        semantics="Entfernt einen Druckprovider – Gegenstück zu 'AddPrintProvider'.",
        uninstall="Typischerweise mit '-' in der Deinstallationssektion.",
        example='-DeletePrintProvider "MyProv"',
        pitfall="Falsche Reihenfolge kann den Spooler-Dienst blockieren.",
    ),
    "DeleteService": CommandDoc(
        name="DeleteService",
        syntax="DeleteService <Dienstname>",
        semantics="Entfernt einen Windows-Dienst – Gegenstück zu 'AddService' bzw. der [Services]-Sektion.",
        uninstall="Typischerweise mit '-' in der Deinstallationssektion.",
        example='-DeleteService "MeinDienst"',
        pitfall="Läuft der Dienst noch, vorher 'StopService' aufrufen (oder Stop dependenter Dienste).",
    ),
    "DeleteXml": CommandDoc(
        name="DeleteXml",
        syntax="DeleteXml (<Datei>, <XPath>)",
        semantics="Löscht XML-Knoten, die dem XPath-Ausdruck entsprechen, in der Datei.",
        uninstall="Keine automatische Rücknahme – Original ggf. vorher sichern.",
        example='DeleteXml ("%App%\\config.xml", "/Konfiguration/Altlasten/*")',
        pitfall="XPath präzise fassen – zu breite Ausdrücke löschen mehr als beabsichtigt.",
    ),
    "Erase": CommandDoc(
        name="Erase",
        syntax="Erase <Dateipfad>  ·  -Erase <Dateipfad>",
        semantics="Alias für 'Del' – löscht eine einzelne Datei.",
        uninstall="Wie 'Del' mit führendem '-'.",
        example='Erase "%Temp%\\install_temp.log"',
        pitfall="In neuen Paketen die kurze Standardform 'Del' bevorzugen.",
    ),
    "EmptyClipboard": CommandDoc(
        name="EmptyClipboard",
        syntax="EmptyClipboard",
        semantics="Leert die Windows-Zwischenablage komplett.",
        uninstall="Keine Rücknahme nötig/sinnvoll.",
        example="EmptyClipboard",
        pitfall="Vernichtet ungefragt Benutzerdaten in der Zwischenablage – nur in begründeten "
        "Sicherheits-/Kiosk-Szenarien einsetzen.",
    ),
    "Increment": CommandDoc(
        name="Increment",
        syntax="Increment (<Variable>[, n])",
        semantics="Erhöht eine Variable um n (Standard 1). Arbeitet auch direkt auf Registry-Werten "
        "('%HKLM,…%'-Notation) und INI-Werten.",
        uninstall="Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.",
        example="Increment (Zaehler)",
        pitfall="Nicht-numerische Werte führen zu Laufzeitfehlern.",
    ),
    "Multiply": CommandDoc(
        name="Multiply",
        syntax="Multiply (<Variable>, n)",
        semantics="Multipliziert eine Variable mit n. Arbeitet auch direkt auf Registry- und INI-Werten.",
        uninstall="Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.",
        example="Multiply (GroesseMB, 1024)",
        pitfall="Ganzzahlüberläufe bei großen Werten beachten (32-Bit-Bereich).",
    ),
    "MkDir": CommandDoc(
        name="MkDir",
        syntax="MkDir <Verzeichnispfad>",
        semantics="Lange Form von 'MD': erstellt ein Verzeichnis inklusive übergeordneter Strukturen.",
        uninstall="Wie 'MD' – automatische Rücknahme über den Interpreter-Undo-Log.",
        example='MkDir "%App%\\logs"',
        pitfall="Siehe 'MD'.",
    ),
    "PlaySound": CommandDoc(
        name="PlaySound",
        syntax="PlaySound <Disk>, <Name>, <Flags>",
        semantics="Spielt eine Sounddatei aus dem Paket ab (z. B. während des Begrüßungsdialogs).",
        uninstall="Ohne Bedeutung für die Deinstallation.",
        example='PlaySound 1, "intro.wav", 0',
        pitfall="Bei silent Verteilung ohne Audiosession wirkungslos; Datei muss über [Installer] "
        "mitkopiert werden.",
    ),
    "Prompt": CommandDoc(
        name="Prompt",
        syntax="Prompt <Variable>",
        semantics="Stellt die in [Prompts] definierte interaktive Abfrage und speichert die Antwort in "
        "der Variablen. Wird von Silent-Schaltern (/S…) übersteuert – dann greift der dort "
        "definierte Default.",
        uninstall="Ohne '-'; typischerweise nur im Installationsteil sinnvoll.",
        example="[Prompts]\r\nRebootNow=Sofort neu starten?, JA/NEIN, JA\r\n\r\n[Set:Product]\r\nPrompt RebootNow",
        pitfall="In silenten Paketen (/S0–/S2) erscheint kein Dialog – Antworlogik muss den Default "
        "sauber behandeln (VAL-028).",
    ),
    "RD": CommandDoc(
        name="RD",
        syntax="RD <Verzeichnispfad>  ·  RmDir <Verzeichnispfad>",
        semantics="Entfernt ein VERZEICHNIS, das LEER sein muss (Remove Directory) – im Unterschied zu "
        "'DelTree', das rekursiv löscht.",
        uninstall="Mit '-' im Deinstallationspfad.",
        example='-RD "%App%\\empty_sub"',
        pitfall="Bei nicht-leerem Verzeichnis schlägt der Befehl still fehl – vorher Contents prüfen "
        "bzw. '-DelTree' verwenden.",
    ),
    "RmDir": CommandDoc(
        name="RmDir",
        syntax="RmDir <Verzeichnispfad>",
        semantics="Lange Form von 'RD': entfernt ein leeres Verzeichnis.",
        uninstall="Mit '-' im Deinstallationspfad.",
        example='-RmDir "%App%\\empty_sub"',
        pitfall="Siehe 'RD'.",
    ),
    "RegAsm": CommandDoc(
        name="RegAsm",
        syntax="RegAsm <Assembly> [Optionen]",
        semantics="Registriert eine .NET-Assembly (RegAsm) – für COM-Interop-Pakete, die keine "
        "regasm.exe-Zeile über CallHidden callsen wollen.",
        uninstall="Mit '-' bzw. '/u'-Option im Deinstallationspfad.",
        example='RegAsm "%App%\\bin\\MeineLib.dll" /codebase',
        pitfall="/codebase erzeugt Versionskonflikte bei parallelen Installationen; %ErrorLevel% prüfen.",
    ),
    "Rem": CommandDoc(
        name="Rem",
        syntax="Rem <Kommentar>",
        semantics="Kommentar als eigener Befehl – wird protokolliert und läuft (anders als ';'-Kommentare) "
        "IMMER auch bei der Deinstallation.",
        uninstall="Ohne '-' in beiden Richtungen aktiv (verifizierte Semantik).",
        example='Rem Maschinenteil gestartet um %SysDate% %SysTime%',
        pitfall="Für reine Quelltext-Kommentare ';'-Zeilen bevorzugen (erscheinen nicht im Log).",
    ),
    "Rename": CommandDoc(
        name="Rename",
        syntax="Rename <Quelle> <Ziel>  ·  Ren <Quelle> <Ziel>",
        semantics="Benennt eine Datei um. Wird bei der Deinstallation automatisch rückgängig gemacht "
        "(Interpreter-Undo-Log) – keine '-Ren'-Spiegelzeile nötig.",
        uninstall="Automatische Rücknahme durch den Interpreter.",
        example='Rename "%App%\\config.neu" "%App%\\config.xml"',
        pitfall="Nur gleiche Partition/Ordnerlogik; Ziel darf nicht existieren.",
    ),
    "Ren": CommandDoc(
        name="Ren",
        syntax="Ren <Quelle> <Ziel>",
        semantics="Kurzform von 'Rename': benennt eine Datei um; automatische Rücknahme bei /U.",
        uninstall="Automatische Rücknahme durch den Interpreter.",
        example='Ren "%App%\\config.neu" "%App%\\config.xml"',
        pitfall="Siehe 'Rename'.",
    ),
    "ReplaceRegValue": CommandDoc(
        name="ReplaceRegValue",
        syntax='ReplaceRegValue (<Root>, "<Key>", "<Wert>", "<Suche>", "<Ersetze>", n)',
        semantics="Suchen/Ersetzen innerhalb eines Registry-Wertes; n = n-tes Vorkommen oder alle.",
        uninstall="Ohne automatische Rücknahme – Originalwert ggf. vorher sichern.",
        example='ReplaceRegValue (HKLM, "Software\\Vendor\\App", "Path", "C:\\Old", "%App%", 0)',
        pitfall="Ersetzungen in REG_SZ/EXPAND_SZ-Werten; n=0 ersetzt alle Vorkommen.",
    ),
    "ReplaceTextFile": CommandDoc(
        name="ReplaceTextFile",
        syntax='ReplaceTextFile ("<Datei>", "<Suche>", "<Ersetze>", n)',
        semantics="Suchen/Ersetzen in einer Textdatei; n = n-tes Vorkommen oder alle (0). Auch als "
        "Funktion außerhalb [Requirements] nutzbar.",
        uninstall="Ohne automatische Rücknahme – Original ggf. vorher sichern.",
        example='ReplaceTextFile ("%App%\\app.ini", "SERVER=old", "SERVER=new", 0)',
        pitfall="Kein Regex – exakte String-Suche; Zeichencodierung der Datei beachten (ANSI).",
    ),
    "ReplaceVars": CommandDoc(
        name="ReplaceVars",
        syntax="ReplaceVars <Datei>",
        semantics="Löst %Variablen% in der angegebenen Datei in-place auf (nützlich für Konfig-Templates "
        "aus dem Paket).",
        uninstall="Ohne automatische Rücknahme.",
        example='ReplaceVars "%App%\\config.template"',
        pitfall="Die Ersetzung ist endgültig – Originaltemplate separat mitkopieren, wenn es mehrfach "
        "gebraucht wird.",
    ),
    "ReadXmlNode": CommandDoc(
        name="ReadXmlNode",
        syntax="ReadXmlNode (<Datei>, <XPath>)",
        semantics="Liest einen XML-Knoten in die Zielvariable – reine Leseoperation für Set-Zuweisungen.",
        uninstall="Ohne Rücknahmebedarf.",
        example='Set Version = ReadXmlNode ("%App%\\config.xml", "/Konfiguration/Version/@value")\r\nReplaceEnv Version',
        pitfall="Wie alle dynamischen Lesezugriffe anschließend 'ReplaceEnv <Var>' aufrufen.",
    ),
    "ReadXmlText": CommandDoc(
        name="ReadXmlText",
        syntax="ReadXmlText (<Datei>, <XPath>)",
        semantics="Liest den Textinhalt eines XML-Knotens in die Zielvariable.",
        uninstall="Ohne Rücknahmebedarf.",
        example='Set Host = ReadXmlText ("%App%\\config.xml", "/Konfiguration/Host")\r\nReplaceEnv Host',
        pitfall="Siehe 'ReadXmlNode'.",
    ),
    "UpdateXml": CommandDoc(
        name="UpdateXml",
        syntax="UpdateXml (<Datei>, <XPath>, <Wert>[, …])",
        semantics="Aktualisiert oder erzeugt XML-Knoten/Werte in der Datei.",
        uninstall="Keine automatische Rücknahme – Original ggf. vorher sichern.",
        example='UpdateXml ("%App%\\config.xml", "/Konfiguration/Version/@value", "2.0")',
        pitfall="XPath präzise fassen; Namensräume beachten.",
    ),
    "ShowPicture": CommandDoc(
        name="ShowPicture",
        syntax="ShowPicture <Disk>, <Datei>, <X>, <Y>",
        semantics="Zeigt ein Bild aus dem Paket an fester Position an (z. B. während der Installation).",
        uninstall="Ohne Bedeutung für die Deinstallation.",
        example='ShowPicture 1, "branding.bmp", 100, 100',
        pitfall="Bei silent Verteilung nicht sichtbar; Datei über [Installer] mitkopieren.",
    ),
    "SplashDialogOn": CommandDoc(
        name="SplashDialogOn",
        syntax="SplashDialogOn <X>, <Y>, <Breite>, <Höhe>",
        semantics="Öffnet einen schemalosen Splash-Dialog an fester Position (z. B. für Statusmeldungen "
        "während langer Installationsphasen).",
        uninstall="Ohne '-'; UI-Befehl.",
        example='SplashDialogOn 200, 200, 400, 120',
        pitfall="Immer 'SplashDialogOff' erreichen (auch im Fehlerpfad), sonst bleibt der Dialog stehen.",
    ),
    "SplashDialogText": CommandDoc(
        name="SplashDialogText",
        syntax="SplashDialogText <Text>",
        semantics="Setzt/aktualisiert den Text des geöffneten Splash-Dialogs.",
        uninstall="Ohne '-'; UI-Befehl.",
        example='SplashDialogText Kopiere Dateien …',
        pitfall="Wirkt nur zwischen SplashDialogOn und SplashDialogOff.",
    ),
    "SplashDialogOff": CommandDoc(
        name="SplashDialogOff",
        syntax="SplashDialogOff",
        semantics="Schließt den Splash-Dialog.",
        uninstall="Ohne '-'; UI-Befehl.",
        example="SplashDialogOff",
        pitfall="Auch in Fehlersektionen aufrufen, damit der Dialog nicht stehen bleibt.",
    ),
    "StartService": CommandDoc(
        name="StartService",
        syntax="StartService <Dienstname>",
        semantics="Startet einen (installierten) Windows-Dienst – z. B. nach Konfigurationsänderungen.",
        uninstall="Mit '-' im Deinstallationspfad, wenn der Dienst vor dem Entfernen zu stoppen ist "
        "(hierfür eigentlich 'StopService').",
        example='StartService "MeinDienst"',
        pitfall="Startet nur installierte Dienste; nach 'AddService' bzw. SERVICE-Copyflag verwenden.",
    ),
    "StopService": CommandDoc(
        name="StopService",
        syntax="StopService <Dienstname>",
        semantics="Stoppt einen laufenden Windows-Dienst – z. B. vor Dateiupdates oder 'DeleteService'.",
        uninstall="Mit '-' im Deinstallationspfad vor 'DeleteService'.",
        example='-StopService "MeinDienst"',
        pitfall="Dependente Dienste zuerst stoppen; manche Dienste benötigen Timeout.",
    ),
    "SystemShutdown": CommandDoc(
        name="SystemShutdown",
        syntax="SystemShutdown <Text>, <Reboot>, <Force>, <Timeout>, <Async>",
        semantics="Fährt das System kontrolliert herunter oder startet neu (1=Reboot, 0=Shutdown; "
        "Force beendet Prozesse erzwungen; Timeout=Countdown in Sekunden, -1 ohne sichtbaren "
        "Countdown; Async=1 kehrt sofort zurück). Feldverifikation aus dem Matrix42-Agent-Paket: "
        "'%ShutdownTextDesc%, 1, 0, -1, 1' (User-Kontext) bzw. '…, 1, 0, 15, 1' (kein User, 15 s).",
        uninstall="Ohne '-'; Systembefehl.",
        example='SystemShutdown %ShutdownTextDesc%, 1, 0, -1, 1',
        pitfall="Nachfolgende Setup.inf-Zeilen laufen bei Sync/=0 nicht mehr; Force verwirft ungespeicherte "
        "Daten. Für Reboot nach Paketende bevorzugt 'SetReboot 1' verwenden!",
    ),
    "Unrar": CommandDoc(
        name="Unrar",
        syntax='Unrar ("<Archiv>", "<Ziel>", ["<Maske>"], ["<Passwort>"])',
        semantics="Entpackt ein RAR-Archiv in das Zielverzeichnis (UnRAR.dll/UnRAR64.dll aus dem "
        "User-Ordner des Pakets; Modulpfad-Logik). Maske und Passwort optional.",
        uninstall="Ohne automatische Rücknahme – Ziele ggf. per '-DelTree' bereinigen.",
        example='Unrar ("%Src%\\Files\\data.rar", "%App%\\data")',
        pitfall="Passwörter ab INF-Version 6.5 Setup-verschlüsselt (EmpCrypt); Ziele vorher per MD anlegen.",
    ),
    "Unzip": CommandDoc(
        name="Unzip",
        syntax='Unzip ("<Zip>", "<Ziel>", ["<Maske>"], ["<Passwort>"])',
        semantics="Entpackt ein ZIP-Archiv in das Zielverzeichnis; Maske (z. B. '*.xml') und Passwort "
        "optional.",
        uninstall="Ohne automatische Rücknahme – Ziele ggf. per '-DelTree' bereinigen.",
        example='Unzip ("%Src%\\Files\\config.zip", "%App%\\config", "*.xml")',
        pitfall="Zielverzeichnis vorher per MD anlegen; %ErrorLevel% prüfen.",
    ),
    "WaitUntilFileExists": CommandDoc(
        name="WaitUntilFileExists",
        syntax='WaitUntilFileExists "<Datei>"[, <Timeout>]  ·  -WaitUntilFileExists …',
        semantics="Wartet, bis die Datei existiert (Polling), maximal bis zum optionalen Timeout "
        "(Sekunden) – z. B. auf Ausgabedateien gestarteter Prozesse.",
        uninstall="Mit '-' im Deinstallationspfad.",
        example='WaitUntilFileExists "%Temp%\\setup_done.flag", 120',
        pitfall="Ohne Timeout wartet der Befehl endlos – immer Timeout angeben.",
    ),
    "WaitUntilProcessExists": CommandDoc(
        name="WaitUntilProcessExists",
        syntax="WaitUntilProcessExists <Prozessname>[, <Timeout>]",
        semantics="Wartet, bis der Prozess läuft – z. B. bis ein per 'Run'-Ersatz gestarteter Agent "
        "einsatzbereit ist.",
        uninstall="Mit '-' im Deinstallationspfad.",
        example='WaitUntilProcessExists "agent.exe", 60',
        pitfall="Prüft nur Prozessexistenz, nicht Einsatzbereitschaft (Ports/Dienste) – ggf. zusätzlich "
        "'WaitUntilRegKeyExists' nutzen.",
    ),
    "WaitUntilRegKeyExists": CommandDoc(
        name="WaitUntilRegKeyExists",
        syntax='WaitUntilRegKeyExists "<Root>,<Key>[,<Wert>]"[, <Timeout>]',
        semantics="Wartet, bis der Registry-Schlüssel/Wert existiert. Das Argument MUSS in "
        "Anführungszeichen stehen, da die Komponenten selbst kommagetrennt sind!",
        uninstall="Mit '-' im Deinstallationspfad.",
        example='WaitUntilRegKeyExists "HKLM,SOFTWARE\\Vendor\\App,Ready", 90',
        pitfall="Quotes sind Pflicht (Kommata im Argument); Timeout immer angeben.",
    ),
    "WaitWhileProcessExists": CommandDoc(
        name="WaitWhileProcessExists",
        syntax="WaitWhileProcessExists <Prozessname>[, <Timeout>]",
        semantics="Wartet, bis der Prozess ENDET – typisch vor Deinstallation/Update, z. B. nach "
        "'AskKillProcesses' als Sanft-Pendant.",
        uninstall="Mit '-' im Deinstallationspfad.",
        example='WaitWhileProcessExists "app.exe", 120',
        pitfall="Ohne Timeout endloses Warten; bei Timeout weiterlaufen lassen und Ergebnis prüfen.",
    ),
}


# --------------------------------------------------------------------------
# If-Prädikate (verifizierte Funktionsliste des Interpreters 26.1.0 —
# diese fünf Does*-Prädikate sind die einzigen existierenden)
# --------------------------------------------------------------------------

PREDICATE_DOCS: dict[str, PredicateDoc] = {
    "DoesRegKeyExist": PredicateDoc(
        name="DoesRegKeyExist",
        syntax='DoesRegKeyExist ("<Root>,<SubKey>[,<ValueName>]")',
        semantics="Prüft, ob ein Registry-Schlüssel oder ein optional angegebener Wert existiert; "
        "liefert '1' (ja/vorhanden) oder '0' (nein/nicht vorhanden). Kanonisches Standardprädikat der Referenz. "
        "Die ValueName-Komponente macht es zum Nachfolger der früher dokumentierten Wert-Abfrage.",
        example='If DoesRegKeyExist ("%RegUninstallKey%") == "1" Then "Set:Repair" '
        'Else "Set:Install" EndIf',
        pitfall="Argument in Klammern zwingend in Anführungszeichen setzen (die Komma-Komponenten erfordern "
        "den umschließenden String). Ergebnis immer mit '\"1\"' oder '\"0\"' vergleichen – niemals mit "
        "True/False oder unquoted 1.",
    ),
    "DoesFileExist": PredicateDoc(
        name="DoesFileExist",
        syntax='DoesFileExist ("<Dateipfad>")',
        semantics="Prüft die physische Dateiexistenz auf dem Dateisystem; liefert '1' wenn die Datei existiert, "
        "andernfalls '0'.",
        example='If DoesFileExist ("%App%\\bin\\app.exe") == "1" Then '
        '"Set:AlreadyInstalled" EndIf',
        pitfall="Dateipfad immer quoten. Hervorragend geeignet zur Erfolgskontrolle nach Installation oder "
        "Deinstallation (nicht nur auf %ErrorLevel% verlassen).",
    ),
    "DoesPathExist": PredicateDoc(
        name="DoesPathExist",
        syntax='DoesPathExist ("<Verzeichnispfad>")',
        semantics="Prüft, ob ein Verzeichnis auf dem Dateisystem existiert; liefert '1' oder '0'. "
        "Verifiziertes Gegenstück zur (nicht existierenden) älteren 'DoesDirExist'-Schreibweise.",
        example='If DoesPathExist ("%ProgramFiles%\\Vendor\\App") == "1" Then '
        '"Set:FolderFound" Else "Set:Install" EndIf',
        pitfall="Pfad in Anführungszeichen setzen; keine Wildcards übergeben. Für reine Dateiprüfungen "
        "'DoesFileExist' verwenden.",
    ),
    "DoesProcessExist": PredicateDoc(
        name="DoesProcessExist",
        syntax='DoesProcessExist ("<Prozessname.exe>")',
        semantics="Prüft zur Laufzeit, ob ein bestimmter Prozess im Windows-System aktiv läuft; "
        "liefert '1' wenn der Prozess aktiv ist, andernfalls '0'.",
        example='If DoesProcessExist ("outlook.exe") == "1" Then "Set:AppRunning" EndIf',
        pitfall="Prüft den reinen Prozessnamen. Für interaktive Benutzerdialoge mit Timeout-Countdown ist "
        "'AskKillProcesses' vorzuziehen.",
    ),
    "DoesTextInFileExist": PredicateDoc(
        name="DoesTextInFileExist",
        syntax='DoesTextInFileExist ("<Text>", "<Datei>")',
        semantics="Prüft, ob ein Text in einer Datei enthalten ist; liefert '1' oder '0'. "
        "Verifizierte Funktion der Interpreter-Funktionstabelle 26.1.0.",
        example='If DoesTextInFileExist ("LicenseOK", "%App%\\config.ini") == "1" Then "Set:Licensed" EndIf',
        pitfall="Beide Argumente in Anführungszeichen setzen; für große Dateien ist der Check teuer – "
        "nicht in engen Schleifen einsetzen.",
    ),
}


# --------------------------------------------------------------------------
# Set-Funktionen (Referenz / Referenztemplates)
# --------------------------------------------------------------------------

FUNCTION_DOCS: dict[str, FunctionDoc] = {
    "GetUninstallKeyName": FunctionDoc(
        name="GetUninstallKeyName",
        syntax="GetUninstallKeyName (%DisplayName%[,x64|x86])",
        semantics="Durchsucht dynamisch die Windows-Registry unter "
        "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall (sowie WOW6432Node) nach dem angegebenen "
        "Anzeigenamen und ermittelt die zugehörige Uninstall-GUID oder den Schlüsselnamen – essenziell für "
        "robuste MSI-/EXE-Deinstallationen und Versions-Upgrades.",
        example="Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)\r\n"
        "ReplaceEnv MSIGUID_X64\r\n"
        'If "%MSIGUID_X64%" != "" Then "Set:UninstallOld" EndIf',
        pitfall="Zwingend unmittelbar danach 'ReplaceEnv <Variable>' aufrufen, sonst bleibt die Ergebnisvariable "
        "unaufgelöst! Auf 64-Bit-Systemen empfiehlt es sich, x64 und x86 abzufragen, falls ältere Versionen als "
        "32-Bit installiert waren.",
    ),
    # ------------------------------------------------------------------
    # Verifizierte Funktionen (Legacy-Help + Interpreter 26.1.0)
    # ------------------------------------------------------------------
    "Left": FunctionDoc(
        name="Left",
        syntax='Left ("<String>", n)',
        semantics="Liefert die ersten n Zeichen des Strings.",
        example='Set Kurz = Left ("%ProductName%", 8)\r\nReplaceEnv Kurz',
        pitfall="Wie alle Stringfunktionen nur über Set + ReplaceEnv auswerten.",
    ),
    "Right": FunctionDoc(
        name="Right",
        syntax='Right ("<String>", n)',
        semantics="Liefert die letzten n Zeichen des Strings.",
        example='Set Ext = Right ("%File%", 3)\r\nReplaceEnv Ext',
        pitfall="n größer als die Stringlänge liefert den ganzen String.",
    ),
    "Mid": FunctionDoc(
        name="Mid",
        syntax='Mid ("<String>", n1, n2)',
        semantics="Liefert n2 Zeichen ab Position n1 (1-basiert).",
        example='Set Teil = Mid ("%Version%", 1, 1)\r\nReplaceEnv Teil',
        pitfall="Position 1 ist das erste Zeichen (nicht 0).",
    ),
    "Len": FunctionDoc(
        name="Len",
        syntax='Len ("<String>")',
        semantics="Liefert die Länge des Strings.",
        example='Set N = Len ("%ComputerName%")\r\nReplaceEnv N',
        pitfall="Leerstrings liefern 0; für Bedingungen in If-Zeilen direkt einsetzbar.",
    ),
    "Uppercase": FunctionDoc(
        name="Uppercase",
        syntax='Uppercase ("<String>")',
        semantics="Wandelt den String in Großbuchstaben.",
        example='Set Up = Uppercase ("%ComputerName%")\r\nReplaceEnv Up',
        pitfall="Nur ASCII-Wandlung – Umlaute prüfen.",
    ),
    "Lowercase": FunctionDoc(
        name="Lowercase",
        syntax='Lowercase ("<String>")',
        semantics="Wandelt den String in Kleinbuchstaben.",
        example='Set Low = Lowercase ("%User%")\r\nReplaceEnv Low',
        pitfall="Nur ASCII-Wandlung – Umlaute prüfen.",
    ),
    "RemoveFromLeft": FunctionDoc(
        name="RemoveFromLeft",
        syntax='RemoveFromLeft ("<String>", n)',
        semantics="Entfernt die ersten n Zeichen des Strings.",
        example='Set OhneLaufwerk = RemoveFromLeft ("%Path%", 3)\r\nReplaceEnv OhneLaufwerk',
        pitfall="Für Laufwerkpfade: 'C:\\' sind 3 Zeichen.",
    ),
    "RemoveFromRight": FunctionDoc(
        name="RemoveFromRight",
        syntax='RemoveFromRight ("<String>", n)',
        semantics="Entfernt die letzten n Zeichen des Strings.",
        example='Set Basis = RemoveFromRight ("%File%", 4)\r\nReplaceEnv Basis',
        pitfall="Dateiendungen inkl. Punkt zählen ('.exe' = 4 Zeichen).",
    ),
    "HexToString": FunctionDoc(
        name="HexToString",
        syntax='HexToString ("<Hex>", [<Unicode>])',
        semantics="Wandelt Hex-Daten in einen String um (optional Unicode). Nur außerhalb [Requirements] "
        "verwendbar. Wird von Matrix42-eigenen INFs mit 'CollapseEnv' kombiniert.",
        example='Set X = HexToString ("%Reg%", 1)\r\nCollapseEnv X',
        pitfall="In [Requirements]-Zeilen unzulässig; Ergebnis via ReplaceEnv/CollapseEnv auflösen.",
    ),
    "StringToHex": FunctionDoc(
        name="StringToHex",
        syntax='StringToHex ("<String>", [<Unicode>])',
        semantics="Wandelt einen String in Hex-Darstellung um. Nur außerhalb [Requirements].",
        example='Set Hx = StringToHex ("Wert")\r\nReplaceEnv Hx',
        pitfall="In [Requirements]-Zeilen unzulässig.",
    ),
    "GetIP": FunctionDoc(
        name="GetIP",
        syntax="GetIP ()",
        semantics="Liefert die IP-Adresse des primären Netzwerkadapters.",
        example="Set IP = GetIP ()\r\nReplaceEnv IP",
        pitfall="Bei mehreren Adaptern primären Adapter prüfen; ohne Netzwerk leer.",
    ),
    "GetNIC": FunctionDoc(
        name="GetNIC",
        syntax="GetNIC ([<Index>])",
        semantics="Liefert Informationen zum (n-ten) Netzwerkadapter.",
        example="Set NIC0 = GetNIC (0)\r\nReplaceEnv NIC0",
        pitfall="Index außerhalb der Adapterliste liefert Leerstring.",
    ),
    "GetNICs": FunctionDoc(
        name="GetNICs",
        syntax="GetNICs ()",
        semantics="Liefert die Liste aller Netzwerkadapter. Nur außerhalb [Requirements].",
        example="Set Alle = GetNICs ()\r\nReplaceEnv Alle",
        pitfall="In [Requirements]-Zeilen unzulässig.",
    ),
    "GetDCName": FunctionDoc(
        name="GetDCName",
        syntax="GetDCName ()",
        semantics="Liefert den Namen des Domain Controllers der Anmeldedomäne.",
        example="Set DC = GetDCName ()\r\nReplaceEnv DC",
        pitfall="In Arbeitsgruppen ohne DC leer; Offline-Szenarien abfangen.",
    ),
    "GetDiskFreeSpace": FunctionDoc(
        name="GetDiskFreeSpace",
        syntax='GetDiskFreeSpace ("<Laufwerk>")',
        semantics="Liefert den freien Speicherplatz exakt – Achtung: korrekt nur bis ca. 2,1 GB "
        "(Legacy-32-Bit-Semantik).",
        example='Set Free = GetDiskFreeSpace ("C:")\r\nReplaceEnv Free',
        pitfall="Für moderne Platten 'GetDiskFreeSpaceKB' verwenden!",
    ),
    "GetDiskFreeSpaceKB": FunctionDoc(
        name="GetDiskFreeSpaceKB",
        syntax='GetDiskFreeSpaceKB ("<Laufwerk>")',
        semantics="Liefert den freien Speicherplatz in Kilobytes – die zuverlässige Variante für "
        "moderne Datenträgergrößen.",
        example='If GetDiskFreeSpaceKB ("C:") < "1048576" Then "Set:NoSpace" EndIf',
        pitfall="Vor großen Kopieraktionen (Installer-Sektion) als Vorbedingung prüfen.",
    ),
    "GetDotNetPatchLevel": FunctionDoc(
        name="GetDotNetPatchLevel",
        syntax='GetDotNetPatchLevel ("<Version>")',
        semantics="Liefert das höchste installierte Patch-Level der angegebenen .NET-Version.",
        example='Set PL = GetDotNetPatchLevel ("4.0.0.0")\r\nReplaceEnv PL',
        pitfall="Rückgabe 0, wenn die Basisversion fehlt.",
    ),
    "IsDotNetVersionAvailable": FunctionDoc(
        name="IsDotNetVersionAvailable",
        syntax='IsDotNetVersionAvailable ("<Version>")',
        semantics="Prüft, ob eine .NET-Runtime-Version verfügbar ist (Erkennung v1.0.3705 bis v4.8 "
        "Client/Full); liefert '1'/'0'.",
        example='If IsDotNetVersionAvailable ("4.8") == "0" Then "Set:InstallDotNet" EndIf',
        pitfall="Client- vs. Full-Profile unterscheiden; Version exakt angeben.",
    ),
    "BitAnd": FunctionDoc(
        name="BitAnd",
        syntax="BitAnd (<Bits>, <Maske>)",
        semantics="Bitweises UND – typisch für die Distribution-Flags des Setup-Assistenten: "
        "1=INSTALL, 2=UPDATE, 4=FORCE, 8=UNINSTALL.",
        example='If BitAnd (%Distribution%, 8) == "8" Then "Set:UninstallPath" EndIf',
        pitfall="Distribution-Flags nur im Setup-Kontext gesetzt; Zahlen dezimal/numerisch vergleichen.",
    ),
    "BitOr": FunctionDoc(
        name="BitOr",
        syntax="BitOr (<Bits>, <Maske>)",
        semantics="Bitweises ODER – kombiniert Flags zu einer Maske.",
        example="Set Mode = BitOr (1, 4)\r\nReplaceEnv Mode",
        pitfall="Ergebnis numerisch; für Vergleiche als Zahl behandeln.",
    ),
    "BitXOr": FunctionDoc(
        name="BitXOr",
        syntax="BitXOr (<Bits>, <Maske>)",
        semantics="Bitweises XOR – schaltet Flags um.",
        example="Set Toggle = BitXOr (%Mode%, 2)\r\nReplaceEnv Toggle",
        pitfall="Zweimalige Anwendung hebt die Umschaltung wieder auf.",
    ),
    "FileSize": FunctionDoc(
        name="FileSize",
        syntax='FileSize ("<Datei>")',
        semantics="Liefert die Dateigröße in Bytes ('0' bei fehlender Datei) – auch als If-Funktion "
        "einsetzbar.",
        example='If FileSize ("%App%\\app.exe") > "0" Then "Set:Installed" EndIf',
        pitfall="Fehlende Datei von 0-Byte-Datei semantisch nicht unterscheidbar – Existenz per "
        "DoesFileExist separat prüfen.",
    ),
    "FileVersion": FunctionDoc(
        name="FileVersion",
        syntax='FileVersion ("<Datei>"[, <Feld>])',
        semantics="Liefert die Dateiversion (ggf. einzelnes Feld: 1..4) einer PE-Datei – Standardwerkzeug "
        "für Installationsprüfungen.",
        example='If FileVersion ("%App%\\bin\\app.exe") < "2.0" Then "Set:Upgrade" EndIf',
        pitfall="Versionsvergleich: ab [Setup] Version=14.2 numerisch je Punkt-Segment, davor "
        "ziffernweise lexikalisch!",
    ),
    "ReadTextFile": FunctionDoc(
        name="ReadTextFile",
        syntax='ReadTextFile ("<Datei>")',
        semantics="Liest den kompletten Inhalt einer Textdatei als String ein (Leerstring, wenn die "
        "Datei fehlt; benötigt MSXML 6.0 auf dem Zielsystem).",
        example='Set Inhalt = ReadTextFile ("%App%\\version.txt")\r\nReplaceEnv Inhalt',
        pitfall="Bei fehlender Datei KEIN Fehler, sondern Leerstring – Existenz separat prüfen; große "
        "Dateien sprengen Variablengrenzen.",
    ),
    "GetClipboardText": FunctionDoc(
        name="GetClipboardText",
        syntax="GetClipboardText ()",
        semantics="Liest den aktuellen Textinhalt der Windows-Zwischenablage.",
        example="Set Clip = GetClipboardText ()\r\nReplaceEnv Clip",
        pitfall="Nicht-Textinhalte liefern Leerstring; im SYSTEM-Kontext meist ohne Nutzen.",
    ),
    "Tokenize": FunctionDoc(
        name="Tokenize",
        syntax="Tokenize (<Variable>[, <Separator>])",
        semantics="Zerlegt den Wert einer Variablen anhand des Separators (Standard Komma) in indizierte "
        "Teilvariablen (%Var_1%, %Var_2%, …) und liefert die Anzahl – auch als If-Funktion nutzbar.",
        example="Set N = Tokenize (Liste, \";\")\r\nReplaceEnv N",
        pitfall="Teilvariablen sind erst NACH ReplaceEnv verfügbar; Separator in Quotes übergeben.",
    ),
}


# --------------------------------------------------------------------------
# Aufruf-Flags / Steuerung (Kap. 5)
# --------------------------------------------------------------------------

FLAG_DOCS: dict[str, FlagDoc] = {
    "#Section": FlagDoc(
        name="#Sektionsaufruf",
        syntax="#Set:Name[, FLAGS]  ·  #Shell:Name  ·  #Reg:Name[, FLAGS]",
        semantics="Ruft eine benannte Sektion aus [Product] (oder anderen Steuerungssektionen) als Unterprogramm "
        "auf (GOSUB-Prinzip). Nach Abarbeitung der Sektion setzt Empirum die Ausführung mit der nächsten Zeile fort.",
        example="#Set:Product, DONTDELETE\r\n#Reg:Product, DONTDELETE",
        pitfall="'If ... Then' springt direkt zu Sektionsnamen ohne '#'. Das '#' gehört ausschließlich in die "
        "Aufrufliste in [Product], nicht hinter 'Then'!",
    ),
    "#!": FlagDoc(
        name="#! Mehrfachaufruf",
        syntax="#!Set:Name",
        semantics="Erlaubt den erneuten Aufruf einer bereits zuvor ausgeführten Sektion. Standardmäßig führt "
        "Empirum jede Sektion pro Lauf nur genau einmal aus; das Ausrufezeichen hebelt diesen Schutz gezielt aus.",
        example="#!Set:LogStatus",
        pitfall="Sparsamer Einsatz empfohlen; nur verwenden, wenn dieselbe Sektion bewusst mehrfach ausgeführt werden soll.",
    ),
    "DONTDELETE": FlagDoc(
        name="DONTDELETE",
        syntax="#Set:Product, DONTDELETE  ·  #Reg:Product, DONTDELETE",
        semantics="Gibt an, dass die aufgerufene Sektion NUR bei der Installation ausgeführt wird. Bei der "
        "Deinstallation (/U) wird die Zeile komplett übersprungen.",
        example="#Set:Product, DONTDELETE",
        pitfall="Ohne DONTDELETE wird eine #Set:-Sektion bei /U rückwärts durchlaufen, wobei Zeilen mit führendem '-' "
        "ausgeführt werden. DONTDELETE schützt Installationssektionen vor versehentlicher Rückwärtsausführung.",
    ),
    "DELETE": FlagDoc(
        name="DELETE",
        syntax="#Set:Deinstallation, DELETE  ·  #Reg:OnUninstallProduct, DELETE",
        semantics="Gibt an, dass die Sektion NUR bei der Deinstallation (/U) ausgeführt wird. Der reguläre "
        "Installationslauf überspringt diese Sektion vollständig.",
        example="#Set:Deinstallation, DELETE\r\n#Reg:OnUninstallProduct, DELETE",
        pitfall="Typisch für dedizierte Deinstallations-Sektionen und Registry-Werte, die beim Entfernen wiederhergestellt "
        "werden sollen (Reg:OnUninstall...).",
    ),
    "MACHINE": FlagDoc(
        name="MACHINE",
        syntax="#Set:Product, MACHINE  ·  #FileCheckMachine, MACHINE",
        semantics="Grenzt die Sektionsausführung strikt auf den Maschinenteil ein (Ausführung einmalig als "
        "SYSTEM-Konto).",
        example="#Set:MachineConfig, MACHINE",
        pitfall="Wird im Benutzerteil (/AW) ignoriert. Für maschinenweite Treiber-, Dienst- und HKLM-Konfigurationen gedacht.",
    ),
    "CLIENT": FlagDoc(
        name="CLIENT",
        syntax="#Set:UserConfig, CLIENT  ·  #Shell:UserLinks, CLIENT",
        semantics="Grenzt die Ausführung strikt auf den Benutzerteil ein. Läuft für jeden angemeldeten Anwender "
        "im Benutzerkontext (erfordert zwingend /AW in [SetupInfo] und im Depot-Befehl).",
        example="#Set:UserConfig, CLIENT",
        pitfall="Funktioniert nur, wenn das Paket mit /AW verteilt wird. Im Maschinenteil wird die Zeile übersprungen.",
    ),
    "-prefix": FlagDoc(
        name="'-'-Uninstall-Präfix",
        syntax="-CallHidden …  ·  -DelTree …  ·  -SetReboot 1",
        semantics="Befehlszeilen mit führendem '-' werden bei der Deinstallation ausgeführt, wenn [Product] "
        "von unten nach oben rückwärts abgearbeitet wird. If-Verzweigungen und #-Aufrufe erhalten kein '-'.",
        example="-CallHidden MsiExec /X %MSIGUID% /qn\r\n-DelTree \"%App%\"",
        pitfall="In [Reg:...] bedeutet '-HKLM,...' das Löschen des Eintrags bei der Deinstallation – NICHT bei der "
        "Installation! Wer während der Installation Registry löschen muss, nutzt 'CallHidden reg.exe delete ...'.",
    ),
    "ADMIN": FlagDoc(
        name="ADMIN",
        syntax="#Set:AdminStep, ADMIN",
        semantics="Sektion wird nur ausgeführt, wenn der aktuell angemeldete Benutzer über lokale Administratorrechte verfügt.",
        example="#Set:AdminStep, ADMIN",
        pitfall="Im reinen Benutzerteil (/AW) von Standardbenutzern wird die Sektion stillschweigend übersprungen.",
    ),
    "WINDOWS64": FlagDoc(
        name="WINDOWS64",
        syntax="1:%Temp%\\Setup64.exe, %CommonSetupDir%\\Setup.exe, OPTIONAL ALWAYS WINDOWS64, 0",
        semantics="Beschränkt Datei-Kopierbefehle oder Aufrufe auf 64-Bit-Windows-Betriebssysteme.",
        example="1:%Temp%\\Setup64.exe, %CommonSetupDir%\\Setup.exe, OPTIONAL ALWAYS WINDOWS64, 0",
        pitfall="Auf 32-Bit-Systemen wird die Operation übersprungen.",
    ),
    "WINDOWS32": FlagDoc(
        name="WINDOWS32",
        syntax="#Set:Win32Config, WINDOWS32",
        semantics="Beschränkt die Ausführung auf 32-Bit-Windows-Betriebssysteme.",
        example="#Set:Win32Config, WINDOWS32",
        pitfall="Auf modernen 64-Bit-Plattformen inaktiv.",
    ),
    # ------------------------------------------------------------------
    # Copy-Flags (Legacy-Help Section 24 Flags-Tabelle, CF-001..024)
    # ------------------------------------------------------------------
    "CF:APPEND": FlagDoc(
        name="APPEND", syntax="1:%SetupInfDir%\\Setup.inf, , APPEND, 0",
        semantics="Datei wird an bereits kopierte Datei angehängt (Disketten-Überlauf-Logik).",
        example="1:Files\\add.cfg, %App%\\config.cfg, APPEND, 0",
        pitfall="Zieldatei muss bereits existieren.",
    ),
    "CF:EXPAND": FlagDoc(
        name="EXPAND (Copy-Flag)", syntax="1:Files\\datei.ex_, %App%\\datei.exe, EXPAND, 0",
        semantics="Einzelne Datei expandieren (LZEXPAND), auch wenn [Application] Expand=0 steht.",
        example="1:Files\\lib.dl_, %App%\\lib.dll, EXPAND, 0",
        pitfall="Globaler Schalter ist [Application] Expand= (Default 0).",
    ),
    "CF:NODATEWARNING": FlagDoc(
        name="NODATEWARNING", syntax="…, NODATEWARNING, 0",
        semantics="Keine Warnung, wenn Zieldatei neuer ist als die Quelle.",
        example="1:Files\\app.exe, %App%\\app.exe, NODATEWARNING, 0",
        pitfall="—",
    ),
    "CF:REPLACEOLDER": FlagDoc(
        name="REPLACEOLDER", syntax="…, REPLACEOLDER, 0",
        semantics="Ältere Zieldatei wird ersetzt (Standardverhalten explizit machen).",
        example="1:Files\\app.exe, %App%\\app.exe, REPLACEOLDER, 0",
        pitfall="—",
    ),
    "CF:DONTREPLACE": FlagDoc(
        name="DONTREPLACE", syntax="…, DONTREPLACE, 0",
        semantics="Existierende Zieldatei wird nicht überschrieben.",
        example="1:Files\\config.ini, %App%\\config.ini, DONTREPLACE, 0",
        pitfall="Für Konfigdateien, die der Anwender ändern darf.",
    ),
    "CF:REPLACEVARS": FlagDoc(
        name="REPLACEVARS", syntax="…, REPLACEVARS, 0",
        semantics="%Variablen% werden beim Kopieren in der Datei aufgelöst (in-place).",
        example="1:Files\\app.ini, %App%\\app.ini, REPLACEVARS, 0",
        pitfall="Ersetzung ist endgültig; Original im Paket bleibt unangetastet.",
    ),
    "CF:CREATE": FlagDoc(
        name="CREATE", syntax="…, CREATE, 0",
        semantics="Zielverzeichnis wird bei Bedarf angelegt.",
        example="1:Files\\log\\start.log, %App%\\logs\\start.log, CREATE, 0",
        pitfall="—",
    ),
    "CF:CASCADED": FlagDoc(
        name="CASCADED", syntax="…, CASCADED, 0",
        semantics="Zielverzeichnis wird bei der Deinstallation KOMPLETT gelöscht (inkl. später "
        "hinzugekommener Dateien).",
        example="1:Files\\data\\*, %App%\\data\\*, CASCADED, 0",
        pitfall="Radikal: CASCADED löscht bei /U den ganzen Ordner, auch fremde Dateien!",
    ),
    "CF:LOCALAPP": FlagDoc(
        name="LOCALAPP", syntax="…, LOCALAPP, 0",
        semantics="Datei wird nur bei lokaler Installation kopiert/verarbeitet (nicht bei "
        "Workstation-/Server-Installation vom Netz).",
        example="1:Files\\local.dat, %App%\\local.dat, LOCALAPP, 0",
        pitfall="—",
    ),
    "CF:RDONLY": FlagDoc(
        name="RDONLY", syntax="…, RDONLY, 0",
        semantics="Zieldatei erhält das Schreibschutz-Attribut.",
        example="1:Files\\vorlage.dotx, %App%\\vorlage.dotx, RDONLY, 0",
        pitfall="Schreibschutz verhindert spätere Updates durch MSI/Installateur.",
    ),
    "CF:HIDDEN": FlagDoc(
        name="HIDDEN", syntax="…, HIDDEN, 0",
        semantics="Zieldatei erhält das Versteckt-Attribut.",
        example="1:Files\\core.dat, %App%\\core.dat, HIDDEN, 0",
        pitfall="—",
    ),
    "CF:SYSTEM": FlagDoc(
        name="SYSTEM", syntax="…, SYSTEM, 0",
        semantics="Zieldatei erhält das System-Attribut.",
        example="1:Files\\drv.sys, %System%\\drivers\\drv.sys, SYSTEM, 0",
        pitfall="—",
    ),
    "CF:BACKUP": FlagDoc(
        name="BACKUP", syntax="…, BACKUP, 0",
        semantics="Vor dem Überschreiben wird eine .BAK-Sicherung angelegt.",
        example="1:Files\\app.exe, %App%\\app.exe, BACKUP, 0",
        pitfall="—",
    ),
    "CF:SHARED": FlagDoc(
        name="SHARED", syntax="…, SHARED, 0",
        semantics="Datei gilt als gemeinsam genutzt (Zähler/Deinstall-Logik).",
        example="1:Files\\share.dll, %CommonFilesDir%\\Vendor\\share.dll, SHARED, 0",
        pitfall="—",
    ),
    "CF:SHAREDDLL": FlagDoc(
        name="SHAREDDLL", syntax="…, SHAREDDLL, 0",
        semantics="DLL-Verwendungs-Zähler in der Registry; empfohlen in Kombination mit SERVICE; "
        "wird bei REGISTER automatisch gesetzt.",
        example="1:Files\\ctrl.ocx, %CommonFilesDir%\\Vendor\\ctrl.ocx, SHAREDDLL REGISTER, 0",
        pitfall="Ohne Zähler bleiben Shared-DLLs bei Deinstallation anderer Pakete bestehen.",
    ),
    "CF:REGASM": FlagDoc(
        name="REGASM", syntax="…, REGASM, 0",
        semantics=".NET-Assembly wird nach dem Kopieren registriert (RegAsm).",
        example="1:Files\\MeineLib.dll, %App%\\MeineLib.dll, REGASM, 0",
        pitfall="/codebase-Konflikte bei parallelen Versionen beachten.",
    ),
    "CF:SERVICE": FlagDoc(
        name="SERVICE", syntax="…, SERVICE, 0",
        semantics="EXE wird als Dienst installiert (Definition aus [Services]); SERVICE_AUTO_START "
        "startet den Dienst sofort.",
        example="1:Files\\svc.exe, %App%\\svc.exe, SERVICE, 0",
        pitfall="Dienstpasswort ab INF 6.5 verschlüsselt; Deinstall stoppt/entfernt den Dienst.",
    ),
    "CF:REGISTER": FlagDoc(
        name="REGISTER", syntax="…, REGISTER, 0",
        semantics="OLE/OCX-Selbstregistrierung (DllRegisterServer) nach dem Kopieren; braucht "
        "SHAREDDLL (wird automatisch ergänzt).",
        example="1:Files\\ctl.ocx, %App%\\ctl.ocx, REGISTER, 0",
        pitfall="Nur für echte COM-Komponenten; bei Fehlern bricht die Installation ab.",
    ),
    "CF:SETUPHOOK": FlagDoc(
        name="SETUPHOOK", syntax="…, SETUPHOOK, 0",
        semantics="Datei wird über den Setup-Hook (HOOK_AFTERCOPYFILE) nachbearbeitet – Hook-DLL "
        "via [Application] SetupExtDll/SetupHookFunc.",
        example="1:Files\\data.bin, %App%\\data.bin, SETUPHOOK, 0",
        pitfall="Hook-DLL muss vorhanden sein, sonst Fehler.",
    ),
    "CF:CHECKRTVERSION": FlagDoc(
        name="CHECKRTVERSION", syntax="…, CHECKRTVERSION, 0",
        semantics="Prüft die Runtime-Version vor der Verarbeitung der Datei.",
        example="1:Files\\rt.exe, %App%\\rt.exe, CHECKRTVERSION, 0",
        pitfall="—",
    ),
    "CF:SETUSERINFO": FlagDoc(
        name="SETUSERINFO", syntax="…, SETUSERINFO, 0",
        semantics="Übernimmt Benutzer-/Firmeninfo ([Application] DefaultUser/DefaultCompany) in die "
        "Datei.",
        example="1:Files\\license.ini, %App%\\license.ini, SETUSERINFO, 0",
        pitfall="—",
    ),
    "CF:KEEPEXISTING": FlagDoc(
        name="KEEPEXISTING", syntax="…, KEEPEXISTING, 0",
        semantics="Existierende Datei bleibt unverändert bestehen (kein Überschreiben, kein "
        "Datumswarnungs-Prompt).",
        example="1:Files\\user.cfg, %App%\\user.cfg, KEEPEXISTING, 0",
        pitfall="—",
    ),
    # ------------------------------------------------------------------
    # Setup.exe-Aufrufschalter (Legacy-Help SETUP_Aufruf.htm, SW-001..019)
    # ------------------------------------------------------------------
    "SW:/A": FlagDoc(
        name="/A", syntax="Setup.exe /A",
        semantics="Administrator-Installation mit Auswahl-Dialog; Varianten /AS (Server) und /AW "
        "(Workstation) ohne Auswahl.",
        example="Setup.exe /AS",
        pitfall="/A-Installationen legen Quelle-/Ziellogik für spätere Client-Setups fest.",
    ),
    "SW:/B": FlagDoc(
        name="/B<Datei>", syntax="Setup.exe /BC:\\Temp\\setup.dbg",
        semantics="Debug-Log-Datei schreiben (Inhalt wie DebugView-Ausgabe).",
        example="Setup.exe /B\"%Temp%\\setup.dbg\" /S2",
        pitfall="Nur zur Fehlersuche ausrollen – Log kann groß werden.",
    ),
    "SW:/C": FlagDoc(
        name="/C", syntax="Setup.exe /C",
        semantics="Client-Installation erzwingen (nur bei Administrator-Installation wirksam).",
        example="Setup.exe /C",
        pitfall="—",
    ),
    "SW:/D": FlagDoc(
        name="/D", syntax="Setup.exe /D",
        semantics="Ausführung von CD erzwingen (nicht bei Administrator-Installation).",
        example="Setup.exe /D",
        pitfall="—",
    ),
    "SW:/E": FlagDoc(
        name="/E[+]<Datei>", syntax="Setup.exe /EC:\\Temp\\err.log  ·  /E+… (anhängen)",
        semantics="Fehler-Log-Datei schreiben; mit '+' an vorhandene Datei anhängen.",
        example="Setup.exe /E+\"%Temp%\\setuperr.log\" /S2",
        pitfall="Pfad mit Leerzeichen quoten.",
    ),
    "SW:/F": FlagDoc(
        name="/F", syntax="Setup.exe /F",
        semantics="Bei fehlender Datei nicht nach der Quelle fragen, sondern abbrechen.",
        example="Setup.exe /F /S2",
        pitfall="Ideal für vollautomatische Verteilung ohne Interaktion.",
    ),
    "SW:/L": FlagDoc(
        name="/L", syntax="Setup.exe /L",
        semantics="Lokale Installation erzwingen (nur bei Administrator-Installation).",
        example="Setup.exe /L",
        pitfall="—",
    ),
    "SW:/M": FlagDoc(
        name="/M", syntax="Setup.exe /M",
        semantics="Weitere Optionen HINZUFÜGEN, ohne Deinstall-/Neuinstall-Abfrage (= Hinzufügen-Modus).",
        example="Setup.exe /M /S2",
        pitfall="Kombiniert mit /O<Option> für gezielte Optionsnachinstallation.",
    ),
    "SW:/N": FlagDoc(
        name="/N", syntax="Setup.exe /N",
        semantics="Neuinstallation erzwingen (= Neu statt Hinzufügen/Deinstallieren).",
        example="Setup.exe /N /S2",
        pitfall="—",
    ),
    "SW:/O": FlagDoc(
        name="/O+/-<Option>", syntax="Setup.exe /O+API /O-Docs /S2",
        semantics="Optionen per Kommandozeile aktivieren (+Name) bzw. deaktivieren (-Name); der "
        "Optionsdialog unterbleibt dadurch.",
        example="Setup.exe /O+Product /O+API /S2",
        pitfall="Optionsnamen exakt wie in [Options]; Hierarchien via '\\' im Optionsnamen.",
    ),
    "SW:/P": FlagDoc(
        name="/P<Verzeichnis>", syntax="Setup.exe /PC:\\Quelle",
        semantics="Standard-Quellverzeichnis für Kopiervorgänge setzen.",
        example="Setup.exe /P\"\\\\Server\\Share\\Paket\"",
        pitfall="—",
    ),
    "SW:/R": FlagDoc(
        name="/R", syntax="Setup.exe /R",
        semantics="Reinstall-Modus: letzte Installation wiederholen (benötigt MachineKeyName etc.); "
        "mit /X4 originäres Quellverzeichnis verwenden.",
        example="Setup.exe /R /S2",
        pitfall="—",
    ),
    "SW:/S": FlagDoc(
        name="/S<Level>", syntax="Setup.exe /S0 … /S4",
        semantics="Silent-Level: 0=nichts sichtbar; 1=Kopierdialog; 2=+Hintergrund, Prompts sichtbar; "
        "3=keine Versionskonflikt-Warnungen (Standardantworten); 4=minimale Störung aber "
        "Prompts+Prozess-Beenden-Dialoge. Prompts bei 2/3, nicht bei 0/1. Deinstall: bis "
        "Level 2 ohne Sicherheitsabfrage.",
        example="Setup.exe /S2 /AW",
        pitfall="Level 0/1 unterdrücken [Prompts]-Abfragen – Defaults müssen sauber sein (VAL-028).",
    ),
    "SW:/T": FlagDoc(
        name="/T0|/T1", syntax="Setup.exe /T0",
        semantics="Testmodus: erzeugt %ProductNameShort%.txt (Dateiliste, Level 0) bzw. .bat "
        "(Kopieranweisungen, Level 1) im Temp-Verzeichnis – Installation wird NICHT ausgeführt.",
        example="Setup.exe /T1",
        pitfall="Ideal, um Kopierlogik vorab zu prüfen.",
    ),
    "SW:/U": FlagDoc(
        name="/U", syntax="Setup.exe /U",
        semantics="Deinstallation: [Product] wird von unten nach oben abgearbeitet, '-'-Zeilen und "
        "DELETE-Sektionen laufen, DONTDELETE wird übersprungen.",
        example="Setup.exe /U /S2",
        pitfall="Deinstallations-Fehlersektionen brauchen '--'- bzw. '-'-Stil je Engine-Version (VAL-004).",
    ),
    "SW:/X": FlagDoc(
        name="/X<Flag>", syntax="Setup.exe /X2 /X8",
        semantics="Erweiterungs-Flags (kombinierbar): 2=HKCU/DONTREPLACE-Dateien beim Update-Deinstall "
        "behalten, 4=originäres Quellverzeichnis bei Reinstall, 8=kein Reboot sondern Reboot-Code "
        "als Exit, 20=±1h Sommerzeit-Toleranz beim Datumsvergleich.",
        example="Setup.exe /X8 /S2",
        pitfall="/X8 verlangt Auswertung des Exit-Codes durch den Aufrufer (SwDepot/Agent).",
    ),
    "SW:/AS": FlagDoc(
        name="/AS /AW", syntax="Setup.exe /AS  ·  Setup.exe /AW",
        semantics="Admin-Installation als Server- (/AS) bzw. Workstation- (/AW ohne Auswahl) Variante. "
        "Hinweis: /AW steuert in [SetupInfo] zugleich den Benutzerteil (User Part).",
        example="Setup.exe /AW /S2",
        pitfall="Doppelbedeutung von /AW (Admin-Workstation vs. Benutzerteil) im Kontext prüfen.",
    ),
    # ------------------------------------------------------------------
    # Registry-Zusatzflags (Legacy-Help A.2.6)
    # ------------------------------------------------------------------
    "RG:+0x2": FlagDoc(
        name="+0x2 (Registry)", syntax='HKLM,"Key","Wert",0x00000002,"1"',
        semantics="Nur schreiben, wenn der Wert noch nicht vorhanden ist; bei der Deinstallation nur "
        "löschen, wenn der Wert exakt gleich ist (Wertgleichheit).",
        example='HKLM,"Software\\Vendor","FirstRun",0x00000002,"1"',
        pitfall="Additiv zum Basistyp: REG_SZ 0x00000000 + 0x2 = 0x00000002; "
        "REG_DWORD 0x00010001 + 0x2 = 0x00010003.",
    ),
    "RG:+0x8": FlagDoc(
        name="+0x8 (Registry)", syntax='HKLM,"Key","Wert",0x00000008,"Daten"',
        semantics="Daten werden an den vorhandenen Wert ANGEHÄNGT statt ersetzt.",
        example='HKLM,"Software\\Vendor","Log",0x00000008,"Zeile2\\0"',
        pitfall="Bei MULTI_SZ/BINARY sinnvoll; Anhäufen über mehrere Updates bedenken.",
    ),
    "RG:+0x10": FlagDoc(
        name="+0x10 (Registry)", syntax='HKLM,"Key",0x00000010',
        semantics="Legt einen leeren Registry-Schlüssel an (ohne Wert).",
        example='HKLM,"Software\\Vendor\\Empty",0x00000010',
        pitfall="—",
    ),
    # ------------------------------------------------------------------
    # If-Operatoren & Logik (OP-001..007)
    # ------------------------------------------------------------------
    "OP:&": FlagDoc(
        name="& / | (If-Logik)", syntax='If A == "1" & B == "2" | C == "3" Then "S" EndIf',
        semantics="'&' verknüpft UND, '|' ODER. Es gibt KEINE Präzedenz von & über | – Auswertung "
        "von links; Klammern sind erlaubt und empfohlen.",
        example='If (A == "1" & B == "2") | C == "3" Then "Set:X" EndIf',
        pitfall="Ohne Klammern gemischte &/|-Ausdrücke mehrdeutig – immer klammern!",
    ),
    "OP:INGLOBALGROUP": FlagDoc(
        name="INGLOBALGROUP", syntax='If "%User%" INGLOBALGROUP "Domänen-Admins" Then "S" EndIf',
        semantics="Prüft, ob der Benutzer Mitglied der globalen Domänengruppe ist (If-Operator, "
        "kein Prädikat mit Klammern).",
        example='If "%UserDomain%\\%User%" INGLOBALGROUP "Software-Admins" Then "Set:Admin" EndIf',
        pitfall="Benutzer und Gruppe in Quotes; verschachtelte Gruppen je nach Domänenmodus "
        "unvollständig.",
    ),
    "OP:INLOCALGROUP": FlagDoc(
        name="INLOCALGROUP", syntax='If "%User%" INLOCALGROUP "Administratoren" Then "S" EndIf',
        semantics="Prüft die Mitgliedschaft in einer lokalen Gruppe – Nachfolger der entfernten "
        "CheckLanAdministrator-Idee.",
        example='If "%User%" INLOCALGROUP "Administratoren" Then "Set:Admin" EndIf',
        pitfall="Gruppennamen sind lokalisiert (deutsch 'Administratoren', englisch 'Administrators') "
        "– SID-basierte Alternativen bevorzugen.",
    ),
    "OP:!=": FlagDoc(
        name="!= / <>", syntax='If %ErrorLevel% != "0" Then "S" EndIf',
        semantics="Ungleich-Vergleich; '<>' ist Alias von '!='. Vergleichsoperatoren <, <=, >, >= "
        "vergleichen numerisch/lexikalisch; Zahlen dürfen unquoted stehen.",
        example='If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf',
        pitfall="Versionsvergleiche: ab [Setup] Version=14.2 numerisch je Punkt-Segment, davor "
        "ziffernweise lexikalisch ('4.10' > '4.8' nur ab 14.2!).",
    ),
}


# --------------------------------------------------------------------------
# Variablen-Referenz (Kap. 4 – 29 Kernvariablen + Spezialmuster)
# --------------------------------------------------------------------------

VARIABLE_DOCS: dict[str, VariableDoc] = {
    "%App%": VariableDoc(
        name="%App%",
        category="Verzeichnis",
        meaning="Installations-Zielverzeichnis der Anwendung auf dem Zielclient. Vollständiges Synonym für "
        "%ApplicationDir%, gesteuert über [Application] ApplicationDir=.",
        example_value=r"C:\Program Files\Vendor\App",
        usage='CallHidden "%App%\\bin\\app.exe" /S\r\n-DelTree "%App%"',
        pitfall="Niemals durch feste Pfade wie C:\\Program Files ersetzen. Bei Deinstallation standardmäßig "
        "mit '-DelTree \"%App%\"' restlos bereinigen.",
    ),
    "%AppData%": VariableDoc(
        name="%AppData%",
        category="Benutzerverzeichnis (Roaming)",
        meaning="Roaming-Anwendungsdatenverzeichnis des aktuell angemeldeten Benutzers (%APPDATA%).",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming",
        usage='Copy "%Src%\\Files\\config.xml", "%AppData%\\Vendor\\config.xml"',
        pitfall="Nur im Benutzerteil (/AW, CLIENT-Flag) verlässlich verfügbar! Im Maschinenteil verweist "
        "die Variable auf das SYSTEM-Profil (C:\\Windows\\System32\\config\\systemprofile\\...).",
    ),
    "%ApplicationDir%": VariableDoc(
        name="%ApplicationDir%",
        category="Verzeichnis",
        meaning="Definiertes Anwendungsverzeichnis aus [Application] ApplicationDir=. Basisdefinition für die Kurzform %App%.",
        example_value=r"C:\Program Files\%ProductName%",
        usage="[Application]\r\nApplicationDir=%ProgramFilesDir%\\%ProductName%",
        pitfall="Wird in [Application] deklariert; im Ausführungsskript ist die kurze Form %App% der empfohlene Standard.",
    ),
    "%CommonAppData%": VariableDoc(
        name="%CommonAppData%",
        category="Systemverzeichnis (All Users)",
        meaning="Gemeinsames Anwendungsdaten-Verzeichnis für alle Benutzer des Systems (%ProgramData%).",
        example_value=r"C:\ProgramData",
        usage='MD "%CommonAppData%\\%DeveloperName%\\%ProductName%"\r\n'
        'Copy "%Src%\\Files\\license.lic", "%CommonAppData%\\%DeveloperName%\\%ProductName%\\license.lic"',
        pitfall="Standardbenutzer haben unter C:\\ProgramData standardmäßig eingeschränkte Schreibrechte. "
        "Falls Anwender Konfigurationen modifizieren müssen, Schreibrechte in [Security:Product] vergeben.",
    ),
    "%CommonDesktop%": VariableDoc(
        name="%CommonDesktop%",
        category="Verknüpfung / Desktop",
        meaning="Öffentlicher Desktop-Ordner aller Benutzer ('Public Desktop'). Hier abgelegte Verknüpfungen sind "
        "für jeden angemeldeten Benutzer auf dem Desktop sichtbar.",
        example_value=r"C:\Users\Public\Desktop",
        usage='[Shell:Product]\r\n"%CommonDesktop%\\%ProductName%", "%App%\\app.exe"',
        pitfall="Wird bei 'CommonShellLinks=1' automatisch als Desktop-Ziel verwendet. Bei Deinstallation mit "
        "'-Del \"%CommonDesktop%\\%ProductName%.lnk\"' oder automatischer ShellLinks-Bereinigung entfernen.",
    ),
    "%CommonFilesDir%": VariableDoc(
        name="%CommonFilesDir%",
        category="Systemverzeichnis",
        meaning="Verzeichnis für gemeinsam genutzte Programmdateien ('Common Files').",
        example_value=r"C:\Program Files\Common Files",
        usage="CommonSetupDir=%CommonFilesDir%\\Setup%SetupBits%",
        pitfall="Architekturabhängig; zeigt auf 64-Bit-Systemen für 64-Bit-Prozesse auf C:\\Program Files\\Common Files, "
        "für 32-Bit-Prozesse auf C:\\Program Files (x86)\\Common Files.",
    ),
    "%CommonPrograms%": VariableDoc(
        name="%CommonPrograms%",
        category="Verknüpfung / Startmenü",
        meaning="Gemeinsamer Startmenü-Ordner 'Programme' für alle Benutzer ('All Users Start Menu').",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        usage='[Shell:Product]\r\n"%CommonPrograms%\\%DeveloperName%\\%ProductName%", "%App%\\app.exe"',
        pitfall="In modernen Windows-Versionen (10/11) werden Ordnerstrukturen oft flach dargestellt. Bei "
        "Deinstallation mit '-DelTree \"%CommonPrograms%\\%DeveloperName%\"' bereinigen.",
    ),
    "%Company%": VariableDoc(
        name="%Company%",
        category="Metadaten / Organisation",
        meaning="Firmen- bzw. Organisationsname aus den globalen Einstellungen der Empirum Management Console (EMC).",
        example_value="Musterfirma GmbH",
        usage='Text8="%Company%", Arial, 18, , 2170F3, 4, 10, RIGHT BOLD ITALIC',
        pitfall="Kann Leer- und Sonderzeichen enthalten; bei der Verwendung in Datei- oder Registry-Pfaden stets quoten.",
    ),
    "%ComputerName%": VariableDoc(
        name="%ComputerName%",
        category="System",
        meaning="NetBIOS-Name des Zielcomputers im Netzwerk.",
        example_value="CLIENT042",
        usage="VM_LicenseKey=%%%V_MachineValuesPath%\\%ComputerName%.ini,%ComputerName%,LicenseKey%%",
        pitfall="Dient zur Adressierung von MachineValues-INI-Dateien. Groß-/Kleinschreibung bei Netzlaufwerken "
        "und UNC-Shares beachten.",
    ),
    "%DeveloperName%": VariableDoc(
        name="%DeveloperName%",
        category="Paket-Metadaten",
        meaning="Hersteller- bzw. Entwicklername des Softwarepakets aus [Application] DeveloperName=.",
        example_value="Adobe",
        usage="UserKeyName=$Matrix42Packages$\\%DeveloperName%\\%ProductName%",
        pitfall="Muss konsistent zu DeveloperNameShort gepflegt werden; Namensänderungen führen zu verwaisten "
        "Registry- und Deinstallationsschlüsseln.",
    ),
    "%DomainName%": VariableDoc(
        name="%DomainName%",
        category="Netzwerk / Domäne",
        meaning="Windows-Domänenname des Computers.",
        example_value="CORP",
        usage="V_MachineValuesPath=\\\\%EmpirumServer%\\Values$\\MachineValues\\%DomainName%",
        pitfall="Bei Arbeitsgruppen-Rechnern ('WORKGROUP') weicht der Pfad auf dem Empirum-Server ab; bei "
        "Domänenmitgliedern liefert es die NetBIOS-Domäne.",
    ),
    "%EmpirumServer%": VariableDoc(
        name="%EmpirumServer%",
        category="Empirum-Infrastruktur",
        meaning="Name oder FQDN des Empirum-Servers bzw. des zuständigen SubDepots, von dem der Agent das Paket bezieht.",
        example_value="EMPIRUM01.corp.local",
        usage="V_MachineValuesPath=\\\\%EmpirumServer%\\Values$\\MachineValues\\%DomainName%",
        pitfall="Niemals feste Server-IPs oder Hostnamen fest verdrahten! %EmpirumServer% wird vom UEM-Agenten "
        "dynamisch anhand der SubDepot-Zuweisung aufgelöst.",
    ),
    "%ErrorLevel%": VariableDoc(
        name="%ErrorLevel%",
        category="Ablaufsteuerung / Returncode",
        meaning="Rückgabecode (Exit-Code) des unmittelbar zuvor ausgeführten Befehls (Call, CallHidden, Script).",
        example_value="0 (Erfolg), 3010 (Reboot erforderlich), 1603 (Fataler Fehler)",
        usage='CallHidden MsiExec /I "%Src%\\Files\\setup.msi" /qn\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        'If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf',
        pitfall="Wird von jedem nachfolgenden Befehl überschrieben! Unmittelbar nach Call/CallHidden prüfen. "
        "3010 bedeutet Erfolg mit Neustartanforderung.",
    ),
    "%LocalAppData%": VariableDoc(
        name="%LocalAppData%",
        category="Benutzerverzeichnis (Lokal)",
        meaning="Lokales (nicht roamendes) Anwendungsdaten-Verzeichnis des Benutzers (%LOCALAPPDATA%).",
        example_value=r"C:\Users\<Benutzer>\AppData\Local",
        usage='Copy "%Src%\\cache.bin", "%LocalAppData%\\Vendor\\App\\cache.bin"',
        pitfall="Nur im Benutzerteil (/AW, CLIENT-Flag) verlässlich verfügbar! Im Maschinenteil verweist es auf das SYSTEM-Profil.",
    ),
    "%Personal%": VariableDoc(
        name="%Personal%",
        category="Benutzerverzeichnis (Dokumente)",
        meaning="Dokumenten-Ordner des aktuellen Benutzers ('Eigene Dokumente' / Documents).",
        example_value=r"C:\Users\<Benutzer>\Documents",
        usage="[Application]\r\nDataDir=%Personal%",
        pitfall="Bei Ordnerumleitung (Folder Redirection oder OneDrive Known Folder Move) zeigt dieser Pfad auf den "
        "synchronisierten oder Netzlaufwerk-Ordner.",
    ),
    "%ProgramFiles%": VariableDoc(
        name="%ProgramFiles%",
        category="Systemverzeichnis",
        meaning="Standard-Programmverzeichnis der Zielarchitektur (64-Bit auf x64 mit Platform=x64).",
        example_value=r"C:\Program Files",
        usage='CallHidden "%ProgramFiles%\\Vendor\\App\\setup.exe" /S',
        pitfall="Hängt vom Platform-Wert in [Setup] ab! Für explizit 32-Bit-Pfade auf 64-Bit-Systemen immer "
        "%ProgramFiles(x86)% verwenden.",
    ),
    "%ProgramFiles(x86)%": VariableDoc(
        name="%ProgramFiles(x86)%",
        category="Systemverzeichnis (32-Bit)",
        meaning="Programmverzeichnis für 32-Bit-Anwendungen auf einem 64-Bit-Windows-Betriebssystem.",
        example_value=r"C:\Program Files (x86)",
        usage="ApplicationDir=%ProgramFiles(x86)%\\%ProductName%",
        pitfall="Auf reinen 32-Bit-Betriebssystemen existiert dieser Pfad nicht (fällt dort auf C:\\Program Files zurück).",
    ),
    "%ProgramFilesDir%": VariableDoc(
        name="%ProgramFilesDir%",
        category="Systemverzeichnis",
        meaning="Identisch zu %ProgramFiles%, aus der Windows-Registry (ProgramFilesDir) ermittelt.",
        example_value=r"C:\Program Files",
        usage="[Application]\r\nApplicationDir=%ProgramFilesDir%\\%ProductName%",
        pitfall="Synonym zu %ProgramFiles%; in [Application] ist ProgramFilesDir historisch die bevorzugte Konvention.",
    ),
    "%ProgramFilesDirx86%": VariableDoc(
        name="%ProgramFilesDirx86%",
        category="Systemverzeichnis (32-Bit)",
        meaning="Identisch zu %ProgramFiles(x86)%, aus der Windows-Registry (ProgramFilesDir (x86)) ermittelt.",
        example_value=r"C:\Program Files (x86)",
        usage="[Application]\r\nApplicationDir=%ProgramFilesDirx86%\\%ProductName%",
        pitfall="Auf 32-Bit-Systemen identisch zu %ProgramFilesDir%.",
    ),
    "%ProductName%": VariableDoc(
        name="%ProductName%",
        category="Paket-Metadaten",
        meaning="Produkt- bzw. Paketname aus [Application] ProductName=.",
        example_value="7-Zip",
        usage="V_LogFileInstall=%Temp%\\Install_%ProductName%.log",
        pitfall="Keine verbotenen Dateisystem-Sonderzeichen (/ \\ : * ? \" < > |) verwenden; steuert das Empirum-Software-Register.",
    ),
    "%Sendto%": VariableDoc(
        name="%Sendto%",
        category="Verknüpfung / Shell",
        meaning="Verzeichnis des Windows-Kontextmenüs 'Senden an' (SendTo) des Benutzers.",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\SendTo",
        usage='#Shell:SendTo, CLIENT\r\n\r\n[Shell:SendTo]\r\n"%Sendto%\\AppName", "%App%\\app.exe"',
        pitfall="Erfordert zwingend den Benutzerteil (/AW, CLIENT-Flag), da das Menü rein benutzerbezogen ist.",
    ),
    "%SetupBits%": VariableDoc(
        name="%SetupBits%",
        category="Architektur / Engine",
        meaning="Bit-Architektur des ausführenden Setup.exe-Prozesses (32 oder 64).",
        example_value="64 (auf 64-Bit-Systemen) bzw. 32",
        usage="CommonSetupDir=%CommonFilesDir%\\Setup%SetupBits%",
        pitfall="Gibt die Bitbreite des Empirum-Setup-Interpreters an, nicht zwingend die Zielarchitektur des "
        "Programms (letztere wird in Platform=x64 geregelt).",
    ),
    "%Src%": VariableDoc(
        name="%Src%",
        category="Quelle / Paketpfad",
        meaning="Absoluter Pfad zum Quellverzeichnis des Pakets zur Laufzeit (lokaler PackageStore-Cache oder Depotshare). "
        "Definiert durch SrcDir=.. in [Application].",
        example_value="C:\\EmpirumAgent\\PackageStore\\Vendor\\Product\\1.0\\",
        usage='CallHidden MsiExec /I "%Src%\\Files\\setup.msi" /qn',
        pitfall="Immer in Anführungszeichen setzen (\"%Src%\\Files\\...\"), da Paket- und Depotpfade häufig Leerzeichen enthalten.",
    ),
    "%System%": VariableDoc(
        name="%System%",
        category="Systemverzeichnis",
        meaning="Windows-Systemordner (System32).",
        example_value=r"C:\Windows\System32",
        usage='CallHidden "%System%\\reg.exe" add "HKLM\\Software\\Vendor" /v Test /t REG_SZ /d 1 /f',
        pitfall="Auf 64-Bit-Windows unterliegt ein 32-Bit-Prozess der WOW64-Dateisystemumleitung nach SysWOW64, "
        "wenn Platform nicht auf x64 steht.",
    ),
    "%Temp%": VariableDoc(
        name="%Temp%",
        category="Systemverzeichnis (Temporär)",
        meaning="Temporäres Arbeitsverzeichnis des aktuellen Ausführungskontextes.",
        example_value=r"C:\Windows\Temp (als SYSTEM) bzw. C:\Users\<User>\AppData\Local\Temp",
        usage="V_LogFileInstall=%Temp%\\Install_%ProductName%.log",
        pitfall="Im Maschinenteil (SYSTEM) hat ein Standardbenutzer keine Leserechte auf C:\\Windows\\Temp; "
        "Logdateien bei Bedarf nach %ProgramData% schreiben.",
    ),
    "%UserDomain%": VariableDoc(
        name="%UserDomain%",
        category="Netzwerk / Benutzer",
        meaning="NetBIOS-Name der Domäne des aktuell angemeldeten Benutzers.",
        example_value="CORP",
        usage='V_UserValuesPath=%HKLM,"Software\\matrix42\\Software Depot","HomeServer"%\\Values$\\UserValues\\%UserDomain%',
        pitfall="Im reinen Maschinenteil vor der Benutzeranmeldung liefert die Variable die Computerdomäne oder "
        "NT AUTHORITY. Nur im Benutzerteil (/AW) verlässlich.",
    ),
    "%Version%": VariableDoc(
        name="%Version%",
        category="Paket-Metadaten",
        meaning="Produktversion aus [Application] Version=.",
        example_value="1.0",
        usage="MachineKeyName=$Matrix42Packages$\\%DeveloperName%\\%ProductName%\\%Version%",
        pitfall="Muss exakt mit der Version im Empirum Software-Depot übereinstimmen; Änderungen erfordern "
        "eine Paket-Revisionserhöhung.",
    ),
    "%WinDir%": VariableDoc(
        name="%WinDir%",
        category="Systemverzeichnis",
        meaning="Hauptverzeichnis des Windows-Betriebssystems (%SystemRoot%).",
        example_value=r"C:\Windows",
        usage='CallHidden "%WinDir%\\notepad.exe"',
        pitfall="Niemals fest als C:\\Windows schreiben, da Windows in Spezialumgebungen auf anderen Laufwerken liegen kann.",
    ),
    "%WindowsUser%": VariableDoc(
        name="%WindowsUser%",
        category="Benutzer",
        meaning="Benutzername des aktuell interaktiv angemeldeten Windows-Benutzers (%USERNAME%).",
        example_value="s.mueller",
        usage="VU_Language=%%%V_UserValuesPath%\\%WindowsUser%.ini,%WindowsUser%,Language%%\r\nReplaceEnv VU_Language",
        pitfall="Im reinen Maschinenteil ohne /AW ist der Wert leer oder SYSTEM. Für benutzerspezifische Aktionen immer /AW verwenden.",
    ),
    # ------------------------------------------------------------------
    # Verifizierte Erweiterung (Legacy-Help Section 12 + Interpreter
    # 26.1.0)
    # ------------------------------------------------------------------
    "%Windows%": VariableDoc(
        name="%Windows%", category="Systemverzeichnis",
        meaning="Synonym für %WinDir% (dokumentierte Langform).",
        example_value=r"C:\Windows",
        usage='Copy "%Src%\\Files\\ini.ini", "%Windows%\\ini.ini"',
        pitfall="In neuen Paketen einheitlich %WinDir% verwenden.",
    ),
    "%Desktop%": VariableDoc(
        name="%Desktop%", category="Verknüpfung / Desktop",
        meaning="Desktop-Ordner – abhängig von CommonShellLinks gemeinsam oder benutzerbezogen.",
        example_value=r"C:\Users\Public\Desktop bzw. C:\Users\<Benutzer>\Desktop",
        usage='Copy "%Src%\\link.lnk", "%Desktop%\\link.lnk"',
        pitfall="Ziel hängt vom CommonShellLinks-Schalter ab – Verknüpfungen besser über [Shell:] steuern.",
    ),
    "%UserDesktop%": VariableDoc(
        name="%UserDesktop%", category="Benutzerverzeichnis",
        meaning="Desktop-Ordner des aktuellen Benutzers (unabhängig von CommonShellLinks).",
        example_value=r"C:\Users\<Benutzer>\Desktop",
        usage='Copy "%Src%\\readme.txt", "%UserDesktop%\\readme.txt"',
        pitfall="Nur im Benutzerteil (/AW) verlässlich.",
    ),
    "%StartMenu%": VariableDoc(
        name="%StartMenu%", category="Verknüpfung / Startmenü",
        meaning="Startmenü-Ordner – abhängig von CommonShellLinks gemeinsam oder benutzerbezogen.",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu",
        usage='MD "%StartMenu%\\Programs\\%DeveloperName%"',
        pitfall="Siehe %Desktop%.",
    ),
    "%CommonStartMenu%": VariableDoc(
        name="%CommonStartMenu%", category="Verknüpfung / Startmenü",
        meaning="Gemeinsamer Startmenü-Ordner aller Benutzer.",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu",
        usage='MD "%CommonStartMenu%\\Programs\\%DeveloperName%"',
        pitfall="Schreibrechte als Standardbenutzer eingeschränkt.",
    ),
    "%Programs%": VariableDoc(
        name="%Programs%", category="Verknüpfung / Startmenü",
        meaning="Startmenü\\Programme-Ordner – abhängig von CommonShellLinks.",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        usage='[Shell:Product]\r\n"%Programs%\\%ProductName%", "%App%\\app.exe"',
        pitfall="Siehe %Desktop%.",
    ),
    "%UserPrograms%": VariableDoc(
        name="%UserPrograms%", category="Benutzerverzeichnis",
        meaning="Startmenü\\Programme des aktuellen Benutzers.",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
        usage='MD "%UserPrograms%\\%ProductName%"',
        pitfall="Nur im Benutzerteil (/AW) verlässlich.",
    ),
    "%Startup%": VariableDoc(
        name="%Startup%", category="Verknüpfung / Autostart",
        meaning="Autostart-Ordner – abhängig von CommonShellLinks gemeinsam oder benutzerbezogen.",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp",
        usage='Copy "%Src%\\agent.lnk", "%Startup%\\agent.lnk"',
        pitfall="Autostart-Einträge bei Deinstallation zwingend zurücknehmen.",
    ),
    "%UserStartup%": VariableDoc(
        name="%UserStartup%", category="Benutzerverzeichnis",
        meaning="Autostart-Ordner des aktuellen Benutzers.",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\StartUp",
        usage='Copy "%Src%\\user.lnk", "%UserStartup%\\user.lnk"',
        pitfall="Nur im Benutzerteil (/AW) verlässlich.",
    ),
    "%CommonStartup%": VariableDoc(
        name="%CommonStartup%", category="Verknüpfung / Autostart",
        meaning="Gemeinsamer Autostart-Ordner aller Benutzer.",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp",
        usage='Copy "%Src%\\agent.lnk", "%CommonStartup%\\agent.lnk"',
        pitfall="Startet Anwendungen für ALLE Benutzer bei der Anmeldung.",
    ),
    "%ProgramFilesSys%": VariableDoc(
        name="%ProgramFilesSys%", category="Systemverzeichnis (32-Bit)",
        meaning="x86-Programmverzeichnis auf x64-Systemen (System-Bit-Sicht des Setup-Prozesses).",
        example_value=r"C:\Program Files (x86)",
        usage="ApplicationDir=%ProgramFilesSys%\\%ProductName%",
        pitfall="Für bewusst 32-Bit-Ziele %ProgramFiles(x86)% bevorzugen (klarere Semantik).",
    ),
    "%CommonFilesDirx86%": VariableDoc(
        name="%CommonFilesDirx86%", category="Systemverzeichnis (32-Bit)",
        meaning="Common-Files-Verzeichnis für 32-Bit-Anwendungen auf x64.",
        example_value=r"C:\Program Files (x86)\Common Files",
        usage="V_Shared86=%CommonFilesDirx86%\\Vendor",
        pitfall="Auf 32-Bit-Systemen identisch zu %CommonFilesDir%.",
    ),
    "%WriteableSystem%": VariableDoc(
        name="%WriteableSystem%", category="Systemverzeichnis",
        meaning="Terminalserver-korrekt beschreibbares Systemverzeichnis.",
        example_value=r"C:\Windows\System32",
        usage='Copy "%Src%\\drv.ini", "%WriteableSystem%\\drv.ini"',
        pitfall="Auf Terminalservern sonst ggf. Schreibumleitung in Benutzersitzung.",
    ),
    "%Fonts%": VariableDoc(
        name="%Fonts%", category="Systemverzeichnis",
        meaning="Schriftarten-Ordner von Windows.",
        example_value=r"C:\Windows\Fonts",
        usage='Copy "%Src%\\Files\\corp.ttf", "%Fonts%\\corp.ttf"',
        pitfall="Schriften zusätzlich per Registry (Fonts-Schlüssel) registrieren.",
    ),
    "%Templates%": VariableDoc(
        name="%Templates%", category="Benutzerverzeichnis",
        meaning="Vorlagen-Ordner des Benutzers (Shell-Folder Templates).",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Templates",
        usage='Copy "%Src%\\brief.dotx", "%Templates%\\brief.dotx"',
        pitfall="Benutzerbezogen – im Maschinenteil zeigt es auf das SYSTEM-Profil.",
    ),
    "%Favorites%": VariableDoc(
        name="%Favorites%", category="Benutzerverzeichnis",
        meaning="Favoriten-Ordner des Benutzers.",
        example_value=r"C:\Users\<Benutzer>\Favorites",
        usage='MD "%Favorites%\\Links"',
        pitfall="Benutzerbezogen – /AW.",
    ),
    "%Recent%": VariableDoc(
        name="%Recent%", category="Benutzerverzeichnis",
        meaning="Ordner 'Zuletzt verwendete Dateien' des Benutzers.",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Recent",
        usage='Del "%Recent%\\*.lnk"',
        pitfall="Benutzerbezogen – /AW; Löschungen sind Eingriffe in die Benutzerhistorie.",
    ),
    "%UserProfile%": VariableDoc(
        name="%UserProfile%", category="Benutzerverzeichnis",
        meaning="Profil-Stammverzeichnis des aktuellen Benutzers.",
        example_value=r"C:\Users\<Benutzer>",
        usage='MD "%UserProfile%\\AppData\\Local\\Vendor"',
        pitfall="Im Maschinenteil (SYSTEM) zeigt es auf das SYSTEM-Profil!",
    ),
    "%Client%": VariableDoc(
        name="%Client%", category="Empirum-Infrastruktur",
        meaning="Installationsart-Kontext des Setups (verifizierte Variable, Admin/Client-Logik).",
        example_value="1",
        usage="If %Client% == \"1\" Then \"Set:ClientSetup\" EndIf",
        pitfall="Nur in Admin-/Client-Installationspaketen relevant.",
    ),
    "%ClientSrcDir%": VariableDoc(
        name="%ClientSrcDir%", category="Quelle / Paketpfad",
        meaning="Quellverzeichnis des Benutzerteils einer Admin-Installation.",
        example_value=r"\\Server\Depot$\Product\Client",
        usage='Copy "%ClientSrcDir%\\user.cfg", "%AppData%\\user.cfg"',
        pitfall="Nur bei Admin-/Workstation-Installationen gesetzt.",
    ),
    "%Data%": VariableDoc(
        name="%Data%", category="Verzeichnis",
        meaning="Datenverzeichnis aus [Application] DataDir=.",
        example_value=r"C:\ProgramData\Vendor\App\Data",
        usage="[Application]\r\nDataDir=%CommonAppData%\\%DeveloperName%\\%ProductName%",
        pitfall="Wie %App% über [Application] definieren, nicht hartkodieren.",
    ),
    "%User%": VariableDoc(
        name="%User%", category="Benutzer",
        meaning="Setup-Benutzername (Kontext der Setup-Ausführung).",
        example_value="SYSTEM bzw. s.mueller",
        usage='Echo Installation läuft als %User%',
        pitfall="Unterscheidet sich von %WindowsUser%, wenn Setup elevated läuft.",
    ),
    "%WindowsVersion%": VariableDoc(
        name="%WindowsVersion%", category="System",
        meaning="Windows-Version als String (z. B. '10.0'); feldverifiziert im Agent-Paket: "
        "'If %WindowsVersion% < \"10.0\" …'.",
        example_value="10.0",
        usage='If %WindowsVersion% < "10.0" Then "Set:UnsupportedOS" EndIf',
        pitfall="Ab [Setup] Version=14.2 numerisch je Punkt-Segment vergleichen, davor ziffernweise "
        "lexikalisch!",
    ),
    "%WindowsName%": VariableDoc(
        name="%WindowsName%", category="System",
        meaning="Marketingname des Betriebssystems.",
        example_value="Windows 10 Pro",
        usage='Echo Betriebssystem: %WindowsName%',
        pitfall="Für Logik ONAME nicht parsen – dafür %OS.Name%/%WindowsVersion% nutzen.",
    ),
    "%WindowsBits%": VariableDoc(
        name="%WindowsBits%", category="Architektur",
        meaning="Bitbreite des Betriebssystems (32/64).",
        example_value="64",
        usage='If %WindowsBits% == "64" Then "Set:x64" EndIf',
        pitfall="Für die Setup-Prozess-Sicht %SetupBits% verwenden.",
    ),
    "%IsLaptop%": VariableDoc(
        name="%IsLaptop%", category="System",
        meaning="'1', wenn das Gerät ein Notebook/Portable ist, sonst '0' (Chassis-Typ).",
        example_value="1",
        usage='If %IsLaptop% == "1" Then "Set:LaptopConfig" EndIf',
        pitfall="VMs und Tablets können je nach Chassis-Typ unerwartet klassifiziert werden.",
    ),
    "%InstalledVersion%": VariableDoc(
        name="%InstalledVersion%", category="Ablaufsteuerung",
        meaning="Version der BEREITS installierten Paketversion – nur in [Requirements] gültig "
        "(Service-Release-Logik mit ServiceRelease=1).",
        example_value="1.9",
        usage="[Requirements]\r\n%InstalledVersion% < 2.0",
        pitfall="Nur in [Requirements] gesetzt; außerhalb leer.",
    ),
    "%InstalledRevision%": VariableDoc(
        name="%InstalledRevision%", category="Ablaufsteuerung",
        meaning="Revision der bereits installierten Version – nur in [Requirements].",
        example_value="3",
        usage="[Requirements]\r\n%InstalledRevision% < 5",
        pitfall="Nur in [Requirements] gesetzt; außerhalb leer.",
    ),
    "%Option%": VariableDoc(
        name="%Option%", category="Ablaufsteuerung",
        meaning="Name der aktuell gewählten Installationsoption (aus [Options]).",
        example_value="Product",
        usage='If %Option% == "API" Then "Set:InstallAPI" EndIf',
        pitfall="Bei mehreren gewählten Optionen pro Durchlauf gesetzt; [%Option%]-Gemeinschaftssektion "
        "beachten.",
    ),
    "%OptionName%": VariableDoc(
        name="%OptionName%", category="Ablaufsteuerung",
        meaning="Anzeigename der aktuellen Option.",
        example_value="Produkt",
        usage='Echo Installiere Option: %OptionName%',
        pitfall="Lokalisierter Text – nicht für Logik verwenden.",
    ),
    "%OptionText%": VariableDoc(
        name="%OptionText%", category="Ablaufsteuerung",
        meaning="Beschreibungstext der aktuellen Option.",
        example_value="Kernkomponenten installieren",
        usage='Echo %OptionText%',
        pitfall="Lokalisierter Text – nicht für Logik verwenden.",
    ),
    "%SetupInf%": VariableDoc(
        name="%SetupInf%", category="Empirum-Infrastruktur",
        meaning="Bezeichnung der aktuell ablaufenden Setup.inf.",
        example_value="Setup.inf",
        usage='Echo Lade %SetupInf%',
        pitfall="Für Pfade %SetupInfPathName% verwenden.",
    ),
    "%SetupInfFileName%": VariableDoc(
        name="%SetupInfFileName%", category="Empirum-Infrastruktur",
        meaning="Dateiname der Setup.inf.",
        example_value="Setup.inf",
        usage='Copy "%SetupInfPathName%", "%App%\\%SetupInfFileName%"',
        pitfall="—",
    ),
    "%SetupInfPathName%": VariableDoc(
        name="%SetupInfPathName%", category="Empirum-Infrastruktur",
        meaning="Voller Pfad der aktuell ablaufenden Setup.inf.",
        example_value=r"C:\EmpirumAgent\PackageStore\Vendor\App\1.0\Install\Setup.inf",
        usage='Copy "%SetupInfPathName%", "%App%\\Setup.inf"',
        pitfall="Pfad enthält Leerzeichen – quoten.",
    ),
    "%SetupInfServerName%": VariableDoc(
        name="%SetupInfServerName%", category="Empirum-Infrastruktur",
        meaning="Name des Servers/Depots, von dem die Setup.inf geladen wurde.",
        example_value="EMPIRUM01",
        usage='Echo Quelle: %SetupInfServerName%',
        pitfall="Für Depot-Pfade %EmpirumServer% bevorzugen.",
    ),
    "%SysDate%": VariableDoc(
        name="%SysDate%", category="Ablaufsteuerung",
        meaning="Aktuelles Systemdatum (kurze Darstellung) – u. a. in SwDepot-Logdateinamen sichtbar.",
        example_value="01.01.2026",
        usage='Echo Durchlauf vom %SysDate% %SysTime%',
        pitfall="Regionsabhängiges Format – nicht sortierbar; nur für Logs.",
    ),
    "%SysTime%": VariableDoc(
        name="%SysTime%", category="Ablaufsteuerung",
        meaning="Aktuelle Systemzeit.",
        example_value="14:30",
        usage='Echo Durchlauf vom %SysDate% %SysTime%',
        pitfall="Nur für Logs; nicht für Logik.",
    ),
    "%LongSysTime%": VariableDoc(
        name="%LongSysTime%", category="Ablaufsteuerung",
        meaning="Systemzeit mit Sekunden/Anteilen (long form).",
        example_value="14:30:15",
        usage='Echo Start: %LongSysTime%',
        pitfall="Nur für Logs.",
    ),
    "%ExactSysTime%": VariableDoc(
        name="%ExactSysTime%", category="Ablaufsteuerung",
        meaning="Exakte Systemzeit mit maximaler Auflösung (z. B. für Performance-Messungen).",
        example_value="14:30:15.123",
        usage='Echo T0=%ExactSysTime%',
        pitfall="Auflösung Plattform-abhängig.",
    ),
    "%CLRDir%": VariableDoc(
        name="%CLRDir%", category="Systemverzeichnis",
        meaning="Installationsverzeichnis der .NET-CLR (höchste installierte Version).",
        example_value=r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319",
        usage='CallHidden "%CLRDir%\\RegAsm.exe" "%App%\\lib.dll" /codebase',
        pitfall="Version wechselt mit .NET-Updates – nicht dauerhaft hart in Konfigen verankern.",
    ),
    "%MediaPath%": VariableDoc(
        name="%MediaPath%", category="Systemverzeichnis",
        meaning="Windows-Medienordner.",
        example_value=r"C:\Windows\Media",
        usage='PlaySound 1, "%MediaPath%\\tada.wav", 0',
        pitfall="—",
    ),
    "%PrintServer%": VariableDoc(
        name="%PrintServer%", category="Netzwerk / Drucker",
        meaning="Standard-Druckserver des Systems.",
        example_value="PRINT01",
        usage='AddPrinterConnection "\\\\%PrintServer%\\Etage1"',
        pitfall="Ohne konfigurierten Druckserver leer.",
    ),
    "%PrintEnvironment%": VariableDoc(
        name="%PrintEnvironment%", category="Netzwerk / Drucker",
        meaning="Druckertreiber-Umgebung (z. B. 'Windows x64').",
        example_value="Windows x64",
        usage='AddPrinterDriver "Generic / Text Only", "%PrintEnvironment%", "%Src%\\Driver"',
        pitfall="Muss zur Zielarchitektur passen.",
    ),
    "%PrintHood%": VariableDoc(
        name="%PrintHood%", category="Benutzerverzeichnis",
        meaning="Ordner 'Druckumgebung' des Benutzers (Shell-Folder PrintHood).",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Printer Shortcuts",
        usage='MD "%PrintHood%\\Vendor"',
        pitfall="Benutzerbezogen – /AW.",
    ),
    "%NetHood%": VariableDoc(
        name="%NetHood%", category="Benutzerverzeichnis",
        meaning="Ordner 'Netzwerkumgebung' des Benutzers (Shell-Folder NetHood).",
        example_value=r"C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Network Shortcuts",
        usage='MD "%NetHood%\\Vendor"',
        pitfall="Benutzerbezogen – /AW.",
    ),
    "%InternetCache%": VariableDoc(
        name="%InternetCache%", category="Benutzerverzeichnis",
        meaning="Cache-Ordner des Browsers (Temporary Internet Files).",
        example_value=r"C:\Users\<Benutzer>\AppData\Local\Microsoft\Windows\INetCache",
        usage='-DelTree "%InternetCache%\\Vendor"',
        pitfall="Benutzerbezogen; Pflücken von Browserdaten datenschutzrechtlich prüfen.",
    ),
    "%Cookies%": VariableDoc(
        name="%Cookies%", category="Benutzerverzeichnis",
        meaning="Cookie-Ordner des Browsers.",
        example_value=r"C:\Users\<Benutzer>\AppData\Local\Microsoft\Windows\INetCookies",
        usage='-DelTree "%Cookies%\\Vendor"',
        pitfall="Benutzerbezogen; Löschen entfernt Anmeldedaten!",
    ),
    "%History%": VariableDoc(
        name="%History%", category="Benutzerverzeichnis",
        meaning="Browser-Verlaufsordner des Benutzers.",
        example_value=r"C:\Users\<Benutzer>\AppData\Local\Microsoft\Windows\History",
        usage='Echo Cleanup %History%',
        pitfall="Benutzerbezogen; Verlaufslöschung ist Benutzereingriff.",
    ),
    "%LocalSettings%": VariableDoc(
        name="%LocalSettings%", category="Benutzerverzeichnis",
        meaning="Legacy-'Local Settings'-Ordner des Profils (Kompatibilitätsansicht).",
        example_value=r"C:\Users\<Benutzer>\AppData\Local",
        usage='Copy "%Src%\\cache.dat", "%LocalSettings%\\Vendor\\cache.dat"',
        pitfall="Legacy-Alias – neue Pakete %LocalAppData% verwenden.",
    ),
    "%Accessories%": VariableDoc(
        name="%Accessories%", category="Startmenü-Zubehör",
        meaning="Startmenü-Zubehörordner (Accessories-Shell-Folder, dokumentierte New-Folder-Variable).",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Accessories",
        usage='MD "%Accessories%\\%DeveloperName%"',
        pitfall="Ordner existiert auf deutschen Systemen lokalisiert – Variable löst korrekt auf.",
    ),
    "%Games%": VariableDoc(
        name="%Games%", category="Startmenü-Zubehör",
        meaning="Startmenü-Spieleordner (dokumentierte New-Folder-Variable).",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Games",
        usage='MD "%Games%\\%DeveloperName%"',
        pitfall="—",
    ),
    "%Multimedia%": VariableDoc(
        name="%Multimedia%", category="Startmenü-Zubehör",
        meaning="Startmenü-Multimediaordner (dokumentierte New-Folder-Variable).",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Accessories\Media",
        usage='MD "%Multimedia%\\%DeveloperName%"',
        pitfall="—",
    ),
    "%SystemTools%": VariableDoc(
        name="%SystemTools%", category="Startmenü-Zubehör",
        meaning="Startmenü-Systemwerkzeugeordner (dokumentierte New-Folder-Variable).",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools",
        usage='MD "%SystemTools%\\%DeveloperName%"',
        pitfall="—",
    ),
    "%AdminTools%": VariableDoc(
        name="%AdminTools%", category="Startmenü-Zubehör",
        meaning="Verwaltungswerkzeuge-Ordner (dokumentierte New-Folder-Variable).",
        example_value=r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools",
        usage='MD "%AdminTools%\\%DeveloperName%"',
        pitfall="—",
    ),
    "%CDBurnArea%": VariableDoc(
        name="%CDBurnArea%", category="Systemverzeichnis",
        meaning="Staging-Bereich für Brennvorgänge aller Benutzer.",
        example_value=r"C:\Users\Public\Documents\Burn",
        usage='Copy "%Src%\\iso.lst", "%CDBurnArea%\\iso.lst"',
        pitfall="—",
    ),
    "%AppPaths%": VariableDoc(
        name="%AppPaths%", category="Registry / AppPaths",
        meaning="AppPaths-Schlüssel des aktuellen Anwendungskontexts (dokumentierte Variable für "
        "App-Pfad-Registrierungen).",
        example_value=r"HKCR\AppPaths",
        usage="; Kontextvariable für AppPaths-Registrierung",
        pitfall="—",
    ),
    "%MyMusic%": VariableDoc(
        name="%MyMusic%", category="Benutzerverzeichnis (Medien)",
        meaning="Musik-Ordner des Benutzers.",
        example_value=r"C:\Users\<Benutzer>\Music",
        usage='MD "%MyMusic%\\Vendor"',
        pitfall="Bei Ordnerumleitung (OneDrive KFM) abweichend.",
    ),
    "%MyPictures%": VariableDoc(
        name="%MyPictures%", category="Benutzerverzeichnis (Medien)",
        meaning="Bilder-Ordner des Benutzers.",
        example_value=r"C:\Users\<Benutzer>\Pictures",
        usage='MD "%MyPictures%\\Vendor"',
        pitfall="Bei Ordnerumleitung abweichend.",
    ),
    "%MyVideo%": VariableDoc(
        name="%MyVideo%", category="Benutzerverzeichnis (Medien)",
        meaning="Video-Ordner des Benutzers.",
        example_value=r"C:\Users\<Benutzer>\Videos",
        usage='MD "%MyVideo%\\Vendor"',
        pitfall="Bei Ordnerumleitung abweichend.",
    ),
    "%OS.Name%": VariableDoc(
        name="%OS.Name%", category="Betriebssystem (OS.*)",
        meaning="Betriebssystemname aus der OS.*-Familie (verifizierte Variablentabelle).",
        example_value="Windows 10 Pro",
        usage='If %OS.Name% != "Windows 11" Then "Set:Win10" EndIf',
        pitfall="Für Versionsvergleiche %OS.MajorVersion%/%OS.BuildNumber% verwenden.",
    ),
    "%OS.MajorVersion%": VariableDoc(
        name="%OS.MajorVersion%", category="Betriebssystem (OS.*)",
        meaning="Hauptversionsnummer des Betriebssystems.",
        example_value="10",
        usage='If %OS.MajorVersion% >= "10" Then "Set:Modern" EndIf',
        pitfall="Zahlenvergleich ab Engine 14.2 numerisch je Segment.",
    ),
    "%OS.MinorVersion%": VariableDoc(
        name="%OS.MinorVersion%", category="Betriebssystem (OS.*)",
        meaning="Nebenversionsnummer des Betriebssystems.",
        example_value="0",
        usage='If %OS.MinorVersion% == "0" Then "OK" EndIf',
        pitfall="—",
    ),
    "%OS.BuildNumber%": VariableDoc(
        name="%OS.BuildNumber%", category="Betriebssystem (OS.*)",
        meaning="Build-Nummer des Betriebssystems.",
        example_value="26100",
        usage='If %OS.BuildNumber% < "22000" Then "Set:OldBuild" EndIf',
        pitfall="Numerisch vergleichen (5-stellige Builds > lexikalisch '9999').",
    ),
    "%OS.CSDVersion%": VariableDoc(
        name="%OS.CSDVersion%", category="Betriebssystem (OS.*)",
        meaning="Service-Pack-Bezeichner (Legacy; bei modernen Windows leer).",
        example_value="Service Pack 1",
        usage='If %OS.CSDVersion% == "" Then "OK" EndIf',
        pitfall="Seit Windows 10 immer leer – nicht mehr für SP-Logik verwenden.",
    ),
    "%OS.DisplayString%": VariableDoc(
        name="%OS.DisplayString%", category="Betriebssystem (OS.*)",
        meaning="Anzeigestring des Betriebssystems.",
        example_value="Windows 10 Pro",
        usage='Echo OS: %OS.DisplayString%',
        pitfall="Nur für Ausgaben.",
    ),
    "%OS.ProductType%": VariableDoc(
        name="%OS.ProductType%", category="Betriebssystem (OS.*)",
        meaning="Produkttyp (Workstation/Server/Domain Controller).",
        example_value="1",
        usage='If %OS.ProductType% == "3" Then "Set:ServerSKip" EndIf',
        pitfall="Werte: 1=Workstation, 2=Domain Controller, 3=Server.",
    ),
    "%OS.SuiteMask%": VariableDoc(
        name="%OS.SuiteMask%", category="Betriebssystem (OS.*)",
        meaning="Bitmaske der installierten Produktsuite.",
        example_value="256",
        usage='If %OS.SuiteMask% == "256" Then "OK" EndIf',
        pitfall="Bitmasken nur mit BitAnd auswerten.",
    ),
    "%OS.ServicePackMajor%": VariableDoc(
        name="%OS.ServicePackMajor%", category="Betriebssystem (OS.*)",
        meaning="Hauptversionsnummer des Service Packs / kumulativen Updates.",
        example_value="0",
        usage='If %OS.ServicePackMajor% < "1" Then "OK" EndIf',
        pitfall="Seit Windows 10 meist 0.",
    ),
    "%OS.PlatformId%": VariableDoc(
        name="%OS.PlatformId%", category="Betriebssystem (OS.*)",
        meaning="Plattform-ID (VER_PLATFORM_*).",
        example_value="2",
        usage='If %OS.PlatformId% == "2" Then "WinNT" EndIf',
        pitfall="—",
    ),
    "%$Everyone%": VariableDoc(
        name="%$Everyone%", category="Gruppen für [Security:]",
        meaning="Lokalisierte Gruppe 'Jeder' für die Verwendung in [Security:]-Sektionen.",
        example_value="Jeder",
        usage="[Security:Product]\r\nFileDacl.Add (\"%App%\", %$Everyone%, SET, READ)",
        pitfall="Nur für [Security:]-Sektionen gedacht (lokalisierte Gruppe).",
    ),
    "%$LocalAdmins%": VariableDoc(
        name="%$LocalAdmins%", category="Gruppen für [Security:]",
        meaning="Lokalisierte Gruppe der lokalen Administratoren für [Security:].",
        example_value="Administratoren",
        usage="[Security:Product]\r\nFileDacl.Add (\"%App%\", %$LocalAdmins%, SET, ALL)",
        pitfall="Nur für [Security:]-Sektionen gedacht.",
    ),
    "%$DomainUsers%": VariableDoc(
        name="%$DomainUsers%", category="Gruppen für [Security:]",
        meaning="Lokalisierte Gruppe der Domänenbenutzer für [Security:].",
        example_value="Domänen-Benutzer",
        usage="[Security:Product]\r\nFileDacl.Add (\"%App%\", %$DomainUsers%, SET, CHANGE)",
        pitfall="Nur für [Security:]-Sektionen gedacht.",
    ),
    "%Root,SubKey,ValueName%": VariableDoc(
        name="%Root,SubKey,ValueName%",
        category="Registry-Syntax",
        meaning="Direktes Auslesen eines Windows-Registry-Wertes zur Laufzeit. Root ist HKLM, HKCU, HKCR, HKU oder HKCC.",
        example_value=r"%HKLM,SOFTWARE\Microsoft\Windows\CurrentVersion,ProgramFilesDir%",
        usage="Set V_ProgramFiles = %HKLM,SOFTWARE\\Microsoft\\Windows\\CurrentVersion,ProgramFilesDir%\r\nReplaceEnv V_ProgramFiles",
        pitfall="Zwischen Root und SubKey steht ein Komma, KEIN Backslash! Bei leerem Wertnamen wird der Standardwert (Default) gelesen.",
    ),
    "%%%Path.ini,Section,Key%%%": VariableDoc(
        name="%%%Path.ini,Section,Key%%%",
        category="INI-Syntax",
        meaning="Liest einen Schlüsselwert aus einer externen INI-Datei (z. B. MachineValues oder UserValues auf dem Server).",
        example_value=r"%%%V_MachineValuesPath%\%ComputerName%.ini,%ComputerName%,LicenseKey%%",
        usage="VM_LicenseKey = %%%V_MachineValuesPath%\\%ComputerName%.ini,%ComputerName%,LicenseKey%%\r\nReplaceEnv VM_LicenseKey",
        pitfall="Erfordert dreifache Prozentzeichen ('%%%...%%'). Nach der Zuweisung MUSS ReplaceEnv aufgerufen werden, um den Wert aufzulösen.",
    ),
    "%VM_*%": VariableDoc(
        name="%VM_*%",
        category="MachineValues (Computer)",
        meaning="Maschinenspezifische Paketvariable (Computer-Ebene), deklariert in [VarDefInfo] mit Typ 0.",
        example_value="%VM_LicenseKey%",
        usage="[VarDefInfo]\r\nVM_LicenseKey, 0, 0\r\n\r\n[Product]\r\nReplaceEnv VM_LicenseKey",
        pitfall="Muss in [VarDefInfo] deklariert und vor der ersten Verwendung in [Product] zwingend mit 'ReplaceEnv VM_...' aufgelöst werden!",
    ),
    "%VU_*%": VariableDoc(
        name="%VU_*%",
        category="UserValues (Benutzer)",
        meaning="Benutzerspezifische Paketvariable (Benutzer-Ebene), deklariert in [VarDefInfo] mit Typ 1. Erfordert /AW.",
        example_value="%VU_Language%",
        usage="[VarDefInfo]\r\nVU_Language, 1, 1\r\n\r\n[Product]\r\nReplaceEnv VU_Language",
        pitfall="Benötigt zwingend den Schalter /AW in Command line options und im Software-Depot, sonst wird die Variable nicht pro Benutzer aufgelöst.",
    ),
}


# --------------------------------------------------------------------------
# Klasse 1 – undokumentierte Variablen (verifizierte Variablentabelle
# des Interpreters 26.1.0): kompakte Doks mit
# Warnhinweis; erscheinen nur hinter dem Feature-Flag in der Hilfe.
# --------------------------------------------------------------------------
def _undocumented_variable(name: str, meaning: str) -> VariableDoc:
    return VariableDoc(
        name=name,
        category="Undokumentiert (26.1.0)",
        meaning=f"⚠ UNDOKUMENTIERT (Klasse 1): {meaning} – verifiziert gegen den "
        "Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.",
        example_value="",
        usage="",
        pitfall="Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation "
        "gegen den Zielinterpreter einsetzen.",
    )


VARIABLE_DOCS.update(
    {
        name: _undocumented_variable(name, meaning)
        for name, meaning in (
            ("%DstDir%", "Zielverzeichnis-Variable; praktisch von Matrix42 selbst in OutlookSignatur.inf genutzt (Schreibweise %DSTDIR% im Testkorpus)"),
            ("%CalledFromService%", "Kontext-Flag, ob der Aufruf vom Setup-Service kommt"),
            ("%CurrentFqdnUser%", "Voll qualifizierter (FQDN-)Benutzername des aktuellen Kontexts"),
            ("%System16%", "16-Bit-Systemverzeichnis (Legacy)"),
            ("%SharedDir%", "Gemeinsames (Shared-)Verzeichnis des Systems"),
            ("%ResourcesDir%", "Windows-Ressourcenverzeichnis"),
            ("%UserProfiles%", "Profil-Stammverzeichnis aller Benutzer (z. B. C:\\Users)"),
            ("%CommonOEMLinks%", "OEM-Links-Ordner für alle Benutzer"),
            ("%LocalAppDataLow%", "LocalLow-Profilordner des Benutzers"),
            ("%PhotoAlbums%", "Fotoordner des Benutzers"),
            ("%Playlists%", "Wiedergabelisten-Ordner des Benutzers"),
            ("%OriginalImages%", "OriginalImages-Ordner des Benutzers"),
            ("%SavedGames%", "Gespeicherte Spiele des Benutzers"),
            ("%SavedSearches%", "Gespeicherte Suchen des Benutzers"),
            ("%SidebarDefaultParts%", "Standardkomponenten der Sidebar (Vista-Ära)"),
            ("%SidebarParts%", "Sidebar-Komponenten (Vista-Ära)"),
            ("%Contacts%", "Kontakte-Ordner des Benutzers"),
            ("%QuickLaunch%", "Schnellstartleiste des Benutzers"),
            ("%Public%", "Öffentlicher Benutzerordner (C:\\Users\\Public)"),
            ("%Downloads%", "Download-Ordner des Benutzers"),
            ("%PrintProcessorDir%", "Druckprozessor-Verzeichnis des Spoolers"),
            ("%PrinterDriverDir%", "Druckertreiber-Verzeichnis des Spoolers"),
            ("%LocalizedResourcesDir%", "Lokalisiertes Ressourcenverzeichnis"),
            ("%MediaPathUnexpanded%", "Unaufgelöster (nicht expandierter) Windows-Medienpfad"),
        )
    }
)


_COMMAND_LOOKUP = {key.casefold(): doc for key, doc in COMMAND_DOCS.items()}
_PREDICATE_LOOKUP = {key.casefold(): doc for key, doc in PREDICATE_DOCS.items()}
_FUNCTION_LOOKUP = {key.casefold(): doc for key, doc in FUNCTION_DOCS.items()}
_FLAG_LOOKUP = {key.casefold(): doc for key, doc in FLAG_DOCS.items()}
_VARIABLE_LOOKUP = {key.casefold(): doc for key, doc in VARIABLE_DOCS.items()}


def lookup_command(name: str) -> CommandDoc | None:
    """Case-insensitive command lookup ('-CallHidden' and casing tolerated)."""
    return _COMMAND_LOOKUP.get(name.strip().lstrip("-").casefold())


def lookup_predicate(name: str) -> PredicateDoc | None:
    return _PREDICATE_LOOKUP.get(name.strip().casefold())


def lookup_function(name: str) -> FunctionDoc | None:
    return _FUNCTION_LOOKUP.get(name.strip().casefold())


def lookup_flag(name: str) -> FlagDoc | None:
    return _FLAG_LOOKUP.get(name.strip().casefold())


def lookup_variable(name: str) -> VariableDoc | None:
    return _VARIABLE_LOOKUP.get(name.strip().casefold())



# --------------------------------------------------------------------------
# Schnellkurs (8 Kapitel, didaktisch gestuft)
# --------------------------------------------------------------------------

COURSE_CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        number=1,
        title="Was ist ein Empirum-Paket?",
        intro=(
            "Ein Empirum-Paket ist ein Ordner mit fester Struktur: "
            "<Paket>\\Install\\Setup.inf und <Paket>\\Files\\… (die Payload). "
            "Die Setup.inf ist eine INI-artige Textdatei, die das Verhalten des "
            "Pakets vollständig steuert – die Setup.exe des Empirum-Agents "
            "interpretiert sie nur.",
            "Lebenszyklus: Das Paket liegt im Depot (Configurator$\\PackageStore "
            "oder Software-Depot), wird in ein Software-Register importiert und "
            "auf dem Client von der Setup.exe ausgeführt. Derselbe Mechanismus "
            "installiert, repariert und deinstalliert.",
            "Wichtigste Pfade der Setup.inf selbst: SrcDir=.. bedeutet, dass die "
            "Paketwurzel das Elternverzeichnis von Install\\ ist; %Src% zeigt "
            "auf die Quelle, %App% auf das Zielverzeichnis der Kopierliste.",
        ),
        key_rule="Setup.inf ist das Programm, Setup.exe ist der Interpreter – "
        "und das Paket ist der Ordner drumherum.",
        example="<Paket>\\\r\n  Install\\\r\n    Setup.inf    ; SrcDir=.. → "
        "Paketwurzel\r\n  Files\\\r\n    setup.msi   ; %Src%\\Files\\setup.msi",
        quiz=(
            QuizItem(
                question="Wo liegt die Payload eines Pakets und wie referenziert "
                "sie die Setup.inf?",
                answer="Unter <Paket>\\Files\\; referenziert als "
                "%Src%\\Files\\…, weil SrcDir=.. die Paketwurzel ist.",
            ),
            QuizItem(
                question="Was interpretiert die Setup.inf?",
                answer="Die Setup.exe des Empirum-Agents (UEM). Die Setup.inf "
                "selbst ist nur Text und tut nichts.",
            ),
        ),
    ),
    Chapter(
        number=2,
        title="Maschinenteil vs. Benutzerteil",
        intro=(
            "Jede Installation hat zwei Bereiche: den Maschinenteil (läuft "
            "einmalig als SYSTEM auf dem Computer – Dateien, HKLM, Dienste, "
            "MSI) und den optionalen Benutzerteil (läuft bei jeder neuen "
            "Benutzeranmeldung – HKCU, Benutzer-Verknüpfungen, AskKillProcesses).",
            "Der Benutzerteil wird nur ausgeführt, wenn /AW in den Command line "
            "options von [SetupInfo] steht UND zusätzlich im Software-Depot "
            "unter Paketeigenschaften → Prüfung → Befehl ergänzt wurde. Fehlt "
            "eins von beiden, läuft der Benutzerteil nie.",
            "Schalter im Überblick: /S1 = nur Maschinenteil, /S2 = silent "
            "installieren, /U = deinstallieren, /AW = Benutzerteil anhängen.",
        ),
        key_rule="/AW muss an zwei Stellen stehen: in [SetupInfo] UND im "
        "Depot-Befehl – sonst läuft der Benutzerteil nie.",
        example="[SetupInfo]\r\nCommand line options=/S2 /AW   ; App-seitig\r\n"
        "; Depot: Paketeigenschaften → Prüfung → Befehl: … /S2 /AW",
        quiz=(
            QuizItem(
                question="Welche zwei Bedingungen braucht der Benutzerteil?",
                answer="/AW in [SetupInfo] Command line options und /AW im "
                "Depot-Befehl (Paketeigenschaften → Prüfung).",
            ),
            QuizItem(
                question="Unter welchem Konto läuft der Maschinenteil?",
                answer="SYSTEM – daher funktionieren HKCU-Schreiber dort nicht.",
            ),
        ),
    ),
    Chapter(
        number=3,
        title="[Product] steuert alles: Aufruflogik Install/Uninstall",
        intro=(
            "Die Sektion [Product] ist das Hauptprogramm. Zeilen mit # rufen "
            "Sektionen als Unterprogramm auf (GOSUB-Prinzip): Nach deren Ende "
            "geht es in der nächsten Zeile weiter.",
            "Installation: [Product] wird von oben nach unten abgearbeitet. "
            "Deinstallation: von unten nach oben – und nur Zeilen mit '-' "
            "werden ausgeführt. If-Abfragen und #-Aufrufe bekommen kein '-'; "
            "For-Schleifen laufen intern rückwärts.",
            "Die Flags an #-Aufrufen steuern die Richtung: DONTDELETE = nur "
            "Installation, DELETE = nur Deinstallation, MACHINE/CLIENT = "
            "Maschinen-/Benutzerteil, ADMIN/SHARED/WINDOWS32/WINDOWS64 = "
            "Kontextfilter. #! erzwingt die erneute Ausführung einer sonst "
            "nur einmal laufenden Sektion.",
            "Sonderrolle [Shell:Product]: läuft bei Installation automatisch "
            "zuletzt, bei Deinstallation zuerst – ganz ohne #-Aufruf, sofern "
            "ShellLinks=1.",
        ),
        key_rule="Install: [Product] top-down. Uninstall: bottom-up, nur '-'-"
        "Zeilen; DONTDELETE=install-only, DELETE=uninstall-only.",
        example="[Product]\r\n#Set:Product, DONTDELETE      ; nur Install\r\n"
        "#Reg:OnUninstallProduct, DELETE  ; nur Uninstall\r\n"
        "#Reg:Product, DONTDELETE\r\n#Security:Product       ; beide Richtungen",
        quiz=(
            QuizItem(
                question="In welcher Reihenfolge läuft [Product] bei der "
                "Deinstallation und welche Zeilen führen aus?",
                answer="Von unten nach oben; nur mit '-' präfixierte Befehle. "
                "If- und #-Zeilen brauchen kein '-'.",
            ),
            QuizItem(
                question="Was bedeutet das Flag DELETE an #Reg:OnUninstallProduct?",
                answer="Die Sektion läuft ausschließlich bei der Deinstallation "
                "(Restore-Werte setzen statt löschen).",
            ),
            QuizItem(
                question="Wann läuft [Shell:Product] ohne expliziten Aufruf?",
                answer="Bei ShellLinks=1: Installation zuletzt, Deinstallation "
                "zuerst.",
            ),
        ),
    ),
    Chapter(
        number=4,
        title="Sektionstypen im Überblick",
        intro=(
            "Setup.inf-Sektionen haben feste Rollen. Identität und Steuerung "
            "leben in SetupInfo/Setup/Application; Variablen in Environment/"
            "Strings; Ausführung in Product/Set:/Reg:/Shell:/Ini:/Security:; "
            "Kopieren in Installer; Prozesse in Processes.",
            "Die Paket-Standard verlangt das vollständige Skelett inklusive "
            "leerer Nice-to-Have-Sektionen – der EMP-PackageX3-Wizard erzeugt "
            "es automatisch. Die Detailbedeutung jeder Sektion steht in der "
            "integrierten Sektions-Referenz (Registerkarten im Lerncenter).",
        ),
        key_rule="Erst Identität (Application), dann Steuerung (Product), dann "
        "Ausführung (Set:/Reg:/Shell:) – nie Ausführung in Identitätssektionen.",
        example="Siehe Sektions-Referenz im Lerncenter (Suchfeld: z. B. "
        "'Installer' oder 'Reg:')",
        quiz=(
            QuizItem(
                question="Wo gehören Registry-Schreiber hin – und wohin die "
                "Restore-Werte?",
                answer="Schreiben in [Reg:Product]; Restore-Werte bei Uninstall "
                "in [Reg:OnUninstallProduct] mit DELETE-Flag.",
            ),
            QuizItem(
                question="Was macht die [Installer]-Sektion?",
                answer="Datei-Kopierliste des Maschinenteils (Quelle → Ziel mit "
                "Flags), z. B. Setup.inf nach %App%\\%SetupInfDir%.",
            ),
        ),
    ),
    Chapter(
        number=5,
        title="Befehle & Kontrollstrukturen",
        intro=(
            "Befehle leben in Set:-Sektionen. Dateien/MSI/Skripte starten mit "
            "Call (sichtbar) oder CallHidden (unsichtbar, Standard für Silent); "
            "Run wartet nicht. Nach jedem Aufruf ist %ErrorLevel% der "
            "Returncode des Programms.",
            "Kontrollstruktur ist die einzeilige If-Zeile: If <Prädikat> == "
            "\"<Wert>\" Then \"<Sektion>\" Else \"<Andere>\" EndIf. In If kann "
            "man nur zu SEKTIONEN springen – keine Befehle. Prädikate: "
            "DoesRegKeyExist, DoesFileExist, ErrorLevel-Vergleiche.",
            "Variablen: Set weist zu (inkl. GetUninstallKeyName), ReplaceEnv "
            "löst sofort auf, AddMeter reserviert Fortschrittsbalken-Zeilen. "
            "Sleep 3000 nach MSI-Deinstallation gibt dem System Zeit, bevor "
            "DelTree/Bereinigung läuft.",
        ),
        key_rule="Nach jedem Call/CallHidden: If %ErrorLevel% == \"3010\" Then "
        "\"RebootRequired\" EndIf und != \"0\" → Fehlersektion.",
        example='CallHidden MsiExec /I "%Src%\\Files\\setup.msi" /qn\r\n'
        'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
        'If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf',
        quiz=(
            QuizItem(
                question="Warum CallHidden statt Call in Silent-Paketen?",
                answer="Call zeigt ein Fenster; CallHidden läuft unsichtbar und "
                "wartet trotzdem auf den Returncode.",
            ),
            QuizItem(
                question="Was kann das Then einer If-Zeile aufrufen?",
                answer="Nur Sektionsnamen (Sprung) – keine Befehle.",
            ),
        ),
    ),
    Chapter(
        number=6,
        title="Variablen & Substitution",
        intro=(
            "Built-in-Variablen decken Pfade ab: %Src% (Quelle), %App% (Ziel), "
            "%ProgramFiles%, %ProgramFilesDirx86%, %Temp%, %ErrorLevel% … "
            "Produktwerte wie %ProductName%/%Version% kommen aus [Application].",
            "Eigene Variablen: V_… in [Environment] (Log-Pfade, DisplayName), "
            "Texte in [Strings:07/09] (Lokalisierung), dynamische Werte per "
            "Set … = … + ReplaceEnv. Maschinen-/benutzerabhängige Werte "
            "kommen per VM_/VU_ aus MachineValues-/UserValues-INIs – VU_ "
            "benötigt /AW.",
            "Indirekte Auflösung: %%HKLM,Pfad,Wert%% liest Registry-Werte zur "
            "Laufzeit in eine Variable (siehe UninstallString-Muster der "
            "EXE-Vorlage).",
        ),
        key_rule="Niemals C:\\-Pfade hardcodieren – immer %-Variablen "
        "(VAL-010); unbekannte Variablen meldet VAL-021.",
        example="[Environment]\r\n"
        "V_LogFileInstall=%Temp%\\Install_%ProductName%.%Version%.log\r\n"
        "V_MachineValuesPath=\\\\%EmpirumServer%\\Values$\\MachineValues…",
        quiz=(
            QuizItem(
                question="Worin unterscheiden sich VM_ und VU_?",
                answer="VM_ = maschinenabhängig (MachineValues-INI), VU_ = "
                "benutzerabhängig (UserValues-INI, braucht /AW).",
            ),
            QuizItem(
                question="Wie liest man einen Registry-Wert zur Laufzeit in "
                "eine Variable?",
                answer="Set VAR=%%HKLM,Pfad,Wert%% und danach ReplaceEnv VAR.",
            ),
        ),
    ),
    Chapter(
        number=7,
        title="Fehlerbehandlung & Reboot",
        intro=(
            "Returncode 3010 bedeutet 'erfolg, Reboot erforderlich'. Das Muster: "
            "If %ErrorLevel% == \"3010\" Then \"RebootRequired\" EndIf – in "
            "[RebootRequired] steht SetReboot 1 (und -SetReboot 1 für den "
            "Uninstall-Fall).",
            "Fehler landen in dedizierten Fehlersektionen: [Set:"
            "InstallationError], [Set:ReinstallationError], [Set:"
            "DeInstallationError] mit ErrorLogMsg + Abort (Deinstallation mit "
            "'-'). Der Sprung dorthin erfolgt per If %ErrorLevel% != \"0\".",
            "Reboot=0 in [Application] verhindert unkontrollierte Reboots des "
            "Setup-Prozesses; kontrollierte Reboots laufen ausschließlich über "
            "SetReboot im 3010-Pfad.",
        ),
        key_rule="Reboot=0 setzen; 3010 → RebootRequired/SetReboot; Fehler != 0 "
        "→ Fehlersektion mit ErrorLogMsg + Abort.",
        example='[RebootRequired]\r\nSetReboot 1\r\n-SetReboot 1\r\n\r\n'
        "[Set:InstallationError]\r\nErrorLogMsg %ErrorLogMessage%\r\n"
        "Abort %ErrorText%",
        quiz=(
            QuizItem(
                question="Was bedeutet ErrorLevel 3010 und wie reagiert man?",
                answer="Erfolg mit Reboot-Bedarf (MSI-typisch); verzweige nach "
                "[RebootRequired] → SetReboot 1.",
            ),
            QuizItem(
                question="Warum Reboot=0 in [Application]?",
                answer="Verhindert unkontrollierte Abbruch-Reboots; kontrolliert "
                "wird ausschließlich über SetReboot gesetzt.",
            ),
        ),
    ),
    Chapter(
        number=8,
        title="Der praktische Pfad mit EMP-PackageX3",
        intro=(
            "Vom Installer zum Depot-Paket in fünf Schritten: (1) PackageCreator "
            "(Werkzeuge → PackageCreator) wählt MSI/EXE/Script/Links, inspiziert "
            "Metadaten und erzeugt das Standardskelett inklusive aller "
            "Standardsektionen.",
            "(2) Im Editor prüfen: Lint (F7) mit den VAL-Regeln, QuickFix (Strg+.), "
            "Prettifier für einheitliche Formatierung; der Workflow-Tab zeigt "
            "die Ausführungslogik Install/Uninstall.",
            "(3) Simulator (Werkzeuge) läuft Install/Uninstall trocken und "
            "meldet Lücken wie fehlende Deinstallationssektionen. (4) Test-Runner "
            "als Dry-Run/echte VM-Ausführung nur mit Whitelist + "
            ".emp_packagex3_vm-Marker.",
            "(5) Deploy: PackageStore-Dialog mit 'Paket prüfen' (Readiness) "
            "vorher, dann Import in der Empirum MMC. Im Depot-Befehl /AW "
            "spiegeln, falls gesetzt (VAL-017 erinnert).",
        ),
        key_rule="Wizard → Lint → Simulator → VM-Dry-Run → Readiness → Deploy; "
        "jede Schicht fängt Fehler, die die vorige ließ.",
        example="Werkzeuge → PackageCreator… → F7 → Werkzeuge → Simulator → "
        "Test-Runner (Dry-Run) → Werkzeuge → PackageStore deployen",
        quiz=(
            QuizItem(
                question="Welche Prüfung läuft direkt vor dem PackageStore-"
                "Deploy und was blockiert sie?",
                answer="'Paket prüfen' (Readiness): Struktur (Install\\Setup.inf, "
                "Files\\), SrcDir/SetupInfDir und Lint-ERRORs blockieren.",
            ),
            QuizItem(
                question="Was schützt den Test-Runner vor Produktivläufen?",
                answer="Whitelist-Roots + .emp_packagex3_vm-Marker (und nur "
                "Dry-Run als Default).",
            ),
        ),
    ),
)


# --------------------------------------------------------------------------
# VAL-Diagnosen: Lang-Erklärung (Ursache/Behebung/Referenz)
# --------------------------------------------------------------------------

VAL_DOCS: dict[str, ValDoc] = {
    "VAL-001": ValDoc(
        "VAL-001", "ERROR",
        "Ein #-Verweis zeigt auf eine Sektion, die im Dokument nicht "
        "existiert (Tippfehler oder gelöschte Sektion).",
        "Sektion anlegen (QuickFix erzeugt Stub) oder Verweis korrigieren.",
        "Kap. 5 – Sektions-Aufrufe",
    ),
    "VAL-002": ValDoc(
        "VAL-002", "ERROR",
        "Funktionsprädikat in If ist gequotet (\"FileExists(…)\") und wird so "
        "als String-Vergleich interpretiert statt als Funktion.",
        "Äußere Anführungszeichen um das Prädikat entfernen (QuickFix).",
        "Kap. 5 – If/Prädikate",
    ),
    "VAL-003": ValDoc(
        "VAL-003", "ERROR",
        "DelTree-Argument endet mit Backslash – riskantes Löschmuster.",
        "Abschließenden Backslash entfernen (QuickFix).",
        "Kap. 6 – DelTree",
    ),
    "VAL-004": ValDoc(
        "VAL-004", "ERROR",
        "Abort/ErrorLogMsg in einer Deinstallations-Fehlersektion ohne "
        "'--'-Präfix (Legacy-Stil) – würde zur falschen Zeit laufen.",
        "'--'-Präfix ergänzen oder auf Fehlersektionen mit '-'-Command-"
        "Style umstellen.",
        "Kap. 5 – Uninstall-Logik",
    ),
    "VAL-005": ValDoc(
        "VAL-005", "WARNING",
        "ShellLinks=1 und zusätzlich #Shell:… in [Product] – Verknüpfungen "
        "würden doppelt angelegt/entfernt.",
        "Entweder die #Shell-Referenz entfernen oder ShellLinks=0 setzen.",
        "Kap. 9 – Shell-Sektion",
    ),
    "VAL-006": ValDoc(
        "VAL-006", "WARNING",
        "Benutzerteil-Merkmale (HKCU, VU_, AskKillProcesses) vorhanden, aber "
        "kein /AW in [SetupInfo].",
        "/AW in Command line options ergänzen (QuickFix) UND im Depot-Befehl "
        "spiegeln.",
        "Kap. 2 – Maschinenteil/Benutzerteil",
    ),
    "VAL-007": ValDoc(
        "VAL-007", "WARNING",
        "Registry-Löschung nahe Wurzel-/Herstellerebene (HKLM,SOFTWARE oder "
        "…\\Microsoft).",
        "Löschziel prüfen und auf die konkrete Anwendungsebene vertiefen.",
        "Kap. 7 – Registry",
    ),
    "VAL-008": ValDoc(
        "VAL-008", "WARNING",
        "Nach Call/CallHidden/Run fehlt die %ErrorLevel%-Prüfung (0/3010). "
        "Ausgenommen sind taskkill-Befehle (best-effort).",
        "ErrorLevel-Block einfügen (QuickFix: If … Then … EndIf-Zeilen).",
        "Kap. 6 – ErrorLevel",
    ),
    "VAL-009": ValDoc(
        "VAL-009", "WARNING",
        "Unkontrolliertes Reboot=1 in [Application] bzw. unkonditioniertes "
        "SetReboot 1.",
        "Reboot=0 setzen und über den 3010-Pfad ([RebootRequired]) steuern.",
        "Kap. 11 – Reboot",
    ),
    "VAL-010": ValDoc(
        "VAL-010", "INFO",
        "Hartcodierter Program-Files-Pfad statt %-Variable.",
        "Durch %ProgramFiles% bzw. %ProgramFiles(x86)% ersetzen (QuickFix).",
        "Kap. 4 – Variablen",
    ),
    "VAL-011": ValDoc(
        "VAL-011", "INFO",
        "Nach einem Deinstallations-/MSI-Aufruf fehlt Sleep vor der Bereinigung "
        "(Dateisperren).",
        "Sleep 3000 zwischen Aufruf und DelTree/Bereinigung einfügen.",
        "Kap. 6 – Sleep",
    ),
    "VAL-012": ValDoc(
        "VAL-012", "ERROR",
        "Standardsektion fehlt (das Skeleton verlangt Vollständigkeit, "
        "auch leere Sektionen).",
        "Sektion anlegen (QuickFix) oder Vorlage neu erzeugen.",
        "Kap. 3 – Sektions-Referenz",
    ),
    "VAL-013": ValDoc(
        "VAL-013", "ERROR",
        "Pflichtfeld in [Application] fehlt (Identität/Reparaturpfad "
        "unvollständig). Kurznamen (ProductNameShort/DeveloperNameShort) "
        "sind optional und werden als Info gewertet.",
        "Feld ergänzen – der PackageCreator setzt alle Pflichtfelder vor.",
        "Kap. 3 – [Application]",
    ),
    "VAL-014": ValDoc(
        "VAL-014", "ERROR",
        "[Setup] Version fehlt oder ist leer (Setup.inf-Dialekt).",
        "Version=14.2 setzen.",
        "Kap. 3 – [Setup]",
    ),
    "VAL-015": ValDoc(
        "VAL-015", "ERROR",
        "SrcDir/SetupInfDir verletzen das Install\\Setup.inf-Layout oder "
        "[Environment] CommonSetupDir fehlt.",
        "SrcDir=.. und SetupInfDir=Install setzen; CommonSetupDir ergänzen.",
        "Kap. 1 – Paketaufbau",
    ),
    "VAL-016": ValDoc(
        "VAL-016", "WARNING",
        "MsiExec /I ohne die Empfehlung ALLUSERS=\"1\" REBOOT="
        "REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn.",
        "Flags ergänzen (Snippet msi-install zeigt das Muster).",
        "Kap. 13 – MSI-Paketierung",
    ),
    "VAL-017": ValDoc(
        "VAL-017", "INFO",
        "/AW ist in SetupInfo gesetzt – Erinnerung, den Depot-Befehl zu "
        "spiegeln.",
        "Im Software-Depot unter Paketeigenschaften → Prüfung → Befehl /AW "
        "ergänzen.",
        "Kap. 2 – Benutzerteil",
    ),
    "VAL-018": ValDoc(
        "VAL-018", "INFO",
        "'-'-Präfix in [Reg:…] löscht erst bei der Deinstallation – häufig "
        "Missverständnis.",
        "Für Löschung während der Installation CallHidden reg.exe delete … "
        "nutzen (Snippet vorhanden).",
        "Kap. 7 – Registry",
    ),
    "VAL-019": ValDoc(
        "VAL-019", "WARNING",
        "Der Befehl ist nicht in der Setup.inf-Befehlsreferenz dokumentiert "
        "(Tippfehler oder exotischer Befehl).",
        "Schreibweise gegen die Befehlsliste prüfen (Hilfe → Setup.inf-Hilfe).",
        "Kap. 6 – Befehle",
    ),
    "VAL-020": ValDoc(
        "VAL-020", "ERROR",
        "If-Zeile mit Then, aber ohne EndIf in derselben Zeile – entspricht "
        "nicht der Referenz-Syntax.",
        "EndIf am Zeilenende ergänzen.",
        "Kap. 5 – If/Then/Else/EndIf",
    ),
    "VAL-021": ValDoc(
        "VAL-021", "WARNING",
        "Verwendete %Variable% ist weder eingebaut noch im Dokument definiert "
        "(Environment/Strings/Application/Set).",
        "Variable in [Environment] definieren oder Schreibweise korrigieren.",
        "Kap. 4 – Variablen",
    ),
    "VAL-022": ValDoc(
        "VAL-022", "ERROR",
        "[Reg:…]-Sektionen sind rein deklarativ; prozedurale Befehle wie If, "
        "CallHidden oder RegModify verlieren hier ihre Bedingung oder sind ungültig.",
        "Befehle in [Set:…]-Sektionen verschieben; bedingte Registry-Änderungen "
        "mit CallHidden reg.exe add in [Set:Then_…] ausführen.",
        "Kap. 7 – Registry",
    ),
    "VAL-023": ValDoc(
        "VAL-023", "WARNING",
        "Variable wird über dynamische Funktion (z. B. GetUninstallKeyName) oder Registry/INI zugewiesen, "
        "wird aber in dieser Sektion nicht mit 'ReplaceEnv <Var>' aufgelöst.",
        "Nach 'Set <Var> = ...' ein 'ReplaceEnv <Var>' ergänzen, damit Platzhalter sofort expandiert werden.",
        "Kap. 4 – Variablen",
    ),
    "VAL-024": ValDoc(
        "VAL-024", "WARNING",
        "Befehl 'Abort' wird ohne vorangehendes 'ErrorLogMsg' aufgerufen; "
        "im Empirum-Fehlerprotokoll fehlt dadurch eine aussagekräftige Fehlerursache.",
        "Vor 'Abort' ein 'ErrorLogMsg <Meldung>' einfügen.",
        "Kap. 8 – Fehlerbehandlung",
    ),
    "VAL-025": ValDoc(
        "VAL-025", "ERROR",
        "Ungültige Zuweisungssyntax 'Sleep=…'. Befehl 'Sleep' verlangt Befehlssyntax 'Sleep <Millisekunden>' "
        "ohne Gleichheitszeichen.",
        "In 'Sleep <Millisekunden>' korrigieren (z. B. 'Sleep 3000').",
        "Befehlsreferenz – Sleep",
    ),
    "VAL-026": ValDoc(
        "VAL-026", "ERROR",
        "Befehl oder Prädikat existiert nicht im Empirum-Interpreter 26.1.0 "
        "(verifiziert gegen Setup.exe/Setup64.exe). Betroffen u. a. "
        "CheckLanAdministrator, Run sowie die Alias-Prädikate FileExists/"
        "DirExists/RegKeyExists/RegValueExists/ProcessExists/ServiceExists. "
        "Unbekannte Befehle werden vom Interpreter als Programmstart interpretiert "
        "(SETUP_ERR_UNRECOGNIZABLE) und versagen dadurch still.",
        "Umbenennungs-QuickFix nutzen (z. B. Run→CallHidden, FileExists→DoesFileExist, "
        "DirExists→DoesPathExist, RegValueExists→DoesRegKeyExist mit ValueName-Komponente). "
        "Für Dienst-Prüfungen DoesRegKeyExist auf HKLM,SYSTEM\\CurrentControlSet\\Services\\<Name> "
        "verwenden; CheckLanAdministrator-Zeilen entfernen.",
        "Verifikation – Empirum-Interpreter 26.1.0",
    ),
    "VAL-027": ValDoc(
        "VAL-027", "WARNING",
        "Registry-Typcode in [Reg:…] entspricht nicht der offiziellen Typentabelle des "
        "Empirum-Interpreters (z. B. alter PackagerX-QWORD-Code 0x00010004 statt 0x00040001). "
        "Falsche Codes führen zu falschen Werttypen oder zu ignorierten Zeilen.",
        "Typcode korrigieren (QuickFix bei bekannten Fehlcodes). Offiziell: REG_SZ=0x00000000, "
        "REG_BINARY=0x00000001, REG_MULTI_SZ=0x00010000, REG_DWORD=0x00010001, "
        "REG_EXPAND_SZ=0x00020000, REG_NONE=0x00020001, REG_QWORD=0x00040001, "
        "REG_BINARY_SZ=0x10000001; additive Verhaltens-Flags +0x2/+0x8/+0x10 sind erlaubt.",
        "Verifikation – Empirum-Interpreter 26.1.0 ",
    ),
    "VAL-028": ValDoc(
        "VAL-028", "WARNING",
        "Interaktive Befehle (Prompt, AskKillProcesses, CloseWindow, SplashDialog*) in einem "
        "Paket mit Silent-Level /S0 oder /S1 – Dialoge und Prompts werden auf diesen Stufen "
        "unterdrückt (dokumentierte Silent-Semantik des Setup.exe-Aufrufs).",
        "Entweder das Silent-Level erhöhen (/S2 zeigt Prompts) oder die Befehlslogik auf die "
        "Default-Antwort der [Prompts]-Definition umstellen und Default bewusst setzen.",
        "Befehlsreferenz – Setup.exe-Schalter /S<Level>",
    ),
    "VAL-029": ValDoc(
        "VAL-029", "WARNING",
        "'AbortSilent' meldet dem Software-Depot 'Success' und führt den Benutzerteil trotzdem "
        "aus (dokumentierte 26.1.0-Semantik) – das Paket erscheint trotz Abbruch als erfolgreich.",
        "Für echte Fehler 'ErrorLogMsg' + 'Abort' verwenden; 'AbortSilent' nur für bewusstes, "
        "stilles Überspringen einsetzen.",
        "Befehlsreferenz – AbortSilent",
    ),
    "VAL-030": ValDoc(
        "VAL-030", "ERROR",
        "Setup.inf beginnt mit einem Byte Order Mark (BOM: EF BB BF, FF FE, FE FF oder Mojibake ï»¿). "
        "Der native Win32/MFC-Interpreter von Empirum (Setup.exe) kann die erste Sektion [SetupInfo] "
        "durch den BOM nicht erkennen und bricht sofort ab. Zudem kann der Matrix42 Package Editor "
        "die Datei nicht parsen und der Einzelschritt-Debug startet nicht.",
        "Datei ohne BOM als Windows-1252 (ANSI) speichern. Ein QuickFix steht zur Verfügung.",
        "Empirum Knowledge Base – Zeichensatz Windows-1252 (ANSI/CP1252), kein BOM",
    ),
    "VAL-031": ValDoc(
        "VAL-031", "ERROR",
        "Zeile enthält Zeichen, die im Windows-1252 (ANSI/CP1252)-Zeichensatz nicht darstellbar sind "
        "(z. B. typografische Sonderzeichen, Emojis, asiatische/kyrillische Zeichen) oder die Datei "
        "ist nicht als Windows-1252 deklariert. Empirum unterstützt ausschließlich Windows-1252. "
        "Beim Speichern als CP1252 schlägt die Kodierung fehl; beim Speichern als UTF-8 interpretiert "
        "Setup.exe die Zeichen fehlerhaft.",
        "Nicht unterstützte Sonderzeichen entfernen oder durch ASCII/CP1252-Äquivalente ersetzen.",
        "Empirum Reference – Zeichensatz Windows-1252 (CP1252)",
    ),
    "VAL-032": ValDoc(
        "VAL-032", "ERROR",
        "Benutzerkontext-Befehl (%AppData%, %LocalAppData%, %Desktop%, %Personal%, %Sendto% oder "
        "prozeduraler HKCU-Schreibzugriff) liegt außerhalb der CLIENT-Sektion, obwohl das Paket "
        "einen echten Benutzerteil besitzt. Im Maschinendurchlauf läuft die Zeile als SYSTEM und "
        "wirkt auf das SYSTEM-Profil statt auf den angemeldeten Benutzer (Benutzerkontext).",
        "Zeile nach [Set:Client] verschieben (CLIENT-Flag + /AW) – sofern sie nicht bewusst in "
        "beiden Durchläufen laufen soll; dann die MACHINE-Flags an den [Product]-Einträgen entfernen.",
        "User-Parts: /AW, CLIENT/MACHINE",
    ),
    "VAL-033": ValDoc(
        "VAL-033", "ERROR",
        "Doppelte [Set:Client]-Sektion: Empirum führt gleichnamige Sektionen zusammen, die "
        "Ausführungsreihenfolge wird unbestimmt – der Benutzerteil muss genau eine Sektion sein.",
        "Alle Benutzerbefehle in EINE [Set:Client]-Sektion zusammenführen (niemals zwei "
        "gleichnamige Sektionen emittieren).",
        "User-Parts: Sektions-Merge",
    ),
    "VAL-034": ValDoc(
        "VAL-034", "WARNING",
        "MACHINE-Flag auf einem #Reg:-Aufruf, dessen Zielsektion HKCU-Einträge enthält. Die "
        "Sektion wird im Benutzerdurchlauf (/AW) übersprungen und die HKCU-Werte pro Benutzer "
        "stillschweigend nie geschrieben.",
        "MACHINE-Flag vom Registry-Aufruf entfernen, damit die Sektion in beiden Durchläufen "
        "läuft (HKLM-Schreibzugriffe sind idempotent). QuickFix verfügbar.",
        "User-Parts: Flag-Tabelle #Reg:Product",
    ),
}


def val_rule_range() -> str:
    """Display range of the shipped VAL rules, e.g. 'VAL-001…027'.

    Derived from VAL_DOCS so menus and help headings never go stale when
    engine rules are added.
    """
    codes = sorted(VAL_DOCS)
    if not codes:
        return "VAL"
    return f"{codes[0]}…{codes[-1][-3:]}"
