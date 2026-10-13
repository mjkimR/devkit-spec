"""devkit_spec.proposals: proposals and the spec bundles they become.

``create_proposal`` scaffolds ``docs/proposals/PROP-<slug>/`` (bound to workflow ``incubated-delivery`` when the
project has it), ``create_padr`` a preliminary decision inside it, and ``handoff_proposal`` turns an approved proposal
into ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/``, promoting PADRs to ADRs, moving materials and rewriting what pointed into
the proposal. ``create_spec`` creates a spec bundle without a proposal. Contracts: ``CAP-DLV-proposal-incubation`` and ``CAP-DLV-spec-bundles`` (``docs/capabilities/delivery/``).
"""

from devkit_spec.proposals.binding import BUGFIX_WORKFLOW, DEFAULT_WORKFLOW, PROPOSAL_WORKFLOW, resolve_binding
from devkit_spec.proposals.body import CarriedProposal, carry_proposal_body, ensure_ac_ids
from devkit_spec.proposals.handoff import HANDOFF_WORKFLOW, HandoffResult, PromotedDecision, handoff_proposal
from devkit_spec.proposals.prune import prune_proposals
from devkit_spec.proposals.rewrite import RelocationPlan, Rewritten, Unresolved
from devkit_spec.proposals.scaffold import (
    TARGET_DOCS,
    CreatedDecision,
    CreatedProposal,
    clean_slug,
    create_padr,
    create_proposal,
    yaml_scalar,
)
from devkit_spec.proposals.specs import SKELETON_MARKER, CreatedSpec, create_spec, mark_skeleton, spec_files

__all__ = [
    "BUGFIX_WORKFLOW",
    "DEFAULT_WORKFLOW",
    "HANDOFF_WORKFLOW",
    "PROPOSAL_WORKFLOW",
    "SKELETON_MARKER",
    "TARGET_DOCS",
    "CarriedProposal",
    "CreatedDecision",
    "CreatedProposal",
    "CreatedSpec",
    "HandoffResult",
    "PromotedDecision",
    "RelocationPlan",
    "Rewritten",
    "Unresolved",
    "carry_proposal_body",
    "clean_slug",
    "create_padr",
    "create_proposal",
    "create_spec",
    "ensure_ac_ids",
    "handoff_proposal",
    "mark_skeleton",
    "prune_proposals",
    "resolve_binding",
    "spec_files",
    "yaml_scalar",
]
