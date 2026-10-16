"""Every skill and playbook document of the bundle stays within devkit's skill document budget.

devkit's opt-in ``RULE-skill-document-size`` (``authoring`` bundle) warns above 12288 bytes; the bundle's own
documents stay under it so a project that enables the rule sees no warning from them. A skill that outgrows it moves
conditional content into ``references/`` (devkit's ``skill-authoring`` playbook), so links and references are checked
here too. A failure names the size and the limit, so an author sees the margin.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BUNDLE = Path(__file__).resolve().parents[1] / "src/devkit_spec/bundle"
BUDGET = 12288
DOCUMENTS = sorted([*BUNDLE.glob("skills/**/*.md"), *BUNDLE.glob("playbooks/**/*.md")])
SKILLS = sorted(path.parent for path in BUNDLE.glob("skills/*/SKILL.md"))
# Restructured to leave headroom for the next edit (SPEC-subagent-procedure-in-contract).
HEADROOM = {"spec": BUDGET - 512, "spec-delegate": BUDGET - 512}
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def _relative_links(path: Path) -> list[str]:
    return [target for target in LINK.findall(path.read_text(encoding="utf-8")) if "://" not in target]


def _over(size: int, limit: int) -> str:
    return f"{size} bytes exceed the limit {limit} by {size - limit}"


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda path: str(path.relative_to(BUNDLE)))
def test_within_budget(path: Path) -> None:
    size = len(path.read_bytes())
    assert size <= BUDGET, _over(size, BUDGET)


@pytest.mark.parametrize("skill", sorted(HEADROOM))
def test_restructured_skills_keep_headroom(skill: str) -> None:
    size = len((BUNDLE / f"skills/{skill}/SKILL.md").read_bytes())
    assert size <= HEADROOM[skill], _over(size, HEADROOM[skill])


@pytest.mark.parametrize("skill", SKILLS, ids=lambda path: path.name)
def test_skill_links_resolve_and_every_reference_is_linked(skill: Path) -> None:
    linked: set[Path] = set()
    for document in skill.rglob("*.md"):
        for target in _relative_links(document):
            resolved = (document.parent / target).resolve()
            assert resolved.exists(), f"{document.relative_to(BUNDLE)} -> {target}"
            linked.add(resolved)
    for reference in (skill / "references").glob("*.md"):
        assert reference.resolve() in linked, f"{reference.relative_to(BUNDLE)} is not linked from its skill"
