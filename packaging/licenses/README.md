# Drittanbieter-Lizenztexte für Binärpakete

Diese Texte gehören in jedes ausgelieferte Binärpaket (`dist/EMP-PackageX3/`):

| Datei | Komponente | Lizenz |
|---|---|---|
| `LGPL-3.0.txt` | PySide6, shiboken6, Qt | LGPL-3.0 |
| `GPL-3.0.txt` | Bezugstext der LGPL-3.0 | GPL-3.0 |

Quelle: <https://www.gnu.org/licenses/lgpl-3.0.txt> und
<https://www.gnu.org/licenses/gpl-3.0.txt> (unverändert übernommen).

Zusätzlich mitliefern:

- `LICENSE` (MIT, dieses Projekt)
- `THIRD_PARTY_LICENSES.md` (Hinweise und Pflichten)

Der Release-Workflow (`.github/workflows/release.yml`) kopiert diese Dateien
automatisch in das ZIP. Die Qt-DLLs bleiben als separate Dateien im
Installationsverzeichnis (One-Dir-Build) und damit austauschbar — Voraussetzung
für die LGPL-Weitergabe.
