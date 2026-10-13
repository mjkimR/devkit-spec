from __future__ import annotations

from pathlib import Path

import pytest
from conftest import Write
from rules.support import found, run

from devkit_spec.rules.document_summary import DocumentSummaryRule, foreign_letters

RULE = DocumentSummaryRule()


def _doc(document_id: str, summary: str | None = None, status: str = "active", body: str = "") -> str:
    line = f"summary: {summary}\n" if summary is not None else ""
    return f"---\nid: {document_id}\ntitle: 제목\n{line}status: {status}\n---\n{body}"


@pytest.mark.parametrize(
    "path",
    [
        "docs/capabilities/core/CAP-CORE-a.md",
        "docs/stories/core/US-a.md",
        "docs/decisions/2026-10/20261001-a.md",
        "docs/architecture/ARCH-03-context.md",
        "docs/proposals/PROP-a/proposal.md",
        "specs/2026-10/20261001-a/spec.md",
    ],
)
def test_required_kinds(workspace: Path, write: Write, path: str) -> None:
    ids = {"capabilities": "CAP-CORE-a", "stories": "US-a", "decisions": "ADR-a", "architecture": "ARCH-03-context"}
    document_id = next((v for k, v in ids.items() if f"/{k}/" in path), "PROP-a" if "proposals" in path else "SPEC-a")
    write(path, _doc(document_id))
    assert found(run(RULE, workspace)) == [(path, 1, f"{document_id} has no summary")]
    write(path, _doc(document_id, "Ranks documents for a query by meaning."))
    assert run(RULE, workspace) == []


def test_optional_kinds_and_skeletons(workspace: Path, write: Write) -> None:
    write("specs/2026-10/20261001-a/spec.md", _doc("SPEC-a", body="<!-- devkit:skeleton -->\n"))
    write("specs/2026-10/20261001-a/plan.md", _doc("PLAN-a"))
    write("docs/materials/MAT-a.md", _doc("MAT-a", "자료"))
    write("docs/proposals/PROP-a/decisions/PADR-a.md", _doc("PADR-a"))
    assert run(RULE, workspace) == []


@pytest.mark.parametrize(
    ("summary", "message"),
    [
        ('""', "summary must be a non-empty string"),
        ("[a, b]", "summary must be a non-empty string"),
        ("문서를 의미로 검색한다", "summary must be English; it contains 문서를의미"),
        ("Search with カタカナ", "summary must be English; it contains カタナ"),
    ],
)
def test_malformed_summaries(workspace: Path, write: Write, summary: str, message: str) -> None:
    write("docs/capabilities/core/CAP-CORE-a.md", _doc("CAP-CORE-a", summary))
    assert found(run(RULE, workspace)) == [("docs/capabilities/core/CAP-CORE-a.md", 4, message)]


def test_latin_accents_digits_and_symbols_are_english_enough() -> None:
    assert foreign_letters("Café 2.0 — naïve `x`: 100% (v1) → résumé") == []


def test_length_limit(workspace: Path, write: Write) -> None:
    write("docs/capabilities/core/CAP-CORE-a.md", _doc("CAP-CORE-a", "x" * 301))
    assert [m for _, _, m in found(run(RULE, workspace))] == [
        "summary has 301 characters; keep it to one or two sentences (300 at most)"
    ]


def test_history_and_targets(workspace: Path, write: Write) -> None:
    write("specs/2026-10/20261001-done/spec.md", _doc("SPEC-done", status="completed"))
    write("docs/capabilities/core/CAP-CORE-a.md", _doc("CAP-CORE-a"))
    write("docs/capabilities/core/CAP-CORE-b.md", _doc("CAP-CORE-b"))
    assert [f for f, _, _ in found(run(RULE, workspace))] == [
        "docs/capabilities/core/CAP-CORE-a.md",
        "docs/capabilities/core/CAP-CORE-b.md",
    ]
    assert [f for f, _, _ in found(run(RULE, workspace, "docs/capabilities/core/CAP-CORE-b.md"))] == [
        "docs/capabilities/core/CAP-CORE-b.md"
    ]
