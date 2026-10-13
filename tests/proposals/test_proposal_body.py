from __future__ import annotations

import pytest

from devkit_spec.proposals import carry_proposal_body, ensure_ac_ids
from devkit_spec.proposals.body import classify


def test_ensure_ac_ids_tags_every_h3() -> None:
    body, ids = ensure_ac_ids(
        "### Scenario one: first\n- **Given** x\n\n### [AC-07] already tagged\n- ok\n\n### Two [AC-01] [AC-02] tags\n- bad\n"
    )
    assert ids == ["AC-01", "AC-07", "AC-03"]
    assert "### Scenario 1 [AC-01]: Scenario one: first\n" in body
    assert "### [AC-07] already tagged\n" in body
    assert "### Scenario 3 [AC-03]: Two tags\n" in body


def test_ensure_ac_ids_wraps_list_items_and_prose() -> None:
    body, ids = ensure_ac_ids("- **Given** a\n- **Given** b\n  - nested\n")
    assert ids == ["AC-01", "AC-02"]
    assert body == (
        "### Scenario 1 [AC-01]: Carried from proposal\n- **Given** a\n\n"
        "### Scenario 2 [AC-02]: Carried from proposal\n- **Given** b\n  - nested\n"
    )
    body, ids = ensure_ac_ids("Some prose only, no list.\n")
    assert ids == ["AC-01"]
    assert body.startswith("### Scenario 1 [AC-01]: Carried from proposal\n\nSome prose only")


def test_ensure_ac_ids_ignores_fenced_code() -> None:
    body, ids = ensure_ac_ids("```\n### not a heading\n- not an item\n```\n")
    assert ids == ["AC-01"]
    assert body.startswith("### Scenario 1 [AC-01]: Carried from proposal\n\n```")


def test_ensure_ac_ids_placeholder_for_an_empty_body() -> None:
    body, ids = ensure_ac_ids("")
    assert ids == ["AC-01"]
    assert body.startswith("### [AC-01] <scenario>\n- **Given** <precondition>\n")


@pytest.mark.parametrize(
    ("heading", "kind"),
    [
        ("", "problem"),
        ("1. Background & Hypothesis", "problem"),
        ("Origin of the idea", "problem"),
        ("Non-Goals", "non-goals"),
        ("Out of scope", "non-goals"),
        ("Expected Acceptance Checks", "acceptance"),
        ("2. Technical Spike Questions", "notes"),
    ],
)
def test_classify(heading: str, kind: str) -> None:
    assert classify(heading) == kind


def test_carry_regroups_sections() -> None:
    carried = carry_proposal_body(
        "---\nid: PROP-x\n---\n\n# [PROP-x] X\n\nPreamble.\n\n## Background\n\nWhy.\n\n### Detail\n\nMore.\n\n---\n\n"
        "## Non-Goals\n\n1. Nothing.\n\n## Acceptance\n\n- **Given** it\n\n## Open Questions\n\n```md\n## kept\n```\n"
    )
    assert carried.problem == "Preamble.\n\n### Background\n\nWhy.\n\n#### Detail\n\nMore.\n\n"
    assert carried.non_goals == "1. Nothing.\n\n"
    assert carried.acceptance == "- **Given** it\n\n"
    assert carried.notes == "### Open Questions\n\n```md\n## kept\n```\n\n"
