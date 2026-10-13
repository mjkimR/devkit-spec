from __future__ import annotations

from pathlib import Path

from devkit.rules import Rule, RuleContext, Violation, evaluate_rules


def run(rule: Rule, root: Path, *targets: str, fix: bool = False) -> list[Violation]:
    """Evaluate ``rule`` in ``root`` (whole workspace unless ``targets``), fixing first when ``fix``."""
    ctx = RuleContext(workspace_root=root, changed_files=list(targets), fix=fix)
    result = evaluate_rules(ctx, [rule])
    assert result.errors == []
    return result.violations


def found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]
