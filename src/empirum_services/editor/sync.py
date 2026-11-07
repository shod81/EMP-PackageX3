"""Dual-view synchronisation controller (AST as SSOT)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from empirum_core.ast.model import Document
from empirum_core.parser.lexer import lex_text
from empirum_core.serializer.serialize import serialize_document


class EditOrigin(StrEnum):
    CODE = "code"
    VISUAL = "visual"
    SYSTEM = "system"


@dataclass(slots=True)
class SyncState:
    document: Document
    text: str
    version: int = 0
    last_origin: EditOrigin = EditOrigin.SYSTEM


@dataclass
class SyncController:
    """Single-writer sync with version token to prevent feedback loops."""

    debounce_ms: int = 150
    _state: SyncState = field(init=False)
    _applying: bool = field(default=False, init=False)
    _encoding_ambiguous: bool = field(default=False, init=False)
    _read_only: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        empty = lex_text("[SetupInfo]\r\nProductName=\r\n")
        self._state = SyncState(document=empty, text=serialize_document(empty))

    @property
    def version(self) -> int:
        return self._state.version

    @property
    def document(self) -> Document:
        return self._state.document

    @property
    def text(self) -> str:
        return self._state.text

    @property
    def encoding_ambiguous(self) -> bool:
        return self._encoding_ambiguous

    @property
    def read_only(self) -> bool:
        return self._read_only

    def set_encoding(self, encoding_name: str, *, has_bom: bool = False) -> None:
        self._state.document.encoding_name = encoding_name
        self._state.document.has_bom = has_bom
        self._state.version += 1  # waiting UIs must observe the change
        self._encoding_ambiguous = False
        self._read_only = False

    def load_bytes(self, data: bytes) -> SyncState:
        from empirum_core.parser.encoding import detect_encoding
        from empirum_core.parser.lexer import lex_document
        from empirum_core.serializer.serialize import serialize_to_bytes

        detected = detect_encoding(data)
        result = lex_document(data, encoding=detected)
        text = serialize_document(result.document)
        again = serialize_to_bytes(result.document)
        if again == data:
            text = data.decode(result.document.encoding_name, errors="replace")
            text = text.lstrip("\ufeff\xef\xbb\xbf")
        self._encoding_ambiguous = detected.ambiguous
        self._read_only = detected.ambiguous
        self._state = SyncState(
            document=result.document,
            text=text,
            version=self._state.version + 1,
            last_origin=EditOrigin.SYSTEM,
        )
        return self._state

    def apply_code_edit(
        self, text: str, *, expected_version: int | None = None
    ) -> SyncState | None:
        if self._applying:
            return None
        if expected_version is not None and expected_version != self._state.version:
            return None
        self._applying = True
        try:
            normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
            doc = lex_text(normalized, encoding_name=self._state.document.encoding_name)
            doc.has_bom = self._state.document.has_bom
            self._state = SyncState(
                document=doc,
                text=normalized,
                version=self._state.version + 1,
                last_origin=EditOrigin.CODE,
            )
            return self._state
        finally:
            self._applying = False

    def apply_visual_patch(
        self, document: Document, *, expected_version: int | None = None
    ) -> SyncState | None:
        if self._applying:
            return None
        if expected_version is not None and expected_version != self._state.version:
            return None
        self._applying = True
        try:
            text = serialize_document(document)
            self._state = SyncState(
                document=document,
                text=text,
                version=self._state.version + 1,
                last_origin=EditOrigin.VISUAL,
            )
            return self._state
        finally:
            self._applying = False
