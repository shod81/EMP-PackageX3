"""Additional automated sync scenarios (toward plan target of 30)."""

from __future__ import annotations

import pytest

from empirum_core.ast.model import KeyValueLine
from empirum_core.parser.lexer import lex_text
from empirum_core.prettify import prettify_document, prettify_text
from empirum_core.serializer.serialize import serialize_document
from empirum_services.editor.sync import EditOrigin, SyncController

_SAMPLES = [
    "[SetupInfo]\r\nProductName=A\r\n",
    "[SetupInfo]\r\nProductName=B\r\nManufacturer=X\r\n",
    "[Application]\r\nReboot=0\r\nShellLinks=0\r\n",
    "[Set_Install]\r\nEcho=1\r\nEcho=2\r\n",
    "[Set_Uninstall]\r\nDelTree=%Dst%\r\n",
    "; comment only preamble\r\n[SetupInfo]\r\nProductName=C\r\n",
    "[Product]\r\n#Shell:CreateLinks\r\n\r\n[CreateLinks]\r\nLinkName=L\r\n",
    "[SetupInfo]\r\nProductName=\"Quoted Name\"\r\n",
    "[Set_Install]\r\nIf=FileExists(\"%App%\\x\")\r\n",
    "[Set_Install]\r\nCall=a.exe\r\nIf=%ErrorLevel%\r\n",
    "[Error_Uninstall]\r\n--Abort=fail\r\n",
    "[SetupInfo]\r\nProductName=Umlaut\r\n; äöü\r\n",
    "[A]\r\nK=1\r\n\r\n[B]\r\nK=2\r\n",
    "[SetupInfo]\r\nProductName=\r\n",
    "[Set_Registry]\r\nRoot=HKLM\r\nKey=Software\\X\r\n",
]


@pytest.mark.parametrize("sample", _SAMPLES, ids=[f"s{i}" for i in range(len(_SAMPLES))])
def test_sync_code_roundtrip_param(sample: str) -> None:
    sync = SyncController()
    state = sync.apply_code_edit(sample)
    assert state is not None
    again = serialize_document(state.document)
    # second parse stays stable
    sync2 = SyncController()
    sync2.apply_code_edit(again)
    assert sync2.document.structural_hash() == state.document.structural_hash()


@pytest.mark.parametrize("idx", list(range(10)))
def test_sync_visual_toggle_product_name(idx: int) -> None:
    sync = SyncController()
    sync.apply_code_edit(f"[SetupInfo]\r\nProductName=V{idx}\r\n")
    doc = sync.document
    section = doc.section("SetupInfo")
    assert section is not None
    for node in section.lines:
        if isinstance(node, KeyValueLine) and node.key == "ProductName":
            node.value = f"V{idx}X"
            node.preserve_raw = False
            node.raw = None
    state = sync.apply_visual_patch(doc)
    assert state is not None
    assert f"ProductName=V{idx}X" in state.text
    assert state.last_origin == EditOrigin.VISUAL


def test_prettify_adds_section_gap() -> None:
    text = "[A]\r\nK=1\r\n[B]\r\nK=2\r\n"
    out = prettify_text(text)
    assert "\r\n\r\n[B]" in out or "\r\n\r\n[B]\r\n" in out


def test_prettify_document_idempotent() -> None:
    doc = lex_text("[SetupInfo]\r\nProductName=X\r\n\r\n[Set_Install]\r\nEcho=1\r\n")
    once = prettify_document(doc)
    twice = prettify_document(once)
    assert serialize_document(once) == serialize_document(twice)
