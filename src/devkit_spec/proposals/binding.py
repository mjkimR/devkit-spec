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

DEFAULT_WORKFLOW = "direct-delivery"
"""The workflow a spec bundle follows when nothing names another."""
PROPOSAL_WORKFLOW = "incubated-delivery"
"""The workflow a proposal bundle follows until its handoff."""
BUGFIX_WORKFLOW = "bugfix"
"""A spec bound to this workflow carries ``kind: bugfix`` (its exit checks ``frontmatter(spec.md kind bugfix)``)."""

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
    explicit ``value`` that is not a string, does not resolve or does not validate raises ``error``.
    """
    if value is not None and not isinstance(value, str):
        raise error(f"{source}: {field} must be a workflow id", target_files=[source])
    explicit = (value or "").strip()
    workflow = explicit or default
    try:
        doc = Workspace(root, lint=None, ancestor=None).definition(workflow)
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
