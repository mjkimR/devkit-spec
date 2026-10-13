# Glossary

The terms of devkit-spec as its documents, commands and skills use them. Where a capability or decision defines a
term's contract, the last column names it. Search synonyms for these terms live in [glossary.yaml](glossary.yaml).

## 1. Documents

| Term | Definition | Defined in |
| :--- | :--- | :--- |
| **Living Spec** | The durable, current-state contract in `docs/`: capabilities, stories, architecture and decisions. Changed statements are rewritten in place; history lives in Git, ADRs and dated materials. | `CAP-DOCS-document-model` |
| **Document** | A Markdown file under `docs/` or `specs/` whose frontmatter declares a well-formed ID (`id`, or `reconcile_id` for a reconcile record). READMEs, templates, this glossary and the development guides are not documents. | `CAP-DOCS-document-model` |
| **Document ID** | `<PREFIX>-<slug>`; the prefix names the kind (`CAP`, `US`, `ARCH`, `ADR`, `PROP`, `PADR`, `SPEC`, `PLAN`, `TASKS`, `REC`, `FB`, `MAT`). Repository-wide and unique; derived from the path, never a date or sequence number. | `CAP-DOCS-document-model` |
| **Capability** (`CAP`) | A durable functional contract of an area: business rules, interfaces, data contracts, error codes. | `CAP-DOCS-document-model` |
| **Story** (`US`) | An actor's journey with Given/When/Then acceptance scenarios; linked M:N with capabilities in both directions. | `CAP-DOCS-document-model` |
| **Architecture document** (`ARCH`) | An arc42 chapter or deep dive under `docs/architecture/`. | [architecture/README.md](architecture/README.md) |
| **Decision** (`ADR`) | An append-only architecture decision record; replaced only through `supersedes`. | [decisions/README.md](decisions/README.md) |
| **Material** (`MAT`) | Free-form, dated reference material under `docs/materials/`; exempt from most rules. | [materials/README.md](materials/README.md) |
| **Summary** | The one or two English sentences in a document's frontmatter saying what it defines; embedded by dense search. | `CAP-GOV-spec-rules` |
| **Reference** | A full ID in a relation field (`stories`, `capabilities`, `related_*`, `spec`, `plan`) or in prose as `` `ID` ``. Markdown paths to ID-bearing documents are not references and are reported. | `CAP-DOCS-document-model` |
| **Provenance** | The `proposal` field of a spec: the proposal it was handed off from; history, not a reference. | `CAP-DOCS-document-model` |
| **Traceability link** | The bidirectional `stories:` / `capabilities:` link between a capability and a story. | `CAP-GOV-spec-rules` |
| **Namespace** | A monorepo package registered in `[[tool.spec.namespaces]]` with its own Living Spec under `docs/packages/<name>/` (its docs root). Narrows browsing; IDs stay repository-wide. `global` holds everything else. | `CAP-DOCS-namespaces` |
| **Historical document** | A file of a spec bundle whose `spec.md` is `status: completed`: work history, hidden from listings unless `--history` and checked by most rules only when explicitly targeted. | `CAP-DOCS-document-lookup` |
| **Glossary expansion** | Adding a term's whole synonym cluster from `docs/glossary.yaml` to a search query that contains any of its words. | `CAP-DOCS-document-search` |
| **Pinning** | A search query equal to a document's ID, path or file name puts that document first (`score=-`). | `CAP-DOCS-document-search` |

## 2. Work Units

| Term | Definition | Defined in |
| :--- | :--- | :--- |
| **Feature spec / spec bundle** | `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` with `spec.md` (`SPEC-<slug>`), `plan.md`, `tasks.md` and, by completion, `reconcile.md`: the work unit of one change. Not to be confused with a devkit bundle. | `CAP-DLV-spec-bundles` |
| **Proposal bundle** | `docs/proposals/PROP-<slug>/` with `proposal.md`, optional `target-docs.md`, `decisions/` (PADRs) and `materials/`: incubation of uncertain work before a spec exists. | `CAP-DLV-proposal-incubation` |
| **PADR** | A preliminary decision record inside a proposal (`PADR-<slug>`); promoted to an accepted `ADR-<slug>` at handoff. | `CAP-DLV-proposal-incubation` |
| **Target docs (blueprint)** | A proposal's `target-docs.md`: the Living Spec changes planned once the proposal is accepted, with a `targets` list of files. | `CAP-DLV-proposal-incubation` |
| **Handoff** | `devkit spec proposal handoff`: turning an approved proposal into a spec bundle, promoting PADRs, moving materials, rewriting references and removing the proposal. | `CAP-DLV-proposal-incubation` |
| **Reconcile record** | A spec bundle's `reconcile.md` (`REC-<slug>`): `status` `pending` or `resolved` and `targets` (`file`, `resolution` `modified` or `waived`, `rationale`). | `CAP-GOV-spec-rules` |
| **Reconciliation** | Bringing changed behaviour, capabilities and constraints of completed work into the Living Spec before reporting completion (`spec-sync`). | `CAP-DLV-delivery-workflows` |
| **Acceptance criterion ID** | `[AC-NN]` on each acceptance criterion heading of `spec.md`, covered by tasks in `tasks.md`. | `CAP-GOV-spec-rules` |
| **Boundary** | A task's `_Boundary:_` line in `tasks.md`: the expected scope of the task and its code paths. | `CAP-TRACE-code-entrypoints` |
| **Skeleton marker** | devkit's `<!-- devkit:skeleton -->` first body line of a generated file; a workflow's `not-skeleton` check keeps the stage open until the file is written. | `CAP-DLV-spec-bundles` |
| **Feedback** (`FB`) | A recorded observation about the harness or the repository, captured with `spec-feedback`. | `CAP-HARN-agent-guidance` |

## 3. Delivery

| Term | Definition | Defined in |
| :--- | :--- | :--- |
| **Route** | The delivery path chosen by uncertainty, contract impact and risk: Route 1 (S-Lane), Route 2 (direct delivery or bugfix), Route 3 (incubated, local review), Route 4 (incubated, team review through a pull request). | `CAP-DLV-delivery-workflows` |
| **S-Lane** | Route 1: low uncertainty and low risk, done within the session with no planning files; workflow `s-lane`. | `CAP-DLV-delivery-workflows` |
| **Workflow** | A devkit workflow definition shipped by the bundle (`s-lane`, `direct-delivery`, `bugfix`, `incubated-delivery`): ordered stages with exit checks, gates and returns. | `CAP-DLV-delivery-workflows` |
| **Unit / anchor / binding** | devkit's terms: a unit is a work directory a workflow drives; its anchor is the file that binds it (`spec.md` or `proposal.md`); the binding is `workflow` plus `workflow_hash` in the anchor. | `CAP-DLV-delivery-workflows` |
| **Stage** | One step of a workflow (`intent`, `specify`, `build-verify`, ...); `devkit workflow next` names the current one and its unmet checks. | `CAP-DLV-delivery-workflows` |
| **Gate** | A stage that waits for a decision: G1 `intent`, G2 `direction`, G3 `integration`; policy `ask`, `auto` or `off` in `[workflow.approvals]`. | `ADR-approval-gates-intent-direction-integration` |
| **Exception stage** (E) | The out-of-band stage every workflow has for a retry cap, tool failure or unresolved conflict; no gate. | `CAP-DLV-delivery-workflows` |
| **Handoff workflow** | The workflow a spec follows after handoff, named in a proposal's `handoff_workflow` (default `direct-delivery`). | `ADR-handoff-workflow-key` |
| **Envelope** | devkit's YAML record of a stage result (`specs/.../envelopes/<kind>-<NN>.yaml`): `status`, findings, checks, diff scope. Written with `devkit workflow envelope new`. | `CAP-DLV-delivery-workflows` |
| **Final change report** | The `final-report` envelope before G3, carrying the tests, build and lint evidence. | `CAP-DLV-delivery-workflows` |
| **Role contract / support role** | A host-neutral subagent definition (`challenger`, `reconciler`, `reviewer`, `scout`) that a stage may delegate to; projected per agent host; always optional. | `CAP-HARN-agent-guidance` |
| **Developer** | The main agent session that runs a workflow and records envelopes, as opposed to a delegated support role. | `CAP-DLV-delivery-workflows` |
| **Project policy** | The effective gate, stage and Git policy printed by `devkit spec policy`. | `CAP-DLV-project-policy` |

## 4. Collaboration and Traceability

| Term | Definition | Defined in |
| :--- | :--- | :--- |
| **Entrypoint** | A literal workspace-relative file or directory a capability or story declares in `entrypoints` as code that implements it. | `CAP-TRACE-code-entrypoints` |
| **Work scope** | The documents and code paths a task declares or touches: a document side, a code side (declared, candidate, observed) and unresolved inputs. | `CAP-COLL-work-scope-registry` |
| **Scope registry** | One JSON record per running task under `<git-common-dir>/devkit-spec-scope/<namespace>/`, shared by every worktree, with an append-only journal. Detection only; never exclusive ownership. | `CAP-COLL-work-scope-registry` |
| **Owner token** | The secret a registration returns once and saves in the worktree's Git directory; the record stores only its hash. | `CAP-COLL-work-scope-registry` |
| **Overlap** | Two scope sets naming the same document path, or code paths where one equals or contains the other. Evidence for scheduling, not a proof of conflict. | `CAP-COLL-work-scope-registry` |
| **Task worktree** | A linked Git worktree per Route 2, Route 3 or bugfix task (`devkit worktree start <slug>`) under `[tool.spec] worktree = true`. | `CAP-DLV-project-policy` |

## 5. Packaging and Harness

| Term | Definition | Defined in |
| :--- | :--- | :--- |
| **devkit bundle (asset package)** | devkit's unit of distributable agent assets, declared in `bundle.toml`. devkit-spec ships the bundle named `spec`. Not to be confused with a spec bundle (a work unit). | `ARCH-05-1-containers` |
| **Preset** | A named asset selection of a bundle: `core` (default, `auto_select`) and `docs-skeleton` (opt-in). | `ADR-docs-skeleton-is-opt-in` |
| **Constitution** | The bundle's `AGENTS.md`, returned by `devkit get-context spec`: the rules of spec-driven delivery an agent reads once per context. | `CAP-HARN-agent-guidance` |
| **Instruction** | A judgment and policy text with a read condition (`contract-authoring`, `living-spec-writing`). | `CAP-HARN-agent-guidance` |
| **Skill** | A procedure an agent invokes by name (`spec`, `spec-next`, `spec-specify`, ...). | `ADR-skills-named-spec` |
| **Playbook** | An occasional procedure found through `devkit playbook search` (`brownfield-adoption`, `feedback-hygiene`). | `CAP-HARN-agent-guidance` |
| **Guidance pointer** | The `spec-pointer` line devkit writes into the `DEVKIT:START/END` block of `AGENTS.md`. | `CAP-HARN-agent-guidance` |
| **Managed files** | The synchronized copies under `.devkit/managed/`; never edited by hand. | `ARCH-07-deployment` |
| **Receipt** | `.devkit/installation.json`: what `devkit sync` deployed. | `ARCH-07-deployment` |
| **Command plugin** | A command group added to `devkit` through the `devkit.commands` entry point; `devkit spec` is one. | `CAP-HARN-command-mount` |
| **Sentinel** | A one-line `[KIND: value key=value ...]` result line on stdout. | `ARCH-08-cross-cutting` |
| **Advisory** | An Agent Advisory Protocol block on stderr (`[ERROR]`, `[WARN]`, `[NOTICE]`) with a stable code and an `[ACTION]` directive. | `ARCH-08-cross-cutting` |
| **Snapshot run** | A rule run on a Git snapshot: `devkit rules check --staged` (the commit gate) or `--ci --base <ref>`; rules see the snapshot through `ctx.cache` and the diff through `ctx.snapshot`. | `ARCH-08-cross-cutting` |
| **Commit gate** | devkit's Git hooks; its `verify-commands` gate runs `devkit rules check --staged` before a commit. | `ARCH-06-runtime-view` |
| **specrig** | The retired Go predecessor of devkit-spec. | [specrig port map](development/specrig-port-map.md) |
