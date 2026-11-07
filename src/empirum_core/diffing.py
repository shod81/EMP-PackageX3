"""Simple text diff between two Setup.inf projections."""

from __future__ import annotations

import difflib


def unified_inf_diff(left: str, right: str, *, fromfile: str = "a", tofile: str = "b") -> str:
    left_lines = left.replace("\r\n", "\n").splitlines(keepends=True)
    right_lines = right.replace("\r\n", "\n").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(left_lines, right_lines, fromfile=fromfile, tofile=tofile)
    )
