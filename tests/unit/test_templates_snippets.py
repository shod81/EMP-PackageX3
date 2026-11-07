from empirum_core.inspect import PackageMetadata
from empirum_core.linter import lint_document
from empirum_core.setupinf_contract import (
    APPLICATION_KEYS,
    ERROR_SECTION_BODIES,
    MSI_INSTALL_FLAGS,
    PRODUCT_REFS,
    STANDARD_SECTIONS,
)
from empirum_core.snippets import get_snippet, snippet_names
from empirum_core.templates import render_template


def _meta(**kwargs) -> PackageMetadata:
    base = dict(
        product_name="Demo",
        product_version="1.2.3",
        manufacturer="Hodrius",
        source_path=r"C:\tmp\Demo.msi",
    )
    base.update(kwargs)
    return PackageMetadata(**base)


def test_all_templates_render_standard_sections() -> None:
    meta = _meta(source_path=r"C:\t\a.msi", exe_kind="NSIS")
    for kind in ("msi", "exe", "script", "links"):
        doc = render_template(kind, meta)
        names = {s.name.casefold() for s in doc.sections}
        for required in STANDARD_SECTIONS:
            assert required.casefold() in names, f"{kind}: missing [{required}]"


def test_snippets_available() -> None:
    assert "errorlevel-block" in snippet_names()
    assert 'If %ErrorLevel% == "3010" Then "RebootRequired" EndIf' in get_snippet(
        "errorlevel-block"
    )
    assert "reg-delete-install" in snippet_names()
    assert "reg.exe delete" in get_snippet("reg-delete-install")
    assert "msi-dynamic-reinstall" in snippet_names()
    assert "GetUninstallKeyName" in get_snippet("msi-dynamic-reinstall")
    assert "DoesRegKeyExist" in get_snippet("msi-dynamic-reinstall")
    assert "reg-condition-query" in snippet_names()
    assert "reg-modify-procedural" in snippet_names()
    assert "reg-restore-uninstall" in snippet_names()


def test_snippets_use_reference_command_style() -> None:
    """No If=/Sleep= key-value forms; every Then line closes with EndIf."""
    for name in snippet_names():
        snippet = get_snippet(name)
        assert "If=" not in snippet, name
        assert "Sleep=" not in snippet, name
        for line in snippet.splitlines():
            if "Then" in line:
                assert "EndIf" in line, f"{name}: {line}"


def test_all_templates_lint_clean() -> None:
    for kind, path in (
        ("msi", r"C:\tmp\Demo.msi"),
        ("exe", r"C:\tmp\Demo.exe"),
        ("script", r"C:\tmp\install.cmd"),
        ("links", r"C:\tmp\app.exe"),
    ):
        meta = _meta(package_type=kind.upper(), source_path=path, exe_kind="NSIS")
        diags = lint_document(render_template(kind, meta))
        errors = [d for d in diags if d.severity.value == "error"]
        assert errors == [], f"{kind}: {[e.code + ':' + e.message for e in errors]}"


def test_msi_template_standard_keys_and_flags() -> None:
    doc = render_template("msi", _meta(package_type="MSI"))
    app = next(s for s in doc.sections if s.name.casefold() == "application")
    keys = {n.key.casefold(): n.value for n in app.lines if hasattr(n, "key")}
    for req in APPLICATION_KEYS:
        assert req.casefold() in keys, f"missing Application key {req}"
    assert keys["srcdir"] == ".."
    assert keys["setupinfdir"] == "Install"
    blob = "\n".join(
        getattr(n, "text", "") or f"{getattr(n, 'key', '')}={getattr(n, 'value', '')}"
        for s in doc.sections
        for n in s.lines
    )
    for flag in MSI_INSTALL_FLAGS:
        assert flag in blob


def test_exe_template_has_app_active() -> None:
    doc = render_template("exe", _meta(package_type="EXE", source_path=r"C:\a.exe"))
    names = {s.name.casefold() for s in doc.sections}
    assert "set:appactive" in names
    product = next(s for s in doc.sections if s.name.casefold() == "product")
    refs = "\n".join(getattr(n, "text", "") for n in product.lines)
    assert "AppActive" in refs


def test_render_template_rejects_unknown_kind() -> None:
    import pytest

    with pytest.raises(ValueError, match="Unbekannter"):
        render_template("unatend", _meta())  # typo must not fall back silently


def test_render_template_sanitizes_meta_line_injection() -> None:
    meta = _meta(product_name="Evil\r\n[Injected]")
    doc = render_template("msi", meta)
    assert doc.section("Injected") is None
    setupinfo = doc.section("SetupInfo")
    assert setupinfo is not None
    desc = [n.value for n in setupinfo.lines if getattr(n, "key", "") == "Description"]
    assert desc and "\r" not in desc[0] and "\n" not in desc[0]


def test_msi_install_snippet_lint_clean() -> None:
    from empirum_core.parser.lexer import lex_text

    text = (
        "[SetupInfo]\r\nMethod=MSI\r\n\r\n[Setup]\r\nVersion=14.2\r\n\r\n"
        "[Application]\r\nProductName=X\r\n\r\n[Set:Product]\r\n" + get_snippet("msi-install")
    )
    doc = lex_text(text)
    diags = lint_document(doc)
    assert not any(d.code == "VAL-011" for d in diags)
    assert not any(
        d.code == "VAL-016" and "empfohlene Flags" in d.message for d in diags
    )


def test_templates_pass_conformance_rules() -> None:
    """VAL-019/020/021: generated templates are reference-conformant."""
    for kind, path in (
        ("msi", r"C:\tmp\Demo.msi"),
        ("exe", r"C:\tmp\Demo.exe"),
        ("script", r"C:\tmp\install.cmd"),
        ("links", r"C:\tmp\app.exe"),
    ):
        meta = _meta(package_type=kind.upper(), source_path=path, exe_kind="NSIS")
        diags = lint_document(render_template(kind, meta))
        offenders = [d.code for d in diags if d.code in {"VAL-019", "VAL-020", "VAL-021"}]
        assert offenders == [], f"{kind}: {offenders}"


# -- M-2: setupinf_contract is the single source of truth --------------------------


def _product_texts(doc) -> list[str]:
    product = next(s for s in doc.sections if s.name.casefold() == "product")
    return [getattr(n, "text", "") for n in product.lines]


def test_template_product_ref_order_matches_contract() -> None:
    """Templates emit the [Product] refs in exactly PRODUCT_REFS order."""
    expected = [ref for _target, ref in PRODUCT_REFS]
    for kind in ("msi", "exe", "script", "links"):
        doc = render_template(
            kind, _meta(package_type=kind.upper(), source_path=r"C:\tmp\Demo.exe")
        )
        actual = [line for line in _product_texts(doc) if line in expected]
        assert actual == expected, kind


def test_template_error_bodies_match_contract() -> None:
    """Templates emit the three error handlers with the shared canonical bodies."""
    for kind in ("msi", "exe", "script", "links"):
        doc = render_template(
            kind, _meta(package_type=kind.upper(), source_path=r"C:\tmp\Demo.exe")
        )
        for name, body in ERROR_SECTION_BODIES.items():
            section = doc.section(name)
            assert section is not None, f"{kind}: missing [{name}]"
            texts = [t for t in (getattr(n, "text", "") for n in section.lines) if t]
            assert texts == list(body), f"{kind}:{name}"


def test_contract_invariants() -> None:
    """Error handlers are standard sections; Shell:Product never gets a ref
    (it auto-runs via ShellLinks=1, an extra #Shell ref would duplicate links)."""
    assert set(ERROR_SECTION_BODIES) <= set(STANDARD_SECTIONS)
    assert "Shell:Product" not in {target for target, _ref in PRODUCT_REFS}


def test_uninstall_error_snippet_uses_canonical_section() -> None:
    """Snippet keeps German sample text but must target a canonical handler."""
    snippet = get_snippet("uninstall-error-pair")
    lines = snippet.splitlines()
    deinstall = "Set:DeInstallationError"
    assert deinstall in ERROR_SECTION_BODIES
    assert lines[0] == f"[{deinstall}]"
    assert all(line.startswith("-") for line in lines[1:])  # uninstall-only
