# Empirum PackageStore – Deploy fertiger Setup.inf-Pakete

## Zweck

Fertige Empirum-Pakete (`Install\Setup.inf` + `Files\…`) werden üblicherweise auf

`\\%EmpirumServer%\Configurator$\PackageStore\`

abgelegt und von dort in der **Empirum Management Console** in ein
**Software-Register** importiert.

EMP-PackageX3 unterstützt diesen Schritt als **Kopier-/Deploy-Option**.
Der MMC-Import selbst bleibt manuell (Empirum-Admin).

## Skelett-Reparatur vor dem Deploy

Meldet „Paket prüfen“ VAL-012 (fehlende Standardsektionen – typisch bei
konvertierten Bestandspaketen), erscheint im Deploy-Dialog der Button
**„Fehlende Standardsektionen ergänzen…“**:

- fehlende Sektionen werden als leere Stubs in kanonischer Standard-Reihenfolge angehängt,
- die kanonischen `#`-Aufrufe werden in `[Product]` gesichert
  (`#Reg:Product, DONTDELETE`, `#Reg:OnUninstallProduct, DELETE`,
  `#Ini:Product, DONTDELETE`, `#Security:Product`, `#Set:Product/Deinstallation`
  falls fehlend; `[Shell:Product]` läuft automatisch via `ShellLinks=1`),
- Encoding/BOM/CRLF der bestehenden Datei bleiben erhalten,
- automatisch wird ein WAL-Backup angelegt – **außerhalb** des Pakets unter
  `%LOCALAPPDATA%\HodriusSystems\EMP-PackageX3\backups\<Paketname>\`, damit kein
  `.emp_packagex3_bak` mitdeployt wird und read-only-Shares funktionieren
  (`default_repair_backup_dir`, überschreibbar via `backup_dir=`),
- danach läuft die Paketprüfung erneut.

Neue Sektionen sind verhaltensneutral (leer); nur die drei Fehler-Handler
erhalten den kanonischen Abort-Block (`ErrorLogMsg`/`Abort`, im
Deinstallationspfad negiert), `[RebootRequired]` bleibt bewusst leer - ein
`SetReboot 1` würde den Repair in einen erzwungenen Reboot verwandeln.
Der Deploy-Blocker (Lint-ERROR) ist damit aufgelöst. Derselbe Repair steht im
Editor unter
**Werkzeuge → Fehlende Standardsektionen ergänzen** (auf dem geöffneten Dokument,
mit Undo). Implementierung: `empirum_core.skeleton_repair` +
`repair_missing_standard_sections` in `empirum_services.package_readiness`.

## Zwei Depots – nicht verwechseln

| Depot | Zweck |
|-------|--------|
| `Dokumente\EMP-PackageX3-Depot` | Updates der **App** EMP-PackageX3 (`VERSION.json`) |
| `Configurator$\PackageStore` | Fertige **Empirum-Softwarepakete** für den EMC-Import |

## Einstellungen

| Feld | Bedeutung |
|------|-----------|
| EmpirumServer | Hostname/FQDN; ersetzt `%EmpirumServer%` im Pfad (alternativ Umgebungsvariable `EmpirumServer` / `EMPIRUMSERVER`) |
| PackageStore-Pfad | Standard `\\%EmpirumServer%\Configurator$\PackageStore` |
| Store-Modus | `vendor_product_version` → `Hersteller\Produkt\Version\` oder `flat` → `Produkt_Version\` |

## Bedienung

1. Paket erzeugen (PackageCreator) oder `Setup.inf` öffnen  
2. **Werkzeuge → Nach Empirum PackageStore deployen…**  
   (nach dem Wizard optional direkt angeboten)  
3. Zuerst **Dry-Run**, dann echtes Deploy (ggf. Overwrite)  
4. In der Empirum Management Console: Software-Register → Import aus PackageStore  

## Voraussetzungen

- Netzwerkzugriff / Rechte auf `Configurator$`  
- Paketstruktur mit `Install\Setup.inf`  
- EmpirumServer bekannt (Einstellung oder Env)

## CLI-/Service-API

```python
from empirum_services.package_store import deploy_to_package_store, DeployMode

deploy_to_package_store(
    Path(r"D:\Packages\DemoApp_1.0.0"),
    r"\\%EmpirumServer%\Configurator$\PackageStore",
    manufacturer="Acme",
    empirum_server="emp-srv01",
    mode=DeployMode.VENDOR_PRODUCT_VERSION,
    overwrite=False,
    dry_run=False,
)
```
