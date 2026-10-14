from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from scope.support import CAP_A, CAP_B, CAP_EMPTY, CAP_PLANNED, GIT_ENV, SPEC, git, make_repo, write

from devkit_spec.errors import ProposalNotFoundError, ScopeInputInvalidError, ScopeSpecNotFoundError
from devkit_spec.scope import (
    Deadline,
    Diff,
    Granularity,
    ScopePath,
    ScopeSet,
    Source,
    Stage,
    compare,
    compare_all,
    from_proposal,
    from_spec,
    observe_git,
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "repo")


def _reasons(scope: ScopeSet) -> dict[str, str]:
    return {item.value: item.reason for item in scope.unresolved}


def test_from_proposal(repo: Path) -> None:
    scope = from_proposal(repo, "one")
    assert scope.id == "PROP-one"
    assert [(item.path, item.kind) for item in scope.docs] == [
        (CAP_A, Granularity.FILE),
        (CAP_EMPTY, Granularity.FILE),
        (CAP_PLANNED, Granularity.UNKNOWN),
        ("docs/decisions/ADR-x.md", Granularity.FILE),
    ]
    assert all(item.stage is Stage.PROP for item in scope.docs)
    assert [(item.path, item.kind, item.source) for item in scope.code] == [
        ("src/a", Granularity.DIR, Source.CANDIDATE),
        ("src/shared.py", Granularity.FILE, Source.CANDIDATE),
    ]
    assert _reasons(scope) == {CAP_EMPTY: "no-entrypoints", CAP_PLANNED: "planned-doc"}
    assert from_proposal(repo, "PROP-one").id == "PROP-one"

    bare = from_proposal(repo, "bare")
    assert bare.docs == [] and _reasons(bare) == {"target-docs.md": "missing-target-docs"}
    write(repo, "docs/proposals/PROP-bare/target-docs.md", "---\nid: PROP-bare-target\n---\n")
    assert _reasons(from_proposal(repo, "bare")) == {"target-docs.md": "no-targets"}
    write(repo, "docs/proposals/PROP-single.md", "---\nid: PROP-single\nstatus: draft\n---\n")
    assert _reasons(from_proposal(repo, "single")) == {"target-docs.md": "missing-target-docs"}
    with pytest.raises(ProposalNotFoundError):
        from_proposal(repo, "nope")


def test_from_spec(repo: Path) -> None:
    scope = from_spec(repo, SPEC)
    assert scope.id == "SPEC-s"
    assert [(item.path, item.stage) for item in scope.docs] == [(CAP_A, Stage.SPEC)]
    assert {item.path: item.source for item in scope.code} == {
        "src/a": Source.DECLARED_CODE,  # declared wins over the candidate of the same path
        "src/b": Source.DECLARED_CODE,
        "src/shared.py": Source.CANDIDATE,
    }
    assert _reasons(scope) == {
        "N/A": "not-a-path",
        "docs/capabilities/": "excluded-tree",
        "src/**": "invalid-path",
        CAP_B: "waived",
    }
    assert scope.diff == [Diff(CAP_EMPTY, "target-docs")]

    write(repo, "specs/2026-10/20261002-n/spec.md", "---\nid: SPEC-n\n---\n")
    write(repo, "specs/2026-10/20261002-n/target-docs.md", f"---\ntargets:\n  - file: {CAP_B}\n---\n")
    planned = from_spec(repo, "specs/2026-10/20261002-n")
    assert [(item.path, item.stage) for item in planned.docs] == [(CAP_B, Stage.PROP)]
    assert _reasons(planned) == {"reconcile.md": "missing-reconcile", "tasks.md": "missing-tasks"}

    with pytest.raises(ScopeSpecNotFoundError):
        from_spec(repo, "specs/2026-10/20261003-missing")
    write(repo, "specs/2026-10/20261002-n/reconcile.md", "---\ntargets: nope\n---\n")
    with pytest.raises(ScopeInputInvalidError):
        from_spec(repo, "specs/2026-10/20261002-n")


def test_observe_git(repo: Path) -> None:
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "src/committed.py", "c = 1\n")
    git(repo, "add", "src/committed.py")
    git(repo, "commit", "-q", "-m", "c")
    write(repo, "src/staged.py", "s = 1\n")
    git(repo, "add", "src/staged.py")
    write(repo, "src/a/a.py", "a = 2\n")
    write(repo, "src/untracked.py", "u = 1\n")
    write(repo, "src/odd[1].py", "o = 1\n")  # outside the path contract: left out
    observed, unresolved = observe_git(repo, base, Deadline(30), "2026-10-13T00:00:00.000000Z")
    assert unresolved == []
    assert [item.path for item in observed] == ["src/a/a.py", "src/committed.py", "src/staged.py", "src/untracked.py"]
    assert {(item.source, item.stage, item.first_seen) for item in observed} == {
        (Source.OBSERVED, Stage.BUILD, "2026-10-13T00:00:00.000000Z")
    }
    assert [item.reason for item in observe_git(repo, "deadbeef", Deadline(30), "")[1]] == ["unknown-base-revision"]
    assert [item.reason for item in observe_git(repo, "", Deadline(30), "")[1]] == ["missing-base-revision"]


def test_observe_git_from_the_fork_point_of_the_base_ref(repo: Path) -> None:
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "switch", "-q", "-c", "task")
    write(repo, "src/a/a.py", "a = 2\n")
    write(repo, "src/shared.py", "s = 'task'\n")
    git(repo, "commit", "-q", "-am", "task")
    git(repo, "switch", "-q", "main")
    write(repo, "src/b/b.py", "b = 2\n")
    write(repo, "src/shared.py", "s = 'main'\n")
    git(repo, "commit", "-q", "-am", "upstream")
    git(repo, "switch", "-q", "task")
    merge = subprocess.run(
        ["git", "merge", "-q", "main"], cwd=repo, env={**os.environ, **GIT_ENV}, capture_output=True, check=False
    )
    assert merge.returncode == 1, "the merge conflicts on src/shared.py"
    write(repo, "src/shared.py", "s = 'resolved'\n")  # the conflict resolution is the task's own change
    git(repo, "commit", "-q", "-am", "merge main")

    observed, unresolved = observe_git(repo, base, Deadline(30), "", base_ref="refs/heads/main")
    assert unresolved == []
    assert [item.path for item in observed] == ["src/a/a.py", "src/shared.py"], "upstream changes are not observed"
    fixed, _ = observe_git(repo, base, Deadline(30), "")
    assert "src/b/b.py" in {item.path for item in fixed}, "without a base ref the range starts at base_revision"
    observed, unresolved = observe_git(repo, base, Deadline(30), "", base_ref="refs/heads/gone")
    assert [(item.value, item.reason) for item in unresolved] == [("refs/heads/gone", "missing-base-ref")]
    assert "src/b/b.py" in {item.path for item in observed}, "an unresolvable base ref falls back to base_revision"


def test_observe_git_registered_after_a_task_commit_skips_a_later_merge_of_the_base_ref(repo: Path) -> None:
    git(repo, "switch", "-q", "-c", "task")
    write(repo, "src/a/a.py", "a = 2\n")
    git(repo, "commit", "-q", "-am", "task")
    base = git(repo, "rev-parse", "HEAD")  # registered after the task's first commit
    git(repo, "switch", "-q", "main")
    write(repo, "src/b/b.py", "b = 2\n")
    git(repo, "commit", "-q", "-am", "upstream")
    git(repo, "switch", "-q", "task")
    git(repo, "merge", "-q", "--no-edit", "main")  # the fork point and base_revision have diverged
    write(repo, "src/shared.py", "s = 'task'\n")
    git(repo, "commit", "-q", "-am", "after the merge")

    observed, unresolved = observe_git(repo, base, Deadline(30), "", base_ref="refs/heads/main")
    assert unresolved == []
    assert [item.path for item in observed] == ["src/shared.py"], "what the task merged in is not observed"
    observed, unresolved = observe_git(repo, "deadbeef", Deadline(30), "", base_ref="refs/heads/main")
    assert [item.reason for item in unresolved] == ["unknown-base-revision"]


@pytest.mark.parametrize("stage", ["committed", "staged", "unstaged"])
def test_observe_git_lists_both_sides_of_a_rename(repo: Path, stage: str) -> None:
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "mv", "src/a/a.py", "src/moved.py")
    if stage == "committed":
        git(repo, "commit", "-q", "-m", "move")
    elif stage == "unstaged":
        git(repo, "reset", "-q")
        git(repo, "add", "-N", "src/moved.py")
    observed, _ = observe_git(repo, base, Deadline(30), "")
    assert {"src/a/a.py", "src/moved.py"} <= {item.path for item in observed}


def test_observe_git_is_relative_to_a_workspace_below_the_top_level(repo: Path) -> None:
    write(repo, "pkg/.devkit/config.toml", "")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "pkg")
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "pkg/src/x.py", "x = 1\n")
    write(repo, "outside.py", "o = 1\n")
    observed, _ = observe_git(repo / "pkg", base, Deadline(30), "")
    assert [item.path for item in observed] == ["src/x.py"]


def test_compare(repo: Path) -> None:
    one, two = from_proposal(repo, "one"), from_proposal(repo, "two")
    result = compare(one, two)
    assert (result.a, result.b) == ("PROP-one", "PROP-two")
    assert [(item.path, item.granularity) for item in result.docs] == [(CAP_PLANNED, Granularity.UNKNOWN)]
    assert result.code == () and result.unresolved == 3

    a = ScopeSet("a", code=[ScopePath("src/a", Granularity.DIR, Source.DECLARED_CODE, Stage.SPEC)])
    b = ScopeSet(
        "b",
        observed=[
            ScopePath("src/a/x.py", Granularity.FILE, Source.OBSERVED, Stage.BUILD),
            ScopePath("src/ab/y.py", Granularity.FILE, Source.OBSERVED, Stage.BUILD),
        ],
    )
    pair = compare(a, b)
    assert [(item.path, item.other, item.granularity, item.source, item.other_source) for item in pair.code] == [
        ("src/a", "src/a/x.py", Granularity.DIR, Source.DECLARED_CODE, Source.OBSERVED)
    ]
    assert pair.overlapping and not compare(b, ScopeSet("c")).overlapping
    assert len(compare_all([one, two, a])) == 3


def test_package_targets_keep_shared_code_candidates(repo: Path) -> None:
    target = "docs/packages/p/capabilities/core/CAP-CORE-shared.md"
    write(repo, target, "---\nid: CAP-CORE-shared\nstatus: active\nentrypoints: [src/shared.py]\n---\n")
    for slug in ("one", "two"):
        write(repo, f"docs/proposals/PROP-{slug}/target-docs.md", f"---\ntargets:\n  - file: {target}\n---\n")
    a, b = from_proposal(repo, "one"), from_proposal(repo, "two")
    assert [item.path for item in a.code] == ["src/shared.py"]
    result = compare(a, b)
    assert len(result.docs) == 1 and len(result.code) == 1 and result.unresolved == 0


def test_from_spec_reads_a_wrapped_boundary(repo: Path) -> None:
    # AC-03: the registry takes the parse of CAP-TRACE-code-entrypoints, continuation lines included.
    base = "specs/2026-10/20261004-w"
    write(repo, f"{base}/spec.md", "---\nid: SPEC-w\n---\n")
    write(repo, f"{base}/tasks.md", "- [ ] t\n  - **_Boundary**: `src/a`,\n    `src/b`,\n    `src/shared.py`\n")
    scope = from_spec(repo, base)
    assert [item.path for item in scope.code if item.source is Source.DECLARED_CODE] == [
        "src/a",
        "src/b",
        "src/shared.py",
    ]
