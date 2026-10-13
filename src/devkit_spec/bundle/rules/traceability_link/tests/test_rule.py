"""``RULE-traceability-link``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from pathlib import Path

from devkit.rules import Autofixable, RuleContext, Violation
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)
STORY = "docs/stories/governance/US-test-story.md"
CAP = "docs/capabilities/governance/CAP-TEST-contract.md"


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def _namespaces(*names: str) -> str:
    """``.devkit/config.toml`` registering a namespace per name, with source path ``packages/<name>``."""
    return "".join(f'[[tool.spec.namespaces]]\nname = "{name}"\npath = "packages/{name}"\n\n' for name in names)


def _doc(document_id: str, header: str = "", status: str = "active") -> str:
    return f"---\nid: {document_id}\nstatus: {status}\n{header}---\n# {document_id}\n"


def _one_sided(root: Path, cap_header: str = "stories: []\n") -> Path:
    write_files(
        root,
        {
            STORY: _doc("US-test-story", "capabilities:\n  - CAP-TEST-contract\n"),
            "docs/stories/README.md": "# Stories\n",
            "docs/stories/delivery/US-other.md": _doc("US-other", "capabilities:\n  - CAP-OTHER-contract\n"),
            "docs/capabilities/governance/CAP-OTHER-contract.md": _doc(
                "CAP-OTHER-contract", "stories:\n  - US-other\n"
            ),
            CAP: _doc("CAP-TEST-contract", cap_header),
        },
    )
    return root / CAP


def test_missing_reverse_link_is_reported_and_fixed(tmp_path: Path) -> None:
    cap = _one_sided(tmp_path)
    violations = check(RULE, tmp_path)
    assert _found(violations) == [
        (CAP, 1, f"CAP-TEST-contract is missing the reverse story link to US-test-story ({STORY})")
    ]
    assert violations[0].fixable and "US-test-story" in violations[0].remediation

    dry = RuleContext(workspace_root=tmp_path, fix=True, dry_run=True)
    assert isinstance(RULE, Autofixable)
    assert RULE.fix(dry) == [CAP]
    assert "stories: []" in cap.read_text() and len(check(RULE, tmp_path)) == 1

    fixed = check(RULE, tmp_path, fix=True)
    assert _found(fixed) == [] and all(v.fixed for v in fixed)
    assert "stories: [US-test-story]\n" in cap.read_text()
    assert check(RULE, tmp_path) == []
    assert check(RULE, tmp_path, fix=True) == []


def test_missing_reverse_capability_link(tmp_path: Path) -> None:
    files = {
        "docs/capabilities/a/CAP-A-one.md": _doc("CAP-A-one", "stories: [US-one, US-two]\n"),
        "docs/stories/a/US-one.md": _doc("US-one", "capabilities:\n  - CAP-A-zero\n"),
        "docs/stories/a/US-two.md": _doc("US-two"),
        "docs/capabilities/a/CAP-A-zero.md": _doc("CAP-A-zero", "stories:\n  - US-one\n"),
    }
    assert [(f, m) for f, _, m in _found(check(RULE, tmp_path, files))] == [
        (
            "docs/stories/a/US-one.md",
            "US-one is missing the reverse capability link to CAP-A-one (docs/capabilities/a/CAP-A-one.md)",
        ),
        (
            "docs/stories/a/US-two.md",
            "US-two is missing the reverse capability link to CAP-A-one (docs/capabilities/a/CAP-A-one.md)",
        ),
    ]
    assert _found(check(RULE, tmp_path, fix=True)) == []
    assert "capabilities:\n  - CAP-A-zero\n  - CAP-A-one\n---" in (tmp_path / "docs/stories/a/US-one.md").read_text()
    assert "status: active\ncapabilities:\n  - CAP-A-one\n---" in (tmp_path / "docs/stories/a/US-two.md").read_text()


def test_fix_keeps_list_style(tmp_path: Path) -> None:
    cap = "docs/capabilities/a/CAP-A-one.md"
    files = {
        "docs/stories/a/US-one.md": _doc("US-one", "capabilities: [CAP-A-one]\n"),
        "docs/stories/a/US-two.md": _doc("US-two", "capabilities: [CAP-A-one]\n"),
        cap: _doc("CAP-A-one", "stories:\n- 'US-zero'  # first\ntitle: x\n"),
        "docs/stories/a/US-zero.md": _doc("US-zero", 'capabilities: ["CAP-A-one"]\n'),
    }
    assert _found(check(RULE, tmp_path, files, fix=True)) == []
    assert "stories:\n- 'US-zero'  # first\n- US-one\n- US-two\ntitle: x\n" in (tmp_path / cap).read_text()


def test_exact_ids_only(tmp_path: Path) -> None:
    files = {
        "docs/stories/a/US-one.md": _doc("US-one", "capabilities: [CAP-A-one]\n"),
        "docs/capabilities/a/CAP-A-one.md": _doc("CAP-A-one", "stories: [US-one-extra, docs/stories/a/US-one.md]\n"),
    }
    assert len(_found(check(RULE, tmp_path, files))) == 1


def test_ambiguous_ids_are_not_fixed(tmp_path: Path) -> None:
    first = "docs/capabilities/test/CAP-TEST-one.md"
    second = "docs/capabilities/other/CAP-TEST-one.md"
    files = {
        "docs/stories/test/US-one.md": "---\nid: US-one\ncapabilities: [CAP-TEST-one]\n---\n",
        first: "---\nid: CAP-TEST-one\nstories: []\n---\n",
        second: "---\nid: CAP-TEST-one\nstories: []\n---\n",
    }
    violations = check(RULE, tmp_path, files, fix=True)
    assert len(_found(violations)) == 2 and not any(v.fixable for v in violations)
    assert "stories: []" in (tmp_path / first).read_text() and "stories: []" in (tmp_path / second).read_text()


def test_malformed_field_is_not_fixed(tmp_path: Path) -> None:
    cap = "docs/capabilities/a/CAP-A-one.md"
    files = {
        "docs/stories/a/US-one.md": _doc("US-one", "capabilities: [CAP-A-one]\n"),
        cap: _doc("CAP-A-one", "stories: US-zero\n"),
    }
    violations = check(RULE, tmp_path, files, fix=True)
    assert len(_found(violations)) == 1 and not violations[0].fixable
    assert "stories: US-zero\n" in (tmp_path / cap).read_text()


def test_targeting(tmp_path: Path) -> None:
    cap = _one_sided(tmp_path)
    assert _found(check(RULE, tmp_path, targets=[CAP])) == [
        (CAP, 1, f"CAP-TEST-contract is missing the reverse story link to US-test-story ({STORY})")
    ]
    # Only the story is targeted: the one-sided link is reported where it is declared, and not fixed there.
    violations = check(RULE, tmp_path, targets=[STORY], fix=True)
    assert _found(violations) == [
        (STORY, 5, f"US-test-story links CAP-TEST-contract, but {CAP} does not list US-test-story in stories")
    ]
    assert f"devkit rules fix {CAP}" in violations[0].remediation and not violations[0].fixable
    assert "stories: []" in cap.read_text()
    assert check(RULE, tmp_path, targets=["docs/capabilities/governance/CAP-OTHER-contract.md"]) == []


def test_materials_are_skipped(tmp_path: Path) -> None:
    files = {
        "docs/stories/materials/US-m.md": _doc("US-m", "capabilities: [CAP-A-one]\n"),
        "docs/capabilities/a/CAP-A-one.md": _doc("CAP-A-one"),
    }
    assert check(RULE, tmp_path, files) == []


def test_namespace_documents_link_like_global_ones(tmp_path: Path) -> None:
    story = "docs/packages/api/stories/auth/US-api-login.md"
    cap = "docs/packages/api/capabilities/auth/CAP-API-login.md"
    files = {
        story: _doc("US-api-login", "capabilities:\n  - CAP-API-login\n  - CAP-TEST-contract\n"),
        cap: _doc("CAP-API-login", "stories: []\n"),
        CAP: _doc("CAP-TEST-contract", "stories: [US-api-login]\n"),
    }
    assert check(RULE, tmp_path, files) == []

    assert _found(check(RULE, tmp_path, {".devkit/config.toml": _namespaces("api")})) == [
        (cap, 1, f"CAP-API-login is missing the reverse story link to US-api-login ({story})")
    ]
    assert _found(check(RULE, tmp_path, fix=True)) == []
    assert "stories: [US-api-login]\n" in (tmp_path / cap).read_text()
