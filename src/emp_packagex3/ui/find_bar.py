"""Inline search bar for the Setup.inf editor (Ctrl+F / F3 / Shift+F3)."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from emp_packagex3.ui.tooltip_mode import apply_tooltip_mode, bind_field

# M-5: live typing is debounced so a full-document match count does not run on
# every keystroke; Enter/buttons/case toggle/Esc flush immediately.
_SEARCH_DEBOUNCE_MS = 120


class FindBar(QFrame):
    """Search bar below the editor: term, direction, case toggle, match status.

    Emits search_requested(term, case_sensitive, backward) on Enter, buttons
    and live typing; the main window performs the search and reports back
    via set_status().
    """

    search_requested = Signal(str, bool, bool)
    closed = Signal()

    def __init__(self, parent: QWidget | None = None, *, tooltip_mode: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("findBar")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._term = QLineEdit()
        self._term.setPlaceholderText("Suchen…")
        bind_field(self._term, "edit.find_term")

        self._case = QCheckBox("Groß/Klein")
        bind_field(self._case, "edit.find_case")

        prev_btn = QPushButton("Zurück")
        prev_btn.setToolTip("Vorheriger Treffer (Umschalt+Eingabe)")
        next_btn = QPushButton("Weiter")
        next_btn.setToolTip("Nächster Treffer (Eingabe)")

        self._status = QLabel()
        self._status.setObjectName("findStatus")

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.setToolTip("Suche schließen (Esc)")
        bind_field(close_btn, "edit.find_close")

        # M-5: create the debounce timer before wiring textChanged -> _schedule_search.
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(_SEARCH_DEBOUNCE_MS)
        self._debounce.timeout.connect(lambda: self._emit_search(backward=False))

        self._term.returnPressed.connect(lambda: self._emit_search(backward=False))
        self._case.toggled.connect(lambda _checked: self._emit_search(backward=False))
        next_btn.clicked.connect(lambda: self._emit_search(backward=False))
        prev_btn.clicked.connect(lambda: self._emit_search(backward=True))
        close_btn.clicked.connect(self._close)
        self._term.textChanged.connect(self._schedule_search)
        self._term.installEventFilter(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(self._term, stretch=1)
        layout.addWidget(self._case)
        layout.addWidget(prev_btn)
        layout.addWidget(next_btn)
        layout.addWidget(self._status)
        layout.addWidget(close_btn)

        apply_tooltip_mode(self, tooltip_mode)

    # -- events -------------------------------------------------------------

    def eventFilter(
        self, obj: QObject, event: QEvent
    ) -> bool:  # noqa: N802 – Qt API
        """Shift+Return searches backwards, like established editors."""
        if (
            obj is self._term
            and isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self._emit_search(backward=True)
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 – Qt API
        if event.key() == Qt.Key.Key_Escape:
            self._close()
            return
        super().keyPressEvent(event)

    # -- API ------------------------------------------------------------------

    def open_with(self, term: str = "") -> None:
        """Show the bar, prefill the term (e.g. editor selection) and search once.

        A pending debounce is flushed here so opening the bar always reports a
        fresh result – even when the term is unchanged (M-5).
        """
        if term and term != self._term.text():
            self._term.setText(term)
        self.show()
        self._term.setFocus()
        self._term.selectAll()
        self._emit_search(backward=False)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def term(self) -> str:
        """Current search term (what the next search would use)."""
        return self._term.text()

    def set_term(self, term: str) -> None:
        """Set the term without searching; the caller triggers the search."""
        self._term.setText(term)

    def case_sensitive(self) -> bool:
        """True when the Groß/Klein toggle is active."""
        return self._case.isChecked()

    def search(self, *, backward: bool = False) -> None:
        """Search now with the current term/case and flush the debounce."""
        self._emit_search(backward=backward)

    def dismiss(self) -> None:
        """Close the bar (Esc / ✕).

        Named ``dismiss`` on purpose: ``close()`` is ``QWidget.close()`` and
        overriding it would change the widget semantics.
        """
        self._close()

    def is_open(self) -> bool:
        """True when the bar was shown and not closed (M-5).

        Deliberately not ``isVisible()``: that is also False while the owning
        window has not been shown yet, which made the shortcuts/tests flaky.
        """
        return not self.isHidden()

    # -- internals ------------------------------------------------------------

    def _schedule_search(self, *_ignored: object) -> None:
        self._debounce.start()

    def _emit_search(self, *, backward: bool) -> None:
        """Emit a search now, cancelling any pending debounce (no double fire)."""
        if self._debounce.isActive():
            self._debounce.stop()
        self.search_requested.emit(self._term.text(), self._case.isChecked(), backward)

    def _close(self) -> None:
        self._debounce.stop()  # a closing bar must not emit afterwards
        self.hide()
        self.closed.emit()
