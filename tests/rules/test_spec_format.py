from __future__ import annotations

from datetime import date
from pathlib import Path

from conftest import Write
from devkit.rules import RuleContext, evaluate_rules
from rules.support import found, run

from devkit_spec.rules.spec_format import SpecFormatRule

RULE = SpecFormatRule()
TODAY = date.today().isoformat()


def test_required_frontmatter(workspace: Path, write: Write) -> None:
    write("docs/capabilities/CAP-TEST-alpha.md", "---\nid: CAP-TEST-alpha\ntitle: T\nstatus: active\n---\n# T\n")
    write("docs/capabilities/CAP-TEST-beta.md", "---\nid: CAP-TEST-beta\ntitle: Incomplete\n---\n# Incomplete\n")
    write("docs/capabilities/CAP-TEST-gamma.md", "# Raw markdown without frontmatter\n")
    write("docs/stories/US-blank.md", "---\nid: US-blank\ntitle: ''\nstatus: 3\n---\n")
    write("docs/proposals/x/proposal.md", "---\nid: PROP-x\ntitle: a\ntitle: b\nstatus: draft\n---\n")
    violations = {(v.file, v.message, v.fixable) for v in run(RULE, workspace)}
    malformed = {v for v in violations if v[0] == "docs/proposals/x/proposal.md"}
    assert violations - malformed == {
        ("docs/capabilities/CAP-TEST-beta.md", "frontmatter is missing the required field 'status'", True),
        (
            "docs/capabilities/CAP-TEST-gamma.md",
            "document has no YAML frontmatter block (--- ... --- on the first line)",
            True,
        ),
        ("docs/stories/US-blank.md", "frontmatter is missing the required field 'title'", True),
        ("docs/stories/US-blank.md", "frontmatter field 'status' must be a string", False),
    }
    [(_, message, fixable)] = malformed
    assert message.startswith("frontmatter is malformed: invalid YAML frontmatter") and "duplicate key" in message
    assert not fixable


def test_unclosed_frontmatter(workspace: Path, write: Write) -> None:
    write("docs/stories/US-open.md", "---\nid: US-open\n# Body\n")
    assert found(run(RULE, workspace)) == [
        (
            "docs/stories/US-open.md",
            1,
            "frontmatter is malformed: frontmatter opened with '---' is never closed by a '---' or '...' line",
        )
    ]


def test_only_document_files_in_scope_are_checked(workspace: Path, write: Write) -> None:
    for path in (
        "docs/capabilities/README.md",
        "docs/capabilities/CAP-template.md",
        "docs/capabilities/.drafts/CAP-x.md",
        "docs/proposals/x/materials/notes.md",
        "docs/architecture/ARCH-x.md",
        "specs/2026-10/20261001-x/reconcile.md",
        "template/agents/skills/spec/SKILL.md",
    ):
        write(path, "# no frontmatter\n")
    assert run(RULE, workspace) == []


def test_only_targets_are_reported(workspace: Path, write: Write) -> None:
    files = ["docs/capabilities/CAP-test.md", "specs/test/reconcile.md", "template/agents/skills/spec/SKILL.md"]
    for path in [*files, "docs/stories/US-other.md"]:
        write(path, "# no frontmatter\n")
    assert [file for file, _, _ in found(run(RULE, workspace, *files))] == [files[0]]


def test_fix_adds_frontmatter(workspace: Path, write: Write) -> None:
    beta = write("docs/capabilities/CAP-TEST-beta.md", "---\nid: CAP-TEST-beta\ntitle: Test Cap\n---\n# Test\n")
    gamma = write("docs/capabilities/CAP-TEST-gamma.md", "# [CAP-TEST-gamma] Extracted Title\n\nSome body text\n")

    ctx = RuleContext(workspace_root=workspace, fix=True, dry_run=True)
    result = evaluate_rules(ctx, [RULE])
    assert result.errors == [] and len(found(result.violations)) == 2
    assert "status" not in beta.read_text() and gamma.read_text().startswith("# ")

    fixed = run(RULE, workspace, fix=True)
    assert found(fixed) == [] and len(fixed) == 2 and all(v.fixed for v in fixed)
    assert beta.read_text() == (
        f"---\nid: CAP-TEST-beta\ntitle: Test Cap\nstatus: draft\ncreated_at: {TODAY}\n---\n# Test\n"
    )
    assert gamma.read_text() == (
        f"---\nid: CAP-TEST-gamma\ntitle: Extracted Title\nstatus: draft\ncreated_at: {TODAY}\n---\n\n"
        "# [CAP-TEST-gamma] Extracted Title\n\nSome body text\n"
    )


def test_fix_fills_blank_fields_and_quotes_titles(workspace: Path, write: Write) -> None:
    blank = write(
        "docs/stories/US-x.md", "---\r\nid: US-x\r\ntitle:\r\nstatus: ~  # later\r\ncreated: 2026-01-01\r\n---\r\n"
    )
    colon = write("docs/stories/US-y.md", "# Story: the title\n")
    assert found(run(RULE, workspace, fix=True)) == []
    assert (
        blank.read_bytes().decode()
        == "---\r\nid: US-x\r\ntitle: US-x\r\nstatus: draft\r\ncreated: 2026-01-01\r\n---\r\n"
    )
    assert colon.read_text().startswith('---\nid: US-y\ntitle: "Story: the title"\n')


def test_fix_leaves_accepted_and_malformed_files_alone(workspace: Path, write: Write) -> None:
    texts = {
        "docs/capabilities/CAP-A-ok.md": "---\nid: CAP-A-ok\ntitle: T\nstatus: active\n---\n",
        "docs/capabilities/CAP-A-bad.md": "---\nid: [x\n---\n",
        "docs/capabilities/CAP-A-int.md": "---\nid: CAP-A-int\ntitle: T\nstatus: 1\n---\n",
    }
    for path, text in texts.items():
        write(path, text)
    assert {v.file for v in run(RULE, workspace, fix=True)} == {
        "docs/capabilities/CAP-A-bad.md",
        "docs/capabilities/CAP-A-int.md",
    }
    assert all((workspace / path).read_text() == text for path, text in texts.items())
