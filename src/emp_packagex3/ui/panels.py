"""Visual editor panels: overview, registry, shell links, workflow."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.execution_logic import execution_steps
from emp_packagex3.ui.tooltip_mode import bind_field
from empirum_core.ast.model import CommentLine, Document, KeyValueLine, RawLine, Section
from empirum_core.serializer.serialize import touch_key_value

_ROLE = Qt.ItemDataRole.UserRole

_TIP_OVERVIEW = (
    "Übersicht: alle Sektionen der Setup.inf; Werte in der rechten Spalte editierbar."
)
_TIP_REGISTRY = "Registry: erkannte Registry-Zeilen zur schnellen Kontrolle."
_TIP_SHELL = "ShellLinks: Verknüpfungen und #Shell-Referenzen verwalten."
_TIP_WORKFLOW = (
    "Workflow: Ablaufsektionen ([Product], Set:/Install/Uninstall/Repair/Fehler/Reboot) "
    "mit Einzelschritten."
)

# The standard uses Set:Name; legacy templates used Set_Name. Also bare Install*/Repair*/…
_WORKFLOW_EXACT = frozenset(
    {
        "product",
        "ok",
        "rebootrequired",
        "installation",
        "repair",
        "installmsi",
        "repairmsi",
    }
)


class VisualPanels(QTabWidget):
    """Right-hand visual tools. Emits document_changed when user edits structure."""

    document_changed = Signal(object)  # Document

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._document: Document | None = None

        self._overview = QTreeWidget()
        self._overview.setHeaderLabels(["Struktur", "Wert"])
        self._overview.itemChanged.connect(self._on_overview_edit)

        self._registry = QTreeWidget()
        self._registry.setHeaderLabels(["Sektion", "Feld", "Wert"])

        self._shell = QListWidget()
        self._shell_dest = QComboBox()
        self._shell_dest.addItem(
            "Common Desktop – All Users Desktop (%CommonDesktop%)", "%CommonDesktop%"
        )
        self._shell_dest.addItem(
            "Common Programs – All Users Startmenü (%CommonPrograms%)", "%CommonPrograms%"
        )
        self._shell_name = QLineEdit()
        self._shell_path = QLineEdit()
        self._shell_path.setPlaceholderText(r"%ProgramFiles%\App\app.exe")
        shell_page = QWidget()
        shell_layout = QVBoxLayout(shell_page)
        shell_layout.addWidget(QLabel("ShellLinks / #Shell-Referenzen"))
        shell_layout.addWidget(self._shell)
        shell_layout.addWidget(QLabel("Ablageort"))
        shell_layout.addWidget(self._shell_dest)
        shell_layout.addWidget(QLabel("Anzeigename"))
        shell_layout.addWidget(self._shell_name)
        shell_layout.addWidget(QLabel("Ziel (%…%-Variable bevorzugt)"))
        shell_layout.addWidget(self._shell_path)
        add_btn = QPushButton("Verknüpfung hinzufügen")
        add_btn.clicked.connect(self._add_shell_link)
        shell_layout.addWidget(add_btn)
        shell_layout.addStretch(1)

        self._workflow = QTreeWidget()
        self._workflow.setHeaderLabels(["Ablauf / Schritt", "Detail"])
        self._workflow.setColumnWidth(0, 220)

        self._exec_mode = QComboBox()
        self._exec_mode.addItem("Struktur (Sektionen)")
        self._exec_mode.addItem("Ausführung: Installation (top-down)")
        self._exec_mode.addItem("Ausführung: Deinstallation (bottom-up)")
        self._exec_mode.currentIndexChanged.connect(lambda _i: self._reload())
        bind_field(self._exec_mode, "panels.exec_mode")
        workflow_page = QWidget()
        workflow_layout = QVBoxLayout(workflow_page)
        workflow_layout.setContentsMargins(0, 0, 0, 0)
        workflow_layout.addWidget(self._exec_mode)
        workflow_layout.addWidget(self._workflow)

        self.addTab(self._overview, "Übersicht")
        self.addTab(self._registry, "Registry")
        self.addTab(shell_page, "ShellLinks")
        self.addTab(workflow_page, "Workflow")

        bind_field(self._overview, "panels.overview")
        bind_field(self._registry, "panels.registry")
        bind_field(self._shell, "panels.shell")
        bind_field(self._shell_dest, "panels.shell_dest")
        bind_field(self._shell_name, "panels.shell_name")
        bind_field(self._shell_path, "panels.shell_path")
        bind_field(add_btn, "panels.shell_add")
        bind_field(self._workflow, "panels.workflow")
        self.setTabToolTip(0, _TIP_OVERVIEW)
        self.setTabToolTip(1, _TIP_REGISTRY)
        self.setTabToolTip(2, _TIP_SHELL)
        self.setTabToolTip(3, _TIP_WORKFLOW)

    def set_document(self, document: Document) -> None:
        self._document = document
        self._reload()

    def _reload(self) -> None:
        doc = self._document
        self._overview.blockSignals(True)
        self._overview.clear()
        self._registry.clear()
        self._shell.clear()
        self._workflow.clear()
        if doc is None:
            self._overview.blockSignals(False)
            return

        if self._exec_mode.currentIndex() > 0:
            self._load_execution_view(doc)
            self._overview.blockSignals(False)
            return

        for section in doc.sections:
            sec_item = QTreeWidgetItem([f"[{section.name}]", ""])
            self._overview.addTopLevelItem(sec_item)
            for node in section.lines:
                if isinstance(node, KeyValueLine):
                    child = QTreeWidgetItem([node.key, node.value])
                    child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable)
                    child.setData(0, _ROLE, (section.name, node.key))
                    sec_item.addChild(child)
                    if _looks_registry(section.name, node.key):
                        self._registry.addTopLevelItem(
                            QTreeWidgetItem([section.name, node.key, node.value])
                        )
                elif isinstance(node, RawLine) and "#Shell" in node.text:
                    self._shell.addItem(node.text.strip())
            if section.name.casefold().startswith("shell:"):
                for node in section.lines:
                    if isinstance(node, RawLine) and node.text.strip():
                        self._shell.addItem(f"[{section.name}] {node.text.strip()}")
            if _workflow_section(section.name):
                self._add_workflow_section(section)
            sec_item.setExpanded(True)
        self._overview.blockSignals(False)

    def _load_execution_view(self, doc: Document) -> None:
        """Numbered steps in true execution order (install or uninstall)."""
        uninstall = self._exec_mode.currentIndex() == 2
        for step in execution_steps(doc, uninstall=uninstall):
            line = f" Z{step.line_no}" if step.line_no else ""
            item = QTreeWidgetItem(
                [f"{step.order}.", f"[{step.section}]{line} {step.text}", step.note]
            )
            if step.kind == "shell-auto":
                item.setForeground(0, Qt.GlobalColor.darkYellow)
            elif step.kind == "info":
                item.setForeground(0, Qt.GlobalColor.red)
            self._workflow.addTopLevelItem(item)

    def _add_workflow_section(self, section: Section) -> None:
        steps = _workflow_steps(section)
        role = _workflow_role(section.name)
        header = QTreeWidgetItem(
            [f"[{section.name}]", f"{len(steps)} Schritte · {role}"]
        )
        self._workflow.addTopLevelItem(header)
        for kind, detail in steps:
            header.addChild(QTreeWidgetItem([kind, detail]))
        header.setExpanded(True)

    def _on_overview_edit(self, item: QTreeWidgetItem, column: int) -> None:
        if self._document is None or column != 1:
            return
        data = item.data(0, _ROLE)
        if not isinstance(data, tuple) or len(data) != 2:
            return
        section_name, key = data
        section = self._document.section(str(section_name))
        if section is None:
            return
        for node in section.lines:
            if isinstance(node, KeyValueLine) and node.key == key:
                node.value = item.text(1)
                node.preserve_raw = False
                node.raw = None
                self.document_changed.emit(self._document)
                return

    def _add_shell_link(self) -> None:
        """Append a standard-conformant link line to [Shell:Product].

        Reference syntax: comma-separated fields
        ``"<Root>%\\<Name>", <Ziel>[, <Parameter>[, …]]`` with Root being
        %CommonDesktop% or %CommonPrograms% – activated via ShellLinks=1 /
        CommonShellLinks=1 in [Application] (no #Shell ref, see VAL-005).
        """
        if self._document is None:
            return
        name = self._shell_name.text().strip() or "App"
        path = self._shell_path.text().strip() or r"%ProgramFiles%\App\app.exe"
        root = self._shell_dest.currentData() or "%CommonDesktop%"
        sec_name = "Shell:Product"
        section = self._document.section(sec_name)
        if section is None:
            section = Section(name=sec_name, lines=[])
            self._document.sections.append(section)
        section.lines.append(
            RawLine(text=f'"{root}\\{name}", "{path}"')
        )
        # Shell links only execute when the Application flags are enabled.
        app = self._document.section("Application")
        if app is not None:
            if touch_key_value(app, "ShellLinks", "1") is None:
                app.lines.append(KeyValueLine(key="ShellLinks", value="1", preserve_raw=False))
            if touch_key_value(app, "CommonShellLinks", "1") is None:
                app.lines.append(
                    KeyValueLine(key="CommonShellLinks", value="1", preserve_raw=False)
                )
        self.document_changed.emit(self._document)
        self._reload()


def _looks_registry(section_name: str, key: str) -> bool:
    s = section_name.casefold()
    k = key.casefold()
    return "reg" in s or k in {"root", "key", "valuename", "valuedata"} or k.startswith("hk")


def _workflow_section(name: str) -> bool:
    """True for install/uninstall flow sections (standard Set:… and legacy Set_…)."""
    n = name.casefold().lstrip("-")
    if n in _WORKFLOW_EXACT:
        return True
    if n.startswith(("set:", "set_")):
        return True
    if n.startswith(("uninstall", "reinstall", "deinstall", "repair", "error")):
        return True
    # InstallMSI / Installation / Install_x64 — but not [Installer] copy list
    return bool(n.startswith("install") and n != "installer")


def _workflow_role(name: str) -> str:
    n = name.casefold()
    if n == "product":
        return "Einstieg (GOSUB)"
    if n.startswith("set:appactive") or n.startswith("set_appactive"):
        return "Prozesse"
    if "error" in n:
        return "Fehlerpfad"
    # Covers Set:Deinstallation, Set_Uninstall and bare [Uninstall]/[Uninstall_x64]
    if "deinstall" in n or "uninstall" in n:
        return "Deinstallation"
    if "reinstall" in n or "repair" in n:
        return "Reparatur/Update"
    if n == "rebootrequired" or "reboot" in n:
        return "Reboot"
    if n.startswith("set:product") or n.startswith("set_install") or n.startswith("install"):
        return "Installation"
    if n.startswith("set:"):
        return "Set-Block"
    return "Ablauf"


def _workflow_steps(section: Section) -> list[tuple[str, str]]:
    """Actionable lines only (skip blank/comment)."""
    out: list[tuple[str, str]] = []
    for node in section.lines:
        if isinstance(node, CommentLine):
            continue
        if isinstance(node, KeyValueLine):
            out.append((node.key, node.value))
            continue
        if isinstance(node, RawLine):
            text = node.text.strip()
            if not text or text.startswith(";"):
                continue
            if text.startswith("#"):
                out.append(("→ Sektion", text))
            elif text.casefold().startswith("if "):
                out.append(("If", text[2:].strip() if text[2:3] == " " else text))
            else:
                # Empirum command line: "CallHidden …", "AddMeter -1", …
                parts = text.split(None, 1)
                cmd = parts[0]
                detail = parts[1] if len(parts) > 1 else ""
                out.append((cmd.lstrip("-"), detail))
    return out
