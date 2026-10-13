from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from devkit.cli import cli as devkit_cli
from proposals.support import accept
from scope.support import CAP_A, CAP_PLANNED, SPEC, git, make_repo, write

from devkit_spec.proposals import create_proposal

SPEC_B = "specs/2026-10/20261002-b"


def _scope(root: Path, *args: str) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", "scope", *args, "-w", str(root)])


def _json(result: Result) -> dict:
    return json.loads(result.stdout)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "repo")


@pytest.fixture
def worktrees(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    """Two linked worktrees of ``repo``: ``a`` runs ``SPEC``, ``b`` a bundle that also touches ``src/a``."""
    write(repo, f"{SPEC_B}/spec.md", "---\nid: SPEC-b\nstatus: in-progress\n---\n")
    write(repo, f"{SPEC_B}/tasks.md", "- [ ] **Task 1**: t\n  - **_Boundary**: `src/a/a.py`, `src/c/`\n")
    write(
        repo,
        f"{SPEC_B}/reconcile.md",
        f"---\nreconcile_id: REC-b\nstatus: pending\ntargets:\n  - file: {CAP_A}\n    resolution: modified\n---\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "b")
    a, b = tmp_path / "repo-wt-a", tmp_path / "repo-wt-b"
    git(repo, "worktree", "add", "-q", "-b", "a", str(a))
    git(repo, "worktree", "add", "-q", "-b", "b", str(b))
    return a, b


def test_compare_proposals_and_specs(repo: Path) -> None:
    result = _scope(repo, "compare", "--proposal", "one", "--proposal", "two", "--spec", SPEC)
    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0] == "[PAIR: a=PROP-one b=PROP-two docs=1 code=0 unresolved=3]"
    assert lines[1] == f"[EVIDENCE: {CAP_PLANNED} a=PROP-one b=PROP-two kind=doc granularity=unknown]"
    assert "[PAIR: a=PROP-one b=SPEC-s docs=1 code=2 unresolved=6]" in lines
    assert (
        "[EVIDENCE: src/a a=PROP-one b=SPEC-s kind=code granularity=dir other=src/a source=candidate "
        "other_source=declared-code]"
    ) in lines
    assert "[DIFF: docs/capabilities/x/CAP-X-empty.md set=SPEC-s in=target-docs]" in lines
    assert f"[UNRESOLVED: {CAP_PLANNED} set=PROP-one reason=planned-doc]" in lines
    assert lines[-1] == "[SUMMARY: sets=3 pairs=3 overlapping=3]"
    assert not (repo / ".git/devkit-spec-scope").exists(), "compare never touches the registry"

    data = _json(_scope(repo, "compare", "--proposal", "one", "--spec", SPEC, "--format", "json"))
    assert data["summary"] == {"sets": 2, "pairs": 1, "overlapping": 1}
    assert data["sets"][1]["id"] == "SPEC-s" and data["pairs"][0]["a"] == "PROP-one"


def test_compare_input_errors(repo: Path) -> None:
    one = _scope(repo, "compare", "--proposal", "one", "--format", "json")
    assert one.exit_code == 2 and _json(one)["error"]["code"] == "ARGUMENT_INVALID"
    missing = _scope(repo, "compare", "--proposal", "one", "--proposal", "nope", "--format", "json")
    assert _json(missing)["error"]["code"] == "SPEC_PROPOSAL_NOT_FOUND"
    gone = _scope(repo, "compare", "--proposal", "one", "--spec", "specs/none", "--format", "json")
    assert _json(gone)["error"]["code"] == "SPEC_SCOPE_SPEC_NOT_FOUND"


def test_two_worktrees_register_query_update_release_and_sweep(worktrees: tuple[Path, Path], repo: Path) -> None:
    a, b = worktrees
    first = _scope(a, "register", "--spec", SPEC)
    assert first.exit_code == 0, first.output
    match = re.fullmatch(
        r"\[SCOPE: SPEC-s namespace=(\w{16}) revision=1 scopes=\d+ unresolved=4 shared_path=(\S+) token=(\S+)\]\n",
        first.stdout,
    )
    assert match, first.stdout
    namespace, shared, token = match.groups()
    assert Path(shared) == repo / ".git/devkit-spec-scope"
    second = _scope(b, "register", "--spec", SPEC_B, "--format", "json")
    assert second.exit_code == 0, second.output
    assert _json(second)["namespace"] == namespace and "token_hash" not in _json(second)["record"]

    query = _scope(a, "query")
    assert query.exit_code == 0, query.output
    assert token not in query.stdout, "the token is printed by register only"
    lines = query.stdout.splitlines()
    assert lines[0].startswith(f"[RECORD: SPEC-s revision=1 worktree={a} ") and lines[0].endswith("own=yes]")
    assert lines[1].startswith("[RECORD: SPEC-b revision=1 ") and lines[1].endswith("own=no]")
    assert lines[2] == "[PAIR: a=SPEC-s b=SPEC-b docs=1 code=3 unresolved=4]"
    assert (
        "[EVIDENCE: src/a a=SPEC-s b=SPEC-b kind=code granularity=dir other=src/a/a.py source=declared-code other_source=declared-code]"
        in lines
    )
    assert lines[-1] == f"[SUMMARY: namespace={namespace} records=2 pairs=1 overlapping=1 problems=0]"
    from_base = _scope(repo, "query")
    assert "[PAIR: a=SPEC-b b=SPEC-s docs=1 code=3 unresolved=4]" in from_base.stdout.splitlines()
    planned = _scope(repo, "query", "--spec", SPEC_B)
    assert "[PAIR: a=SPEC-b b=SPEC-s docs=1 code=3 unresolved=4]" in planned.stdout.splitlines()

    write(b, "src/a/a.py", "a = 'b'\n")
    write(b, "src/c/new.py", "c = 1\n")
    update = _scope(b, "update", "--spec", SPEC_B)
    assert update.exit_code == 0, update.output
    ack = update.stdout.splitlines()[-1]
    assert re.fullmatch(
        r"\[SCOPE_ACK: status=applied revision=2 added=2 removed=0 overlaps=1 unresolved=0 request_id=\S+\]", ack
    )
    data = _json(_scope(b, "update", "--spec", SPEC_B, "--format", "json"))
    assert data["ack"]["status"] == "applied" and data["ack"]["revision"] == 3 and data["pairs"][0]["b"] == "SPEC-s"

    released = _scope(a, "release")
    assert released.stdout == "[SCOPE: SPEC-s released=yes registered=yes already=no revision=1]\n"
    assert _scope(a, "release").stdout == "[SCOPE: - released=no registered=no already=no revision=-]\n"

    git(repo, "worktree", "remove", "--force", str(b))
    report = _scope(repo, "sweep")
    assert report.stdout.splitlines() == [
        "[SWEEP: SPEC-b verdict=stale reason=worktree-missing revision=3]",
        f"[SUMMARY: namespace={namespace} active=0 stale=1 unverifiable=0 error=0 removed=0]",
    ]
    moved = _scope(repo, "sweep", "--apply", "--expect", "SPEC-b=2", "--format", "json")
    assert moved.exit_code == 2 and _json(moved)["errors"][0]["code"] == "SPEC_SCOPE_STALE_REVISION"
    assert _json(moved)["results"][0]["reason"] == "stale-revision"
    applied = _scope(repo, "sweep", "--apply")
    assert (
        applied.exit_code == 0
        and "[SWEEP: SPEC-b verdict=removed reason=worktree-missing revision=3]" in applied.stdout
    )

    history = _scope(repo, "query", "--history", "--task", "b")
    events = [line.split()[1] for line in history.stdout.splitlines()[:-1]]
    assert events == ["register", "update", "update", "sweep", "sweep", "sweep"]
    assert history.stdout.splitlines()[-1] == f"[SUMMARY: namespace={namespace} events=6 problems=0]"
    by_id = _json(_scope(repo, "query", "--history", "--task", "SPEC-s", "--format", "json"))
    assert [event["event"] for event in by_id["events"]] == ["register", "release"]


def test_update_failure_prints_the_ack_then_the_error(repo: Path) -> None:
    result = _scope(repo, "update", "--spec", SPEC)
    assert result.exit_code == 2
    assert re.fullmatch(
        r"\[SCOPE_ACK: status=failed revision=0 added=0 removed=0 overlaps=0 unresolved=0 request_id=\S+\]\n",
        result.stdout,
    )
    assert "(SPEC_SCOPE_TOKEN_MISSING)" in result.stderr
    data = _json(_scope(repo, "update", "--spec", SPEC, "--format", "json"))
    assert data["ack"]["status"] == "failed" and data["errors"][0]["code"] == "SPEC_SCOPE_TOKEN_MISSING"


def test_register_errors(repo: Path) -> None:
    missing = _scope(repo, "register", "--format", "json")
    assert _json(missing)["error"]["code"] == "ARGUMENT_INVALID"
    assert _json(_scope(repo, "register", "--spec", "specs/none", "--format", "json"))["error"]["code"] == (
        "SPEC_SCOPE_SPEC_NOT_FOUND"
    )
    assert _scope(repo, "register", "--spec", SPEC).exit_code == 0
    again = _scope(repo, "register", "--spec", SPEC, "--format", "json")
    assert _json(again)["error"]["code"] == "SPEC_SCOPE_TOKEN_EXISTS"


def test_option_errors(repo: Path) -> None:
    assert _json(_scope(repo, "query", "--task", "x", "--format", "json"))["error"]["code"] == "ARGUMENT_INVALID"
    assert _json(_scope(repo, "sweep", "--expect", "x=1", "--format", "json"))["error"]["code"] == "ARGUMENT_INVALID"
    bad = _scope(repo, "sweep", "--apply", "--expect", "x", "--format", "json")
    assert _json(bad)["error"]["code"] == "ARGUMENT_INVALID"
    write(repo, ".devkit/config.toml", "[tool.spec.scope]\ntimeout = 0\n")
    assert _json(_scope(repo, "query", "--format", "json"))["error"]["code"] == "SPEC_CONFIG_INVALID"


def test_outside_git(tmp_path: Path) -> None:
    write(tmp_path, ".devkit/config.toml", "")
    result = _scope(tmp_path, "query", "--format", "json")
    assert result.exit_code == 2 and _json(result)["error"]["code"] == "SPEC_SCOPE_NOT_A_WORKTREE"


def test_history_reports_unreadable_lines(repo: Path) -> None:
    assert _scope(repo, "query", "--history").stdout.splitlines()[-1].endswith("events=0 problems=0]")
    assert _json(_scope(repo, "query", "--history", "--format", "json"))["events"] == []
    _scope(repo, "register", "--spec", SPEC)
    journal = next((repo / ".git/devkit-spec-scope").glob("*/journal.jsonl"))
    with journal.open("a") as handle:
        handle.write("not json\n")
    result = _scope(repo, "query", "--history")
    assert result.exit_code == 0 and result.stdout.splitlines()[-1].endswith("events=1 problems=1]")
    assert "(SPEC_SCOPE_JOURNAL_LINE_INVALID)" in result.stderr
    assert _scope(repo, "query", "--history", "--strict").exit_code == 1


def test_journal_unavailable_keeps_stdout_and_exit(repo: Path) -> None:
    namespace_dir = repo / ".git/devkit-spec-scope"
    register = _scope(repo, "register", "--spec", SPEC)
    journal = next(namespace_dir.glob("*/journal.jsonl"))
    journal.unlink()
    journal.mkdir()
    released = _scope(repo, "release")
    assert released.exit_code == 0 and released.stdout.startswith("[SCOPE: SPEC-s released=yes")
    assert released.stderr.count("(SPEC_SCOPE_JOURNAL_UNAVAILABLE)") == 1
    assert register.exit_code == 0


def test_unreadable_record_is_a_warning(repo: Path) -> None:
    _scope(repo, "register", "--spec", SPEC)
    namespace_dir = next((repo / ".git/devkit-spec-scope").iterdir())
    (namespace_dir / "broken.json").write_text("{")
    result = _scope(repo, "query")
    assert result.exit_code == 0 and result.stdout.splitlines()[-1].endswith("problems=1]")
    assert "(SPEC_SCOPE_RECORD_INVALID)" in result.stderr


def test_handoff_registers_inside_a_linked_worktree(repo: Path, tmp_path: Path) -> None:
    created = create_proposal(repo, "demo")
    accept(repo / created.path)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "proposal")
    linked = tmp_path / "repo-wt-demo"
    git(repo, "worktree", "add", "-q", "-b", "demo", str(linked))
    result = CliRunner().invoke(devkit_cli, ["spec", "proposal", "handoff", "demo", "-w", str(linked)])
    assert result.exit_code == 0, result.output
    scope_lines = [line for line in result.stdout.splitlines() if line.startswith("[SCOPE: ")]
    assert len(scope_lines) == 1 and scope_lines[0].startswith("[SCOPE: SPEC-demo namespace=")
    assert " token=" in scope_lines[0]
    query = _scope(linked, "query")
    assert query.stdout.splitlines()[0].startswith("[RECORD: SPEC-demo revision=1") and "own=yes" in query.stdout
    history = _json(_scope(linked, "query", "--history", "--format", "json"))
    assert history["events"][0]["source"] == "handoff" and history["events"][0]["slug"] == "demo"


def test_handoff_in_the_base_checkout_does_not_register(repo: Path) -> None:
    created = create_proposal(repo, "demo")
    accept(repo / created.path)
    result = CliRunner().invoke(
        devkit_cli, ["spec", "proposal", "handoff", "demo", "-w", str(repo), "--format", "json"]
    )
    assert result.exit_code == 0, result.output
    assert _json(result)["scope"] is None
    assert not (repo / ".git/devkit-spec-scope-token").exists()
