"""PackageCreator wizard – guided Empirum/Standard package creation for IT admins."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.ui.tooltip_mode import apply_tooltip_mode, bind_field
from empirum_core.inspect import (
    FolderCopySpec,
    PackageMetadata,
    RegFileSpec,
    RegistryEntrySpec,
    ShellLinkSpec,
)
from empirum_core.parser.reg_parser import parse_reg_file, reg_has_hkcu
from empirum_services.creator.generator import generate_package, inspect_source

_SILENT_PRESETS: list[tuple[str, str, str]] = [
    ("Auto (aus Inspektion)", "", ""),
    ("NSIS", "NSIS", "/S"),
    ("Inno Setup", "Inno", "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART"),
    ("InstallShield", "InstallShield", "/s /sms"),
    ("Generic quiet", "Generic", "/quiet /norestart"),
    ("Benutzerdefiniert…", "", ""),
]

_STEPS: tuple[tuple[str, str], ...] = (
    ("Typ", "Paketmethode wählen"),
    ("Quelle", "Installer einlesen"),
    ("Metadaten", "Produktidentität"),
    ("Optionen", "Plattform & Laufzeit"),
    ("Ergänzungen", "Ordner, Registry & Startmenü"),
    ("Deinstall", "Was die Vorlage macht"),
    ("Erzeugen", "Paket schreiben"),
)


_TYPE_HELP: dict[str, str] = {
    "MSI": (
        "Windows-Installer (.msi). Erzeugt Standard-MSI-Vorlage mit MsiExec /I "
        "(ALLUSERS, REBOOT=REALLYSUPPRESS, ARPSYSTEMCOMPONENT), Reparatur-/GUID-Logik "
        "und Set:Deinstallation."
    ),
    "EXE": (
        "Unattend-EXE (NSIS, Inno, InstallShield, …). CallHidden mit Silent-Schaltern, "
        "optional AskKillProcesses und GetUninstallKeyName für die Deinstallation."
    ),
    "Script": (
        "Eigene Skripte (z. B. install.cmd / uninstall.cmd unter Files\\). "
        "Geeignet für Wrapper, Batch oder PowerShell-Aufrufe."
    ),
    "Links": (
        "Vorlage für Shell-Links (Startmenü). ShellLinks=1 steuert [Shell:Product] – "
        "kein zusätzliches #Shell:Product (VAL-005)."
    ),
}


def _help_panel(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setWordWrap(True)
    lab.setObjectName("wizardHelp")
    lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lab


def _title(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName("wizardTitle")
    return lab


def _muted(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName("wizardMuted")
    lab.setWordWrap(True)
    return lab


class AddFolderDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        product_name: str = "App",
        initial_dir: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ordnerkopie hinzufügen")
        self.resize(520, 320)
        self._local_path = initial_dir
        self._product_name = product_name.replace(" ", "_") or "App"

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._folder_name = QLineEdit()
        self._folder_name.setPlaceholderText("z. B. Config oder Templates (unter Files\\)")
        if initial_dir:
            self._folder_name.setText(Path(initial_dir).name)

        browse_btn = QPushButton("Lokalen Quellordner wählen…")
        browse_btn.clicked.connect(self._on_browse)

        name_layout = QHBoxLayout()
        name_layout.addWidget(self._folder_name, stretch=1)
        name_layout.addWidget(browse_btn)

        self._target_path = QComboBox()
        self._target_path.setEditable(True)
        self._update_target_presets()
        self._folder_name.textChanged.connect(lambda _: self._update_target_presets())

        self._flags = QLineEdit("/S /H /E /V /Y")
        self._flags.setPlaceholderText("/S /H /E /V /Y")

        self._delete_on_uninstall = QCheckBox("Bei Deinstallation Ordner löschen (-DelTree)")
        self._delete_on_uninstall.setChecked(True)

        form.addRow("Ordnername (Files\\...):", name_layout)
        form.addRow("Zielpfad auf Client:", self._target_path)
        form.addRow("XCOPY-Flags:", self._flags)
        form.addRow("", self._delete_on_uninstall)

        hint = _muted(
            "Empirum führt XCOPY zuverlässig mit 'cmd /c xcopy \"%Src%\\Files\\<Ordner>\" "
            "\"<Ziel>\" /S /H /E /V /Y' aus.\n"
            "Lokale Ordner werden beim Paketerzeugen automatisch nach Files\\<Ordner> kopiert."
        )
        layout.addLayout(form)
        layout.addWidget(hint)

        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        ok_btn = QPushButton("Hinzufügen")
        ok_btn.setObjectName("wizardPrimary")
        cancel_btn = QPushButton("Abbrechen")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(ok_btn)
        layout.addLayout(btn_box)

    def _update_target_presets(self) -> None:
        p = self._product_name
        sub = self._folder_name.text().strip() or "Config"
        presets = [
            rf"%ProgramFiles%\{p}\{sub}",
            rf"%ProgramFiles%\{p}",
            rf"%CommonAppData%\{p}\{sub}",
            rf"%AppData%\{p}\{sub}",
            rf"%LocalAppData%\{p}\{sub}",
            rf"%WinDir%\{sub}",
            rf"%App%\{sub}",
        ]
        curr = self._target_path.currentText()
        self._target_path.clear()
        self._target_path.addItems(presets)
        if curr:
            self._target_path.setEditText(curr)

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Lokalen Quellordner wählen")
        if path:
            self._local_path = path
            f_name = Path(path).name
            self._folder_name.setText(f_name)
            self._update_target_presets()

    def _on_accept(self) -> None:
        if not self._folder_name.text().strip():
            QMessageBox.warning(self, "Ordnerkopie", "Bitte einen Ordnernamen angeben.")
            return
        if not self._target_path.currentText().strip():
            QMessageBox.warning(self, "Ordnerkopie", "Bitte einen Zielpfad angeben.")
            return
        self.accept()

    def get_spec(self) -> FolderCopySpec:
        return FolderCopySpec(
            folder_name=self._folder_name.text().strip(),
            target_path=self._target_path.currentText().strip(),
            local_source_path=self._local_path,
            xcopy_flags=self._flags.text().strip() or "/S /H /E /V /Y",
            delete_on_uninstall=self._delete_on_uninstall.isChecked(),
        )


class AddRegistryValueDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registry-Wert anlegen")
        self.resize(500, 280)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._root = QComboBox()
        self._root.addItems(["HKLM", "HKCU", "HKCR"])

        self._key_path = QLineEdit()
        self._key_path.setPlaceholderText(r"Software\Hersteller\Produkt")

        self._value_name = QLineEdit()
        self._value_name.setPlaceholderText("Leer für (Standard)-Wert")

        self._type = QComboBox()
        self._type.addItems(
            [
                "REG_SZ",
                "REG_DWORD",
                "REG_QWORD",
                "REG_EXPAND_SZ",
                "REG_BINARY",
                "REG_MULTI_SZ",
            ]
        )

        self._value_data = QLineEdit()
        self._value_data.setPlaceholderText("Wertdaten")

        self._delete_on_uninstall = QCheckBox("Bei Deinstallation entfernen (-HKLM...)")

        form.addRow("Stamm (Root):", self._root)
        form.addRow("Schlüsselpfad:", self._key_path)
        form.addRow("Wertname:", self._value_name)
        form.addRow("Typ:", self._type)
        form.addRow("Wertdaten:", self._value_data)
        form.addRow("", self._delete_on_uninstall)

        hint = _muted("HKCU-Werte aktivieren automatisch den Benutzerteil (/AW).")
        layout.addLayout(form)
        layout.addWidget(hint)

        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        ok_btn = QPushButton("Hinzufügen")
        ok_btn.setObjectName("wizardPrimary")
        cancel_btn = QPushButton("Abbrechen")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(ok_btn)
        layout.addLayout(btn_box)

    def _on_accept(self) -> None:
        if not self._key_path.text().strip():
            QMessageBox.warning(self, "Registry-Wert", "Bitte einen Schlüsselpfad angeben.")
            return
        self.accept()

    def get_spec(self) -> RegistryEntrySpec:
        return RegistryEntrySpec(
            root=self._root.currentText(),
            key_path=self._key_path.text().strip(),
            value_name=self._value_name.text().strip(),
            reg_type=self._type.currentText(),
            value_data=self._value_data.text().strip(),
            delete_on_uninstall=self._delete_on_uninstall.isChecked(),
        )


class RegImportDialog(QDialog):
    def __init__(self, file_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(".reg-Datei einbinden")
        self.resize(500, 240)
        self._file_path = file_path
        self._file_name = Path(file_path).name

        layout = QVBoxLayout(self)
        layout.addWidget(_title(f"Datei: {self._file_name}"))

        self._mode_reg_exe = QRadioButton("Mit reg.exe importieren (nach Files\\Reg\\ ablegen)")
        self._mode_reg_exe.setChecked(True)
        self._mode_convert = QRadioButton(
            "In native [Reg:Product]-Zeilen umwandeln (empfohlen für sauberes Empirum)"
        )

        layout.addWidget(self._mode_reg_exe)
        layout.addWidget(self._mode_convert)

        self._has_hkcu = reg_has_hkcu(file_path)
        if self._has_hkcu:
            warn = _help_panel(
                "Hinweis: Diese .reg-Datei enthält HKCU-Schlüssel. "
                "Der Benutzerteil (/AW) wird automatisch aktiviert."
            )
            layout.addWidget(warn)

        layout.addStretch(1)
        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        ok_btn = QPushButton("Übernehmen")
        ok_btn.setObjectName("wizardPrimary")
        cancel_btn = QPushButton("Abbrechen")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(ok_btn)
        layout.addLayout(btn_box)

    def import_mode(self) -> str:
        return "reg_exe" if self._mode_reg_exe.isChecked() else "convert"

    def has_hkcu(self) -> bool:
        return self._has_hkcu


class AddShellLinkDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        product_name: str = "App",
        vendor: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Startmenü-Icon hinzufügen")
        self.resize(540, 360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._dest = QComboBox()
        self._dest.addItem(
            "Common Programs – Startmenü All Users (%CommonPrograms%)", "common_programs"
        )
        self._dest.addItem(
            "CommonDesktop – Desktop All Users (%CommonDesktop%)", "common_desktop"
        )
        self._dest.currentIndexChanged.connect(self._on_dest_changed)

        self._name = QLineEdit(product_name or "App")
        self._subfolder = QLineEdit(vendor or "")
        self._subfolder.setPlaceholderText("Unterordner in %CommonPrograms% (leer = Hauptmenü)")

        self._target = QLineEdit()
        self._target.setText(
            rf"%ProgramFiles%\{product_name}\{product_name}.exe"
            if product_name
            else r"%ProgramFiles%\App\app.exe"
        )

        self._args = QLineEdit()
        self._args.setPlaceholderText("Optionale Aufrufargumente")

        self._working_dir = QLineEdit()
        self._working_dir.setText(
            rf"%ProgramFiles%\{product_name}" if product_name else r"%ProgramFiles%\App"
        )

        self._description = QLineEdit(f"{product_name} starten" if product_name else "")

        self._icon_file = QLineEdit()
        self._icon_file.setPlaceholderText("Leer = Ziel-Exe als Icon verwenden")

        self._icon_index = QLineEdit("0")

        self._window_state = QComboBox()
        self._window_state.addItem("1 – Normal", 1)
        self._window_state.addItem("2 – Minimiert", 2)
        self._window_state.addItem("3 – Maximiert", 3)

        form.addRow("Ablageort:", self._dest)
        form.addRow("Titel / Name:", self._name)
        form.addRow("Startmenü-Unterordner:", self._subfolder)
        form.addRow("Ziel (%...%-Variable):", self._target)
        form.addRow("Argumente:", self._args)
        form.addRow("Arbeitsverzeichnis:", self._working_dir)
        form.addRow("Beschreibung / Tooltip:", self._description)
        form.addRow("Icon-Datei (optional):", self._icon_file)
        form.addRow("Icon-Index:", self._icon_index)
        form.addRow("Fensterstatus:", self._window_state)

        hint = _muted(
            "Wird in [Shell:Product] angelegt: Common Programs → AllUsers-Startmenü "
            "(%CommonPrograms%), CommonDesktop → AllUsers-Desktop (%CommonDesktop%).\n"
            "Empirum entfernt die Verknüpfung bei Deinstallation automatisch."
        )
        layout.addLayout(form)
        layout.addWidget(hint)

        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        ok_btn = QPushButton("Hinzufügen")
        ok_btn.setObjectName("wizardPrimary")
        cancel_btn = QPushButton("Abbrechen")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(ok_btn)
        layout.addLayout(btn_box)

    def _on_dest_changed(self, _index: int) -> None:
        desktop = self._dest.currentData() == "common_desktop"
        self._subfolder.setEnabled(not desktop)
        self._subfolder.setPlaceholderText(
            "nur für Common Programs (Startmenü-Unterordner)"
            if desktop
            else "Unterordner in %CommonPrograms% (leer = Hauptmenü)"
        )

    def _on_accept(self) -> None:
        if not self._name.text().strip():
            QMessageBox.warning(self, "Startmenü", "Bitte einen Verknüpfungsnamen angeben.")
            return
        if not self._target.text().strip():
            QMessageBox.warning(self, "Startmenü", "Bitte ein Ziel angeben.")
            return
        self.accept()

    def get_spec(self) -> ShellLinkSpec:
        try:
            idx = int(self._icon_index.text().strip())
        except ValueError:
            idx = 0
        state = self._window_state.currentData()
        dest = self._dest.currentData() or "common_programs"
        return ShellLinkSpec(
            destination=dest,
            name=self._name.text().strip(),
            subfolder=self._subfolder.text().strip() if dest != "common_desktop" else "",
            target=self._target.text().strip(),
            arguments=self._args.text().strip(),
            working_dir=self._working_dir.text().strip(),
            description=self._description.text().strip(),
            icon_file=self._icon_file.text().strip(),
            icon_index=idx,
            window_state=int(state) if state is not None else 1,
        )


class CreatorWizard(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        tooltip_mode: bool = True,
        theme: str = "light",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("PackageCreator – Empirum-Paket erzeugen")
        self.resize(720, 560)
        self.setMinimumSize(640, 480)
        self._theme_name = theme.casefold()
        self._meta = PackageMetadata(package_type="MSI")
        self._stack = QStackedWidget()
        self._step_labels: list[QLabel] = []

        self._source = QLineEdit()
        self._source.setPlaceholderText(r"C:\Installer\Produkt_Setup.msi")
        self._type = QComboBox()
        for key in ("MSI", "EXE", "Script", "Links"):
            self._type.addItem(key, key)
        self._type_help = _help_panel(_TYPE_HELP["MSI"])
        self._type.currentTextChanged.connect(self._on_type_changed)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Anzeigename in [Application] ProductName")
        self._version = QLineEdit("1.0.0")
        self._vendor = QLineEdit()
        self._vendor.setPlaceholderText("Hersteller / DeveloperName")
        self._product_code = QLineEdit()
        self._product_code.setReadOnly(True)
        self._product_code.setPlaceholderText("wird bei MSI-Inspektion gesetzt")

        self._arch = QComboBox()
        self._arch.addItems(["x64", "x86", "ARM64", "*"])
        self._silent_preset = QComboBox()
        for label, _kind, _args in _SILENT_PRESETS:
            self._silent_preset.addItem(label)
        self._silent_args = QLineEdit()
        self._silent_args.setPlaceholderText("/S  bzw.  /VERYSILENT …")
        self._silent_preset.currentIndexChanged.connect(self._on_silent_preset)
        self._processes = QLineEdit()
        self._processes.setPlaceholderText("excel.exe|Excel|ABORT;winword.exe|Word|CONTINUE")
        self._needs_aw = QCheckBox(
            "Benutzerteil aktivieren (/AW in SetupInfo) – "
            "im Software-Depot denselben Schalter setzen"
        )
        self._user_part = QCheckBox(
            "Benutzerteil-Sektion [Set:Client] erzeugen (CLIENT-Flag, "
            "MACHINE-Flags am Maschinenteil, /AW)"
        )
        self._user_commands = QTextEdit()
        self._user_commands.setPlaceholderText(
            "CallHidden \"%Src%\\Files\\usersetup.exe\"\n"
            "MD %AppData%\\Vendor\\AppConfig"
        )
        self._user_commands.setFixedHeight(88)

        self._inspect_status = _muted("Noch nicht inspiziert.")
        self._target = QLineEdit()
        self._target.setPlaceholderText(r"C:\EmpirumPakete")
        self._summary = QTextEdit()
        self._summary.setReadOnly(True)
        self._summary.setObjectName("wizardSummary")
        self._result_path: Path | None = None

        self._folder_copies: list[FolderCopySpec] = []
        self._registry_entries: list[RegistryEntrySpec] = []
        self._reg_files: list[RegFileSpec] = []
        self._shell_links: list[ShellLinkSpec] = []

        bind_field(self._type, "wizard.type")
        bind_field(self._source, "wizard.source")
        bind_field(self._name, "wizard.name")
        bind_field(self._version, "wizard.version")
        bind_field(self._vendor, "wizard.vendor")
        bind_field(self._product_code, "wizard.product_code")
        bind_field(self._arch, "wizard.arch")
        bind_field(self._silent_preset, "wizard.silent_preset")
        bind_field(self._silent_args, "wizard.silent_args")
        bind_field(self._processes, "wizard.processes")
        bind_field(self._needs_aw, "wizard.needs_aw")
        bind_field(self._user_part, "wizard.user_part")
        bind_field(self._user_commands, "wizard.user_commands")
        bind_field(self._target, "wizard.target")
        bind_field(self._summary, "wizard.summary")

        self._stack.addWidget(self._page_type())
        self._stack.addWidget(self._page_source())
        self._stack.addWidget(self._page_meta())
        self._stack.addWidget(self._page_options())
        self._stack.addWidget(self._page_enhancements())
        self._stack.addWidget(self._page_uninstall())
        self._stack.addWidget(self._page_generate())
        self._stack.currentChanged.connect(self._update_step_chrome)


        header = self._build_header()
        steps = self._build_step_bar()

        nav = QHBoxLayout()
        self._back = QPushButton("← Zurück")
        self._next = QPushButton("Weiter →")
        self._next.setObjectName("wizardPrimary")
        self._back.clicked.connect(self._go_back)
        self._next.clicked.connect(self._go_next)
        bind_field(self._back, "wizard.back")
        bind_field(self._next, "wizard.next")
        nav.addWidget(self._back)
        nav.addStretch(1)
        nav.addWidget(self._next)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)
        root.addWidget(header)
        root.addWidget(steps)
        root.addWidget(self._stack, stretch=1)
        root.addLayout(nav)

        self.setStyleSheet(self._dialog_qss())
        self._sync_nav()
        self._update_step_chrome(0)
        apply_tooltip_mode(self, tooltip_mode)

    def result_setup_inf(self) -> Path | None:
        return self._result_path

    def _dialog_qss(self) -> str:
        from emp_packagex3.ui.theme import dialog_colors

        c = dialog_colors(self._theme_name)
        return f"""
            QDialog {{
                background: {c["bg"]};
                color: {c["text"]};
            }}
            QLabel#wizardBrand {{
                font-size: 15px;
                font-weight: 600;
                color: {c["brand"]};
            }}
            QLabel#wizardSubtitle {{
                color: {c["muted"]};
                font-size: 12px;
            }}
            QLabel#wizardTitle {{
                font-size: 16px;
                font-weight: 600;
                color: {c["brand"]};
                padding-top: 4px;
            }}
            QLabel#wizardMuted {{
                color: {c["muted"]};
                font-size: 12px;
            }}
            QLabel#wizardHelp {{
                background: {c["help_bg"]};
                border-left: 3px solid {c["help_accent"]};
                color: {c["help_text"]};
                padding: 10px 12px;
                font-size: 12px;
            }}
            QLabel#wizardStep {{
                color: {c["muted"]};
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 10px;
                background: transparent;
            }}
            QLabel#wizardStep[active="true"] {{
                color: #ffffff;
                background: {c["primary"]};
                font-weight: 600;
            }}
            QLabel#wizardStep[done="true"] {{
                color: {c["brand"]};
                background: {c["step_done_bg"]};
            }}
            QFrame#wizardStepBar {{
                background: {c["panel_bg"]};
                border: 1px solid {c["border"]};
                border-radius: 8px;
            }}
            QTextEdit#wizardSummary {{
                background: {c["input_bg"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: 6px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                padding: 8px;
            }}
            QLineEdit, QComboBox, QTextEdit {{
                min-height: 26px;
                background: {c["input_bg"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
            }}
            QPushButton#wizardPrimary {{
                background: {c["primary"]};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 18px;
                font-weight: 600;
            }}
            QPushButton#wizardPrimary:hover {{
                background: {c["primary_hover"]};
            }}
            QPushButton#wizardPrimary:disabled {{
                background: {c["primary_disabled"]};
            }}
            QTabWidget::pane {{
                border: 1px solid {c["border"]};
                background: {c["bg"]};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background: {c["panel_bg"]};
                color: {c["text"]};
                padding: 6px 14px;
                border: 1px solid {c["border"]};
                border-bottom: none;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background: {c["primary"]};
                color: #ffffff;
                font-weight: 600;
            }}
            QTableWidget {{
                background: {c["input_bg"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                gridline-color: {c["border"]};
            }}
            QHeaderView::section {{
                background: {c["panel_bg"]};
                color: {c["brand"]};
                padding: 4px 6px;
                border: 1px solid {c["border"]};
                font-weight: 600;
            }}
        """


    def _build_header(self) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        brand = QLabel("PackageCreator")
        brand.setObjectName("wizardBrand")
        sub = QLabel(
            "Erzeugt ein standardkonformes Empirum-Paket (Install\\Setup.inf + Files\\). "
            "Nach dem Assistenten bitte lokal prüfen – PackageStore-Deploy ist ein eigener Schritt."
        )
        sub.setObjectName("wizardSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(brand)
        lay.addWidget(sub)
        return box

    def _build_step_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("wizardStepBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)
        self._step_labels.clear()
        for i, (short, _long) in enumerate(_STEPS):
            lab = QLabel(f"{i + 1} {short}")
            lab.setObjectName("wizardStep")
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lab.setToolTip(_long)
            self._step_labels.append(lab)
            lay.addWidget(lab, stretch=1)
        return bar

    def _update_step_chrome(self, index: int) -> None:
        for i, lab in enumerate(self._step_labels):
            lab.setProperty("active", "true" if i == index else "false")
            lab.setProperty("done", "true" if i < index else "false")
            lab.style().unpolish(lab)
            lab.style().polish(lab)

    def _page_shell(self, title: str, help_text: str, body: QWidget) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(10)
        lay.addWidget(_title(title))
        lay.addWidget(_help_panel(help_text))
        lay.addWidget(body, stretch=1)
        return page

    def _page_type(self) -> QWidget:
        body = QWidget()
        form = QFormLayout(body)
        form.setSpacing(10)
        form.addRow("Pakettyp", self._type)
        form.addRow(self._type_help)
        form.addRow(
            _muted(
                "MSI und EXE sind die üblichen Wege für Softwareverteilung. "
                "Script/Links für Sonderfälle."
            )
        )
        return self._page_shell(
            "1 · Paketmethode wählen",
            "Dieser Schritt legt fest, welche Empirum-Vorlage erzeugt wird "
            "(Method=MSI oder Unattend). Später im Software-Depot muss dieselbe "
            "Methode und ggf. /AW im Befehl passen.",
            body,
        )

    def _page_source(self) -> QWidget:
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(10)
        row = QHBoxLayout()
        row.addWidget(self._source, stretch=1)
        browse = QPushButton("Durchsuchen…")
        browse.clicked.connect(self._browse_source)
        row.addWidget(browse)
        lay.addLayout(row)
        inspect_btn = QPushButton("Quelle inspizieren")
        inspect_btn.clicked.connect(self._inspect)
        bind_field(inspect_btn, "wizard.inspect")
        lay.addWidget(inspect_btn)
        lay.addWidget(self._inspect_status)
        lay.addStretch(1)
        return self._page_shell(
            "2 · Installer-Quelle",
            "Wählen Sie die MSI/EXE (oder später Skript-Payload). „Inspizieren“ liest "
            "Name, Version, Hersteller, Architektur und bei MSI den ProductCode. "
            "Die Datei wird beim Erzeugen nach Files\\ kopiert und in der Setup.inf "
            "als %Src%\\Files\\… referenziert.",
            body,
        )

    def _page_meta(self) -> QWidget:
        body = QWidget()
        form = QFormLayout(body)
        form.setSpacing(10)
        form.addRow("Produktname", self._name)
        form.addRow("Version", self._version)
        form.addRow("Hersteller", self._vendor)
        form.addRow("MSI ProductCode", self._product_code)
        form.addRow(
            _muted(
                "Diese Felder landen in [Application] und steuern UninstallKeyName / "
                "MachineKeyName unter $Matrix42Packages$. ProductCode wird als "
                "V_ProductCode in [Environment] abgelegt (Referenz); Deinstall nutzt "
                "GetUninstallKeyName(%V_DisplayName%)."
            )
        )
        return self._page_shell(
            "3 · Produktmetadaten",
            "Prüfen Sie die aus der Quelle übernommenen Werte. Falsche Namen führen "
            "später zu doppelten Uninstall-Keys oder fehlender Repair-Erkennung.",
            body,
        )

    def _page_options(self) -> QWidget:
        body = QWidget()
        form = QFormLayout(body)
        form.setSpacing(10)
        form.addRow("Plattform ([Setup] Platform)", self._arch)
        form.addRow("EXE Silent-Preset", self._silent_preset)
        form.addRow("Silent-Argumente", self._silent_args)
        form.addRow("AskKillProcesses", self._processes)
        form.addRow(
            _muted(
                "Prozesse: exe|Anzeigename|ABORT oder CONTINUE, mehrere mit Semikolon. "
                "Leer lassen, wenn keine laufenden Clients beendet werden müssen."
            )
        )
        form.addRow(self._needs_aw)
        form.addRow(self._user_part)
        form.addRow("Benutzerteil-Befehle", self._user_commands)
        form.addRow(
            _muted(
                "Ein Befehl pro Zeile – landet in [Set:Client] und läuft pro "
                "angemeldetem Benutzer (/AW). CallHidden-Zeilen erhalten "
                "automatisch die 3010/0-ErrorLevel-Prüfung."
            )
        )
        return self._page_shell(
            "4 · Laufzeit-Optionen",
            "Platform steuert, auf welchen Clients das Paket läuft (x64 / x86 / *). "
            "Silent-Argumente gelten nur für EXE/Unattend. /AW braucht der Benutzerteil "
            "(HKCU, VU_, [Set:Client]) – identisch in SetupInfo und Depot-Befehl.",
            body,
        )

    def _page_enhancements(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setObjectName("enhancementsTabs")

        # Tab 1: Ordner kopieren
        tab_folders = QWidget()
        lay_f = QVBoxLayout(tab_folders)
        lay_f.setContentsMargins(8, 8, 8, 8)
        lay_f.addWidget(
            QLabel("Zusätzliche Ordner aus %Src%\\Files\\ nach Zielpfad auf dem Client kopieren:")
        )
        self._table_folders = QTableWidget(0, 4)
        self._table_folders.setHorizontalHeaderLabels([
            "Ordner (Files\\...)", "Zielpfad", "XCOPY-Befehl", "Uninstall DelTree"
        ])
        hdr_f = self._table_folders.horizontalHeader()
        hdr_f.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr_f.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr_f.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr_f.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table_folders.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        lay_f.addWidget(self._table_folders)

        btn_row_f = QHBoxLayout()
        add_f_btn = QPushButton("+ Ordner hinzufügen…")
        add_f_btn.clicked.connect(self._add_folder_dialog)
        del_f_btn = QPushButton("Entfernen")
        del_f_btn.clicked.connect(self._remove_folder_entry)
        btn_row_f.addWidget(add_f_btn)
        btn_row_f.addWidget(del_f_btn)
        btn_row_f.addStretch(1)
        lay_f.addLayout(btn_row_f)

        # Tab 2: Registry
        tab_reg = QWidget()
        lay_r = QVBoxLayout(tab_reg)
        lay_r.setContentsMargins(8, 8, 8, 8)
        lay_r.addWidget(
            QLabel("Registry-Werte in [Reg:Product] oder .reg-Dateien importieren:")
        )
        self._table_registry = QTableWidget(0, 4)
        self._table_registry.setHorizontalHeaderLabels([
            "Typ / Modus", "Schlüssel / Datei", "Wertname", "Daten / Pfad"
        ])
        hdr_r = self._table_registry.horizontalHeader()
        hdr_r.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr_r.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr_r.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr_r.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table_registry.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        lay_r.addWidget(self._table_registry)

        btn_row_r = QHBoxLayout()
        add_reg_file_btn = QPushButton("+ .reg-Datei hinzufügen…")
        add_reg_file_btn.clicked.connect(self._add_reg_file_dialog)
        add_reg_val_btn = QPushButton("+ Registry-Wert anlegen…")
        add_reg_val_btn.clicked.connect(self._add_reg_value_dialog)
        del_r_btn = QPushButton("Entfernen")
        del_r_btn.clicked.connect(self._remove_registry_entry)
        btn_row_r.addWidget(add_reg_file_btn)
        btn_row_r.addWidget(add_reg_val_btn)
        btn_row_r.addWidget(del_r_btn)
        btn_row_r.addStretch(1)
        lay_r.addLayout(btn_row_r)

        # Tab 3: Startmenü-Icons
        tab_links = QWidget()
        lay_l = QVBoxLayout(tab_links)
        lay_l.setContentsMargins(8, 8, 8, 8)
        lay_l.addWidget(
            QLabel(
                "AllUsers-Verknüpfungen in [Shell:Product] – Common Programs "
                "(Startmenü) oder CommonDesktop:"
            )
        )
        self._table_shell_links = QTableWidget(0, 4)
        self._table_shell_links.setHorizontalHeaderLabels([
            "Name", "Ablagepfad", "Ziel", "Arbeitsverzeichnis"
        ])
        hdr_l = self._table_shell_links.horizontalHeader()
        hdr_l.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr_l.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr_l.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr_l.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table_shell_links.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        lay_l.addWidget(self._table_shell_links)

        btn_row_l = QHBoxLayout()
        add_link_btn = QPushButton("+ Startmenü-Icon hinzufügen…")
        add_link_btn.clicked.connect(self._add_shell_link_dialog)
        del_link_btn = QPushButton("Entfernen")
        del_link_btn.clicked.connect(self._remove_shell_link_entry)
        btn_row_l.addWidget(add_link_btn)
        btn_row_l.addWidget(del_link_btn)
        btn_row_l.addStretch(1)
        lay_l.addLayout(btn_row_l)

        tabs.addTab(tab_folders, "📁 Ordner kopieren")
        tabs.addTab(tab_reg, "🔑 Registry & .reg")
        tabs.addTab(tab_links, "🚀 Startmenü-Icons")

        bind_field(tab_folders, "wizard.folders")
        bind_field(tab_reg, "wizard.registry")
        bind_field(tab_links, "wizard.links")

        return self._page_shell(
            "5 · Paket-Ergänzungen (Ordner, Registry & Startmenü)",
            "Optional: Zusätzliche Ordner kopieren (cmd /c xcopy), Registry-Keys einspielen "
            "oder Startmenü-Verknüpfungen für alle Benutzer (%CommonPrograms%) anlegen.",
            tabs,
        )

    def _add_folder_dialog(self) -> None:
        pname = self._name.text().strip() or "App"
        dlg = AddFolderDialog(self, product_name=pname)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            spec = dlg.get_spec()
            self._folder_copies.append(spec)
            self._refresh_folder_table()

    def _remove_folder_entry(self) -> None:
        row = self._table_folders.currentRow()
        if 0 <= row < len(self._folder_copies):
            self._folder_copies.pop(row)
            self._refresh_folder_table()

    def _refresh_folder_table(self) -> None:
        self._table_folders.setRowCount(len(self._folder_copies))
        for i, fc in enumerate(self._folder_copies):
            self._table_folders.setItem(i, 0, QTableWidgetItem(f"Files\\{fc.folder_name}"))
            self._table_folders.setItem(i, 1, QTableWidgetItem(fc.target_path))
            src_arg = f'"%Src%\\Files\\{fc.folder_name}"'
            cmd_preview = f'cmd /c xcopy {src_arg} "{fc.target_path}" {fc.xcopy_flags}'
            self._table_folders.setItem(i, 2, QTableWidgetItem(cmd_preview))
            del_text = f'-DelTree "{fc.target_path}"' if fc.delete_on_uninstall else "Nein"
            self._table_folders.setItem(i, 3, QTableWidgetItem(del_text))

    def _add_reg_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Registry-Datei (.reg) wählen",
            "",
            "Registry-Dateien (*.reg);;Alle Dateien (*.*)",
        )
        if not path:
            return
        dlg = RegImportDialog(path, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.has_hkcu():
                self._needs_aw.setChecked(True)
            mode = dlg.import_mode()
            if mode == "reg_exe":
                spec = RegFileSpec(
                    file_name=Path(path).name,
                    local_source_path=path,
                    import_mode="reg_exe",
                    target_subfolder="Reg",
                )
                self._reg_files.append(spec)
            else:
                entries = parse_reg_file(path)
                self._registry_entries.extend(entries)
            self._refresh_registry_table()

    def _add_reg_value_dialog(self) -> None:
        dlg = AddRegistryValueDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            spec = dlg.get_spec()
            if spec.root.upper() == "HKCU":
                self._needs_aw.setChecked(True)
            self._registry_entries.append(spec)
            self._refresh_registry_table()

    def _remove_registry_entry(self) -> None:
        row = self._table_registry.currentRow()
        n_files = len(self._reg_files)
        if 0 <= row < n_files:
            self._reg_files.pop(row)
            self._refresh_registry_table()
        elif n_files <= row < n_files + len(self._registry_entries):
            self._registry_entries.pop(row - n_files)
            self._refresh_registry_table()

    def _refresh_registry_table(self) -> None:
        total = len(self._reg_files) + len(self._registry_entries)
        self._table_registry.setRowCount(total)
        for i, rf in enumerate(self._reg_files):
            self._table_registry.setItem(i, 0, QTableWidgetItem(".reg-Import (reg.exe)"))
            reg_loc = f"Files\\{rf.target_subfolder}\\{rf.file_name}"
            self._table_registry.setItem(i, 1, QTableWidgetItem(reg_loc))
            self._table_registry.setItem(i, 2, QTableWidgetItem("–"))
            src_lbl = rf.local_source_path or rf.file_name
            self._table_registry.setItem(i, 3, QTableWidgetItem(src_lbl))
        offset = len(self._reg_files)
        for j, re_entry in enumerate(self._registry_entries):
            row = offset + j
            root_lbl = f"{re_entry.root} ({re_entry.reg_type})"
            self._table_registry.setItem(row, 0, QTableWidgetItem(root_lbl))
            self._table_registry.setItem(row, 1, QTableWidgetItem(re_entry.key_path))
            val_name = re_entry.value_name or "(Standard)"
            self._table_registry.setItem(row, 2, QTableWidgetItem(val_name))
            self._table_registry.setItem(row, 3, QTableWidgetItem(re_entry.value_data))

    def _add_shell_link_dialog(self) -> None:
        pname = self._name.text().strip() or "App"
        vendor = self._vendor.text().strip()
        dlg = AddShellLinkDialog(self, product_name=pname, vendor=vendor)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            spec = dlg.get_spec()
            self._shell_links.append(spec)
            self._refresh_shell_table()

    def _remove_shell_link_entry(self) -> None:
        row = self._table_shell_links.currentRow()
        if 0 <= row < len(self._shell_links):
            self._shell_links.pop(row)
            self._refresh_shell_table()

    def _refresh_shell_table(self) -> None:
        self._table_shell_links.setRowCount(len(self._shell_links))
        for i, sl in enumerate(self._shell_links):
            self._table_shell_links.setItem(i, 0, QTableWidgetItem(sl.name))
            if sl.destination.casefold() == "common_desktop":
                path = f"%CommonDesktop%\\{sl.name}"
            elif sl.subfolder:
                path = f"%CommonPrograms%\\{sl.subfolder}\\{sl.name}"
            else:
                path = f"%CommonPrograms%\\{sl.name}"
            self._table_shell_links.setItem(i, 1, QTableWidgetItem(path))
            self._table_shell_links.setItem(i, 2, QTableWidgetItem(sl.target))
            self._table_shell_links.setItem(i, 3, QTableWidgetItem(sl.working_dir or "–"))

    def _page_uninstall(self) -> QWidget:
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(8)
        bullets = QLabel(
            "<ul style='margin-left:12px; margin-top:0;'>"
            "<li><b>Install:</b> [Product] → #Set:Product (DONTDELETE) → InstallMSI / "
            "Installation mit ErrorLevel 3010 → RebootRequired.</li>"
            "<li><b>Deinstall:</b> #Set:Deinstallation (DELETE), Befehle mit "
            "<code>-</code>-Präfix, Sleep 3000 nach MSI/EXE-Aufruf.</li>"
            "<li><b>Registry:</b> leere [Reg:Product] / [Reg:OnUninstallProduct] als "
            "Platzhalter – manuell erweitern. <code>-HK…</code> löscht erst bei "
            "Deinstallation; Install-Löschung → Snippet „Reg.exe Delete“.</li>"
            "<li><b>Danach:</b> Paket lokal/VM testen, dann Werkzeuge → PackageStore.</li>"
            "</ul>"
        )
        bullets.setWordWrap(True)
        bullets.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(bullets)
        lay.addStretch(1)
        return self._page_shell(
            "6 · Install- & Deinstall-Logik",
            "Hier mussten Sie nichts eintragen – der Assistent zeigt, was die Standard-Vorlage "
            "automatisch anlegt. So wissen Sie vor dem Erzeugen, welche Sektionen entstehen.",
            body,
        )

    def _page_generate(self) -> QWidget:
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(10)
        lay.addWidget(_muted("Zielordner – darunter entsteht <Name>_<Version>\\"))
        row = QHBoxLayout()
        row.addWidget(self._target, stretch=1)
        browse = QPushButton("Ziel wählen…")
        browse.clicked.connect(self._browse_target)
        row.addWidget(browse)
        lay.addLayout(row)
        lay.addWidget(_muted("Zusammenfassung (wird beim Öffnen dieses Schritts aktualisiert):"))
        lay.addWidget(self._summary, stretch=1)
        return self._page_shell(
            "7 · Paket erzeugen",
            "Schreibt Install\\Setup.inf (Windows-1252/ANSI, CRLF), legt Files\\ an und kopiert "
            "die Quelle. Anschließend Setup.inf im Editor prüfen (Lint F7). "
            "PackageStore-Kopieren ist bewusst kein Teil dieses Assistenten.",
            body,
        )


    def _on_type_changed(self, text: str) -> None:
        self._type_help.setText(_TYPE_HELP.get(text, ""))

    def _on_silent_preset(self, index: int) -> None:
        if index < 0 or index >= len(_SILENT_PRESETS):
            return
        _label, kind, args = _SILENT_PRESETS[index]
        if index == 0:
            from empirum_core.templates import silent_args_for

            self._silent_args.setText(silent_args_for(self._meta))
            return
        if args:
            self._silent_args.setText(args)
        if kind:
            self._meta.exe_kind = kind

    def _browse_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Installer wählen",
            "",
            "Installer (*.msi *.exe);;Alle (*.*)",
        )
        if path:
            self._source.setText(path)

    def _browse_target(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Paketablage wählen")
        if path:
            self._target.setText(path)

    def _inspect(self) -> None:
        path = self._source.text().strip()
        if not path:
            QMessageBox.warning(self, "PackageCreator", "Bitte zuerst eine Quelldatei wählen.")
            return
        try:
            self._meta = inspect_source(path)
        except Exception as exc:
            self._inspect_status.setText(f"Inspektion fehlgeschlagen: {exc}")
            QMessageBox.critical(self, "PackageCreator", f"Inspektion fehlgeschlagen:\n{exc}")
            return
        self._type.setCurrentText(
            self._meta.package_type
            if self._meta.package_type in {"MSI", "EXE", "Script", "Links"}
            else "EXE"
        )
        self._name.setText(self._meta.product_name)
        self._version.setText(self._meta.product_version or "1.0.0")
        self._vendor.setText(self._meta.manufacturer)
        self._product_code.setText(self._meta.product_code)
        idx = self._arch.findText(self._meta.architecture)
        if idx >= 0:
            self._arch.setCurrentIndex(idx)
        kind = (self._meta.exe_kind or "").casefold()
        preset_idx = 0
        for i, (_label, k, _args) in enumerate(_SILENT_PRESETS):
            if k and k.casefold() == kind:
                preset_idx = i
                break
        self._silent_preset.setCurrentIndex(preset_idx)
        bits = [self._meta.display_label()]
        if self._meta.product_code:
            bits.append(f"ProductCode {self._meta.product_code}")
        if self._meta.exe_kind:
            bits.append(f"EXE-Typ {self._meta.exe_kind}")
        self._inspect_status.setText("Gelesen: " + " · ".join(bits))

    def _collect(self) -> None:
        self._meta.package_type = self._type.currentText()
        self._meta.product_name = self._name.text().strip() or self._meta.product_name
        self._meta.product_version = self._version.text().strip() or "1.0.0"
        self._meta.manufacturer = self._vendor.text().strip()
        self._meta.architecture = self._arch.currentText()
        if self._source.text().strip():
            self._meta.source_path = self._source.text().strip()
        code = self._product_code.text().strip()
        if code:
            self._meta.product_code = code
        silent = self._silent_args.text().strip()
        if silent:
            self._meta.properties["silent_args"] = silent
        else:
            self._meta.properties.pop("silent_args", None)
        procs = self._processes.text().strip()
        if procs:
            self._meta.properties["kill_processes"] = procs
        else:
            self._meta.properties.pop("kill_processes", None)
        if self._needs_aw.isChecked() or bool(procs):
            self._meta.properties["needs_aw"] = "1"
        else:
            self._meta.properties.pop("needs_aw", None)
        user_commands = [
            line.strip()
            for line in self._user_commands.toPlainText().splitlines()
            if line.strip()
        ]
        if self._user_part.isChecked() and user_commands:
            self._meta.user_context_commands = user_commands
        else:
            self._meta.user_context_commands = []
        idx = self._silent_preset.currentIndex()
        if 0 <= idx < len(_SILENT_PRESETS):
            _label, kind, _args = _SILENT_PRESETS[idx]
            if kind:
                self._meta.exe_kind = kind
        self._meta.folder_copies = list(self._folder_copies)
        self._meta.registry_entries = list(self._registry_entries)
        self._meta.reg_files = list(self._reg_files)
        self._meta.shell_links = list(self._shell_links)
        if any(e.root.upper() == "HKCU" for e in self._registry_entries):
            self._meta.properties["needs_aw"] = "1"
        for rf in self._reg_files:
            if rf.local_source_path and reg_has_hkcu(rf.local_source_path):
                self._meta.properties["needs_aw"] = "1"

    def _go_back(self) -> None:
        i = self._stack.currentIndex()
        if i > 0:
            self._stack.setCurrentIndex(i - 1)
        self._sync_nav()

    def _go_next(self) -> None:
        i = self._stack.currentIndex()
        if i == self._stack.count() - 1:
            self._generate()
            return
        if i == 1 and self._source.text().strip() and not self._name.text().strip():
            self._inspect()
        self._collect()
        self._stack.setCurrentIndex(i + 1)
        if self._stack.currentIndex() == self._stack.count() - 1:
            self._refresh_summary()
        self._sync_nav()

    def _sync_nav(self) -> None:
        i = self._stack.currentIndex()
        self._back.setEnabled(i > 0)
        last = i == self._stack.count() - 1
        self._next.setText("Paket erzeugen" if last else "Weiter →")

    def _refresh_summary(self) -> None:
        self._collect()
        pkg_name = (
            f"{(self._meta.product_name or 'Package').replace(' ', '_')}"
            f"_{self._meta.product_version or '1.0.0'}"
        )
        target = self._target.text().strip() or "(noch kein Ziel)"
        fc_count = len(self._folder_copies)
        reg_count = len(self._registry_entries) + len(self._reg_files)
        links_count = len(self._shell_links)
        user_part_note = (
            f"[Set:Client] mit {len(self._meta.user_context_commands)} Befehlen"
            if self._meta.has_user_part
            else "–"
        )
        self._summary.setPlainText(
            f"Methode / Typ     : {self._meta.package_type}\n"
            f"Produkt          : {self._meta.product_name}\n"
            f"Version          : {self._meta.product_version}\n"
            f"Hersteller       : {self._meta.manufacturer}\n"
            f"ProductCode      : {self._meta.product_code or '–'}\n"
            f"Platform         : {self._meta.architecture}\n"
            f"EXE-Kind         : {self._meta.exe_kind or '–'}\n"
            f"Silent-Args      : {self._meta.properties.get('silent_args', '(auto)')}\n"
            f"AskKillProcesses : {self._meta.properties.get('kill_processes', '–')}\n"
            f"/AW              : {self._meta.properties.get('needs_aw', '0')}\n"
            f"Benutzerteil     : {user_part_note}\n"
            f"Ordnerkopien     : {fc_count} Verzeichnisse\n"
            f"Registry-Einträge: {reg_count} Einträge\n"
            f"Startmenü-Icons  : {links_count} Verknüpfungen\n"
            f"Quelle           : {self._meta.source_path or '–'}\n"
            f"Zielwurzel       : {target}\n"
            f"Paketordner      : {target}\\{pkg_name}\n"
            f"Setup.inf        : …\\{pkg_name}\\Install\\Setup.inf\n"
        )


    def _generate(self) -> None:
        self._collect()
        target = self._target.text().strip()
        if not target:
            QMessageBox.warning(self, "PackageCreator", "Bitte ein Zielverzeichnis wählen.")
            return
        missing = [
            label
            for label, value in (
                ("Produktname", self._meta.product_name),
                ("Version", self._meta.product_version),
                ("Hersteller", self._meta.manufacturer),
            )
            if not str(value).strip()
        ]
        if missing:
            QMessageBox.warning(
                self,
                "PackageCreator",
                "Bitte ausfüllen: " + ", ".join(missing)
                + "\n(leere Identität erzeugt keine korrekte Setup.inf)",
            )
            return
        try:
            result = generate_package(self._meta, target, kind=self._meta.package_type)
        except Exception as exc:
            QMessageBox.critical(self, "PackageCreator", f"Generierung fehlgeschlagen:\n{exc}")
            return
        self._result_path = result.setup_inf
        errs = [d for d in result.diagnostics if d.severity.value == "error"]
        msg = (
            f"Paket erzeugt.\n\n"
            f"Ordner:\n{result.package_dir}\n\n"
            f"Setup.inf:\n{result.setup_inf}\n\n"
            f"Nächste Schritte: Inhalt prüfen (Lint F7), ggf. auf VM testen, "
            f"danach Werkzeuge → PackageStore deployen."
        )
        for warning in result.warnings:
            msg += f"\n\nWarnung: {warning}"
        if self._meta.architecture.casefold() == "arm64":
            msg += "\n\nHinweis: ARM64 wird als Platform=* erzeugt (eigenes ARM64-Target ab 1.1)."
        if errs:
            msg += f"\n\nAchtung: {len(errs)} Lint-Fehler in der Vorlage – bitte im Editor beheben."
        if self._meta.properties.get("needs_aw") == "1" or self._meta.has_user_part:
            msg += (
                "\n\n/AW ist gesetzt: Im Empirum Software-Depot unter "
                "Paketeigenschaften → Prüfung → Befehl ebenfalls /AW eintragen."
            )
        QMessageBox.information(self, "PackageCreator", msg)
        self.accept()
