from __future__ import annotations

import errno
import os
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from conftest import Write
from devkit.core import FrontmatterError
from devkit.core.frontmatter import parse
from proposals.support import INCUBATED, MONTH, STAMP, TODAY, WORKFLOW, accept, spec_dir, write_workflow

from devkit_spec.errors import (
    ProposalHandoffError,
    ProposalInvalidError,
    ProposalNeedsDecomposeError,
    ProposalNotApprovedError,
    ProposalNotFoundError,
    ProposalSlugConflictError,
    ProposalSlugError,
    ProposalTargetExistsError,
    ProposalWorkflowError,
)
from devkit_spec.proposals import SKELETON_MARKER, HandoffResult, create_padr, create_proposal, handoff_proposal
from devkit_spec.proposals import specs as specs_module

SPEC = f"specs/{MONTH}/{STAMP}"


def _new(
    root: Path, slug: str, *, title: str | None = None, target_area: str | None = None, with_target_docs: bool = False
) -> Path:
    """A scaffolded bundle; returns its proposal.md."""
    created = create_proposal(
        root, slug, title=title, target_area=target_area, with_target_docs=with_target_docs, today=TODAY
    )
    return root / created.path


def _codes(result: HandoffResult) -> list[str]:
    return [notice.code for notice in result.notices]


def test_lifecycle(workspace: Path) -> None:
    proposal = _new(
        workspace,
        "fast-engine",
        title="Fast Rule Engine",
        target_area="capabilities/governance/",
        with_target_docs=True,
    )
    create_padr(workspace, "fast-engine", "Use Go AST Parser")
    create_padr(workspace, "fast-engine", "Parallel File Worker Pool")
    with pytest.raises(ProposalNotApprovedError) as raised:
        handoff_proposal(workspace, "fast-engine", today=TODAY)
    assert raised.value.advisory.mode == "INTERACTION"
    (proposal.parent / "materials/survey.md").write_text("# Survey Report\nResearch content", encoding="utf-8")
    accept(proposal)
    with proposal.open("a", encoding="utf-8") as handle:
        handle.write("\n\n## Complex Section\nHere is some `inline code` and:\n```yaml\nfoo: bar\n```\n")
    blueprint = (proposal.parent / "target-docs.md").read_text(encoding="utf-8")

    result = handoff_proposal(workspace, "PROP-fast-engine", today=TODAY)

    target = spec_dir(workspace, "fast-engine")
    assert (result.proposal, result.spec, result.dir) == ("PROP-fast-engine", "SPEC-fast-engine", f"{SPEC}-fast-engine")
    spec = (target / "spec.md").read_text(encoding="utf-8")
    assert spec.startswith("---\nid: SPEC-fast-engine\n")
    assert "# [SPEC-fast-engine] Fast Rule Engine" in spec
    assert "### [AC-01] <scenario>" in spec and "[AC-02]" not in spec
    assert "### 1. Background & Hypothesis" in spec
    assert "## 5. Carried Proposal Notes" in spec
    assert "### Complex Section\n\nHere is some `inline code` and:\n```yaml\nfoo: bar\n```" in spec
    assert f"- **Preserved Materials**: `docs/materials/{MONTH}/{STAMP}-fast-engine`" in spec
    tasks = (target / "tasks.md").read_text(encoding="utf-8")
    assert "  - _Requirements: AC-01_" in tasks
    assert "  - **_Boundary**: capabilities/governance/" in tasks
    plan = (target / "plan.md").read_text(encoding="utf-8")
    assert "Target Docs Blueprint: `PROP-fast-engine-target`" in plan

    # The blueprint is kept verbatim apart from its provenance.
    assert result.target_docs == f"{SPEC}-fast-engine/target-docs.md"
    assert (target / "target-docs.md").read_text(encoding="utf-8") == blueprint.replace(
        "proposal: PROP-fast-engine", "proposal: SPEC-fast-engine", 1
    )

    assert [(d.id, d.padr) for d in result.decisions] == [
        ("ADR-parallel-file-worker-pool", "PADR-parallel-file-worker-pool"),
        ("ADR-use-go-ast-parser", "PADR-use-go-ast-parser"),
    ]
    adr = (workspace / f"docs/decisions/{MONTH}/{STAMP}-use-go-ast-parser.md").read_text(encoding="utf-8")
    assert "id: ADR-use-go-ast-parser\n" in adr
    assert "# [ADR-use-go-ast-parser] " in adr
    assert "\nstatus: accepted\n" in adr
    assert "\n- **Status**: Accepted\n" in adr
    assert "proposal: SPEC-fast-engine" in adr
    assert "PADR-" not in adr and "Draft" not in adr

    assert result.materials == f"docs/materials/{MONTH}/{STAMP}-fast-engine"
    assert (workspace / f"docs/materials/{MONTH}/{STAMP}-fast-engine/survey.md").is_file()
    assert not proposal.parent.exists()
    assert result.workflow is None
    assert _codes(result) == ["SPEC_PROPOSAL_UNBOUND", "SPEC_PROPOSAL_REFS_REWRITTEN"]


def test_without_target_docs(workspace: Path) -> None:
    accept(_new(workspace, "lean-idea", title="Lean Idea"))
    result = handoff_proposal(workspace, "lean-idea", today=TODAY)
    target = spec_dir(workspace, "lean-idea")
    assert result.target_docs is None and not (target / "target-docs.md").exists()
    assert "Target Docs Blueprint" not in (target / "plan.md").read_text(encoding="utf-8")
    assert result.materials is None and result.decisions == []
    assert not (workspace / "docs/proposals/PROP-lean-idea").exists()


@pytest.mark.parametrize("status", ["draft", "reviewing", "rejected"])
def test_only_an_accepted_proposal_is_handed_off(workspace: Path, status: str) -> None:
    proposal = _new(workspace, "pending")
    proposal.write_text(proposal.read_text(encoding="utf-8").replace("status: draft", f"status: {status}"), "utf-8")
    with pytest.raises(ProposalNotApprovedError) as raised:
        handoff_proposal(workspace, "pending", today=TODAY)
    assert "plan-accept" in raised.value.message
    assert proposal.is_file() and not (workspace / "specs").exists()


def test_a_proposal_marked_for_decomposition_is_never_handed_off(workspace: Path) -> None:
    proposal = _new(workspace, "large")
    accept(proposal, "\nneeds_decompose: true")
    with pytest.raises(ProposalNeedsDecomposeError) as raised:
        handoff_proposal(workspace, "large", today=TODAY)
    assert raised.value.code == "SPEC_PROPOSAL_NEEDS_DECOMPOSE"
    assert proposal.is_file() and not (workspace / "specs").exists()


def test_unknown_proposal(workspace: Path) -> None:
    with pytest.raises(ProposalNotFoundError):
        handoff_proposal(workspace, "nothing", today=TODAY)


def test_rewrites_links_into_the_bundle(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "linked", title="Linked Proposal", with_target_docs=True)
    bundle = proposal.parent
    create_padr(workspace, "linked", "Pick Engine")
    write("docs/capabilities/lifecycle/CAP-X.md", "# cap\n")
    write(
        "docs/proposals/PROP-linked/materials/survey.md",
        "# Survey\n"
        "[back](../proposal.md) [padr](../decisions/PADR-pick-engine.md#sec) [cap](../../../capabilities/lifecycle/CAP-X.md)\n"
        "[dirlink](../) [sibling](./notes.md)\n",
    )
    write("docs/proposals/PROP-linked/materials/notes.md", "# notes\n")
    other = _new(workspace, "other", title="Other")
    other.write_text(
        "# Other\n"
        "See [prop](../PROP-linked/proposal.md), [blueprint](../PROP-linked/target-docs.md), "
        "[padr](../PROP-linked/decisions/PADR-pick-engine.md), [mat](../PROP-linked/materials/survey.md), "
        "[dir](../PROP-linked/).\n"
        "Ambiguous: [decisions](../PROP-linked/decisions/) and [missing](../PROP-linked/materials/absent/x.md).\n"
        "Keep: [ext](https://example.com/PROP-linked/proposal.md) [anchor](#top) [abs](/docs/proposals/PROP-linked/proposal.md)\n"
        "```md\n[code](../PROP-linked/proposal.md)\n```\n",
        encoding="utf-8",
    )
    write("specs/note.md", "[p](../docs/proposals/PROP-linked/proposal.md)\n")
    accept(proposal)

    result = handoff_proposal(workspace, "linked", today=TODAY)

    spec_rel = f"{SPEC}-linked"
    mat_rel = f"docs/materials/{MONTH}/{STAMP}-linked"
    assert set(result.rewritten_files) == {
        f"{mat_rel}/survey.md",
        "docs/proposals/PROP-other/proposal.md",
        "specs/note.md",
        f"docs/decisions/{MONTH}/{STAMP}-pick-engine.md",
        f"{spec_rel}/target-docs.md",
    }
    assert [u.to_dict() for u in result.unresolved] == [
        {
            "path": "docs/proposals/PROP-other/proposal.md",
            "line": 3,
            "kind": "link",
            "target": "../PROP-linked/decisions/",
            "reason": "unmapped",
        }
    ]
    assert "SPEC_PROPOSAL_LINK_UNRESOLVED" in _codes(result)

    got = other.read_text(encoding="utf-8")
    assert f"[prop](../../../{spec_rel}/spec.md)" in got
    assert f"[blueprint](../../../{spec_rel}/target-docs.md)" in got
    assert f"[padr](../../decisions/{MONTH}/{STAMP}-pick-engine.md)" in got
    assert f"[mat](../../materials/{MONTH}/{STAMP}-linked/survey.md)" in got
    assert f"[dir](../../../{spec_rel}/)" in got  # the trailing slash is kept
    assert "[decisions](../PROP-linked/decisions/)" in got
    # A link into the moved materials keeps pointing into them, as broken as before.
    assert f"[missing](../../materials/{MONTH}/{STAMP}-linked/absent/x.md)" in got
    assert (
        "[ext](https://example.com/PROP-linked/proposal.md) [anchor](#top) [abs](/docs/proposals/PROP-linked/proposal.md)"
        in got
    )
    assert "```md\n[code](../PROP-linked/proposal.md)\n```" in got

    material = (workspace / mat_rel / "survey.md").read_text(encoding="utf-8")
    assert f"[back](../../../../{spec_rel}/spec.md)" in material
    assert f"[padr](../../../decisions/{MONTH}/{STAMP}-pick-engine.md#sec)" in material
    assert "[cap](../../../capabilities/lifecycle/CAP-X.md)" in material
    assert f"[dirlink](../../../../{spec_rel}/)" in material
    assert "[sibling](./notes.md)" in material
    assert (workspace / "specs/note.md").read_text(encoding="utf-8") == f"[p]({MONTH}/{STAMP}-linked/spec.md)\n"
    rewritten = {(r.path, r.line, r.old): r.new for r in result.rewritten if r.kind == "link"}
    assert (
        rewritten[("specs/note.md", 1, "../docs/proposals/PROP-linked/proposal.md")]
        == f"{MONTH}/{STAMP}-linked/spec.md"
    )
    assert not bundle.exists()


def test_carries_the_proposal_body(workspace: Path, write: Write) -> None:
    write("docs/capabilities/lifecycle/CAP-X.md", "# cap\n")
    write(
        "docs/proposals/PROP-carry/proposal.md",
        """---
id: PROP-carry
title: Carry Me
status: accepted
created_at: 2026-10-06
target_area: capabilities/lifecycle/
milestone: "v0.5: First"
boundaries:
  owns:
    - src/scaffold/
    - capabilities/lifecycle/
  excludes:
    - docs/decisions/
---

# [PROP-carry] Carry Me

Intro paragraph before any H2 with a link to [CAP-X](../../capabilities/lifecycle/CAP-X.md).

## Origin and Reason for Handoff

Why this exists. See also [notes](materials/notes.md).

### Detail heading

Nested detail.

---

## Remaining Scope

1. Do the thing.

## Expected Acceptance Checks

- **Given** a bundle, **When** handoff runs, **Then** the body is carried.
- **Given** nothing, **When** handoff runs, **Then** a placeholder exists.

## Non-Goals

1. **Scope Excluded**: Parsing meaning.
   - **Rationale**: Deterministic only.

## Resume Conditions and Dependencies

- Needs nothing.
""",
    )
    write("docs/proposals/PROP-carry/materials/notes.md", "# notes\n")
    write(
        "docs/proposals/PROP-carry/target-docs.md",
        "---\nid: PROP-carry-target\ntitle: t\nstatus: draft\n---\n\n# blueprint\n\n[cap](../../capabilities/lifecycle/CAP-X.md)\n",
    )

    result = handoff_proposal(workspace, "carry", today=TODAY)

    spec = (spec_dir(workspace, "carry") / "spec.md").read_text(encoding="utf-8")
    assert "## 1. Problem Statement & Motivation\n\nHanded off from proposal PROP-carry on 2026-10-13." in spec
    assert "milestone: 'v0.5: First'\n" in spec
    assert (
        "Intro paragraph before any H2 with a link to [CAP-X](../../../docs/capabilities/lifecycle/CAP-X.md)." in spec
    )
    assert (
        "### Origin and Reason for Handoff\n\nWhy this exists. See also "
        f"[notes](../../../docs/materials/{MONTH}/{STAMP}-carry/notes.md).\n\n#### Detail heading"
    ) in spec
    assert "## 3. Non-Goals\n\n1. **Scope Excluded**: Parsing meaning." in spec
    assert "### Non-Goals" not in spec
    assert (
        "## 4. Acceptance Criteria & Behavioral Contracts\n\n"
        "### Scenario 1 [AC-01]: Carried from proposal\n- **Given** a bundle"
    ) in spec
    assert "\n### Scenario 2 [AC-02]: Carried from proposal\n- **Given** nothing" in spec
    assert "### Expected Acceptance Checks" not in spec
    assert "### Remaining Scope\n\n1. Do the thing." in spec
    assert "### Resume Conditions and Dependencies\n\n- Needs nothing." in spec
    assert "\n---\n\n## Remaining Scope" not in spec

    plan = (spec_dir(workspace, "carry") / "plan.md").read_text(encoding="utf-8")
    assert (
        "### Planned Boundaries:\n- `src/scaffold/`\n- `capabilities/lifecycle/`\n\n"
        "### Excluded Boundaries:\n- `docs/decisions/`\n"
    ) in plan
    tasks = (spec_dir(workspace, "carry") / "tasks.md").read_text(encoding="utf-8")
    assert "  - **_Boundary**: src/scaffold/, capabilities/lifecycle/\n  - _Requirements: AC-01, AC-02_" in tasks
    blueprint = (spec_dir(workspace, "carry") / "target-docs.md").read_text(encoding="utf-8")
    assert "[cap](../../../docs/capabilities/lifecycle/CAP-X.md)" in blueprint
    assert f"{SPEC}-carry/spec.md" in result.rewritten_files
    assert f"{SPEC}-carry/target-docs.md" in result.rewritten_files
    assert result.unresolved == []


def test_rewrites_id_references_and_provenance(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "ref-test", title="Test", with_target_docs=True)
    create_padr(workspace, "ref-test", "Choose parser")
    accept(proposal)
    with proposal.open("a", encoding="utf-8") as handle:
        handle.write("\n[PADR-choose-parser]\n")
    write(
        "docs/consumer.md",
        "---\nid: US-consumer\nspec: SPEC-other\n---\n[PROP-ref-test] [PADR-choose-parser]\n"
        "Historical PROP-ref-test and `[PROP-ref-test]`\n```\n[PADR-choose-parser]\n```\n",
    )
    write("docs/README.md", "# Docs\n[PROP-ref-test]\n")

    result = handoff_proposal(workspace, "ref-test", today=TODAY)

    assert result.unresolved == []
    consumer = (workspace / "docs/consumer.md").read_text(encoding="utf-8")
    assert "`SPEC-ref-test` `ADR-choose-parser`" in consumer
    assert "Historical PROP-ref-test and `[PROP-ref-test]`" in consumer
    assert "```\n[PADR-choose-parser]\n```" in consumer
    assert "`SPEC-ref-test`" in (workspace / "docs/README.md").read_text(encoding="utf-8")
    adr = (workspace / result.decisions[0].path).read_text(encoding="utf-8")
    assert "proposal: SPEC-ref-test" in adr
    assert "spec: SPEC-ref-test" in (spec_dir(workspace, "ref-test") / "plan.md").read_text(encoding="utf-8")
    ids = {(r.path, r.line, r.old, r.new) for r in result.rewritten if r.kind == "id"}
    assert ("docs/consumer.md", 5, "PROP-ref-test", "SPEC-ref-test") in ids
    assert ("docs/consumer.md", 5, "PADR-choose-parser", "ADR-choose-parser") in ids
    assert ("docs/README.md", 2, "PROP-ref-test", "SPEC-ref-test") in ids
    assert not any(path == "docs/consumer.md" and line in (6, 8) for path, line, _, _ in ids)
    assert "SPEC_PROPOSAL_REFS_REWRITTEN" in _codes(result)


def test_carries_the_files_nothing_else_carries(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "relative")
    write("docs/proposals/PROP-relative/decisions/unpromoted.md", "---\nid: PADR-unpromoted\n---\n")
    write("docs/proposals/PROP-relative/notes.md", "# Notes\n[back](proposal.md) [mat](materials/a.md)\n")
    write("docs/proposals/PROP-relative/diagram.png", "png")
    write("docs/proposals/PROP-relative/materials/a.md", "# a\n")
    write("docs/README.md", "[PROP-relative] [PADR-unpromoted] [notes](proposals/PROP-relative/notes.md)\n")
    accept(proposal)

    result = handoff_proposal(workspace, "relative", today=TODAY)

    mat_rel = f"docs/materials/{MONTH}/{STAMP}-relative"
    assert result.materials == mat_rel
    assert (workspace / mat_rel / "decisions/unpromoted.md").is_file()
    assert (workspace / mat_rel / "diagram.png").read_text() == "png"
    assert (workspace / mat_rel / "a.md").is_file()
    notes = (workspace / mat_rel / "notes.md").read_text(encoding="utf-8")
    assert f"[back](../../../../{SPEC}-relative/spec.md) [mat](a.md)" in notes
    readme = (workspace / "docs/README.md").read_text(encoding="utf-8")
    assert "`SPEC-relative`" in readme and "[PADR-unpromoted]" in readme
    assert f"[notes](materials/{MONTH}/{STAMP}-relative/notes.md)" in readme
    assert result.unresolved == []
    assert not proposal.parent.exists()


def test_carried_files_only_need_a_materials_target(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "loose")
    write("docs/proposals/PROP-loose/notes.md", "# Notes\n")
    accept(proposal)
    result = handoff_proposal(workspace, "loose", today=TODAY)
    mat_rel = f"docs/materials/{MONTH}/{STAMP}-loose"
    assert result.materials == mat_rel
    assert (workspace / mat_rel / "notes.md").is_file()


def test_refuses_a_carried_file_that_clashes_with_materials(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "dup")
    write("docs/proposals/PROP-dup/notes.md", "# root\n")
    write("docs/proposals/PROP-dup/materials/notes.md", "# material\n")
    accept(proposal)
    with pytest.raises(ProposalTargetExistsError) as raised:
        handoff_proposal(workspace, "dup", today=TODAY)
    assert raised.value.target_files == ("docs/proposals/PROP-dup/notes.md",)
    assert proposal.is_file() and not (workspace / "specs").exists()


def test_promotes_a_draft_status_with_a_comment(workspace: Path) -> None:
    proposal = _new(workspace, "commented")
    create_padr(workspace, "commented", "Pick One")
    padr = proposal.parent / "decisions/PADR-pick-one.md"
    text = padr.read_text(encoding="utf-8")
    assert "\nstatus: draft\n" in text
    padr.write_text(text.replace("\nstatus: draft\n", "\nstatus: draft  # draft | accepted\n", 1), encoding="utf-8")
    accept(proposal)
    handoff_proposal(workspace, "commented", today=TODAY)
    adr = (workspace / f"docs/decisions/{MONTH}/{STAMP}-pick-one.md").read_text(encoding="utf-8")
    assert "\nstatus: accepted  # draft | accepted\n" in adr


def test_promoted_adrs_keep_working_links(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "adr-links")
    create_padr(workspace, "adr-links", "Pick A")
    create_padr(workspace, "adr-links", "Pick B")
    write("docs/capabilities/x/CAP-X.md", "# cap\n")
    padr = proposal.parent / "decisions/PADR-pick-a.md"
    padr.write_text(
        padr.read_text(encoding="utf-8")
        + "\n[cap](../../../capabilities/x/CAP-X.md) [b](PADR-pick-b.md) [p](../proposal.md)\n"
        "Supersedes `PADR-pick-b`; unrelated to `PADR-elsewhere`.\n",
        encoding="utf-8",
    )
    accept(proposal)

    result = handoff_proposal(workspace, "adr-links", today=TODAY)

    adr = (workspace / f"docs/decisions/{MONTH}/{STAMP}-pick-a.md").read_text(encoding="utf-8")
    assert f"[cap](../../capabilities/x/CAP-X.md) [b]({STAMP}-pick-b.md) [p](../../../{SPEC}-adr-links/spec.md)" in adr
    assert "Supersedes `ADR-pick-b`; unrelated to `PADR-elsewhere`." in adr
    assert result.unresolved == []


def test_leaves_completed_bundles_alone(workspace: Path, write: Write) -> None:
    accept(_new(workspace, "history"))
    refs = "See [PROP-history] and [the proposal](../../../docs/proposals/PROP-history/proposal.md).\n"
    write("specs/2026-09/20260901-done/spec.md", "---\nid: SPEC-done\nstatus: completed\n---\n")
    write("specs/2026-09/20260901-done/reconcile.md", "---\nreconcile_id: REC-done\n---\n" + refs)
    write("specs/2026-09/20260902-active/spec.md", "---\nid: SPEC-active\nstatus: in-progress\n---\n")
    write("specs/2026-09/20260902-active/plan.md", "---\nid: PLAN-active\n---\n" + refs)
    # Feedback stays current after its bundle completes, so its references move with the handoff.
    write("specs/2026-09/20260901-done/feedback/x.md", "---\nid: FB-x\nstatus: open\n---\nSee [PROP-history].\n")

    result = handoff_proposal(workspace, "history", today=TODAY)

    assert refs in (workspace / "specs/2026-09/20260901-done/reconcile.md").read_text(encoding="utf-8")
    feedback = (workspace / "specs/2026-09/20260901-done/feedback/x.md").read_text(encoding="utf-8")
    assert "SPEC-history" in feedback and "PROP-history" not in feedback
    plan = (workspace / "specs/2026-09/20260902-active/plan.md").read_text(encoding="utf-8")
    assert "`SPEC-history`" in plan and "PROP-history" not in plan
    assert [path for path in result.rewritten_files if "20260901-done" in path] == [
        "specs/2026-09/20260901-done/feedback/x.md"
    ]


def _frontmatter_keys(text: str) -> list[str]:
    data = parse(text).data
    assert data is not None
    return list(data)


def test_marks_skeletons(workspace: Path) -> None:
    write_workflow(workspace, "sdd-spec-feature")
    accept(_new(workspace, "marked"))
    result = handoff_proposal(workspace, "marked", today=TODAY)
    target = spec_dir(workspace, "marked")
    for name in ("spec.md", "plan.md", "tasks.md"):
        text = (target / name).read_text(encoding="utf-8")
        lines = text.split("\n")
        closing = lines.index("---", 1)
        assert lines[closing + 1] == SKELETON_MARKER, name
        assert text.count(SKELETON_MARKER) == 1, name
    spec = (target / "spec.md").read_text(encoding="utf-8")
    assert "\nworkflow: sdd-spec-feature\nworkflow_hash: sha256:" in spec
    assert "## 3. Non-Goals\n\n1. **Scope Excluded**: <what this change will not do>\n" in spec
    assert "### [AC-01] <scenario>\n- **Given** <precondition>\n" in spec
    assert _frontmatter_keys((target / "tasks.md").read_text(encoding="utf-8")) == ["id", "spec", "plan"]
    assert _frontmatter_keys((target / "plan.md").read_text(encoding="utf-8")) == ["id", "spec"]
    assert result.workflow == "sdd-spec-feature"
    assert result.next_command == f"devkit workflow next --unit {SPEC}-marked"


def test_binds_the_proposal_workflow(workspace: Path) -> None:
    write_workflow(workspace, "sdd-spec-feature")
    write_workflow(workspace, "sdd-spec-bugfix")
    accept(_new(workspace, "defect"), "\ntask_kind: bugfix")
    result = handoff_proposal(workspace, "defect", today=TODAY)
    spec = (spec_dir(workspace, "defect") / "spec.md").read_text(encoding="utf-8")
    assert "\nworkflow: sdd-spec-bugfix\nworkflow_hash: sha256:" in spec
    assert spec.startswith("---\nid: SPEC-defect\n")
    assert "kind" not in parse(spec).data  # type: ignore[operator]  # the bound workflow is the task-kind
    # sdd-spec-bugfix writes plan.md and tasks.md later; the scope they would carry lands in spec.md's notes.
    assert sorted(path.name for path in spec_dir(workspace, "defect").iterdir()) == ["spec.md"]
    assert (
        "## 5. Carried Proposal Notes" in spec
        and "### Target Area & Boundaries\n\n- Target Area: capabilities/<area>/\n"
        "- Planned Boundaries: `capabilities/<area>/`\n- Excluded Boundaries: `docs/decisions/`\n"
        in spec
    )
    assert "### [AC-01] <scenario>" in spec
    assert result.workflow == "sdd-spec-bugfix" and "SPEC_PROPOSAL_UNBOUND" not in _codes(result)


@pytest.mark.parametrize("definition", [None, WORKFLOW.format(id="sdd-spec-bugfix").replace("schema_version: 1", "")])
def test_an_unbindable_proposal_workflow_writes_nothing(workspace: Path, definition: str | None) -> None:
    write_workflow(workspace, "sdd-spec-feature")
    if definition is not None:
        write_workflow(workspace, "sdd-spec-bugfix", definition)
    proposal = _new(workspace, "defect")
    accept(proposal, "\ntask_kind: bugfix")
    with pytest.raises(ProposalWorkflowError) as raised:
        handoff_proposal(workspace, "defect", today=TODAY)
    assert "bugfix" in raised.value.message
    assert proposal.is_file()
    assert not (workspace / "specs").exists()


def test_the_proposal_units_own_binding_is_not_carried(workspace: Path) -> None:
    write_workflow(workspace, "sdd-spec-feature")
    write_workflow(workspace, "sdd-proposal", INCUBATED)
    proposal = _new(workspace, "unit")
    assert "workflow: sdd-proposal" in proposal.read_text(encoding="utf-8")
    accept(proposal)
    result = handoff_proposal(workspace, "unit", today=TODAY)
    assert result.workflow == "sdd-spec-feature"
    spec = parse((spec_dir(workspace, "unit") / "spec.md").read_text(encoding="utf-8")).data
    assert spec is not None and spec["workflow"] == "sdd-spec-feature" and "kind" not in spec


def test_without_the_default_workflow_the_spec_stays_unbound(workspace: Path) -> None:
    accept(_new(workspace, "unbound"))
    result = handoff_proposal(workspace, "unbound", today=TODAY)
    assert "workflow_hash" not in (spec_dir(workspace, "unbound") / "spec.md").read_text(encoding="utf-8")
    assert result.workflow is None and result.next_command is None
    assert "SPEC_PROPOSAL_UNBOUND" in _codes(result)


def test_refuses_a_slug_a_spec_already_uses(workspace: Path, write: Write) -> None:
    write("specs/2026-09/20260901-demo/spec.md", "---\nid: SPEC-demo\nstatus: completed\n---\n")
    proposal = write(
        "docs/proposals/PROP-demo/proposal.md",
        "---\nid: PROP-demo\ntitle: Demo\nstatus: accepted\n---\n# [PROP-demo] Demo\n",
    )
    with pytest.raises(ProposalSlugConflictError):
        handoff_proposal(workspace, "demo", today=TODAY)
    assert proposal.is_file()
    assert [p.name for p in (workspace / "specs").iterdir()] == ["2026-09"]


def test_refuses_to_overwrite_and_writes_nothing(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "clash")
    create_padr(workspace, "clash", "Taken")
    write("docs/proposals/PROP-clash/materials/a.md", "# a\n")
    accept(proposal)
    existing = write(f"docs/decisions/{MONTH}/{STAMP}-taken.md", "keep\n")
    with pytest.raises(ProposalTargetExistsError) as raised:
        handoff_proposal(workspace, "clash", today=TODAY)
    assert raised.value.target_files == (f"docs/decisions/{MONTH}/{STAMP}-taken.md",)
    assert existing.read_text(encoding="utf-8") == "keep\n"
    assert proposal.is_file() and (proposal.parent / "materials/a.md").is_file()
    assert not (workspace / "specs").exists()


def test_refuses_an_adr_id_another_document_declares(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "twice")
    create_padr(workspace, "twice", "Same")
    accept(proposal)
    write("docs/decisions/2026-01/20260101-same.md", "---\nid: ADR-same\n---\n")
    with pytest.raises(ProposalTargetExistsError):
        handoff_proposal(workspace, "twice", today=TODAY)
    assert proposal.is_file()


def test_a_failed_write_is_rolled_back(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "fails")
    create_padr(workspace, "fails", "Decision")
    write("docs/proposals/PROP-fails/materials/a.md", "# a\n")
    accept(proposal)
    write("docs/decisions", "not a directory\n")  # the ADR cannot be written
    with pytest.raises(ProposalHandoffError):
        handoff_proposal(workspace, "fails", today=TODAY)
    assert not (workspace / "specs" / MONTH).exists()
    assert proposal.is_file() and (proposal.parent / "materials/a.md").is_file()
    assert (proposal.parent / "decisions/PADR-decision.md").is_file()


def _fail_binding(error: Exception) -> Callable[..., None]:
    def write_binding(*_: object) -> None:
        raise error

    return write_binding


@pytest.mark.parametrize(
    ("error", "raised_type"), [(FrontmatterError("bad"), FrontmatterError), (RuntimeError("bug"), ProposalHandoffError)]
)
def test_any_failure_while_writing_is_rolled_back(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch, error: Exception, raised_type: type[Exception]
) -> None:
    write_workflow(workspace, "sdd-spec-feature")
    proposal = _new(workspace, "bind")
    write("docs/proposals/PROP-bind/materials/a.md", "# a\n")
    accept(proposal)
    with monkeypatch.context() as patch:
        patch.setattr("devkit_spec.proposals.specs.write_binding", _fail_binding(error))
        with pytest.raises(raised_type) as raised:
            handoff_proposal(workspace, "bind", today=TODAY)
    # An advisory error keeps its own code; anything else is a handoff failure.
    assert raised.value is error or isinstance(raised.value, ProposalHandoffError)
    assert not (workspace / "specs" / MONTH).exists()
    assert proposal.is_file() and (proposal.parent / "materials/a.md").is_file()
    # Nothing is left behind, so the handoff can be rerun.
    assert handoff_proposal(workspace, "bind", today=TODAY).workflow == "sdd-spec-feature"


def _cross_device(bundle: Path) -> Callable[[object, object], None]:
    """``os.rename`` that fails with ``EXDEV`` for every path in ``bundle``, as across file systems."""
    rename = os.rename

    def fake(source: object, destination: object) -> None:
        if Path(str(source)).is_relative_to(bundle):
            raise OSError(errno.EXDEV, "Invalid cross-device link")
        rename(source, destination)  # type: ignore[arg-type]

    return fake


def test_moves_across_file_systems(workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch) -> None:
    proposal = _new(workspace, "far")
    write("docs/proposals/PROP-far/materials/a.md", "# a\n")
    write("docs/proposals/PROP-far/notes.md", "# notes\n")
    accept(proposal)
    monkeypatch.setattr("devkit_spec.proposals.specs.os.rename", _cross_device(proposal.parent))
    result = handoff_proposal(workspace, "far", today=TODAY)
    preserved = workspace / f"docs/materials/{MONTH}/{STAMP}-far"
    assert result.materials == preserved.relative_to(workspace).as_posix()
    assert (preserved / "a.md").read_text(encoding="utf-8") == "# a\n"
    assert (preserved / "notes.md").is_file()
    assert not proposal.parent.exists()


def test_a_partial_copy_across_file_systems_is_removed(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal = _new(workspace, "partial")
    write("docs/proposals/PROP-partial/materials/a.md", "# a\n")
    write(f"docs/materials/{MONTH}/kept.md", "# kept\n")  # the month directory exists already
    accept(proposal)

    def copytree(source: Path, destination: Path, **_: object) -> None:
        destination.mkdir()
        (destination / "a.md").write_text("# a", encoding="utf-8")
        raise OSError("No space left on device")

    monkeypatch.setattr("devkit_spec.proposals.specs.os.rename", _cross_device(proposal.parent))
    monkeypatch.setattr("devkit_spec.proposals.specs.shutil.copytree", copytree)
    with pytest.raises(ProposalHandoffError):
        handoff_proposal(workspace, "partial", today=TODAY)
    assert sorted(p.name for p in (workspace / f"docs/materials/{MONTH}").iterdir()) == ["kept.md"]
    assert not (workspace / "specs" / MONTH).exists()
    assert (proposal.parent / "materials/a.md").read_text(encoding="utf-8") == "# a\n"


def test_single_file_proposal(workspace: Path, write: Write) -> None:
    write(
        "docs/proposals/PROP-single.md",
        "---\nid: PROP-single\ntitle: Single\nstatus: accepted\ntarget_area: capabilities/x/\n---\n\n"
        "# [PROP-single] Single\n\n## Background\n\nNot carried.\n",
    )
    write("docs/stories/US-a.md", "---\nid: US-a\n---\n[PROP-single] [s](../proposals/PROP-single.md)\n")
    result = handoff_proposal(workspace, "single", today=TODAY)
    spec = (spec_dir(workspace, "single") / "spec.md").read_text(encoding="utf-8")
    assert "Not carried." not in spec and "## 5. Carried Proposal Notes" not in spec
    story = (workspace / "docs/stories/US-a.md").read_text(encoding="utf-8")
    assert f"`SPEC-single` [s](../../{SPEC}-single/spec.md)" in story
    assert not (workspace / "docs/proposals/PROP-single.md").exists()
    assert result.decisions == [] and result.materials is None


@pytest.mark.parametrize("value", ["refactor", "elsewhere/x.md", "[feature]"])
def test_a_task_kind_outside_the_axis_writes_nothing(workspace: Path, value: str) -> None:
    write_workflow(workspace, "sdd-spec-feature")
    proposal = _new(workspace, "odd")
    accept(proposal, f"\ntask_kind: {value}")
    with pytest.raises(ProposalInvalidError) as raised:
        handoff_proposal(workspace, "odd", today=TODAY)
    assert "task_kind" in raised.value.message
    assert proposal.is_file() and not (workspace / "specs").exists()


@pytest.mark.parametrize("field", ["planning_effort", "dev_effort"])
@pytest.mark.parametrize("value", ["extreme", "123", "[low]", "''"])
def test_an_effort_hint_outside_the_axis_writes_nothing(workspace: Path, field: str, value: str) -> None:
    write_workflow(workspace, "sdd-spec-feature")
    proposal = _new(workspace, "bad-effort")
    accept(proposal, f"\n{field}: {value}")
    with pytest.raises(ProposalInvalidError) as raised:
        handoff_proposal(workspace, "bad-effort", today=TODAY)
    assert raised.value.code == "SPEC_PROPOSAL_INVALID"
    assert field in raised.value.message and "low | medium | high" in raised.value.message
    assert proposal.is_file() and not (workspace / "specs").exists()


def test_handoff_returns_dev_effort_and_never_copies_effort_hints_to_spec(workspace: Path, write: Write) -> None:
    proposal = create_proposal(workspace, "with-effort", planning_effort="low", dev_effort="high", today=TODAY)
    accept(workspace / proposal.path)
    result = handoff_proposal(workspace, "with-effort", today=TODAY)
    assert result.dev_effort == "high"
    assert result.to_dict()["dev_effort"] == "high"
    spec_meta = parse((spec_dir(workspace, "with-effort") / "spec.md").read_text(encoding="utf-8")).data
    assert spec_meta is not None
    assert "planning_effort" not in spec_meta and "dev_effort" not in spec_meta

    write(
        "docs/proposals/PROP-legacy/proposal.md",
        "---\nid: PROP-legacy\ntitle: Legacy\nstatus: accepted\n---\n# [PROP-legacy] Legacy\n",
    )
    legacy = handoff_proposal(workspace, "legacy", today=TODAY)
    assert legacy.dev_effort is None and legacy.to_dict()["dev_effort"] is None


def test_refuses_a_legacy_slug_that_starts_with_a_number(workspace: Path, write: Write) -> None:
    write(
        "docs/proposals/PROP-2024-budget.md",
        "---\nid: PROP-2024-budget\ntitle: Budget\nstatus: accepted\n---\n\n# [PROP-2024-budget] Budget\n",
    )
    with pytest.raises(ProposalSlugError) as raised:
        handoff_proposal(workspace, "2024-budget", today=TODAY)
    assert raised.value.code == "SPEC_PROPOSAL_SLUG_INVALID"
    assert raised.value.target_files == ("docs/proposals/PROP-2024-budget.md",)
    assert "Rename PROP-2024-budget" in str(raised.value.advisory.fix)

    proposal = _new(workspace, "cache")
    write("docs/proposals/PROP-cache/decisions/PADR-2024-cache.md", "---\nid: PADR-2024-cache\nstatus: draft\n---\n")
    accept(proposal)
    with pytest.raises(ProposalSlugError) as raised:
        handoff_proposal(workspace, "cache", today=TODAY)
    assert raised.value.target_files == ("docs/proposals/PROP-cache/decisions/PADR-2024-cache.md",)
    assert proposal.is_file() and not (workspace / "specs").exists()


def test_leaves_operating_system_junk_behind(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "junk")
    for path in ("materials/.DS_Store", "materials/sub/Thumbs.db", ".DS_Store", "decisions/desktop.ini"):
        write(f"docs/proposals/PROP-junk/{path}", "junk")
    accept(proposal)
    result = handoff_proposal(workspace, "junk", today=TODAY)
    assert result.materials is None
    assert "Preserved Materials" not in (spec_dir(workspace, "junk") / "spec.md").read_text(encoding="utf-8")
    assert not (workspace / "docs/materials").exists() and not proposal.parent.exists()


def test_carries_other_hidden_files(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "hidden")
    write("docs/proposals/PROP-hidden/.DS_Store", "junk")
    write("docs/proposals/PROP-hidden/.notes", "keep")
    accept(proposal)
    result = handoff_proposal(workspace, "hidden", today=TODAY)
    preserved = workspace / f"docs/materials/{MONTH}/{STAMP}-hidden"
    assert result.materials == preserved.relative_to(workspace).as_posix()
    assert sorted(path.name for path in preserved.iterdir()) == [".notes"]


def test_never_moves_a_file_through_a_symlink_in_materials(
    workspace: Path, write: Write, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    proposal = _new(workspace, "linked")
    (proposal.parent / "materials/sub").symlink_to(outside, target_is_directory=True)
    write("docs/proposals/PROP-linked/sub/x.md", "# x\n")
    accept(proposal)
    with pytest.raises(ProposalTargetExistsError) as raised:
        handoff_proposal(workspace, "linked", today=TODAY)
    assert raised.value.target_files == ("docs/proposals/PROP-linked/sub/x.md",)
    assert list(outside.iterdir()) == [] and not (workspace / "specs").exists()


def test_refuses_a_destination_that_resolves_outside_the_workspace(
    workspace: Path, write: Write, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    (workspace / "docs/materials").mkdir(parents=True)
    (workspace / f"docs/materials/{MONTH}").symlink_to(outside, target_is_directory=True)
    proposal = _new(workspace, "away")
    write("docs/proposals/PROP-away/notes.md", "# notes\n")
    accept(proposal)
    with pytest.raises(ProposalTargetExistsError) as raised:
        handoff_proposal(workspace, "away", today=TODAY)
    assert "outside the workspace" in raised.value.message
    assert list(outside.iterdir()) == [] and not (workspace / "specs").exists()
    assert (proposal.parent / "notes.md").is_file()


def test_refuses_materials_whose_destination_resolves_outside_the_workspace(
    workspace: Path, write: Write, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    (workspace / "docs/materials").mkdir(parents=True)
    (workspace / f"docs/materials/{MONTH}").symlink_to(outside, target_is_directory=True)
    proposal = _new(workspace, "away")
    write("docs/proposals/PROP-away/materials/survey.md", "# survey\n")  # materials/ only, no other file
    accept(proposal)
    with pytest.raises(ProposalTargetExistsError) as raised:
        handoff_proposal(workspace, "away", today=TODAY)
    assert "outside the workspace" in raised.value.message
    assert raised.value.target_files == (f"docs/materials/{MONTH}/{STAMP}-away",)
    assert list(outside.iterdir()) == [] and not (workspace / "specs").exists()
    assert (proposal.parent / "materials/survey.md").is_file() and proposal.is_file()


@pytest.mark.parametrize("decision", [False, True], ids=["spec", "decision"])
def test_refuses_a_spec_or_decision_whose_directory_resolves_outside_the_workspace(
    workspace: Path, tmp_path_factory: pytest.TempPathFactory, decision: bool
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    proposal = _new(workspace, "away")
    if decision:
        create_padr(workspace, "away", "Pick One")
    linked = workspace / (f"docs/decisions/{MONTH}" if decision else f"specs/{MONTH}")
    linked.parent.mkdir(parents=True, exist_ok=True)
    linked.symlink_to(outside, target_is_directory=True)
    accept(proposal)
    with pytest.raises(ProposalTargetExistsError) as raised:
        handoff_proposal(workspace, "away", today=TODAY)
    assert "outside the workspace" in raised.value.message
    assert list(outside.iterdir()) == [] and proposal.is_file()


@pytest.mark.parametrize("inside", [True, False], ids=["inside", "outside"])
def test_never_writes_extras_through_a_symlinked_materials_directory(
    workspace: Path, write: Write, tmp_path_factory: pytest.TempPathFactory, inside: bool
) -> None:
    linked = workspace / "docs/research" if inside else tmp_path_factory.mktemp("outside")
    write("docs/research/keep.md", "# keep\n")
    if not inside:
        (linked / "keep.md").write_text("# keep\n", encoding="utf-8")
    proposal = _new(workspace, "linky")
    shutil.rmtree(proposal.parent / "materials", ignore_errors=True)
    (proposal.parent / "materials").symlink_to(linked, target_is_directory=True)
    write("docs/proposals/PROP-linky/notes.md", "# notes\n")
    accept(proposal)
    with pytest.raises(ProposalTargetExistsError) as raised:
        handoff_proposal(workspace, "linky", today=TODAY)
    assert raised.value.target_files == ("docs/proposals/PROP-linky/notes.md",)
    assert sorted(path.name for path in linked.iterdir()) == ["keep.md"]
    assert not (workspace / "specs").exists() and not (workspace / f"docs/materials/{MONTH}").exists()
    assert (proposal.parent / "materials").is_symlink() and (proposal.parent / "notes.md").is_file()


def _failing_move(fail: Callable[[Path], bool]) -> Callable[..., None]:
    """``move_path`` that raises for the sources ``fail`` selects."""
    move = specs_module.move_path

    def move_path(source: Path, *args: object) -> None:
        if fail(source):
            raise OSError("simulated failure")
        move(source, *args)  # type: ignore[arg-type]

    return move_path


def test_a_roll_back_leaves_no_directory_inside_the_materials(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal = _new(workspace, "prune")
    write("docs/proposals/PROP-prune/materials/a.md", "# a\n")
    write("docs/proposals/PROP-prune/extra/deep/notes.md", "# notes\n")
    write("docs/proposals/PROP-prune/z.md", "# z\n")
    accept(proposal)
    monkeypatch.setattr("devkit_spec.proposals.handoff.move_path", _failing_move(lambda path: path.name == "z.md"))
    with pytest.raises(ProposalHandoffError):
        handoff_proposal(workspace, "prune", today=TODAY)
    bundle = proposal.parent
    assert sorted(p.relative_to(bundle).as_posix() for p in (bundle / "materials").rglob("*")) == ["materials/a.md"]
    assert (bundle / "extra/deep/notes.md").is_file() and (bundle / "z.md").is_file()
    assert not (workspace / "docs/materials").exists() and not (workspace / "specs").exists()


def test_a_roll_back_never_removes_what_it_could_not_move_back(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal = _new(workspace, "stuck")
    write("docs/proposals/PROP-stuck/materials/a.md", "# a\n")
    write("docs/proposals/PROP-stuck/z.md", "# z\n")
    accept(proposal)
    preserved = workspace / f"docs/materials/{MONTH}/{STAMP}-stuck"
    monkeypatch.setattr("devkit_spec.proposals.handoff.move_path", _failing_move(lambda path: path.name == "z.md"))
    move = shutil.move

    def refuse(source: object, destination: object) -> object:
        if Path(str(source)) == preserved:
            raise OSError("simulated failure")
        return move(source, destination)  # type: ignore[arg-type]

    monkeypatch.setattr("devkit_spec.proposals.specs.shutil.move", refuse)
    with pytest.raises(ProposalHandoffError) as raised:
        handoff_proposal(workspace, "stuck", today=TODAY)
    assert "roll-back was incomplete" in raised.value.message
    assert any("could not be moved back" in detail for detail in raised.value.details)
    assert any("was kept" in detail for detail in raised.value.details)
    assert (preserved / "a.md").read_text(encoding="utf-8") == "# a\n"
    assert not (workspace / "specs" / MONTH).exists()


def test_a_roll_back_reports_a_stuck_file_where_a_later_move_back_carried_it(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal = _new(workspace, "carried")
    write("docs/proposals/PROP-carried/materials/a.md", "# a\n")
    write("docs/proposals/PROP-carried/notes.md", "# notes\n")
    write("docs/proposals/PROP-carried/z.md", "# z\n")
    accept(proposal)
    bundle = proposal.parent.resolve()
    preserved = workspace.resolve() / f"docs/materials/{MONTH}/{STAMP}-carried"
    monkeypatch.setattr("devkit_spec.proposals.handoff.move_path", _failing_move(lambda path: path.name == "z.md"))
    move = shutil.move

    def refuse(source: object, destination: object) -> object:
        if Path(str(source)) == preserved / "notes.md":
            raise OSError("simulated failure")
        return move(source, destination)  # type: ignore[arg-type]

    monkeypatch.setattr("devkit_spec.proposals.specs.shutil.move", refuse)
    with pytest.raises(ProposalHandoffError) as raised:
        handoff_proposal(workspace, "carried", today=TODAY)
    assert "roll-back was incomplete" in raised.value.message
    stuck = [detail for detail in raised.value.details if "could not be moved back" in detail]
    assert stuck == [
        f"{bundle / 'materials/notes.md'} could not be moved back to {bundle / 'notes.md'}: simulated failure"
    ]
    assert (bundle / "materials/notes.md").read_text(encoding="utf-8") == "# notes\n", "moving materials/ back took it"
    assert not preserved.exists()


def test_links_into_an_unmoved_materials_directory_stay_unmapped(workspace: Path, write: Write) -> None:
    proposal = _new(workspace, "empty")
    write("docs/proposals/PROP-empty/notes.md", "# notes\n")
    write("docs/README.md", "[foo](proposals/PROP-empty/materials/foo.md)\n")
    accept(proposal)
    result = handoff_proposal(workspace, "empty", today=TODAY)
    assert result.materials == f"docs/materials/{MONTH}/{STAMP}-empty"
    assert (workspace / "docs/README.md").read_text(
        encoding="utf-8"
    ) == "[foo](proposals/PROP-empty/materials/foo.md)\n"
    assert [(u.path, u.target, u.reason) for u in result.unresolved] == [
        ("docs/README.md", "proposals/PROP-empty/materials/foo.md", "unmapped")
    ]


@pytest.mark.parametrize(
    ("status", "promoted"),
    [('"draft"', "accepted"), ("'proposed' # x", "accepted # x"), ('"draft #2"', '"draft #2"'), ("draft#2", "draft#2")],
)
def test_promotes_only_a_draft_status_value(workspace: Path, status: str, promoted: str) -> None:
    proposal = _new(workspace, "quoted")
    create_padr(workspace, "quoted", "Pick One")
    padr = proposal.parent / "decisions/PADR-pick-one.md"
    padr.write_text(padr.read_text(encoding="utf-8").replace("\nstatus: draft\n", f"\nstatus: {status}\n", 1))
    accept(proposal)
    handoff_proposal(workspace, "quoted", today=TODAY)
    adr = (workspace / f"docs/decisions/{MONTH}/{STAMP}-pick-one.md").read_text(encoding="utf-8")
    assert f"\nstatus: {promoted}\n" in adr
