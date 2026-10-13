"""``RULE-document-reference``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from pathlib import Path

from devkit.rules import Violation
from devkit.rules.testing import check, load_rule

RULE = load_rule(__file__)


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def _doc(document_id: str, body: str = "", header: str = "", status: str = "active") -> str:
    return f"---\nid: {document_id}\nstatus: {status}\n{header}---\n{body}"


def test_resolvable_references_pass(tmp_path: Path) -> None:
    files = {
        "docs/a.md": _doc("CAP-A-a", "`US-b`\n", "stories:\n  - US-b\n"),
        "docs/b.md": _doc("US-b", "`CAP-A-a`\n", "capabilities: [CAP-A-a]\n"),
    }
    assert check(RULE, tmp_path, files) == []


def test_reference_problems(tmp_path: Path) -> None:
    files = {"docs/a.md": _doc("CAP-A-a", "`US-none`\n", "stories:\n  - CAP-A-a\n  - docs/b.md\nspec: [x]\n")}
    assert _found(check(RULE, tmp_path, files)) == [
        ("docs/a.md", 7, "spec must be one ID"),
        ("docs/a.md", 5, "stories takes US- IDs, got CAP-A-a"),
        ("docs/a.md", 6, "stories must contain a full document ID, got 'docs/b.md'"),
        ("docs/a.md", 9, "no document has the ID US-none"),
    ]


def test_duplicates_and_shared_proposal_slugs(tmp_path: Path) -> None:
    files = {
        "docs/a.md": _doc("US-dup"),
        "docs/b.md": _doc("US-dup"),
        "docs/proposals/x/proposal.md": _doc("PROP-x"),
        "specs/2026-10/20261001-x/spec.md": _doc("SPEC-x"),
    }
    messages = _found(check(RULE, tmp_path, files))
    assert ("docs/a.md", 1, "US-dup is declared by 2 documents: docs/a.md, docs/b.md") in messages
    assert ("docs/b.md", 1, "US-dup is declared by 2 documents: docs/a.md, docs/b.md") in messages
    assert any(path == "docs/proposals/x/proposal.md" and "shares its slug" in m for path, _, m in messages)


def test_brackets_and_handed_off_proposals_are_fixed(tmp_path: Path) -> None:
    files = {
        "specs/2026-10/20261001-x/spec.md": _doc("SPEC-x", "", "proposal: PROP-x\n"),
        "docs/a.md": _doc("CAP-A-a", "See [SPEC-x] and `PROP-x`, [link](https://x).\n"),
    }
    violations = check(RULE, tmp_path, files)
    assert {(v.message, v.fixable) for v in violations} == {
        ("prose reference SPEC-x must be written `SPEC-x`, not [SPEC-x]", True),
        ("PROP-x was handed off; reference `SPEC-x`", True),
    }
    fixed = check(RULE, tmp_path, fix=True)
    assert _found(fixed) == [] and all(v.fixed for v in fixed)
    assert (tmp_path / "docs/a.md").read_text().endswith("See `SPEC-x` and `SPEC-x`, [link](https://x).\n")
    assert "proposal: PROP-x" in (tmp_path / "specs/2026-10/20261001-x/spec.md").read_text()


def test_internal_path_links_must_be_ids(tmp_path: Path) -> None:
    files = {
        "docs/a/one.md": _doc(
            "CAP-A-one", "[two](../b/two.md) [readme](../b/README.md) [x](../b/two.md#h) ![i](../b/two.md)\n"
        ),
        "docs/b/two.md": _doc("US-two"),
        "docs/b/README.md": "# readme\n",
    }
    assert _found(check(RULE, tmp_path, files)) == [
        ("docs/a/one.md", 5, "internal document link ../b/two.md must be the ID `US-two`")
    ]


def test_history_and_materials_are_skipped_unless_targeted(tmp_path: Path) -> None:
    files = {
        "specs/2026-10/20261001-done/spec.md": _doc("SPEC-done", "`US-gone` [US-x]\n", status="completed"),
        "docs/materials/m.md": _doc("MAT-m", "`US-gone`\n"),
    }
    assert check(RULE, tmp_path, files) == []
    targeted = _found(check(RULE, tmp_path, targets=["specs/2026-10/20261001-done/spec.md"]))
    assert [m for _, _, m in targeted] == ["no document has the ID US-gone", "no document has the ID US-x"]


def test_only_targets_are_reported(tmp_path: Path) -> None:
    files = {"docs/a.md": _doc("CAP-A-a", "`US-none`\n"), "docs/b.md": _doc("CAP-A-b", "`US-none`\n")}
    assert [file for file, _, _ in _found(check(RULE, tmp_path, files, targets=["docs/b.md"]))] == ["docs/b.md"]
