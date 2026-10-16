from __future__ import annotations

from pathlib import Path

import pytest
from conftest import Write
from devkit.advisory import AdvisoryError
from devkit.core.errors import ArgumentError
from devkit.core.frontmatter import parse
from proposals.support import INCUBATED, TODAY, accept, write_workflow

from devkit_spec.errors import (
    ProposalExistsError,
    ProposalNotApprovedError,
    ProposalNotFoundError,
    ProposalSlugConflictError,
    ProposalSlugError,
)
from devkit_spec.proposals import clean_slug, create_padr, create_proposal, create_spec, yaml_scalar


@pytest.mark.parametrize(
    ("raw", "slug"),
    [
        ("fast-engine", "fast-engine"),
        ("PROP-Fast Engine.md", "fast-engine"),
        ("  --a/b__c!!  ", "a-b__c"),
        ("!!!", ""),
    ],
)
def test_clean_slug(raw: str, slug: str) -> None:
    assert clean_slug(raw) == slug


@pytest.mark.parametrize(
    ("value", "scalar"),
    [
        ("plain title", "plain title"),
        ("A: B subtitle", "'A: B subtitle'"),
        ("has # hash", "'has # hash'"),
        ('say "hi"', 'say "hi"'),
        ("yes", "'yes'"),
    ],
)
def test_yaml_scalar_quotes_only_when_needed(value: str, scalar: str) -> None:
    assert yaml_scalar(value) == scalar


def test_create_proposal_bundle(workspace: Path) -> None:
    created = create_proposal(
        workspace,
        "Fast Engine",
        title="Fast: Rule Engine",
        target_area="capabilities/governance",
        milestone="Phase 1: Foundation",
        with_target_docs=True,
        today=TODAY,
    )
    bundle = workspace / "docs/proposals/PROP-fast-engine"
    data = created.to_dict()
    assert {key: data[key] for key in ("id", "dir", "path", "target_docs", "workflow", "next_command")} == {
        "id": "PROP-fast-engine",
        "dir": "docs/proposals/PROP-fast-engine",
        "path": "docs/proposals/PROP-fast-engine/proposal.md",
        "target_docs": "docs/proposals/PROP-fast-engine/target-docs.md",
        "workflow": None,
        "next_command": None,
    }
    assert [notice.code for notice in created.notices] == ["SPEC_PROPOSAL_UNBOUND"]
    assert (bundle / "decisions").is_dir() and (bundle / "materials").is_dir()
    meta = parse((bundle / "proposal.md").read_text(encoding="utf-8")).data
    assert meta is not None
    assert meta["id"] == "PROP-fast-engine"
    assert meta["title"] == "Fast: Rule Engine"
    assert meta["status"] == "draft"
    assert meta["target_area"] == "capabilities/governance/"
    assert meta["milestone"] == "Phase 1: Foundation"
    assert meta["boundaries"] == {"owns": ["capabilities/governance/"], "excludes": ["docs/decisions/"]}
    assert "workflow" not in meta and meta["task_kind"] == "feature"
    assert "supersedes" not in meta and "needs_decompose" not in meta
    target = (bundle / "target-docs.md").read_text(encoding="utf-8")
    assert "id: PROP-fast-engine-target\n" in target
    assert "proposal: PROP-fast-engine\n" in target
    assert "## 5. System Before & After Comparison (Before & After)" in target


def test_create_proposal_writes_the_task_kind_and_close_fields_when_given(workspace: Path) -> None:
    accept(workspace / create_proposal(workspace, "old-fix").path)
    created = create_proposal(workspace, "fix", task_kind="bugfix", supersedes="PROP-old-fix", needs_decompose=True)
    meta = parse((workspace / created.path).read_text(encoding="utf-8")).data
    assert meta is not None and "workflow" not in meta
    assert meta["task_kind"] == "bugfix" and meta["supersedes"] == "PROP-old-fix" and meta["needs_decompose"] is True


def test_create_proposal_supersedes_an_accepted_proposal_only(workspace: Path) -> None:
    with pytest.raises(ProposalNotFoundError) as missing:
        create_proposal(workspace, "fix", supersedes="PROP-old-fix")
    assert missing.value.target_files == ("--supersedes",)
    create_proposal(workspace, "old-fix")
    with pytest.raises(ProposalNotApprovedError) as draft:
        create_proposal(workspace, "fix", supersedes="PROP-old-fix")
    assert draft.value.code == "SPEC_PROPOSAL_NOT_APPROVED" and "draft, not accepted" in str(draft.value)
    assert draft.value.target_files == ("docs/proposals/PROP-old-fix/proposal.md",)
    assert not (workspace / "docs/proposals/PROP-fix").exists()


@pytest.mark.parametrize(
    ("fields", "flag"),
    [
        ({"task_kind": "refactor"}, "--task-kind"),
        ({"supersedes": "old-fix"}, "--supersedes"),
        ({"supersedes": "PROP-fix"}, "--supersedes"),
    ],
)
def test_create_proposal_refuses_values_outside_the_contract(
    workspace: Path, fields: dict[str, str], flag: str
) -> None:
    with pytest.raises(ArgumentError) as raised:
        create_proposal(workspace, "fix", **fields)  # type: ignore[arg-type]
    assert raised.value.target_files == (flag,)
    assert not (workspace / "docs/proposals/PROP-fix").exists()


def test_create_proposal_binds_sdd_proposal(workspace: Path) -> None:
    write_workflow(workspace, "sdd-proposal", INCUBATED)
    created = create_proposal(workspace, "bound")
    meta = parse((workspace / created.path).read_text(encoding="utf-8")).data
    assert meta is not None and meta["workflow"] == "sdd-proposal"
    assert str(meta["workflow_hash"]).startswith("sha256:")
    assert created.workflow == "sdd-proposal" and created.notices == []
    assert created.next_command == "devkit workflow next --unit docs/proposals/PROP-bound"


def test_create_proposal_without_target_docs(workspace: Path) -> None:
    created = create_proposal(workspace, "lean")
    assert created.target_docs is None
    assert not (workspace / "docs/proposals/PROP-lean/target-docs.md").exists()
    meta = parse((workspace / created.path).read_text(encoding="utf-8")).data
    assert meta is not None and meta["title"] == "lean"


def test_create_proposal_refuses_an_existing_proposal(workspace: Path, write: Write) -> None:
    create_proposal(workspace, "dup")
    with pytest.raises(ProposalExistsError):
        create_proposal(workspace, "dup")
    write("docs/proposals/PROP-single.md", "---\nid: PROP-single\n---\n")
    with pytest.raises(ProposalExistsError):
        create_proposal(workspace, "single")


def test_create_proposal_refuses_an_empty_slug(workspace: Path) -> None:
    with pytest.raises(ProposalSlugError) as raised:
        create_proposal(workspace, "--!")
    assert raised.value.code == "SPEC_PROPOSAL_SLUG_INVALID"


def test_new_documents_get_slugs_the_id_convention_accepts(workspace: Path) -> None:
    assert create_proposal(workspace, "fast_engine", today=TODAY).id == "PROP-fast-engine"
    for call in (
        lambda: create_proposal(workspace, "2024-budget", today=TODAY),
        lambda: create_padr(workspace, "fast-engine", "2024 Budget"),
        lambda: create_spec(workspace, "SPEC-20261006-foo", day=TODAY),
    ):
        with pytest.raises(AdvisoryError) as raised:
            call()
        assert raised.value.code in ("SPEC_PROPOSAL_SLUG_INVALID", "SPEC_SLUG_INVALID")
        assert "first segment has no letter" in raised.value.message
    assert not (workspace / "docs/proposals/PROP-2024-budget").exists()


def test_slug_conflicts_with_an_existing_spec(workspace: Path, write: Write) -> None:
    write("specs/2026-09/20260901-demo/spec.md", "---\nid: SPEC-demo\nstatus: completed\n---\n")
    write("docs/capabilities/broken.md", "---\nid: [unterminated\n")  # an unrelated broken document
    with pytest.raises(ProposalSlugConflictError) as raised:
        create_proposal(workspace, "demo")
    assert raised.value.target_files == ("specs/2026-09/20260901-demo/spec.md",)
    assert raised.value.advisory.mode == "INTERACTION"
    assert not (workspace / "docs/proposals/PROP-demo").exists()


def test_a_broken_spec_does_not_block_a_proposal(workspace: Path, write: Write) -> None:
    write("specs/2026-09/20260901-draft/spec.md", "---\nid: [unterminated\n")
    create_proposal(workspace, "fresh")


def test_create_padr(workspace: Path) -> None:
    create_proposal(workspace, "fast-engine")
    created = create_padr(workspace, "fast-engine", "Use Go AST Parser", today=TODAY)
    assert created.to_dict() == {
        "id": "PADR-use-go-ast-parser",
        "path": "docs/proposals/PROP-fast-engine/decisions/PADR-use-go-ast-parser.md",
        "proposal": "PROP-fast-engine",
    }
    text = (workspace / created.path).read_text(encoding="utf-8")
    meta = parse(text).data
    assert meta == {
        "id": "PADR-use-go-ast-parser",
        "title": "Use Go AST Parser",
        "proposal": "PROP-fast-engine",
        "status": "draft",
        "created_at": TODAY,
    }
    assert "# [PADR-use-go-ast-parser] Use Go AST Parser\n" in text
    assert "- **Status**: Draft\n" in text
    with pytest.raises(ProposalExistsError):
        create_padr(workspace, "fast-engine", "use go ast parser")


def test_create_padr_with_an_explicit_slug(workspace: Path) -> None:
    create_proposal(workspace, "plans")
    with pytest.raises(ProposalSlugError) as raised:
        create_padr(workspace, "plans", "2024 roadmap")
    assert raised.value.advisory.fix is not None and "--slug" in raised.value.advisory.fix
    created = create_padr(workspace, "plans", "2024 roadmap", padr_slug="PADR-Roadmap 2024", today=TODAY)
    assert created.id == "PADR-roadmap-2024"
    assert created.path == "docs/proposals/PROP-plans/decisions/PADR-roadmap-2024.md"
    text = (workspace / created.path).read_text(encoding="utf-8")
    assert "title: 2024 roadmap\n" in text and "# [PADR-roadmap-2024] 2024 roadmap\n" in text
    with pytest.raises(ProposalSlugError):
        create_padr(workspace, "plans", "Any", padr_slug="2024-roadmap")


def test_padr_ids_are_unique_across_proposals(workspace: Path) -> None:
    create_proposal(workspace, "first")
    create_proposal(workspace, "second")
    create_padr(workspace, "first", "Same decision")
    with pytest.raises(ProposalExistsError) as raised:
        create_padr(workspace, "second", "Same decision")
    assert raised.value.target_files == ("docs/proposals/PROP-first/decisions/PADR-same-decision.md",)


def test_padr_needs_a_bundle_and_a_title(workspace: Path) -> None:
    with pytest.raises(ProposalNotFoundError):
        create_padr(workspace, "absent", "Title")
    create_proposal(workspace, "there")
    with pytest.raises(ProposalSlugError):
        create_padr(workspace, "there", "?!")
