# Changelog

## 1.1.0 (Erstes Open-Source-Release)

- **Release-Pipeline:** `.github/workflows/release.yml` baut bei Tag `v*` ein
  One-Dir-Paket, legt die Lizenztexte bei und veröffentlicht ZIP + SHA256 als
  GitHub-Release. `packaging/VERSION.json` zeigt auf das Release-Asset.
- **Lizenz:** MIT statt proprietär (`LICENSE`, `pyproject.toml`, Copyright-Hinweise,
  Statusbar und Feedback-ZIP). Drittanbieter-Hinweise in `THIRD_PARTY_LICENSES.md`,
  insbesondere die LGPL-3.0-Pflichten für PySide6/Qt.
- **Paket-Standard statt interner Konventionsbezeichnung:** Die Konventionsabkürzung ist
  aus Code, Symbolen, UI-Texten, Tests und Doku entfernt. Module:
  `empirum_core.setupinf_contract` und `empirum_core.skeleton_repair`; Konstanten
  `STANDARD_SECTIONS`, `APPLICATION_KEYS`, `PRODUCT_REFS`, `USER_PART_*`,
  `ERROR_SECTION_BODIES`; Funktionen `product_refs_for`,
  `missing_standard_sections`, `add_missing_standard_sections`,
  `repair_missing_standard_sections`. UI: „Standardsektionen“, „Standardskelett“,
  „standardkonform“. Doku: `docs/setupinf-standard-alignment.md`, `docs/user-parts.md`.
- **Bereinigung:** Interne Verifikations- und Handoff-Dokumente entfernt; Beispieldaten
  in Tests und Fixtures auf generische Namen umgestellt; Support-Wege auf GitHub-Issues
  umgestellt; Herkunftsangaben aus Binäranalysen aus Code und Doku entfernt.
- **Qualität:** `ruff check` und `mypy --strict` vollständig grün (E501-Ausnahme nur
  für die Hilfetext-Datenbank), Importreihenfolge sortiert, doppelte
  `Abort`-Diagnose-Blöcke zusammengeführt, Typannotationen in Hilfe-Dialog und
  Linter ergänzt.
- **Repo-Hygiene:** `.gitattributes` schützt die CRLF-Golden-Dateien, Community-Dateien
  (`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`) ergänzt.

## 1.0.3 (Shell-Verknüpfungen: Ablageort wählbar — Common Programs neben CommonDesktop)

### Shell-Verknüpfungen: Ablageort wählbar — Common Programs neben CommonDesktop

`[Shell:Product]`-Verknüpfungen können jetzt wahlweise im All-Users-Startmenü
(%CommonPrograms% → Startmenü\Programme) oder auf dem All-Users-Desktop
(%CommonDesktop%) angelegt werden:

- **Editor (ShellLinks-Panel)**: Neue Combobox „Ablageort" mit den Optionen
  „Common Desktop – All Users Desktop (%CommonDesktop%)" (Default, wie bisher)
  und „Common Programs – All Users Startmenü (%CommonPrograms%)". Der
  Anzeigename darf bei Common Programs einen Unterordner enthalten
  (z. B. `Vendor\App` → `%CommonPrograms%\Vendor\App`).
- **PackageCreator/Wizard („Startmenü-Icon hinzufügen")**: Neue Combobox
  „Ablageort" (Default Common Programs, zusätzlich CommonDesktop); bei
  CommonDesktop wird das Feld „Startmenü-Unterordner" deaktiviert, da
  Desktop-Links keinen Unterordner erhalten. Die Tabelle „Paket-Ergänzungen"
  zeigt in der Spalte „Ablagepfad" jetzt den echten Zielpfad je Verknüpfung.
- **Datenmodell/Generator**: `ShellLinkSpec.destination`
  (`common_programs` | `common_desktop`, Default `common_programs`); der
  Template-Generator emittiert je nachdem `%CommonPrograms%\[Unterordner\]Name`
  oder `%CommonDesktop%\Name`.
- **Tests**: `test_template_shell_link_common_desktop`,
  `test_shell_link_add_destination_choice` sowie Erweiterungen in
  `test_creator_enhancements_ui.py`; Gesamt-Suite bleibt grün (415 Tests).

## 1.0.2 (User-Parts + Befehlsreferenz: undokumentierte Einträge kennzeichnen)

### Befehlsreferenz: nicht dokumentierte Befehle/Einträge (Klasse 1) kennzeichnen

Die Hilfe/Befehlsreferenz (Hilfe → Setup.inf-Hilfe bzw. Setup.inf-Befehlsreferenz)
macht jetzt immer sichtbar, welche Einträge zu den nicht dokumentierten
undokumentierte Konstrukten gehören (verifiziert im Interpreter 26.1.0 — Befehlsermittlung
aus dem Schwesterprojekt UEMAgentWindows —, aber in der gesamten offiziellen
Matrix42-Hilfe nicht vorhanden):

- **Übersichtsseite**: Neue Anmerkung „Nicht dokumentierte Befehle & Einträge (Klasse 1)"
  nennt die 4 undokumentierte Befehle namentlich (`BlockInput`, `CollapseEnv`, `Extract`, `RenDir`)
  sowie die Anzahl der weiteren undokumentierten Einträge (24 Variablen, 24 $-Gruppen,
  11 [Application]-Keys, 2 Setup.exe-Schalter /SX und /Y:) — inklusive Hinweis auf das
  experimentelle Feature-Flag (Datei → Einstellungen… → Experimentell), unabhängig vom
  Flag-Zustand.
- **Baum**: Klasse-1-Einträge tragen zusätzlich das Suffix „(undok.)", damit sie auch in
  Suchergebnissen eindeutig als nicht dokumentiert erkennbar bleiben.
- **Detailseiten**: Undokumentierte Befehle und Variablen erhalten oben die orange
  Warnbox „⚠ UNDOKUMENTIERT (Klasse 1)" (einheitlicher Warnungstext, auch für die
  Gruppen-Seiten der $-Gruppen/[Application]-Keys/Schalter).
- **Tests**: `test_command_reference.py` erweitert (Overview-Anmerkung, Suffix-Kennzeichnung
  im Baum, Warn-Badge auf Detailseiten); Gesamt-Suite bleibt grün.

### User-Parts: [Set:Client], CLIENT/MACHINE-Flags, /AW-Kette, VAL-032..034

User-Parts werden so erzeugt, dass der Empirum-Installer Maschinen- und
Benutzerausführung eindeutig auflöst (Details: `docs/user-parts.md`).

- **PackageCreator/Wizard**: Neue Option „Benutzerteil-Sektion [Set:Client] erzeugen"
  mit Befehlseditor (ein Befehl pro Zeile). `PackageMetadata.user_context_commands`
  ist das Kontext-Modell (`user|machine`) je Befehl.
- **Templates (MSI/EXE/Script/Links)**: Bei User-Part erhält jeder Maschinen-Eintrag
  in `[Product]` den Zusatz `MACHINE` (kommagetrennt, unquoted), der User-Part wird
  als `#Set:Client, CLIENT` zuletzt emittiert; `[SetupInfo]` bekommt
  `Command line options=/S2 /AW`. `#Reg:Product` bleibt ohne `MACHINE`, wenn
  HKCU-Einträge vorliegen (VAL-006-Kette). CallHidden-Benutzerbefehle erhalten
  automatisch die 3010/0-ErrorLevel-Prüfung. Pakete ohne User-Part bleiben
  unverändert (`/S2`, keine Flags — Golden-kompatibel).
- **Contract**: `setupinf_contract.product_refs_for()` ist die neue Single Source of
  Truth für die kontextsensitiven `[Product]`-Refs; `PRODUCT_REFS` (Maschine)
  bleibt unverändert.
- **Skelett-Reparatur**: Trägt für eine bestehende `[Set:Client]`-Sektion den
  fehlenden `#Set:Client, CLIENT`-Aufruf nach (erzeugt nie selbst eine User-Part-Sektion);
  idempotent.
- **Linter**:
  - **VAL-006 (Gegenrichtung, ERROR)**: `CLIENT`-Sektion/Flag vorhanden, aber `/AW`
    fehlt ⇒ Fehler (Benutzerteil läuft nie); QuickFix ergänzt `/AW`.
    HKCU/VU_/AskKillProcesses ohne `/AW` bleibt WARNUNG.
  - **VAL-032 (ERROR)**: Benutzerkontext-Befehl (`%AppData%`, `%LocalAppData%`,
    `%Desktop%`, `%Personal%`, `%Sendto%`, prozeduraler HKCU-Schreibzugriff)
    außerhalb der CLIENT-Sektion, obwohl ein echter User-Part existiert.
    Deinstallations-/Reinstall-Pfade sind bewusst ausgenommen; ohne User-Part bleibt
    das bewusste Mitlaufen im Benutzerdurchlauf erlaubt.
  - **VAL-033 (ERROR)**: Doppelte `[Set:Client]`-Sektion.
  - **VAL-034 (WARNING + QuickFix)**: `MACHINE` auf einem `#Reg:`-Aufruf trotz
    HKCU-Einträgen in der Zielsektion.
- **Completer/Snippets**: `[Set:Client]`, `#Set:Client`, `#Set:Client, CLIENT`
  sowie Snippets `user-part` und `user-part-product-ref`; Learning-Content-Doku für
  VAL-032..034 inkl. `wizard.user_part`/`wizard.user_commands`-Tooltips.
- **Tests**: 25 neue Unit-Tests (`tests/unit/test_user_part.py`): Contract-Verträge,
  User-Part-Templates, HKCU-Mischfall, Merge/Idempotenz der Reparatur,
  Wizard-Collect sowie den Negativfall (Maschinenpaket ohne Flags).

## 1.0.0 (Final Release: Setup.inf Encoding-Standard, VAL-030/031, Pre-Deploy Readiness)

Offizielles **1.0.0 Release** von EMP-PackageX3.

- **Kritischer Setup.inf-Encoding-Fix (ANSI / Windows-1252 ohne BOM)**:
  - Generierte Pakete werden ausnahmslos als reines Windows-1252 (ANSI) ohne BOM
    und mit Windows-Zeilenenden (`\r\n`) geschrieben.
  - Beseitigt das sofortige Schließen („Blinken") von `Setup.exe` und ermöglicht
    den fehlerfreien Einzelschritt-Debug im Matrix42 Empirum Package Editor.
  - Umlaute und Sonderzeichen werden standardkonform als Einzelbyte (z. B. `ü` = `0xFC`)
    gespeichert, ohne UTF-8-Multibyte-Mojibake.
- **Neue Validierungsregeln (Linter)**:
  - **VAL-030 (ERROR)**: Erkennt UTF-8- und UTF-16-BOMs sowie Mojibake-Reste (`\ufeff`, `ï»¿`)
    und bietet einen automatischen 1-Klick-QuickFix (`strip_bom_and_set_cp1252`).
  - **VAL-031 (ERROR / WARNUNG)**: Prüft zeilenweise auf nicht in Windows-1252 darstellbare
    Zeichen inkl. exakter `U+XXXX`-Angabe und fängt undefinierte CP1252-Bytes (`81, 8D, 8F, 90, 9D`) ab;
    warnt bei abweichender Encoding-Deklaration inkl. QuickFix (`set_cp1252`).
- **Paket-Bereitstellungs-Gates & Reparatur**:
  - **PKG-009 (FAIL)**: Verhindert die Bereitstellung in Empirum PackageStore / MMC-Depot, wenn ein BOM vorhanden ist.
  - **PKG-010 (WARN)**: Weist auf abweichendes Encoding vor der Bereitstellung hin.
  - **PKG-011 (FAIL)**: Blockiert die Bereitstellung bei nicht in CP1252 dekodierbaren Bytes unter Nennung des Byte-Offsets.
  - **Auto-Repair**: Entfernt BOMs vollautomatisch und normalisiert Dokumente zu Windows-1252 (ANSI) mit WAL-Backup.
- **Vollständige Empirum 26.1.0-Kompatibilität**:
  - Verifizierte Befehls-, Funktions- und Variablenkataloge (~45 Befehle, 26 Funktionen, 65+ Variablen, 24 Copy-Flags, 19 Setup.exe-Schalter).
  - Reverse Uninstallation Execution Simulator (`/U`-Modus mit OP-008-Semantik).
  - Umfassende Byte-Level-Testabdeckung mit 100% Bestehensrate.

## 1.0.0-rc14 (Empirum 26.1.0: verifizierte Befehlsreferenz, P1-Korrekturen, Feature-Flag)

Vollständige Angleichung von Engine und Befehlsreferenz an den Setup.inf-Interpreter
**Matrix Empirum 26.1.0** (Verifikation gegen Setup.exe/Setup64.exe und die
Legacy-Hilfe).

- **P1-Korrekturen (K-01…K-03 + Run, „must-fix")**:
  - `CheckLanAdministrator` und `Run` existieren nicht als Befehle im Interpreter
    (0 Treffer; unbekannte Befehle werden als Programmstart interpretiert,
    `SETUP_ERR_UNRECOGNIZABLE`) → aus Katalog/Doku/Completer entfernt; neue
    **VAL-026 (ERROR)** erkennt die nicht-existierenden Konstrukte mit
    Umbenennungs-QuickFix (Run→CallHidden, FileExists→DoesFileExist,
    DirExists→DoesPathExist, …).
  - `SETUPINF_PREDICATES` auf die fünf verifizierten Prädikate reduziert
    (`DoesFileExist/DoesPathExist/DoesProcessExist/DoesRegKeyExist/DoesTextInFileExist`).
  - Registry-Typkonstanten auf die offizielle Tabelle korrigiert
    (`REG_QWORD=0x00040001`; `REG_NONE`/`REG_BINARY_SZ` ergänzt); neue Single
    Source of Truth `SETUPINF_REG_TYPES`; **VAL-027** prüft Typcodes inkl.
    Additivflags (+0x2/+0x8/+0x10) mit QuickFix für Altlasten; Doku-Tabellen
    (System_Prompt, Befehlsreferenz) korrigiert; Wizard-Dropdown um REG_QWORD.
- **Klasse-2-Referenzlücken (dokumentiert, risikofrei)**:
  - Katalog +~45 Befehle (AbortReboot/AbortSilent, XML-Befehle, Unzip/Unrar,
    Dienste- und komplette Druckerfamilie, WaitUntil*/WaitWhile*, SystemShutdown,
    Splash/PlaySound/ShowPicture, CallRunAs(Hidden), Arithmetik, lange/kurze
    Formen MD/MkDir…), +26 Set-Funktionen (Left/Right/Mid/Len, BitAnd/Or/XOr,
    IsDotNetVersionAvailable, ReadTextFile, …), +65 dokumentierte Variablen
    (Shell-Ordner, OS.*-Familie, Option-/SetupInf-/Zeitvariablen, $-Gruppen).
  - Neue Kataloge: Copy-Flags (CF-001…024), Setup.exe-Schalter (SW-001…019 mit
    exakter /S-Level-Semantik), Registry-Zusatzflags; Hilfe-Baum um „Copy-Flags",
    „Setup.exe-Schalter", „[Security:]-DSL" (Section 43: LocalUser/Privilege/
    FileDacl/RegDacl/NetShare/NetDomain) und „If-Operatoren" erweitert; neue
    Sektionen ([Prompts], [Services], [EventSources], [Admin]/[Client]/
    [Workstation], [Icons], [%Option%] …).
  - System_Prompt-Referenz: neues Kapitel 19 „Erweiterte Befehlsreferenz 26.1.0".
- **Engine-Semantik (OP-008, verifiziert)**:
  - Simulator + Ausführungs-Projektion: bei /U laufen nur `'-'`-Zeilen plus die
    Immer-Befehle (AddMeter, Beep, CD, Rem, ReplaceEnv, Set); Copy/MD/MkDir/Ren/
    Rename werden automatisch rückgängig gemacht (als „automatisch rückgängig"
    annotiert); Install überspringt DELETE-Refs, Uninstall DONTDELETE-Refs.
  - Simulator-State erweitert: Dienste (`services`), Shutdown-Flag, MkDir/RmDir/
    Rename/RenDir, Arithmetik auf Variablen, KillProcess-Extended-Parameter.
  - Neue Lint-Regeln: **VAL-028** (interaktive Befehle bei /S0–/S1 unterdrückt),
    **VAL-029** (AbortSilent meldet Success). VAL-022 deckt jetzt den gesamten
    Befehlskatalog ab.
- **Klasse-1-Befehle hinter Feature-Flag** (`undocumented_commands`,
  Einstellungen → Experimentell; default AUS): CollapseEnv, Extract, RenDir,
  BlockInput sowie 24 undokumentierte Variablen (u. a. %DstDir%), 24 $-Gruppen, undokumentierte
  [Application]-Keys und Schalter (/SX, /Y:) — im Completer/Linter/Hilfe-Baum
  nur bei aktivem Flag, mit deutlichen Warnhinweisen (kein Matrix42-Support).
  `lint_document(..., options=LintOptions(...))` neu; Simulator versteht
  CollapseEnv/RenDir.
- Zielversion-Angabe auf **Empirum 26.1** aktualisiert; statische
  „VAL-001…021"-Labels dynamisch aus der Regelbasis.

## 1.0.0-rc13 (Simulator Deinstallation & Setup.inf Härtung)

- **Simulator Deinstallation**: Korrektur der Ausführungsreihenfolge in `SimMode.UNINSTALL`
  auf echtes Reverse-Execution / Bottom-Up Verhalten (Zeilen- und Sektionsabarbeitung
  von unten nach oben gemäß Matrix42 Empirum `Setup.exe /U`).
- **Setup.inf Engine & Hardening**:
  - Härtung VAL-023..025 (Deadlock-Prävention, Berechtigungsprüfungen)
  - Vollständiges State-Tracking im Simulator (Dateien, Registry, beendete Prozesse, Variablen, Reboot)
  - Synchronisation der Befehls- und Variablenreferenzen

## 1.0.0-rc12 (Strukturierte Empirum-Hilfe)

- Hilfe → **Setup.inf-Befehlsreferenz…**: strukturierte, durchsuchbare Empirum-Referenz
  (Befehle gruppiert, If-Prädikate, Set-Funktionen, Variablen, Sektionen, Flags, Lint)
- Katalog ergänzt: Prädikate (`Does*` + Aliase), `GetUninstallKeyName`; Completer nutzt sie

## 1.0.0-rc11 (Befehlsreferenz)

- Hilfe → **Setup.inf-Befehlsreferenz…**: durchsuchbare Übersicht aller
  Empirum-Setup.inf-Befehle (Katalog) mit Syntax, Kurzbeschreibung,
  Uninstall-Hinweis und regelkonformem Beispiel; inkl. `CheckLanAdministrator`

## 1.0.0-rc10 (Review-Fixes: QuickFix, Suche, Startverhalten, Konsistenz)

- **„QuickFix anwenden“ ist jetzt echt.** VAL-012 war toter Code: der
  Fix wurde nie angeboten und `apply_first_quickfix` übersprang
  `note="insert_section"`. Jetzt fügen **Ctrl+.** bzw. das Kontextmenü der
  Diagnoseliste („QuickFix anwenden“) die fehlende Sektion direkt ein – die
  drei Fehler-Handler inklusive kanonischem `ErrorLogMsg`/`Abort`-Block, alle
  übrigen als leerer Stub. `QuickFix` trägt dafür das neue Feld `section_name`
  (rückwärtskompatibel, nur Keyword-Konstruktionen); das Anwenden ist idempotent
  (vorhandene Sektion ⇒ Hinweis statt Duplikat).
- **QuickFix-Pfade nachgezogen.** Beide Einstiege (Ctrl+. *und*
  Kontextmenü) flushen jetzt eine noch im 150-ms-Debounce stehende Eingabe,
  bevor sie die Sektion einfügen, und markieren das Dokument als geändert
  (`*` + Speicherabfrage beim Schließen); zuvor ging im Kontextmenü-Pfad eine
  gerade getippte Zeile verloren und die Änderung blieb unbemerkt. Umgekehrt
  faken Flushes ohne echte Änderung (F7 „Prüfen“, Speichern, wiederholte Fixes)
  kein `*` mehr; Prettifier und Skelett-Reparatur setzen das Flag explizit, wenn sie
  den Code wirklich verändern.
- **Editor-Suche: Tippen wird entprellt.** Statt pro Tastendruck einen
  vollständigen Trefferzähler über das Dokument laufen zu lassen, wird die
  Live-Suche 120 ms entprellt; Enter/Buttons/Groß-Klein-Schalter flushen sofort,
  ein geschlossener Balken emittiert gar nichts mehr. Zusätzlich: Status nur noch
  in **einem** `set_status` (der doppelte Aufruf hat den Trefferzähler
  überschrieben), Hinweis „· umgebrochen“ beim Wrap-Around, **F3/Shift+F3**
  nutzt bei geschlossenem Balken den letzten Suchbegriff weiter (öffnet keinen
  leeren Balken mehr) und **Esc** schließt die Suche auch dann, wenn der Fokus
  im Editor bzw. im Fenster liegt. `FindBar.is_open()` ersetzt das irreführende
  `isVisible()` (war `False`, solange das Fenster nicht angezeigt wurde).
- **Fensterstart blockiert nicht mehr an Netzlaufwerken.** Der
  Lokal-Depot-Abgleich lief bisher **vor** dem Anzeigen des Fensters und
  `except (OSError, ValueError)` kann einen SMB-Hänger nicht abfangen. Er läuft
  jetzt über `showEvent` (+`QTimer.singleShot`) nach dem ersten Paint und wird
  für UNC-Pfade (`\\Server\Share\…`) komplett übersprungen.
- **Completer bietet das echte Standardskelett.** `SECTIONS` ist jetzt
  `STANDARD_SECTIONS` statt einer eigenen Liste mit erfundenen Altnamen
  (`Set_Install`, `Set_Uninstall`, `Error_Install`, `Error_Uninstall`).
- **Eine Quelle für `[Product]`-Refs und Fehler-Bodies.** Templates und
  `skeleton_repair` teilen sich `PRODUCT_REFS`/`ERROR_SECTION_BODIES` in
  `empirum_core.setupinf_contract`. Damit laufen generierte und reparierte Pakete
  beim Uninstall identisch ab (`#Set:Deinstallation` steht wieder **hinter**
  `#Reg:OnUninstallProduct`, entsprechend der bottom-up-Reihenfolge von
  Empirum). Die Vorlagen-Ausgabe bleibt byte-identisch (Golden-Corpus).
- **Skelett-Reparatur legt sein Backup außerhalb des Pakets ab.** Der
  WAL-Backup landete in `<Paket>\Install\.emp_packagex3_bak` und wurde beim
  Deploy mitkopiert (nur `deploy_package` filtert ihn). Neu:
  `%LOCALAPPDATA%\HodriusSystems\EMP-PackageX3\backups\<Paketname>\`
  (`default_repair_backup_dir`, per `backup_dir=` überschreibbar).
- **Coverage-Maske entschärft.** Der pauschale Ausschluss `raise TypeError`
  ist aus der pyproject-Konfiguration entfernt; der einzig betroffene, defensiv
  unerreichbare Zweig in `serializer/serialize.py` trägt jetzt ein lokales
  `# pragma: no cover`. Künftige echte `TypeError`-Pfade bleiben sichtbar.
- **Fix: ungespeicherte Änderungen gehen beim Schließen nicht mehr verloren.**
  Ein Tastaturanschlag innerhalb des 150-ms-Debounce-Fensters war noch nicht in
  `_dirty` sichtbar, `closeEvent`/`_confirm_maybe_save` prüften aber nur dieses
  Flag. Die ausstehende Änderung wird jetzt vorher geflusht; der Fenstertitel
  zeigt den Änderungszustand (`*`).
- **Skelett-Reparatur: Fehler-Handler mit kanonischem Abort-Block.**
  `skeleton_repair` legt `[Set:InstallationError]`/`[Set:ReinstallationError]`/
  `[Set:DeInstallationError]` mit den Standard-Bodies (`ErrorLogMsg`/`Abort`, im
  Deinstallationspfad negiert) statt leer an; `[RebootRequired]` bleibt bewusst
  leer (kein erzwungener Reboot). Alle übrigen Sektionen bleiben leere,
  verhaltensneutrale Stubs.
- **Coverage-Gate über alle vier Pakete.** `pytest` misst jetzt `empirum_core`,
  `emp_packagex3`, `empirum_services` und `empirum_infra`; die Paketschwellen
  erzwingt `scripts/check_coverage_gates.py` als eigener CI-Schritt.
- **Repo-Hygiene:** `.kilo/`, `.kilocode/` und `.emp_packagex3_bak/` sind jetzt
  in `.gitignore` (bisher nur lokal in `.git/info/exclude`).
- **Nachlese (Review-Nachzügler):** F3/Shift+F3 bei geschlossenem Suchbalken
  meldet Begriff und Trefferzahl jetzt in der Statusleiste – vorher schrieb der
  Pfad in die Trefferanzeige des *versteckten* Balkens und blieb unsichtbar.
  Angehängte Sektionen (Skelett-Reparatur, „QuickFix anwenden“) halten den einen
  Leerzeilen-Abstand wie der Prettifier, und `[Product]`-Refs werden **vor**
  abschließenden Leerzeilen eingefügt – reparierter Code braucht damit keinen
  zweiten Prettify-Lauf mehr. Eine akzeptierte Encoding-Auswahl setzt `*`
  (Speicherabfrage beim Schließen), weil sie den nächsten Schreibvorgang
  bestimmt; Abbrechen lässt das Dokument unverändert schreibgeschützt.
- **Hygiene:** `empirum_services.app_paths.app_data_dir()` ist die eine Quelle
  für `%LOCALAPPDATA%\HodriusSystems\EMP-PackageX3` (Settings, Logs, Backups)
  und respektiert ein umgeleitetes `LOCALAPPDATA`; `FindBar` bekommt für die
  Suchsteuerung eine öffentliche API (`term`/`set_term`/`search`/`dismiss`);
  die UNC-Erkennung nutzt `PureWindowsPath().drive` statt Präfix-Vergleich (auch
  `//server/share` und `\\?\UNC\...` werden erkannt); die kanonischen
  Fehler-Bodies sind als `MappingProxyType` eingefroren.

## 1.0.0-rc9 (Linter-Verfeinerungen & Dynamisches MSI-Reinstall)

- **VAL-008 Ausnahme für `taskkill`:**
  Aufrufe von `taskkill` bzw. `taskkill.exe` (z. B. `CallHidden cmd.exe /c taskkill /F /IM "..."`)
  benötigen keine zwingende `%ErrorLevel%`-Prüfung mehr. Das Beenden von Prozessen vor der Installation
  ist Best-Effort (Exitcode 128 bei nicht laufendem Prozess ist harmlos).
- **VAL-013 Herabstufung von Kurznamen:**
  Fehlende `ProductNameShort` und `DeveloperNameShort` im Abschnitt `[Application]` erzeugen keinen
  `ERROR` mehr, sondern werden als `INFO` ausgewiesen, da Kurznamen in modernen Paketen selten genutzt werden.
- **Snippet `msi-dynamic-reinstall` hinzugefügt:**
  Neues Snippet unter **Werkzeuge → Snippet: Dynamischer MSI-Reinstall…** zur dynamischen
  Erkennung von installierten MSI-Produkt-GUIDs (x64 und x86) via `GetUninstallKeyName`
  und bedingter Verzweigung via `DoesRegKeyExist` für saubere Reinstallationen.

## 1.0.0-rc8 (PackageCreator Ergänzungen)

- **PackageCreator Ergänzungen (Variante 1 - Tabbed Step):**
  Neuer Assistenten-Schritt mit drei Reitern für erweiterte Paketierungsaufgaben:
  - **Ordner kopieren:** Automatisches Bereitstellen von Quellordnern unter `%Src%\Files\...`
    und Ausführung via `cmd /c xcopy ... /S /H /E /V /Y` sowie Deinstallations-Bereinigung (`-DelTree`).
  - **Registry & .reg:** Import von `.reg`-Dateien via `reg.exe import` (Ablage unter `Files\Reg\`)
    oder wahlweise Konvertierung in native `[Reg:Product]`-Zeilen; Direkteingabe von Registry-Werten;
    automatische Erkennung von `HKCU` und Aktivierung des `/AW`-Benutzerteils.
  - **Startmenü-Icons:** Erstellung von AllUsers-Verknüpfungen in `[Shell:Product]` unter `%CommonPrograms%\...`.

## 1.0.0-rc6 (Simulator-Werkzeugfenster)

- **Simulator neu als nicht-modales Werkzeugfenster** (loest die alte
  MessageBox ab, die auf 40 Aktionen/25 Luecken gekuerzt war und nicht
  scrollbar): Baumansicht aller Aktionen gruppiert nach Sektion in
  Abarbeitungsreihenfolge, Luecken als eigene Gruppe mit Warnbalken,
  Endzustand (Dateien), Volltext-Filter, Modus-Umschalter
  Installation/Deinstallation im Fenster.
- **Doppelklick springt zur Zeile** im Editor (Markierung wie im
  Diagnose-Panel) - Editor bleibt nebenbei bedienbar, „Neu simulieren“
  aktualisiert nach Aenderungen.
- **Text-Export** des kompletten Reports (wie Diagnose-Export);
  Aktions-Tooltips zeigen Befehls-Semantik/Uninstall-Hinweis
  (Anschluss an die Setup.inf-Akademie); hell/dunkel themekonform.

- **Fehlende Standardsektionen per Klick ergänzen** (löst VAL-012-Blocker vor
  dem Deploy, typisch bei konvertierten Bestandspaketen):
  PackageStore-Dialog bietet bei VAL-012 „Fehlende Standardsektionen
  ergänzen…“ an (WAL-Backup, danach erneute Prüfung); im Editor als
  Werkzeuge → Fehlende Standardsektionen ergänzen (mit Undo).
  Leere Stubs in kanonischer Standard-Reihenfolge + kanonische #Aufrufe in
  [Product]; Encoding/BOM/CRLF bleiben erhalten; idempotent.
  Implementierung: `empirum_core.skeleton_repair` /
  `repair_missing_standard_sections`.

## 1.0.0-rc7 (Editor-Suche)

- **Suche im Setup.inf-Editor** (Nutzerwunsch): Strg+F oeffnet eine
  Suchleiste unter dem Editor (Suchbegriff, Weiter/Zurueck,
  Gross/Klein-Umschalter, Live-Trefferzaehler, Esc schliesst).
  F3 / Umschalt+F3 suchen weiter, Suche mit Wrap-around; Treffer werden
  im Editor markiert, bei Strg+F wird eine bestehende Auswahl als
  Suchbegriff uebernommen. Menue: Bearbeiten -> Suchen/Weitersuchen.

## 1.0.0-rc7 (Befehlskatalog: MD)

- **`MD` (Verzeichnis anlegen) in den Befehlskatalog aufgenommen** -
  Beta-Meldung: VAL-019 warnte zu Unrecht bei `MD C:\...`-Zeilen aus
  migrierten Paketen (Feld-ueblich, dokumentiert u. a. auf
  wpm-blog.de; fehlte in der gebuendelten Referenz). COMMAND_DOCS
  Eintrag (Syntax/Uninstall-Verhalten: Aufraeumen via DelTree) und
  Schnellkurs regeneriert.

## 1.0.0-rc7 (Simulator-Tabellenlayout)

- **Spalten-Überlappung im Simulator-Fenster behoben** (Nutzer-Meldung
  aus der Beta: Nummer und Befehlstext überlagerten sich bei
  DPI-Skalierung >100%): feste Pixelbreiten ersetzt durch
  ResizeToContents (Nummer/Befehl/Zeile) + Stretch für Detail;
  Gruppenzeilen (Sektionen, Lücken, Endzustand) laufen jetzt über die
  volle Breite (setFirstColumnSpanned) und können nicht mehr in der
  Befehls-Spalte gequetscht werden.

## 1.0.0-rc7 (Beta-Feedback-Härtung)

- **Globaler Crash-Hook:** unbehandelte Ausnahmen (auch aus Qt-Slots)
  landen mit Traceback im Rotationslog statt im Leeren zu verschwinden
  (Windowed-EXE ohne Konsole); die App bietet danach direkt das
  Feedback-Paket an (crash_hook.py, an exekutierhaften Positionen
  reentrancy-gesichert, verkettet den bisherigen excepthook).
- **Editor-Hover stabilisiert:** der allgemeine Editor-Tooltip und die
  Befehls-/Sektions-Tooltips kaempften um die Anzeige (Flackern).
  Jetzt ein Mechanismus: ueber Keyword wird der native Tooltip
  unterdrueckt und der Kontext-Tip pro Wort einmalig angezeigt,
  beim Verlassen restauriert. **Zusaetzlich gefixt:** Befehls-Tooltips
  trafen wegen Groß-/Kleinschreibung nie zu (case-insensitives
  lookup_command) - sie funktionierten bisher gar nicht.
- Beta-Checkliste: Meldungs-Vorlage (Betreff-Schema, Schritte,
  Erwartet/Passiert, Schweregrade P0-P3, Datenschutz-Hinweis).

## 1.0.0-rc6 (Fixes)

- **Readiness-Ordering-Fix (Deploy-Sicherheit):** Lint-ERRORs wurden von
  WARN-Items maskiert (PKG-008/007) - ein Paket mit fehlenden
  Standardsektionen wurde als deploybar gemeldet. ERROR blockiert
  jetzt immer.
- **VAL-016 erkennt `MsiExec.exe`** (mit .exe-Suffix) und meldet dann
  gezielt die fehlenden Standard-Flags statt 'MSI-Paket ohne MsiExec /I'.
- **Katalog ergaenzt:** `%AppData%` und `%LocalAppData%` sind laut
  Referenz dokumentierte Variablen - VAL-021 warnt bei ihnen nicht mehr
  (False Positive bei konvertierten Paketen).

- **Explorer-Oeffnen repariert:** `emp-packagex3 C:\Paket\Install\Setup.inf`
  bzw. Oeffnen-mit im Windows Explorer laedt die Datei direkt (seit rc4
  brach die strict-CLI das ab - unbekannte Argumente beendeten die App
  unsichtbar mit Exit 2). Unbekannte Flags failen weiterhin mit Exit 2.
- Schnellkurs K8: Tippfehler (meldt -> meldet) korrigiert;
  docs/setupinf-schnellkurs.md regeneriert


## 1.0.0-rc5

- **Lerncenter** (Hilfe → Setup.inf-Schnellkurs…): 8 didaktisch gestufte
  Kapitel mit Merksätzen, Systembeispielen und Selbsttest-Fragen;
  vollständige Sektions-Referenz (24 Typen), Befehls-Referenz inkl.
  Uninstall-Verhalten und Lang-Erklärungen aller VAL-Diagnosen;
  Volltextsuche und HTML-Export – komplett offline/frozen-fähig
- **Workflow-Tab „Ausführungslogik“:** nummerierte echte Ausführungs-
  reihenfolge für Installation (top-down, DONTDELETE) und Deinstallation
  (bottom-up, DELETE/'-‘-Zeilen) inkl. Shell:Product-Sonderrolle und
  Kurzbedeutung je Schritt
- **Editor-Hover** (Tooltip-Modus): Befehle zeigen Syntax/Semantik/
  Uninstall-Hinweis, Sektionsköpfe die Referenz-Bedeutung
- **Diagnose-Details:** Kontextmenü in der Diagnoseliste mit Ursache/
  Behebung/Referenz je VAL-Code


## 1.0.0-rc4

- **Befehls-/Variablenkatalog** (`setupinf_contract.SETUPINF_COMMANDS` /
  `SETUPINF_VARIABLES`): maschinenlesbar aus der Befehlsreferenz abgeleitet;
  Completer, Snippets und Linter speisen sich daraus (Drift wie
  `%ProgramFilesSys%` damit ausgeschlossen)
- **Shell-Link-Editor** schreibt standardkonforme `[Shell:Product]`-Zeilen
  (`"%CommonDesktop%\Name", "Ziel"`) inkl. ShellLinks/CommonShellLinks=1 –
  die undokumentierte `[CreateLinks]`/`LinkName`/`LinkPath`-Syntax wird nicht
  mehr erzeugt
- **Snippets & QuickFixes im Referenz-Command-Style:** `If … Then "…" EndIf`
  einzeilig, `Sleep 3000` statt `If=`/`Sleep=` (errorlevel-block,
  uninstall-error-pair auf [Set:DeInstallationError], msi-install,
  VAL-008-Snippet, VAL-011-QuickFix)
- **Fehler-/Reboot-Maske** bearbeitet die Fehlersektionen der Vorlage
  ([Set:InstallationError]/[Set:ReinstallationError]/[Set:DeInstallationError],
  Command-Style mit '-'-Präfix) statt Legacy-`[Error_*]`-KV-Sektionen
- **VAL-019** (WARN): Befehl nicht in der Referenz dokumentiert ·
  **VAL-020** (ERROR): If mit Then ohne EndIf · **VAL-021** (WARN):
  undefinierte `%Variable%` (Built-ins ∪ Environment/Strings/Application/Set)
- **Links-Template** verwendet `%CommonPrograms%` statt des undokumentierten
  `%CommonStartMenu%` (von VAL-021 gefunden)


## 1.0.0-rc3

Umfassende Behebung der Befunde aus Konsistenzprüfung & Code-Review (alle Stufen):

- **PackageStore:** Pfad-Traversal über Hersteller/Produkt/Version geschlossen
  (`.`/`..`, trailing dots, reservierte Namen + Containment-Guard); `rmtree` nur
  mit Overwrite, mit Read-only-Retry; Dry-Run-Bestätigungsfluss im Dialog
- **Update-Check:** Pre-Release-Semantik korrekt (`1.0.0-rc2 < 1.0.0`) – RC→Final
  wird erkannt; BOM-tolerante Manifeste, 1-MiB-Limit, Timeout-Weitergabe
- **Core:** Roundtrip-Bruch durch `str.splitlines()` behoben (Steuerzeichen
  bleiben Zeileninhalt); VAL-015 akzeptiert gequotete Werte; VAL-006/001/016
  werten Kommentare nicht mehr aus (frische Templates lint-clean); VAL-007
  kennt die gequotete Registry-Form; VAL-008/011 erkennen auch
  `CallHidden`-RawLine-Stil; VAL-010-QuickFix nutzt nur definierte Variablen;
  Prettify rechnet Zeilen-Spans neu; `LexerError` als echter Fehlervertrag
- **Templates/Snippets:** unbekannter Vorlagentyp → ValueError;
  Metadaten-Injection (CR/LF) wird neutralisiert; `msi-install`-Snippet standardkonform
- **Services/Infra:** Runner expandiert den Default-Setup.exe-Pfad, hat
  Subprocess-Timeout (900 s) und UTF-8-Ausgabe; PE-Inspector degradiert statt zu
  crashen; Generator sanitized die Produktversion, sichert Setup.inf per WAL-Backup
  und warnt bei fehlender Installer-Quelle; fs_safe gegen Temp-/Backup-Kollisionen;
  MSI-COM-Handles werden freigegeben, Architektur-Default „Unknown“
- **UI/Robustheit:** Fehlerdialoge statt durchschlagender Exceptions in Slots;
  Ungespeichert-Nachfrage beim Schließen + „Neu“; Diagnose-Sprung ohne
  Markierungs-Akkumulation; Completer fügt Vorschläge tatsächlich ein (kontext-
  sensibil für `[Sektion]`, `#Set:…`, `%Var`); Shell-Link-Panel erhält bestehende
  Zeilen; Einstellungen atomar/korrupt-sicher; Log-Ordner-Wechsel wirkt sofort;
  Encoding-Dialog bewahrt BOM; Fehler-/Reboot-Maske befüllt aus dem Dokument;
  Wizard validiert Pflichtfelder; CLI `--help`/Exit-Codes; Dark-Theme für
  Einstellungs-/Wizard-Dialoge, Diagnose-Farben und Header
- **Skripte/Packaging:** `build_onedir.ps1` läuft auf Fresh Clones (uv-Erkennung,
  Exitcode-Prüfung); `publish_local_depot.ps1` schreibt BOM-frei (PS 5.1 sicher);
  `sign_exe.ps1` mit Exit-Codes; Spec ohne Legacy-Kwargs, VERSION.json gebündelt;
  Release-Gates mit sauberen Fehlern und Platzhalter-Warnung
- **Hygiene:** Mypy/CI decken alle vier Pakete ab (11 Typfehler behoben);
  `dist-known-good/` ignoriert; `pytest-qt` entfernt; README kanonische uv-Aufrufe

## 1.0.0-rc2

- standardkonforme PackageCreator-Templates (MSI/EXE/Script/Links)
- Setup.inf-Hardening: alle Standardsektionen (inkl. Nice-to-Have),
  `setupinf_contract`, MSI `ALLUSERS`/`ARPSYSTEMCOMPONENT`, Unattend `AppActive`/`Processes`
- VAL-012…018 Strukturregeln; VAL-001 erkennt `#Set:…, FLAGS` / bare `#Section`
- VAL-006/017: `/AW` bei HKCU/VU_/AskKillProcesses + Depot-Hinweis; Lexer akzeptiert Keys mit Leerzeichen
- VAL-018 + Snippet: `-HK…` in `[Reg:…]` = Deinstall; Install-Löschung via `reg.exe`
- PackageCreator fragt nach Erzeugen **nicht** mehr automatisch nach PackageStore-Deploy
- Paketprüfung vor PackageStore-Deploy (`package_readiness`)
- Simulator folgt standard `[Product]` → `Set:Product` / `InstallMSI`
- Wizard: EXE-Silent-Presets, AskKillProcesses, MSI ProductCode → `V_ProductCode`
- Hilfe → Feedback-Paket (Logs als ZIP)
- Generate: UTF-8 BOM + CRLF; Doku `docs/setupinf-standard-alignment.md` + `docs/reference/`
- Primärziel Empirum **25.4** in Versionsmatrix / Beta-Checkliste
- Tooltip-Modus (Hilfe → Tooltip-Modus / F1): Lernhilfen für Menüs und Felder
- PackageCreator & Einstellungen: übersichtlichere Abschnitte, Hilfetexte, Scroll-Layout
- App-Icon (Paket/Setup.inf-Motiv) für Fenster, Taskleiste und Onedir-EXE

## 1.0.0-rc1

- Release Candidate: automatisierte Release-Gates (`scripts/check_release_gates.py`)
- App-Depot Publish-Skript (`scripts/publish_local_depot.ps1`)
- Beta-Checkliste für Paketierer (`docs/beta-checklist.md`)
- PackageStore-Deploy (0.5.2) in RC enthalten

## 0.5.2

- Deploy fertiger Setup.inf-Pakete nach `%EmpirumServer%\\Configurator$\\PackageStore`
- Einstellungen: EmpirumServer, PackageStore-Pfad, Store-Modus (Vendor/Flat)
- Menü Werkzeuge + optionaler Hinweis nach PackageCreator
- Doku `docs/package-store-deploy.md`

## 0.5.1

- Signaturanleitung `docs/sign-anleitung.md`
- Lokales Depot (Dokumente\\EMP-PackageX3-Depot), HTTP später über dieselbe Einstellung
- Beta-File-Logging (Rotating) + Log-Ordner im Menü, `--debug`

## 0.5.0

- Einstellungen (Theme, Runner-Whitelist, Update-URL) persistent
- Update-Check gegen Depot-VERSION.json
- Signatur-Hilfsskript `scripts/sign_exe.ps1`
- CI: mypy für Core/Services/Infra, Manifest-Sanity; ARM64 als 1.1 dokumentiert

## 0.4.0

- WAL-Backup + Encoding-Dialog bei Mehrdeutigkeit (R-02)
- MSI-Inspector mit Mock/Fixture-Backend für CI
- Dark/Light-Theme, Diagnose-Export, Diff disk↔Editor
- Build-Skript `scripts/build_onedir.ps1`

## 0.3.0

- Syntax-Highlighting für Setup.inf
- Visual-Panels: Übersicht (editierbar), Registry, ShellLinks, Workflow
- Prettifier (Ctrl+Shift+F)
- Simulator Installation/Deinstallation, Test-Runner Dry-Run aus der UI
- Erweiterte Sync-/Simulator-Tests
- Empirum-Versionsmatrix und PyInstaller-Spec

## 0.2.0

- Linter VAL-001…011, Lint-MVP, Completer
- PackageCreator-Wizard, PE/MSI-Inspektoren, Templates
- SyncController, Simulator-Kern, VM-Whitelist-Runner
- 25 Golden-Files

## 0.1.0

- Projektgerüst, Core-Roundtrip, erste Services
