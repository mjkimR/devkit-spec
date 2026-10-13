"""``RULE-document-summary``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from pathlib import Path

import pytest
from devkit.rules import Violation
from devkit.rules.testing import check, load_rule

from devkit_spec.rules.document_summary import foreign_letters

RULE = load_rule(__file__)


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


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
def test_required_kinds(tmp_path: Path, path: str) -> None:
    ids = {"capabilities": "CAP-CORE-a", "stories": "US-a", "decisions": "ADR-a", "architecture": "ARCH-03-context"}
    document_id = next((v for k, v in ids.items() if f"/{k}/" in path), "PROP-a" if "proposals" in path else "SPEC-a")
    assert _found(check(RULE, tmp_path, {path: _doc(document_id)})) == [(path, 1, f"{document_id} has no summary")]
    assert check(RULE, tmp_path, {path: _doc(document_id, "Ranks documents for a query by meaning.")}) == []


def test_optional_kinds_and_skeletons(tmp_path: Path) -> None:
    files = {
        "specs/2026-10/20261001-a/spec.md": _doc("SPEC-a", body="<!-- devkit:skeleton -->\n"),
        "specs/2026-10/20261001-a/plan.md": _doc("PLAN-a"),
        "docs/materials/MAT-a.md": _doc("MAT-a", "자료"),
        "docs/proposals/PROP-a/decisions/PADR-a.md": _doc("PADR-a"),
    }
    assert check(RULE, tmp_path, files) == []


@pytest.mark.parametrize(
    ("summary", "message"),
    [
        ('""', "summary must be a non-empty string"),
        ("[a, b]", "summary must be a non-empty string"),
        ("문서를 의미로 검색한다", "summary must be English; it contains 문서를의미"),
        ("Search with カタカナ", "summary must be English; it contains カタナ"),
    ],
)
def test_malformed_summaries(tmp_path: Path, summary: str, message: str) -> None:
    files = {"docs/capabilities/core/CAP-CORE-a.md": _doc("CAP-CORE-a", summary)}
    assert _found(check(RULE, tmp_path, files)) == [("docs/capabilities/core/CAP-CORE-a.md", 4, message)]


def test_latin_accents_digits_and_symbols_are_english_enough() -> None:
    assert foreign_letters("Café 2.0 — naïve `x`: 100% (v1) → résumé") == []


def test_length_limit(tmp_path: Path) -> None:
    files = {"docs/capabilities/core/CAP-CORE-a.md": _doc("CAP-CORE-a", "x" * 301)}
    assert [m for _, _, m in _found(check(RULE, tmp_path, files))] == [
        "summary has 301 characters; keep it to one or two sentences (300 at most)"
    ]


def test_history_and_targets(tmp_path: Path) -> None:
    files = {
        "specs/2026-10/20261001-done/spec.md": _doc("SPEC-done", status="completed"),
        "docs/capabilities/core/CAP-CORE-a.md": _doc("CAP-CORE-a"),
        "docs/capabilities/core/CAP-CORE-b.md": _doc("CAP-CORE-b"),
    }
    assert [f for f, _, _ in _found(check(RULE, tmp_path, files))] == [
        "docs/capabilities/core/CAP-CORE-a.md",
        "docs/capabilities/core/CAP-CORE-b.md",
    ]
    assert [f for f, _, _ in _found(check(RULE, tmp_path, targets=["docs/capabilities/core/CAP-CORE-b.md"]))] == [
        "docs/capabilities/core/CAP-CORE-b.md"
    ]
