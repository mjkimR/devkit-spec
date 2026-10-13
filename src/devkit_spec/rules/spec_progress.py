"""``RULE-spec-progress``: a spec whose tasks have started is marked ``status: in-progress``.

A bundle (``RULE-spec-lifecycle`` reads them) is reported, on ``spec.md``, when its status is ``draft`` or
``planned`` and at least one task of ``tasks.md`` is checked (``devkit.rules.count_tasks``). A bundle whose every task
is checked and whose ``reconcile.md`` is resolved is left to ``RULE-spec-lifecycle``, which moves it to ``completed``,
so the two fixes never disagree.

The status says where the work is; it is not a contract, so the rule is a ``warning`` (devkit gives each rule one
severity, so the hint cannot live inside ``RULE-spec-lifecycle``, whose violations are errors). Targeting and the fix
follow ``RULE-spec-lifecycle``: a bundle is reported when the run targets its ``spec.md`` or names its ``tasks.md``
as an explicit target, and the fix rewrites only the top-level ``status:`` line of a targeted ``spec.md``.
"""

from __future__ import annotations

from devkit.rules import Phase, RuleContext, Severity, Violation
from devkit.rules.rules import BaseRule

from devkit_spec.rules import FIX_COMMAND
from devkit_spec.rules.spec_lifecycle import Bundle, bundles, has_status_line, placement, stale, with_status

RULE_ID = "RULE-spec-progress"
IN_PROGRESS = "in-progress"
NOT_STARTED = frozenset({"draft", "planned"})


class SpecProgressRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="spec-progress-status",
            description="A draft or planned spec with at least one checked task is marked status: in-progress.",
            phase=Phase.LINTER,
            severity=Severity.WARNING,
            guide="guide.md",
            related=("spec:living-spec-writing",),
        )

    def check(self, ctx: RuleContext) -> list[Violation]:
        found: list[Violation] = []
        for bundle in bundles(ctx):
            file = _reported(ctx, bundle)
            if file is None:
                continue
            found.append(
                Violation(
                    rule_id=self.id,
                    file=file,
                    line=1,
                    message=(
                        f"Spec status '{bundle.spec_status}' of {bundle.spec} is behind its tasks:"
                        f" {bundle.done_tasks} of {bundle.done_tasks + bundle.open_tasks} checked"
                    ),
                    remediation=f"Run `{FIX_COMMAND} {bundle.spec}` to set status: {IN_PROGRESS} in spec.md",
                    fixable=file == bundle.spec and has_status_line(ctx, bundle.spec),
                )
            )
        return found

    def fix(self, ctx: RuleContext) -> list[str]:
        changed: list[str] = []
        for bundle in bundles(ctx):
            if _reported(ctx, bundle) != bundle.spec:
                continue
            text = ctx.cache.read_text_strict(bundle.spec)
            updated = with_status(text, IN_PROGRESS) if text is not None else None
            if updated is not None and updated != text:
                ctx.cache.write_text(bundle.spec, updated, dry_run=ctx.dry_run)
                changed.append(bundle.spec)
        return changed


def _reported(ctx: RuleContext, bundle: Bundle) -> str | None:
    """The file the bundle's violation lands on, or ``None`` when it is not reported."""
    if bundle.spec_status not in NOT_STARTED or bundle.done_tasks == 0 or stale(bundle):
        return None
    return placement(ctx, bundle, (bundle.tasks,))
