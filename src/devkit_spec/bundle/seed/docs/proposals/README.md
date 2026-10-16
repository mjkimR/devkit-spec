# Proposals

An incubation space to propose and mature new features, technical spikes, or architectural improvements. Every proposal is managed as an isolated bundle directory (`PROP-{slug}/`).

---

## 1. Zero-Clutter Lifecycle Principles

- **Draft & Review (`draft` / `reviewing`)**: In Backlog, scaffold the bundle using `devkit spec proposal new <slug>` (`--task-kind bugfix` for a defect) and define the core hypothesis and spike questions in `proposal.md`; the user's confirmation of the draft is `plan-intent`. Planning runs on its own `plan-<slug>` branch and collects its questions for the user in one round. Isolate preliminary decisions into `decisions/PADR-{slug}.md` and research into `materials/`.
- **Graduation (`accepted`)**: the user's `plan-accept` sets `status: accepted`. Development then starts with `devkit spec proposal handoff <slug>`, which creates the execution specification at `specs/{YYYY-MM}/{YYYYMMDD}-{slug}/` bound to `sdd-spec-<task_kind>`, carries the `plan-intent` and `plan-accept` records, promotes PADRs into `docs/decisions/`, moves `materials/` and any other bundle file (such as a `notes.md`) into `docs/materials/`, copies `target-docs.md` (if present) to the spec directory, rewrites Markdown links and ID references pointing into the bundle, and removes the bundle directory. Follow up the reported unresolved links (`spec-next` skill).
- **Rejection (`rejected`)**: Change only `status: rejected`, with the user's reason in the commit message. A later hygiene pass records the rejection ADR in `docs/decisions/` (referencing the proposal and the rejection commit) and deletes the bundle directory in the same commit.
- Historical context and discussions are tracked via Git history. No `archive/` directories are maintained.

---

## 2. Bundle Layout & Frontmatter Conventions

```text
docs/proposals/PROP-{slug}/
├── proposal.md            # (Required) Core proposal: background, hypothesis, spike questions, non-goals
├── target-docs.md         # (Recommended) Blueprint of target Living Spec changes upon acceptance
├── decisions/             # (Optional) Preliminary decision records (PADR-{slug}.md ...)
└── materials/             # (Optional) On-demand research, benchmarks, external surveys
```

- **`proposal.md` Frontmatter Convention**:
  ```yaml
  ---
  id: PROP-<slug>
  title: Proposal Title
  summary: <One or two English sentences: what this proposal changes and why>   # required, English
  status: draft                         # draft | reviewing | accepted | rejected
  created_at: YYYY-MM-DD
  target_area: capabilities/<area>/      # Target capability area on graduation
  priority: high                        # critical | high | medium | low (estimated priority)
  size: M                               # S | M | L | XL (estimated scope)
  milestone: "Phase 1: Foundation"      # (Optional) Target milestone, phase, or release
  boundaries:
    owns:
      - capabilities/<area>/
    excludes:
      - template/
  task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
  planning_effort: medium               # low | medium | high: Planning activity-effort hint
  dev_effort: medium                    # low | medium | high: Development activity-effort hint
  # supersedes: PROP-<old-slug>         # close by supersede: the accepted proposal this draft replaces
  # needs_decompose: true               # Backlog splits this draft before Planning starts
  ---
  ```
  - **`priority`**: Business/system significance (`critical` > `high` > `medium` > `low`).
  - **`size`**: Estimated implementation scope (S=single fix, M=1-2 sessions, L=complex module, XL=major overhaul).
  - **`milestone`**: (Optional) Target milestone or phase name; carried over to `spec.md` on handoff.
  - **`boundaries`**: Declared scope impact (`owns`) and excluded scope (`excludes`).
  - **`planning_effort` / `dev_effort`**: Non-authoritative `activity-effort` hints (`low` | `medium` | `high`, default `medium`) for Planning and Development; `dev_effort` is refined during Planning before `plan-accept` and returned by `handoff`, while confirmed run effort is recorded on `worker-NN.yaml` envelopes (never copied to `spec.md`).
- **`materials/` Markdown**: follow the material convention: file `{YYYYMMDD}-{slug}.md`, `id: MAT-<slug>`, `created_at`, H1 `# [MAT-<slug>] <title>`. `RULE-spec-format` skips `materials/` directories, so the frontmatter is recommended, not checked. Non-Markdown files need no metadata. After handoff the files move to `docs/materials/`.
- **`target-docs.md` (Recommended)**: Focuses on "What docs/ changes will look like once accepted", while `proposal.md` focuses on "Why". Covers capability ledger, user stories, architecture & decisions, conventions & governance, and before/after comparisons. Recommended for `size: M/L/XL` or when Living Spec structural changes are expected.

---

## 3. CLI Proposal Management & Dynamic Discovery

Do not manually maintain catalog tables in README files. Active proposals are discovered dynamically by parsing frontmatter metadata:

```bash
devkit spec proposal new <slug>                        # Scaffold proposal bundle
devkit spec proposal new <slug> --milestone "Phase 1"   # Scaffold with target milestone
devkit spec proposal new <slug> --with-target-docs      # Scaffold with Living Spec target blueprint
devkit spec proposal new <slug> --task-kind bugfix     # A defect: the spec follows sdd-spec-bugfix
devkit spec proposal new <slug> --planning-effort low --dev-effort high  # Scaffold with explicit effort hints
devkit spec proposal new <slug> --needs-decompose      # Split in Backlog before Planning
devkit spec proposal padr <slug> <title> --summary <text>  # Scaffold preliminary decision (PADR); the summary is kept by the promoted ADR
devkit spec list proposal                               # List proposals
devkit spec proposal handoff <slug>                     # Graduate proposal (scaffold spec, clean bundle)
```
