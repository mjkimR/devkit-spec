"""``RULE-traceability-link``: stories and capabilities link each other in both directions.

A story (a document under ``docs/stories/``) lists the capabilities it needs in ``capabilities``; a capability (under
``docs/capabilities/``) lists the stories it serves in ``stories``. The relation is M:N and must be recorded on both
sides by exact ID: when a story lists a capability that does not list the story back, or a capability lists a story
that does not list it back, the document missing the reverse link is reported. When that document is not reported
(the run does not target it), the one-sided link is reported on the referencing document instead, so a change that
adds only one side is caught.

The fix appends the missing ID to the reverse field (creating the field when absent, keeping a flow ``[...]`` or
block list in its style), in current documents only and within the targets when the run names any. It never guesses:
a link is fixed only when both IDs are declared by exactly one document and the field is absent or a list. Missing
targets, duplicate IDs and wrong ID kinds are ``RULE-document-reference``'s.

Stories and capabilities of a namespace docs root (``docs/packages/<name>/stories/``, ``.../capabilities/``) are
checked as the global ones, and links cross namespaces freely: IDs are repository-wide.
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml
from devkit.core import FrontmatterError
from devkit.core.frontmatter import locate
from devkit.rules import Phase, RuleContext, Severity, Violation
from devkit.rules.rules import BaseRule

from devkit_spec.config import Namespace
from devkit_spec.documents import Document, DocumentIndex, Reference
from devkit_spec.namespaces import living_path
from devkit_spec.rules import FIX_COMMAND, document_index, is_material, namespaces, reportable

RULE_ID = "RULE-traceability-link"
STORIES_DIRECTORY = "docs/stories/"
CAPABILITIES_DIRECTORY = "docs/capabilities/"
# The field of each side that holds the IDs of the other side.
STORY_FIELD = "capabilities"
CAPABILITY_FIELD = "stories"
_COMPOSER: type[yaml.SafeLoader] = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


@dataclass(frozen=True, slots=True)
class _Gap:
    """``source`` links ``target`` through ``ref``, but ``target``'s ``field`` does not list ``source``."""

    source: Document
    target: Document
    ref: Reference
    field: str
    label: str  # what ``target`` is missing: "story" or "capability"

    def fixable(self, index: DocumentIndex) -> bool:
        """Whether the fix adds the link: both IDs are unambiguous and ``field`` is absent or a list."""
        unique = all(len(index.by_id.get(d.id, [])) == 1 for d in (self.source, self.target))
        return unique and isinstance(self.target.frontmatter.get(self.field, []), list)


def _links(document: Document, field: str) -> list[Reference]:
    return [ref for ref in document.references if ref.field == field]


def _lists(document: Document, field: str, document_id: str) -> bool:
    return any(ref.target.strip() == document_id for ref in _links(document, field))


def _gaps(index: DocumentIndex, registered: tuple[Namespace, ...]) -> list[_Gap]:
    """Every one-sided link, stories before capabilities, each reported once per target document."""
    current = [(d, living_path(registered, d.path)) for d in index.documents if not is_material(d)]
    stories = [d for d, path in current if path.startswith(STORIES_DIRECTORY)]
    capabilities = [d for d, path in current if path.startswith(CAPABILITIES_DIRECTORY)]
    gaps: list[_Gap] = []
    seen: set[tuple[str, str]] = set()
    for sources, targets, field, back, label in (
        (stories, capabilities, STORY_FIELD, CAPABILITY_FIELD, "story"),
        (capabilities, stories, CAPABILITY_FIELD, STORY_FIELD, "capability"),
    ):
        by_id: dict[str, list[Document]] = {}
        for target in targets:
            by_id.setdefault(target.id, []).append(target)
        for source in sources:
            for ref in _links(source, field):
                for target in by_id.get(ref.target.strip(), []):
                    key = (source.path, target.path)
                    if key not in seen and not _lists(target, back, source.id):
                        seen.add(key)
                        gaps.append(_Gap(source, target, ref, back, label))
    return gaps


class TraceabilityLinkRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="bidirectional-traceability-link-check",
            description="Stories and capabilities record their M:N links in both directions by exact ID.",
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            guide="traceability_link.md",
        )

    def check(self, ctx: RuleContext) -> list[Violation]:
        index = document_index(ctx)
        found: list[Violation] = []
        for gap in _gaps(index, namespaces(ctx)):
            source, target = gap.source, gap.target
            fixable = gap.fixable(index)
            if reportable(ctx, index, target):
                remediation = f"Add {source.id} to the {gap.field} list of {target.path}"
                found.append(
                    Violation(
                        rule_id=self.id,
                        file=target.path,
                        line=1,
                        message=f"{target.id} is missing the reverse {gap.label} link to {source.id} ({source.path})",
                        remediation=f"{remediation}, or run `{FIX_COMMAND}`" if fixable else remediation,
                        fixable=fixable,
                    )
                )
            elif reportable(ctx, index, source):
                found.append(
                    Violation(
                        rule_id=self.id,
                        file=source.path,
                        line=gap.ref.line,
                        column=gap.ref.column,
                        message=f"{source.id} links {target.id}, but {target.path} does not list {source.id}"
                        f" in {gap.field}",
                        remediation=f"Add {source.id} to the {gap.field} list of {target.path}"
                        + (f", or run `{FIX_COMMAND} {target.path}`" if fixable else ""),
                    )
                )
        return found

    def fix(self, ctx: RuleContext) -> list[str]:
        index = document_index(ctx)
        additions: dict[str, dict[str, list[str]]] = {}
        for gap in _gaps(index, namespaces(ctx)):
            target = gap.target
            if index.is_historical(target) or not ctx.is_file_targeted(target.path) or not gap.fixable(index):
                continue
            items = additions.setdefault(target.path, {}).setdefault(gap.field, [])
            if gap.source.id not in items:
                items.append(gap.source.id)
        changed: list[str] = []
        for path, fields in additions.items():
            text = ctx.cache.read_text_strict(path)
            if text is None:
                continue
            updated: str | None = text
            for field, ids in fields.items():
                updated = _add_items(updated, field, ids) if updated is not None else None
            if updated is not None and updated != text:
                ctx.cache.write_text(path, updated, dry_run=ctx.dry_run)
                changed.append(path)
        return changed


def _add_items(text: str, field: str, ids: list[str]) -> str | None:
    """``text`` with ``ids`` appended to the frontmatter list ``field``; ``None`` when that is not safe.

    An absent field is added at the end of the header as a block list; a flow list (``[]``, ``[A]``) gets the IDs
    inside its brackets and a block list new ``- ID`` lines at its indentation. Any other value is left alone.
    """
    try:
        block = locate(text)
    except FrontmatterError:
        return None
    if block is None:
        return None
    newline = block.newline or "\n"
    try:
        root = yaml.compose(block.header, Loader=_COMPOSER)
    except yaml.YAMLError:
        return None
    if root is None:
        root = yaml.MappingNode("tag:yaml.org,2002:map", [])
    if not isinstance(root, yaml.MappingNode):
        return None
    node = next((value for key, value in root.value if isinstance(key, yaml.ScalarNode) and key.value == field), None)
    if node is None:
        entry = f"{field}:{newline}" + "".join(f"  - {item}{newline}" for item in ids)
        return text[: block.header_end] + entry + text[block.header_end :]
    if not isinstance(node, yaml.SequenceNode):
        return None
    starts = [0] + [i + 1 for i, char in enumerate(block.header) if char == "\n"]

    def offset(mark: yaml.Mark) -> int:
        return block.header_start + starts[mark.line] + mark.column

    if node.flow_style:
        if node.value:
            at = offset(node.value[-1].end_mark)
            return text[:at] + "".join(f", {item}" for item in ids) + text[at:]
        at = text.rindex("]", 0, offset(node.end_mark))
        return text[:at] + ", ".join(ids) + text[at:]
    if not node.value:
        return None
    end = text.find("\n", offset(node.value[-1].end_mark))
    if end < 0:
        return None
    indent = " " * node.start_mark.column
    entries = "".join(f"{indent}- {item}{newline}" for item in ids)
    return text[: end + 1] + entries + text[end + 1 :]
