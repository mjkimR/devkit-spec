from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import threading
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from scope.contract import SCENARIOS
from scope.support import record, registry

from devkit_spec.errors import (
    ScopeLockUnsupportedError,
    ScopeNamespaceError,
    ScopeSharedPathError,
    ScopeStaleRevisionError,
    ScopeTimeoutError,
)
from devkit_spec.scope import (
    Deadline,
    Event,
    FlockLocker,
    Granularity,
    LocalRegistry,
    Registry,
    ScopePath,
    Source,
    Stage,
    Verdict,
)
from devkit_spec.scope.localfs import Unlock, is_temp


def _no_temp(directory: Path) -> None:
    assert [entry.name for entry in directory.iterdir() if is_temp(entry.name)] == []


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario.__name__)
def test_local_registry_contract(tmp_path: Path, scenario: Callable[[Registry], None]) -> None:
    scenario(registry(tmp_path / "shared"))


def test_records_are_json_files_with_safe_names(tmp_path: Path) -> None:
    fs = registry(tmp_path)
    for namespace in ("..", ".", ".hidden", "a/b", ""):
        with pytest.raises(ScopeNamespaceError):
            fs.register(record("a", "/wt", namespace=namespace), Deadline(5))
    fs.register(record(".tmp-x", "/wt"), Deadline(5))
    fs.register(record("../escape", "/wt"), Deadline(5))
    assert len(fs.query("ns", Deadline(5))[0]) == 2, "ids that look like temp or parent paths get safe names"
    assert sorted(entry.name for entry in (tmp_path / "ns").iterdir()) == [".lock", "_._escape.json", "_tmp-x.json"]
    assert not (tmp_path / "escape.json").exists()
    stored = json.loads((tmp_path / "ns/_tmp-x.json").read_text())
    assert stored["schema_version"] == 1 and stored["task_id"] == ".tmp-x" and "token" not in stored


def test_unreadable_records_are_problems_not_records(tmp_path: Path) -> None:
    fs = registry(tmp_path)
    fs.register(record("a", "/wt/a"), Deadline(5))
    (tmp_path / "ns/broken.json").write_text("{")
    (tmp_path / "ns/wrong.json").write_text('{"task_id": 3}')
    records, problems = fs.query("ns", Deadline(5))
    assert [item.task_id for item in records] == ["a"]
    assert [(problem.file, problem.reason) for problem in problems] == [
        ("broken.json", "parse"),
        ("wrong.json", "parse"),
    ]


def test_sweep_verdicts_and_revision_protection(tmp_path: Path) -> None:
    live = str(tmp_path / "live")
    fs = registry(tmp_path / "shared", worktree_exists=lambda path, _deadline: path == live)
    fs.register(record("alive", live), Deadline(5))
    _, gone = fs.register(record("gone", "/wt/gone"), Deadline(5))
    fs.register(record("remote", "/wt/remote", hostname="host-b"), Deadline(5))
    (tmp_path / "shared/ns/broken.json").write_text("{")

    verdicts = {item.task_id: (item.verdict, item.reason) for item in fs.sweep("ns", False, {}, Deadline(5))}
    assert verdicts == {
        "alive": (Verdict.ACTIVE, ""),
        "gone": (Verdict.STALE, "worktree-missing"),
        "remote": (Verdict.UNVERIFIABLE, "other-host"),
        "broken": (Verdict.ERROR, "parse"),
    }
    assert (tmp_path / "shared/ns/gone.json").exists(), "without apply nothing is removed"

    results = fs.sweep("ns", True, {"gone": gone.revision + 1}, Deadline(5))
    assert [(item.verdict, item.reason) for item in results if item.task_id == "gone"] == [
        (Verdict.ERROR, "stale-revision")
    ]
    assert (tmp_path / "shared/ns/gone.json").exists()
    results = fs.sweep("ns", True, {"gone": gone.revision}, Deadline(5))
    assert [item.verdict for item in results if item.task_id == "gone"] == [Verdict.REMOVED]
    assert not (tmp_path / "shared/ns/gone.json").exists()
    assert (tmp_path / "shared/ns/remote.json").exists(), "a record of another host is never removed"


class _Unsupported:
    def acquire(self, lock_file: Path, deadline: Deadline) -> Unlock:
        raise ScopeLockUnsupportedError("no flock here")


class _Blocking:
    def acquire(self, lock_file: Path, deadline: Deadline) -> Unlock:
        while not deadline.expired():
            time.sleep(0.005)
        raise ScopeTimeoutError("blocked")


def test_locker_errors_pass_through(tmp_path: Path) -> None:
    with pytest.raises(ScopeLockUnsupportedError):
        registry(tmp_path, locker=_Unsupported()).register(record("a", "/wt"), Deadline(5))
    with pytest.raises(ScopeTimeoutError):
        registry(tmp_path, locker=_Blocking()).query("ns", Deadline(0.05))


def test_flock_timeout_and_recovery(tmp_path: Path) -> None:
    fs = registry(tmp_path)
    token, stored = fs.register(record("a", "/wt/a"), Deadline(5))
    unlock = FlockLocker().acquire(tmp_path / "ns/.lock", Deadline(5))  # held by another holder
    started = time.monotonic()
    with pytest.raises(ScopeTimeoutError):
        fs.update(token, stored.revision, "r1", stored, Deadline(0.2))
    assert time.monotonic() - started < 2
    (tmp_path / "ns" / ".a.json.devkit-left-over.tmp").write_text("partial")  # an interrupted publish
    unlock()
    updated = fs.update(token, stored.revision, "r2", stored, Deadline(5))
    assert updated.revision == 2
    _no_temp(tmp_path / "ns")


def test_unsafe_lock_file_is_a_shared_path_error(tmp_path: Path) -> None:
    (tmp_path / "ns").mkdir()
    (tmp_path / "elsewhere").write_text("")
    (tmp_path / "ns/.lock").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ScopeSharedPathError):
        registry(tmp_path).query("ns", Deadline(5))


def test_threads_contend_on_the_lock(tmp_path: Path) -> None:
    fs = registry(tmp_path)
    token, stored = fs.register(record("a", "/wt/a"), Deadline(5))
    outcomes: list[str] = []

    def write(request: str) -> None:
        try:
            fs.update(token, stored.revision, request, stored, Deadline(5))
            outcomes.append("applied")
        except ScopeStaleRevisionError:
            outcomes.append("stale")

    threads = [threading.Thread(target=write, args=(f"r{index}",)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(outcomes) == ["applied", "stale"], "the same revision is applied once"
    assert fs.query("ns", Deadline(5))[0][0].revision == 2


_HELPER = textwrap.dedent(
    """
    import sys
    from devkit_spec.errors import ScopeStaleRevisionError
    from devkit_spec.scope import Deadline, Granularity, LocalRegistry, ScopePath, Source, Stage

    shared, task, token, rounds = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    fs = LocalRegistry(__import__("pathlib").Path(shared), hostname="host-a")
    for round in range(rounds):
        while True:
            own = next(item for item in fs.query("ns", Deadline(30))[0] if item.task_id == task)
            path = ScopePath(f"src/round{round}.py", Granularity.UNKNOWN, Source.OBSERVED, Stage.BUILD)
            try:
                fs.update(token, own.revision, f"{task}-{round}", own.with_(scopes=(*own.scopes, path)), Deadline(30))
                break
            except ScopeStaleRevisionError:
                continue
    """
)


def test_processes_update_concurrently_through_flock(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    fs = registry(shared)
    shared_path = ScopePath("src/shared.py", Granularity.FILE, Source.DECLARED_CODE, Stage.SPEC)
    tokens = {}
    for task in ("task-a", "task-b", "task-c", "task-d"):
        token, _ = fs.register(record(task, f"/wt/{task}").with_(scopes=(shared_path,)), Deadline(5))
        tokens[task] = token
    processes = [
        subprocess.Popen([sys.executable, "-c", _HELPER, str(shared), task, token, "5"], env=os.environ.copy())
        for task, token in tokens.items()
    ]
    assert [process.wait(timeout=120) for process in processes] == [0, 0, 0, 0]
    records, problems = fs.query("ns", Deadline(5))
    assert problems == [] and len(records) == 4
    for item in records:
        assert item.revision == 6, item.task_id
        assert [path.path for path in item.scopes][1:] == [f"src/round{index}.py" for index in range(5)]
        json.loads((shared / "ns" / f"{item.task_id}.json").read_text())
    _no_temp(shared / "ns")


@pytest.mark.skipif(os.geteuid() == 0, reason="permissions are not enforced for root")
def test_write_failure_leaves_the_record_intact(tmp_path: Path) -> None:
    fs = registry(tmp_path)
    token, stored = fs.register(record("a", "/wt/a"), Deadline(5))
    directory = tmp_path / "ns"
    before = (directory / "a.json").read_bytes()
    directory.chmod(0o500)  # no new file: the temp file cannot be created, so nothing is published
    try:
        observed = ScopePath("src/x.py", Granularity.UNKNOWN, Source.OBSERVED, Stage.BUILD)
        with pytest.raises(ScopeSharedPathError):
            fs.update(token, stored.revision, "r1", stored.with_(scopes=(observed,)), Deadline(5))
    finally:
        directory.chmod(0o755)
    assert (directory / "a.json").read_bytes() == before
    _no_temp(directory)
    assert fs.update(token, stored.revision, "r2", stored, Deadline(5)).revision == 2


def test_journal_appends_lines_and_reads_them_back_in_time_order(tmp_path: Path) -> None:
    fs = registry(tmp_path)
    fs.append(
        "ns", [Event("register", at="2026-10-08T00:00:02.000000Z", task="SPEC-a", slug="a", revision=1)], Deadline(5)
    )
    journal = tmp_path / "ns/journal.jsonl"
    with journal.open("ab") as handle:
        handle.write(b'{"event": "upd')  # an interrupted append: no newline
    fs.append("ns", [Event("release", at="2026-10-08T00:00:01.000000Z", task="SPEC-a")], Deadline(5))
    lines = journal.read_text().splitlines()
    assert len(lines) == 3 and lines[1] == '{"event": "upd'
    events, problems = fs.history("ns", Deadline(5))
    assert [event.event for event in events] == ["release", "register"]
    assert [(problem.file, problem.line, problem.reason) for problem in problems] == [("journal.jsonl", 2, "parse")]
    assert json.loads(lines[0]) == {
        "at": "2026-10-08T00:00:02.000000Z",
        "event": "register",
        "task": "SPEC-a",
        "slug": "a",
        "revision": 1,
    }
    assert registry(tmp_path).history("other", Deadline(5)) == ([], [])


def test_record_reads_skip_the_journal(tmp_path: Path) -> None:
    fs = LocalRegistry(tmp_path, hostname="host-a")
    fs.append("ns", [Event("guard", at="2026-10-08T00:00:00.000000Z")], Deadline(5))
    assert fs.query("ns", Deadline(5)) == ([], [])
