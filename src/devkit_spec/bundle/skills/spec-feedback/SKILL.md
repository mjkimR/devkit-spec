---
name: spec-feedback
description: 'Record repository or spec-bundle observations: friction, inefficiency, guessed decisions and rule/playbook needs. Use for user feedback or session sweep requests (/spec-feedback). Requested sweeps ignore the collect-feedback stage switch and write no envelope.'
---

# spec-feedback: Repository & Spec Bundle Feedback Capture

One observation, one file, committed with the work. Feedback files are non-blocking: they stay `status: open` through completion and integration. Promoting, dismissing or forwarding them happens only in a separate feedback-hygiene session the user asks for; this skill only records.

---

## 1. When to record

Record when one of these is true. Agents are expected to record freely; the cost is one small file.

| kind | Record when | Later destination (hygiene) |
| :--- | :--- | :--- |
| `friction` | An instruction, skill, CLI command, spec document or rule blocked the task or forced a workaround | rule / playbook / bundle fix |
| `suggestion` | A more efficient procedure, structure or default is visible | bundle fix / proposal |
| `change-request` | A specific procedure or instruction should be changed in a specific way | bundle fix |
| `question` | An instruction was ambiguous and you decided by guess; a human should confirm | guide or skill wording |

Two scopes:

- `scope: repo`: the observation is about **this repository**: a rule it needs, a playbook it lacks, a mismatch in its own Living Spec, its own in-repository bundle.
- `scope: bundle`: the observation is about **the `spec` bundle itself**: a skill, the spec constitution (`devkit get-context spec`), an instruction, a workflow, a role contract, a shipped rule or template, or a `devkit spec` / `devkit workflow` command it drives.

Do not record: ordinary task defects (fix them), rejected non-goals, or ideas with no concrete target.

---

## 2. Procedure

1. **Finish the current step first.** Do not leave the task mid-step to write feedback. Exception: for `question`, write at least the one-line decision right after you make it so the chosen interpretation is not lost.
2. **Locate the destination** (paths and IDs are checked by `RULE-id-convention`):
   - Formal spec work (Route 2 and above): `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/feedback/<name>.md`, in the spec bundle you are working in (no date prefix on the file).
   - Work without a spec bundle (S-Lane, investigation or review): `specs/<YYYY-MM>/feedback/<YYYYMMDD>-<name>.md`, current month, today's date.
   - Create the `feedback/` directory if it does not exist. Never write under `.devkit/` or `docs/`.
   - `<name>` is kebab-case and not used by another feedback file (`devkit spec resolve FB-<name>` finds none).
3. **Write one file from the [feedback template](references/template.md).** Fill the frontmatter completely; set `id: FB-<name>` (no date) and the H1 `# [FB-<name>] <title>` (`devkit rules fix <file>` aligns both with the path). Keep the body to the section for your `kind` plus **Evidence** (quoted instruction text or a command-output excerpt). One minute of writing is the budget.
   - `target` is the most important field: the asset path or command a maintainer should open.
   - `origin: user` when the user raised the point; otherwise `agent`. A user-raised item is a flag, not a transcript: do not quote the user's words anywhere in the file.
   - **Evidence is what you observed yourself**: instruction or document text, command output, file state. The user's remark is not evidence. If the only support is "the user said so", the item is a `question`, not a `change-request`.
   - **The assessment is yours.** Write why you agree or disagree on the merits. "The user asked for it, so accepted" is deference, not a judgment, and it hides the reasoning a hygiene session needs.
   - `severity: critical` only when the next task in this repository will certainly block at the same point. Simple inconvenience is `blocked` or below.
   - `recurring: true` when you have seen this before in this repository.
   - Never paste secrets, tokens or personal data. This file is committed and shared in the PR.
4. **Return to the task.** Do not mention the file as a completion item; `devkit spec list feedback` discovers it. Do not change `status` yourself.

---

## 3. Category reference

| category | Meaning |
| :--- | :--- |
| `instruction-conflict` | Instructions conflict with each other, or with repository reality |
| `tool-error` | CLI or skill command failed, or an advisory gave wrong guidance |
| `spec-ambiguity` | spec/plan/tasks wording left the decision open |
| `context-overflow` | Required reading was too large; something was skipped or summarized |
| `missing-capability` | A needed command, field, template or rule does not exist |
| `docs-mismatch` | Guide or capability document differs from actual behavior |
| `redundant-step` | A step that does not contribute to the result; duplicate reads or checks |
| `token-cost` | Text read every session but not used |
| `other` | None of the above; state the nature in one line at the top of the body |

---

## 4. Output in the conversation

For a single observation, one line:

```markdown
> Feedback recorded: `specs/<...>/feedback/<name>.md` (<scope>/<kind>, <severity>)
```

---

## 5. Sweep (stage or user request)

For a workflow stage sweep (`collect-feedback`, or S-Lane's `report-session`) or an explicit user-requested session sweep, read the [sweep procedure](references/sweep.md). Requested sweeps ignore the stage switch (`[workflow.stages] collect-feedback = "off"`) and write no envelope. Deduplication covers the full open backlog: `devkit spec list feedback --status open --history -n 0`.
