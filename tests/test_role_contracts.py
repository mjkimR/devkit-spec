"""The role contracts' bodies are the subagents' prompts; caller guidance lives in ``spec-delegate``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

BUNDLE = Path(__file__).resolve().parents[1] / "src/devkit_spec/bundle"
WORKERS = ("development-worker", "planning-worker")
ROLES = ("challenger", "reconciler", "reviewer", "scout", *WORKERS)
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


@pytest.mark.parametrize("role", WORKERS)
def test_a_worker_commits_its_result_and_records_in_its_worktree(role: str) -> None:
    # ADR-worker-delivers-committed-result; 01 §4.1-4.2: one-shot workers write their own records and commit.
    metadata, body = _contract(role)
    assert metadata["x-git-actions"] == ["read", "commit"]
    hosts = metadata["hosts"]
    assert hosts["claude-code"]["status"] == "native"
    # Role subagents run nested: Host -> worker -> role.
    assert {"Write", "Edit", "Bash", "Agent"} <= set(hosts["claude-code"]["tools"])
    assert hosts["codex"]["status"] == "unsupported"
    assert hosts["antigravity"]["status"] == "unverified"
    assert "git -C <worktree>" in body and "absolute" in body
    assert "Do not push, merge, rebase, reset, amend, stash or check out (`MUST NOT`)" in body
    assert "devkit workflow envelope new" in body and "`worker` envelope" in body
    assert "`head` set to your last commit" in body
    assert "do not write envelope files" not in body


def test_the_development_worker_commits_at_stage_boundaries_and_on_a_problem() -> None:
    body = " ".join(_contract("development-worker")[1].split())
    assert "Commit at every stage boundary" in body
    assert "with write-scope paths only, then `git -C <worktree> commit` on the unit branch" in body
    assert "never bypassed (`--no-verify`). Leave the worktree clean." in body
    assert "One path outside the write scope rejects the whole result" in body
    assert "emergency commit" in body and "what you tried and the recovery you recommend" in body
    assert "Do not revert, close, raise the depth or narrow the scope yourself" in body
    assert "with your recommended option and record the reason" in body


def test_the_development_worker_result_is_self_contained() -> None:
    body = _contract("development-worker")[1]
    assert "run `devkit rules fix <unit>/spec.md`" in body
    assert "pytest's `tmp_path` or an ignored path inside the worktree" in body
    # activity-effort decides the nested roles; the reconciler only verifies.
    assert "a separate `reconciler` nested subagent that verifies" in body


def test_the_planning_worker_collects_questions_in_one_round() -> None:
    body = " ".join(_contract("planning-worker")[1].split())
    assert "Collect the questions for the user in one round, never stopping at the first" in body
    assert "as a commit of their own" in body
    assert "status: reviewing" in body and "needs_decompose: true" in body
    assert "Waiting for the user's answers is not a problem" in body


@pytest.mark.parametrize("role", [r for r in ROLES if r not in WORKERS])
def test_every_other_role_stays_read_only(role: str) -> None:
    assert _contract(role)[0]["x-git-actions"] == ["read"]


def test_the_reconciler_verifies_and_never_drafts() -> None:
    metadata, body = _contract("reconciler")
    assert "Write" not in metadata["hosts"]["claude-code"]["tools"]
    assert "You do not draft documents" in body


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
    text = " ".join(TASKS.read_text(encoding="utf-8").split())
    assert "a task a `development-worker` builds names the `docs/` paths its checks require" in text


def test_the_host_validates_the_committed_range_and_blocks_a_failure() -> None:
    delegate = DELEGATE.read_text(encoding="utf-8")
    assert "except a worker, which commits on its activity branch ([worker](references/worker.md))" in delegate
    assert "your range check is a `validation` envelope" in delegate
    text = " ".join(WORKER_RESULTS.read_text(encoding="utf-8").split())
    assert "From the last accepted head to the returned head" in text
    assert "merge-base --is-ancestor <accepted> <returned>" in text
    assert "diff --name-only <accepted> <returned>` is in the write scope" in text
    assert "`git -C <worktree> status --short` is empty" in text
    assert "--status failed" in text and "never reset or amend" in text
    assert "a pull request stays open and blocked" in text
    assert "A blocked unit goes to no review and no integration" in text
    assert "validate the cumulative range again from the same last accepted head" in text
    assert "the base checkout's status and HEAD are as recorded" in text
    assert "except the validation envelopes you wrote under `<unit>/envelopes/` since `<accepted>`" in text
    assert "A worker never writes a `validation` envelope" in text
    assert "Never pass a blocked unit's current HEAD as the base" in text
    assert "`build-verify`, or `fix-verify` in `sdd-spec-bugfix`" in text
    assert (
        "A unit is blocked while its latest `validation` envelope is `failed`, whatever a worker returns afterwards"
        in text
    )
    assert "a problem a worker recorded has no resolution that names it" in text
    assert "A comment or a rerun request alone resolves nothing" in text


def test_orchestration_follows_the_committed_result_contract() -> None:
    text = " ".join(ORCHESTRATE.read_text(encoding="utf-8").split())
    assert (
        "commits at every stage boundary through the commit gate, writes its own records and returns its head" in text
    )
    assert "the committed range from the last accepted head" in text
    assert "A failing range is blocked, never discarded" in text
    assert "a blocked unit goes no further" in text
    assert "A `session`-depth task never becomes a unit" in text
    assert "`local-orchestrated` is the user's choice, never yours" in text
