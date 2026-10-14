"""``--apply``: append derived paths to the ``entrypoints`` frontmatter of capability and story documents.

Per document, the ``new`` pairs whose path exists and is not folded are written: directories with a trailing
``/``, sorted, after the entries already declared. An addition an existing entry or another addition already
covers is dropped, so a document never lists a directory and files inside it from one apply. Only the
``entrypoints`` block of the frontmatter changes: every other byte of the file stays as it was. A rerun writes
nothing (every written path is ``declared``). A changed document is replaced atomically and keeps its permission
bits. A document that cannot be read or written, is a symbolic link or lies below one that leaves the workspace (the
document index never follows links), or whose ``entrypoints`` is present but not a list of strings, is reported and
left unchanged; the others are still written.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from devkit.core import FrontmatterError, atomic_write_text
from devkit.core.frontmatter import locate, parse

from devkit_spec.entrypoints.derive import Pair, Reason, SkipKind, Skipped, State
from devkit_spec.entrypoints.paths import covers, normalize
from devkit_spec.errors import EntrypointsPathError

_KEY = re.compile(r"^entrypoints:[ \t]*(.*)$")
# A line that continues a top-level key's value: indented, or a zero-indented sequence item.
_CONTINUATION = re.compile(r"^(?:[ \t]+\S|-(?:[ \t]|$))")
# A line inside a value that carries none of it: blank, or a comment.
_FILLER = re.compile(r"^[ \t]*(?:#.*)?$")
_CREATED = re.compile(r"^created_at:")


@dataclass(frozen=True)
class Applied:
    """A document whose ``entrypoints`` were extended by ``added``."""

    doc: str
    doc_path: str
    added: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"doc": self.doc, "doc_path": self.doc_path, "added": list(self.added)}


@dataclass
class ApplyResult:
    applied: list[Applied] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)  # (document path, problem)


def apply(root: Path, pairs: Sequence[Pair], only: set[str] | None = None) -> ApplyResult:
    """Write the new, existing, unfolded paths of ``pairs`` into their documents (``only`` restricts the document
    paths when given)."""
    result = ApplyResult()
    by_doc: dict[str, list[Pair]] = {}
    for pair in pairs:
        if only is None or pair.doc_path in only:
            by_doc.setdefault(pair.doc_path, []).append(pair)
    for doc_path in sorted(by_doc):
        additions: list[str] = []
        for pair in by_doc[doc_path]:
            if pair.state is not State.NEW:
                continue
            if pair.folded_into is not None or not pair.exists:
                reason = Reason.FOLDED if pair.folded_into is not None else Reason.MISSING_PATH
                result.skipped.append(Skipped(SkipKind.APPLY, pair.code, reason, pair.spec, pair.task))
                continue
            shown = f"{pair.code}/" if (root / pair.code).is_dir() else pair.code
            if shown not in additions:
                additions.append(shown)
        if not additions:
            continue
        try:
            added = _write(root, root / doc_path, sorted(additions))
        except (OSError, UnicodeDecodeError, FrontmatterError, ValueError) as exc:
            problem = exc.message if isinstance(exc, FrontmatterError) else str(exc)
            result.failures.append((doc_path, problem))
            continue
        if added:
            result.applied.append(Applied(by_doc[doc_path][0].doc, doc_path, tuple(added)))
    return result


def _write(root: Path, path: Path, additions: list[str]) -> list[str]:
    if path.is_symlink():
        raise ValueError("the document is a symbolic link; edit the file it points to, then rerun")
    if not path.parent.resolve().is_relative_to(root.resolve()):
        raise ValueError("the document's directory resolves outside the workspace through a symbolic link")
    text = path.read_bytes().decode("utf-8")
    data = parse(text).data
    if data is None:
        raise ValueError("the document has no frontmatter block")
    value = data.get("entrypoints")
    if value is None:
        existing: list[str] = []
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        existing = value
    else:
        raise ValueError(
            "entrypoints is not a list of path strings; rewrite it as a YAML list of paths (entrypoints:"
            " followed by '  - <path>' lines), then rerun"
        )
    added = collapse(existing, additions)
    if added:
        atomic_write_text(path, set_entrypoints(text, [*existing, *added]))
    return added


def collapse(existing: Iterable[str], additions: Sequence[str]) -> list[str]:
    """``additions`` without those an existing entry or another addition covers as an ancestor directory."""
    normalized = []
    for entry in [*existing, *additions]:
        with contextlib.suppress(EntrypointsPathError):
            normalized.append(normalize(entry))
    kept = []
    for addition in additions:
        try:
            path = normalize(addition)
        except EntrypointsPathError:
            continue
        if not any(other != path and covers(other, path) for other in normalized):
            kept.append(addition)
    return kept


def set_entrypoints(text: str, entries: Sequence[str]) -> str:
    """``text`` with its frontmatter ``entrypoints`` set to ``entries`` (deduplicated, order kept).

    An existing ``entrypoints`` key is replaced where it stands (with every line of its value); without one the
    block goes before ``created_at`` or at the end of the header. No entries write ``entrypoints: []``. Every
    other character of ``text`` is kept. Raises ``ValueError`` when ``text`` has no frontmatter block.
    """
    block = locate(text)
    if block is None:
        raise ValueError("the document has no frontmatter block")
    newline = "\r\n" if block.newline == "\r\n" or "\r\n" in block.header else "\n"
    lines = block.header.split(newline)
    if lines and lines[-1] == "":
        lines.pop()
    rendered = _render(list(dict.fromkeys(entry.strip() for entry in entries if entry.strip())))
    out: list[str] = []
    inserted = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if not inserted and _KEY.match(line):
            out.extend(rendered)
            inserted = True
            index = _value_end(lines, index + 1)
            continue
        if not inserted and _CREATED.match(line):
            out.extend(rendered)
            inserted = True
        out.append(line)
        index += 1
    if not inserted:
        out.extend(rendered)
    header = newline.join(out) + newline
    return text[: block.header_start] + header + text[block.header_end :]


def _value_end(lines: list[str], start: int) -> int:
    """The index after the last line of the value that starts at ``lines[start]``.

    Blank and comment lines between continuation lines belong to the value; those after its last continuation line
    precede the next key and are kept.
    """
    end = start
    index = start
    while index < len(lines):
        line = lines[index]
        if _CONTINUATION.match(line) and not line.lstrip().startswith("#"):
            end = index + 1
        elif not _FILLER.match(line):
            break
        index += 1
    return end


def _render(entries: list[str]) -> list[str]:
    if not entries:
        return ["entrypoints: []"]
    dumped = yaml.safe_dump(entries, default_flow_style=False, allow_unicode=True, width=10_000)
    return ["entrypoints:", *(f"  {line}" for line in dumped.rstrip("\n").split("\n"))]
