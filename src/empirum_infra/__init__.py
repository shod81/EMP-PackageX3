"""Infrastructure adapters (filesystem, COM, process runner, inspectors)."""

from empirum_infra.fs_safe import WriteResult, write_bytes_with_backup
from empirum_infra.inspectors import inspect_msi, inspect_pe

__all__ = ["WriteResult", "inspect_msi", "inspect_pe", "write_bytes_with_backup"]
