# EMP-PackageX3 – Signaturanleitung (Authenticode)

**Produkt:** EMP-PackageX3  
**Copyright:** © 2026 Stefan Hodrius · MIT-Lizenz  
**Ziel:** Signierte Windows-EXE ohne SmartScreen-/AV-Falschalarme (Plan-Risiko R-03)

## 1. Voraussetzungen

1. **Code-Signing-Zertifikat** (empfohlen: **EV Code Signing**)
   - Kauf bei einem anerkannten CA (z. B. DigiCert, Sectigo, GlobalSign)
   - EV liegt oft auf USB-Token/HSM – Token beim Signieren einstecken, PIN bereithalten
2. **Windows SDK / Signing Tools** mit `signtool.exe` im PATH  
   Typischer Pfad:
   `C:\Program Files (x86)\Windows Kits\10\bin\<Version>\x64\signtool.exe`
3. Gebaute App (Onedir):
   ```powershell
   .\scripts\build_onedir.ps1
   ```
   Ergebnis: `dist\EMP-PackageX3\EMP-PackageX3.exe`

Prüfen, ob SignTool gefunden wird:

```powershell
Get-Command signtool
signtool /?
```

## 2. Signieren (Standardweg)

Im Repo-Root:

```powershell
.\scripts\sign_exe.ps1 -ExePath .\dist\EMP-PackageX3\EMP-PackageX3.exe
```

Das Skript:

- signiert mit SHA-256 (`/fd SHA256`)
- setzt einen Timestamp (`/tr`, Standard DigiCert)
- wählt automatisch ein geeignetes Zertifikat aus dem Store (`/a`)
- verifiziert anschließend (`signtool verify /pa`)

Anderer Timestamp-Server:

```powershell
.\scripts\sign_exe.ps1 `
  -ExePath .\dist\EMP-PackageX3\EMP-PackageX3.exe `
  -TimestampUrl "http://timestamp.sectigo.com"
```

## 3. Manuell mit signtool

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a `
  .\dist\EMP-PackageX3\EMP-PackageX3.exe

signtool verify /pa /v .\dist\EMP-PackageX3\EMP-PackageX3.exe
```

Zertifikat gezielt wählen (Thumbprint aus `certmgr.msc`):

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
  /sha1 <THUMBPRINT_OHNE_LEERZEICHEN> `
  .\dist\EMP-PackageX3\EMP-PackageX3.exe
```

## 4. Was signieren?

| Artefakt | Empfehlung |
|----------|------------|
| `EMP-PackageX3.exe` | **Pflicht** |
| Weitere `.dll` / `.pyd` im Onedir-Ordner | Optional, erhöht Reputation weiter |
| ZIP der ganzen Onedir-Struktur | ZIP selbst wird nicht „EXE-signiert“ – Signatur steckt in der EXE |

Onedir als ZIP fürs Depot packen **nach** dem Signieren der EXE.

## 5. Verifizieren / Troubleshooting

Eigenschaften der EXE → Digital Signatures → Signatur sichtbar und gültig.

Häufige Fehler:

| Symptom | Ursache / Maßnahme |
|---------|-------------------|
| `signtool` nicht gefunden | Windows SDK installieren, PATH setzen |
| Kein Zertifikat | Token einstecken, Zertifikat im Benutzer-/Maschinenstore prüfen |
| Timestamp fehlgeschlagen | Anderen `/tr`-Server versuchen, Firewall prüfen |
| SmartScreen warnt trotzdem | Bei neuem EV-Zertifikat Reputation aufbauen; interne Whitelist (Defender/Sophos) pflegen |

## 6. Ablauf für ein Release

1. `uv run pytest` grün  
2. `.\scripts\build_onedir.ps1`  
3. `.\scripts\sign_exe.ps1 -ExePath .\dist\EMP-PackageX3\EMP-PackageX3.exe`  
4. Ordner `dist\EMP-PackageX3` als ZIP ins **lokale oder Netzwerk-Depot** legen  
5. `VERSION.json` im Depot aktualisieren (Version, notes, download_url/Pfad)  
6. Beta-Tester informieren  

## 7. Ohne Zertifikat (nur intern)

Die App läuft unsigniert. Für interne Tests akzeptabel; für breiten Admin-Rollout **nicht** empfohlen. Antivirus-Ausnahmen ggf. manuell setzen.
