"""Pre-deploy / package readiness checks for Empirum packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from empirum_core.ast.model import KeyValueLine
from empirum_core.linter import Diagnostic, Severity, lint_document
from empirum_core.linter.engine import SRCDIR_ALLOWED_VALUES
from empirum_core.parser.encoding import decode_bytes
from empirum_core.parser.lexer import lex_text
from empirum_core.quoting.quote import Quoter
from empirum_core.serializer.serialize import serialize_to_bytes
from empirum_core.skeleton_repair import add_missing_standard_sections
from empirum_infra.fs_safe import write_bytes_with_backup
from empirum_services.app_paths import app_data_dir
from empirum_services.package_store import PackageStoreError, validate_package_dir


class ReadinessLevel(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(slots=True)
class ReadinessItem:
    level: ReadinessLevel
    code: str
    message: str


@dataclass(slots=True)
class PackageReadinessReport:
    package_dir: Path
    setup_inf: Path
    has_files_dir: bool
    items: list[ReadinessItem] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def level(self) -> ReadinessLevel:
        # ERROR diagnostics must never be masked by WARN items (deploy safety).
        if any(i.level == ReadinessLevel.FAIL for i in self.items):
            return ReadinessLevel.FAIL
        if any(d.severity == Severity.ERROR for d in self.diagnostics):
            return ReadinessLevel.FAIL
        if any(i.level == ReadinessLevel.WARN for i in self.items):
            return ReadinessLevel.WARN
        if any(d.severity == Severity.WARNING for d in self.diagnostics):
            return ReadinessLevel.WARN
        return ReadinessLevel.OK

    @property
    def ok_to_deploy(self) -> bool:
        return self.level != ReadinessLevel.FAIL

    def summary_lines(self) -> list[str]:
        lines = [
            f"Paket: {self.package_dir}",
            f"Setup.inf: {self.setup_inf}",
            f"Files\\: {'ja' if self.has_files_dir else 'fehlt'}",
            f"Gesamt: {self.level.value.upper()}",
        ]
        for item in self.items:
            lines.append(f"[{item.level.value}] {item.code}: {item.message}")
        errors = [d for d in self.diagnostics if d.severity == Severity.ERROR]
        warns = [d for d in self.diagnostics if d.severity == Severity.WARNING]
        if errors:
            lines.append(f"Lint-Fehler: {len(errors)}")
            for d in errors[:12]:
                loc = f" Z{d.line}" if d.line else ""
                lines.append(f"  {d.code}{loc}: {d.message}")
        if warns:
            lines.append(f"Lint-Warnungen: {len(warns)}")
            for d in warns[:8]:
                loc = f" Z{d.line}" if d.line else ""
                lines.append(f"  {d.code}{loc}: {d.message}")
        return lines


def check_package_readiness(package_dir: Path) -> PackageReadinessReport:
    """Validate Empirum folder layout + lint Setup.inf before PackageStore deploy."""
    try:
        layout = validate_package_dir(package_dir)
    except PackageStoreError as exc:
        root = Path(package_dir)
        return PackageReadinessReport(
            package_dir=root,
            setup_inf=root / "Install" / "Setup.inf",
            has_files_dir=False,
            items=[
                ReadinessItem(
                    ReadinessLevel.FAIL,
                    "PKG-001",
                    str(exc),
                )
            ],
        )

    report = PackageReadinessReport(
        package_dir=layout.package_dir,
        setup_inf=layout.setup_inf,
        has_files_dir=layout.has_files_dir,
    )
    if not layout.has_files_dir:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.WARN,
                "PKG-002",
                "Ordner Files\\ fehlt – Payload oft unter %Src%\\Files\\ erwartet",
            )
        )

    try:
        data = layout.setup_inf.read_bytes()
        text, detected = decode_bytes(data)
        doc = lex_text(text, encoding_name=detected.name)
        doc.has_bom = detected.has_bom
    except OSError as exc:
        report.items.append(
            ReadinessItem(ReadinessLevel.FAIL, "PKG-003", f"Setup.inf nicht lesbar: {exc}")
        )
        return report
    except UnicodeDecodeError as exc:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.FAIL,
                "PKG-011",
                f"Setup.inf Encoding (nicht ANSI/CP1252 bei Offset {exc.start}): {exc}",
            )
        )
        return report

    report.diagnostics = lint_document(doc)

    if detected.has_bom:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.FAIL,
                "PKG-009",
                (
                    "Setup.inf beginnt mit einem Byte Order Mark "
                    "(BOM: EF BB BF / FF FE / FE FF) – der native Empirum-Interpreter "
                    "(Setup.exe) bricht ab und der Package Editor kann die Datei nicht parsen. "
                    "Bitte als ANSI / Windows-1252 ohne BOM speichern."
                ),
            )
        )
    elif detected.name.casefold() not in {"cp1252", "windows-1252", "ansi"}:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.WARN,
                "PKG-010",
                (
                    f"Setup.inf ist als '{detected.name}' kodiert – "
                    "Empirum-Standard ist Windows-1252 (ANSI). "
                    "Umlaute und Sonderzeichen können als Mojibake dargestellt werden."
                ),
            )
        )

    try:
        data.decode("cp1252")
    except UnicodeDecodeError as exc:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.FAIL,
                "PKG-011",
                (
                    f"Setup.inf enthält bei Byte-Offset {exc.start} "
                    f"nicht-CP1252-konforme Bytes: {exc.reason}. "
                    "Empirum erwartet reines Windows-1252 (ANSI)."
                ),
            )
        )

    # Explicit path contract (also covered by VAL-015 when Application present)
    app = doc.section("Application")
    if app is None:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.FAIL,
                "PKG-004",
                "[Application] fehlt – kein gültiges Empirum-Paket",
            )
        )
    else:
        keys = {
            n.key.casefold(): Quoter.strip_optional_quotes(n.value).strip()
            for n in app.lines
            if isinstance(n, KeyValueLine)
        }
        src = keys.get("srcdir", "")
        if src and src not in SRCDIR_ALLOWED_VALUES:
            report.items.append(
                ReadinessItem(
                    ReadinessLevel.FAIL,
                    "PKG-005",
                    f"SrcDir={src!r} – erwartet '..' (Paketwurzel = Parent von Install)",
                )
            )
        sif = keys.get("setupinfdir", "")
        if sif and sif.casefold() != "install":
            report.items.append(
                ReadinessItem(
                    ReadinessLevel.FAIL,
                    "PKG-006",
                    f"SetupInfDir={sif!r} – erwartet 'Install'",
                )
            )

    aw_diags = [d for d in report.diagnostics if d.code == "VAL-006"]
    if aw_diags:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.WARN,
                "PKG-007",
                "Benutzerteil erkannt ohne /AW in SetupInfo – Depot-Befehl ebenfalls /AW setzen",
            )
        )
    elif any(
        d.code == "VAL-017" for d in report.diagnostics
    ):
        report.items.append(
            ReadinessItem(
                ReadinessLevel.WARN,
                "PKG-008",
                (
                    "SetupInfo enthält /AW – im Software-Depot unter "
                    "Prüfung→Befehl ebenfalls /AW pflegen"
                ),
            )
        )

    if report.level == ReadinessLevel.OK:
        report.items.append(
            ReadinessItem(
                ReadinessLevel.OK,
                "PKG-000",
                "Paketstruktur und Lint ohne Fehler – Deploy möglich",
            )
        )
    return report


@dataclass(slots=True)
class SkeletonRepairResult:
    """Outcome of an on-disk standard skeleton repair."""

    package_dir: Path
    setup_inf: Path
    added_sections: list[str]
    added_refs: list[str]
    backup_path: Path | None
    bom_stripped: bool = False


def default_repair_backup_dir(package_dir: Path) -> Path:
    """External WAL backup folder for a package repair (M-3).

    ``<LOCALAPPDATA>\\HodriusSystems\\EMP-PackageX3\\backups\\<Paketname>``.

    Deliberately outside the package: an in-package ``.emp_packagex3_bak`` would
    be deployed to the PackageStore (only ``deploy_package`` filters it) and the
    package root itself may be read-only (Configurator$ share / UNC). Shares the
    ``app_paths.app_data_dir()`` base with the settings and log folders.
    """
    return app_data_dir() / "backups" / Path(package_dir).name


def repair_missing_standard_sections(
    package_dir: Path,
    *,
    add_product_refs: bool = True,
    backup_dir: Path | None = None,
    strip_bom: bool = True,
) -> SkeletonRepairResult:
    """Add missing standard sections to the package's Setup.inf on disk.

    Encoding/BOM/newline of the existing file are preserved unless strip_bom is True
    (a UTF-8 BOM is stripped and normalized to Windows-1252 for Empirum runtime compatibility).
    The previous file is kept as WAL backup in ``default_repair_backup_dir`` (i.e.
    outside the package – see M-3); pass ``backup_dir`` to override. Readiness itself
    stays read-only - re-run ``check_package_readiness`` afterwards.
    """
    layout = validate_package_dir(package_dir)
    data = layout.setup_inf.read_bytes()
    text, detected = decode_bytes(data)
    doc = lex_text(text, encoding_name=detected.name)
    doc.has_bom = detected.has_bom

    bom_stripped = False
    if strip_bom and doc.has_bom:
        doc.has_bom = False
        doc.encoding_name = "cp1252"
        bom_stripped = True

    repair = add_missing_standard_sections(doc, add_product_refs=add_product_refs)
    backup_path: Path | None = None
    if repair.added_sections or repair.added_refs or bom_stripped:
        result = write_bytes_with_backup(
            layout.setup_inf,
            serialize_to_bytes(doc),
            backup_dir=backup_dir or default_repair_backup_dir(layout.package_dir),
        )
        backup_path = result.backup_path
    return SkeletonRepairResult(
        package_dir=layout.package_dir,
        setup_inf=layout.setup_inf,
        added_sections=repair.added_sections,
        added_refs=repair.added_refs,
        backup_path=backup_path,
        bom_stripped=bom_stripped,
    )
