"""Automate verifiable 1.0 release checklist items (no EV cert / human beta)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def check_version_sync() -> str:
    sys.path.insert(0, str(SRC))
    from emp_packagex3 import __version__ as app_ver

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    marker = 'version = "'
    try:
        line = next(ln for ln in pyproject.splitlines() if ln.startswith("version = "))
    except StopIteration:
        _fail("pyproject.toml enthält keine 'version = ' Zeile")
        raise  # unreachable, for type checkers
    proj_ver = line.split(marker, 1)[1].rstrip('"')
    manifest = json.loads((ROOT / "packaging" / "VERSION.json").read_text(encoding="utf-8"))
    man_ver = str(manifest["version"])
    if not (app_ver == proj_ver == man_ver):
        _fail(f"version mismatch app={app_ver} pyproject={proj_ver} VERSION.json={man_ver}")
    _ok(f"version sync {app_ver}")
    if "depot.example.local" in str(manifest.get("download_url", "")):
        print("WARN: download_url ist noch der Platzhalter (depot.example.local)")
    return app_ver


def check_golden_corpus() -> None:
    golden = list((ROOT / "testdata" / "golden").glob("*.inf"))
    if len(golden) < 25:
        _fail(f"golden corpus expected >=25, got {len(golden)}")
    _ok(f"golden corpus {len(golden)} files")


def check_vm_runner_default() -> None:
    sys.path.insert(0, str(SRC))
    from emp_packagex3.settings import AppSettings

    s = AppSettings.defaults()
    if not s.require_vm_marker:
        _fail("require_vm_marker must default to True")
    _ok("runner defaults require_vm_marker=True")


def check_package_store_defaults() -> None:
    sys.path.insert(0, str(SRC))
    from emp_packagex3.settings import AppSettings
    from empirum_services.package_store import default_package_store_unc

    s = AppSettings.defaults()
    expected = default_package_store_unc()
    if "PackageStore" not in s.package_store_path:
        _fail("package_store_path missing PackageStore")
    if s.package_store_path != expected:
        _fail(f"unexpected default store path: {s.package_store_path}")
    _ok("PackageStore defaults present")


def check_docs() -> None:
    required = [
        ROOT / "docs" / "sign-anleitung.md",
        ROOT / "docs" / "local-depot.md",
        ROOT / "docs" / "package-store-deploy.md",
        ROOT / "docs" / "beta-logging.md",
        ROOT / "docs" / "beta-checklist.md",
        ROOT / "docs" / "empirum-version-matrix.md",
        ROOT / "docs" / "release.md",
        ROOT / "docs" / "setupinf-standard-alignment.md",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    if missing:
        _fail(f"missing docs: {', '.join(missing)}")
    _ok(f"release docs present ({len(required)})")


def main() -> None:
    print("EMP-PackageX3 release gates")
    ver = check_version_sync()
    check_golden_corpus()
    check_vm_runner_default()
    check_package_store_defaults()
    check_docs()
    print(f"All automated gates passed for {ver}")
    print("Remaining (manual/field): EV signing, beta with packagers, real depot URL")


if __name__ == "__main__":
    main()
