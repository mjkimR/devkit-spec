# spec-rule templates

Read this at Step 2 of the `spec-rule` skill. Starting points for a new rule asset in the repository's in-repository bundle (`tools/<repo>-devkit/src/<package>/bundle/`). Rename `RULE-myrepo-final-newline`, `final_newline` and the classes; keep the structure. The example is complete and fixable: Markdown files under the configured paths must end with a newline.

## Layout and registration

```text
bundle/
  bundle.toml
  rules/final_newline/
    rule.py               # BaseRule subclass(es); every .py file outside tests/ is loaded
    guide.md              # guide: `devkit rules explain`, cited by violations
    tests/test_rule.py    # the rule's tests, deployed with it (no __init__.py)
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

devkit's guide sections, read by an agent that just hit a violation:

```markdown
# [RULE-myrepo-final-newline] Final Newline

## 1. Overview

What the rule guarantees and why; phase and severity; which files it checks and which not.

## 2. Cause of Violation

Each condition reported, with its message and where it is reported.

## 3. Remediation

What `devkit rules fix` does, and what must be fixed by hand.

## 4. Configuration

| Setting | Type | Default | Meaning |
| --- | --- | --- | --- |
| `paths` | list of patterns | `["docs/**"]` | Checked files |
| `extensions` | list of suffixes | `[".md"]` | Checked extensions |

## 5. Exceptions

How a justified exception is recorded (path override, `[rules] exclude`, severity override).

## 6. Examples

Optional.
```

## Rule file

```python
"""``RULE-myrepo-final-newline``: text files under the configured paths end with a newline."""

from __future__ import annotations

from dataclasses import dataclass, field

from devkit.rules import Phase, RuleContext, Severity, Violation, match_path, validate_pattern
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
            guide="guide.md",  # relative to the module defining the class
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

For a larger rule, keep the implementation in the bundle package (`<package>/rules/final_newline.py`, importable and type-checked) and let the deployed `rule.py` only subclass it, as the `spec` bundle's rules do; `guide.md` stays beside the deployed file.

## Tests

`rules/final_newline/tests/test_rule.py`. `devkit rules test RULE-myrepo-final-newline` runs it isolated (no project `conftest.py` or pytest configuration), so it imports only `devkit.rules.testing` and the environment's packages.

```python
from __future__ import annotations

from pathlib import Path

from devkit.rules.testing import check, load_rule

RULE = load_rule(__file__)  # the folder above tests/, loaded as devkit loads the deployed copy


def test_reports_only_targeted_files_in_scope(tmp_path: Path) -> None:
    files = {"docs/ok.md": "# Ok\n", "docs/bad.md": "# Bad", "docs/other.md": "# Other", "README.md": "# Out"}
    assert {v.file for v in check(RULE, tmp_path, files)} == {"docs/bad.md", "docs/other.md"}
    assert [v.file for v in check(RULE, tmp_path, targets=["docs/bad.md"])] == ["docs/bad.md"]
    assert {v.file for v in check(RULE, tmp_path, exclude=["docs/other.md"])} == {"docs/bad.md"}


def test_fix_repairs_and_is_idempotent(tmp_path: Path) -> None:
    found = check(RULE, tmp_path, {"docs/bad.md": "# Bad"}, fix=True)
    assert [(v.file, v.fixed) for v in found] == [("docs/bad.md", True)]
    assert (tmp_path / "docs/bad.md").read_text() == "# Bad\n"
    assert check(RULE, tmp_path, fix=True) == []


def test_settings_apply_per_path(tmp_path: Path) -> None:
    settings = {"paths": ["docs/**", "guides/**"], "overrides": [{"path": "guides/legacy/**", "extensions": [".txt"]}]}
    files = {"guides/a.md": "x", "guides/legacy/b.md": "x"}
    assert [v.file for v in check(RULE, tmp_path, files, settings=settings)] == ["guides/a.md"]
```

`check` runs the real engine: settings go through the `[rules.settings.<id>]` parser (invalid values raise `RulesRunError`), and `fix=True` runs one fix pass and one recheck, so a repaired finding comes back with `fixed=True` and a second run returning nothing proves idempotency. `evaluate` returns the whole `EvaluationResult`. Branch on `v.rule_id`, `v.file` and `v.fixable`, not on message text.
