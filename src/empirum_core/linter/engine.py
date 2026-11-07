"""Linter engine and built-in VAL rules (see builtin_rules for the full set)."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from empirum_core.ast.model import CommentLine, Document, KeyValueLine, LineNode, RawLine, Section
from empirum_core.parser import work as W
from empirum_core.quoting.quote import Quoter
from empirum_core.setupinf_contract import (
    APPLICATION_KEYS,
    ERROR_SECTION_BODIES,
    MSI_INSTALL_FLAGS,
    SETUPINF_COMMANDS,
    SETUPINF_COMMANDS_UNDOCUMENTED,
    SETUPINF_FUNCTIONS,
    SETUPINF_REG_TYPES,
    SETUPINF_VARIABLES,
    SETUPINF_VARIABLES_UNDOCUMENTED,
    STANDARD_SECTIONS,
)


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class QuickFix:
    id: str
    title: str
    replacement_line: str | None = None
    note: str | None = None
    # Set for ``note="insert_section"``: the section the fix creates. Kept as an
    # explicit field so the apply path never parses the display text.
    section_name: str | None = None


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: Severity
    message: str
    line: int | None = None
    column: int | None = None
    quick_fixes: tuple[QuickFix, ...] = ()


class LinterRule(Protocol):
    code: str
    severity: Severity

    def check(self, document: Document) -> list[Diagnostic]: ...


@dataclass(slots=True)
class Rule:
    code: str
    severity: Severity
    check_fn: Callable[[Document], list[Diagnostic]]

    def check(self, document: Document) -> list[Diagnostic]:
        return self.check_fn(document)


def lint_document(
    document: Document,
    *,
    rules: list[Rule] | None = None,
    options: LintOptions | None = None,
) -> list[Diagnostic]:
    opts = options if options is not None else LintOptions()
    active = rules if rules is not None else builtin_rules(opts)
    findings: list[Diagnostic] = []
    for rule in active:
        findings.extend(rule.check(document))
    findings.sort(key=lambda d: (d.line or 0, d.code))
    return findings


@dataclass(frozen=True, slots=True)
class LintOptions:
    """Feature gating for lint rules (fed from the app settings).

    undocumented_commands: class-1 undocumented commands/variables (verified
    26.1.0, absent from all official docs) count as known when enabled.
    """

    undocumented_commands: bool = False


def builtin_rules(options: LintOptions | None = None) -> list[Rule]:
    opts = options if options is not None else LintOptions()
    return [
        Rule("VAL-001", Severity.ERROR, _val_001),
        Rule("VAL-002", Severity.ERROR, _val_002),
        Rule("VAL-003", Severity.ERROR, _val_003),
        Rule("VAL-004", Severity.ERROR, _val_004),
        Rule("VAL-005", Severity.WARNING, _val_005),
        Rule("VAL-006", Severity.WARNING, _val_006),
        Rule("VAL-007", Severity.WARNING, _val_007),
        Rule("VAL-008", Severity.WARNING, _val_008),
        Rule("VAL-009", Severity.WARNING, _val_009),
        Rule("VAL-010", Severity.INFO, _val_010),
        Rule("VAL-011", Severity.INFO, _val_011),
        Rule("VAL-012", Severity.ERROR, _val_012),
        Rule("VAL-013", Severity.ERROR, _val_013),
        Rule("VAL-014", Severity.ERROR, _val_014),
        Rule("VAL-015", Severity.ERROR, _val_015),
        Rule("VAL-016", Severity.WARNING, _val_016),
        Rule("VAL-017", Severity.INFO, _val_017),
        Rule("VAL-018", Severity.INFO, _val_018),
        Rule("VAL-019", Severity.WARNING, lambda doc: _val_019(doc, opts)),
        Rule("VAL-020", Severity.ERROR, _val_020),
        Rule("VAL-021", Severity.WARNING, lambda doc: _val_021(doc, opts)),
        Rule("VAL-022", Severity.ERROR, _val_022),
        Rule("VAL-023", Severity.WARNING, _val_023),
        Rule("VAL-024", Severity.WARNING, _val_024),
        Rule("VAL-025", Severity.ERROR, _val_025),
        Rule("VAL-026", Severity.ERROR, _val_026),
        Rule("VAL-027", Severity.WARNING, _val_027),
        Rule("VAL-028", Severity.WARNING, _val_028),
        Rule("VAL-029", Severity.WARNING, _val_029),
        Rule("VAL-030", Severity.ERROR, _val_030),
        Rule("VAL-031", Severity.ERROR, _val_031),
        Rule("VAL-032", Severity.ERROR, _val_032),
        Rule("VAL-033", Severity.ERROR, _val_033),
        Rule("VAL-034", Severity.WARNING, _val_034),
    ]


def _line_of(kv: KeyValueLine) -> int | None:
    return kv.span.start_line if kv.span else None


def _val_001(document: Document) -> list[Diagnostic]:
    known = W.section_names(document)
    out: list[Diagnostic] = []
    seen: set[tuple[str, str, int]] = set()
    for ref in W.find_section_refs(document):
        if W.section_ref_exists(ref, known):
            continue
        key = (ref.kind, ref.name.casefold(), ref.line)
        if key in seen:
            continue  # same target repeated on one line -> one diagnostic
        seen.add(key)
        stub_name = W.preferred_stub_section(ref)
        stub = f"[{stub_name}]"
        label = f"#{ref.kind}:{ref.name}" if ref.kind else f"#{ref.name}"
        out.append(
            Diagnostic(
                code="VAL-001",
                severity=Severity.ERROR,
                message=f"Sektionsverweis {label} zeigt auf fehlende Sektion",
                line=ref.line,
                quick_fixes=(
                    QuickFix(
                        id="VAL-001.stub",
                        title=f"Stub-Sektion {stub} anlegen",
                        note="insert_section",
                        replacement_line=stub,
                    ),
                ),
            )
        )
    return out


def _val_002(document: Document) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for _section, kv in W.kv_pairs(document):
        if not W.looks_like_if_key(kv.key):
            continue
        if W.if_predicate_is_quoted_function(kv.value):
            fixed = kv.value
            if kv.value.startswith('"') and kv.value.endswith('"') and len(kv.value) >= 2:
                fixed = kv.value[1:-1]
            elif kv.value.startswith('"'):
                fixed = kv.value[1:]
            quick_fixes: tuple[QuickFix, ...] = ()
            if fixed != kv.value:
                quick_fixes = (
                    QuickFix(
                        id="VAL-002.unquote",
                        title="Äußere Anführungszeichen entfernen",
                        replacement_line=f"{kv.key}={fixed}",
                    ),
                )
            out.append(
                Diagnostic(
                    code="VAL-002",
                    severity=Severity.ERROR,
                    message="Funktionsprädikat in If ist gequotet (String-Vergleich-Falle)",
                    line=_line_of(kv),
                    quick_fixes=quick_fixes,
                )
            )
    return out


def _val_003(document: Document) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for _section, kv in W.kv_pairs(document):
        if kv.key.casefold() != "deltree":
            continue
        value = Quoter.strip_optional_quotes(kv.value)
        if value.endswith("\\") or value.endswith("/"):
            fixed_val = value.rstrip("\\/")
            was_quoted = kv.value.startswith('"') and kv.value.endswith('"')
            new_value = f'"{fixed_val}"' if was_quoted else fixed_val
            out.append(
                Diagnostic(
                    code="VAL-003",
                    severity=Severity.ERROR,
                    message="DelTree-Argument endet mit Backslash",
                    line=_line_of(kv),
                    quick_fixes=(
                        QuickFix(
                            id="VAL-003.strip",
                            title="Abschließenden Backslash entfernen",
                            replacement_line=f"{kv.key}={new_value}",
                        ),
                    ),
                )
            )
    return out


_ABORT_KEYS = frozenset({"abort", "errorlogmsg"})


def _val_004(document: Document) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for section, kv in W.kv_pairs(document):
        if section is None or not W.is_uninstall_error_section(section.name):
            continue
        key = kv.key
        if key.startswith("--"):
            continue
        base = key[1:] if key.startswith("-") and not key.startswith("--") else key
        if base.casefold() not in _ABORT_KEYS:
            continue
        out.append(
            Diagnostic(
                code="VAL-004",
                severity=Severity.ERROR,
                message=f"{key} in Deinstallations-Fehlersektion ohne --Präfix",
                line=_line_of(kv),
                quick_fixes=(
                    QuickFix(
                        id="VAL-004.prefix",
                        title="--Präfix ergänzen",
                        replacement_line=f"--{base}={kv.value}",
                    ),
                ),
            )
        )
    return out


def _node_text(node: KeyValueLine | RawLine | CommentLine) -> str | None:
    if isinstance(node, CommentLine):
        return None
    if isinstance(node, RawLine):
        return node.text
    return node.raw or f"{node.key}={node.value}"


_COMMAND_KEYS = frozenset({"call", "callhidden", "run", "msiexec"})
_RAW_COMMAND_RE = re.compile(r"(?i)^-?(callhidden|call|run|msiexec)\b")


def _command_statement(node: object) -> tuple[str, str] | None:
    """Unified command projection: Key=Value style AND RawLine command style.

    Returns (verb, text) for Call/CallHidden/Run/MsiExec statements, else None.
    """
    if isinstance(node, KeyValueLine):
        if node.key.casefold() in _COMMAND_KEYS:
            return node.key.casefold(), node.raw or f"{node.key}={node.value}"
        return None
    if isinstance(node, RawLine):
        text = node.text.strip()
        match = _RAW_COMMAND_RE.match(text)
        if match:
            return match.group(1).casefold(), text
    return None


def _val_005(document: Document) -> list[Diagnostic]:
    product = document.section("Product")
    app = document.section("Application")
    if product is None:
        return []
    shell_links_on = False
    if app is not None:
        for node in app.lines:
            if isinstance(node, KeyValueLine) and node.key.casefold() == "shelllinks":
                shell_links_on = (
                    Quoter.strip_optional_quotes(node.value).strip().casefold()
                    in {"1", "yes", "true", "on"}
                )
    if not shell_links_on:
        return []
    out: list[Diagnostic] = []
    for node in product.lines:
        text = _node_text(node)
        if text is None:
            continue
        if re.search(r"#Shell\s*:", text, re.IGNORECASE):
            out.append(
                Diagnostic(
                    code="VAL-005",
                    severity=Severity.WARNING,
                    message=(
                        "ShellLinks=1 und #Shell:… in [Product] erzeugen Doppelverknüpfungen"
                    ),
                    line=node.span.start_line if node.span else None,
                    quick_fixes=(
                        QuickFix(
                            id="VAL-005.drop_ref",
                            title="#Shell-Referenz aus [Product] entfernen",
                            note="delete_line",
                        ),
                        QuickFix(
                            id="VAL-005.disable",
                            title="ShellLinks=0 setzen",
                            replacement_line="ShellLinks=0",
                            note="set_application_key",
                        ),
                    ),
                )
            )
    return out


def _setupinfo_cmdline(document: Document) -> tuple[str, int | None, str]:
    """Return (value, line, found key) for SetupInfo command-line options.

    standard key is "Command line options"; legacy files may use CmdLine etc.
    The found key is preserved so quick-fixes do not silently rename it.
    """
    setup = document.section("SetupInfo")
    if setup is None:
        return "", None, "Command line options"
    for node in setup.lines:
        if isinstance(node, KeyValueLine):
            key = re.sub(r"[\s_]+", "", node.key.casefold())
            if key in {"commandlineoptions", "cmdline", "options"}:
                return node.value, _line_of(node), node.key
        elif isinstance(node, RawLine):
            text = node.text.strip()
            m = re.match(
                r"(?i)^(command\s*line\s*options|commandlineoptions|cmdline)\s*=\s*(.*)$",
                text,
            )
            if m:
                line_no = node.span.start_line if node.span else None
                return m.group(2), line_no, m.group(1)
    return "", None, "Command line options"


def _needs_user_part(document: Document) -> bool:
    """True when package likely requires Empirum user part (/AW).

    Only ACTIVE lines count – commented-out placeholders are not features.
    """
    for loc in W.iter_located(document):
        if loc.text.lstrip().startswith(";"):
            continue
        if re.search(r"\bHKCU\b", loc.text, re.IGNORECASE):
            return True
        if re.search(r"\bVU_", loc.text, re.IGNORECASE):
            return True
        if re.search(r"\bAskKillProcesses\b", loc.text, re.IGNORECASE):
            return True
    return False


# --- User-part context helpers (CLIENT/MACHINE, /AW) -------------------------

_CLIENT_SECTION_CF = "set:client"
# Known section-call flags (Legacy-Help flags table); anything else ends a
# flag list when parsing the tokens after a '#Kind:Name' ref.
_REF_FLAG_TOKENS = frozenset({"DONTDELETE", "DELETE", "MACHINE", "CLIENT", "ADMIN"})

# Per-user profile variables: only meaningful in the user part; in the machine
# pass (SYSTEM) they resolve to the system profile (Anti-Pattern 9).
_USER_PROFILE_VAR_RE = re.compile(
    r"%(AppData|LocalAppData|Desktop|Personal|Sendto)%", re.IGNORECASE
)
# Procedural HKCU writes in Set: sections (reg.exe import may pull HKCU from a
# file we cannot see statically — only explicit HKCU arguments count).
_HKCU_WRITE_RE = re.compile(
    r"(?i)\bHKCU\b.*\breg(\.exe)?\s+(add|import|load)\b"
    r"|\breg(\.exe)?\s+(add|import|load)\b.*\bHKCU\b"
)


def _ref_flags_on_line(text: str, name: str, kind: str = "") -> set[str]:
    """Flags of the '#Kind:Name, FLAG, …' call for ``name`` on this line.

    Anchored at the actual ref occurrence (``#Kind:Name``), not the first
    name substring — the name may legitimately appear in line text earlier.
    """
    if kind:
        pattern = re.compile(
            r"(?i)#" + re.escape(kind) + r"\s*:\s*" + re.escape(name)
        )
    else:
        pattern = re.compile(re.escape(name))
    match = pattern.search(text)
    if match is None:
        return set()
    tail = text[match.end() :]
    flags: set[str] = set()
    for token in re.split(r"[,\s]+", tail.strip()):
        if not token:
            continue
        upper = token.strip().upper()
        if upper not in _REF_FLAG_TOKENS:
            break  # first non-flag token ends the flag list
        flags.add(upper)
    return flags


def _product_ref_lines(
    document: Document,
) -> Iterator[tuple[Section, LineNode, str]]:
    """Active [Product] lines (all [Product] sections, Empirum merges them)."""
    for section in document.sections:
        if section.name.casefold() != "product":
            continue
        for node in section.lines:
            text = _node_text(node)
            if text is None or text.lstrip().startswith(";"):
                continue
            yield section, node, text


def _has_user_part(document: Document) -> bool:
    """Real user part: a [Set:Client] section OR any CLIENT-flagged call."""
    if document.section("Set:Client") is not None:
        return True
    for _section, _node, text in _product_ref_lines(document):
        for ref in W.find_section_refs_in_text(text):
            if "CLIENT" in _ref_flags_on_line(text, ref.name, ref.kind):
                return True
    return False


def _client_scoped_sections(document: Document) -> set[str]:
    """Casefolded section names executing in the user context.

    The [Set:Client] section itself plus every section called with the CLIENT
    flag from [Product] (transitively flat: one hop, matching the standard style).
    """
    scoped = {_CLIENT_SECTION_CF}
    known = W.section_names(document)
    for _section, _node, text in _product_ref_lines(document):
        for ref in W.find_section_refs_in_text(text):
            if "CLIENT" not in _ref_flags_on_line(text, ref.name, ref.kind):
                continue
            resolved = W.resolve_section_ref(ref, known)
            if resolved:
                scoped.add(resolved)
    return scoped


def _val_006(document: Document) -> list[Diagnostic]:
    has_client = _has_user_part(document)
    if not has_client and not _needs_user_part(document):
        return []
    options, line_no, cmd_key = _setupinfo_cmdline(document)
    if re.search(r"/AW\b", options, re.IGNORECASE):
        return []
    # Preserve the key that was actually found (legacy CmdLine stays CmdLine)
    replacement = f"{cmd_key}={options} /AW".strip() if options else f"{cmd_key}=/S2 /AW"
    if has_client:
        # Counter-direction: a real CLIENT section without /AW
        # never executes – the whole user part is dead. Hard error.
        message = (
            "Benutzerteil-Sektion ([Set:Client], CLIENT) ohne /AW in [SetupInfo] – "
            "der Benutzerteil läuft nie; auch im Software-Depot unter "
            "Prüfung→Befehl /AW setzen"
        )
        severity = Severity.ERROR
    else:
        message = (
            "Benutzerteil-Merkmale (HKCU / VU_ / AskKillProcesses) ohne /AW in "
            "[SetupInfo] – auch im Software-Depot unter Prüfung→Befehl /AW setzen"
        )
        severity = Severity.WARNING
    return [
        Diagnostic(
            code="VAL-006",
            severity=severity,
            message=message,
            line=line_no,
            quick_fixes=(
                QuickFix(
                    id="VAL-006.aw",
                    title="/AW in SetupInfo-Optionen ergänzen",
                    replacement_line=replacement,
                ),
            ),
        )
    ]


_DANGEROUS_ROOTS = [
    # Quoted fields are the canonical standard form: HKLM,"SOFTWARE\Microsoft\"
    re.compile(r'(?i)-?HKLM\s*,\s*"?SOFTWARE\\Microsoft\\?"?$'),
    re.compile(r'(?i)-?HKLM\s*,\s*"?SOFTWARE\\?"?$'),
]
_DANGEROUS_SERVICES = re.compile(
    r'(?i)^-HKLM\s*,\s*"?SYSTEM\\CurrentControlSet\\Services(\\[^\s,"]*)?'
)


def _val_007(document: Document) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        text = loc.text.strip()
        if not text.upper().startswith(("-HK", "HK")):
            continue
        matched_dangerous = False
        for pat in _DANGEROUS_ROOTS:
            if pat.search(text):
                out.append(
                    Diagnostic(
                        code="VAL-007",
                        severity=Severity.WARNING,
                        message="Gefährliche Registry-Löschung nahe Wurzel-/Herstellerebene",
                        line=loc.line_no,
                        quick_fixes=(
                            QuickFix(
                                id="VAL-007.confirm",
                                title="Löschziel manuell prüfen / vertiefen",
                                note="manual",
                            ),
                        ),
                    )
                )
                matched_dangerous = True
                break
        if not matched_dangerous and _DANGEROUS_SERVICES.search(text):
            out.append(
                Diagnostic(
                    code="VAL-007",
                    severity=Severity.WARNING,
                    message=(
                        "Gefährliche Registry-Löschung unter SYSTEM\\CurrentControlSet\\Services\\ "
                        "beschädigt Windows-Systemdienste bei Deinstallation (Originalwert in "
                        "[Reg:OnUninstallProduct] oder via -CallHidden reg.exe in "
                        "[Set:Deinstallation] "
                        "wiederherstellen)"
                    ),
                    line=loc.line_no,
                    quick_fixes=(
                        QuickFix(
                            id="VAL-007.service_confirm",
                            title="Dienst-Löschung manuell prüfen / Wiederherstellung nutzen",
                            note="manual",
                        ),
                    ),
                )
            )
    return out


def _val_008(document: Document) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    located = W.iter_located(document)
    for idx, loc in enumerate(located):
        stmt = _command_statement(loc.node)
        if stmt is None:
            continue
        verb, cmd_text = stmt
        # taskkill is intentionally best-effort (exit code 128 if process not running)
        if re.search(r"\btaskkill(\.exe)?\b", cmd_text, re.IGNORECASE):
            continue
        window: list[W.LocatedLine] = []
        for w in located[idx + 1 : idx + 6]:
            if w.section is not loc.section:
                break  # %ErrorLevel% from another section is not this call's check
            if isinstance(w.node, CommentLine):
                continue
            window.append(w)
        found = any(
            re.search(r"%ErrorLevel%", w.text, re.IGNORECASE)
            or (isinstance(w.node, KeyValueLine) and w.node.key.casefold() == "if")
            for w in window
        )
        if not found:
            snippet = (
                'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf\r\n'
                'If %ErrorLevel% != "0" Then "Set:InstallationError" EndIf'
            )
            out.append(
                Diagnostic(
                    code="VAL-008",
                    severity=Severity.WARNING,
                    message=f"Nach {verb} fehlt %ErrorLevel%-Prüfung (0/3010)",
                    line=loc.line_no,
                    quick_fixes=(
                        QuickFix(
                            id="VAL-008.snippet",
                            title="ErrorLevel-Block einfügen",
                            replacement_line=snippet,
                            note="insert_after",
                        ),
                    ),
                )
            )
    return out


def _val_009(document: Document) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if not isinstance(loc.node, KeyValueLine):
            continue
        key = loc.node.key.casefold()
        val = loc.node.value.strip()
        if key == "reboot" and val == "1":
            out.append(
                Diagnostic(
                    code="VAL-009",
                    severity=Severity.WARNING,
                    message="Unkontrollierter Reboot=1 – besser Reboot=0 + 3010-Behandlung",
                    line=loc.line_no,
                    quick_fixes=(
                        QuickFix(
                            id="VAL-009.off",
                            title="Reboot=0 setzen",
                            replacement_line="Reboot=0",
                        ),
                    ),
                )
            )
        if key == "setreboot" and val == "1":
            out.append(
                Diagnostic(
                    code="VAL-009",
                    severity=Severity.WARNING,
                    message="Unkonditioniertes SetReboot 1",
                    line=loc.line_no,
                    quick_fixes=(
                        QuickFix(
                            id="VAL-009.setoff",
                            title="SetReboot entfernen / konditionieren",
                            note="manual",
                        ),
                    ),
                )
            )
    return out


def _val_010(document: Document) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if W.has_hardcoded_program_files(loc.text):
            suggestion = re.sub(
                r"(?i)([A-Z]:\\)?Program Files \(x86\)",
                r"%ProgramFiles(x86)%",
                loc.text,
            )
            suggestion = re.sub(
                r"(?i)([A-Z]:\\)?Program Files",
                r"%ProgramFiles%",
                suggestion,
            )
            out.append(
                Diagnostic(
                    code="VAL-010",
                    severity=Severity.INFO,
                    message="Hart codierter Program-Files-Pfad – Systemvariable bevorzugen",
                    line=loc.line_no,
                    quick_fixes=(
                        QuickFix(
                            id="VAL-010.var",
                            title="Durch %ProgramFiles%/%ProgramFiles(x86)% ersetzen",
                            replacement_line=suggestion,
                        ),
                    ),
                )
            )
    return out


def _val_011(document: Document) -> list[Diagnostic]:
    """Sleep must follow MSI/uninstall calls before cleanup statements.

    Scans forward within the section: comments, blank lines and the call's
    If=%ErrorLevel% block are skipped; the first Sleep satisfies the rule,
    another command/cleanup statement or the section end does not.
    """
    out: list[Diagnostic] = []
    located = W.iter_located(document)
    for idx, loc in enumerate(located):
        stmt = _command_statement(loc.node)
        if stmt is None:
            continue
        verb, text = stmt
        sec = loc.section.name.casefold() if loc.section else ""
        lowered = text.casefold()
        relevant = (
            "uninstall" in sec or ".msi" in lowered or "msiexec" in lowered or verb == "msiexec"
        )
        if not relevant:
            continue
        has_sleep = False
        for w in located[idx + 1 :]:
            if w.section is not loc.section:
                break
            if isinstance(w.node, CommentLine):
                continue
            if isinstance(w.node, RawLine):
                stripped = w.text.strip()
                if not stripped:
                    continue
                if re.match(r"(?i)^-?If\b", stripped):
                    continue  # errorlevel handling belongs to the call
                if re.match(r"(?i)^-?Sleep\b", stripped):
                    has_sleep = True
                    break
                match = re.match(r"(?i)^-?(\w+)", stripped)
                if match and match.group(1).casefold() in _COMMAND_KEYS | {"deltree"}:
                    break
                continue
            assert isinstance(w.node, KeyValueLine)
            key = w.node.key.casefold()
            if key == "if":
                continue
            if key == "sleep":
                has_sleep = True
                break
            if key in _COMMAND_KEYS or key == "deltree":
                break
        if has_sleep:
            continue
        out.append(
            Diagnostic(
                code="VAL-011",
                severity=Severity.INFO,
                message="Nach Deinstallations-/MSI-Aufruf fehlt Sleep vor Bereinigung",
                line=loc.line_no,
                quick_fixes=(
                    QuickFix(
                        id="VAL-011.sleep",
                        title="Sleep 3000 einfügen",
                        replacement_line="Sleep 3000",
                        note="insert_after",
                    ),
                ),
            )
        )
    return out


_REQUIRED_SECTIONS = STANDARD_SECTIONS
_REQUIRED_APPLICATION_KEYS = APPLICATION_KEYS
# Shared path contract (VAL-015 and package_readiness PKG-005/006).
SRCDIR_ALLOWED_VALUES = frozenset({"..", ".\\..", "../"})


def _is_package_shaped(document: Document) -> bool:
    names = W.section_names(document)
    return bool({"setupinfo", "setup", "application"} & names)


def _section_kv_map(document: Document, section_name: str) -> dict[str, KeyValueLine]:
    wanted = section_name.casefold()
    out: dict[str, KeyValueLine] = {}
    for section in document.sections:
        if section.name.casefold() != wanted:
            continue
        for node in section.lines:
            if isinstance(node, KeyValueLine):
                out[node.key.casefold()] = node
    return out


def _line_text(node: object) -> str | None:
    """Active line text for structure checks; comments yield None."""
    if isinstance(node, CommentLine):
        return None
    if isinstance(node, KeyValueLine):
        return f"{node.key}={node.value}"
    text = getattr(node, "text", None)
    if isinstance(text, str):
        return text
    return str(node)


def _val_012(document: Document) -> list[Diagnostic]:
    """Required Empirum/Standard sections for a package-shaped Setup.inf."""
    if not _is_package_shaped(document):
        return []
    known = W.section_names(document)
    out: list[Diagnostic] = []
    for name in _REQUIRED_SECTIONS:
        if name.casefold() not in known:
            # QuickFix body: the section header plus the canonical body for the
            # three standard error handlers (empty for every other stub). Applied via
            # ``note="insert_section"``: the section is appended at document end.
            body = ERROR_SECTION_BODIES.get(name, ())
            out.append(
                Diagnostic(
                    code="VAL-012",
                    severity=Severity.ERROR,
                    message=f"Standardsektion [{name}] fehlt",
                    quick_fixes=(
                        QuickFix(
                            id="VAL-012.stub",
                            title=f"Sektion [{name}] anlegen",
                            replacement_line="\r\n".join((f"[{name}]", *body)),
                            note="insert_section",
                            section_name=name,
                        ),
                    ),
                )
            )
    return out


def _val_013(document: Document) -> list[Diagnostic]:
    """Required [Application] keys for Empirum package identity / repair path."""
    if not _is_package_shaped(document):
        return []
    if "application" not in W.section_names(document):
        return []
    keys = _section_kv_map(document, "Application")
    out: list[Diagnostic] = []
    for req in _REQUIRED_APPLICATION_KEYS:
        if req.casefold() not in keys:
            is_short = req.casefold() in {"productnameshort", "developernameshort"}
            severity = Severity.INFO if is_short else Severity.ERROR
            msg = (
                f"[Application] Optionaler Kurzname fehlt: {req}"
                if is_short
                else f"[Application] Pflichtfeld fehlt: {req}"
            )
            out.append(
                Diagnostic(
                    code="VAL-013",
                    severity=severity,
                    message=msg,
                )
            )
    return out


def _val_014(document: Document) -> list[Diagnostic]:
    """[Setup] Version must be present (Empirum Setup.exe dialect)."""
    if not _is_package_shaped(document):
        return []
    if "setup" not in W.section_names(document):
        return []
    keys = _section_kv_map(document, "Setup")
    ver = keys.get("version")
    if ver is None or not ver.value.strip():
        return [
            Diagnostic(
                code="VAL-014",
                severity=Severity.ERROR,
                message="[Setup] Version fehlt (erwartet z. B. 14.2)",
            )
        ]
    return []


def _val_015(document: Document) -> list[Diagnostic]:
    """SrcDir/SetupInfDir path contract for Install\\Setup.inf layout."""
    if not _is_package_shaped(document):
        return []
    if "application" not in W.section_names(document):
        return []
    keys = _section_kv_map(document, "Application")
    out: list[Diagnostic] = []
    src = keys.get("srcdir")
    # Values may be quoted (canonical standard form) – compare unquoted.
    if (
        src is not None
        and Quoter.strip_optional_quotes(src.value).strip() not in SRCDIR_ALLOWED_VALUES
    ):
        out.append(
            Diagnostic(
                code="VAL-015",
                severity=Severity.ERROR,
                message="SrcDir sollte '..' sein (Paketwurzel = Parent von Install)",
                line=_line_of(src),
                quick_fixes=(
                    QuickFix(
                        id="VAL-015.srcdir",
                        title="SrcDir=.. setzen",
                        replacement_line="SrcDir=..",
                    ),
                ),
            )
        )
    setup_inf_dir = keys.get("setupinfdir")
    if (
        setup_inf_dir is not None
        and Quoter.strip_optional_quotes(setup_inf_dir.value).strip().casefold() != "install"
    ):
        out.append(
            Diagnostic(
                code="VAL-015",
                severity=Severity.ERROR,
                message="SetupInfDir sollte 'Install' sein (Install\\Setup.inf)",
                line=_line_of(setup_inf_dir),
                quick_fixes=(
                    QuickFix(
                        id="VAL-015.setupinfdir",
                        title="SetupInfDir=Install setzen",
                        replacement_line="SetupInfDir=Install",
                    ),
                ),
            )
        )
    env = _section_kv_map(document, "Environment")
    if "environment" in W.section_names(document) and "commonsetupdir" not in env:
        out.append(
            Diagnostic(
                code="VAL-015",
                severity=Severity.ERROR,
                message="[Environment] CommonSetupDir fehlt (Setup.exe-Zielpfad)",
            )
        )
    return out


def _val_016(document: Document) -> list[Diagnostic]:
    """MSI install calls should carry Empirum-Paket-Standard silent + per-machine flags."""
    if not _is_package_shaped(document):
        return []
    setupinfo = _section_kv_map(document, "SetupInfo")
    method_node = setupinfo.get("method")
    method = (method_node.value if method_node is not None else "").strip().casefold()
    blob_parts: list[str] = []
    for section in document.sections:
        for node in section.lines:
            text = _line_text(node)
            if text is not None:
                blob_parts.append(text)
    blob = "\n".join(blob_parts)
    has_msi_exec = bool(re.search(r"msiexec(?:\.exe)?\s+/i\b", blob, flags=re.IGNORECASE))
    if method != "msi" and not has_msi_exec:
        return []
    out: list[Diagnostic] = []
    # Prefer checking install lines specifically
    install_lines: list[tuple[int | None, str]] = []
    for section in document.sections:
        for node in section.lines:
            text = _line_text(node)
            if text is None:
                continue
            if re.search(r"msiexec(?:\.exe)?\s+/i\b", text, flags=re.IGNORECASE):
                span = getattr(node, "span", None)
                line_no = span.start_line if span is not None else None
                install_lines.append((line_no, text))
    if not install_lines and method == "msi":
        out.append(
            Diagnostic(
                code="VAL-016",
                severity=Severity.WARNING,
                message=(
                    'MSI-Paket ohne MsiExec /I – erwartet ALLUSERS="1" '
                    "REBOOT=REALLYSUPPRESS ARPSYSTEMCOMPONENT=1 /qn"
                ),
            )
        )
        return out
    for line_no, text in install_lines:
        missing = [
            flag for flag in MSI_INSTALL_FLAGS if flag.casefold() not in text.casefold()
        ]
        # ALLUSERS="1" may appear as ALLUSERS=1
        if 'ALLUSERS="1"' in missing and re.search(
            r'ALLUSERS\s*=\s*"?1"?', text, flags=re.IGNORECASE
        ):
            missing = [m for m in missing if m != 'ALLUSERS="1"']
        if missing:
            out.append(
                Diagnostic(
                    code="VAL-016",
                    severity=Severity.WARNING,
                    message="MsiExec /I ohne empfohlene Flags: " + ", ".join(missing),
                    line=line_no,
                )
            )
    return out

def _val_017(document: Document) -> list[Diagnostic]:
    """Remind admins to mirror /AW in the Empirum software depot package command."""
    if not _is_package_shaped(document):
        return []
    options, line_no, _cmd_key = _setupinfo_cmdline(document)
    if not re.search(r"/AW\b", options, re.IGNORECASE):
        return []
    return [
        Diagnostic(
            code="VAL-017",
            severity=Severity.INFO,
            message=(
                "SetupInfo enthält /AW – im Empirum Software-Depot unter "
                "Paketeigenschaften → Prüfung → Befehl ebenfalls /AW ergänzen, "
                "sonst läuft der Benutzerteil nie"
            ),
            line=line_no,
        )
    ]

def _val_018(document: Document) -> list[Diagnostic]:
    """Clarify that -HK… in [Reg:…] deletes on uninstall, not install."""
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if loc.section is None:
            continue
        if not loc.section.name.casefold().startswith("reg"):
            continue
        text_line = loc.text.lstrip()
        if text_line.startswith(";"):
            continue
        if not re.match(r"(?i)^-\s*HK(LM|CU|CR|U)\b", text_line):
            continue
        out.append(
            Diagnostic(
                code="VAL-018",
                severity=Severity.INFO,
                message=(
                    "'-'-Präfix in [Reg:…] löscht erst bei Deinstallation. "
                    "Für Löschung während der Installation: "
                    'CallHidden reg.exe delete "HKLM\\…" /f'
                ),
                line=loc.line_no or None,
            )
        )
    return out



def _looks_like_command_section(name: str) -> bool:
    """Sections whose RawLine content consists of Setup.inf statements."""
    n = name.casefold()
    if n.startswith(("set:", "set_")):
        return True
    return bool(
        n.startswith(
            ("install", "uninstall", "deinstall", "reinstall", "repair", "error", "reboot")
        )
        or n in {"product", "ok"}
    )


_COMMAND_TOKEN_RE = re.compile(r"^(-?)([A-Za-z_][A-Za-z0-9_]*)\b")
_KNOWN_COMMANDS = frozenset(cmd.casefold() for cmd in SETUPINF_COMMANDS)
# Class-1 undocumented commands (feature-flagged via LintOptions.undocumented_commands)
_KNOWN_UNDOCUMENTED_COMMANDS = frozenset(
    cmd.casefold() for cmd in SETUPINF_COMMANDS_UNDOCUMENTED
)

# P1-Korrekturen K-01/K-02 + Run (verified against the Empirum 26.1.0 interpreter):
# these constructs do NOT exist. Unknown commands run through the program
# start fallback (SETUP_ERR_UNRECOGNIZABLE) and silently do the wrong thing.
_NONEXISTENT_COMMAND_FIXES: dict[str, str] = {
    "run": "CallHidden",
    "checklanadministrator": "",
}
_NONEXISTENT_PREDICATE_FIXES: dict[str, str] = {
    "fileexists": "DoesFileExist",
    "direxists": "DoesPathExist",
    "doesdirexist": "DoesPathExist",
    "regkeyexists": "DoesRegKeyExist",
    "regvalueexists": "DoesRegKeyExist",
    "doesregvalueexist": "DoesRegKeyExist",
    "processexists": "DoesProcessExist",
    "serviceexists": "",
    "doesserviceexist": "",
}
_NONEXISTENT_TOKENS = frozenset(_NONEXISTENT_COMMAND_FIXES) | frozenset(
    _NONEXISTENT_PREDICATE_FIXES
)
_NONEXISTENT_PRED_RE = re.compile(
    r"\b(?P<name>"
    + "|".join(
        name
        for name in _NONEXISTENT_PREDICATE_FIXES
        if name not in _NONEXISTENT_COMMAND_FIXES
    )
    + r")\s*\(",
    re.IGNORECASE,
)
_VALID_PREDICATES_HINT = (
    "DoesFileExist, DoesPathExist, DoesProcessExist, DoesRegKeyExist, "
    "DoesTextInFileExist"
)


def _val_019(document: Document, options: LintOptions | None = None) -> list[Diagnostic]:
    """Raw statements must use commands documented in the reference.

    WARNING (not ERROR): the reference command table may be incomplete
    regarding exotic but real Empirum commands. Tokens proven non-existent
    are left to VAL-026 (ERROR). With the undocumented-commands feature
    flag, class-1 undocumented commands count as known.
    """
    options = options or LintOptions()
    known = _KNOWN_COMMANDS
    if options.undocumented_commands:
        known = known | _KNOWN_UNDOCUMENTED_COMMANDS
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if loc.section is None or not _looks_like_command_section(loc.section.name):
            continue
        if not isinstance(loc.node, RawLine):
            continue
        text = loc.text.strip()
        if not text or text.startswith((";", "#")):
            continue
        match = _COMMAND_TOKEN_RE.match(text)
        if match is None:
            continue
        token = match.group(2).casefold()
        if token in _NONEXISTENT_COMMAND_FIXES:
            continue  # VAL-026 reports with ERROR + rename fix
        if token not in known:
            out.append(
                Diagnostic(
                    code="VAL-019",
                    severity=Severity.WARNING,
                    message=(
                        f"Befehl „{match.group(2)}“ ist nicht in der "
                        "Setup.inf-Befehlsreferenz dokumentiert"
                    ),
                    line=loc.line_no,
                )
            )
    return out


def _val_020(document: Document) -> list[Diagnostic]:
    """Reference syntax: If <cond> Then "Section" [Else "Other"] EndIf (one line)."""
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        text = loc.text.strip()
        match = _COMMAND_TOKEN_RE.match(text)
        if match is None or match.group(2).casefold() != "if":
            continue
        if isinstance(loc.node, KeyValueLine) and not re.search(
            r"\bThen\b", text, re.IGNORECASE
        ):
            continue  # legacy bare If= form handled by VAL-002 territory
        if re.search(r"\bThen\b", text, re.IGNORECASE) and not re.search(
            r"\bEndIf\b", text, re.IGNORECASE
        ):
            out.append(
                Diagnostic(
                    code="VAL-020",
                    severity=Severity.ERROR,
                    message="If mit Then ohne EndIf in derselben Zeile (Referenz-Syntax)",
                    line=loc.line_no,
                )
            )
    return out


_VAR_USE_RE = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")
_SET_DEFINE_RE = re.compile(r"(?i)^-?Set\s+([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _defined_variables(
    document: Document, options: LintOptions | None = None
) -> set[str]:
    """Built-ins plus document-defined names (Environment/Strings/Application/Set/VarDefInfo)."""
    opts = options if options is not None else LintOptions()
    defined = {var.strip("%").casefold() for var in SETUPINF_VARIABLES}
    if opts.undocumented_commands:
        defined |= {var.strip("%").casefold() for var in SETUPINF_VARIABLES_UNDOCUMENTED}
    for section in document.sections:
        n = section.name.casefold()
        if n.startswith(("environment", "strings", "sysstrings", "application", "vardefinfo")):
            for node in section.lines:
                if isinstance(node, KeyValueLine):
                    defined.add(node.key.casefold())
                elif isinstance(node, RawLine):
                    raw = node.text.strip()
                    if raw and not raw.startswith(";"):
                        token = raw.split(",")[0].split("=")[0].strip()
                        if token:
                            defined.add(token.casefold())
        elif _looks_like_command_section(section.name):
            for node in section.lines:
                # `Set NAME = …` definitions appear as RawLine OR as KeyValueLine
                # with key "Set NAME" (the lexer treats the '=' as KV separator).
                if isinstance(node, RawLine):
                    match = _SET_DEFINE_RE.match(node.text.strip())
                    if match:
                        defined.add(match.group(1).casefold())
                elif isinstance(node, KeyValueLine) and node.key.casefold().startswith(
                    "set "
                ):
                    name = node.key[4:].strip()
                    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                        defined.add(name.casefold())
    return defined


def _val_021(document: Document, options: LintOptions | None = None) -> list[Diagnostic]:
    """%Var% uses must be built-in or defined by the document."""
    options = options or LintOptions()
    defined = _defined_variables(document, options)
    out: list[Diagnostic] = []
    seen: set[tuple[str, int]] = set()
    for loc in W.iter_located(document):
        if isinstance(loc.node, CommentLine):
            continue
        for match in _VAR_USE_RE.finditer(loc.text):
            name = match.group(1).casefold()
            if name in defined:
                continue
            key = (name, loc.line_no)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Diagnostic(
                    code="VAL-021",
                    severity=Severity.WARNING,
                    message=(
                        f"Variable %{match.group(1)}% ist weder eingebaut noch "
                        "im Dokument definiert (Environment/Strings/Application/Set)"
                    ),
                    line=loc.line_no,
                )
            )
    return out


# VAL-022: [Reg:*] sections are purely declarative — EVERY catalog command
# is procedural there. Derived from the command catalog plus the legacy
# RegModify* spellings seen in migrated packages.
_PROCEDURAL_REG_COMMANDS = frozenset(
    cmd.casefold() for cmd in SETUPINF_COMMANDS
) | {
    "regmodify",
    "regmodifydword",
    "regmodifyqword",
    "regmodifymultisz",
    "regmodifybinary",
}


def _val_022(document: Document) -> list[Diagnostic]:
    """Reg:* sections are declarative; procedural commands must be in Set:*."""
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if loc.section is None:
            continue
        if not loc.section.name.casefold().startswith("reg:"):
            continue
        if isinstance(loc.node, CommentLine):
            continue
        text = loc.text.strip()
        if not text or text.startswith(";"):
            continue

        token: str | None = None
        if isinstance(loc.node, KeyValueLine):
            key = loc.node.key.strip()
            parts = key.split(None, 1)
            cmd = parts[0].lstrip("-").casefold()
            if cmd in _PROCEDURAL_REG_COMMANDS:
                token = parts[0].lstrip("-")
        elif isinstance(loc.node, RawLine):
            match = _COMMAND_TOKEN_RE.match(text)
            if match:
                cmd = match.group(2).casefold()
                if cmd in _PROCEDURAL_REG_COMMANDS:
                    token = match.group(2)

        if token:
            out.append(
                Diagnostic(
                    code="VAL-022",
                    severity=Severity.ERROR,
                    message=(
                        f"Sektion [{loc.section.name}] ist rein deklarativ – "
                        f"Befehl „{token}“ gehört prozedural in eine "
                        "[Set:...]-Sektion (z. B. via CallHidden reg.exe add)"
                    ),
                    line=loc.line_no,
                )
            )
    return out


_DYNAMIC_SET_VAL_RE = re.compile(
    r'(?i)(?:\b(?:'
    + '|'.join(re.escape(f) for f in SETUPINF_FUNCTIONS)
    + r')\b|"%?(?:HKLM|HKCU|HKCR|HKU|Root),|%%%)'
)


def _val_023(document: Document) -> list[Diagnostic]:
    """Variables set from dynamic expressions should be expanded with ReplaceEnv."""
    out: list[Diagnostic] = []
    for section in document.sections:
        if not _looks_like_command_section(section.name):
            continue
        lines = section.lines
        for i, node in enumerate(lines):
            var_name: str | None = None
            expr: str = ""
            line_no = node.span.start_line if node.span else 0

            if isinstance(node, KeyValueLine) and node.key.casefold().startswith("set "):
                name_candidate = node.key[4:].strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name_candidate):
                    var_name = name_candidate
                    expr = node.value
            elif isinstance(node, RawLine):
                text = node.text.strip()
                if not text or text.startswith(";"):
                    continue
                match = _SET_DEFINE_RE.match(text)
                if match:
                    var_name = match.group(1)
                    expr = text.split("=", 1)[1] if "=" in text else ""

            if not var_name or not _DYNAMIC_SET_VAL_RE.search(expr):
                continue

            has_replace_env = False
            target_cf = var_name.casefold()
            for follower in lines[i + 1:]:
                if isinstance(follower, KeyValueLine):
                    k = follower.key.strip().lstrip("-").casefold()
                    if k == f"replaceenv {target_cf}" or (
                        k == "replaceenv" and follower.value.strip().casefold() == target_cf
                    ):
                        has_replace_env = True
                        break
                elif isinstance(follower, RawLine):
                    t = follower.text.strip().lstrip("-")
                    m = re.match(r"(?i)^ReplaceEnv\s+([A-Za-z_][A-Za-z0-9_]*)", t)
                    if m and m.group(1).casefold() == target_cf:
                        has_replace_env = True
                        break

            if not has_replace_env:
                out.append(
                    Diagnostic(
                        code="VAL-023",
                        severity=Severity.WARNING,
                        message=(
                            f"Variable %{var_name}% wird über dynamischen Ausdruck zugewiesen, "
                            f"aber in dieser Sektion nicht mit 'ReplaceEnv {var_name}' aufgelöst"
                        ),
                        line=line_no,
                    )
                )
    return out


def _val_024(document: Document) -> list[Diagnostic]:
    """Abort should be preceded by ErrorLogMsg in the same section."""
    out: list[Diagnostic] = []
    for section in document.sections:
        if not _looks_like_command_section(section.name):
            continue
        has_errorlog = False
        for node in section.lines:
            line_no = node.span.start_line if node.span else 0
            if isinstance(node, KeyValueLine):
                k = node.key.strip().lstrip("-").casefold()
                if k == "errorlogmsg" or k.startswith("errorlogmsg "):
                    has_errorlog = True
                elif (k == "abort" or k.startswith("abort ")) and not has_errorlog:
                    out.append(
                        Diagnostic(
                            code="VAL-024",
                            severity=Severity.WARNING,
                            message=(
                                "Befehl 'Abort' ohne vorangehendes 'ErrorLogMsg' – "
                                "im Protokoll fehlt die Fehlerursache."
                            ),
                            line=line_no,
                        )
                    )
            elif isinstance(node, RawLine):
                text = node.text.strip()
                if not text or text.startswith(";"):
                    continue
                if re.match(r"(?i)^-?ErrorLogMsg\b", text):
                    has_errorlog = True
                elif re.match(r"(?i)^-?Abort\b", text) and not has_errorlog:
                    out.append(
                        Diagnostic(
                            code="VAL-024",
                            severity=Severity.WARNING,
                            message=(
                                "Befehl 'Abort' ohne vorangehendes 'ErrorLogMsg' – "
                                "im Protokoll fehlt die Fehlerursache."
                            ),
                            line=line_no,
                        )
                    )
    return out


def _val_025(document: Document) -> list[Diagnostic]:
    """Sleep requires command syntax 'Sleep <ms>', not assignment 'Sleep=<ms>'."""
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if isinstance(loc.node, CommentLine):
            continue
        line_text = loc.text.strip()
        if not line_text or line_text.startswith(";"):
            continue

        if isinstance(loc.node, KeyValueLine):
            key_clean = loc.node.key.strip()
            if key_clean.lstrip("-").casefold() == "sleep":
                val = loc.node.value.strip()
                prefix = "-" if key_clean.startswith("-") else ""
                fix = f"{prefix}Sleep {val}"
                out.append(
                    Diagnostic(
                        code="VAL-025",
                        severity=Severity.ERROR,
                        message=(
                            f"Ungültige Zuweisungssyntax '{line_text}'. Der Befehl 'Sleep' "
                            f"verlangt Befehlssyntax '{fix}' (ohne Gleichheitszeichen)"
                        ),
                        line=loc.line_no,
                        quick_fixes=(
                            QuickFix(
                                id="VAL-025.syntax",
                                title=f"In '{fix}' korrigieren",
                                replacement_line=fix,
                            ),
                        ),
                    )
                )
        elif isinstance(loc.node, RawLine):
            m = re.match(r"^(-?)\s*Sleep\s*=\s*(.*)$", line_text, re.IGNORECASE)
            if m:
                prefix = m.group(1)
                val = m.group(2).strip()
                fix = f"{prefix}Sleep {val}"
                out.append(
                    Diagnostic(
                        code="VAL-025",
                        severity=Severity.ERROR,
                        message=(
                            f"Ungültige Zuweisungssyntax '{line_text}'. Der Befehl 'Sleep' "
                            f"verlangt Befehlssyntax '{fix}' (ohne Gleichheitszeichen)"
                        ),
                        line=loc.line_no,
                        quick_fixes=(
                            QuickFix(
                                id="VAL-025.syntax",
                                title=f"In '{fix}' korrigieren",
                                replacement_line=fix,
                            ),
                        ),
                    )
                )
    return out


def _val_026_fixes_for(
    found: str, full_line: str, replacement: str
) -> tuple[QuickFix, ...]:
    """QuickFix tuple for a non-existent token (rename or manual/delete)."""
    if replacement:
        fixed = full_line.replace(found, replacement, 1)
        return (
            QuickFix(
                id="VAL-026.rename",
                title=f"„{found}“ durch „{replacement}“ ersetzen",
                replacement_line=fixed,
            ),
        )
    if found.casefold() == "checklanadministrator":
        return (
            QuickFix(
                id="VAL-026.delete",
                title="Zeile entfernen (Befehl existiert nicht)",
                note="delete_line",
            ),
        )
    return (
        QuickFix(
            id="VAL-026.manual",
            title="Manuell ersetzen (kein Dienst-Prädikat im Interpreter)",
            note="manual",
        ),
    )


def _val_026(document: Document) -> list[Diagnostic]:
    """K-01/K-02 (must-fix): commands/predicates that do not exist in the
    Empirum 26.1.0 interpreter (verified). The interpreter executes
    unknown commands through the program start fallback
    (SETUP_ERR_UNRECOGNIZABLE), so these constructs fail silently.
    """
    out: list[Diagnostic] = []
    seen: set[tuple[str, int]] = set()

    # Command position: first token of a statement in command-style sections.
    for loc in W.iter_located(document):
        if loc.section is None or not _looks_like_command_section(loc.section.name):
            continue
        if not isinstance(loc.node, RawLine):
            continue
        text = loc.text.strip()
        if not text or text.startswith((";", "#")):
            continue
        match = _COMMAND_TOKEN_RE.match(text)
        if match is None:
            continue
        token = match.group(2)
        replacement = _NONEXISTENT_COMMAND_FIXES.get(token.casefold())
        if replacement is None:
            continue
        key = (token.casefold(), loc.line_no)
        if key in seen:
            continue
        seen.add(key)
        message = (
            f"Befehl „{token}“ existiert nicht im Empirum-Interpreter 26.1.0 "
            "(verifiziert) – die Zeile wird als Programmstart interpretiert "
            "(SETUP_ERR_UNRECOGNIZABLE)"
        )
        if replacement == "CallHidden":
            message += "; für wartende Ausführung „CallHidden“ verwenden"
        out.append(
            Diagnostic(
                code="VAL-026",
                severity=Severity.ERROR,
                message=message,
                line=loc.line_no,
                quick_fixes=_val_026_fixes_for(token, text, replacement),
            )
        )

    # Predicate position: If conditions and [Requirements] expressions.
    for loc in W.iter_located(document):
        if isinstance(loc.node, CommentLine):
            continue
        is_if = isinstance(loc.node, KeyValueLine) and W.looks_like_if_key(
            loc.node.key.strip()
        )
        is_requirements = (
            loc.section is not None
            and loc.section.name.casefold() == "requirements"
        )
        if not is_if and not is_requirements:
            if not isinstance(loc.node, RawLine):
                continue
            token_match = _COMMAND_TOKEN_RE.match(loc.text.strip())
            if token_match is None or token_match.group(2).casefold() != "if":
                continue
        for match in _NONEXISTENT_PRED_RE.finditer(loc.text):
            name = match.group("name")
            replacement = _NONEXISTENT_PREDICATE_FIXES.get(name.casefold(), "")
            key = (name.casefold(), loc.line_no)
            if key in seen:
                continue
            seen.add(key)
            if replacement:
                message = (
                    f"Prädikat „{name}“ existiert nicht im Empirum-Interpreter 26.1.0 "
                    f"(verifiziert); gültig sind: {_VALID_PREDICATES_HINT}"
                )
                if name.casefold() in ("regvalueexists", "doesregvalueexist"):
                    message += " – Wert-Existenz prüft DoesRegKeyExist inkl. ValueName-Komponente"
            elif name.casefold() in ("serviceexists", "doesserviceexist"):
                message = (
                    f"Prädikat „{name}“ existiert nicht im Empirum-Interpreter 26.1.0 "
                    "(verifiziert); Dienst-Existenz über "
                    'DoesRegKeyExist ("HKLM,SYSTEM\\CurrentControlSet\\Services\\<Name>") prüfen'
                )
            else:
                message = (
                    f"Prädikat „{name}“ existiert nicht im Empirum-Interpreter 26.1.0 "
                    f"(verifiziert); gültig sind: {_VALID_PREDICATES_HINT}"
                )
            out.append(
                Diagnostic(
                    code="VAL-026",
                    severity=Severity.ERROR,
                    message=message,
                    line=loc.line_no,
                    quick_fixes=_val_026_fixes_for(name, loc.text, replacement),
                ),
            )
    return out


# VAL-027: [Reg:*] type constants are validated against the official table
# (SETUPINF_REG_TYPES, K-03). Additive behaviour flags +0x2/+0x8/+0x10
# may be OR-ed onto a base type; all official base codes have
# bits 1/3/4 clear, so masking them out recovers the base unambiguously.
_REG_TYPE_BASES = frozenset(int(code, 16) for code in SETUPINF_REG_TYPES.values())
_REG_EXTRA_FLAG_MASK = 0x2 | 0x8 | 0x10  # 0x1A
_UNQUOTED_HEX_RE = re.compile(r"\b0[xX][0-9A-Fa-f]{4,8}\b")
_QUOTED_SEGMENT_RE = re.compile(r'"[^"\r\n]*"')
# PackagerX's own former wrong constants: unambiguous replacements.
_KNOWN_BAD_REG_CODES: dict[int, str] = {
    0x00010004: "0x00040001",  # old wrong REG_QWORD
}


def _val_027(document: Document) -> list[Diagnostic]:
    """[Reg:*] type constant must match the official Empirum type table."""
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if loc.section is None:
            continue
        if not loc.section.name.casefold().startswith("reg:"):
            continue
        if isinstance(loc.node, CommentLine):
            continue
        text = loc.text.strip()
        if not text or text.startswith(";"):
            continue
        # Data fields are quoted; the type constant is the only unquoted hex
        # token on a [Reg:*] line.
        unquoted = _QUOTED_SEGMENT_RE.sub('""', text)
        match = _UNQUOTED_HEX_RE.search(unquoted)
        if match is None:
            continue
        token = match.group(0)
        try:
            value = int(token, 16)
        except ValueError:
            continue
        base = value & ~_REG_EXTRA_FLAG_MASK
        if base in _REG_TYPE_BASES:
            continue
        replacement_code = _KNOWN_BAD_REG_CODES.get(value)
        message = (
            f"Unbekannter oder veralteter Registry-Typcode '{token}' in "
            f"[{loc.section.name}] – maßgeblich ist die offizielle Tabelle "
            "(REG_SZ=0x00000000, REG_BINARY=0x00000001, REG_MULTI_SZ=0x00010000, "
            "REG_DWORD=0x00010001, REG_EXPAND_SZ=0x00020000, REG_NONE=0x00020001, "
            "REG_QWORD=0x00040001, REG_BINARY_SZ=0x10000001; additive Flags "
            "+0x2/+0x8/+0x10 erlaubt)"
        )
        quick_fixes: tuple[QuickFix, ...] = ()
        if replacement_code:
            message += f"; ehemaliger PackagerX-Fehler, korrekt ist '{replacement_code}'"
            quick_fixes = (
                QuickFix(
                    id="VAL-027.fixcode",
                    title=f"Typcode in '{replacement_code}' korrigieren",
                    replacement_line=text.replace(token, replacement_code, 1),
                ),
            )
        out.append(
            Diagnostic(
                code="VAL-027",
                severity=Severity.WARNING,
                message=message,
                line=loc.line_no,
                quick_fixes=quick_fixes,
            )
        )
    return out


# VAL-028: interactive commands are suppressed at silent levels /S0 and /S1
# (Legacy-Help SETUP_Aufruf.htm / SW-019: Prompts sichtbar erst ab Level 2).
_SILENT_SUPPRESSING_RE = re.compile(r"/S[01]\b", re.IGNORECASE)
_INTERACTIVE_COMMANDS = frozenset({
    "prompt",
    "askkillprocesses",
    "closewindow",
    "splashdialogon",
    "splashdialogtext",
})


def _val_028(document: Document) -> list[Diagnostic]:
    """Dialog/interaction commands have no effect at /S0–/S1 silent level."""
    options, _, _ = _setupinfo_cmdline(document)
    if not _SILENT_SUPPRESSING_RE.search(options):
        return []
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if loc.section is None or not _looks_like_command_section(loc.section.name):
            continue
        if not isinstance(loc.node, RawLine):
            continue
        text = loc.text.strip()
        if not text or text.startswith((";", "#")):
            continue
        match = _COMMAND_TOKEN_RE.match(text)
        if match is None:
            continue
        token = match.group(2)
        if token.casefold() not in _INTERACTIVE_COMMANDS:
            continue
        out.append(
            Diagnostic(
                code="VAL-028",
                severity=Severity.WARNING,
                message=(
                    f"Befehl „{token}“ ist interaktiv, aber das Paket läuft mit "
                    "Silent-Level /S0//S1 – Dialoge und Prompts werden unterdrückt "
                    "und der dort definierte Default greift automatisch"
                ),
                line=loc.line_no,
            )
        )
    return out


def _val_029(document: Document) -> list[Diagnostic]:
    """AbortSilent reports SUCCESS to the depot (documented 26.1.0 semantics)."""
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        if loc.section is None or not _looks_like_command_section(loc.section.name):
            continue
        if isinstance(loc.node, CommentLine):
            continue
        text = loc.text.strip()
        if not text or text.startswith((";", "#")):
            continue
        hit = False
        if isinstance(loc.node, KeyValueLine):
            hit = loc.node.key.strip().lstrip("-").casefold().startswith("abortsilent")
        else:
            match = _COMMAND_TOKEN_RE.match(text)
            hit = bool(match and match.group(2).casefold() == "abortsilent")
        if hit:
            out.append(
                Diagnostic(
                    code="VAL-029",
                    severity=Severity.WARNING,
                    message=(
                        "'AbortSilent' meldet dem Software-Depot 'Success' und führt den "
                        "Benutzerteil trotzdem aus – für echte Fehler stattdessen "
                        "'ErrorLogMsg' + 'Abort' verwenden"
                    ),
                    line=loc.line_no,
                )
            )
    return out


def _val_030(document: Document) -> list[Diagnostic]:
    """VAL-030 (Error): File/document starts with UTF-8 or UTF-16 BOM or Mojibake residue."""
    out: list[Diagnostic] = []
    has_bom = document.has_bom
    if not has_bom and document.sections:
        first_sec = document.sections[0]
        if (first_sec.header_raw or "").startswith(("\ufeff", "ï»¿", "\xef\xbb\xbf")):
            has_bom = True
    if not has_bom and document.preamble:
        first_node = document.preamble[0]
        first_line = first_node.text if isinstance(first_node, RawLine) else ""
        if first_line.startswith(("\ufeff", "ï»¿", "\xef\xbb\xbf")):
            has_bom = True

    if has_bom:
        out.append(
            Diagnostic(
                code="VAL-030",
                severity=Severity.ERROR,
                message=(
                    "Setup.inf beginnt mit einem Byte Order Mark "
                    "(BOM: EF BB BF / FF FE / FE FF / ï»¿) – der native Empirum-Interpreter "
                    "(Setup.exe) und der Package Editor können die erste Sektion "
                    "nicht erkennen und brechen sofort ab"
                ),
                line=1,
                quick_fixes=(
                    QuickFix(
                        id="VAL-030.remove_bom",
                        title="BOM entfernen und als Windows-1252 (ANSI) speichern",
                        note="strip_bom_and_set_cp1252",
                    ),
                ),
            )
        )
    return out


_UNDEFINED_CP1252_BYTES = {b"\x81", b"\x8d", b"\x8f", b"\x90", b"\x9d"}


def _is_cp1252_char(c: str) -> bool:
    try:
        b = c.encode("cp1252")
        return b not in _UNDEFINED_CP1252_BYTES
    except UnicodeEncodeError:
        return False


def _val_031(document: Document) -> list[Diagnostic]:
    """VAL-031 (Error/Warning): Non-CP1252 characters or non-ANSI encoding declaration."""
    out: list[Diagnostic] = []
    if document.encoding_name.casefold() not in {"cp1252", "windows-1252", "ansi"}:
        out.append(
            Diagnostic(
                code="VAL-031",
                severity=Severity.WARNING,
                message=(
                    f"Setup.inf ist als '{document.encoding_name}' statt Windows-1252 (ANSI) "
                    "deklariert – Empirum erwartet ANSI / Windows-1252. Umlaute und Sonderzeichen "
                    "können als Mojibake erscheinen"
                ),
                line=1,
                quick_fixes=(
                    QuickFix(
                        id="VAL-031.set_cp1252",
                        title="Encoding auf Windows-1252 (ANSI) umstellen",
                        note="set_cp1252",
                    ),
                ),
            )
        )

    for loc in W.iter_located(document):
        text = loc.text
        try:
            b = text.encode("cp1252")
            has_undef = any(bytes([byte]) in _UNDEFINED_CP1252_BYTES for byte in b)
            if not has_undef:
                continue
        except UnicodeEncodeError:
            pass

        bad = sorted({c for c in text if not _is_cp1252_char(c)})
        if bad:
            preview = ", ".join(f"'{c}' (U+{ord(c):04X})" for c in bad[:3])
            out.append(
                Diagnostic(
                    code="VAL-031",
                    severity=Severity.ERROR,
                    message=(
                        "Zeile enthält nicht in Windows-1252 (ANSI) darstellbare Zeichen: "
                        f"{preview} – Empirum unterstützt nur Windows-1252; führt zu "
                        "Abbruch oder Datenverlust"
                    ),
                    line=loc.line_no,
                )
            )
    return out


# VAL-032..034 (User-Parts): a package with a real user part
# ([Set:Client] / CLIENT flag) must route every user-context command there;
# the machine pass executes them as SYSTEM otherwise (user context).


def _val_032(document: Document) -> list[Diagnostic]:
    """User-context commands must live in the CLIENT-scoped sections.

    Only fires when a real user part exists: packages whose /AW results solely
    from HKCU/profile detection deliberately keep such lines in [Set:Product]
    (they then run in BOTH passes). Uninstall/reinstall paths keep machine
    context by design and are exempt.
    """
    if not _has_user_part(document):
        return []
    client_scoped = _client_scoped_sections(document)
    out: list[Diagnostic] = []
    for loc in W.iter_located(document):
        section = loc.section
        if section is None or not _looks_like_command_section(section.name):
            continue
        name_cf = section.name.casefold()
        if name_cf in client_scoped:
            continue
        if "deinstall" in name_cf or "uninstall" in name_cf or name_cf.startswith(
            ("set:reinstall", "reinstall", "repair")
        ):
            continue
        if isinstance(loc.node, CommentLine):
            continue
        text = loc.text.strip()
        if not text or text.startswith((";", "#")):
            continue
        hit = _USER_PROFILE_VAR_RE.search(text)
        if hit is None and not _HKCU_WRITE_RE.search(text):
            continue
        what = f"%{hit.group(1)}%" if hit else "HKCU"
        out.append(
            Diagnostic(
                code="VAL-032",
                severity=Severity.ERROR,
                message=(
                    f"Benutzerkontext-Befehl ({what}) in [{section.name}] außerhalb "
                    "der CLIENT-Sektion – im Maschinendurchlauf läuft er als SYSTEM "
                    "und wirkt auf das SYSTEM-Profil. Nach [Set:Client] verschieben "
                    "(/AW + CLIENT-Flag), sofern er nicht bewusst in beiden "
                    "Durchläufen laufen soll (dann MACHINE-Flags entfernen)"
                ),
                line=loc.line_no,
            )
        )
    return out


def _val_033(document: Document) -> list[Diagnostic]:
    """Duplicate [Set:Client] sections: merged by Empirum, order becomes
    accidental — one user part must be exactly one section."""
    out: list[Diagnostic] = []
    seen = 0
    for section in document.sections:
        if section.name.casefold() != _CLIENT_SECTION_CF:
            continue
        seen += 1
        if seen > 1:
            out.append(
                Diagnostic(
                    code="VAL-033",
                    severity=Severity.ERROR,
                    message=(
                        "Doppelte [Set:Client]-Sektion – Empirum führt gleichnamige "
                        "Sektionen zusammen, die Ausführungsreihenfolge wird "
                        "unbestimmt. Alle Benutzerbefehle in EINE [Set:Client]-"
                        "Sektion zusammenführen"
                    ),
                    line=section.span.start_line if section.span else None,
                )
            )
    return out


def _val_034(document: Document) -> list[Diagnostic]:
    """MACHINE flag on a #Reg:… call whose target section holds HKCU entries.

    The machine flag makes the section skip the user pass — per-user HKCU
    values would silently never be written (flag table).
    """
    known = W.section_names(document)
    out: list[Diagnostic] = []
    for _section, node, text in _product_ref_lines(document):
        for ref in W.find_section_refs_in_text(text):
            if ref.kind.casefold() != "reg":
                continue
            if "MACHINE" not in _ref_flags_on_line(text, ref.name, ref.kind):
                continue
            resolved = W.resolve_section_ref(ref, known)
            if resolved is None:
                continue
            target = next(
                (s for s in document.sections if s.name.casefold() == resolved), None
            )
            if target is None:
                continue
            has_hkcu = any(
                (
                    isinstance(line, KeyValueLine)
                    and re.match(r"(?i)^\s*-?HKCU\b", line.key)
                )
                or (
                    isinstance(line, RawLine)
                    and re.match(r"(?i)^\s*-?HKCU\b", line.text)
                )
                for line in target.lines
            )
            if not has_hkcu:
                continue
            fixed = re.sub(r"(?i),\s*MACHINE\b", "", text).rstrip()
            out.append(
                Diagnostic(
                    code="VAL-034",
                    severity=Severity.WARNING,
                    message=(
                        f"MACHINE-Flag auf {ref.kind}:{ref.name}, aber [{target.name}] "
                        "enthält HKCU-Einträge – die Sektion wird im "
                        "Benutzerdurchlauf (/AW) übersprungen und die HKCU-Werte "
                        "pro Benutzer nie geschrieben. Flag entfernen, damit die "
                        "Sektion in beiden Durchläufen läuft (HKLM-Schreibzugriffe "
                        "sind idempotent)"
                    ),
                    line=node.span.start_line if node.span else None,
                    quick_fixes=(
                        QuickFix(
                            id="VAL-034.drop_machine",
                            title="MACHINE-Flag vom Registry-Aufruf entfernen",
                            replacement_line=fixed,
                        ),
                    ),
                )
            )
    return out


