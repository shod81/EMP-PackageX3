"""Local Empirum test runner – VM/whitelist only (plan adjustment #3).

Threat model: the whitelist + VM marker protect against ACCIDENTAL runs on
productive hosts (wrong folder, missing snapshot). They are not a security
boundary – any local process can create the marker file and whitelist roots
are user-writable. Run only in disposable VMs with snapshots.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class RunnerSafetyError(RuntimeError):
    """Raised when execution target is not an approved test environment."""


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    """Whitelist of allowed package/test roots. No elevation outside these paths."""

    allowed_roots: tuple[Path, ...]
    setup_exe: Path | None = None
    require_vm_marker: bool = True
    vm_marker_file: str = ".emp_packagex3_vm"
    timeout_seconds: float = 900.0

    @classmethod
    def default(cls) -> RunnerConfig:
        temp = Path(os.environ.get("TEMP", os.environ.get("TMP", ".")))
        return cls(
            allowed_roots=(
                (temp / "EmpirumTest").resolve(),
                Path("C:/EmpirumTestVM").resolve(),
            ),
            require_vm_marker=True,
        )


@dataclass(slots=True)
class RunnerResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def assert_safe_target(package_dir: Path, config: RunnerConfig | None = None) -> Path:
    cfg = config or RunnerConfig.default()
    target = package_dir.resolve()
    if not any(target.is_relative_to(root) for root in cfg.allowed_roots):
        raise RunnerSafetyError(
            f"Paketpfad nicht auf Whitelist: {target}. "
            f"Erlaubt: {', '.join(str(r) for r in cfg.allowed_roots)}"
        )
    if cfg.require_vm_marker:
        marker = None
        for root in cfg.allowed_roots:
            if target.is_relative_to(root):
                candidate = root / cfg.vm_marker_file
                if candidate.is_file():
                    marker = candidate
                    break
        if marker is None:
            raise RunnerSafetyError(
                "VM-/Testumgebungs-Marker fehlt "
                f"({cfg.vm_marker_file}). Kein elevierter Lauf ohne Snapshot-Umgebung."
            )
    return target


def build_command(
    package_dir: Path,
    *,
    mode: str = "install",
    setup_exe: Path | None = None,
) -> list[str]:
    setup_inf = package_dir / "Install" / "Setup.inf"
    if not setup_inf.is_file():
        raise FileNotFoundError(setup_inf)
    mode_l = mode.casefold()
    if mode_l not in {"install", "uninstall"}:
        raise ValueError(f"mode muss 'install' oder 'uninstall' sein, erhalten: {mode!r}")
    # %…% tokens are not expanded by CreateProcess – resolve them here.
    exe = setup_exe or Path(
        os.path.expandvars(
            os.environ.get(
                "EMPIRUM_SETUP_EXE",
                r"%CommonFilesDir%\Setup64\Setup.exe",
            )
        )
    )
    # Empirum flags: /S2 silent install, /U uninstall
    flag = "/U" if mode_l == "uninstall" else "/S2"
    return [str(exe), str(setup_inf), flag]


def run_package(
    package_dir: Path,
    *,
    mode: str = "install",
    config: RunnerConfig | None = None,
    dry_run: bool = True,
) -> RunnerResult:
    """Execute only after safety checks. Default dry_run=True (no process start)."""
    cfg = config or RunnerConfig.default()
    target = assert_safe_target(package_dir, cfg)
    cmd = build_command(target, mode=mode, setup_exe=cfg.setup_exe)
    if dry_run:
        return RunnerResult(command=cmd, returncode=0, stdout="dry-run", stderr="")
    # Real execution still requires whitelist + marker; caller opts in explicitly.
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=cfg.timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout
        partial = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        return RunnerResult(
            command=cmd,
            returncode=-1,
            stdout="",
            stderr=(
                f"Setup.exe-Aufruf nach {cfg.timeout_seconds:.0f}s abgebrochen (Timeout)."
                f" Teilweise Ausgabe: {partial or ''}"
            ),
        )
    return RunnerResult(
        command=cmd,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
