# EMP-PackageX3

Matrix42 Empirum **PackageCreator & PackageEditor** — Setup.inf-Pakete erstellen, prüfen,
reparieren und deployen.

> **Unabhängiges Projekt.** EMP-PackageX3 steht in keiner Verbindung zu Matrix42 und wird
> von Matrix42 weder unterstützt noch gesponsert. „Matrix42" und „Empirum" sind Marken
> ihrer jeweiligen Inhaber; die Nennung dient ausschließlich der Beschreibung der
> Kompatibilität.

## Funktionen

- **Editor** mit Syntaxhervorhebung, Autovervollständigung, Suchen/Ersetzen und
  Roundtrip-Garantie (Lesen → Schreiben bleibt byte-identisch, außer bei bewussten Änderungen).
- **Linter** mit VAL-Regelkatalog: Struktur, `[Product]`-Aufrufe, Registry-Typcodes,
  MSI-Flags, User-Parts, Sicherheits- und Reboot-Prüfungen — inklusive QuickFix.
- **Paket-Standard**: kanonisches Setup.inf-Skelett mit Standardsektionen,
  Fehler-Handlern und `[Product]`-Reihenfolge. Fehlende Sektionen lassen sich per Klick
  ergänzen (idempotent, mit Backup).
- **PackageCreator-Wizard** für MSI, EXE/Unattend, Skripte und Shell-Links, inklusive
  Metadaten-Inspektion (MSI/PE) und User-Part-Erkennung.
- **Simulator** für Install-/Uninstall-Abläufe (Dateien, Registry, Prozesse, Variablen).
- **Setup.inf-Hilfe & Lerncenter**: Befehls-, Prädikaten-, Funktions- und
  Variablenreferenz, Schnellkurs, Sektions- und Flag-Übersicht.
- **PackageStore-Deploy** mit Vorabprüfung und Reparaturblockern.
- **Encoding-Handling**: Windows-1252/UTF-8 inklusive BOM-Erkennung und -Heilung.

## Installation

Voraussetzungen: Windows, Python 3.12, [uv](https://docs.astral.sh/uv/).

```powershell
uv sync --extra dev
uv run emp-packagex3
uv run emp-packagex3 C:\Paket\Install\Setup.inf   # Datei direkt öffnen
```

Tests und Qualitätsgates:

```powershell
uv run pytest
uv run ruff check src tests
uv run mypy
uv run python scripts/check_release_gates.py
```

Build (One-Dir-Bundle):

```powershell
.\scripts\build_onedir.ps1
```

Zielplattform und Versionsmatrix: [docs/empirum-version-matrix.md](docs/empirum-version-matrix.md).

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [docs/setupinf-standard-alignment.md](docs/setupinf-standard-alignment.md) | Paket-Standard: Sektionen, Keys, `[Product]`-Reihenfolge, VAL-Regeln |
| [docs/user-parts.md](docs/user-parts.md) | Benutzerkontext: `[Set:Client]`, `CLIENT`/`MACHINE`, `/AW` |
| [docs/setupinf-schnellkurs.md](docs/setupinf-schnellkurs.md) | Setup.inf-Schnellkurs (generiert aus `learning_content.py`) |
| [docs/package-store-deploy.md](docs/package-store-deploy.md) | PackageStore-Deploy und Reparatur |
| [docs/local-depot.md](docs/local-depot.md) | Lokales Depot und Update-Kanal |
| [docs/beta-logging.md](docs/beta-logging.md) | Logpfade und Diagnose |
| [docs/reference/](docs/reference/) | Setup.inf-Referenz und Quick Reference (PDF) |

## Datenschutz

Die Anwendung arbeitet offline. Sie schreibt Einstellungen, Logs und Backups unter
`%LOCALAPPDATA%\HodriusSystems\EMP-PackageX3`. Das Feedback-ZIP enthält Logs und
Systeminformationen und kann lokale Pfade, Rechner- und Servernamen enthalten — bitte vor
dem Teilen prüfen.

## Lizenz

[MIT](LICENSE). Die mitgelieferten Drittanbieter-Komponenten stehen unter eigenen Lizenzen,
siehe [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Mitmachen

Beiträge sind willkommen — siehe [CONTRIBUTING.md](CONTRIBUTING.md) und
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Sicherheitslücken bitte über
[SECURITY.md](SECURITY.md) melden, nicht als öffentliches Issue.
