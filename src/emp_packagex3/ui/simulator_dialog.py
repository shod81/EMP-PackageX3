"""Simulator result as a non-modal tool window (tree, gaps, state, jump, export).

Replaces the former QMessageBox output: all actions are shown grouped by
section in walk order, gaps are promoted to a dedicated warning group,
the final state is listed, double-click jumps to the editor line and the
report can be exported as text. Core simulator is untouched.
"""

from __future__ import annotations

import html
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.execution_logic import command_note
from emp_packagex3.ui.tooltip_mode import apply_tooltip_mode, bind_field
from empirum_core.ast.model import Document
from empirum_core.simulator import SimMode, SimReport, simulate

_ROLE_LINE = 0x0100  # Qt.ItemDataRole.UserRole equivalent for plain ints


class SimulatorDialog(QDialog):
    """Non-modal tool window showing simulate() results with editor jump."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        document: Document,
        mode: SimMode,
        on_jump: Callable[[int], None],
        theme: str = "light",
        tooltip_mode: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setModal(False)
        self._document = document
        self._mode = mode
        self._on_jump = on_jump
        self._theme_name = theme.casefold()
        self._update_title()
        self.resize(980, 640)
        self.setMinimumSize(700, 480)

        # Header: mode toggle + entry + stats
        self._btn_install = QPushButton("Installation")
        self._btn_install.setCheckable(True)
        self._btn_deinstall = QPushButton("Deinstallation")
        self._btn_deinstall.setCheckable(True)
        self._btn_install.clicked.connect(lambda: self._set_mode(SimMode.INSTALL))
        self._btn_deinstall.clicked.connect(lambda: self._set_mode(SimMode.UNINSTALL))
        bind_field(self._btn_install, "sim.mode")
        bind_field(self._btn_deinstall, "sim.mode")

        self._entry_label = QLabel()
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet("font-weight: 600;")

        header = QHBoxLayout()
        header.addWidget(self._btn_install)
        header.addWidget(self._btn_deinstall)
        header.addWidget(self._entry_label, stretch=1)
        header.addWidget(self._stats_label)

        # Gap banner (visible only with gaps)
        self._gap_banner = QLabel()
        self._gap_banner.setObjectName("gapBanner")
        self._gap_banner.setWordWrap(True)
        self._gap_banner.setVisible(False)

        # Main tree
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filtern (Sektion, Befehl, Detail)…")
        bind_field(self._filter, "sim.filter")
        self._filter.textChanged.connect(lambda _t: self._apply_filter())

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["#", "Befehl", "Detail", "Zeile"])
        # DPI/font-safe sizing: number and line columns follow their content,
        # Detail stretches - fixed pixel widths overlapped at >100% scaling.
        tree_header = self._tree.header()
        tree_header.setMinimumSectionSize(32)
        tree_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tree_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tree_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tree_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        tree_header.setStretchLastSection(False)
        self._tree.itemActivated.connect(self._on_item_activated)
        bind_field(self._tree, "sim.tree")

        buttons = QHBoxLayout()
        refresh = QPushButton("Neu simulieren")
        refresh.clicked.connect(self.refresh)
        bind_field(refresh, "sim.refresh")
        export_btn = QPushButton("Als Text exportieren…")
        export_btn.clicked.connect(self._export)
        bind_field(export_btn, "sim.export")
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.close)
        buttons.addWidget(refresh)
        buttons.addWidget(export_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        root = QVBoxLayout(self)
        root.addLayout(header)
        root.addWidget(self._gap_banner)
        root.addWidget(self._filter)
        root.addWidget(self._tree, stretch=1)
        root.addLayout(buttons)

        self.setStyleSheet(self._dialog_qss())
        self._sync_mode_buttons()
        self.refresh()
        apply_tooltip_mode(self, tooltip_mode)

    # -- data ---------------------------------------------------------------

    def set_mode(self, mode: SimMode) -> None:
        """Switch direction and re-simulate (public for reuse by MainWindow)."""
        self._set_mode(mode)

    def _set_mode(self, mode: SimMode) -> None:
        if mode == self._mode:
            self._sync_mode_buttons()
            return
        self._mode = mode
        self._sync_mode_buttons()
        self.refresh()

    def _sync_mode_buttons(self) -> None:
        self._btn_install.setChecked(self._mode == SimMode.INSTALL)
        self._btn_deinstall.setChecked(self._mode == SimMode.UNINSTALL)

    def _update_title(self) -> None:
        mode_name = "Installation" if self._mode == SimMode.INSTALL else "Deinstallation"
        self.setWindowTitle(f"Simulator {mode_name} – EMP-PackageX3")

    def refresh(self) -> None:
        """Re-run the simulation and rebuild the tree."""
        self._report = simulate(self._document, self._mode)
        self._update_title()
        entry = self._report.entry_section or "–"
        self._entry_label.setText(f"Einstiegssektion: {entry}")
        n_gaps = len(self._report.gaps)
        self._stats_label.setText(f"{len(self._report.actions)} Aktionen · {n_gaps} Lücken")
        self._gap_banner.setVisible(n_gaps > 0)
        if n_gaps:
            first = html.escape(self._report.gaps[0])
            more = f" (+{n_gaps - 1} weitere, siehe Baum)" if n_gaps > 1 else ""
            self._gap_banner.setText(f"⚠ {n_gaps} Lücke(n) gefunden: {first}{more}")
        self._rebuild()

    def _rebuild(self) -> None:
        report = self._report
        self._tree.clear()

        def make_group(title: str, *, color_key: str | None = None) -> QTreeWidgetItem:
            """Full-width group row (text cannot be squeezed into a column)."""
            item = QTreeWidgetItem([title, "", "", ""])
            item.setFirstColumnSpanned(True)
            if color_key:
                item.setForeground(0, self._palette_brush(color_key))
            self._tree.addTopLevelItem(item)
            item.setExpanded(True)
            return item

        if report.gaps:
            gaps_item = make_group(
                f"⚠ Lücken ({len(report.gaps)})", color_key="warning_text"
            )
            for gap in report.gaps:
                child = QTreeWidgetItem(["", "Lücke", gap, ""])
                child.setForeground(2, self._palette_brush("warning_text"))
                gaps_item.addChild(child)

        current_section: QTreeWidgetItem | None = None
        current_name: str | None = None
        for number, action in enumerate(report.actions, start=1):
            if action.section != current_name:
                current_name = action.section
                current_section = make_group(f"[{action.section}]", color_key="brand")
            note = command_note(f"{action.command} {action.detail}")
            line_text = f"Z{action.line}" if action.line else "–"
            child = QTreeWidgetItem(
                [str(number), action.command, action.detail, line_text]
            )
            child.setToolTip(1, note)
            child.setToolTip(2, note)
            child.setData(0, _ROLE_LINE, action.line)
            if action.line > 0:
                child.setToolTip(3, "Doppelklick: zur Zeile im Editor springen")
            assert current_section is not None
            current_section.addChild(child)

        state = report.final_state
        if state.files:
            files_item = make_group(f"Endzustand – Dateien ({len(state.files)})")
            for entry in sorted(state.files):
                files_item.addChild(QTreeWidgetItem(["", "Datei", entry, ""]))
        if state.reg_keys:
            reg_item = make_group(f"Endzustand – Registry ({len(state.reg_keys)})")
            for entry in sorted(state.reg_keys):
                reg_item.addChild(QTreeWidgetItem(["", "Registry", entry, ""]))
        if state.variables:
            vars_item = make_group(f"Endzustand – Variablen ({len(state.variables)})")
            for k, v in sorted(state.variables.items()):
                vars_item.addChild(QTreeWidgetItem(["", f"%{k}%", v, ""]))
        if state.terminated_processes:
            proc_item = make_group(
                f"Endzustand – Beendete Prozesse ({len(state.terminated_processes)})"
            )
            for proc in sorted(state.terminated_processes):
                proc_item.addChild(QTreeWidgetItem(["", "Prozess", proc, ""]))
        if state.reboot_requested:
            reboot_item = make_group("Endzustand – Neustart", color_key="warning_text")
            reboot_item.addChild(
                QTreeWidgetItem(["", "Reboot", "System-Neustart angefordert (SetReboot)", ""])
            )
        self._apply_filter()

    # -- interaction ----------------------------------------------------------

    def _on_item_activated(self, item: QTreeWidgetItem, _column: int) -> None:
        line = item.data(0, _ROLE_LINE)
        if isinstance(line, int) and line > 0:
            self._on_jump(line)

    def _apply_filter(self) -> None:
        term = self._filter.text().strip().casefold()
        for index in range(self._tree.topLevelItemCount()):
            group = self._tree.topLevelItem(index)
            if group is None:
                continue
            visible_children = 0
            for child_index in range(group.childCount()):
                child = group.child(child_index)
                if child is None:
                    continue
                haystack = " ".join(
                    child.text(col) for col in range(1, 4)
                ).casefold()
                match = term in haystack or term in group.text(0).casefold()
                child.setHidden(bool(term) and not match)
                if not child.isHidden():
                    visible_children += 1
            group.setHidden(bool(term) and visible_children == 0)

    def _export(self) -> None:
        text = format_simulator_report(self._report)
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Simulator-Report exportieren",
            "emp_packagex3_simulator.txt",
            "Text (*.txt)",
        )
        if not path_str:
            return
        try:
            Path(path_str).write_text(text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Simulator", f"Export fehlgeschlagen:\n{exc}")
            return
        self._stats_label.setText(
            self._stats_label.text() + f" · exportiert: {Path(path_str).name}"
        )

    # -- styling --------------------------------------------------------------

    def _palette_brush(self, key: str) -> QColor:
        from emp_packagex3.ui.theme import dialog_colors

        return QColor(dialog_colors(self._theme_name)[key])

    def _dialog_qss(self) -> str:
        from emp_packagex3.ui.theme import dialog_colors

        c = dialog_colors(self._theme_name)
        return f"""
            QDialog {{
                background: {c["bg"]};
                color: {c["text"]};
            }}
            QLabel {{
                color: {c["text"]};
            }}
            QLineEdit {{
                min-height: 26px;
                background: {c["input_bg"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
            }}
            QTreeWidget {{
                background: {c["input_bg"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: 4px;
            }}
            QLabel#gapBanner {{
                background: {c["warning_bg"]};
                color: {c["warning_text"]};
                border: 1px solid {c["warning_text"]};
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: 600;
            }}
            QPushButton {{
                background: {c["panel_bg"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                padding: 5px 12px;
            }}
            QPushButton:checked {{
                background: {c["primary"]};
                color: #ffffff;
                font-weight: 600;
            }}
        """


def format_simulator_report(
    report: SimReport,
    *,
    package: str = "",
    app_version: str = "",
) -> str:
    """Plain-text report for the export button (pure, testable without Qt)."""
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    mode_name = "Installation" if report.mode == SimMode.INSTALL else "Deinstallation"
    lines = [
        "EMP-PackageX3 Simulator-Report",
        f"Erstellt (UTC): {stamp}",
        f"App-Version: {app_version}" if app_version else "App-Version: –",
        f"Paket: {package}" if package else "Paket: –",
        f"Modus: {mode_name} · Einstiegssektion: {report.entry_section or '–'}",
        f"Aktionen: {len(report.actions)} · Lücken: {len(report.gaps)}",
        "---",
    ]
    current_section: str | None = None
    for number, action in enumerate(report.actions, start=1):
        if action.section != current_section:
            current_section = action.section
            lines.append(f"[{action.section}]")
        detail = f" {action.detail}" if action.detail else ""
        lines.append(f"  {number}. Z{action.line or '?'}: {action.command}{detail}")
    if report.gaps:
        lines.append("--- Lücken ---")
        lines.extend(f"  ! {gap}" for gap in report.gaps)
    if report.final_state.files:
        lines.append("--- Endzustand: Dateien ---")
        lines.extend(f"  {entry}" for entry in sorted(report.final_state.files))
    if report.final_state.reg_keys:
        lines.append("--- Endzustand: Registry ---")
        lines.extend(f"  {entry}" for entry in sorted(report.final_state.reg_keys))
    if report.final_state.variables:
        lines.append("--- Endzustand: Variablen ---")
        lines.extend(f"  %{k}% = {v}" for k, v in sorted(report.final_state.variables.items()))
    if report.final_state.terminated_processes:
        lines.append("--- Endzustand: Beendete Prozesse ---")
        lines.extend(f"  {proc}" for proc in sorted(report.final_state.terminated_processes))
    if report.final_state.reboot_requested:
        lines.append("--- Endzustand: Neustart ---")
        lines.append("  System-Neustart angefordert (SetReboot)")
    return "\n".join(lines) + "\n"
