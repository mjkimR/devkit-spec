"""``devkit spec proposal new|padr|handoff``: incubate a proposal, record its preliminary decisions, hand it off.

Text output (paths are relative to the workspace root):

- ``new``: ``[PROPOSAL: <id> path= dir= target_docs= workflow=]`` and, when ``proposal.md`` is bound to a workflow,
  ``[NEXT_CMD: devkit workflow next --unit <dir>]``.
- ``padr``: ``[PADR: <id> path= proposal=]``.
- ``handoff``: ``[HANDOFF: <proposal id> spec= dir= workflow=]``, then ``[TARGET_DOCS: <path>]``,
  ``[MATERIALS: <dir>]``, one ``[PROMOTED_ADR: <id> path= padr=]`` per promoted decision, one
  ``[REWRITTEN: <path>:<line> kind=link|id from= to=]`` per rewritten link or reference, one
  ``[UNRESOLVED_LINK: <path>:<line> kind= target= reason=]`` per link or reference left as it was, and
  ``[NEXT_CMD: devkit workflow next --unit <dir>]`` when ``spec.md`` is bound to a workflow.

Unresolved links are a ``SPEC_PROPOSAL_LINK_UNRESOLVED`` warning, rewritten ID references a
``SPEC_PROPOSAL_REFS_REWRITTEN`` notice and an unbound proposal or spec a ``SPEC_PROPOSAL_UNBOUND`` notice, all on
stderr.
"""

from __future__ import annotations

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
from devkit_spec.proposals import create_padr, create_proposal, handoff_proposal

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
        with_target_docs=with_target_docs,
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
            )
        )
        if created.next_command:
            click.echo(f"[NEXT_CMD: {created.next_command}]")
    echo_notices(created.notices)
    exit_on_warnings(created.notices)


@proposal_group.command(name="padr")
@click.argument("slug")
@click.argument("title")
@WORKSPACE
@FORMAT_OPTION
@boundary
def padr_cmd(slug: str, title: str, workspace_root: str | None, output_format: str) -> None:
    """Record a preliminary decision PADR-<title slug> in proposal SLUG's decisions/."""
    created = create_padr(resolve_root(workspace_root), slug, title)
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
    result = handoff_proposal(resolve_root(workspace_root), slug, direction_chosen=direction_chosen)
    if is_json(output_format):
        echo_json(result.to_dict())
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
        if result.next_command:
            click.echo(f"[NEXT_CMD: {result.next_command}]")
    echo_notices(result.notices)
    exit_on_warnings(result.notices)
