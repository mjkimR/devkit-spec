"""``devkit.post_finish`` extension: the spec cleanup after ``devkit worktree finish`` or ``devkit.integration``.

devkit calls ``after_finish(base, result)`` in the base checkout once the task's branch is merged and its worktree
removed, or once ``finish --discard`` dropped it unmerged (``discarded``) at a close. When the approval-bound local
integration service (``devkit.integration``) prepares and executes a request, it calls ``integration_plan``,
``integration_validate`` and ``integration_run`` on the same extension object so the cleanup scope is bound to the
approved request digest and never sweeps records outside the finished worktree or at an unapproved revision.

The result names the activity branch (``branch``: ``plan-<slug>`` or ``dev-<slug>``) and its ``slug`` without the
prefix, which names the proposal. A project that deploys the ``spec`` bundle then needs two cleanups the merge cannot
do:

- ``docs/proposals/PROP-<slug>/``: a handoff deleted the proposal in the worktree; the merge removed its tracked
  files here but leaves the empty directories (``prune_proposals``);
- the task's work scope record: its worktree is gone, so the record is stale (``CAP-COLL-work-scope-registry``).
  Only the records of the finished worktree are removed, at the revision read here, as ``scope sweep --apply``
  would remove them; other stale records stay for an explicit sweep. A ``--no-worktree`` task ran in the base
  checkout itself (the result's ``path``), which is still there, so a sweep would keep its record: the base
  checkout's own record is released instead, as ``scope release`` would.

Each cleanup returns one notice line per change, and neither failure stops the other: a prune that fails (a
directory that cannot be listed or removed) is a ``SPEC_PROPOSAL_CLEANUP_FAILED`` warning whose fix is
``devkit spec proposal prune <slug>``, and the sweep still runs; when the record removal fails (a malformed
``[tool.spec]``, a registry timeout), its error is returned next to the prune notices, which devkit reports as a
warning (``SPEC_CONFIG_INVALID``, ``SPEC_SCOPE_TIMEOUT``, ...), and its fix ends with
``devkit spec scope sweep --apply``. A project without the ``spec`` bundle is left alone.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from devkit.advisory import AdvisoryError
from devkit.core.errors import GitError
from devkit.core.git import run_git
from devkit.integration import (
    CleanupContractError,
    CleanupResult,
    CleanupTarget,
    IntegrationContext,
    StaleRequestError,
)
from devkit.worktree import FinishResult, slug_of

from devkit_spec.errors import PostFinishCleanupNotice, ProposalCleanupWarning, SpecError
from devkit_spec.proposals.prune import prune_proposals
from devkit_spec.proposals.scaffold import require_slug
from devkit_spec.scope.flow import Session, journal, open_session, own, release, sweep_events
from devkit_spec.scope.location import load_token
from devkit_spec.scope.model import Verdict

SOURCE = "post-finish"
KIND_PROPOSAL = "proposal-prune"
KIND_SCOPE = "scope-record"
_SWEEP_FIX = "run devkit spec scope sweep --apply to remove the finished worktree's scope record"


def _has_spec_bundle(base: Path) -> bool:
    return (base / ".devkit" / "managed" / "spec").is_dir()


def _prune_slug(slug: str) -> str:
    try:
        return require_slug(slug)
    except SpecError:
        return ""


def _prune_step(base: Path, slug: str) -> tuple[bool, list[str | AdvisoryError]]:
    lines: list[str | AdvisoryError] = []
    try:
        pruned = prune_proposals(base, slug)
    except SpecError:  # a slug that cannot name a proposal has none to prune
        pruned = []
    except OSError as exc:  # a directory that cannot be listed or removed: report it and still sweep
        target = f"docs/proposals/PROP-{slug}"
        lines.append(
            ProposalCleanupWarning(
                f"the empty proposal directories of {target} could not be pruned: {exc}",
                target_files=[target],
                fix=f"Fix the permissions of the directory in [TARGET], then run devkit spec proposal prune {slug}",
            )
        )
        return False, lines
    lines.extend(f"removed empty proposal directory {path}" for path in pruned)
    return True, lines


def _with_sweep_fix(exc: AdvisoryError) -> AdvisoryError:
    exc.fix = f"{exc.fix.rstrip('.')}, then {_SWEEP_FIX}" if exc.fix else _SWEEP_FIX.capitalize()
    return exc


def _worktree_records(session: Session, base: Path, worktree: Path) -> dict[str, int]:
    if worktree.resolve() == base.resolve():
        if load_token(session.location.token_path) is None:
            return {}
        try:
            mine = own(session)
        except SpecError as exc:
            if exc.code == "SPEC_SCOPE_RECORD_MISSING":
                return {}
            raise
        return {mine.record.task_id: mine.record.revision}
    records, _ = session.registry.query(session.location.namespace, session.deadline)
    finished = worktree.resolve()
    return {record.task_id: record.revision for record in records if Path(record.worktree).resolve() == finished}


def _sweep(base: Path, worktree: Path) -> list[str | AdvisoryError]:
    session = open_session(base)
    if worktree.resolve() == base.resolve():  # a --no-worktree task: the base checkout's own record
        released = release(session, source=SOURCE)
        done = [f"released the scope record of {released.task}"] if released.task and not released.already else []
        return [*done, *released.notices]
    namespace = session.location.namespace
    records, _ = session.registry.query(namespace, session.deadline)
    finished = worktree.resolve()
    expected = {r.task_id: r.revision for r in records if Path(r.worktree).resolve() == finished}
    if not expected:
        return []
    results = session.registry.sweep(namespace, True, expected, session.deadline, only=set(expected))
    notices: list[str | AdvisoryError] = list(journal(session.registry, namespace, sweep_events(results, SOURCE)))
    removed = [result.task_id for result in results if result.verdict is Verdict.REMOVED]
    return [f"removed the scope record of {task}" for task in removed] + notices


def _parse_targets(
    context: IntegrationContext, targets: tuple[CleanupTarget, ...]
) -> tuple[tuple[CleanupTarget, ...], dict[str, int]]:
    slug = _prune_slug(slug_of(context.finish.branch))
    expected_prune = (
        (CleanupTarget(KIND_PROPOSAL, f"docs/proposals/PROP-{slug}", context.finish.source_sha),) if slug else ()
    )
    prune_targets: list[CleanupTarget] = []
    scope_targets: dict[str, int] = {}
    for target in targets:
        if target.kind == KIND_PROPOSAL:
            prune_targets.append(target)
        elif target.kind == KIND_SCOPE:
            if target.identity in scope_targets or not target.revision.isdigit() or int(target.revision) < 1:
                raise CleanupContractError(
                    "scope-record cleanup target requires a unique task id and positive revision"
                )
            scope_targets[target.identity] = int(target.revision)
        else:
            raise CleanupContractError(f"unknown spec cleanup target kind: {target.kind}")
    if tuple(prune_targets) != expected_prune:
        raise StaleRequestError("approved proposal cleanup target does not match the branch and source commit")
    return tuple(prune_targets), scope_targets


def _is_post_git(base: Path, context: IntegrationContext) -> bool:
    plan = context.finish
    try:
        head = run_git(base, "rev-parse", "--verify", "HEAD^{commit}").decode("utf-8", errors="replace").strip()
    except GitError:
        return False
    if head != plan.source_sha:
        return False
    return plan.worktree_identity is None or not Path(plan.path).exists()


def _run_scoped_sweep(
    base: Path, worktree: Path, expected: Mapping[str, int]
) -> tuple[bool, list[str | AdvisoryError]]:
    session = open_session(base)
    current = _worktree_records(session, base, worktree)
    if any(task_id not in expected or expected[task_id] != rev for task_id, rev in current.items()):
        raise StaleRequestError("the finished worktree's scope record changed since the request was prepared")
    if not expected or not current:
        return True, []
    if worktree.resolve() == base.resolve():
        task_id = next(iter(current))
        released = release(session, task_id=task_id, source=SOURCE)
        done = [f"released the scope record of {released.task}"] if released.task and not released.already else []
        return True, [*done, *released.notices]
    namespace = session.location.namespace
    remaining = {task_id: expected[task_id] for task_id in current}
    results = session.registry.sweep(namespace, True, remaining, session.deadline, only=set(remaining))
    if any(result.reason == "stale-revision" for result in results):
        raise StaleRequestError("the finished worktree's scope record changed since the request was prepared")
    notices: list[str | AdvisoryError] = list(journal(session.registry, namespace, sweep_events(results, SOURCE)))
    removed = [result.task_id for result in results if result.verdict is Verdict.REMOVED]
    all_removed = len(removed) == len(remaining) and all(result.verdict is Verdict.REMOVED for result in results)
    return all_removed, [f"removed the scope record of {task}" for task in removed] + notices


class _Cleanup:
    """Dual-mode ``devkit.post_finish`` extension: classic callable and ``ScopedCleanup``."""

    integration_local_only = True

    def __call__(self, base: Path, result: dict[str, Any]) -> list[str | AdvisoryError] | None:
        """Prune the slug's empty proposal directories and remove the finished worktree's scope records."""
        if not _has_spec_bundle(base):
            return None
        slug = str(result.get("slug", ""))
        _, lines = _prune_step(base, slug)
        try:
            lines += _sweep(base, Path(str(result.get("path", ""))))
        except AdvisoryError as exc:  # keep the prune notices; the record waits for an explicit sweep
            lines.append(_with_sweep_fix(exc))
        return lines or None

    def integration_plan(self, context: IntegrationContext) -> tuple[CleanupTarget, ...]:
        """Declare the exact proposal directory and scope-record targets for ``context``."""
        base = Path(context.finish.base)
        if not _has_spec_bundle(base):
            return ()
        targets: list[CleanupTarget] = []
        slug = _prune_slug(slug_of(context.finish.branch))
        if slug:
            targets.append(CleanupTarget(KIND_PROPOSAL, f"docs/proposals/PROP-{slug}", context.finish.source_sha))
        session = open_session(base)
        records = _worktree_records(session, base, Path(context.finish.path))
        for task_id, revision in sorted(records.items()):
            targets.append(CleanupTarget(KIND_SCOPE, task_id, str(revision)))
        return tuple(targets)

    def integration_validate(self, context: IntegrationContext, targets: tuple[CleanupTarget, ...]) -> None:
        """Verify that ``targets`` still match the branch and the finished worktree's scope records."""
        base = Path(context.finish.base)
        if not _has_spec_bundle(base):
            if targets:
                raise StaleRequestError("the spec bundle is no longer installed in the base checkout")
            return
        _, expected_scope = _parse_targets(context, targets)
        post_git = _is_post_git(base, context)
        try:
            session = open_session(base)
            current = _worktree_records(session, base, Path(context.finish.path))
        except AdvisoryError:
            if post_git:
                return  # defer transient post-git registry errors to integration_run so proposal pruning still runs
            raise
        if any(task_id not in expected_scope or expected_scope[task_id] != rev for task_id, rev in current.items()):
            raise StaleRequestError("the finished worktree's scope record changed since the request was prepared")
        if not post_git and current != expected_scope:
            raise StaleRequestError("the approved scope record is missing; prepare a new request")

    def integration_run(
        self, context: IntegrationContext, result: FinishResult, targets: tuple[CleanupTarget, ...]
    ) -> CleanupResult:
        """Execute the approved proposal prune and scope-record cleanup targets."""
        del result
        base = Path(context.finish.base)
        if not _has_spec_bundle(base):
            if targets:
                raise StaleRequestError("the spec bundle is no longer installed in the base checkout")
            return CleanupResult(done=True)
        prune_targets, expected_scope = _parse_targets(context, targets)
        done = True
        items: list[str | AdvisoryError] = []
        if prune_targets:
            prune_ok, prune_items = _prune_step(base, slug_of(context.finish.branch))
            done = done and prune_ok
            items.extend(prune_items)
        try:
            sweep_ok, sweep_items = _run_scoped_sweep(base, Path(context.finish.path), expected_scope)
            done = done and sweep_ok
            items.extend(sweep_items)
        except StaleRequestError:
            raise
        except AdvisoryError as exc:
            done = False
            items.append(_with_sweep_fix(exc))
        notices = tuple(item if isinstance(item, AdvisoryError) else PostFinishCleanupNotice(item) for item in items)
        return CleanupResult(done=done, notices=notices)


after_finish = _Cleanup()
integration_local_only = after_finish.integration_local_only
integration_plan = after_finish.integration_plan
integration_validate = after_finish.integration_validate
integration_run = after_finish.integration_run
