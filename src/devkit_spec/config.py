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

[tool.spec.feedback]
capture = "observed"       # concrete observations recorded autonomously; or requested-only
coverage = "repo"          # repository-owned tools and assets; or repo-and-upstream
detail = "standard"        # brief, standard or detailed
reminder = "contextual"    # contextual or off

[tool.spec.scope]          # the work-scope registry (devkit spec scope); every key is optional
shared_path = "/srv/scope" # absolute; default: devkit-spec-scope/ in the Git common directory
namespace = "team"         # default: a hash of the Git common directory
timeout = 10               # seconds per registry command, 1 to 300
```

``template`` is the ``devkit.config_template`` extension: ``devkit config template`` writes these tables into
``.devkit/config.toml`` as comments, each key at the default ``read_spec_config`` applies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from devkit.core import TemplateKey, TemplateTable, is_safe_relpath, read_project_config

from devkit_spec.errors import SpecConfigError

TABLE = "spec"
GLOBAL = "global"
NAMESPACE_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PACKAGES_DIR = "docs/packages"
SCOPE_NAMESPACE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
SCOPE_TIMEOUT_DEFAULT = 10
SCOPE_TIMEOUT_RANGE = (1, 300)
FEEDBACK_CHOICES = {
    "capture": ("observed", "requested-only"),
    "coverage": ("repo", "repo-and-upstream"),
    "detail": ("brief", "standard", "detailed"),
    "reminder": ("contextual", "off"),
}


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
class FeedbackConfig:
    """Repository-first observation policy consumed by the feedback skills through ``spec policy``."""

    capture: str = "observed"
    coverage: str = "repo"
    detail: str = "standard"
    reminder: str = "contextual"


@dataclass(frozen=True)
class SpecConfig:
    worktree: bool = True
    namespaces: tuple[Namespace, ...] = field(default=())
    scope: ScopeConfig = field(default=ScopeConfig())
    feedback: FeedbackConfig = field(default=FeedbackConfig())


def template() -> list[TemplateTable]:
    """``[tool.spec]`` and its tables for devkit's commented config template, at ``read_spec_config``'s defaults."""
    defaults = SpecConfig()
    low, high = SCOPE_TIMEOUT_RANGE
    return [
        TemplateTable(
            (
                TemplateKey(
                    "worktree", defaults.worktree, "route 2 and above (formal specs, proposals) run in a task worktree"
                ),
            ),
        ),
        TemplateTable(
            (
                TemplateKey(
                    "name",
                    help=f"lowercase words joined by -, not {GLOBAL!r}; its Living Spec is {PACKAGES_DIR}/<name>/",
                    kind="string",
                    example="api",
                ),
                TemplateKey(
                    "path",
                    help="the package's workspace-relative source directory",
                    kind="string",
                    example="services/api",
                ),
            ),
            path=("namespaces",),
            help="A package of a monorepo with its own Living Spec; one table per package.",
            array=True,
        ),
        TemplateTable(
            (
                TemplateKey(
                    "shared_path",
                    help="unset: devkit-spec-scope/ in the Git common directory; clones that share the path and the"
                    " namespace share one registry",
                    kind="string, an absolute directory (or one starting with ~)",
                    example="/srv/devkit-spec-scope",
                ),
                TemplateKey(
                    "namespace",
                    help="unset: a hash of the Git common directory",
                    kind="string of letters, digits, '.', '_' and '-', not starting with '.'",
                    example="team",
                ),
                TemplateKey(
                    "timeout",
                    defaults.scope.timeout,
                    "seconds one registry command may wait",
                    kind=f"integer from {low} to {high}",
                ),
            ),
            path=("scope",),
            help="The work-scope registry of `devkit spec scope`.",
        ),
        TemplateTable(
            tuple(
                TemplateKey(
                    key,
                    getattr(defaults.feedback, key),
                    help_text,
                    kind=" | ".join(f'"{choice}"' for choice in FEEDBACK_CHOICES[key]),
                )
                for key, help_text in (
                    (
                        "capture",
                        "observed records concrete observations autonomously; requested-only waits for explicit feedback requests",
                    ),
                    (
                        "coverage",
                        "repository-owned assets first; repo-and-upstream also covers tools used from upstream",
                    ),
                    (
                        "detail",
                        "brief: context and evidence; standard: kind-specific assessment; detailed: reproduction, versions and conditions",
                    ),
                    (
                        "reminder",
                        "contextual suggests a sweep for reusable observations; off disables optional reminders",
                    ),
                )
            ),
            path=("feedback",),
            help="Feedback capture policy; explicit user feedback requests override autonomous capture and coverage limits.",
        ),
    ]


def read_spec_config(root: Path) -> SpecConfig:
    """The ``[tool.spec]`` table of the project at ``root``; defaults when absent."""
    tool = read_project_config(root).get("tool", {})
    table = tool.get(TABLE, {}) if isinstance(tool, dict) else None
    if not isinstance(table, dict):
        raise SpecConfigError("config tool.spec: expected a table")
    unknown = sorted(set(table) - {"worktree", "namespaces", "scope", "feedback"})
    if unknown:
        raise SpecConfigError(f"config tool.spec: unknown keys: {', '.join(unknown)}")
    worktree = table.get("worktree", True)
    if not isinstance(worktree, bool):
        raise SpecConfigError(f"config tool.spec.worktree: expected true or false, got {worktree!r}")
    return SpecConfig(
        worktree=worktree,
        namespaces=_namespaces(table.get("namespaces", [])),
        scope=_scope(table.get("scope", {})),
        feedback=_feedback(table.get("feedback", {})),
    )


def _feedback(value: object) -> FeedbackConfig:
    where = "config tool.spec.feedback"
    if not isinstance(value, dict):
        raise SpecConfigError(f"{where}: expected a table")
    unknown = sorted(set(value) - set(FEEDBACK_CHOICES))
    if unknown:
        raise SpecConfigError(f"{where}: unknown keys: {', '.join(unknown)}")
    defaults = FeedbackConfig()
    settings: dict[str, str] = {}
    for key, choices in FEEDBACK_CHOICES.items():
        entry = value.get(key, getattr(defaults, key))
        if not isinstance(entry, str) or entry not in choices:
            raise SpecConfigError(f"{where}.{key}: expected {' | '.join(choices)}, got {entry!r}")
        settings[key] = entry
    return FeedbackConfig(**settings)


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
        if not isinstance(path, str) or not is_safe_relpath(path):
            raise SpecConfigError(f"{where}: path must be a workspace-relative directory, got {path!r}")
        if not is_safe_relpath(path, canonical=True):
            canonical = PurePosixPath(path).as_posix()
            raise SpecConfigError(
                f"{where}: path must be in canonical form (no ./, //, or trailing /), got {path!r}",
                fix=f"Write path = {canonical!r} in [[tool.spec.namespaces]] of .devkit/config.toml",
            )
        if any(other.name == name for other in found) or any(other.path == path for other in found):
            raise SpecConfigError(f"{where}: name {name!r} or path {path!r} is already registered")
        found.append(Namespace(name, path))
    return tuple(found)
