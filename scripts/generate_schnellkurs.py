"""Regenerate docs/setupinf-schnellkurs.md from learning_content.py.

Usage: uv run python scripts/generate_schnellkurs.py
(After changing learning_content.py, run this to keep docs in sync.)
"""

import sys
from pathlib import Path

sys.path.insert(0, "src")
from emp_packagex3.learning_content import (  # noqa: E402
    COMMAND_DOCS,
    COURSE_CHAPTERS,
    FUNCTION_DOCS,
    PREDICATE_DOCS,
    SECTION_REFERENCE,
    VAL_DOCS,
    VARIABLE_DOCS,
)

FENCE = "```"
NL = chr(10)
CR = chr(13)

lines = [
    "# Setup.inf-Schnellkurs (kanonisch, aus learning_content.py generiert)",
    "",
    "> Generiert aus `src/emp_packagex3/learning_content.py` – Inhalte dort",
    "> pflegen und diese Datei neu generieren, damit App und Doku nicht driften.",
    "",
]
for c in COURSE_CHAPTERS:
    lines += [f"## Kapitel {c.number}: {c.title}", ""]
    lines += list(c.intro)
    lines += ["", f"> **Merksatz:** {c.key_rule}", "", "**Systembeispiel:**", "",
              FENCE + "ini", c.example.replace(CR, ""), FENCE, "", "### Selbsttest", ""]
    for i, q in enumerate(c.quiz, 1):
        lines += [f"{i}. **{q.question}**", f"   *Antwort:* {q.answer}", ""]

lines += ["## Sektions-Referenz", ""]
for doc in SECTION_REFERENCE.values():
    marker = "Paket-Standard" if doc.standard_section else "optional"
    lines += [f"### [{doc.name}] ({marker})", "", doc.meaning, "",
              f"*Wann brauche ich das?* {doc.when_needed}", "", FENCE + "ini",
              doc.example.replace(CR, ""), FENCE, "", f"*Referenz: {doc.reference}*", ""]

lines += ["## Befehls-Referenz", ""]
for doc in COMMAND_DOCS.values():
    lines += [f"### {doc.name}", "", FENCE, doc.syntax.replace(CR, " / "), FENCE, "",
              doc.semantics, "", f"*Uninstall-Verhalten:* {doc.uninstall}", "", FENCE + "ini",
              doc.example.replace(CR, NL), FENCE, "", f"*Fallstricke & Best Practice:* {doc.pitfall}", ""]

lines += ["## Prädikate (If-Bedingungen)", ""]
for doc in PREDICATE_DOCS.values():
    alias = f" *(Alias von `{doc.alias_of}`)*" if doc.alias_of else ""
    lines += [f"### {doc.name}{alias}", "", FENCE, doc.syntax.replace(CR, " / "), FENCE, "",
              doc.semantics, "", FENCE + "ini",
              doc.example.replace(CR, NL), FENCE, "", f"*Fallstricke & Best Practice:* {doc.pitfall}", ""]

lines += ["## Funktionen (Set-Zuweisung)", ""]
for doc in FUNCTION_DOCS.values():
    lines += [f"### {doc.name}", "", FENCE, doc.syntax.replace(CR, " / "), FENCE, "",
              doc.semantics, "", FENCE + "ini",
              doc.example.replace(CR, NL), FENCE, "", f"*Fallstricke & Best Practice:* {doc.pitfall}", ""]

lines += ["## Variablen-Referenz (%...%)", ""]
for doc in VARIABLE_DOCS.values():
    lines += [f"### {doc.name} ({doc.category})", "",
              doc.meaning, "", f"*Typischer Wert / Pfad:* `{doc.example_value}`", "",
              FENCE + "ini", doc.usage.replace(CR, NL), FENCE, "",
              f"*Fallstricke & Best Practice:* {doc.pitfall}", ""]

lines += ["## Lint-Diagnosen VAL-001…025", ""]
for doc in VAL_DOCS.values():
    lines += [f"### {doc.code} ({doc.severity})", "", f"*Ursache:* {doc.cause}", "",
              f"*Behebung:* {doc.remedy}", "", f"*Referenz: {doc.reference}*", ""]

Path("docs/setupinf-schnellkurs.md").write_text(NL.join(lines), encoding="utf-8")
print(f"generiert: {len(lines)} Zeilen")
