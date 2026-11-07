"""Linter package – built-in VAL rule catalogue (Empirum-Paket-Standard structure)."""

from empirum_core.linter.engine import (
    Diagnostic,
    LintOptions,
    QuickFix,
    Rule,
    Severity,
    builtin_rules,
    lint_document,
)

__all__ = [
    "Diagnostic",
    "LintOptions",
    "QuickFix",
    "Rule",
    "Severity",
    "builtin_rules",
    "lint_document",
]
