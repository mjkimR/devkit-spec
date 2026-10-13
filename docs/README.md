# devkit-spec Documentation

This directory is devkit-spec's own Living Spec, written with the `spec` bundle it ships: the current contract of
the package, kept in place as it changes. History lives in Git, the ADRs and dated materials, never in these
documents. Every ID-bearing document is referred to by its full ID; `devkit spec resolve <ID>` prints its path.

## 1. Where to Start

| Question | Read |
| :--- | :--- |
| What is devkit-spec, what does it leave to devkit? | `ARCH-01-introduction-and-goals`, `ARCH-03-context` |
| What ships in the wheel and how does a project receive it? | `ARCH-05-1-containers`, `ARCH-07-deployment` |
| Which module does what? | `ARCH-05-2-components` |
| How do commands, the commit gate and worktrees interact at run time? | `ARCH-06-runtime-view` |
| Output contract, codes, configuration, rule targeting | `ARCH-08-cross-cutting` |
| Why is it built this way? | the decisions: `devkit spec list decision` |
| Where did each specrig component go? | `MAT-specrig-port-map` |
| What does a term mean? | [glossary.md](glossary.md) |
| How do I build, test and change devkit-spec? | [development/](development/setup.md) |

## 2. Capabilities and Stories

Capabilities (`docs/capabilities/<area>/`) hold the contracts: business rules, commands, options, output sentinels,
JSON keys, configuration keys and error codes. Stories (`docs/stories/<area>/`) describe the actor journeys they
serve; both link each other by ID.

| Area | Capabilities | Stories |
| :--- | :--- | :--- |
| `documents` | `CAP-DOCS-document-model`, `CAP-DOCS-document-lookup`, `CAP-DOCS-document-search`, `CAP-DOCS-namespaces` | `US-find-the-right-documents` |
| `governance` | `CAP-GOV-spec-rules` | `US-keep-the-living-spec-consistent` |
| `traceability` | `CAP-TRACE-code-entrypoints` | |
| `delivery` | `CAP-DLV-delivery-workflows`, `CAP-DLV-spec-bundles`, `CAP-DLV-proposal-incubation`, `CAP-DLV-project-policy` | `US-route-development-intent`, `US-incubate-and-hand-off-a-proposal` |
| `collaboration` | `CAP-COLL-work-scope-registry` | `US-run-parallel-work-safely` |
| `harness` | `CAP-HARN-agent-guidance`, `CAP-HARN-command-mount` | `US-adopt-in-an-existing-repository` |

Find documents by meaning with `devkit spec search "<question>"`, browse with
`devkit spec list --all-namespaces`, and follow references with `devkit spec refs <ID> --direction out|in`.

## 3. Directory Map

| Directory | Holds |
| :--- | :--- |
| `architecture/` | arc42 chapters with C4 diagrams ([conventions](architecture/README.md)) |
| `capabilities/<area>/` | `CAP-<AREA>-<slug>` contracts |
| `stories/<area>/` | `US-<slug>` journeys with Given/When/Then scenarios |
| `decisions/<YYYY-MM>/` | `ADR-<slug>` records, append-only ([conventions](decisions/README.md)) |
| `proposals/` | `PROP-<slug>` bundles incubating uncertain work ([conventions](proposals/README.md)) |
| `materials/<YYYY-MM>/` | Dated reference material, free-form ([conventions](materials/README.md)) |
| `development/` | Contributor guides without IDs: setup, workflow, CI |
| `glossary.md`, `glossary.yaml` | Terms; the search synonyms of `devkit spec search` |

Feature specs live in `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` at the repository root.

## 4. Writing Here

- Development work starts with `/spec <intent>` after `uv run --no-active devkit get-context spec`; the constitution
  routes it and names the instructions to read (`contract-authoring`, `living-spec-writing`).
- New documents start from `.devkit/managed/spec/templates/{capability,story,decision,proposal}.md`.
- Every capability, story, decision, architecture document, proposal and spec carries an English `summary`
  (`RULE-document-summary`); `devkit rules check` runs every spec rule on this tree.
- Every `SPEC_` code defined under `src/` is documented with its level and condition in its owning capability
  (`tests/test_documented_codes.py`).
