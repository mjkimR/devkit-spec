"""``RULE-spec-format``: capabilities, stories and proposals carry a frontmatter block with ``id``, ``title`` and
``status``.

Checks every document file (``documents.is_document_file``) under ``docs/capabilities/``, ``docs/stories/`` and
``docs/proposals/``, and under the ``capabilities/`` and ``stories/`` of every namespace docs root
(``docs/packages/<name>/``, registered in ``[[tool.spec.namespaces]]``), outside ``materials/`` directories, whether or
not it declares a well-formed ID:

- a file without a frontmatter block (fixable);
- a frontmatter block that does not follow devkit's grammar (unclosed, invalid YAML, not a mapping);
- a missing or blank ``id``, ``title`` or ``status`` (fixable), or one that is not a string.

The fix prepends a block to a file without one (``id`` the file stem, ``title`` the first ``# `` heading without a
leading ``[ID]``, else the stem, ``status: draft`` and ``created_at`` today) and fills the missing fields of an
existing block with the same values, adding ``created_at`` when neither ``created_at``, ``created`` nor ``date`` is
set. It never touches a file the check accepts, a malformed block or a field of the wrong type. None of these files
can be work history (only spec bundle files are), so every targeted file is checked.

The ``namespace`` field of a bundle anchor (a ``proposal.md`` under ``docs/proposals/``, a ``spec.md`` under
``specs/``), when present, must be a string naming ``global`` or a registered namespace; it is not fixable. Anchors are
reported as the other rules report documents (a completed spec only when explicitly targeted), except that a run
targeting ``.devkit/config.toml`` checks every current anchor, because a change to the registry can invalidate them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from devkit.core import CONFIG_PATH, FrontmatterError
from devkit.core.frontmatter import BOM, load_header, locate
from devkit.rules import Phase, RuleContext, Severity, Violation, match_path
from devkit.rules.rules import BaseRule

from devkit_spec.config import GLOBAL, Namespace
from devkit_spec.documents import Document, DocumentIndex, in_source_directory, is_document_file
from devkit_spec.rules import FIX_COMMAND, document_index, explicitly_targeted, namespaces, reportable

RULE_ID = "RULE-spec-format"
SCOPE = ("docs/capabilities", "docs/stories", "docs/proposals")
NAMESPACE_SCOPE = ("capabilities", "stories")
NAMESPACE_FIELD = "namespace"
REQUIRED = ("id", "title", "status")
CREATED_FIELDS = ("created_at", "created", "date")
DEFAULT_STATUS = "draft"
# The rest of a ``name:`` line whose value is empty or null (a comment may follow), up to its line ending.
_BLANK_VALUE = r"""[ \t]*(?:""|''|~|null|Null|NULL)?[ \t]*(?:#[^\r\n]*)?(?=\r?$)"""
REMEDIATION = {
    "id": "Set id to the document's full ID, equal to the file stem (CAP-<AREA>-<slug>, US-<slug>, PROP-<slug>)",
    "title": "Set title to the document's title",
    "status": "Set status to the document's lifecycle status (for example draft, proposed, active)",
}


@dataclass(frozen=True, slots=True)
class _Problem:
    message: str
    remediation: str
    fixable: bool = False


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _problems(ctx: RuleContext, path: str) -> list[_Problem]:
    try:
        data = ctx.cache.get_frontmatter(path)
    except FrontmatterError as exc:
        return [_Problem(f"frontmatter is malformed: {exc.message}", "Close the block with --- and fix its YAML")]
    if data is None:
        return [
            _Problem(
                "document has no YAML frontmatter block (--- ... --- on the first line)",
                f"Add a frontmatter block with id, title and status, or run `{FIX_COMMAND}`",
                fixable=True,
            )
        ]
    problems: list[_Problem] = []
    for name in REQUIRED:
        value = data.get(name)
        if _blank(value):
            problems.append(
                _Problem(
                    f"frontmatter is missing the required field '{name}'",
                    f"{REMEDIATION[name]}, or run `{FIX_COMMAND}`",
                    fixable=True,
                )
            )
        elif not isinstance(value, str):
            problems.append(_Problem(f"frontmatter field '{name}' must be a string", REMEDIATION[name]))
    return problems


def _directories(registered: tuple[Namespace, ...]) -> list[str]:
    """``SCOPE``, then the ``NAMESPACE_SCOPE`` directories of each namespace docs root."""
    return [*SCOPE, *(f"{namespace.docs}/{name}" for namespace in registered for name in NAMESPACE_SCOPE)]


def _scope(ctx: RuleContext) -> list[str]:
    """Workspace-relative paths of the targeted files the rule checks, by directory (``_directories``), then path."""
    root = ctx.workspace_root
    paths: list[str] = []
    for directory in _directories(namespaces(ctx)):
        if not (root / directory).is_dir():
            continue
        for path in ctx.cache.find_files(root / directory, extensions=(".md",)):
            relative = path.relative_to(root).as_posix()
            if (
                is_document_file(path.name)
                and in_source_directory(relative)
                and "/materials/" not in relative
                and ctx.is_file_targeted(relative)
            ):
                paths.append(relative)
    return paths


class SpecFormatRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="spec-markdown-frontmatter-check",
            description="Capabilities, stories and proposals carry YAML frontmatter with id, title and status.",
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            guide="guide.md",
        )

    def check(self, ctx: RuleContext) -> list[Violation]:
        found = [
            Violation(
                rule_id=self.id,
                file=path,
                line=1,
                message=problem.message,
                remediation=problem.remediation,
                fixable=problem.fixable,
            )
            for path in _scope(ctx)
            for problem in _problems(ctx, path)
        ]
        return found + self._namespace_fields(ctx)

    def _namespace_fields(self, ctx: RuleContext) -> list[Violation]:
        """The bundle anchors whose ``namespace`` is not ``global`` or a registered namespace."""
        known = [GLOBAL, *(namespace.name for namespace in namespaces(ctx))]
        index = document_index(ctx)
        found: list[Violation] = []
        for document in index.documents:
            if not _is_anchor(document.path) or NAMESPACE_FIELD not in document.frontmatter:
                continue
            if not _namespace_checked(ctx, index, document):
                continue
            value = document.frontmatter[NAMESPACE_FIELD]
            if isinstance(value, str) and value in known:
                continue
            message = (
                f"frontmatter namespace {value!r} is not global or a registered namespace"
                if isinstance(value, str)
                else f"frontmatter field '{NAMESPACE_FIELD}' must be a string"
            )
            found.append(
                Violation(
                    rule_id=self.id,
                    file=document.path,
                    line=_field_line(ctx.cache.read_text(document.path), NAMESPACE_FIELD),
                    message=message,
                    remediation=(
                        f"Set namespace to one of {', '.join(known)} (registered in [[tool.spec.namespaces]] of"
                        f" {CONFIG_PATH}), or remove the field to keep the bundle global"
                    ),
                )
            )
        return found

    def fix(self, ctx: RuleContext) -> list[str]:
        changed: list[str] = []
        today = date.today().isoformat()
        for path in _scope(ctx):
            if not any(problem.fixable for problem in _problems(ctx, path)):
                continue
            text = ctx.cache.read_text_strict(path)
            if text is None:
                continue
            updated = _fixed(text, Path(path).stem, today)
            if updated is not None and updated != text:
                ctx.cache.write_text(path, updated, dry_run=ctx.dry_run)
                changed.append(path)
        return changed


def _is_anchor(path: str) -> bool:
    """Whether ``path`` is a bundle anchor that may declare a ``namespace``: a proposal's ``proposal.md`` under
    ``docs/proposals/`` or a spec bundle's ``spec.md`` under ``specs/``."""
    name = path.rsplit("/", 1)[-1]
    return (path.startswith("docs/proposals/") and name == "proposal.md") or (
        path.startswith("specs/") and name == "spec.md"
    )


def _namespace_checked(ctx: RuleContext, index: DocumentIndex, document: Document) -> bool:
    """Whether the ``namespace`` of ``document`` is checked: it is reportable, or the run targets the namespace
    registry (``.devkit/config.toml``) and the document is current and not excluded."""
    if reportable(ctx, index, document):
        return True
    if not explicitly_targeted(ctx, CONFIG_PATH) or index.is_historical(document):
        return False
    return not any(match_path(pattern, document.path) for pattern in ctx.exclude)


def _field_line(text: str, name: str) -> int:
    """The 1-based line of the first top-level ``name:`` line of the frontmatter, else 1."""
    try:
        block = locate(text)
    except FrontmatterError:
        return 1
    if block is None:
        return 1
    match = re.search(rf"^{re.escape(name)}[ \t]*:", block.header, re.M)
    if match is None:
        return 1
    return text.count("\n", 0, block.header_start + match.start()) + 1


def _fixed(text: str, stem: str, today: str) -> str | None:
    """``text`` with its missing required fields filled in; ``None`` when its frontmatter cannot be fixed."""
    try:
        block = locate(text)
    except FrontmatterError:
        return None
    if block is None:
        start = 1 if text.startswith(BOM) else 0
        newline = "\r\n" if text.split("\n", 1)[0].endswith("\r") else "\n"
        values = {"id": stem, "title": _h1_title(text[start:]) or stem, "status": DEFAULT_STATUS, "created_at": today}
        header = "".join(_line(name, value) + newline for name, value in values.items())
        return f"{text[:start]}---{newline}{header}---{newline}{newline}{text[start:]}"
    header = block.header
    try:
        data = load_header(header)
    except FrontmatterError:
        return None
    defaults = {"id": stem, "title": _h1_title(text[block.end :]) or stem, "status": DEFAULT_STATUS}
    missing = {name: value for name, value in defaults.items() if _blank(data.get(name))}
    if not missing:
        return None
    if all(_blank(data.get(name)) for name in CREATED_FIELDS):
        missing["created_at"] = today
    newline = block.newline or "\n"
    for name, value in missing.items():
        line = _line(name, value)
        if name not in data:
            if header and not header.endswith("\n"):
                header += newline
            header += line + newline
            continue
        blank_line = re.compile(rf"^{re.escape(name)}[ \t]*:{_BLANK_VALUE}", re.M)
        header, count = blank_line.subn(line.replace("\\", r"\\"), header, count=1)
        if count == 0:
            return None
    return text[: block.header_start] + header + text[block.header_end :]


def _line(name: str, value: str) -> str:
    """``name: value``; ``created_at`` is written as a plain YAML date, every other value as a string."""
    return f"{name}: {value if name == 'created_at' else _scalar(value)}"


def _h1_title(body: str) -> str:
    """The first ``# `` heading of ``body`` without a leading ``[...]`` (``# [ID] Title`` gives ``Title``)."""
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title.startswith("[") and "]" in title:
                title = title[title.index("]") + 1 :].strip()
            return title
    return ""


def _scalar(value: str) -> str:
    """``value`` as a YAML scalar that reads back as the same string: plain when it does, else double-quoted."""
    try:
        if yaml.safe_load(f"k: {value}") == {"k": value}:
            return value
    except yaml.YAMLError:
        pass
    return json.dumps(value, ensure_ascii=False)
