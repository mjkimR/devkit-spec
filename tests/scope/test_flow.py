from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import pytest
from devkit.advisory import ActionMode, AdvisoryError, Level
from scope.support import SPEC, git, make_repo, write

from devkit_spec.config import ScopeConfig
from devkit_spec.errors import (
    ScopeNotAWorktreeError,
    ScopeRecordMissingError,
    ScopeSharedPathError,
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
    flow,
    locate,
    open_session,
    own,
    register,
    release,
    slug_from_spec,
    update,
)
from devkit_spec.scope import location as location_module
from devkit_spec.scope.location import SHARED_DIR, TOKEN_FILE, load_token, save_token


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
    assert (stored.task_id, stored.base_revision, stored.base_ref, stored.worktree) == (
        "SPEC-s",
        git(repo, "rev-parse", "HEAD"),
        "",  # the base checkout itself: the range starts at base_revision
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


def test_a_registration_that_loses_the_token_race_is_rolled_back(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session = open_session(repo)
    namespace = session.location.namespace
    winner, _ = session.registry.register(Record(namespace=namespace, task_id="first", worktree=str(repo)), Deadline(5))

    def raced(path: Path, token: str) -> None:  # the concurrent registration saves its token first
        save_token(path, winner)
        save_token(path, token)

    monkeypatch.setattr(flow, "save_token", raced)
    with pytest.raises(ScopeTokenExistsError) as raised:
        register(session, SPEC, "second")
    assert raised.value.details == ()
    records = session.registry.query(namespace, Deadline(5))[0]
    assert [(item.task_id, item.shared_worktree) for item in records] == [("first", False)], (
        "the losing record is removed and the winner no longer shares the worktree"
    )
    assert own(session).record.task_id == "first", "the winner keeps its token"


def test_token_files_are_complete_or_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    path = tmp_path / "git" / TOKEN_FILE
    path.parent.mkdir()
    stale, fresh, other = (path.parent / name for name in (f".{TOKEN_FILE}-ab_12cd3", f".{TOKEN_FILE}-zz99yy00", ".x"))
    for leftover in (stale, fresh, other):
        leftover.write_text("live-token\n")
    old = time.time() - 3600
    os.utime(stale, (old, old))
    os.utime(other, (old, old))
    assert load_token(path) is None
    assert not stale.exists() and fresh.exists() and other.exists(), "only old files of the temp pattern are removed"
    path.write_text("partial")
    assert load_token(path) is None, "a token without its newline is incomplete"
    path.unlink()

    def no_links(*args: object) -> None:
        raise OSError(1, "Operation not permitted")

    monkeypatch.setattr(location_module.os, "link", no_links)
    save_token(path, "one")
    assert load_token(path) == "one" and path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        save_token(path, "two")
    monkeypatch.undo()

    session = open_session(repo)
    session.location.token_path.write_text("")  # an interrupted save without hard links
    with pytest.raises(ScopeTokenExistsError):
        register(session, SPEC)
    assert release(session).registered is False and not session.location.token_path.exists()
    assert register(session, SPEC).record.task_id == "SPEC-s"


def test_save_token_is_exclusive(tmp_path: Path) -> None:
    path = tmp_path / "git" / TOKEN_FILE
    save_token(path, "one")
    with pytest.raises(FileExistsError):
        save_token(path, "two")
    assert path.read_text() == "one\n" and path.stat().st_mode & 0o777 == 0o600
    assert [entry.name for entry in path.parent.iterdir()] == [TOKEN_FILE], "no temporary file is left"


def test_a_failed_rollback_is_a_detail_of_the_original_error(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session = open_session(repo)

    def unwritable(path: Path, token: str) -> None:
        raise PermissionError("read-only git directory")

    monkeypatch.setattr(flow, "save_token", unwritable)
    with pytest.raises(ScopeSharedPathError) as raised:
        register(session, SPEC)
    assert raised.value.details == ()
    assert session.registry.query(session.location.namespace, Deadline(5))[0] == [], "the record is rolled back"

    def timed_out(*args: object) -> None:
        raise ScopeTimeoutError("waiting for the namespace lock exceeded the scope timeout of 5s")

    monkeypatch.setattr(session.registry, "release", timed_out)
    with pytest.raises(ScopeSharedPathError) as raised:
        register(session, SPEC)
    assert "read-only git directory" in raised.value.message, "the original error is kept"
    assert len(raised.value.details) == 1 and "SPEC-s could not be removed" in raised.value.details[0]
    assert "scope timeout" in raised.value.details[0]


def test_a_retried_request_is_answered_from_the_stored_record(repo: Path) -> None:
    session = open_session(repo)
    register(session, SPEC)
    write(repo, "src/new.py", "n = 1\n")
    write(repo, "src/other.py", "o = 1\n")
    applied = update(session, SPEC)
    assert (applied.status, applied.revision, applied.added, applied.removed) == (AckStatus.APPLIED, 2, 2, 0)
    (repo / SPEC).rename(repo / "specs/moved")  # collecting again would fail
    replay = update(session, SPEC, applied.request_id)
    assert replay.error is None
    assert (replay.status, replay.revision, replay.added, replay.removed) == (AckStatus.APPLIED, 2, 2, 0), (
        "a replay reports the counts its request recorded"
    )
    assert replay.record == applied.record
    assert update(session, SPEC).status == AckStatus.FAILED, "a new request collects again"


def test_observed_scope_forks_from_the_base_branch(repo: Path, tmp_path: Path) -> None:
    linked = tmp_path / "repo-wt-task"
    git(repo, "worktree", "add", "-q", "-b", "task", str(linked))
    session = open_session(linked)
    registered = register(session, SPEC)
    assert registered.record.base_ref == "refs/heads/main"
    write(linked, "src/a/a.py", "a = 2\n")
    git(linked, "commit", "-q", "-am", "task")
    write(repo, "src/b/b.py", "b = 2\n")  # upstream work on the base branch
    git(repo, "commit", "-q", "-am", "upstream")
    git(linked, "merge", "-q", "--no-edit", "main")

    ack = update(session, SPEC)
    observed = {path.path for path in ack.record.scopes if path.source is Source.OBSERVED} if ack.record else set()
    assert observed == {"src/a/a.py"}, "what the task merged in from its base branch is not observed"

    git(repo, "branch", "-m", "main", "trunk")
    ack = update(session, SPEC)
    assert ack.status == AckStatus.APPLIED and ack.record is not None
    assert ack.record.base_ref == "refs/heads/trunk", "a renamed base branch is detected again"
    assert not [item for item in ack.record.unresolved if item.reason == "missing-base-ref"]
    assert {path.path for path in ack.record.scopes if path.source is Source.OBSERVED} == {"src/a/a.py"}

    git(repo, "switch", "-q", "--detach")
    git(repo, "branch", "-D", "trunk")
    ack = update(session, SPEC)
    assert ack.status == AckStatus.APPLIED and ack.record is not None
    assert ("refs/heads/trunk", "missing-base-ref") in {(item.value, item.reason) for item in ack.record.unresolved}
    observed = {path.path for path in ack.record.scopes if path.source is Source.OBSERVED}
    assert {"src/a/a.py", "src/b/b.py"} <= observed, "an unresolvable base ref falls back to base_revision"

    git(repo, "switch", "-q", "-c", "next")
    ack = update(session, SPEC)
    assert ack.record is not None and ack.record.base_ref == "refs/heads/next", "the next detection replaces it"
    assert not [item for item in ack.record.unresolved if item.reason == "missing-base-ref"]


def _observed(session: Session) -> set[str]:
    ack = update(session, SPEC)
    assert ack.record is not None, ack.error
    return {path.path for path in ack.record.scopes if path.source is Source.OBSERVED}


def test_a_base_checkout_on_another_branch_adds_no_upstream_paths(repo: Path, tmp_path: Path) -> None:
    git(repo, "switch", "-q", "-c", "other")
    write(repo, "src/b/b.py", "b = 'other'\n")
    git(repo, "commit", "-q", "-am", "other")
    git(repo, "switch", "-q", "main")
    write(repo, "src/shared.py", "s = 'main'\n")  # main moves on after other forked
    git(repo, "commit", "-q", "-am", "main")
    git(repo, "switch", "-q", "other")  # the base checkout is on other when the task registers
    linked = tmp_path / "repo-wt-task"
    git(repo, "worktree", "add", "-q", "-b", "task", str(linked), "main")
    session = open_session(linked)
    assert register(session, SPEC).record.base_ref == "refs/heads/other"
    write(linked, "src/a/a.py", "a = 2\n")
    git(linked, "commit", "-q", "-am", "task")
    assert _observed(session) == {"src/a/a.py"}, "the range is never wider than base_revision..HEAD"


def test_a_worktree_forked_from_another_branch_adds_no_upstream_paths(repo: Path, tmp_path: Path) -> None:
    git(repo, "branch", "release")
    linked = tmp_path / "repo-wt-release"
    git(repo, "worktree", "add", "-q", "-b", "prep", str(linked), "release")
    write(linked, "src/b/b.py", "b = 'release'\n")
    git(linked, "commit", "-q", "-am", "release work")
    git(linked, "switch", "-q", "--detach")
    git(repo, "branch", "-f", "release", "prep")
    task = tmp_path / "repo-wt-task"
    git(repo, "worktree", "add", "-q", "-b", "task", str(task), "release")  # the base checkout stays on main
    session = open_session(task)
    assert register(session, SPEC).record.base_ref == "refs/heads/main"
    write(task, "src/a/a.py", "a = 2\n")
    git(task, "commit", "-q", "-am", "task")
    assert _observed(session) == {"src/a/a.py"}, "release's own commits are not the task's"


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


def test_an_unreadable_own_record_keeps_the_token(repo: Path) -> None:
    session = open_session(repo)
    register(session, SPEC)
    path = session.location.shared_path / session.location.namespace / "SPEC-s.json"
    path.write_text(path.read_text() + "trailing garbage")  # still names the token hash
    for call in (lambda: release(session), lambda: release(session, "SPEC-s"), lambda: own(session)):
        with pytest.raises(AdvisoryError) as raised:
            call()
        error = raised.value
        assert (error.code, error.level, error.mode) == (
            "SPEC_SCOPE_RECORD_INVALID",
            Level.ERROR,
            ActionMode.INTERACTION,
        )
        assert error.target_files == (str(path),) and error.details == ("SPEC-s.json: parse",)
        assert "token is kept" in error.message
    assert session.location.token_path.exists(), "the token of a record that cannot be read is kept"
    ack = update(session, SPEC)
    assert ack.status == AckStatus.FAILED and ack.error is not None and ack.error.code == "SPEC_SCOPE_RECORD_INVALID"


def test_unrelated_unreadable_records_do_not_block_release(repo: Path) -> None:
    session = open_session(repo)
    register(session, SPEC)
    directory = session.location.shared_path / session.location.namespace
    (directory / "SPEC-other.json").write_text("{not json")  # another task's corrupt record
    assert release(session, "SPEC-gone").already and session.location.token_path.exists()
    with pytest.raises(AdvisoryError) as raised:
        release(session, "SPEC-other")  # that task's own record file is the unreadable one
    assert raised.value.target_files == (str(directory / "SPEC-other.json"),)
    released = release(session, "SPEC-s")
    assert (released.task, released.already) == ("SPEC-s", False) and not session.location.token_path.exists()

    register(session, SPEC)
    (directory / "SPEC-s.json").unlink()  # the record is gone: the token is orphaned
    with pytest.raises(ScopeRecordMissingError):
        own(session)
    assert isinstance(update(session, SPEC).error, ScopeRecordMissingError)
    released = release(session)
    assert released.already and not session.location.token_path.exists(), "the orphaned token is removed"


def test_journal_failure_is_one_warning(repo: Path) -> None:
    session = open_session(repo)
    (session.location.shared_path / session.location.namespace / "journal.jsonl").mkdir(parents=True)
    registered = register(session, SPEC)
    assert [notice.code for notice in registered.notices] == ["SPEC_SCOPE_JOURNAL_UNAVAILABLE"]
    ack = update(session, SPEC)
    assert ack.status == AckStatus.APPLIED and [notice.code for notice in ack.notices] == [
        "SPEC_SCOPE_JOURNAL_UNAVAILABLE"
    ]


def test_auto_register_only_in_a_linked_worktree_at_either_level(repo: Path, tmp_path: Path) -> None:
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

    for level in ("required", "auto"):
        write(linked, ".devkit/config.toml", f'[tool.spec]\nworktree = "{level}"\n')
        release(session)
        registered, notices = auto_register(linked, SPEC, source="handoff")
        assert registered is not None and notices == [], level
    plain = tmp_path / "plain"
    write(plain, ".devkit/config.toml", "")
    assert auto_register(plain, "specs/x", source="handoff") == (None, [])


def test_slug_from_spec() -> None:
    assert slug_from_spec("specs/2026-10/20261008-scope-journal") == "scope-journal"
    assert slug_from_spec("specs/2026-10/20261008-x/") == "x"
    assert slug_from_spec("specs/other") == ""
