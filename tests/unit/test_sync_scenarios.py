"""Automated Dual-View sync scenarios (Phase-3 core)."""

from __future__ import annotations

from empirum_core.ast.model import KeyValueLine
from empirum_core.serializer.serialize import serialize_document
from empirum_services.editor.sync import EditOrigin, SyncController


def test_sync_code_to_visual_updates_ast() -> None:
    sync = SyncController()
    sync.apply_code_edit("[SetupInfo]\r\nProductName=Alpha\r\n")
    assert sync.document.section("SetupInfo") is not None
    kv = sync.document.section("SetupInfo").lines[0]
    assert isinstance(kv, KeyValueLine)
    assert kv.value == "Alpha"
    assert sync._state.last_origin == EditOrigin.CODE


def test_sync_visual_to_code() -> None:
    sync = SyncController()
    sync.apply_code_edit("[SetupInfo]\r\nProductName=A\r\n")
    doc = sync.document
    section = doc.section("SetupInfo")
    assert section is not None
    for node in section.lines:
        if isinstance(node, KeyValueLine) and node.key == "ProductName":
            node.value = "Beta"
            node.preserve_raw = False
            node.raw = None
    state = sync.apply_visual_patch(doc)
    assert state is not None
    assert "ProductName=Beta" in state.text.replace(" ", "")
    assert state.last_origin == EditOrigin.VISUAL


def test_sync_version_gate_blocks_stale() -> None:
    sync = SyncController()
    sync.apply_code_edit("[A]\r\nK=1\r\n")
    v = sync.version
    assert sync.apply_code_edit("[A]\r\nK=2\r\n", expected_version=v) is not None
    assert sync.apply_visual_patch(sync.document, expected_version=0) is None


def test_sync_no_feedback_loop_on_reapply_same() -> None:
    sync = SyncController()
    text = "[SetupInfo]\r\nProductName=Z\r\n"
    sync.apply_code_edit(text)
    v1 = sync.version
    # Re-serialize and apply as visual should bump version but stay consistent
    sync.apply_visual_patch(sync.document)
    assert "ProductName=Z" in serialize_document(sync.document)
    assert sync.version > v1


def test_sync_load_bytes_preserves_sections() -> None:
    sync = SyncController()
    data = b"[SetupInfo]\r\nProductName=Load\r\n\r\n[Set_Install]\r\nEcho=hi\r\n"
    state = sync.load_bytes(data)
    assert state.document.section("Set_Install") is not None
    assert state.last_origin == EditOrigin.SYSTEM
