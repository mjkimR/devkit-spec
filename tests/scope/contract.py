"""The registry adapter contract, runnable against any ``Registry`` (specrig's ``contracttest``).

Each scenario takes a fresh, empty registry whose ``hostname`` is ``host-a``.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from scope.support import record

from devkit_spec.errors import (
    ScopeRecordMissingError,
    ScopeStaleRevisionError,
    ScopeTaskExistsError,
    ScopeTimeoutError,
    ScopeTokenMismatchError,
    ScopeUnsupportedError,
)
from devkit_spec.scope import Deadline, Granularity, Registry, ScopePath, Source, Stage, token_hash


def _deadline() -> Deadline:
    return Deadline(10)


def register_query(registry: Registry) -> None:
    token, stored = registry.register(record("a", "/wt/a"), _deadline())
    assert token and stored.revision == 1
    assert stored.token_hash == token_hash(token), "records store the hash, never the token"
    assert stored.scopes[0].first_seen
    with pytest.raises(ScopeTaskExistsError):
        registry.register(record("a", "/wt/a2"), _deadline())
    registry.register(record("b", "/wt/b"), _deadline())
    records, problems = registry.query("ns", _deadline())
    assert problems == [] and [item.task_id for item in records] == ["a", "b"]
    assert registry.query("other", _deadline()) == ([], [])


def update_revision_token(registry: Registry) -> None:
    token, stored = registry.register(record("a", "/wt/a"), _deadline())
    token_b, _ = registry.register(record("b", "/wt/b"), _deadline())
    first = stored.scopes[0].first_seen
    added = ScopePath("src/new.py", Granularity.UNKNOWN, Source.OBSERVED, Stage.BUILD)
    proposed = stored.with_(scopes=(*stored.scopes, added))
    updated = registry.update(token, stored.revision, "req-1", proposed, _deadline())
    assert updated.revision == stored.revision + 1
    assert updated.scopes[0].first_seen == first, "first_seen survives an update"
    assert updated.scopes[1].first_seen
    assert updated.token_hash == stored.token_hash
    with pytest.raises(ScopeStaleRevisionError):
        registry.update(token, stored.revision, "req-2", proposed, _deadline())
    with pytest.raises(ScopeTokenMismatchError):
        registry.update(token_b, updated.revision, "req-3", proposed, _deadline())
    with pytest.raises(ScopeRecordMissingError):
        registry.update(token, updated.revision, "req-4", record("missing", "/wt/m"), _deadline())
    records, _ = registry.query("ns", _deadline())
    assert {item.task_id: item.revision for item in records}["a"] == updated.revision, "rejections write nothing"


def idempotent_request(registry: Registry) -> None:
    token, stored = registry.register(record("a", "/wt/a"), _deadline())
    applied = registry.update(token, stored.revision, "same", stored, _deadline())
    again = registry.update(token, 42, "same", stored, _deadline())
    assert again.revision == applied.revision, "a replayed request id is answered without a write"
    assert again.last_request_id == "same"


def release(registry: Registry) -> None:
    token, _ = registry.register(record("a", "/wt/a"), _deadline())
    token_b, _ = registry.register(record("b", "/wt/b"), _deadline())
    with pytest.raises(ScopeTokenMismatchError):
        registry.release("ns", "a", token_b, _deadline())
    assert len(registry.query("ns", _deadline())[0]) == 2, "a foreign token releases nothing"
    registry.release("ns", "a", token, _deadline())
    registry.release("ns", "a", token, _deadline())  # repeating a release is a no-op
    assert [item.task_id for item in registry.query("ns", _deadline())[0]] == ["b"]


def shared_worktree(registry: Registry) -> None:
    _, first = registry.register(record("a", "/wt/same"), _deadline())
    assert not first.shared_worktree
    _, second = registry.register(record("b", "/wt/same"), _deadline())
    assert second.shared_worktree
    assert all(item.shared_worktree for item in registry.query("ns", _deadline())[0])


def claim_reserved(registry: Registry) -> None:
    token, stored = registry.register(record("a", "/wt/a"), _deadline())
    with pytest.raises(ScopeUnsupportedError):
        registry.claim(token, stored, _deadline())


def deadline(registry: Registry) -> None:
    expired = Deadline(0)
    with pytest.raises(ScopeTimeoutError):
        registry.query("ns", expired)
    with pytest.raises(ScopeTimeoutError):
        registry.register(record("a", "/wt/a"), expired)
    registry.register(record("a", "/wt/a"), _deadline())  # the registry is usable after a timed-out call


SCENARIOS: list[Callable[[Registry], None]] = [
    register_query,
    update_revision_token,
    idempotent_request,
    release,
    shared_worktree,
    claim_reserved,
    deadline,
]
