"""Document namespaces: the packages of a monorepo, each with its own Living Spec under ``docs/packages/<name>/``.

A namespace narrows what browsing shows, never what exists: IDs, ``resolve``, ``refs`` and the reference rules stay
repository-wide. Every document belongs to one namespace:

- a document under ``docs/packages/<name>/`` belongs to ``<name>``;
- the files of a spec bundle (``specs/<YYYY-MM>/<bundle>/...``) or a proposal bundle
  (``docs/proposals/<bundle>/...``) belong to the namespace their ``spec.md`` or ``proposal.md`` names in its
  ``namespace`` frontmatter field, so a bundle keeps its package wherever the work happens; a single-file proposal
  (``docs/proposals/<name>.md``) belongs to the namespace its own ``namespace`` field names;
- everything else is ``global``.

A selection (``--namespace``, ``--all-namespaces``, or detected from the current directory) shows its namespace plus
the global documents. The current directory selects the namespace whose docs root contains it, else the one whose
source path contains it (the deepest one), else nothing (every namespace).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from devkit.core.errors import ArgumentError

from devkit_spec.config import GLOBAL, Namespace
from devkit_spec.documents import Document, DocumentIndex


@dataclass(frozen=True)
class Selection:
    """``name`` ``None`` selects every namespace; ``global`` only the global documents; any other name that namespace
    and the global documents."""

    name: str | None = None

    def matches(self, namespace: str) -> bool:
        return self.name is None or namespace == self.name or (self.name != GLOBAL and namespace == GLOBAL)


def _within(path: str, root: str) -> bool:
    return root == "" or path == root or path.startswith(f"{root}/")


def detect(namespaces: Sequence[Namespace], root: Path, cwd: Path) -> str | None:
    """The namespace the current directory selects, or ``None`` outside every package."""
    try:
        relative = cwd.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    relative = "" if relative == "." else relative
    for namespace in namespaces:
        if _within(relative, namespace.docs):
            return namespace.name
    containing = [namespace for namespace in namespaces if _within(relative, namespace.path)]
    return max(containing, key=lambda namespace: len(namespace.path)).name if containing else None


def require(namespaces: Sequence[Namespace], name: str) -> str:
    """``name`` when it is ``global`` or a registered namespace; ``ArgumentError`` naming ``--namespace`` otherwise."""
    known = [GLOBAL, *(namespace.name for namespace in namespaces)]
    if name not in known:
        raise ArgumentError(
            f"--namespace {name}: not a registered namespace",
            target_files=["--namespace"],
            fix=f"Pass one of {', '.join(known)} (registered in [[tool.spec.namespaces]] of .devkit/config.toml)",
        )
    return name


def select(namespaces: Sequence[Namespace], root: Path, cwd: Path, name: str | None, every: bool) -> Selection:
    """The selection of ``--namespace NAME`` / ``--all-namespaces``, else the one the current directory implies.

    ``NAME`` must be ``global`` or a registered namespace (``ArgumentError`` otherwise), also when none is registered;
    without registered namespaces every selection shows everything.
    """
    if name is not None and every:
        raise ArgumentError(
            "--namespace and --all-namespaces cannot be combined",
            target_files=["--namespace", "--all-namespaces"],
            fix="Pass one of --namespace NAME and --all-namespaces",
        )
    if name is not None:
        require(namespaces, name)
    if every or not namespaces:
        return Selection()
    if name is not None:
        return Selection(name)
    return Selection(detect(namespaces, root, cwd))


def _bundle_anchor(path: str) -> str | None:
    parts = path.split("/")
    if len(parts) >= 4 and parts[0] == "specs" and parts[2] != "feedback":
        return "/".join([*parts[:3], "spec.md"])
    if len(parts) >= 4 and parts[:2] == ["docs", "proposals"]:
        return "/".join([*parts[:3], "proposal.md"])
    if len(parts) == 3 and parts[:2] == ["docs", "proposals"]:
        return path
    return None


def namespace_resolver(index: DocumentIndex, namespaces: Sequence[Namespace]) -> Callable[[Document], str]:
    """A function giving the namespace each document of ``index`` belongs to (``global`` when none applies)."""
    by_path = {document.path: document for document in index.documents}
    names = {namespace.name for namespace in namespaces}

    def namespace_of(document: Document) -> str:
        for namespace in namespaces:
            if _within(document.path, namespace.docs):
                return namespace.name
        anchor_path = _bundle_anchor(document.path)
        anchor = by_path.get(anchor_path) if anchor_path else None
        declared = anchor.frontmatter.get("namespace") if anchor else None
        return declared if isinstance(declared, str) and declared in names else GLOBAL

    return namespace_of


def living_path(namespaces: Sequence[Namespace], path: str) -> str:
    """``docs/packages/<name>/X`` as the global ``docs/X`` it mirrors; any other path unchanged."""
    for namespace in namespaces:
        if _within(path, namespace.docs) and path != namespace.docs:
            return "docs/" + path[len(namespace.docs) + 1 :]
    return path


def docs_roots(namespaces: Sequence[Namespace]) -> list[str]:
    """``docs`` and every namespace's docs root."""
    return ["docs", *(namespace.docs for namespace in namespaces)]
