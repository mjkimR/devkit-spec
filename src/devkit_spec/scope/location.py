"""Where a worktree finds the registry and keeps its owner token.

The default shared path is ``devkit-spec-scope/`` in the Git common directory and the default namespace the first
16 hex digits of the SHA-256 of that directory's absolute path, so every worktree of one repository shares them
without configuration, and a cache clean never touches them. ``[tool.spec.scope]`` overrides both; to share one
registry between clones or hosts, set the same absolute ``shared_path`` and an explicit ``namespace`` on each.

The token lives in the worktree's own Git directory (``<git-dir>/devkit-spec-scope-token``, mode 0600): one per
worktree, created exclusively, never in the working tree, never in the registry. It is written to a temporary file
(``.devkit-spec-scope-token-<random>``) and hard-linked into place; a file system without hard links gets the token
file created exclusively and written in place instead, so ``load_token`` takes only a file that ends with its newline
for a token. A temporary file a crash left behind is removed by the next ``save_token`` or ``load_token`` once it is
older than a minute.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from devkit.core import GitError, run_git

from devkit_spec.config import ScopeConfig
from devkit_spec.errors import ScopeNotAWorktreeError
from devkit_spec.scope.deadline import Deadline

SHARED_DIR = "devkit-spec-scope"
TOKEN_FILE = "devkit-spec-scope-token"
_TEMP_TOKEN = re.compile(rf"\.{re.escape(TOKEN_FILE)}-[a-z0-9_]{{8}}")  # what tempfile.mkstemp names in save_token
_TEMP_TOKEN_AGE = 60.0  # seconds: older temporary token files belong to no save still in progress


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
    """The saved token; ``None`` when there is none.

    A file that does not end with the token's newline (empty or partial: a save in progress, or one interrupted on a
    file system without hard links) holds no token either; ``incomplete_token`` tells the two apart.
    """
    _clean_temp_tokens(path.parent)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    token = text.strip()
    return token if token and text.endswith("\n") else None


def incomplete_token(path: Path) -> bool:
    """Whether a token file exists at ``path`` but ``load_token`` takes it for no token (empty or partial)."""
    return path.exists() and load_token(path) is None


def _clean_temp_tokens(directory: Path) -> None:
    """Remove the temporary token files a crashed ``save_token`` left in ``directory`` (exact name pattern only)."""
    cutoff = time.time() - _TEMP_TOKEN_AGE
    with contextlib.suppress(OSError):
        for entry in directory.glob(f".{TOKEN_FILE}-*"):
            if not _TEMP_TOKEN.fullmatch(entry.name):
                continue
            with contextlib.suppress(OSError):
                if entry.lstat().st_mtime < cutoff:
                    entry.unlink()


def _symbolic_head(cwd: Path, deadline: Deadline) -> str:
    """The branch ref ``HEAD`` points to in the Git directory or work tree at ``cwd``; ``""`` when detached."""
    try:
        return run_git(cwd, "symbolic-ref", "--quiet", "HEAD", deadline=deadline).decode().strip()
    except GitError as exc:
        if exc.returncode is None:
            raise
        return ""


def base_ref(location: Location, deadline: Deadline) -> str:
    """The branch the base checkout is on now (``refs/heads/<name>``): the best available guess at the task's base
    branch. devkit records no fork branch for a worktree, and the base checkout may have switched branches since the
    worktree was created, so a consumer never trusts it alone (``observe_git`` checks it against the base revision).

    ``""`` when the base checkout is detached, or when this workspace is on that same branch (the base checkout
    itself): there no upstream commit can be told apart from the task's own.
    """
    ref = _symbolic_head(location.common_dir, deadline)  # the base checkout's HEAD lives in the common directory
    return "" if not ref or ref == _symbolic_head(location.root, deadline) else ref


def ref_exists(root: Path, ref: str, deadline: Deadline) -> bool:
    """Whether ``ref`` names a commit in the repository at ``root``."""
    try:
        run_git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", deadline=deadline)
    except GitError as exc:
        if exc.returncode is None:
            raise
        return False
    return True


def save_token(path: Path, token: str) -> None:
    """Create the token file, readable by its owner only; ``FileExistsError`` when the worktree already holds one.

    The token is written to a temporary file and hard-linked into place, so a reader sees no token or a complete
    one, and of two registrations racing in one worktree exactly one saves its token. Without hard links the token
    file is created exclusively and written in place: still exactly one winner, and a reader that comes between the
    creation and the write sees a file without the final newline, which ``load_token`` takes for no token.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _clean_temp_tokens(path.parent)
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
