"""``devkit spec``: the command group devkit-spec mounts under the ``devkit`` command line.

devkit's root group finds it through the ``devkit.commands`` entry point
``spec`` and imports this module only when ``devkit spec`` runs. Commands
follow devkit's output contract: each one is built on ``devkit.core.cli``
(``boundary``, ``FORMAT_OPTION``, ``workspace_option``) and raises
``AdvisoryError`` subclasses with ``SPEC_`` codes. ``--version`` prints one
``[VERSION: devkit-spec <version>]`` line; ``devkit --version`` reports devkit
itself.
"""

from __future__ import annotations

import click

from devkit_spec.cli.documents import list_cmd, refs_cmd, resolve_cmd
from devkit_spec.cli.entrypoints import entrypoints_group
from devkit_spec.cli.policy import policy_cmd
from devkit_spec.cli.proposals import proposal_group
from devkit_spec.cli.scope import scope_group
from devkit_spec.cli.search import search_cmd
from devkit_spec.cli.specs import spec_new_cmd

DISTRIBUTION = "devkit-spec"


def _print_version(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    from importlib.metadata import version

    click.echo(f"[VERSION: {DISTRIBUTION} {version(DISTRIBUTION)}]")
    ctx.exit()


@click.group(name="spec")
@click.option(
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=_print_version,
    help=f"Print a [VERSION: {DISTRIBUTION} <version>] line and exit",
)
def cli() -> None:
    """Spec-driven development: Living Spec documents, feature specs and their reconciliation."""


cli.add_command(resolve_cmd)
cli.add_command(refs_cmd)
cli.add_command(list_cmd)
cli.add_command(policy_cmd)
cli.add_command(proposal_group)
cli.add_command(search_cmd)
cli.add_command(spec_new_cmd)
cli.add_command(entrypoints_group)
cli.add_command(scope_group)
