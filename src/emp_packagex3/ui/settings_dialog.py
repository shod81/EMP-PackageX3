"""Settings dialog for EMP-PackageX3 – grouped, admin-oriented layout."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.settings import AppSettings
from emp_packagex3.ui.tooltip_mode import (
    apply_tooltip_mode,
    bind_field,
    bind_labeled_field,
)


def _help(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setWordWrap(True)
    lab.setObjectName("settingsHelp")
    lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lab


def _section_title(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName("settingsSection")
    return lab


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Einstellungen – EMP-PackageX3")
        self.resize(620, 640)
        self.setMinimumSize(520, 480)
        self._theme_name = (settings.theme or "light").casefold()

        self._theme = QComboBox()
        self._theme.addItem("Hell (light)", "light")
        self._theme.addItem("Dunkel (dark)", "dark")
        theme_val = (settings.theme or "light").casefold()
        self._theme.setCurrentIndex(1 if theme_val == "dark" else 0)

        self._roots = QTextEdit()
        self._roots.setPlainText("\n".join(settings.runner_roots))
        self._roots.setMaximumHeight(90)
        self._marker = QCheckBox("VM-Marker-Datei .emp_packagex3_vm im Whitelist-Root verlangen")
        self._marker.setChecked(settings.require_vm_marker)

        self._depot = QLineEdit(settings.depot_path)
        self._depot.setPlaceholderText(r"C:\Users\…\Documents\EMP-PackageX3-Depot")
        self._manifest = QLineEdit(settings.update_manifest_url)
        self._manifest.setPlaceholderText("leer = <Depot>/VERSION.json")

        self._debug = QCheckBox("Debug-Logging in Datei (für Beta empfohlen)")
        self._debug.setChecked(settings.debug_logging)
        self._log_dir = QLineEdit(settings.log_dir)
        self._log_dir.setPlaceholderText("leer = AppData\\…\\HodriusSystems\\EMP-PackageX3\\logs")

        self._empirum_server = QLineEdit(settings.empirum_server)
        self._empirum_server.setPlaceholderText("empirum01.firma.local")
        self._package_store = QLineEdit(settings.package_store_path)
        self._package_store.setPlaceholderText(
            r"\\%EmpirumServer%\Configurator$\PackageStore"
        )
        self._store_mode = QComboBox()
        self._store_mode.addItem(
            "Hersteller \\ Produkt \\ Version", "vendor_product_version"
        )
        self._store_mode.addItem("Flach (Produkt_Version)", "flat")
        mode = (settings.package_store_mode or "vendor_product_version").casefold()
        self._store_mode.setCurrentIndex(1 if mode == "flat" else 0)

        self._tooltip_mode = QCheckBox("Tooltip-Modus (Lernhilfen beim Hover, auch F1)")
        self._tooltip_mode.setChecked(settings.tooltip_mode)

        self._undocumented = QCheckBox(
            "Experimentell: undokumentierte Befehle (Klasse 1) freischalten"
        )
        self._undocumented.setChecked(settings.undocumented_commands)

        # Labels for tip binding
        theme_lbl = QLabel("Oberfläche")
        roots_lbl = QLabel("Erlaubte Roots (eine Zeile = ein Pfad)")
        depot_lbl = QLabel("Depot-Pfad oder -URL")
        manifest_lbl = QLabel("Manifest-Override")
        log_lbl = QLabel("Log-Ordner")
        server_lbl = QLabel("EmpirumServer (Hostname)")
        store_lbl = QLabel("PackageStore-Pfad")
        mode_lbl = QLabel("Zielstruktur")

        bind_labeled_field(theme_lbl, self._theme, "settings.theme")
        bind_field(roots_lbl, "settings.runner_roots_label")
        bind_field(self._roots, "settings.runner_roots")
        bind_field(self._marker, "settings.vm_marker")
        bind_labeled_field(depot_lbl, self._depot, "settings.depot")
        bind_labeled_field(manifest_lbl, self._manifest, "settings.manifest")
        bind_field(self._debug, "settings.debug")
        bind_labeled_field(log_lbl, self._log_dir, "settings.log_dir")
        bind_labeled_field(server_lbl, self._empirum_server, "settings.empirum_server")
        bind_labeled_field(store_lbl, self._package_store, "settings.package_store")
        bind_labeled_field(mode_lbl, self._store_mode, "settings.store_mode")
        bind_field(self._tooltip_mode, "settings.tooltip_mode")
        bind_field(self._undocumented, "settings.undocumented_commands")

        content = QWidget()
        form = QVBoxLayout(content)
        form.setSpacing(14)
        form.setContentsMargins(4, 4, 12, 4)

        form.addWidget(_section_title("Darstellung & Lernen"))
        form.addWidget(
            _help(
                "Theme der Oberfläche und optionale Lern-Tooltips für Menüs und Felder. "
                "Tooltip-Modus lässt sich auch über Hilfe → Tooltip-Modus bzw. F1 umschalten."
            )
        )
        appearance = QFormLayout()
        appearance.setSpacing(8)
        appearance.addRow(theme_lbl, self._theme)
        appearance.addRow(self._tooltip_mode)
        form.addLayout(appearance)

        form.addWidget(_section_title("Experimentell: undokumentierte Befehle"))
        form.addWidget(
            _help(
                "Undokumentierte Konstrukte sind im Empirum-Interpreter 26.1.0 verifiziert "
                "vorhanden (z. B. CollapseEnv, Extract, RenDir, BlockInput), fehlen aber "
                "komplett in der offiziellen Matrix42-Hilfe. Es gibt KEINEN Support- oder "
                "Sicherheitsnetz; die Semantik ist teils offen (Extract, /SX, /Y:). "
                "Freischaltung ergänzt Completer, Linter-Freigabe und einen eigenen "
                "Hilfe-Bereich mit Warnhinweisen."
            )
        )
        expert_form = QFormLayout()
        expert_form.setSpacing(8)
        expert_form.addRow(self._undocumented)
        form.addLayout(expert_form)

        form.addWidget(_section_title("Test-Runner (Sicherheit)"))
        form.addWidget(
            _help(
                "Setup.exe-Dry-Runs nur unter diesen Verzeichnissen. Mit VM-Marker "
                "verhindert ihr versehentliche Läufe auf Produktiv-PCs – die Datei "
                ".emp_packagex3_vm muss im Whitelist-Root liegen."
            )
        )
        form.addWidget(roots_lbl)
        form.addWidget(self._roots)
        form.addWidget(self._marker)

        form.addWidget(_section_title("App-Update-Depot"))
        form.addWidget(
            _help(
                "Ort für EMP-PackageX3-Updates (Onedir / VERSION.json) – "
                "nicht der Empirum PackageStore für Softwarepakete. "
                "Standard: Dokumente\\EMP-PackageX3-Depot. Später auch UNC oder https://…"
            )
        )
        depot_form = QFormLayout()
        depot_form.setSpacing(8)
        depot_form.addRow(depot_lbl, self._depot)
        depot_form.addRow(manifest_lbl, self._manifest)
        form.addLayout(depot_form)

        form.addWidget(_section_title("Protokollierung"))
        form.addWidget(
            _help(
                "Rotierende Logdateien für Beta-Diagnose. Über Hilfe → Feedback-Paket "
                "lassen sich Logs als ZIP exportieren."
            )
        )
        log_form = QFormLayout()
        log_form.setSpacing(8)
        log_form.addRow(self._debug)
        log_form.addRow(log_lbl, self._log_dir)
        form.addLayout(log_form)

        form.addWidget(_section_title("Empirum PackageStore"))
        form.addWidget(
            _help(
                "Ziel für fertige Setup.inf-Pakete (MMC-Import). Typisch "
                "\\\\Server\\Configurator$\\PackageStore. Deploy erfolgt manuell unter "
                "Werkzeuge → Nach Empirum PackageStore deployen… – nicht automatisch "
                "nach dem PackageCreator."
            )
        )
        store_form = QFormLayout()
        store_form.setSpacing(8)
        store_form.addRow(server_lbl, self._empirum_server)
        store_form.addRow(store_lbl, self._package_store)
        store_form.addRow(mode_lbl, self._store_mode)
        form.addLayout(store_form)
        form.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        scroll.setObjectName("settingsScroll")

        header = QWidget()
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(2)
        brand = QLabel("Einstellungen")
        brand.setObjectName("settingsBrand")
        sub = QLabel(
            "App-Verhalten, Runner-Sicherheit, Update-Depot und Empirum PackageStore. "
            "Änderungen gelten nach OK für diese Installation."
        )
        sub.setObjectName("settingsSubtitle")
        sub.setWordWrap(True)
        header_lay.addWidget(brand)
        header_lay.addWidget(sub)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_btn is not None:
            ok_btn.setText("Speichern")
            ok_btn.setObjectName("settingsPrimary")
            bind_field(ok_btn, "settings.ok")
        if cancel_btn is not None:
            cancel_btn.setText("Abbrechen")
            bind_field(cancel_btn, "settings.cancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)
        root.addWidget(header)
        root.addWidget(scroll, stretch=1)
        root.addWidget(buttons)

        self.setStyleSheet(self._dialog_qss())
        apply_tooltip_mode(self, settings.tooltip_mode)

    def _dialog_qss(self) -> str:
        from emp_packagex3.ui.theme import dialog_colors

        c = dialog_colors(self._theme_name)
        return f"""
            QDialog {{
                background: {c["bg"]};
                color: {c["text"]};
            }}
            QLabel#settingsBrand {{
                font-size: 15px;
                font-weight: 600;
                color: {c["brand"]};
            }}
            QLabel#settingsSubtitle {{
                color: {c["muted"]};
                font-size: 12px;
            }}
            QLabel#settingsSection {{
                font-size: 13px;
                font-weight: 600;
                color: {c["brand"]};
                padding-top: 6px;
            }}
            QLabel#settingsHelp {{
                background: {c["help_bg"]};
                border-left: 3px solid {c["help_accent"]};
                color: {c["help_text"]};
                padding: 8px 10px;
                font-size: 12px;
            }}
            QScrollArea#settingsScroll {{
                background: transparent;
                border: none;
            }}
            QLineEdit, QComboBox, QTextEdit {{
                min-height: 26px;
                background: {c["input_bg"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
            }}
            QPushButton#settingsPrimary {{
                background: {c["primary"]};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton#settingsPrimary:hover {{
                background: {c["primary_hover"]};
            }}
        """

    def result_settings(self, base: AppSettings) -> AppSettings:
        roots = [
            line.strip()
            for line in self._roots.toPlainText().splitlines()
            if line.strip()
        ]
        theme_data = self._theme.currentData()
        theme = str(theme_data) if theme_data else "light"
        mode_data = self._store_mode.currentData()
        store_mode = str(mode_data) if mode_data else "vendor_product_version"
        return AppSettings(
            theme=theme,
            runner_roots=roots or list(base.runner_roots),
            require_vm_marker=self._marker.isChecked(),
            depot_path=self._depot.text().strip() or base.depot_path,
            update_manifest_url=self._manifest.text().strip(),
            last_update_check=base.last_update_check,
            debug_logging=self._debug.isChecked(),
            log_dir=self._log_dir.text().strip(),
            empirum_server=self._empirum_server.text().strip(),
            package_store_path=self._package_store.text().strip()
            or base.package_store_path,
            package_store_mode=store_mode or base.package_store_mode,
            tooltip_mode=self._tooltip_mode.isChecked(),
            undocumented_commands=self._undocumented.isChecked(),
        )
