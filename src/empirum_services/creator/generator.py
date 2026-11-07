"""Package generation: folders + Setup.inf from metadata/templates."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from empirum_core.inspect import PackageMetadata
from empirum_core.linter import Diagnostic, lint_document
from empirum_core.serializer.serialize import serialize_to_bytes
from empirum_core.templates import render_template
from empirum_infra.fs_safe import write_bytes_with_backup


@dataclass(slots=True)
class GenerateResult:
    package_dir: Path
    setup_inf: Path
    diagnostics: list[Diagnostic]
    warnings: list[str] = field(default_factory=list)


def inspect_source(path: str | Path) -> PackageMetadata:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".msi":
        from empirum_infra.inspectors.msi import inspect_msi

        return inspect_msi(file_path)
    if suffix in {".exe", ".dll"}:
        from empirum_infra.inspectors.pe import inspect_pe

        return inspect_pe(file_path)
    meta = PackageMetadata(
        product_name=file_path.stem,
        package_type="Script",
        source_path=str(file_path.resolve()),
    )
    return meta


def generate_package(
    meta: PackageMetadata,
    target_root: str | Path,
    *,
    kind: str | None = None,
    copy_source: bool = True,
) -> GenerateResult:
    root = Path(target_root)
    safe_name = _safe_dir_name(meta.product_name or "Package")
    # Version comes from foreign file metadata – sanitize like the name.
    safe_version = _safe_dir_name(meta.product_version or "1.0.0")
    package_dir = root / f"{safe_name}_{safe_version}"
    install_dir = package_dir / "Install"
    files_dir = package_dir / "Files"
    install_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    # If reg_files requested conversion to [Reg:Product], parse and add before template rendering
    for rf in list(meta.reg_files):
        if rf.import_mode == "convert" and rf.local_source_path:
            src_rf = Path(rf.local_source_path)
            if src_rf.is_file():
                from empirum_core.parser.reg_parser import parse_reg_file

                parsed = parse_reg_file(src_rf)
                meta.registry_entries.extend(parsed)
            else:
                warnings.append(
                    f"Zu konvertierende .reg-Datei nicht gefunden: {src_rf}"
                )

    tmpl = kind or meta.package_type or "Script"
    doc = render_template(tmpl, meta)
    setup_inf = install_dir / "Setup.inf"
    # Empirum/Standard: CRLF + Windows-1252 (ANSI), no BOM (Setup.exe/Package Editor).
    # WAL backup keeps the previous Setup.inf when regenerating into an existing package.
    write_bytes_with_backup(setup_inf, serialize_to_bytes(doc))

    if copy_source and meta.source_path:
        src = Path(meta.source_path)
        if src.is_file():
            shutil.copy2(src, files_dir / src.name)
        else:
            warnings.append(
                f"Quell-Installer nicht gefunden: {src} – Files\\ bleibt leer, "
                "Paket ist ohne Payload nicht deploybar"
            )

    # Process folder copies
    for fc in meta.folder_copies:
        target_sub = files_dir / fc.folder_name
        target_sub.mkdir(parents=True, exist_ok=True)
        if fc.local_source_path:
            src_fc = Path(fc.local_source_path)
            if src_fc.is_dir():
                shutil.copytree(src_fc, target_sub, dirs_exist_ok=True)
            else:
                warnings.append(
                    f"Quellordner nicht gefunden: {src_fc} – Files\\{fc.folder_name} bleibt leer"
                )

    # Process .reg files deployment
    for rf in meta.reg_files:
        if rf.import_mode == "reg_exe":
            sub_name = rf.target_subfolder.strip()
            sub_dir = files_dir / sub_name if sub_name else files_dir
            sub_dir.mkdir(parents=True, exist_ok=True)
            if rf.local_source_path:
                src_rf = Path(rf.local_source_path)
                if src_rf.is_file():
                    shutil.copy2(src_rf, sub_dir / rf.file_name)
                else:
                    warnings.append(
                        f"Registry-Datei nicht gefunden: {src_rf} – "
                        f"Files\\{sub_name}\\{rf.file_name} fehlt"
                    )


    diagnostics = lint_document(doc)
    return GenerateResult(
        package_dir=package_dir,
        setup_inf=setup_inf,
        diagnostics=diagnostics,
        warnings=warnings,
    )



def _safe_dir_name(name: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip()
    return cleaned.replace(" ", "_") or "Package"
