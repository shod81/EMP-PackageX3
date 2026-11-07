"""Binary inspection results shared across MSI/PE/EXE."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FolderCopySpec:
    """Specification for copying folders via cmd /c xcopy."""

    folder_name: str = ""
    target_path: str = ""
    local_source_path: str = ""
    xcopy_flags: str = "/S /H /E /V /Y"
    delete_on_uninstall: bool = True


@dataclass(slots=True)
class RegistryEntrySpec:
    """Specification for single registry entries in [Reg:Product]."""

    root: str = "HKLM"  # HKLM | HKCU | HKCR
    key_path: str = ""
    value_name: str = ""
    reg_type: str = "REG_SZ"  # REG_SZ | REG_DWORD | REG_EXPAND_SZ | REG_BINARY | REG_MULTI_SZ
    value_data: str = ""
    delete_on_uninstall: bool = False


@dataclass(slots=True)
class RegFileSpec:
    """Specification for importing or converting .reg files."""

    file_name: str = ""
    local_source_path: str = ""
    import_mode: str = "reg_exe"  # reg_exe | convert
    target_subfolder: str = "Reg"


@dataclass(slots=True)
class ShellLinkSpec:
    """Specification for shortcuts in [Shell:Product]."""

    # common_programs → %CommonPrograms% (All Users Startmenü\Programme)
    # common_desktop  → %CommonDesktop%  (All Users Desktop)
    destination: str = "common_programs"
    name: str = ""
    subfolder: str = ""
    target: str = ""
    arguments: str = ""
    working_dir: str = ""
    description: str = ""
    icon_file: str = ""
    icon_index: int = 0
    window_state: int = 1


@dataclass(slots=True)
class PackageMetadata:
    """Normalized metadata for wizard / template instantiation."""

    product_name: str = ""
    product_version: str = ""
    manufacturer: str = ""
    product_code: str = ""
    upgrade_code: str = ""
    package_type: str = "Unknown"  # MSI | EXE | Script | Links
    architecture: str = "x64"  # x86 | x64 | ARM64 | Any
    source_path: str = ""
    exe_kind: str = ""  # Inno | NSIS | InstallShield | Generic | ""
    properties: dict[str, str] = field(default_factory=dict)
    folder_copies: list[FolderCopySpec] = field(default_factory=list)
    registry_entries: list[RegistryEntrySpec] = field(default_factory=list)
    reg_files: list[RegFileSpec] = field(default_factory=list)
    shell_links: list[ShellLinkSpec] = field(default_factory=list)
    # User-part commands (per-user context). Empty list =
    # pure machine package. Non-empty: commands are emitted into [Set:Client]
    # (CLIENT flag) and machine [Product] entries get the MACHINE flag.
    user_context_commands: list[str] = field(default_factory=list)

    @property
    def has_user_part(self) -> bool:
        """True when the package carries a real user part (CLIENT section)."""
        return bool(self.user_context_commands)

    def display_label(self) -> str:
        bits = [self.product_name or "(unnamed)", self.product_version, self.package_type]
        return " · ".join(p for p in bits if p)

