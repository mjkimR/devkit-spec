"""Backlog guard: Backlog changes only a draft proposal whose Planning has not started (01 §5.1).

Planning runs on ``plan-<slug>``; while that branch exists (locally or fetched from a remote) the proposal is
reviewed there, and Backlog must not edit, split or delete the base's copy. Backlog edits proposals by hand, so the
guard is a command an agent runs before each such change (``devkit spec proposal check``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from devkit.core import FrontmatterError
from devkit.core.frontmatter import parse

from devkit_spec.branches import planning_branches
from devkit_spec.errors import ProposalInPlanningError, ProposalNotFoundError
from devkit_spec.proposals.scaffold import bundle_dir, require_slug, single_file


@dataclass(frozen=True)
class BacklogCheck:
    id: str
    path: str
    status: str

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "path": self.path, "status": self.status, "editable": True}


def check_backlog_editable(root: Path, raw_slug: str) -> BacklogCheck:
    """The draft proposal ``raw_slug`` when Backlog may change it; ``ProposalInPlanningError`` while its
    ``plan-<slug>`` exists or once it left ``draft``, ``ProposalNotFoundError`` when there is none."""
    slug = require_slug(raw_slug.strip().removeprefix("PROP-"))
    bundle, single = bundle_dir(root, slug), single_file(root, slug)
    anchor = bundle / "proposal.md" if bundle.is_dir() else single
    rel = anchor.relative_to(root).as_posix()
    if not anchor.is_file():
        raise ProposalNotFoundError(f"PROP-{slug} has no proposal at {rel}", target_files=[rel])
    try:
        status = str((parse(anchor.read_text("utf-8")).data or {}).get("status") or "")
    except (FrontmatterError, OSError, UnicodeError):
        status = ""
    branch = planning_branches(root).get(slug)
    if branch is not None:
        raise ProposalInPlanningError(
            f"PROP-{slug} is in Planning on {branch}; Backlog does not edit, split or delete it",
            target_files=[rel],
            fix=f"Change it on {branch} as part of its Planning, or wait until that branch is merged and removed",
        )
    if status != "draft":
        raise ProposalInPlanningError(
            f"PROP-{slug} is {status or 'without a status'}, not draft; Backlog changes only a draft whose Planning has"
            " not started",
            target_files=[rel],
            fix="Leave it to its Planning, its Development or the hygiene cleanup of a rejected proposal",
        )
    return BacklogCheck(f"PROP-{slug}", rel, status)
