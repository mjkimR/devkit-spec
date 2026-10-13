---
name: sr-rule
description: Author, test, and register a deterministic project governance rule as a devkit rule (a BaseRule subclass with its guide, shipped in the repository's own bundle) with optional safe autofix and typed settings.
---

# sr-rule: Governance Rule & Autofix Authoring Workflow

Use this skill when introducing a project convention, architectural boundary, document integrity check, or deterministic remediation (autofix) as a rule.

Rules are not prompt instructions or advisory text. They are fast, deterministic checks that `devkit rules check` runs in the session, the commit gate (`devkit rules check --staged`) runs before every commit and CI runs with `devkit rules check --ci --base <ref>`, to prevent context drift and architectural erosion. The spec bundle's own rules (`RULE-id-convention`, `RULE-spec-lifecycle`, ...; `devkit rules explain <RULE-id>`) are worked examples of the pattern.

---

## 1. Principles

### Principle 1: A project rule ships in the project's own bundle
- A rule the repository keeps is a `kind = "rule"` asset of its **in-repository bundle** (a content package under `tools/<repo>-devkit/`, installed as a dev dependency; devkit's `in-repo-bundle` instruction, listed by `devkit get-context devkit`, describes the setup). `devkit sync` deploys it under `.devkit/managed/<bundle>/`, records it in `.devkit/installation.json`, and `devkit rules` loads it without flags.
- One directory per rule asset: `rules/<name>/<name>.py` (one or more `BaseRule` subclasses; every `.py` file of the asset is loaded) and `rules/<name>/<name>.md` (the guide `devkit rules explain` prints and violations cite).
- `devkit rules check --rules-dir <dir>` loads unrecorded rule files for a local experiment; the commit gate never runs them. Promote a finished experiment into the bundle.
- Never edit `.devkit/managed/` (a changed copy is a `RULES_LOAD_FAILED` loading error). A distributed rule is tuned only in `[rules]` of `.devkit/config.toml`; replacing its content is `devkit override create`.
- Prefix the ID with the repository name (`RULE-myrepo-no-todo`) unless shadowing an upstream rule of the same ID is the intent: a later-loaded rule with an earlier rule's ID replaces it.

### Principle 2: Phase separation (linter vs hygiene)
- **`Phase.LINTER`**: the active gate for sessions, the commit gate and CI. Use for non-negotiable boundaries and contract integrity.
- **`Phase.HYGIENE`**: out-of-session debt collection, run only by `devkit rules check --phase hygiene`. A new rule meeting many existing violations starts here with `promote_to=Phase.LINTER`; the run reports `[PROMOTION: ... remaining=N]` until it can be flipped.
- A project can park a linter rule in hygiene with `[rules.phase_overrides]` ([config](references/config.md)).

### Principle 3: Deterministic autofix
- If a violation can be resolved **without subjective inference or human ambiguity** (missing frontmatter defaults, link normalization, a missing backlink), implement `fix(ctx) -> list[str]` (the `Autofixable` protocol) and mark those violations `fixable=True`.
- Fix only when repository state determines exactly one result (one candidate path, one target ID) or a documented default applies. With several candidates, report a remediation instead.
- Write only through `ctx.cache.write_text`, keep every other byte, leave files `ctx.cache.read_text_strict` rejects alone, and return every path written. The engine runs one fix pass and one recheck; a second run must produce zero changes and zero violations (idempotency). Under `ctx.dry_run` return the paths without writing.

---

## 2. Rule Authoring Workflow

### Step 1: Design ID, phase, severity and targets
1. **Rule ID**: `RULE-<kebab-case>` (prefixed, Principle 1).
2. **Phase**: `linter` or `hygiene` (optional `promote_to`).
3. **Severity**: `error` fails the command (exit 1); `warning` and `info` are reported findings that do not fail. There are no suppression comments: a justified exception is a path in `[rules] exclude`, a per-path settings override, or a severity override in `.devkit/config.toml`, each with a comment giving the reason.
4. **Targets and settings**: which files the rule reads, and which limits or paths a project may tune (typed settings, [config](references/config.md)).

### Step 2: Create the rule files and register the asset
Write `rules/<name>/<name>.py` and `rules/<name>/<name>.md` in the bundle source, then add the asset to its `bundle.toml` and to the preset the project selects. Templates: [templates](references/templates.md).

### Step 3: Implement the check (and fix)
Read files only through `ctx.cache` (`find_files`, `read_text`, `get_frontmatter`, `get_links`, `get_catalog`), so the snapshot gates evaluate exactly the staged or CI tree. Report a file only when `ctx.is_file_targeted(rel)` is true: it applies the run's targets and `[rules] exclude`. Read settings with `ctx.settings(self, rel)`. Give each `Violation` a message and an actionable `remediation`. Template: [templates](references/templates.md#rule-file).

### Step 4: Write tests
Tests live in the bundle package's `tests/`, never in the rule directory (every `.py` file there is loaded as a rule file). Cover a valid case, a violation, targeting and exclusion, the fix, and idempotency (a second fix changes nothing). Template: [templates](references/templates.md#tests).

### Step 5: Validate against devkit
```bash
devkit rules check --rules-dir <bundle>/rules     # trial before deployment
devkit sync                                       # deploy and record the receipt
devkit rules phases                               # default and effective phase
devkit rules explain RULE-<id>                    # settings and the guide as deployed
devkit rules check                                # whole workspace; --phase hygiene for hygiene rules
devkit rules fix --dry-run && devkit rules fix    # fixable findings, then the repair
```
Commit the rule source with the updated `.devkit/installation.json`: the commit gate (`devkit rules check --staged`) reads managed rules only when their hash matches the staged receipt, and a stale receipt fails the gate with a `[FIX]` to run `devkit sync`.

---

## 3. Negative Constraints (MUST NOT)

- **Do NOT edit deployed copies** under `.devkit/managed/` or `.devkit/overrides/`; fixers cannot write there either (`RULES_PINNED_WRITE_REFUSED`).
- **Do NOT read or write the disk directly** in `check` or `fix`; bypassing `ctx.cache` breaks the snapshot gates and the recheck.
- **Do NOT introduce heavy dependencies**: prefer the standard library and devkit's helpers (`devkit.core.frontmatter`, `devkit.rules.extract_links`, `devkit.rules.count_tasks`). A rule file imports only what the project's environment provides.
- **Do NOT persist state files** (debt ledgers, caches); recompute diagnostics deterministically on every run.
- **Do NOT use non-deterministic heuristics, network access or LLM calls** inside rules: evaluation must be deterministic, offline and fast.
- **Do NOT print**: a rule returns violations and raises nothing for findings; output belongs to `devkit rules`.
