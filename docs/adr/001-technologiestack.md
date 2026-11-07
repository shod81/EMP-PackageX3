# ADR-001: Technologiestack für EMP-PackageX3

- **Status:** Akzeptiert
- **Produkt:** EMP-PackageX3
- **Copyright:** Stefan Hodrius (MIT)

## Kontext

Windows-10/11-Desktopanwendung (x64 primär; ARM64 ab 1.1) für Erstellung, Validierung und Pflege von Matrix42-Empirum-Setup.inf-Paketen.

## Entscheidung

Python 3.12 + PySide6 6.7+ (LGPL) + QPlainTextEdit/QSyntaxHighlighter; comtypes/pywin32 für Windows-Installer-COM; pefile für PE; PyInstaller Onedir + Code-Signing.

## Begründung

1. Dokumentierte NFR-/Team-Präferenz für Python/PySide6 (primär)
2. Höchste Iterationsgeschwindigkeit und Parser-Eignung
3. Qt-C++-Rendering erfüllt Reaktivität bei großen Dateien
4. Gewichtete Matrix nur unterstützend (4,40 vs. 4,35) – keine alleinige Entscheidungsgrundlage

## Konsequenzen

- Positiv: pytest/hypothesis, LGPL ohne Copyleft für die App, schnelle Domäneniteration
- Negativ: AV-Falschalarme (PyInstaller), GIL-Planung, IntelliSense Eigenbau (Scope 1.0 begrenzt)

## Alternativen

.NET 8 + WPF + AvalonEdit – verworfen. Domäne bleibt Qt-frei, falls später portiert wird (ohne parallele C#-Skizze in P0).
