# Setup.inf-Schnellkurs (kanonisch, aus learning_content.py generiert)

> Generiert aus `src/emp_packagex3/learning_content.py` – Inhalte dort
> pflegen und diese Datei neu generieren, damit App und Doku nicht driften.

## Kapitel 1: Was ist ein Empirum-Paket?

Ein Empirum-Paket ist ein Ordner mit fester Struktur: <Paket>\Install\Setup.inf und <Paket>\Files\… (die Payload). Die Setup.inf ist eine INI-artige Textdatei, die das Verhalten des Pakets vollständig steuert – die Setup.exe des Empirum-Agents interpretiert sie nur.
Lebenszyklus: Das Paket liegt im Depot (Configurator$\PackageStore oder Software-Depot), wird in ein Software-Register importiert und auf dem Client von der Setup.exe ausgeführt. Derselbe Mechanismus installiert, repariert und deinstalliert.
Wichtigste Pfade der Setup.inf selbst: SrcDir=.. bedeutet, dass die Paketwurzel das Elternverzeichnis von Install\ ist; %Src% zeigt auf die Quelle, %App% auf das Zielverzeichnis der Kopierliste.

> **Merksatz:** Setup.inf ist das Programm, Setup.exe ist der Interpreter – und das Paket ist der Ordner drumherum.

**Systembeispiel:**

```ini
<Paket>\
  Install\
    Setup.inf    ; SrcDir=.. → Paketwurzel
  Files\
    setup.msi   ; %Src%\Files\setup.msi
```

### Selbsttest

1. **Wo liegt die Payload eines Pakets und wie referenziert sie die Setup.inf?**
   *Antwort:* Unter <Paket>\Files\; referenziert als %Src%\Files\…, weil SrcDir=.. die Paketwurzel ist.

2. **Was interpretiert die Setup.inf?**
   *Antwort:* Die Setup.exe des Empirum-Agents (UEM). Die Setup.inf selbst ist nur Text und tut nichts.

## Kapitel 2: Maschinenteil vs. Benutzerteil

Jede Installation hat zwei Bereiche: den Maschinenteil (läuft einmalig als SYSTEM auf dem Computer – Dateien, HKLM, Dienste, MSI) und den optionalen Benutzerteil (läuft bei jeder neuen Benutzeranmeldung – HKCU, Benutzer-Verknüpfungen, AskKillProcesses).
Der Benutzerteil wird nur ausgeführt, wenn /AW in den Command line options von [SetupInfo] steht UND zusätzlich im Software-Depot unter Paketeigenschaften → Prüfung → Befehl ergänzt wurde. Fehlt eins von beiden, läuft der Benutzerteil nie.
Schalter im Überblick: /S1 = nur Maschinenteil, /S2 = silent installieren, /U = deinstallieren, /AW = Benutzerteil anhängen.

> **Merksatz:** /AW muss an zwei Stellen stehen: in [SetupInfo] UND im Depot-Befehl – sonst läuft der Benutzerteil nie.

**Systembeispiel:**

```ini
[SetupInfo]
Command line options=/S2 /AW   ; App-seitig
; Depot: Paketeigenschaften → Prüfung → Befehl: … /S2 /AW
```

### Selbsttest

1. **Welche zwei Bedingungen braucht der Benutzerteil?**
   *Antwort:* /AW in [SetupInfo] Command line options und /AW im Depot-Befehl (Paketeigenschaften → Prüfung).

2. **Unter welchem Konto läuft der Maschinenteil?**
   *Antwort:* SYSTEM – daher funktionieren HKCU-Schreiber dort nicht.

## Kapitel 3: [Product] steuert alles: Aufruflogik Install/Uninstall

Die Sektion [Product] ist das Hauptprogramm. Zeilen mit # rufen Sektionen als Unterprogramm auf (GOSUB-Prinzip): Nach deren Ende geht es in der nächsten Zeile weiter.
Installation: [Product] wird von oben nach unten abgearbeitet. Deinstallation: von unten nach oben – und nur Zeilen mit '-' werden ausgeführt. If-Abfragen und #-Aufrufe bekommen kein '-'; For-Schleifen laufen intern rückwärts.
Die Flags an #-Aufrufen steuern die Richtung: DONTDELETE = nur Installation, DELETE = nur Deinstallation, MACHINE/CLIENT = Maschinen-/Benutzerteil, ADMIN/SHARED/WINDOWS32/WINDOWS64 = Kontextfilter. #! erzwingt die erneute Ausführung einer sonst nur einmal laufenden Sektion.
Sonderrolle [Shell:Product]: läuft bei Installation automatisch zuletzt, bei Deinstallation zuerst – ganz ohne #-Aufruf, sofern ShellLinks=1.

> **Merksatz:** Install: [Product] top-down. Uninstall: bottom-up, nur '-'-Zeilen; DONTDELETE=install-only, DELETE=uninstall-only.

**Systembeispiel:**

```ini
[Product]
#Set:Product, DONTDELETE      ; nur Install
#Reg:OnUninstallProduct, DELETE  ; nur Uninstall
#Reg:Product, DONTDELETE
#Security:Product       ; beide Richtungen
```

### Selbsttest

1. **In welcher Reihenfolge läuft [Product] bei der Deinstallation und welche Zeilen führen aus?**
   *Antwort:* Von unten nach oben; nur mit '-' präfixierte Befehle. If- und #-Zeilen brauchen kein '-'.

2. **Was bedeutet das Flag DELETE an #Reg:OnUninstallProduct?**
   *Antwort:* Die Sektion läuft ausschließlich bei der Deinstallation (Restore-Werte setzen statt löschen).

3. **Wann läuft [Shell:Product] ohne expliziten Aufruf?**
   *Antwort:* Bei ShellLinks=1: Installation zuletzt, Deinstallation zuerst.

## Kapitel 4: Sektionstypen im Überblick

Setup.inf-Sektionen haben feste Rollen. Identität und Steuerung leben in SetupInfo/Setup/Application; Variablen in Environment/Strings; Ausführung in Product/Set:/Reg:/Shell:/Ini:/Security:; Kopieren in Installer; Prozesse in Processes.
Die Paket-Standard verlangt das vollständige Skelett inklusive leerer Nice-to-Have-Sektionen – der EMP-PackageX3-Wizard erzeugt es automatisch. Die Detailbedeutung jeder Sektion steht in der integrierten Sektions-Referenz (Registerkarten im Lerncenter).

> **Merksatz:** Erst Identität (Application), dann Steuerung (Product), dann Ausführung (Set:/Reg:/Shell:) – nie Ausführung in Identitätssektionen.

**Systembeispiel:**

```ini
Siehe Sektions-Referenz im Lerncenter (Suchfeld: z. B. 'Installer' oder 'Reg:')
```

### Selbsttest

1. **Wo gehören Registry-Schreiber hin – und wohin die Restore-Werte?**
   *Antwort:* Schreiben in [Reg:Product]; Restore-Werte bei Uninstall in [Reg:OnUninstallProduct] mit DELETE-Flag.

2. **Was macht die [Installer]-Sektion?**
   *Antwort:* Datei-Kopierliste des Maschinenteils (Quelle → Ziel mit Flags), z. B. Setup.inf nach %App%\%SetupInfDir%.

## Kapitel 5: Befehle & Kontrollstrukturen

Befehle leben in Set:-Sektionen. Dateien/MSI/Skripte starten mit Call (sichtbar) oder CallHidden (unsichtbar, Standard für Silent); Run wartet nicht. Nach jedem Aufruf ist %ErrorLevel% der Returncode des Programms.
Kontrollstruktur ist die einzeilige If-Zeile: If <Prädikat> == "<Wert>" Then "<Sektion>" Else "<Andere>" EndIf. In If kann man nur zu SEKTIONEN springen – keine Befehle. Prädikate: DoesRegKeyExist, DoesFileExist, ErrorLevel-Vergleiche.
Variablen: Set weist zu (inkl. GetUninstallKeyName), ReplaceEnv löst sofort auf, AddMeter reserviert Fortschrittsbalken-Zeilen. Sleep 3000 nach MSI-Deinstallation gibt dem System Zeit, bevor DelTree/Bereinigung läuft.

> **Merksatz:** Nach jedem Call/CallHidden: If %ErrorLevel% == "3010" Then "RebootRequired" EndIf und != "0" → Fehlersektion.

**Systembeispiel:**

```ini
CallHidden MsiExec /I "%Src%\Files\setup.msi" /qn
If %ErrorLevel% == "3010" Then "RebootRequired" EndIf
If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf
```

### Selbsttest

1. **Warum CallHidden statt Call in Silent-Paketen?**
   *Antwort:* Call zeigt ein Fenster; CallHidden läuft unsichtbar und wartet trotzdem auf den Returncode.

2. **Was kann das Then einer If-Zeile aufrufen?**
   *Antwort:* Nur Sektionsnamen (Sprung) – keine Befehle.

## Kapitel 6: Variablen & Substitution

Built-in-Variablen decken Pfade ab: %Src% (Quelle), %App% (Ziel), %ProgramFiles%, %ProgramFilesDirx86%, %Temp%, %ErrorLevel% … Produktwerte wie %ProductName%/%Version% kommen aus [Application].
Eigene Variablen: V_… in [Environment] (Log-Pfade, DisplayName), Texte in [Strings:07/09] (Lokalisierung), dynamische Werte per Set … = … + ReplaceEnv. Maschinen-/benutzerabhängige Werte kommen per VM_/VU_ aus MachineValues-/UserValues-INIs – VU_ benötigt /AW.
Indirekte Auflösung: %%HKLM,Pfad,Wert%% liest Registry-Werte zur Laufzeit in eine Variable (siehe UninstallString-Muster der EXE-Vorlage).

> **Merksatz:** Niemals C:\-Pfade hardcodieren – immer %-Variablen (VAL-010); unbekannte Variablen meldet VAL-021.

**Systembeispiel:**

```ini
[Environment]
V_LogFileInstall=%Temp%\Install_%ProductName%.%Version%.log
V_MachineValuesPath=\\%EmpirumServer%\Values$\MachineValues…
```

### Selbsttest

1. **Worin unterscheiden sich VM_ und VU_?**
   *Antwort:* VM_ = maschinenabhängig (MachineValues-INI), VU_ = benutzerabhängig (UserValues-INI, braucht /AW).

2. **Wie liest man einen Registry-Wert zur Laufzeit in eine Variable?**
   *Antwort:* Set VAR=%%HKLM,Pfad,Wert%% und danach ReplaceEnv VAR.

## Kapitel 7: Fehlerbehandlung & Reboot

Returncode 3010 bedeutet 'erfolg, Reboot erforderlich'. Das Muster: If %ErrorLevel% == "3010" Then "RebootRequired" EndIf – in [RebootRequired] steht SetReboot 1 (und -SetReboot 1 für den Uninstall-Fall).
Fehler landen in dedizierten Fehlersektionen: [Set:InstallationError], [Set:ReinstallationError], [Set:DeInstallationError] mit ErrorLogMsg + Abort (Deinstallation mit '-'). Der Sprung dorthin erfolgt per If %ErrorLevel% != "0".
Reboot=0 in [Application] verhindert unkontrollierte Reboots des Setup-Prozesses; kontrollierte Reboots laufen ausschließlich über SetReboot im 3010-Pfad.

> **Merksatz:** Reboot=0 setzen; 3010 → RebootRequired/SetReboot; Fehler != 0 → Fehlersektion mit ErrorLogMsg + Abort.

**Systembeispiel:**

```ini
[RebootRequired]
SetReboot 1
-SetReboot 1

[Set:InstallationError]
ErrorLogMsg %ErrorLogMessage%
Abort %ErrorText%
```

### Selbsttest

1. **Was bedeutet ErrorLevel 3010 und wie reagiert man?**
   *Antwort:* Erfolg mit Reboot-Bedarf (MSI-typisch); verzweige nach [RebootRequired] → SetReboot 1.

2. **Warum Reboot=0 in [Application]?**
   *Antwort:* Verhindert unkontrollierte Abbruch-Reboots; kontrolliert wird ausschließlich über SetReboot gesetzt.

## Kapitel 8: Der praktische Pfad mit EMP-PackageX3

Vom Installer zum Depot-Paket in fünf Schritten: (1) PackageCreator (Werkzeuge → PackageCreator) wählt MSI/EXE/Script/Links, inspiziert Metadaten und erzeugt das Standardskelett inklusive aller Standardsektionen.
(2) Im Editor prüfen: Lint (F7) mit den VAL-Regeln, QuickFix (Strg+.), Prettifier für einheitliche Formatierung; der Workflow-Tab zeigt die Ausführungslogik Install/Uninstall.
(3) Simulator (Werkzeuge) läuft Install/Uninstall trocken und meldet Lücken wie fehlende Deinstallationssektionen. (4) Test-Runner als Dry-Run/echte VM-Ausführung nur mit Whitelist + .emp_packagex3_vm-Marker.
(5) Deploy: PackageStore-Dialog mit 'Paket prüfen' (Readiness) vorher, dann Import in der Empirum MMC. Im Depot-Befehl /AW spiegeln, falls gesetzt (VAL-017 erinnert).

> **Merksatz:** Wizard → Lint → Simulator → VM-Dry-Run → Readiness → Deploy; jede Schicht fängt Fehler, die die vorige ließ.

**Systembeispiel:**

```ini
Werkzeuge → PackageCreator… → F7 → Werkzeuge → Simulator → Test-Runner (Dry-Run) → Werkzeuge → PackageStore deployen
```

### Selbsttest

1. **Welche Prüfung läuft direkt vor dem PackageStore-Deploy und was blockiert sie?**
   *Antwort:* 'Paket prüfen' (Readiness): Struktur (Install\Setup.inf, Files\), SrcDir/SetupInfDir und Lint-ERRORs blockieren.

2. **Was schützt den Test-Runner vor Produktivläufen?**
   *Antwort:* Whitelist-Roots + .emp_packagex3_vm-Marker (und nur Dry-Run als Default).

## Sektions-Referenz

### [SetupInfo] (Paket-Standard)

Steuert das Verhalten des Setup.exe-Aufrufs: Silent-Optionen, Paket-Metadaten für das Depot.

*Wann brauche ich das?* Immer. Hier stehen Command line options (/S1 /S2 /U /AW) und Beschreibung/Methodik für den Paketierer.

```ini
[SetupInfo]
Description=DemoApp 1.0
Method=MSI
Command line options=/S2 /AW
```

*Referenz: Kap. 3 – [SetupInfo]*

### [VarDefInfo] (Paket-Standard)

Deklariert Variablen-Typen: Computer (VM_) oder Benutzer (VU_), inkl. NULL-Werte-Erlaubnis.

*Wann brauche ich das?* Sobald VM_/VU_-Variablen aus MachineValues/UserValues-INIs genutzt werden (mit /AW für VU_).

```ini
[VarDefInfo]
; <Variable>, <Type: 0=Computer 1=User>, <Allow NULL: 0=No 1=Yes>
```

*Referenz: Kap. 3 – [VarDefInfo]*

### [Setup] (Paket-Standard)

Dialekt-/Verhaltensversion der Setup.inf und Fenster-/Plattform-Einstellungen für den Setup-Assistenten.

*Wann brauche ich das?* Immer; Version=14.2 ist der aktuelle Dialekt (nicht die Empirum-Produktversion).

```ini
[Setup]
Version=14.2
ShowCaption=1
Platform=x64
```

*Referenz: Kap. 3 – [Setup], Kap. 12*

### [Requirements] (Paket-Standard)

Vorbedingungen für die Installation (OS, Service Packs, Abhängigkeiten), geprüft vor dem Start.

*Wann brauche ich das?* Bei Paketen mit harten Voraussetzungen oder Abhängigkeiten.

```ini
[Requirements]
```

*Referenz: Kap. 3 – [Requirements]*

### [Application] (Paket-Standard)

Identität des Pakets im Empirum-Register: Namen, Version, Uninstall-Strings, Pfade (SrcDir/SetupInfDir/ApplicationDir), Verhalten (Reboot, ShellLinks, Timeouts).

*Wann brauche ich das?* Immer – die Identität steuert Software-Register, ARP und Reparatur.

```ini
[Application]
ProductName=DemoApp
Version=1.0
SrcDir=..
SetupInfDir=Install
Reboot=0
```

*Referenz: Kap. 3 – [Application]*

### [Strings:07 / Strings:09] (Paket-Standard)

Lokalisierungstexte je Sprachkode (07=deutsch, 09=englisch); Einbindung über UseStringSection.

*Wann brauche ich das?* Immer im Paket-Standard; jedes %TextVar% in Dialogen/Logs kommt hierher.

```ini
[Strings:07]
EndMessageDesc=Die Installation wurde erfolgreich abgeschlossen!
```

*Referenz: Kap. 3 – [Strings]*

### [SysStrings:07 / SysStrings:09] (Paket-Standard)

Wie Strings, aber systemsprachabhängig statt benutzerbezogen.

*Wann brauche ich das?* Wenn Texte unabhängig von der Benutzer-, aber abhängig von der Systemsprache sein sollen.

```ini
[SysStrings:07]
Users=Benutzer
```

*Referenz: Kap. 3 – [SysStrings]*

### [Environment] (Paket-Standard)

Definiert Paketvariablen (V_…), Pfade (CommonSetupDir) und Logdatei-Namen; wird vor der Abarbeitung substituiert.

*Wann brauche ich das?* Immer im Paket-Standard – zentrale Stelle für Log-Pfade, DisplayName, MSI-GUID-Halter (V_ProductCode).

```ini
[Environment]
V_LogFileInstall=%Temp%\Install_%ProductName%.log
CommonSetupDir=%CommonFilesDir%\Setup%SetupBits%
```

*Referenz: Kap. 3 – [Environment], Kap. 4*

### [Encryption] (Paket-Standard)

Optionale Entschlüsselungsinformation für verschlüsselte Paketbestandteile.

*Wann brauche ich das?* Nur bei verschlüsselten Paketen (selten).

```ini
[Encryption]
```

*Referenz: Kap. 3 – [Encryption]*

### [Disks] (Paket-Standard)

Medien-/Quelllaufwerke der Paketdateien.

*Wann brauche ich das?* Immer (Standard-Stub mit Disk1).

```ini
[Disks]
1=Installationsmedium 1
```

*Referenz: Kap. 3 – [Disks]*

### [Options] (Paket-Standard)

Auswahloptionen des Setup-Assistenten; verbindet Anzeigename mit Sektionen und Copy-Flags (COPYALWAYS).

*Wann brauche ich das?* Immer im Paket-Standard (Installer/Product-Optionen).

```ini
[Options]
Product=%ProductName%, COPYALWAYS, Product, "%ProductDesc%"
```

*Referenz: Kap. 3 – [Options]*

### [Processes] (Paket-Standard)

Benannte Prozesse für AskKillProcesses: EXE-Name, Anzeigename, KILLPROCESS-Modus (ABORT/CONTINUE).

*Wann brauche ich das?* Bei laufenden Apps vor Installation (Unattend-EXE, Office-Addins …). Benötigt /AW für den Benutzerteil-Dialog.

```ini
[Processes]
APP1=app.exe, DemoApp, KILLPROCESS ABORT
```

*Referenz: Kap. 10 – Prozessmanagement*

### [Installer] (Paket-Standard)

Datei-Kopierliste des Maschinenteils: Quelle → Ziel mit Flags (ALWAYS/OPTIONAL, DIRECTORY, WINDOWS64 …).

*Wann brauche ich das?* Immer im Paket-Standard – kopiert Setup.inf/Setup.ico in das Anwendungsverzeichnis (%App%\%SetupInfDir%).

```ini
[Installer]
1:%SetupInfDir%\Setup.inf, , ALWAYS, 0
```

*Referenz: Kap. 8 – Installer*

### [Product] (Paket-Standard)

Das Hauptprogramm: Einstiegspunkt der Ablaufsteuerung. #Aufrufe mit Flags (DONTDELETE/DELETE/MACHINE/CLIENT) regieren Install und Uninstall.

*Wann brauche ich das?* Immer – hier wird die Logik des Pakets orchestriert.

```ini
[Product]
#Set:Product, DONTDELETE
#Set:Deinstallation, DELETE
```

*Referenz: Kap. 3 – [Product], Kap. 5*

### [Set:<Name>] (Paket-Standard)

Benutzerdefinierte Ausführungssektion (Unterprogramm): Beflehe Dateien, MSI, Skripte; bei Uninstall laufen '-'-Zeilen rückwärts.

*Wann brauche ich das?* Für jeden logischen Schritt (Install, Deinstallation, Fehlerpfade, AppActive …).

```ini
[Set:Product]
AddMeter -1
CallHidden MsiExec /I "%Src%\Files\setup.msi" /qn
If %ErrorLevel% == "3010" Then "RebootRequired" EndIf
```

*Referenz: Kap. 3 – [Set:], Kap. 5*

### [Reg:<Name>] (Paket-Standard)

Registry-Sektion: schreibt Werte (Install), löscht sie bei Uninstall; '-'-Zeilen wirken umgekehrt (nur Uninstall).

*Wann brauche ich das?* Für HKLM/HKCU-Schreiber; Restore-Werte gehören in Reg:OnUninstall…

```ini
[Reg:Product]
HKLM,"Software\Hersteller\App","Version",0x00000000,2
```

*Referenz: Kap. 7 – Registry*

### [Reg:OnUninstall<Name>] (Paket-Standard)

Registry-Werte, die bei der Deinstallation gesetzt werden (Restore statt Löschen); Aufruf mit Flag DELETE.

*Wann brauche ich das?* Wenn ein Schlüssel beim Entfernen einen definierten Rücksetzwert erhalten soll.

```ini
[Reg:OnUninstallProduct]
HKLM,"Software\Hersteller\App","Version",0x00000000,1
```

*Referenz: Kap. 5 – Reg:OnUninstall*

### [Shell:<Name>] (Paket-Standard)

Verknüpfungen als kommaseparierte Felder (Ziel, Programm, Parameter, Icon …). Läuft bei Install automatisch zuletzt, bei Uninstall zuerst (ShellLinks=1).

*Wann brauche ich das?* Für Desktop-/Startmenü-Verknüpfungen; CommonShellLinks=1 für alle Benutzer.

```ini
[Shell:Product]
"%CommonDesktop%\DemoApp", "%ProgramFiles%\Demo\app.exe"
```

*Referenz: Kap. 9 – Verknüpfungen*

### [Ini:<Name>] (Paket-Standard)

INI-Datei-Einträge (Sektion/Schlüssel/Wert), die bei Uninstall zurückgenommen werden.

*Wann brauche ich das?* Für Alt-Applikationen mit INI-Konfiguration.

```ini
[Ini:Product]
```

*Referenz: Kap. 3 – [Ini:]*

### [Security:<Name>] (Paket-Standard)

NTFS-Berechtigungen auf Dateien/Registrierung; Abarbeitung unabhängig vom '-'-Präfix.

*Wann brauche ich das?* Wenn Ordner/Keys spezielle ACLs brauchen.

```ini
[Security:Product]
```

*Referenz: Kap. 3 – [Security:]*

### [RebootRequired] (Paket-Standard)

Sammelsektion für den Reboot-Pfad: SetReboot 1 nach ErrorLevel 3010 (und Rücknahme mit '-SetReboot 1').

*Wann brauche ich das?* Immer im Paket-Standard – Ziel der 3010-Verzweigung.

```ini
[RebootRequired]
SetReboot 1
-SetReboot 1
If %ErrorLevel% == "3010" Then "RebootRequired" EndIf
```

*Referenz: Kap. 11 – Reboot*

### [Bat:<Name>] (optional)

Erzeugt/ändert BAT-/Textdateien zeilenweise (Append-Stil).

*Wann brauche ich das?* Legacy-Hilfsmittel für Autoexec/Profile-Anpassungen.

```ini
[Bat:Config]
```

*Referenz: Kap. 3 – [Bat:]*

### [ODBC<Component>:<Name>] (optional)

ODBC-Datenquellen- und Treiber-Konfiguration.

*Wann brauche ich das?* Nur für Applikationen mit ODBC-Anbindung.

```ini
[ODBCDriver:App]
```

*Referenz: Kap. 3 – [ODBC…]*

### [Config.sys:<Name>] (optional)

Einträge für Config.sys (DOS-Ära; Wartung legacy).

*Wann brauche ich das?* Praktisch nicht mehr.

```ini
[Config.sys:Legacy]
```

*Referenz: Kap. 3 – [Config.sys:]*

### [IP<Component>:<Name>] (optional)

IP-/Netzwerkkomponenten-Konfiguration.

*Wann brauche ich das?* Spezialfall Netzwerkkomponenten.

```ini
[IPTcp:Cfg]
```

*Referenz: Kap. 3 – [IP…]*

### [[Admin]] (optional)

Installationsart Administrator: steuert Admin-Setup-Verhalten (Keys z. B. Reboot, InstallAtLast, AdminSetup).

*Wann brauche ich das?* Bei Admin-Installationen (/A-Varianten) mit abweichendem Verhalten.

```ini
[Admin]
Reboot=0
```

*Referenz: Erw. Referenz 26.1.0 – Installationsarten*

### [[Client]] (optional)

Installationsart Client (Benutzerteil-Konfiguration, ClientPath/AppPath-Logik).

*Wann brauche ich das?* Bei Admin-/Workstation-Setups mit Client-Anteil.

```ini
[Client]
```

*Referenz: Erw. Referenz 26.1.0 – Installationsarten*

### [[Workstation]] (optional)

Installationsart Workstation (Server-/Workstation-Paar von /AS//AW).

*Wann brauche ich das?* Bei Workstation-Installationen.

```ini
[Workstation]
```

*Referenz: Erw. Referenz 26.1.0 – Installationsarten*

### [[Prompts]] (optional)

Definition interaktiver Abfragen für den 'Prompt'-Befehl: Frage, Typ (z. B. JA/NEIN, EINGABE) und Default-Antwort; Silent-Schalter (/S…) übersteuern mit dem Default.

*Wann brauche ich das?* Wenn der Paketierer vor Installationsschritten interaktiv entscheiden lässt.

```ini
[Prompts]
RebootNow=Sofort neu starten?, JA/NEIN, NEIN
```

*Referenz: Erw. Referenz 26.1.0 – Prompt*

### [[Services]] (optional)

Dienstedefinition mit Win32-CreateService-Parametern: <Name>=<Anzeigename>,<Typ>,<Starttyp>,<Fehlerkontrolle>,<Ladegruppe>,<Abhängigkeiten ;getrennt>,<Konto>,<Passwort>[,<EventSource>][,<Startparameter>]. SERVICE_AUTO_START startet sofort.

*Wann brauche ich das?* Wenn eine EXE des Pakets als Windows-Dienst laufen soll (alternativ AddService-Befehl oder SERVICE-Copyflag).

```ini
[Services]
Svc1=Mein Dienst,0x10,2,1,,;HKLM\Software\MeinDienst,LocalSystem,,,MeinEventSource
```

*Referenz: Erw. Referenz 26.1.0 – Dienste*

### [[EventSources]] (optional)

Ereignisquellen für das Windows-Ereignisprotokoll (deklarative Alternative zum AddEventSource-Befehl).

*Wann brauche ich das?* Wenn die Anwendung EventLog-Einträge schreiben soll.

```ini
[EventSources]
1=MeineApp
```

*Referenz: Erw. Referenz 26.1.0 – EventSources*

### [[UserKeyNames]] (optional)

Zusätzliche Uninstall-Key-Namen, unter denen alte Installationen im Software-Register gesucht werden.

*Wann brauche ich das?* Bei Herstellerwechsel/umbenannten Paketen, um Altversionen sauber zu finden.

```ini
[UserKeyNames]
1=OldVendor\OldApp
```

*Referenz: Erw. Referenz 26.1.0 – UserKeyNames*

### [[OptionDependencies]] (optional)

Abhängigkeiten zwischen [Options]-Einträgen (Option A erfordert Option B).

*Wann brauche ich das?* Bei Mehr-Optionen-Paketen mit logischen Abhängigkeiten.

```ini
[OptionDependencies]
API=Core
```

*Referenz: Erw. Referenz 26.1.0 – Optionen*

### [[OptionGroups]] (optional)

Gruppierung von Optionen im Optionsdialog des Setup-Assistenten.

*Wann brauche ich das?* Bei vielen Optionen für übersichtliche Dialoge.

```ini
[OptionGroups]
```

*Referenz: Erw. Referenz 26.1.0 – Optionen*

### [[Icons]] (optional)

Icon-Definitionen (Datei, Index, Transparenzfarbe) für den Setup-Assistenten; feldverifiziert im Agent-Paket 2604.2.2: 'Product = <Datei>, <Index>, <Transparenz>, ICON'.

*Wann brauche ich das?* Für eigenes Branding des Assistenten.

```ini
[Icons]
Product = %Src%\Files\app.ico, 0, 0xFF00FF, ICON
```

*Referenz: Erw. Referenz 26.1.0 – Icons*

### [[%Option%]] (optional)

Gemeinsame Sektion für WILDCARD-Optionen: Der Platzhalter [%Option%] wird für jede gewählte Option ausgeführt; einzelne Optionen können zusätzlich eigene Sektionen [<Optionsname>] haben.

*Wann brauche ich das?* Bei vielen Optionen mit gemeinsamer Grundlogik.

```ini
[%Option%]
Echo Verarbeite Option %Option%
```

*Referenz: Erw. Referenz 26.1.0 – Optionen*

### [Win.ini:<Name>] (optional)

Historische typisierte Sektion für Win.ini-Einträge.

*Wann brauche ich das?* Legacy (16-Bit-Ära).

```ini
[Win.ini:Legacy]
```

*Referenz: Kap. 3 – typisierte Sektionen*

### [System.ini:<Name>] (optional)

Historische typisierte Sektion für System.ini-Einträge.

*Wann brauche ich das?* Legacy (16-Bit-Ära).

```ini
[System.ini:Legacy]
```

*Referenz: Kap. 3 – typisierte Sektionen*

### [Autoexec.bat:<Name>] (optional)

Historische typisierte Sektion für Autoexec.bat-Anpassungen.

*Wann brauche ich das?* Legacy (DOS-Ära).

```ini
[Autoexec.bat:Legacy]
```

*Referenz: Kap. 3 – typisierte Sektionen*

## Befehls-Referenz

### AddMeter

```
AddMeter <Wert>  ·  -AddMeter <Wert>
```

Steuert oder reserviert Zeilen im Fortschrittsbalken des Empirum Setup-Assistenten. Der Standardaufruf 'AddMeter -1' reserviert im Maschinenteil einen Teilschritt für die Abarbeitung externer Installer (MSI, Unattended Setup), sodass der Balken während längerer Teilschritte nicht springt oder auf 0 % stehen bleibt.

*Uninstall-Verhalten:* Bekommt im Deinstallationspfad das Minuszeichen: '-AddMeter -1' (gibt den Teilschritt bei der Deinstallation wieder frei und hält den Fortschrittsbalken synchron).

```ini
[Product]

AddMeter -1

#Set:Product, DONTDELETE

#Set:Deinstallation, DELETE

-AddMeter -1
```

*Fallstricke & Best Practice:* Ohne 'AddMeter -1' springt der Fortschrittsbalken des UEM-Agenten oft unregelmäßig von 0 % direkt auf 100 %. 'AddMeter' ist primär im interaktiven/Fortschritts-Modus sichtbar, gehört aber als Best Practice fest in jeden Hauptablauf.

### Abort

```
Abort [<Fehlertext>]  ·  -Abort [<Fehlertext>]
```

Bricht die Paketverarbeitung sofort ab und meldet dem Empirum-Agenten den Status 'Failure' (Fehlgeschlagen). Trägt den optionalen Fehlertext ins lokale Setup-Log ein und stoppt die weitere Ausführung aller nachfolgenden Sektionen.

*Uninstall-Verhalten:* In Deinstallations-Fehlersektionen mit führendem Minus: '-Abort %ErrorText%'.

```ini
[Set:InstallationError]

ErrorLogMsg %ErrorLogMessage%

Abort %ErrorText%
```

*Fallstricke & Best Practice:* Niemals 'Abort' ohne vorheriges 'ErrorLogMsg' aufrufen! Während 'Abort' den Prozess stoppt, sorgt 'ErrorLogMsg' für den dauerhaften Eintrag im 'SetupErrorLog' des Empirum-Servers/Depots. Nach 'Abort' finden keine nachfolgenden Aufräumarbeiten statt.

### AskKillProcesses

```
AskKillProcesses <TimeoutInSekunden>, <ProzessAlias1>[, <ProzessAlias2> ...]
```

Zeigt dem interaktiv angemeldeten Benutzer einen Dialog mit Countdown, in dem er aufgefordert wird, die gelisteten blockierenden Prozesse (definiert in der Sektion [Processes]) selbst zu schließen. Nach Ablauf des Timeouts greift der dort definierte Modus ('KILLPROCESS CONTINUE' für erzwungenes Beenden oder 'KILLPROCESS ABORT' für Paketabbruch).

*Uninstall-Verhalten:* Mit führendem Minus für den Deinstallationslauf: '-AskKillProcesses 300, AppProc'.

```ini
[Processes]

AppProc = acroread.exe, Adobe Acrobat Reader, KILLPROCESS CONTINUE



[Set:Product]

AskKillProcesses 300, AppProc
```

*Fallstricke & Best Practice:* Da der Befehl eine Benutzerinteraktion darstellt, setzt er eine interaktive Sitzung voraus (/AW oder sichtbare Ausführung). Läuft das Paket rein silent als SYSTEM ohne angemeldeten Benutzer, kann der Dialog hängen oder das Timeout ungeprüft ablaufen. Bei 'KILLPROCESS CONTINUE' droht Datenverlust durch erzwungene Prozessbeendigung.

### Call

```
Call <Programm> [Parameter]  ·  -Call <Programm> [Parameter]
```

Führt ein externes Programm synchron mit sichtbarem Konsolen- bzw. Anwendungsfenster aus und blockiert die Setup.exe, bis der Prozess beendet ist. Weist nach Beendigung der Variablen %ErrorLevel% den Rückgabecode (Exit-Code) des Prozesses zu.

*Uninstall-Verhalten:* Mit führendem '-' für den Deinstallationspfad: '-Call "%App%\uninstall.exe" /S'.

```ini
Call "%Src%\Files\helper.exe" /arg1

If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf
```

*Fallstricke & Best Practice:* Öffnet ein sichtbares Konsolen-/Befehlsfenster, das Anwender irritieren kann! Für automatisierte Softwareverteilung im Depot ist fast immer 'CallHidden' die richtige Wahl. Pfade mit Leerzeichen müssen stets mit '"%...%"' gequotet werden.

### CallHidden

```
CallHidden <Programm> [Parameter]  ·  -CallHidden <Programm> [Parameter]
```

Startet ein externes Programm unsichtbar und synchron mit komplett verstecktem Konsolenfenster (SW_HIDE) und wartet auf dessen Beendigung. Weist %ErrorLevel% den Rückgabecode des aufgerufenen Prozesses zu. Der universelle Standard für MSI- (MsiExec.exe), Unattended-EXE- und PowerShell-/CMD-Aufrufe.

*Uninstall-Verhalten:* Mit '-' für Deinstallationsaufrufe: '-CallHidden MsiExec /X %V_ProductCode% /qn REBOOT=REALLYSUPPRESS'.

```ini
CallHidden MsiExec /I "%Src%\Files\setup.msi" ALLUSERS="1" REBOOT=REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn

If %ErrorLevel% == "3010" Then "RebootRequired" EndIf

If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf
```

*Fallstricke & Best Practice:* Pfade mit Leerzeichen zwingend in Anführungszeichen setzen! Unmittelbar nach dem Aufruf muss %ErrorLevel% geprüft werden, da nachfolgende Befehle den Returncode überschreiben. Bei MSI-Installationen sind 0 und 3010 (Reboot erforderlich) reguläre Erfolgs-Codes.

### Copy

```
Copy <Quelle>, <Ziel>[, Flags]  ·  -Copy <Quelle>, <Ziel>
```

Kopiert eine Datei zur Laufzeit von der Quelle zum Ziel. Unterstützt Empirum-Pfade wie %Src%, %App%, %ProgramFiles% oder %AppData%. Erweiterte Form (verifiziert, xcopy-artig): 'Copy <Quelle> <Ziel> [/S] [/D] [/EXCLUDE:<Datei>]' – /S rekursiv, /D nur neuere Dateien, /EXCLUDE schließt Muster aus.

*Uninstall-Verhalten:* Wird bei der Deinstallation automatisch rückgängig gemacht (Interpreter-Undo-Log); eine zusätzliche '-'-Spiegelzeile ist nicht nötig.

```ini
Copy "%Src%\Files\settings.json", "%App%\settings.json"
```

*Fallstricke & Best Practice:* Für das Ausrollen großer statischer Dateisammlungen ist die Sektion [Installer] vorzuziehen, da sie Prüfsummen, automatische Ordnererstellung und Paketkomprimierung bietet. Dateipfade immer quoten. Bei der erweiterten Form werden Argumente per Leerzeichen (nicht Komma) getrennt.

### Del

```
Del <Dateipfad>  ·  -Del <Dateipfad>
```

Löscht eine einzelne Datei dauerhaft vom Dateisystem.

*Uninstall-Verhalten:* Mit führendem '-': '-Del "%CommonDesktop%\App.lnk"' entfernt die Datei bei der Deinstallation.

```ini
Del "%Temp%\install_temp.log"

-Del "%CommonDesktop%\%ProductName%.lnk"
```

*Fallstricke & Best Practice:* Pfade immer in Anführungszeichen fassen ('"%Path%"'). 'Del' kann keine ganzen Ordnerbäume löschen – dafür ist 'DelTree' zuständig. Wildcards (*.*) sollten vermieden werden.

### DelTree

```
DelTree <Verzeichnispfad>  ·  -DelTree <Verzeichnispfad>
```

Löscht ein Verzeichnis rekursiv mit allen darin enthaltenen Dateien und Unterverzeichnissen. De-facto-Standard zur Bereinigung des Installationsverzeichnisses bei der Deinstallation.

*Uninstall-Verhalten:* Mit führendem Minus: '-DelTree "%App%"'.

```ini
-DelTree "%App%"

-DelTree "%CommonPrograms%\%DeveloperName%"
```

*Fallstricke & Best Practice:* NIEMALS mit abschließendem Backslash angeben (z. B. 'DelTree "%App%\"' erzeugt VAL-003, da die Empirum-Engine den Backslash oft als Syntaxfehler interpretiert)! Niemals auf Stammordner wie %ProgramFiles%, C:\ oder Systemordner anwenden (VAL-007).

### Echo

```
Echo <Text>  ·  -Echo <Text>
```

Schreibt eine Textzeile in die Protokolldatei der Installation zur Statuskontrolle und Diagnose im Empirum Management Center.

*Uninstall-Verhalten:* Mit '-' für Meldungen im Deinstallationslauf: '-Echo Deinstallation von %ProductName% beendet'.

```ini
Echo [Setup] Starte Installation von %ProductName% %Version%...
```

*Fallstricke & Best Practice:* 'Echo' setzt keine Fehlercodes zurück und ersetzt keine strukturierte Fehlerbehandlung mit 'ErrorLogMsg' und 'Abort'.

### EndIf

```
If <Bedingung> Then "<Sektion>" [Else "<Sektion>"] EndIf
```

Terminiert die einzeilige Empirum If-Kontrollstruktur. In der Setup.inf-Spezifikation MUSS die gesamte Verzweigung in einer einzelnen Zeile formuliert sein.

*Uninstall-Verhalten:* Kontrollstrukturen erhalten kein '-'.

```ini
If %ErrorLevel% == "3010" Then "RebootRequired" EndIf
```

*Fallstricke & Best Practice:* Ein 'Then' ohne zugehöriges 'EndIf' in derselben Zeile ist ein fataler Syntaxfehler (VAL-020). Mehrzeilige If-Blöcke wie in Visual Basic oder PowerShell werden von Empirum nicht unterstützt!

### ErrorLogMsg

```
ErrorLogMsg <Meldung>  ·  -ErrorLogMsg <Meldung>
```

Protokolliert eine formatierte Fehlermeldung mit Fehlercode und Kontext im SetupErrorLog des Empirum-Systems. Bricht das Skript nicht selbstständig ab.

*Uninstall-Verhalten:* Mit '-' in Deinstallations-Fehlersektionen: '-ErrorLogMsg %ErrorLogMessage%'.

```ini
[Set:InstallationError]

ErrorLogMsg %ErrorLogMessage% (Returncode: %ErrorLevel%)

Abort %ErrorText%
```

*Fallstricke & Best Practice:* Immer in Kombination mit 'Abort' verwenden, um einen sichtbaren Paketfehler im Management Center zu erzeugen. Ohne 'Abort' läuft das Skript trotz protokollierter Fehlermeldung weiter.

### Exit

```
Exit
```

Beendet die Ausführung der aktuellen Sektion oder der gesamten Setup.inf vorzeitig mit Erfolgsstatus (Success).

*Uninstall-Verhalten:* Kontrollanweisung; erhält kein '-'.

```ini
[Set:CheckRequirements]

If DoesFileExist ("%App%\installed.flag") == "1" Then "Set:SkipAll" EndIf



[Set:SkipAll]

Echo Anwendung bereits vorhanden, überspringe...

Exit
```

*Fallstricke & Best Practice:* Wenn 'Exit' in einer per '#' aufgerufenen Sektion steht, bricht es die Ausführung ab. Bei unbedachtem Einsatz können nachfolgende Schritte in [Product] (z. B. Registry, Verknüpfungen) unbemerkt übersprungen werden.

### For

```
For <Variable>, <Start>, <Ende>[, <Schrittweite>], <Zielsektion>
```

Führt eine Zählschleife aus. In jedem Durchlauf wird die angegebene Zielsektion ausgeführt, wobei der Zähler über '%<Variable>%' (z. B. '%Counter%') abrufbar ist. Bei der Deinstallation führt die Setup.exe die Schleife automatisch rückwärts aus!

*Uninstall-Verhalten:* Bekommt kein '-'; die Setup.exe kehrt die Zählrichtung bei Deinstallation selbstständig von <Ende> nach <Start> um.

```ini
[Set:Installation]

For counter, 1, 5, , EchoCounter



[EchoCounter]

Echo Installation Schritt %Counter%

-Echo Deinstallation Schritt %Counter%
```

*Fallstricke & Best Practice:* Soll die Zählrichtung bei der Installation absteigend sein, muss eine negative Schrittweite angegeben werden ('For counter, 5, 1, -1, EchoCounter'). Keine komplex verschachtelten Schleifen bauen.

### If

```
If <Bedingung> Then "<Sektion>" [Else "<Sektion>"] EndIf
```

Bedingte Verzweigung zu benannten Untersektionen (GOSUB-Prinzip). Unterstützt Vergleiche von Variablen (%ErrorLevel% == "0") sowie Prädikatsfunktionen (DoesRegKeyExist(...) == "1", DoesFileExist(...) == "1"). Kehrt nach Beendigung der Zielsektion hinter das EndIf zurück.

*Uninstall-Verhalten:* Kontrollzeilen erhalten kein '-'.

```ini
If DoesRegKeyExist ("%RegUninstallKey%") == "1" Then "Set:Repair" Else "Set:Install" EndIf

If %ErrorLevel% == "3010" Then "RebootRequired" EndIf
```

*Fallstricke & Best Practice:* Hinter 'Then' und 'Else' dürfen AUSSCHLIESSLICH Sektionsnamen in Anführungszeichen stehen – keine Direktbefehle! Vergleichswerte müssen in Anführungszeichen stehen ("0", "1"). Funktionsprädikate selbst nicht zusätzlich in Anführungszeichen fassen (VAL-002).

### KillProcess

```
KillProcess <Prozessname>[, <Timeout>[, <Abfrage>]]  ·  -KillProcess <Prozessname>
```

Beendet sofort und ohne Rückfrage einen laufenden Windows-Prozess anhand seines Dateinamens (entspricht taskkill.exe /F /IM <Prozessname>). Erweiterte, dokumentierte Form: optionale Parameter <Timeout> (Sekunden warten) und <Abfrage>; im Prozessnamen sind Wildcards erlaubt.

*Uninstall-Verhalten:* Mit '-' bei Deinstallation: '-KillProcess app.exe'.

```ini
KillProcess acroread.exe

KillProcess app*.exe, 30, 1
```

*Fallstricke & Best Practice:* Harte Terminierung – Anwender verlieren ungespeicherte Daten. Für interaktive Applikationen ist 'AskKillProcesses' die empfohlene, anwenderfreundliche Alternative. Wildcards mit Bedacht einsetzen ('*' beendet alle passenden Prozesse!).

### MD

```
MD <Verzeichnispfad>
```

Erstellt ein Verzeichnis (Make Directory) inklusive aller notwendigen übergeordneten Ordnerstrukturen, falls diese noch nicht existieren. Lange Form: 'MkDir'.

*Uninstall-Verhalten:* Wird bei der Deinstallation automatisch rückgängig gemacht (Interpreter-Undo-Log, verifizierte Semantik) – eine '-MD'-Spiegelzeile ist nicht nötig.

```ini
MD "%ProgramData%\Vendor\AppName\Config"

MD "%App%\bin"
```

*Fallstricke & Best Practice:* Trailing-Backslashes sind bei 'MD' im Unterschied zu 'DelTree' unkritisch. Verzeichnisse, die über [Installer]/Copy-Flags (CASCADED) angelegt wurden, bereinigt ebenfalls der Uninstall-Lauf.

### Next

```
Next  (Schleifenende zu For …)
```

Schließt optional einen Schleifenblock ab, falls dieser mehrzeilig ohne Zielsektion formuliert wurde.

*Uninstall-Verhalten:* Ohne '-'.

```ini
For i, 1, 3, , StepSection



[StepSection]

Echo Schritt %i%
```

*Fallstricke & Best Practice:* Empirum-Best-Practice ist der Aufruf über eine Zielsektion ('For Var,1,5,,Sektion'). Ein unvollständiges oder unpassendes 'Next' führt zu Syntaxfehlern.

### ReplaceEnv

```
ReplaceEnv <Variablenname>  ·  -ReplaceEnv <Variablenname>
```

Expandiert den aktuellen Wert einer Variablen und löst indirekte Referenzen, Registry-Abfragen (%HKLM,...%) oder Maschinen-/Benutzerwerte (VM_*, VU_*) sofort auf.

*Uninstall-Verhalten:* Mit '-' für die Deinstallationsphase: '-ReplaceEnv MSIGUID_X64'.

```ini
Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%, x64)

ReplaceEnv MSIGUID_X64

If "%MSIGUID_X64%" != "" Then "Set:UninstallOld" EndIf
```

*Fallstricke & Best Practice:* Ohne 'ReplaceEnv' bleibt die Variable unaufgelöst und enthält den Literal-Ausdruck oder ist leer. Unbedingt nach 'Set' mit Funktions- oder Registry-Zuweisung ausführen!

### Set

```
Set <Variable> = <Wert/Ausdruck>  ·  -Set <Variable> = <Wert>
```

Weist einer Variablen einen Wert, einen Pfad, eine Umgebungsvariable oder das Ergebnis einer Funktion (z. B. GetUninstallKeyName) zu.

*Uninstall-Verhalten:* Mit '-': '-Set Variable = ...' für Deinstallationszuweisungen.

```ini
Set V_LogFile = %Temp%\Setup_%ProductName%.log

Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%, x64)

ReplaceEnv MSIGUID_X64
```

*Fallstricke & Best Practice:* Bei dynamischen Zuweisungen und Funktionen muss unmittelbar danach 'ReplaceEnv <Variable>' aufgerufen werden.

### SetReboot

```
SetReboot <Modus>  ·  -SetReboot <Modus>
```

Setzt eine kontrollierte Reboot-Anforderung für das Paket an die Empirum-Engine ('1' = Reboot anfordern). Standardziel für den Returncode 3010 nach MSI- und Treiber-Setups.

*Uninstall-Verhalten:* Mit '-': '-SetReboot 1' fordert einen Neustart nach der Deinstallation an.

```ini
[RebootRequired]

SetReboot 1

-SetReboot 1
```

*Fallstricke & Best Practice:* Niemals statisch 'Reboot=1' in [Application] setzen, wenn der Neustart nur im Bedarfsfall erforderlich ist (VAL-009). Stattdessen nach der Installation per 'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf' dynamisch 'SetReboot 1' triggern.

### Sleep

```
Sleep <Millisekunden>
```

Pausiert die Ausführung der Setup.exe für die angegebene Zeitspanne in Millisekunden (z. B. 'Sleep 3000' = 3 Sekunden). Typisch nach MSI-Installationen oder Deinstallationen, um dem System Zeit zum Freigeben von Dateihandles und Beenden von Hilfsprozessen zu geben.

*Uninstall-Verhalten:* Läuft in beiden Richtungen gleichermaßen; erhält kein '-'.

```ini
Sleep 3000
```

*Fallstricke & Best Practice:* Strikte Befehlssyntax: 'Sleep 3000' (Command-Style mit Leerzeichen), NICHT 'Sleep=3000' schreiben! Nicht als Ersatz für saubere Prozessprüfungen missbrauchen.

### CollapseEnv

```
CollapseEnv <Variable>
```

⚠ UNDOKUMENTIERT (Klasse 1): Wertet einen in der Variable gespeicherten Funktionsausdruck aus (verzögerte Auswertung). Top-Fund der Verifikation: voll funktionsfähig und von Matrix42 selbst in PSTBackupInfo.inf genutzt – Beispielkette: 'Set X=HexToString("%Reg%",1)' → 'CollapseEnv X' → Ergebnis.

*Uninstall-Verhalten:* Ohne '-'; Auswertungsphase.

```ini
Set X = HexToString ("%Reg%", 1)

CollapseEnv X
```

*Fallstricke & Best Practice:* Kein offizieller Support, kein Sicherheitsnetz. Nur einsetzen, wenn das Verhalten gegen den Zielinterpreter 26.1.0 verifiziert wurde.

### Extract

```
Extract <…>  (Parameter offen)
```

⚠ UNDOKUMENTIERT (Klasse 1): Entpackt Dateien aus der Setup.cab des Pakets. Befehlstabelle und 'Setup.cab'-String sind verifiziert; die genaue Parametersignatur ist ungeklärt.

*Uninstall-Verhalten:* Unbekannt.

```ini
; Parameter offen – nicht ohne Verifikation einsetzen
```

*Fallstricke & Best Practice:* Semantik offen: Es existiert keine dokumentierte Parameterliste. Setup.cab trägt die Sonderfall-Disknummer 0. Nicht generieren, nur manuell prüfen.

### RenDir

```
RenDir <Alt> <Neu>
```

⚠ UNDOKUMENTIERT (Klasse 1): Benennt ein Verzeichnis um (verifizierte Befehlstabelle, keine Doku).

*Uninstall-Verhalten:* Unbekannt (vermutlich analog Rename automatisch rückgängig).

```ini
RenDir "%App%\old" "%App%\new"
```

*Fallstricke & Best Practice:* Kein offizieller Support. Für dokumentierte Pfade 'Rename' für Dateien verwenden; Verzeichnisse besser über Kopie + DelTree abbilden.

### BlockInput

```
BlockInput <0|1>
```

⚠ UNDOKUMENTIERT (Klasse 1): Sperrt die Benutzereingabe als Befehlsform (1 = Sperre an, 0 = auf). Dokumentiert ist nur der [Setup]-Key BlockInput=; im Paket-User-Ordner existiert sogar eine BlockInput.exe.

*Uninstall-Verhalten:* Ohne '-'.

```ini
BlockInput 1

… kritische Schritte …

BlockInput 0
```

*Fallstricke & Best Practice:* Blockiert die Eingabe des angemeldeten Benutzers – bei Absturz zwischen an/aus bleibt die Sperre ggf. bestehen! Kein offizieller Support.

### AbortReboot

```
AbortReboot [<Text>]
```

Bricht die Paketverarbeitung ab und fordert zugleich einen Neustart an – Kombination aus Abort und Reboot-Anforderung für Fehlerfälle, die erst nach einem Neustart sauber wiederholbar sind.

*Uninstall-Verhalten:* Mit führendem '-' in Deinstallations-Fehlersektionen.

```ini
[Set:InstallationError]

ErrorLogMsg %ErrorLogMessage%

AbortReboot %ErrorText%
```

*Fallstricke & Best Practice:* Der Neustart wird auch im Fehlerfall gezogen – nachfolgende Aufräumschritte entfallen. Wie 'Abort' niemals ohne vorheriges 'ErrorLogMsg' verwenden.

### AbortSilent

```
AbortSilent [<Text>]
```

Bricht die Verarbeitung still (ohne Fehlerdialog) ab und schreibt LastError ins SwDepot-Log. Achtung, dokumentierte Sondersemantik: meldet dem Depot 'Success' und führt den Benutzerteil trotzdem aus!

*Uninstall-Verhalten:* Mit führendem '-' im Deinstallationspfad.

```ini
AbortSilent "Vorbedingung nicht erfüllt – Überspringe %ProductName%"
```

*Fallstricke & Best Practice:* Nicht für echte Fehler verwenden: Das Paket erscheint im Software-Depot als ERFOLGREICH, obwohl der Maschinenteil abgebrochen wurde. Nur für bewusstes, still Überspringen gedacht.

### AddEventSource

```
AddEventSource <Name>
```

Registriert eine Ereignisquelle im Windows-Ereignisprotokoll, damit die Anwendung Einträge unter Application/<Name> schreiben kann. Deklarative Alternative: Sektion [EventSources].

*Uninstall-Verhalten:* Erfolgt über die zugehörige Uninstall-Logik der [EventSources]-Sektion; als einzelner Befehl keine automatische Rücknahme.

```ini
AddEventSource "%ProductName%"
```

*Fallstricke & Best Practice:* Der Name muss zur MessageDLL/Registry der Anwendung passen, sonst schlägt das Schreiben von Ereignissen später fehl.

### AddMonitor

```
AddMonitor <Name>, <DLL>[, <Umgebung>]
```

Installiert einen Druckmonitor (Language Monitor) für den Druckspooler – Teil der Druckerverwaltungs-Befehlsfamilie (Legacy-Help Section 25).

*Uninstall-Verhalten:* Gegenstück 'DeleteMonitor' in der Deinstallationssektion aufrufen.

```ini
AddMonitor "MyMon", "mymon.dll"
```

*Fallstricke & Best Practice:* Nur für Treiberpakete mit eigenem Monitor nötig; die DLL muss bereits kopiert sein.

### AddPort

```
AddPort <Name>[, <Host>]  ·  -AddPort <Name>
```

Legt einen Druckport an (z. B. Local Port oder TCP/IP-Port) – Teil der Druckerverwaltungs-Befehlsfamilie.

*Uninstall-Verhalten:* Gegenstück 'DeletePort' in der Deinstallationssektion.

```ini
AddPort "LPT3:"
```

*Fallstricke & Best Practice:* Ports, die andere Drucker mitnutzen, dürfen bei Deinstallation nicht entfernt werden.

### AddPrinter

```
AddPrinter <Name>, <Treiber>, <Port>[, <Beschreibung>, …]  (16 Parameter, Legacy-Help Section 25)
```

Installiert einen Drucker mit Treiber, Port und Standardeinstellungen. Die vollständige 16-parametrige Signatur ist in der Legacy-Hilfe 'Drucker-Befehle' dokumentiert.

*Uninstall-Verhalten:* Mit '-' bzw. Gegenstück 'DeletePrinter' im Deinstallationspfad.

```ini
AddPrinter "Kassendrucker", "Generic / Text Only", "LPT1:"
```

*Fallstricke & Best Practice:* Treiber und Port müssen VOR dem Drucker existieren (AddPrinterDriver, AddPort). Reihenfolge in der Deinstallation exakt umgekehrt aufbauen.

### AddPrinterConnection

```
AddPrinterConnection \\<Server>\<Drucker>
```

Verbindet den aktuellen Benutzer mit einem freigegebenen Netzdrucker (per-user Verbindung).

*Uninstall-Verhalten:* Gegenstück 'DeletePrinterConnection' – typischerweise im Benutzerteil (/AW).

```ini
AddPrinterConnection "\\PRINT01\Etage1"
```

*Fallstricke & Best Practice:* Per-user-Verbindung: im Maschinenteil (SYSTEM) wirkungslos – CLIENT-Flag bzw. /AW nötig.

### AddPrinterDriver

```
AddPrinterDriver <Name>, <Umgebung>, <Pfad>[, …]
```

Installiert einen Druckertreiber in den Treiberspeicher (maschinenweit).

*Uninstall-Verhalten:* Gegenstück 'DeletePrinterDriver' in der Deinstallationssektion.

```ini
AddPrinterDriver "Generic / Text Only", "Windows x64", "%Src%\Driver"
```

*Fallstricke & Best Practice:* Architektur (Umgebung) muss zur Zielplattform passen; treiberalte Pakete benötigen ggf. beide Varianten (x86/x64).

### AddPrintProcessor

```
AddPrintProcessor <Name>, <DLL>[, <Umgebung>]
```

Registriert einen Druckprozessor (Render-Pipeline) für den Spooler.

*Uninstall-Verhalten:* Gegenstück 'DeletePrintProcessor'.

```ini
AddPrintProcessor "MyProc", "myproc.dll"
```

*Fallstricke & Best Practice:* Reines Spezialwerkzeug für Treiberpakete.

### AddPrintProvider

```
AddPrintProvider <Name>, <DLL>[, …]
```

Registriert einen Druckprovider (Port-Monitor-DLL des Spoolers).

*Uninstall-Verhalten:* Gegenstück 'DeletePrintProvider'.

```ini
AddPrintProvider "MyProv", "myprov.dll"
```

*Fallstricke & Best Practice:* Reines Spezialwerkzeug; Fehler hier legen den kompletten Spooler lahm.

### AddService

```
AddService <Parameter>  (CreateService-Parameter)
```

Legt einen Windows-Dienst an (Win32 CreateService-Parameter). Alternativen: Sektion [Services] oder das SERVICE-Copyflag in [Installer] – SERVICE_AUTO_START startet sofort.

*Uninstall-Verhalten:* Gegenstück 'DeleteService' in der Deinstallationssektion.

```ini
[Services]

Svc1=Mein Dienst,0x10,2,1,,;HKLM\Software\MeinDienst,,
```

*Fallstricke & Best Practice:* Dienstpasswörter ab Setup.inf-Version 6.5 nur verschlüsselt (EmpCrypt.exe). Bevorzugt [Services]-Sektion statt Einzelbefehl verwenden.

### Append

```
Append <Quelle> <Ziel>
```

Hängt den Inhalt der Quelldatei an die Zieldatei an (ohne die Zieldatei zu ersetzen).

*Uninstall-Verhalten:* Keine automatische Rücknahme – Rückbau ggf. über eigene Deinstallationslogik.

```ini
Append "%Src%\Files\add.cfg", "%App%\config.cfg"
```

*Fallstricke & Best Practice:* Zieldatei muss existieren; ansonsten vorher per Copy anlegen.

### Beep

```
Beep [0-4]
```

Gibt einen akustischen Signalton (Varianten 0–4) aus. Läuft als einer der wenigen Befehle IMMER auch bei der Deinstallation – auch ohne '-'.

*Uninstall-Verhalten:* Ohne '-' in beiden Richtungen aktiv (verifizierte Semantik).

```ini
Beep 1
```

*Fallstricke & Best Practice:* Bei silenten Verteilungen (/S0-/S1) ohne sichtbaren Dialog bleibt nur der Ton – überspringen oder abhängig vom Silent-Level verzweigen.

### CallRunAs

```
CallRunAs /U:<Konto> /P:<Passwort> "<Programm>" [Parameter]
```

Startet ein Programm wartend unter einem anderen Benutzerkonto (RunAs). Passwörter müssen ab Setup.inf-Version 6.5 Setup-verschlüsselt angegeben werden (EmpCrypt.exe).

*Uninstall-Verhalten:* Mit führendem '-' für Deinstallationsaufrufe.

```ini
CallRunAs /U:CORP\svcInstaller /P:<verschlüsselt> "%Src%\Files\agent.exe" /S
```

*Fallstricke & Best Practice:* Klartext-Passwörter werden ab INF-Version 6.5 abgelehnt. Konto braucht 'Log on as a batch job'-Rechte; Fehlercodes wie ErrorLevel auswerten.

### CallRunAsHidden

```
CallRunAsHidden /U:<Konto> /P:<Passwort> "<Programm>" [Parameter]
```

Wie 'CallRunAs', aber mit komplett verstecktem Fenster – Standard für automatisierte RunAs-Aufrufe im Softwarepaket.

*Uninstall-Verhalten:* Mit führendem '-' für Deinstallationsaufrufe.

```ini
CallRunAsHidden /U:CORP\svcInstaller /P:<verschlüsselt> "reg.exe" add …
```

*Fallstricke & Best Practice:* Gleiche Verschlüsselungspflicht wie CallRunAs; %ErrorLevel% unmittelbar danach prüfen.

### CD

```
CD <Pfad>  ·  ChDir <Pfad>
```

Wechselt das Arbeitsverzeichnis für nachfolgende Programmstarts (Call/CallHidden). Läuft IMMER auch bei der Deinstallation – auch ohne '-'.

*Uninstall-Verhalten:* Ohne '-' in beiden Richtungen aktiv (verifizierte Semantik).

```ini
CD "%TEMP%"
```

*Fallstricke & Best Practice:* Wirkt nur auf relative Pfade nachfolgender Aufrufe; absolute Pfade ignorieren das Arbeitsverzeichnis.

### ChDir

```
ChDir <Pfad>  ·  CD <Pfad>
```

Lange Form von 'CD': wechselt das Arbeitsverzeichnis. Läuft immer auch bei der Deinstallation – auch ohne '-'.

*Uninstall-Verhalten:* Ohne '-' in beiden Richtungen aktiv.

```ini
ChDir "%App%\bin"
```

*Fallstricke & Best Practice:* Siehe 'CD'.

### CloseWindow

```
CloseWindow <Titel>[, <Flags>[, <Timeout>[, <Prompt>]]]
```

Schließt ein Fenster anhand des Titels (Wildcards erlaubt). Flags: CLOSEWINDOW (freundlich), DESTROYWINDOW, QUERYCLOSEWINDOW (rückfragen) und KILLPROCESS, jeweils kombinierbar mit CONTINUE/ABORT für das weitere Verhalten.

*Uninstall-Verhalten:* Mit führendem '-' im Deinstallationspfad.

```ini
CloseWindow "Unbenannt - Editor*", QUERYCLOSEWINDOW, 30, 1
```

*Fallstricke & Best Practice:* Wildcards im Titel können fremde Fenster treffen; im Silent-Modus übernimmt der CONTINUE/ABORT-Modus die Entscheidung statt des Benutzers.

### DDE

```
DDE <…>
```

Historische DDE-Steuerung des Windows 3.x/9x-Program-Managers (Gruppen/Icons). Nur für Legacy-Pakete aus der Vor-NT-Ära relevant.

*Uninstall-Verhalten:* Keine Relevanz.

```ini
; nur Legacy
```

*Fallstricke & Best Practice:* In modernen Umgebungen nicht verwenden; funktioniert nicht mit dem Windows-95-Programm-Manager-losen Shells.

### Decrement

```
Decrement (<Variable>[, n])
```

Vermindert eine Variable um n (Standard 1). Arbeitet auch direkt auf Registry-Werten ('%HKLM,…%'-Notation) und INI-Werten ('%Datei,Sektion,Key%').

*Uninstall-Verhalten:* Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.

```ini
Decrement (Zaehler, 1)
```

*Fallstricke & Best Practice:* Nicht-numerische Inhalte führen zu Laufzeitfehlern; bei Registry-Zielen stellt Decrement sicher, dass der Wert numerisch ist.

### Divide

```
Divide (<Variable>, n)
```

Dividiert eine Variable durch n. Arbeitet auch direkt auf Registry- und INI-Werten.

*Uninstall-Verhalten:* Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.

```ini
Divide (GroesseKB, 1024)
```

*Fallstricke & Best Practice:* Division durch 0 bricht das Paket ab; Ergebnisse sind ganzzahlig.

### DeleteAllPrinters

```
DeleteAllPrinters
```

Entfernt alle auf dem System eingerichteten Drucker – radikales Gegenstück der Druckerfamilie, z. B. für kioskartige Setups.

*Uninstall-Verhalten:* Nur in Deinstallations-/Aufräum-Szenarien verwenden.

```ini
-DeleteAllPrinters
```

*Fallstricke & Best Practice:* Entfernt auch nutzerdefinierte und Netzdrucker – in normalen Paketen DURCHAUS tabu!

### DeleteMonitor

```
DeleteMonitor <Name>[, <Umgebung>]
```

Entfernt einen Druckmonitor – Gegenstück zu 'AddMonitor'.

*Uninstall-Verhalten:* Typischerweise mit '-' in der Deinstallationssektion.

```ini
-DeleteMonitor "MyMon"
```

*Fallstricke & Best Practice:* Nur entfernen, wenn kein Drucker den Monitor mehr nutzt.

### DeletePort

```
DeletePort <Name>
```

Entfernt einen Druckport – Gegenstück zu 'AddPort'.

*Uninstall-Verhalten:* Typischerweise mit '-' in der Deinstallationssektion.

```ini
-DeletePort "LPT3:"
```

*Fallstricke & Best Practice:* Standardports (LPT1:, COM1:, FILE:) dürfen nie gelöscht werden.

### DeletePrinter

```
DeletePrinter <Name>
```

Entfernt einen Drucker – Gegenstück zu 'AddPrinter'.

*Uninstall-Verhalten:* Typischerweise mit '-' in der Deinstallationssektion.

```ini
-DeletePrinter "Kassendrucker"
```

*Fallstricke & Best Practice:* Zuerst Drucker, dann Treiber, dann Ports/Monitore löschen (umgekehrte Installationsreihenfolge).

### DeletePrinterConnection

```
DeletePrinterConnection \\<Server>\<Drucker>
```

Entfernt eine per-user Netzdrucker-Verbindung – Gegenstück zu 'AddPrinterConnection'.

*Uninstall-Verhalten:* Im Benutzerteil (/AW) der Deinstallation.

```ini
-DeletePrinterConnection "\\PRINT01\Etage1"
```

*Fallstricke & Best Practice:* Per-user-Operation – im Maschinenteil wirkungslos.

### DeletePrinterDriver

```
DeletePrinterDriver <Name>[, <Umgebung>]
```

Entfernt einen Druckertreiber – Gegenstück zu 'AddPrinterDriver'.

*Uninstall-Verhalten:* Typischerweise mit '-' in der Deinstallationssektion.

```ini
-DeletePrinterDriver "Generic / Text Only"
```

*Fallstricke & Best Practice:* Treiber, die noch von anderen Druckern verwendet werden, lassen sich nicht entfernen.

### DeletePrintProcessor

```
DeletePrintProcessor <Name>[, <Umgebung>]
```

Entfernt einen Druckprozessor – Gegenstück zu 'AddPrintProcessor'.

*Uninstall-Verhalten:* Typischerweise mit '-' in der Deinstallationssektion.

```ini
-DeletePrintProcessor "MyProc"
```

*Fallstricke & Best Practice:* Nur entfernen, wenn kein Drucker den Prozessor mehr referenziert.

### DeletePrintProvider

```
DeletePrintProvider <Name>
```

Entfernt einen Druckprovider – Gegenstück zu 'AddPrintProvider'.

*Uninstall-Verhalten:* Typischerweise mit '-' in der Deinstallationssektion.

```ini
-DeletePrintProvider "MyProv"
```

*Fallstricke & Best Practice:* Falsche Reihenfolge kann den Spooler-Dienst blockieren.

### DeleteService

```
DeleteService <Dienstname>
```

Entfernt einen Windows-Dienst – Gegenstück zu 'AddService' bzw. der [Services]-Sektion.

*Uninstall-Verhalten:* Typischerweise mit '-' in der Deinstallationssektion.

```ini
-DeleteService "MeinDienst"
```

*Fallstricke & Best Practice:* Läuft der Dienst noch, vorher 'StopService' aufrufen (oder Stop dependenter Dienste).

### DeleteXml

```
DeleteXml (<Datei>, <XPath>)
```

Löscht XML-Knoten, die dem XPath-Ausdruck entsprechen, in der Datei.

*Uninstall-Verhalten:* Keine automatische Rücknahme – Original ggf. vorher sichern.

```ini
DeleteXml ("%App%\config.xml", "/Konfiguration/Altlasten/*")
```

*Fallstricke & Best Practice:* XPath präzise fassen – zu breite Ausdrücke löschen mehr als beabsichtigt.

### Erase

```
Erase <Dateipfad>  ·  -Erase <Dateipfad>
```

Alias für 'Del' – löscht eine einzelne Datei.

*Uninstall-Verhalten:* Wie 'Del' mit führendem '-'.

```ini
Erase "%Temp%\install_temp.log"
```

*Fallstricke & Best Practice:* In neuen Paketen die kurze Standardform 'Del' bevorzugen.

### EmptyClipboard

```
EmptyClipboard
```

Leert die Windows-Zwischenablage komplett.

*Uninstall-Verhalten:* Keine Rücknahme nötig/sinnvoll.

```ini
EmptyClipboard
```

*Fallstricke & Best Practice:* Vernichtet ungefragt Benutzerdaten in der Zwischenablage – nur in begründeten Sicherheits-/Kiosk-Szenarien einsetzen.

### Increment

```
Increment (<Variable>[, n])
```

Erhöht eine Variable um n (Standard 1). Arbeitet auch direkt auf Registry-Werten ('%HKLM,…%'-Notation) und INI-Werten.

*Uninstall-Verhalten:* Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.

```ini
Increment (Zaehler)
```

*Fallstricke & Best Practice:* Nicht-numerische Werte führen zu Laufzeitfehlern.

### Multiply

```
Multiply (<Variable>, n)
```

Multipliziert eine Variable mit n. Arbeitet auch direkt auf Registry- und INI-Werten.

*Uninstall-Verhalten:* Ohne '-' nur Installation; Spiegelung bei Bedarf mit '-'.

```ini
Multiply (GroesseMB, 1024)
```

*Fallstricke & Best Practice:* Ganzzahlüberläufe bei großen Werten beachten (32-Bit-Bereich).

### MkDir

```
MkDir <Verzeichnispfad>
```

Lange Form von 'MD': erstellt ein Verzeichnis inklusive übergeordneter Strukturen.

*Uninstall-Verhalten:* Wie 'MD' – automatische Rücknahme über den Interpreter-Undo-Log.

```ini
MkDir "%App%\logs"
```

*Fallstricke & Best Practice:* Siehe 'MD'.

### PlaySound

```
PlaySound <Disk>, <Name>, <Flags>
```

Spielt eine Sounddatei aus dem Paket ab (z. B. während des Begrüßungsdialogs).

*Uninstall-Verhalten:* Ohne Bedeutung für die Deinstallation.

```ini
PlaySound 1, "intro.wav", 0
```

*Fallstricke & Best Practice:* Bei silent Verteilung ohne Audiosession wirkungslos; Datei muss über [Installer] mitkopiert werden.

### Prompt

```
Prompt <Variable>
```

Stellt die in [Prompts] definierte interaktive Abfrage und speichert die Antwort in der Variablen. Wird von Silent-Schaltern (/S…) übersteuert – dann greift der dort definierte Default.

*Uninstall-Verhalten:* Ohne '-'; typischerweise nur im Installationsteil sinnvoll.

```ini
[Prompts]

RebootNow=Sofort neu starten?, JA/NEIN, JA



[Set:Product]

Prompt RebootNow
```

*Fallstricke & Best Practice:* In silenten Paketen (/S0–/S2) erscheint kein Dialog – Antworlogik muss den Default sauber behandeln (VAL-028).

### RD

```
RD <Verzeichnispfad>  ·  RmDir <Verzeichnispfad>
```

Entfernt ein VERZEICHNIS, das LEER sein muss (Remove Directory) – im Unterschied zu 'DelTree', das rekursiv löscht.

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad.

```ini
-RD "%App%\empty_sub"
```

*Fallstricke & Best Practice:* Bei nicht-leerem Verzeichnis schlägt der Befehl still fehl – vorher Contents prüfen bzw. '-DelTree' verwenden.

### RmDir

```
RmDir <Verzeichnispfad>
```

Lange Form von 'RD': entfernt ein leeres Verzeichnis.

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad.

```ini
-RmDir "%App%\empty_sub"
```

*Fallstricke & Best Practice:* Siehe 'RD'.

### RegAsm

```
RegAsm <Assembly> [Optionen]
```

Registriert eine .NET-Assembly (RegAsm) – für COM-Interop-Pakete, die keine regasm.exe-Zeile über CallHidden callsen wollen.

*Uninstall-Verhalten:* Mit '-' bzw. '/u'-Option im Deinstallationspfad.

```ini
RegAsm "%App%\bin\MeineLib.dll" /codebase
```

*Fallstricke & Best Practice:* /codebase erzeugt Versionskonflikte bei parallelen Installationen; %ErrorLevel% prüfen.

### Rem

```
Rem <Kommentar>
```

Kommentar als eigener Befehl – wird protokolliert und läuft (anders als ';'-Kommentare) IMMER auch bei der Deinstallation.

*Uninstall-Verhalten:* Ohne '-' in beiden Richtungen aktiv (verifizierte Semantik).

```ini
Rem Maschinenteil gestartet um %SysDate% %SysTime%
```

*Fallstricke & Best Practice:* Für reine Quelltext-Kommentare ';'-Zeilen bevorzugen (erscheinen nicht im Log).

### Rename

```
Rename <Quelle> <Ziel>  ·  Ren <Quelle> <Ziel>
```

Benennt eine Datei um. Wird bei der Deinstallation automatisch rückgängig gemacht (Interpreter-Undo-Log) – keine '-Ren'-Spiegelzeile nötig.

*Uninstall-Verhalten:* Automatische Rücknahme durch den Interpreter.

```ini
Rename "%App%\config.neu" "%App%\config.xml"
```

*Fallstricke & Best Practice:* Nur gleiche Partition/Ordnerlogik; Ziel darf nicht existieren.

### Ren

```
Ren <Quelle> <Ziel>
```

Kurzform von 'Rename': benennt eine Datei um; automatische Rücknahme bei /U.

*Uninstall-Verhalten:* Automatische Rücknahme durch den Interpreter.

```ini
Ren "%App%\config.neu" "%App%\config.xml"
```

*Fallstricke & Best Practice:* Siehe 'Rename'.

### ReplaceRegValue

```
ReplaceRegValue (<Root>, "<Key>", "<Wert>", "<Suche>", "<Ersetze>", n)
```

Suchen/Ersetzen innerhalb eines Registry-Wertes; n = n-tes Vorkommen oder alle.

*Uninstall-Verhalten:* Ohne automatische Rücknahme – Originalwert ggf. vorher sichern.

```ini
ReplaceRegValue (HKLM, "Software\Vendor\App", "Path", "C:\Old", "%App%", 0)
```

*Fallstricke & Best Practice:* Ersetzungen in REG_SZ/EXPAND_SZ-Werten; n=0 ersetzt alle Vorkommen.

### ReplaceTextFile

```
ReplaceTextFile ("<Datei>", "<Suche>", "<Ersetze>", n)
```

Suchen/Ersetzen in einer Textdatei; n = n-tes Vorkommen oder alle (0). Auch als Funktion außerhalb [Requirements] nutzbar.

*Uninstall-Verhalten:* Ohne automatische Rücknahme – Original ggf. vorher sichern.

```ini
ReplaceTextFile ("%App%\app.ini", "SERVER=old", "SERVER=new", 0)
```

*Fallstricke & Best Practice:* Kein Regex – exakte String-Suche; Zeichencodierung der Datei beachten (ANSI).

### ReplaceVars

```
ReplaceVars <Datei>
```

Löst %Variablen% in der angegebenen Datei in-place auf (nützlich für Konfig-Templates aus dem Paket).

*Uninstall-Verhalten:* Ohne automatische Rücknahme.

```ini
ReplaceVars "%App%\config.template"
```

*Fallstricke & Best Practice:* Die Ersetzung ist endgültig – Originaltemplate separat mitkopieren, wenn es mehrfach gebraucht wird.

### ReadXmlNode

```
ReadXmlNode (<Datei>, <XPath>)
```

Liest einen XML-Knoten in die Zielvariable – reine Leseoperation für Set-Zuweisungen.

*Uninstall-Verhalten:* Ohne Rücknahmebedarf.

```ini
Set Version = ReadXmlNode ("%App%\config.xml", "/Konfiguration/Version/@value")

ReplaceEnv Version
```

*Fallstricke & Best Practice:* Wie alle dynamischen Lesezugriffe anschließend 'ReplaceEnv <Var>' aufrufen.

### ReadXmlText

```
ReadXmlText (<Datei>, <XPath>)
```

Liest den Textinhalt eines XML-Knotens in die Zielvariable.

*Uninstall-Verhalten:* Ohne Rücknahmebedarf.

```ini
Set Host = ReadXmlText ("%App%\config.xml", "/Konfiguration/Host")

ReplaceEnv Host
```

*Fallstricke & Best Practice:* Siehe 'ReadXmlNode'.

### UpdateXml

```
UpdateXml (<Datei>, <XPath>, <Wert>[, …])
```

Aktualisiert oder erzeugt XML-Knoten/Werte in der Datei.

*Uninstall-Verhalten:* Keine automatische Rücknahme – Original ggf. vorher sichern.

```ini
UpdateXml ("%App%\config.xml", "/Konfiguration/Version/@value", "2.0")
```

*Fallstricke & Best Practice:* XPath präzise fassen; Namensräume beachten.

### ShowPicture

```
ShowPicture <Disk>, <Datei>, <X>, <Y>
```

Zeigt ein Bild aus dem Paket an fester Position an (z. B. während der Installation).

*Uninstall-Verhalten:* Ohne Bedeutung für die Deinstallation.

```ini
ShowPicture 1, "branding.bmp", 100, 100
```

*Fallstricke & Best Practice:* Bei silent Verteilung nicht sichtbar; Datei über [Installer] mitkopieren.

### SplashDialogOn

```
SplashDialogOn <X>, <Y>, <Breite>, <Höhe>
```

Öffnet einen schemalosen Splash-Dialog an fester Position (z. B. für Statusmeldungen während langer Installationsphasen).

*Uninstall-Verhalten:* Ohne '-'; UI-Befehl.

```ini
SplashDialogOn 200, 200, 400, 120
```

*Fallstricke & Best Practice:* Immer 'SplashDialogOff' erreichen (auch im Fehlerpfad), sonst bleibt der Dialog stehen.

### SplashDialogText

```
SplashDialogText <Text>
```

Setzt/aktualisiert den Text des geöffneten Splash-Dialogs.

*Uninstall-Verhalten:* Ohne '-'; UI-Befehl.

```ini
SplashDialogText Kopiere Dateien …
```

*Fallstricke & Best Practice:* Wirkt nur zwischen SplashDialogOn und SplashDialogOff.

### SplashDialogOff

```
SplashDialogOff
```

Schließt den Splash-Dialog.

*Uninstall-Verhalten:* Ohne '-'; UI-Befehl.

```ini
SplashDialogOff
```

*Fallstricke & Best Practice:* Auch in Fehlersektionen aufrufen, damit der Dialog nicht stehen bleibt.

### StartService

```
StartService <Dienstname>
```

Startet einen (installierten) Windows-Dienst – z. B. nach Konfigurationsänderungen.

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad, wenn der Dienst vor dem Entfernen zu stoppen ist (hierfür eigentlich 'StopService').

```ini
StartService "MeinDienst"
```

*Fallstricke & Best Practice:* Startet nur installierte Dienste; nach 'AddService' bzw. SERVICE-Copyflag verwenden.

### StopService

```
StopService <Dienstname>
```

Stoppt einen laufenden Windows-Dienst – z. B. vor Dateiupdates oder 'DeleteService'.

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad vor 'DeleteService'.

```ini
-StopService "MeinDienst"
```

*Fallstricke & Best Practice:* Dependente Dienste zuerst stoppen; manche Dienste benötigen Timeout.

### SystemShutdown

```
SystemShutdown <Text>, <Reboot>, <Force>, <Timeout>, <Async>
```

Fährt das System kontrolliert herunter oder startet neu (1=Reboot, 0=Shutdown; Force beendet Prozesse erzwungen; Timeout=Countdown in Sekunden, -1 ohne sichtbaren Countdown; Async=1 kehrt sofort zurück). Feldverifikation aus dem Matrix42-Agent-Paket: '%ShutdownTextDesc%, 1, 0, -1, 1' (User-Kontext) bzw. '…, 1, 0, 15, 1' (kein User, 15 s).

*Uninstall-Verhalten:* Ohne '-'; Systembefehl.

```ini
SystemShutdown %ShutdownTextDesc%, 1, 0, -1, 1
```

*Fallstricke & Best Practice:* Nachfolgende Setup.inf-Zeilen laufen bei Sync/=0 nicht mehr; Force verwirft ungespeicherte Daten. Für Reboot nach Paketende bevorzugt 'SetReboot 1' verwenden!

### Unrar

```
Unrar ("<Archiv>", "<Ziel>", ["<Maske>"], ["<Passwort>"])
```

Entpackt ein RAR-Archiv in das Zielverzeichnis (UnRAR.dll/UnRAR64.dll aus dem User-Ordner des Pakets; Modulpfad-Logik). Maske und Passwort optional.

*Uninstall-Verhalten:* Ohne automatische Rücknahme – Ziele ggf. per '-DelTree' bereinigen.

```ini
Unrar ("%Src%\Files\data.rar", "%App%\data")
```

*Fallstricke & Best Practice:* Passwörter ab INF-Version 6.5 Setup-verschlüsselt (EmpCrypt); Ziele vorher per MD anlegen.

### Unzip

```
Unzip ("<Zip>", "<Ziel>", ["<Maske>"], ["<Passwort>"])
```

Entpackt ein ZIP-Archiv in das Zielverzeichnis; Maske (z. B. '*.xml') und Passwort optional.

*Uninstall-Verhalten:* Ohne automatische Rücknahme – Ziele ggf. per '-DelTree' bereinigen.

```ini
Unzip ("%Src%\Files\config.zip", "%App%\config", "*.xml")
```

*Fallstricke & Best Practice:* Zielverzeichnis vorher per MD anlegen; %ErrorLevel% prüfen.

### WaitUntilFileExists

```
WaitUntilFileExists "<Datei>"[, <Timeout>]  ·  -WaitUntilFileExists …
```

Wartet, bis die Datei existiert (Polling), maximal bis zum optionalen Timeout (Sekunden) – z. B. auf Ausgabedateien gestarteter Prozesse.

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad.

```ini
WaitUntilFileExists "%Temp%\setup_done.flag", 120
```

*Fallstricke & Best Practice:* Ohne Timeout wartet der Befehl endlos – immer Timeout angeben.

### WaitUntilProcessExists

```
WaitUntilProcessExists <Prozessname>[, <Timeout>]
```

Wartet, bis der Prozess läuft – z. B. bis ein per 'Run'-Ersatz gestarteter Agent einsatzbereit ist.

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad.

```ini
WaitUntilProcessExists "agent.exe", 60
```

*Fallstricke & Best Practice:* Prüft nur Prozessexistenz, nicht Einsatzbereitschaft (Ports/Dienste) – ggf. zusätzlich 'WaitUntilRegKeyExists' nutzen.

### WaitUntilRegKeyExists

```
WaitUntilRegKeyExists "<Root>,<Key>[,<Wert>]"[, <Timeout>]
```

Wartet, bis der Registry-Schlüssel/Wert existiert. Das Argument MUSS in Anführungszeichen stehen, da die Komponenten selbst kommagetrennt sind!

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad.

```ini
WaitUntilRegKeyExists "HKLM,SOFTWARE\Vendor\App,Ready", 90
```

*Fallstricke & Best Practice:* Quotes sind Pflicht (Kommata im Argument); Timeout immer angeben.

### WaitWhileProcessExists

```
WaitWhileProcessExists <Prozessname>[, <Timeout>]
```

Wartet, bis der Prozess ENDET – typisch vor Deinstallation/Update, z. B. nach 'AskKillProcesses' als Sanft-Pendant.

*Uninstall-Verhalten:* Mit '-' im Deinstallationspfad.

```ini
WaitWhileProcessExists "app.exe", 120
```

*Fallstricke & Best Practice:* Ohne Timeout endloses Warten; bei Timeout weiterlaufen lassen und Ergebnis prüfen.

## Prädikate (If-Bedingungen)

### DoesRegKeyExist

```
DoesRegKeyExist ("<Root>,<SubKey>[,<ValueName>]")
```

Prüft, ob ein Registry-Schlüssel oder ein optional angegebener Wert existiert; liefert '1' (ja/vorhanden) oder '0' (nein/nicht vorhanden). Kanonisches Standardprädikat der Referenz. Die ValueName-Komponente macht es zum Nachfolger der früher dokumentierten Wert-Abfrage.

```ini
If DoesRegKeyExist ("%RegUninstallKey%") == "1" Then "Set:Repair" Else "Set:Install" EndIf
```

*Fallstricke & Best Practice:* Argument in Klammern zwingend in Anführungszeichen setzen (die Komma-Komponenten erfordern den umschließenden String). Ergebnis immer mit '"1"' oder '"0"' vergleichen – niemals mit True/False oder unquoted 1.

### DoesFileExist

```
DoesFileExist ("<Dateipfad>")
```

Prüft die physische Dateiexistenz auf dem Dateisystem; liefert '1' wenn die Datei existiert, andernfalls '0'.

```ini
If DoesFileExist ("%App%\bin\app.exe") == "1" Then "Set:AlreadyInstalled" EndIf
```

*Fallstricke & Best Practice:* Dateipfad immer quoten. Hervorragend geeignet zur Erfolgskontrolle nach Installation oder Deinstallation (nicht nur auf %ErrorLevel% verlassen).

### DoesPathExist

```
DoesPathExist ("<Verzeichnispfad>")
```

Prüft, ob ein Verzeichnis auf dem Dateisystem existiert; liefert '1' oder '0'. Verifiziertes Gegenstück zur (nicht existierenden) älteren 'DoesDirExist'-Schreibweise.

```ini
If DoesPathExist ("%ProgramFiles%\Vendor\App") == "1" Then "Set:FolderFound" Else "Set:Install" EndIf
```

*Fallstricke & Best Practice:* Pfad in Anführungszeichen setzen; keine Wildcards übergeben. Für reine Dateiprüfungen 'DoesFileExist' verwenden.

### DoesProcessExist

```
DoesProcessExist ("<Prozessname.exe>")
```

Prüft zur Laufzeit, ob ein bestimmter Prozess im Windows-System aktiv läuft; liefert '1' wenn der Prozess aktiv ist, andernfalls '0'.

```ini
If DoesProcessExist ("outlook.exe") == "1" Then "Set:AppRunning" EndIf
```

*Fallstricke & Best Practice:* Prüft den reinen Prozessnamen. Für interaktive Benutzerdialoge mit Timeout-Countdown ist 'AskKillProcesses' vorzuziehen.

### DoesTextInFileExist

```
DoesTextInFileExist ("<Text>", "<Datei>")
```

Prüft, ob ein Text in einer Datei enthalten ist; liefert '1' oder '0'. Verifizierte Funktion der Interpreter-Funktionstabelle 26.1.0.

```ini
If DoesTextInFileExist ("LicenseOK", "%App%\config.ini") == "1" Then "Set:Licensed" EndIf
```

*Fallstricke & Best Practice:* Beide Argumente in Anführungszeichen setzen; für große Dateien ist der Check teuer – nicht in engen Schleifen einsetzen.

## Funktionen (Set-Zuweisung)

### GetUninstallKeyName

```
GetUninstallKeyName (%DisplayName%[,x64|x86])
```

Durchsucht dynamisch die Windows-Registry unter HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall (sowie WOW6432Node) nach dem angegebenen Anzeigenamen und ermittelt die zugehörige Uninstall-GUID oder den Schlüsselnamen – essenziell für robuste MSI-/EXE-Deinstallationen und Versions-Upgrades.

```ini
Set MSIGUID_X64 = GetUninstallKeyName (%V_DisplayName%,x64)

ReplaceEnv MSIGUID_X64

If "%MSIGUID_X64%" != "" Then "Set:UninstallOld" EndIf
```

*Fallstricke & Best Practice:* Zwingend unmittelbar danach 'ReplaceEnv <Variable>' aufrufen, sonst bleibt die Ergebnisvariable unaufgelöst! Auf 64-Bit-Systemen empfiehlt es sich, x64 und x86 abzufragen, falls ältere Versionen als 32-Bit installiert waren.

### Left

```
Left ("<String>", n)
```

Liefert die ersten n Zeichen des Strings.

```ini
Set Kurz = Left ("%ProductName%", 8)

ReplaceEnv Kurz
```

*Fallstricke & Best Practice:* Wie alle Stringfunktionen nur über Set + ReplaceEnv auswerten.

### Right

```
Right ("<String>", n)
```

Liefert die letzten n Zeichen des Strings.

```ini
Set Ext = Right ("%File%", 3)

ReplaceEnv Ext
```

*Fallstricke & Best Practice:* n größer als die Stringlänge liefert den ganzen String.

### Mid

```
Mid ("<String>", n1, n2)
```

Liefert n2 Zeichen ab Position n1 (1-basiert).

```ini
Set Teil = Mid ("%Version%", 1, 1)

ReplaceEnv Teil
```

*Fallstricke & Best Practice:* Position 1 ist das erste Zeichen (nicht 0).

### Len

```
Len ("<String>")
```

Liefert die Länge des Strings.

```ini
Set N = Len ("%ComputerName%")

ReplaceEnv N
```

*Fallstricke & Best Practice:* Leerstrings liefern 0; für Bedingungen in If-Zeilen direkt einsetzbar.

### Uppercase

```
Uppercase ("<String>")
```

Wandelt den String in Großbuchstaben.

```ini
Set Up = Uppercase ("%ComputerName%")

ReplaceEnv Up
```

*Fallstricke & Best Practice:* Nur ASCII-Wandlung – Umlaute prüfen.

### Lowercase

```
Lowercase ("<String>")
```

Wandelt den String in Kleinbuchstaben.

```ini
Set Low = Lowercase ("%User%")

ReplaceEnv Low
```

*Fallstricke & Best Practice:* Nur ASCII-Wandlung – Umlaute prüfen.

### RemoveFromLeft

```
RemoveFromLeft ("<String>", n)
```

Entfernt die ersten n Zeichen des Strings.

```ini
Set OhneLaufwerk = RemoveFromLeft ("%Path%", 3)

ReplaceEnv OhneLaufwerk
```

*Fallstricke & Best Practice:* Für Laufwerkpfade: 'C:\' sind 3 Zeichen.

### RemoveFromRight

```
RemoveFromRight ("<String>", n)
```

Entfernt die letzten n Zeichen des Strings.

```ini
Set Basis = RemoveFromRight ("%File%", 4)

ReplaceEnv Basis
```

*Fallstricke & Best Practice:* Dateiendungen inkl. Punkt zählen ('.exe' = 4 Zeichen).

### HexToString

```
HexToString ("<Hex>", [<Unicode>])
```

Wandelt Hex-Daten in einen String um (optional Unicode). Nur außerhalb [Requirements] verwendbar. Wird von Matrix42-eigenen INFs mit 'CollapseEnv' kombiniert.

```ini
Set X = HexToString ("%Reg%", 1)

CollapseEnv X
```

*Fallstricke & Best Practice:* In [Requirements]-Zeilen unzulässig; Ergebnis via ReplaceEnv/CollapseEnv auflösen.

### StringToHex

```
StringToHex ("<String>", [<Unicode>])
```

Wandelt einen String in Hex-Darstellung um. Nur außerhalb [Requirements].

```ini
Set Hx = StringToHex ("Wert")

ReplaceEnv Hx
```

*Fallstricke & Best Practice:* In [Requirements]-Zeilen unzulässig.

### GetIP

```
GetIP ()
```

Liefert die IP-Adresse des primären Netzwerkadapters.

```ini
Set IP = GetIP ()

ReplaceEnv IP
```

*Fallstricke & Best Practice:* Bei mehreren Adaptern primären Adapter prüfen; ohne Netzwerk leer.

### GetNIC

```
GetNIC ([<Index>])
```

Liefert Informationen zum (n-ten) Netzwerkadapter.

```ini
Set NIC0 = GetNIC (0)

ReplaceEnv NIC0
```

*Fallstricke & Best Practice:* Index außerhalb der Adapterliste liefert Leerstring.

### GetNICs

```
GetNICs ()
```

Liefert die Liste aller Netzwerkadapter. Nur außerhalb [Requirements].

```ini
Set Alle = GetNICs ()

ReplaceEnv Alle
```

*Fallstricke & Best Practice:* In [Requirements]-Zeilen unzulässig.

### GetDCName

```
GetDCName ()
```

Liefert den Namen des Domain Controllers der Anmeldedomäne.

```ini
Set DC = GetDCName ()

ReplaceEnv DC
```

*Fallstricke & Best Practice:* In Arbeitsgruppen ohne DC leer; Offline-Szenarien abfangen.

### GetDiskFreeSpace

```
GetDiskFreeSpace ("<Laufwerk>")
```

Liefert den freien Speicherplatz exakt – Achtung: korrekt nur bis ca. 2,1 GB (Legacy-32-Bit-Semantik).

```ini
Set Free = GetDiskFreeSpace ("C:")

ReplaceEnv Free
```

*Fallstricke & Best Practice:* Für moderne Platten 'GetDiskFreeSpaceKB' verwenden!

### GetDiskFreeSpaceKB

```
GetDiskFreeSpaceKB ("<Laufwerk>")
```

Liefert den freien Speicherplatz in Kilobytes – die zuverlässige Variante für moderne Datenträgergrößen.

```ini
If GetDiskFreeSpaceKB ("C:") < "1048576" Then "Set:NoSpace" EndIf
```

*Fallstricke & Best Practice:* Vor großen Kopieraktionen (Installer-Sektion) als Vorbedingung prüfen.

### GetDotNetPatchLevel

```
GetDotNetPatchLevel ("<Version>")
```

Liefert das höchste installierte Patch-Level der angegebenen .NET-Version.

```ini
Set PL = GetDotNetPatchLevel ("4.0.0.0")

ReplaceEnv PL
```

*Fallstricke & Best Practice:* Rückgabe 0, wenn die Basisversion fehlt.

### IsDotNetVersionAvailable

```
IsDotNetVersionAvailable ("<Version>")
```

Prüft, ob eine .NET-Runtime-Version verfügbar ist (Erkennung v1.0.3705 bis v4.8 Client/Full); liefert '1'/'0'.

```ini
If IsDotNetVersionAvailable ("4.8") == "0" Then "Set:InstallDotNet" EndIf
```

*Fallstricke & Best Practice:* Client- vs. Full-Profile unterscheiden; Version exakt angeben.

### BitAnd

```
BitAnd (<Bits>, <Maske>)
```

Bitweises UND – typisch für die Distribution-Flags des Setup-Assistenten: 1=INSTALL, 2=UPDATE, 4=FORCE, 8=UNINSTALL.

```ini
If BitAnd (%Distribution%, 8) == "8" Then "Set:UninstallPath" EndIf
```

*Fallstricke & Best Practice:* Distribution-Flags nur im Setup-Kontext gesetzt; Zahlen dezimal/numerisch vergleichen.

### BitOr

```
BitOr (<Bits>, <Maske>)
```

Bitweises ODER – kombiniert Flags zu einer Maske.

```ini
Set Mode = BitOr (1, 4)

ReplaceEnv Mode
```

*Fallstricke & Best Practice:* Ergebnis numerisch; für Vergleiche als Zahl behandeln.

### BitXOr

```
BitXOr (<Bits>, <Maske>)
```

Bitweises XOR – schaltet Flags um.

```ini
Set Toggle = BitXOr (%Mode%, 2)

ReplaceEnv Toggle
```

*Fallstricke & Best Practice:* Zweimalige Anwendung hebt die Umschaltung wieder auf.

### FileSize

```
FileSize ("<Datei>")
```

Liefert die Dateigröße in Bytes ('0' bei fehlender Datei) – auch als If-Funktion einsetzbar.

```ini
If FileSize ("%App%\app.exe") > "0" Then "Set:Installed" EndIf
```

*Fallstricke & Best Practice:* Fehlende Datei von 0-Byte-Datei semantisch nicht unterscheidbar – Existenz per DoesFileExist separat prüfen.

### FileVersion

```
FileVersion ("<Datei>"[, <Feld>])
```

Liefert die Dateiversion (ggf. einzelnes Feld: 1..4) einer PE-Datei – Standardwerkzeug für Installationsprüfungen.

```ini
If FileVersion ("%App%\bin\app.exe") < "2.0" Then "Set:Upgrade" EndIf
```

*Fallstricke & Best Practice:* Versionsvergleich: ab [Setup] Version=14.2 numerisch je Punkt-Segment, davor ziffernweise lexikalisch!

### ReadTextFile

```
ReadTextFile ("<Datei>")
```

Liest den kompletten Inhalt einer Textdatei als String ein (Leerstring, wenn die Datei fehlt; benötigt MSXML 6.0 auf dem Zielsystem).

```ini
Set Inhalt = ReadTextFile ("%App%\version.txt")

ReplaceEnv Inhalt
```

*Fallstricke & Best Practice:* Bei fehlender Datei KEIN Fehler, sondern Leerstring – Existenz separat prüfen; große Dateien sprengen Variablengrenzen.

### GetClipboardText

```
GetClipboardText ()
```

Liest den aktuellen Textinhalt der Windows-Zwischenablage.

```ini
Set Clip = GetClipboardText ()

ReplaceEnv Clip
```

*Fallstricke & Best Practice:* Nicht-Textinhalte liefern Leerstring; im SYSTEM-Kontext meist ohne Nutzen.

### Tokenize

```
Tokenize (<Variable>[, <Separator>])
```

Zerlegt den Wert einer Variablen anhand des Separators (Standard Komma) in indizierte Teilvariablen (%Var_1%, %Var_2%, …) und liefert die Anzahl – auch als If-Funktion nutzbar.

```ini
Set N = Tokenize (Liste, ";")

ReplaceEnv N
```

*Fallstricke & Best Practice:* Teilvariablen sind erst NACH ReplaceEnv verfügbar; Separator in Quotes übergeben.

## Variablen-Referenz (%...%)

### %App% (Verzeichnis)

Installations-Zielverzeichnis der Anwendung auf dem Zielclient. Vollständiges Synonym für %ApplicationDir%, gesteuert über [Application] ApplicationDir=.

*Typischer Wert / Pfad:* `C:\Program Files\Vendor\App`

```ini
CallHidden "%App%\bin\app.exe" /S

-DelTree "%App%"
```

*Fallstricke & Best Practice:* Niemals durch feste Pfade wie C:\Program Files ersetzen. Bei Deinstallation standardmäßig mit '-DelTree "%App%"' restlos bereinigen.

### %AppData% (Benutzerverzeichnis (Roaming))

Roaming-Anwendungsdatenverzeichnis des aktuell angemeldeten Benutzers (%APPDATA%).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming`

```ini
Copy "%Src%\Files\config.xml", "%AppData%\Vendor\config.xml"
```

*Fallstricke & Best Practice:* Nur im Benutzerteil (/AW, CLIENT-Flag) verlässlich verfügbar! Im Maschinenteil verweist die Variable auf das SYSTEM-Profil (C:\Windows\System32\config\systemprofile\...).

### %ApplicationDir% (Verzeichnis)

Definiertes Anwendungsverzeichnis aus [Application] ApplicationDir=. Basisdefinition für die Kurzform %App%.

*Typischer Wert / Pfad:* `C:\Program Files\%ProductName%`

```ini
[Application]

ApplicationDir=%ProgramFilesDir%\%ProductName%
```

*Fallstricke & Best Practice:* Wird in [Application] deklariert; im Ausführungsskript ist die kurze Form %App% der empfohlene Standard.

### %CommonAppData% (Systemverzeichnis (All Users))

Gemeinsames Anwendungsdaten-Verzeichnis für alle Benutzer des Systems (%ProgramData%).

*Typischer Wert / Pfad:* `C:\ProgramData`

```ini
MD "%CommonAppData%\%DeveloperName%\%ProductName%"

Copy "%Src%\Files\license.lic", "%CommonAppData%\%DeveloperName%\%ProductName%\license.lic"
```

*Fallstricke & Best Practice:* Standardbenutzer haben unter C:\ProgramData standardmäßig eingeschränkte Schreibrechte. Falls Anwender Konfigurationen modifizieren müssen, Schreibrechte in [Security:Product] vergeben.

### %CommonDesktop% (Verknüpfung / Desktop)

Öffentlicher Desktop-Ordner aller Benutzer ('Public Desktop'). Hier abgelegte Verknüpfungen sind für jeden angemeldeten Benutzer auf dem Desktop sichtbar.

*Typischer Wert / Pfad:* `C:\Users\Public\Desktop`

```ini
[Shell:Product]

"%CommonDesktop%\%ProductName%", "%App%\app.exe"
```

*Fallstricke & Best Practice:* Wird bei 'CommonShellLinks=1' automatisch als Desktop-Ziel verwendet. Bei Deinstallation mit '-Del "%CommonDesktop%\%ProductName%.lnk"' oder automatischer ShellLinks-Bereinigung entfernen.

### %CommonFilesDir% (Systemverzeichnis)

Verzeichnis für gemeinsam genutzte Programmdateien ('Common Files').

*Typischer Wert / Pfad:* `C:\Program Files\Common Files`

```ini
CommonSetupDir=%CommonFilesDir%\Setup%SetupBits%
```

*Fallstricke & Best Practice:* Architekturabhängig; zeigt auf 64-Bit-Systemen für 64-Bit-Prozesse auf C:\Program Files\Common Files, für 32-Bit-Prozesse auf C:\Program Files (x86)\Common Files.

### %CommonPrograms% (Verknüpfung / Startmenü)

Gemeinsamer Startmenü-Ordner 'Programme' für alle Benutzer ('All Users Start Menu').

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs`

```ini
[Shell:Product]

"%CommonPrograms%\%DeveloperName%\%ProductName%", "%App%\app.exe"
```

*Fallstricke & Best Practice:* In modernen Windows-Versionen (10/11) werden Ordnerstrukturen oft flach dargestellt. Bei Deinstallation mit '-DelTree "%CommonPrograms%\%DeveloperName%"' bereinigen.

### %Company% (Metadaten / Organisation)

Firmen- bzw. Organisationsname aus den globalen Einstellungen der Empirum Management Console (EMC).

*Typischer Wert / Pfad:* `Musterfirma GmbH`

```ini
Text8="%Company%", Arial, 18, , 2170F3, 4, 10, RIGHT BOLD ITALIC
```

*Fallstricke & Best Practice:* Kann Leer- und Sonderzeichen enthalten; bei der Verwendung in Datei- oder Registry-Pfaden stets quoten.

### %ComputerName% (System)

NetBIOS-Name des Zielcomputers im Netzwerk.

*Typischer Wert / Pfad:* `CLIENT042`

```ini
VM_LicenseKey=%%%V_MachineValuesPath%\%ComputerName%.ini,%ComputerName%,LicenseKey%%
```

*Fallstricke & Best Practice:* Dient zur Adressierung von MachineValues-INI-Dateien. Groß-/Kleinschreibung bei Netzlaufwerken und UNC-Shares beachten.

### %DeveloperName% (Paket-Metadaten)

Hersteller- bzw. Entwicklername des Softwarepakets aus [Application] DeveloperName=.

*Typischer Wert / Pfad:* `Adobe`

```ini
UserKeyName=$Matrix42Packages$\%DeveloperName%\%ProductName%
```

*Fallstricke & Best Practice:* Muss konsistent zu DeveloperNameShort gepflegt werden; Namensänderungen führen zu verwaisten Registry- und Deinstallationsschlüsseln.

### %DomainName% (Netzwerk / Domäne)

Windows-Domänenname des Computers.

*Typischer Wert / Pfad:* `CORP`

```ini
V_MachineValuesPath=\\%EmpirumServer%\Values$\MachineValues\%DomainName%
```

*Fallstricke & Best Practice:* Bei Arbeitsgruppen-Rechnern ('WORKGROUP') weicht der Pfad auf dem Empirum-Server ab; bei Domänenmitgliedern liefert es die NetBIOS-Domäne.

### %EmpirumServer% (Empirum-Infrastruktur)

Name oder FQDN des Empirum-Servers bzw. des zuständigen SubDepots, von dem der Agent das Paket bezieht.

*Typischer Wert / Pfad:* `EMPIRUM01.corp.local`

```ini
V_MachineValuesPath=\\%EmpirumServer%\Values$\MachineValues\%DomainName%
```

*Fallstricke & Best Practice:* Niemals feste Server-IPs oder Hostnamen fest verdrahten! %EmpirumServer% wird vom UEM-Agenten dynamisch anhand der SubDepot-Zuweisung aufgelöst.

### %ErrorLevel% (Ablaufsteuerung / Returncode)

Rückgabecode (Exit-Code) des unmittelbar zuvor ausgeführten Befehls (Call, CallHidden, Script).

*Typischer Wert / Pfad:* `0 (Erfolg), 3010 (Reboot erforderlich), 1603 (Fataler Fehler)`

```ini
CallHidden MsiExec /I "%Src%\Files\setup.msi" /qn

If %ErrorLevel% == "3010" Then "RebootRequired" EndIf

If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf
```

*Fallstricke & Best Practice:* Wird von jedem nachfolgenden Befehl überschrieben! Unmittelbar nach Call/CallHidden prüfen. 3010 bedeutet Erfolg mit Neustartanforderung.

### %LocalAppData% (Benutzerverzeichnis (Lokal))

Lokales (nicht roamendes) Anwendungsdaten-Verzeichnis des Benutzers (%LOCALAPPDATA%).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Local`

```ini
Copy "%Src%\cache.bin", "%LocalAppData%\Vendor\App\cache.bin"
```

*Fallstricke & Best Practice:* Nur im Benutzerteil (/AW, CLIENT-Flag) verlässlich verfügbar! Im Maschinenteil verweist es auf das SYSTEM-Profil.

### %Personal% (Benutzerverzeichnis (Dokumente))

Dokumenten-Ordner des aktuellen Benutzers ('Eigene Dokumente' / Documents).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\Documents`

```ini
[Application]

DataDir=%Personal%
```

*Fallstricke & Best Practice:* Bei Ordnerumleitung (Folder Redirection oder OneDrive Known Folder Move) zeigt dieser Pfad auf den synchronisierten oder Netzlaufwerk-Ordner.

### %ProgramFiles% (Systemverzeichnis)

Standard-Programmverzeichnis der Zielarchitektur (64-Bit auf x64 mit Platform=x64).

*Typischer Wert / Pfad:* `C:\Program Files`

```ini
CallHidden "%ProgramFiles%\Vendor\App\setup.exe" /S
```

*Fallstricke & Best Practice:* Hängt vom Platform-Wert in [Setup] ab! Für explizit 32-Bit-Pfade auf 64-Bit-Systemen immer %ProgramFiles(x86)% verwenden.

### %ProgramFiles(x86)% (Systemverzeichnis (32-Bit))

Programmverzeichnis für 32-Bit-Anwendungen auf einem 64-Bit-Windows-Betriebssystem.

*Typischer Wert / Pfad:* `C:\Program Files (x86)`

```ini
ApplicationDir=%ProgramFiles(x86)%\%ProductName%
```

*Fallstricke & Best Practice:* Auf reinen 32-Bit-Betriebssystemen existiert dieser Pfad nicht (fällt dort auf C:\Program Files zurück).

### %ProgramFilesDir% (Systemverzeichnis)

Identisch zu %ProgramFiles%, aus der Windows-Registry (ProgramFilesDir) ermittelt.

*Typischer Wert / Pfad:* `C:\Program Files`

```ini
[Application]

ApplicationDir=%ProgramFilesDir%\%ProductName%
```

*Fallstricke & Best Practice:* Synonym zu %ProgramFiles%; in [Application] ist ProgramFilesDir historisch die bevorzugte Konvention.

### %ProgramFilesDirx86% (Systemverzeichnis (32-Bit))

Identisch zu %ProgramFiles(x86)%, aus der Windows-Registry (ProgramFilesDir (x86)) ermittelt.

*Typischer Wert / Pfad:* `C:\Program Files (x86)`

```ini
[Application]

ApplicationDir=%ProgramFilesDirx86%\%ProductName%
```

*Fallstricke & Best Practice:* Auf 32-Bit-Systemen identisch zu %ProgramFilesDir%.

### %ProductName% (Paket-Metadaten)

Produkt- bzw. Paketname aus [Application] ProductName=.

*Typischer Wert / Pfad:* `7-Zip`

```ini
V_LogFileInstall=%Temp%\Install_%ProductName%.log
```

*Fallstricke & Best Practice:* Keine verbotenen Dateisystem-Sonderzeichen (/ \ : * ? " < > |) verwenden; steuert das Empirum-Software-Register.

### %Sendto% (Verknüpfung / Shell)

Verzeichnis des Windows-Kontextmenüs 'Senden an' (SendTo) des Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\SendTo`

```ini
#Shell:SendTo, CLIENT



[Shell:SendTo]

"%Sendto%\AppName", "%App%\app.exe"
```

*Fallstricke & Best Practice:* Erfordert zwingend den Benutzerteil (/AW, CLIENT-Flag), da das Menü rein benutzerbezogen ist.

### %SetupBits% (Architektur / Engine)

Bit-Architektur des ausführenden Setup.exe-Prozesses (32 oder 64).

*Typischer Wert / Pfad:* `64 (auf 64-Bit-Systemen) bzw. 32`

```ini
CommonSetupDir=%CommonFilesDir%\Setup%SetupBits%
```

*Fallstricke & Best Practice:* Gibt die Bitbreite des Empirum-Setup-Interpreters an, nicht zwingend die Zielarchitektur des Programms (letztere wird in Platform=x64 geregelt).

### %Src% (Quelle / Paketpfad)

Absoluter Pfad zum Quellverzeichnis des Pakets zur Laufzeit (lokaler PackageStore-Cache oder Depotshare). Definiert durch SrcDir=.. in [Application].

*Typischer Wert / Pfad:* `C:\EmpirumAgent\PackageStore\Vendor\Product\1.0\`

```ini
CallHidden MsiExec /I "%Src%\Files\setup.msi" /qn
```

*Fallstricke & Best Practice:* Immer in Anführungszeichen setzen ("%Src%\Files\..."), da Paket- und Depotpfade häufig Leerzeichen enthalten.

### %System% (Systemverzeichnis)

Windows-Systemordner (System32).

*Typischer Wert / Pfad:* `C:\Windows\System32`

```ini
CallHidden "%System%\reg.exe" add "HKLM\Software\Vendor" /v Test /t REG_SZ /d 1 /f
```

*Fallstricke & Best Practice:* Auf 64-Bit-Windows unterliegt ein 32-Bit-Prozess der WOW64-Dateisystemumleitung nach SysWOW64, wenn Platform nicht auf x64 steht.

### %Temp% (Systemverzeichnis (Temporär))

Temporäres Arbeitsverzeichnis des aktuellen Ausführungskontextes.

*Typischer Wert / Pfad:* `C:\Windows\Temp (als SYSTEM) bzw. C:\Users\<User>\AppData\Local\Temp`

```ini
V_LogFileInstall=%Temp%\Install_%ProductName%.log
```

*Fallstricke & Best Practice:* Im Maschinenteil (SYSTEM) hat ein Standardbenutzer keine Leserechte auf C:\Windows\Temp; Logdateien bei Bedarf nach %ProgramData% schreiben.

### %UserDomain% (Netzwerk / Benutzer)

NetBIOS-Name der Domäne des aktuell angemeldeten Benutzers.

*Typischer Wert / Pfad:* `CORP`

```ini
V_UserValuesPath=%HKLM,"Software\matrix42\Software Depot","HomeServer"%\Values$\UserValues\%UserDomain%
```

*Fallstricke & Best Practice:* Im reinen Maschinenteil vor der Benutzeranmeldung liefert die Variable die Computerdomäne oder NT AUTHORITY. Nur im Benutzerteil (/AW) verlässlich.

### %Version% (Paket-Metadaten)

Produktversion aus [Application] Version=.

*Typischer Wert / Pfad:* `1.0`

```ini
MachineKeyName=$Matrix42Packages$\%DeveloperName%\%ProductName%\%Version%
```

*Fallstricke & Best Practice:* Muss exakt mit der Version im Empirum Software-Depot übereinstimmen; Änderungen erfordern eine Paket-Revisionserhöhung.

### %WinDir% (Systemverzeichnis)

Hauptverzeichnis des Windows-Betriebssystems (%SystemRoot%).

*Typischer Wert / Pfad:* `C:\Windows`

```ini
CallHidden "%WinDir%\notepad.exe"
```

*Fallstricke & Best Practice:* Niemals fest als C:\Windows schreiben, da Windows in Spezialumgebungen auf anderen Laufwerken liegen kann.

### %WindowsUser% (Benutzer)

Benutzername des aktuell interaktiv angemeldeten Windows-Benutzers (%USERNAME%).

*Typischer Wert / Pfad:* `s.mueller`

```ini
VU_Language=%%%V_UserValuesPath%\%WindowsUser%.ini,%WindowsUser%,Language%%

ReplaceEnv VU_Language
```

*Fallstricke & Best Practice:* Im reinen Maschinenteil ohne /AW ist der Wert leer oder SYSTEM. Für benutzerspezifische Aktionen immer /AW verwenden.

### %Windows% (Systemverzeichnis)

Synonym für %WinDir% (dokumentierte Langform).

*Typischer Wert / Pfad:* `C:\Windows`

```ini
Copy "%Src%\Files\ini.ini", "%Windows%\ini.ini"
```

*Fallstricke & Best Practice:* In neuen Paketen einheitlich %WinDir% verwenden.

### %Desktop% (Verknüpfung / Desktop)

Desktop-Ordner – abhängig von CommonShellLinks gemeinsam oder benutzerbezogen.

*Typischer Wert / Pfad:* `C:\Users\Public\Desktop bzw. C:\Users\<Benutzer>\Desktop`

```ini
Copy "%Src%\link.lnk", "%Desktop%\link.lnk"
```

*Fallstricke & Best Practice:* Ziel hängt vom CommonShellLinks-Schalter ab – Verknüpfungen besser über [Shell:] steuern.

### %UserDesktop% (Benutzerverzeichnis)

Desktop-Ordner des aktuellen Benutzers (unabhängig von CommonShellLinks).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\Desktop`

```ini
Copy "%Src%\readme.txt", "%UserDesktop%\readme.txt"
```

*Fallstricke & Best Practice:* Nur im Benutzerteil (/AW) verlässlich.

### %StartMenu% (Verknüpfung / Startmenü)

Startmenü-Ordner – abhängig von CommonShellLinks gemeinsam oder benutzerbezogen.

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu`

```ini
MD "%StartMenu%\Programs\%DeveloperName%"
```

*Fallstricke & Best Practice:* Siehe %Desktop%.

### %CommonStartMenu% (Verknüpfung / Startmenü)

Gemeinsamer Startmenü-Ordner aller Benutzer.

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu`

```ini
MD "%CommonStartMenu%\Programs\%DeveloperName%"
```

*Fallstricke & Best Practice:* Schreibrechte als Standardbenutzer eingeschränkt.

### %Programs% (Verknüpfung / Startmenü)

Startmenü\Programme-Ordner – abhängig von CommonShellLinks.

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs`

```ini
[Shell:Product]

"%Programs%\%ProductName%", "%App%\app.exe"
```

*Fallstricke & Best Practice:* Siehe %Desktop%.

### %UserPrograms% (Benutzerverzeichnis)

Startmenü\Programme des aktuellen Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs`

```ini
MD "%UserPrograms%\%ProductName%"
```

*Fallstricke & Best Practice:* Nur im Benutzerteil (/AW) verlässlich.

### %Startup% (Verknüpfung / Autostart)

Autostart-Ordner – abhängig von CommonShellLinks gemeinsam oder benutzerbezogen.

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp`

```ini
Copy "%Src%\agent.lnk", "%Startup%\agent.lnk"
```

*Fallstricke & Best Practice:* Autostart-Einträge bei Deinstallation zwingend zurücknehmen.

### %UserStartup% (Benutzerverzeichnis)

Autostart-Ordner des aktuellen Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\StartUp`

```ini
Copy "%Src%\user.lnk", "%UserStartup%\user.lnk"
```

*Fallstricke & Best Practice:* Nur im Benutzerteil (/AW) verlässlich.

### %CommonStartup% (Verknüpfung / Autostart)

Gemeinsamer Autostart-Ordner aller Benutzer.

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp`

```ini
Copy "%Src%\agent.lnk", "%CommonStartup%\agent.lnk"
```

*Fallstricke & Best Practice:* Startet Anwendungen für ALLE Benutzer bei der Anmeldung.

### %ProgramFilesSys% (Systemverzeichnis (32-Bit))

x86-Programmverzeichnis auf x64-Systemen (System-Bit-Sicht des Setup-Prozesses).

*Typischer Wert / Pfad:* `C:\Program Files (x86)`

```ini
ApplicationDir=%ProgramFilesSys%\%ProductName%
```

*Fallstricke & Best Practice:* Für bewusst 32-Bit-Ziele %ProgramFiles(x86)% bevorzugen (klarere Semantik).

### %CommonFilesDirx86% (Systemverzeichnis (32-Bit))

Common-Files-Verzeichnis für 32-Bit-Anwendungen auf x64.

*Typischer Wert / Pfad:* `C:\Program Files (x86)\Common Files`

```ini
V_Shared86=%CommonFilesDirx86%\Vendor
```

*Fallstricke & Best Practice:* Auf 32-Bit-Systemen identisch zu %CommonFilesDir%.

### %WriteableSystem% (Systemverzeichnis)

Terminalserver-korrekt beschreibbares Systemverzeichnis.

*Typischer Wert / Pfad:* `C:\Windows\System32`

```ini
Copy "%Src%\drv.ini", "%WriteableSystem%\drv.ini"
```

*Fallstricke & Best Practice:* Auf Terminalservern sonst ggf. Schreibumleitung in Benutzersitzung.

### %Fonts% (Systemverzeichnis)

Schriftarten-Ordner von Windows.

*Typischer Wert / Pfad:* `C:\Windows\Fonts`

```ini
Copy "%Src%\Files\corp.ttf", "%Fonts%\corp.ttf"
```

*Fallstricke & Best Practice:* Schriften zusätzlich per Registry (Fonts-Schlüssel) registrieren.

### %Templates% (Benutzerverzeichnis)

Vorlagen-Ordner des Benutzers (Shell-Folder Templates).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Templates`

```ini
Copy "%Src%\brief.dotx", "%Templates%\brief.dotx"
```

*Fallstricke & Best Practice:* Benutzerbezogen – im Maschinenteil zeigt es auf das SYSTEM-Profil.

### %Favorites% (Benutzerverzeichnis)

Favoriten-Ordner des Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\Favorites`

```ini
MD "%Favorites%\Links"
```

*Fallstricke & Best Practice:* Benutzerbezogen – /AW.

### %Recent% (Benutzerverzeichnis)

Ordner 'Zuletzt verwendete Dateien' des Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Recent`

```ini
Del "%Recent%\*.lnk"
```

*Fallstricke & Best Practice:* Benutzerbezogen – /AW; Löschungen sind Eingriffe in die Benutzerhistorie.

### %UserProfile% (Benutzerverzeichnis)

Profil-Stammverzeichnis des aktuellen Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>`

```ini
MD "%UserProfile%\AppData\Local\Vendor"
```

*Fallstricke & Best Practice:* Im Maschinenteil (SYSTEM) zeigt es auf das SYSTEM-Profil!

### %Client% (Empirum-Infrastruktur)

Installationsart-Kontext des Setups (verifizierte Variable, Admin/Client-Logik).

*Typischer Wert / Pfad:* `1`

```ini
If %Client% == "1" Then "Set:ClientSetup" EndIf
```

*Fallstricke & Best Practice:* Nur in Admin-/Client-Installationspaketen relevant.

### %ClientSrcDir% (Quelle / Paketpfad)

Quellverzeichnis des Benutzerteils einer Admin-Installation.

*Typischer Wert / Pfad:* `\\Server\Depot$\Product\Client`

```ini
Copy "%ClientSrcDir%\user.cfg", "%AppData%\user.cfg"
```

*Fallstricke & Best Practice:* Nur bei Admin-/Workstation-Installationen gesetzt.

### %Data% (Verzeichnis)

Datenverzeichnis aus [Application] DataDir=.

*Typischer Wert / Pfad:* `C:\ProgramData\Vendor\App\Data`

```ini
[Application]

DataDir=%CommonAppData%\%DeveloperName%\%ProductName%
```

*Fallstricke & Best Practice:* Wie %App% über [Application] definieren, nicht hartkodieren.

### %User% (Benutzer)

Setup-Benutzername (Kontext der Setup-Ausführung).

*Typischer Wert / Pfad:* `SYSTEM bzw. s.mueller`

```ini
Echo Installation läuft als %User%
```

*Fallstricke & Best Practice:* Unterscheidet sich von %WindowsUser%, wenn Setup elevated läuft.

### %WindowsVersion% (System)

Windows-Version als String (z. B. '10.0'); feldverifiziert im Agent-Paket: 'If %WindowsVersion% < "10.0" …'.

*Typischer Wert / Pfad:* `10.0`

```ini
If %WindowsVersion% < "10.0" Then "Set:UnsupportedOS" EndIf
```

*Fallstricke & Best Practice:* Ab [Setup] Version=14.2 numerisch je Punkt-Segment vergleichen, davor ziffernweise lexikalisch!

### %WindowsName% (System)

Marketingname des Betriebssystems.

*Typischer Wert / Pfad:* `Windows 10 Pro`

```ini
Echo Betriebssystem: %WindowsName%
```

*Fallstricke & Best Practice:* Für Logik ONAME nicht parsen – dafür %OS.Name%/%WindowsVersion% nutzen.

### %WindowsBits% (Architektur)

Bitbreite des Betriebssystems (32/64).

*Typischer Wert / Pfad:* `64`

```ini
If %WindowsBits% == "64" Then "Set:x64" EndIf
```

*Fallstricke & Best Practice:* Für die Setup-Prozess-Sicht %SetupBits% verwenden.

### %IsLaptop% (System)

'1', wenn das Gerät ein Notebook/Portable ist, sonst '0' (Chassis-Typ).

*Typischer Wert / Pfad:* `1`

```ini
If %IsLaptop% == "1" Then "Set:LaptopConfig" EndIf
```

*Fallstricke & Best Practice:* VMs und Tablets können je nach Chassis-Typ unerwartet klassifiziert werden.

### %InstalledVersion% (Ablaufsteuerung)

Version der BEREITS installierten Paketversion – nur in [Requirements] gültig (Service-Release-Logik mit ServiceRelease=1).

*Typischer Wert / Pfad:* `1.9`

```ini
[Requirements]

%InstalledVersion% < 2.0
```

*Fallstricke & Best Practice:* Nur in [Requirements] gesetzt; außerhalb leer.

### %InstalledRevision% (Ablaufsteuerung)

Revision der bereits installierten Version – nur in [Requirements].

*Typischer Wert / Pfad:* `3`

```ini
[Requirements]

%InstalledRevision% < 5
```

*Fallstricke & Best Practice:* Nur in [Requirements] gesetzt; außerhalb leer.

### %Option% (Ablaufsteuerung)

Name der aktuell gewählten Installationsoption (aus [Options]).

*Typischer Wert / Pfad:* `Product`

```ini
If %Option% == "API" Then "Set:InstallAPI" EndIf
```

*Fallstricke & Best Practice:* Bei mehreren gewählten Optionen pro Durchlauf gesetzt; [%Option%]-Gemeinschaftssektion beachten.

### %OptionName% (Ablaufsteuerung)

Anzeigename der aktuellen Option.

*Typischer Wert / Pfad:* `Produkt`

```ini
Echo Installiere Option: %OptionName%
```

*Fallstricke & Best Practice:* Lokalisierter Text – nicht für Logik verwenden.

### %OptionText% (Ablaufsteuerung)

Beschreibungstext der aktuellen Option.

*Typischer Wert / Pfad:* `Kernkomponenten installieren`

```ini
Echo %OptionText%
```

*Fallstricke & Best Practice:* Lokalisierter Text – nicht für Logik verwenden.

### %SetupInf% (Empirum-Infrastruktur)

Bezeichnung der aktuell ablaufenden Setup.inf.

*Typischer Wert / Pfad:* `Setup.inf`

```ini
Echo Lade %SetupInf%
```

*Fallstricke & Best Practice:* Für Pfade %SetupInfPathName% verwenden.

### %SetupInfFileName% (Empirum-Infrastruktur)

Dateiname der Setup.inf.

*Typischer Wert / Pfad:* `Setup.inf`

```ini
Copy "%SetupInfPathName%", "%App%\%SetupInfFileName%"
```

*Fallstricke & Best Practice:* —

### %SetupInfPathName% (Empirum-Infrastruktur)

Voller Pfad der aktuell ablaufenden Setup.inf.

*Typischer Wert / Pfad:* `C:\EmpirumAgent\PackageStore\Vendor\App\1.0\Install\Setup.inf`

```ini
Copy "%SetupInfPathName%", "%App%\Setup.inf"
```

*Fallstricke & Best Practice:* Pfad enthält Leerzeichen – quoten.

### %SetupInfServerName% (Empirum-Infrastruktur)

Name des Servers/Depots, von dem die Setup.inf geladen wurde.

*Typischer Wert / Pfad:* `EMPIRUM01`

```ini
Echo Quelle: %SetupInfServerName%
```

*Fallstricke & Best Practice:* Für Depot-Pfade %EmpirumServer% bevorzugen.

### %SysDate% (Ablaufsteuerung)

Aktuelles Systemdatum (kurze Darstellung) – u. a. in SwDepot-Logdateinamen sichtbar.

*Typischer Wert / Pfad:* `01.01.2026`

```ini
Echo Durchlauf vom %SysDate% %SysTime%
```

*Fallstricke & Best Practice:* Regionsabhängiges Format – nicht sortierbar; nur für Logs.

### %SysTime% (Ablaufsteuerung)

Aktuelle Systemzeit.

*Typischer Wert / Pfad:* `14:30`

```ini
Echo Durchlauf vom %SysDate% %SysTime%
```

*Fallstricke & Best Practice:* Nur für Logs; nicht für Logik.

### %LongSysTime% (Ablaufsteuerung)

Systemzeit mit Sekunden/Anteilen (long form).

*Typischer Wert / Pfad:* `14:30:15`

```ini
Echo Start: %LongSysTime%
```

*Fallstricke & Best Practice:* Nur für Logs.

### %ExactSysTime% (Ablaufsteuerung)

Exakte Systemzeit mit maximaler Auflösung (z. B. für Performance-Messungen).

*Typischer Wert / Pfad:* `14:30:15.123`

```ini
Echo T0=%ExactSysTime%
```

*Fallstricke & Best Practice:* Auflösung Plattform-abhängig.

### %CLRDir% (Systemverzeichnis)

Installationsverzeichnis der .NET-CLR (höchste installierte Version).

*Typischer Wert / Pfad:* `C:\Windows\Microsoft.NET\Framework64\v4.0.30319`

```ini
CallHidden "%CLRDir%\RegAsm.exe" "%App%\lib.dll" /codebase
```

*Fallstricke & Best Practice:* Version wechselt mit .NET-Updates – nicht dauerhaft hart in Konfigen verankern.

### %MediaPath% (Systemverzeichnis)

Windows-Medienordner.

*Typischer Wert / Pfad:* `C:\Windows\Media`

```ini
PlaySound 1, "%MediaPath%\tada.wav", 0
```

*Fallstricke & Best Practice:* —

### %PrintServer% (Netzwerk / Drucker)

Standard-Druckserver des Systems.

*Typischer Wert / Pfad:* `PRINT01`

```ini
AddPrinterConnection "\\%PrintServer%\Etage1"
```

*Fallstricke & Best Practice:* Ohne konfigurierten Druckserver leer.

### %PrintEnvironment% (Netzwerk / Drucker)

Druckertreiber-Umgebung (z. B. 'Windows x64').

*Typischer Wert / Pfad:* `Windows x64`

```ini
AddPrinterDriver "Generic / Text Only", "%PrintEnvironment%", "%Src%\Driver"
```

*Fallstricke & Best Practice:* Muss zur Zielarchitektur passen.

### %PrintHood% (Benutzerverzeichnis)

Ordner 'Druckumgebung' des Benutzers (Shell-Folder PrintHood).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Printer Shortcuts`

```ini
MD "%PrintHood%\Vendor"
```

*Fallstricke & Best Practice:* Benutzerbezogen – /AW.

### %NetHood% (Benutzerverzeichnis)

Ordner 'Netzwerkumgebung' des Benutzers (Shell-Folder NetHood).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Roaming\Microsoft\Windows\Network Shortcuts`

```ini
MD "%NetHood%\Vendor"
```

*Fallstricke & Best Practice:* Benutzerbezogen – /AW.

### %InternetCache% (Benutzerverzeichnis)

Cache-Ordner des Browsers (Temporary Internet Files).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Local\Microsoft\Windows\INetCache`

```ini
-DelTree "%InternetCache%\Vendor"
```

*Fallstricke & Best Practice:* Benutzerbezogen; Pflücken von Browserdaten datenschutzrechtlich prüfen.

### %Cookies% (Benutzerverzeichnis)

Cookie-Ordner des Browsers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Local\Microsoft\Windows\INetCookies`

```ini
-DelTree "%Cookies%\Vendor"
```

*Fallstricke & Best Practice:* Benutzerbezogen; Löschen entfernt Anmeldedaten!

### %History% (Benutzerverzeichnis)

Browser-Verlaufsordner des Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Local\Microsoft\Windows\History`

```ini
Echo Cleanup %History%
```

*Fallstricke & Best Practice:* Benutzerbezogen; Verlaufslöschung ist Benutzereingriff.

### %LocalSettings% (Benutzerverzeichnis)

Legacy-'Local Settings'-Ordner des Profils (Kompatibilitätsansicht).

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\AppData\Local`

```ini
Copy "%Src%\cache.dat", "%LocalSettings%\Vendor\cache.dat"
```

*Fallstricke & Best Practice:* Legacy-Alias – neue Pakete %LocalAppData% verwenden.

### %Accessories% (Startmenü-Zubehör)

Startmenü-Zubehörordner (Accessories-Shell-Folder, dokumentierte New-Folder-Variable).

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Accessories`

```ini
MD "%Accessories%\%DeveloperName%"
```

*Fallstricke & Best Practice:* Ordner existiert auf deutschen Systemen lokalisiert – Variable löst korrekt auf.

### %Games% (Startmenü-Zubehör)

Startmenü-Spieleordner (dokumentierte New-Folder-Variable).

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Games`

```ini
MD "%Games%\%DeveloperName%"
```

*Fallstricke & Best Practice:* —

### %Multimedia% (Startmenü-Zubehör)

Startmenü-Multimediaordner (dokumentierte New-Folder-Variable).

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Accessories\Media`

```ini
MD "%Multimedia%\%DeveloperName%"
```

*Fallstricke & Best Practice:* —

### %SystemTools% (Startmenü-Zubehör)

Startmenü-Systemwerkzeugeordner (dokumentierte New-Folder-Variable).

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools`

```ini
MD "%SystemTools%\%DeveloperName%"
```

*Fallstricke & Best Practice:* —

### %AdminTools% (Startmenü-Zubehör)

Verwaltungswerkzeuge-Ordner (dokumentierte New-Folder-Variable).

*Typischer Wert / Pfad:* `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools`

```ini
MD "%AdminTools%\%DeveloperName%"
```

*Fallstricke & Best Practice:* —

### %CDBurnArea% (Systemverzeichnis)

Staging-Bereich für Brennvorgänge aller Benutzer.

*Typischer Wert / Pfad:* `C:\Users\Public\Documents\Burn`

```ini
Copy "%Src%\iso.lst", "%CDBurnArea%\iso.lst"
```

*Fallstricke & Best Practice:* —

### %AppPaths% (Registry / AppPaths)

AppPaths-Schlüssel des aktuellen Anwendungskontexts (dokumentierte Variable für App-Pfad-Registrierungen).

*Typischer Wert / Pfad:* `HKCR\AppPaths`

```ini
; Kontextvariable für AppPaths-Registrierung
```

*Fallstricke & Best Practice:* —

### %MyMusic% (Benutzerverzeichnis (Medien))

Musik-Ordner des Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\Music`

```ini
MD "%MyMusic%\Vendor"
```

*Fallstricke & Best Practice:* Bei Ordnerumleitung (OneDrive KFM) abweichend.

### %MyPictures% (Benutzerverzeichnis (Medien))

Bilder-Ordner des Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\Pictures`

```ini
MD "%MyPictures%\Vendor"
```

*Fallstricke & Best Practice:* Bei Ordnerumleitung abweichend.

### %MyVideo% (Benutzerverzeichnis (Medien))

Video-Ordner des Benutzers.

*Typischer Wert / Pfad:* `C:\Users\<Benutzer>\Videos`

```ini
MD "%MyVideo%\Vendor"
```

*Fallstricke & Best Practice:* Bei Ordnerumleitung abweichend.

### %OS.Name% (Betriebssystem (OS.*))

Betriebssystemname aus der OS.*-Familie (verifizierte Variablentabelle).

*Typischer Wert / Pfad:* `Windows 10 Pro`

```ini
If %OS.Name% != "Windows 11" Then "Set:Win10" EndIf
```

*Fallstricke & Best Practice:* Für Versionsvergleiche %OS.MajorVersion%/%OS.BuildNumber% verwenden.

### %OS.MajorVersion% (Betriebssystem (OS.*))

Hauptversionsnummer des Betriebssystems.

*Typischer Wert / Pfad:* `10`

```ini
If %OS.MajorVersion% >= "10" Then "Set:Modern" EndIf
```

*Fallstricke & Best Practice:* Zahlenvergleich ab Engine 14.2 numerisch je Segment.

### %OS.MinorVersion% (Betriebssystem (OS.*))

Nebenversionsnummer des Betriebssystems.

*Typischer Wert / Pfad:* `0`

```ini
If %OS.MinorVersion% == "0" Then "OK" EndIf
```

*Fallstricke & Best Practice:* —

### %OS.BuildNumber% (Betriebssystem (OS.*))

Build-Nummer des Betriebssystems.

*Typischer Wert / Pfad:* `26100`

```ini
If %OS.BuildNumber% < "22000" Then "Set:OldBuild" EndIf
```

*Fallstricke & Best Practice:* Numerisch vergleichen (5-stellige Builds > lexikalisch '9999').

### %OS.CSDVersion% (Betriebssystem (OS.*))

Service-Pack-Bezeichner (Legacy; bei modernen Windows leer).

*Typischer Wert / Pfad:* `Service Pack 1`

```ini
If %OS.CSDVersion% == "" Then "OK" EndIf
```

*Fallstricke & Best Practice:* Seit Windows 10 immer leer – nicht mehr für SP-Logik verwenden.

### %OS.DisplayString% (Betriebssystem (OS.*))

Anzeigestring des Betriebssystems.

*Typischer Wert / Pfad:* `Windows 10 Pro`

```ini
Echo OS: %OS.DisplayString%
```

*Fallstricke & Best Practice:* Nur für Ausgaben.

### %OS.ProductType% (Betriebssystem (OS.*))

Produkttyp (Workstation/Server/Domain Controller).

*Typischer Wert / Pfad:* `1`

```ini
If %OS.ProductType% == "3" Then "Set:ServerSKip" EndIf
```

*Fallstricke & Best Practice:* Werte: 1=Workstation, 2=Domain Controller, 3=Server.

### %OS.SuiteMask% (Betriebssystem (OS.*))

Bitmaske der installierten Produktsuite.

*Typischer Wert / Pfad:* `256`

```ini
If %OS.SuiteMask% == "256" Then "OK" EndIf
```

*Fallstricke & Best Practice:* Bitmasken nur mit BitAnd auswerten.

### %OS.ServicePackMajor% (Betriebssystem (OS.*))

Hauptversionsnummer des Service Packs / kumulativen Updates.

*Typischer Wert / Pfad:* `0`

```ini
If %OS.ServicePackMajor% < "1" Then "OK" EndIf
```

*Fallstricke & Best Practice:* Seit Windows 10 meist 0.

### %OS.PlatformId% (Betriebssystem (OS.*))

Plattform-ID (VER_PLATFORM_*).

*Typischer Wert / Pfad:* `2`

```ini
If %OS.PlatformId% == "2" Then "WinNT" EndIf
```

*Fallstricke & Best Practice:* —

### %$Everyone% (Gruppen für [Security:])

Lokalisierte Gruppe 'Jeder' für die Verwendung in [Security:]-Sektionen.

*Typischer Wert / Pfad:* `Jeder`

```ini
[Security:Product]

FileDacl.Add ("%App%", %$Everyone%, SET, READ)
```

*Fallstricke & Best Practice:* Nur für [Security:]-Sektionen gedacht (lokalisierte Gruppe).

### %$LocalAdmins% (Gruppen für [Security:])

Lokalisierte Gruppe der lokalen Administratoren für [Security:].

*Typischer Wert / Pfad:* `Administratoren`

```ini
[Security:Product]

FileDacl.Add ("%App%", %$LocalAdmins%, SET, ALL)
```

*Fallstricke & Best Practice:* Nur für [Security:]-Sektionen gedacht.

### %$DomainUsers% (Gruppen für [Security:])

Lokalisierte Gruppe der Domänenbenutzer für [Security:].

*Typischer Wert / Pfad:* `Domänen-Benutzer`

```ini
[Security:Product]

FileDacl.Add ("%App%", %$DomainUsers%, SET, CHANGE)
```

*Fallstricke & Best Practice:* Nur für [Security:]-Sektionen gedacht.

### %Root,SubKey,ValueName% (Registry-Syntax)

Direktes Auslesen eines Windows-Registry-Wertes zur Laufzeit. Root ist HKLM, HKCU, HKCR, HKU oder HKCC.

*Typischer Wert / Pfad:* `%HKLM,SOFTWARE\Microsoft\Windows\CurrentVersion,ProgramFilesDir%`

```ini
Set V_ProgramFiles = %HKLM,SOFTWARE\Microsoft\Windows\CurrentVersion,ProgramFilesDir%

ReplaceEnv V_ProgramFiles
```

*Fallstricke & Best Practice:* Zwischen Root und SubKey steht ein Komma, KEIN Backslash! Bei leerem Wertnamen wird der Standardwert (Default) gelesen.

### %%%Path.ini,Section,Key%%% (INI-Syntax)

Liest einen Schlüsselwert aus einer externen INI-Datei (z. B. MachineValues oder UserValues auf dem Server).

*Typischer Wert / Pfad:* `%%%V_MachineValuesPath%\%ComputerName%.ini,%ComputerName%,LicenseKey%%`

```ini
VM_LicenseKey = %%%V_MachineValuesPath%\%ComputerName%.ini,%ComputerName%,LicenseKey%%

ReplaceEnv VM_LicenseKey
```

*Fallstricke & Best Practice:* Erfordert dreifache Prozentzeichen ('%%%...%%'). Nach der Zuweisung MUSS ReplaceEnv aufgerufen werden, um den Wert aufzulösen.

### %VM_*% (MachineValues (Computer))

Maschinenspezifische Paketvariable (Computer-Ebene), deklariert in [VarDefInfo] mit Typ 0.

*Typischer Wert / Pfad:* `%VM_LicenseKey%`

```ini
[VarDefInfo]

VM_LicenseKey, 0, 0



[Product]

ReplaceEnv VM_LicenseKey
```

*Fallstricke & Best Practice:* Muss in [VarDefInfo] deklariert und vor der ersten Verwendung in [Product] zwingend mit 'ReplaceEnv VM_...' aufgelöst werden!

### %VU_*% (UserValues (Benutzer))

Benutzerspezifische Paketvariable (Benutzer-Ebene), deklariert in [VarDefInfo] mit Typ 1. Erfordert /AW.

*Typischer Wert / Pfad:* `%VU_Language%`

```ini
[VarDefInfo]

VU_Language, 1, 1



[Product]

ReplaceEnv VU_Language
```

*Fallstricke & Best Practice:* Benötigt zwingend den Schalter /AW in Command line options und im Software-Depot, sonst wird die Variable nicht pro Benutzer aufgelöst.

### %DstDir% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Zielverzeichnis-Variable; praktisch von Matrix42 selbst in OutlookSignatur.inf genutzt (Schreibweise %DSTDIR% im Testkorpus) – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %CalledFromService% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Kontext-Flag, ob der Aufruf vom Setup-Service kommt – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %CurrentFqdnUser% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Voll qualifizierter (FQDN-)Benutzername des aktuellen Kontexts – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %System16% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): 16-Bit-Systemverzeichnis (Legacy) – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %SharedDir% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Gemeinsames (Shared-)Verzeichnis des Systems – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %ResourcesDir% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Windows-Ressourcenverzeichnis – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %UserProfiles% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Profil-Stammverzeichnis aller Benutzer (z. B. C:\Users) – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %CommonOEMLinks% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): OEM-Links-Ordner für alle Benutzer – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %LocalAppDataLow% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): LocalLow-Profilordner des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %PhotoAlbums% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Fotoordner des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %Playlists% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Wiedergabelisten-Ordner des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %OriginalImages% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): OriginalImages-Ordner des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %SavedGames% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Gespeicherte Spiele des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %SavedSearches% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Gespeicherte Suchen des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %SidebarDefaultParts% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Standardkomponenten der Sidebar (Vista-Ära) – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %SidebarParts% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Sidebar-Komponenten (Vista-Ära) – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %Contacts% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Kontakte-Ordner des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %QuickLaunch% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Schnellstartleiste des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %Public% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Öffentlicher Benutzerordner (C:\Users\Public) – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %Downloads% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Download-Ordner des Benutzers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %PrintProcessorDir% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Druckprozessor-Verzeichnis des Spoolers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %PrinterDriverDir% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Druckertreiber-Verzeichnis des Spoolers – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %LocalizedResourcesDir% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Lokalisiertes Ressourcenverzeichnis – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

### %MediaPathUnexpanded% (Undokumentiert (26.1.0))

⚠ UNDOKUMENTIERT (Klasse 1): Unaufgelöster (nicht expandierter) Windows-Medienpfad – verifiziert gegen den Interpreter 26.1.0, fehlt in der gesamten offiziellen Hilfe.

*Typischer Wert / Pfad:* ``

```ini

```

*Fallstricke & Best Practice:* Kein Matrix42-Support, kein Sicherheitsnetz – nur nach eigener Verifikation gegen den Zielinterpreter einsetzen.

## Lint-Diagnosen VAL-001…025

### VAL-001 (ERROR)

*Ursache:* Ein #-Verweis zeigt auf eine Sektion, die im Dokument nicht existiert (Tippfehler oder gelöschte Sektion).

*Behebung:* Sektion anlegen (QuickFix erzeugt Stub) oder Verweis korrigieren.

*Referenz: Kap. 5 – Sektions-Aufrufe*

### VAL-002 (ERROR)

*Ursache:* Funktionsprädikat in If ist gequotet ("FileExists(…)") und wird so als String-Vergleich interpretiert statt als Funktion.

*Behebung:* Äußere Anführungszeichen um das Prädikat entfernen (QuickFix).

*Referenz: Kap. 5 – If/Prädikate*

### VAL-003 (ERROR)

*Ursache:* DelTree-Argument endet mit Backslash – riskantes Löschmuster.

*Behebung:* Abschließenden Backslash entfernen (QuickFix).

*Referenz: Kap. 6 – DelTree*

### VAL-004 (ERROR)

*Ursache:* Abort/ErrorLogMsg in einer Deinstallations-Fehlersektion ohne '--'-Präfix (Legacy-Stil) – würde zur falschen Zeit laufen.

*Behebung:* '--'-Präfix ergänzen oder auf Fehlersektionen mit '-'-Command-Style umstellen.

*Referenz: Kap. 5 – Uninstall-Logik*

### VAL-005 (WARNING)

*Ursache:* ShellLinks=1 und zusätzlich #Shell:… in [Product] – Verknüpfungen würden doppelt angelegt/entfernt.

*Behebung:* Entweder die #Shell-Referenz entfernen oder ShellLinks=0 setzen.

*Referenz: Kap. 9 – Shell-Sektion*

### VAL-006 (WARNING)

*Ursache:* Benutzerteil-Merkmale (HKCU, VU_, AskKillProcesses) vorhanden, aber kein /AW in [SetupInfo].

*Behebung:* /AW in Command line options ergänzen (QuickFix) UND im Depot-Befehl spiegeln.

*Referenz: Kap. 2 – Maschinenteil/Benutzerteil*

### VAL-007 (WARNING)

*Ursache:* Registry-Löschung nahe Wurzel-/Herstellerebene (HKLM,SOFTWARE oder …\Microsoft).

*Behebung:* Löschziel prüfen und auf die konkrete Anwendungsebene vertiefen.

*Referenz: Kap. 7 – Registry*

### VAL-008 (WARNING)

*Ursache:* Nach Call/CallHidden/Run fehlt die %ErrorLevel%-Prüfung (0/3010). Ausgenommen sind taskkill-Befehle (best-effort).

*Behebung:* ErrorLevel-Block einfügen (QuickFix: If … Then … EndIf-Zeilen).

*Referenz: Kap. 6 – ErrorLevel*

### VAL-009 (WARNING)

*Ursache:* Unkontrolliertes Reboot=1 in [Application] bzw. unkonditioniertes SetReboot 1.

*Behebung:* Reboot=0 setzen und über den 3010-Pfad ([RebootRequired]) steuern.

*Referenz: Kap. 11 – Reboot*

### VAL-010 (INFO)

*Ursache:* Hartcodierter Program-Files-Pfad statt %-Variable.

*Behebung:* Durch %ProgramFiles% bzw. %ProgramFiles(x86)% ersetzen (QuickFix).

*Referenz: Kap. 4 – Variablen*

### VAL-011 (INFO)

*Ursache:* Nach einem Deinstallations-/MSI-Aufruf fehlt Sleep vor der Bereinigung (Dateisperren).

*Behebung:* Sleep 3000 zwischen Aufruf und DelTree/Bereinigung einfügen.

*Referenz: Kap. 6 – Sleep*

### VAL-012 (ERROR)

*Ursache:* Standardsektion fehlt (das Skeleton verlangt Vollständigkeit, auch leere Sektionen).

*Behebung:* Sektion anlegen (QuickFix) oder Vorlage neu erzeugen.

*Referenz: Kap. 3 – Sektions-Referenz*

### VAL-013 (ERROR)

*Ursache:* Pflichtfeld in [Application] fehlt (Identität/Reparaturpfad unvollständig). Kurznamen (ProductNameShort/DeveloperNameShort) sind optional und werden als Info gewertet.

*Behebung:* Feld ergänzen – der PackageCreator setzt alle Pflichtfelder vor.

*Referenz: Kap. 3 – [Application]*

### VAL-014 (ERROR)

*Ursache:* [Setup] Version fehlt oder ist leer (Setup.inf-Dialekt).

*Behebung:* Version=14.2 setzen.

*Referenz: Kap. 3 – [Setup]*

### VAL-015 (ERROR)

*Ursache:* SrcDir/SetupInfDir verletzen das Install\Setup.inf-Layout oder [Environment] CommonSetupDir fehlt.

*Behebung:* SrcDir=.. und SetupInfDir=Install setzen; CommonSetupDir ergänzen.

*Referenz: Kap. 1 – Paketaufbau*

### VAL-016 (WARNING)

*Ursache:* MsiExec /I ohne die Empfehlung ALLUSERS="1" REBOOT=REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn.

*Behebung:* Flags ergänzen (Snippet msi-install zeigt das Muster).

*Referenz: Kap. 13 – MSI-Paketierung*

### VAL-017 (INFO)

*Ursache:* /AW ist in SetupInfo gesetzt – Erinnerung, den Depot-Befehl zu spiegeln.

*Behebung:* Im Software-Depot unter Paketeigenschaften → Prüfung → Befehl /AW ergänzen.

*Referenz: Kap. 2 – Benutzerteil*

### VAL-018 (INFO)

*Ursache:* '-'-Präfix in [Reg:…] löscht erst bei der Deinstallation – häufig Missverständnis.

*Behebung:* Für Löschung während der Installation CallHidden reg.exe delete … nutzen (Snippet vorhanden).

*Referenz: Kap. 7 – Registry*

### VAL-019 (WARNING)

*Ursache:* Der Befehl ist nicht in der Setup.inf-Befehlsreferenz dokumentiert (Tippfehler oder exotischer Befehl).

*Behebung:* Schreibweise gegen die Befehlsliste prüfen (Hilfe → Setup.inf-Hilfe).

*Referenz: Kap. 6 – Befehle*

### VAL-020 (ERROR)

*Ursache:* If-Zeile mit Then, aber ohne EndIf in derselben Zeile – entspricht nicht der Referenz-Syntax.

*Behebung:* EndIf am Zeilenende ergänzen.

*Referenz: Kap. 5 – If/Then/Else/EndIf*

### VAL-021 (WARNING)

*Ursache:* Verwendete %Variable% ist weder eingebaut noch im Dokument definiert (Environment/Strings/Application/Set).

*Behebung:* Variable in [Environment] definieren oder Schreibweise korrigieren.

*Referenz: Kap. 4 – Variablen*

### VAL-022 (ERROR)

*Ursache:* [Reg:…]-Sektionen sind rein deklarativ; prozedurale Befehle wie If, CallHidden oder RegModify verlieren hier ihre Bedingung oder sind ungültig.

*Behebung:* Befehle in [Set:…]-Sektionen verschieben; bedingte Registry-Änderungen mit CallHidden reg.exe add in [Set:Then_…] ausführen.

*Referenz: Kap. 7 – Registry*

### VAL-023 (WARNING)

*Ursache:* Variable wird über dynamische Funktion (z. B. GetUninstallKeyName) oder Registry/INI zugewiesen, wird aber in dieser Sektion nicht mit 'ReplaceEnv <Var>' aufgelöst.

*Behebung:* Nach 'Set <Var> = ...' ein 'ReplaceEnv <Var>' ergänzen, damit Platzhalter sofort expandiert werden.

*Referenz: Kap. 4 – Variablen*

### VAL-024 (WARNING)

*Ursache:* Befehl 'Abort' wird ohne vorangehendes 'ErrorLogMsg' aufgerufen; im Empirum-Fehlerprotokoll fehlt dadurch eine aussagekräftige Fehlerursache.

*Behebung:* Vor 'Abort' ein 'ErrorLogMsg <Meldung>' einfügen.

*Referenz: Kap. 8 – Fehlerbehandlung*

### VAL-025 (ERROR)

*Ursache:* Ungültige Zuweisungssyntax 'Sleep=…'. Befehl 'Sleep' verlangt Befehlssyntax 'Sleep <Millisekunden>' ohne Gleichheitszeichen.

*Behebung:* In 'Sleep <Millisekunden>' korrigieren (z. B. 'Sleep 3000').

*Referenz: Befehlsreferenz – Sleep*

### VAL-026 (ERROR)

*Ursache:* Befehl oder Prädikat existiert nicht im Empirum-Interpreter 26.1.0 (verifiziert gegen Setup.exe/Setup64.exe). Betroffen u. a. CheckLanAdministrator, Run sowie die Alias-Prädikate FileExists/DirExists/RegKeyExists/RegValueExists/ProcessExists/ServiceExists. Unbekannte Befehle werden vom Interpreter als Programmstart interpretiert (SETUP_ERR_UNRECOGNIZABLE) und versagen dadurch still.

*Behebung:* Umbenennungs-QuickFix nutzen (z. B. Run→CallHidden, FileExists→DoesFileExist, DirExists→DoesPathExist, RegValueExists→DoesRegKeyExist mit ValueName-Komponente). Für Dienst-Prüfungen DoesRegKeyExist auf HKLM,SYSTEM\CurrentControlSet\Services\<Name> verwenden; CheckLanAdministrator-Zeilen entfernen.

*Referenz: Verifikation – Empirum-Interpreter 26.1.0*

### VAL-027 (WARNING)

*Ursache:* Registry-Typcode in [Reg:…] entspricht nicht der offiziellen Typentabelle des Empirum-Interpreters (z. B. alter PackagerX-QWORD-Code 0x00010004 statt 0x00040001). Falsche Codes führen zu falschen Werttypen oder zu ignorierten Zeilen.

*Behebung:* Typcode korrigieren (QuickFix bei bekannten Fehlcodes). Offiziell: REG_SZ=0x00000000, REG_BINARY=0x00000001, REG_MULTI_SZ=0x00010000, REG_DWORD=0x00010001, REG_EXPAND_SZ=0x00020000, REG_NONE=0x00020001, REG_QWORD=0x00040001, REG_BINARY_SZ=0x10000001; additive Verhaltens-Flags +0x2/+0x8/+0x10 sind erlaubt.

*Referenz: Verifikation – Empirum-Interpreter 26.1.0 *

### VAL-028 (WARNING)

*Ursache:* Interaktive Befehle (Prompt, AskKillProcesses, CloseWindow, SplashDialog*) in einem Paket mit Silent-Level /S0 oder /S1 – Dialoge und Prompts werden auf diesen Stufen unterdrückt (dokumentierte Silent-Semantik des Setup.exe-Aufrufs).

*Behebung:* Entweder das Silent-Level erhöhen (/S2 zeigt Prompts) oder die Befehlslogik auf die Default-Antwort der [Prompts]-Definition umstellen und Default bewusst setzen.

*Referenz: Befehlsreferenz – Setup.exe-Schalter /S<Level>*

### VAL-029 (WARNING)

*Ursache:* 'AbortSilent' meldet dem Software-Depot 'Success' und führt den Benutzerteil trotzdem aus (dokumentierte 26.1.0-Semantik) – das Paket erscheint trotz Abbruch als erfolgreich.

*Behebung:* Für echte Fehler 'ErrorLogMsg' + 'Abort' verwenden; 'AbortSilent' nur für bewusstes, stilles Überspringen einsetzen.

*Referenz: Befehlsreferenz – AbortSilent*

### VAL-030 (ERROR)

*Ursache:* Setup.inf beginnt mit einem Byte Order Mark (BOM: EF BB BF, FF FE, FE FF oder Mojibake ï»¿). Der native Win32/MFC-Interpreter von Empirum (Setup.exe) kann die erste Sektion [SetupInfo] durch den BOM nicht erkennen und bricht sofort ab. Zudem kann der Matrix42 Package Editor die Datei nicht parsen und der Einzelschritt-Debug startet nicht.

*Behebung:* Datei ohne BOM als Windows-1252 (ANSI) speichern. Ein QuickFix steht zur Verfügung.

*Referenz: Empirum Knowledge Base – Zeichensatz Windows-1252 (ANSI/CP1252), kein BOM*

### VAL-031 (ERROR)

*Ursache:* Zeile enthält Zeichen, die im Windows-1252 (ANSI/CP1252)-Zeichensatz nicht darstellbar sind (z. B. typografische Sonderzeichen, Emojis, asiatische/kyrillische Zeichen) oder die Datei ist nicht als Windows-1252 deklariert. Empirum unterstützt ausschließlich Windows-1252. Beim Speichern als CP1252 schlägt die Kodierung fehl; beim Speichern als UTF-8 interpretiert Setup.exe die Zeichen fehlerhaft.

*Behebung:* Nicht unterstützte Sonderzeichen entfernen oder durch ASCII/CP1252-Äquivalente ersetzen.

*Referenz: Empirum Reference – Zeichensatz Windows-1252 (CP1252)*

### VAL-032 (ERROR)

*Ursache:* Benutzerkontext-Befehl (%AppData%, %LocalAppData%, %Desktop%, %Personal%, %Sendto% oder prozeduraler HKCU-Schreibzugriff) liegt außerhalb der CLIENT-Sektion, obwohl das Paket einen echten Benutzerteil besitzt. Im Maschinendurchlauf läuft die Zeile als SYSTEM und wirkt auf das SYSTEM-Profil statt auf den angemeldeten Benutzer (Benutzerkontext).

*Behebung:* Zeile nach [Set:Client] verschieben (CLIENT-Flag + /AW) – sofern sie nicht bewusst in beiden Durchläufen laufen soll; dann die MACHINE-Flags an den [Product]-Einträgen entfernen.

*Referenz: User-Parts: /AW, CLIENT/MACHINE*

### VAL-033 (ERROR)

*Ursache:* Doppelte [Set:Client]-Sektion: Empirum führt gleichnamige Sektionen zusammen, die Ausführungsreihenfolge wird unbestimmt – der Benutzerteil muss genau eine Sektion sein.

*Behebung:* Alle Benutzerbefehle in EINE [Set:Client]-Sektion zusammenführen (niemals zwei gleichnamige Sektionen emittieren).

*Referenz: User-Parts: Sektions-Merge*

### VAL-034 (WARNING)

*Ursache:* MACHINE-Flag auf einem #Reg:-Aufruf, dessen Zielsektion HKCU-Einträge enthält. Die Sektion wird im Benutzerdurchlauf (/AW) übersprungen und die HKCU-Werte pro Benutzer stillschweigend nie geschrieben.

*Behebung:* MACHINE-Flag vom Registry-Aufruf entfernen, damit die Sektion in beiden Durchläufen läuft (HKLM-Schreibzugriffe sind idempotent). QuickFix verfügbar.

*Referenz: User-Parts: Flag-Tabelle #Reg:Product*
