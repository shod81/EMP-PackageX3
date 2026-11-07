"""Standard skeleton repair: add missing standard sections + canonical [Product] refs.

VAL-012 reports missing standard sections (typical for migrated
packages). This module resolves them: missing sections are appended in the
canonical standard order and, optionally, the canonical '#'-calls are ensured in
[Product] exactly as the wizard templates emit them.

New sections are empty, behavior-neutral stubs - with two deliberate exceptions:

- the three error handlers are created with the shared canonical bodies
  (``setupinf_contract.ERROR_SECTION_BODIES`` - ``ErrorLogMsg`` + ``Abort``,
  negated in the deinstallation path), so a repaired package aborts like a
  reference package, and
- ``[RebootRequired]`` stays empty: the template body (``SetReboot 1``) would
  turn a structural repair into a forced reboot.

Sections that already exist are never touched.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from empirum_core.ast.model import (
    CommentLine,
    Document,
    KeyValueLine,
    LineNode,
    RawLine,
    Section,
    append_section,
)
from empirum_core.parser.work import recompute_spans
from empirum_core.setupinf_contract import (
    ERROR_SECTION_BODIES,
    PRODUCT_REFS,
    STANDARD_SECTIONS,
    USER_PART_PRODUCT_REF,
)

# Canonical refs + error-handler bodies now live in empirum_core.setupinf_contract,
# shared with the wizard templates, so the two can never drift apart (this is
# what keeps a repaired package's uninstall order identical to a generated
# one). Shell:Product is deliberately absent from PRODUCT_REFS: it
# auto-runs via ShellLinks=1 and a #Shell ref would duplicate links (VAL-005).

_HASH_TOKEN_RE = re.compile(r"#!?\s*([A-Za-z_][A-Za-z0-9_]*\s*:\s*[A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True, slots=True)
class SkeletonRepair:
    """Result of a skeleton repair: what was added (canonical names)."""

    added_sections: list[str]
    added_refs: list[str]


def missing_standard_sections(document: Document) -> list[str]:
    """Standard section names missing from the document (canonical order)."""
    present = {s.name.casefold() for s in document.sections}
    return [name for name in STANDARD_SECTIONS if name.casefold() not in present]


def add_missing_standard_sections(
    document: Document,
    *,
    add_product_refs: bool = True,
) -> SkeletonRepair:
    """Append missing standard sections and ensure [Product] refs.

    Sections are appended at the document end in canonical standard order; the three
    error handlers are created with their canonical abort body (see
    ``setupinf_contract.ERROR_SECTION_BODIES``), everything else as an empty stub.
    For every canonical target the matching '#'-call is inserted into [Product]
    unless a call to that section already exists (case-insensitive). Idempotent:
    a second call adds nothing.
    """
    known = {s.name.casefold(): s for s in document.sections}
    added_sections: list[str] = []

    for name in STANDARD_SECTIONS:
        if name.casefold() in known:
            continue
        section = Section(
            name=name,
            header_raw=name,
            lines=[RawLine(text=line) for line in ERROR_SECTION_BODIES.get(name, ())],
        )
        # Keeps the one-blank-line gap prettify would add (repair output is
        # expected to look canonical straight away).
        append_section(document, section)
        known[name.casefold()] = section
        added_sections.append(name)

    added_refs: list[str] = []
    if add_product_refs:
        # Empirum merges duplicate sections: scan ALL [Product] sections for
        # existing refs, insert new ones into the first.
        products = [s for s in document.sections if s.name.casefold() == "product"]
        existing_tokens: set[str] = set()
        for section in products:
            existing_tokens |= _existing_ref_tokens(section)
        if products:
            for target, ref_line in PRODUCT_REFS:
                # Only call sections that exist or were just created.
                target_key = target.casefold()
                if target_key not in known:
                    continue
                if target_key in existing_tokens:
                    continue
                _insert_ref(products[0], ref_line)
                existing_tokens.add(target_key)
                added_refs.append(ref_line)
            # User part: a [Set:Client] section without a
            # #Set:Client call would never execute. The repair never CREATES
            # the section (it cannot invent user commands), it only wires an
            # existing user part into [Product] with the canonical CLIENT ref.
            client_ref, client_call = USER_PART_PRODUCT_REF
            if client_ref.casefold() in known and client_ref.casefold() not in existing_tokens:
                _insert_ref(products[0], client_call)
                existing_tokens.add(client_ref.casefold())
                added_refs.append(client_call)

    if added_sections or added_refs:
        recompute_spans(document)
    return SkeletonRepair(added_sections=added_sections, added_refs=added_refs)


def _insert_ref(product: Section, ref_line: str) -> None:
    """Insert a '#'-call above the trailing blank lines of [Product].

    Inserting *after* a trailing blank would eat the section gap and glue the
    next header to [Product] (prettify would then add a line on top of it), so
    the ref goes in front of the blank run.
    """
    index = len(product.lines)
    while index and _is_blank(product.lines[index - 1]):
        index -= 1
    product.lines.insert(index, RawLine(text=ref_line))


def _is_blank(node: LineNode) -> bool:
    return isinstance(node, RawLine) and node.text == ""


def _existing_ref_tokens(product: Section) -> set[str]:
    """Casefolded '#Kind:Name' tokens already called from [Product] (active lines)."""
    tokens: set[str] = set()
    for node in product.lines:
        if isinstance(node, CommentLine):
            continue
        if isinstance(node, KeyValueLine):
            text = node.raw or f"{node.key}={node.value}"
        elif isinstance(node, RawLine):
            text = node.text
        else:
            continue
        if text.lstrip().startswith(";"):
            continue
        for match in _HASH_TOKEN_RE.finditer(text):
            tokens.add(re.sub(r"\s+", "", match.group(1)).casefold())
    return tokens
