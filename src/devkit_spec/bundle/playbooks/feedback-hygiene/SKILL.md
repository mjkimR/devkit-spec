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

Feedback files recorded by the `spec-feedback` skill (spec-local, proposal-local or month-level paths, kind `feedback`) stay
`status: open` through completion and integration. This playbook is the only path that changes their status:
`spec-feedback` records, it never promotes. Run it in a hygiene session the user asks for, typically when open or
critical items have accumulated.

Resolved items end `promoted`, `dismissed` or `forwarded`, with traceable destinations and artifacts ready for
review. Items awaiting ownership resolution or authorized external submission remain `open`.

## Prerequisites

- The user asked for this playbook. Destinations are the user's decisions; this playbook drafts and asks.
- A clean working tree (`git status`), or an isolated branch or task worktree.
- `uv run devkit spec list feedback --status open --all-namespaces -n 0` lists at least one item; otherwise report an
  empty backlog and stop.

## Step 1: Collect

```bash
uv run devkit spec list feedback --status open --all-namespaces -n 0
```

Feedback of completed spec bundles is included; `--query <text>` narrows by ID or title. Each line carries `severity`,
`scope` and `target`, critical items first. A scope or severity the user names narrows the selection with
`--where scope=<scope>` or `--where severity=<a>,<b>`; otherwise take every open item. Read each selected file's
remaining frontmatter (`kind`, `category`, `recurring`, `origin`) in Step 2.

## Step 2: Group and order

- Determine ownership from the observed target and evidence: `repo`, `upstream` or `unknown`. Repository-owned
  rules, skills, instructions and tools are the base targets. Do not ask the user to classify tools; propose the
  resolution destination yourself. Unknown or cross-tool items stay eligible and may need multiple linked fixes.
- Group items with the same `target`; a group shares one decision.
- Order groups and items: `critical`, then `recurring: true`, then `blocked`, `workaround`, `noise`.
- Read each body's Evidence section. A suggestion without observed evidence is a dismissal candidate
  ("insufficient evidence").

## Step 3: Decide the destination with the user

Propose the resolution destination or destinations per group. Draft artifacts within existing authorization
first; request decisions only beyond that scope. External reports are prepared as drafts until submission is authorized:

| Scope | Destination | Action |
| :--- | :--- | :--- |
| `repo` | Rule | Draft it with the `spec-rule` skill in the project's in-repository bundle |
| `repo` | Playbook | Draft `playbooks/<slug>/SKILL.md` and its `kind = "playbook"` asset in the project's in-repository bundle (`devkit get-context devkit`, instruction `in-repo-bundle`), then `uv run devkit sync` |
| `repo` | Decision | Draft `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md` from `.devkit/managed/spec/templates/decision.md` |
| `repo` | Living Spec fix | A wrong capability, story or architecture statement: fix it through the `spec` skill |
| any | Dismissal | Record the reason in the disposition line (Step 4) |
| `upstream` | Forward draft | Prepare a report for the owning tool or bundle, including devkit and devkit-spec; submit only with explicit external-send authorization, then cite the actual report location |
| `unknown` | Ownership review | Inspect the observed targets, propose repository or upstream destinations, and keep unresolved items open |

An asset developed in this repository has `scope: repo` even when shipped as an upstream tool to other projects; promote it locally: a defect with clear
expected behavior becomes a `bugfix` task (`sdd-session-bugfix`, or `sdd-spec-bugfix` when its behavior must be written
down), a small wording fix a `session` change, an open design question a draft proposal (`uv run devkit spec proposal new <slug>`).

## Step 4: Update status and seal

A forwarding draft alone does not count as `forwarded`; leave it `open` until submission is authorized and an actual report location exists. Link all resolution destinations for an issue spanning several tools.

Set the frontmatter `status` of each resolved file (`promoted`, `dismissed` or `forwarded`) and append one
disposition line to its body so the destination is traceable:

```markdown
- **Disposition**: <destination ID, path or issue link>: <one-line summary of what was done>
```

The destination is the spec, proposal, decision, rule or playbook ID that received the item, the changed file path
for a `session` fix, or the report location for a forward. A dismissal states its reason in the same line.

## Step 5: Stale activity branches

A hygiene session also surfaces stalled work. `uv run devkit rules check -p hygiene` warns about each `plan-*` and
`dev-*` branch idle longer than `[worktree] stale_after` (it needs `gh auth status`; otherwise it notes the skip);
`uv run devkit worktree stale` prints the same as `[STALE_BRANCH: ...]` lines with the pull request state and the
resume command. List them for the user with the two ways on, resume or discard, per §4 of the `spec` skill's
`references/branches.md`, and do neither unasked: the warning never cleans anything up.

## Step 6: Rejected proposals

The same run lists each rejected proposal still in the base (`SPEC_PROPOSAL_REJECTED_PENDING`). Its cleanup is
Host work, done here once the user agrees: find the rejection commit and the user's reason
(`git log -1 --format='%H %B' -S'status: rejected' -- <proposal.md>`), write a rejection ADR under `docs/decisions/`
that references the proposal and that commit. Before deleting, follow the
[feedback retirement procedure](../../skills/spec/references/feedback-retirement.md): preserve open observations,
retire historical references with Git context, update relative links and validate current references. Keep the proposal
on collision, invalid input or an unresolved live dependency. Put preservation, the ADR and deletion in the same commit. Nothing is rewritten from
the reason; quote it.

## Completion conditions

- Every resolved item selected in Step 1 has `status` `promoted`, `dismissed` or `forwarded` and one disposition line;
  `uv run devkit spec list feedback --status open --all-namespaces -n 0` lists none of the resolved items. Report items still open because ownership or external submission is pending.
- Every promotion's draft exists and was reviewed by the user; nothing was promoted without approval.
- Every rejected proposal the run listed is cleaned up (rejection ADR and deletion in one commit) or reported as left
  for later.
- `uv run devkit rules check` exits `0`; the status updates and drafts are proposed as one commit.
