# Mitmachen

Danke für dein Interesse an EMP-PackageX3.

## Voraussetzungen

- Windows 10/11 (x64), Python 3.12, [uv](https://docs.astral.sh/uv/)
- Matrix42 Empirum ist **nicht** erforderlich, um zu entwickeln oder Tests laufen zu lassen

## Setup

```powershell
uv sync --extra dev
uv run pytest
```

## Vor jedem Pull Request

```powershell
uv run ruff check src tests
uv run mypy
uv run pytest
uv run python scripts/check_release_gates.py
```

CI führt dieselben Schritte aus; ein PR ohne grüne Pipeline wird nicht gemerged.

## Leitlinien

- **Verhalten nicht brechen:** Der Editor garantiert einen byte-identischen Roundtrip.
  Änderungen an Parser, Lexer, Serializer oder Quoting brauchen einen Regressionstest.
- **Golden-Corpus ist Referenz:** `testdata/golden/` bleibt unverändert, außer die Änderung
  ist ausdrücklich Teil des Auftrags. Die Dateien sind CRLF-kodiert (siehe `.gitattributes`).
- **Kanonische Quellen:** Sektionen, Keys, `[Product]`-Reihenfolge und Fehler-Handler stehen
  in `empirum_core/setupinf_contract.py`; Texte im Lerncenter in `learning_content.py`.
  `docs/setupinf-schnellkurs.md` wird daraus generiert (`scripts/generate_schnellkurs.py`) —
  nicht von Hand editieren.
- **Neue Lint-Regeln** brauchen: Implementierung, `ValDoc`-Eintrag in `learning_content.py`,
  Test in `tests/unit/test_linter_val.py` und einen Eintrag in der Regelübersicht.
- **Keine Zugangsdaten, Kunden- oder Firmennamen** in Code, Tests, Fixtures oder Doku.
  Beispieldaten bleiben generisch (`Acme`, `Demo`).
- Sprache: Code und Kommentare englisch, Benutzeroberfläche und Doku deutsch.

## Pull Requests

- Ein Thema pro PR, kurze Beschreibung, Testplan.
- Neue Dateien bitte mit dem MIT-Header-konformen Copyright-Hinweis des Projekts.
- Keine Änderungen an `LICENSE` oder `THIRD_PARTY_LICENSES.md` ohne Rückfrage.
