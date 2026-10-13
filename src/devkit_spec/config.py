"""devkit-spec's project policy: the ``[tool.spec]`` table of ``.devkit/config.toml``.

devkit passes ``[tool.<name>]`` tables through unread, so devkit-spec owns
this one. Policy that devkit already models stays in devkit's own tables:
approvals and stage switches in ``[workflow.approvals]`` and
``[workflow.stages]``, pull requests and branch cleanup in ``[worktree]``.

```toml
[tool.spec]
worktree = true   # route 2 and above (formal specs, proposals) run in a task worktree
```
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from devkit.core import read_project_config

from devkit_spec.errors import SpecConfigError

TABLE = "spec"


@dataclass(frozen=True)
class SpecConfig:
    worktree: bool = True


def read_spec_config(root: Path) -> SpecConfig:
    """The ``[tool.spec]`` table of the project at ``root``; defaults when absent."""
    tool = read_project_config(root).get("tool", {})
    table = tool.get(TABLE, {}) if isinstance(tool, dict) else None
    if not isinstance(table, dict):
        raise SpecConfigError("config tool.spec: expected a table")
    unknown = sorted(set(table) - {"worktree"})
    if unknown:
        raise SpecConfigError(f"config tool.spec: unknown keys: {', '.join(unknown)}")
    worktree = table.get("worktree", True)
    if not isinstance(worktree, bool):
        raise SpecConfigError(f"config tool.spec.worktree: expected true or false, got {worktree!r}")
    return SpecConfig(worktree=worktree)
