# Beta-Logging

Für Beta-Tester schreibt EMP-PackageX3 **Rotating File Logs**:

`%LOCALAPPDATA%\HodriusSystems\EMP-PackageX3\logs\emp-packagex3.log`

(plus ältere `emp-packagex3.log.1` …)

## Steuerung

- Einstellung **Debug-Logging** (Standard: an in der Beta)
- CLI: `emp-packagex3 --debug`
- Menü **Datei → Log-Ordner öffnen**

## Was geloggt wird

- Start/Version/Theme
- Öffnen/Speichern von Setup.inf (Pfad, Fehler)
- Update-Check (Quelle)
- Unerwartete Exceptions (Stacktrace bei Fehlern)

Beim Feedback bitte die aktuelle `emp-packagex3.log` (und ggf. Diagnose-Export) mitschicken.
