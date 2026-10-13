from __future__ import annotations

from pathlib import Path

import pytest
from conftest import Write
from entrypoints.support import BUNDLE, CAP, CAP_TEXT, STORY, STORY_TEXT, documents, fixture

from devkit_spec.entrypoints import Pair, State, apply, collapse, derive, load_bundle, set_entrypoints


def _derive(root: Path) -> list[Pair]:
    pairs, _ = derive(root, load_bundle(root, BUNDLE), documents(root))
    return pairs


def test_apply_writes_only_new_existing_paths_idempotently(workspace: Path, write: Write) -> None:
    fixture(write)
    result = apply(workspace, _derive(workspace))
    assert result.failures == []
    assert [(item.doc, item.added) for item in result.applied] == [
        ("CAP-X-one", ("src/pkg/",)),
        ("US-two", ("src/declared/a.go", "src/pkg/")),
    ]
    assert sum(item.reason == "missing-path" for item in result.skipped) == 2
    assert sum(item.reason == "folded" for item in result.skipped) == 2
    after = (workspace / CAP).read_text()
    assert after == (
        "---\nid: CAP-X-one\ntitle: One\nstatus: active\nentrypoints:\n  - src/declared/\n  - src/pkg/\n"
        "created_at: 2026-10-01\n---\n\n# body\n"
    )
    assert (workspace / STORY).read_text() == (
        "---\nid: US-two\nstatus: active\nentrypoints:\n  - src/declared/a.go\n  - src/pkg/\n---\n"
    )

    pairs = _derive(workspace)
    assert all(pair.state is State.DECLARED for pair in pairs if pair.exists)
    assert apply(workspace, pairs).applied == []
    assert (workspace / CAP).read_text() == after


def test_apply_restricted_to_documents(workspace: Path, write: Write) -> None:
    fixture(write)
    result = apply(workspace, _derive(workspace), {STORY})
    assert [item.doc for item in result.applied] == ["US-two"]
    assert (workspace / CAP).read_text() == CAP_TEXT
    assert (workspace / STORY).read_text() != STORY_TEXT


def test_apply_collapses_directory_and_files(workspace: Path, write: Write) -> None:
    write("docs/capabilities/x/CAP-X.md", "---\nid: CAP-X\n---\n")
    write("src/pkg/a.go", "package a\n")
    pairs = [
        Pair("CAP-X", "docs/capabilities/x/CAP-X.md", "src/pkg/a.go", State.NEW, True),
        Pair("CAP-X", "docs/capabilities/x/CAP-X.md", "src/pkg", State.NEW, True),
    ]
    assert [item.added for item in apply(workspace, pairs).applied] == [("src/pkg/",)]


def test_apply_reports_folded_candidates(workspace: Path, write: Write) -> None:
    write("docs/capabilities/x/CAP-X.md", "---\nid: CAP-X\n---\n")
    write("src/pkg/a.go", "package a\n")
    pair = Pair("CAP-X", "docs/capabilities/x/CAP-X.md", "src/pkg/a.go", State.NEW, True, folded_into="src/pkg")
    result = apply(workspace, [pair])
    assert result.applied == []
    assert [(item.kind, item.value, item.reason) for item in result.skipped] == [("apply", "src/pkg/a.go", "folded")]


def test_apply_collects_failures_and_continues(workspace: Path, write: Write) -> None:
    write("docs/capabilities/x/CAP-X.md", "no frontmatter\n")
    write("docs/capabilities/x/CAP-Y.md", "---\nid: CAP-Y\n---\n")
    write("src/a.go", "package a\n")
    pairs = [
        Pair("CAP-X", "docs/capabilities/x/CAP-X.md", "src/a.go", State.NEW, True),
        Pair("CAP-Y", "docs/capabilities/x/CAP-Y.md", "src/a.go", State.NEW, True),
    ]
    result = apply(workspace, pairs)
    assert [path for path, _ in result.failures] == ["docs/capabilities/x/CAP-X.md"]
    assert [item.doc for item in result.applied] == ["CAP-Y"]


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (
            "---\nid: A\nentrypoints: []\nstories: []\n---\nbody\n",
            "---\nid: A\nentrypoints:\n  - src/a\nstories: []\n---\nbody\n",
        ),
        (
            "---\nid: A\nentrypoints:\n  - old/\n  - older/\nstatus: x\n---\n",
            "---\nid: A\nentrypoints:\n  - src/a\nstatus: x\n---\n",
        ),
        (
            "---\nid: A\nentrypoints:\n- old/\n- older/\nstatus: x\n---\n",
            "---\nid: A\nentrypoints:\n  - src/a\nstatus: x\n---\n",
        ),
        (
            "---\nid: A\nentrypoints: [old/,\n  older/]\nstatus: x\n---\n",
            "---\nid: A\nentrypoints:\n  - src/a\nstatus: x\n---\n",
        ),
        (
            "---\nid: A\ncreated_at: 2026-01-01\n---\n",
            "---\nid: A\nentrypoints:\n  - src/a\ncreated_at: 2026-01-01\n---\n",
        ),
        ("---\nid: A\nstatus: x\n---\n\n# T\n", "---\nid: A\nstatus: x\nentrypoints:\n  - src/a\n---\n\n# T\n"),
        (
            "---\r\nid: A\r\nstatus: x\r\n---\r\nbody\r\n",
            "---\r\nid: A\r\nstatus: x\r\nentrypoints:\r\n  - src/a\r\n---\r\nbody\r\n",
        ),
        ("---\n---\nbody\n", "---\nentrypoints:\n  - src/a\n---\nbody\n"),
    ],
)
def test_set_entrypoints(before: str, after: str) -> None:
    assert set_entrypoints(before, ["src/a"]) == after


def test_set_entrypoints_quotes_dedupes_and_empties() -> None:
    assert set_entrypoints("---\nid: A\n---\n", ["src/space dir/", "src/space dir/", "yes"]) == (
        "---\nid: A\nentrypoints:\n  - src/space dir/\n  - 'yes'\n---\n"
    )
    assert set_entrypoints("---\nid: A\nentrypoints:\n  - a\n---\n", []) == "---\nid: A\nentrypoints: []\n---\n"
    with pytest.raises(ValueError):
        set_entrypoints("no frontmatter", ["x"])


def test_collapse() -> None:
    assert collapse(["src/"], ["cli/workflow/", "cli/workflow/a.go", "src/b.go"]) == ["cli/workflow/"]
    assert collapse([], ["src/b.go"]) == ["src/b.go"]
