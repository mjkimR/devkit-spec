"""``devkit.hygiene`` extension: rejected proposals waiting for their cleanup (01 §6.2, ``CAP-DLV-proposal-incubation``).

A rejection only sets ``status: rejected`` (the user's reason is in the commit message) and merges the Planning
branch. The later cleanup is the Host's: a rejection ADR outside the proposal directory, referencing the proposal
and the rejection commit, and the deletion of the proposal in the same commit. A whole-workspace ``devkit rules check
--phase hygiene`` calls ``rejected_proposals(root)``, which reports each rejected proposal still in the base as a
``SPEC_PROPOSAL_REJECTED_PENDING`` warning, so the cleanup is not forgotten. A project without the ``spec`` bundle is
left alone.
"""

from __future__ import annotations

from pathlib import Path

from devkit.advisory import AdvisoryError
from devkit.core import FrontmatterError
from devkit.core.frontmatter import parse

from devkit_spec.errors import ProposalRejectedPendingWarning
from devkit_spec.proposals.scaffold import PROPOSALS


def _anchors(root: Path) -> list[Path]:
    directory = root / PROPOSALS
    if not directory.is_dir():
        return []
    bundles = [path / "proposal.md" for path in directory.glob("PROP-*") if path.is_dir()]
    singles = [path for path in directory.glob("PROP-*.md") if path.is_file()]
    return sorted(path for path in [*bundles, *singles] if path.is_file())


def rejected_proposals(root: Path) -> list[AdvisoryError] | None:
    """One ``SPEC_PROPOSAL_REJECTED_PENDING`` warning per rejected proposal of the base; ``None`` without the bundle."""
    if not (root / ".devkit" / "managed" / "spec").is_dir():
        return None
    found: list[AdvisoryError] = []
    for anchor in _anchors(root):
        try:
            status = (parse(anchor.read_text("utf-8")).data or {}).get("status")
        except (FrontmatterError, OSError, UnicodeError):
            continue  # the spec-format rule reports an unreadable proposal
        if status != "rejected":
            continue
        rel = anchor.relative_to(root).as_posix()
        target = rel.removesuffix("/proposal.md")
        found.append(
            ProposalRejectedPendingWarning(
                f"{target} is rejected and waits for its cleanup",
                target_files=[rel],
                fix=f"Find the rejection commit and its reason (git log -1 --format='%H %B' -S'status: rejected' --"
                f" {rel}), write a rejection ADR under docs/decisions/ referencing {target} and that commit, and delete"
                f" {target} in the same commit",
            )
        )
    return found or None
