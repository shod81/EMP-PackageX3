"""Update check: local file depot now, HTTP/HTTPS later via same setting."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Pre-release identifier ordering: dev < alpha < beta < rc < final.
_PRE_RELEASE_RANK = {"dev": 0, "alpha": 1, "a": 1, "beta": 2, "b": 2, "rc": 3, "c": 3, "pre": 3}
_UNKNOWN_PRE_RANK = 2
_IDENTIFIER_RE = re.compile(r"([a-z]*)(\d*)")


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    current: str
    latest: str
    notes: str
    download_url: str
    update_available: bool
    source: str = ""


def _release_numbers(version: str) -> tuple[int, ...]:
    numbers: list[int] = []
    for chunk in version.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        if digits:
            numbers.append(int(digits))
    return tuple(numbers) or (0,)


def _identifier_key(identifier: str) -> tuple[int, int, str]:
    match = _IDENTIFIER_RE.match(identifier)
    name = match.group(1) if match else ""
    digits = match.group(2) if match else ""
    number = int(digits) if digits else 0
    rank = _PRE_RELEASE_RANK.get(name, _UNKNOWN_PRE_RANK)
    return (rank, number, name)


def version_sort_key(
    version: str,
) -> tuple[tuple[int, ...], int, tuple[tuple[int, int, str], ...]]:
    """Sort key with semver-like pre-release semantics (rc2 < 1.0.0 final)."""
    text = version.strip().lower()
    main, _, suffix = text.partition("-")
    release = _release_numbers(main)
    is_final = not suffix
    pre = () if is_final else tuple(_identifier_key(part) for part in suffix.split(".") if part)
    return (release, 1 if is_final else 0, pre)


def compare_versions(current: str, latest: str) -> int:
    a = version_sort_key(current)
    b = version_sort_key(latest)
    n = max(len(a[0]), len(b[0]))
    a = (a[0] + (0,) * (n - len(a[0])), a[1], a[2])
    b = (b[0] + (0,) * (n - len(b[0])), b[1], b[2])
    return (a > b) - (a < b)


def check_update_from_json(manifest: dict[str, object], current: str) -> UpdateInfo:
    latest = str(manifest.get("version", current))
    notes = str(manifest.get("notes", ""))
    download_url = str(manifest.get("download_url", ""))
    available = compare_versions(current, latest) < 0
    return UpdateInfo(
        current=current,
        latest=latest,
        notes=notes,
        download_url=download_url,
        update_available=available,
    )


# Manifests are small JSON files – 1 MiB is a generous ceiling against
# corrupted or hostile responses being pulled fully into memory.
_MAX_MANIFEST_BYTES = 1 << 20


def load_manifest(location: str, *, timeout: float = 5.0) -> dict[str, object]:
    loc = location.strip()
    if not loc:
        raise ValueError("empty manifest location")
    if loc.lower().startswith(("http://", "https://")):
        # http stays allowed for intranet depots; prefer https in production.
        request = urllib.request.Request(loc, headers={"User-Agent": "EMP-PackageX3"})
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = response.read(_MAX_MANIFEST_BYTES).decode("utf-8-sig")
        data = json.loads(payload)
    else:
        path = Path(loc)
        if path.is_dir():
            path = path / "VERSION.json"
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    return data


def check_update(location: str, current: str, *, timeout: float = 5.0) -> UpdateInfo:
    if not location.strip():
        return UpdateInfo(
            current=current,
            latest=current,
            notes="Kein Depot/Manifest konfiguriert.",
            download_url="",
            update_available=False,
            source="",
        )
    try:
        manifest = load_manifest(location, timeout=timeout)
        info = check_update_from_json(manifest, current)
        return UpdateInfo(
            current=info.current,
            latest=info.latest,
            notes=info.notes,
            download_url=info.download_url,
            update_available=info.update_available,
            source=location,
        )
    except (
        urllib.error.URLError,
        TimeoutError,
        ValueError,
        json.JSONDecodeError,
        OSError,
    ) as exc:
        return UpdateInfo(
            current=current,
            latest=current,
            notes=f"Update-Check fehlgeschlagen: {exc}",
            download_url="",
            update_available=False,
            source=location,
        )


def utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
