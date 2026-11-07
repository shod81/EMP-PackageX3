# User-Parts: Benutzerkontext in EMP-PackageX3

**Thema:** Pakete mit Befehlen im Benutzerkontext werden so erzeugt und geprüft, dass der
Empirum-Installer eindeutig weiß, welche Teile pro Maschine und welche pro Benutzer
auszuführen sind.

Kontext-Modell je Befehl: `PackageMetadata.user_context_commands`
(`context: user|machine`; Maschinenbefehle bleiben im Normalfluss).

## 1. Referenz-Vertrag der generierten Setup.inf

Paket **mit** User-Part (Wizard-Checkbox + mind. ein Befehl):

```ini
[SetupInfo]
Command line options=/S2 /AW        ; /AW nur bei User-Part/HKCU, sonst nur /S2

[Product]
#Set:Product, DONTDELETE, MACHINE   ; Maschinenteil — genau einmal pro Maschine
#Reg:OnUninstallProduct, DELETE, MACHINE
#Reg:Product, DONTDELETE, MACHINE   ; OHNE MACHINE, wenn [Reg:Product] HKCU enthält
#Ini:Product, DONTDELETE, MACHINE
#Security:Product, MACHINE
#Set:Deinstallation, DELETE, MACHINE
#Set:Client, CLIENT                 ; User-Part — zuletzt, nur im Benutzerdurchlauf

[Set:Client]
CallHidden usersetup.exe            ; alle Benutzerbefehle
If "%ErrorLevel%" == "3010" Then "RebootRequired" EndIf   ; automatisch nach Call*-Zeilen
If "%ErrorLevel%" != "0" Then "Set:InstallationError" EndIf
MD %AppData%\AppConfig
```

Paket **ohne** User-Part bleibt unverändert: `Command line options=/S2`, keine Flags an
den `[Product]`-Einträgen (Golden-kompatibel, byte-identisch).

### Flags an den [Product]-Einträgen

| Eintrag | Flag(s) mit User-Part | Begründung |
|---|---|---|
| `#Set:Product` | `DONTDELETE, MACHINE` | Maschinenteil läuft bei `/AW` nicht im Benutzerdurchlauf |
| `#Reg:OnUninstallProduct` / `#Ini:Product` / `#Security:Product` | bestehende Flags + `MACHINE` | Maschinenteil |
| `#Reg:Product` | `MACHINE` **nur ohne HKCU-Einträge** | mit HKCU: unflagged lassen, damit die Sektion im Benutzerdurchlauf mitläuft (VAL-006/VAL-034) |
| `#Set:Deinstallation` | `DELETE, MACHINE` | Deinstallation läuft im Maschinenkontext |
| `#Set:Client` | `CLIENT` | User-Part — nur im Benutzerkontext |

Regel in einem Satz: Jeder Maschinen-Eintrag bekommt den Zusatz `MACHINE`
(kommagetrennt, ohne Anführungszeichen); der User-Part-Eintrag bekommt `CLIENT`.

### /AW-Aktivierung (VAL-006-Kette)

`/AW` ist gesetzt, wenn **eines** gilt:

1. echter User-Part (`user_context_commands` nicht leer ⇒ `[Set:Client]` + `CLIENT`),
2. Registry-/Befehlskontext enthält HKCU bzw. Benutzerprofil-Variablen
   (`%AppData%`, `%LocalAppData%`, `%Desktop%`, `%Personal%`, `%Sendto%`),
3. manuelle Eigenschaft `needs_aw` bzw. `AskKillProcesses` (bestehendes Verhalten).

Ohne `/AW` läuft Setup.exe nur als SYSTEM — HKCU-Werte und User-Parts würden
stillschweigend ins Systemprofil geschrieben (Anti-Pattern 9).

## 2. Umsetzung in EMP-PackageX3

| Baustein | Umsetzung |
|---|---|
| Kontext-Erkennung | `PackageMetadata.user_context_commands` (`empirum_core.inspect`) |
| Befehls-Sammlung | Wizard sammelt die Benutzerbefehle direkt (Seite 4 · Laufzeit-Optionen) |
| Sektionsbildung | `templates/__init__.py::_user_part_block()` — genau ein Block, nie zwei gleichnamige Sektionen; ErrorLevel-Paar nach `Call*`-Zeilen |
| `[Product]`-Flags | `setupinf_contract.product_refs_for(user_part=…, reg_machine_only=…)` — Single Source of Truth, geteilt mit Templates |
| `/AW`-Header | `_standard_header()` in `templates/__init__.py` (erweitert um `meta.has_user_part`) |

**Design-Entscheidung:** `MACHINE` wird nur gesetzt, wenn das Paket einen *echten*
User-Part hat. Pakete, deren `/AW` allein aus HKCU-/Profilvariablen-Erkennung resultiert
(ohne User-Part), behalten die unflagged Einträge — deren `[Set:Product]`-Inhalt läuft
**gewollt** im Benutzerdurchlauf mit (z. B. `MD %AppData%\…`). `Set:Client` ist bewusst
**nicht** Teil von `STANDARD_SECTIONS` (VAL-012 fordert keinen User-Part).

## 3. Linter-Regeln

| Regel | Schwere | Prüfung |
|---|---|---|
| VAL-006 (Gegenrichtung) | **ERROR** | `CLIENT`-Sektion/-Flag vorhanden, aber `/AW` fehlt ⇒ Benutzerteil läuft nie. QuickFix ergänzt `/AW`. HKCU/VU_/AskKillProcesses ohne `/AW` bleibt WARNING. |
| VAL-032 | ERROR | Benutzerkontext-Befehl (`%AppData%`/`%LocalAppData%`/`%Desktop%`/`%Personal%`/`%Sendto%` oder prozeduraler HKCU-Schreibzugriff) außerhalb der CLIENT-Sektion, obwohl ein User-Part existiert. CLIENT-gescopte Sektionen = `[Set:Client]` + alle per `CLIENT`-Flag aufgerufenen Sektionen. Ausgenommen: Deinstallations-/Reinstall-Pfade (Maschinenkontext). |
| VAL-033 | ERROR | Doppelte `[Set:Client]`-Sektion (Empirum merged gleichnamige Sektionen; Reihenfolge unbestimmt). |
| VAL-034 | WARNING | `MACHINE` auf einem `#Reg:`-Aufruf, dessen Zielsektion HKCU-Einträge enthält (Werte würden im Benutzerdurchlauf übersprungen). QuickFix entfernt das Flag. |

## 4. Abgrenzung / bewusst nicht geändert

* `[Reg:Product]` wird nicht in Maschinen-/Benutzer-Sektionen aufgeteilt; bei gemischten
  HKCU/HKLM-Daten bleibt die Sektion unflagged und läuft in beiden Durchläufen
  (HKLM-Werte sind idempotent).
* Deinstallations-Inhalte behalten ihre Maschinenkontext-Zuordnung.
* Die Golden-Dateien (`testdata/golden/`) sind Maschinenpakete und bleiben byte-identisch;
  das neue Verhalten ist über `tests/unit/test_user_part.py` abgedeckt.
* Skelett-Reparatur (`skeleton_repair.py`): erzeugt **nie** eine `[Set:Client]`-Sektion,
  trägt aber für eine bestehende den fehlenden `#Set:Client, CLIENT`-Aufruf nach
  (idempotent). Bestehende Ref-Zeilen werden nicht umgeschrieben.
