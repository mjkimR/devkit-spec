---
id: FB-planning-decisions-without-worker-questions
title: "Record Planning decisions without a preceding worker question"
scope: upstream
kind: suggestion
category: missing-capability
target: "devkit workflow envelope answer"
skill: spec
agent: codex
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-16
---

# [FB-planning-decisions-without-worker-questions] Record Planning decisions without a preceding worker question

## 2. Suggestion / Change Request

- **Current Procedure**: Decisions made while shaping options can precede any worker question. The answer command
  only records answers to questions in an existing worker envelope.
- **Proposed Procedure**: Let hygiene assess a concise decision-record path for these cases, without manufacturing
  an earlier question or storing conversation text. Keep explicit approval gates separate.
- **Expected Benefit**: Decision lists remain traceable even when the direction is settled before a question round.
- **Cost & Risk**: A new generic record path belongs upstream and must not infer user decisions or duplicate gates.
- **Attempted**: Inspected CLI help and current worker-record instructions; no unsupported record was fabricated.

## Diagnostic Details

- **Reproduction**: Inspect envelope answer help and compare with a Planning direction change preceding worker questions.
- **Expected / Actual**: A place for a concise decision; actual command requires a worker envelope with questions/options.
- **Versions**: devkit-spec 4e17ead; exact installed devkit package version unknown.
- **Conditions**: Direct proposal Planning; no prior question envelope for the design decision.
- **Workarounds Attempted**: Record the proposed decision in the proposal/PADR and present it at plan-accept.
- **Related Assets**: spec/references/worker-records.md and devkit workflow envelope answer.

## Evidence

CLI help: answer records decisions on a worker envelope's questions; --answers-to must name a worker envelope
with those questions/options. The worker-record reference only documents that path. The Planning materials of
`SPEC-planning-feedback-capture` contain a proposed direction without prior worker-question answers.
