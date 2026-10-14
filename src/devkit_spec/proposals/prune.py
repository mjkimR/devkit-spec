"""Remove proposal directories a handoff left empty in another checkout.

A handoff deletes the proposal bundle in the worktree it runs in. When that branch is merged into the base checkout,
Git removes the tracked files there but leaves the directories (``decisions/``, ``materials/``) behind. A directory
holding no file at any depth is removed; any file, tracked or not, keeps its directory, so nothing is ever deleted
but empty directories (``devkit.core.remove_empty_tree``; symbolic links count as files).
"""

from __future__ import annotations

from pathlib import Path

from devkit.core import remove_empty_tree

from devkit_spec.proposals.scaffold import PROPOSALS, require_slug


def prune_proposals(root: Path, slug: str | None = None) -> list[str]:
    """Remove empty ``docs/proposals/PROP-<slug>/`` trees (every ``PROP-*`` one without ``slug``); return them."""
    base = root / PROPOSALS
    if slug is not None:
        candidates = [base / f"PROP-{require_slug(slug)}"]
    else:
        candidates = sorted(base.glob("PROP-*")) if base.is_dir() else []
    return [path.relative_to(root).as_posix() for path in candidates if remove_empty_tree(path)]
