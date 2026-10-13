from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from conftest import Write
from entrypoints.support import BUNDLE, CAP, documents, fixture

from devkit_spec.entrypoints import (
    Pair,
    State,
    Target,
    aggregate,
    classify_boundary,
    covers,
    derive,
    entrypoint_bearing,
    exclude,
    load_bundle,
    normalize,
    overlaps,
    parse_boundaries,
    select,
)
from devkit_spec.errors import EntrypointsInputInvalidError, EntrypointsInputMissingError, EntrypointsPathError


def _find(pairs: list[Pair], doc: str, code: str) -> Pair | None:
    return next((pair for pair in pairs if pair.doc == doc and pair.code == code), None)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("src/", "src"), ("./src/main.go", "src/main.go"), (".", "."), ("a//b/./c", "a/b/c"), ("src dir/", "src dir")],
)
def test_normalize(value: str, expected: str) -> None:
    assert normalize(value) == expected


@pytest.mark.parametrize("value", ["", "  ", "/src", "../src", "a/../b", "src/*", "a?b", "[x]", "C:x", "a\\b", "a\nb"])
def test_normalize_rejects(value: str) -> None:
    with pytest.raises(EntrypointsPathError) as raised:
        normalize(value)
    assert raised.value.code == "SPEC_ENTRYPOINTS_PATH_INVALID"


def test_covers_and_overlaps_compare_whole_segments() -> None:
    assert covers("src", "src/a.py") and covers(".", "x") and covers("src", "src")
    assert not covers("src/a", "src/ab")
    assert overlaps("src/", "src/a/b.py") and overlaps("src/a/b.py", "./src") and not overlaps("src/*", "src")


def test_entrypoint_bearing() -> None:
    assert entrypoint_bearing("docs/capabilities/x/CAP-X-a.md")
    assert entrypoint_bearing("docs/stories/x/US-a.md")
    assert entrypoint_bearing("docs/packages/api/capabilities/core/CAP-CORE-a.md")
    assert not entrypoint_bearing("docs/decisions/ADR-x.md")
    assert not entrypoint_bearing("docs/packages/api/decisions/ADR-x.md")
    assert not entrypoint_bearing("docs/capabilities/x/notes.txt")


def test_load_bundle_parses_boundaries(workspace: Path, write: Write) -> None:
    fixture(write)
    bundle = load_bundle(workspace, BUNDLE)
    assert (bundle.spec_id, bundle.status) == ("SPEC-one", "completed")
    assert len(bundle.targets) == 4
    assert [task.values for task in bundle.tasks] == [
        ["src/pkg/", "src/pkg/sub/c.go", "src/declared/a.go"],
        ["docs/capabilities/", "N/A", "src/**/*.go", "src/missing.go"],
    ]
    assert [task.title for task in bundle.tasks] == ["**Task 1**: engine", "**Task 2**: docs"]


def test_load_bundle_errors(workspace: Path, write: Write) -> None:
    with pytest.raises(EntrypointsInputMissingError) as missing:
        load_bundle(workspace, "specs/2026-10/missing")
    assert missing.value.target_files == ("specs/2026-10/missing/tasks.md",)
    write("specs/2026-10/20261002-bad/tasks.md", "- [ ] t\n")
    with pytest.raises(EntrypointsInputMissingError):
        load_bundle(workspace, "specs/2026-10/20261002-bad")
    for text in ("no frontmatter\n", "---\ntargets: [\n---\n", "---\ntargets: x\n---\n", "---\ntargets: [x]\n---\n"):
        write("specs/2026-10/20261002-bad/reconcile.md", text)
        with pytest.raises(EntrypointsInputInvalidError):
            load_bundle(workspace, "specs/2026-10/20261002-bad")
    write("specs/2026-10/20261002-bad/reconcile.md", "---\nreconcile_id: REC-bad\n---\n")
    bundle = load_bundle(workspace, "specs/2026-10/20261002-bad")
    assert (bundle.spec_id, bundle.targets) == ("20261002-bad", ())


def test_parse_boundaries_keeps_globs_and_strips_only_wrapping_bold() -> None:
    tasks = parse_boundaries("- [ ] t\n  - **_Boundary**: **src/a/**, src/**, `src/b/` (note), **src/c/**, N/A\n")
    assert [task.values for task in tasks] == [["src/a/", "src/**", "src/b/", "src/c/", "N/A"]]
    assert classify_boundary("src/**") == (None, "invalid-path")
    before = parse_boundaries("_Boundary: src/x\n- [ ] t\n")
    assert [(task.index, task.values) for task in before] == [(0, ["src/x"]), (1, [])]


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("", "not-a-path"),
        ("N/A", "not-a-path"),
        ("None", "not-a-path"),
        (".", "excluded-tree"),
        ("docs", "excluded-tree"),
    ],
)
def test_classify_boundary_skips(raw: str, reason: str) -> None:
    assert classify_boundary(raw) == (None, reason)


def test_derive_states_folding_and_skips(workspace: Path, write: Write) -> None:
    fixture(write)
    pairs, skipped = derive(workspace, load_bundle(workspace, BUNDLE), documents(workspace))
    # 2 bearing documents x 4 candidates (src/pkg, src/pkg/sub/c.go, src/declared/a.go, src/missing.go)
    assert len(pairs) == 8
    declared = _find(pairs, "CAP-X-one", "src/declared/a.go")
    assert declared is not None
    assert (declared.state, declared.exists, declared.task, declared.spec) == (State.DECLARED, True, 1, "SPEC-one")
    new = _find(pairs, "US-two", "src/pkg")
    assert new is not None and new.state is State.NEW and new.folded_into is None
    folded = _find(pairs, "US-two", "src/pkg/sub/c.go")
    assert folded is not None and folded.folded_into == "src/pkg"
    missing = _find(pairs, "CAP-X-one", "src/missing.go")
    assert missing is not None and not missing.exists and missing.task == 2
    assert {item.value: str(item.reason) for item in skipped} == {
        "docs/decisions/ADR-x.md": "not-entrypoint-bearing",
        "docs/capabilities/x/CAP-X-gone.md": "waived",
        "docs/capabilities/": "excluded-tree",
        "N/A": "not-a-path",
        "src/**/*.go": "invalid-path",
    }
    assert _find(pairs, "CAP-X-one", "src/fenced") is None
    assert [pair.doc_path for pair in pairs] == sorted(pair.doc_path for pair in pairs)


def test_derive_reports_targets_that_are_not_documents(workspace: Path, write: Write) -> None:
    fixture(write)
    write("docs/capabilities/x/CAP-X-noid.md", "---\ntitle: no id\n---\n")
    bundle = load_bundle(workspace, BUNDLE)
    targets = (
        Target("docs/capabilities/x/CAP-X-noid.md", "modified"),
        Target("docs/capabilities/x/CAP-X-absent.md", "modified"),
        Target(f"./{CAP}", "modified"),
        Target(CAP, "modified"),
    )
    pairs, skipped = derive(workspace, replace(bundle, targets=targets), documents(workspace))
    assert [(item.value, str(item.reason)) for item in skipped if item.kind == "target"] == [
        ("docs/capabilities/x/CAP-X-noid.md", "not-a-document"),
        ("docs/capabilities/x/CAP-X-absent.md", "missing-doc"),
    ]
    assert {pair.doc_path for pair in pairs} == {CAP}


def test_package_targets_carry_entrypoints(workspace: Path, write: Write) -> None:
    fixture(write)
    target = "docs/packages/a/capabilities/core/CAP-CORE-alpha.md"
    write(target, "---\nid: CAP-CORE-alpha\nstatus: active\n---\n")
    bundle = load_bundle(workspace, BUNDLE)
    bundle = replace(bundle, targets=(Target(target, "modified"),))
    pairs, _ = derive(workspace, bundle, documents(workspace))
    assert pairs[0].doc_path == target
    assert _find(pairs, "CAP-CORE-alpha", "src/pkg") is not None


def _pair(code: str, spec: str, **fields: object) -> Pair:
    defaults: dict[str, object] = {"doc": "D", "doc_path": "docs/capabilities/x/D.md", "state": State.NEW}
    return Pair(code=code, spec=spec, exists=True, **(defaults | fields))  # type: ignore[arg-type]


def test_aggregate_counts_specs_and_min_count() -> None:
    first = [_pair("src/a", "SPEC-1", task=1), _pair("src/a/x.go", "SPEC-1", folded_into="src/a")]
    second = [_pair("src/a", "SPEC-2", task=3), _pair("src/b", "SPEC-2")]
    merged = aggregate([first, second], 1)
    assert [(pair.code, pair.count, pair.specs, pair.spec, pair.task) for pair in merged] == [
        ("src/a", 2, ("SPEC-1", "SPEC-2"), None, None),
        ("src/b", 1, ("SPEC-2",), None, None),
    ]
    assert [pair.code for pair in aggregate([first, second], 2)] == ["src/a"]
    assert merged[0].to_dict() == {
        "doc": "D",
        "doc_path": "docs/capabilities/x/D.md",
        "code": "src/a",
        "count": 2,
        "specs": ["SPEC-1", "SPEC-2"],
        "state": "new",
        "exists": True,
    }


def test_exclude_and_select() -> None:
    pairs = [
        _pair("AGENTS.md", "S"),
        _pair("cli/workflow/a.go", "S"),
        _pair("cli/workflow/a_test.go", "S"),
        _pair("template/x", "S"),
    ]
    kept, skipped = exclude(pairs, ["AGENTS.md", "cli/workflow/a_test.go"])
    assert [pair.code for pair in kept] == ["cli/workflow/a.go", "template/x"]
    assert [(item.value, str(item.reason), str(item.kind)) for item in skipped] == [
        ("AGENTS.md", "excluded", "boundary"),
        ("cli/workflow/a_test.go", "excluded", "boundary"),
    ]
    assert len(select(pairs, ["cli/workflow/"])) == 2
    assert len(select(pairs, [])) == 4
    with pytest.raises(EntrypointsPathError):
        exclude(pairs, ["../x"])
    with pytest.raises(EntrypointsPathError):
        select(pairs, ["src/*"])
