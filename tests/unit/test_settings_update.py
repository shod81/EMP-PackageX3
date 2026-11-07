from __future__ import annotations

import json
from pathlib import Path

from emp_packagex3.settings import (
    AppSettings,
    load_settings,
    resolve_manifest_location,
    save_settings,
)
from empirum_services.local_depot import ensure_local_depot
from empirum_services.update_check import check_update, check_update_from_json, compare_versions


def test_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    s = AppSettings(
        theme="dark",
        runner_roots=["D:\\VM"],
        depot_path=str(tmp_path / "depot"),
        debug_logging=True,
        tooltip_mode=False,
    )
    save_settings(s, path)
    loaded = load_settings(path)
    assert loaded.theme == "dark"
    assert loaded.depot_path.endswith("depot")
    assert loaded.debug_logging is True
    assert loaded.tooltip_mode is False


def test_undocumented_commands_flag_defaults_off_and_roundtrips(tmp_path: Path) -> None:
    # Class-1 secret commands are OFF by default (no Matrix42 safety net)
    assert AppSettings.defaults().undocumented_commands is False

    path = tmp_path / "settings.json"
    save_settings(AppSettings(undocumented_commands=True), path)
    loaded = load_settings(path)
    assert loaded.undocumented_commands is True

    # Strict bool: hand-edited "true" string must not enable the flag
    path.write_text('{"undocumented_commands": "true"}', encoding="utf-8")
    assert load_settings(path).undocumented_commands is False


def test_resolve_manifest_from_depot_folder(tmp_path: Path) -> None:
    s = AppSettings(depot_path=str(tmp_path), update_manifest_url="")
    loc = resolve_manifest_location(s)
    assert loc.endswith("VERSION.json")


def test_compare_versions() -> None:
    assert compare_versions("0.4.0", "0.5.0") < 0
    assert compare_versions("0.5.0", "0.5.0") == 0
    assert compare_versions("1.0.0", "0.9.9") > 0
    # Pre-releases sort below the final release of the same version (review S4).
    assert compare_versions("1.0.0-rc2", "1.0.0") < 0
    assert compare_versions("1.0.0", "1.0.0-rc2") > 0
    assert compare_versions("1.0.0-rc1", "1.0.0-rc2") < 0
    assert compare_versions("1.0.0-beta", "1.0.0-rc1") < 0
    assert compare_versions("0.5.2", "1.0.0-rc1") < 0


def test_update_from_rc_to_final_detected() -> None:
    info = check_update_from_json({"version": "1.0.0"}, current="1.0.0-rc2")
    assert info.update_available is True
    downgrade = check_update_from_json({"version": "1.0.0-rc1"}, current="1.0.0")
    assert downgrade.update_available is False


def test_update_manifest_detects_newer() -> None:
    info = check_update_from_json(
        {"version": "0.5.0", "notes": "n", "download_url": "u"},
        current="0.4.0",
    )
    assert info.update_available is True
    assert info.latest == "0.5.0"


def test_local_depot_and_check_update(tmp_path: Path) -> None:
    manifest = ensure_local_depot(tmp_path, version="0.9.0", notes="local")
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["version"] == "0.9.0"
    info = check_update(str(manifest), current="0.5.0")
    assert info.update_available is True
    assert info.latest == "0.9.0"


def test_load_manifest_accepts_utf8_bom(tmp_path: Path) -> None:
    manifest = tmp_path / "VERSION.json"
    manifest.write_bytes(b"\xef\xbb\xbf" + json.dumps({"version": "9.9.9"}).encode("utf-8"))
    info = check_update(str(manifest), current="1.0.0")
    assert info.update_available is True
    assert info.latest == "9.9.9"


def test_local_depot_updates_stale_version(tmp_path: Path) -> None:
    depot = tmp_path / "depot"
    ensure_local_depot(depot, version="0.9.0", notes="alt")
    manifest = depot / "VERSION.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["version"] == "0.9.0"
    ensure_local_depot(depot, version="1.0.0", notes="neu")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["version"] == "1.0.0"
    assert data["notes"] == "neu"
    assert "1.0.0" in data["download_url"]


def test_load_settings_backs_up_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{ not json", encoding="utf-8")
    loaded = load_settings(path)
    assert loaded == AppSettings.defaults()
    assert (tmp_path / "settings.corrupt").is_file()


def test_load_settings_rejects_string_runner_roots(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"runner_roots": "C:\\VM"}', encoding="utf-8")
    loaded = load_settings(path)
    assert loaded.runner_roots == AppSettings.defaults().runner_roots


def test_load_settings_strict_bools(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"tooltip_mode": "false"}', encoding="utf-8")
    loaded = load_settings(path)
    # hand-edited "false" must not become True
    assert loaded.tooltip_mode is False
