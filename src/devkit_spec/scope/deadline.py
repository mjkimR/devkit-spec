"""The deadline every registry operation runs under, and Git calls bounded by it.

A command gets one ``Deadline`` (``[tool.spec.scope] timeout``): devkit's ``Deadline`` whose expiry raises
``ScopeTimeoutError``. The lock wait (``devkit.core.file_lock``) and each Git subprocess (``devkit.core.run_git``)
take the time that is left; a Git subprocess that outlives its share is killed, so a timed-out command ends within a
moment of its deadline.
"""

from __future__ import annotations

from pathlib import Path

from devkit import core
from devkit.core import run_git

from devkit_spec.errors import ScopeTimeoutError

JOURNAL_SECONDS = 5.0  # one journal append, independent of the operation's own deadline
ROLLBACK_SECONDS = 5.0  # removing a record whose token could not be saved, independent of the command's deadline


def timeout_error(what: str, seconds: float) -> ScopeTimeoutError:
    return ScopeTimeoutError(f"{what} exceeded the scope timeout of {seconds:g}s")


class Deadline(core.Deadline):
    """devkit's ``Deadline`` that raises ``ScopeTimeoutError`` (``SPEC_SCOPE_TIMEOUT``) when it runs out."""

    def __init__(self, seconds: float) -> None:
        super().__init__(seconds, error=timeout_error)


def git_lines(cwd: Path, *args: str, deadline: Deadline) -> list[str]:
    """The NUL-separated output of a ``-z`` Git command under ``deadline``, decoded with ``surrogateescape``."""
    output = run_git(cwd, *args, deadline=deadline).decode("utf-8", errors="surrogateescape")
    return [item for item in output.split("\0") if item]
