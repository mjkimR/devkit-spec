"""The data of the work-scope registry: scope paths, scope sets, records, comparison results and journal events.

Every path is workspace-relative and normalized by the entrypoint path contract (``devkit_spec.entrypoints``).
``to_dict`` gives the JSON form the registry stores and ``--format json`` prints; ``from_dict`` reads a stored
record back and raises ``ValueError`` for anything that is not one.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = 1


class Source(StrEnum):
    """Where a scope path came from."""

    DECLARED_DOC = "declared-doc"  # a document target of target-docs.md or reconcile.md
    DECLARED_CODE = "declared-code"  # a tasks.md _Boundary entry
    CANDIDATE = "candidate"  # an entrypoint of a document target
    OBSERVED = "observed"  # a path Git reports as changed in the worktree


class Stage(StrEnum):
    """The lifecycle stage at which a scope path was declared or observed."""

    PROP = "prop"
    SPEC = "spec"
    BUILD = "build"


class Granularity(StrEnum):
    FILE = "file"
    DIR = "dir"
    UNKNOWN = "unknown"  # not in the working tree (planned, or deleted)


def now() -> str:
    """The current time in RFC 3339 UTC with microseconds (``2026-10-13T08:00:00.000000Z``)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True)
class ScopePath:
    """One scope entry: a normalized path, its granularity, source and stage, and when it was first recorded."""

    path: str
    kind: Granularity
    source: Source
    stage: Stage
    first_seen: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (str(self.source), self.path)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "path": self.path,
            "kind": str(self.kind),
            "source": str(self.source),
            "stage": str(self.stage),
        }
        if self.first_seen:
            data["first_seen"] = self.first_seen
        return data

    @classmethod
    def from_dict(cls, data: Any) -> ScopePath:
        mapping = _mapping(data, "scope path")
        return cls(
            path=_text(mapping, "path", required=True),
            kind=Granularity(mapping.get("kind", "unknown")),
            source=Source(mapping["source"]),
            stage=Stage(mapping.get("stage", "build")),
            first_seen=_text(mapping, "first_seen"),
        )


@dataclass(frozen=True)
class Unresolved:
    """An input the analysis could not turn into a scope path; it never counts as ``no overlap``.

    ``reason``: ``planned-doc``, ``no-entrypoints``, ``not-a-path``, ``invalid-path``, ``excluded-tree``, ``waived``,
    ``no-targets``, ``missing-target-docs``, ``missing-reconcile``, ``missing-tasks``, ``missing-base-revision``,
    ``unknown-base-revision`` or ``missing-base-ref``.
    """

    value: str
    reason: str
    source: Source | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"value": self.value, "reason": self.reason}
        if self.source is not None:
            data["source"] = str(self.source)
        return data

    @classmethod
    def from_dict(cls, data: Any) -> Unresolved:
        mapping = _mapping(data, "unresolved entry")
        source = mapping.get("source")
        return cls(
            value=_text(mapping, "value"),
            reason=_text(mapping, "reason", required=True),
            source=Source(source) if source else None,
        )


@dataclass(frozen=True)
class Diff:
    """A document target only one of a bundle's two declarations names (``in``: ``target-docs`` or ``reconcile``)."""

    path: str
    side: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "in": self.side}


@dataclass
class ScopeSet:
    """The scope of one proposal, spec bundle or record: documents, declared and candidate code, observed paths."""

    id: str
    docs: list[ScopePath] = field(default_factory=list)
    code: list[ScopePath] = field(default_factory=list)
    observed: list[ScopePath] = field(default_factory=list)
    unresolved: list[Unresolved] = field(default_factory=list)
    diff: list[Diff] = field(default_factory=list)

    def all_paths(self) -> list[ScopePath]:
        return [*self.docs, *self.code, *self.observed]

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "docs": [path.to_dict() for path in self.docs],
            "code": [path.to_dict() for path in self.code],
            "observed": [path.to_dict() for path in self.observed],
            "unresolved": [item.to_dict() for item in self.unresolved],
            "diff": [item.to_dict() for item in self.diff],
        }


@dataclass(frozen=True)
class Evidence:
    """One overlapping path of a pair: ``path`` on the first side (with its granularity), ``other`` on the second."""

    kind: str  # doc | code
    path: str
    granularity: Granularity
    other: str
    source: Source
    other_source: Source

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "path": self.path,
            "granularity": str(self.granularity),
            "other": self.other,
            "source": str(self.source),
            "other_source": str(self.other_source),
        }


@dataclass(frozen=True)
class PairResult:
    """The comparison of two scope sets: evidence and counts only; ranking and weighting are the consumer's."""

    a: str
    b: str
    docs: tuple[Evidence, ...]
    code: tuple[Evidence, ...]
    unresolved: int

    @property
    def overlapping(self) -> bool:
        return bool(self.docs or self.code)

    def to_dict(self) -> dict[str, object]:
        return {
            "a": self.a,
            "b": self.b,
            "docs": [item.to_dict() for item in self.docs],
            "code": [item.to_dict() for item in self.code],
            "unresolved": self.unresolved,
        }


@dataclass(frozen=True)
class Record:
    """One registered task scope (schema version 1). The registry stores the token's hash, never the token.

    ``base_ref`` is the base branch the observed range forks from (``""``: the fixed ``base_revision``);
    ``last_added`` and ``last_removed`` are the counts of the update ``last_request_id`` applied, so a retried
    request is answered with them.
    """

    namespace: str
    task_id: str
    worktree: str
    hostname: str = ""
    token_hash: str = ""
    revision: int = 0
    base_revision: str = ""
    base_ref: str = ""
    shared_worktree: bool = False
    spec: str = ""
    scopes: tuple[ScopePath, ...] = ()
    unresolved: tuple[Unresolved, ...] = ()
    updated_at: str = ""
    last_request_id: str = ""
    last_added: int = 0
    last_removed: int = 0
    schema_version: int = SCHEMA_VERSION

    def with_(self, **changes: Any) -> Record:
        return replace(self, **changes)

    def to_set(self) -> ScopeSet:
        """The record as a scope set for comparison."""
        result = ScopeSet(id=self.task_id, unresolved=list(self.unresolved))
        for path in self.scopes:
            if path.source is Source.DECLARED_DOC:
                result.docs.append(path)
            elif path.source is Source.OBSERVED:
                result.observed.append(path)
            else:
                result.code.append(path)
        return result

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "namespace": self.namespace,
            "task_id": self.task_id,
            "token_hash": self.token_hash,
            "revision": self.revision,
            "base_revision": self.base_revision,
            "base_ref": self.base_ref,
            "worktree": self.worktree,
            "hostname": self.hostname,
            "shared_worktree": self.shared_worktree,
            "spec": self.spec,
            "scopes": [path.to_dict() for path in self.scopes],
            "unresolved": [item.to_dict() for item in self.unresolved],
            "updated_at": self.updated_at,
            "last_request_id": self.last_request_id,
            "last_added": self.last_added,
            "last_removed": self.last_removed,
        }

    def public_dict(self) -> dict[str, object]:
        """``to_dict`` without the token hash: what ``--format json`` prints."""
        data = self.to_dict()
        del data["token_hash"]
        return data

    @classmethod
    def from_dict(cls, data: Any) -> Record:
        mapping = _mapping(data, "record")
        revision = mapping.get("revision", 0)
        version = mapping.get("schema_version", SCHEMA_VERSION)
        counts = [mapping.get(key, 0) for key in ("last_added", "last_removed")]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (revision, version, *counts)):
            raise ValueError("revision, schema_version, last_added and last_removed must be integers")
        shared = mapping.get("shared_worktree", False)
        if not isinstance(shared, bool):
            raise ValueError("shared_worktree must be a boolean")
        return cls(
            schema_version=version,
            namespace=_text(mapping, "namespace", required=True),
            task_id=_text(mapping, "task_id", required=True),
            token_hash=_text(mapping, "token_hash"),
            revision=revision,
            base_revision=_text(mapping, "base_revision"),
            base_ref=_text(mapping, "base_ref"),
            worktree=_text(mapping, "worktree"),
            hostname=_text(mapping, "hostname"),
            shared_worktree=shared,
            spec=_text(mapping, "spec"),
            scopes=tuple(ScopePath.from_dict(item) for item in _list(mapping, "scopes")),
            unresolved=tuple(Unresolved.from_dict(item) for item in _list(mapping, "unresolved")),
            updated_at=_text(mapping, "updated_at"),
            last_request_id=_text(mapping, "last_request_id"),
            last_added=counts[0],
            last_removed=counts[1],
        )


@dataclass(frozen=True)
class Problem:
    """A registry file, or a line of the journal (``line`` > 0), that could not be read: ``reason`` ``parse`` or
    ``permission``."""

    file: str
    reason: str
    line: int = 0

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"file": self.file, "reason": self.reason}
        if self.line:
            data["line"] = self.line
        return data


class Verdict(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    UNVERIFIABLE = "unverifiable"
    ERROR = "error"
    REMOVED = "removed"


@dataclass(frozen=True)
class SweepResult:
    """The verdict on one record file; ``spec`` and ``worktree`` are journal context (empty when unreadable)."""

    task_id: str
    file: str
    verdict: Verdict
    reason: str = ""
    revision: int = 0
    spec: str = ""
    worktree: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "file": self.file,
            "verdict": str(self.verdict),
            "reason": self.reason,
            "revision": self.revision,
        }


class EventKind(StrEnum):
    REGISTER = "register"
    UPDATE = "update"
    RELEASE = "release"
    SWEEP = "sweep"
    GUARD = "guard"  # reserved: specrig journaled worktree guard refusals; devkit's worktree commands do not


@dataclass(frozen=True)
class AckCounts:
    added: int
    removed: int
    overlaps: int
    unresolved: int


@dataclass(frozen=True)
class Event:
    """One journal line: diagnostic history, never an input to overlap, stale or stage verdicts.

    ``source`` names the command that recorded it when that is not the ``scope`` subcommand of the same name
    (``handoff``). Empty values are left out of the JSON line.
    """

    event: str
    at: str = ""
    task: str = ""
    slug: str = ""
    revision: int = 0
    request_id: str = ""
    status: str = ""
    counts: AckCounts | None = None
    verdict: str = ""
    reason: str = ""
    code: str = ""
    worktree: str = ""
    spec: str = ""
    source: str = ""

    def matches(self, task: str) -> bool:
        """Whether the event belongs to the task ID or slug ``task``."""
        return bool(task) and task in (self.task, self.slug)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"at": self.at, "event": self.event}
        for key in ("task", "slug"):
            if getattr(self, key):
                data[key] = getattr(self, key)
        if self.revision:
            data["revision"] = self.revision
        for key in ("request_id", "status"):
            if getattr(self, key):
                data[key] = getattr(self, key)
        if self.counts is not None:
            data |= {
                "added": self.counts.added,
                "removed": self.counts.removed,
                "overlaps": self.counts.overlaps,
                "unresolved": self.counts.unresolved,
            }
        for key in ("verdict", "reason", "code", "worktree", "spec", "source"):
            if getattr(self, key):
                data[key] = getattr(self, key)
        return data

    @classmethod
    def from_dict(cls, data: Any) -> Event:
        mapping = _mapping(data, "event")
        counts = None
        if all(isinstance(mapping.get(key), int) for key in ("added", "removed", "overlaps", "unresolved")):
            counts = AckCounts(mapping["added"], mapping["removed"], mapping["overlaps"], mapping["unresolved"])
        revision = mapping.get("revision", 0)
        if isinstance(revision, bool) or not isinstance(revision, int):
            raise ValueError("revision must be an integer")
        return cls(
            event=_text(mapping, "event", required=True),
            at=_text(mapping, "at"),
            task=_text(mapping, "task"),
            slug=_text(mapping, "slug"),
            revision=revision,
            request_id=_text(mapping, "request_id"),
            status=_text(mapping, "status"),
            counts=counts,
            verdict=_text(mapping, "verdict"),
            reason=_text(mapping, "reason"),
            code=_text(mapping, "code"),
            worktree=_text(mapping, "worktree"),
            spec=_text(mapping, "spec"),
            source=_text(mapping, "source"),
        )


def _mapping(data: Any, what: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{what} must be a JSON object")
    return data


def _text(mapping: dict[str, Any], key: str, *, required: bool = False) -> str:
    value = mapping.get(key, "")
    if value is None:
        value = ""
    if not isinstance(value, str) or (required and not value):
        raise ValueError(f"{key} must be a {'non-empty ' if required else ''}string")
    return value


def _list(mapping: dict[str, Any], key: str) -> list[Any]:
    value = mapping.get(key) or []
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value
