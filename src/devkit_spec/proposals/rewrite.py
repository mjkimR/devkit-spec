"""Rewrite what pointed into a handed-off proposal: relative Markdown links and document ID references.

``RelocationPlan`` says where each part of the proposal went. The rewriting never fails a handoff: a link or
reference without a new target, and a file that cannot be read or written, become ``Unresolved`` entries.

Every Markdown file under ``docs/`` and ``specs/`` is scanned except the proposal itself, directories starting with
``.``, symbolic links and the files of completed spec bundles, which record the proposal as it was.
"""

from __future__ import annotations

import os
import posixpath
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from devkit.core import FrontmatterError
from devkit.core.frontmatter import locate
from devkit.rules import extract_links

from devkit_spec.documents import Document, DocumentIndex, Reference, parse_document, rewrite, visible_lines
from devkit_spec.documents.ids import ID_SOURCE
from devkit_spec.documents.index import SOURCE_DIRECTORIES
from devkit_spec.documents.model import BODY

LINK = "link"
ID = "id"
UNMAPPED = "unmapped"  # a link into the proposal with no new location
REMOVED = "removed"  # a reference to the ID of a proposal document nothing replaced
AMBIGUOUS = "ambiguous"  # several documents declare the ID, so it is not rewritten
UNREADABLE = "unreadable"
UNWRITABLE = "unwritable"

_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_CODE_SPAN_ID = re.compile(rf"`({ID_SOURCE})`")
_BRACKET_ID = re.compile(rf"\[({ID_SOURCE})\]")


@dataclass(frozen=True)
class Rewritten:
    """One rewritten link destination or ID reference at ``path:line`` (workspace-relative)."""

    path: str
    line: int
    kind: str
    old: str
    new: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "line": self.line, "kind": self.kind, "from": self.old, "to": self.new}


@dataclass(frozen=True)
class Unresolved:
    """A link or ID reference into the proposal left as it was (``line`` ``0`` for a whole file)."""

    path: str
    line: int
    kind: str
    target: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "line": self.line, "kind": self.kind, "target": self.target, "reason": self.reason}


@dataclass
class RelocationPlan:
    """Absolute paths: the removed ``proposal`` (bundle directory or single file), the new target of a link to the
    bundle directory itself, old file to new file (``exact``), old directory to new directory (``prefixes``), and new
    directory to the old one its files were written for (``moved``), so their relative links resolve as written."""

    proposal: str
    dir_target: str | None = None
    exact: dict[str, str] = field(default_factory=dict)
    prefixes: dict[str, str] = field(default_factory=dict)
    moved: dict[str, str] = field(default_factory=dict)

    def contains(self, path: str) -> bool:
        return path == self.proposal or path.startswith(self.proposal + os.sep)


@dataclass
class RewriteReport:
    files: list[str] = field(default_factory=list)
    rewritten: list[Rewritten] = field(default_factory=list)
    unresolved: list[Unresolved] = field(default_factory=list)


def completed_bundles(index: DocumentIndex) -> set[str]:
    """Absolute directories of the spec bundles whose ``spec.md`` has ``status: completed``."""
    found = set()
    for document in index.documents:
        parts = document.path.split("/")
        if len(parts) == 4 and parts[0] == "specs" and parts[3] == "spec.md" and document.status == "completed":
            found.add(str(index.root / "/".join(parts[:3])))
    return found


def markdown_files(root: Path, plan: RelocationPlan, skip: set[str]) -> list[str]:
    """Absolute paths of the Markdown files to scan, sorted."""
    files: list[str] = []
    for name in SOURCE_DIRECTORIES:
        base = root / name
        if base.is_symlink() or not base.is_dir():
            continue
        for current, dirnames, filenames in os.walk(base):
            dirnames[:] = [
                d
                for d in dirnames
                if not d.startswith(".")
                and not os.path.islink(os.path.join(current, d))
                and not plan.contains(os.path.join(current, d))
                and os.path.join(current, d) not in skip
            ]
            for filename in filenames:
                path = os.path.join(current, filename)
                if filename.endswith(".md") and path != plan.proposal and not os.path.islink(path):
                    files.append(path)
    return sorted(files)


def _display(root: Path, path: str) -> str:
    return Path(os.path.relpath(path, root)).as_posix()


def _read(path: str) -> str:
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _new_location(plan: RelocationPlan, target: str) -> str | None:
    """Where the absolute ``target`` inside the proposal went, ``None`` when nothing replaced it."""
    if target in plan.exact:
        return plan.exact[target]
    if target == plan.proposal and plan.dir_target:
        return plan.dir_target
    for old, new in plan.prefixes.items():
        if target.startswith(old + os.sep):
            return new + target[len(old) :]
    return None


def rewrite_links(root: Path, files: Iterable[str], plan: RelocationPlan, report: RewriteReport) -> None:
    """Point relative links into the proposal at the new locations; links in moved files keep their targets."""
    for file in files:
        display = _display(root, file)
        try:
            text = _read(file)
        except (OSError, UnicodeDecodeError):
            report.unresolved.append(Unresolved(display, 0, LINK, "", UNREADABLE))
            continue
        here = os.path.dirname(file)
        base = here
        for new, old in plan.moved.items():
            if here == new or here.startswith(new + os.sep):
                base = old + here[len(new) :]
                break
        lines = text.split("\n")
        edits: list[tuple[int, int, int, str]] = []
        for link in extract_links(text):
            target = link.target
            cut = min((i for i in (target.find("#"), target.find("?")) if i >= 0), default=len(target))
            path_part, suffix = target[:cut], target[cut:]
            if not path_part or path_part.startswith("/") or _SCHEME.match(path_part):
                continue
            resolved = os.path.normpath(os.path.join(base, path_part))
            inside = plan.contains(resolved)
            if not inside and base == here:
                continue
            new_abs = _new_location(plan, resolved) if inside else resolved
            if new_abs is None:
                report.unresolved.append(Unresolved(display, link.line, LINK, target, UNMAPPED))
                continue
            new_rel = Path(os.path.relpath(new_abs, here)).as_posix()
            if new_rel == posixpath.normpath(path_part):
                continue  # the same file from the new location: keep the author's spelling
            edits.append((link.line - 1, link.target_start, link.target_end, new_rel + suffix))
            report.rewritten.append(Rewritten(display, link.line, LINK, target, new_rel + suffix))
        if not edits:
            continue
        for index, start, end, replacement in sorted(edits, reverse=True):
            lines[index] = lines[index][:start] + replacement + lines[index][end:]
        try:
            _write(file, "\n".join(lines))
        except OSError:
            report.unresolved.append(Unresolved(display, 0, LINK, "", UNWRITABLE))
            continue
        report.files.append(display)


def _parse(root: Path, path: str) -> Document | None:
    try:
        return parse_document(_display(root, path), _read(path))
    except (OSError, UnicodeDecodeError, FrontmatterError):
        return None


def _body_references(path: str, text: str) -> list[Reference]:
    """The prose references of a file that declares no ID (a README, a material without frontmatter)."""
    block = locate(text)
    start, first_line = (block.end, block.body_line) if block is not None else (0, 1)
    refs: list[Reference] = []
    for line in visible_lines(text, start=start, first_line=first_line):
        found = [(m, False) for m in _CODE_SPAN_ID.finditer(line.text)]
        found += [(m, True) for m in _BRACKET_ID.finditer(line.text)]
        for match, bracket in sorted(found, key=lambda item: item[0].start()):
            refs.append(
                Reference(
                    target=match.group(1),
                    source="",
                    path=path,
                    field=BODY,
                    line=line.number,
                    column=match.start(1) + 1,
                    start=line.offset + match.start(1),
                    end=line.offset + match.end(1),
                    bracket=bracket,
                )
            )
    return refs


def rewrite_ids(
    root: Path, files: Iterable[str], plan: RelocationPlan, index: DocumentIndex, report: RewriteReport
) -> None:
    """Rewrite references (fields, prose, ``proposal`` provenance) to the IDs of relocated proposal documents.

    The mapping comes from the documents actually written (``plan.exact``: proposal to spec, PADR to ADR, the
    blueprint to its copy), never from slug guesses. A reference to an ID declared inside the proposal that nothing
    replaced is ``removed``; an ID other documents declare too is ``ambiguous`` and stays.
    """
    removed = {d.id for d in index.documents if plan.contains(str(index.root / d.path))}
    mapping: dict[str, str] = {}
    for old_path, new_path in sorted(plan.exact.items()):
        old, new = _parse(root, old_path), _parse(root, new_path)
        if old is None or new is None:
            continue
        others = [d.path for d in index.by_id.get(old.id, []) if str(index.root / d.path) not in (old_path, new_path)]
        if others:
            report.unresolved.append(Unresolved(_display(root, old_path), 1, ID, old.id, AMBIGUOUS))
            continue
        mapping[old.id] = new.id
    for file in files:
        display = _display(root, file)
        try:
            text = _read(file)
            document = parse_document(display, text)
        except (OSError, UnicodeDecodeError, FrontmatterError):
            report.unresolved.append(Unresolved(display, 0, ID, "", UNREADABLE))
            continue
        refs = [*document.references, *document.provenance] if document else _body_references(display, text)
        updated = rewrite(text, refs, mapping)
        changed: list[Rewritten] = []
        for ref in sorted(refs, key=lambda ref: ref.start):
            new_id = mapping.get(ref.target)
            if new_id is not None and new_id != ref.target:
                changed.append(Rewritten(display, ref.line, ID, ref.target, new_id))
            elif new_id is None and ref.target in removed:
                report.unresolved.append(Unresolved(display, ref.line, ID, ref.target, REMOVED))
        if updated == text:
            continue
        try:
            _write(file, updated)
        except OSError:
            report.unresolved.append(Unresolved(display, 0, ID, "", UNWRITABLE))
            continue
        report.files.append(display)
        report.rewritten.extend(changed)
