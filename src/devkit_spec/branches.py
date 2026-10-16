"""Activity branches: Development runs on ``dev-<slug>``, Planning on ``plan-<slug>`` (01 §4.7).

``current_branch`` reads the branch of a checkout; ``require_development_branch`` refuses to write a slug's
Development unit (a spec bundle from ``devkit spec new`` or a proposal handoff) on any other branch, in a linked
worktree and in the base checkout alike: the unit would land on another task's branch, or on the base itself.
Outside Git nothing is checked.
"""

from __future__ import annotations

from pathlib import Path

from devkit.advisory import AdvisoryError
from devkit.core import GitError, run_git

PLANNING_PREFIX = "plan-"
DEVELOPMENT_PREFIX = "dev-"
BRANCH_LIMIT = 64  # devkit worktree's limit on an activity branch name
SLUG_LIMIT = BRANCH_LIMIT - len(PLANNING_PREFIX)  # so plan-<slug> and dev-<slug> both fit


def checkout(root: Path) -> tuple[bool, str] | None:
    """``(linked, branch)`` of the checkout at ``root`` (``branch`` empty on a detached HEAD); ``None`` outside Git.

    A ``GitError`` without an exit status (Git missing, a timeout) propagates.
    """
    try:
        dirs = run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir", "--git-dir").splitlines()
    except GitError as exc:
        if exc.returncode is None:
            raise
        return None
    common, git_dir = (Path(line.decode()).resolve() for line in dirs[:2])
    try:
        branch = run_git(root, "symbolic-ref", "--quiet", "--short", "HEAD").decode().strip()
    except GitError as exc:
        if exc.returncode is None:
            raise
        branch = ""
    return common != git_dir, branch


def require_development_branch(root: Path, slug: str, action: str, error: type[AdvisoryError]) -> None:
    """Refuse ``action`` for ``slug`` unless the checkout at ``root`` is on ``dev-<slug>``; raises ``error``."""
    found = checkout(root)
    if found is None:
        return
    linked, branch = found
    expected = f"{DEVELOPMENT_PREFIX}{slug}"
    if branch == expected:
        return
    where = "worktree" if linked else "checkout"
    raise error(
        f"{action} of {slug} in the {where} of branch {branch or '- (detached HEAD)'}; it runs on branch {expected}",
        target_files=[str(root)],
        fix=f"Run it on {expected}: in the base checkout `devkit worktree start {expected}` (cd to the path it prints)"
        f" or `devkit worktree start {expected} --no-worktree`; an existing {expected} is continued with"
        f" `devkit worktree start {expected} --existing-branch {expected} --unit <dir>`. Then rerun there",
    )


def planning_branches(root: Path) -> dict[str, str]:
    """``slug -> ref`` for every ``plan-<slug>`` branch, local or fetched from a remote (``refs/remotes/*/``); the
    local ref wins. Empty outside Git. Planning is running for such a slug (01 §4.7): devkit fetches nothing, so a
    branch made elsewhere shows only once it was fetched."""
    try:
        listed = run_git(
            root,
            "for-each-ref",
            "--format=%(refname)",
            f"refs/heads/{PLANNING_PREFIX}*",
            f"refs/remotes/*/{PLANNING_PREFIX}*",
        ).decode()
    except GitError as exc:
        if exc.returncode is None:
            raise
        return {}
    found: dict[str, str] = {}
    for ref in listed.splitlines():
        short = ref.removeprefix("refs/heads/").removeprefix("refs/remotes/")
        name = short.rsplit("/", 1)[-1] if ref.startswith("refs/remotes/") else short
        if not name.startswith(PLANNING_PREFIX) or ref.endswith("/HEAD"):
            continue
        slug = name.removeprefix(PLANNING_PREFIX)
        if ref.startswith("refs/heads/") or slug not in found:
            found[slug] = short
    return found
