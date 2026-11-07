"""Execution-order projection of a Setup.inf (install/uninstall learning view).

Implements the reference semantics (Kap. 5, verified OP-008 against the
26.1.0 interpreter):
- Install: [Product] top-down; DONTDELETE/unflagged refs run, DELETE skipped;
  inside sections only lines WITHOUT a '-' prefix run.
- Uninstall: [Product] bottom-up; DELETE/unflagged refs run, DONTDELETE skipped;
  inside sections only '-'-prefixed command lines run (If/# lines carry no '-')
  PLUS the always-both commands (AddMeter, Beep, CD, Rem, ReplaceEnv, Set),
  which run in both directions without '-'. Copy/MD/MkDir/Ren/Rename without
  '-' are auto-reversed by the interpreter undo log instead.
- [Shell:<Name>] runs automatically LAST on install / FIRST on uninstall
  when [Application] ShellLinks=1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from emp_packagex3.learning_content import COMMAND_DOCS
from empirum_core.ast.model import CommentLine, Document, KeyValueLine, RawLine, Section
from empirum_core.setupinf_contract import (
    SETUPINF_ALWAYS_BOTH_COMMANDS,
    SETUPINF_AUTO_REVERSED_COMMANDS,
)

_REF_RE = re.compile(r"#!?\s*(?P<kind>Set|Shell|Reg|Ini|Security)\s*:\s*(?P<name>[^\s,\]]+)")
_COMMAND_RE = re.compile(r"^-?([A-Za-z_][A-Za-z0-9_]*)")
_COMMAND_LOOKUP = {key.casefold(): doc for key, doc in COMMAND_DOCS.items()}
_ALWAYS_BOTH_CF = frozenset(c.casefold() for c in SETUPINF_ALWAYS_BOTH_COMMANDS)
_AUTO_REVERSED_CF = frozenset(c.casefold() for c in SETUPINF_AUTO_REVERSED_COMMANDS)


@dataclass(frozen=True, slots=True)
class ExecStep:
    order: int
    section: str
    line_no: int | None
    text: str
    kind: str  # command | ref | shell-auto | info
    note: str


def execution_steps(document: Document, *, uninstall: bool) -> list[ExecStep]:
    """Numbered steps in true execution order for the requested direction."""
    steps: list[ExecStep] = []
    visited: set[str] = set()

    shell_sections = _auto_shell_sections(document)
    if uninstall and shell_sections:
        for name in shell_sections:
            steps.append(
                ExecStep(
                    order=0,
                    section=name,
                    line_no=None,
                    text=f"[{name}] läuft automatisch zuerst (ShellLinks=1)",
                    kind="shell-auto",
                    note="Verknüpfungen entfernen",
                )
            )

    product = document.section("Product")
    if product is not None:
        refs = _product_refs(product)
        ordered = refs[::-1] if uninstall else refs
        for ref in ordered:
            if uninstall and "DONTDELETE" in ref.flags:
                continue
            if not uninstall and "DELETE" in ref.flags and "DONTDELETE" not in ref.flags:
                continue
            # Der Aufruf selbst ist ein Schritt (GOSUB sichtbar halten)
            steps.append(
                ExecStep(0, "Product", None, ref.text, "ref",
                         "Unterprogramm-Aufruf (GOSUB)")
            )
            target = _resolve_target(document, ref.kind, ref.name)
            _walk(document, target, steps, visited, uninstall=uninstall)

    if not uninstall and shell_sections:
        for name in shell_sections:
            steps.append(
                ExecStep(
                    order=0,
                    section=name,
                    line_no=None,
                    text=f"[{name}] läuft automatisch zuletzt (ShellLinks=1)",
                    kind="shell-auto",
                    note="Verknüpfungen erstellen",
                )
            )

    for index, step in enumerate(steps, start=1):
        steps[index - 1] = ExecStep(
            order=index,
            section=step.section,
            line_no=step.line_no,
            text=step.text,
            kind=step.kind,
            note=step.note,
        )
    return steps


@dataclass(frozen=True, slots=True)
class _Ref:
    kind: str
    name: str
    flags: str
    text: str


def _product_refs(product: Section) -> list[_Ref]:
    refs: list[_Ref] = []
    for node in product.lines:
        text = _node_text(node)
        if not text or text.lstrip().startswith(";"):
            continue
        match = _REF_RE.search(text)
        if match:
            flags = text[match.end() :].upper()
            refs.append(
                _Ref(
                    kind=match.group("kind"),
                    name=match.group("name"),
                    flags=flags,
                    text=text.strip(),
                )
            )
    return refs


def _walk(
    document: Document,
    section_name: str,
    steps: list[ExecStep],
    visited: set[str],
    *,
    uninstall: bool,
) -> None:
    key = section_name.casefold()
    if key in visited:
        return
    visited.add(key)
    section = document.section(section_name)
    if section is None:
        steps.append(
            ExecStep(0, section_name, None, f"[{section_name}] fehlt", "info", "")
        )
        return
    lines = section.lines
    if uninstall:
        lines = lines[::-1]
    for node in lines:
        text = _node_text(node)
        if not text:
            continue
        stripped = text.strip()
        if stripped.startswith(";"):
            continue
        is_minus = stripped.startswith("-")
        if uninstall:
            note = command_note(stripped)
            if not is_minus and not _is_control_line(stripped):
                token_match = _COMMAND_RE.match(stripped)
                token = token_match.group(1).casefold() if token_match else ""
                if token in _ALWAYS_BOTH_CF:
                    pass  # verified: runs in both directions without '-'
                elif token in _AUTO_REVERSED_CF:
                    note = "automatisch rückgängig (Interpreter-Undo-Log)"
                else:
                    continue  # install-only command
        else:
            if is_minus:
                continue  # uninstall-only command
        steps.append(
            ExecStep(
                0,
                section.name,
                node.span.start_line if node.span else None,
                stripped,
                "command",
                command_note(stripped) if not uninstall else note,
            )
        )
        # Follow only pure '#' calls; If/Then targets are conditional jumps
        # and stay visible as their own step.
        if stripped.startswith("#"):
            match = _REF_RE.search(stripped)
            if match:
                target = _resolve_target(document, match.group("kind"), match.group("name"))
                _walk(document, target, steps, visited, uninstall=uninstall)


def _resolve_target(document: Document, kind: str, name: str) -> str:
    """#Set:X -> [Set:X] first, bare [X] second (reference resolution)."""
    known = {s.name.casefold(): s.name for s in document.sections}
    for candidate in (f"{kind}:{name}", name):
        hit = known.get(candidate.casefold())
        if hit is not None:
            return hit
    return name


def _is_control_line(stripped: str) -> bool:
    """If-Abfragen und #-Aufrufe tragen kein '-' (Referenz Kap. 5)."""
    low = stripped.casefold()
    return low.startswith("if ") or stripped.startswith("#")


def _auto_shell_sections(document: Document) -> list[str]:
    app = document.section("Application")
    if app is None:
        return []
    for node in app.lines:
        if (
            isinstance(node, KeyValueLine)
            and node.key.casefold() == "shelllinks"
            and node.value.strip().casefold() in {"1", "yes", "true", "on"}
        ):
            return [
                s.name
                for s in document.sections
                if s.name.casefold().startswith("shell:")
            ]
    return []


def command_note(text: str) -> str:
    match = _COMMAND_RE.match(text)
    if match:
        doc = _COMMAND_LOOKUP.get(match.group(1).casefold())
        if doc is not None:
            return doc.semantics.split(". ")[0] + "."
    if text.startswith("#"):
        return "Unterprogramm-Aufruf (GOSUB)"
    return ""


def _node_text(node: object) -> str:
    if isinstance(node, KeyValueLine):
        return node.raw or f"{node.key}={node.value}"
    if isinstance(node, RawLine):
        return node.text
    if isinstance(node, CommentLine):
        return node.raw or f";{node.text}"
    return ""
