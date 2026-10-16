from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from conftest import Write
from devkit.cli import cli as devkit_cli


def _doc(document_id: str, body: str = "", **fields: str) -> str:
    header = "".join(f"{key}: {value}\n" for key, value in fields.items())
    return f"---\nid: {document_id}\n{header}---\n{body}"


def _spec(*args: str, workspace: Path) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", *args, "-w", str(workspace)])


@pytest.fixture
def docs(workspace: Path, write: Write) -> Path:
    write(
        "docs/capabilities/core/CAP-CORE-a.md", _doc("CAP-CORE-a", "`US-b` `US-gone`\n", status="active", area="core")
    )
    write("docs/stories/core/US-b.md", _doc("US-b", "`CAP-CORE-a`\n", status="active", title="Story B", area="core"))
    write("docs/stories/ops/US-c.md", _doc("US-c", "`CAP-CORE-a`\n", status="proposed", title="Story C", area="ops"))
    write("specs/2026-10/20261001-done/spec.md", _doc("SPEC-done", status="completed"))
    write("specs/2026-10/20261002-open/spec.md", _doc("SPEC-open", status="draft", title="Open"))
    write("specs/2026-10/20261002-open/tasks.md", "- [x] one\n- [ ] two\n")
    return workspace


def test_resolve(docs: Path) -> None:
    result = _spec("resolve", "US-b", "SPEC-open", workspace=docs)
    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "[DOCUMENT: US-b kind=story status=active path=docs/stories/core/US-b.md]",
        "[DOCUMENT: SPEC-open kind=spec status=draft path=specs/2026-10/20261002-open/spec.md]",
    ]


def test_resolve_reports_each_unresolved_id_after_the_resolved_ones(docs: Path) -> None:
    result = _spec("resolve", "US-b", "US-none", "US-other", workspace=docs)
    assert result.exit_code == 2
    assert result.stdout.startswith("[DOCUMENT: US-b ")
    assert result.stderr.count("(SPEC_ID_UNRESOLVED)") == 2


def test_resolve_json(docs: Path) -> None:
    result = _spec("resolve", "US-b", "US-none", "--format", "json", workspace=docs)
    payload = json.loads(result.stdout)
    assert result.exit_code == 2 and result.stderr == ""
    assert [d["id"] for d in payload["documents"]] == ["US-b"]
    assert [e["code"] for e in payload["errors"]] == ["SPEC_ID_UNRESOLVED"]


def test_refs_out_marks_dangling_references(docs: Path) -> None:
    result = _spec("refs", "CAP-CORE-a", workspace=docs)
    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "[REF: US-b path=docs/stories/core/US-b.md status=active fields=body count=1]",
        "[REF: US-gone path=- status=- fields=body count=1]",
        "[PAGE: total=2 offset=0 limit=20 count=2 next=-]",
    ]


def test_refs_in_pages(docs: Path) -> None:
    result = _spec("refs", "CAP-CORE-a", "--direction", "in", "--limit", "1", workspace=docs)
    lines = result.stdout.splitlines()
    assert lines[0].startswith("[REF: US-b ")
    assert lines[1] == "[PAGE: total=2 offset=0 limit=1 count=1 next=1]"
    assert lines[2] == f"[NEXT_CMD: devkit spec refs CAP-CORE-a --direction in -w {docs} --limit 1 --offset 1]"
    second = _spec("refs", "CAP-CORE-a", "--direction", "in", "--limit", "1", "--offset", "1", workspace=docs)
    assert second.stdout.splitlines()[0].startswith("[REF: US-c ")


def test_refs_of_an_unknown_id(docs: Path) -> None:
    result = _spec("refs", "US-none", workspace=docs)
    assert result.exit_code == 2 and "(SPEC_ID_UNRESOLVED)" in result.stderr


def test_feedback_of_a_completed_bundle_is_listed_without_history(docs: Path, write: Write) -> None:
    # AC-01: the bundle's other files stay hidden.
    write("specs/2026-10/20261001-done/feedback/x.md", _doc("FB-x", status="open"))
    payload = json.loads(_spec("list", "feedback", "--status", "open", "--format", "json", workspace=docs).stdout)
    assert [(d["id"], d["historical"]) for d in payload["documents"]] == [("FB-x", False)]
    assert "SPEC-done" not in _spec("list", "spec", workspace=docs).stdout


def test_list_hides_history_and_counts_tasks(docs: Path) -> None:
    result = _spec("list", "spec", workspace=docs)
    assert result.stdout.splitlines() == [
        "[DOCUMENT: SPEC-open kind=spec status=draft path=specs/2026-10/20261002-open/spec.md tasks=1/2 title=Open]",
        "[PAGE: total=1 offset=0 limit=20 count=1 next=-]",
    ]
    assert "SPEC-done" in _spec("list", "spec", "--history", workspace=docs).stdout


@pytest.mark.parametrize(
    ("args", "ids"),
    [
        ((), ["CAP-CORE-a", "US-b", "US-c", "SPEC-open"]),
        (("story",), ["US-b", "US-c"]),
        (("--status", "Proposed,draft"), ["US-c", "SPEC-open"]),
        (("--area", "ops"), ["US-c"]),
        (("--query", "story b"), ["US-b"]),
    ],
)
def test_list_filters(docs: Path, args: tuple[str, ...], ids: list[str]) -> None:
    payload = json.loads(_spec("list", *args, "--format", "json", workspace=docs).stdout)
    assert [d["id"] for d in payload["documents"]] == ids


UNKNOWN_STATUS = "(SPEC_LIST_STATUS_UNKNOWN)"


@pytest.fixture
def statuses(workspace: Path, write: Write) -> Path:
    """Specs carrying planned and completed (the completed one historical), feedback carrying open."""
    write("specs/2026-10/20261001-done/spec.md", _doc("SPEC-done", status="completed"))
    write("specs/2026-10/20261002-next/spec.md", _doc("SPEC-next", status="planned", title="Next"))
    write("specs/2026-10/20261003-later/spec.md", _doc("SPEC-later", status="Planned", title="Later"))
    write("specs/2026-10/20261002-next/feedback/x.md", _doc("FB-x", status="open"))
    return workspace


def test_list_names_an_unknown_status(statuses: Path) -> None:
    # AC-01: the page and the exit code stay as they were; one notice names the value and the known statuses.
    result = _spec("list", "spec", "--status", "bogus", workspace=statuses)
    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["[PAGE: total=0 offset=0 limit=20 count=0 next=-]"]
    assert result.stderr.count(UNKNOWN_STATUS) == 1
    notice = next(line for line in result.stderr.splitlines() if UNKNOWN_STATUS in line)
    assert notice.startswith("[NOTICE]") and "bogus" in notice
    fix = next(line for line in result.stderr.splitlines() if line.startswith("[FIX]"))
    assert fix.endswith("completed, planned")


def test_list_json_carries_the_unknown_status_notice(statuses: Path) -> None:
    # AC-02
    result = _spec("list", "spec", "--status", "bogus", "--format", "json", workspace=statuses)
    payload = json.loads(result.stdout)
    assert result.exit_code == 0 and payload["total"] == 0
    [notice] = payload["notices"]
    assert notice["code"] == "SPEC_LIST_STATUS_UNKNOWN" and "bogus" in notice["message"]
    assert notice["advisory"]["fix"].endswith("completed, planned")


def test_list_names_only_the_unknown_statuses(statuses: Path) -> None:
    # AC-03: the comparison stays case-insensitive and the known value is not named.
    result = _spec("list", "spec", "--status", "Planned,bogus", "--format", "json", workspace=statuses)
    payload = json.loads(result.stdout)
    assert [d["id"] for d in payload["documents"]] == ["SPEC-later", "SPEC-next"]
    [notice] = payload["notices"]
    assert notice["message"].startswith("--status bogus:") and "planned" not in notice["message"]


def test_list_counts_hidden_statuses_as_known(statuses: Path, write: Write) -> None:
    # AC-04: a status on a historical spec, or on a spec of another namespace, is known.
    hidden = _spec("list", "spec", "--status", "completed", workspace=statuses)
    assert hidden.exit_code == 0 and "total=0 " in hidden.stdout
    assert UNKNOWN_STATUS not in hidden.stderr
    write("specs/2026-10/20261004-web/spec.md", _doc("SPEC-web", status="blocked", namespace="web"))
    write(
        ".devkit/config.toml",
        '[[tool.spec.namespaces]]\nname = "api"\npath = "services/api"\n'
        '[[tool.spec.namespaces]]\nname = "web"\npath = "apps/web"\n',
    )
    other = _spec("list", "spec", "--status", "blocked", "--namespace", "api", workspace=statuses)
    assert other.exit_code == 0 and "total=0 " in other.stdout
    assert UNKNOWN_STATUS not in other.stderr


def test_list_without_kinds_counts_every_kind(statuses: Path) -> None:
    # AC-05
    every = _spec("list", "--status", "open", workspace=statuses)
    assert every.exit_code == 0 and "[DOCUMENT: FB-x " in every.stdout
    assert UNKNOWN_STATUS not in every.stderr
    specs = _spec("list", "spec", "--status", "open", "--format", "json", workspace=statuses)
    [notice] = json.loads(specs.stdout)["notices"]
    assert notice["code"] == "SPEC_LIST_STATUS_UNKNOWN" and notice["message"].startswith("--status open:")


def test_list_without_status_values_adds_no_notice(statuses: Path) -> None:
    result = _spec("list", "spec", "--status", ",", "--format", "json", workspace=statuses)
    payload = json.loads(result.stdout)
    assert payload["total"] == 2 and payload["notices"] == []


def test_negative_paging_is_an_argument_error(docs: Path) -> None:
    result = _spec("list", "--limit", "-1", workspace=docs)
    assert result.exit_code == 2 and "(ARGUMENT_INVALID)" in result.stderr


def test_invalid_documents_are_warnings(docs: Path, write: Write) -> None:
    write("docs/bad.md", "---\nid: [x]\n---\n")
    result = _spec("list", "story", workspace=docs)
    assert result.exit_code == 0 and "(SPEC_DOCUMENT_INVALID)" in result.stderr
    assert _spec("--strict", "list", workspace=docs).exit_code == 2  # --strict belongs to the command, not the group
    assert _spec("list", "--strict", workspace=docs).exit_code == 1


def test_list_by_entrypoint_overlap(workspace: Path, write: Write) -> None:
    write(
        "docs/capabilities/core/CAP-CORE-a.md",
        _doc("CAP-CORE-a", status="active", entrypoints="[src/app/search/, src/cli.py]"),
    )
    write("docs/stories/core/US-b.md", _doc("US-b", status="active", entrypoints="[src/app/search/rank.py]"))
    write("docs/stories/core/US-c.md", _doc("US-c", status="active"))

    def ids(path: str) -> list[str]:
        return [
            d["id"]
            for d in json.loads(_spec("list", "--file", path, "--format", "json", workspace=workspace).stdout)[
                "documents"
            ]
        ]

    assert ids("src/app/search/rank.py") == ["CAP-CORE-a", "US-b"]
    assert ids("src/app") == ["CAP-CORE-a", "US-b"]
    assert ids("src/cli.py") == ["CAP-CORE-a"]
    assert ids("src/other.py") == []
    for invalid in ("/src/app", "src/*.py", "../src", "src/../app"):
        result = _spec("list", "--file", invalid, workspace=workspace)
        assert result.exit_code == 2 and "(SPEC_ENTRYPOINTS_PATH_INVALID)" in result.stderr, invalid


def _feedback(write: Write, name: str, **fields: str) -> None:
    write(f"specs/2026-10/feedback/20261013-{name}.md", _doc(f"FB-{name}", status="open", title=name, **fields))


@pytest.fixture
def feedback(workspace: Path, write: Write) -> Path:
    write(
        "docs/capabilities/core/CAP-CORE-a.md",
        _doc("CAP-CORE-a", status="open", stories="[US-x, US-y]"),
    )
    _feedback(write, "a", severity="critical", scope="upstream", target='"devkit spec list"', recurring="true")
    _feedback(write, "b", severity="blocked", scope="repo", created_at="2026-10-13", at="2026-10-13T05:25:43Z")
    _feedback(write, "c", severity="noise", scope="upstream")
    _feedback(write, "d", severity="Critical", scope="repo")
    _feedback(write, "e", severity="workaround")
    _feedback(write, "f")
    return workspace


def _ids(workspace: Path, *args: str) -> list[str]:
    result = _spec("list", *args, "--format", "json", workspace=workspace)
    assert result.exit_code == 0, result.output
    return [d["id"] for d in json.loads(result.stdout)["documents"]]


def test_where_keeps_documents_whose_field_is_one_of_the_values(feedback: Path) -> None:
    # AC-01: values compare case-insensitively after trimming.
    assert _ids(feedback, "feedback", "--where", "severity=critical, BLOCKED") == ["FB-a", "FB-d", "FB-b"]


def test_where_items_and_other_filters_combine_with_and(feedback: Path) -> None:
    # AC-02: a document without the field (the capability) never matches.
    assert _ids(feedback, "--where", "severity=critical", "--where", "scope=upstream", "--status", "open") == ["FB-a"]


def test_where_matches_booleans_and_list_elements(feedback: Path) -> None:
    # AC-03
    assert _ids(feedback, "--where", "recurring=true") == ["FB-a"]
    assert _ids(feedback, "--where", "stories=US-y") == ["CAP-CORE-a"]
    assert _ids(feedback, "--where", "recurring=false") == []
    assert _ids(feedback, "--where", "created_at=2026-10-13", "--where", "at=2026-10-13T05:25:43+00:00") == ["FB-b"]


@pytest.mark.parametrize("item", ["severity", "=critical", "severity=", "severity=,", " =x"])
def test_malformed_where_is_an_argument_error(feedback: Path, item: str) -> None:
    # AC-04
    result = _spec("list", "--where", item, workspace=feedback)
    assert result.exit_code == 2 and result.stdout == ""
    assert "(ARGUMENT_INVALID)" in result.stderr and f"--where {item}:" in result.stderr


def test_feedback_is_ordered_by_severity_within_its_kind(feedback: Path) -> None:
    # AC-05: critical, blocked, workaround, noise, then any other or missing value; ties by ID.
    assert _ids(feedback) == ["CAP-CORE-a", "FB-a", "FB-d", "FB-b", "FB-e", "FB-c", "FB-f"]


def test_feedback_lines_and_records_carry_severity_scope_and_target(feedback: Path) -> None:
    # AC-06
    lines = _spec("list", "--where", "scope=upstream", "--where", "severity=critical", workspace=feedback).stdout
    assert lines.splitlines()[0] == (
        "[DOCUMENT: FB-a kind=feedback status=open path=specs/2026-10/feedback/20261013-a.md tasks=- "
        'severity=critical scope=upstream target="devkit spec list" title=a]'
    )
    capability = _spec("list", "capability", workspace=feedback).stdout.splitlines()[0]
    assert "severity=" not in capability and "scope=" not in capability and "target=" not in capability
    records = {
        d["id"]: d for d in json.loads(_spec("list", "--format", "json", workspace=feedback).stdout)["documents"]
    }
    assert (records["FB-a"]["severity"], records["FB-a"]["scope"], records["FB-a"]["target"]) == (
        "critical",
        "upstream",
        "devkit spec list",
    )
    assert (records["FB-f"]["severity"], records["FB-f"]["scope"], records["FB-f"]["target"]) == (None, None, None)
    assert "severity" not in records["CAP-CORE-a"]
    assert (
        "[DOCUMENT: FB-f kind=feedback status=open path=specs/2026-10/feedback/20261013-f.md tasks=- "
        "severity=- scope=- target=- title=f]"
    ) in _spec("list", "feedback", workspace=feedback).stdout.splitlines()


def test_next_page_command_repeats_every_where(feedback: Path) -> None:
    # AC-07
    result = _spec(
        "list",
        "feedback",
        "--where",
        "severity=critical,blocked",
        "--where",
        "scope=repo",
        "--limit",
        "1",
        workspace=feedback,
    )
    assert result.stdout.splitlines()[-1] == (
        "[NEXT_CMD: devkit spec list feedback --where severity=critical,blocked --where scope=repo "
        f"-w {feedback} --limit 1 --offset 1]"
    )


def test_feedback_with_unknown_owner_remains_discoverable(feedback: Path, write: Write) -> None:
    _feedback(write, "ambiguous-owner", severity="workaround", scope="unknown", target='"devkit workflow next"')
    assert _ids(feedback, "feedback", "--status", "open", "--where", "scope=unknown") == ["FB-ambiguous-owner"]
    payload = json.loads(
        _spec("list", "feedback", "--where", "scope=unknown", "--format", "json", workspace=feedback).stdout
    )
    assert payload["documents"][0]["target"] == "devkit workflow next"


def test_proposal_lines_and_records_carry_task_kind_and_effort_hints(workspace: Path, write: Write) -> None:
    write(
        "docs/proposals/PROP-a/proposal.md",
        _doc(
            "PROP-a",
            status="draft",
            title="Alpha",
            task_kind="feature",
            planning_effort="low",
            dev_effort="high",
        ),
    )
    write(
        "docs/proposals/PROP-b/proposal.md",
        _doc("PROP-b", status="accepted", title="Beta"),
    )
    write("docs/capabilities/core/CAP-CORE-a.md", _doc("CAP-CORE-a", status="active", title="Cap"))

    lines = _spec("list", "proposal", workspace=workspace).stdout.splitlines()
    assert lines[:2] == [
        "[DOCUMENT: PROP-a kind=proposal status=draft path=docs/proposals/PROP-a/proposal.md tasks=- "
        "task_kind=feature planning_effort=low dev_effort=high title=Alpha]",
        "[DOCUMENT: PROP-b kind=proposal status=accepted path=docs/proposals/PROP-b/proposal.md tasks=- "
        "task_kind=- planning_effort=- dev_effort=- title=Beta]",
    ]
    records = {
        d["id"]: d for d in json.loads(_spec("list", "--format", "json", workspace=workspace).stdout)["documents"]
    }
    assert (
        records["PROP-a"]["task_kind"],
        records["PROP-a"]["planning_effort"],
        records["PROP-a"]["dev_effort"],
    ) == ("feature", "low", "high")
    assert (
        records["PROP-b"]["task_kind"],
        records["PROP-b"]["planning_effort"],
        records["PROP-b"]["dev_effort"],
    ) == (None, None, None)
    assert "planning_effort" not in records["CAP-CORE-a"] and "dev_effort" not in records["CAP-CORE-a"]
    assert _ids(workspace, "proposal", "--where", "planning_effort=low", "--where", "dev_effort=high") == ["PROP-a"]
