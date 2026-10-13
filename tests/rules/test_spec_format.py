from __future__ import annotations

from datetime import date
from pathlib import Path

from conftest import Write
from devkit.rules import RuleContext, evaluate_rules
from rules.support import found, namespaces_config, run

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


def test_namespace_docs_roots_are_checked(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", namespaces_config("api"))
    capability = write("docs/packages/api/capabilities/auth/CAP-AUTH-x.md", "# X\n")
    write("docs/packages/api/stories/auth/US-x.md", "---\nid: US-x\ntitle: X\n---\n")
    for path in (
        "docs/packages/api/architecture/ARCH-x.md",
        "docs/packages/api/capabilities/auth/materials/notes.md",
        "docs/packages/web/capabilities/CAP-WEB-x.md",
    ):
        write(path, "# out of scope\n")
    assert sorted((file, message) for file, _, message in found(run(RULE, workspace))) == [
        (
            "docs/packages/api/capabilities/auth/CAP-AUTH-x.md",
            "document has no YAML frontmatter block (--- ... --- on the first line)",
        ),
        ("docs/packages/api/stories/auth/US-x.md", "frontmatter is missing the required field 'status'"),
    ]
    assert [file for file, _, _ in found(run(RULE, workspace, "docs/packages/api/stories/auth/US-x.md"))] == [
        "docs/packages/api/stories/auth/US-x.md"
    ]
    assert found(run(RULE, workspace, fix=True)) == []
    assert capability.read_text().startswith("---\nid: CAP-AUTH-x\ntitle: X\nstatus: draft\n")


def _anchor(document_id: str, header: str = "") -> str:
    return f"---\nid: {document_id}\ntitle: T\nstatus: draft\n{header}---\n# T\n"


def test_namespace_field_names_global_or_a_registered_namespace(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", namespaces_config("api"))
    write("docs/proposals/PROP-a/proposal.md", _anchor("PROP-a", "namespace: api\n"))
    write("docs/proposals/PROP-b/proposal.md", _anchor("PROP-b", "namespace: global\n"))
    write("docs/proposals/PROP-c/proposal.md", _anchor("PROP-c", "namespace: web\n"))
    write("docs/proposals/PROP-d/proposal.md", _anchor("PROP-d"))
    write("specs/2026-10/20261013-e/spec.md", _anchor("SPEC-e", "namespace: 3\n"))
    write("specs/2026-10/20261013-e/plan.md", "---\nid: PLAN-e\nnamespace: web\n---\n")
    write("specs/2026-10/20261013-f/spec.md", "---\nid: SPEC-f\ntitle: T\nstatus: completed\nnamespace: web\n---\n")
    violations = run(RULE, workspace)
    assert found(violations) == [
        ("docs/proposals/PROP-c/proposal.md", 5, "frontmatter namespace 'web' is not global or a registered namespace"),
        ("specs/2026-10/20261013-e/spec.md", 5, "frontmatter field 'namespace' must be a string"),
    ]
    assert violations[0].remediation.startswith("Set namespace to one of global, api (registered in")
    assert not any(v.fixable for v in violations)
    # A completed spec is work history: checked only when named.
    assert [v.file for v in run(RULE, workspace, "specs/2026-10/20261013-f/spec.md")] == [
        "specs/2026-10/20261013-f/spec.md"
    ]


def test_namespace_fields_are_rechecked_when_the_config_changes(workspace: Path, write: Write) -> None:
    config = write(".devkit/config.toml", namespaces_config("api", "web"))
    write("docs/proposals/PROP-a/proposal.md", _anchor("PROP-a", "namespace: web\n"))
    write("specs/2026-10/20261013-b/spec.md", _anchor("SPEC-b", "namespace: web\n"))
    write("specs/2026-10/20261013-c/spec.md", "---\nid: SPEC-c\ntitle: T\nstatus: completed\nnamespace: web\n---\n")
    write("docs/stories/US-other.md", _anchor("US-other"))
    assert run(RULE, workspace, ".devkit/config.toml") == []
    config.write_text(namespaces_config("api"), encoding="utf-8")
    assert run(RULE, workspace, "docs/stories/US-other.md") == []
    assert [v.file for v in run(RULE, workspace, ".devkit/config.toml")] == [
        "docs/proposals/PROP-a/proposal.md",
        "specs/2026-10/20261013-b/spec.md",
    ]
    excluded = RuleContext(
        workspace_root=workspace, changed_files=[".devkit/config.toml"], exclude=("docs/proposals/**",)
    )
    assert [v.file for v in evaluate_rules(excluded, [RULE]).violations] == ["specs/2026-10/20261013-b/spec.md"]
