---
id: FB-gate-answers-carry-conversation-transcripts
title: Gate answers and assumptions carry conversation transcripts instead of a user flag
scope: repo
kind: change-request
category: token-cost
target: skills/spec-next/references/workflow-signals.md, skills/spec/references/worktree.md, devkit workflow answer
skill: spec
agent: claude-code
origin: user
severity: critical
recurring: false
status: promoted
created_at: 2026-10-15
---

# [FB-gate-answers-carry-conversation-transcripts] Gate answers and assumptions carry conversation transcripts instead of a user flag

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: The gate-answer guidance names `devkit workflow answer ... --action accept` and only
  mentions `--note` for a decline; it says nothing about who answered or what a note may hold. Nothing stops an
  agent from writing a dated paraphrase or quotes of the conversation into `--note`, and that is what happened for
  G1 and G2 of this spec. `references/worktree.md` asks for "the request wording" in the final change report's
  assumptions, which asks for a transcript outright.
- **Proposed Procedure**: A recorded G1/G2 answer carries `--by user` (or the host for a policy delegation) and no
  conversation content: no quotes, no dates, no paraphrase of the chat. `--note` stays for a decline reason or a
  return choice, stated as the decision, not as who said what. Assumptions name an override as "user request:
  current checkout" (the fact), never the wording. Apply this in the gate rows of `workflow-signals.md`, the gate
  paragraph of the `spec` skill, `references/worktree.md` and `references/completion.md`, mirroring the existing
  `spec-feedback` rule "a user-raised item is a flag, not a transcript".
- **Expected Benefit**: Decision records and reports stop growing with text that every later `next`, review and
  report reads but no check uses; the authority fact (`by: user`) stays verifiable. My assessment: agreed. The
  approval's authority is the user's answer itself; a transcript in the record adds neither verification nor
  traceability that `by` and `at` do not already give, and it leaks conversation into tracked files.
- **Cost & Risk**: Wording changes in four skill files, two of them near their byte budgets (`spec/SKILL.md`,
  `spec-integrate/SKILL.md`). A decline loses nothing: its reason is a decision, not a transcript.
- **Attempted**: Applied by hand to this spec's two decision records (`note` removed, `by: user` added); the
  workflow still evaluates G1 and G2 as satisfied.

## Diagnostic Details

- **Reproduction**: Answer a G1 or G2 gate in a Route 2 spec after a chat agreement, following
  `workflow-signals.md`; nothing in the guidance shapes `--note` or `--by`.
- **Expected / Actual**: Expected a user flag only; actual records held a dated, quoted summary of the chat.
- **Versions**: devkit-spec at base `79b3cb1`; devkit-agt `856f1af`.
- **Conditions**: `GATE_POLICY intent/direction policy=ask`; claude-code host.
- **Workarounds Attempted**: Edited `decisions/01-gate-intent.yaml` and `decisions/02-gate-direction.yaml` to
  `by: user` without a note; `devkit workflow next` reports `[DONE: intent direction specify]`.
- **Related Assets**: `skills/spec-next/references/workflow-signals.md`, `skills/spec/SKILL.md`,
  `skills/spec/references/worktree.md`, `skills/spec/references/completion.md`, `skills/spec-feedback/SKILL.md`,
  `devkit workflow answer` (`--note`, `--by`).

## Evidence

```text
skills/spec-next/references/workflow-signals.md:9
  After their explicit answer, record a G1 or G2 answer: `devkit workflow answer --unit <dir> --request
  gate:<gate> --action accept` (or `--action decline --note "..."`).
skills/spec/references/worktree.md:3
  record the deviation and the request wording in the final change report's assumptions.
skills/spec-feedback/SKILL.md:65
  A user-raised item is a flag, not a transcript: do not quote the user's words anywhere in the file.
devkit workflow answer --help
  --note TEXT  Free-text note, recommended on decline
  --by TEXT    Who answered (person or host)
decisions/01-gate-intent.yaml before the fix: a `note:` holding a dated summary with quoted chat lines.
```

- **Disposition**: S-Lane `f116d59` (`src/devkit_spec/bundle/AGENTS.md`, `skills/spec/SKILL.md`, `skills/spec-next/references/workflow-signals.md`, `skills/spec/references/worktree.md`, workflows, `CAP-DLV-delivery-workflows`, `ARCH-06-runtime-view`): records name the authority (`--by user`) and carry no conversation, following specrig's authority-only reporting.
