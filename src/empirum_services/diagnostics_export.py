"""Export linter diagnostics for support tickets."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from empirum_core.linter import Diagnostic


def format_diagnostics_report(
    diagnostics: list[Diagnostic],
    *,
    package: str = "",
    app_version: str = "",
) -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "EMP-PackageX3 Diagnose-Export",
        f"UTC: {stamp}",
        f"App: {app_version}",
        f"Paket: {package}",
        f"Anzahl: {len(diagnostics)}",
        "---",
    ]
    for d in diagnostics:
        lines.append(
            f"Z{d.line or '?'} [{d.severity.value}] {d.code}: {d.message}"
        )
    return "\n".join(lines) + "\n"


def write_diagnostics_report(path: Path, text: str) -> Path:
    path = Path(path)
    path.write_text(text, encoding="utf-8")
    return path
