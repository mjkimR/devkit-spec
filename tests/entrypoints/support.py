from __future__ import annotations

from pathlib import Path

from conftest import Write

from devkit_spec.documents import Document, DocumentIndex

BUNDLE = "specs/2026-10/20261001-one"
CAP = "docs/capabilities/x/CAP-X-one.md"
STORY = "docs/stories/x/US-two.md"
CAP_TEXT = "---\nid: CAP-X-one\ntitle: One\nstatus: active\nentrypoints:\n  - src/declared/\ncreated_at: 2026-10-01\n---\n\n# body\n"
STORY_TEXT = "---\nid: US-two\nstatus: active\n---\n"
TASKS = "\n".join(
    [
        "---",
        "id: TASKS-one",
        "---",
        "",
        "- [x] **Task 1**: engine",
        "  - **_Boundary**: `src/pkg/`, `src/pkg/sub/c.go`, `src/declared/a.go` (note)",
        "  - _Requirements: AC-01_",
        "- [ ] **Task 2**: docs",
        "  - _Boundary: docs/capabilities/, N/A, src/**/*.go, src/missing.go",
        "  - _Requirements: AC-02_",
        "```",
        "- [ ] fenced task",
        "  - _Boundary: src/fenced",
        "```",
        "",
    ]
)
RECONCILE = "\n".join(
    [
        "---",
        "reconcile_id: REC-one",
        "status: resolved",
        "targets:",
        f"  - file: {CAP}",
        "    resolution: modified",
        f"  - file: {STORY}",
        "    resolution: modified",
        "  - file: docs/decisions/ADR-x.md",
        "    resolution: modified",
        "  - file: docs/capabilities/x/CAP-X-gone.md",
        "    resolution: waived",
        "    rationale: no longer relevant to this change",
        "---",
        "",
        "# Reconciliation",
        "",
    ]
)


def fixture(write: Write) -> None:
    """Derivation fixture: two bearing documents, one decision, a waived target and mixed boundaries."""
    write(CAP, CAP_TEXT)
    write(STORY, STORY_TEXT)
    write("docs/decisions/ADR-x.md", "---\nid: ADR-x\n---\n")
    write("src/declared/a.go", "package a\n")
    write("src/pkg/b.go", "package b\n")
    write("src/pkg/sub/c.go", "package c\n")
    write(f"{BUNDLE}/spec.md", "---\nid: SPEC-one\nstatus: completed\n---\n")
    write(f"{BUNDLE}/tasks.md", TASKS)
    write(f"{BUNDLE}/reconcile.md", RECONCILE)


def documents(root: Path) -> dict[str, Document]:
    return {document.path: document for document in DocumentIndex.load(root).documents}
