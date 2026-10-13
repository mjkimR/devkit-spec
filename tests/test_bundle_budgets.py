"""Every skill and playbook document of the bundle stays within devkit's skill document budget.

devkit's opt-in ``RULE-skill-document-size`` (``authoring`` bundle) warns above 8192 bytes; the bundle's own
documents stay under it so a project that enables the rule sees no warning from them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

BUNDLE = Path(__file__).resolve().parents[1] / "src/devkit_spec/bundle"
BUDGET = 8192
DOCUMENTS = sorted([*BUNDLE.glob("skills/**/*.md"), *BUNDLE.glob("playbooks/**/*.md")])


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda path: str(path.relative_to(BUNDLE)))
def test_within_budget(path: Path) -> None:
    assert len(path.read_bytes()) <= BUDGET
