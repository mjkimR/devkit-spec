"""``devkit spec policy``: the project policy that routing, gate and Git decisions follow, in one place.

Text output: ``[GATE_POLICY: <gate> policy= source=]`` for the gates of the spec workflows (``plan-intent``,
``plan-accept``, ``dev-integration``) and any other gate the project configures, ``[STAGE_POLICY: <stage> state=off]``
per stage the project switched off, ``[GIT_POLICY: worktree= pull_request= delete_branch= setup=]``,
``[ROUTING_POLICY: depth_escalation=]`` and ``[FEEDBACK_POLICY: capture= coverage= detail= reminder=]``.
``source`` is ``fixed`` for a gate a person always decides (``plan-intent``, ``plan-accept``), ``config`` when
``.devkit/config.toml`` sets the value, else ``default``. A policy key for a fixed gate, or ``dev-integration =
"off"``, is ``SPEC_CONFIG_INVALID``; a key that names no gate (``exception``) is a ``SPEC_APPROVAL_KEY_IGNORED``
warning and is not listed.
"""

from __future__ import annotations

from dataclasses import asdict

import click
from devkit.core.cli import (
    FORMAT_OPTION,
    boundary,
    echo_json,
    echo_notices,
    exit_on_warnings,
    is_json,
    resolve_root,
    workspace_option,
)
from devkit.workflow import load_workflow_config
from devkit.worktree import read_worktree_config

from devkit_spec.cli.output import fields_line, sentinel
from devkit_spec.config import FIXED_GATES, INTEGRATION_GATE, check_approvals, read_spec_config
from devkit_spec.errors import ApprovalKeyIgnoredWarning

GATES = (*FIXED_GATES, INTEGRATION_GATE)
# Keys that name no gate: ``exception`` is a shared stage a person always handles (03 §2).
NOT_GATES = ("exception",)


@click.command(name="policy")
@workspace_option()
@FORMAT_OPTION
@boundary
def policy_cmd(workspace_root: str | None, output_format: str) -> None:
    """Print effective approval, stage, Git, routing and feedback policy; read it before routing or recording
    feedback."""
    root = resolve_root(workspace_root)
    workflow = load_workflow_config(root)
    check_approvals(workflow.approvals)
    worktree = read_worktree_config(root)
    spec = read_spec_config(root)
    gates = [*GATES, *sorted(set(workflow.approvals) - set(GATES) - set(NOT_GATES))]
    notices = [
        ApprovalKeyIgnoredWarning(
            f"[workflow.approvals] {key} has no effect: {key} is a stage a person always handles, not a gate",
            fix=f"Remove {key} from [workflow.approvals] in .devkit/config.toml",
        )
        for key in sorted(set(workflow.approvals) & set(NOT_GATES))
    ]
    approvals = {
        gate: {
            "policy": workflow.policy(gate),
            "source": "fixed" if gate in FIXED_GATES else "config" if gate in workflow.approvals else "default",
        }
        for gate in gates
    }
    stages_off = sorted(stage for stage in workflow.stages if workflow.stage_policy(stage) == "off")
    feedback = asdict(spec.feedback)
    git = {
        "worktree": spec.worktree,
        "pull_request": worktree.pull_request,
        "delete_branch": worktree.delete_branch,
        "setup": worktree.setup,
    }
    routing = {"depth_escalation": spec.depth_escalation}
    if is_json(output_format):
        echo_json(
            {
                "approvals": approvals,
                "stages_off": stages_off,
                "git": git,
                "routing": routing,
                "feedback": feedback,
                "notices": [notice.to_dict() for notice in notices],
            }
        )
        exit_on_warnings(notices)
        return
    for gate, entry in approvals.items():
        click.echo(sentinel("GATE_POLICY", gate, **entry))
    for stage in stages_off:
        click.echo(sentinel("STAGE_POLICY", stage, state="off"))
    click.echo(fields_line("GIT_POLICY", **git))
    click.echo(fields_line("ROUTING_POLICY", **routing))
    click.echo(fields_line("FEEDBACK_POLICY", **feedback))
    echo_notices(notices)
    exit_on_warnings(notices)
