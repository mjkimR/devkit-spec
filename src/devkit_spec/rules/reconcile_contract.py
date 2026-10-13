"""``RULE-reconcile-contract``: a ``reconcile.md`` record is well formed.

``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/reconcile.md`` records how a change was reconciled into the Living Spec. Its
frontmatter needs ``reconcile_id`` (its value is ``RULE-id-convention``'s), ``status`` ``pending`` (reconciliation
under way) or ``resolved``, and ``targets``: a list of ``{file, resolution, rationale}`` where ``file`` is a
workspace-relative path, unique in the list, ``resolution`` is ``modified`` (the Living Spec file changed with this
work) or ``waived`` (no change needed), and a waiver's ``rationale`` holds at least 20 non-whitespace characters, so
it says why. Whether a completed spec has a resolved record is ``RULE-spec-lifecycle``'s.

Checked on every targeted ``reconcile.md`` of a current bundle (a completed bundle's record is history, checked only
when named as an explicit target). Not ported yet: specrig's diff evidence (a ``modified`` target must be in the
diff of the commit or pull request that resolves the record), which needs the rule engine to expose the Git snapshot
a ``check --staged`` or ``--ci`` run evaluates.
"""

from __future__ import annotations

from devkit.core import FrontmatterError, is_safe_relpath
from devkit.rules import Phase, RuleContext, Severity, Violation
from devkit.rules.rules import BaseRule

from devkit_spec.rules import explicitly_targeted

RULE_ID = "RULE-reconcile-contract"
STATUSES = ("pending", "resolved")
RESOLUTIONS = ("modified", "waived")
MIN_RATIONALE = 20
REMEDIATION = (
    "Give reconcile.md reconcile_id, status pending|resolved and targets: [{file, resolution: modified|waived,"
    f" rationale}}] with a rationale of at least {MIN_RATIONALE} non-whitespace characters for each waiver"
)


def _problems(data: dict[str, object]) -> list[str]:
    problems: list[str] = []
    if not isinstance(data.get("reconcile_id"), str) or not str(data.get("reconcile_id")).strip():
        problems.append("reconcile_id is missing")
    status = data.get("status")
    if status not in STATUSES:
        problems.append(f"status must be pending or resolved, got {status!r}")
    targets = data.get("targets")
    if not isinstance(targets, list):
        problems.append("targets must be a list (empty when nothing in the Living Spec is affected)")
        return problems
    seen: set[str] = set()
    for position, target in enumerate(targets, 1):
        if not isinstance(target, dict):
            problems.append(f"targets[{position}] must be a mapping of file, resolution and rationale")
            continue
        file = target.get("file")
        if not isinstance(file, str) or not is_safe_relpath(file) or file in seen:
            problems.append(f"targets[{position}].file {file!r} must be a unique workspace-relative path")
        else:
            seen.add(file)
        resolution = target.get("resolution")
        if resolution not in RESOLUTIONS:
            problems.append(f"targets[{position}].resolution must be modified or waived, got {resolution!r}")
        elif resolution == "waived":
            rationale = target.get("rationale")
            length = sum(not char.isspace() for char in rationale) if isinstance(rationale, str) else 0
            if length < MIN_RATIONALE:
                problems.append(
                    f"targets[{position}] waiver of {file} needs a rationale of at least {MIN_RATIONALE}"
                    f" non-whitespace characters, has {length}"
                )
    return problems


class ReconcileContractRule(BaseRule):
    def __init__(self) -> None:
        super().__init__(
            id=RULE_ID,
            name="reconcile-contract",
            description="A reconcile.md record has an id, a pending or resolved status and well-formed targets.",
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            guide="reconcile_contract.md",
        )

    def check(self, ctx: RuleContext) -> list[Violation]:
        root = ctx.workspace_root
        if not (root / "specs").is_dir():
            return []
        found: list[Violation] = []
        for path in ctx.cache.find_files(root / "specs", extensions=(".md",)):
            relative = path.relative_to(root).as_posix()
            parts = relative.split("/")
            if path.name != "reconcile.md" or len(parts) != 4 or not ctx.is_file_targeted(relative):
                continue
            if self._completed(ctx, "/".join(parts[:3])) and not explicitly_targeted(ctx, relative):
                continue
            try:
                data = ctx.cache.get_frontmatter(path)
            except FrontmatterError as exc:
                found.append(self._violation(relative, f"frontmatter is malformed: {exc.message}"))
                continue
            if data is None:
                found.append(self._violation(relative, "reconcile.md has no frontmatter"))
                continue
            found.extend(self._violation(relative, problem) for problem in _problems(data))
        return found

    def _completed(self, ctx: RuleContext, bundle: str) -> bool:
        spec = ctx.workspace_root / bundle / "spec.md"
        try:
            data = ctx.cache.get_frontmatter(spec) if spec.is_file() else None
        except FrontmatterError:
            return False
        status = data.get("status") if data else None
        return isinstance(status, str) and status.strip().lower() == "completed"

    def _violation(self, file: str, message: str) -> Violation:
        return Violation(rule_id=self.id, file=file, line=1, message=message, remediation=REMEDIATION)
