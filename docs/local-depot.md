# Lokales Software-Depot (jetzt) und HTTP später

> **Hinweis:** Dieses Depot dient **App-Updates** von EMP-PackageX3.
> Fertige Empirum-Pakete gehören nach `Configurator$\PackageStore`
> (siehe [package-store-deploy.md](package-store-deploy.md)).

## Standard

Beim ersten Start legt EMP-PackageX3 an:

`%USERPROFILE%\Documents\EMP-PackageX3-Depot\`

mit:

- `VERSION.json` – Versionsmanifest
- `README.txt` – Kurzhinweise

In den **Einstellungen**:

| Feld | Bedeutung |
|------|-----------|
| Depot-Pfad / -URL | Lokaler Ordner **oder** später `https://…/emp-packagex3/` |
| Manifest-Override | Optionaler direkter Pfad/URL zur `VERSION.json`; leer = `<Depot>/VERSION.json` |

Der Ordner wird **nach** dem ersten Anzeigen des Fensters angelegt (nicht mehr
während des Starts), damit ein langsames oder nicht erreichbares Laufwerk den
Programmstart nicht blockiert. UNC-Pfade (`\\Server\Share\…`) werden dabei
übersprungen – ein `mkdir`/Manifest-Refresh auf einer toten Freigabe würde sonst
im SMB-Timeout hängen. Für Netz-Depots pflegt der Admin die `VERSION.json`
direkt; der Update-Check liest sie unverändert.

## Update-Check

Menü **Datei → Auf Update prüfen…** liest das Manifest (Datei oder HTTP) und vergleicht mit der App-Version.

## Später auf Netzwerk/HTTP umstellen

1. Inhalt des lokalen Depots auf Share/Webserver kopieren  
2. In den Einstellungen Depot-Pfad auf UNC oder `https://…` ändern  
3. Kein Code-Wechsel nötig – gleiche Logik
