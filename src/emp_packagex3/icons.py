"""Locate bundled application icons (dev tree, wheel, or frozen Onedir)."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def _icon_candidates(name: str) -> list[Path]:
    here = Path(__file__).resolve().parent
    out: list[Path] = [here / "resources" / name]
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            out.append(Path(meipass) / "emp_packagex3" / "resources" / name)
            out.append(Path(meipass) / "resources" / name)
            out.append(Path(meipass) / "assets" / name)
        out.append(Path(sys.executable).resolve().parent / "assets" / name)
    # Repo-root assets/ when running from a source checkout
    for parent in here.parents[:3]:
        out.append(parent / "assets" / name)
    return out


def icon_path(name: str = "emp_packagex3.ico") -> Path | None:
    for path in _icon_candidates(name):
        if path.is_file():
            return path
    if name.lower().endswith(".ico"):
        return icon_path("emp_packagex3.png")
    return None


def load_app_icon() -> QIcon:
    for name in ("emp_packagex3.ico", "emp_packagex3.png"):
        path = icon_path(name)
        if path is not None:
            return QIcon(str(path))
    if getattr(sys, "frozen", False):
        return QIcon(sys.executable)
    return QIcon()
