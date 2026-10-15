---
name: spec-feedback
description: 'Record repository-owned tool and asset observations, optionally including upstream tools: friction, inefficiency, guessed decisions and rule/playbook needs. Use for user feedback or session sweep requests (/spec-feedback). Requested sweeps ignore the collect-feedback stage switch and write no envelope.'
---

# spec-feedback: Repository-First Feedback Capture

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

Repository-owned assets are the base targets: rules, skills, instructions, playbooks, workflows, role contracts,
script/CLI tools, templates, Living Spec documents and in-repository bundles, including project overrides.

Read `devkit spec policy` before recording. Its `FEEDBACK_POLICY` line (JSON `feedback`) controls autonomous capture:

- `capture=observed`: record concrete observations as they arise and during enabled stage sweeps.
- `capture=requested-only`: record only when the user explicitly requests feedback; stage sweeps produce policy-skip evidence.
- `coverage=repo`: collect repository-owned assets by default.
- `coverage=repo-and-upstream`: also collect upstream tools used in the work, including devkit, devkit-spec and other tools.
- `detail=brief|standard|detailed`: follow the detail contract in the [template](references/template.md).
- `reminder=contextual|off`: governs optional reminders from the router, not mandatory stage execution.

Explicit requests to record an observation or sweep the session override autonomous capture, coverage and stage
restrictions. They still follow evidence, detail, privacy and hygiene constraints. Never ask the user to classify a
tool, choose its maintainer or supply frontmatter; the agent fills these fields from observations.

Ownership scopes:

- `scope: repo`: this repository owns the affected asset. A spec skill developed in devkit-spec is `repo`; an
  installed copy used by another repository is `upstream`. A project override is `repo`.
- `scope: upstream`: an installed or external tool or bundle owns the affected asset. devkit and devkit-spec can
  both be recorded in the same backlog without separate intake procedures.
- `scope: unknown`: ownership is uncertain or the issue spans repository and upstream assets. Record the observed
  target and defer ownership to hygiene; uncertainty must not block relevant feedback capture.

`target` identifies the observed command or asset, not the presumed resolution owner. Hygiene determines where
it is fixed and may link one observation to several destinations.

Do not record: ordinary task defects (fix them), rejected non-goals, or ideas with no concrete target.

---

## 2. Procedure

1. **Finish the current step first.** Do not leave the task mid-step to write feedback. Exception: for `question`, write at least the one-line decision right after you make it so the chosen interpretation is not lost.
2. **Locate the destination** (paths and IDs are checked by `RULE-id-convention`):
   - Formal spec work (Route 2 and above): `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/feedback/<name>.md`, in the spec bundle you are working in (no date prefix on the file).
   - Work without a spec bundle (S-Lane, investigation or review): `specs/<YYYY-MM>/feedback/<YYYYMMDD>-<name>.md`, current month, today's date.
   - Create the `feedback/` directory if it does not exist. Never write under `.devkit/` or `docs/`.
   - `<name>` is kebab-case and not used by another feedback file (`devkit spec resolve FB-<name>` finds none).
3. **Write one file from the [feedback template](references/template.md).** Fill the frontmatter completely; set `id: FB-<name>` (no date) and the H1 `# [FB-<name>] <title>` (`devkit rules fix <file>` aligns both with the path). Keep the body to the section for your `kind` plus **Evidence** (quoted instruction text or a command-output excerpt). Use the configured detail level; brief and standard records should take about one minute. Detailed records prioritize useful evidence over that budget.
   - `target` is the most important field: the asset path or command a maintainer should open.
   - `origin: user` when the user raised the point; otherwise `agent`. A user-raised item is a flag, not a transcript: do not quote the user's words anywhere in the file.
   - **Evidence is what you observed yourself**: instruction or document text, command output, file state. Do not paste raw command output verbatim; summarize or excerpt the relevant lines, and redact local absolute paths or identifiers with placeholders (e.g. `<repo>`, `<worktree>`). The user's remark is not evidence. If the only support is "the user said so", the item is a `question`, not a `change-request`.
   - **The assessment is yours.** Write why you agree or disagree on the merits. "The user asked for it, so accepted" is deference, not a judgment, and it hides the reasoning a hygiene session needs.
   - `severity: critical` only when the next task in this repository will certainly block at the same point. Simple inconvenience is `blocked` or below.
   - `recurring: true` when you have seen this before in this repository.
   - Never paste secrets, tokens or personal data (including local usernames and machine absolute paths). This file is committed and shared in the PR.
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

For a workflow stage sweep (`collect-feedback`, or S-Lane's `report-session`) or an explicit user-requested session sweep, read the [sweep procedure](references/sweep.md). Requested sweeps override autonomous capture and coverage limits and ignore the stage switch (`[workflow.stages] collect-feedback = "off"`) and write no envelope. Deduplication covers the full open backlog: `devkit spec list feedback --status open --all-namespaces -n 0`.
