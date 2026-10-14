"""The registry operations a worktree performs on its own task: register, update (the ACK), release, and journaling.

A worktree runs one task: everything Git observes there is attributed to it. Libraries never print: each function
returns its result with the warnings to report (``notices``); journal failures are warnings only and never change
an operation's outcome.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from devkit.advisory import AdvisoryError, Level

from devkit_spec.config import read_spec_config
from devkit_spec.errors import (
    ScopeAckFailedError,
    ScopeJournalWarning,
    ScopeNotAWorktreeError,
    ScopeRecordInvalidWarning,
    ScopeRecordMissingError,
    ScopeRegisterFailedWarning,
    ScopeSharedPathError,
    ScopeSharedWorktreeWarning,
    ScopeStaleRevisionError,
    ScopeTimeoutError,
    ScopeTokenExistsError,
    ScopeTokenMissingError,
)
from devkit_spec.scope.compare import compare_with
from devkit_spec.scope.deadline import JOURNAL_SECONDS, Deadline
from devkit_spec.scope.inputs import from_spec, observe_git
from devkit_spec.scope.localfs import LocalRegistry
from devkit_spec.scope.location import Location, head_revision, load_token, locate, remove_token, save_token
from devkit_spec.scope.model import (
    AckCounts,
    Event,
    EventKind,
    PairResult,
    Problem,
    Record,
    ScopePath,
    ScopeSet,
    SweepResult,
    Verdict,
)
from devkit_spec.scope.model import now as utc_now
from devkit_spec.scope.registry import Journaler, Registry, new_request_id, token_hash

SOURCE_HANDOFF = "handoff"
_SPEC_DIR = re.compile(r"^\d{8}-(.+)$")


@dataclass(frozen=True)
class Session:
    """An open registry: the location of this workspace, the adapter and the command's deadline."""

    location: Location
    registry: LocalRegistry
    deadline: Deadline


def open_session(root: Path) -> Session:
    """Read ``[tool.spec.scope]``, locate the registry for the workspace at ``root`` and start the deadline."""
    config = read_spec_config(root).scope
    deadline = Deadline(config.timeout)
    location = locate(root, config, deadline)
    return Session(location, LocalRegistry(location.shared_path), deadline)


# --- journal ------------------------------------------------------------------------------------------------------


def slug_from_spec(spec: str) -> str:
    """The slug of a spec directory named ``YYYYMMDD-<slug>``; ``""`` for any other name."""
    match = _SPEC_DIR.match(posixpath.basename(spec.rstrip("/")))
    return match.group(1) if match else ""


def record_event(kind: EventKind, record: Record, source: str = "") -> Event:
    return Event(
        event=str(kind),
        task=record.task_id,
        slug=slug_from_spec(record.spec),
        revision=record.revision,
        worktree=record.worktree,
        spec=record.spec,
        source=source,
    )


def sweep_events(results: Sequence[SweepResult], source: str = "") -> list[Event]:
    """One ``sweep`` event per verdict other than ``active``."""
    return [
        Event(
            event=str(EventKind.SWEEP),
            task=result.task_id,
            slug=slug_from_spec(result.spec),
            revision=result.revision,
            verdict=str(result.verdict),
            reason=result.reason,
            worktree=result.worktree,
            spec=result.spec,
            source=source,
        )
        for result in results
        if result.verdict is not Verdict.ACTIVE
    ]


def journal(registry: Registry, namespace: str, events: Sequence[Event]) -> list[AdvisoryError]:
    """Append ``events`` when the adapter keeps a journal, under its own deadline; a failure is one warning."""
    if not events or not isinstance(registry, Journaler):
        return []
    stamp = utc_now()
    stamped = [event if event.at else _at(event, stamp) for event in events]
    try:
        registry.append(namespace, stamped, Deadline(JOURNAL_SECONDS))
    except (AdvisoryError, OSError) as exc:
        target = str(registry.journal_path(namespace)) if isinstance(registry, LocalRegistry) else namespace
        message = exc.message if isinstance(exc, AdvisoryError) else str(exc)
        return [ScopeJournalWarning(f"the event journal could not be written: {message}", target_files=[target])]
    return []


def _at(event: Event, stamp: str) -> Event:
    return replace(event, at=stamp)


# --- register -----------------------------------------------------------------------------------------------------


@dataclass
class Registered:
    location: Location
    record: Record
    token: str
    notices: list[AdvisoryError] = field(default_factory=list)


def collect(location: Location, spec_dir: str, base_revision: str, deadline: Deadline, stamp: str) -> ScopeSet:
    """The declared scope of the bundle plus what Git observes in the worktree since ``base_revision``."""
    scope = from_spec(location.root, spec_dir)
    observed, unresolved = observe_git(location.root, base_revision, deadline, stamp)
    scope.observed = observed
    scope.unresolved += unresolved
    return scope


def register(session: Session, spec_dir: str, task_id: str | None = None, *, source: str = "") -> Registered:
    """Register the bundle at the workspace-relative ``spec_dir`` as this worktree's task and save its token.

    ``task_id`` defaults to the spec ID. Raises ``ScopeTokenExistsError`` when this worktree already holds a token.
    """
    location, registry, deadline = session.location, session.registry, session.deadline
    if location.token_path.exists():
        raise ScopeTokenExistsError("this worktree already registered a task", target_files=[str(location.token_path)])
    stamp = utc_now()
    base = head_revision(location.root, deadline)
    scope = collect(location, spec_dir, base, deadline, stamp)
    record = Record(
        namespace=location.namespace,
        task_id=task_id or scope.id,
        worktree=str(location.root),
        base_revision=base,
        spec=spec_dir,
        scopes=tuple(scope.all_paths()),
        unresolved=tuple(scope.unresolved),
    )
    token, stored = registry.register(record, deadline)
    try:
        save_token(location.token_path, token)
    except OSError as exc:
        registry.release(stored.namespace, stored.task_id, token, deadline)  # never leave a record nobody can release
        raise ScopeSharedPathError(
            f"the token could not be saved: {exc}", target_files=[str(location.token_path)]
        ) from exc
    notices: list[AdvisoryError] = []
    if stored.shared_worktree:
        notices.append(
            ScopeSharedWorktreeWarning(
                f"another task registered this worktree too; changes observed in {stored.worktree} count for both",
                target_files=[stored.worktree],
            )
        )
    notices += journal(registry, location.namespace, [record_event(EventKind.REGISTER, stored, source)])
    return Registered(location, stored, token, notices)


def auto_register(root: Path, spec_dir: str, *, source: str) -> tuple[Registered | None, list[AdvisoryError]]:
    """Register ``spec_dir`` when the project runs formal work in worktrees and ``root`` is a linked worktree.

    Outside Git, in the base checkout or with ``[tool.spec] worktree = false`` nothing happens. A failure is a
    ``SPEC_SCOPE_REGISTER_FAILED`` warning: the caller's own operation has already succeeded.
    """
    try:
        if not read_spec_config(root).worktree:
            return None, []
        session = open_session(root)
        if not session.location.linked:
            return None, []
        registered = register(session, spec_dir, source=source)
    except ScopeNotAWorktreeError:
        return None, []
    except AdvisoryError as exc:
        warning = ScopeRegisterFailedWarning(
            f"the scope of {spec_dir} was not registered: {exc.message}",
            f"{exc.code}: {exc.fix or exc.message}",
            fix=f"Fix the cause in [DETAIL], then run devkit spec scope register --spec {spec_dir} in this worktree",
        )
        return None, [warning]
    return registered, registered.notices


# --- own record ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Own:
    token: str
    record: Record
    others: list[Record]
    problems: list[Problem]


def own(session: Session) -> Own:
    """This worktree's record (found by its token) and the other records of the namespace.

    Raises ``ScopeTokenMissingError`` without a token, ``ScopeRecordMissingError`` when its record is gone and
    ``SPEC_SCOPE_RECORD_INVALID`` at ``ERROR`` when it is not found while some record files cannot be read.
    """
    location = session.location
    token = load_token(location.token_path)
    if token is None:
        raise ScopeTokenMissingError(
            "this worktree holds no scope registry token", target_files=[str(location.token_path)]
        )
    records, problems = session.registry.query(location.namespace, session.deadline)
    digest = token_hash(token)
    mine = [record for record in records if record.token_hash == digest]
    if not mine:
        if problems:
            raise _unreadable(location, problems)
        raise ScopeRecordMissingError(
            "the record of this worktree's token no longer exists (released or swept)",
            target_files=[str(location.token_path)],
        )
    others = [record for record in records if record.token_hash != digest]
    return Own(token, mine[0], others, problems)


def _unreadable(location: Location, problems: Sequence[Problem]) -> AdvisoryError:
    """This worktree's record is not among the readable ones, and unreadable files may hold it."""
    directory = location.shared_path / location.namespace
    return ScopeRecordInvalidWarning(
        "this worktree's record is not readable: it may be one of the record files that cannot be read",
        *(f"{problem.file}: {problem.reason}" for problem in problems),
        target_files=[str(directory / problem.file) for problem in problems],
    ).with_level(Level.ERROR)


# --- update -------------------------------------------------------------------------------------------------------


class AckStatus:
    APPLIED = "applied"
    FAILED = "failed"
    STALE = "stale"
    TIMEOUT = "timeout"


@dataclass
class Ack:
    """The outcome of one update; ``error`` is set unless ``status`` is ``applied``."""

    status: str
    request_id: str
    revision: int = 0
    added: int = 0
    removed: int = 0
    overlaps: int = 0
    unresolved: int = 0
    record: Record | None = None
    pairs: list[PairResult] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)
    error: AdvisoryError | None = None
    notices: list[AdvisoryError] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "revision": self.revision,
            "added": self.added,
            "removed": self.removed,
            "overlaps": self.overlaps,
            "unresolved": self.unresolved,
            "request_id": self.request_id,
            "record": self.record.public_dict() if self.record else None,
        }


def _diff_scopes(before: Sequence[ScopePath], after: Sequence[ScopePath]) -> tuple[int, int]:
    was = {path.key for path in before}
    now = {path.key for path in after}
    return len(now - was), len(was - now)


def update(session: Session, spec_dir: str, request_id: str | None = None, *, source: str = "") -> Ack:
    """Recollect the bundle's declared and observed scope, write it with this worktree's token and the revision just
    read, and compare it with the namespace's other records.

    ``request_id`` retries an update whose outcome was not observed: an ID the record already applied is answered
    from the stored record without a second write. Never raises for a registry failure: the ACK carries it.
    """
    location, registry, deadline = session.location, session.registry, session.deadline
    ack = Ack(status=AckStatus.APPLIED, request_id=request_id or new_request_id())
    current: Record | None = None
    try:
        mine = own(session)
        current = mine.record
        ack.problems = mine.problems
        stamp = utc_now()
        scope = collect(location, spec_dir, current.base_revision, deadline, stamp)
        proposed = current.with_(spec=spec_dir, scopes=tuple(scope.all_paths()), unresolved=tuple(scope.unresolved))
        ack.added, ack.removed = _diff_scopes(current.scopes, proposed.scopes)
        stored = registry.update(mine.token, current.revision, ack.request_id, proposed, deadline)
    except AdvisoryError as exc:
        ack.error = exc
        if isinstance(exc, ScopeStaleRevisionError):
            ack.status = AckStatus.STALE
        elif isinstance(exc, ScopeTimeoutError):
            ack.status = AckStatus.TIMEOUT
        else:
            ack.status = AckStatus.FAILED
    except OSError as exc:
        ack.error = ScopeAckFailedError(f"the scope update failed: {exc}")
        ack.status = AckStatus.FAILED
    else:
        ack.revision = stored.revision
        ack.record = stored
        ack.unresolved = len(stored.unresolved)
        ack.pairs = compare_with(stored.to_set(), [other.to_set() for other in mine.others])
        ack.overlaps = sum(pair.overlapping for pair in ack.pairs)
    event = Event(
        event=str(EventKind.UPDATE),
        task=current.task_id if current else "",
        slug=slug_from_spec(spec_dir),
        revision=ack.revision if ack.record else (current.revision if current else 0),
        request_id=ack.request_id,
        status=ack.status,
        counts=AckCounts(ack.added, ack.removed, ack.overlaps, ack.unresolved) if ack.record else None,
        worktree=str(location.root),
        spec=spec_dir,
        source=source,
    )
    ack.notices += journal(registry, location.namespace, [event])
    return ack


# --- release ------------------------------------------------------------------------------------------------------


@dataclass
class Released:
    """``task`` is ``""`` when this worktree held no token (``registered`` false) or its record was already gone."""

    task: str
    revision: int
    registered: bool
    already: bool
    notices: list[AdvisoryError] = field(default_factory=list)


def release(session: Session, task_id: str | None = None, *, source: str = "") -> Released:
    """Remove this worktree's record with its token and delete the token; repeating is a no-op.

    Without ``task_id`` and without a token nothing happens (``registered`` false). With ``task_id`` the token must
    own that record (``ScopeTokenMismatchError``), and a token is required (``ScopeTokenMissingError``). A record not
    found while some record files cannot be read is ``SPEC_SCOPE_RECORD_INVALID`` at ``ERROR``; the token is kept.
    """
    location, registry, deadline = session.location, session.registry, session.deadline
    token = load_token(location.token_path)
    if token is None:
        if task_id:
            raise ScopeTokenMissingError(
                "this worktree holds no scope registry token", target_files=[str(location.token_path)]
            )
        return Released("", 0, registered=False, already=False)
    records, problems = registry.query(location.namespace, deadline)
    digest = token_hash(token)
    if task_id:
        target = next((record for record in records if record.task_id == task_id), None)
    else:
        target = next((record for record in records if record.token_hash == digest), None)
    if target is None:
        if problems:  # the record looked for may be one of the unreadable files: keep the token
            raise _unreadable(location, problems)
        if not any(record.token_hash == digest for record in records):
            remove_token(location.token_path)  # orphaned: its record was released or swept
        return Released(task_id or "", 0, registered=True, already=True)
    registry.release(location.namespace, target.task_id, token, deadline)
    remove_token(location.token_path)
    notices = journal(registry, location.namespace, [record_event(EventKind.RELEASE, target, source)])
    return Released(target.task_id, target.revision, registered=True, already=False, notices=notices)
