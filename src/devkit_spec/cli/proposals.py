"""``devkit spec proposal new|padr|handoff|prune``: incubate a proposal, record its preliminary decisions, hand it off.

Text output (paths are relative to the workspace root):

- ``new``: ``[PROPOSAL: <id> path= dir= target_docs= workflow=]``, with a trailing ``namespace=`` when the bundle
  reports one (``CreatedProposal.namespace``), and, when ``proposal.md`` is bound to a workflow,
  ``[NEXT_CMD: devkit workflow next --unit <dir>]``.
- ``padr``: ``[PADR: <id> path= proposal=]``.
- ``prune``: ``[PRUNED: <dir>]`` per empty proposal directory removed, else ``[OK: nothing to prune]``.
- ``handoff``: ``[HANDOFF: <proposal id> spec= dir= workflow=]``, then ``[TARGET_DOCS: <path>]``,
  ``[MATERIALS: <dir>]``, one ``[PROMOTED_ADR: <id> path= padr=]`` per promoted decision, one
  ``[REWRITTEN: <path>:<line> kind=link|id from= to=]`` per rewritten link or reference, one
  ``[UNRESOLVED_LINK: <path>:<line> kind= target= reason=]`` per link or reference left as it was,
  ``[SCOPE: <task> namespace= ... token=]`` when it registered the bundle's work scope, and
  ``[NEXT_CMD: devkit workflow next --unit <dir>]`` when ``spec.md`` is bound to a workflow.

A handoff inside a linked worktree with ``[tool.spec] worktree = true`` registers the new bundle in the work-scope
registry (``devkit spec scope register``); a registration failure is a ``SPEC_SCOPE_REGISTER_FAILED`` warning and
leaves the handoff done.

Unresolved links are a ``SPEC_PROPOSAL_LINK_UNRESOLVED`` warning, rewritten ID references a
``SPEC_PROPOSAL_REFS_REWRITTEN`` notice and an unbound proposal or spec a ``SPEC_PROPOSAL_UNBOUND`` notice, all on
stderr.
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
    "--handoff-workflow",
    default=None,
    help="Workflow the spec follows after handoff (handoff_workflow) [default at handoff: direct-delivery]",
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
@click.option("--with-target-docs", is_flag=True, help="Also scaffold target-docs.md, the Living Spec blueprint")
@WORKSPACE
@FORMAT_OPTION
@boundary
def new_cmd(
    slug: str,
    title: str | None,
    target_area: str | None,
    milestone: str | None,
    handoff_workflow: str | None,
    namespace: str | None,
    summary: str | None,
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
        handoff_workflow=handoff_workflow,
        namespace=namespace,
        summary=summary,
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
@WORKSPACE
@FORMAT_OPTION
@boundary
def padr_cmd(slug: str, title: str, summary: str | None, workspace_root: str | None, output_format: str) -> None:
    """Record a preliminary decision PADR-<title slug> in proposal SLUG's decisions/."""
    created = create_padr(resolve_root(workspace_root), slug, title, summary=summary)
    if is_json(output_format):
        echo_json(created.to_dict())
        return
    click.echo(sentinel("PADR", created.id, path=created.path, proposal=created.proposal))


@proposal_group.command(name="handoff")
@click.argument("slug")
@click.option(
    "--direction-chosen",
    is_flag=True,
    help="The user chose this draft or reviewing proposal's direction; hand it off without status: accepted",
)
@WORKSPACE
@FORMAT_OPTION
@boundary
def handoff_cmd(slug: str, direction_chosen: bool, workspace_root: str | None, output_format: str) -> None:
    """Hand the approved proposal SLUG off to a spec bundle and remove the proposal."""
    root = resolve_root(workspace_root)
    result = handoff_proposal(root, slug, direction_chosen=direction_chosen)
    registered, scope_notices = auto_register(root, result.dir, source=SOURCE_HANDOFF)
    result.notices += scope_notices
    if is_json(output_format):
        scope = registered_dict(registered.location, registered.record, registered.token) if registered else None
        echo_json(result.to_dict() | {"scope": scope})
    else:
        click.echo(sentinel("HANDOFF", result.proposal, spec=result.spec, dir=result.dir, workflow=result.workflow))
        if result.target_docs:
            click.echo(sentinel("TARGET_DOCS", result.target_docs))
        if result.materials:
            click.echo(sentinel("MATERIALS", result.materials))
        for decision in result.decisions:
            click.echo(sentinel("PROMOTED_ADR", decision.id, path=decision.path, padr=decision.padr))
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
