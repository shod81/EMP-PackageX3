"""Deploy Empirum packages to Configurator$\\PackageStore for MMC import.

Typical target:
  \\\\%EmpirumServer%\\Configurator$\\PackageStore\\[<Manufacturer>\\][<Product>\\][<Version>\\]

After copy, an Empirum admin imports the package into a software register
via the Empirum Management Console (Import from PackageStore).
"""

from __future__ import annotations

import os
import re
import shutil
import stat
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class DeployMode(StrEnum):
    FLAT = "flat"  # PackageStore/Product_Version/
    VENDOR_PRODUCT_VERSION = "vendor_product_version"  # Mfr/Product/Version/


@dataclass(frozen=True, slots=True)
class PackageLayout:
    package_dir: Path
    setup_inf: Path
    has_files_dir: bool


@dataclass(frozen=True, slots=True)
class DeployPlan:
    source: Path
    destination: Path
    mode: DeployMode
    overwrite: bool


@dataclass(frozen=True, slots=True)
class DeployResult:
    destination: Path
    copied_files: int
    dry_run: bool
    message: str


class PackageStoreError(ValueError):
    """Invalid package or PackageStore target."""


_SAFE = re.compile(r"[^\w.\- ]+", re.UNICODE)

# Windows reserved device names are invalid directory segments.
_RESERVED_SEGMENT_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def _rmtree_readonly_retry(function: Callable[..., object], path: str, _exc: BaseException) -> None:
    """rmtree hook: clear the read-only attribute and retry the failed step."""
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _is_within(child: Path, parent: Path) -> bool:
    """Component-wise containment check (case-insensitive, no resolve needed)."""
    parent_parts = [part.casefold().rstrip("\\/") for part in parent.parts]
    child_parts = [part.casefold().rstrip("\\/") for part in child.parts]
    if child_parts[: len(parent_parts)] != parent_parts:
        return False
    return all(part not in {"..", ""} for part in child_parts[len(parent_parts):])


def _ensure_within_store(destination: Path, store_root: Path) -> None:
    if not _is_within(destination, store_root):
        raise PackageStoreError(
            f"Ungültiges Deploy-Ziel außerhalb des PackageStore: {destination}"
        )


_ENV_TOKEN_RE = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")


def _expand_env(text: str, env: dict[str, str]) -> str:
    """Expand %VAR% tokens against the given environment (not os.environ)."""

    def repl(match: re.Match[str]) -> str:
        return env.get(match.group(1), match.group(0))

    return _ENV_TOKEN_RE.sub(repl, text)


def expand_empirum_path(
    path: str,
    *,
    empirum_server: str = "",
    environ: dict[str, str] | None = None,
) -> str:
    """Expand %EmpirumServer% / %EMPIRUMSERVER% and Windows env vars."""
    env = dict(os.environ if environ is None else environ)
    server = (
        empirum_server.strip()
        or env.get("EmpirumServer", "").strip()
        or env.get("EMPIRUMSERVER", "").strip()
        or env.get("EMPIRUM_SERVER", "").strip()
    )
    if server:
        env.setdefault("EmpirumServer", server)
        env.setdefault("EMPIRUMSERVER", server)
        env.setdefault("EMPIRUM_SERVER", server)
    text = path
    # Case-insensitive replace for EmpirumServer token
    for key in ("EmpirumServer", "EMPIRUMSERVER", "EMPIRUM_SERVER"):
        token = f"%{key}%"
        if token.lower() in text.lower() and server:
            # manual case-insensitive replace
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            text = pattern.sub(server, text)
    return _expand_env(text, env)


def default_package_store_unc(empirum_server: str = "") -> str:
    server = empirum_server.strip() or "%EmpirumServer%"
    return f"\\\\{server}\\Configurator$\\PackageStore"


def validate_package_dir(package_dir: Path) -> PackageLayout:
    root = Path(package_dir)
    if root.is_file() and root.name.lower() == "setup.inf":
        # Allow pointing at Setup.inf → package root is parent of Install
        if root.parent.name.lower() == "install":
            root = root.parent.parent
        else:
            raise PackageStoreError("Setup.inf muss unter <Paket>\\Install\\ liegen")
    setup = root / "Install" / "Setup.inf"
    if not setup.is_file():
        raise PackageStoreError(f"Kein Empirum-Paket: fehlt {setup}")
    return PackageLayout(
        package_dir=root.resolve(),
        setup_inf=setup.resolve(),
        has_files_dir=(root / "Files").is_dir(),
    )


def _safe_segment(value: str, fallback: str) -> str:
    cleaned = _SAFE.sub("_", value).strip().replace(" ", "_")
    # Trailing dots/spaces are dropped by Windows and would shift the path.
    cleaned = cleaned.rstrip(".")
    if cleaned in {"", ".", ".."} or cleaned.upper() in _RESERVED_SEGMENT_NAMES:
        return fallback
    return cleaned


def build_destination(
    store_root: Path,
    *,
    package_dir: Path,
    manufacturer: str = "",
    product: str = "",
    version: str = "",
    mode: DeployMode = DeployMode.VENDOR_PRODUCT_VERSION,
) -> Path:
    name = package_dir.name
    # Heuristic: Product_1.0.0
    prod = product or name
    ver = version
    if not version and "_" in name:
        maybe_prod, maybe_ver = name.rsplit("_", 1)
        if maybe_ver and maybe_ver[0].isdigit():
            prod = product or maybe_prod
            ver = maybe_ver
    prod = _safe_segment(prod, "Package")
    ver = _safe_segment(ver or "1.0.0", "1.0.0")
    mfr = _safe_segment(manufacturer or "Vendor", "Vendor")

    if mode == DeployMode.FLAT:
        return store_root / f"{prod}_{ver}"
    return store_root / mfr / prod / ver


def plan_deploy(
    package_dir: Path,
    store_root: str | Path,
    *,
    manufacturer: str = "",
    product: str = "",
    version: str = "",
    mode: DeployMode = DeployMode.VENDOR_PRODUCT_VERSION,
    overwrite: bool = False,
    empirum_server: str = "",
    require_free_target: bool = True,
) -> DeployPlan:
    layout = validate_package_dir(package_dir)
    expanded = expand_empirum_path(str(store_root), empirum_server=empirum_server)
    root = Path(expanded)
    destination = build_destination(
        root,
        package_dir=layout.package_dir,
        manufacturer=manufacturer,
        product=product,
        version=version,
        mode=mode,
    )
    _ensure_within_store(destination, root)
    if require_free_target and destination.exists() and not overwrite:
        raise PackageStoreError(
            f"Ziel existiert bereits: {destination} (Overwrite aktivieren oder löschen)"
        )
    return DeployPlan(
        source=layout.package_dir,
        destination=destination,
        mode=mode,
        overwrite=overwrite,
    )


def deploy_to_package_store(
    package_dir: Path,
    store_root: str | Path,
    *,
    manufacturer: str = "",
    product: str = "",
    version: str = "",
    mode: DeployMode = DeployMode.VENDOR_PRODUCT_VERSION,
    overwrite: bool = False,
    empirum_server: str = "",
    dry_run: bool = False,
) -> DeployResult:
    plan = plan_deploy(
        package_dir,
        store_root,
        manufacturer=manufacturer,
        product=product,
        version=version,
        mode=mode,
        overwrite=overwrite,
        empirum_server=empirum_server,
        require_free_target=not dry_run,
    )
    if dry_run:
        warn = ""
        if plan.destination.exists() and not overwrite:
            warn = " (WARNUNG: Ziel existiert – für echtes Deploy Overwrite nötig)"
        return DeployResult(
            destination=plan.destination,
            copied_files=0,
            dry_run=True,
            message=f"Dry-Run: würde nach {plan.destination} kopieren{warn}",
        )

    parent = plan.destination.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PackageStoreError(
            f"PackageStore nicht erreichbar ({plan.destination}): {exc}"
        ) from exc

    if plan.destination.exists():
        if not plan.overwrite:
            # Target appeared between planning and execution (TOCTOU).
            raise PackageStoreError(
                f"Ziel existiert bereits: {plan.destination} (Overwrite aktivieren oder löschen)"
            )
        try:
            shutil.rmtree(plan.destination, onexc=_rmtree_readonly_retry)
        except OSError as exc:
            raise PackageStoreError(
                f"Ziel konnte nicht gelöscht werden ({plan.destination}): {exc}"
            ) from exc

    ignore = shutil.ignore_patterns(".emp_packagex3_bak", "*.tmp", "__pycache__")
    shutil.copytree(plan.source, plan.destination, ignore=ignore)
    count = sum(1 for p in plan.destination.rglob("*") if p.is_file())
    return DeployResult(
        destination=plan.destination,
        copied_files=count,
        dry_run=False,
        message=(
            f"{count} Dateien nach {plan.destination} kopiert. "
            "Als Nächstes in der Empirum Management Console: "
            "Software-Register → Paket aus PackageStore importieren."
        ),
    )
