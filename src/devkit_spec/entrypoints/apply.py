"""``--apply``: append derived paths to the ``entrypoints`` frontmatter of capability and story documents.

Per document, the ``new`` pairs whose path exists and is not folded are written: directories with a trailing
``/``, sorted, after the entries already declared. An addition an existing entry or another addition already
covers is dropped, so a document never lists a directory and files inside it from one apply. Only the
``entrypoints`` block of the frontmatter changes: every other byte of the file stays as it was. A rerun writes
nothing (every written path is ``declared``). A document that cannot be read or written is reported and the
others are still written.
"""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from devkit.core import FrontmatterError
from devkit.core.frontmatter import locate, parse

from devkit_spec.entrypoints.derive import Pair, Reason, SkipKind, Skipped, State
from devkit_spec.entrypoints.paths import covers, normalize
from devkit_spec.errors import EntrypointsPathError

_KEY = re.compile(r"^entrypoints:[ \t]*(.*)$")
# A line that continues a top-level key's value: indented, or a zero-indented sequence item.
_CONTINUATION = re.compile(r"^(?:[ \t]+\S|-(?:[ \t]|$))")
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
            added = _write(root / doc_path, sorted(additions))
        except (OSError, UnicodeDecodeError, FrontmatterError, ValueError) as exc:
            problem = exc.message if isinstance(exc, FrontmatterError) else str(exc)
            result.failures.append((doc_path, problem))
            continue
        if added:
            result.applied.append(Applied(by_doc[doc_path][0].doc, doc_path, tuple(added)))
    return result


def _write(path: Path, additions: list[str]) -> list[str]:
    text = path.read_bytes().decode("utf-8")
    data = parse(text).data
    if data is None:
        raise ValueError("the document has no frontmatter block")
    value = data.get("entrypoints")
    existing = [item for item in value if isinstance(item, str)] if isinstance(value, list) else []
    added = collapse(existing, additions)
    if added:
        _write_atomic(path, set_entrypoints(text, [*existing, *added]))
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
            index += 1
            while index < len(lines) and _CONTINUATION.match(lines[index]):
                index += 1
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


def _render(entries: list[str]) -> list[str]:
    if not entries:
        return ["entrypoints: []"]
    dumped = yaml.safe_dump(entries, default_flow_style=False, allow_unicode=True, width=10_000)
    return ["entrypoints:", *(f"  {line}" for line in dumped.rstrip("\n").split("\n"))]


def _write_atomic(path: Path, text: str) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".entrypoints-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(text.encode("utf-8"))
        os.chmod(temporary, path.stat().st_mode & 0o7777)
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise
