from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest
from conftest import Write
from proposals.support import MONTH, STAMP, TODAY, accept, spec_dir

from devkit_spec.documents import DocumentIndex
from devkit_spec.errors import ProposalHandoffError, ProposalInvalidError, ProposalTargetExistsError
from devkit_spec.proposals import create_proposal, handoff_proposal
from devkit_spec.proposals import handoff as handoff_module
from devkit_spec.proposals import specs as specs_module


def _feedback(name: str, status: str = "open", body: str = "") -> str:
    return f"---\nid: FB-{name}\ntitle: Observation\nstatus: {status}\ncreated_at: 2026-10-01\n---\n# [FB-{name}] Observation\n{body}"


def _new(root: Path, slug: str = "review") -> Path:
    proposal = root / create_proposal(root, slug, today=TODAY).path
    accept(proposal)
    return proposal.parent


def test_mixed_feedback_follows_status_and_rewrites_links(workspace: Path, write: Write) -> None:
    bundle = _new(workspace)
    for state in ("open", "promoted", "dismissed", "forwarded"):
        write(
            f"{bundle.relative_to(workspace)}/feedback/{state}.md",
            _feedback(state, state, "`PROP-review` [context](../proposal.md)\n"),
        )
    write("docs/reader.md", "[observation](proposals/PROP-review/feedback/open.md)\n")
    result = handoff_proposal(workspace, "review", today=TODAY)
    target = spec_dir(workspace, "review")
    assert sorted(p.name for p in (target / "feedback").iterdir()) == ["open.md"]
    materials = workspace / str(result.materials)
    assert sorted(p.name for p in (materials / "feedback").iterdir()) == ["dismissed.md", "forwarded.md", "promoted.md"]
    content = (target / "feedback/open.md").read_text()
    assert "status: open" in content and "created_at: 2026-10-01" in content
    assert "`SPEC-review`" in content and "[context](../spec.md)" in content
    assert "specs/2026-10/20261013-review/feedback/open.md" in (workspace / "docs/reader.md").read_text()
    assert not bundle.exists() and result.unresolved == []
    assert DocumentIndex.load(workspace).resolve("FB-open").path == f"{result.dir}/feedback/open.md"


def test_only_open_feedback_creates_no_materials(workspace: Path, write: Write) -> None:
    bundle = _new(workspace)
    content = _feedback("only")
    write(f"{bundle.relative_to(workspace)}/feedback/only.md", content)
    result = handoff_proposal(workspace, "review", today=TODAY)
    assert result.materials is None
    assert (spec_dir(workspace, "review") / "feedback/only.md").read_text() == content


@pytest.mark.parametrize(
    "content",
    [
        "---\nid: [broken\n---\n",
        _feedback("other"),
        _feedback("bad", "unknown"),
        _feedback("bad").replace("status: open\n", ""),
        _feedback("bad").replace("title: Observation", "title: []"),
    ],
)
def test_invalid_feedback_refused_before_writes(workspace: Path, write: Write, content: str) -> None:
    bundle = _new(workspace)
    source = write(f"{bundle.relative_to(workspace)}/feedback/bad.md", content)
    with pytest.raises(ProposalInvalidError):
        handoff_proposal(workspace, "review", today=TODAY)
    assert source.read_text() == content
    assert not spec_dir(workspace, "review").exists()
    assert not (workspace / "docs/materials").exists()


@pytest.mark.parametrize("kind", ["directory-link", "file-link", "nested", "dated"])
def test_unsafe_feedback_source_refused(workspace: Path, write: Write, kind: str) -> None:
    bundle = _new(workspace)
    directory = bundle / "feedback"
    if kind == "directory-link":
        outside = write("outside/observation.md", _feedback("observation")).parent
        directory.symlink_to(outside, target_is_directory=True)
    elif kind == "file-link":
        directory.mkdir()
        (directory / "observation.md").symlink_to(write("outside.md", _feedback("observation")))
    else:
        name = "nested/observation" if kind == "nested" else "20261016-observation"
        write(f"{bundle.relative_to(workspace)}/feedback/{name}.md", _feedback("observation"))
    with pytest.raises(ProposalInvalidError):
        handoff_proposal(workspace, "review", today=TODAY)
    assert bundle.exists() and not spec_dir(workspace, "review").exists()


def test_settled_feedback_collision_is_preflight(workspace: Path, write: Write) -> None:
    bundle = _new(workspace)
    rel = bundle.relative_to(workspace)
    write(f"{rel}/feedback/settled.md", _feedback("settled", "dismissed"))
    write(f"{rel}/materials/feedback/settled.md", "existing")
    with pytest.raises(ProposalTargetExistsError):
        handoff_proposal(workspace, "review", today=TODAY)
    assert (bundle / "feedback/settled.md").exists()
    assert not spec_dir(workspace, "review").exists()


@pytest.mark.parametrize("cross_device", [False, True])
def test_failure_after_feedback_move_restores_sources(
    workspace: Path,
    write: Write,
    monkeypatch: pytest.MonkeyPatch,
    cross_device: bool,
) -> None:
    bundle = _new(workspace)
    rel = bundle.relative_to(workspace)
    content = _feedback("open")
    source = write(f"{rel}/feedback/open.md", content)
    write(f"{rel}/notes.md", "notes")
    move = handoff_module.move_path
    rename = os.rename
    if cross_device:

        def exdev(src: object, dst: object) -> None:
            raise OSError(errno.EXDEV, "cross-device")

        monkeypatch.setattr(specs_module.os, "rename", exdev)

    def fail_after_feedback(
        src: Path,
        dst: Path,
        written: list[Path],
        moved: list[tuple[Path, Path]],
        leftovers: list[Path],
    ) -> None:
        if src.name == "notes.md":
            raise OSError("injected after feedback move")
        move(src, dst, written, moved, leftovers)

    monkeypatch.setattr(handoff_module, "move_path", fail_after_feedback)
    with pytest.raises(ProposalHandoffError):
        handoff_proposal(workspace, "review", today=TODAY)
    monkeypatch.setattr(specs_module.os, "rename", rename)
    assert source.read_text() == content and (bundle / "notes.md").read_text() == "notes"
    assert not spec_dir(workspace, "review").exists()
    assert not (workspace / f"docs/materials/{MONTH}/{STAMP}-review").exists()


def test_unreadable_feedback_refused_before_writes(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _new(workspace)
    source = write(f"{bundle.relative_to(workspace)}/feedback/unreadable.md", _feedback("unreadable"))
    read = Path.read_text

    def deny(path: Path, *args: object, **kwargs: object) -> str:
        if path == source:
            raise PermissionError("unreadable feedback")
        return read(path, encoding="utf-8")

    monkeypatch.setattr(Path, "read_text", deny)
    with pytest.raises(ProposalInvalidError):
        handoff_proposal(workspace, "review", today=TODAY)
    assert source.exists() and not spec_dir(workspace, "review").exists()
