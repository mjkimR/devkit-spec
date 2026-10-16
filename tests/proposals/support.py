"""Helpers shared by the proposal tests."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

TODAY = date(2026, 10, 13)
MONTH = "2026-10"
STAMP = "20261013"

WORKFLOW = """---
id: {id}
title: Delivery
status: active
schema_version: 1
layout:
  work_dir: specs
  unit_path: "{{date:%Y-%m}}/{{date:%Y%m%d}}-{{slug}}"
  anchor: spec.md
stages:
  - id: specify
    name: Specify
    human_gate: false
    entry: []
    exit: [not-skeleton(spec.md)]
    artifacts: [spec.md]
    skills: []
    role: developer
    isolation: none
    returns: []
---

Prose, not parsed.
"""

INCUBATED = """---
id: sdd-proposal
title: Incubated delivery
status: active
schema_version: 1
layout:
  work_dir: docs/proposals
  unit_path: "PROP-{slug}"
  anchor: proposal.md
stages:
  - id: intent-proposal
    name: Proposal
    human_gate: false
    entry: []
    exit: [anchor-exists]
    artifacts: [proposal.md]
    skills: []
    role: developer
    isolation: none
    returns: []
---

Prose, not parsed.
"""


# A spec workflow with the plan-intent gate; ``middle`` holds stages between it and specify.
GATED = """---
id: {id}
title: Delivery
status: active
schema_version: 1
layout:
  work_dir: specs
  unit_path: "{{date:%Y-%m}}/{{date:%Y%m%d}}-{{slug}}"
  anchor: spec.md
stages:
  - id: intent
    name: Plan intent
    human_gate: plan-intent
    entry: []
    exit: [anchor-exists]
    artifacts: [spec.md]
    skills: []
    role: developer
    isolation: none
    returns: []
{middle}  - id: specify
    name: Specify
    human_gate: false
    entry: []
    exit: [not-skeleton(spec.md)]
    artifacts: [spec.md]
    skills: []
    role: developer
    isolation: none
    returns: []
---

Prose, not parsed.
"""

CHARACTERIZE = """  - id: characterize
    name: Characterize
    human_gate: false
    entry: [anchor-exists]
    exit: [not-skeleton(spec.md)]
    artifacts: [spec.md]
    skills: []
    role: developer
    isolation: none
    returns: []
"""


def write_workflow(root: Path, workflow_id: str, text: str | None = None) -> Path:
    """A definition in the project's ``.devkit/workflows/`` (devkit's default ``definitions_dir``)."""
    path = root / ".devkit" / "workflows" / f"{workflow_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text is not None else WORKFLOW.format(id=workflow_id), encoding="utf-8")
    return path


def accept(proposal: Path, extra: str = "") -> None:
    """Set the proposal's status to accepted, adding ``extra`` frontmatter lines after it."""
    text = proposal.read_text(encoding="utf-8")
    if "\ntask_kind:" in extra:  # replace the scaffolded task_kind line instead of duplicating the key
        text = re.sub(r"(?m)^task_kind:.*\n", "", text, count=1)
    proposal.write_text(text.replace("status: draft", "status: accepted" + extra, 1), encoding="utf-8")


def spec_dir(root: Path, slug: str) -> Path:
    return root / "specs" / MONTH / f"{STAMP}-{slug}"
