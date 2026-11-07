# Beta-Checkliste EMP-PackageX3 (Feldarbeit)

**Ziel:** ~5 Paketierer ohne kritische Eskalation (Release-Kriterium 1.0).  
**App-Version:** ab `1.0.0-rc13` · **Empirum-Ziel:** **25.4** · Logs: [beta-logging.md](beta-logging.md).

## Bekannt aus Review rc3

- Dark-Theme: Einstellungs-/Wizard-Dialoge, Diagnose-Farben und Header folgen jetzt dem Theme; PackageStore-Dialog erbt den App-Stil.

## Meldungs-Vorlage (Copy & Paste)

```
Betreff: [PBX3-BETA][Szenario-Nr][P0-P3] Kurzbeschreibung
Version: (Fenstertitel, z. B. 1.0.0-rc6) | Windows-Version
Szenario: Nr. X aus dieser Checkliste
Schritte: 1. ... 2. ... 3. ...
Erwartet: ...
Passiert: ...
Anlage: Feedback-ZIP (Hilfe -> Feedback-Paket), ggf. Setup.inf/Diagnose-/Simulator-Export
```

Schweregrade: **P0** Absturz/Datenverlust (sofort) - **P1** Funktion falsch
- **P2** Bedienung unklar - **P3** Verbesserungswunsch.
Keine Payload/Kundendaten mitschicken; Setup.inf vor Anhang ggf. anonymisieren.
Bei einem Absturz fragt die App selbst nach dem Feedback-Paket (Fehler landen
immer im Log).

## Vor dem Start

- [ ] Onedir gebaut (`.\scripts\build_onedir.ps1`)
- [ ] Optional signiert (`.\scripts\sign_exe.ps1` + [sign-anleitung.md](sign-anleitung.md))
- [ ] Ins App-Depot gelegt (`.\scripts\publish_local_depot.ps1`) oder ZIP verteilt
- [ ] EmpirumServer / PackageStore-Pfad in Einstellungen bekannt
- [ ] Test gegen Empirum **25.4** (Management Console / Client) geplant

## Szenarien pro Tester

1. **Editor:** bestehende `Setup.inf` öffnen, Lint (F7), QuickFix, speichern (WAL/Backup)
2. **PackageCreator:** MSI oder EXE → Paket erzeugen → optional PackageStore-Deploy (Dry-Run)
3. **Simulator:** Install/Uninstall im Werkzeugfenster (Baum + Lücken),
   Doppelklick springt zur Zeile, Report als Text exportierbar
4. **Test-Runner:** nur auf VM mit `.emp_packagex3_vm` + Whitelist (Dry-Run prüfen)
5. **Update-Check:** Datei → Auf Update prüfen (lokales Depot)
6. **Schnellkurs:** Hilfe → Setup.inf-Schnellkurs… (Kapitel, Sektionen, Befehle, VAL-Erklärungen; Workflow-Tab auf Ausführung Install/Uninstall stellen)
7. **Tooltip-Modus:** Hilfe → Tooltip-Modus (oder F1) – über Menüs/Felder fahren
7. **Paket prüfen:** PackageStore-Dialog → „Paket prüfen“ vor Dry-Run/Deploy
8. **Feedback:** Hilfe → Feedback-Paket (Logs) – ZIP an Support senden
9. **Empirum 25.4:** Probeimport PackageStore → Software-Register → optional Client-Lauf
11. **Logs:** bei Problemen Log-Ordner öffnen und/oder Feedback-ZIP mitschicken

## Abnahmekriterien

- Kein Datenverlust an `Setup.inf`
- Kein Runner-Start auf Produktiv-Host ohne Marker
- PackageStore-Kopien landen unter erwartetem UNC/Pfad
- Import/Lauf unter Empirum **25.4** ohne kritischen Blocker
- Kritische Bugs: Blocker für 1.0; Rest → Backlog 1.0.x / 1.1

## Feedback-Kanal

Issue im Repo – bitte App-Version, **Empirum 25.4** (Build), Log-Auszug.
