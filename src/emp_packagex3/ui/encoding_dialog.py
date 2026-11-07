"""Encoding choice when detection is ambiguous (R-02 Ausnahmeplan)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from empirum_core.parser.encoding import DetectedEncoding


class EncodingChoiceDialog(QDialog):
    def __init__(
        self,
        detected: DetectedEncoding,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Encoding wählen")
        self._detected = detected
        self._cp = QRadioButton("Windows CP1252 (Empirum-Feldstandard)")
        self._utf = QRadioButton("UTF-8")
        self._keep_bom = QRadioButton("UTF-8 mit BOM beibehalten")
        self._keep_bom.setEnabled(detected.has_bom)
        if detected.name == "utf-8" and detected.has_bom:
            self._keep_bom.setChecked(True)  # preserve roundtrip by default
        elif detected.name == "utf-8":
            self._utf.setChecked(True)
        else:
            self._cp.setChecked(True)
        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "Encoding ist mehrdeutig. Datei wird erst nach Auswahl schreibbar "
                "gespeichert (Plan R-02)."
            )
        )
        root.addWidget(self._cp)
        root.addWidget(self._utf)
        root.addWidget(self._keep_bom)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def chosen(self) -> DetectedEncoding:
        if self._keep_bom.isEnabled() and self._keep_bom.isChecked():
            return DetectedEncoding(name="utf-8", has_bom=True, ambiguous=False)
        if self._utf.isChecked() or self._keep_bom.isChecked():
            return DetectedEncoding(name="utf-8", has_bom=False, ambiguous=False)
        return DetectedEncoding(name="cp1252", has_bom=False, ambiguous=False)
