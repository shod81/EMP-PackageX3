"""Light/Dark QSS themes for EMP-PackageX3."""

from __future__ import annotations

LIGHT_QSS = """
QWidget {
  background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
    stop:0 #e8eef1, stop:1 #f5f7f8);
  color: #1a1a1a;
}
QPlainTextEdit, QListWidget, QTreeWidget, QTabWidget, QLineEdit, QTextEdit {
  background: #fbfcfd; color: #1a1a1a;
  border: 1px solid #c5d0d6; border-radius: 4px;
}
QMenuBar, QMenu { background: #eef2f4; color: #1a1a1a; }
QStatusBar { background: #e4eaed; }
QPushButton {
  background: #dfe8ec; color: #1a1a1a;
  border: 1px solid #b6c4cc; padding: 4px 10px;
}
"""

DARK_QSS = """
QWidget {
  background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
    stop:0 #1b2429, stop:1 #12181c);
  color: #e8eef1;
}
QPlainTextEdit, QListWidget, QTreeWidget, QTabWidget, QLineEdit, QTextEdit {
  background: #1e272c; color: #e8eef1;
  border: 1px solid #3a4a52; border-radius: 4px;
}
QMenuBar, QMenu { background: #1e272c; color: #e8eef1; }
QStatusBar { background: #151c20; color: #c5d0d6; }
QPushButton {
  background: #2a3a42; color: #e8eef1;
  border: 1px solid #3a4a52; padding: 4px 10px;
}
"""


def theme_qss(name: str) -> str:
    return DARK_QSS if name.casefold() == "dark" else LIGHT_QSS


def dialog_colors(name: str) -> dict[str, str]:
    """Shared palette for themed dialogs (settings / wizard / store / simulator)."""
    if name.casefold() == "dark":
        return {
            "bg": "#1b2429",
            "input_bg": "#1e272c",
            "border": "#3a4a52",
            "text": "#e8eef1",
            "brand": "#9fd4e8",
            "muted": "#a8b6bd",
            "help_bg": "#233038",
            "help_accent": "#2a6f8f",
            "help_text": "#cdd8dd",
            "primary": "#2a5a72",
            "primary_hover": "#356d88",
            "primary_disabled": "#3c4a52",
            "step_done_bg": "#2c3d47",
            "panel_bg": "#202b31",
            "warning_bg": "#4d4310",
            "warning_text": "#ffc76b",
        }
    return {
        "bg": "#f7f9fa",
        "input_bg": "#ffffff",
        "border": "#d8e0e5",
        "text": "#1a1a1a",
        "brand": "#1a3a4a",
        "muted": "#5a6a72",
        "help_bg": "#eef3f6",
        "help_accent": "#2a6f8f",
        "help_text": "#2c3e48",
        "primary": "#1a3a4a",
        "primary_hover": "#244a5c",
        "primary_disabled": "#9aadb8",
        "step_done_bg": "#d5e4ec",
        "panel_bg": "#ffffff",
        "warning_bg": "#fff3bf",
        "warning_text": "#8a5a00",
    }
