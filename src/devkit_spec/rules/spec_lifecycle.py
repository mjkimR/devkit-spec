"""``RULE-spec-lifecycle``: a spec bundle's ``spec.md`` status, ``tasks.md`` progress and ``reconcile.md`` agree.

Every ``spec.md`` under ``specs/`` defines a bundle (its directory). The rule reports, on ``spec.md``:

- ``status: completed`` without a ``reconcile.md`` beside it;
- ``status: completed`` with a ``reconcile.md`` whose status is not ``resolved``;
- any other status while ``reconcile.md`` is ``resolved`` and ``tasks.md`` has at least one checklist item and none
  open (``devkit.rules.count_tasks``): the status is stale (fixable: the fix sets ``status: completed``).

Statuses are compared trimmed and lower-cased. Completed bundles are checked too: their status is what the first two
conditions are about, so the history exclusion of the other rules (``rules.reportable``) does not apply here.

The relationship spans three files, so a change to any of them can break it. A bundle is reported when the run
targets its ``spec.md`` (every bundle in a whole-workspace run, excluded ones aside) or names its ``reconcile.md`` or
``tasks.md`` as an explicit target; the violation then lands on ``spec.md`` when that is targeted, otherwise on the
first named file, so it is always reported in a file the run targets. The fix rewrites only a targeted ``spec.md``
whose frontmatter has a top-level ``status:`` line, and keeps every other character of the file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from devkit.core import FrontmatterError
from devkit.core.frontmatter import locate
from devkit.rules import Phase, RuleContext, Severity, Violation, count_tasks
from devkit.rules.rules import BaseRule

from devkit_spec.rules import FIX_COMMAND, explicitly_targeted

RULE_ID = "RULE-spec-lifecycle"
COMPLETED = "completed"
RESOLVED = "resolved"
_STATUS_LINE = re.compile(r"^status:[ \t]*[^\r\n]*", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class _Bundle:
    """The lifecycle files of one spec bundle (workspace-relative paths) and what they say."""

    spec: str
    reconcile: str
    tasks: str
    spec_status: str
    has_reconcile: bool
    reconcile_status: str
    open_tasks: int
    done_tasks: int


@dataclass(frozen=True, slots=True)
class _Finding:
    file: str
    message: str
    remediation: str
    fixable: bool


class SpecLifecycleRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="spec-lifecycle-consistency",
            description=(
                "Completed specs have a resolved reconcile.md, and specs whose tasks and reconcile are finished are"
                " marked status: completed."
            ),
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            guide="guide.md",
            related=("spec:living-spec-writing",),
        )

    def check(self, ctx: RuleContext) -> list[Violation]:
        found: list[Violation] = []
        for bundle in _bundles(ctx):
            finding = _evaluate(ctx, bundle)
            if finding is not None:
                found.append(
                    Violation(
                        rule_id=self.id,
                        file=finding.file,
                        line=1,
                        message=finding.message,
                        remediation=finding.remediation,
                        fixable=finding.fixable,
                    )
                )
        return found

    def fix(self, ctx: RuleContext) -> list[str]:
        changed: list[str] = []
        for bundle in _bundles(ctx):
            finding = _evaluate(ctx, bundle)
            if finding is None or not finding.fixable:
                continue
            text = ctx.cache.read_text_strict(bundle.spec)
            updated = _completed(text) if text is not None else None
            if updated is not None and updated != text:
                ctx.cache.write_text(bundle.spec, updated, dry_run=ctx.dry_run)
                changed.append(bundle.spec)
        return changed


def _bundles(ctx: RuleContext) -> list[_Bundle]:
    root = ctx.workspace_root
    bundles: list[_Bundle] = []
    for path in ctx.cache.find_files(root / "specs", extensions=(".md",)):
        if path.name != "spec.md":
            continue
        spec = path.relative_to(root).as_posix()
        base = spec.removesuffix("spec.md")
        reconcile, tasks = f"{base}reconcile.md", f"{base}tasks.md"
        has_reconcile = _read(ctx, reconcile) is not None
        tasks_text = _read(ctx, tasks)
        done, total = count_tasks(tasks_text) if tasks_text is not None else (0, 0)
        bundles.append(
            _Bundle(
                spec=spec,
                reconcile=reconcile,
                tasks=tasks,
                spec_status=_status(ctx, spec),
                has_reconcile=has_reconcile,
                reconcile_status=_status(ctx, reconcile) if has_reconcile else "",
                open_tasks=total - done,
                done_tasks=done,
            )
        )
    return bundles


def _evaluate(ctx: RuleContext, bundle: _Bundle) -> _Finding | None:
    """The bundle's violation, placed on a file the run targets; ``None`` when consistent or not targeted."""
    spec_targeted = ctx.is_file_targeted(bundle.spec)
    if spec_targeted:
        file = bundle.spec
    else:
        named = [path for path in (bundle.reconcile, bundle.tasks) if explicitly_targeted(ctx, path)]
        if not named:
            return None
        file = named[0]
    if bundle.spec_status == COMPLETED:
        if not bundle.has_reconcile:
            return _Finding(
                file,
                f"Completed spec {bundle.spec} has no reconcile.md",
                "Write reconcile.md with reconcile_id, status: resolved and targets after syncing the"
                " Living Spec, or set the spec status back to its real stage",
                fixable=False,
            )
        if bundle.reconcile_status != RESOLVED:
            return _Finding(
                file,
                f"Completed spec {bundle.spec} has reconcile.md with status '{bundle.reconcile_status}'",
                "Resolve every reconcile target (modified, or waived with a substantive rationale) and set the"
                " reconcile status: resolved",
                fixable=False,
            )
        return None
    if bundle.has_reconcile and bundle.reconcile_status == RESOLVED and bundle.done_tasks > 0 and not bundle.open_tasks:
        fixable = spec_targeted and _has_status_line(ctx, bundle.spec)
        return _Finding(
            file,
            f"Spec status '{bundle.spec_status}' of {bundle.spec} is stale:"
            " all tasks are checked and reconcile.md is resolved",
            f"Run `{FIX_COMMAND} {bundle.spec}` to set status: completed in spec.md",
            fixable=fixable,
        )
    return None


def _read(ctx: RuleContext, path: str) -> str | None:
    try:
        return ctx.cache.read_text(path)
    except FileNotFoundError:
        return None


def _status(ctx: RuleContext, path: str) -> str:
    """The frontmatter ``status`` trimmed and lower-cased; ``""`` when missing, not a scalar or unreadable."""
    try:
        data = ctx.cache.get_frontmatter(path)
    except FrontmatterError:
        return ""
    value = data.get("status") if data else None
    if value is None or isinstance(value, dict | list):
        return ""
    return str(value).strip().lower()


def _has_status_line(ctx: RuleContext, path: str) -> bool:
    text = _read(ctx, path)
    return text is not None and _completed(text) is not None


def _completed(text: str) -> str | None:
    """``text`` with its frontmatter ``status:`` line set to ``completed``; ``None`` when there is no such line."""
    try:
        block = locate(text)
    except FrontmatterError:
        return None
    if block is None or not _STATUS_LINE.search(block.header):
        return None
    header = _STATUS_LINE.sub("status: completed", block.header)
    return text[: block.header_start] + header + text[block.header_end :]
