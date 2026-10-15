"""The proposal unit's workflow records at handoff: dropped, and the spec's gates recorded from the user's answer."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from conftest import Write
from devkit.workflow import Workspace, load_decisions
from proposals.support import CHARACTERIZE, GATED, INCUBATED, MONTH, STAMP, TODAY, accept, spec_dir, write_workflow

from devkit_spec.proposals import CarriedGate, create_padr, create_proposal, handoff_proposal
from devkit_spec.proposals import handoff as handoff_module

UNIT = "docs/proposals/PROP-{slug}"


def _proposal(root: Path, slug: str) -> Path:
    """A bundle bound to ``incubated-delivery`` whose spec follows the gated ``direct-delivery``; returns its
    proposal.md."""
    write_workflow(root, "incubated-delivery", INCUBATED)
    write_workflow(root, "direct-delivery", GATED.format(id="direct-delivery", middle=""))
    write_workflow(root, "bugfix", GATED.format(id="bugfix", middle=CHARACTERIZE))
    created = create_proposal(root, slug, today=TODAY)
    return root / created.path


def _record(root: Path, slug: str, name: str, **fields: object) -> None:
    """A decision record of the proposal unit: an ``accept`` of the direction gate in ``incubated-delivery`` unless
    ``fields`` say otherwise."""
    data = {
        "request": "gate:direction",
        "kind": "approve",
        "action": "accept",
        "workflow": "incubated-delivery",
        "stage": "direction-handoff",
        "at": "2026-10-13T00:00:00Z",
    }
    data |= fields
    path = root / UNIT.format(slug=slug) / "decisions" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _answered(root: Path, slug: str, *, by: str = "user") -> None:
    _record(root, slug, "01-gate-intent.yaml", request="gate:intent", stage="intent-proposal", by="user")
    _record(root, slug, "02-gate-direction.yaml", request="gate:direction", stage="direction-handoff", by=by)


def _spec_records(root: Path, slug: str) -> list[dict[str, object]]:
    directory = spec_dir(root, slug) / "decisions"
    if not directory.is_dir():
        return []
    return [yaml.safe_load(path.read_text(encoding="utf-8")) for path in sorted(directory.iterdir())]


def test_drops_the_unit_records_and_carries_the_rest(workspace: Path, write: Write) -> None:
    proposal = _proposal(workspace, "records")
    unit = UNIT.format(slug="records")
    _answered(workspace, "records")
    write(f"{unit}/decisions/03-broken.yaml", "request: [\n")
    write(f"{unit}/decisions/notes.yaml", "kept: true\n")
    write(f"{unit}/envelopes/scout-01.yaml", "kind: scout\n")
    write(f"{unit}/notes.md", "# Notes\n")
    create_padr(workspace, "records", "Use records")
    accept(proposal)

    result = handoff_proposal(workspace, "records", today=TODAY)

    assert result.dropped_records == [
        f"{unit}/decisions/01-gate-intent.yaml",
        f"{unit}/decisions/02-gate-direction.yaml",
        f"{unit}/decisions/03-broken.yaml",
        f"{unit}/envelopes/scout-01.yaml",
    ]
    materials = workspace / f"docs/materials/{MONTH}/{STAMP}-records"
    assert sorted(path.relative_to(materials).as_posix() for path in materials.rglob("*") if path.is_file()) == [
        "decisions/notes.yaml",
        "notes.md",
    ]
    assert [decision.padr for decision in result.decisions] == ["PADR-use-records"]
    assert not (workspace / unit).exists()
    assert not (spec_dir(workspace, "records") / "envelopes").exists()


def test_records_alone_create_no_materials_directory(workspace: Path) -> None:
    proposal = _proposal(workspace, "bare")
    _answered(workspace, "bare")
    accept(proposal)
    result = handoff_proposal(workspace, "bare", today=TODAY)
    assert result.materials is None
    assert not (workspace / "docs/materials").exists()
    assert len(result.dropped_records) == 2


def test_records_the_specs_gates_from_the_users_direction_answer(workspace: Path) -> None:
    _proposal(workspace, "carry")
    _answered(workspace, "carry")

    result = handoff_proposal(workspace, "carry", direction_chosen=True, today=TODAY)

    spec = f"specs/{MONTH}/{STAMP}-carry"
    assert result.carried_gates == [
        CarriedGate("gate:intent", f"{spec}/decisions/01-gate-intent.yaml"),
        CarriedGate("gate:direction", f"{spec}/decisions/02-gate-direction.yaml"),
    ]
    records = _spec_records(workspace, "carry")
    assert [(r["request"], r["action"], r["by"], r["note"], r["workflow"]) for r in records] == [
        ("gate:intent", "accept", "user", "PROP-carry", "direct-delivery"),
        ("gate:direction", "accept", "user", "PROP-carry", "direct-delivery"),
    ]
    assert result.notices == []
    ws = Workspace(workspace, lint=None, ancestor=None)
    evaluation = ws.evaluate_unit(ws.resolve_unit(spec), lint=False)
    assert evaluation.to_dict()["done"] == ["intent", "direction"]


def test_records_only_the_intent_gate_of_a_bugfix_spec(workspace: Path) -> None:
    accept(_proposal(workspace, "defect"), "\nhandoff_workflow: bugfix")
    _answered(workspace, "defect")
    result = handoff_proposal(workspace, "defect", today=TODAY)
    assert [gate.request for gate in result.carried_gates] == ["gate:intent"]
    assert [record["request"] for record in _spec_records(workspace, "defect")] == ["gate:intent"]


@pytest.mark.parametrize(
    "records",
    [
        [],
        [("02-gate-direction.yaml", {"by": "policy"})],
        [("02-gate-direction.yaml", {"by": "user", "action": "decline"})],
        [
            ("02-gate-direction.yaml", {"by": "user"}),
            ("03-gate-direction.yaml", {"by": "user", "action": "decline"}),
            ("04-gate-direction.yaml", {"by": "user", "action": "cancel"}),
        ],
        [
            ("02-gate-direction.yaml", {"by": "user"}),
            ("03-return-spike.yaml", {"request": "return:spike", "kind": "return", "stage": "spike", "by": "user"}),
        ],
        [("02-gate-direction.yaml", {"by": "user", "workflow": "other"})],
    ],
    ids=["none", "policy", "declined", "declined-after-accept", "returned", "other-workflow"],
)
def test_records_nothing_without_the_users_direction_answer(
    workspace: Path, records: list[tuple[str, dict[str, object]]]
) -> None:
    accept(_proposal(workspace, "ask"))
    for name, fields in records:
        _record(workspace, "ask", name, **fields)
    assert load_decisions(workspace / UNIT.format(slug="ask")).errors == []
    result = handoff_proposal(workspace, "ask", today=TODAY)
    assert result.carried_gates == []
    assert _spec_records(workspace, "ask") == []


def test_a_cancel_after_the_users_accept_changes_nothing(workspace: Path) -> None:
    _proposal(workspace, "cancel")
    _answered(workspace, "cancel")
    _record(workspace, "cancel", "03-gate-direction.yaml", by="user", action="cancel")
    result = handoff_proposal(workspace, "cancel", direction_chosen=True, today=TODAY)
    assert [gate.request for gate in result.carried_gates] == ["gate:intent", "gate:direction"]


def test_records_nothing_for_an_unbound_spec(workspace: Path) -> None:
    write_workflow(workspace, "incubated-delivery", INCUBATED)
    accept(workspace / create_proposal(workspace, "loose", today=TODAY).path)
    _answered(workspace, "loose")
    result = handoff_proposal(workspace, "loose", today=TODAY)
    assert result.workflow is None and result.carried_gates == []
    assert _spec_records(workspace, "loose") == []


def test_a_recording_failure_is_a_warning(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    accept(_proposal(workspace, "fails"))
    _answered(workspace, "fails")
    real = handoff_module.record_answer

    def record_answer(ws: Workspace, unit: object, request: str, *args: object, **kwargs: object) -> object:
        if request == "gate:direction":
            raise OSError("disk full")
        return real(ws, unit, request, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(handoff_module, "record_answer", record_answer)
    result = handoff_proposal(workspace, "fails", today=TODAY)

    assert [gate.request for gate in result.carried_gates] == ["gate:intent"]
    assert [record["request"] for record in _spec_records(workspace, "fails")] == ["gate:intent"]
    [notice] = result.notices
    assert notice.code == "SPEC_PROPOSAL_GATE_NOT_CARRIED"
    assert "gate:direction" in notice.message and "disk full" in notice.details
    spec = f"specs/{MONTH}/{STAMP}-fails"
    assert notice.fix is not None
    assert f"devkit workflow answer --unit {spec} --request gate:direction --action accept --by user" in notice.fix
    assert not (workspace / UNIT.format(slug="fails")).exists()
