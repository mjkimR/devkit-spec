"""The inputs of a spec bundle the derivation reads: ``_Boundary`` lines of ``tasks.md``, targets of ``reconcile.md``.

``tasks.md`` is scanned outside fenced code blocks. Each ``_Boundary:`` line (bold or italic markers around the
label allowed, as a list item or not) belongs to the most recent checklist item (``- [ ]``/``- [x]``); one before
any checklist item belongs to task ``0``. Its value is split on commas; each entry loses backticks and ``(...)``
notes, and a value wrapped in ``**...**`` loses the markers.

``reconcile.md`` frontmatter is read in the shape ``RULE-reconcile-contract`` checks: ``targets`` a list of
mappings with ``file`` and ``resolution``. ``spec.md`` is optional: its ``id`` and ``status`` label the bundle
(the directory name when it has no ID).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from devkit.core import FrontmatterError
from devkit.core.frontmatter import parse

from devkit_spec.errors import EntrypointsInputInvalidError, EntrypointsInputMissingError

_CHECKLIST_ITEM = re.compile(r"^ *(?:- |\* |\+ )\[[ xX]\] (.*)$")
_BOUNDARY_LINE = re.compile(r"^\s*(?:[-*+]\s+)?\**_Boundary\**\s*:\**\s*(.*)$")
_PAREN_NOTE = re.compile(r"\([^)]*\)")
_BOLD = re.compile(r"^\*\*(.+)\*\*$")


@dataclass(frozen=True)
class Target:
    """One ``reconcile.md`` target as the derivation reads it."""

    file: str
    resolution: str


@dataclass
class TaskBoundary:
    """The ``_Boundary`` values declared under one task: ``index`` is its 1-based checklist position, ``0`` for
    values before the first task."""

    index: int
    title: str = ""
    values: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Bundle:
    """The parsed inputs of one spec bundle; ``dir`` is workspace-relative."""

    dir: str
    spec_id: str
    status: str
    targets: tuple[Target, ...]
    tasks: tuple[TaskBoundary, ...]


def parse_boundaries(text: str) -> list[TaskBoundary]:
    """The ``_Boundary`` values of ``tasks.md``, grouped by task."""
    tasks: list[TaskBoundary] = []
    current: TaskBoundary | None = None
    items = 0
    fenced = False
    for line in text.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        item = _CHECKLIST_ITEM.match(line)
        if item:
            items += 1
            current = TaskBoundary(index=items, title=item.group(1).strip())
            tasks.append(current)
            continue
        boundary = _BOUNDARY_LINE.match(line)
        if boundary is None:
            continue
        if current is None:
            current = TaskBoundary(index=0)
            tasks.append(current)
        current.values.extend(split_boundary(boundary.group(1)))
    return tasks


def split_boundary(value: str) -> list[str]:
    """The entries of one ``_Boundary`` value."""
    entries = []
    for part in value.split(","):
        part = _PAREN_NOTE.sub("", part).replace("`", "").strip()
        part = _BOLD.sub(r"\1", part).strip()
        if part:
            entries.append(part)
    return entries


def load_bundle(root: Path, directory: str) -> Bundle:
    """Read the bundle at the workspace-relative ``directory``.

    Raises ``EntrypointsInputMissingError`` without ``tasks.md`` or ``reconcile.md`` and
    ``EntrypointsInputInvalidError`` when one cannot be read or ``reconcile.md`` has no well-formed targets.
    """
    base = root / directory
    spec_id, status = base.name, ""
    try:
        spec = parse((base / "spec.md").read_text(encoding="utf-8")).data or {}
    except (OSError, UnicodeDecodeError, FrontmatterError):
        spec = {}
    if isinstance(spec.get("id"), str) and spec["id"].strip():
        spec_id = spec["id"].strip()
    if isinstance(spec.get("status"), str):
        status = spec["status"].strip()
    tasks = parse_boundaries(_read(base / "tasks.md", f"{directory}/tasks.md"))
    targets = _targets(_read(base / "reconcile.md", f"{directory}/reconcile.md"), f"{directory}/reconcile.md")
    return Bundle(dir=directory, spec_id=spec_id, status=status, targets=targets, tasks=tuple(tasks))


def _read(path: Path, relative: str) -> str:
    if not path.is_file():
        raise EntrypointsInputMissingError(f"bundle input missing: {relative}", target_files=[relative])
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise EntrypointsInputInvalidError(f"cannot read {relative}: {exc}", target_files=[relative]) from exc


def _targets(text: str, relative: str) -> tuple[Target, ...]:
    def invalid(problem: str) -> EntrypointsInputInvalidError:
        return EntrypointsInputInvalidError(f"cannot read {relative}: {problem}", target_files=[relative])

    try:
        data = parse(text).data
    except FrontmatterError as exc:
        raise invalid(exc.message) from exc
    if data is None:
        raise invalid("no frontmatter")
    value = data.get("targets") or []
    if not isinstance(value, list):
        raise invalid("targets must be a list")
    targets = []
    for position, entry in enumerate(value, 1):
        if not isinstance(entry, dict) or not isinstance(entry.get("file", ""), str):
            raise invalid(f"targets[{position}] must be a mapping with a string file")
        resolution = entry.get("resolution")
        targets.append(Target(file=entry.get("file", ""), resolution=resolution if isinstance(resolution, str) else ""))
    return tuple(targets)
