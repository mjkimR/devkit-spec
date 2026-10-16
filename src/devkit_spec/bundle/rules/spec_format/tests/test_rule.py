"""``RULE-spec-format``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from devkit.rules import RuleContext, Violation, evaluate_rules
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)
TODAY = date.today().isoformat()
CONFIG = ".devkit/config.toml"


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def _namespaces(*names: str) -> str:
    """``.devkit/config.toml`` registering a namespace per name, with source path ``packages/<name>``."""
    return "".join(f'[[tool.spec.namespaces]]\nname = "{name}"\npath = "packages/{name}"\n\n' for name in names)


def test_required_frontmatter(tmp_path: Path) -> None:
    files = {
        "docs/capabilities/CAP-TEST-alpha.md": "---\nid: CAP-TEST-alpha\ntitle: T\nstatus: active\n---\n# T\n",
        "docs/capabilities/CAP-TEST-beta.md": "---\nid: CAP-TEST-beta\ntitle: Incomplete\n---\n# Incomplete\n",
        "docs/capabilities/CAP-TEST-gamma.md": "# Raw markdown without frontmatter\n",
        "docs/stories/US-blank.md": "---\nid: US-blank\ntitle: ''\nstatus: 3\n---\n",
        "docs/proposals/x/proposal.md": "---\nid: PROP-x\ntitle: a\ntitle: b\nstatus: draft\n---\n",
    }
    violations = {(v.file, v.message, v.fixable) for v in check(RULE, tmp_path, files)}
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


def test_unclosed_frontmatter(tmp_path: Path) -> None:
    assert _found(check(RULE, tmp_path, {"docs/stories/US-open.md": "---\nid: US-open\n# Body\n"})) == [
        (
            "docs/stories/US-open.md",
            1,
            "frontmatter is malformed: frontmatter opened with '---' is never closed by a '---' or '...' line",
        )
    ]


def test_only_document_files_in_scope_are_checked(tmp_path: Path) -> None:
    paths = (
        "docs/capabilities/README.md",
        "docs/capabilities/CAP-template.md",
        "docs/capabilities/.drafts/CAP-x.md",
        "docs/proposals/x/materials/notes.md",
        "docs/architecture/ARCH-x.md",
        "specs/2026-10/20261001-x/reconcile.md",
        "template/agents/skills/spec/SKILL.md",
    )
    assert check(RULE, tmp_path, dict.fromkeys(paths, "# no frontmatter\n")) == []


def test_only_targets_are_reported(tmp_path: Path) -> None:
    targets = ["docs/capabilities/CAP-test.md", "specs/test/reconcile.md", "template/agents/skills/spec/SKILL.md"]
    files = dict.fromkeys([*targets, "docs/stories/US-other.md"], "# no frontmatter\n")
    assert [file for file, _, _ in _found(check(RULE, tmp_path, files, targets=targets))] == [targets[0]]


def test_fix_adds_frontmatter(tmp_path: Path) -> None:
    beta = tmp_path / "docs/capabilities/CAP-TEST-beta.md"
    gamma = tmp_path / "docs/capabilities/CAP-TEST-gamma.md"
    write_files(
        tmp_path,
        {
            "docs/capabilities/CAP-TEST-beta.md": "---\nid: CAP-TEST-beta\ntitle: Test Cap\n---\n# Test\n",
            "docs/capabilities/CAP-TEST-gamma.md": "# [CAP-TEST-gamma] Extracted Title\n\nSome body text\n",
        },
    )

    ctx = RuleContext(workspace_root=tmp_path, fix=True, dry_run=True)
    result = evaluate_rules(ctx, [RULE])
    assert result.errors == [] and len(_found(result.violations)) == 2
    assert "status" not in beta.read_text() and gamma.read_text().startswith("# ")

    fixed = check(RULE, tmp_path, fix=True)
    assert _found(fixed) == [] and len(fixed) == 2 and all(v.fixed for v in fixed)
    assert beta.read_text() == (
        f"---\nid: CAP-TEST-beta\ntitle: Test Cap\nstatus: draft\ncreated_at: {TODAY}\n---\n# Test\n"
    )
    assert gamma.read_text() == (
        f"---\nid: CAP-TEST-gamma\ntitle: Extracted Title\nstatus: draft\ncreated_at: {TODAY}\n---\n\n"
        "# [CAP-TEST-gamma] Extracted Title\n\nSome body text\n"
    )


def test_fix_fills_blank_fields_and_quotes_titles(tmp_path: Path) -> None:
    files = {
        "docs/stories/US-x.md": "---\r\nid: US-x\r\ntitle:\r\nstatus: ~  # later\r\ncreated: 2026-01-01\r\n---\r\n",
        "docs/stories/US-y.md": "# Story: the title\n",
    }
    assert _found(check(RULE, tmp_path, files, fix=True)) == []
    assert (
        tmp_path / "docs/stories/US-x.md"
    ).read_bytes().decode() == "---\r\nid: US-x\r\ntitle: US-x\r\nstatus: draft\r\ncreated: 2026-01-01\r\n---\r\n"
    assert (tmp_path / "docs/stories/US-y.md").read_text().startswith('---\nid: US-y\ntitle: "Story: the title"\n')


def test_fix_leaves_accepted_and_malformed_files_alone(tmp_path: Path) -> None:
    texts = {
        "docs/capabilities/CAP-A-ok.md": "---\nid: CAP-A-ok\ntitle: T\nstatus: active\n---\n",
        "docs/capabilities/CAP-A-bad.md": "---\nid: [x\n---\n",
        "docs/capabilities/CAP-A-int.md": "---\nid: CAP-A-int\ntitle: T\nstatus: 1\n---\n",
    }
    assert {v.file for v in check(RULE, tmp_path, texts, fix=True)} == {
        "docs/capabilities/CAP-A-bad.md",
        "docs/capabilities/CAP-A-int.md",
    }
    assert all((tmp_path / path).read_text() == text for path, text in texts.items())


def test_namespace_docs_roots_are_checked(tmp_path: Path) -> None:
    capability = "docs/packages/api/capabilities/auth/CAP-AUTH-x.md"
    files = {
        CONFIG: _namespaces("api"),
        capability: "# X\n",
        "docs/packages/api/stories/auth/US-x.md": "---\nid: US-x\ntitle: X\n---\n",
        "docs/packages/api/architecture/ARCH-x.md": "# out of scope\n",
        "docs/packages/api/capabilities/auth/materials/notes.md": "# out of scope\n",
        "docs/packages/web/capabilities/CAP-WEB-x.md": "# out of scope\n",
    }
    assert sorted((file, message) for file, _, message in _found(check(RULE, tmp_path, files))) == [
        (capability, "document has no YAML frontmatter block (--- ... --- on the first line)"),
        ("docs/packages/api/stories/auth/US-x.md", "frontmatter is missing the required field 'status'"),
    ]
    assert [
        file for file, _, _ in _found(check(RULE, tmp_path, targets=["docs/packages/api/stories/auth/US-x.md"]))
    ] == ["docs/packages/api/stories/auth/US-x.md"]
    assert _found(check(RULE, tmp_path, fix=True)) == []
    assert (tmp_path / capability).read_text().startswith("---\nid: CAP-AUTH-x\ntitle: X\nstatus: draft\n")


def _anchor(document_id: str, header: str = "") -> str:
    return f"---\nid: {document_id}\ntitle: T\nstatus: draft\n{header}---\n# T\n"


def test_namespace_field_names_global_or_a_registered_namespace(tmp_path: Path) -> None:
    files = {
        CONFIG: _namespaces("api"),
        "docs/proposals/PROP-a/proposal.md": _anchor("PROP-a", "namespace: api\n"),
        "docs/proposals/PROP-b/proposal.md": _anchor("PROP-b", "namespace: global\n"),
        "docs/proposals/PROP-c/proposal.md": _anchor("PROP-c", "namespace: web\n"),
        "docs/proposals/PROP-d/proposal.md": _anchor("PROP-d"),
        "specs/2026-10/20261013-e/spec.md": _anchor("SPEC-e", "namespace: 3\n"),
        "specs/2026-10/20261013-e/plan.md": "---\nid: PLAN-e\nnamespace: web\n---\n",
        "specs/2026-10/20261013-f/spec.md": "---\nid: SPEC-f\ntitle: T\nstatus: completed\nnamespace: web\n---\n",
    }
    violations = check(RULE, tmp_path, files)
    assert _found(violations) == [
        ("docs/proposals/PROP-c/proposal.md", 5, "frontmatter namespace 'web' is not global or a registered namespace"),
        ("specs/2026-10/20261013-e/spec.md", 5, "frontmatter field 'namespace' must be a string"),
    ]
    assert violations[0].remediation.startswith("Set namespace to one of global, api (registered in")
    assert not any(v.fixable for v in violations)
    # A completed spec is work history: checked only when named.
    assert [v.file for v in check(RULE, tmp_path, targets=["specs/2026-10/20261013-f/spec.md"])] == [
        "specs/2026-10/20261013-f/spec.md"
    ]


def test_namespace_fields_are_rechecked_when_the_config_changes(tmp_path: Path) -> None:
    files = {
        CONFIG: _namespaces("api", "web"),
        "docs/proposals/PROP-a/proposal.md": _anchor("PROP-a", "namespace: web\n"),
        "specs/2026-10/20261013-b/spec.md": _anchor("SPEC-b", "namespace: web\n"),
        "specs/2026-10/20261013-c/spec.md": "---\nid: SPEC-c\ntitle: T\nstatus: completed\nnamespace: web\n---\n",
        "docs/stories/US-other.md": _anchor("US-other"),
    }
    assert check(RULE, tmp_path, files, targets=[CONFIG]) == []
    write_files(tmp_path, {CONFIG: _namespaces("api")})
    assert check(RULE, tmp_path, targets=["docs/stories/US-other.md"]) == []
    assert [v.file for v in check(RULE, tmp_path, targets=[CONFIG])] == [
        "docs/proposals/PROP-a/proposal.md",
        "specs/2026-10/20261013-b/spec.md",
    ]
    excluded = RuleContext(workspace_root=tmp_path, changed_files=[CONFIG], exclude=("docs/proposals/**",))
    assert [v.file for v in evaluate_rules(excluded, [RULE]).violations] == ["specs/2026-10/20261013-b/spec.md"]


def test_fix_derives_proposal_bundle_ids(tmp_path: Path) -> None:
    files = {
        "docs/proposals/PROP-fast/proposal.md": "# [PROP-fast] Fast\n",
        "docs/proposals/PROP-fast/target-docs.md": "---\ntitle: Target\nstatus: draft\n---\n",
        "docs/proposals/PROP-fast/decisions/PADR-cache.md": "---\ntitle: Cache\nstatus: draft\n---\n",
        "docs/proposals/PROP-single.md": "---\ntitle: Single\nstatus: draft\n---\n",
    }
    violations = check(RULE, tmp_path, files)
    assert all(v.fixable for v in violations) and len(violations) == 4
    assert _found(check(RULE, tmp_path, fix=True)) == []
    expected = {
        "docs/proposals/PROP-fast/proposal.md": "PROP-fast",
        "docs/proposals/PROP-fast/target-docs.md": "PROP-fast-target",
        "docs/proposals/PROP-fast/decisions/PADR-cache.md": "PADR-cache",
        "docs/proposals/PROP-single.md": "PROP-single",
    }
    for path, document_id in expected.items():
        assert f"\nid: {document_id}\n" in (tmp_path / path).read_text(), path


def test_fix_leaves_an_underivable_id_missing(tmp_path: Path) -> None:
    files = {
        "docs/proposals/PROP-fast/notes.md": "---\ntitle: Notes\nstatus: draft\n---\n",
        "docs/proposals/draft/proposal.md": "# Draft\n",
    }
    violations = check(RULE, tmp_path, files)
    missing = [v for v in violations if v.message == "frontmatter is missing the required field 'id'"]
    assert [v.file for v in missing] == ["docs/proposals/PROP-fast/notes.md"]
    assert not missing[0].fixable and "devkit rules fix" not in missing[0].remediation
    assert (tmp_path / "docs/proposals/PROP-fast/notes.md").read_text() == files["docs/proposals/PROP-fast/notes.md"]
    # The fix writes the other fields of a file without a block, leaving the id to be set by hand.
    assert _found(check(RULE, tmp_path, fix=True)) == [
        ("docs/proposals/PROP-fast/notes.md", 1, "frontmatter is missing the required field 'id'"),
        ("docs/proposals/draft/proposal.md", 1, "frontmatter is missing the required field 'id'"),
    ]
    assert (tmp_path / "docs/proposals/PROP-fast/notes.md").read_text() == files["docs/proposals/PROP-fast/notes.md"]
    assert (tmp_path / "docs/proposals/draft/proposal.md").read_text() == (
        f"---\ntitle: Draft\nstatus: draft\ncreated_at: {TODAY}\n---\n\n# Draft\n"
    )


def test_fix_derives_proposal_feedback_identity(tmp_path: Path) -> None:
    name = "docs/proposals/PROP-review/feedback/observed.md"
    write_files(tmp_path, {name: "---\ntitle: Observed\nstatus: open\n---\n# Observation\n"})
    check(RULE, tmp_path, fix=True)
    assert "id: FB-observed\n" in (tmp_path / name).read_text()
    assert not _found(check(RULE, tmp_path))


def test_new_proposal_feedback_defaults_to_open(tmp_path: Path) -> None:
    name = "docs/proposals/PROP-review/feedback/observed.md"
    write_files(tmp_path, {name: "# Observation\n"})
    check(RULE, tmp_path, fix=True)
    fixed = (tmp_path / name).read_text()
    assert "id: FB-observed" in fixed and "status: open" in fixed


def test_proposal_effort_hints_are_validated(tmp_path: Path) -> None:
    files = {
        "docs/proposals/PROP-ok/proposal.md": _anchor("PROP-ok", "planning_effort: low\ndev_effort: high\n"),
        "docs/proposals/PROP-omitted/proposal.md": _anchor("PROP-omitted"),
        "docs/proposals/PROP-bad/proposal.md": _anchor("PROP-bad", "planning_effort: extreme\ndev_effort: 3\n"),
        "docs/proposals/PROP-single.md": _anchor("PROP-single", "dev_effort: ''\n"),
        "docs/proposals/PROP-ok/target-docs.md": _anchor("PROP-ok-target", "planning_effort: extreme\n"),
        "specs/2026-10/20261013-e/spec.md": _anchor("SPEC-e", "dev_effort: extreme\n"),
    }
    violations = check(RULE, tmp_path, files, fix=True)
    assert _found(violations) == [
        (
            "docs/proposals/PROP-bad/proposal.md",
            5,
            "frontmatter planning_effort 'extreme' is not one of low | medium | high",
        ),
        (
            "docs/proposals/PROP-bad/proposal.md",
            6,
            "frontmatter field 'dev_effort' must be a string (low | medium | high)",
        ),
        ("docs/proposals/PROP-single.md", 5, "frontmatter dev_effort '' is not one of low | medium | high"),
    ]
    assert not any(v.fixable for v in violations)
    assert violations[0].remediation == "Set planning_effort to one of low | medium | high, or remove the field"
