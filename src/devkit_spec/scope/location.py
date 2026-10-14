"""Where a worktree finds the registry and keeps its owner token.

The default shared path is ``devkit-spec-scope/`` in the Git common directory and the default namespace the first
16 hex digits of the SHA-256 of that directory's absolute path, so every worktree of one repository shares them
without configuration, and a cache clean never touches them. ``[tool.spec.scope]`` overrides both; to share one
registry between clones or hosts, set the same absolute ``shared_path`` and an explicit ``namespace`` on each.

The token lives in the worktree's own Git directory (``<git-dir>/devkit-spec-scope-token``, mode 0600): one per
worktree, created exclusively, never in the working tree, never in the registry.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from devkit.core import GitError, run_git

from devkit_spec.config import ScopeConfig
from devkit_spec.errors import ScopeNotAWorktreeError
from devkit_spec.scope.deadline import Deadline

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
        inside = run_git(root, "rev-parse", "--is-inside-work-tree", deadline=deadline).strip()
        output = run_git(
            root, "rev-parse", "--path-format=absolute", "--git-common-dir", "--git-dir", deadline=deadline
        )
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
        return run_git(root, "rev-parse", "--verify", "--quiet", "HEAD", deadline=deadline).decode().strip()
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


def _symbolic_head(cwd: Path, deadline: Deadline) -> str:
    """The branch ref ``HEAD`` points to in the Git directory or work tree at ``cwd``; ``""`` when detached."""
    try:
        return run_git(cwd, "symbolic-ref", "--quiet", "HEAD", deadline=deadline).decode().strip()
    except GitError as exc:
        if exc.returncode is None:
            raise
        return ""


def base_ref(location: Location, deadline: Deadline) -> str:
    """The branch the base checkout is on (``refs/heads/<name>``), which ``devkit worktree finish`` integrates into.

    ``""`` when the base checkout is detached, or when this workspace is on that same branch (the base checkout
    itself): there no upstream commit can be told apart from the task's own.
    """
    ref = _symbolic_head(location.common_dir, deadline)  # the base checkout's HEAD lives in the common directory
    return "" if not ref or ref == _symbolic_head(location.root, deadline) else ref


def save_token(path: Path, token: str) -> None:
    """Create the token file, readable by its owner only; ``FileExistsError`` when the worktree already holds one.

    The token is written to a temporary file and linked into place, so a reader sees no token or a complete one,
    and of two registrations racing in one worktree exactly one saves its token.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{TOKEN_FILE}-", dir=path.parent)  # created with mode 0600
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"{token}\n")
        try:
            os.link(name, path)
        except FileExistsError:
            raise
        except OSError:  # a file system without hard links: create the token exclusively instead
            _create_exclusive(path, token)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(name)


def _create_exclusive(path: Path, token: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(f"{token}\n")


def remove_token(path: Path) -> None:
    with contextlib.suppress(FileNotFoundError):
        path.unlink()
