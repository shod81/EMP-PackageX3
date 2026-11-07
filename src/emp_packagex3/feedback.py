"""Create a feedback ZIP with logs and environment info for beta support."""

from __future__ import annotations

import platform
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from emp_packagex3 import COPYRIGHT, __version__
from emp_packagex3.logging_setup import default_log_dir


def create_feedback_zip(
    destination: Path,
    *,
    log_dir: Path | None = None,
    extra_note: str = "",
) -> Path:
    """Write a ZIP containing recent logs + a README.txt with version/OS info."""
    dest = Path(destination)
    if dest.suffix.casefold() != ".zip":
        dest = dest.with_suffix(".zip")
    dest.parent.mkdir(parents=True, exist_ok=True)

    logs = Path(log_dir) if log_dir else default_log_dir()
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    readme = (
        f"EMP-PackageX3 Feedback\n"
        f"Version: {__version__}\n"
        f"Copyright: {COPYRIGHT}\n"
        f"Generated (UTC): {stamp}\n"
        f"OS: {platform.platform()}\n"
        f"Python: {platform.python_version()}\n"
        f"Log-Dir: {logs}\n"
        f"\n"
        f"Hinweis des Absenders:\n{extra_note.strip() or '(keine)'}\n"
        f"\n"
        f"Bitte dieses ZIP an ein GitHub-Issue anhaengen:\n"
        f"https://github.com/shod81/EMP-PackageX3/issues\n"
        f"Vor dem Teilen pruefen: Logs enthalten lokale Pfade und Rechnernamen.\n"
    )

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme)
        if logs.is_dir():
            for path in sorted(logs.glob("*.log*")):
                if path.is_file():
                    zf.write(path, arcname=f"logs/{path.name}")
        else:
            zf.writestr("logs/MISSING.txt", f"Log-Ordner nicht gefunden: {logs}\n")
    return dest.resolve()
