"""The registry adapter contract, owner tokens and request IDs.

Every adapter compares and writes atomically for one namespace and takes the caller's ``Deadline``. The local file
adapter (``localfs``) is the only implementation; ``claim`` (an exclusive publish) stays reserved and raises
``ScopeUnsupportedError``. Errors are the ``SPEC_SCOPE_*`` advisories of ``devkit_spec.errors``:

- ``register``: ``ScopeTaskExistsError`` when the namespace has the task ID;
- ``update``: ``ScopeRecordMissingError``, ``ScopeTokenMismatchError``, ``ScopeStaleRevisionError`` (the revision read
  is not the stored one); a ``request_id`` the record last applied is answered from the stored record unchanged;
- ``release``: a missing record is a no-op, a foreign token ``ScopeTokenMismatchError``; a record left alone in the
  worktree the released one shared loses its ``shared_worktree`` flag (not while an unreadable record may share it);
- ``record_file`` and ``may_hold`` relate the ``Problem`` of an unreadable record to a task ID or a token, so a caller
  refuses only for the unreadable records that may be the one it looks for;
- every operation: ``ScopeTimeoutError``, ``ScopeNamespaceError``, ``ScopeLockUnsupportedError``,
  ``ScopeSharedPathError``.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from collections.abc import Collection, Mapping
from typing import Protocol, runtime_checkable

from devkit_spec.scope.deadline import Deadline
from devkit_spec.scope.model import Event, Problem, Record, SweepResult


def new_token() -> str:
    """An opaque owner token (32 random bytes, URL-safe base64)."""
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    """What a record stores instead of the token: its SHA-256 in hex."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_request_id() -> str:
    """A random UUID for one update request."""
    return str(uuid.uuid4())


class Registry(Protocol):
    def register(self, record: Record, deadline: Deadline) -> tuple[str, Record]:
        """Create the record (revision 1) and return the only copy of its token with the stored record."""
        ...

    def query(self, namespace: str, deadline: Deadline) -> tuple[list[Record], list[Problem]]:
        """Every readable record of the namespace by task ID, and the files that could not be read."""
        ...

    def update(self, token: str, expected_revision: int, request_id: str, record: Record, deadline: Deadline) -> Record:
        """Replace the record when ``token`` owns it and its revision is ``expected_revision``."""
        ...

    def release(self, namespace: str, task_id: str, token: str, deadline: Deadline) -> None:
        """Delete the record when ``token`` owns it (a missing record is a no-op) and clear ``shared_worktree`` on a
        record left alone in its worktree."""
        ...

    def record_file(self, task_id: str) -> str:
        """The name a ``Problem`` gives the record of ``task_id`` when it cannot be read."""
        ...

    def may_hold(self, namespace: str, problem: Problem, token_digest: str) -> bool:
        """Whether the unreadable record of ``problem`` may be the record of the token hashed to ``token_digest``."""
        ...

    def sweep(
        self,
        namespace: str,
        apply: bool,
        expected: Mapping[str, int],
        deadline: Deadline,
        *,
        only: Collection[str] | None = None,
    ) -> list[SweepResult]:
        """Classify every record (only the tasks in ``only`` when given); with ``apply``, remove the stale ones whose
        revision ``expected`` still matches."""
        ...

    def claim(self, token: str, record: Record, deadline: Deadline) -> Record:
        """Reserved: publish the record exclusively."""
        ...


@runtime_checkable
class Journaler(Protocol):
    """Implemented by adapters that keep an append-only event journal per namespace."""

    def append(self, namespace: str, events: list[Event], deadline: Deadline) -> None: ...

    def history(self, namespace: str, deadline: Deadline) -> tuple[list[Event], list[Problem]]: ...
