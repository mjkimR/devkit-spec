"""``RULE-document-summary``: documents carry a short English ``summary``, the main signal of document search.

``devkit spec search`` embeds a document's ID and ``summary``; titles and bodies may be in any language and are ranked
lexically only. A summary therefore has to exist where agents search and has to be English for the embedding model.

- Capabilities, stories, decisions, architecture documents, proposals (``proposal.md``) and specs (``spec.md``) MUST
  have a ``summary``: a non-empty string. A file that still carries the skeleton marker (a spec just created by
  ``devkit spec new`` or a handoff) is exempt until it is written.
- Any ``summary``, required or not, MUST be English: no letter outside the Latin script (digits, punctuation and
  symbols are free), and at most ``max_length`` characters (setting, default 300), one or two sentences.

Current documents only (a completed bundle's files when explicitly targeted); materials are free-form and exempt. Not
fixable: a summary is written, never generated.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from devkit.rules import Phase, RuleContext, Severity, Violation
from devkit.rules.rules import BaseRule

from devkit_spec.documents import Document, Kind
from devkit_spec.rules import document_index, is_material, reportable

RULE_ID = "RULE-document-summary"
SKELETON_MARKER = "<!-- devkit:skeleton -->"
REQUIRED = {Kind.CAPABILITY, Kind.STORY, Kind.DECISION, Kind.ARCHITECTURE}
ANCHORS = {Kind.PROPOSAL: "proposal.md", Kind.SPEC: "spec.md"}
REMEDIATION = (
    "Write `summary:` in the frontmatter: one or two English sentences saying what the document defines"
    " (the title and body may stay in any language)"
)


@dataclass(frozen=True)
class DocumentSummarySettings:
    max_length: int = 300


def required(document: Document) -> bool:
    """Whether ``document``'s kind needs a summary (a proposal or spec only for its anchor file)."""
    if document.kind in REQUIRED:
        return True
    anchor = ANCHORS.get(document.kind)
    return anchor is not None and document.path.rsplit("/", 1)[-1] == anchor


def foreign_letters(text: str) -> list[str]:
    """The distinct letters of ``text`` outside the Latin script, in order of appearance."""
    found: list[str] = []
    for char in text:
        if char.isalpha() and "LATIN" not in unicodedata.name(char, "") and char not in found:
            found.append(char)
    return found


def _line(text: str, key: str) -> int:
    for number, line in enumerate(text.split("\n"), 1):
        if line.startswith(f"{key}:"):
            return number
        if number > 1 and line.strip() == "---":
            break
    return 1


class DocumentSummaryRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="document-summary",
            description="Searchable documents carry a short English summary, the main signal of document search.",
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            settings=DocumentSummarySettings(),
            guide="document_summary.md",
        )

    def validate_settings(self, settings: DocumentSummarySettings) -> None:
        if settings.max_length <= 0:
            raise ValueError("max_length must be a positive integer")

    def check(self, ctx: RuleContext) -> list[Violation]:
        index = document_index(ctx)
        found: list[Violation] = []
        for document in index.documents:
            if is_material(document) or not reportable(ctx, index, document):
                continue
            problem = self._problem(ctx, document)
            if problem is not None:
                text = ctx.cache.read_text(document.path)
                line = _line(text, "summary") if "summary" in document.frontmatter else 1
                found.append(
                    Violation(
                        rule_id=self.id,
                        file=document.path,
                        line=line,
                        message=problem,
                        remediation=REMEDIATION,
                    )
                )
        return found

    def _problem(self, ctx: RuleContext, document: Document) -> str | None:
        value = document.frontmatter.get("summary")
        if value is None:
            if not required(document) or SKELETON_MARKER in ctx.cache.read_text(document.path):
                return None
            return f"{document.id} has no summary"
        if not isinstance(value, str) or not value.strip():
            return "summary must be a non-empty string"
        letters = foreign_letters(value)
        if letters:
            return f"summary must be English; it contains {''.join(letters[:5])}"
        limit = ctx.settings(self, document.path).max_length
        if len(value.strip()) > limit:
            return f"summary has {len(value.strip())} characters; keep it to one or two sentences ({limit} at most)"
        return None
