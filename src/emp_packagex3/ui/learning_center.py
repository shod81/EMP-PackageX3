"""Learning center: Setup.inf crash course, section and command reference."""

from __future__ import annotations

import html

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.learning_content import (
    CHAPTER_EXPORT_NAME,
    COMMAND_DOCS,
    COURSE_CHAPTERS,
    SECTION_REFERENCE,
    VAL_DOCS,
    Chapter,
    CommandDoc,
    SectionDoc,
)
from emp_packagex3.ui.tooltip_mode import apply_tooltip_mode, bind_field


class LearningCenterDialog(QDialog):
    """Hilfe → Setup.inf-Schnellkurs: Kapitel, Sektions- und Befehlsreferenz."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        tooltip_mode: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Setup.inf-Schnellkurs – Lerncenter")
        self.resize(1000, 680)
        self._term = ""

        self._toc = QListWidget()
        self._toc.setMinimumWidth(230)
        self._toc.addItem("Kurs – Alle Kapitel")
        for chapter in COURSE_CHAPTERS:
            item = QListWidgetItem(f"K{chapter.number} · {chapter.title}")
            item.setData(0x0100, f"chapter:{chapter.number}")
            self._toc.addItem(item)
        self._toc.addItem("Referenz – Sektionen")
        item = QListWidgetItem("Alle Sektionen")
        item.setData(0x0100, "sections:all")
        self._toc.addItem(item)
        for key, sdoc in SECTION_REFERENCE.items():
            item = QListWidgetItem(sdoc.name)
            item.setData(0x0100, f"section:{key}")
            self._toc.addItem(item)
        self._toc.addItem("Referenz – Befehle")
        item = QListWidgetItem("Alle Befehle")
        item.setData(0x0100, "commands:all")
        self._toc.addItem(item)
        for key, cdoc in COMMAND_DOCS.items():
            item = QListWidgetItem(cdoc.name)
            item.setData(0x0100, f"command:{key}")
            self._toc.addItem(item)
        self._toc.addItem("Referenz – Lint-Diagnosen")
        item = QListWidgetItem("VAL-001…021")
        item.setData(0x0100, "vals:all")
        self._toc.addItem(item)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Suchen (Kapitel, Sektionen, Befehle)…")
        bind_field(self._search, "learn.search")
        self._search.textChanged.connect(self._on_search)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)

        export_btn = QPushButton("Als HTML exportieren…")
        export_btn.clicked.connect(self._export_html)
        bind_field(export_btn, "learn.export")
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        bind_field(close_btn, "learn.close")

        buttons = QHBoxLayout()
        buttons.addWidget(export_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        left = QVBoxLayout()
        left.addWidget(self._search)
        left.addWidget(self._toc)
        left_box = QWidget()
        left_box.setLayout(left)

        root = QHBoxLayout(self)
        root.addWidget(left_box)
        col = QVBoxLayout()
        col.addWidget(self._browser, stretch=1)
        col.addLayout(buttons)
        root.addLayout(col)

        self._toc.currentItemChanged.connect(self._on_toc)
        self._toc.setCurrentRow(0)
        apply_tooltip_mode(self, tooltip_mode)

    # -- rendering ----------------------------------------------------------

    def _on_toc(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        key = str(current.data(0x0100) or "")
        if key.startswith("chapter:"):
            number = int(key.split(":", 1)[1])
            chapter = next(c for c in COURSE_CHAPTERS if c.number == number)
            self._browser.setHtml(render_chapter_html(chapter, term=self._term))
        elif key.startswith("section:"):
            name = key.split(":", 1)[1]
            sdoc = SECTION_REFERENCE[name]
            self._browser.setHtml(render_section_html(sdoc, term=self._term))
        elif key.startswith("sections:all"):
            self._browser.setHtml(render_all_sections_html(term=self._term))
        elif key.startswith("command:"):
            name = key.split(":", 1)[1]
            cdoc = COMMAND_DOCS[name]
            self._browser.setHtml(render_command_html(cdoc, term=self._term))
        elif key.startswith("commands:all"):
            self._browser.setHtml(render_all_commands_html(term=self._term))
        elif key.startswith("vals:all"):
            self._browser.setHtml(render_val_docs_html(term=self._term))
        else:
            self._browser.setHtml(render_overview_html(term=self._term))

    def _on_search(self, text: str) -> None:
        self._term = text.strip()
        self._on_toc(self._toc.currentItem(), None)

    def _export_html(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Lerncenter als HTML exportieren",
            CHAPTER_EXPORT_NAME,
            "HTML (*.html)",
        )
        if not path:
            return
        html_text = render_full_export_html()
        export_path = path if path.lower().endswith(".html") else path + ".html"
        from pathlib import Path

        Path(export_path).write_text(html_text, encoding="utf-8")
        self._browser.setHtml(
            f"<p>Exportiert nach: {html.escape(export_path)}</p>"
            + self._browser.toHtml()
        )


# -- pure render helpers (testable without Qt) -------------------------------


def _hl(text: str, term: str) -> str:
    escaped = html.escape(text)
    if term:
        low = escaped.casefold()
        needle = html.escape(term).casefold()
        idx = low.find(needle)
        if idx >= 0:
            escaped = (
                escaped[:idx]
                + "<b>"
                + escaped[idx : idx + len(needle)]
                + "</b>"
                + escaped[idx + len(needle) :]
            )
    return escaped


def _pre(text: str) -> str:
    return f"<pre>{html.escape(text)}</pre>"


def render_overview_html(*, term: str = "") -> str:
    items = "".join(
        f"<li>K{_hl(str(c.number), term)} · <b>{_hl(c.title, term)}</b> – "
        f"{_hl(c.key_rule, term)}</li>"
        for c in COURSE_CHAPTERS
    )
    return (
        "<h1>Setup.inf-Schnellkurs</h1>"
        "<p>Acht didaktisch gestufte Kapitel von der Paketstruktur bis zum "
        "Deploy-Pfad – systemorientiert, mit Beispielen aus den mitgelieferten "
        "Referenzvorlagen und Selbsttest-Fragen.</p>"
        f"<ul>{items}</ul>"
        "<p>Dazu: <b>Sektions-Referenz</b> (alle Sektionstypen), "
        "<b>Befehls-Referenz</b> (inkl. Uninstall-Verhalten) und "
        "<b>Lint-Diagnosen</b> mit Lang-Erklärung.</p>"
        "<p><i>Quelle: projekteigene Setup.inf-Referenz (docs/reference).</i></p>"
    )


def render_chapter_html(chapter: Chapter, *, term: str = "") -> str:
    paragraphs = "".join(f"<p>{_hl(p, term)}</p>" for p in chapter.intro)
    quiz = "".join(
        f"<p><b>Frage:</b> {_hl(q.question, term)}<br>"
        f"<b>Antwort:</b> {_hl(q.answer, term)}</p>"
        for q in chapter.quiz
    )
    return (
        f"<h1>Kapitel {chapter.number} · {html.escape(chapter.title)}</h1>"
        f"{paragraphs}"
        f"<p style='background:#eef3f6;border-left:4px solid #2a6f8f;"
        "padding:8px;'><b>Merksatz:</b> "
        f"{_hl(chapter.key_rule, term)}</p>"
        f"<h3>Systembeispiel</h3>{_pre(chapter.example)}"
        f"<h3>Selbsttest</h3>{quiz}"
    )


def render_section_html(doc: SectionDoc, *, term: str = "") -> str:
    return (
        f"<h1>Sektion [{html.escape(doc.name)}]</h1>"
        f"<p><b>Bedeutung:</b> {_hl(doc.meaning, term)}</p>"
        f"<p><b>Wann brauche ich das?</b> {_hl(doc.when_needed, term)}</p>"
        f"<p><b>Paket-Standard:</b> {'ja' if doc.standard_section else 'optional'}</p>"
        f"<h3>Beispiel</h3>{_pre(doc.example)}"
        f"<p><i>Referenz: {_hl(doc.reference, term)}</i></p>"
    )


def render_all_sections_html(*, term: str = "") -> str:
    parts = ["<h1>Sektions-Referenz (alle Sektionstypen)</h1>"]
    for doc in SECTION_REFERENCE.values():
        if term and term.casefold() not in (
            doc.name + doc.meaning + doc.when_needed
        ).casefold():
            continue
        parts.append(
            f"<h2>[{html.escape(doc.name)}]</h2>"
            f"<p>{_hl(doc.meaning, term)} "
            f"<i>({'Paket-Standard' if doc.standard_section else 'optional'})</i></p>"
            f"{_pre(doc.example)}"
        )
    return "".join(parts)


def render_command_html(doc: CommandDoc, *, term: str = "") -> str:
    return (
        f"<h1>Befehl {html.escape(doc.name)}</h1>"
        f"<p><b>Syntax:</b> <code>{html.escape(doc.syntax)}</code></p>"
        f"<p><b>Bedeutung:</b> {_hl(doc.semantics, term)}</p>"
        f"<p><b>Uninstall-Verhalten:</b> {_hl(doc.uninstall, term)}</p>"
        f"<h3>Praxis-Beispiel</h3>{_pre(doc.example)}"
        f"<p style='color:#8a5a00;'><b>Fallstricke & Best Practice:</b> "
        f"{_hl(doc.pitfall, term)}</p>"
    )


def render_all_commands_html(*, term: str = "") -> str:
    parts = ["<h1>Befehls-Referenz</h1>"]
    for doc in COMMAND_DOCS.values():
        if term and term.casefold() not in (
            doc.name + doc.semantics + doc.pitfall
        ).casefold():
            continue
        parts.append(
            f"<h2>{html.escape(doc.name)}</h2>"
            f"<p><code>{html.escape(doc.syntax)}</code></p>"
            f"<p>{_hl(doc.semantics, term)}</p>"
            f"<p><b>Uninstall-Verhalten:</b> {_hl(doc.uninstall, term)}</p>"
            f"{_pre(doc.example)}"
            f"<p style='color:#8a5a00;'><b>Fallstricke & Best Practice:</b> "
            f"{_hl(doc.pitfall, term)}</p>"
        )
    return "".join(parts)


def render_val_docs_html(*, term: str = "") -> str:
    parts = ["<h1>Lint-Diagnosen VAL-001…021</h1>"]
    for doc in VAL_DOCS.values():
        if term and term.casefold() not in (doc.code + doc.cause).casefold():
            continue
        parts.append(
            f"<h2>{doc.code} ({doc.severity})</h2>"
            f"<p><b>Ursache:</b> {_hl(doc.cause, term)}</p>"
            f"<p><b>Behebung:</b> {_hl(doc.remedy, term)}</p>"
            f"<p><i>Referenz: {html.escape(doc.reference)}</i></p>"
        )
    return "".join(parts)


def render_full_export_html() -> str:
    chapters = "".join(render_chapter_html(c) for c in COURSE_CHAPTERS)
    return (
        "<html><head><meta charset='utf-8'>"
        "<title>Setup.inf-Schnellkurs – EMP-PackageX3</title></head><body>"
        + render_overview_html()
        + chapters
        + render_all_sections_html()
        + render_all_commands_html()
        + render_val_docs_html()
        + "</body></html>"
    )
