"""Remove proposal directories a handoff left empty in another checkout.

A handoff deletes the proposal bundle in the worktree it runs in. When that branch is merged into the base checkout,
Git removes the tracked files there but leaves the directories (``decisions/``, ``materials/``) behind. A directory
holding no file at any depth is removed; any file, tracked or not, keeps its directory, so nothing is ever deleted
but empty directories.
"""

from __future__ import annotations

import os
from pathlib import Path

from devkit_spec.proposals.scaffold import PROPOSALS, require_slug


def _remove_empty_tree(directory: Path) -> bool:
    """Remove ``directory`` when it and every directory under it hold no file (symbolic links count as files)."""
    if directory.is_symlink() or not directory.is_dir():
        return False
    for current, dirnames, filenames in os.walk(directory):
        here = Path(current)
        if filenames or any((here / name).is_symlink() for name in dirnames):
            return False
    for current, _dirnames, _filenames in os.walk(directory, topdown=False):
        Path(current).rmdir()
    return True


def prune_proposals(root: Path, slug: str | None = None) -> list[str]:
    """Remove empty ``docs/proposals/PROP-<slug>/`` trees (every ``PROP-*`` one without ``slug``); return them."""
    base = root / PROPOSALS
    if slug is not None:
        candidates = [base / f"PROP-{require_slug(slug)}"]
    else:
        candidates = sorted(base.glob("PROP-*")) if base.is_dir() else []
    return [path.relative_to(root).as_posix() for path in candidates if _remove_empty_tree(path)]
