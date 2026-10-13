"""The document index of a workspace: every ID-bearing Markdown file under ``docs/`` and ``specs/``.

The index is rebuilt from the files on every load; there is no second source
of truth to go stale. Symbolic links, directories starting with ``.``,
``README.md`` files and templates (``*-template.md``, ``*_template.md``) are
not documents. A file that cannot be read or whose frontmatter is malformed is
left out and reported as a ``SPEC_DOCUMENT_INVALID`` warning, so one broken
file never hides the others. IDs and references are repository-wide.

A parsed document is reused by later loads while its file's text is
unchanged, so the rules of one run, which each load the index, parse every
file once.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from devkit.core import FrontmatterError

from devkit_spec.documents.model import Document, Reference
from devkit_spec.documents.parse import parse_document
from devkit_spec.errors import DocumentInvalidWarning, DuplicateIdError, UnresolvedIdError

SOURCE_DIRECTORIES = ("docs", "specs")
COMPLETED = "completed"
_PARSED_LIMIT = 20_000
_parsed: dict[tuple[str, str], Document | None] = {}


def is_document_file(name: str) -> bool:
    """Whether a file name can hold an indexed document."""
    return name.endswith(".md") and name != "README.md" and not name.endswith(("-template.md", "_template.md"))


def in_source_directory(relative: str) -> bool:
    """Whether a workspace-relative path lies under ``docs/`` or ``specs/`` outside directories starting with ``.``."""
    parts = relative.split("/")
    return len(parts) > 1 and parts[0] in SOURCE_DIRECTORIES and not any(part.startswith(".") for part in parts[1:-1])


def _parse(relative: str, text: str) -> Document | None:
    key = (relative, text)
    if key not in _parsed:
        if len(_parsed) >= _PARSED_LIMIT:
            _parsed.clear()
        _parsed[key] = parse_document(relative, text)
    return _parsed[key]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _files(root: Path) -> Iterable[Path]:
    for directory in SOURCE_DIRECTORIES:
        base = root / directory
        if base.is_symlink() or not base.is_dir():
            continue
        for current, dirnames, filenames in os.walk(base):
            here = Path(current)
            dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and not (here / d).is_symlink())
            for name in sorted(filenames):
                path = here / name
                if is_document_file(name) and not path.is_symlink() and path.is_file():
                    yield path


@dataclass
class DocumentIndex:
    """``documents`` in path order, ``by_id`` every document declaring an ID, ``problems`` the files left out,
    ``historical`` the paths of the files of completed spec bundles (work history, no longer current)."""

    root: Path
    documents: list[Document] = field(default_factory=list)
    by_id: dict[str, list[Document]] = field(default_factory=dict)
    problems: list[DocumentInvalidWarning] = field(default_factory=list)
    historical: set[str] = field(default_factory=set)

    @classmethod
    def load(
        cls, root: Path, *, files: Iterable[Path] | None = None, read: Callable[[Path], str] = _read
    ) -> DocumentIndex:
        """Index the documents under ``root``.

        ``files`` replaces the directory walk (absolute paths; anything that is not a document file under a source
        directory is skipped) and ``read`` the file reader (strict UTF-8; ``UnicodeDecodeError`` and ``OSError``
        become problems), so a rule run reads through its workspace cache.
        """
        index = cls(root=root.resolve())
        for path in _files(index.root) if files is None else files:
            relative = path.relative_to(index.root).as_posix()
            if not (is_document_file(path.name) and in_source_directory(relative)):
                continue
            try:
                document = _parse(relative, read(path))
            except (OSError, UnicodeDecodeError, FrontmatterError) as exc:
                reason = exc.message if isinstance(exc, FrontmatterError) else str(exc)
                index.problems.append(DocumentInvalidWarning(f"{relative}: {reason}", target_files=[relative]))
                continue
            if document is not None:
                index.documents.append(document)
                index.by_id.setdefault(document.id, []).append(document)
        index.documents.sort(key=lambda document: document.path)
        specs = {d.path: d for d in index.documents if d.path.endswith("/spec.md")}
        for document in index.documents:
            bundle = _spec_bundle(document.path)
            spec = specs.get(f"{bundle}/spec.md") if bundle else None
            if spec is not None and spec.status == COMPLETED:
                index.historical.add(document.path)
        return index

    def is_historical(self, document: Document) -> bool:
        return document.path in self.historical

    def resolve(self, document_id: str) -> Document:
        """The one document declaring ``document_id``; ``UnresolvedIdError`` or ``DuplicateIdError`` otherwise."""
        found = self.by_id.get(document_id, [])
        if len(found) == 1:
            return found[0]
        if not found:
            raise UnresolvedIdError(f"no document has the ID {document_id}", target_files=[document_id])
        paths = [document.path for document in found]
        raise DuplicateIdError(f"{len(paths)} documents declare the ID {document_id}", *paths, target_files=paths)

    def outgoing(self, document: Document) -> dict[str, list[Reference]]:
        """``document``'s references grouped by target ID, in ID order."""
        return _grouped(document.references, lambda ref: ref.target)

    def incoming(self, document_id: str) -> dict[str, list[Reference]]:
        """References to ``document_id`` grouped by the ID of the referencing document, in ID order."""
        refs = [ref for document in self.documents for ref in document.references if ref.target == document_id]
        return _grouped(refs, lambda ref: ref.source)


def _spec_bundle(path: str) -> str | None:
    """``specs/<month>/<bundle>`` for a file inside a spec bundle, else ``None``."""
    parts = path.split("/")
    return "/".join(parts[:3]) if len(parts) >= 4 and parts[0] == "specs" else None


def _grouped(refs: Iterable[Reference], key: Callable[[Reference], str]) -> dict[str, list[Reference]]:
    groups: dict[str, list[Reference]] = {}
    for ref in refs:
        groups.setdefault(key(ref), []).append(ref)
    return dict(sorted(groups.items()))
