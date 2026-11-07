"""Persistent application settings (theme, runner whitelist, depot, logging)."""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from empirum_services.app_paths import app_data_dir
from empirum_services.local_depot import default_local_depot_path
from empirum_services.package_store import default_package_store_unc


@dataclass(slots=True)
class AppSettings:
    theme: str = "light"
    runner_roots: list[str] = field(
        default_factory=lambda: [
            str(Path.home() / "AppData" / "Local" / "Temp" / "EmpirumTest"),
            "C:\\EmpirumTestVM",
        ]
    )
    require_vm_marker: bool = True
    # Local folder OR http(s) URL to VERSION.json / depot root (App-Updates)
    depot_path: str = field(default_factory=lambda: str(default_local_depot_path()))
    # Explicit manifest override (file path or URL). Empty = <depot_path>/VERSION.json
    update_manifest_url: str = ""
    last_update_check: str = ""
    debug_logging: bool = True  # Beta default: verbose file logs
    log_dir: str = ""
    # Empirum PackageStore (Configurator$) – fertige Setup.inf-Pakete
    empirum_server: str = ""
    package_store_path: str = field(default_factory=default_package_store_unc)
    package_store_mode: str = "vendor_product_version"
    # Learning tooltips on menus/fields for IT admins
    tooltip_mode: bool = True
    # Class-1 undocumented commands (verified 26.1.0, absent from ALL official
    # docs): gated because there is no Matrix42 support net (Semantik teils offen).
    undocumented_commands: bool = False

    @classmethod
    def defaults(cls) -> AppSettings:
        return cls()


def settings_path() -> Path:
    base = app_data_dir()
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


def load_settings(path: Path | None = None) -> AppSettings:
    file = path or settings_path()
    if not file.is_file():
        return AppSettings.defaults()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # Keep the corrupt file for inspection instead of silently losing config.
        with contextlib.suppress(OSError):
            file.rename(file.with_suffix(".corrupt"))
        return AppSettings.defaults()
    defaults = AppSettings.defaults()
    raw_roots = data.get("runner_roots", defaults.runner_roots)
    runner_roots = (
        [str(r) for r in raw_roots] if isinstance(raw_roots, list) else defaults.runner_roots
    )
    return AppSettings(
        theme=str(data.get("theme", defaults.theme)),
        runner_roots=runner_roots,
        require_vm_marker=_as_bool(data.get("require_vm_marker", defaults.require_vm_marker)),
        depot_path=str(data.get("depot_path", defaults.depot_path)),
        update_manifest_url=str(data.get("update_manifest_url", "")),
        last_update_check=str(data.get("last_update_check", "")),
        debug_logging=_as_bool(data.get("debug_logging", defaults.debug_logging)),
        log_dir=str(data.get("log_dir", "")),
        empirum_server=str(data.get("empirum_server", "")),
        package_store_path=str(
            data.get("package_store_path", defaults.package_store_path)
        ),
        package_store_mode=str(
            data.get("package_store_mode", defaults.package_store_mode)
        ),
        tooltip_mode=_as_bool(data.get("tooltip_mode", defaults.tooltip_mode)),
        undocumented_commands=_as_bool(
            data.get("undocumented_commands", defaults.undocumented_commands)
        ),
    )


def _as_bool(value: object) -> bool:
    """Strict bool: hand-edited strings like \"false\" must not become True."""
    return value is True or value == 1


def save_settings(settings: AppSettings, path: Path | None = None) -> Path:
    file = path or settings_path()
    file.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: a crash mid-save must not produce a corrupt settings.json.
    tmp = file.with_name(f".{file.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    tmp.replace(file)
    return file


def resolve_manifest_location(settings: AppSettings) -> str:
    """Return path or URL used for update checks."""
    if settings.update_manifest_url.strip():
        return settings.update_manifest_url.strip()
    depot = settings.depot_path.strip()
    if not depot:
        return ""
    if depot.lower().startswith(("http://", "https://")):
        return depot.rstrip("/") + "/VERSION.json"
    return str((Path(depot) / "VERSION.json").resolve())
