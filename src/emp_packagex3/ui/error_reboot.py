"""Error / Reboot configuration mask.

Edits the standard error sections emitted by the templates
([Set:InstallationError] / [Set:ReinstallationError] / [Set:DeInstallationError])
in reference command style: ``Abort <text>`` / ``ErrorLogMsg <text>`` with a
'-' prefix in the deinstallation path. Legacy [Error_*] KV sections are no
longer generated.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.ui.tooltip_mode import apply_tooltip_mode, bind_field
from empirum_core.ast.model import Document, KeyValueLine, RawLine, Section

_ERROR_SECTIONS = (
    ("Set:InstallationError", False),
    ("Set:ReinstallationError", False),
    ("Set:DeInstallationError", True),
)


class ErrorRebootDialog(QDialog):
    def __init__(
        self,
        document: Document,
        parent: QWidget | None = None,
        *,
        tooltip_mode: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fehler- / Reboot-Maske")
        self._document = document
        current_reboot = _first_kv(document, "Application", "Reboot")
        current_abort = _command_arg(document, "Set:InstallationError", "Abort")
        current_err = _command_arg(document, "Set:InstallationError", "ErrorLogMsg")
        self._reboot = QCheckBox("Reboot=0 erzwingen (empfohlen)")
        self._reboot.setChecked((current_reboot or "1").strip() != "0")
        self._abort = QLineEdit(current_abort or "Installation fehlgeschlagen")
        self._err = QLineEdit(current_err or "Details siehe Logdatei")
        bind_field(self._reboot, "error.reboot")
        bind_field(self._abort, "error.abort")
        bind_field(self._err, "error.logmsg")
        form = QFormLayout()
        form.addRow(self._reboot)
        form.addRow("Abort-Text (Fehlersektionen)", self._abort)
        form.addRow("ErrorLogMsg", self._err)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(buttons)
        apply_tooltip_mode(self, tooltip_mode)

    def apply(self) -> Document:
        doc = self._document
        if self._reboot.isChecked():
            app = doc.section("Application")
            if app is None:
                app = Section(name="Application", lines=[])
                doc.sections.insert(0, app)
            _set_kv(app, "Reboot", "0")
        abort = self._abort.text().strip() or "Installation fehlgeschlagen"
        err = self._err.text().strip() or "Details siehe Logdatei"
        for sec_name, uninstall in _ERROR_SECTIONS:
            section = doc.section(sec_name)
            if section is None:
                section = Section(name=sec_name, lines=[])
                doc.sections.append(section)
            prefix = "-" if uninstall else ""
            _set_command(section, f"{prefix}Abort", abort)
            _set_command(section, f"{prefix}ErrorLogMsg", err)
        return doc


def _set_kv(section: Section, key: str, value: str) -> None:
    for node in section.lines:
        if isinstance(node, KeyValueLine) and node.key.casefold() == key.casefold():
            node.value = value
            node.preserve_raw = False
            node.raw = None
            return
    section.lines.append(KeyValueLine(key=key, value=value, preserve_raw=False))


def _set_command(section: Section, command: str, arg: str) -> None:
    """Set ``Command arg`` in command style, updating an existing line in place."""
    wanted = command.casefold().lstrip("-")
    for node in section.lines:
        if isinstance(node, RawLine):
            stripped = node.text.strip()
            parts = stripped.split(None, 1)
            if parts and parts[0].casefold().lstrip("-") == wanted:
                node.text = f"{command} {arg}"
                return
    section.lines.append(RawLine(text=f"{command} {arg}"))


def _first_kv(document: Document, section_name: str, key: str) -> str | None:
    section = document.section(section_name)
    if section is None:
        return None
    for node in section.lines:
        if isinstance(node, KeyValueLine) and node.key.casefold() == key.casefold():
            return node.value
    return None


def _command_arg(document: Document, section_name: str, command: str) -> str | None:
    section = document.section(section_name)
    if section is None:
        return None
    wanted = command.casefold()
    for node in section.lines:
        if isinstance(node, RawLine):
            parts = node.text.strip().split(None, 1)
            if parts and parts[0].casefold().lstrip("-") == wanted:
                return parts[1] if len(parts) > 1 else ""
    return None
