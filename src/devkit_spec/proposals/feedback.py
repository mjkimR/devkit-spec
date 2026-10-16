"""Preflight proposal-local feedback before a handoff can retire its source bundle."""

from __future__ import annotations

import re
from pathlib import Path

from devkit.core import FrontmatterError

from devkit_spec.documents import parse_document
from devkit_spec.errors import ProposalInvalidError
from devkit_spec.proposals.scaffold import first_segment_has_letter

FEEDBACK = "feedback"
STATUSES = frozenset({"open", "promoted", "dismissed", "forwarded"})
_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)


def plan_open_feedback(root: Path, bundle: Path, target: Path) -> list[tuple[Path, Path]]:
    """Validate all direct feedback Markdown; return open-file moves, leaving settled files to generic materials.

    Symlinks and nested directories in feedback are refused rather than followed or silently archived. Non-Markdown
    sidecars and README.md keep the normal extra-file preservation behavior. No source is written here.
    """
    directory = bundle / FEEDBACK
    rel = directory.relative_to(root).as_posix()
    if directory.is_symlink():
        raise ProposalInvalidError(f"{rel}: feedback source must not be a symbolic link", target_files=[rel])
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ProposalInvalidError(f"{rel}: feedback must be a directory", target_files=[rel])
    try:
        paths = sorted(directory.iterdir())
    except OSError as exc:
        raise ProposalInvalidError(f"{rel}: cannot read feedback: {exc}", target_files=[rel]) from exc
    moves: list[tuple[Path, Path]] = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if path.is_symlink() or path.is_dir():
            raise ProposalInvalidError(
                f"{rel}: feedback must contain direct files, not links or directories", target_files=[rel]
            )
        if path.suffix != ".md" or path.name == "README.md":
            continue
        if not _NAME.fullmatch(path.stem) or not first_segment_has_letter(path.stem):
            raise ProposalInvalidError(f"{rel}: feedback name must be an undated kebab-case slug", target_files=[rel])
        try:
            document = parse_document(rel, path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, FrontmatterError) as exc:
            raise ProposalInvalidError(f"{rel}: cannot read valid feedback: {exc}", target_files=[rel]) from exc
        if (
            document is None
            or document.id != f"FB-{path.stem}"
            or document.status not in STATUSES
            or not isinstance(document.frontmatter.get("title"), str)
            or not document.frontmatter["title"].strip()
        ):
            raise ProposalInvalidError(
                f"{rel}: feedback requires its path-derived FB id, title and a known status", target_files=[rel]
            )
        if document.status == "open":
            moves.append((path, target / FEEDBACK / path.name))
    return moves
