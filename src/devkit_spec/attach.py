"""``devkit.attach_check`` extension: is the unit the one of the activity branch it is attached to?

devkit calls ``attach_check(root, branch, unit, tip)`` before ``devkit worktree start <branch> --existing-branch
... --unit <unit>`` changes anything, with the base checkout's root, the activity branch (``plan-<slug>`` or
``dev-<slug>``), the unit directory relative to that root and the commit the branch is attached at. devkit itself
checks only the branch name and that the directory exists at ``tip``; which unit belongs to which activity is
spec-driven knowledge, so it is checked here (``CAP-DLV-delivery-workflows``):

- ``plan-<slug>``: the proposal bundle ``docs/proposals/PROP-<slug>`` bound to ``sdd-proposal``, neither
  ``rejected`` (a rejected proposal is never resumed) nor marked ``needs_decompose`` (Backlog splits it first);
- ``dev-<slug>``: the spec bundle ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>`` bound to an ``sdd-spec-*`` workflow, or,
  before Development's first step handed it off, the accepted proposal bundle ``docs/proposals/PROP-<slug>``.

The files are read at ``tip`` through Git, since no worktree may exist yet. Each mismatch is a reason to refuse
(``WORKTREE_ATTACH_REFUSED``); a Git failure other than a missing file propagates, and devkit refuses then too
(``WORKTREE_ATTACH_CHECK_FAILED``).
"""

from __future__ import annotations

import re
from pathlib import Path

from devkit.core import FrontmatterError, GitError, run_git
from devkit.core.frontmatter import parse

PROPOSAL_UNIT = re.compile(r"(?:.+/)?docs/proposals/PROP-(?P<slug>[^/]+)")
SPEC_UNIT = re.compile(r"(?:.+/)?specs/\d{4}-\d{2}/\d{8}-(?P<slug>[^/]+)")
PROPOSAL_WORKFLOW = "sdd-proposal"
SPEC_WORKFLOW_PREFIX = "sdd-spec-"


def _anchor(root: Path, tip: str, unit: str, name: str) -> dict[str, object] | None:
    """The frontmatter of ``<unit>/<name>`` at ``tip``; ``None`` when the file is not there."""
    try:
        text = run_git(root, "show", f"{tip}:{unit}/{name}").decode("utf-8", errors="replace")
    except GitError as exc:
        if exc.returncode is None:
            raise
        return None
    try:
        return parse(text).data or {}
    except FrontmatterError as exc:
        return {"__error__": str(exc)}


def _bound(meta: dict[str, object] | None, unit: str, name: str, tip: str) -> tuple[str, list[str]]:
    """The workflow the anchor binds, with the reasons it cannot be read."""
    if meta is None:
        return "", [f"{unit} has no {name} at {tip[:7]}"]
    if "__error__" in meta:
        return "", [f"{unit}/{name} at {tip[:7]} has unreadable frontmatter: {meta['__error__']}"]
    workflow = meta.get("workflow")
    return (workflow if isinstance(workflow, str) else ""), []


def attach_check(root: Path, branch: str, unit: str, tip: str) -> list[str]:
    """The reasons ``unit`` at ``tip`` is not the unit of the activity branch ``branch``; empty when it is."""
    activity, _, slug = branch.partition("-")
    unit = unit.strip("/")
    proposal, spec = PROPOSAL_UNIT.fullmatch(unit), SPEC_UNIT.fullmatch(unit)
    if activity == "plan":
        if proposal is None:
            return [f"{unit} is not a proposal bundle docs/proposals/PROP-<slug>; a plan- branch carries a proposal"]
        match, anchor, expected = proposal, "proposal.md", f"bound to {PROPOSAL_WORKFLOW}"
    elif activity == "dev":
        if spec is None and proposal is None:
            return [
                f"{unit} is neither a spec bundle specs/<YYYY-MM>/<YYYYMMDD>-<slug> nor a proposal bundle"
                " docs/proposals/PROP-<slug>; a dev- branch carries a spec, or the accepted proposal before its handoff"
            ]
        match = spec or proposal
        anchor = "spec.md" if spec else "proposal.md"
        expected = f"bound to an {SPEC_WORKFLOW_PREFIX}* workflow" if spec else "accepted and bound to sdd-proposal"
    else:
        return [f"{branch} is not a plan- or dev- activity branch"]
    assert match is not None
    reasons = []
    if match["slug"] != slug:
        reasons.append(f"{unit} is the unit of slug {match['slug']}, not of {branch}")
    meta = _anchor(root, tip, unit, anchor)
    workflow, problems = _bound(meta, unit, anchor, tip)
    if problems:
        return reasons + problems
    fits = workflow.startswith(SPEC_WORKFLOW_PREFIX) if anchor == "spec.md" else workflow == PROPOSAL_WORKFLOW
    if anchor == "proposal.md" and activity == "dev" and meta is not None and meta.get("status") != "accepted":
        fits = False
    if anchor == "proposal.md" and activity == "plan" and meta is not None:
        if meta.get("status") == "rejected":
            reasons.append(f"{unit} is rejected: a rejected proposal is never resumed; it waits for hygiene cleanup")
        if meta.get("needs_decompose") is True:
            reasons.append(f"{unit} is marked needs_decompose: Backlog splits it before Planning")
    if not fits:
        reasons.append(f"{unit}/{anchor} at {tip[:7]} is not {expected} (workflow: {workflow or '-'})")
    return reasons
