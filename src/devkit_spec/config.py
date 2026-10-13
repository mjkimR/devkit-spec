"""devkit-spec's project policy: the ``[tool.spec]`` table of ``.devkit/config.toml``.

devkit passes ``[tool.<name>]`` tables through unread, so devkit-spec owns
this one. Policy that devkit already models stays in devkit's own tables:
approvals and stage switches in ``[workflow.approvals]`` and
``[workflow.stages]``, pull requests and branch cleanup in ``[worktree]``.

```toml
[tool.spec]
worktree = true   # route 2 and above (formal specs, proposals) run in a task worktree

[[tool.spec.namespaces]]   # a package of a monorepo with its own Living Spec under docs/packages/<name>/
name = "api"
path = "services/api"

[tool.spec.scope]          # the work-scope registry (devkit spec scope); every key is optional
shared_path = "/srv/scope" # absolute; default: devkit-spec-scope/ in the Git common directory
namespace = "team"         # default: a hash of the Git common directory
timeout = 10               # seconds per registry command, 1 to 300
```
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from devkit.core import is_safe_relpath, read_project_config

from devkit_spec.errors import SpecConfigError

TABLE = "spec"
GLOBAL = "global"
NAMESPACE_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PACKAGES_DIR = "docs/packages"
SCOPE_NAMESPACE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
SCOPE_TIMEOUT_DEFAULT = 10
SCOPE_TIMEOUT_RANGE = (1, 300)


@dataclass(frozen=True)
class Namespace:
    """A package of the workspace: ``path`` is its source directory, ``docs`` its Living Spec root."""

    name: str
    path: str

    @property
    def docs(self) -> str:
        return f"{PACKAGES_DIR}/{self.name}"


@dataclass(frozen=True)
class ScopeConfig:
    """``[tool.spec.scope]``: where the work-scope registry lives and how long one command may wait.

    ``shared_path`` is absolute (``~`` expanded) or ``None`` for ``devkit-spec-scope/`` in the Git common directory;
    ``namespace`` ``None`` is a hash of that common directory; ``timeout`` is in seconds.
    """

    shared_path: Path | None = None
    namespace: str | None = None
    timeout: int = SCOPE_TIMEOUT_DEFAULT


@dataclass(frozen=True)
class SpecConfig:
    worktree: bool = True
    namespaces: tuple[Namespace, ...] = field(default=())
    scope: ScopeConfig = field(default=ScopeConfig())


def read_spec_config(root: Path) -> SpecConfig:
    """The ``[tool.spec]`` table of the project at ``root``; defaults when absent."""
    tool = read_project_config(root).get("tool", {})
    table = tool.get(TABLE, {}) if isinstance(tool, dict) else None
    if not isinstance(table, dict):
        raise SpecConfigError("config tool.spec: expected a table")
    unknown = sorted(set(table) - {"worktree", "namespaces", "scope"})
    if unknown:
        raise SpecConfigError(f"config tool.spec: unknown keys: {', '.join(unknown)}")
    worktree = table.get("worktree", True)
    if not isinstance(worktree, bool):
        raise SpecConfigError(f"config tool.spec.worktree: expected true or false, got {worktree!r}")
    return SpecConfig(
        worktree=worktree, namespaces=_namespaces(table.get("namespaces", [])), scope=_scope(table.get("scope", {}))
    )


def _scope(value: object) -> ScopeConfig:
    where = "config tool.spec.scope"
    if not isinstance(value, dict):
        raise SpecConfigError(f"{where}: expected a table")
    unknown = sorted(set(value) - {"shared_path", "namespace", "timeout"})
    if unknown:
        raise SpecConfigError(f"{where}: unknown keys: {', '.join(unknown)}")
    shared = value.get("shared_path")
    shared_path: Path | None = None
    if shared is not None:
        expanded = Path(shared).expanduser() if isinstance(shared, str) and shared.strip() else None
        if expanded is None or not expanded.is_absolute():
            raise SpecConfigError(
                f"{where}.shared_path: expected an absolute directory path (or one starting with ~), got {shared!r}"
            )
        shared_path = expanded
    namespace = value.get("namespace")
    if namespace is not None and (not isinstance(namespace, str) or not SCOPE_NAMESPACE.match(namespace)):
        raise SpecConfigError(
            f"{where}.namespace: expected letters, digits, '.', '_' and '-' not starting with '.', got {namespace!r}"
        )
    timeout = value.get("timeout", SCOPE_TIMEOUT_DEFAULT)
    low, high = SCOPE_TIMEOUT_RANGE
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not low <= timeout <= high:
        raise SpecConfigError(f"{where}.timeout: expected whole seconds from {low} to {high}, got {timeout!r}")
    return ScopeConfig(shared_path=shared_path, namespace=namespace, timeout=timeout)


def _namespaces(value: object) -> tuple[Namespace, ...]:
    if not isinstance(value, list):
        raise SpecConfigError("config tool.spec.namespaces: expected an array of tables")
    found: list[Namespace] = []
    for position, entry in enumerate(value):
        where = f"config tool.spec.namespaces[{position}]"
        if not isinstance(entry, dict) or set(entry) != {"name", "path"}:
            raise SpecConfigError(f"{where}: expected exactly the keys name and path")
        name, path = entry["name"], entry["path"]
        if not isinstance(name, str) or not NAMESPACE_NAME.match(name) or name == GLOBAL:
            raise SpecConfigError(f"{where}: name must be lowercase words joined by - and not {GLOBAL!r}, got {name!r}")
        if not isinstance(path, str) or not is_safe_relpath(path) or path.endswith("/"):
            raise SpecConfigError(f"{where}: path must be a workspace-relative directory, got {path!r}")
        if any(other.name == name for other in found) or any(other.path == path for other in found):
            raise SpecConfigError(f"{where}: name {name!r} or path {path!r} is already registered")
        found.append(Namespace(name, path))
    return tuple(found)
