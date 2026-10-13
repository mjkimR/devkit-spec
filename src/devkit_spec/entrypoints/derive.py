"""Derivation: join a bundle's ``_Boundary`` code paths with its reconciled capability and story documents.

Document side: each ``reconcile.md`` target that is not ``waived`` and is entrypoint-bearing (``paths``), once.
Code side: each ``_Boundary`` entry that is a literal path outside ``docs/`` and ``specs/``, once per bundle; one
under another candidate of the same bundle is folded into the shortest such ancestor. Every (document, code) pair
is reported with ``state`` (``declared`` when an equal or ancestor entrypoint exists, else ``new``) and ``exists``
(the path is in the working tree). What is not turned into a pair is ``Skipped`` with a reason. A pair is a
mechanical join of declarations, not proof that the code implements the document.
"""

from __future__ import annotations

import posixpath
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path

from devkit_spec.documents import Document
from devkit_spec.entrypoints.bundle import Bundle
from devkit_spec.entrypoints.paths import ROOT, covers, entrypoint_bearing, exists, normalize
from devkit_spec.errors import EntrypointsPathError

NOT_APPLICABLE = ("n/a", "none")
EXCLUDED_TREES = ("docs", "specs")


class State(StrEnum):
    NEW = "new"
    DECLARED = "declared"


class SkipKind(StrEnum):
    BOUNDARY = "boundary"
    TARGET = "target"
    BUNDLE = "bundle"
    APPLY = "apply"


class Reason(StrEnum):
    NOT_A_PATH = "not-a-path"
    INVALID_PATH = "invalid-path"
    EXCLUDED_TREE = "excluded-tree"
    EXCLUDED = "excluded"
    WAIVED = "waived"
    NOT_ENTRYPOINT_BEARING = "not-entrypoint-bearing"
    MISSING_DOC = "missing-doc"
    NOT_A_DOCUMENT = "not-a-document"
    INPUT_MISSING = "input-missing"
    INVALID_INPUT = "invalid-input"
    FOLDED = "folded"
    MISSING_PATH = "missing-path"


@dataclass(frozen=True)
class Pair:
    """One derived document-code link.

    A pair of one bundle has ``spec`` and ``task``; an aggregated pair (``aggregate``) has ``count`` and ``specs``
    instead. ``folded_into`` is the same-bundle ancestor candidate that covers ``code``.
    """

    doc: str
    doc_path: str
    code: str
    state: State
    exists: bool
    spec: str | None = None
    task: int | None = None
    folded_into: str | None = None
    count: int | None = None
    specs: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"doc": self.doc, "doc_path": self.doc_path, "code": self.code}
        if self.count is None:
            data |= {"spec": self.spec, "task": self.task, "folded_into": self.folded_into}
        else:
            data |= {"count": self.count, "specs": list(self.specs or ())}
        return data | {"state": str(self.state), "exists": self.exists}


@dataclass(frozen=True)
class Skipped:
    """An input or candidate the derivation did not turn into a pair, or that ``--apply`` did not write."""

    kind: SkipKind
    value: str
    reason: Reason
    spec: str | None = None
    task: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": str(self.kind),
            "value": self.value,
            "spec": self.spec,
            "task": self.task,
            "reason": str(self.reason),
        }


@dataclass(frozen=True)
class _Doc:
    id: str
    path: str
    entrypoints: tuple[str, ...]


@dataclass
class _Candidate:
    path: str
    task: int
    folded: str | None = None


def declared_entrypoints(document: Document) -> tuple[str, ...]:
    """The string values of a document's ``entrypoints`` (none when the field is absent or not a list)."""
    value = document.frontmatter.get("entrypoints")
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def classify_boundary(raw: str) -> tuple[str | None, Reason | None]:
    """The normalized code path of one ``_Boundary`` entry, or why it is skipped."""
    value = raw.strip()
    if not value or value.lower() in NOT_APPLICABLE:
        return None, Reason.NOT_A_PATH
    try:
        code = normalize(value)
    except EntrypointsPathError:
        return None, Reason.INVALID_PATH
    if code == ROOT or code in EXCLUDED_TREES or code.startswith(tuple(f"{tree}/" for tree in EXCLUDED_TREES)):
        return None, Reason.EXCLUDED_TREE
    return code, None


def derive(root: Path, bundle: Bundle, documents: Mapping[str, Document]) -> tuple[list[Pair], list[Skipped]]:
    """The pairs of one bundle and what was skipped; ``documents`` maps workspace-relative paths to the index's
    documents."""
    skipped: list[Skipped] = []
    docs: list[_Doc] = []
    seen_docs: set[str] = set()
    for target in bundle.targets:
        written = target.file.strip()
        if not written:
            continue
        file = posixpath.normpath(written)

        def skip(reason: Reason, value: str = written) -> None:
            skipped.append(Skipped(SkipKind.TARGET, value, reason, spec=bundle.spec_id))

        if target.resolution.strip().lower() == "waived":
            skip(Reason.WAIVED)
        elif not entrypoint_bearing(file):
            skip(Reason.NOT_ENTRYPOINT_BEARING)
        elif file in seen_docs:
            continue
        elif file in documents:
            seen_docs.add(file)
            document = documents[file]
            docs.append(_Doc(document.id, file, declared_entrypoints(document)))
        else:
            skip(Reason.NOT_A_DOCUMENT if (root / file).is_file() else Reason.MISSING_DOC)

    candidates: list[_Candidate] = []
    seen_code: set[str] = set()
    for task in bundle.tasks:
        for raw in task.values:
            code, reason = classify_boundary(raw)
            if code is None:
                skipped.append(Skipped(SkipKind.BOUNDARY, raw, reason or Reason.NOT_A_PATH, bundle.spec_id, task.index))
            elif code not in seen_code:
                seen_code.add(code)
                candidates.append(_Candidate(code, task.index))
    _fold(candidates)

    present = {candidate.path: exists(root, candidate.path) for candidate in candidates}
    pairs = [
        Pair(
            doc=doc.id,
            doc_path=doc.path,
            code=candidate.path,
            state=state_for(doc.entrypoints, candidate.path),
            exists=present[candidate.path],
            spec=bundle.spec_id,
            task=candidate.task,
            folded_into=candidate.folded,
        )
        for doc in docs
        for candidate in candidates
    ]
    return sort_pairs(pairs), skipped


def _fold(candidates: list[_Candidate]) -> None:
    for candidate in candidates:
        for other in candidates:
            if (
                other.path != candidate.path
                and candidate.path.startswith(f"{other.path}/")
                and (candidate.folded is None or len(other.path) < len(candidate.folded))
            ):
                candidate.folded = other.path


def state_for(existing: Iterable[str], code: str) -> State:
    """``declared`` when an existing entrypoint equals ``code`` or is a directory containing it."""
    for entry in existing:
        try:
            declared = normalize(entry)
        except EntrypointsPathError:
            continue
        if covers(declared, code):
            return State.DECLARED
    return State.NEW


def sort_pairs(pairs: Iterable[Pair]) -> list[Pair]:
    return sorted(pairs, key=lambda pair: (pair.doc_path, pair.code))


def aggregate(per_bundle: Iterable[Sequence[Pair]], min_count: int) -> list[Pair]:
    """Merge per-bundle pairs by (document, code): folded pairs are left out, and pairs seen in fewer than
    ``min_count`` distinct specs are dropped."""
    merged: dict[tuple[str, str], Pair] = {}
    specs: dict[tuple[str, str], set[str]] = {}
    for pairs in per_bundle:
        for pair in pairs:
            if pair.folded_into is not None:
                continue
            key = (pair.doc_path, pair.code)
            if key not in merged:
                merged[key] = pair
                specs[key] = set()
            if pair.spec:
                specs[key].add(pair.spec)
    out = [
        replace(pair, spec=None, task=None, folded_into=None, count=len(specs[key]), specs=tuple(sorted(specs[key])))
        for key, pair in merged.items()
        if len(specs[key]) >= min_count
    ]
    return sort_pairs(out)


def _normalize_all(paths: Iterable[str]) -> list[str]:
    return [normalize(path) for path in paths]


def select(pairs: Sequence[Pair], includes: Sequence[str]) -> list[Pair]:
    """The pairs whose code path equals or lies under one of ``includes`` (all pairs when it is empty).

    Raises ``EntrypointsPathError`` for an invalid path.
    """
    wanted = _normalize_all(includes)
    if not wanted:
        return list(pairs)
    return [pair for pair in pairs if any(covers(path, pair.code) for path in wanted)]


def exclude(pairs: Sequence[Pair], excludes: Sequence[str]) -> tuple[list[Pair], list[Skipped]]:
    """Drop the pairs whose code path equals or lies under one of ``excludes``, each reported as skipped.

    Raises ``EntrypointsPathError`` for an invalid path.
    """
    dropped = _normalize_all(excludes)
    kept: list[Pair] = []
    skipped: list[Skipped] = []
    for pair in pairs:
        if any(covers(path, pair.code) for path in dropped):
            skipped.append(Skipped(SkipKind.BOUNDARY, pair.code, Reason.EXCLUDED, pair.spec, pair.task))
        else:
            kept.append(pair)
    return kept, skipped
