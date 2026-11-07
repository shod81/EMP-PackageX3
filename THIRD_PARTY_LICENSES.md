# Drittanbieter-Komponenten

EMP-PackageX3 wird unter der MIT-Lizenz (siehe [LICENSE](LICENSE)) verbreitet und nutzt
folgende Fremdkomponenten. Für Binärverteilungen (One-Dir-Build) sind die Lizenztexte
mitzuliefern.

## Laufzeit-Abhängigkeiten

| Komponente | Version | Lizenz | Verwendung |
|---|---|---|---|
| [PySide6](https://pypi.org/project/PySide6/) | ≥ 6.7 | LGPL-3.0 (alternativ GPL-3.0 oder kommerziell) | GUI (Qt for Python) |
| [shiboken6](https://pypi.org/project/shiboken6/) | ≥ 6.7 | LGPL-3.0 | Binding-Laufzeit von PySide6 |
| [Qt](https://www.qt.io/licensing) | 6.x | LGPL-3.0 | Von PySide6 mitgelieferte Bibliotheken |
| [pefile](https://pypi.org/project/pefile/) | ≥ 2024.8.26 | MIT | PE-Inspektion (EXE-Metadaten) |
| [comtypes](https://pypi.org/project/comtypes/) | ≥ 1.4.17 | MIT | COM-Zugriff (Windows-Shell) |

## Entwicklungs-Abhängigkeiten

pytest, pytest-cov, hypothesis, ruff, mypy, pyinstaller — eigene Lizenzen (MIT/BSD/Apache/
GPL mit Ausnahme), nicht Teil der Laufzeitauslieferung.

## Pflichten bei der Weitergabe von Binärpaketen (LGPL-3.0)

PySide6, shiboken6 und Qt stehen unter LGPL-3.0. Wer ein gebautes Paket weitergibt, muss:

1. **Lizenztexte mitliefern** — `LGPL-3.0.txt` und `GPL-3.0.txt` (die LGPL-3.0 verweist
   ergänzend auf die GPL-3.0) sowie diesen Hinweis. Die Texte liegen den PySide6-Wheels
   unter `*.dist-info/licenses/` bei und sind unter
   <https://www.gnu.org/licenses/lgpl-3.0.txt> bzw. <https://www.gnu.org/licenses/gpl-3.0.txt>
   abrufbar.
2. **Quellenhinweis** — wo die unveränderten Qt-/PySide6-Bibliotheken bezogen werden können
   (PyPI-Wheels der eingesetzten Version).
3. **Austauschbarkeit erhalten** — die Qt-DLLs müssen als separate Dateien im
   Installationsverzeichnis liegen (One-Dir-Build erfüllt das; kein Einbetten in eine
   einzelne EXE, keine Verschlüsselung des Verzeichnisses).
4. **Keine zusätzlichen Einschränkungen** — die MIT-Lizenz dieses Projekts darf das
   Debuggen und Ersetzen der LGPL-Komponenten nicht untersagen.

Der Build legt die Lizenztexte nicht automatisch bei. Vor einer Veröffentlichung eines
Binärpakets die Dateien in `packaging/licenses/` ablegen und mit ausliefern.

## Marken

„Matrix42" und „Empirum" sind Marken der Matrix42 AG bzw. ihrer Inhaber. Die Nennung in
diesem Projekt beschreibt ausschließlich die Kompatibilität mit dem Setup.inf-Format.
Es besteht keine Verbindung zu Matrix42; das Projekt wird von Matrix42 weder unterstützt
noch gesponsert.
