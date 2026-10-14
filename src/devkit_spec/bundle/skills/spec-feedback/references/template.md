# Feedback template

Read this when writing a feedback file (step 3 of the `spec-feedback` recording procedure). Copy the block below (inside the four-backtick fence) into the destination file, replace every `<...>` placeholder, keep one of sections 1 and 2, and delete the comment.

````markdown
---
id: FB-<name>
title: <title>
scope: repo                         # repo | upstream | unknown; ownership of the observed asset, filled by the agent
kind: friction                      # friction | suggestion | change-request | question
category: other                     # instruction-conflict | tool-error | spec-ambiguity | context-overflow | missing-capability | docs-mismatch | redundant-step | token-cost | other
target: <asset path or command>     # e.g. the spec-specify skill, devkit spec list, CAP-<AREA>-<slug>
skill: none                         # active skill when observed (spec, spec-specify, spec-review, ...) or none
agent: <claude-code | codex | antigravity | ...>
origin: agent                       # agent | user  (user = raised by the user; set the flag without quoting the user)
severity: workaround                # critical | blocked | workaround | noise
recurring: false                    # true if observed 2+ times
status: open                        # open | promoted | dismissed | forwarded  (changed only by a feedback-hygiene session)
created_at: <YYYY-MM-DD>
---

# [FB-<name>] <title>

<!--
One incident per file. Use the configured detail level; brief/standard should take about 1 minute.
If kind is friction / question, fill out Section 1 and remove Section 2.
If kind is suggestion / change-request, fill out Section 2 and remove Section 1.
Evidence must include only direct observations: instructions, doc excerpts, command outputs, file states. Do not quote user utterances.
Judgments must reflect the agent's own assessment.
Do not include secrets, tokens, or PII.
If category is other, specify the nature in the first line below.
-->

## 1. Friction / Question (friction, question)

- **Context**: What was being done
- **Expectation**: What the documentation/instructions promised
- **Actual**: What actually happened
- **Workaround (or Interpretation Chosen)**: How it was bypassed or interpreted
- **Suggestion**: What to fix so future runs avoid getting blocked here

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: How it is currently done
- **Proposed Procedure**: How it should change
- **Expected Benefit**: Reduced steps, tokens, or decision fatigue
- **Cost & Risk**: What could break if changed
- **Attempted**: Tested in this session vs hypothesis

## Evidence

```text
<Directly observed instruction/doc excerpts, command output, or file state. Do not include user utterances.>
```
````

## Configured detail

Read `FEEDBACK_POLICY detail` from `devkit spec policy`. All levels keep complete frontmatter, one observation per
file, direct Evidence, the agent's own assessment and no secrets, tokens or personal data.

- **brief**: retain the applicable section with context/current procedure, actual observation or proposed change,
  a short assessment and Evidence. Omit unused template bullets.
- **standard**: fill the applicable kind-specific section and Evidence as shown above.
- **detailed**: use standard detail and add the following section before Evidence. Fill missing facts with
  `unknown`; do not fabricate output, version numbers or reproduction results. Use `not applicable` when a
  field does not apply. Do not rerun risky or expensive commands just to complete the record.

```markdown
## Diagnostic Details

- **Reproduction**: Observed steps and command, or unknown when not reproduced.
- **Expected / Actual**: Expected behavior and the directly observed result.
- **Versions**: Known tool/package versions or revision; unknown for unavailable versions.
- **Conditions**: Relevant repository, configuration, host and occurrence conditions, without personal data.
- **Workarounds Attempted**: Attempts and their outcomes, or not attempted.
- **Related Assets**: Observed command, source paths, instructions or document IDs.
```
