"""Learning / Admin tooltip mode for EMP-PackageX3.

When enabled, bound widgets and actions show explanatory tooltips on hover
so IT admins can discover menu entries and fields quickly.
"""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QMenuBar,
    QProxyStyle,
    QStyle,
    QStyleHintReturn,
    QStyleOption,
    QWidget,
)

TIP_PROP = "empTip"
TIP_DURATION_MS = 20_000
# Hover delay before a tip appears (Qt default is often ~700 ms)
TIP_WAKE_MS = 120
TIP_FALL_ASLEEP_MS = 150


class _FastToolTipStyle(QProxyStyle):
    """Shorten tooltip wake delay while learning mode is active."""

    fast: bool = False

    def styleHint(
        self,
        hint: QStyle.StyleHint,
        option: QStyleOption | None = None,
        widget: QWidget | None = None,
        returnData: QStyleHintReturn | None = None,
    ) -> int:
        if self.fast:
            if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay:
                return TIP_WAKE_MS
            if hint == QStyle.StyleHint.SH_ToolTip_FallAsleepDelay:
                return TIP_FALL_ASLEEP_MS
        return int(super().styleHint(hint, option, widget, returnData))


_fast_style: _FastToolTipStyle | None = None


def set_tooltip_mode_delay(enabled: bool) -> None:
    """Apply fast tooltip wake delay app-wide when learning mode is on."""
    global _fast_style
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return
    if _fast_style is None:
        # Base on current platform style; keep one proxy for the app lifetime
        _fast_style = _FastToolTipStyle()
        app.setStyle(_fast_style)
    _fast_style.fast = enabled


def bind_tip(target: QWidget | QAction, text: str) -> None:
    """Attach a learning tip (always stored; shown only in tooltip mode)."""
    target.setProperty(TIP_PROP, text)


def tip_text(target: QWidget | QAction) -> str:
    raw = target.property(TIP_PROP)
    return str(raw) if raw else ""


def apply_tooltip_mode(root: QWidget, enabled: bool) -> None:
    """Show or hide learning tips on root and all children (widgets + actions)."""
    set_tooltip_mode_delay(enabled)
    duration = TIP_DURATION_MS if enabled else -1

    for widget in [root, *root.findChildren(QWidget)]:
        text = tip_text(widget)
        if text:
            widget.setToolTip(text if enabled else "")
            widget.setToolTipDuration(duration if enabled else -1)
        if isinstance(widget, QMenu):
            widget.setToolTipsVisible(enabled)

    for action in [a for a in root.findChildren(QAction) if isinstance(a, QAction)]:
        text = tip_text(action)
        if not text:
            continue
        action.setToolTip(text if enabled else "")
        action.setStatusTip(text if enabled else "")

    # Menubar actions are often parented to the window, not found via QMenu alone
    menubar = root.findChild(QMenuBar)
    if menubar is not None:
        for action in menubar.actions():
            _apply_action_tree(action, enabled)


def _apply_action_tree(action: QAction, enabled: bool) -> None:
    text = tip_text(action)
    if text:
        action.setToolTip(text if enabled else "")
        action.setStatusTip(text if enabled else "")
    menu = action.menu()
    if not isinstance(menu, QMenu):
        return
    menu.setToolTipsVisible(enabled)
    for child in menu.actions():
        if child.isSeparator():
            continue
        _apply_action_tree(child, enabled)


def bind_main_window_tips(
    *,
    brand: QWidget,
    subtitle: QWidget,
    editor: QWidget,
    panels: QWidget,
    diag_list: QWidget,
    status: QWidget,
) -> None:
    bind_tip(
        brand,
        "EMP-PackageX3 – PackageCreator & PackageEditor für Empirum Setup.inf "
        "(Zielplattform Empirum, siehe Hilfe → Über).",
    )
    bind_tip(
        subtitle,
        "Kernfunktionen: Pakete erzeugen, Setup.inf bearbeiten, Lint-Regeln prüfen, "
        "Installation simulieren.",
    )
    bind_tip(
        editor,
        "Setup.inf-Editor (Text). Änderungen werden mit der Visual-Ansicht "
        "synchronisiert. Speichern legt WAL-Backup an. IntelliSense mit Tab/Enter.",
    )
    bind_tip(
        panels,
        "Visuelle Ansicht der Setup.inf: Übersicht (editierbar), Registry, "
        "ShellLinks und Workflow-Sektionen – parallel zum Texteditor.",
    )
    bind_tip(
        diag_list,
        "Lint-Diagnosen (VAL-001…021). Doppelklick/Enter springt zur Zeile. "
        "F7 aktualisiert die Liste. QuickFix: Strg+.",
    )
    bind_tip(
        status,
        "Statuszeile: Kurzmeldungen und bei aktivem Tooltip-Modus die "
        "StatusTip-Texte der Menüeinträge.",
    )


# Menu tip catalog (German, admin-oriented)
MENU_TIPS: dict[str, str] = {
    "file.new": "Leert den Editor (ungespeicherte Änderungen werden nachgefragt).",
    "file.open": "Öffnet eine vorhandene Setup.inf im Editor (Encoding-Dialog bei Mehrdeutigkeit).",
    "file.save": "Speichert die aktuelle Setup.inf inkl. WAL-Backup vor dem Schreiben.",
    "file.save_as": "Speichert unter neuem Pfad – typisch Install\\Setup.inf im Paketordner.",
    "file.settings": "Theme, Runner-Whitelist, App-Depot, PackageStore, Logging und Tooltip-Modus.",
    "file.update": "Vergleicht die App-Version mit VERSION.json im konfigurierten Depot.",
    "file.logs": "Öffnet den Ordner mit Beta-Rotationslogs (Fehleranalyse).",
    "file.roundtrip": "Prüft, ob Parser→Serializer die Datei ohne semantischen Verlust rundtrippt.",
    "edit.undo": "Macht die letzte Textänderung im Editor rückgängig.",
    "edit.redo": "Stellt eine rückgängig gemachte Editor-Änderung wieder her.",
    "edit.cut": "Schneidet die Auswahl aus und legt sie in die Zwischenablage.",
    "edit.copy": "Kopiert die Auswahl in die Zwischenablage.",
    "edit.paste": "Fügt den Zwischenablage-Inhalt an der Cursorposition ein.",
    "edit.select_all": "Markiert den gesamten Editorinhalt.",
    "edit.prettify": "Normalisiert Abschnitte/Einrückung der Setup.inf (Prettifier).",
    "edit.find": "Öffnet die Suchleiste unter dem Editor (Strg+F); F3 weitersuchen.",
    "edit.find_next": "Springt zum nächsten Treffer (F3).",
    "edit.find_prev": "Springt zum vorherigen Treffer (Umschalt+F3).",
    "tools.lint": "Führt VAL-001…021 aus (Referenzen, Struktur, Empirum-Fallstricke).",
    "tools.skeleton_repair": (
        "Ergaenzt fehlende Standardsektionen und sichert die kanonischen "
        "#Aufrufe in [Product] (VAL-012) - Fehler-Handler mit kanonischem "
        "Abort-Block, uebrige Stubs leer; typisch bei konvertierten "
        "Paketen."
    ),
    "tools.quickfix": "Wendet den ersten verfügbaren QuickFix der aktuellen Diagnosen an.",
    "tools.wizard": "PackageCreator: MSI/EXE/Script/Links → standardkonformes Empirum-Paket.",
    "tools.sim_install": (
        "Oeffnet das Simulator-Werkzeugfenster (Installation): alle Aktionen in "
        "Abarbeitungsreihenfolge, Luecken, Endzustand, Sprung zur Zeile, Export."
    ),
    "tools.sim_uninstall": (
        "Simulator-Werkzeugfenster im Deinstallationsmodus (bottom-up, nur "
        "'-'-Zeilen) - gleiche Ansicht wie Installation."
    ),
    "tools.runner": "Dry-Run des echten Setup.exe-Aufrufs – nur Whitelist + VM-Marker.",
    "tools.packagestore": (
        "Kopiert das fertige Paket nach Configurator$\\PackageStore (MMC-Import danach)."
    ),
    "tools.error_reboot": "Setzt Reboot=0 und Fehlertexte für Install-/Uninstall-Error-Sektionen.",
    "tools.snippet": "Fügt den ErrorLevel-Block (0 / 3010) an der Cursorposition ein.",
    "tools.snippet_reg": (
        "CallHidden reg.exe delete … – Registry während der Installation löschen "
        "(nicht -HKLM in [Reg:Product]; '-' dort erst bei Deinstallation)."
    ),
    "tools.snippet_msi_reinstall": (
        "Fügt dynamische MSI-GUID-Ermittlung (GetUninstallKeyName / DoesRegKeyExist) "
        "für sauberen Reinstall und Vorversionen-Deinstallation ein."
    ),
    "tools.theme": "Wechselt zwischen Light- und Dark-Theme.",
    "tools.export_diag": "Exportiert aktuelle Lint-Diagnosen als Textdatei.",
    "tools.diff": "Vergleicht Editor-Inhalt mit der zuletzt gespeicherten Datei auf Disk.",
    "help.learning": (
        "Setup.inf-Schnellkurs: 8 Kapitel, Sektions-/Befehls-Referenz und "
        "Lint-Erklärungen – der Grundkurs für Paketierer."
    ),
    "help.command_reference": (
        "Strukturierte Empirum-Befehlsreferenz: Befehle, Prädikate, Funktionen, "
        "Variablen, Sektionen, Flags und Lint – durchsuchbar."
    ),
    "help.tooltip_mode": "Schaltet Lern-Tooltips für Menüs und UI-Elemente ein oder aus.",
    "help.feedback": "Packt Logs + Versionsinfo als ZIP für einen Fehlerbericht (GitHub-Issue).",
    "help.about": "Version, Copyright und Empirum-Zielplattform.",
}


def bind_action(action: QAction, tip_key: str) -> QAction:
    bind_tip(action, MENU_TIPS[tip_key])
    action.setProperty("empTipKey", tip_key)
    return action


# Dialog / panel field tips
FIELD_TIPS: dict[str, str] = {
    "settings.theme": "Oberflächendesign der App: light oder dark (wird nach OK übernommen).",
    "settings.runner_roots": (
        "Erlaubte Wurzelpfade für den Test-Runner (eine Zeile = ein Root). "
        "Setup.exe-Aufrufe außerhalb dieser Pfade werden blockiert."
    ),
    "settings.runner_roots_label": (
        "Whitelist für den Dry-Run-Runner: nur Pakete unter diesen Roots dürfen "
        "mit Setup.exe getestet werden."
    ),
    "settings.vm_marker": (
        "Wenn aktiv: Runner nur, wenn die Datei .emp_packagex3_vm im Whitelist-Root "
        "liegt (Schutz vor versehentlichem Live-Lauf)."
    ),
    "settings.depot_intro": (
        "App-Update-Depot für EMP-PackageX3 selbst (Onedir/VERSION.json) – "
        "nicht der Empirum PackageStore für Softwarepakete."
    ),
    "settings.depot": (
        "Pfad oder URL zum App-Depot (Standard: Dokumente\\EMP-PackageX3-Depot). "
        "Datei → Nach Updates suchen liest VERSION.json von hier."
    ),
    "settings.manifest": (
        "Optionaler direkter Pfad/URL zur VERSION.json. Leer = <Depot>/VERSION.json "
        "bzw. <URL>/VERSION.json."
    ),
    "settings.manifest_hint": (
        "Ohne Override sucht die App VERSION.json direkt im Depot-Ordner bzw. unter der Depot-URL."
    ),
    "settings.debug": (
        "Schreibt ausführliche Rotationslogs nach AppData (oder Log-Ordner) – für Beta empfohlen."
    ),
    "settings.log_dir": (
        "Abweichender Ordner für Logdateien. Leer = "
        "AppData\\…\\HodriusSystems\\EMP-PackageX3\\logs. "
        "Über Hilfe/Datei → Logs öffnen erreichbar."
    ),
    "settings.store_intro": (
        "Ziel für fertige Empirum-Pakete (MMC-Import). Typisch "
        "\\\\Server\\Configurator$\\PackageStore – getrennt vom App-Depot oben."
    ),
    "settings.empirum_server": (
        "Hostname des Empirum-Servers. Ersetzt %EmpirumServer% im PackageStore-Pfad "
        "beim Deploy (Werkzeuge → PackageStore)."
    ),
    "settings.package_store": (
        "UNC- oder lokaler Root des PackageStores, z. B. "
        "\\\\%EmpirumServer%\\Configurator$\\PackageStore."
    ),
    "settings.store_mode": (
        "Ordnerstruktur unter dem Store: vendor_product_version = "
        "Hersteller\\Produkt\\Version; flat = Produkt_Version."
    ),
    "settings.tooltip_mode": (
        "Lernmodus: Erklär-Tooltips an Menüs und Einstellungsfeldern beim Überfahren "
        "mit der Maus (auch über F1 / Hilfe umschaltbar)."
    ),
    "settings.undocumented_commands": (
        "Experimentell: schaltet die verifizierten, aber undokumentierten "
        "Klasse-1-Befehle frei (Completer, Linter-Freigabe, Hilfe-Bereich). "
        "Ohne offizielle Matrix42-Dokumentation – Einsatz auf eigenes Risiko."
    ),
    "settings.ok": "Übernimmt die Einstellungen und schließt den Dialog.",
    "settings.cancel": "Verwirft Änderungen und schließt den Dialog.",
    "panels.exec_mode": (
        "Workflow-Ansicht: Struktur oder nummerierte Ausführungsreihenfolge "
        "für Installation (top-down) bzw. Deinstallation (bottom-up, nur '-'-Zeilen)."
    ),
    "learn.search": "Filtert Kapitel, Sektionen und Befehle im Lerncenter.",
    "learn.export": "Exportiert den kompletten Schnellkurs als HTML-Datei.",
    "learn.close": "Schließt das Lerncenter.",
    "cmdref.search": "Filtert die Befehlsliste nach Name, Syntax, Beschreibung oder Beispiel.",
    "cmdref.list": "Alle Empirum-Setup.inf-Befehle – Auswahl zeigt Details rechts.",
    "cmdref.detail": "Syntax, Kurzbeschreibung, Uninstall-Hinweis, Beispiel und Fallstricke.",
    "cmdref.close": "Schließt die Befehlsreferenz.",
    "emphelp.search": "Filtert Befehle, Prädikate, Funktionen, Variablen, Sektionen und Flags.",
    "emphelp.tree": "Themenbaum der Empirum-Setup.inf-Hilfe.",
    "emphelp.detail": "Detailansicht zum gewählten Hilfethema.",
    "emphelp.close": "Schließt die Empirum-Hilfe.",
    "sim.mode": (
        "Wechselt zwischen Installations- und Deinstallationssimulation - "
        "Ergebnis wird sofort neu berechnet."
    ),
    "sim.filter": "Filtert Aktionen nach Sektion, Befehl oder Detail (Live).",
    "sim.tree": (
        "Aktionen gruppiert nach Sektion in Abarbeitungsreihenfolge; "
        "Doppelklick auf eine Zeilennummer springt in den Editor."
    ),
    "sim.export": "Schreibt den kompletten Simulator-Report als Textdatei.",
    "sim.refresh": "Simuliert erneut mit dem aktuellen Editorstand.",
    "edit.find_term": "Suchbegriff; Eingabe sucht live, Eingabetaste weitersuchen.",
    "edit.find_case": "Nur bei übereinstimmender Groß-/Kleinschreibung suchen.",
    "edit.find_close": "Schließt die Suchleiste (Esc).",
    "panels.overview": "Baum aller Sektionen/Keys – Werte in Spalte 2 editierbar (Sync → Text).",
    "panels.registry": "Gefundene Registry-relevante Zeilen (HKLM/HKCU o. ä.) zur Übersicht.",
    "panels.shell": "Verknüpfungen aus [Shell:…]-Sektionen und #Shell-Referenzen.",
    "panels.shell_dest": (
        "Ablageort der Verknüpfung: CommonDesktop (%CommonDesktop%, All Users Desktop) "
        "oder Common Programs (%CommonPrograms%, All Users Startmenü\\Programme)."
    ),
    "panels.shell_name": (
        "Anzeigename der Verknüpfung; bei Common Programs ggf. mit Unterordner "
        "(z. B. Vendor\\App) unter %CommonPrograms%."
    ),
    "panels.shell_path": "Ziel der Verknüpfung, z. B. %ProgramFiles%\\App\\app.exe.",
    "panels.shell_add": (
        "Fügt eine standardkonforme Link-Zeile an [Shell:Product] an "
        "(ShellLinks/CommonShellLinks werden gesetzt)."
    ),
    "panels.workflow": (
        "Ablauf der Setup.inf: [Product], Set:/Set_-, "
        "Install-/Uninstall-/Repair-/Fehler-/Reboot-Sektionen "
        "mit Einzelschritten (Call, If, #Refs)."
    ),
    "store.package": "Lokaler Paketordner mit Install\\Setup.inf (+ Files).",
    "store.server": "Empirum-Servername; ersetzt %EmpirumServer% im PackageStore-Pfad.",
    "store.root": "PackageStore-Root (UNC oder lokal gemappt).",
    "store.mfr": "Herstellerordner im Store (bei vendor_product_version).",
    "store.product": "Produktname im Zielpfad; leer = aus Paketordner-Namen.",
    "store.version": "Version im Zielpfad; leer = Heuristik aus Ordnernamen.",
    "store.mode": "Ordnerstruktur unter dem PackageStore-Root.",
    "store.overwrite": "Löscht vorhandenes Ziel vor dem Kopieren.",
    "store.dry": "Prüft Pfade ohne zu kopieren – vor dem echten Deploy empfohlen.",
    "store.browse": "Paketordner im Dateisystem wählen.",
    "store.check": "Prüft Install\\Setup.inf, Files\\, SrcDir/SetupInfDir und Lint vor dem Deploy.",
    "store.repair": (
        "Repariert die Setup.inf auf Disk: fehlende Standardsektionen ergänzen "
        "(WAL-Backup automatisch) und danach erneut prüfen."
    ),
    "store.log": "Protokoll der Deploy-Prüfung bzw. des Kopiervorgangs.",
    "wizard.type": "Vorlagentyp: MSI, Unattend-EXE, Script oder Links (Standardskelett).",
    "wizard.source": "Pflichtquelle (MSI/EXE/…); wird nach Files\\ kopiert und inspiziert.",
    "wizard.inspect": (
        "Liest Metadaten aus MSI/PE (Name, Version, Hersteller, ProductCode, Architektur)."
    ),
    "wizard.name": "ProductName in [Application] / SetupInfo.",
    "wizard.version": "ProductVersion der Empirum-Pakets.",
    "wizard.vendor": "DeveloperName / Hersteller (Matrix42-Registry-Keys).",
    "wizard.product_code": "MSI ProductCode aus der Inspektion (wird als V_ProductCode abgelegt).",
    "wizard.arch": "Platform-Hinweis (x64/x86/ARM64/*) für [Setup].",
    "wizard.silent_preset": "Voreinstellung der stillen EXE-Schalter nach Installer-Typ.",
    "wizard.silent_args": "Argumente für CallHidden bei Unattend-EXE (überschreibt Auto).",
    "wizard.processes": "AskKillProcesses: exe|Anzeigename|ABORT – mehrere mit Semikolon.",
    "wizard.needs_aw": "Aktiviert /AW in SetupInfo; Depot-Befehl muss ebenfalls /AW tragen.",
    "wizard.user_part": (
        "Erzeugt [Set:Client] mit CLIENT-Flag; Maschineneinträge in [Product] erhalten "
        "zusätzlich MACHINE und SetupInfo bekommt /AW (Benutzerteil pro angemeldetem Benutzer)."
    ),
    "wizard.user_commands": (
        "Ein Befehl pro Zeile für den Benutzerteil (%AppData%/HKCU zeigen auf den "
        "angemeldeten Benutzer). CallHidden-Zeilen bekommen automatisch die "
        "3010/0-ErrorLevel-Prüfung."
    ),
    "wizard.target": "Zielverzeichnis, unter dem der Paketordner Name_Version angelegt wird.",
    "wizard.folders": "Zusätzliche Ordner kopieren (cmd /c xcopy aus Files\\ nach Zielpfad).",
    "wizard.registry": "Registry-Einträge in [Reg:Product] oder .reg-Importe via reg.exe.",
    "wizard.links": "AllUsers Startmenü-Verknüpfungen in [Shell:Product] (%CommonPrograms%).",
    "wizard.summary": "Zusammenfassung vor dem Erzeugen.",
    "wizard.back": "Vorheriger Wizard-Schritt.",
    "wizard.next": (
        "Nächster Schritt bzw. Paket erzeugen – danach lokal prüfen, PackageStore separat."
    ),

    "error.reboot": "Setzt Reboot=0 in [Application] (unkontrollierten Reboot vermeiden).",
    "error.abort": "Abort-Text für Fehlersektionen bei fehlgeschlagener Installation.",
    "error.logmsg": "ErrorLogMsg – Meldung, die Empirum ins Log schreibt.",
}


def bind_field(widget: QWidget, tip_key: str) -> None:
    bind_tip(widget, FIELD_TIPS[tip_key])


def bind_labeled_field(
    label: QWidget,
    field: QWidget,
    tip_key: str,
) -> None:
    """Bind the same learning tip to a form label and its input widget."""
    text = FIELD_TIPS[tip_key]
    bind_tip(label, text)
    bind_tip(field, text)