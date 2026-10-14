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

from devkit.advisory import Actor, AdvisoryError, Level, Retry

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
from devkit_spec.scope.deadline import JOURNAL_SECONDS, ROLLBACK_SECONDS, Deadline
from devkit_spec.scope.inputs import from_spec, observe_git
from devkit_spec.scope.localfs import LocalRegistry
from devkit_spec.scope.location import (
    Location,
    base_ref,
    head_revision,
    incomplete_token,
    load_token,
    locate,
    ref_exists,
    remove_token,
    save_token,
)
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


def collect(
    location: Location, spec_dir: str, base_revision: str, deadline: Deadline, stamp: str, *, base_ref: str = ""
) -> ScopeSet:
    """The declared scope of the bundle plus what Git observes in the worktree on the task's side of ``base_ref``
    (since ``base_revision`` without one)."""
    scope = from_spec(location.root, spec_dir)
    observed, unresolved = observe_git(location.root, base_revision, deadline, stamp, base_ref=base_ref)
    scope.observed = observed
    scope.unresolved += unresolved
    return scope


def register(session: Session, spec_dir: str, task_id: str | None = None, *, source: str = "") -> Registered:
    """Register the bundle at the workspace-relative ``spec_dir`` as this worktree's task and save its token.

    ``task_id`` defaults to the spec ID. The record keeps HEAD as ``base_revision`` and the branch the base checkout
    is on as ``base_ref``. Raises ``ScopeTokenExistsError`` when this worktree already holds a token, also when a
    concurrent registration saved its token first; a record whose token could not be saved is removed again.
    """
    location, registry, deadline = session.location, session.registry, session.deadline
    if location.token_path.exists():
        raise ScopeTokenExistsError("this worktree already registered a task", target_files=[str(location.token_path)])
    stamp = utc_now()
    base = head_revision(location.root, deadline)
    ref = base_ref(location, deadline)
    scope = collect(location, spec_dir, base, deadline, stamp, base_ref=ref)
    record = Record(
        namespace=location.namespace,
        task_id=task_id or scope.id,
        worktree=str(location.root),
        base_revision=base,
        base_ref=ref,
        spec=spec_dir,
        scopes=tuple(scope.all_paths()),
        unresolved=tuple(scope.unresolved),
    )
    token, stored = registry.register(record, deadline)
    try:
        save_token(location.token_path, token)
    except OSError as exc:
        # never leave a record nobody can release; a failed rollback is a detail of the original error
        details = _rollback(registry, stored, token)
        target = [str(location.token_path)]
        if isinstance(exc, FileExistsError):
            raise ScopeTokenExistsError(
                "another registration in this worktree saved its token first", *details, target_files=target
            ) from exc
        raise ScopeSharedPathError(f"the token could not be saved: {exc}", *details, target_files=target) from exc
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


def _rollback(registry: Registry, stored: Record, token: str) -> list[str]:
    """Release the record just registered, under its own deadline; the failure as a detail line, if any."""
    try:
        registry.release(stored.namespace, stored.task_id, token, Deadline(ROLLBACK_SECONDS))
    except (AdvisoryError, OSError) as exc:
        message = exc.message if isinstance(exc, AdvisoryError) else str(exc)
        return [f"the record of task {stored.task_id} could not be removed again and has no token: {message}"]
    return []


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
    ``SPEC_SCOPE_RECORD_INVALID`` at ``ERROR`` (``INTERACTION``) when it is not found while unreadable record files
    may hold it (``Registry.may_hold``); unreadable files that cannot be it are only ``problems``.
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
        suspects = _suspects(session, problems, digest)
        if suspects:
            raise _unreadable(location, suspects, _OWN_UNREADABLE)
        raise ScopeRecordMissingError(
            "the record of this worktree's token no longer exists (released or swept)",
            target_files=[str(location.token_path)],
        )
    others = [record for record in records if record.token_hash != digest]
    return Own(token, mine[0], others, problems)


_OWN_UNREADABLE = (
    "this worktree's record is not among the readable records and may be one of the record files that cannot be read"
)


def _suspects(session: Session, problems: Sequence[Problem], digest: str) -> list[Problem]:
    """The unreadable record files that may be the record of the token hashed to ``digest``."""
    namespace = session.location.namespace
    return [problem for problem in problems if session.registry.may_hold(namespace, problem, digest)]


def _unreadable(location: Location, problems: Sequence[Problem], message: str) -> ScopeRecordInvalidWarning:
    """The record looked for may be one of the unreadable ``problems``: an ``ERROR`` the user resolves
    (``INTERACTION``), because only a person can tell whether those files may be repaired or deleted. Until then
    nothing is removed and this worktree's token is kept."""
    directory = location.shared_path / location.namespace
    return ScopeRecordInvalidWarning(
        f"{message}; this worktree's token is kept until the files are repaired or removed",
        *(f"{problem.file}: {problem.reason}" for problem in problems),
        level=Level.ERROR,
        actor=Actor.USER,
        retry=Retry.AFTER_FIX,
        what_to_report=(
            "The record files in [TARGET] cannot be read and may hold the record this command needs; "
            "this worktree's token is kept"
        ),
        fix=(
            "Once the user decides, repair the record files in [TARGET] or delete those whose tasks are finished "
            "(devkit spec scope sweep lists them with verdict=error), then rerun the same command"
        ),
        target_files=[str(directory / problem.file) for problem in problems],
    )


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


def _current_base_ref(location: Location, stored: str, deadline: Deadline) -> str:
    """The record's base ref while it names a commit; else the base branch detected now (``base_ref``) when that one
    does, so a renamed or deleted base branch, or one the base checkout took after a detached registration, stops
    being unresolved; else the stored one (``observe_git`` then reports it as ``missing-base-ref``)."""
    if stored and ref_exists(location.root, stored, deadline):
        return stored
    detected = base_ref(location, deadline)
    if detected and detected != stored and ref_exists(location.root, detected, deadline):
        return detected
    return stored


def _diff_scopes(before: Sequence[ScopePath], after: Sequence[ScopePath]) -> tuple[int, int]:
    was = {path.key for path in before}
    now = {path.key for path in after}
    return len(now - was), len(was - now)


def update(session: Session, spec_dir: str, request_id: str | None = None, *, source: str = "") -> Ack:
    """Recollect the bundle's declared and observed scope, write it with this worktree's token and the revision just
    read, and compare it with the namespace's other records.

    The observed range forks from the record's ``base_ref`` (``observe_git``); a record without one, or whose
    ``base_ref`` no longer names a commit (renamed or deleted), takes the base branch detected now when that one does
    (``_current_base_ref``). ``request_id`` retries an update
    whose outcome was not observed: an ID the record already applied is answered from the stored record, with the
    ``added`` and ``removed`` counts that request recorded, before anything is collected or written. Never raises
    for a registry failure: the ACK carries it.
    """
    location, registry, deadline = session.location, session.registry, session.deadline
    ack = Ack(status=AckStatus.APPLIED, request_id=request_id or new_request_id())
    current: Record | None = None
    try:
        mine = own(session)
        current = mine.record
        ack.problems = mine.problems
        if request_id and current.last_request_id == request_id:
            stored = current  # already applied: answered from the stored record
        else:
            stamp = utc_now()
            ref = _current_base_ref(location, current.base_ref, deadline)
            scope = collect(location, spec_dir, current.base_revision, deadline, stamp, base_ref=ref)
            added, removed = _diff_scopes(current.scopes, scope.all_paths())
            proposed = current.with_(
                base_ref=ref,
                spec=spec_dir,
                scopes=tuple(scope.all_paths()),
                unresolved=tuple(scope.unresolved),
                last_added=added,
                last_removed=removed,
            )
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
        ack.added, ack.removed = stored.last_added, stored.last_removed  # a replay reports the counts it recorded
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

    Without ``task_id`` and without a token nothing happens (``registered`` false); an incomplete token file (one
    ``load_token`` takes for no token) is removed. With ``task_id`` the token must own that record
    (``ScopeTokenMismatchError``), and a token is required (``ScopeTokenMissingError``). A token whose record is gone
    is removed (orphaned), unless an unreadable record file may hold that record. ``SPEC_SCOPE_RECORD_INVALID`` at
    ``ERROR`` (the token kept) is raised only when the record looked for may be unreadable: with ``task_id`` when
    that task's own record file cannot be read, without it when an unreadable file may hold this token's record.
    """
    location, registry, deadline = session.location, session.registry, session.deadline
    token = load_token(location.token_path)
    if token is None:
        if task_id:
            raise ScopeTokenMissingError(
                "this worktree holds no scope registry token", target_files=[str(location.token_path)]
            )
        if incomplete_token(location.token_path):
            remove_token(location.token_path)  # a token nobody can present: an interrupted save
        return Released("", 0, registered=False, already=False)
    records, problems = registry.query(location.namespace, deadline)
    digest = token_hash(token)
    suspects = _suspects(session, problems, digest)
    if task_id:
        target = next((record for record in records if record.task_id == task_id), None)
        named = [problem for problem in problems if problem.file == registry.record_file(task_id)]
        if target is None and named:
            raise _unreadable(location, named, f"the record of task {task_id} cannot be read")
    else:
        target = next((record for record in records if record.token_hash == digest), None)
        if target is None and suspects:
            raise _unreadable(location, suspects, _OWN_UNREADABLE)
    if target is None:
        if not suspects and not any(record.token_hash == digest for record in records):
            remove_token(location.token_path)  # orphaned: its record was released or swept
        return Released(task_id or "", 0, registered=True, already=True)
    registry.release(location.namespace, target.task_id, token, deadline)
    remove_token(location.token_path)
    notices = journal(registry, location.namespace, [record_event(EventKind.RELEASE, target, source)])
    return Released(target.task_id, target.revision, registered=True, already=False, notices=notices)
