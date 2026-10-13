from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest
from scope.support import SPEC, git, make_repo, write

from devkit_spec.config import ScopeConfig
from devkit_spec.errors import (
    ScopeNotAWorktreeError,
    ScopeRecordMissingError,
    ScopeStaleRevisionError,
    ScopeTimeoutError,
    ScopeTokenExistsError,
    ScopeTokenMismatchError,
    ScopeTokenMissingError,
)
from devkit_spec.scope import (
    AckStatus,
    Deadline,
    FlockLocker,
    Granularity,
    Record,
    ScopePath,
    Session,
    Source,
    Stage,
    auto_register,
    default_namespace,
    locate,
    open_session,
    own,
    register,
    release,
    slug_from_spec,
    update,
)
from devkit_spec.scope.location import SHARED_DIR, TOKEN_FILE


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "repo")


def _events(session: Session) -> list[dict[str, object]]:
    path = session.location.shared_path / session.location.namespace / "journal.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_locate_defaults_and_configuration(repo: Path, tmp_path: Path) -> None:
    location = locate(repo, ScopeConfig(), Deadline(10))
    assert location.shared_path == repo / ".git" / SHARED_DIR
    assert location.namespace == default_namespace(repo / ".git") and len(location.namespace) == 16
    assert location.token_path == repo / ".git" / TOKEN_FILE and not location.linked
    custom = locate(repo, ScopeConfig(shared_path=tmp_path / "shared", namespace="team"), Deadline(10))
    assert (custom.shared_path, custom.namespace) == (tmp_path / "shared", "team")
    linked = tmp_path / "repo-wt-x"
    git(repo, "worktree", "add", "-q", "-b", "x", str(linked))
    other = locate(linked, ScopeConfig(), Deadline(10))
    assert other.linked and (other.shared_path, other.namespace) == (location.shared_path, location.namespace)
    assert other.token_path.parent == repo / ".git/worktrees/repo-wt-x"
    outside = tmp_path / "plain"
    outside.mkdir()
    with pytest.raises(ScopeNotAWorktreeError):
        locate(outside, ScopeConfig(), Deadline(10))


def test_register_update_release_flow(repo: Path) -> None:
    session = open_session(repo)
    ack = update(session, SPEC)
    assert ack.status == AckStatus.FAILED and isinstance(ack.error, ScopeTokenMissingError)

    registered = register(session, SPEC)
    stored = registered.record
    assert (stored.task_id, stored.base_revision, stored.worktree) == (
        "SPEC-s",
        git(repo, "rev-parse", "HEAD"),
        str(repo),
    )
    assert session.location.token_path.read_text().strip() == registered.token
    assert session.location.token_path.stat().st_mode & 0o777 == 0o600
    assert (
        registered.token not in (session.location.shared_path / session.location.namespace / "SPEC-s.json").read_text()
    )

    other = Record(
        namespace=session.location.namespace,
        task_id="SPEC-other",
        worktree="/wt/other",
        scopes=(ScopePath("src/a/a.py", Granularity.FILE, Source.DECLARED_CODE, Stage.SPEC),),
    )
    session.registry.register(other, Deadline(5))
    write(repo, "src/new.py", "n = 1\n")
    ack = update(session, SPEC)
    assert (ack.status, ack.revision, ack.added, ack.removed, ack.overlaps) == (AckStatus.APPLIED, 2, 1, 0, 1)
    assert ack.request_id and ack.error is None
    assert (ack.pairs[0].code[0].path, ack.pairs[0].code[0].other) == ("src/a", "src/a/a.py")
    again = update(session, SPEC)
    assert (again.status, again.added, again.revision) == (AckStatus.APPLIED, 0, 3)
    replay = update(session, SPEC, again.request_id)
    assert (replay.status, replay.revision) == (AckStatus.APPLIED, 3), "an applied request id is not written twice"

    released = release(session)
    assert (released.task, released.revision, released.already) == ("SPEC-s", 3, False)
    assert not session.location.token_path.exists()
    assert release(session).registered is False, "releasing again changes nothing"
    events = _events(session)
    assert [event["event"] for event in events] == ["update", "register", "update", "update", "update", "release"]
    first_update = events[0]
    assert first_update["status"] == "failed" and "task" not in first_update
    applied = events[2]
    assert (applied["task"], applied["slug"], applied["added"], applied["overlaps"]) == ("SPEC-s", "s", 1, 1)


def test_second_registration_in_a_worktree_is_refused(repo: Path) -> None:
    session = open_session(repo)
    register(session, SPEC, "first")
    with pytest.raises(ScopeTokenExistsError):
        register(session, SPEC, "second")
    assert [item.task_id for item in session.registry.query(session.location.namespace, Deadline(5))[0]] == ["first"]


def test_update_statuses_for_stale_timeout_and_orphaned_records(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session = open_session(repo)
    register(session, SPEC)
    original = session.registry.update

    def moved_on(token: str, expected: int, request: str, record: Record, deadline: Deadline) -> Record:
        original(token, expected, "someone-else", record, deadline)
        return original(token, expected, request, record, deadline)

    monkeypatch.setattr(session.registry, "update", moved_on)
    ack = update(session, SPEC)
    assert ack.status == AckStatus.STALE and isinstance(ack.error, ScopeStaleRevisionError)
    monkeypatch.undo()

    unlock = FlockLocker().acquire(session.location.shared_path / session.location.namespace / ".lock", Deadline(5))
    timer = threading.Timer(0.5, unlock)  # the holder lets go before the journal append gives up
    timer.start()
    ack = update(Session(session.location, session.registry, Deadline(0.2)), SPEC)
    timer.join()
    assert ack.status == AckStatus.TIMEOUT and isinstance(ack.error, ScopeTimeoutError)
    assert ack.notices == [], "the journal append runs under its own deadline"

    assert [event["status"] for event in _events(session) if event["event"] == "update"] == ["stale", "timeout"]
    (session.location.shared_path / session.location.namespace / "SPEC-s.json").unlink()
    ack = update(session, SPEC)
    assert isinstance(ack.error, ScopeRecordMissingError)
    with pytest.raises(ScopeRecordMissingError):
        own(session)
    released = release(session)
    assert released.already and not session.location.token_path.exists(), "an orphaned token is removed"


def test_release_of_a_named_task(repo: Path) -> None:
    session = open_session(repo)
    with pytest.raises(ScopeTokenMissingError):
        release(session, "SPEC-s")
    register(session, SPEC)
    session.registry.register(
        Record(namespace=session.location.namespace, task_id="SPEC-x", worktree="/wt/x"), Deadline(5)
    )
    with pytest.raises(ScopeTokenMismatchError):
        release(session, "SPEC-x")
    assert release(session, "SPEC-nope").already and session.location.token_path.exists()
    assert release(session, "SPEC-s").task == "SPEC-s"


def test_journal_failure_is_one_warning(repo: Path) -> None:
    session = open_session(repo)
    (session.location.shared_path / session.location.namespace / "journal.jsonl").mkdir(parents=True)
    registered = register(session, SPEC)
    assert [notice.code for notice in registered.notices] == ["SPEC_SCOPE_JOURNAL_UNAVAILABLE"]
    ack = update(session, SPEC)
    assert ack.status == AckStatus.APPLIED and [notice.code for notice in ack.notices] == [
        "SPEC_SCOPE_JOURNAL_UNAVAILABLE"
    ]


def test_auto_register_only_in_a_linked_worktree_with_the_worktree_policy(repo: Path, tmp_path: Path) -> None:
    assert auto_register(repo, SPEC, source="handoff") == (None, []), "the base checkout never registers"
    linked = tmp_path / "repo-wt-s"
    git(repo, "worktree", "add", "-q", "-b", "s", str(linked))
    registered, notices = auto_register(linked, SPEC, source="handoff")
    assert registered is not None and notices == []
    assert registered.record.worktree == str(linked)
    session = open_session(linked)
    assert _events(session)[-1]["source"] == "handoff"
    again, notices = auto_register(linked, SPEC, source="handoff")
    assert again is None and [notice.code for notice in notices] == ["SPEC_SCOPE_REGISTER_FAILED"]
    assert "SPEC_SCOPE_TOKEN_EXISTS" in notices[0].details[0]

    write(linked, ".devkit/config.toml", "[tool.spec]\nworktree = false\n")
    release(session)
    assert auto_register(linked, SPEC, source="handoff") == (None, [])
    plain = tmp_path / "plain"
    write(plain, ".devkit/config.toml", "")
    assert auto_register(plain, "specs/x", source="handoff") == (None, [])


def test_slug_from_spec() -> None:
    assert slug_from_spec("specs/2026-10/20261008-scope-journal") == "scope-journal"
    assert slug_from_spec("specs/2026-10/20261008-x/") == "x"
    assert slug_from_spec("specs/other") == ""
