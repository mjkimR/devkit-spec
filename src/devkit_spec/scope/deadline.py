"""The deadline every registry operation runs under, and Git calls bounded by it.

A command gets one ``Deadline`` (``[tool.spec.scope] timeout``); the lock wait and each Git subprocess take the time
that is left, and running out raises ``ScopeTimeoutError``. A Git subprocess that outlives its share is killed by
``run_git``'s timeout, so a timed-out command ends within a moment of its deadline.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from devkit.core import GitError, run_git

from devkit_spec.errors import ScopeTimeoutError

JOURNAL_SECONDS = 5.0  # one journal append, independent of the operation's own deadline


class Deadline:
    """A point in monotonic time; ``remaining`` seconds until it."""

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self._end = time.monotonic() + seconds

    def remaining(self) -> float:
        return self._end - time.monotonic()

    def expired(self) -> bool:
        return self.remaining() <= 0

    def check(self, what: str) -> None:
        """Raise ``ScopeTimeoutError`` when the deadline has passed."""
        if self.expired():
            raise timeout_error(what, self.seconds)


def timeout_error(what: str, seconds: float) -> ScopeTimeoutError:
    return ScopeTimeoutError(f"{what} exceeded the scope timeout of {seconds:g}s")


def git(cwd: Path, *args: str, deadline: Deadline) -> bytes:
    """``run_git`` with the time left; ``ScopeTimeoutError`` when it runs out, ``GitError`` for any other failure."""
    label = f"git {args[0]}" if args else "git"
    deadline.check(label)
    try:
        return run_git(cwd, *args, timeout=max(deadline.remaining(), 0.001))
    except GitError as exc:
        if isinstance(exc.__cause__, subprocess.TimeoutExpired):
            raise timeout_error(label, deadline.seconds) from exc
        raise


def git_lines(cwd: Path, *args: str, deadline: Deadline) -> list[str]:
    """The NUL-separated output of a ``-z`` Git command, decoded with ``surrogateescape``."""
    output = git(cwd, *args, deadline=deadline).decode("utf-8", errors="surrogateescape")
    return [item for item in output.split("\0") if item]
