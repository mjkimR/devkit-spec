"""``devkit spec new``: create a spec bundle without a proposal.

Text output: ``[SPEC: SPEC-<slug> path=<bundle dir> workflow=<id|->]`` and, when ``spec.md`` is bound to a workflow,
``[NEXT_CMD: devkit workflow next --unit <dir>]``. An unbound spec is a ``SPEC_UNBOUND`` notice on stderr.
"""

from __future__ import annotations

from datetime import datetime

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
from devkit_spec.proposals import create_spec


@click.command(name="new")
@click.argument("slug")
@click.option("--title", "-t", default=None, help="Spec title [default: the slug]")
@click.option(
    "--workflow",
    default=None,
    help="Workflow spec.md is bound to (bugfix adds kind: bugfix) [default: direct-delivery]",
)
@click.option(
    "--date",
    "day",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Date of the bundle directory and created field, YYYY-MM-DD [default: today]",
)
@workspace_option()
@FORMAT_OPTION
@boundary
def spec_new_cmd(
    slug: str,
    title: str | None,
    workflow: str | None,
    day: datetime | None,
    workspace_root: str | None,
    output_format: str,
) -> None:
    """Create the spec bundle specs/<YYYY-MM>/<YYYYMMDD>-<SLUG>/ (SPEC, PLAN and TASKS skeletons) and bind spec.md."""
    created = create_spec(
        resolve_root(workspace_root), slug, title=title, workflow=workflow, day=day.date() if day else None
    )
    if is_json(output_format):
        echo_json(created.to_dict())
    else:
        click.echo(sentinel("SPEC", created.id, path=created.dir, workflow=created.workflow))
        if created.next_command:
            click.echo(f"[NEXT_CMD: {created.next_command}]")
    echo_notices(created.notices)
    exit_on_warnings(created.notices)
