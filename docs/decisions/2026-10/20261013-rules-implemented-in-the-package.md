---
id: ADR-rules-implemented-in-the-package
title: Implement the spec rules in the package
summary: The spec rules are implemented and tested in devkit_spec.rules; the bundle deploys one thin rule file per rule that only subclasses the package's class, plus the guide devkit rules explain prints.
status: accepted
created_at: 2026-10-13
---

# [ADR-rules-implemented-in-the-package] Implement the spec rules in the package

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `ARCH-05-2-components`, `CAP-GOV-spec-rules`, `CAP-TRACE-code-entrypoints`

---

## 1. Context & Problem Statement

devkit's rule engine loads `kind = "rule"` assets from the synchronized copies of a bundle
(`.devkit/managed/<bundle>/rules/<name>/rule.py`) and instantiates the rule classes a rule file defines; the guide
beside the file is what `devkit rules explain` prints. The spec rules share a substantial library: the document index,
the Markdown scanner, namespaces and the entrypoint path contract. Where should the rule code live?

---

## 2. Decision Drivers

- Rule code is tested and versioned with the package that defines the document model.
- Every rule loads the same document index; a file is parsed once per run, however many rules read it.
- The deployed file stays stable, so a managed copy rarely changes between versions.
- devkit's engine instantiates only classes defined in the rule file.

---

## 3. Considered Options

### Option 1: Logic in `devkit_spec.rules`, thin subclass files in the bundle (Selected)
- **Overview**: each `bundle/rules/<name>/rule.py` imports the package's rule class and subclasses it; the guide
  `guide.md` sits beside it.
- **Pros**:
  - Rules are ordinary package modules, covered by the package's tests.
  - The rules share `document_index(ctx)` and the other helpers through normal imports.
- **Cons**:
  - The deployed file imports `devkit_spec`, so the package must be installed wherever `devkit rules` runs.

### Option 2: Full rule code in the deployed rule files
- **Overview**: each rule file is self-contained.
- **Pros**: no import of the package from managed files.
- **Cons**: the shared library is duplicated into every file or loaded by path; the code is tested as copies; a
  change rewrites every managed file.

### Option 3: Built-in rules in devkit
- **Overview**: ship the rules with devkit's own rules.
- **Pros**: no bundle rule files.
- **Cons**: puts the document model into devkit (`ADR-rebuild-specrig-on-devkit` keeps devkit SDD-agnostic).

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it satisfies devkit's loading contract with a one-line subclass while keeping every line of rule logic
in tested, versioned package code.

---

## 5. Consequences

- **Positive**: the rule implementation and its tests change together; the managed copy is a stable one-liner and
  the guide is the only rule text a project reads.
- **Negative / Risks**: a project, its commit gate and its CI must install devkit-spec in the environment that runs
  `devkit rules check` (`ARCH-07-deployment`).
- **Follow-ups**: rules read files only through `ctx.cache` so snapshot runs and rechecks see the right tree
  (`ARCH-08-cross-cutting`).
