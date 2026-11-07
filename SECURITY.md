# Sicherheit

## Schwachstellen melden

Bitte **kein** öffentliches Issue für Sicherheitslücken. Nutze stattdessen
GitHub → *Security* → *Report a vulnerability* (privates Advisory) im Repository.

Hilfreich sind:

- betroffene Version (`Hilfe → Info` oder Dateiname des Builds),
- Betriebssystem und Empirum-Version,
- Schritte zur Reproduktion, idealerweise mit einer minimalen `Setup.inf`,
- Auswirkung (z. B. Schreiben außerhalb des Paketverzeichnisses, Ausführen von Code).

## Ablauf

- Eingang wird innerhalb von 7 Tagen bestätigt.
- Wir prüfen den Befund, entwickeln einen Fix und stimmen den
  Veröffentlichungszeitpunkt ab.
- Auf Wunsch wird der Melder im Advisory genannt.

## Umfang

Im Fokus stehen:

- Pfadverarbeitung beim Öffnen, Speichern und Reparieren von Paketen
  (Pfad-Traversal, Symlinks, Schreiben außerhalb des Zielverzeichnisses),
- Verarbeitung nicht vertrauenswürdiger `Setup.inf`, `.reg`- und MSI/PE-Dateien
  (Parser-Abstürze, Ressourcenverbrauch),
- Rechteausweitung durch den Runner/Simulator,
- Update-Mechanismus (Manifest, Downloads).

Nicht im Umfang: Fehlverhalten der Empirum- oder Windows-Infrastruktur selbst,
Angriffe, die bereits lokale Administratorrechte voraussetzen.

## Sichere Nutzung

- Pakete nur aus vertrauenswürdigen Quellen öffnen.
- Den Runner nur in einer VM oder auf einem Testsystem einsetzen (`require_vm_marker`).
- Feedback-ZIPs vor dem Teilen prüfen: Logs enthalten Pfade, Rechner- und Servernamen.
- Builds ohne Signatur lösen SmartScreen-Warnungen aus; vergleiche die veröffentlichte
  SHA256-Summe.
