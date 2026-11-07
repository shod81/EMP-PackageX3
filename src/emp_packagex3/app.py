"""EMP-PackageX3 main window – full editor surface for plan completion."""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QFont,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QShowEvent,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3 import (
    APP_DISPLAY_NAME,
    APP_NAME,
    COPYRIGHT,
    ORG_NAME,
    TARGET_EMPIRUM_VERSION,
    __version__,
)
from emp_packagex3.learning_content import lookup_command, lookup_section, val_rule_range
from emp_packagex3.logging_setup import get_logger
from emp_packagex3.settings import (
    AppSettings,
    load_settings,
    resolve_manifest_location,
    save_settings,
)
from emp_packagex3.ui.completer import attach_completer, refresh_completer
from emp_packagex3.ui.highlighter import SetupInfHighlighter
from emp_packagex3.ui.panels import VisualPanels
from emp_packagex3.ui.tooltip_mode import (
    apply_tooltip_mode,
    bind_action,
    bind_main_window_tips,
    tip_text,
)
from empirum_core.ast.model import Document, RawLine, Section, append_section
from empirum_core.linter import Diagnostic, LintOptions, QuickFix, lint_document
from empirum_core.parser.lexer import lex_document, lex_text
from empirum_core.parser.work import recompute_spans
from empirum_core.prettify import prettify_document
from empirum_core.serializer.serialize import serialize_to_bytes
from empirum_core.simulator import SimMode
from empirum_services.editor.sync import SyncController

if TYPE_CHECKING:
    from emp_packagex3.ui.simulator_dialog import SimulatorDialog

log = get_logger("emp_packagex3.app")


def _template_manifest_path() -> Path | None:
    """VERSION.json template: bundled next to the EXE when frozen, else repo."""
    candidates: list[Path]
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates = [
            base / "packaging" / "VERSION.json",
            Path(sys.executable).parent / "packaging" / "VERSION.json",
        ]
    else:
        candidates = [Path(__file__).resolve().parents[2] / "packaging" / "VERSION.json"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def package_dir_for_file(path: Path) -> Path:
    """Package root for any file inside an Empirum package layout.

    Install\\Setup.inf → grandparent; other files → nearest ancestor that
    contains Install\\Setup.inf; fallback: parent directory.
    """
    if path.name.casefold() == "setup.inf" and path.parent.name.casefold() == "install":
        return path.parent.parent
    for candidate in (path, *path.parents):
        if (candidate / "Install" / "Setup.inf").is_file():
            return candidate
    return path.parent


def _is_local_path(path: Path) -> bool:
    """False for network paths (``\\\\server\\share\\...``) – SMB can block for seconds.

    R-3: a depot on an unreachable share must never stall window startup, so the
    local-depot sync is skipped for network paths. The drive part alone decides:
    ``PureWindowsPath`` reports ``\\\\server\\share`` (also for the ``//server/share``
    spelling and for ``\\\\?\\UNC\\...``), while drive letters, relative paths and
    POSIX-style values stay "local" – an extra ``startswith("//")`` test flagged
    nothing the drive check misses.
    """
    return not PureWindowsPath(str(path)).drive.startswith("\\\\")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_DISPLAY_NAME} {__version__}[*]")
        self.resize(1400, 860)
        self._path: Path | None = None
        self._sync = SyncController()
        self._diags: list[Diagnostic] = []
        self._updating_editor = False
        self._dirty = False
        self._sim_dialog: SimulatorDialog | None = None
        self._hover_state: str | None = None
        # M-5: last search term (F3 reuses it) + wrap-around flag for the status.
        self._last_search_term = ""
        self._find_wrapped = False
        self._settings: AppSettings = load_settings()
        self._theme = self._settings.theme
        # R-3: the depot sync runs after the first paint (showEvent), never
        # during construction – it may touch a slow or unreachable share.
        self._depot_initialized = False
        log.info("MainWindow start version=%s theme=%s", __version__, self._theme)

        self._editor = QPlainTextEdit()
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._editor.setMouseTracking(True)
        self._editor.viewport().installEventFilter(self)
        self._editor.installEventFilter(self)  # M-5: window-level Esc
        font = QFont("Cascadia Code", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._editor.setFont(font)
        self._completer = attach_completer(
            self._editor, undocumented=self._settings.undocumented_commands
        )
        self._highlighter = SetupInfHighlighter(self._editor.document())

        self._panels = VisualPanels()
        self._panels.document_changed.connect(self._on_visual_document)

        self._diag_list = QListWidget()
        # itemActivated covers double-click AND Enter – avoids double firing
        self._diag_list.itemActivated.connect(self._jump_diag)
        self._diag_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._diag_list.customContextMenuRequested.connect(self._show_diag_menu)

        brand = QLabel(APP_DISPLAY_NAME)
        brand.setStyleSheet("font-size: 18px; font-weight: 600; color: #1a3a4a;")
        subtitle = QLabel("PackageCreator · PackageEditor · Linter · Simulator")
        subtitle.setStyleSheet("color: #5a6a72;")
        self._brand = brand
        self._subtitle = subtitle

        header = QVBoxLayout()
        header.addWidget(brand)
        header.addWidget(subtitle)

        editors = QSplitter(Qt.Orientation.Horizontal)
        # Editor page: editor on top, hidden find bar below (Ctrl+F / F3).
        from emp_packagex3.ui.find_bar import FindBar

        self._find_bar = FindBar(tooltip_mode=self._settings.tooltip_mode)
        self._find_bar.search_requested.connect(self._on_search_requested)
        self._find_bar.closed.connect(self._editor.setFocus)
        self._find_bar.setVisible(False)
        editor_page = QWidget()
        editor_lay = QVBoxLayout(editor_page)
        editor_lay.setContentsMargins(0, 0, 0, 0)
        editor_lay.setSpacing(2)
        editor_lay.addWidget(self._editor, stretch=1)
        editor_lay.addWidget(self._find_bar)
        editors.addWidget(editor_page)
        editors.addWidget(self._panels)
        editors.setSizes([780, 520])

        body = QSplitter(Qt.Orientation.Vertical)
        body.addWidget(editors)
        body.addWidget(self._diag_list)
        body.setSizes([640, 180])

        root = QVBoxLayout()
        root.addLayout(header)
        root.addWidget(body, stretch=1)
        wrap = QWidget()
        wrap.setLayout(root)
        self.setCentralWidget(wrap)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(COPYRIGHT)

        self._lint_timer = QTimer(self)
        self._lint_timer.setSingleShot(True)
        self._lint_timer.setInterval(self._sync.debounce_ms)
        self._lint_timer.timeout.connect(self._on_debounce)
        self._editor.textChanged.connect(self._schedule_sync)

        bind_main_window_tips(
            brand=self._brand,
            subtitle=self._subtitle,
            editor=self._editor,
            panels=self._panels,
            diag_list=self._diag_list,
            status=self.statusBar(),
        )
        self._build_menu()
        self._apply_theme()
        self._apply_state_to_ui()
        self._apply_tooltip_mode()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&Datei")
        new_act = QAction("&Neu", self)
        new_act.setShortcut(QKeySequence("Ctrl+N"))
        new_act.triggered.connect(self.new_file)
        bind_action(new_act, "file.new")
        file_menu.addAction(new_act)
        for text, slot, shortcut, tip_key in (
            ("&Öffnen…", self.open_file, "Ctrl+O", "file.open"),
            ("&Speichern", self.save_file, "Ctrl+S", "file.save"),
            ("Speichern unter…", self.save_file_as, None, "file.save_as"),
        ):
            act = QAction(text, self)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            act.triggered.connect(slot)
            bind_action(act, tip_key)
            file_menu.addAction(act)
        file_menu.addSeparator()
        settings_act = QAction("&Einstellungen…", self)
        settings_act.triggered.connect(self.open_settings)
        bind_action(settings_act, "file.settings")
        file_menu.addAction(settings_act)
        update_act = QAction("&Auf Update prüfen…", self)
        update_act.triggered.connect(self.check_for_updates)
        bind_action(update_act, "file.update")
        file_menu.addAction(update_act)
        logs_act = QAction("&Log-Ordner öffnen", self)
        logs_act.triggered.connect(self.open_log_folder)
        bind_action(logs_act, "file.logs")
        file_menu.addAction(logs_act)
        file_menu.addSeparator()
        rt = QAction("Roundtrip &prüfen", self)
        rt.triggered.connect(self.check_roundtrip)
        bind_action(rt, "file.roundtrip")
        file_menu.addAction(rt)

        edit_menu = self.menuBar().addMenu("&Bearbeiten")
        edit_entries: list[
            tuple[str | None, Callable[[], None] | None, str | None, str | None]
        ] = [
            ("&Rückgängig", self._editor.undo, "Ctrl+Z", "edit.undo"),
            ("&Wiederherstellen", self._editor.redo, "Ctrl+Y", "edit.redo"),
            (None, None, None, None),
            ("Auss&chneiden", self._editor.cut, "Ctrl+X", "edit.cut"),
            ("&Kopieren", self._editor.copy, "Ctrl+C", "edit.copy"),
            ("&Einfügen", self._editor.paste, "Ctrl+V", "edit.paste"),
            (None, None, None, None),
            ("Alles &markieren", self._editor.selectAll, "Ctrl+A", "edit.select_all"),
            (None, None, None, None),
            ("&Formatieren", self.run_prettify, "Ctrl+Shift+F", "edit.prettify"),
            (None, None, None, None),
            ("&Suchen…", self.open_find, "Ctrl+F", "edit.find"),
            ("Weiter&suchen", self._find_next_action, "F3", "edit.find_next"),
            ("Suche &rückwärts", self._find_prev_action, "Shift+F3", "edit.find_prev"),
        ]
        for label, handler, shortcut, edit_tip_key in edit_entries:
            if label is None:
                edit_menu.addSeparator()
                continue
            act = QAction(label, self)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            assert handler is not None and edit_tip_key is not None
            act.triggered.connect(handler)
            bind_action(act, edit_tip_key)
            edit_menu.addAction(act)
        edit_menu.aboutToShow.connect(lambda m=edit_menu: self._widen_menu_for_shortcuts(m))

        tools = self.menuBar().addMenu("&Werkzeuge")
        for text, slot, shortcut, tip_key, sep_after in (
            (f"&Lint ({val_rule_range()})", self.run_lint, "F7", "tools.lint", False),
            (
                "Quick&Fix erste Diagnose",
                self.apply_first_quickfix,
                "Ctrl+.",
                "tools.quickfix",
                False,
            ),
            (
                "&Fehlende Standardsektionen ergänzen",
                self.run_skeleton_repair,
                None,
                "tools.skeleton_repair",
                True,
            ),
            ("Package&Creator…", self.open_wizard, None, "tools.wizard", False),
            (
                "Simulator &Installation",
                lambda: self.run_simulator(SimMode.INSTALL),
                None,
                "tools.sim_install",
                False,
            ),
            (
                "Simulator &Deinstallation",
                lambda: self.run_simulator(SimMode.UNINSTALL),
                None,
                "tools.sim_uninstall",
                True,
            ),
            ("Test-Runner (Dry-Run / VM)…", self.run_runner_dry, None, "tools.runner", False),
            (
                "Nach Empirum &PackageStore deployen…",
                self.open_package_store_deploy,
                None,
                "tools.packagestore",
                True,
            ),
            ("Fehler-/&Reboot-Maske…", self.open_error_reboot, None, "tools.error_reboot", False),
            (
                "Snippet: ErrorLevel-Block",
                self.insert_errorlevel_snippet,
                None,
                "tools.snippet",
                False,
            ),
            (
                "Snippet: Reg.exe Delete (Install)…",
                self.insert_reg_delete_snippet,
                None,
                "tools.snippet_reg",
                False,
            ),
            (
                "Snippet: Dynamischer MSI-Reinstall…",
                self.insert_msi_reinstall_snippet,
                None,
                "tools.snippet_msi_reinstall",
                True,
            ),
            ("Theme Dark/Light umschalten", self.toggle_theme, None, "tools.theme", False),
            ("Diagnosen exportieren…", self.export_diagnostics, None, "tools.export_diag", False),
            ("Diff zu Datei auf Disk…", self.diff_against_disk, None, "tools.diff", False),
        ):
            act = QAction(text, self)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            act.triggered.connect(slot)
            bind_action(act, tip_key)
            tools.addAction(act)
            if sep_after:
                tools.addSeparator()
        tools.aboutToShow.connect(lambda m=tools: self._widen_menu_for_shortcuts(m))

        help_menu = self.menuBar().addMenu("&Hilfe")
        learning = QAction("Setup.inf-&Schnellkurs…", self)
        learning.triggered.connect(self.open_learning_center)
        bind_action(learning, "help.learning")
        help_menu.addAction(learning)
        cmd_ref = QAction("Setup.inf-&Befehlsreferenz…", self)
        cmd_ref.triggered.connect(self.open_command_reference)
        bind_action(cmd_ref, "help.command_reference")
        help_menu.addAction(cmd_ref)
        self._tooltip_mode_act = QAction("&Tooltip-Modus", self)
        self._tooltip_mode_act.setCheckable(True)
        self._tooltip_mode_act.setChecked(self._settings.tooltip_mode)
        self._tooltip_mode_act.setShortcut(QKeySequence("F1"))
        self._tooltip_mode_act.toggled.connect(self._on_tooltip_mode_toggled)
        bind_action(self._tooltip_mode_act, "help.tooltip_mode")
        help_menu.addAction(self._tooltip_mode_act)
        feedback = QAction("&Feedback-Paket (Logs)…", self)
        feedback.triggered.connect(self.create_feedback_package)
        bind_action(feedback, "help.feedback")
        help_menu.addAction(feedback)
        about = QAction("&Über…", self)
        about.triggered.connect(self.show_about)
        bind_action(about, "help.about")
        help_menu.addAction(about)

    def _apply_tooltip_mode(self) -> None:
        enabled = self._settings.tooltip_mode
        apply_tooltip_mode(self, enabled)
        if enabled:
            self.statusBar().showMessage(
                "Tooltip-Modus aktiv – mit der Maus über Menüs und Felder fahren · "
                f"{COPYRIGHT}"
            )

    def _on_tooltip_mode_toggled(self, checked: bool) -> None:
        self._settings.tooltip_mode = checked
        save_settings(self._settings)
        self._apply_tooltip_mode()
        log.info("tooltip_mode=%s", checked)

    @staticmethod
    def _widen_menu_for_shortcuts(menu: QMenu) -> None:
        """Ensure label and native shortcut columns do not overlap (Windows Qt)."""
        fm = menu.fontMetrics()
        max_text = 0
        max_sc = 0
        for act in menu.actions():
            if act.isSeparator():
                continue
            label = act.text().replace("&", "")
            max_text = max(max_text, fm.horizontalAdvance(label))
            sc = act.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
            if sc:
                max_sc = max(max_sc, fm.horizontalAdvance(sc))
        # left margin + text + gap + shortcut + right margin
        menu.setMinimumWidth(max_text + max_sc + fm.horizontalAdvance("        ") + 40)

    def _schedule_sync(self) -> None:
        if self._updating_editor:
            return
        self._lint_timer.start()

    def _on_debounce(self) -> None:
        text = self._editor.toPlainText()
        before = self._sync.text
        state = self._sync.apply_code_edit(text)
        if state is None:
            return
        if state.text != before:
            # F-3: only a real change is a change – a flush without an edit
            # (F7, save, a repeated quick fix) must not fake unsaved changes.
            self._set_dirty(True)
        self._panels.set_document(self._sync.document)
        self._refresh_diagnostics()

    def _on_visual_document(self, document: Document) -> None:
        state = self._sync.apply_visual_patch(document)
        if state is None:
            return
        self._set_dirty(True)
        self._updating_editor = True
        self._editor.setPlainText(state.text.replace("\r\n", "\n"))
        self._updating_editor = False
        self._panels.set_document(self._sync.document)
        self._refresh_diagnostics()

    def _apply_state_to_ui(self) -> None:
        self._updating_editor = True
        self._editor.setPlainText(self._sync.text.replace("\r\n", "\n"))
        self._updating_editor = False
        self._panels.set_document(self._sync.document)
        self._refresh_diagnostics()

    def _set_dirty(self, value: bool) -> None:
        """Track unsaved changes and surface them in the window title (``*``)."""
        self._dirty = value
        self.setWindowModified(value)

    def _refresh_diagnostics(self) -> None:
        self._diags = lint_document(
            self._sync.document,
            options=LintOptions(
                undocumented_commands=self._settings.undocumented_commands
            ),
        )
        palette = self._ui_palette()
        self._diag_list.clear()
        for d in self._diags:
            item = QListWidgetItem(
                f"Z{d.line or '?'}  [{d.severity.value}] {d.code} — {d.message}"
            )
            item.setData(Qt.ItemDataRole.UserRole, d)
            if d.severity.value == "error":
                item.setForeground(QColor(palette["error"]))
            elif d.severity.value == "warning":
                item.setForeground(QColor(palette["warning"]))
            self._diag_list.addItem(item)
        self.statusBar().showMessage(
            f"{len(self._diags)} Diagnose(n) · Sync v{self._sync.version} · {COPYRIGHT}"
        )

    # -- editor search (Ctrl+F / F3 / Shift+F3) -------------------------------

    def open_find(self) -> None:
        """Show the find bar, prefilling the editor selection if any."""
        cursor = self._editor.textCursor()
        term = cursor.selectedText() if cursor.hasSelection() else ""
        self._find_bar.open_with(term.replace("\u2029", " ") if term else "")

    def _find_next_action(self) -> None:
        self._find_step(backward=False)

    def _find_prev_action(self) -> None:
        self._find_step(backward=True)

    def _find_step(self, *, backward: bool) -> None:
        """F3 / Shift+F3: continue with the bar's term, else reuse the last one.

        M-5: a closed bar is no longer a reason to pop up an empty search – the
        previous term is reused silently. The reuse path also reports its result
        in the status bar, so F3 is not just an unexplained cursor jump.
        """
        if self._find_bar.is_open() and self._find_bar.term().strip():
            self._find_bar.search(backward=backward)
            return
        if not self._find_bar.is_open() and self._last_search_term:
            term = self._last_search_term
            status = self._search_status(term, self._find_bar.case_sensitive(), backward)
            message = f"Suche „{term}“: {status}" if status else f"Suche „{term}“"
            self.statusBar().showMessage(message, 4000)
            return
        self.open_find()

    def _on_search_requested(self, term: str, case_sensitive: bool, backward: bool) -> None:
        self._find_bar.set_status(self._search_status(term, case_sensitive, backward))

    def _search_status(self, term: str, case_sensitive: bool, backward: bool) -> str:
        """Run the search once and build the status text for it.

        Shared by the bar label and the F3-reuse path so both report the same
        count / "nicht gefunden" / wrap hint for one and the same search.
        """
        if not term.strip():
            self._last_search_term = ""
            return ""
        found = self._find(term, case_sensitive, backward)
        self._last_search_term = term
        count = self._count_matches(term, case_sensitive)
        if not count:
            return "nicht gefunden"
        # M-5: exactly one status update; the wrap hint replaces the previous
        # double set_status() (which stomped the count on a failed hit).
        suffix = " · umgebrochen" if found and self._find_wrapped else ""
        return f"{count} Treffer{suffix}"

    def _find(self, term: str, case_sensitive: bool, backward: bool) -> bool:
        """Find the next/previous occurrence with wrap-around; select it."""
        document = self._editor.document()
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        cursor = self._editor.textCursor()
        if not backward and cursor.hasSelection():
            cursor.setPosition(cursor.selectionEnd())
        found = document.find(term, cursor, flags)
        self._find_wrapped = False
        if found.isNull():  # wrap around
            wrap = QTextCursor(document)
            if backward:
                wrap.movePosition(QTextCursor.MoveOperation.End)
            found = document.find(term, wrap, flags)
            self._find_wrapped = not found.isNull()
        if found.isNull():
            return False
        self._editor.setTextCursor(found)
        return True

    def _count_matches(self, term: str, case_sensitive: bool) -> int:
        document = self._editor.document()
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        cursor = QTextCursor(document)
        count = 0
        while True:
            found = document.find(term, cursor, flags)
            if found.isNull():
                break
            count += 1
            cursor = found
            if count > 100_000:  # paranoia guard for huge documents
                break
        return count

    def _jump_diag(self, item: QListWidgetItem) -> None:
        d: Diagnostic | None = item.data(Qt.ItemDataRole.UserRole)
        if not d or not d.line:
            return
        self._jump_to_line(d.line)

    def _jump_to_line(self, line: int) -> None:
        """Scroll to and highlight a 1-based editor line (diagnostics, simulator)."""
        block = self._editor.document().findBlockByLineNumber(line - 1)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(self._ui_palette()["highlight"]))
        selection.cursor = QTextCursor(block)
        selection.cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        # setExtraSelections replaces the previous highlight (no accumulation)
        self._editor.setExtraSelections([selection])

    def new_file(self) -> None:
        if not self._confirm_maybe_save():
            return
        empty = lex_text("[SetupInfo]\r\nProductName=\r\n")
        self._sync.apply_visual_patch(empty)
        self._path = None
        self._set_dirty(False)
        self._apply_state_to_ui()
        self.statusBar().showMessage("Neues Dokument")

    def _flush_pending_edit(self) -> None:
        """Apply a debounced editor edit immediately (``_dirty`` lags behind it)."""
        if self._lint_timer.isActive():
            self._lint_timer.stop()
            self._on_debounce()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 – Qt API
        """R-3: defer the local-depot sync until after the first paint."""
        super().showEvent(event)
        if not self._depot_initialized:
            self._depot_initialized = True
            QTimer.singleShot(0, self._ensure_local_depot)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 – Qt API
        """M-5: Esc closes the find bar from anywhere in the window."""
        if event.key() == Qt.Key.Key_Escape and self._find_bar.is_open():
            self._find_bar.dismiss()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 – Qt API
        self._flush_pending_edit()  # a keystroke < debounce_ms ago is not in _dirty yet
        if self._dirty and not self._confirm_maybe_save():
            event.ignore()
            return
        event.accept()

    def _confirm_maybe_save(self) -> bool:
        """Ask about unsaved changes; True when the window may close/proceed."""
        self._flush_pending_edit()
        if not self._dirty:
            return True
        ret = QMessageBox.question(
            self,
            APP_NAME,
            "Ungespeicherte Änderungen vorhanden. Vor dem Schließen speichern?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if ret == QMessageBox.StandardButton.Save:
            self.save_file()
            return not self._dirty  # save may have been cancelled/failed
        return ret == QMessageBox.StandardButton.Discard

    def open_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Setup.inf öffnen",
            "",
            "Empirum Setup (Setup.inf);;INF (*.inf);;Alle (*.*)",
        )
        if not path_str:
            return
        self._load_path(Path(path_str))

    def load_file_at_startup(self, path: Path) -> None:
        """Open a document passed via CLI / Explorer file association."""
        if not path.is_file():
            log.warning("startup file not found: %s", path)
            QMessageBox.warning(self, APP_NAME, f"Datei nicht gefunden:\n{path}")
            return
        self._load_path(path)

    def _load_path(self, path: Path) -> None:
        """Load a Setup.inf from disk (dialog, CLI, wizard)."""
        log.info("open_file %s", path)
        try:
            self._sync.load_bytes(path.read_bytes())
        except Exception as exc:
            log.exception("open_file failed")
            QMessageBox.critical(self, APP_NAME, f"Öffnen fehlgeschlagen:\n{exc}")
            return
        self._path = path
        self._set_dirty(False)
        self._apply_state_to_ui()
        if self._sync.encoding_ambiguous:
            from emp_packagex3.ui.encoding_dialog import EncodingChoiceDialog
            from empirum_core.parser.encoding import DetectedEncoding

            dlg = EncodingChoiceDialog(
                DetectedEncoding(
                    name=self._sync.document.encoding_name,
                    has_bom=self._sync.document.has_bom,
                    ambiguous=True,
                ),
                self,
            )
            if dlg.exec():
                chosen = dlg.chosen()
                self._sync.set_encoding(chosen.name, has_bom=chosen.has_bom)
                self._editor.setReadOnly(False)
                # The chosen encoding is what the next write will use: without
                # the dirty flag a plain "close" would silently drop the choice
                # and save with the detected encoding again.
                self._set_dirty(True)
                self.statusBar().showMessage(
                    f"Encoding festgelegt: {chosen.name} – bitte speichern", 5000
                )
            else:
                self._editor.setReadOnly(True)
                self.statusBar().showMessage(
                    "Schreibgeschützt – Encoding unklar (R-02)"
                )
        else:
            self._editor.setReadOnly(False)

    def save_file(self) -> None:
        if self._sync.read_only:
            QMessageBox.warning(
                self, APP_NAME, "Speichern gesperrt: bitte zuerst Encoding wählen."
            )
            return
        if self._path is None:
            self.save_file_as()
            return
        self._persist(self._path)

    def save_file_as(self) -> None:
        if self._sync.read_only:
            QMessageBox.warning(
                self, APP_NAME, "Speichern gesperrt: bitte zuerst Encoding wählen."
            )
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Setup.inf speichern",
            str(self._path) if self._path else "Setup.inf",
            "INF (*.inf);;Alle (*.*)",
        )
        if not path_str:
            return
        self._path = Path(path_str)
        self._persist(self._path)

    def _persist(self, path: Path) -> None:
        from empirum_infra.fs_safe import write_bytes_with_backup

        self._on_debounce()
        try:
            data = serialize_to_bytes(self._sync.document)
            result = write_bytes_with_backup(path, data)
        except Exception as exc:
            log.exception("save failed path=%s", path)
            QMessageBox.critical(self, APP_NAME, f"Speichern fehlgeschlagen:\n{exc}")
            return
        self._set_dirty(False)
        bak = f" · Backup {result.backup_path.name}" if result.backup_path else ""
        log.info("saved %s bytes=%s backup=%s", path, result.bytes_written, result.backup_path)
        self.statusBar().showMessage(f"Gespeichert: {path}{bak}")

    def check_roundtrip(self) -> None:
        if self._path is None:
            QMessageBox.information(self, APP_NAME, "Bitte zuerst eine Datei öffnen.")
            return
        try:
            original = self._path.read_bytes()
            again = serialize_to_bytes(lex_document(original).document)
        except Exception as exc:
            log.exception("roundtrip check failed")
            QMessageBox.critical(self, APP_NAME, f"Roundtrip-Prüfung fehlgeschlagen:\n{exc}")
            return
        ok = again == original
        QMessageBox.information(
            self,
            APP_NAME,
            "Roundtrip byte-identisch." if ok else f"Abweichung ({len(original)}→{len(again)}).",
        )

    def run_prettify(self) -> None:
        self._on_debounce()
        before = self._sync.text
        pretty = prettify_document(self._sync.document)
        self._sync.apply_visual_patch(pretty)
        if self._sync.text != before:
            # F-3: _on_debounce no longer sets the flag blindly – a prettify run
            # that really rewrites the document has to raise it itself.
            self._set_dirty(True)
        self._apply_state_to_ui()
        self.statusBar().showMessage("Prettifier angewendet")

    def run_lint(self) -> None:
        self._on_debounce()
        msg = "Keine Befunde." if not self._diags else f"{len(self._diags)} Befund(e) in der Liste."
        QMessageBox.information(self, APP_NAME, msg)

    def apply_first_quickfix(self) -> None:
        self._on_debounce()
        for d in self._diags:
            for fix in d.quick_fixes:
                if fix.note in {"strip_bom_and_set_cp1252", "set_cp1252"}:
                    self._sync.set_encoding("cp1252", has_bom=False)
                    self._set_dirty(True)
                    self._apply_state_to_ui()
                    self.statusBar().showMessage(f"QuickFix: {fix.title}")
                    return
                if not fix.replacement_line:
                    continue
                if fix.note == "insert_section":
                    # Structural fix (VAL-012): carries no line – the section is
                    # appended at document end.
                    if self._apply_section_fix(fix):
                        self.statusBar().showMessage(f"QuickFix: {fix.title}")
                        return
                    continue
                if not d.line:
                    continue
                if fix.note in {
                    "insert_after",
                    "delete_line",
                    "set_application_key",
                }:
                    continue
                if "\n" in fix.replacement_line or "\r" in fix.replacement_line:
                    continue
                block = self._editor.document().findBlockByLineNumber(d.line - 1)
                if not block.isValid():
                    continue
                cursor = QTextCursor(block)
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                cursor.insertText(fix.replacement_line)
                self._on_debounce()
                self.statusBar().showMessage(f"QuickFix: {fix.title}")
                return
        QMessageBox.information(self, APP_NAME, "Kein anwendbarer QuickFix.")

    def _apply_section_fix(self, fix: QuickFix) -> bool:
        """Apply a ``note="insert_section"`` quick fix: append the section.

        The body comes from the fix's ``replacement_line`` (header stripped), so
        standard error handlers arrive with their canonical Abort block instead of as
        empty stubs. Returns False if the section already exists.
        """
        name = fix.section_name or ""
        if not name:
            return False
        document = self._sync.document
        if any(s.name.casefold() == name.casefold() for s in document.sections):
            self.statusBar().showMessage(f"[{name}] existiert bereits.")
            return False
        block = (fix.replacement_line or "").replace("\r\n", "\n")
        header = f"[{name}]"
        body = [line for line in block.split("\n") if line.strip() and line.strip() != header]
        section = Section(name=name, header_raw=name, lines=[RawLine(text=line) for line in body])
        append_section(document, section)
        recompute_spans(document)
        self._sync.apply_visual_patch(document)
        self._set_dirty(True)  # F-2: an applied fix is an unsaved change
        self._apply_state_to_ui()
        return True

    def _apply_quickfix_for(self, d: Diagnostic) -> None:
        """Apply the first applicable quick fix of a diagnostic."""
        self._flush_pending_edit()  # F-1: a just-typed edit must not be lost
        for fix in d.quick_fixes:
            if fix.note in {"strip_bom_and_set_cp1252", "set_cp1252"}:
                self._sync.set_encoding("cp1252", has_bom=False)
                self._set_dirty(True)
                self._apply_state_to_ui()
                self.statusBar().showMessage(f"QuickFix: {fix.title}")
                return
            if fix.note == "insert_section" and fix.replacement_line:
                if self._apply_section_fix(fix):
                    self.statusBar().showMessage(f"QuickFix: {fix.title}")
                return

    _apply_insert_section_fix_for = _apply_quickfix_for

    def run_skeleton_repair(self) -> None:
        """Add missing standard sections to the current document (VAL-012)."""
        from empirum_core.skeleton_repair import add_missing_standard_sections

        self._on_debounce()
        bom_stripped = False
        if self._sync.document.has_bom:
            self._sync.set_encoding("cp1252", has_bom=False)
            bom_stripped = True
        repair = add_missing_standard_sections(self._sync.document)
        if not repair.added_sections and not repair.added_refs and not bom_stripped:
            QMessageBox.information(
                self,
                APP_NAME,
                "Setup.inf ist standardkonform – keine fehlenden Sektionen.",
            )
            return
        self._sync.apply_visual_patch(self._sync.document)
        self._set_dirty(True)  # F-3: the repair rewrote the document (guard above)
        self._apply_state_to_ui()
        sections = ", ".join(f"[{s}]" for s in repair.added_sections) or "–"
        refs = "\n".join(repair.added_refs) or "–"
        extra = (
            "\n\nUTF-8-BOM wurde entfernt und Encoding auf Windows-1252 gesetzt."
            if bom_stripped
            else ""
        )
        QMessageBox.information(
            self,
            "Standardskelett ergänzt",
            f"Ergänzte Sektionen:\n{sections}\n\n"
            f"Ergänzte #Aufrufe in [Product]:\n{refs}{extra}\n\n"
            "Fehler-Handler erhalten den kanonischen Abort-Block (ErrorLogMsg/Abort), "
            "alle übrigen Stubs bleiben leer – Struktur prüfen (F7) und speichern.",
        )
        log.info(
            "skeleton repair sections=%s refs=%s bom_stripped=%s",
            repair.added_sections,
            repair.added_refs,
            bom_stripped,
        )

    def open_wizard(self) -> None:
        from emp_packagex3.wizard.creator import CreatorWizard

        dlg = CreatorWizard(self, tooltip_mode=self._settings.tooltip_mode, theme=self._theme)
        if dlg.exec() and dlg.result_setup_inf():
            path = dlg.result_setup_inf()
            assert path is not None
            try:
                self._sync.load_bytes(path.read_bytes())
            except Exception as exc:
                log.exception("open_wizard load failed")
                QMessageBox.critical(self, APP_NAME, f"Paket öffnen fehlgeschlagen:\n{exc}")
                return
            self._path = path
            self._set_dirty(False)
            self._apply_state_to_ui()
            self.statusBar().showMessage(
                f"Paket erzeugt – bitte prüfen/testen. PackageStore später unter "
                f"Werkzeuge → Nach Empirum PackageStore deployen… ({path.parent.parent})"
            )

    def _current_package_dir(self) -> Path | None:
        if self._path is None:
            return None
        return package_dir_for_file(self._path)

    def open_package_store_deploy(self) -> None:
        from emp_packagex3.ui.package_store_dialog import PackageStoreDeployDialog

        pkg = self._current_package_dir()
        dlg = PackageStoreDeployDialog(
            package_dir=pkg,
            store_root=self._settings.package_store_path,
            empirum_server=self._settings.empirum_server,
            default_mode=self._settings.package_store_mode,
            tooltip_mode=self._settings.tooltip_mode,
            parent=self,
        )
        dlg.exec()
        log.info(
            "package store deploy dialog closed store=%s server=%s",
            self._settings.package_store_path,
            self._settings.empirum_server or "(env/%EmpirumServer%)",
        )

    def run_simulator(self, mode: SimMode = SimMode.INSTALL) -> None:
        """Open the non-modal simulator tool window (reuse if already open)."""
        from emp_packagex3.ui.simulator_dialog import SimulatorDialog

        self._on_debounce()
        if self._sim_dialog is not None and self._sim_dialog.isVisible():
            self._sim_dialog.set_mode(mode)
            self._sim_dialog.refresh()
            self._sim_dialog.raise_()
            self._sim_dialog.activateWindow()
            return
        self._sim_dialog = SimulatorDialog(
            self,
            document=self._sync.document,
            mode=mode,
            on_jump=self._jump_to_line,
            theme=self._theme,
            tooltip_mode=self._settings.tooltip_mode,
        )
        self._sim_dialog.show()
        self._sim_dialog.raise_()
        self._sim_dialog.activateWindow()

    def run_runner_dry(self) -> None:
        from empirum_services.runner import RunnerConfig, RunnerSafetyError, run_package

        if self._path is None:
            QMessageBox.information(self, APP_NAME, "Bitte Paket/Setup.inf öffnen.")
            return
        package_dir = package_dir_for_file(self._path)
        cfg = RunnerConfig(
            allowed_roots=tuple(Path(p) for p in self._settings.runner_roots),
            require_vm_marker=self._settings.require_vm_marker,
            # No explicit setup_exe -> resolved default (%CommonFilesDir%\Setup64\Setup.exe)
        )
        try:
            result = run_package(package_dir, config=cfg, dry_run=True)
        except RunnerSafetyError as exc:
            QMessageBox.warning(
                self,
                APP_NAME,
                f"Runner blockiert (Sicherheit):\n{exc}\n\n"
                "Whitelist unter Einstellungen anpassen oder "
                ".emp_packagex3_vm anlegen.",
            )
            return
        except FileNotFoundError as exc:
            QMessageBox.warning(self, APP_NAME, f"Setup.inf/Struktur fehlt:\n{exc}")
            return
        QMessageBox.information(
            self,
            "Test-Runner Dry-Run",
            "Befehl (nicht ausgeführt):\n" + " ".join(result.command),
        )

    def open_error_reboot(self) -> None:
        from emp_packagex3.ui.error_reboot import ErrorRebootDialog

        self._on_debounce()
        dlg = ErrorRebootDialog(
            self._sync.document,
            self,
            tooltip_mode=self._settings.tooltip_mode,
        )
        if dlg.exec():
            doc = dlg.apply()
            self._sync.apply_visual_patch(doc)
            self._apply_state_to_ui()

    def insert_errorlevel_snippet(self) -> None:
        from empirum_core.snippets import get_snippet

        cursor = self._editor.textCursor()
        cursor.insertText(get_snippet("errorlevel-block").replace("\r\n", "\n"))

    def insert_reg_delete_snippet(self) -> None:
        from empirum_core.snippets import get_snippet

        cursor = self._editor.textCursor()
        cursor.insertText(get_snippet("reg-delete-install").replace("\r\n", "\n"))
        self.statusBar().showMessage(
            "Hinweis: '-' in [Reg:…] löscht erst bei Deinstallation – reg.exe für Install-Zeit"
        )
        self._on_debounce()

    def insert_msi_reinstall_snippet(self) -> None:
        from empirum_core.snippets import get_snippet

        cursor = self._editor.textCursor()
        cursor.insertText(get_snippet("msi-dynamic-reinstall").replace("\r\n", "\n"))
        self.statusBar().showMessage(
            "Snippet eingefügt: Dynamische MSI-GUID-Erkennung "
            "(GetUninstallKeyName / DoesRegKeyExist)"
        )
        self._on_debounce()

    def _apply_theme(self) -> None:
        from emp_packagex3.ui.theme import theme_qss

        self.setStyleSheet(theme_qss(self._theme))
        if self._theme == "dark":
            self._brand.setStyleSheet("font-size: 18px; font-weight: 600; color: #9fd4e8;")
            self._subtitle.setStyleSheet("color: #a8b6bd;")
        else:
            self._brand.setStyleSheet("font-size: 18px; font-weight: 600; color: #1a3a4a;")
            self._subtitle.setStyleSheet("color: #5a6a72;")

    def _ui_palette(self) -> dict[str, str]:
        if self._theme == "dark":
            return {"error": "#ff9b9b", "warning": "#ffc76b", "highlight": "#4d4310"}
        return {"error": "#a32020", "warning": "#8a5a00", "highlight": "#fff3bf"}

    def toggle_theme(self) -> None:
        self._theme = "dark" if self._theme == "light" else "light"
        self._settings.theme = self._theme
        save_settings(self._settings)
        self._apply_theme()
        self.statusBar().showMessage(f"Theme: {self._theme}")

    def open_settings(self) -> None:
        from emp_packagex3.ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(self._settings, self)
        if dlg.exec():
            self._settings = dlg.result_settings(self._settings)
            save_settings(self._settings)
            self._theme = self._settings.theme
            self._apply_theme()
            self._ensure_local_depot()
            self._tooltip_mode_act.blockSignals(True)
            self._tooltip_mode_act.setChecked(self._settings.tooltip_mode)
            self._tooltip_mode_act.blockSignals(False)
            self._apply_tooltip_mode()
            refresh_completer(
                self._completer, undocumented=self._settings.undocumented_commands
            )
            self._refresh_diagnostics()
            log.info(
                "settings saved depot=%s debug=%s tooltip_mode=%s undocumented=%s",
                self._settings.depot_path,
                self._settings.debug_logging,
                self._settings.tooltip_mode,
                self._settings.undocumented_commands,
            )
            self.statusBar().showMessage(
                "Einstellungen gespeichert (Logging-Stufe ggf. nach Neustart aktiv)"
            )

    def _ensure_local_depot(self) -> None:
        from empirum_services.local_depot import ensure_local_depot

        depot = self._settings.depot_path.strip()
        if not depot or depot.lower().startswith(("http://", "https://")):
            return
        if not _is_local_path(Path(depot)):
            # R-3: never create/refresh the manifest on a share from the UI
            # thread – an unreachable server blocks for the SMB timeout.
            log.info("local depot skipped (network path): %s", depot)
            return
        try:
            manifest = ensure_local_depot(
                Path(depot),
                version=__version__,
                template_manifest=_template_manifest_path(),
            )
            log.debug("local depot ready manifest=%s", manifest)
        except (OSError, ValueError) as exc:
            log.warning("local depot init failed: %s", exc)

    def open_log_folder(self) -> None:
        import os

        from emp_packagex3.logging_setup import default_log_dir

        if self._settings.log_dir.strip():
            directory = Path(self._settings.log_dir)
        else:
            directory = default_log_dir()
        directory.mkdir(parents=True, exist_ok=True)
        os.startfile(directory)  # noqa: S606 – Windows explorer
        log.info("opened log folder %s", directory)

    def create_feedback_package(self) -> None:
        from emp_packagex3.feedback import create_feedback_zip
        from emp_packagex3.logging_setup import default_log_dir

        suggested = (
            Path.home()
            / "Documents"
            / f"EMP-PackageX3-Feedback-{__version__}.zip"
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Feedback-Paket speichern",
            str(suggested),
            "ZIP (*.zip)",
        )
        if not path:
            return
        note, ok = QInputDialog.getMultiLineText(
            self,
            "Hinweis für den Support",
            "Kurze Beschreibung des Problems (landet im ZIP als README):",
            "",
        )
        if not ok:
            return
        log_dir = (
            Path(self._settings.log_dir)
            if self._settings.log_dir.strip()
            else default_log_dir()
        )
        try:
            zip_path = create_feedback_zip(Path(path), log_dir=log_dir, extra_note=note)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, APP_NAME, f"Feedback-ZIP fehlgeschlagen:\n{exc}")
            return
        log.info("feedback zip=%s", zip_path)
        QMessageBox.information(
            self,
            "Feedback-Paket",
            f"ZIP erstellt:\n{zip_path}\n\n"
            "Enthält: Anwendungslogs (lokale Pfade, Rechner-/Servernamen) "
            "sowie Versions-/OS-Info.\n"
            "Bitte als GitHub-Issue anhaengen:\nhttps://github.com/shod81/EMP-PackageX3/issues",
        )

    def check_for_updates(self) -> None:
        from empirum_services.update_check import check_update, utc_now_iso

        self._ensure_local_depot()
        location = resolve_manifest_location(self._settings)
        log.info("update check location=%s", location)
        info = check_update(location, __version__)
        self._settings.last_update_check = utc_now_iso()
        save_settings(self._settings)
        if not location:
            QMessageBox.information(
                self,
                APP_NAME,
                "Kein Depot konfiguriert.\n"
                "Unter Einstellungen einen lokalen Ordner setzen\n"
                "(Standard: Dokumente\\EMP-PackageX3-Depot).",
            )
            return
        if info.update_available:
            QMessageBox.information(
                self,
                "Update verfügbar",
                f"Quelle: {info.source}\n"
                f"Aktuell: {info.current}\nNeu: {info.latest}\n\n"
                f"{info.notes}\n\n{info.download_url}",
            )
        else:
            QMessageBox.information(
                self,
                APP_NAME,
                info.notes
                or f"Keine neuere Version (aktuell {info.current}).\nQuelle: {info.source}",
            )

    def export_diagnostics(self) -> None:
        from empirum_services.diagnostics_export import (
            format_diagnostics_report,
            write_diagnostics_report,
        )

        self._on_debounce()
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Diagnosen exportieren",
            "emp_packagex3_diagnostics.txt",
            "Text (*.txt)",
        )
        if not path_str:
            return
        text = format_diagnostics_report(
            self._diags,
            package=str(self._path) if self._path else "",
            app_version=__version__,
        )
        try:
            write_diagnostics_report(Path(path_str), text)
        except OSError as exc:
            log.exception("diagnostics export failed")
            QMessageBox.critical(self, APP_NAME, f"Export fehlgeschlagen:\n{exc}")
            return
        self.statusBar().showMessage(f"Diagnosen exportiert: {path_str}")

    def diff_against_disk(self) -> None:
        from empirum_core.diffing import unified_inf_diff
        from empirum_core.serializer.serialize import serialize_document

        if self._path is None or not self._path.is_file():
            QMessageBox.information(self, APP_NAME, "Keine geöffnete Datei auf Disk.")
            return
        self._on_debounce()
        try:
            disk = self._path.read_bytes()
        except OSError as exc:
            QMessageBox.critical(self, APP_NAME, f"Lesen fehlgeschlagen:\n{exc}")
            return
        from empirum_core.parser.lexer import lex_document as _lex

        disk_text = serialize_document(_lex(disk).document)
        editor_text = serialize_document(self._sync.document)
        diff = unified_inf_diff(disk_text, editor_text, fromfile="disk", tofile="editor")
        if not diff.strip():
            QMessageBox.information(self, APP_NAME, "Keine Unterschiede.")
            return
        QMessageBox.information(self, "Diff disk ↔ Editor", diff[:4000])

    def open_learning_center(self) -> None:
        from emp_packagex3.ui.learning_center import LearningCenterDialog

        dlg = LearningCenterDialog(self, tooltip_mode=self._settings.tooltip_mode)
        dlg.exec()
        log.info("learning center opened")

    def open_command_reference(self) -> None:
        from emp_packagex3.ui.command_reference import CommandReferenceDialog

        dlg = CommandReferenceDialog(
            self,
            tooltip_mode=self._settings.tooltip_mode,
            undocumented=self._settings.undocumented_commands,
        )
        dlg.exec()
        log.info(
            "command reference opened (undocumented=%s)",
            self._settings.undocumented_commands,
        )

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802 – Qt API
        """Editor hover help (tooltip mode) + Esc closes the find bar (M-5)."""
        if (
            isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Escape
            and self._find_bar.is_open()
        ):
            # Editor keeps focus while searching: catch Esc before Qt's
            # parent-propagation (which the editor does not do for Esc).
            self._find_bar.dismiss()
            return True
        if (
            obj is self._editor.viewport()
            and isinstance(event, QMouseEvent)
            and event.type() == QEvent.Type.MouseMove
            and self._settings.tooltip_mode
        ):
            self._show_editor_help(event)
            return False
        return super().eventFilter(obj, event)

    def _hover_help_for(self, block_text: str, word: str) -> str | None:
        """Pure lookup: contextual tooltip HTML for a section header or command."""
        header = re.match(r"\s*\[([^\]]+)\]", block_text)
        if header:
            sdoc = lookup_section(header.group(1))
            if sdoc is not None:
                return (
                    f"<b>[{sdoc.name}]</b><br>{sdoc.meaning}"
                    f"<br><i>{sdoc.when_needed}</i>"
                )
        cdoc = lookup_command(word)
        if cdoc is not None:
            return (
                f"<b>{cdoc.name}</b><br>{cdoc.semantics}<br>"
                f"<i>Uninstall: {cdoc.uninstall}</i>"
            )
        return None

    def _show_editor_help(self, event: QMouseEvent) -> None:
        """Stable hover help: ONE tooltip mechanism, no fight with the native
        widget tooltip. Over a keyword the native text is suppressed and the
        contextual tip is shown once per word (no flicker on micro-moves);
        leaving the keyword restores the general editor tip."""
        from PySide6.QtWidgets import QToolTip

        cursor = self._editor.cursorForPosition(event.position().toPoint())
        block_text = cursor.block().text()
        word_cursor = QTextCursor(cursor)
        word_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = word_cursor.selectedText()

        help_text = self._hover_help_for(block_text, word)
        if help_text is not None:
            if self._hover_state != help_text:
                self._hover_state = help_text
                self._editor.setToolTip("")  # suppress the native general tip
                QToolTip.showText(
                    event.globalPosition().toPoint(), help_text, self._editor
                )
            return

        if self._hover_state is not None:  # just left a keyword
            self._hover_state = None
            self._editor.setToolTip(tip_text(self._editor))  # restore general tip
            QToolTip.hideText()

    def _show_diag_menu(self, pos: QPoint) -> None:
        item = self._diag_list.itemAt(pos)
        if item is None:
            return
        d: Diagnostic | None = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self._diag_list)
        details = menu.addAction("Details anzeigen…")
        jump = menu.addAction("Zur Zeile springen")
        fix_act = None
        if d is not None and any(
            fix.note in {"strip_bom_and_set_cp1252", "set_cp1252"}
            or (fix.note == "insert_section" and fix.replacement_line)
            for fix in d.quick_fixes
        ):
            fix_act = menu.addAction("QuickFix anwenden")
        chosen = menu.exec(self._diag_list.mapToGlobal(pos))
        if chosen is None:
            return
        if chosen == details:
            self._show_diag_details(item)
        elif chosen == jump:
            self._jump_diag(item)
        elif fix_act is not None and chosen == fix_act and d is not None:
            self._apply_quickfix_for(d)

    def _show_diag_details(self, item: QListWidgetItem) -> None:
        import html as _html

        from emp_packagex3.learning_content import VAL_DOCS

        d: Diagnostic | None = item.data(Qt.ItemDataRole.UserRole)
        if d is None:
            return
        doc = VAL_DOCS.get(d.code)
        if doc is None:
            QMessageBox.information(self, d.code, d.message)
            return
        QMessageBox.information(
            self,
            f"{d.code} – {doc.severity}",
            f"<p><b>{_html.escape(d.message)}</b></p>"
            f"<p><b>Ursache:</b> {_html.escape(doc.cause)}</p>"
            f"<p><b>Behebung:</b> {_html.escape(doc.remedy)}</p>"
            f"<p><i>Referenz: {_html.escape(doc.reference)}</i></p>",
        )

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"Über {APP_DISPLAY_NAME}",
            f"<h3>{APP_DISPLAY_NAME}</h3>"
            f"<p>Version {__version__}</p>"
            f"<p>Zielplattform: Empirum {TARGET_EMPIRUM_VERSION}</p>"
            f"<p>{COPYRIGHT}</p>"
            f"<p>{ORG_NAME}</p>",
        )


def run_app(
    argv: list[str] | None = None,
    *,
    initial_file: Path | None = None,
) -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(__version__)
    from emp_packagex3.icons import load_app_icon

    icon = load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    if initial_file is not None:
        # Explorer file association: load after show so warning dialogs
        # have a parent window on screen.
        window.load_file_at_startup(initial_file)
    return app.exec()
