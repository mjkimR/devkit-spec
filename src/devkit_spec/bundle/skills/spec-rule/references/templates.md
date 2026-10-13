# spec-rule templates

Read this at Step 2 of the `spec-rule` skill. Starting points for a new rule asset in the repository's in-repository bundle (`tools/<repo>-devkit/src/<package>/bundle/`). Rename `RULE-myrepo-final-newline`, `final_newline` and the classes; keep the structure. The example is complete and fixable: Markdown files under the configured paths must end with a newline.

## Layout and registration

```text
bundle/
  bundle.toml
  rules/final_newline/
    final_newline.py      # BaseRule subclass(es); every .py file of the asset is loaded
    final_newline.md      # guide: `devkit rules explain`, cited by violations
```

```toml
# bundle.toml
[[assets]]
id = "final-newline"
kind = "rule"
source = "rules/final_newline"

[presets.all]             # or the preset the project selects
assets = ["final-newline"]
```

## Guide

```markdown
# RULE-myrepo-final-newline

One paragraph: what the rule protects and why a violation matters.

## Violations

The concrete file state that triggers the rule, and the file and line it is reported on.

## Remediation

Step-by-step fix; what `devkit rules fix` does and what must be fixed by hand.

## Settings

| Key | Default | Meaning |
| --- | --- | --- |
| `paths` | `["docs/**"]` | Workspace-relative patterns of checked files |
| `extensions` | `[".md"]` | Checked file extensions |

## Examples

Incorrect: ...

Correct: ...
```

## Rule file

```python
"""``RULE-myrepo-final-newline``: text files under the configured paths end with a newline."""

from __future__ import annotations

from dataclasses import dataclass, field

from devkit.rules import Phase, RuleContext, Severity, Violation
from devkit.rules.engine.settings import match_path, validate_pattern
from devkit.rules.rules import BaseRule


@dataclass(frozen=True)
class FinalNewlineSettings:
    # Fields: int, float, str, bool or list[str], each optionally `| None`; no nested tables.
    paths: list[str] = field(default_factory=lambda: ["docs/**"])
    extensions: list[str] = field(default_factory=lambda: [".md"])


class FinalNewlineRule(BaseRule):
    def __init__(self) -> None:  # instantiated without arguments
        super().__init__(
            id="RULE-myrepo-final-newline",
            name="final-newline",
            description="Text files under the configured paths end with a newline.",
            phase=Phase.LINTER,
            severity=Severity.ERROR,
            settings=FinalNewlineSettings(),
            guide="final_newline.md",  # relative to this file
        )

    def validate_settings(self, settings: FinalNewlineSettings) -> None:
        # Raise ValueError for values the field types cannot express.
        for pattern in settings.paths:
            validate_pattern(pattern)
        for ext in settings.extensions:
            if len(ext) < 2 or not ext.startswith("."):
                raise ValueError(f"extensions must be dot-prefixed, got {ext!r}")

    def check(self, ctx: RuleContext) -> list[Violation]:
        return [
            Violation(
                rule_id=self.id,
                file=rel,
                line=ctx.cache.read_text(rel).count("\n") + 1,
                message="File does not end with a newline",
                remediation="Add a newline after the last line (`devkit rules fix` does it).",
                fixable=True,
            )
            for rel in self._offending(ctx)
        ]

    # Optional (Autofixable): only when the repair has exactly one deterministic result.
    def fix(self, ctx: RuleContext) -> list[str]:
        written: list[str] = []
        for rel in self._offending(ctx):
            text = ctx.cache.read_text_strict(rel)
            if text is None:  # not valid UTF-8: never rewrite
                continue
            if not ctx.dry_run:
                ctx.cache.write_text(rel, text + "\n")
            written.append(rel)
        return written

    def _offending(self, ctx: RuleContext) -> list[str]:
        found: list[str] = []
        for path in ctx.cache.find_files(ctx.workspace_root, extensions=None):
            rel = path.relative_to(ctx.workspace_root).as_posix()
            if not ctx.is_file_targeted(rel):  # run targets and [rules] exclude
                continue
            settings: FinalNewlineSettings = ctx.settings(self, rel)
            if path.suffix not in settings.extensions or not any(match_path(p, rel) for p in settings.paths):
                continue
            text = ctx.cache.read_text(rel)
            if text and not text.endswith("\n"):
                found.append(rel)
        return found
```

The evaluator sets each violation's effective `severity` and `phase`; the rule does not pass them. A rule without settings omits `settings`, `validate_settings` and the `ctx.settings` call. A hygiene rule meant to become a linter rule declares `phase=Phase.HYGIENE, promote_to=Phase.LINTER`.

For a larger rule, keep the implementation in the bundle package (`<package>/rules/final_newline.py`, importable and type-checked) and let the deployed file only subclass it, as the `spec` bundle's rules do; the guide stays beside the deployed file.

## Tests

In the bundle package's `tests/`, never under `bundle/rules/`. Covers scope and targeting, the fix, idempotency, and project settings with `[rules] exclude` through the CLI.

```python
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from devkit.cli import cli
from devkit.rules import RuleContext, RuleRegistry, evaluate_rules

RULES_DIR = Path(__file__).parents[1] / "src/<package>/bundle/rules"
RULE_ID = "RULE-myrepo-final-newline"


def _rules() -> list:
    registry = RuleRegistry()
    rules = registry.discover_from_files([RULES_DIR / "final_newline/final_newline.py"])
    assert not registry.errors
    return rules


def _run(root: Path, *, fix: bool = False, targets: list[str] | None = None) -> list:
    result = evaluate_rules(RuleContext(workspace_root=root, changed_files=targets, fix=fix), _rules())
    assert not result.errors
    return result.violations


def test_reports_only_targeted_files_in_scope(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/ok.md").write_text("# Ok\n")
    (tmp_path / "docs/bad.md").write_text("# Bad")
    (tmp_path / "docs/other.md").write_text("# Other")
    (tmp_path / "README.md").write_text("# Out of scope")
    assert {v.file for v in _run(tmp_path)} == {"docs/bad.md", "docs/other.md"}
    assert [v.file for v in _run(tmp_path, targets=["docs/bad.md"])] == ["docs/bad.md"]


def test_fix_repairs_and_is_idempotent(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/bad.md").write_text("# Bad")
    assert [(v.file, v.fixed) for v in _run(tmp_path, fix=True)] == [("docs/bad.md", True)]
    assert (tmp_path / "docs/bad.md").read_text() == "# Bad\n"
    assert _run(tmp_path, fix=True) == []


def test_project_settings_and_exclude_apply(tmp_path: Path) -> None:
    (tmp_path / ".devkit").mkdir()
    (tmp_path / ".devkit/config.toml").write_text(
        f'[rules]\nexclude = ["docs/legacy/**"]\n\n[rules.settings.{RULE_ID}]\npaths = ["docs/**", "guides/**"]\n'
    )
    for rel in ("docs/legacy/old.md", "guides/a.md"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("no newline")
    result = CliRunner().invoke(
        cli, ["rules", "check", "-w", str(tmp_path), "--rules-dir", str(RULES_DIR), "--format", "json"]
    )
    assert result.exit_code == 1, result.output
    found = [v["file"] for v in json.loads(result.stdout)["violations"] if v["rule_id"] == RULE_ID]
    assert found == ["guides/a.md"]
```

`evaluate_rules` runs one fix pass and one recheck: a repaired finding comes back with `fixed=True`, and a second run returning nothing proves idempotency. Branch on `v.rule_id`, `v.file` and `v.fixable`, not on message text.
