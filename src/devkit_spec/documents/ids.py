"""The document ID grammar: ``<PREFIX>-<slug>``, the prefix naming the document kind.

An ID starts with one of the prefixes below, a dash, then a letter or digit
followed by letters, digits, ``_`` and ``-``. Path and naming conventions per
kind (``CAP-<AREA>-<slug>`` under ``docs/capabilities/<area>/``, dated
partitions for decisions and specs) are checked by the rules, not here: the
index accepts any well-formed ID wherever it is declared.
"""

from __future__ import annotations

import re
from enum import StrEnum


class Kind(StrEnum):
    """What a document is, derived from its ID prefix."""

    CAPABILITY = "capability"
    STORY = "story"
    ARCHITECTURE = "architecture"
    DECISION = "decision"
    PROPOSAL = "proposal"
    PROPOSAL_DECISION = "proposal-decision"
    SPEC = "spec"
    PLAN = "plan"
    TASKS = "tasks"
    RECONCILE = "reconcile"
    FEEDBACK = "feedback"
    MATERIAL = "material"


PREFIXES: dict[str, Kind] = {
    "CAP": Kind.CAPABILITY,
    "US": Kind.STORY,
    "ARCH": Kind.ARCHITECTURE,
    "ADR": Kind.DECISION,
    "PROP": Kind.PROPOSAL,
    "PADR": Kind.PROPOSAL_DECISION,
    "SPEC": Kind.SPEC,
    "PLAN": Kind.PLAN,
    "TASKS": Kind.TASKS,
    "REC": Kind.RECONCILE,
    "FB": Kind.FEEDBACK,
    "MAT": Kind.MATERIAL,
}

ID_SOURCE = rf"(?:{'|'.join(PREFIXES)})-[A-Za-z0-9][A-Za-z0-9_-]*"
ID_PATTERN = re.compile(rf"^{ID_SOURCE}$")


def is_id(value: str) -> bool:
    """Whether ``value`` is a well-formed document ID."""
    return ID_PATTERN.match(value) is not None


def kind_of(document_id: str) -> Kind | None:
    """The kind named by the prefix of a well-formed ID, else ``None``."""
    if not is_id(document_id):
        return None
    return PREFIXES[document_id.split("-", 1)[0]]
