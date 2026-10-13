"""Text output helpers shared by the ``devkit spec`` commands (devkit's sentinel conventions)."""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Sequence

import click

_BARE = re.compile(r'[^\s"\]=]+')
COMMAND = "devkit spec"


def value(item: object) -> str:
    """``-`` when empty, ``yes``/``no`` for a boolean, bare without spaces, quotes or brackets, else a JSON string."""
    if item is None or item == "":
        return "-"
    if isinstance(item, bool):
        return "yes" if item else "no"
    text = str(item)
    return text if _BARE.fullmatch(text) else json.dumps(text, ensure_ascii=False)


def sentinel(name: str, positional: object, /, **fields: object) -> str:
    """``[KIND: <positional> key=value ...]``."""
    parts = [value(positional), *(f"{key}={value(item)}" for key, item in fields.items())]
    return f"[{name}: {' '.join(parts)}]"


def echo_page(total: int, offset: int, limit: int, count: int, next_command: Sequence[str]) -> None:
    """``[PAGE: total= offset= limit= count= next=]`` and, when more items follow, ``[NEXT_CMD: ...]``.

    ``next_command`` is the command's own argument list without ``--offset``; ``limit`` ``0`` means no limit.
    """
    following = offset + count if limit and offset + count < total else None
    click.echo(f"[PAGE: total={total} offset={offset} limit={limit} count={count} next={value(following)}]")
    if following is not None:
        args = [*next_command, "--offset", str(following)]
        click.echo(f"[NEXT_CMD: {COMMAND} {shlex.join(args)}]")


def page[T](items: Sequence[T], offset: int, limit: int) -> list[T]:
    """``items[offset:offset + limit]``; ``limit`` ``0`` means all from ``offset``."""
    return list(items[offset : offset + limit] if limit else items[offset:])
