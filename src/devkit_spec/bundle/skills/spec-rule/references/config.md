# Rule configuration (`[rules]`)

Read this when a rule needs settings a project may tune (limits, extensions, paths), or when a project must change how an existing rule runs. `[rules]` in the Git-tracked `.devkit/config.toml` is the only place a project changes a distributed rule's behavior; deployed copies under `.devkit/managed/` are never edited.

## Declaring settings (rule author)

Pass a frozen dataclass instance with every default as `settings=` to `BaseRule` ([templates](templates.md#rule-file)). Fields are `int`, `float`, `str`, `bool` or `list[str]`, each optionally `| None` (the only fields that accept `null`); nested tables are rejected when the rule loads. Override `validate_settings(settings)` to raise `ValueError` for values the types cannot express (a non-positive limit, a malformed pattern via `devkit.rules.validate_pattern`); it runs on the defaults, the configured values and every override layer before any rule executes. Read the effective values per file with `ctx.settings(self, rel)` inside `check` and `fix`; never cache them across runs or mutate them.

When settings can change the result for unchanged files, the rule rescans its own targets: there is no per-rule configuration file to watch.

## Configuring (project)

```toml
[rules]
exclude = ["docs/research/**", "CHANGELOG.md"]   # never targeted by any rule

[rules.phase_overrides]
RULE-myrepo-final-newline = "hygiene"            # only "hygiene": park a linter rule while debt is cleared

[rules.severity_overrides]
RULE-myrepo-final-newline = "warning"            # error | warning | info

[rules.settings.RULE-myrepo-final-newline]
paths = ["docs/**", "guides/**"]

[[rules.settings.RULE-myrepo-final-newline.overrides]]
path = "docs/generated/**"                       # workspace-relative; ** spans zero or more segments
extensions = [".txt"]
```

- Layers merge in order: defaults, then `[rules.settings.<id>]`, then every override whose `path` matches the file, in declaration order (later wins). Keys an override omits keep the earlier value; arrays replace.
- `*`, `?` and character classes match within one path segment; a standalone `**` matches zero or more segments.
- Unknown rules, unknown keys, wrong types (`true` is not an integer, `"10"` is not a number), explicit nulls, invalid patterns, `validate_settings` rejections and overrides that change nothing (a severity equal to the declared one, a phase override on a hygiene rule) fail the run with exit code `2` before any rule executes, naming the rule. Overrides valid alone but invalid together fail (`RULES_SETTINGS_INVALID`) when a file matches both.
- A phase override is reported by whole-workspace hygiene runs as `[PHASE_OVERRIDE: ... remaining=N]`; at `remaining=0` a `RULES_PROMOTION_READY` notice says to delete the entry.
- Each exception carries a TOML comment giving its reason; a lasting policy exception follows the spec constitution (an ADR).

## Inspecting

- `devkit rules explain <RULE-id>`: phase, severity, effective settings (`[SETTING: key=value default=value]`), each override (`[SETTING_OVERRIDE: path=... ...]`) and the guide.
- `devkit rules phases`: each rule's default and effective phase and pending promotion, without evaluating.
