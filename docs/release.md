# EMP-PackageX3 Release Notes

**Empirum-Zielversion:** **26.1** (Interpreter Setup.exe/Setup64.exe 26.1.0,
verifiziert – siehe [empirum-version-matrix.md](empirum-version-matrix.md)).

## Release 1.1.0 — erstes Open-Source-Release (MIT)

- Lizenz MIT, Drittanbieter-Hinweise inklusive LGPL-3.0-Pflichten für PySide6/Qt.
- Paket-Standard als neutraler Begriff für das Setup.inf-Skelett (vormals interne
  Konventionsbezeichnung), bereinigte Beispieldaten, keine internen Projektbezüge.
- Qualitätsgates: `ruff`, `mypy --strict`, `pytest`, Coverage- und Release-Gates grün.
- Neue Release-Pipeline: Tag `v1.1.0` → One-Dir-Build, ZIP, SHA256 und GitHub-Release.


## Build (One-Dir)

```powershell
.\scripts\build_onedir.ps1
```

Ausgabe: `dist/EMP-PackageX3/`

## Release-Workflow

`.github/workflows/release.yml` läuft bei einem Tag `v*`:

1. Quality Gates (`ruff`, `mypy`, `pytest`, Coverage, Release-Gates)
2. Prüfung: Tag muss zu `packaging/VERSION.json` passen
3. PyInstaller-One-Dir-Build
4. Lizenztexte (`LICENSE`, `THIRD_PARTY_LICENSES.md`, `LGPL-3.0.txt`, `GPL-3.0.txt`)
   werden ins Paket kopiert
5. ZIP `EMP-PackageX3-<Version>.zip` + `…zip.sha256`
6. GitHub-Release mit beiden Assets

```powershell
# Version in pyproject.toml, src/emp_packagex3/__init__.py und packaging/VERSION.json
# anheben, committen, dann:
git tag v1.1.0
git push origin v1.1.0
```

Der `download_url` in `packaging/VERSION.json` zeigt auf das jeweils letzte Release:
`https://github.com/shod81/EMP-PackageX3/releases/latest/download/EMP-PackageX3-<Version>.zip`.
Danach die neu erzeugte `VERSION.json` ins App-Depot übernehmen.

## Signierung

Siehe [sign-anleitung.md](sign-anleitung.md).

```powershell
.\scripts\sign_exe.ps1 -ExePath .\dist\EMP-PackageX3\EMP-PackageX3.exe
```

## App-Depot (Updates)

```powershell
.\scripts\publish_local_depot.ps1
```

Siehe [local-depot.md](local-depot.md). Später UNC/HTTP-URL in den Einstellungen.

## Empirum PackageStore (Softwarepakete)

Fertige Setup.inf-Pakete → `Configurator$\PackageStore` → EMC-Import.  
Siehe [package-store-deploy.md](package-store-deploy.md).

## Beta

Siehe [beta-checklist.md](beta-checklist.md) und [beta-logging.md](beta-logging.md).

## Release-Checkliste 1.0

| Kriterium | Status |
|-----------|--------|
| Golden-File-Regression (≥25) | Gate-Skript / CI |
| Sync-Szenarien | pytest |
| VAL-001…029 | pytest + standard structure |
| Runner nur mit `.emp_packagex3_vm` | Default + Gate |
| Empirum-Versionsmatrix (26.1 Primärziel, verifiziert) | `docs/empirum-version-matrix.md` |
| Befehlskatalog = Interpreter 26.1.0 | `src/empirum_core/setupinf_contract.py` |
| PackageStore-Deploy | 1.0-rc1 |
| Startzeit &lt; 2 s | manuell auf Referenzhardware |
| EV-Code-Signing | Feld (`sign_exe.ps1`) |
| Beta mit 5 Paketierern | Feld (`beta-checklist.md`) |
| Echte Depot-URL | Feld |

```powershell
uv run python scripts/check_release_gates.py
```

## Verteilung

ZIP der Onedir-Struktur ins App-Depot. MSI-Setup der App selbst ist kein 1.0-Ziel.  
ARM64 → 1.1.
