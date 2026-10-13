"""Documents and the references between them."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from devkit_spec.documents.ids import Kind

# Frontmatter fields that reference other documents. A list field holds IDs, a scalar field one ID.
LIST_FIELDS = ("stories", "capabilities", "related_stories", "related_capabilities")
SCALAR_FIELDS = ("spec", "plan")
# Where a document came from: an edge of its history, not of the current contract.
PROVENANCE_FIELDS = ("proposal",)
BODY = "body"


@dataclass(frozen=True, slots=True)
class Reference:
    """One mention of ``target`` in ``source``'s document at ``path``.

    ``field`` is the frontmatter field, or ``body`` for prose. ``line`` and ``column`` are 1-based; ``start`` and
    ``end`` are character offsets of the ID in the document text (for a quoted frontmatter value, the quotes are
    included), so a rewrite replaces exactly what was read. ``bracket`` marks a ``[ID]`` body reference rather than
    the canonical `` `ID` ``.
    """

    target: str
    source: str
    path: str
    field: str
    line: int
    column: int
    start: int
    end: int
    bracket: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "source": self.source,
            "path": self.path,
            "field": self.field,
            "line": self.line,
            "column": self.column,
            "bracket": self.bracket,
        }


@dataclass(frozen=True, slots=True)
class Issue:
    """A malformed reference field the parser skipped; the rules report it."""

    line: int
    message: str


@dataclass(slots=True)
class Document:
    """A Markdown file under ``docs/`` or ``specs/`` whose frontmatter declares a well-formed ID.

    ``id`` is the frontmatter ``id`` (``reconcile_id`` for a reconcile file), ``path`` workspace-relative.
    ``frontmatter`` is the parsed header as it is. ``references`` are the edges of the current contract (reference
    fields and prose), ``provenance`` the ``proposal`` a spec was handed off from. A parsed document is shared
    between index loads of the same text and is never modified afterwards.
    """

    id: str
    path: str
    kind: Kind
    frontmatter: dict[str, Any]
    references: list[Reference] = field(default_factory=list)
    provenance: list[Reference] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def status(self) -> str:
        return _text(self.frontmatter.get("status"))

    @property
    def title(self) -> str:
        return _text(self.frontmatter.get("title"))

    @property
    def summary(self) -> str:
        """The frontmatter ``summary``: one or two English sentences saying what the document defines."""
        return _text(self.frontmatter.get("summary"))

    @property
    def area(self) -> str:
        return _text(self.frontmatter.get("area"))

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": str(self.kind),
            "path": self.path,
            "status": self.status,
            "title": self.title,
            "area": self.area,
            "summary": self.summary,
        }


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
