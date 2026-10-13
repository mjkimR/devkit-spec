from __future__ import annotations

import pytest
from devkit.core import FrontmatterError

from devkit_spec.documents import Kind, is_id, kind_of, parse_document


def _refs(text: str) -> list[tuple[str, str, int, bool]]:
    document = parse_document("docs/x.md", text)
    assert document is not None
    return [(ref.target, ref.field, ref.line, ref.bracket) for ref in document.references]


def _doc(body: str, header: str = "id: CAP-CORE-x\nstatus: active\n") -> str:
    return f"---\n{header}---\n{body}"


@pytest.mark.parametrize(
    ("value", "kind"),
    [("CAP-CORE-x", Kind.CAPABILITY), ("US-a_b-c", Kind.STORY), ("REC-x", Kind.RECONCILE), ("MAT-9", Kind.MATERIAL)],
)
def test_ids_name_their_kind(value: str, kind: Kind) -> None:
    assert is_id(value) and kind_of(value) is kind


@pytest.mark.parametrize("value", ["CAP-", "cap-x", "CAP--x", "XYZ-x", "CAP-x y", " CAP-x"])
def test_malformed_ids(value: str) -> None:
    assert not is_id(value) and kind_of(value) is None


def test_identity_and_fields() -> None:
    document = parse_document("docs/c.md", _doc("", "id: CAP-CORE-x\ntitle: X\nstatus: active\narea: core\n"))
    assert document is not None
    assert (document.id, document.kind, document.title, document.status, document.area) == (
        "CAP-CORE-x",
        Kind.CAPABILITY,
        "X",
        "active",
        "core",
    )


def test_a_reconcile_file_is_identified_by_reconcile_id() -> None:
    document = parse_document("specs/m/b/reconcile.md", "---\nreconcile_id: REC-b\n---\n")
    assert document is not None and document.id == "REC-b" and document.kind is Kind.RECONCILE


@pytest.mark.parametrize("text", ["no frontmatter\n", "---\ntitle: x\n---\n", "---\nid: not-an-id\n---\n"])
def test_files_without_a_well_formed_id_are_not_documents(text: str) -> None:
    assert parse_document("docs/x.md", text) is None


@pytest.mark.parametrize("text", ["---\nid: [CAP-x]\n---\n", "---\nid: CAP-x\nstatus: 3\n---\n", "---\nid: CAP-x\n"])
def test_malformed_frontmatter_raises(text: str) -> None:
    with pytest.raises(FrontmatterError):
        parse_document("docs/x.md", text)


def test_frontmatter_references_keep_their_positions() -> None:
    text = _doc("", "id: CAP-CORE-x\nstories:\n  - US-a\n  - 'US-b'\nspec: SPEC-s\nproposal: PROP-p\n")
    document = parse_document("docs/x.md", text)
    assert document is not None
    assert [(r.target, r.field, r.line, r.column) for r in document.references] == [
        ("US-a", "stories", 4, 5),
        ("US-b", "stories", 5, 5),
        ("SPEC-s", "spec", 6, 7),
    ]
    assert [text[r.start : r.end] for r in document.references] == ["US-a", "'US-b'", "SPEC-s"]
    assert [(r.target, r.field) for r in document.provenance] == [("PROP-p", "proposal")]


def test_malformed_reference_fields_are_issues() -> None:
    document = parse_document(
        "docs/x.md", _doc("", "id: CAP-CORE-x\nstories: US-a\nspec: [SPEC-s]\ncapabilities: [1]\n")
    )
    assert document is not None and document.references == []
    assert [(issue.line, issue.message) for issue in document.issues] == [
        (3, "stories must be a list of IDs"),
        (5, "capabilities must contain string IDs"),
        (4, "spec must be one ID"),
    ]


def test_body_references() -> None:
    body = "# [CAP-CORE-x] Title\n\nSee `US-a` and [ADR-b], not `US-a b` or `x US-c`.\n"
    assert _refs(_doc(body)) == [("US-a", "body", 7, False), ("ADR-b", "body", 7, True)]


def test_body_reference_positions() -> None:
    text = _doc("intro\n  uses `US-a` here\n")
    document = parse_document("docs/x.md", text)
    assert document is not None
    (ref,) = document.references
    assert (ref.line, ref.column, text[ref.start : ref.end]) == (6, 9, "US-a")


@pytest.mark.parametrize(
    "body",
    [
        "```\n`US-a`\n```\n",
        "~~~~md\n[US-a]\n~~~\n~~~~\n",
        "    `US-a` indented code\n",
        "<!-- `US-a`\n[US-b] -->\n",
        "``code `US-a` code``\n",
        "~~`US-a`~~\n",
        "[US-a](path.md) ![US-b] [US-c][ref] [US-d]: x\n",
        "\\[US-a\\] \\`US-b\\`\n",
        "`code\n`US-a` [US-b]\nend` after\n",
        "~~gone\n`US-a`~~\n",
    ],
)
def test_non_prose_is_not_referenced(body: str) -> None:
    assert _refs(_doc(body)) == []


def test_a_heading_does_not_reference_its_own_document() -> None:
    assert _refs(_doc("# `CAP-CORE-x` and `US-a`\n## `CAP-CORE-x`\n")) == [
        ("US-a", "body", 5, False),
        ("CAP-CORE-x", "body", 6, False),
    ]


def test_crlf_line_endings() -> None:
    text = "---\r\nid: CAP-CORE-x\r\nstories:\r\n  - US-a\r\n---\r\nsee `US-b`\r\n"
    assert _refs(text) == [("US-a", "stories", 4, False), ("US-b", "body", 6, False)]


def test_a_span_ends_with_its_paragraph() -> None:
    assert _refs(_doc("`open\n\n`US-a`\n")) == [("US-a", "body", 7, False)]
    assert _refs(_doc("``open `US-a`\n~~~\n")) == [("US-a", "body", 5, False)]


def test_text_after_a_multiline_span_stays_visible() -> None:
    assert _refs(_doc("`a\nb` `US-a`\n")) == [("US-a", "body", 6, False)]


@pytest.mark.parametrize(
    "body",
    [
        "- item\n    `US-a` continued\n",
        "- item\n\n    `US-a` a paragraph of the item\n",
        "1. item\n    - nested `US-a`\n",
        "text\n    `US-a` continues the paragraph\n",
    ],
)
def test_indented_prose_is_referenced(body: str) -> None:
    assert [target for target, *_ in _refs(_doc(body))] == ["US-a"]


@pytest.mark.parametrize("body", ["    `US-a`\n", "text\n\n    `US-a`\n", "text\n\n    code\n\n    `US-a`\n"])
def test_indented_code_is_not(body: str) -> None:
    assert _refs(_doc(body)) == []
