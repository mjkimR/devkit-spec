"""``devkit.post_finish`` extension: the spec cleanup after ``devkit worktree finish`` succeeded.

devkit calls ``after_finish(base, result)`` in the base checkout once the task's branch is merged and its worktree
removed, or once ``finish --discard`` dropped it unmerged (``discarded``) at a close. The result names the activity branch (``branch``: ``plan-<slug>`` or ``dev-<slug>``) and its ``slug``
without the prefix, which names the proposal. A project that deploys the ``spec`` bundle then needs two cleanups the merge cannot do:

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

from pathlib import Path
from typing import Any

from devkit.advisory import AdvisoryError

from devkit_spec.errors import ProposalCleanupWarning, SpecError
from devkit_spec.proposals.prune import prune_proposals
from devkit_spec.scope.flow import journal, open_session, release, sweep_events
from devkit_spec.scope.model import Verdict

SOURCE = "post-finish"


def after_finish(base: Path, result: dict[str, Any]) -> list[str | AdvisoryError] | None:
    """Prune the slug's empty proposal directories and remove the finished worktree's scope records."""
    if not (base / ".devkit" / "managed" / "spec").is_dir():
        return None
    lines: list[str | AdvisoryError] = []
    slug = str(result.get("slug", ""))
    try:
        pruned = prune_proposals(base, slug)
    except SpecError:  # a slug that cannot name a proposal has none to prune
        pruned = []
    except OSError as exc:  # a directory that cannot be listed or removed: report it and still sweep
        pruned = []
        target = f"docs/proposals/PROP-{slug}"
        lines.append(
            ProposalCleanupWarning(
                f"the empty proposal directories of {target} could not be pruned: {exc}",
                target_files=[target],
                fix=f"Fix the permissions of the directory in [TARGET], then run devkit spec proposal prune {slug}",
            )
        )
    lines += [f"removed empty proposal directory {path}" for path in pruned]
    try:
        lines += _sweep(base, Path(str(result.get("path", ""))))
    except AdvisoryError as exc:  # keep the prune notices; the record waits for an explicit sweep
        sweep = "run devkit spec scope sweep --apply to remove the finished worktree's scope record"
        exc.fix = f"{exc.fix.rstrip('.')}, then {sweep}" if exc.fix else sweep.capitalize()
        lines.append(exc)
    return lines or None


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
