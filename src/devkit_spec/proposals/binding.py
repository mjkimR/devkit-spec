"""Bind a new anchor (a spec bundle's ``spec.md``, a proposal's ``proposal.md``) to a devkit workflow.

The workflow is resolved and validated with devkit's own ``Workspace`` (project definitions in
``.devkit/workflows/`` and synchronized ones), before anything is written. A workflow named explicitly must resolve
and validate; a default that is not available leaves the anchor unbound, with a notice.
"""

from __future__ import annotations

import logging
from pathlib import Path

from devkit.advisory import AdvisoryError
from devkit.workflow import Binding, Workspace, schema_hash

from devkit_spec.errors import ProposalWorkflowError, SpecError

TASK_KINDS = ("feature", "bugfix")
"""The values of the ``task-kind`` axis: what the work does. It is not stored on a spec; the bound workflow says it."""
DEFAULT_TASK_KIND = "feature"
EFFORTS = ("low", "medium", "high")
"""The values of the ``activity-effort`` axis and of a proposal's non-authoritative ``planning_effort`` and
``dev_effort`` hints."""
DEFAULT_EFFORT = "medium"
PLANNING_EFFORT = "planning_effort"
DEV_EFFORT = "dev_effort"
PROPOSAL_WORKFLOW = "sdd-proposal"
"""The workflow a proposal bundle follows until its handoff (``planning-depth`` ``proposal``)."""


def spec_workflow(task_kind: str) -> str:
    """The workflow of a spec bundle of ``task_kind``: ``sdd-spec-<task-kind>`` (``planning-depth`` ``spec``)."""
    return f"sdd-spec-{task_kind}"


DEFAULT_WORKFLOW = spec_workflow(DEFAULT_TASK_KIND)
"""The workflow a spec bundle follows when nothing names another."""
BUGFIX_WORKFLOW = spec_workflow("bugfix")
"""A spec bound to this workflow starts with ``spec.md`` only: its ``plan-tasks`` stage writes the plan and tasks."""

_log = logging.getLogger(__name__)


def resolve_binding(
    root: Path,
    value: object,
    source: str,
    *,
    field: str = "workflow",
    default: str = DEFAULT_WORKFLOW,
    error: type[SpecError] = ProposalWorkflowError,
) -> tuple[Binding | None, AdvisoryError | None]:
    """The binding for ``value`` (a workflow id, or ``None``/empty for ``default``), or ``None`` with the reason.

    ``source`` names where ``value`` came from (a file, or a command option) and ``field`` its key, for messages. An
    explicit ``value`` that is not a string, does not resolve, does not validate or names a definition by a path that
    is not the one discovered for its id (devkit's ``Workspace.require_bindable``, ``WORKFLOW_NOT_BINDABLE``) raises
    ``error``.
    """
    if value is not None and not isinstance(value, str):
        raise error(f"{source}: {field} must be a workflow id", target_files=[source])
    explicit = (value or "").strip()
    workflow = explicit or default
    try:
        workspace = Workspace(root, lint=None, ancestor=None)
        doc = workspace.definition(workflow)
        # A binding records only the id: a definition named by a path must be the one discovered for that id.
        workspace.require_bindable(doc, explicit or None)
    except AdvisoryError as exc:
        if explicit:
            raise error(
                f"{field} {workflow} cannot be bound: {exc.message}",
                f"{exc.code}: {exc.message}",
                *exc.details,
                target_files=[source],
            ) from exc
        _log.info("default workflow %s not bound: %s (%s)", workflow, exc.message, exc.code)
        return None, exc
    return Binding(doc.id, schema_hash(doc)), None
