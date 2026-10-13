---
name: feedback-hygiene
description: Triage open feedback files under specs/ in one batch; group them by target, order them by severity and recurrence, and with the user's decision promote them to rules, playbooks, decisions or spec work, or dismiss or forward them and update their status.
aliases:
  - feedback triage
  - process open feedback
  - promote feedback
  - feedback hygiene session
  - triage critical feedback
---

# Feedback hygiene

Feedback files recorded by the `spec-feedback` skill (`specs/**/feedback/*.md`, kind `feedback`) stay
`status: open` through completion and integration. This playbook is the only path that changes their status:
`spec-feedback` records, it never promotes. Run it in a hygiene session the user asks for, typically when open or
critical items have accumulated.

Every target item ends `promoted`, `dismissed` or `forwarded`, with draft artifacts (rules, playbooks, decision
drafts, bundle fixes, proposals, specs) ready for review.

## Prerequisites

- The user asked for this playbook. Destinations are the user's decisions; this playbook drafts and asks.
- A clean working tree (`git status`), or an isolated branch or task worktree.
- `uv run devkit spec list feedback --status open -n 0` lists at least one item; otherwise report an
  empty backlog and stop.

## Step 1: Collect

```bash
uv run devkit spec list feedback --status open -n 0
```

Feedback of completed spec bundles is included; `--query <text>` narrows by ID or title. Each line carries `severity`,
`scope` and `target`, critical items first. A scope or severity the user names narrows the selection with
`--where scope=<scope>` or `--where severity=<a>,<b>`; otherwise take every open item. Read each selected file's
remaining frontmatter (`kind`, `category`, `recurring`, `origin`) in Step 2.

## Step 2: Group and order

- Group items with the same `target`; a group shares one decision.
- Order groups and items: `critical`, then `recurring: true`, then `blocked`, `workaround`, `noise`.
- Read each body's Evidence section. A suggestion without observed evidence is a dismissal candidate
  ("insufficient evidence").

## Step 3: Decide the destination with the user

Propose one destination per group and get the user's approval before drafting:

| Scope | Destination | Action |
| :--- | :--- | :--- |
| `repo` | Rule | Draft it with the `spec-rule` skill in the project's in-repository bundle |
| `repo` | Playbook | Draft `playbooks/<slug>/SKILL.md` and its `kind = "playbook"` asset in the project's in-repository bundle (`devkit get-context devkit`, instruction `in-repo-bundle`), then `uv run devkit sync` |
| `repo` | Decision | Draft `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md` from `.devkit/managed/spec/templates/decision.md` |
| `repo` | Living Spec fix | A wrong capability, story or architecture statement: fix it through the `spec` skill |
| any | Dismissal | Record the reason in the disposition line (Step 4) |
| `bundle` | Forward | The `spec` bundle or a devkit command it drives: report the group to their maintainers (a defect with clear expected behavior, a wording fix or an open design question) and cite where it was reported |

In a repository that develops the bundle itself, a `bundle` group is promoted there instead: a defect with clear
expected behavior becomes a spec (the `direct-delivery` workflow, or `bugfix` when reproduction matters), a small
wording fix an `s-lane` change, an open design question a proposal (`uv run devkit spec proposal new <slug>`).

## Step 4: Update status and seal

Set the frontmatter `status` of each processed file (`promoted`, `dismissed` or `forwarded`) and append one
disposition line to its body so the destination is traceable:

```markdown
- **Disposition**: <destination ID, path or issue link>: <one-line summary of what was done>
```

The destination is the spec, proposal, decision, rule or playbook ID that received the item, the changed file path
for an `s-lane` fix, or the report location for a forward. A dismissal states its reason in the same line.

## Completion conditions

- Every item selected in Step 1 has `status` `promoted`, `dismissed` or `forwarded` and one disposition line;
  `uv run devkit spec list feedback --status open -n 0` lists none of them.
- Every promotion's draft exists and was reviewed by the user; nothing was promoted without approval.
- `uv run devkit rules check` exits `0`; the status updates and drafts are proposed as one commit.
