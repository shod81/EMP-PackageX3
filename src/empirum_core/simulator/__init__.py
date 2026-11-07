"""Execution-flow dry-run simulator (no side effects)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

from empirum_core.ast.model import Document, KeyValueLine, RawLine, Section
from empirum_core.parser import work as W
from empirum_core.setupinf_contract import (
    SETUPINF_ALWAYS_BOTH_COMMANDS,
    SETUPINF_AUTO_REVERSED_COMMANDS,
)


class SimMode(StrEnum):
    INSTALL = "install"
    UNINSTALL = "uninstall"


@dataclass(slots=True)
class SimAction:
    section: str
    line: int
    command: str
    detail: str


@dataclass(slots=True)
class SystemState:
    """Fictional machine state for dry-run."""

    files: set[str] = field(default_factory=set)
    reg_keys: set[str] = field(default_factory=set)
    variables: dict[str, str] = field(default_factory=dict)
    reboot_requested: bool = False
    terminated_processes: set[str] = field(default_factory=set)
    services: dict[str, bool] = field(default_factory=dict)
    shutdown_requested: bool = False


@dataclass(slots=True)
class SimReport:
    mode: SimMode
    actions: list[SimAction] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    final_state: SystemState = field(default_factory=SystemState)
    entry_section: str = ""


_REG_LINE_RE = re.compile(
    r'^-?\s*(HKLM|HKCU|HKCR|HKU|HKCC)\s*,\s*(?:"([^"]*)"|([^,\r\n]+))',
    re.IGNORECASE,
)
_SET_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
_VAR_USE_RE = re.compile(r"%([$A-Za-z0-9_().]+)%")

# Verified uninstall semantics (Legacy-Help, verified 26.1.0):
# '-'-prefixed lines run ONLY at uninstall; non-'-' lines only at install —
# except commands that run in BOTH directions …
_ALWAYS_BOTH_CF = frozenset(c.casefold() for c in SETUPINF_ALWAYS_BOTH_COMMANDS)
# … and commands the interpreter reverses automatically on /U (undo log).
_AUTO_REVERSED_CF = frozenset(c.casefold() for c in SETUPINF_AUTO_REVERSED_COMMANDS)
# Control lines carry no '-' (reference) and stay visible in both directions —
# they route flow instead of causing side effects.
_CONTROL_CF = frozenset({"if", "else", "endif", "for", "next"})

_DECLARE_SECTION_PREFIXES = ("reg:", "ini:", "security:", "shell:", "bat:")


def _is_command_section(name: str) -> bool:
    n = name.casefold()
    if n.startswith(_DECLARE_SECTION_PREFIXES):
        return False
    return n.startswith(("set:", "set_", "product", "install", "uninstall", "deinstall"))


def _line_runs_in_mode(text: str, mode: SimMode) -> tuple[bool, str]:
    """(runs, note) for a statement line under the verified OP-008 rules."""
    stripped = text.lstrip()
    has_minus = stripped.startswith("-")
    if mode == SimMode.INSTALL:
        return (not has_minus, "")
    if has_minus:
        return (True, "")
    token = stripped.split(None, 1)[0].casefold() if stripped else ""
    if token in _ALWAYS_BOTH_CF or token in _CONTROL_CF:
        return (True, "")
    if token in _AUTO_REVERSED_CF:
        return (True, "automatisch rückgängig (Interpreter-Undo-Log)")
    return (False, "")


def _resolve_vars(text: str, variables: dict[str, str]) -> str:
    def _repl(m: re.Match[str]) -> str:
        k = m.group(1)
        for vk, vv in variables.items():
            if vk.casefold() == k.casefold():
                return vv
        return m.group(0)

    return _VAR_USE_RE.sub(_repl, text)


def _init_state_from_document(
    document: Document, state: SystemState, mode: SimMode
) -> None:
    defaults = {
        "WinDir": r"C:\Windows",
        "System": r"C:\Windows\System32",
        "ProgramFiles": r"C:\Program Files",
        "ProgramFiles(x86)": r"C:\Program Files (x86)",
        "CommonFilesDir": r"C:\Program Files\Common Files",
        "CommonAppData": r"C:\ProgramData",
        "Temp": (
            r"C:\Windows\Temp"
            if mode == SimMode.INSTALL
            else r"C:\Users\SimUser\AppData\Local\Temp"
        ),
        "ComputerName": "SIMULATED-PC",
        "WindowsUser": "SYSTEM" if mode == SimMode.INSTALL else "SimUser",
        "ErrorLevel": "0",
    }
    state.variables.update(defaults)

    dev = "Vendor"
    prod = "App"
    ver = "1.0"
    rev = "0"
    app_sec = document.section("Application")
    if app_sec is not None:
        for node in app_sec.lines:
            if isinstance(node, KeyValueLine):
                k = node.key.strip()
                v = node.value.strip().strip('"')
                state.variables[k] = v
                k_cf = k.casefold()
                if k_cf == "productname":
                    prod = v
                elif k_cf == "developername":
                    dev = v
                elif k_cf == "version":
                    ver = v
                elif k_cf == "revision":
                    rev = v
                elif k_cf == "applicationdir":
                    state.variables["App"] = v
                elif k_cf == "srcdir":
                    state.variables["Src"] = v

    if "App" not in state.variables:
        state.variables["App"] = rf"C:\Program Files\{dev}\{prod}"
    if "Src" not in state.variables:
        state.variables["Src"] = rf"C:\EmpirumAgent\PackageStore\{dev}\{prod}\{ver}"
    if "ProductName" not in state.variables:
        state.variables["ProductName"] = prod
    if "DeveloperName" not in state.variables:
        state.variables["DeveloperName"] = dev
    if "Version" not in state.variables:
        state.variables["Version"] = ver
    if "Revision" not in state.variables:
        state.variables["Revision"] = rev

    for sec_name in ("Environment", "Strings", "SysStrings", "VarDefInfo"):
        sec = document.section(sec_name)
        if sec is not None:
            for node in sec.lines:
                if isinstance(node, KeyValueLine):
                    state.variables[node.key.strip()] = node.value.strip().strip('"')


def _apply_action_to_state(
    section_name: str,
    cmd_or_key: str,
    detail_or_val: str,
    report: SimReport,
    *,
    raw_text: str = "",
) -> None:
    state = report.final_state
    if section_name.casefold().startswith("reg:"):
        text_to_check = raw_text or f"{cmd_or_key} {detail_or_val}".strip()
        m = _REG_LINE_RE.match(text_to_check)
        if m:
            root = m.group(1).upper()
            subkey = (m.group(2) or m.group(3) or "").strip()
            entry = f"{root}\\{subkey}" if subkey else root
            is_uninst_minus = text_to_check.lstrip().startswith("-")
            if is_uninst_minus:
                if report.mode == SimMode.UNINSTALL:
                    state.reg_keys.discard(entry)
            else:
                if report.mode == SimMode.INSTALL:
                    state.reg_keys.add(entry)
                elif report.mode == SimMode.UNINSTALL:
                    state.reg_keys.discard(entry)
        return

    cmd_cf = cmd_or_key.strip().lstrip("-").casefold()
    detail = detail_or_val.strip()

    def _first_arg(text: str) -> str:
        return text.strip().strip('"').split(",")[0].strip()

    if cmd_cf in {"run", "call", "callhidden", "callrunas", "callrunashidden", "regasm"}:
        state.files.add(detail)
    elif cmd_cf == "deltree" or cmd_cf in {"del", "erase"}:
        resolved = _resolve_vars(detail.strip('"'), state.variables)
        state.files.discard(resolved)
        state.files.discard(detail)
    elif cmd_cf in {"md", "mkdir"}:
        resolved = _resolve_vars(detail.strip('"'), state.variables)
        state.files.add(resolved)
    elif cmd_cf in {"rd", "rmdir"}:
        resolved = _resolve_vars(detail.strip('"'), state.variables)
        state.files.discard(resolved)
    elif cmd_cf in {"rename", "ren", "rendir"}:
        parts = detail.split()
        if len(parts) >= 2:
            src = _resolve_vars(parts[0].strip('"'), state.variables)
            dst = _resolve_vars(parts[1].strip('"'), state.variables)
            state.files.discard(src)
            state.files.add(dst)
    elif cmd_cf == "copy":
        parts = detail.split(",")
        if len(parts) >= 2:
            dst = parts[1].strip().strip('"')
            resolved = _resolve_vars(dst, state.variables)
            state.files.add(resolved)
    elif cmd_cf in {"addservice"}:
        name = _first_arg(detail)
        if name:
            state.services[name] = False
    elif cmd_cf == "deleteservice":
        state.services.pop(_first_arg(detail), None)
    elif cmd_cf == "startservice":
        name = _first_arg(detail)
        if name:
            state.services[name] = True
    elif cmd_cf == "stopservice":
        name = _first_arg(detail)
        if name:
            state.services[name] = False
    elif cmd_cf == "systemshutdown":
        state.shutdown_requested = True
    elif cmd_cf in {"increment", "decrement", "multiply", "divide"}:
        target = detail.strip().strip("()").split(",")[0].strip()
        operand = "1"
        if "," in detail.strip().strip("()"):
            operand = detail.strip().strip("()").split(",", 1)[1].strip() or "1"
        for vk in list(state.variables.keys()):
            if vk.casefold() != target.casefold():
                continue
            try:
                cur = int(state.variables[vk] or "0")
                num = int(operand)
                if cmd_cf == "increment":
                    state.variables[vk] = str(cur + num)
                elif cmd_cf == "decrement":
                    state.variables[vk] = str(cur - num)
                elif cmd_cf == "multiply":
                    state.variables[vk] = str(cur * num)
                elif cmd_cf == "divide":
                    state.variables[vk] = str(cur // num) if num else state.variables[vk]
            except ValueError:
                pass  # non-numeric variable: leave untouched
            break
    elif cmd_cf.startswith("set ") or cmd_cf == "set":
        var_name = ""
        val = ""
        if cmd_cf.startswith("set "):
            var_name = cmd_or_key.strip()[4:].strip()
            val = detail.strip().strip('"')
        else:
            m = _SET_RE.match(detail)
            if m:
                var_name = m.group(1).strip()
                val = m.group(2).strip().strip('"')
        if var_name:
            state.variables[var_name] = val
    elif cmd_cf.startswith("replaceenv ") or cmd_cf == "replaceenv":
        var_name = (
            detail.strip()
            if cmd_cf == "replaceenv"
            else cmd_or_key.strip()[11:].strip()
        )
        if var_name:
            for k in list(state.variables.keys()):
                if k.casefold() == var_name.casefold():
                    state.variables[k] = _resolve_vars(state.variables[k], state.variables)
    elif cmd_cf.startswith("collapseenv ") or cmd_cf == "collapseenv":
        # Undocumented class-1 command: evaluate the function expression stored
        # in the variable (deferred evaluation, see PSTBackupInfo.inf usage).
        var_name = (
            detail.strip()
            if cmd_cf == "collapseenv"
            else cmd_or_key.strip()[12:].strip()
        )
        if var_name:
            for k in list(state.variables.keys()):
                if k.casefold() == var_name.casefold():
                    state.variables[k] = _resolve_vars(state.variables[k], state.variables)
    elif cmd_cf.startswith("setreboot ") or cmd_cf == "setreboot":
        state.reboot_requested = True
    elif cmd_cf.startswith("killprocess ") or cmd_cf == "killprocess":
        proc = (
            detail
            if cmd_cf == "killprocess"
            else cmd_or_key.strip()[11:].strip()
        )
        proc = _first_arg(proc)  # extended syntax: Name[,Timeout[,Abfrage]]
        if proc:
            state.terminated_processes.add(proc)
    elif cmd_cf.startswith("askkillprocesses ") or cmd_cf == "askkillprocesses":
        target = (
            detail.strip()
            if cmd_cf == "askkillprocesses"
            else cmd_or_key.strip()[17:].strip()
        )
        parts = [p.strip().strip('"') for p in target.split(",")]
        alias = parts[1] if len(parts) >= 2 else (parts[0] if parts else "")
        if alias:
            state.terminated_processes.add(alias)


def simulate(document: Document, mode: SimMode = SimMode.INSTALL) -> SimReport:
    report = SimReport(mode=mode, final_state=SystemState())
    _init_state_from_document(document, report.final_state, mode)
    start = _entry_section(document, mode)
    if start is None:
        wanted = (
            "[Product] / [Set:Product] / [Set_Install]"
            if mode == SimMode.INSTALL
            else "[Set:Deinstallation] / [Set_Uninstall] / [Product]"
        )
        report.gaps.append(f"Einstiegssektion fehlt (gesucht: {wanted})")
        return report

    report.entry_section = start
    visited: set[str] = set()
    _walk(document, start, report, visited)

    if mode == SimMode.INSTALL:
        uninstall = _first_existing(
            document,
            ("Set:Deinstallation", "Set_Deinstallation", "Set_Uninstall"),
        )
        if uninstall is None:
            report.gaps.append("Keine Deinstallations-Sektion (Set:Deinstallation / Set_Uninstall)")
        else:
            install_calls = _call_targets_from_report(report)
            uninstall_text = _section_blob(document.section(uninstall))
            for target in install_calls:
                if target and target.casefold() not in uninstall_text.casefold():
                    report.gaps.append(
                        f"Install-Aufruf ohne offensichtliches Uninstall-Pendant: {target}"
                    )
    return report


def _entry_section(document: Document, mode: SimMode) -> str | None:
    if mode == SimMode.INSTALL:
        return _first_existing(
            document,
            (
                "Product",
                "Set:Product",
                "Set_Product",
                "Set_Install",
                "InstallMSI",
                "Installation",
            ),
        )
    # Uninstall: prefer dedicated deinstall block; Product still useful for #-DELETE walk
    return _first_existing(
        document,
        (
            "Set:Deinstallation",
            "Set_Deinstallation",
            "Set_Uninstall",
            "Product",
        ),
    )


def _first_existing(document: Document, names: tuple[str, ...]) -> str | None:
    known = W.section_names(document)
    for name in names:
        if name.casefold() in known:
            # Preserve declared casing from the document
            for section in document.sections:
                if section.name.casefold() == name.casefold():
                    return section.name
    return None


def _walk(document: Document, section_name: str, report: SimReport, visited: set[str]) -> None:
    key = section_name.casefold()
    if key in visited:
        return
    visited.add(key)
    section = document.section(section_name)
    if section is None:
        report.gaps.append(f"Verweis auf fehlende Sektion [{section_name}]")
        return

    nodes = list(section.lines)
    if report.mode == SimMode.UNINSTALL:
        # Matrix42 Empirum Setup.exe /U executes sections and actions in reverse order (bottom-up)
        nodes.reverse()

    filter_lines = _is_command_section(section.name)

    for node in nodes:
        line_no = node.span.start_line if node.span else 0
        if isinstance(node, KeyValueLine):
            runs = True
            note = ""
            if filter_lines:
                runs, note = _line_runs_in_mode(node.key, report.mode)
            if runs:
                report.actions.append(
                    SimAction(section.name, line_no, node.key, node.value)
                )
                raw = node.raw or f"{node.key}={node.value}"
                if not note:
                    _apply_action_to_state(
                        section.name, node.key, node.value, report, raw_text=raw
                    )
        elif isinstance(node, RawLine):
            text = node.text.strip()
            if not text or text.startswith(";"):
                continue
            if text.startswith("#"):
                report.actions.append(SimAction(section.name, line_no, "ref", text))
            else:
                runs = True
                note = ""
                if filter_lines:
                    runs, note = _line_runs_in_mode(text, report.mode)
                if not runs:
                    continue
                parts = text.split(None, 1)
                cmd = parts[0].lstrip("-")
                detail = parts[1] if len(parts) > 1 else ""
                if note:
                    detail = f"{detail}  [{note}]" if detail else f"[{note}]"
                report.actions.append(SimAction(section.name, line_no, cmd, detail))
                _apply_action_to_state(
                    section.name, cmd, detail, report, raw_text=text
                )

    known = W.section_names(document)
    for node in nodes:
        text = ""
        if isinstance(node, KeyValueLine):
            text = node.raw or f"{node.key}={node.value}"
        elif isinstance(node, RawLine):
            text = node.text
        line_no = node.span.start_line if node.span else 0
        for ref in W.find_section_refs_in_text(text, line_no):
            # Reference chapter 5 semantics: install skips DELETE-marked refs,
            # uninstall skips DONTDELETE-marked refs.
            flags = text.casefold()
            if report.mode == SimMode.INSTALL and re.search(r"\bdelete\b", flags):
                continue
            if report.mode == SimMode.UNINSTALL and re.search(r"\bdontdelete\b", flags):
                continue
            # We still follow all other #refs for visibility; DELETE markers
            # are noted in the action detail.
            resolved = W.resolve_section_ref(ref, known)
            target = resolved or W.preferred_stub_section(ref)
            _walk(document, target, report, visited)


def _call_targets_from_report(report: SimReport) -> list[str]:
    out: list[str] = []
    for action in report.actions:
        if action.command.casefold() not in {"call", "callhidden", "run"}:
            continue
        if not action.detail:
            continue
        sec = action.section.casefold()
        if any(x in sec for x in ("deinstall", "uninstall", "reinstall")):
            continue
        detail = action.detail.strip()
        # MSI uninstall lines sometimes appear via shared refs – ignore /X
        if re.search(r"(?i)msiexec\s+/x\b", detail):
            continue
        out.append(detail)
    return out


def _section_blob(section: Section | None) -> str:
    if section is None:
        return ""
    parts: list[str] = []
    for node in section.lines:
        if isinstance(node, KeyValueLine):
            parts.append(node.raw or f"{node.key}={node.value}")
        else:
            parts.append(getattr(node, "text", "") or "")
    return "\n".join(parts)
