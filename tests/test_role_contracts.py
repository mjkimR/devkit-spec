"""The role contracts' bodies are the subagents' prompts; caller guidance lives in ``spec-delegate``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

BUNDLE = Path(__file__).resolve().parents[1] / "src/devkit_spec/bundle"
ROLES = ("challenger", "reconciler", "reviewer", "scout", "worker")
DELEGATE = BUNDLE / "skills/spec-delegate/SKILL.md"


def _contract(role: str) -> tuple[dict[str, Any], str]:
    _, frontmatter, body = (BUNDLE / f"subagents/{role}.md").read_text(encoding="utf-8").split("---\n", 2)
    return yaml.safe_load(frontmatter), body


@pytest.mark.parametrize("role", ("scout", "challenger"))
def test_a_subagent_only_procedure_lives_in_the_contract(role: str) -> None:
    metadata, body = _contract(role)
    assert "skill" not in metadata
    assert "\n## Procedure\n" in body and "\n## Return\n" in body
    assert not (BUNDLE / f"skills/spec-{role}").exists()


@pytest.mark.parametrize("role", ROLES)
def test_a_contract_body_holds_only_the_role_prompt(role: str) -> None:
    _, body = _contract(role)
    assert "## Host projection notes" not in body
    assert "## Safety conditions" not in body
    assert "the Developer records them" not in body


def test_reviewer_and_reconciler_keep_the_skills_the_main_session_shares() -> None:
    assert _contract("reviewer")[0]["skill"] == "spec-review"
    assert _contract("reconciler")[0]["skill"] == "spec-sync"


def test_only_scout_gains_a_shell() -> None:
    scout = _contract("scout")[0]["hosts"]
    assert "Bash" in scout["claude-code"]["tools"]
    assert "run_command" in scout["antigravity"]["tools"]
    assert scout["antigravity"]["commandExecutionPolicy"] == "sandbox"
    challenger = _contract("challenger")[0]["hosts"]
    assert "Bash" not in challenger["claude-code"]["tools"]
    assert "run_command" not in challenger["antigravity"]["tools"]


def test_the_worker_writes_in_its_worktree_and_never_commits() -> None:
    metadata, body = _contract("worker")
    assert metadata["x-git-actions"] == ["read"]
    hosts = metadata["hosts"]
    assert hosts["claude-code"]["status"] == "native"
    assert {"Write", "Edit", "Bash"} <= set(hosts["claude-code"]["tools"])
    assert hosts["codex"]["status"] == "unsupported"
    assert hosts["antigravity"]["status"] == "unverified"
    assert "git -C <worktree>" in body and "absolute" in body
    assert "Do not stage or commit (`MUST NOT`)" in body
    assert "One path outside the write scope rejects the whole result" in body


def test_spec_delegate_passes_only_the_payload_to_a_projected_role() -> None:
    text = DELEGATE.read_text(encoding="utf-8")
    assert "Read the contract frontmatter first" in text
    assert "With a projected file, pass only the payload" in text
    assert "When the main session substitutes, follow the contract body yourself" in text
    assert "Pass the role contract body" not in text
    assert "[payload](references/payload.md)" in text
    payload = (DELEGATE.parent / "references/payload.md").read_text(encoding="utf-8")
    for role in ROLES:
        assert f"| `{role}` |" in payload, role
