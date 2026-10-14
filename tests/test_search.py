from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from conftest import Write
from devkit.cli import cli as devkit_cli
from devkit.search import SearchMode

from devkit_spec.documents import DocumentIndex, Kind
from devkit_spec.errors import GlossaryInvalidError
from devkit_spec.search import expand_query, load_glossary, search_documents


def _doc(document_id: str, title: str, body: str = "", status: str = "active") -> str:
    return f"---\nid: {document_id}\ntitle: {title}\nstatus: {status}\n---\n{body}"


@pytest.fixture
def docs(workspace: Path, write: Write) -> Path:
    write("docs/capabilities/core/CAP-CORE-search.md", _doc("CAP-CORE-search", "Document search", "Ranks documents.\n"))
    write("docs/stories/core/US-find-docs.md", _doc("US-find-docs", "Find documents", "As an agent I look up specs.\n"))
    write("docs/decisions/2026-10/20261001-cache.md", _doc("ADR-cache", "Cache derived data", "Vectors are cached.\n"))
    write("specs/2026-10/20261001-done/spec.md", _doc("SPEC-done", "Old search work", status="completed"))
    return workspace


def _ids(root: Path, query: str, **options: object) -> list[str]:
    result = search_documents(DocumentIndex.load(root), query, mode=SearchMode.LEXICAL, **options)  # type: ignore[arg-type]
    return [hit.document.id for hit in result.hits]


def test_lexical_ranking_uses_metadata_and_body(docs: Path) -> None:
    assert _ids(docs, "search documents") == ["CAP-CORE-search", "US-find-docs"]
    assert _ids(docs, "vectors") == ["ADR-cache"]


def test_exact_id_path_and_file_name_are_pinned_first(docs: Path) -> None:
    for query in ("ADR-cache", "adr-cache", "docs/decisions/2026-10/20261001-cache.md", "20261001-cache.md"):
        result = search_documents(DocumentIndex.load(docs), query, mode=SearchMode.LEXICAL)
        assert result.hits[0].document.id == "ADR-cache" and result.hits[0].pinned and result.hits[0].score is None


def test_kinds_history_and_limit(docs: Path) -> None:
    assert _ids(docs, "search", kinds={Kind.STORY, Kind.CAPABILITY}) == ["CAP-CORE-search"]
    assert "SPEC-done" not in _ids(docs, "search work")
    assert "SPEC-done" in _ids(docs, "search work", history=True)


def test_feedback_of_a_completed_bundle_is_found_without_history(docs: Path, write: Write) -> None:
    # AC-02: feedback stays current after its bundle completes.
    write("specs/2026-10/20261001-done/feedback/slow.md", _doc("FB-slow", "Zanzibar sync blocks", status="open"))
    assert "FB-slow" in _ids(docs, "zanzibar")
    assert len(_ids(docs, "documents search", limit=1)) == 1


def test_glossary_expands_the_query(docs: Path, write: Write) -> None:
    write("docs/glossary.yaml", "terms:\n  - primary: cache\n    synonyms: [캐시, derived data]\n")
    glossary = load_glossary(docs)
    assert expand_query("캐시 정책", glossary) == "캐시 정책 cache derived data"
    assert expand_query("derived  DATA", glossary) == "derived  DATA cache 캐시"
    assert expand_query("data derived", glossary) == "data derived"  # a multi-word term matches in order
    assert _ids(docs, "캐시") == ["ADR-cache"]


def test_glossary_terms_match_as_tokenized_words(docs: Path, write: Write) -> None:
    write("docs/glossary.yaml", "terms:\n  - primary: work-scope\n    synonyms: [café, scope_registry]\n")
    glossary = load_glossary(docs)
    assert expand_query("Work Scope overlap", glossary) == "Work Scope overlap café scope_registry"
    assert expand_query("cafe", glossary) == "cafe work-scope scope_registry"
    assert expand_query("scope.registry", glossary) == "scope.registry work-scope café"
    assert expand_query("workscope", glossary) == "workscope"


def test_glossary_terms_with_the_same_words_merge_their_clusters(docs: Path, write: Write) -> None:
    write(
        "docs/glossary.yaml",
        "terms:\n  - primary: C++\n    synonyms: [cpp]\n  - primary: C#\n    synonyms: [csharp, cpp]\n",
    )
    glossary = load_glossary(docs)
    assert glossary[("c",)] == ["C++", "cpp", "C#", "csharp"]
    assert glossary[("cpp",)] == ["C++", "cpp", "C#", "csharp"]
    # C++ adds no words a query with C# lacks; both clusters' other terms are added.
    assert expand_query("C# rules", glossary) == "C# rules cpp csharp"
    assert expand_query("csharp", glossary) == "csharp C# cpp"


@pytest.mark.parametrize(
    "text", ["terms: x\n", "terms:\n  - synonyms: [a]\n", "terms:\n  - primary: a\n    synonyms: b\n", ": :\n"]
)
def test_malformed_glossary(docs: Path, write: Write, text: str) -> None:
    write("docs/glossary.yaml", text)
    with pytest.raises(GlossaryInvalidError):
        load_glossary(docs)


def _search(root: Path, *args: str) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", "search", *args, "-w", str(root)])


def test_cli_text(docs: Path) -> None:
    result = _search(docs, "ADR-cache", "--mode", "lexical")
    lines = result.stdout.splitlines()
    assert result.exit_code == 0
    assert lines[0] == "[SEARCH: query=ADR-cache mode=lexical count=1]"
    assert lines[1] == (
        "[HIT: ADR-cache score=- pinned=yes kind=decision status=active"
        ' path=docs/decisions/2026-10/20261001-cache.md title="Cache derived data"]'
    )


def test_cli_json_and_empty_result(docs: Path) -> None:
    payload = json.loads(_search(docs, "search", "--mode", "lexical", "--format", "json").stdout)
    assert payload["mode"] == "lexical" and payload["hits"][0]["id"] == "CAP-CORE-search"
    assert _search(docs, "zzz", "--mode", "lexical").stdout == "[SEARCH: query=zzz mode=lexical count=0]\n"


def test_cli_rejects_a_negative_limit(docs: Path) -> None:
    result = _search(docs, "search", "--limit", "-1")
    assert result.exit_code == 2 and "(ARGUMENT_INVALID)" in result.stderr
