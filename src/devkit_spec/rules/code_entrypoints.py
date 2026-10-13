"""``RULE-code-entrypoints``: every ``entrypoints`` path of a capability or story exists in the workspace.

Checks the capabilities and stories (``docs/capabilities/``, ``docs/stories/`` and the same directories under
``docs/packages/<name>/``) that declare ``entrypoints``:

- the field is a list, and each item a string;
- each item is a literal workspace-relative path (``devkit_spec.entrypoints.normalize``: no glob, absolute path,
  ``..`` segment, backslash, colon or control character);
- each path is a file or directory inside the workspace, symbolic links resolved (one pointing outside counts as
  missing). A snapshot run (``check --staged``, ``--ci``) checks against the snapshot's tree, where an empty
  directory does not exist.

An omitted field and an empty list pass. Not fixable: the rule never guesses whether the code moved or the
declaration is obsolete. Reported for the targeted documents (devkit's targeting) and, in a snapshot run, also for
every current document that declares a path the diff deletes: a commit that removes code without touching the
document declaring it is caught by the commit gate and CI, not only by a whole-workspace run.
"""

from __future__ import annotations

from typing import Any

import yaml
from devkit.core import FrontmatterError
from devkit.core.frontmatter import locate
from devkit.rules import Phase, RuleContext, Severity, Violation, match_path
from devkit.rules.rules import BaseRule

from devkit_spec.documents import Document, DocumentIndex, Kind
from devkit_spec.entrypoints import entrypoint_bearing, exists, normalize
from devkit_spec.entrypoints.paths import covers
from devkit_spec.errors import EntrypointsPathError
from devkit_spec.rules import document_index, reportable

RULE_ID = "RULE-code-entrypoints"
FIELD = "entrypoints"
REMEDIATION = (
    "Update entrypoints to existing workspace-relative files or directories, or restore the missing paths; "
    "remove obsolete declarations"
)
_KINDS = (Kind.CAPABILITY, Kind.STORY)
_COMPOSER: type[yaml.SafeLoader] = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


class CodeEntrypointsRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="code-entrypoints",
            description="Every entrypoints path of a capability or story is an existing workspace file or directory.",
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            guide="code_entrypoints.md",
        )

    def check(self, ctx: RuleContext) -> list[Violation]:
        index = document_index(ctx)
        found: list[Violation] = []
        for document in index.documents:
            if FIELD not in document.frontmatter or document.kind not in _KINDS:
                continue
            if not entrypoint_bearing(document.path):
                continue
            if not (reportable(ctx, index, document) or _declares_deleted(ctx, index, document)):
                continue
            found.extend(self._check(ctx, document))
        return found

    def _check(self, ctx: RuleContext, document: Document) -> list[Violation]:
        value = document.frontmatter[FIELD]
        key_line, item_lines = _lines(ctx.cache.read_text(document.path))
        if not isinstance(value, list):
            return [self._violation(document, key_line, f"{FIELD} must be an array of path strings")]
        found = []
        for position, item in enumerate(value):
            line = item_lines[position] if position < len(item_lines) else key_line
            if not isinstance(item, str):
                found.append(self._violation(document, line, f"{FIELD} must contain only path strings"))
                continue
            try:
                path = normalize(item)
            except EntrypointsPathError as exc:
                found.append(self._violation(document, line, exc.message))
                continue
            if not exists(ctx.workspace_root, path):
                found.append(
                    self._violation(document, line, f"Dead code entrypoint: {item!r} (missing or outside workspace)")
                )
        return found

    def _violation(self, document: Document, line: int, message: str) -> Violation:
        return Violation(rule_id=self.id, file=document.path, line=line, message=message, remediation=REMEDIATION)


def _declares_deleted(ctx: RuleContext, index: DocumentIndex, document: Document) -> bool:
    """In a snapshot run, whether a current, non-excluded document declares a path the diff deletes.

    The commit gate targets only the files a commit changes; a commit that deletes code without touching the document
    declaring it would otherwise pass, so such a document is checked too.
    """
    snapshot = ctx.snapshot
    if snapshot is None or not snapshot.deleted or index.is_historical(document):
        return False
    if any(match_path(pattern, document.path) for pattern in ctx.exclude):
        return False
    value = document.frontmatter.get(FIELD)
    if not isinstance(value, list):
        return False
    declared: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        try:
            declared.append(normalize(item))
        except EntrypointsPathError:
            continue
    return any(covers(entry, deleted) for entry in declared for deleted in snapshot.deleted)


def _lines(text: str) -> tuple[int, list[int]]:
    """The 1-based line of the ``entrypoints`` key and of each of its list items (``1`` and none when unknown)."""
    try:
        block = locate(text)
    except FrontmatterError:
        return 1, []
    if block is None:
        return 1, []
    first = text.count("\n", 0, block.header_start) + 1
    try:
        root: Any = yaml.compose(block.header, Loader=_COMPOSER)
    except yaml.YAMLError:
        return 1, []
    if not isinstance(root, yaml.MappingNode):
        return 1, []
    for key, value in root.value:
        if isinstance(key, yaml.ScalarNode) and key.value == FIELD:
            items = value.value if isinstance(value, yaml.SequenceNode) else []
            return first + key.start_mark.line, [first + item.start_mark.line for item in items]
    return 1, []
