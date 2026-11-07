"""Safe file writes with WAL-style backup (plan risk R-02)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WriteResult:
    path: Path
    backup_path: Path | None
    bytes_written: int


def write_bytes_with_backup(
    path: Path,
    data: bytes,
    *,
    backup_dir: Path | None = None,
) -> WriteResult:
    """Write atomically via temp file; keep timestamped backup if target exists."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if path.is_file():
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        bdir = backup_dir or (path.parent / ".emp_packagex3_bak")
        bdir.mkdir(parents=True, exist_ok=True)
        backup = bdir / f"{path.name}.{stamp}.bak"
        collision = 1
        while backup.exists():  # two saves within the same second must not overwrite
            backup = bdir / f"{path.name}.{stamp}.{collision}.bak"
            collision += 1
        shutil.copy2(path, backup)
    # PID suffix keeps concurrent writers (second editor instance) apart.
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return WriteResult(path=path, backup_path=backup, bytes_written=len(data))
