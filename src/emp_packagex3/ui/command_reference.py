"""Backward-compatible entry: Befehlsreferenz opens the structured Empirum help."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from emp_packagex3.learning_content import COMMAND_DOCS, CommandDoc, lookup_command
from emp_packagex3.ui.empirum_help import (
    EmpirumHelpDialog,
    render_hub_overview_html,
    topic_matches,
)
from empirum_core.setupinf_contract import SETUPINF_COMMANDS

# Re-exports used by tests
__all__ = [
    "CommandReferenceDialog",
    "command_matches",
    "iter_command_docs",
    "render_command_overview_html",
]


def iter_command_docs() -> list[CommandDoc]:
    docs: list[CommandDoc] = []
    for name in SETUPINF_COMMANDS:
        doc = lookup_command(name) or COMMAND_DOCS.get(name)
        if doc is not None:
            docs.append(doc)
    return docs


def command_matches(doc: CommandDoc, term: str) -> bool:
    return topic_matches("command", doc.name, term)


def render_command_overview_html(*, count: int, term: str = "", undocumented: bool = False) -> str:
    _ = count
    html = render_hub_overview_html(undocumented=undocumented)
    if term:
        return (
            f"<p>Filter: <b>{term}</b></p>" + html
        )
    return html


class CommandReferenceDialog(EmpirumHelpDialog):
    """Hilfe → Setup.inf-Befehlsreferenz (strukturierte Empirum-Hilfe)."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        tooltip_mode: bool = True,
        initial_command: str | None = None,
        undocumented: bool = False,
    ) -> None:
        initial = f"command:{initial_command}" if initial_command else "overview"
        super().__init__(
            parent, tooltip_mode=tooltip_mode, initial=initial, undocumented=undocumented
        )
        self.setWindowTitle("Setup.inf-Befehlsreferenz – EMP-PackageX3")
