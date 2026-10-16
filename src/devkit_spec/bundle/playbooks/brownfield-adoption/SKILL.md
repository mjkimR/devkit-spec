---
name: brownfield-adoption
description: Adopt spec-driven development in an existing repository that already has code and docs or specs Markdown; install devkit-spec, contain legacy documents and rule violations so the checks pass, then migrate legacy content into the Living Spec through normal work.
aliases:
  - adopt spec-driven development in an existing repository
  - brownfield adoption
  - migrate legacy docs
  - existing documentation
  - roll out spec rules on an existing codebase
---

# Brownfield adoption

`devkit sync` writes nothing under `docs/` or `specs/`, but the spec rules check the Markdown already there: files in
`docs/architecture/`, `docs/decisions/`, `docs/capabilities/`, `docs/stories/`, `docs/proposals/` and `specs/` break
path and frontmatter conventions, and number-based references such as `ADR-0001` anywhere in `docs/` or `specs/`
break `RULE-id-convention`. This playbook contains that debt so `devkit rules check` passes, then moves legacy content
into the Living Spec as work touches it, each migration ordinary work started with the `spec` skill. Containment never
edits a rule: legacy files move to `docs/materials/`, which the spec rules leave free-form, and any other deferral is
a commented `.devkit/config.toml` entry the user decided.

## Prerequisites

- The user asked for this playbook; their request is the authority for the moves.
- The development environment is managed with `uv`.
- The current state is committed (a rollback point), and `git status` shows no unrelated changes.

## Step 1: Install and synchronize

```bash
uv add --dev devkit devkit-spec
uv run devkit sync
```

The `spec` bundle deploys its `core` preset automatically; in `AGENTS.md` only the `DEVKIT` marker block is written.

## Step 2: Take the baseline and the legacy set

```bash
uv run devkit rules check
uv run devkit rules phases
git ls-files -- 'docs/*.md' 'specs/*.md' > /tmp/legacy.txt
```

The legacy set is the tracked Markdown under `docs/` and `specs/`, minus seeded paths if `spec:docs-skeleton` was
already added (`devkit list` shows them). Review it with the user when it is long or has files already shaped like
the Living Spec; those stay and are fixed as ordinary work. Also note, without moving them, legacy agent instructions
(`AGENTS.md` outside the markers, `CLAUDE.md`, editor rule files) and docs outside `docs/` and `specs/`: inputs to
Step 5.

## Step 3: Contain

Choose per group with the user:

| Situation | Containment |
| :--- | :--- |
| Legacy Markdown under `docs/` or `specs/` | Move it to `docs/materials/_legacy/<original path>` (default) |
| A file a tool needs at its path (an ADR tool, a docs-site build) | Reconfigure the tool, or list the path under `[rules] exclude` |
| A linter rule whose debt is fixed in place, area by area | `[rules.phase_overrides]` `RULE-<id> = "hygiene"` |
| A rule severity that does not fit the project yet | `[rules.severity_overrides]` (`error`, `warning`, `info`) |

Move the legacy set, keeping the layout so links between legacy files keep working:

```bash
while IFS= read -r f; do
  mkdir -p "docs/materials/_legacy/$(dirname "$f")"
  git mv "$f" "docs/materials/_legacy/$f"
done < /tmp/legacy.txt
```

Then update references to the moved paths outside the legacy tree (root `README.md`, docs-site configuration, CI
workflows, agent and editor rule files, code comments): `rg -n --hidden 'docs/|specs/' --glob '!.git/**'
--glob '!docs/**' --glob '!specs/**' --glob '!.devkit/**'`.

Write each deferral with its reason directly above it:

```toml
# Brownfield adoption: the ADR tool reads docs/decisions/NNNN-*.md (user decision).
[rules]
exclude = ["docs/decisions/0*.md"]

# Brownfield adoption: broken links in code docs are repaired as each area is touched.
[rules.phase_overrides]
RULE-markdown-link = "hygiene"
```

`uv run devkit rules check` must exit `0`. Propose committing the containment as one change before any migration,
so moves and content edits stay reviewable apart.

## Step 4: Docs skeleton, policy and commit gate

- **Docs skeleton** (optional): `uv run devkit add spec:docs-skeleton` writes the Living Spec directories, arc42
  starter chapters and glossary only where no file exists; then they are project-owned. A link to a legacy index such
  as `docs/README.md` now reaches the starter; point it at the `_legacy/` copy when the reader needs the old content.
- **Policy**: show `uv run devkit spec policy`. `plan-intent` and `plan-accept` are always the user's;
  `dev-integration` defaults to `ask`. Record only the user's choices (`[workflow.approvals]`, `[workflow.stages]`,
  `[worktree]`, `[tool.spec]`) in `.devkit/config.toml`.
- **Commit gate**: sync installs the hooks; the `rules-check` gate (on by default) refuses a commit touching a file
  with an error finding. The user chooses: fix, park or lower the rule in `[rules]`, or `enabled = false` in
  `[gates.settings.rules-check]` for now. `uv run devkit gate status` must exit `0`.

## Step 5: Classify

Decide per legacy document where its content belongs; record nothing in a tracking file.

| Legacy content | Destination |
| :--- | :--- |
| Behavior the system provides, its scope and invariants | Capability `docs/capabilities/<area>/CAP-<AREA>-<slug>.md` |
| A user goal with acceptance scenarios | Story `docs/stories/<area>/US-<slug>.md` |
| Context, containers, components, runtime, deployment, cross-cutting concepts | arc42 chapter `docs/architecture/ARCH-<NN>-<slug>.md` |
| A decision with its rationale | `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`, dated by the original decision |
| Setup, build, release and contribution guides | `docs/development/` |
| Terms | `docs/glossary.md` |
| Agent working rules | `AGENTS.md` outside the markers when every task needs it; otherwise an instruction, playbook or rule (the `spec-rule` skill) in the project's in-repository bundle (`devkit get-context devkit`, instruction `in-repo-bundle`) |
| An in-progress feature spec (for example spec-kit `specs/NNN-*/`) | A new spec through the `spec` skill when that work resumes |
| Research, meeting notes, superseded plans, completed specs | Stay in `_legacy/` as reference material |

Templates: `.devkit/managed/spec/templates/<kind>.md` (`capability`, `story`, `decision`, `proposal`).

## Step 6: Migrate incrementally

- Migrate an area's legacy content when work touches it, typically in the `spec-sync` skill. Migrate up front only
  what the user asks for, such as decisions that constrain current work.
- Write migrated documents in the current state, citing IDs, without legacy change logs. Fill a starter chapter
  instead of keeping a second architecture description outside `_legacy/`.
- Per migrated file, delete the legacy copy (superseded) or keep it (history the Living Spec does not carry).
- Report a legacy instruction that conflicts with the spec constitution (`devkit get-context spec`) to the user; do
  not choose precedence by file name or read order.
- Retire deferrals as debt clears: a whole-workspace `uv run devkit rules check --phase hygiene` prints
  `[PHASE_OVERRIDE: ... remaining=N]`, and at `remaining=0` a `RULES_PROMOTION_READY` notice says to delete the entry.

## Gotchas

- **Links leaving the legacy tree**: a moved file's relative link out of `_legacy/` (`../src/main.go`) now fails
  `RULE-markdown-link`. Prefix it with `../../../`, or, with the user's decision, exclude `docs/materials/_legacy/**`.
- **`RULE-file-length` warnings under `_legacy/`** (hygiene phase): accept them, or add a commented
  `[[rules.settings.RULE-file-length.overrides]]` entry for `docs/materials/_legacy/**`.
- **`GATE_FOREIGN_HOOK` or `GATE_HOOKS_PATH_SET`** from `gate install`: other hooks exist. Stop and ask the user.

## Completion conditions

- `uv run devkit rules check` exits `0`, and every entry added to `.devkit/config.toml` carries its reason.
- One small real change has gone through the `spec` skill. An empty `_legacy/` is not required.
- `git status` reviewed and the commits proposed (containment, then any migration); observations about this
  procedure recorded with the `spec-feedback` skill when needed.
