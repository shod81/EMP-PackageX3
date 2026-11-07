"""Regression: Setup.inf Key=Value values are literal.

The Empirum interpreter has no INI quote-stripping layer. Re-quoting values
on write (spaces/commas/% → wrap in quotes, inner quotes doubled) destroys
multi-field keys (Text1..Text9, [Options], UninstallDisplayIcon,
CopyDialogRect) and the %HKLM,"path","value"% notation – the package then
dies silently in Setup.exe/Package Editor. These tests pin the working
reference form (reference templates / templates/__init__.py) through every write
path: prettify (clears preserve_raw on ALL KV lines – the worst case),
touch_key_value, fresh KV nodes and linter quick-fixes.
"""

from __future__ import annotations

from empirum_core.linter import lint_document
from empirum_core.parser.lexer import lex_document, lex_text
from empirum_core.prettify import prettify_document
from empirum_core.quoting.quote import Quoter
from empirum_core.serializer.serialize import (
    serialize_document,
    serialize_to_bytes,
    touch_key_value,
)

# Working reference lines (standard form, cf. empirum_core/templates/__init__.py).
# The §8 corruption turned these into e.g.
#   Text1="""%ProductName% %Version%"",  Arial, …"   or
#   V_UserValuesPath="%HKLM,""Software\matrix42\Software Depot"",""HomeServer""%…"
REFERENCE = (
    "[SetupInfo]\r\n"
    "Method=Unattend\r\n"
    "\r\n"
    "[Application]\r\n"
    "ProductName=Fix LoadingSpeed in 24H2\r\n"
    'Text1="%ProductName% %Version%",         Arial,           30, , 2170F3, 4,    , LEFT BOLD ITALIC\r\n'
    'Text9="%InstallationFor% %WindowsUser%", Arial,           16, , 2170F3, 4, -18, BOTTOM ITALIC LEFT\r\n'
    "CopyDialogRect=0%, 0%, 100%, 100%, HCENTER VCENTER\r\n"
    'ReinstallString="%CommonSetupDir%\\Setup.exe" "%App%\\%SetupInfDir%\\Setup.inf"\r\n'
    'UninstallDisplayIcon="%ApplicationDir%\\%SetupInfDir%\\Setup.ico",0\r\n'
    "SrcDir=..\r\n"
    "SetupInfDir=Install\r\n"
    "ShellLinks=1\r\n"
    "\r\n"
    "[Environment]\r\n"
    'V_UserValuesPath=%HKLM,"Software\\matrix42\\Software Depot","HomeServer"%\\Values$\\UserValues\\%UserDomain%\r\n'
    "\r\n"
    "[Options]\r\n"
    'Installer=%InstallerName%, COPYALWAYS, Installer, "%InstallerDesc%"\r\n'
    'Product=%ProductName%,   COPYALWAYS, Product,   "%ProductDesc%"\r\n'
)

# Forbidden §8 corruption patterns (value-level quoting artifacts).
CORRUPTION_FRAGMENTS = (
    'Text1="""',
    '""%Version%""',
    'V_UserValuesPath="%HKLM,""',
    ',""HomeServer""%',
    'Installer="%InstallerName%, COPYALWAYS',
    '""%InstallerDesc%"""',
    'ProductName="Fix LoadingSpeed in 24H2"',
)


def _lines(text: str) -> list[str]:
    return text.split("\r\n")


def test_reference_roundtrip_byte_identical() -> None:
    data = REFERENCE.encode("cp1252")
    assert serialize_to_bytes(lex_document(data).document) == data


def test_prettify_never_requotes_values() -> None:
    """Prettify clears preserve_raw on every KV line — values must stay literal."""
    pretty = serialize_document(prettify_document(lex_text(REFERENCE)))
    for line in _lines(REFERENCE):
        if line and not line.startswith("["):
            assert f"\r\n{line}\r\n" in f"\r\n{pretty}", f"prettify altered: {line!r}"
    for fragment in CORRUPTION_FRAGMENTS:
        assert fragment not in pretty, f"§8 corruption re-introduced: {fragment!r}"


def test_prettify_idempotent_after_fix() -> None:
    once = serialize_document(prettify_document(lex_text(REFERENCE)))
    twice = serialize_document(prettify_document(lex_text(once)))
    assert once == twice


def test_touch_key_value_keeps_other_lines_raw() -> None:
    doc = lex_text(REFERENCE)
    app = doc.section("Application")
    assert app is not None
    touched = touch_key_value(app, "ProductName", "Neuer Name mit Leerzeichen")
    assert touched is not None
    text = serialize_document(doc)
    assert "ProductName=Neuer Name mit Leerzeichen\r\n" in text
    # Untouched multi-field lines keep their exact raw form (no requote).
    assert (
        'Text1="%ProductName% %Version%",         Arial,           30, , 2170F3, 4,    , LEFT BOLD ITALIC\r\n'
        in text
    )
    for fragment in CORRUPTION_FRAGMENTS:
        assert fragment not in text


def test_fresh_kv_node_serializes_literal() -> None:
    from empirum_core.ast.model import Document, KeyValueLine, Section

    doc = Document(
        sections=[
            Section(
                name="Application",
                lines=[
                    KeyValueLine(
                        key="Text1",
                        value='"%ProductName%", Arial, 30',
                        preserve_raw=False,
                    )
                ],
            )
        ]
    )
    assert serialize_document(doc) == '[Application]\r\nText1="%ProductName%", Arial, 30\r\n'


def test_val_003_quickfix_preserves_author_quotes() -> None:
    text = '[Set_Uninstall]\r\nDelTree="%Dst%\\App\\"\r\n'
    diags = [d for d in lint_document(lex_text(text)) if d.code == "VAL-003"]
    assert diags, "quoted DelTree with trailing backslash must still be flagged"
    assert diags[0].quick_fixes[0].replacement_line == 'DelTree="%Dst%\\App"'
    # Unquoted form stays unquoted.
    plain = lint_document(lex_text("[Set_Uninstall]\r\nDelTree=%Dst%\\App\\\r\n"))
    plain_003 = [d for d in plain if d.code == "VAL-003"]
    assert plain_003[0].quick_fixes[0].replacement_line == "DelTree=%Dst%\\App"


def test_semantic_checks_accept_quoted_canonical_form() -> None:
    """SrcDir/SetupInfDir/ShellLinks comparisons tolerate the quoted standard form."""
    text = (
        "[Application]\r\n"
        'SrcDir=".."\r\n'
        'SetupInfDir="Install"\r\n'
        'ShellLinks="1"\r\n'
    )
    diags = lint_document(lex_text(text))
    assert not any(d.code == "VAL-015" for d in diags)
    # And the tolerant helper never touches the value itself.
    assert Quoter.unquote('"1"') == '"1"'
