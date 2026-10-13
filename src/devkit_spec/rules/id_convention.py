"""``RULE-id-convention``: identifiers are slugs derived from the document's path, never dates or sequence numbers.

Checks the identifier targets:

- ADRs at ``docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`` (``ADR-<slug>``);
- spec bundle files at ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/{spec,plan,tasks,reconcile}.md`` (``SPEC-``, ``PLAN-``,
  ``TASKS-``, ``REC-<slug>``; a reconcile file declares ``reconcile_id``);
- feedback at ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/feedback/<slug>.md`` or
  ``specs/<YYYY-MM>/feedback/<YYYYMMDD>-<slug>.md`` (``FB-<slug>``);
- Living Spec documents, whose ID is the file stem: ``docs/capabilities/<area>/CAP-<AREA>-<slug>.md``,
  ``docs/stories/<area>/US-<slug>.md`` (both with ``area: <area>``) and
  ``docs/architecture/ARCH-[<NN>[-<n>]-]<slug>.md`` (``NN`` an arc42 chapter other than 09 and 12).

A target is reported for a path off the convention (and then nothing else), a missing frontmatter, an ``id`` /
``reconcile_id`` or ``area`` other than the path requires (fixable), a first H1 ``[ID]`` or `` `ID` `` token other
than the ID (fixable; a plan, tasks or reconcile heading may also name its ``SPEC-<slug>``), and an ADR, spec or
Living Spec ID that another target's path also derives. Every Markdown file under ``docs/`` (except
``docs/materials/``) and ``specs/`` is reported for a date- or number-based reference (``ADR-0006``,
``SPEC-20261006``, ``US-010``, ``CAP-HARN-007``, ``ARCH-06``) in its frontmatter or prose; code, HTML comments and
escapes are skipped, link labels and targets are not.

Fields are read line by line as written (a top-level ``id:`` / ``area:`` line), so a header YAML rejects is still
checked. The fix sets the ``id`` / ``reconcile_id`` and ``area`` lines (inserting a missing one) and the heading
token, never moves a file, never renames a duplicate slug and never rewrites a reference; it skips completed spec
bundles (within the targets, when the run names any).

A namespace docs root (``docs/packages/<name>/``, registered in ``[[tool.spec.namespaces]]``) holds Living Spec
documents under the same conventions: ``docs/packages/<name>/capabilities/<area>/CAP-<AREA>-<slug>.md`` is checked as
``docs/capabilities/<area>/CAP-<AREA>-<slug>.md``, and so on. IDs stay repository-wide, so a slug a package shares
with ``docs/`` or another package is a duplicate. A package's ``materials/`` directory is skipped like
``docs/materials/``.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from devkit.core import FrontmatterError
from devkit.core.frontmatter import FrontmatterBlock, locate
from devkit.rules import Phase, RuleContext, Severity, Violation
from devkit.rules.rules import BaseRule

from devkit_spec.config import Namespace
from devkit_spec.documents import DocumentIndex, Kind, VisibleLine, visible_lines
from devkit_spec.namespaces import docs_roots, living_path
from devkit_spec.rules import FIX_COMMAND, document_index, explicitly_targeted, namespaces

RULE_ID = "RULE-id-convention"
type Add = Callable[..., None]

_DATED_NAME = re.compile(r"^(\d{8})-([a-z0-9]+(?:-[a-z0-9]+)*)$", re.ASCII)
_SLUG_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", re.ASCII)
_MONTH_NAME = re.compile(r"^(\d{4})-(\d{2})$", re.ASCII)
_CAP_STEM = re.compile(r"^CAP-([A-Z0-9]+)-([a-z0-9]+(?:-[a-z0-9]+)*)$", re.ASCII)
_STORY_STEM = re.compile(r"^US-([a-z0-9]+(?:-[a-z0-9]+)*)$", re.ASCII)
_ARCH_STEM = re.compile(r"^ARCH-(?:(\d{2})(?:-([1-9]))?-)?([a-z0-9]+(?:-[a-z0-9]+)*)$", re.ASCII)
_HEADING_TOKEN = re.compile(r"(?:\[|`)((?:SPEC|PLAN|TASKS|REC|ADR|FB|CAP|US|ARCH)-[^\]`]+)(?:\]|`)")
# Date- or number-based references that are never valid identifiers.
_LEGACY_REF = re.compile(
    r"\b(SPEC-\d{8}(?:-[a-z0-9-]+)?|FB-\d{8}(?:-[a-z0-9-]+)?|P?ADR-\d{4}|US-\d{3,}|CAP-[A-Z0-9]+-\d{3,})\b", re.ASCII
)
# The arc42 chapter number is part of an architecture slug: ARCH-03-context is valid, a bare ARCH-03 is not.
_ARCH_REF = re.compile(r"\bARCH-\d{2}(?:-[0-9a-z]+)*", re.ASCII)
_ARCH_SUBDOCUMENT = re.compile(r"^-[1-9](?=-|$)")
_HAS_LETTER = re.compile(r"[a-z]")
# Header lines, read as written; the value excludes surrounding blanks and a CR line ending.
_ID_LINE = re.compile(r"^(id|reconcile_id):[ \t]*(.*?)[ \t]*(?=\r?$)", re.MULTILINE)
_AREA_LINE = re.compile(r"^area:[ \t]*(.*?)[ \t]*(?=\r?$)", re.MULTILINE)
_ANY_ID_LINE = re.compile(r"^id:.*?(?=\r?$)", re.MULTILINE)

_SPEC_FILES = {"spec.md": "SPEC", "plan.md": "PLAN", "tasks.md": "TASKS", "reconcile.md": "REC"}
# arc42 chapters that may hold a numbered ARCH document; 09 (decisions) and 12 (glossary) live elsewhere.
_ARCH_CHAPTERS = frozenset({"01", "02", "03", "04", "05", "06", "07", "08", "10", "11"})
_LIVING_SPEC = (Kind.CAPABILITY, Kind.STORY, Kind.ARCHITECTURE)
_LIVING_DIRECTORIES = {"capabilities": Kind.CAPABILITY, "stories": Kind.STORY, "architecture": Kind.ARCHITECTURE}
_REFERENCE_REMEDIATION = (
    "Reference documents by slug identifier (ADR-{slug}, SPEC-{slug}, CAP-{AREA}-{slug}, US-{slug}, ARCH-{NN}-{slug}),"
    " written `FULL-ID` in prose"
)


@dataclass(frozen=True, slots=True)
class _Target:
    """An identifier target: ``kind`` is ``SPEC`` for every spec bundle file; ``expected_id`` and ``slug`` are set
    when ``path_issue`` is empty; ``expected_area`` is the parent directory of a capability or story; ``docs_root``
    is the docs root of a Living Spec document (``docs`` or a namespace's ``docs/packages/<name>``)."""

    path: str
    kind: Kind
    field: str = "id"
    slug: str = ""
    expected_id: str = ""
    expected_area: str = ""
    path_issue: str = ""
    docs_root: str = "docs"

    def allowed_tokens(self) -> list[str]:
        """The IDs a first H1 token may name."""
        return [f"SPEC-{self.slug}", self.expected_id] if self.kind is Kind.SPEC else [self.expected_id]

    def heading_id(self) -> str:
        """The ID the fix writes into a mismatched heading token."""
        return f"SPEC-{self.slug}" if self.kind is Kind.SPEC else self.expected_id


def _has_letter(slug: str) -> bool:
    """Whether the first segment of ``slug`` has a letter: ``001-foo`` is a retired sequence number."""
    return _HAS_LETTER.search(slug.split("-", 1)[0]) is not None


def _dated(month: str, name: str) -> tuple[str, str]:
    """``(slug, issue)`` of a ``<YYYYMMDD>-<slug>`` name inside a ``<YYYY-MM>`` partition."""
    match = _DATED_NAME.match(name)
    if match is None:
        return "", f"name must be {{YYYYMMDD}}-{{slug}} with a kebab-case slug: {name}"
    partition = _MONTH_NAME.match(month)
    if partition is None or partition.group(1) + partition.group(2) != match.group(1)[:6]:
        return match.group(2), f'month partition "{month}" does not match date prefix "{match.group(1)}"'
    return match.group(2), ""


def _stem(path: str) -> str:
    return path.rsplit("/", 1)[-1].removesuffix(".md")


def _decision(path: str) -> _Target:
    parts = path.split("/")
    if len(parts) != 4:
        issue = "ADR must be stored at docs/decisions/{YYYY-MM}/{YYYYMMDD}-{slug}.md"
        return _Target(path, Kind.DECISION, path_issue=issue)
    slug, issue = _dated(parts[2], _stem(path))
    return _Target(path, Kind.DECISION, slug=slug, expected_id="" if issue else f"ADR-{slug}", path_issue=issue)


def _spec_file(path: str, prefix: str) -> _Target:
    parts = path.split("/")
    field = "reconcile_id" if prefix == "REC" else "id"
    if len(parts) != 4:
        issue = f"Change Spec must be stored at specs/{{YYYY-MM}}/{{YYYYMMDD}}-{{slug}}/{parts[-1]}"
        return _Target(path, Kind.SPEC, field=field, path_issue=issue)
    slug, issue = _dated(parts[1], parts[2])
    expected = "" if issue else f"{prefix}-{slug}"
    return _Target(path, Kind.SPEC, field=field, slug=slug, expected_id=expected, path_issue=issue)


def _feedback(path: str) -> _Target:
    parts = path.split("/")
    name = _stem(path)
    slug, issue = "", ""
    if len(parts) == 5 and parts[3] == "feedback":
        _, issue = _dated(parts[1], parts[2])
        if not issue:
            if _DATED_NAME.match(name) or not _SLUG_NAME.match(name):
                issue = f"feedback file name must be a kebab-case slug without a date: {name}"
            else:
                slug = name
    elif len(parts) == 4 and parts[2] == "feedback":
        slug, issue = _dated(parts[1], name)
    else:
        issue = (
            "Feedback must be stored at specs/{YYYY-MM}/{YYYYMMDD}-{slug}/feedback/{slug}.md"
            " or specs/{YYYY-MM}/feedback/{YYYYMMDD}-{slug}.md"
        )
    expected = "" if issue else f"FB-{slug}"
    return _Target(path, Kind.FEEDBACK, slug=slug, expected_id=expected, path_issue=issue)


def _living_spec(path: str, kind: Kind, docs_root: str, registered: tuple[Namespace, ...]) -> _Target:
    """The target of a Living Spec document under ``docs_root``, checked by the path it mirrors under ``docs/``."""
    parts = living_path(registered, path).split("/")
    stem = _stem(path)

    def target(**fields: str) -> _Target:
        return _Target(path, kind, docs_root=docs_root, **fields)

    if kind is Kind.CAPABILITY:
        if len(parts) != 4:
            return target(
                path_issue=f"Capability must be stored at {docs_root}/capabilities/{{area}}/CAP-{{AREA}}-{{slug}}.md"
            )
        match = _CAP_STEM.match(stem)
        if match is None or not _has_letter(match.group(2)):
            issue = (
                "file name must be CAP-{AREA}-{slug} with an upper-case area and a kebab-case slug"
                f" that is not a sequence number: {stem}"
            )
            return target(path_issue=issue)
        return target(slug=match.group(2), expected_id=stem, expected_area=parts[2])
    if kind is Kind.STORY:
        if len(parts) != 4:
            return target(path_issue=f"Story must be stored at {docs_root}/stories/{{area}}/US-{{slug}}.md")
        match = _STORY_STEM.match(stem)
        if match is None or not _has_letter(match.group(1)):
            issue = f"file name must be US-{{slug}} with a kebab-case slug that is not a sequence number: {stem}"
            return target(path_issue=issue)
        return target(slug=match.group(1), expected_id=stem, expected_area=parts[2])
    if len(parts) != 3:
        return target(path_issue=f"Architecture document must be stored at {docs_root}/architecture/ARCH-{{slug}}.md")
    match = _ARCH_STEM.match(stem)
    if match is None or not _has_letter(match.group(3)):
        issue = (
            "file name must be ARCH-{slug} or ARCH-{NN}[-{n}]-{slug} with an arc42 chapter number"
            f" and a kebab-case slug: {stem}"
        )
        return target(path_issue=issue)
    chapter = match.group(1)
    if chapter and chapter not in _ARCH_CHAPTERS:
        issue = (
            f'arc42 chapter "{chapter}" is not available for ARCH documents'
            f" (01-08, 10, 11; decisions and glossary have their own directories): {stem}"
        )
        return target(path_issue=issue)
    return target(slug=match.group(3), expected_id=stem)


def _markdown(ctx: RuleContext, directory: str) -> list[str]:
    """Workspace-relative paths of the Markdown files under ``directory``."""
    base = ctx.workspace_root / directory
    if not base.is_dir():
        return []
    return [path.relative_to(ctx.workspace_root).as_posix() for path in ctx.cache.find_files(base, extensions=(".md",))]


def _targets(ctx: RuleContext) -> list[_Target]:
    """Every identifier target of the workspace, whatever the run targets, so duplicates are seen across it."""
    targets: list[_Target] = []
    for path in _markdown(ctx, "docs/decisions"):
        if not path.endswith("/README.md"):
            targets.append(_decision(path))
    for path in _markdown(ctx, "specs"):
        parts = path.split("/")
        if len(parts) >= 2 and parts[-2] == "feedback":
            if parts[-1] != "README.md":
                targets.append(_feedback(path))
        elif parts[-1] in _SPEC_FILES:
            targets.append(_spec_file(path, _SPEC_FILES[parts[-1]]))
    registered = namespaces(ctx)
    for docs_root in docs_roots(registered):
        for directory, kind in _LIVING_DIRECTORIES.items():
            for path in _markdown(ctx, f"{docs_root}/{directory}"):
                if not path.endswith("/README.md"):
                    targets.append(_living_spec(path, kind, docs_root, registered))
    return targets


def _reference_files(ctx: RuleContext) -> list[str]:
    """The Markdown files whose frontmatter and prose must not use date- or number-based references."""
    registered = namespaces(ctx)
    files = [path for path in _markdown(ctx, "docs") if not living_path(registered, path).startswith("docs/materials/")]
    return files + _markdown(ctx, "specs")


def _completed_bundles(index: DocumentIndex) -> set[str]:
    """``specs/<month>/<bundle>`` of every completed spec bundle."""
    return {"/".join(d.path.split("/")[:3]) for d in index.documents if index.is_historical(d)}


def _block(text: str) -> FrontmatterBlock | None:
    """The frontmatter block; an unclosed one counts as none."""
    try:
        return locate(text)
    except FrontmatterError:
        return None


def _field(header: str, name: str) -> str:
    """The value of the first top-level ``name:`` line (``id``, ``reconcile_id`` or ``area``), unquoted."""
    if name == "area":
        match = _AREA_LINE.search(header)
        return match.group(1).strip("\"'") if match else ""
    for match in _ID_LINE.finditer(header):
        if match.group(1) == name:
            return match.group(2).strip("\"'")
    return ""


def _heading(text: str, block: FrontmatterBlock | None) -> VisibleLine | None:
    """The first H1 line of the body outside code and comments; its text is the raw line."""
    start, first_line = (block.end, block.body_line) if block else (0, 1)
    for line in visible_lines(text, start=start, first_line=first_line, mask_links=False, keep_id_spans=False):
        if line.text.startswith("# "):
            raw = text[line.offset : line.offset + len(line.text)]
            return VisibleLine(line.number, line.offset, raw)
    return None


def _heading_token(heading: VisibleLine | None) -> str | None:
    match = _HEADING_TOKEN.search(heading.text) if heading else None
    return match.group(1) if match else None


def _convention_lines(text: str) -> Iterator[VisibleLine]:
    """Frontmatter lines as written, then the body's prose lines with code, comments and escapes blanked."""
    try:
        block = locate(text)
    except FrontmatterError:  # never closed: every line belongs to the frontmatter
        for number, line in enumerate(text.split("\n"), start=1):
            yield VisibleLine(number, 0, line)
        return
    start, first_line = 0, 1
    if block is not None:
        for number, line in enumerate(text[: block.end].split("\n")[: block.body_line - 1], start=1):
            yield VisibleLine(number, 0, line)
        start, first_line = block.end, block.body_line
    yield from visible_lines(text, start=start, first_line=first_line, mask_links=False, keep_id_spans=False)


def _legacy_references(line: str) -> list[re.Match[str]]:
    """The date- or number-based identifier references in one line, in line order."""
    found = list(_LEGACY_REF.finditer(line))
    for match in _ARCH_REF.finditer(line):
        rest = match.group(0)[len("ARCH-") + 2 :]
        rest = _ARCH_SUBDOCUMENT.sub("", rest, count=1)
        if not _HAS_LETTER.search(rest):
            found.append(match)
    return sorted(found, key=lambda match: match.start())


def _set_field(header: str, name: str, value: str, newline: str) -> str:
    """``header`` with every top-level ``name:`` line set to ``value``; a missing ``id`` / ``reconcile_id`` becomes
    the first line, a missing ``area`` follows the ``id`` line."""
    line = f"{name}: {value}"
    if name == "area":
        if _AREA_LINE.search(header):
            return _AREA_LINE.sub(lambda _: line, header)
        anchor = _ANY_ID_LINE.search(header)
        if anchor is not None:
            return f"{header[: anchor.end()]}{newline}{line}{header[anchor.end() :]}"
        return f"{line}{newline}{header}"
    if any(match.group(1) == name for match in _ID_LINE.finditer(header)):
        return _ID_LINE.sub(lambda match: line if match.group(1) == name else match.group(0), header)
    return f"{line}{newline}{header}"


class IdConventionRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="slug-identifier-convention-check",
            description=(
                "ADR, Change Spec and Feedback documents use slug identifiers in date-partitioned paths, Living Spec"
                " identifiers are their file stems, and no reference is date- or number-based."
            ),
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            guide="guide.md",
            related=("spec:living-spec-writing",),
        )

    def check(self, ctx: RuleContext) -> list[Violation]:
        index = document_index(ctx)
        completed = _completed_bundles(index)
        found: list[Violation] = []

        def reportable(path: str) -> bool:
            if not ctx.is_file_targeted(path):
                return False
            return "/".join(path.split("/")[:3]) not in completed or explicitly_targeted(ctx, path)

        def add(
            path: str, line: int, message: str, remediation: str, *, column: int = 0, fixable: bool = False
        ) -> None:
            found.append(
                Violation(
                    rule_id=self.id,
                    file=path,
                    line=line,
                    column=column,
                    message=message,
                    remediation=remediation,
                    fixable=fixable,
                )
            )

        targets = _targets(ctx)
        owners: dict[str, list[str]] = {}
        for target in targets:
            if target.expected_id and (
                target.kind in (Kind.DECISION, *_LIVING_SPEC) or target.expected_id.startswith("SPEC-")
            ):
                owners.setdefault(target.expected_id, []).append(target.path)
        for target in targets:
            if reportable(target.path):
                self._target(ctx, target, owners, add)
        for path in _reference_files(ctx):
            if not reportable(path):
                continue
            for line in _convention_lines(ctx.cache.read_text(path)):
                for match in _legacy_references(line.text):
                    add(
                        path,
                        line.number,
                        f'Date- or number-based identifier reference "{match.group(0)}"',
                        _REFERENCE_REMEDIATION,
                        column=match.start() + 1,
                    )
        return sorted(found, key=lambda v: (v.file, v.line, v.column))

    def _target(self, ctx: RuleContext, target: _Target, owners: dict[str, list[str]], add: Add) -> None:
        path = target.path
        if target.path_issue:
            if target.kind in _LIVING_SPEC:
                remediation = (
                    f"Rename or move the file to the required path (the ID is the file stem), then run `{FIX_COMMAND}`"
                )
            else:
                remediation = (
                    "Move the file to {YYYY-MM}/{YYYYMMDD}-{slug} with the decision or start date,"
                    f" then run `{FIX_COMMAND}`"
                )
            add(path, 1, f"Invalid partition path: {target.path_issue}", remediation)
            return
        text = ctx.cache.read_text(path)
        block = _block(text)
        if block is None:
            add(
                path,
                1,
                f"Missing YAML frontmatter; expected {target.field}: {target.expected_id}",
                f"Add a frontmatter block with {target.field}, title and status",
            )
        else:
            declared = _field(block.header, target.field)
            if declared != target.expected_id:
                add(
                    path,
                    1,
                    f'Frontmatter {target.field} is "{declared}" but the path requires "{target.expected_id}"',
                    f"Run `{FIX_COMMAND}` or set {target.field}: {target.expected_id}",
                    fixable=True,
                )
            area = _field(block.header, "area")
            if target.expected_area and area != target.expected_area:
                directory = "stories" if target.kind is Kind.STORY else "capabilities"
                add(
                    path,
                    1,
                    f'Frontmatter area is "{area}" but the directory requires "{target.expected_area}"',
                    f"Run `{FIX_COMMAND}` or set area: {target.expected_area}"
                    f" (or move the file to {target.docs_root}/{directory}/{area}/)",
                    fixable=True,
                )
        heading = _heading(text, block)
        token = _heading_token(heading)
        if heading is not None and token is not None and token not in target.allowed_tokens():
            add(
                path,
                heading.number,
                f"Heading token [{token}] does not match identifier {' or '.join(target.allowed_tokens())}",
                f"Run `{FIX_COMMAND}` or rewrite the heading token to the slug-based identifier",
                fixable=True,
            )
        sharing = owners.get(target.expected_id, [])
        if len(sharing) > 1:
            add(
                path,
                1,
                f"Identifier {target.expected_id} is duplicated across {', '.join(sharing)}",
                "Rename one slug; slugs must be unique per document type across all partitions and areas",
            )

    def fix(self, ctx: RuleContext) -> list[str]:
        completed = _completed_bundles(document_index(ctx))
        changed: list[str] = []
        for target in _targets(ctx):
            path = target.path
            if target.path_issue or not ctx.is_file_targeted(path) or "/".join(path.split("/")[:3]) in completed:
                continue
            text = ctx.cache.read_text_strict(path)
            if text is None:
                continue
            block = _block(text)
            updated = text
            heading = _heading(text, block)
            token = _heading_token(heading)
            if heading is not None and token is not None and token not in target.allowed_tokens():
                replacement = target.heading_id()
                if f"`{token}`" in heading.text:
                    line = heading.text.replace(f"`{token}`", f"`{replacement}`", 1)
                else:
                    line = heading.text.replace(f"[{token}]", f"[{replacement}]", 1)
                updated = updated[: heading.offset] + line + updated[heading.offset + len(heading.text) :]
            if block is not None:  # the heading follows the header, so the header offsets still hold
                header = block.header
                newline = block.newline or "\n"
                if _field(header, target.field) != target.expected_id:
                    header = _set_field(header, target.field, target.expected_id, newline)
                if target.expected_area and _field(header, "area") != target.expected_area:
                    header = _set_field(header, "area", target.expected_area, newline)
                updated = updated[: block.header_start] + header + updated[block.header_end :]
            if updated != text:
                ctx.cache.write_text(path, updated, dry_run=ctx.dry_run)
                changed.append(path)
        return changed
