"""Setup.inf syntax highlighter for QPlainTextEdit."""

from __future__ import annotations

import re

from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument

# Comment starts at a ';' that is preceded by whitespace (or line start).
_TRAILING_COMMENT_RE = re.compile(r"(?:^|\s);")


class SetupInfHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self._section = _fmt("#1a5f7a", bold=True)
        self._comment = _fmt("#6a737d", italic=True)
        self._key = _fmt("#0b3d91")
        self._value = _fmt("#1b4332")
        self._ref = _fmt("#9a3412", bold=True)
        self._var = _fmt("#7c3aed")

    def highlightBlock(self, text: str) -> None:  # noqa: N802 – Qt API
        stripped = text.lstrip()
        if stripped.startswith(";"):
            self.setFormat(0, len(text), self._comment)
            return
        if stripped.startswith("[") and "]" in stripped:
            self.setFormat(0, len(text), self._section)
            return
        if stripped.startswith("#"):
            self.setFormat(0, len(text), self._ref)
            return
        # Trailing comment: value part ends before ' ;' (Empirum convention)
        comment_start = -1
        search_from = 0
        eq = text.find("=")
        search_from = eq + 1 if eq > 0 else 0
        rest = text[search_from:]
        m = _TRAILING_COMMENT_RE.search(rest)
        if m:
            comment_start = search_from + m.start()
        value_end = comment_start if comment_start > 0 else len(text)
        if eq > 0:
            self.setFormat(0, eq, self._key)
            self.setFormat(eq + 1, value_end - eq - 1, self._value)
        if comment_start > 0:
            self.setFormat(comment_start, len(text) - comment_start, self._comment)
        # variables %...%
        i = 0
        while True:
            start = text.find("%", i)
            if start < 0 or start >= value_end:
                break
            end = text.find("%", start + 1)
            if end < 0 or end >= value_end:
                break
            self.setFormat(start, end - start + 1, self._var)
            i = end + 1


def _fmt(color: str, *, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    return fmt
