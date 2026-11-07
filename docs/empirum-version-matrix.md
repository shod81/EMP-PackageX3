# Empirum / Setup.exe version matrix (Release-Kriterium)

**Primärziel EMP-PackageX3 1.0:** Matrix42 Empirum **26.1** (x64) — Interpreter
Setup.exe/Setup64.exe FileVersion 26.1.0, **verifiziert** (Befehls-, Funktions- und Variablentabellen).

| Empirum Agent / Setup | Status | Notes |
|----------------------|--------|-------|
| Empirum **26.1** Setup.exe/Setup64.exe (FileVersion 26.1.0) | **Primärziel** | Beta- und Release-Referenz; Katalog seit rc14 verifiziert abgeglichen |
| Empirum 25.x (andere Builds) | best effort | gleiche Setup.inf-Dialektfamilie (Engine 14.2) |
| Empirum 23.x / 22.x Setup.exe (x64) | best effort | Regression gegen Golden-Korpus |
| ARM64 Setup.exe | 1.1 | siehe Plan-Anpassung #5 |

## Setup.inf-Dialekt

Erzeugte Pakete setzen `[Setup] Version=14.2` (Empirum-INF-Dialekt, nicht die
Empirum-Produktversion). Validierung: VAL-014.

Test-Runner: nur Whitelist + `.emp_packagex3_vm` Marker (kein Produktiv-Host).
