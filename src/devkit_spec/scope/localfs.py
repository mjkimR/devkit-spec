"""The local file registry: one JSON record per task under ``<shared>/<namespace>/``, and the namespace's journal.

- ``<task-id>.json`` (the task ID mapped to a safe file name) holds one ``Record``; ``.lock`` serializes every
  operation of the namespace with ``flock`` (Linux and macOS; the OS releases it when the process dies);
  ``journal.jsonl`` is the append-only event journal.
- Each operation reads, compares and writes inside one lock hold. A record is published by writing a ``.tmp-*``
  file in the same directory and renaming it over the record, so a reader never sees a partial record; temp files
  an interrupted publish left behind are removed on the next lock acquisition.
- Network file systems are not supported: ``flock`` and rename atomicity are not guaranteed there.
"""

from __future__ import annotations

import contextlib
import json
import os
import socket
import tempfile
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from devkit.advisory import Level
from devkit.core import GitError

from devkit_spec.errors import (
    ScopeLockUnsupportedError,
    ScopeNamespaceError,
    ScopeRecordInvalidWarning,
    ScopeRecordMissingError,
    ScopeSharedPathError,
    ScopeStaleRevisionError,
    ScopeTaskExistsError,
    ScopeTokenMismatchError,
    ScopeUnsupportedError,
)
from devkit_spec.scope.deadline import Deadline, git, timeout_error
from devkit_spec.scope.model import (
    SCHEMA_VERSION,
    Event,
    Problem,
    Record,
    ScopePath,
    SweepResult,
    Verdict,
)
from devkit_spec.scope.model import now as utc_now
from devkit_spec.scope.registry import new_token, token_hash

LOCK_FILE = ".lock"
TMP_PREFIX = ".tmp-"
JOURNAL_FILE = "journal.jsonl"
RECORD_SUFFIX = ".json"
_POLL = 0.01  # seconds between lock attempts

Unlock = Callable[[], None]


class Locker(Protocol):
    def acquire(self, lock_file: Path, deadline: Deadline) -> Unlock:
        """Hold the lock on ``lock_file`` until the returned function is called; ``ScopeTimeoutError`` at the
        deadline."""
        ...


class FlockLocker:
    """An exclusive ``flock`` on the namespace lock file, polled until the deadline."""

    def acquire(self, lock_file: Path, deadline: Deadline) -> Unlock:
        try:
            import fcntl
        except ImportError as exc:  # pragma: no cover - not on Linux or macOS
            raise ScopeLockUnsupportedError("fcntl.flock is not available on this platform") from exc
        fd = os.open(lock_file, os.O_CREAT | os.O_RDWR, 0o644)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                remaining = deadline.remaining()
                if remaining <= 0:
                    os.close(fd)
                    raise timeout_error("waiting for the namespace lock", deadline.seconds) from None
                time.sleep(min(_POLL, remaining))
            except OSError:
                os.close(fd)
                raise

        def unlock() -> None:
            with contextlib.suppress(OSError):
                fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

        return unlock


def safe_name(identifier: str) -> str:
    """``identifier`` as a file name: characters other than letters, digits, ``-``, ``_`` and ``.`` become ``_``,
    and a leading ``.`` becomes ``_``, so an ID never names a hidden, temp, lock or parent file."""
    name = "".join(char if char.isascii() and (char.isalnum() or char in "-_.") else "_" for char in identifier)
    if not name:
        return "_"
    return f"_{name[1:]}" if name.startswith(".") else name


def valid_namespace(namespace: str) -> bool:
    return bool(namespace) and namespace == safe_name(namespace) and not namespace.startswith(".")


class _Unreadable(Exception):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _git_worktree_exists(path: str, deadline: Deadline) -> bool:
    if not path or not Path(path).is_dir():
        return False
    try:
        return git(Path(path), "rev-parse", "--is-inside-work-tree", deadline=deadline).strip() == b"true"
    except GitError:
        return False


class LocalRegistry:
    """The file-based ``Registry`` and ``Journaler`` on the shared directory ``shared``."""

    def __init__(
        self,
        shared: Path,
        *,
        locker: Locker | None = None,
        hostname: str | None = None,
        now: Callable[[], str] = utc_now,
        worktree_exists: Callable[[str, Deadline], bool] = _git_worktree_exists,
    ) -> None:
        self.shared = shared
        self.locker: Locker = locker or FlockLocker()
        self.hostname = hostname if hostname is not None else socket.gethostname()
        self.now = now
        self.worktree_exists = worktree_exists

    # --- plumbing -----------------------------------------------------------------------------------------------

    def namespace_dir(self, namespace: str) -> Path:
        return self.shared / namespace

    def record_path(self, namespace: str, task_id: str) -> Path:
        return self.namespace_dir(namespace) / f"{safe_name(task_id)}{RECORD_SUFFIX}"

    def journal_path(self, namespace: str) -> Path:
        return self.namespace_dir(namespace) / JOURNAL_FILE

    def _shared_error(self, exc: OSError, namespace: str) -> ScopeSharedPathError:
        return ScopeSharedPathError(
            f"the scope registry cannot be used: {exc}", target_files=[str(self.namespace_dir(namespace))]
        )

    @contextlib.contextmanager
    def _locked(self, namespace: str, deadline: Deadline) -> Iterator[Path]:
        if not valid_namespace(namespace):
            raise ScopeNamespaceError(f"invalid registry namespace {namespace!r}", target_files=[namespace])
        deadline.check("the registry operation")  # an expired deadline never starts one
        directory = self.namespace_dir(namespace)
        try:
            directory.mkdir(parents=True, exist_ok=True)
            unlock = self.locker.acquire(directory / LOCK_FILE, deadline)
        except OSError as exc:
            raise self._shared_error(exc, namespace) from exc
        try:
            self._clean_temp(directory)
            try:
                yield directory
            except OSError as exc:
                raise self._shared_error(exc, namespace) from exc
        finally:
            unlock()

    @staticmethod
    def _clean_temp(directory: Path) -> None:
        with contextlib.suppress(OSError):
            for entry in directory.iterdir():
                if entry.name.startswith(TMP_PREFIX):
                    with contextlib.suppress(OSError):
                        entry.unlink()

    @staticmethod
    def _read(path: Path) -> Record:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except PermissionError as exc:
            raise _Unreadable("permission", str(exc)) from exc
        except FileNotFoundError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _Unreadable("parse", f"{path.name}: {exc}") from exc
        try:
            return Record.from_dict(data)
        except (ValueError, KeyError, TypeError) as exc:
            raise _Unreadable("parse", f"{path.name}: {exc}") from exc

    def _read_own(self, path: Path) -> Record | None:
        """The record at ``path``; ``None`` when it does not exist; an error when it cannot be read."""
        try:
            return self._read(path)
        except FileNotFoundError:
            return None
        except _Unreadable as exc:
            raise ScopeRecordInvalidWarning(
                f"the record file cannot be read: {exc}", target_files=[str(path)]
            ).with_level(Level.ERROR) from exc

    @staticmethod
    def _write(path: Path, record: Record) -> None:
        data = json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n"
        fd, name = tempfile.mkstemp(prefix=TMP_PREFIX, dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(name, 0o644)
            os.replace(name, path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(name)
            raise

    def _record_files(self, directory: Path) -> list[Path]:
        try:
            entries = sorted(directory.iterdir())
        except FileNotFoundError:
            return []
        return [
            entry
            for entry in entries
            if entry.name.endswith(RECORD_SUFFIX) and not entry.name.startswith(TMP_PREFIX) and entry.is_file()
        ]

    def _read_all(self, directory: Path) -> tuple[list[Record], list[Problem]]:
        records: list[Record] = []
        problems: list[Problem] = []
        for path in self._record_files(directory):
            try:
                records.append(self._read(path))
            except FileNotFoundError:
                continue
            except _Unreadable as exc:
                problems.append(Problem(path.name, exc.reason))
        records.sort(key=lambda record: record.task_id)
        return records, problems

    # --- the Registry contract ----------------------------------------------------------------------------------

    def register(self, record: Record, deadline: Deadline) -> tuple[str, Record]:
        token = new_token()
        stamp = self.now()
        record = record.with_(
            schema_version=SCHEMA_VERSION,
            token_hash=token_hash(token),
            revision=1,
            updated_at=stamp,
            last_request_id="",
            hostname=record.hostname or self.hostname,
            scopes=tuple(path if path.first_seen else _seen(path, stamp) for path in record.scopes),
        )
        with self._locked(record.namespace, deadline) as directory:
            path = self.record_path(record.namespace, record.task_id)
            if path.exists():
                raise ScopeTaskExistsError(
                    f"the namespace already has a record for task {record.task_id}", target_files=[str(path)]
                )
            others, _ = self._read_all(directory)
            for other in others:
                if other.worktree and other.worktree == record.worktree and other.hostname == record.hostname:
                    record = record.with_(shared_worktree=True)
                    if not other.shared_worktree:
                        self._write(self.record_path(other.namespace, other.task_id), other.with_(shared_worktree=True))
            self._write(path, record)
        return token, record

    def query(self, namespace: str, deadline: Deadline) -> tuple[list[Record], list[Problem]]:
        with self._locked(namespace, deadline) as directory:
            return self._read_all(directory)

    def update(self, token: str, expected_revision: int, request_id: str, record: Record, deadline: Deadline) -> Record:
        with self._locked(record.namespace, deadline):
            path = self.record_path(record.namespace, record.task_id)
            existing = self._read_own(path)
            if existing is None:
                raise ScopeRecordMissingError(
                    f"no record for task {record.task_id} in the namespace", target_files=[str(path)]
                )
            if existing.token_hash != token_hash(token):
                raise ScopeTokenMismatchError(
                    f"the token does not own the record of task {record.task_id}", target_files=[str(path)]
                )
            if request_id and existing.last_request_id == request_id:
                return existing
            if existing.revision != expected_revision:
                raise ScopeStaleRevisionError(
                    f"the record of task {record.task_id} is at revision {existing.revision}, "
                    f"not the revision {expected_revision} that was read",
                    target_files=[str(path)],
                )
            stamp = self.now()
            first_seen = {path.key: path.first_seen for path in existing.scopes if path.first_seen}
            updated = record.with_(
                schema_version=SCHEMA_VERSION,
                token_hash=existing.token_hash,
                revision=existing.revision + 1,
                last_request_id=request_id,
                updated_at=stamp,
                hostname=record.hostname or existing.hostname,
                base_revision=record.base_revision or existing.base_revision,
                shared_worktree=existing.shared_worktree,
                scopes=tuple(
                    _seen(path, first_seen.get(path.key) or path.first_seen or stamp) for path in record.scopes
                ),
            )
            self._write(path, updated)
            return updated

    def release(self, namespace: str, task_id: str, token: str, deadline: Deadline) -> None:
        with self._locked(namespace, deadline):
            path = self.record_path(namespace, task_id)
            existing = self._read_own(path)
            if existing is None:
                return
            if existing.token_hash != token_hash(token):
                raise ScopeTokenMismatchError(
                    f"the token does not own the record of task {task_id}", target_files=[str(path)]
                )
            path.unlink()

    def sweep(self, namespace: str, apply: bool, expected: Mapping[str, int], deadline: Deadline) -> list[SweepResult]:
        results: list[SweepResult] = []
        with self._locked(namespace, deadline) as directory:
            for path in self._record_files(directory):
                try:
                    record = self._read(path)
                except FileNotFoundError:
                    continue
                except _Unreadable as exc:
                    results.append(
                        SweepResult(path.name.removesuffix(RECORD_SUFFIX), path.name, Verdict.ERROR, exc.reason)
                    )
                    continue
                result = SweepResult(
                    record.task_id, path.name, Verdict.ACTIVE, "", record.revision, record.spec, record.worktree
                )
                if record.hostname != self.hostname:
                    result = _verdict(result, Verdict.UNVERIFIABLE, "other-host")
                elif not self.worktree_exists(record.worktree, deadline):
                    result = _verdict(result, Verdict.STALE, "worktree-missing")
                    if apply:
                        want = expected.get(record.task_id)
                        if want is not None and want != record.revision:
                            result = _verdict(result, Verdict.ERROR, "stale-revision")
                        else:
                            try:
                                path.unlink()
                                result = _verdict(result, Verdict.REMOVED, "worktree-missing")
                            except OSError as exc:
                                result = _verdict(result, Verdict.ERROR, str(exc))
                results.append(result)
        return sorted(results, key=lambda result: result.task_id)

    def claim(self, token: str, record: Record, deadline: Deadline) -> Record:
        raise ScopeUnsupportedError("claim is reserved: the local file registry has no exclusive publish")

    # --- the Journaler contract ---------------------------------------------------------------------------------

    def append(self, namespace: str, events: list[Event], deadline: Deadline) -> None:
        if not events:
            return
        data = "".join(json.dumps(event.to_dict(), ensure_ascii=False) + "\n" for event in events).encode("utf-8")
        with self._locked(namespace, deadline):
            path = self.journal_path(namespace)
            with open(path, "a+b") as handle:
                size = handle.seek(0, os.SEEK_END)
                if size:
                    # an interrupted earlier append may have left a line without its newline: end it first
                    handle.seek(size - 1)
                    if handle.read(1) != b"\n":
                        data = b"\n" + data
                handle.write(data)

    def history(self, namespace: str, deadline: Deadline) -> tuple[list[Event], list[Problem]]:
        events: list[Event] = []
        problems: list[Problem] = []
        with self._locked(namespace, deadline):
            try:
                lines = self.journal_path(namespace).read_bytes().split(b"\n")
            except FileNotFoundError:
                return [], []
            for number, raw in enumerate(lines, 1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    events.append(Event.from_dict(json.loads(line)))
                except (ValueError, KeyError, TypeError):
                    problems.append(Problem(JOURNAL_FILE, "parse", number))
        events.sort(key=lambda event: event.at)
        return events, problems


def _seen(path: ScopePath, stamp: str) -> ScopePath:
    return replace(path, first_seen=stamp)


def _verdict(result: SweepResult, verdict: Verdict, reason: str) -> SweepResult:
    return replace(result, verdict=verdict, reason=reason)
