"""Inspector package exports."""

from empirum_infra.inspectors.msi import inspect_msi
from empirum_infra.inspectors.pe import inspect_pe

__all__ = ["inspect_msi", "inspect_pe"]
