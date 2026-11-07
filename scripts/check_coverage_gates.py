"""Enforce per-package coverage floors from the last pytest coverage run.

``pytest`` writes ``.coverage`` (configured in ``pyproject.toml``). A single
global ``--cov-fail-under`` cannot express "90 % in empirum_core, 70 % in the
GUI layer", so this script slices the same coverage data per top-level package
and fails when one of them drops below its floor.

Exit code 0 = all gates passed, 1 = at least one package below its floor.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Floor per package. Values sit ~4 points below the 1.0 status quo
# (empirum_core 93 %, emp_packagex3 72 %, empirum_services 86 %, empirum_infra 69 %)
# so normal refactoring does not break CI, while a package collapsing to zero does.
FLOORS: tuple[tuple[str, int], ...] = (
    ("empirum_core", 88),
    ("emp_packagex3", 68),
    ("empirum_services", 82),
    ("empirum_infra", 65),
)


def _check(package: str, floor: int) -> bool:
    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "report",
        f"--include=src/{package}/*",
        f"--fail-under={floor}",
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = f"{proc.stdout}\n{proc.stderr}"
    total = next(
        (line.strip() for line in output.splitlines() if line.strip().startswith("TOTAL")),
        "no coverage data",
    )
    ok = proc.returncode == 0
    print(f"{'OK' if ok else 'FAIL'}: {package} (floor {floor}%) -> {total}")
    if not ok:
        reason = next(
            (
                line.strip()
                for line in output.splitlines()
                if line.strip().startswith("Coverage failure:")
            ),
            "",
        )
        if reason:
            print(f"      {reason}")
    return ok


def main() -> int:
    if not (ROOT / ".coverage").is_file():
        print("FAIL: .coverage fehlt - zuerst 'pytest' (mit Coverage) laufen lassen")
        return 1
    failed = [package for package, floor in FLOORS if not _check(package, floor)]
    if failed:
        print(f"FAIL: Coverage-Gate verfehlt für: {', '.join(failed)}")
        return 1
    print(f"OK: alle {len(FLOORS)} Paket-Coverage-Gates erfüllt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
