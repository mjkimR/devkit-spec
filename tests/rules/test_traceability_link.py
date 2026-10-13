from __future__ import annotations

from pathlib import Path

from conftest import Write
from devkit.rules import RuleContext
from rules.support import found, run

from devkit_spec.rules.traceability_link import TraceabilityLinkRule

RULE = TraceabilityLinkRule()
STORY = "docs/stories/governance/US-test-story.md"
CAP = "docs/capabilities/governance/CAP-TEST-contract.md"


def _doc(document_id: str, header: str = "", status: str = "active") -> str:
    return f"---\nid: {document_id}\nstatus: {status}\n{header}---\n# {document_id}\n"


def _one_sided(write: Write, cap_header: str = "stories: []\n") -> Path:
    write(STORY, _doc("US-test-story", "capabilities:\n  - CAP-TEST-contract\n"))
    write("docs/stories/README.md", "# Stories\n")
    write("docs/stories/delivery/US-other.md", _doc("US-other", "capabilities:\n  - CAP-OTHER-contract\n"))
    write("docs/capabilities/governance/CAP-OTHER-contract.md", _doc("CAP-OTHER-contract", "stories:\n  - US-other\n"))
    return write(CAP, _doc("CAP-TEST-contract", cap_header))


def test_missing_reverse_link_is_reported_and_fixed(workspace: Path, write: Write) -> None:
    cap = _one_sided(write)
    violations = run(RULE, workspace)
    assert found(violations) == [
        (CAP, 1, f"CAP-TEST-contract is missing the reverse story link to US-test-story ({STORY})")
    ]
    assert violations[0].fixable and "US-test-story" in violations[0].remediation

    dry = RuleContext(workspace_root=workspace, fix=True, dry_run=True)
    assert RULE.fix(dry) == [CAP]
    assert "stories: []" in cap.read_text() and len(run(RULE, workspace)) == 1

    fixed = run(RULE, workspace, fix=True)
    assert found(fixed) == [] and all(v.fixed for v in fixed)
    assert "stories: [US-test-story]\n" in cap.read_text()
    assert run(RULE, workspace) == []
    assert run(RULE, workspace, fix=True) == []


def test_missing_reverse_capability_link(workspace: Path, write: Write) -> None:
    write("docs/capabilities/a/CAP-A-one.md", _doc("CAP-A-one", "stories: [US-one, US-two]\n"))
    story = write("docs/stories/a/US-one.md", _doc("US-one", "capabilities:\n  - CAP-A-zero\n"))
    write("docs/stories/a/US-two.md", _doc("US-two"))
    write("docs/capabilities/a/CAP-A-zero.md", _doc("CAP-A-zero", "stories:\n  - US-one\n"))
    assert [(f, m) for f, _, m in found(run(RULE, workspace))] == [
        (
            "docs/stories/a/US-one.md",
            "US-one is missing the reverse capability link to CAP-A-one (docs/capabilities/a/CAP-A-one.md)",
        ),
        (
            "docs/stories/a/US-two.md",
            "US-two is missing the reverse capability link to CAP-A-one (docs/capabilities/a/CAP-A-one.md)",
        ),
    ]
    assert found(run(RULE, workspace, fix=True)) == []
    assert "capabilities:\n  - CAP-A-zero\n  - CAP-A-one\n---" in story.read_text()
    assert "status: active\ncapabilities:\n  - CAP-A-one\n---" in (workspace / "docs/stories/a/US-two.md").read_text()


def test_fix_keeps_list_style(workspace: Path, write: Write) -> None:
    write("docs/stories/a/US-one.md", _doc("US-one", "capabilities: [CAP-A-one]\n"))
    write("docs/stories/a/US-two.md", _doc("US-two", "capabilities: [CAP-A-one]\n"))
    cap = write("docs/capabilities/a/CAP-A-one.md", _doc("CAP-A-one", "stories:\n- 'US-zero'  # first\ntitle: x\n"))
    write("docs/stories/a/US-zero.md", _doc("US-zero", 'capabilities: ["CAP-A-one"]\n'))
    assert found(run(RULE, workspace, fix=True)) == []
    assert "stories:\n- 'US-zero'  # first\n- US-one\n- US-two\ntitle: x\n" in cap.read_text()


def test_exact_ids_only(workspace: Path, write: Write) -> None:
    write("docs/stories/a/US-one.md", _doc("US-one", "capabilities: [CAP-A-one]\n"))
    write("docs/capabilities/a/CAP-A-one.md", _doc("CAP-A-one", "stories: [US-one-extra, docs/stories/a/US-one.md]\n"))
    assert len(found(run(RULE, workspace))) == 1


def test_ambiguous_ids_are_not_fixed(workspace: Path, write: Write) -> None:
    write("docs/stories/test/US-one.md", "---\nid: US-one\ncapabilities: [CAP-TEST-one]\n---\n")
    first = write("docs/capabilities/test/CAP-TEST-one.md", "---\nid: CAP-TEST-one\nstories: []\n---\n")
    second = write("docs/capabilities/other/CAP-TEST-one.md", "---\nid: CAP-TEST-one\nstories: []\n---\n")
    violations = run(RULE, workspace, fix=True)
    assert len(found(violations)) == 2 and not any(v.fixable for v in violations)
    assert "stories: []" in first.read_text() and "stories: []" in second.read_text()


def test_malformed_field_is_not_fixed(workspace: Path, write: Write) -> None:
    write("docs/stories/a/US-one.md", _doc("US-one", "capabilities: [CAP-A-one]\n"))
    cap = write("docs/capabilities/a/CAP-A-one.md", _doc("CAP-A-one", "stories: US-zero\n"))
    violations = run(RULE, workspace, fix=True)
    assert len(found(violations)) == 1 and not violations[0].fixable
    assert "stories: US-zero\n" in cap.read_text()


def test_targeting(workspace: Path, write: Write) -> None:
    cap = _one_sided(write)
    assert found(run(RULE, workspace, CAP)) == [
        (CAP, 1, f"CAP-TEST-contract is missing the reverse story link to US-test-story ({STORY})")
    ]
    # Only the story is targeted: the one-sided link is reported where it is declared, and not fixed there.
    violations = run(RULE, workspace, STORY, fix=True)
    assert found(violations) == [
        (STORY, 5, f"US-test-story links CAP-TEST-contract, but {CAP} does not list US-test-story in stories")
    ]
    assert f"devkit rules fix {CAP}" in violations[0].remediation and not violations[0].fixable
    assert "stories: []" in cap.read_text()
    assert run(RULE, workspace, "docs/capabilities/governance/CAP-OTHER-contract.md") == []


def test_materials_are_skipped(workspace: Path, write: Write) -> None:
    write("docs/stories/materials/US-m.md", _doc("US-m", "capabilities: [CAP-A-one]\n"))
    write("docs/capabilities/a/CAP-A-one.md", _doc("CAP-A-one"))
    assert run(RULE, workspace) == []
