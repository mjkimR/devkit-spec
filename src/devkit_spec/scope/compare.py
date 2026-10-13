"""Pairwise comparison of scope sets: document overlap, code overlap and the unresolved count of both sides.

A document overlap is the same declared document path on both sides. A code overlap is a pair of declared,
candidate or observed paths where one equals or contains the other (``covers``, by whole segments). The result is
evidence only; it neither ranks pairs nor proves a merge conflict or semantic independence.
"""

from __future__ import annotations

from collections.abc import Sequence

from devkit_spec.entrypoints import covers
from devkit_spec.scope.model import Evidence, PairResult, ScopeSet


def compare(a: ScopeSet, b: ScopeSet) -> PairResult:
    """The overlaps of ``a`` with ``b``; ``unresolved`` counts both sides."""
    other_docs = {path.path: path for path in b.docs}
    docs = [
        Evidence("doc", path.path, path.kind, path.path, path.source, other_docs[path.path].source)
        for path in a.docs
        if path.path in other_docs
    ]
    code: list[Evidence] = []
    seen: set[tuple[str, str]] = set()
    for mine in [*a.code, *a.observed]:
        for theirs in [*b.code, *b.observed]:
            key = (mine.path, theirs.path)
            if key in seen or not (covers(mine.path, theirs.path) or covers(theirs.path, mine.path)):
                continue
            seen.add(key)
            code.append(Evidence("code", mine.path, mine.kind, theirs.path, mine.source, theirs.source))
    return PairResult(
        a=a.id,
        b=b.id,
        docs=tuple(sorted(docs, key=lambda item: item.path)),
        code=tuple(sorted(code, key=lambda item: (item.path, item.other))),
        unresolved=len(a.unresolved) + len(b.unresolved),
    )


def compare_all(sets: Sequence[ScopeSet]) -> list[PairResult]:
    """Every pair of ``sets``, in order."""
    return [compare(sets[i], sets[j]) for i in range(len(sets)) for j in range(i + 1, len(sets))]


def compare_with(mine: ScopeSet, others: Sequence[ScopeSet]) -> list[PairResult]:
    """``mine`` against each of ``others``."""
    return [compare(mine, other) for other in others]
