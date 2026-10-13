"""Where a worktree finds the registry and keeps its owner token.

The default shared path is ``devkit-spec-scope/`` in the Git common directory and the default namespace the first
16 hex digits of the SHA-256 of that directory's absolute path, so every worktree of one repository shares them
without configuration, and a cache clean never touches them. ``[tool.spec.scope]`` overrides both; to share one
registry between clones or hosts, set the same absolute ``shared_path`` and an explicit ``namespace`` on each.

The token lives in the worktree's own Git directory (``<git-dir>/devkit-spec-scope-token``, mode 0600): one per
worktree, never in the working tree, never in the registry.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from devkit.core import GitError

from devkit_spec.config import ScopeConfig
from devkit_spec.errors import ScopeNotAWorktreeError
from devkit_spec.scope.deadline import Deadline, git

SHARED_DIR = "devkit-spec-scope"
TOKEN_FILE = "devkit-spec-scope-token"


@dataclass(frozen=True)
class Location:
    """``root`` is the workspace root (a directory of a Git work tree); the other paths are absolute."""

    root: Path
    common_dir: Path
    git_dir: Path
    shared_path: Path
    namespace: str

    @property
    def token_path(self) -> Path:
        return self.git_dir / TOKEN_FILE

    @property
    def linked(self) -> bool:
        """Whether the workspace is in a linked worktree (its Git directory is not the common one)."""
        return self.git_dir != self.common_dir


def default_namespace(common_dir: Path) -> str:
    return hashlib.sha256(str(common_dir).encode("utf-8")).hexdigest()[:16]


def locate(root: Path, config: ScopeConfig, deadline: Deadline) -> Location:
    """The registry location of the workspace at ``root``; ``ScopeNotAWorktreeError`` outside a Git work tree."""
    try:
        inside = git(root, "rev-parse", "--is-inside-work-tree", deadline=deadline).strip()
        output = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir", "--git-dir", deadline=deadline)
    except GitError as exc:
        if exc.returncode is None:
            raise
        raise ScopeNotAWorktreeError(
            f"{root} is not inside a Git work tree: {exc.stderr}", target_files=[str(root)]
        ) from exc
    if inside != b"true":
        raise ScopeNotAWorktreeError(f"{root} is not inside a Git work tree", target_files=[str(root)])
    common, git_dir = (Path(os.fsdecode(line)).resolve() for line in output.splitlines()[:2])
    return Location(
        root=root,
        common_dir=common,
        git_dir=git_dir,
        shared_path=config.shared_path or common / SHARED_DIR,
        namespace=config.namespace or default_namespace(common),
    )


def head_revision(root: Path, deadline: Deadline) -> str:
    """The commit of ``HEAD``; ``""`` before the first commit."""
    try:
        return git(root, "rev-parse", "--verify", "--quiet", "HEAD", deadline=deadline).decode().strip()
    except GitError as exc:
        if exc.returncode is None:
            raise
        return ""


def load_token(path: Path) -> str | None:
    """The saved token; ``None`` when there is none."""
    try:
        token = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    return token or None


def save_token(path: Path, token: str) -> None:
    """Write the token readable by its owner only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(f"{token}\n")


def remove_token(path: Path) -> None:
    with contextlib.suppress(FileNotFoundError):
        path.unlink()
