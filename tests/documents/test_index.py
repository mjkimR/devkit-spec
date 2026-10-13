from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import Write

from devkit_spec.documents import DocumentIndex
from devkit_spec.errors import DuplicateIdError, UnresolvedIdError


def _doc(document_id: str, body: str = "", status: str = "active") -> str:
    return f"---\nid: {document_id}\nstatus: {status}\n---\n{body}"


def test_only_documents_under_docs_and_specs_are_indexed(workspace: Path, write: Write) -> None:
    write("docs/a.md", _doc("CAP-A-a"))
    write("specs/2026-10/20261001-b/spec.md", _doc("SPEC-b"))
    for skipped in ("README.md", "x-template.md", "x_template.md", ".hidden/c.md", "notes.txt"):
        write(f"docs/{skipped}", _doc("CAP-A-skipped"))
    write("other/d.md", _doc("CAP-A-d"))
    os.symlink(workspace / "docs/a.md", workspace / "docs/link.md")
    index = DocumentIndex.load(workspace)
    assert [document.path for document in index.documents] == ["docs/a.md", "specs/2026-10/20261001-b/spec.md"]


def test_a_malformed_file_is_a_warning_and_the_rest_is_indexed(workspace: Path, write: Write) -> None:
    write("docs/a.md", _doc("CAP-A-a"))
    write("docs/bad.md", "---\nid: CAP-A-bad\nid: again\n---\n")
    index = DocumentIndex.load(workspace)
    assert [document.id for document in index.documents] == ["CAP-A-a"]
    (problem,) = index.problems
    assert problem.code == "SPEC_DOCUMENT_INVALID" and problem.target_files == ("docs/bad.md",)


def test_resolve(workspace: Path, write: Write) -> None:
    write("docs/a.md", _doc("CAP-A-a"))
    write("docs/b.md", _doc("US-dup"))
    write("docs/c.md", _doc("US-dup"))
    index = DocumentIndex.load(workspace)
    assert index.resolve("CAP-A-a").path == "docs/a.md"
    with pytest.raises(UnresolvedIdError):
        index.resolve("CAP-A-none")
    with pytest.raises(DuplicateIdError) as caught:
        index.resolve("US-dup")
    assert caught.value.target_files == ("docs/b.md", "docs/c.md")


def test_references_in_both_directions(workspace: Path, write: Write) -> None:
    write("docs/a.md", _doc("CAP-A-a", "`US-b` `US-c` [US-b]\n"))
    write("docs/b.md", _doc("US-b", "`CAP-A-a`\n"))
    index = DocumentIndex.load(workspace)
    outgoing = index.outgoing(index.resolve("CAP-A-a"))
    assert {key: len(refs) for key, refs in outgoing.items()} == {"US-b": 2, "US-c": 1}
    assert list(index.incoming("US-b")) == ["CAP-A-a"]
    assert list(index.incoming("CAP-A-a")) == ["US-b"]


def test_files_of_completed_spec_bundles_are_historical(workspace: Path, write: Write) -> None:
    write("specs/2026-10/20261001-done/spec.md", _doc("SPEC-done", status="completed"))
    write("specs/2026-10/20261001-done/plan.md", _doc("PLAN-done"))
    write("specs/2026-10/20261002-open/spec.md", _doc("SPEC-open", status="draft"))
    write("specs/2026-10/feedback/20261003-x.md", _doc("FB-x"))
    index = DocumentIndex.load(workspace)
    assert {document.id: index.is_historical(document) for document in index.documents} == {
        "SPEC-done": True,
        "PLAN-done": True,
        "SPEC-open": False,
        "FB-x": False,
    }
