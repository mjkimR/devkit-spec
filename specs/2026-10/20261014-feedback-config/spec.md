---
id: SPEC-feedback-config
title: Repository-first feedback configuration
summary: "Configure repository-first feedback capture, upstream coverage and detail, and expose effective feedback policy."
status: completed
created: 2026-10-14
related_capabilities:
  - CAP-DLV-project-policy
  - CAP-HARN-agent-guidance
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-feedback-config] Repository-first feedback configuration

## 1. Problem Statement & Motivation

Repository-owned rules, skills, instructions, workflows and tools are the primary feedback targets. Projects may
also collect upstream observations without asking users to identify ownership. Capture and detail need configuration.

## 2. User Stories

- As a maintainer, I want one feedback backlog for repository assets and optional upstream observations, with
  ownership and the resolution destination determined during hygiene.

## 3. Non-Goals

- **Scope Excluded**: external issue submission, feedback storage path changes, search configuration and general
  feedback transport in devkit.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] Defaults and validation

- **Given** absent or configured tool.spec.feedback settings
- **When** config is loaded or a commented template rendered
- **Then** defaults are observed/repo/standard/contextual for capture/coverage/detail/reminder; invalid types,
  values or unknown keys raise SPEC_CONFIG_INVALID, and policy commands exit 2.

### [AC-02] Effective feedback policy

- **Given** valid feedback configuration
- **When** devkit spec policy runs in text or JSON mode
- **Then** text includes one FEEDBACK_POLICY sentinel and JSON includes all four effective values under feedback.

### [AC-03] Repository-first recording and explicit requests

- **Given** repository-owned or upstream observations
- **When** recording or sweeping feedback
- **Then** agents use repo/upstream/unknown ownership, never ask users to classify tools, collect repository rules,
  skills, instructions and tools by default, and extend to upstream under repo-and-upstream. Explicit requests
  override autonomous capture, coverage and stage restrictions without creating sweep envelopes.

### [AC-04] Detail, reminders and project setup

- **Given** detailed capture or requested-only capture
- **When** recording or performing a stage sweep
- **Then** detailed records include reproduction, expectations, actual results, versions, conditions and workarounds
  with unknown for missing facts; requested-only skips autonomous observations with sweep evidence. Reminders honor
  off/contextual. This repository configures observed/repo-and-upstream/detailed/contextual.
