"""Structured Empirum Setup.inf help hub (commands, predicates, flags, …)."""

from __future__ import annotations

import html

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.learning_content import (
    COMMAND_DOCS,
    FLAG_DOCS,
    SECTION_REFERENCE,
    SECURITY_DSL_CONSTANTS,
    SECURITY_DSL_DOCS,
    VAL_DOCS,
    FlagDoc,
    FunctionDoc,
    PredicateDoc,
    SectionDoc,
    SecurityOpDoc,
    ValDoc,
    lookup_command,
    lookup_flag,
    lookup_function,
    lookup_predicate,
    lookup_variable,
    val_rule_range,
)
from emp_packagex3.ui.learning_center import (
    render_command_html,
    render_section_html,
)
from emp_packagex3.ui.tooltip_mode import apply_tooltip_mode, bind_field
from empirum_core.setupinf_contract import (
    SETUPINF_COMMAND_GROUPS,
    SETUPINF_COMMANDS,
    SETUPINF_COMMANDS_UNDOCUMENTED,
    SETUPINF_DOLLAR_GROUPS_UNDOCUMENTED,
    SETUPINF_FUNCTIONS,
    SETUPINF_KEYS_UNDOCUMENTED,
    SETUPINF_PREDICATES,
    SETUPINF_SWITCHES_UNDOCUMENTED,
    SETUPINF_VARIABLES,
    SETUPINF_VARIABLES_UNDOCUMENTED,
)

_ROLE = Qt.ItemDataRole.UserRole


def _hl(text: str, term: str) -> str:
    escaped = html.escape(text)
    if not term:
        return escaped
    needle = html.escape(term)
    # case-insensitive highlight via simple split on lower
    low = escaped.casefold()
    nlow = needle.casefold()
    if nlow not in low:
        return escaped
    out: list[str] = []
    start = 0
    while True:
        idx = low.find(nlow, start)
        if idx < 0:
            out.append(escaped[start:])
            break
        out.append(escaped[start:idx])
        out.append(f"<b>{escaped[idx : idx + len(needle)]}</b>")
        start = idx + len(nlow)
    return "".join(out)


def _pre(text: str) -> str:
    return (
        "<pre style='background:#eef3f6;padding:10px;border-radius:4px;'>"
        f"{html.escape(text)}</pre>"
    )


def render_predicate_html(doc: PredicateDoc, *, term: str = "") -> str:
    alias = (
        f"<p><b>Alias von:</b> <code>{html.escape(doc.alias_of)}</code></p>"
        if doc.alias_of
        else ""
    )
    return (
        f"<h1>Prädikat {html.escape(doc.name)}</h1>"
        f"<p><b>Syntax:</b> <code>{html.escape(doc.syntax)}</code></p>"
        f"<p><b>Bedeutung:</b> {_hl(doc.semantics, term)}</p>"
        f"{alias}"
        f"<h3>Beispiel</h3>{_pre(doc.example)}"
        f"<p style='color:#8a5a00;'><b>Fallstricke:</b> {_hl(doc.pitfall, term)}</p>"
    )


def render_function_html(doc: FunctionDoc, *, term: str = "") -> str:
    return (
        f"<h1>Funktion {html.escape(doc.name)}</h1>"
        f"<p><b>Syntax:</b> <code>{html.escape(doc.syntax)}</code></p>"
        f"<p><b>Bedeutung:</b> {_hl(doc.semantics, term)}</p>"
        f"<h3>Beispiel</h3>{_pre(doc.example)}"
        f"<p style='color:#8a5a00;'><b>Fallstricke:</b> {_hl(doc.pitfall, term)}</p>"
    )


def render_flag_html(doc: FlagDoc, *, term: str = "") -> str:
    return (
        f"<h1>{html.escape(doc.name)}</h1>"
        f"<p><b>Syntax:</b> <code>{html.escape(doc.syntax)}</code></p>"
        f"<p><b>Bedeutung:</b> {_hl(doc.semantics, term)}</p>"
        f"<h3>Beispiel</h3>{_pre(doc.example)}"
        f"<p style='color:#8a5a00;'><b>Fallstricke:</b> {_hl(doc.pitfall, term)}</p>"
    )


def render_variable_html(name: str, *, term: str = "") -> str:
    doc = lookup_variable(name)
    if doc is None:
        return (
            f"<h1>Variable {html.escape(name)}</h1>"
            f"<p>Eingebaute Empirum-Variable aus der Setup.inf-Referenz "
            "(Kap. 4). Verwendung in Pfaden, If-Bedingungen und Echo-Zeilen.</p>"
            f"<h3>Beispiel</h3>{_pre(f'Echo Wert: {name}')}"
            f"<p><i>Vollständige Liste: Hilfe → Setup.inf-Hilfe → Variablen.</i></p>"
        )
    return (
        f"<h1>Variable {html.escape(doc.name)}</h1>"
        f"<p><b>Kategorie:</b> {html.escape(doc.category)}</p>"
        f"<p><b>Bedeutung:</b> {_hl(doc.meaning, term)}</p>"
        f"<p><b>Typischer Wert / Pfad:</b> <code>{html.escape(doc.example_value)}</code></p>"
        f"<h3>Typische Verwendung</h3>{_pre(doc.usage)}"
        f"<p style='color:#8a5a00;'><b>Fallstricke & Best Practice:</b> "
        f"{_hl(doc.pitfall, term)}</p>"
    )


def _undoc_warning() -> str:
    """Orange Warnbox: dieser Eintrag gehört zu den undokumentierten Konstrukten."""
    return (
        "<p style='background:#fff3e0;border:1px solid #e65100;padding:8px;'>"
        "<b>⚠ UNDOKUMENTIERT (Klasse 1):</b> Dieser Eintrag ist im Interpreter "
        "26.1.0 verifiziert vorhanden, fehlt aber in der gesamten offiziellen "
        "Matrix42-Hilfe. Es gibt keinen Support und kein Sicherheitsnetz; die "
        "Semantik ist teils offen. Nur nach eigener Verifikation einsetzen.</p>"
    )


def render_undoc_overview_note(*, undocumented: bool = False) -> str:
    """Anmerkung, welche Befehle/Einträge zu den nicht dokumentierten (Klasse 1)
    gehören – immer sichtbar auf der Übersichtsseite der Befehlsreferenz."""
    undoc_cmds = ", ".join(
        f"<code>{html.escape(name)}</code>" for name in SETUPINF_COMMANDS_UNDOCUMENTED
    )
    n_vars = len(SETUPINF_VARIABLES_UNDOCUMENTED)
    n_groups = len(SETUPINF_DOLLAR_GROUPS_UNDOCUMENTED)
    n_keys = len(SETUPINF_KEYS_UNDOCUMENTED)
    n_switches = len(SETUPINF_SWITCHES_UNDOCUMENTED)
    if undocumented:
        flag_note = (
            "Das Feature-Flag ist aktiv: Alle nicht dokumentierten Einträge stehen "
            "unten im Baum im Bereich <b>Undokumentiert (26.1.0) ⚠</b> und sind "
            "dort zusätzlich mit <b>„(undok.)“</b> gekennzeichnet."
        )
    else:
        flag_note = (
            "Diese Einträge erscheinen in dieser Referenz nur, wenn das "
            "experimentelle Feature-Flag „undokumentierte Befehle (Klasse 1)“ "
            "aktiviert ist (Datei → Einstellungen… → Experimentell) – dann als "
            "eigener Bereich <b>Undokumentiert (26.1.0) ⚠</b> mit Kennzeichnung "
            "„(undok.)“ und Warnhinweis."
        )
    return (
        "<h3>Nicht dokumentierte Befehle & Einträge (Klasse 1)</h3>"
        f"<p>Zu den <b>nicht dokumentierten Befehlen</b> gehören: {undoc_cmds} "
        f"({len(SETUPINF_COMMANDS_UNDOCUMENTED)} Zeilenbefehle – verifiziert "
        "gegen den Interpreter 26.1.0, Befehlsermittlung aus dem Schwesterprojekt "
        "UEMAgentWindows, aber in der gesamten offiziellen Matrix42-Hilfe nicht "
        "vorhanden). Weitere undokumentierte Einträge: "
        f"{n_vars} Variablen (u. a. <code>%DstDir%</code>), "
        f"{n_groups} $-Gruppen für [Security:], "
        f"{n_keys} [Application]-Keys (Seriennummer-/Demo-Mechanik) und "
        f"{n_switches} Setup.exe-Schalter (<code>/SX</code>, <code>/Y:</code>). "
        f"{flag_note}</p>"
    )


def render_hub_overview_html(*, undocumented: bool = False) -> str:
    n_cmd = len(SETUPINF_COMMANDS)
    n_pred = len(SETUPINF_PREDICATES)
    n_fn = len(SETUPINF_FUNCTIONS)
    n_var = len(SETUPINF_VARIABLES)
    return (
        "<h1>Empirum Setup.inf-Hilfe</h1>"
        "<p>Strukturierte, durchsuchbare Referenz für IT-Administratoren – "
        "abgeleitet aus der Matrix42-Setup.inf-Referenz "
        "(<code>docs/reference/System_Prompt_Empirum_Setup.inf.md</code>).</p>"
        "<h3>Inhalt</h3><ul>"
        f"<li><b>Befehle</b> – {n_cmd} Zeilenbefehle (Referenz + verifiziert 26.1.0)</li>"
        f"<li><b>Prädikate</b> – {n_pred} If-Bedingungen (verifizierte Does*-Funktionen)</li>"
        f"<li><b>Funktionen</b> – {n_fn} Set-Ausdrücke (z. B. GetUninstallKeyName)</li>"
        f"<li><b>Variablen</b> – {n_var} eingebaute %-Variablen + Spezialmuster "
        "(Registry, INI, VM_/VU_)</li>"
        "<li><b>Sektionen</b> – Sektionstypen inkl. Standard-Pflicht</li>"
        "<li><b>Flags</b> – #Aufruf, DONTDELETE/DELETE, '-'-Uninstall, Copy-Flags, "
        "Setup.exe-Schalter, Registry-Zusatzflags, If-Operatoren</li>"
        f"<li><b>[Security:]-DSL</b> – {len(SECURITY_DSL_DOCS)} Operationen "
        "(LocalUser, Dacl, NetShare …)</li>"
        f"<li><b>Lint</b> – {val_rule_range()}</li>"
        "</ul>"
        "<p><b>Hinweis:</b> Der Katalog ist gegen den Empirum-Interpreter 26.1.0 "
        "verifiziert (Setup.exe/Setup64.exe, 26.1.0). "
        "Nicht existierende Befehle/Prädikate (z. B. <code>Run</code>, "
        "<code>CheckLanAdministrator</code>, Alias-Prädikate) werden per VAL-026 "
        "markiert. If-Prädikate sind keine Zeilenbefehle – sie stehen unter "
        "<i>Prädikate</i>.</p>"
        f"{render_undoc_overview_note(undocumented=undocumented)}"
        "<p><i>Didaktischer Kurs: Hilfe → Setup.inf-Schnellkurs…</i></p>"
    )


def render_security_html(doc: SecurityOpDoc, *, term: str = "") -> str:
    return (
        f"<h1>[Security:] – {html.escape(doc.op)}</h1>"
        f"<p><b>Syntax:</b> <code>{html.escape(doc.syntax)}</code></p>"
        f"<p><b>Bedeutung:</b> {_hl(doc.semantics, term)}</p>"
        f"<h3>Beispiel</h3>{_pre(doc.example)}"
        f"<p style='color:#8a5a00;'><b>Fallstricke & Best Practice:</b> "
        f"{_hl(doc.pitfall, term)}</p>"
    )


def render_security_overview_html() -> str:
    ops = "".join(
        f"<li><b>{html.escape(op)}</b></li>" for op in SECURITY_DSL_DOCS
    )
    consts = "".join(
        f"<tr><td><code>{html.escape(name)}</code></td><td>{html.escape(desc)}</td></tr>"
        for name, desc in SECURITY_DSL_CONSTANTS
    )
    return (
        "<h1>[Security:] – DSL</h1>"
        "<p>Deklarative Sicherheits-Operationen (Legacy-Help Section 43, verifiziert "
        "gegen den Interpreter 26.1.0). Abarbeitung unabhängig vom '-'-Präfix; "
        "Referenzzähler unter <code>HKLM\\Software\\UsageCount\\Setup</code>.</p>"
        f"<h3>Operationen</h3><ul>{ops}</ul>"
        f"<h3>Konstanten</h3><table>{consts}</table>"
    )


def render_undoc_group_html(group: str) -> str:
    """Class-1 (undocumented) listing pages — only reachable behind the feature flag."""
    warning = _undoc_warning()
    if group == "dollargroups":
        items = "".join(
            f"<li><code>{html.escape(g)}</code></li>"
            for g in SETUPINF_DOLLAR_GROUPS_UNDOCUMENTED
        )
        return f"<h1>$-Gruppen (undokumentiert)</h1>{warning}<ul>{items}</ul>"
    if group == "appkeys":
        items = "".join(
            f"<li><code>{html.escape(k)}</code></li>" for k in SETUPINF_KEYS_UNDOCUMENTED
        )
        return (
            f"<h1>Undokumentierte [Application]-Keys</h1>{warning}"
            f"<ul>{items}</ul>"
            "<p>Darunter Seriennummer-/Demo-Mechanik (SerialDLL, CheckSerialProc, "
            "PatchSerialProc, UseProductID* inkl. DEMO_DATE = zeitlich begrenzte "
            "Demo-Installationen).</p>"
        )
    if group == "switches":
        items = "".join(
            f"<li><code>{html.escape(s)}</code></li>" for s in SETUPINF_SWITCHES_UNDOCUMENTED
        )
        return (
            f"<h1>Undokumentierte Setup.exe-Schalter</h1>{warning}<ul>{items}</ul>"
            "<p>Funktion ungeklärt: /SX liegt neben der /S%d-Schaltergruppe "
            "(Vermutung „silent + exit“), /Y:&lt;Datei&gt; neben SystemShutdown "
            "(Vermutung Antwort-/Bestätigungsdatei). Nicht generieren.</p>"
        )
    return f"<h1>Undokumentiert</h1>{warning}"


def _blob(*parts: str) -> str:
    return " ".join(parts).casefold()


def topic_matches(kind: str, key: str, term: str) -> bool:
    if not term:
        return True
    t = term.casefold()
    if kind == "command":
        cdoc = lookup_command(key)
        return bool(cdoc and t in _blob(
            cdoc.name, cdoc.syntax, cdoc.semantics, cdoc.example, cdoc.pitfall
        ))
    if kind == "predicate":
        pdoc = lookup_predicate(key)
        return bool(pdoc and t in _blob(
            pdoc.name, pdoc.syntax, pdoc.semantics, pdoc.example, pdoc.pitfall, pdoc.alias_of
        ))
    if kind == "function":
        fdoc = lookup_function(key)
        return bool(fdoc and t in _blob(
            fdoc.name, fdoc.syntax, fdoc.semantics, fdoc.example, fdoc.pitfall
        ))
    if kind == "flag":
        fgdoc = lookup_flag(key)
        return bool(fgdoc and t in _blob(
            fgdoc.name, fgdoc.syntax, fgdoc.semantics, fgdoc.example, fgdoc.pitfall
        ))
    if kind == "variable":
        vardoc = lookup_variable(key)
        if vardoc is not None:
            return bool(t in _blob(
                vardoc.name, vardoc.category, vardoc.meaning, vardoc.example_value,
                vardoc.usage, vardoc.pitfall
            ))
        return t in key.casefold()
    if kind == "section":
        sdoc = SECTION_REFERENCE.get(key)
        return bool(sdoc and t in _blob(
            sdoc.name, sdoc.meaning, sdoc.when_needed, sdoc.example
        ))
    if kind == "val":
        vdoc = VAL_DOCS.get(key)
        return bool(vdoc and t in _blob(vdoc.code, vdoc.cause, vdoc.remedy))
    if kind == "security":
        secdoc = SECURITY_DSL_DOCS.get(key)
        return bool(
            secdoc
            and t
            in _blob(
                secdoc.op, secdoc.syntax, secdoc.semantics, secdoc.example, secdoc.pitfall
            )
        )
    if kind in {"overview", "group", "heading"}:
        return True
    return t in key.casefold()


class EmpirumHelpDialog(QDialog):
    """Hilfe → Setup.inf-Hilfe: strukturierte Empirum-Referenz."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        tooltip_mode: bool = True,
        initial: str | None = None,
        undocumented: bool = False,
    ) -> None:
        super().__init__(parent)
        self._undocumented = undocumented
        self.setWindowTitle("Setup.inf-Hilfe – EMP-PackageX3")
        self.resize(980, 680)
        self.setMinimumSize(760, 520)

        brand = QLabel("Empirum Setup.inf-Hilfe")
        brand.setObjectName("empHelpBrand")
        sub = QLabel(
            "Befehle, Prädikate, Funktionen, Variablen, Sektionen und Flags – "
            "durchsuchbar für den IT-Administrator."
        )
        sub.setObjectName("empHelpSubtitle")
        sub.setWordWrap(True)

        self._search = QLineEdit()
        self._search.setPlaceholderText(
            "Suchen (z. B. CallHidden, DoesRegKeyExist, %Src%, DONTDELETE)…"
        )
        self._search.setClearButtonEnabled(True)
        bind_field(self._search, "emphelp.search")

        self._count = QLabel()
        self._count.setObjectName("empHelpCount")

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(260)
        self._tree.setObjectName("empHelpTree")
        bind_field(self._tree, "emphelp.tree")

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setObjectName("empHelpBrowser")
        bind_field(self._browser, "emphelp.detail")

        close_btn = QPushButton("Schließen")
        close_btn.setObjectName("empHelpClose")
        close_btn.clicked.connect(self.accept)
        bind_field(close_btn, "emphelp.close")

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(self._search)
        left.addWidget(self._count)
        left.addWidget(self._tree, stretch=1)
        left_box = QWidget()
        left_box.setLayout(left)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(left_box)
        split.addWidget(self._browser)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([280, 680])

        header = QVBoxLayout()
        header.setSpacing(2)
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(brand)
        header.addWidget(sub)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)
        root.addLayout(header)
        rule = QFrame()
        rule.setFrameShape(QFrame.Shape.HLine)
        rule.setObjectName("empHelpRule")
        root.addWidget(rule)
        root.addWidget(split, stretch=1)
        root.addLayout(buttons)

        self.setStyleSheet(self._dialog_qss())
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self._tree.setFont(mono)

        self._search.textChanged.connect(self._rebuild_tree)
        self._tree.currentItemChanged.connect(self._on_select)
        self._rebuild_tree("")
        self._select_initial(initial or "overview")
        apply_tooltip_mode(self, tooltip_mode)

    def _make_item(self, label: str, kind: str, key: str = "") -> QTreeWidgetItem:
        item = QTreeWidgetItem([label])
        item.setData(0, _ROLE, f"{kind}:{key}" if key else kind)
        return item

    def _rebuild_tree(self, text: str) -> None:
        term = text.strip()
        current = ""
        cur = self._tree.currentItem()
        if cur is not None:
            current = str(cur.data(0, _ROLE) or "")

        self._tree.blockSignals(True)
        self._tree.clear()
        visible = 0

        overview = self._make_item("Übersicht", "overview")
        self._tree.addTopLevelItem(overview)
        visible += 1

        # Commands by group
        cmd_root = self._make_item("Befehle", "heading", "commands")
        self._tree.addTopLevelItem(cmd_root)
        for group_name, names in SETUPINF_COMMAND_GROUPS:
            group_item = self._make_item(group_name, "group", group_name)
            for name in names:
                if topic_matches("command", name, term):
                    group_item.addChild(self._make_item(name, "command", name))
                    visible += 1
            if group_item.childCount():
                cmd_root.addChild(group_item)
        grouped = {n for _, names in SETUPINF_COMMAND_GROUPS for n in names}
        for name in SETUPINF_COMMANDS:
            if name in grouped:
                continue
            if topic_matches("command", name, term):
                cmd_root.addChild(self._make_item(name, "command", name))
                visible += 1
        cmd_root.setExpanded(True)

        pred_root = self._make_item("Prädikate (If)", "heading", "predicates")
        self._tree.addTopLevelItem(pred_root)
        for name in SETUPINF_PREDICATES:
            if topic_matches("predicate", name, term):
                pred_root.addChild(self._make_item(name, "predicate", name))
                visible += 1
        pred_root.setExpanded(bool(term))

        fn_root = self._make_item("Funktionen (Set)", "heading", "functions")
        self._tree.addTopLevelItem(fn_root)
        for name in SETUPINF_FUNCTIONS:
            if topic_matches("function", name, term):
                fn_root.addChild(self._make_item(name, "function", name))
                visible += 1
        fn_root.setExpanded(bool(term))

        var_root = self._make_item("Variablen", "heading", "variables")
        self._tree.addTopLevelItem(var_root)
        for name in SETUPINF_VARIABLES:
            if topic_matches("variable", name, term):
                var_root.addChild(self._make_item(name, "variable", name))
                visible += 1
        for name in (
            "%Root,SubKey,ValueName%",
            "%%%Path.ini,Section,Key%%%",
            "%VM_*%",
            "%VU_*%",
        ):
            if topic_matches("variable", name, term):
                var_root.addChild(self._make_item(name, "variable", name))
                visible += 1
        var_root.setExpanded(bool(term))

        sec_root = self._make_item("Sektionen", "heading", "sections")
        self._tree.addTopLevelItem(sec_root)
        for key, sdoc in SECTION_REFERENCE.items():
            if topic_matches("section", key, term):
                sec_root.addChild(self._make_item(sdoc.name, "section", key))
                visible += 1
        sec_root.setExpanded(bool(term))

        # Flags partitioned by catalog prefix: section-call flags (no prefix),
        # Copy-Flags (CF:), Setup.exe switches (SW:), registry extra flags
        # (RG:) and If operators (OP:).
        flag_categories: tuple[tuple[str, tuple[str, ...]], ...] = (
            ("Flags & Aufruf", ("",)),
            ("Copy-Flags", ("CF:",)),
            ("Setup.exe-Schalter", ("SW:",)),
            ("Registry-Zusatzflags", ("RG:",)),
            ("If-Operatoren & Logik", ("OP:",)),
        )
        for cat_label, prefixes in flag_categories:
            cat_root = self._make_item(cat_label, "heading", "flags")
            added = False
            for key, fdoc in FLAG_DOCS.items():
                if not any(key.startswith(p) for p in prefixes):
                    continue
                if topic_matches("flag", key, term):
                    cat_root.addChild(self._make_item(fdoc.name, "flag", key))
                    visible += 1
                    added = True
            if added:
                self._tree.addTopLevelItem(cat_root)
                cat_root.setExpanded(bool(term))

        sec_dsl_root = self._make_item("[Security:]-DSL", "heading", "security")
        self._tree.addTopLevelItem(sec_dsl_root)
        for key, sec_doc in SECURITY_DSL_DOCS.items():
            if topic_matches("security", key, term):
                sec_dsl_root.addChild(self._make_item(sec_doc.op, "security", key))
                visible += 1
        sec_dsl_root.setExpanded(bool(term))

        if self._undocumented:
            undoc_root = self._make_item(
                "Undokumentiert (26.1.0) ⚠", "heading", "undocumented"
            )
            self._tree.addTopLevelItem(undoc_root)
            for name in SETUPINF_COMMANDS_UNDOCUMENTED:
                if topic_matches("command", name, term):
                    undoc_root.addChild(
                        self._make_item(f"{name} (undok.)", "command", name)
                    )
                    visible += 1
            for name in SETUPINF_VARIABLES_UNDOCUMENTED:
                if topic_matches("variable", name, term):
                    undoc_root.addChild(
                        self._make_item(f"{name} (undok.)", "variable", name)
                    )
                    visible += 1
            for label, key in (
                (f"$-Gruppen ({len(SETUPINF_DOLLAR_GROUPS_UNDOCUMENTED)})", "dollargroups"),
                (f"[Application]-Keys ({len(SETUPINF_KEYS_UNDOCUMENTED)})", "appkeys"),
                ("Setup.exe-Schalter (/SX, /Y:)", "switches"),
            ):
                if not term or term.casefold() in label.casefold():
                    undoc_root.addChild(self._make_item(label, "undocgroup", key))
                    visible += 1
            undoc_root.setExpanded(bool(term))

        val_root = self._make_item(f"Lint {val_rule_range()}", "heading", "vals")
        self._tree.addTopLevelItem(val_root)
        for key in VAL_DOCS:
            if topic_matches("val", key, term):
                val_root.addChild(self._make_item(key, "val", key))
                visible += 1
        val_root.setExpanded(bool(term))

        self._tree.blockSignals(False)
        self._count.setText(f"{visible} Themen sichtbar")

        if term:
            # auto-expand all and select first leaf
            self._tree.expandAll()
            leaf = self._first_leaf(self._tree.invisibleRootItem())
            if leaf is not None:
                self._tree.setCurrentItem(leaf)
            else:
                self._browser.setHtml(
                    f"<h1>Keine Treffer</h1><p>Nichts passt zu "
                    f"<b>{html.escape(term)}</b>.</p>"
                )
            return

        # restore selection
        if current:
            found = self._find_by_data(current)
            if found is not None:
                self._tree.setCurrentItem(found)
                return
        self._tree.setCurrentItem(overview)
        self._browser.setHtml(
            render_hub_overview_html(undocumented=self._undocumented)
        )

    def _first_leaf(self, item: QTreeWidgetItem) -> QTreeWidgetItem | None:
        for i in range(item.childCount()):
            child = item.child(i)
            if child is None:
                continue
            data = str(child.data(0, _ROLE) or "")
            kind = data.split(":", 1)[0]
            if kind in {
                "command",
                "predicate",
                "function",
                "variable",
                "section",
                "flag",
                "val",
                "security",
                "undocgroup",
                "overview",
            } and (child.childCount() == 0 or kind == "overview"):
                return child
            deeper = self._first_leaf(child)
            if deeper is not None:
                return deeper
        return None

    def _find_by_data(self, data: str) -> QTreeWidgetItem | None:
        def walk(item: QTreeWidgetItem) -> QTreeWidgetItem | None:
            if str(item.data(0, _ROLE) or "") == data:
                return item
            for i in range(item.childCount()):
                child = item.child(i)
                if child is None:
                    continue
                hit = walk(child)
                if hit is not None:
                    return hit
            return None

        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            top = root.child(i)
            if top is None:
                continue
            hit = walk(top)
            if hit is not None:
                return hit
        return None

    def _select_initial(self, initial: str) -> None:
        mapping = {
            "overview": "overview",
            "commands": "heading:commands",
            "predicates": "heading:predicates",
            "functions": "heading:functions",
            "variables": "heading:variables",
            "sections": "heading:sections",
            "flags": "heading:flags",
            "security": "heading:security",
            "vals": "heading:vals",
        }
        data = mapping.get(initial, initial)
        if ":" not in data and data not in {"overview"}:
            # treat as command name
            data = f"command:{initial}"
        item = self._find_by_data(data)
        if item is not None:
            self._tree.setCurrentItem(item)
            item.setExpanded(True)

    def _on_select(
        self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None
    ) -> None:
        if current is None:
            return
        data = str(current.data(0, _ROLE) or "")
        term = self._search.text().strip()
        if data == "overview" or data.startswith("heading:") or data.startswith("group:"):
            if data == "overview":
                self._browser.setHtml(
                    render_hub_overview_html(undocumented=self._undocumented)
                )
            elif data == "heading:security":
                self._browser.setHtml(render_security_overview_html())
            elif data.startswith("group:"):
                group = data.split(":", 1)[1]
                names = next(
                    (n for g, n in SETUPINF_COMMAND_GROUPS if g == group), ()
                )
                parts = [f"<h1>Befehle – {html.escape(group)}</h1><ul>"]
                for name in names:
                    doc = COMMAND_DOCS.get(name)
                    if doc:
                        parts.append(
                            f"<li><b>{html.escape(name)}</b> – "
                            f"{html.escape(doc.semantics[:120])}…</li>"
                        )
                parts.append("</ul>")
                self._browser.setHtml("".join(parts))
            else:
                self._browser.setHtml(
                    render_hub_overview_html(undocumented=self._undocumented)
                )
            return
        kind, _, key = data.partition(":")
        if kind == "command":
            cmd_doc = lookup_command(key)
            if cmd_doc:
                page = render_command_html(cmd_doc, term=term)
                if key in SETUPINF_COMMANDS_UNDOCUMENTED:
                    page = _undoc_warning() + page
                self._browser.setHtml(page)
        elif kind == "predicate":
            pred_doc = lookup_predicate(key)
            if pred_doc:
                self._browser.setHtml(render_predicate_html(pred_doc, term=term))
        elif kind == "function":
            func_doc = lookup_function(key)
            if func_doc:
                self._browser.setHtml(render_function_html(func_doc, term=term))
        elif kind == "flag":
            flag_doc = lookup_flag(key)
            if flag_doc:
                self._browser.setHtml(render_flag_html(flag_doc, term=term))
        elif kind == "variable":
            page = render_variable_html(key, term=term)
            if key in SETUPINF_VARIABLES_UNDOCUMENTED:
                page = _undoc_warning() + page
            self._browser.setHtml(page)
        elif kind == "section":
            sdoc: SectionDoc | None = SECTION_REFERENCE.get(key)
            if sdoc:
                self._browser.setHtml(render_section_html(sdoc, term=term))
        elif kind == "val":
            vdoc: ValDoc | None = VAL_DOCS.get(key)
            if vdoc:
                self._browser.setHtml(
                    f"<h1>{html.escape(vdoc.code)} ({html.escape(vdoc.severity)})</h1>"
                    f"<p><b>Ursache:</b> {_hl(vdoc.cause, term)}</p>"
                    f"<p><b>Behebung:</b> {_hl(vdoc.remedy, term)}</p>"
                    f"<p><i>Referenz: {html.escape(vdoc.reference)}</i></p>"
                )
        elif kind == "security":
            sdoc_sec: SecurityOpDoc | None = SECURITY_DSL_DOCS.get(key)
            if sdoc_sec:
                self._browser.setHtml(render_security_html(sdoc_sec, term=term))
        elif kind == "undocgroup":
            self._browser.setHtml(render_undoc_group_html(key))

    @staticmethod
    def _dialog_qss() -> str:
        return """
            QDialog { background: #f7f9fa; }
            QLabel#empHelpBrand {
                font-size: 15px; font-weight: 600; color: #1a3a4a;
            }
            QLabel#empHelpSubtitle { color: #5a6a72; font-size: 12px; }
            QLabel#empHelpCount { color: #5a6a72; font-size: 11px; }
            QFrame#empHelpRule { color: #d0d8dc; }
            QTreeWidget#empHelpTree {
                background: #ffffff; border: 1px solid #d0d8dc;
                border-radius: 4px; padding: 4px;
            }
            QTreeWidget#empHelpTree::item:selected {
                background: #1a3a4a; color: #ffffff;
            }
            QTextBrowser#empHelpBrowser {
                background: #ffffff; border: 1px solid #d0d8dc;
                border-radius: 4px; padding: 8px;
            }
            QLineEdit {
                min-height: 28px; background: #ffffff;
                border: 1px solid #d0d8dc; border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton#empHelpClose {
                background: #1a3a4a; color: #ffffff; border: none;
                border-radius: 4px; padding: 8px 16px; font-weight: 600;
            }
            QPushButton#empHelpClose:hover { background: #244a5c; }
        """
