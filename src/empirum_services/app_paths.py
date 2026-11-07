"""Application data locations shared by settings, logs and backups.

``settings.json``, the rotating log files and the repair WAL backups all
live under ``%LOCALAPPDATA%\\HodriusSystems\\EMP-PackageX3``. That base path is
defined here exactly once: three copies under ``emp_packagex3`` could drift
apart, and a hardcoded ``Path.home() / "AppData" / "Local"`` ignores a
redirected (or roaming) ``LOCALAPPDATA``.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_VENDOR_DIR = "HodriusSystems"
APP_FOLDER_NAME = "EMP-PackageX3"


def app_data_dir() -> Path:
    """``<LOCALAPPDATA>/HodriusSystems/EMP-PackageX3`` (not created here)."""
    local = os.environ.get("LOCALAPPDATA")
    base = Path(local) if local else Path.home() / "AppData" / "Local"
    return base / APP_VENDOR_DIR / APP_FOLDER_NAME
