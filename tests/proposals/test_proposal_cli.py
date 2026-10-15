from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner, Result
from conftest import Write
from devkit.cli import cli as devkit_cli
from proposals.support import GATED, INCUBATED, accept, write_workflow


def _proposal(workspace: Path, *args: str) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", "proposal", *args, "-w", str(workspace)])


def test_new_and_padr(workspace: Path) -> None:
    result = _proposal(workspace, "new", "Fast Engine", "--title", "Fast: Engine", "--with-target-docs")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "[PROPOSAL: PROP-fast-engine path=docs/proposals/PROP-fast-engine/proposal.md "
        "dir=docs/proposals/PROP-fast-engine target_docs=docs/proposals/PROP-fast-engine/target-docs.md workflow=-]"
    ]
    assert "(SPEC_PROPOSAL_UNBOUND)" in result.stderr
    result = _proposal(workspace, "padr", "fast-engine", "Use AST parser")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "[PADR: PADR-use-ast-parser path=docs/proposals/PROP-fast-engine/decisions/PADR-use-ast-parser.md "
        "proposal=PROP-fast-engine]"
    ]
    result = _proposal(workspace, "padr", "fast-engine", "Use AST parser", "--format", "json")
    assert result.exit_code == 2 and result.stderr == ""
    assert json.loads(result.stdout)["error"]["code"] == "SPEC_PROPOSAL_EXISTS"


def test_padr_slug_option(workspace: Path) -> None:
    _proposal(workspace, "new", "plans")
    result = _proposal(workspace, "padr", "plans", "2024 roadmap", "--slug", "roadmap-2024")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "[PADR: PADR-roadmap-2024 path=docs/proposals/PROP-plans/decisions/PADR-roadmap-2024.md proposal=PROP-plans]"
    ]


def test_new_json(workspace: Path) -> None:
    result = _proposal(workspace, "new", "lean", "--format", "json")
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert {key: payload[key] for key in ("id", "dir", "path", "target_docs", "workflow", "next_command")} == {
        "id": "PROP-lean",
        "dir": "docs/proposals/PROP-lean",
        "path": "docs/proposals/PROP-lean/proposal.md",
        "target_docs": None,
        "workflow": None,
        "next_command": None,
    }
    assert [notice["code"] for notice in payload["notices"]] == ["SPEC_PROPOSAL_UNBOUND"]


def test_new_binds_the_proposal_and_workflow_next_runs(workspace: Path) -> None:
    write_workflow(workspace, "incubated-delivery", INCUBATED)
    result = _proposal(workspace, "new", "bound", "--handoff-workflow", "bugfix")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "[PROPOSAL: PROP-bound path=docs/proposals/PROP-bound/proposal.md dir=docs/proposals/PROP-bound "
        "target_docs=- workflow=incubated-delivery]",
        "[NEXT_CMD: devkit workflow next --unit docs/proposals/PROP-bound]",
    ]
    assert result.stderr == ""
    result = CliRunner().invoke(
        devkit_cli,
        ["workflow", "next", "--unit", "docs/proposals/PROP-bound", "-w", str(workspace), "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["workflow"] == "incubated-delivery" and payload["bound"] is True, payload


def test_handoff_refuses_an_unapproved_proposal(workspace: Path) -> None:
    _proposal(workspace, "new", "draft-one")
    result = _proposal(workspace, "handoff", "draft-one")
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "(SPEC_PROPOSAL_NOT_APPROVED)" in result.stderr
    assert (workspace / "docs/proposals/PROP-draft-one/proposal.md").is_file()


def test_handoff_text(workspace: Path, write: Write) -> None:
    write_workflow(workspace, "direct-delivery")
    _proposal(workspace, "new", "shipit")
    _proposal(workspace, "padr", "shipit", "Pick")
    write("docs/proposals/PROP-shipit/materials/m.md", "[up](../proposal.md)\n")
    write("docs/stories/US-a.md", "---\nid: US-a\n---\n[PROP-shipit] [gone](../proposals/PROP-shipit/decisions/)\n")
    accept(workspace / "docs/proposals/PROP-shipit/proposal.md")

    result = _proposal(workspace, "handoff", "shipit")

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    head = lines[0]
    assert head.startswith("[HANDOFF: PROP-shipit spec=SPEC-shipit dir=specs/") and head.endswith(
        " workflow=direct-delivery]"
    )
    spec_dir = head.split(" dir=")[1].split(" ")[0]
    month, bundle = spec_dir.split("/")[1:]
    stamp = bundle.split("-")[0]
    assert lines[1] == f"[MATERIALS: docs/materials/{month}/{stamp}-shipit]"
    assert lines[2] == f"[PROMOTED_ADR: ADR-pick path=docs/decisions/{month}/{stamp}-pick.md padr=PADR-pick]"
    assert "[REWRITTEN: docs/stories/US-a.md:4 kind=id from=PROP-shipit to=SPEC-shipit]" in lines
    assert (
        f"[REWRITTEN: docs/materials/{month}/{stamp}-shipit/m.md:1 kind=link from=../proposal.md "
        f"to=../../../../{spec_dir}/spec.md]"
    ) in lines
    assert (
        "[UNRESOLVED_LINK: docs/stories/US-a.md:4 kind=link target=../proposals/PROP-shipit/decisions/ reason=unmapped]"
        in lines
    )
    assert lines[-1] == f"[NEXT_CMD: devkit workflow next --unit {spec_dir}]"
    assert "(SPEC_PROPOSAL_LINK_UNRESOLVED)" in result.stderr
    assert "(SPEC_PROPOSAL_REFS_REWRITTEN)" in result.stderr
    assert not (workspace / "docs/proposals/PROP-shipit").exists()


def test_handoff_strict_fails_on_the_unresolved_link_warning(workspace: Path, write: Write) -> None:
    _proposal(workspace, "new", "strict")
    write("docs/stories/US-a.md", "[gone](../proposals/PROP-strict/decisions/)\n")
    result = _proposal(workspace, "handoff", "strict", "--direction-chosen", "--strict")
    assert result.exit_code == 1
    assert result.stdout.startswith("[HANDOFF: PROP-strict ")


def test_handoff_json(workspace: Path) -> None:
    _proposal(workspace, "new", "jsonic")
    result = _proposal(workspace, "handoff", "jsonic", "--direction-chosen", "--format", "json")
    assert result.exit_code == 0 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["proposal"] == "PROP-jsonic" and payload["spec"] == "SPEC-jsonic"
    assert payload["workflow"] is None and payload["next_command"] is None
    assert [notice["code"] for notice in payload["notices"]] == ["SPEC_PROPOSAL_UNBOUND"]
    assert set(payload) >= {"decisions", "rewritten", "rewritten_files", "unresolved", "materials", "target_docs"}
    assert payload["dropped_records"] == [] and payload["carried_gates"] == []


def test_handoff_reports_dropped_records_and_carried_gates(workspace: Path) -> None:
    write_workflow(workspace, "incubated-delivery", INCUBATED)
    write_workflow(workspace, "direct-delivery", GATED.format(id="direct-delivery", middle=""))
    _proposal(workspace, "new", "gated")
    unit = "docs/proposals/PROP-gated"
    (workspace / unit / "decisions").mkdir(exist_ok=True)
    (workspace / unit / "decisions/01-gate-direction.yaml").write_text(
        "request: gate:direction\nkind: approve\naction: accept\nworkflow: incubated-delivery\n"
        "stage: direction-handoff\nby: user\nat: '2026-10-13T00:00:00Z'\n",
        encoding="utf-8",
    )

    result = _proposal(workspace, "handoff", "gated", "--direction-chosen")

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    spec_dir = lines[0].split(" dir=")[1].split(" ")[0]
    assert lines[1:4] == [
        f"[DROPPED_RECORD: {unit}/decisions/01-gate-direction.yaml]",
        f"[CARRIED_GATE: gate:intent decision={spec_dir}/decisions/01-gate-intent.yaml]",
        f"[CARRIED_GATE: gate:direction decision={spec_dir}/decisions/02-gate-direction.yaml]",
    ]
    assert result.stderr == ""
