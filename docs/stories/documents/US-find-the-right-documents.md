---
id: US-find-the-right-documents
title: Find the Right Documents
summary: An AI coding agent finds the Living Spec documents relevant to a task, by exact ID, by reference, by owned code path or by meaning, within the right monorepo package, before it changes anything.
area: documents
actor: AI coding agent
status: active
capabilities:
  - CAP-DOCS-document-model
  - CAP-DOCS-document-lookup
  - CAP-DOCS-document-search
  - CAP-DOCS-namespaces
created_at: 2026-10-13
---

# [US-find-the-right-documents] Find the Right Documents

## 1. User Story Narrative

- **As a**: AI coding agent starting or continuing development work in a project that uses the `spec` bundle
- **I want to**: find the capabilities, stories, decisions and specs that govern the code and the intent in front of
  me, and follow their references, without reading the whole `docs/` tree
- **So that**: I change code against the current contract, cite documents by their exact IDs and spend my context
  budget only on documents that matter

---

## 2. Background & Context

The Living Spec can hold hundreds of documents, written in any language, across several packages of a monorepo. An
agent usually starts from one of four handles: an ID quoted in a task or a review, a code path it is about to change,
a free-text description of the intent, or a document it already has open. Every handle has a deterministic command
with one-line output: `devkit spec resolve`, `devkit spec list --file`, `devkit spec search` and `devkit spec refs`.
Completed spec bundles are work history and stay out of the way unless asked for.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: Resolve a cited ID and follow its references

- **Given**: a review comment cites a capability by its full ID
- **When**: the agent runs `devkit spec resolve <ID>` and then `devkit spec refs <ID> --direction in`
- **Then**: it receives one `[DOCUMENT: ...]` line with the workspace-relative path, then one `[REF: ...]` line per
  document that references the capability, ending with `[PAGE: ...]`, and exits `0`

### Scenario 2: Find documents by meaning

- **Given**: the agent knows only the intent ("keep references between documents valid"), and the documents carry
  English summaries while their titles and bodies are in another language
- **When**: it runs `devkit spec search "<intent>"`
- **Then**: the documents whose ID and summary match the intent rank among the top hits as `[HIT: ...]` lines, and an
  exact ID, path or file name in the query is pinned first with `score=-`

### Scenario 3: Find the documents that own a code path

- **Given**: the agent is about to change `src/<package>/engine.py`, and a capability declares `src/<package>/` in
  its `entrypoints`
- **When**: it runs `devkit spec list capability --file src/<package>/engine.py`
- **Then**: the capability is listed, even when the file has since been deleted

### Scenario 4: Stay within a package without losing cross-package identity

- **Given**: a monorepo registers the namespaces `api` and `web`, and the agent works under `services/api`
- **When**: it runs `devkit spec list` and then `devkit spec resolve` on an ID of the `web` package
- **Then**: `list` shows the `api` and global documents only, each line with `namespace=`, while `resolve` finds the
  `web` document, because IDs are repository-wide; an unknown `--namespace` fails with `ARGUMENT_INVALID`
