"""Central quoting helpers for Empirum Setup.inf serialization.

The Empirum interpreter reads ``Key=Value`` lines literally — it has no
INI-style quote-stripping layer. Setup.inf values are therefore NEVER
re-quoted on write: wrapping values in quotes and doubling
inner quotes breaks multi-field keys (Text1..Text9, [Options],
UninstallDisplayIcon, CopyDialogRect) and the ``%HKLM,"path","value"%``
notation, and the package dies silently in Setup.exe/Package Editor.

Quotes only appear where the Empirum syntax itself prescribes them (fields
inside multi-field values, reg DATA fields, command arguments); those quotes
are part of the value text and round-trip untouched.
"""

from __future__ import annotations

import re

# Characters that require INI-style quoting — ONLY relevant for dedicated
# contexts that explicitly demand quoted fields (q_path/q_reg_field), never
# for Key=Value serialization.
_NEEDS_QUOTE_VALUE = re.compile(r'[\s;="]')


class Quoter:
    """Empirum-oriented quoting. Key=Value values are literal (VAL-002)."""

    @staticmethod
    def q_key_value(key: str, value: str) -> str:
        # Never quote: the interpreter treats the value after '=' as a
        # literal string; any '"' belongs to the value itself.
        return f"{key}={value}"

    @staticmethod
    def q_value(value: str) -> str:
        # Identity by contract: Setup.inf values are written exactly as given.
        return value

    @staticmethod
    def q_path(path: str) -> str:
        """Quote filesystem paths for contexts whose syntax requires quotes.

        NOT for Key=Value serialization — use q_key_value there.
        """
        return _quote_ini(path)

    @staticmethod
    def q_reg_field(field: str) -> str:
        """Quote a registry field for contexts whose syntax requires quotes."""
        return _quote_ini(field)

    @staticmethod
    def unquote(value: str) -> str:
        # Identity by contract (round-trip guarantee): quotes inside a
        # Key=Value value are content, not markers.
        return value

    @staticmethod
    def strip_optional_quotes(value: str) -> str:
        """Tolerantly drop ONE surrounding quote pair for semantic comparison.

        Read-only checks may use this to accept the canonical quoted form
        (e.g. ``SrcDir=".."``); serialization must NOT — see q_key_value.
        """
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1]
        return value


def _quote_ini(value: str) -> str:
    """INI-style quoting for dedicated field contexts (inner quotes doubled)."""
    if value == "":
        return ""
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value
    if _NEEDS_QUOTE_VALUE.search(value) or value.startswith(" ") or value.endswith(" "):
        escaped = value.replace('"', '""')
        return f'"{escaped}"'
    return value
