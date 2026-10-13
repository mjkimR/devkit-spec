"""The entrypoint path contract: literal workspace-relative paths and which documents carry them.

An entrypoint is a file or directory relative to the workspace root, written with ``/``. ``./`` and a trailing
``/`` are normalized away; ``.`` names the whole workspace. An empty value, an absolute path, a ``..`` segment, a
backslash, a colon (drive), a glob character (``*?[]``), NUL or a line break is invalid. Paths compare by whole
segments and case-sensitively: ``src/a`` covers ``src/a/b.py`` but not ``src/ab``.

Capabilities and stories carry ``entrypoints``: documents under ``docs/capabilities/`` or ``docs/stories/``, and
under the same directories of a namespace's docs root ``docs/packages/<name>/``. Their paths stay
workspace-relative, never package-relative.
"""

from __future__ import annotations

import posixpath
from pathlib import Path

from devkit.core import UnsafePathError, resolve_within

from devkit_spec.errors import EntrypointsPathError

ROOT = "."
_FORBIDDEN = frozenset("\\:*?[]\x00\r\n")
_LIVING_DIRECTORIES = ("docs/capabilities/", "docs/stories/")
_PACKAGES = ("docs", "packages")


def normalize(value: str) -> str:
    """``value`` in normalized form; ``EntrypointsPathError`` when it is not a literal workspace-relative path."""
    if not value.strip() or value.startswith("/") or any(char in _FORBIDDEN for char in value):
        raise EntrypointsPathError(
            f"invalid entrypoint {value!r}: use a literal workspace-relative path", target_files=[value]
        )
    if ".." in value.split("/"):
        raise EntrypointsPathError(f"invalid entrypoint {value!r}: parent traversal is forbidden", target_files=[value])
    return posixpath.normpath(value)


def covers(ancestor: str, path: str) -> bool:
    """Whether the normalized ``ancestor`` is ``path`` itself or a directory containing it."""
    return ancestor in (ROOT, path) or path.startswith(f"{ancestor}/")


def overlaps(first: str, second: str) -> bool:
    """Whether two entrypoint values name the same path or one contains the other; invalid values never overlap."""
    try:
        a, b = normalize(first), normalize(second)
    except EntrypointsPathError:
        return False
    return covers(a, b) or covers(b, a)


def living_path(path: str) -> str:
    """``docs/packages/<name>/X`` as the global ``docs/X`` it mirrors; any other path unchanged."""
    parts = path.split("/")
    if len(parts) >= 4 and tuple(parts[:2]) == _PACKAGES:
        return "/".join(["docs", *parts[3:]])
    return path


def entrypoint_bearing(path: str) -> bool:
    """Whether the workspace-relative ``path`` is a capability or story file, which may declare ``entrypoints``."""
    living = living_path(path)
    return living.startswith(_LIVING_DIRECTORIES) and living.endswith(".md")


def exists(root: Path, path: str) -> bool:
    """Whether the normalized ``path`` is a file or directory inside ``root``, symbolic links resolved."""
    if path == ROOT:
        return True
    try:
        resolved = resolve_within(root, path)
    except UnsafePathError:
        return False
    return resolved.is_dir() or resolved.is_file()
