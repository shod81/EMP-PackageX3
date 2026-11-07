"""Slim IntelliSense for Setup.inf (sections, commands, variables) – 1.0 scope.

Word lists derive from empirum_core.setupinf_contract (reference-verified catalog).
Class-1 undocumented commands/variables (verified, undocumented) are only
offered when `undocumented=True` (feature flag in the app settings).
"""

from __future__ import annotations

import re

from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QCompleter, QPlainTextEdit

from empirum_core.setupinf_contract import (
    SETUPINF_COMMANDS,
    SETUPINF_COMMANDS_UNDOCUMENTED,
    SETUPINF_COPYFLAGS,
    SETUPINF_FUNCTIONS,
    SETUPINF_PREDICATES,
    SETUPINF_SWITCHES,
    SETUPINF_VARIABLES,
    SETUPINF_VARIABLES_UNDOCUMENTED,
    STANDARD_SECTIONS,
    USER_PART_SECTIONS,
)

COMMANDS = list(SETUPINF_COMMANDS)
VARIABLES = list(SETUPINF_VARIABLES)
PREDICATES = list(SETUPINF_PREDICATES)
FUNCTIONS = list(SETUPINF_FUNCTIONS)
COPYFLAGS = list(SETUPINF_COPYFLAGS)
SWITCHES = list(SETUPINF_SWITCHES)

# Section names offered by the completer: the standard catalog itself, so
# the popup can never suggest a legacy/nonexistent [Set_Install]-style name.
# [Set:Client] (user part) is offered additionally — it is valid
# but intentionally not part of the standard required set (VAL-012).
SECTIONS = list(STANDARD_SECTIONS) + list(USER_PART_SECTIONS)

# Valid #Set: targets per standard contract (see empirum_core.setupinf_contract).
SET_TARGETS = [
    "#Set:Product",
    "#Set:Deinstallation",
    "#Set:InstallationError",
    "#Set:ReinstallationError",
    "#Set:DeInstallationError",
    "#Set:Client",
    "#Set:Client, CLIENT",
]

# Token characters that may appear inside a completion prefix.
_TOKEN_RE = re.compile(r"[\w%().:\[\]#-]*$")


def _prefix_at_cursor(editor: QPlainTextEdit) -> str:
    """Completion token ending at the cursor (incl. '[Sect', '#Set:…', '%Var')."""
    cursor = editor.textCursor()
    line = cursor.block().text()
    pos = cursor.positionInBlock()
    match = _TOKEN_RE.search(line[:pos])
    return match.group(0) if match else ""


def completer_words(undocumented: bool = False) -> list[str]:
    """Completion vocabulary; class-1 constructs only behind the feature flag."""
    words = (
        COMMANDS
        + PREDICATES
        + FUNCTIONS
        + VARIABLES
        + COPYFLAGS
        + SWITCHES
        + [f"[{s}]" for s in SECTIONS]
        + SET_TARGETS
    )
    if undocumented:
        words = words + list(SETUPINF_COMMANDS_UNDOCUMENTED) + list(
            SETUPINF_VARIABLES_UNDOCUMENTED
        )
    return words


def refresh_completer(completer: QCompleter, undocumented: bool = False) -> None:
    """Swap the word list of an attached completer (feature flag toggle)."""
    words = completer_words(undocumented)
    model = completer.model()
    if isinstance(model, QStringListModel):
        model.setStringList(words)
    else:  # pragma: no cover - defensive
        completer.setModel(QStringListModel(words, completer))


def attach_completer(
    editor: QPlainTextEdit, *, undocumented: bool = False
) -> QCompleter:
    words = completer_words(undocumented)
    completer = QCompleter(words)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setWidget(editor)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    completer.setModel(QStringListModel(words, completer))

    def insert_completion(completion: str) -> None:
        prefix = _prefix_at_cursor(editor)
        if not prefix:
            return
        cursor = editor.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(prefix)
        )
        cursor.removeSelectedText()
        cursor.insertText(completion)
        editor.setTextCursor(cursor)

    completer.activated.connect(insert_completion)

    def on_text_changed() -> None:
        popup = completer.popup()
        prefix = _prefix_at_cursor(editor)
        if len(prefix) < 1 or popup is None:
            if popup is not None:
                popup.hide()
            return
        completer.setCompletionPrefix(prefix)
        if completer.completionCount() == 0:
            popup.hide()
            return
        cr = editor.cursorRect()
        cr.setWidth(
            popup.sizeHintForColumn(0)
            + popup.verticalScrollBar().sizeHint().width()
        )
        completer.complete(cr)

    editor.textChanged.connect(on_text_changed)
    return completer
