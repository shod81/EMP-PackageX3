"""Local software depot helpers (file-based VERSION.json, later HTTP-ready)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

DEFAULT_DEPOT_NAME = "EMP-PackageX3-Depot"


def default_local_depot_path() -> Path:
    return Path.home() / "Documents" / DEFAULT_DEPOT_NAME


def ensure_local_depot(
    depot_dir: Path,
    *,
    version: str,
    notes: str = "Lokales Depot – Build hier ablegen.",
    template_manifest: Path | None = None,
) -> Path:
    """Create depot folder + VERSION.json; refresh it when the version is stale."""
    depot_dir = Path(depot_dir)
    depot_dir.mkdir(parents=True, exist_ok=True)
    manifest = depot_dir / "VERSION.json"
    fresh = not manifest.is_file()
    if fresh:
        if template_manifest and template_manifest.is_file():
            shutil.copy2(template_manifest, manifest)
            data = _read_manifest_json(manifest)
        else:
            data = {}
    else:
        data = _read_manifest_json(manifest)
    if fresh or data.get("version") != version:
        data["version"] = version
        data["notes"] = notes
        # Local path hint for testers (not always a URL)
        data["download_url"] = str((depot_dir / f"EMP-PackageX3-{version}.zip").resolve())
        manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme = depot_dir / "README.txt"
    if not readme.is_file():
        readme.write_text(
            "Lokales EMP-PackageX3-Depot\n"
            "1. Signierte Onedir-ZIP hier ablegen "
            "(Name wie in VERSION.json download_url).\n"
            "2. VERSION.json bei jedem Release aktualisieren.\n"
            "3. Später: Inhalt auf HTTP-/UNC-Share spiegeln "
            "und URL in den Einstellungen setzen.\n",
            encoding="utf-8",
        )
    return manifest


def _read_manifest_json(manifest: Path) -> dict[str, object]:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}
