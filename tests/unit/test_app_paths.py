"""Shared application data base path (one definition for all app folders)."""

from __future__ import annotations

from pathlib import Path

import pytest

from empirum_services.app_paths import APP_FOLDER_NAME, APP_VENDOR_DIR, app_data_dir


def test_app_data_dir_uses_localappdata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A redirected LOCALAPPDATA must win over the hardcoded profile path."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    assert app_data_dir() == tmp_path / "LocalAppData" / APP_VENDOR_DIR / APP_FOLDER_NAME


def test_app_data_dir_falls_back_to_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    assert app_data_dir() == (
        tmp_path / "AppData" / "Local" / APP_VENDOR_DIR / APP_FOLDER_NAME
    )


def test_settings_logs_and_backups_share_the_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """settings.json, logs/ and backups/ live below the same base folder."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    from emp_packagex3.logging_setup import default_log_dir
    from emp_packagex3.settings import settings_path
    from empirum_services.package_readiness import default_repair_backup_dir

    base = app_data_dir()
    assert base in settings_path().parents
    assert base in default_log_dir().parents
    assert base in default_repair_backup_dir(tmp_path / "Demo_1.0").parents
