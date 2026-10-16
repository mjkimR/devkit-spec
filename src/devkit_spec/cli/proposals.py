"""``devkit spec proposal new|padr|handoff|prune|check``: incubate a proposal, record its preliminary decisions, hand
it off, and guard Backlog changes.

Text output (paths are relative to the workspace root):

- ``new``: ``[PROPOSAL: <id> path= dir= target_docs= workflow= planning_effort= dev_effort=]``, with a trailing
  ``namespace=`` when the bundle reports one (``CreatedProposal.namespace``), and, when ``proposal.md`` is bound to a
  workflow, ``[NEXT_CMD: devkit workflow next --unit <dir>]``.
- ``padr``: ``[PADR: <id> path= proposal=]``.
- ``prune``: ``[PRUNED: <dir>]`` per empty proposal directory removed, else ``[OK: nothing to prune]``.
- ``check``: ``[PROPOSAL: <id> path= status=draft editable=yes]`` when Backlog may edit, split or delete the proposal;
  ``SPEC_PROPOSAL_IN_PLANNING`` while its ``plan-<slug>`` exists or once it left ``draft``.
- ``handoff``: ``[HANDOFF: <proposal id> spec= dir= workflow=]`` (with ``dev_effort=`` when the proposal declared it),
  then ``[TARGET_DOCS: <path>]``,
  ``[MATERIALS: <dir>]``, one ``[PROMOTED_ADR: <id> path= padr=]`` per promoted decision, one
  ``[DROPPED_RECORD: <path>]`` per workflow record of the proposal unit removed with it, one
  ``[CARRIED_GATE: <request> decision=<path>]`` per approval of the proposal (``gate:plan-intent``,
  ``gate:plan-accept``) recorded in the spec under its name, one
  ``[REWRITTEN: <path>:<line> kind=link|id from= to=]`` per rewritten link or reference, one
  ``[UNRESOLVED_LINK: <path>:<line> kind= target= reason=]`` per link or reference left as it was,
  ``[SCOPE: <task> namespace= ... token=]`` when it registered the bundle's work scope, and
  ``[NEXT_CMD: devkit workflow next --unit <dir>]`` when ``spec.md`` is bound to a workflow.

A handoff inside a linked worktree registers the new bundle in the work-scope registry (``devkit spec scope
register``) at either ``[tool.spec] worktree`` level; a registration failure is a ``SPEC_SCOPE_REGISTER_FAILED``
warning and leaves the handoff done.

A gate of the spec that could not be recorded is a ``SPEC_PROPOSAL_GATE_NOT_CARRIED`` warning, unresolved links a
``SPEC_PROPOSAL_LINK_UNRESOLVED`` warning, rewritten ID references a ``SPEC_PROPOSAL_REFS_REWRITTEN`` notice and an
unbound proposal or spec a ``SPEC_PROPOSAL_UNBOUND`` notice, all on stderr.
"""

from __future__ import annotations

from pathlib import Path

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

from devkit_spec.cli.output import sentinel
from devkit_spec.cli.scope import echo_registered, registered_dict
from devkit_spec.proposals import create_padr, create_proposal, handoff_proposal, prune_proposals
from devkit_spec.proposals.backlog import check_backlog_editable
from devkit_spec.scope import SOURCE_HANDOFF, auto_register

WORKSPACE = workspace_option()


@click.group(name="proposal")
def proposal_group() -> None:
    """Incubate proposals in docs/proposals/ and hand approved ones off to spec bundles."""


@proposal_group.command(name="new")
@click.argument("slug")
@click.option("--title", "-t", default=None, help="Proposal title [default: the slug]")
@click.option("--target-area", "-a", default=None, help="Capability area the proposal targets (capabilities/<area>/)")
@click.option("--milestone", "-m", default=None, help="Milestone, phase or release; carried to spec.md on handoff")
@click.option(
    "--task-kind",
    default=None,
    help="task-kind of the work: feature or bugfix; the spec follows sdd-spec-<task-kind> after handoff "
    "[default: feature]",
)
@click.option(
    "--planning-effort",
    default=None,
    help="Recommended activity-effort hint for Planning: low, medium or high [default: medium]",
)
@click.option(
    "--dev-effort",
    default=None,
    help="Recommended activity-effort hint for Development: low, medium or high [default: medium]",
)
@click.option(
    "--namespace",
    default=None,
    help="Document namespace of the bundle: global or a registered package; carried to spec.md "
    "[default: the current directory's]",
)
@click.option(
    "--summary",
    default=None,
    help="One or two English sentences: what the proposal changes and why; carried to spec.md [default: none]",
)
@click.option(
    "--supersedes",
    default=None,
    help="PROP-<slug> of the accepted proposal this draft replaces (close by supersede) [default: none]",
)
@click.option("--needs-decompose", is_flag=True, help="Mark the draft to be split in Backlog before Planning starts")
@click.option("--with-target-docs", is_flag=True, help="Also scaffold target-docs.md, the Living Spec blueprint")
@WORKSPACE
@FORMAT_OPTION
@boundary
def new_cmd(
    slug: str,
    title: str | None,
    target_area: str | None,
    milestone: str | None,
    task_kind: str | None,
    planning_effort: str | None,
    dev_effort: str | None,
    namespace: str | None,
    summary: str | None,
    supersedes: str | None,
    needs_decompose: bool,
    with_target_docs: bool,
    workspace_root: str | None,
    output_format: str,
) -> None:
    """Scaffold the proposal bundle docs/proposals/PROP-<SLUG>/."""
    created = create_proposal(
        resolve_root(workspace_root),
        slug,
        title=title,
        target_area=target_area,
        milestone=milestone,
        task_kind=task_kind,
        planning_effort=planning_effort,
        dev_effort=dev_effort,
        namespace=namespace,
        summary=summary,
        supersedes=supersedes,
        needs_decompose=needs_decompose,
        with_target_docs=with_target_docs,
        cwd=Path.cwd(),
    )
    if is_json(output_format):
        echo_json(created.to_dict())
    else:
        click.echo(
            sentinel(
                "PROPOSAL",
                created.id,
                path=created.path,
                dir=created.dir,
                target_docs=created.target_docs,
                workflow=created.workflow,
                planning_effort=created.planning_effort,
                dev_effort=created.dev_effort,
                **({"namespace": created.namespace} if created.namespace else {}),
            )
        )
        if created.next_command:
            click.echo(f"[NEXT_CMD: {created.next_command}]")
    echo_notices(created.notices)
    exit_on_warnings(created.notices)


@proposal_group.command(name="padr")
@click.argument("slug")
@click.argument("title")
@click.option(
    "--summary",
    default=None,
    help="One or two English sentences: what the decision defines; kept by the promoted ADR [default: none]",
)
@click.option(
    "--slug",
    "padr_slug",
    default=None,
    help="Slug of the PADR ID and file name; its first word needs a letter [default: the title's slug]",
)
@WORKSPACE
@FORMAT_OPTION
@boundary
def padr_cmd(
    slug: str,
    title: str,
    summary: str | None,
    padr_slug: str | None,
    workspace_root: str | None,
    output_format: str,
) -> None:
    """Record a preliminary decision PADR-<slug> in proposal SLUG's decisions/ (the title's slug unless --slug)."""
    created = create_padr(resolve_root(workspace_root), slug, title, summary=summary, padr_slug=padr_slug)
    if is_json(output_format):
        echo_json(created.to_dict())
        return
    click.echo(sentinel("PADR", created.id, path=created.path, proposal=created.proposal))


@proposal_group.command(name="handoff")
@click.argument("slug")
@WORKSPACE
@FORMAT_OPTION
@boundary
def handoff_cmd(slug: str, workspace_root: str | None, output_format: str) -> None:
    """Hand the accepted proposal SLUG off to a spec bundle sdd-spec-<task_kind> and remove the proposal."""
    root = resolve_root(workspace_root)
    result = handoff_proposal(root, slug)
    registered, scope_notices = auto_register(root, result.dir, source=SOURCE_HANDOFF)
    result.notices += scope_notices
    if is_json(output_format):
        scope = registered_dict(registered.location, registered.record, registered.token) if registered else None
        echo_json(result.to_dict() | {"scope": scope})
    else:
        click.echo(
            sentinel(
                "HANDOFF",
                result.proposal,
                spec=result.spec,
                dir=result.dir,
                workflow=result.workflow,
                **({"dev_effort": result.dev_effort} if result.dev_effort else {}),
            )
        )
        if result.target_docs:
            click.echo(sentinel("TARGET_DOCS", result.target_docs))
        if result.materials:
            click.echo(sentinel("MATERIALS", result.materials))
        for decision in result.decisions:
            click.echo(sentinel("PROMOTED_ADR", decision.id, path=decision.path, padr=decision.padr))
        for path in result.dropped_records:
            click.echo(sentinel("DROPPED_RECORD", path))
        for gate in result.carried_gates:
            click.echo(sentinel("CARRIED_GATE", gate.request, decision=gate.decision))
        for item in result.rewritten:
            click.echo(
                sentinel("REWRITTEN", f"{item.path}:{item.line}", kind=item.kind, **{"from": item.old, "to": item.new})
            )
        for item in result.unresolved:
            click.echo(
                sentinel(
                    "UNRESOLVED_LINK",
                    f"{item.path}:{item.line}",
                    kind=item.kind,
                    target=item.target,
                    reason=item.reason,
                )
            )
        if registered:
            echo_registered(registered.location, registered.record, registered.token)
        if result.next_command:
            click.echo(f"[NEXT_CMD: {result.next_command}]")
    echo_notices(result.notices)
    exit_on_warnings(result.notices)


@proposal_group.command(name="prune")
@click.argument("slug", required=False)
@workspace_option()
@FORMAT_OPTION
@boundary
def prune_cmd(slug: str | None, workspace_root: str | None, output_format: str) -> None:
    """Remove the empty docs/proposals/PROP-<SLUG>/ directories a merged handoff left (all of them without SLUG).

    Run it in the base checkout after `devkit worktree finish`; a directory holding any file is kept.
    """
    pruned = prune_proposals(resolve_root(workspace_root), slug)
    if is_json(output_format):
        echo_json({"pruned": pruned})
    elif pruned:
        for path in pruned:
            click.echo(sentinel("PRUNED", path))
    else:
        click.echo("[OK: nothing to prune]")


@proposal_group.command(name="check")
@click.argument("slug")
@WORKSPACE
@FORMAT_OPTION
@boundary
def check_cmd(slug: str, workspace_root: str | None, output_format: str) -> None:
    """Check that Backlog may edit, split or delete proposal SLUG: a draft without a plan-<slug> branch.

    Run it before every Backlog change of a proposal. Remote branches count once fetched (git fetch first).
    """
    checked = check_backlog_editable(resolve_root(workspace_root), slug)
    if is_json(output_format):
        echo_json(checked.to_dict())
        return
    click.echo(sentinel("PROPOSAL", checked.id, path=checked.path, status=checked.status, editable="yes"))
