from __future__ import annotations

from pathlib import Path

from conftest import Write
from rules.support import found, run

from devkit_spec.rules.document_reference import DocumentReferenceRule

RULE = DocumentReferenceRule()


def _doc(document_id: str, body: str = "", header: str = "", status: str = "active") -> str:
    return f"---\nid: {document_id}\nstatus: {status}\n{header}---\n{body}"


def test_resolvable_references_pass(workspace: Path, write: Write) -> None:
    write("docs/a.md", _doc("CAP-A-a", "`US-b`\n", "stories:\n  - US-b\n"))
    write("docs/b.md", _doc("US-b", "`CAP-A-a`\n", "capabilities: [CAP-A-a]\n"))
    assert run(RULE, workspace) == []


def test_reference_problems(workspace: Path, write: Write) -> None:
    write(
        "docs/a.md",
        _doc("CAP-A-a", "`US-none`\n", "stories:\n  - CAP-A-a\n  - docs/b.md\nspec: [x]\n"),
    )
    assert found(run(RULE, workspace)) == [
        ("docs/a.md", 7, "spec must be one ID"),
        ("docs/a.md", 5, "stories takes US- IDs, got CAP-A-a"),
        ("docs/a.md", 6, "stories must contain a full document ID, got 'docs/b.md'"),
        ("docs/a.md", 9, "no document has the ID US-none"),
    ]


def test_duplicates_and_shared_proposal_slugs(workspace: Path, write: Write) -> None:
    write("docs/a.md", _doc("US-dup"))
    write("docs/b.md", _doc("US-dup"))
    write("docs/proposals/x/proposal.md", _doc("PROP-x"))
    write("specs/2026-10/20261001-x/spec.md", _doc("SPEC-x"))
    messages = found(run(RULE, workspace))
    assert ("docs/a.md", 1, "US-dup is declared by 2 documents: docs/a.md, docs/b.md") in messages
    assert ("docs/b.md", 1, "US-dup is declared by 2 documents: docs/a.md, docs/b.md") in messages
    assert any(path == "docs/proposals/x/proposal.md" and "shares its slug" in m for path, _, m in messages)


def test_brackets_and_handed_off_proposals_are_fixed(workspace: Path, write: Write) -> None:
    write("specs/2026-10/20261001-x/spec.md", _doc("SPEC-x", "", "proposal: PROP-x\n"))
    path = write("docs/a.md", _doc("CAP-A-a", "See [SPEC-x] and `PROP-x`, [link](https://x).\n"))
    violations = run(RULE, workspace)
    assert {(v.message, v.fixable) for v in violations} == {
        ("prose reference SPEC-x must be written `SPEC-x`, not [SPEC-x]", True),
        ("PROP-x was handed off; reference `SPEC-x`", True),
    }
    fixed = run(RULE, workspace, fix=True)
    assert found(fixed) == [] and all(v.fixed for v in fixed)
    assert path.read_text().endswith("See `SPEC-x` and `SPEC-x`, [link](https://x).\n")
    assert "proposal: PROP-x" in (workspace / "specs/2026-10/20261001-x/spec.md").read_text()


def test_internal_path_links_must_be_ids(workspace: Path, write: Write) -> None:
    write(
        "docs/a/one.md",
        _doc("CAP-A-one", "[two](../b/two.md) [readme](../b/README.md) [x](../b/two.md#h) ![i](../b/two.md)\n"),
    )
    write("docs/b/two.md", _doc("US-two"))
    write("docs/b/README.md", "# readme\n")
    assert found(run(RULE, workspace)) == [
        ("docs/a/one.md", 5, "internal document link ../b/two.md must be the ID `US-two`")
    ]


def test_history_and_materials_are_skipped_unless_targeted(workspace: Path, write: Write) -> None:
    write("specs/2026-10/20261001-done/spec.md", _doc("SPEC-done", "`US-gone` [US-x]\n", status="completed"))
    write("docs/materials/m.md", _doc("MAT-m", "`US-gone`\n"))
    assert run(RULE, workspace) == []
    targeted = found(run(RULE, workspace, "specs/2026-10/20261001-done/spec.md"))
    assert [m for _, _, m in targeted] == ["no document has the ID US-gone", "no document has the ID US-x"]


def test_only_targets_are_reported(workspace: Path, write: Write) -> None:
    write("docs/a.md", _doc("CAP-A-a", "`US-none`\n"))
    write("docs/b.md", _doc("CAP-A-b", "`US-none`\n"))
    assert [file for file, _, _ in found(run(RULE, workspace, "docs/b.md"))] == ["docs/b.md"]
