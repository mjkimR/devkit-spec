"""The role contracts' bodies are the subagents' prompts; caller guidance lives in ``spec-delegate``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

BUNDLE = Path(__file__).resolve().parents[1] / "src/devkit_spec/bundle"
ROLES = ("challenger", "reconciler", "reviewer", "scout", "worker")
DELEGATE = BUNDLE / "skills/spec-delegate/SKILL.md"
WORKER_RESULTS = BUNDLE / "skills/spec-delegate/references/worker.md"
ORCHESTRATE = BUNDLE / "skills/spec-orchestrate/SKILL.md"
TASKS = BUNDLE / "skills/spec-tasks/SKILL.md"


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


def test_the_worker_commits_a_complete_result_in_its_worktree() -> None:
    # AC-01 (ADR-worker-delivers-committed-result).
    metadata, body = _contract("worker")
    assert metadata["x-git-actions"] == ["read", "commit"]
    hosts = metadata["hosts"]
    assert hosts["claude-code"]["status"] == "native"
    assert {"Write", "Edit", "Bash"} <= set(hosts["claude-code"]["tools"])
    assert hosts["codex"]["status"] == "unsupported"
    assert hosts["antigravity"]["status"] == "unverified"
    assert "git -C <worktree>" in body and "absolute" in body
    assert "with write-scope paths only, then `git -C <worktree> commit` on the unit branch" in body
    assert "never bypassed (`--no-verify`). Leave the worktree clean." in body
    assert "Do not push, merge, rebase, reset, amend, stash or check out (`MUST NOT`)" in body
    assert "`head` set to your last commit" in body
    assert "One path outside the write scope rejects the whole result" in body
    assert "Commit nothing incomplete" in body


def test_the_worker_result_is_self_contained() -> None:
    # AC-02: spec status through the rule's fix, docs only where a boundary names them, throwaway data in the worktree.
    body = _contract("worker")[1]
    assert "run `devkit rules fix <unit>/spec.md`" in body
    assert "A `docs/` path only when a task's `_Boundary:` names it" in body
    assert "pytest's `tmp_path` or an ignored path inside the worktree" in body


@pytest.mark.parametrize("role", [r for r in ROLES if r != "worker"])
def test_every_other_role_stays_read_only(role: str) -> None:
    # AC-03.
    assert _contract(role)[0]["x-git-actions"] == ["read"]


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


def test_tasks_name_the_docs_a_worker_must_write() -> None:
    # AC-02: the documentation a check requires is in the worker task's boundary.
    text = " ".join(TASKS.read_text(encoding="utf-8").split())
    assert "a task a `worker` builds names the `docs/` paths its checks require" in text


def test_the_host_validates_the_committed_range_and_blocks_a_failure() -> None:
    # AC-04.
    delegate = DELEGATE.read_text(encoding="utf-8")
    assert "except a `worker`, which commits on its unit branch ([worker](references/worker.md))" in delegate
    text = " ".join(WORKER_RESULTS.read_text(encoding="utf-8").split())
    assert "From the last accepted head to the returned head" in text
    assert "merge-base --is-ancestor <accepted> <returned>" in text
    assert "diff --name-only <accepted> <returned>` is in the write scope" in text
    assert "changes the `status:` line only" in text
    assert "`git -C <worktree> status --short` is empty" in text
    assert "--status failed" in text and "never reset or amend" in text
    assert "a pull request stays open and blocked" in text
    assert "A blocked unit goes to no review and no integration" in text
    assert "validate the cumulative range again from the same last accepted head" in text


def test_orchestration_follows_the_committed_result_contract() -> None:
    # AC-05.
    text = " ".join(ORCHESTRATE.read_text(encoding="utf-8").split())
    assert "The worker commits its complete build on the unit branch through the commit gate" in text
    assert "the committed range from the last accepted head" in text
    assert "A failing range is blocked, never discarded" in text
    assert "a blocked unit goes no further" in text
