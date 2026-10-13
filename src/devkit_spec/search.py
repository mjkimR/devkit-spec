"""Document search: devkit's ranking (``devkit.search``) with the spec search policy.

The policy on top of the generic ranking:

- **Candidates** are the indexed documents (``documents.DocumentIndex``), current ones only unless ``history``,
  optionally narrowed to some kinds.
- **Fields**: a document's ID, title and area are its metadata, ranked lexically and densely; the body after the
  frontmatter is ranked lexically only, so documents written in other languages are found through their English
  frontmatter.
- **Pinning**: a query equal to a document's ID, workspace-relative path or file name (case-insensitive) puts that
  document first, whatever the ranking.
- **Glossary expansion**: ``docs/glossary.yaml`` (optional; ``terms: [{primary, synonyms: [...]}]``) adds a term's
  whole synonym cluster to the query when the query contains any of its words.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

import yaml
from devkit.core import FrontmatterError
from devkit.core.frontmatter import parse
from devkit.search import SearchDocument, SearchIndex, SearchMode, tokenize

from devkit_spec.documents import Document, DocumentIndex, Kind
from devkit_spec.errors import GlossaryInvalidError

GLOSSARY_PATH = "docs/glossary.yaml"
DEFAULT_LIMIT = 10
# The similarity floor of devkit's playbook search: keeps the hybrid gain, drops the long tail.
DEFAULT_MIN_SIMILARITY = 0.35


@dataclass(frozen=True)
class SpecHit:
    """A ranked document; ``score`` is ``None`` for a pinned exact match."""

    document: Document
    score: float | None
    pinned: bool


@dataclass(frozen=True)
class SpecSearchResult:
    query: str
    expanded: str
    mode: SearchMode
    hits: list[SpecHit]


def load_glossary(root: Path) -> dict[str, list[str]]:
    """Each glossary word (casefolded) mapped to its whole cluster; empty without ``docs/glossary.yaml``."""
    path = root / GLOSSARY_PATH
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise GlossaryInvalidError(f"{GLOSSARY_PATH}: {exc}") from exc
    terms = data.get("terms", []) if isinstance(data, dict) else None
    if not isinstance(terms, list):
        raise GlossaryInvalidError(f"{GLOSSARY_PATH}: terms must be a list of {{primary, synonyms}}")
    index: dict[str, list[str]] = {}
    for term in terms:
        if not isinstance(term, dict) or not isinstance(term.get("primary"), str):
            raise GlossaryInvalidError(f"{GLOSSARY_PATH}: every term needs a primary string")
        synonyms = term.get("synonyms", [])
        if not isinstance(synonyms, list) or not all(isinstance(s, str) for s in synonyms):
            raise GlossaryInvalidError(f"{GLOSSARY_PATH}: synonyms of {term['primary']} must be a list of strings")
        cluster = [term["primary"], *synonyms]
        for word in cluster:
            if word.strip():
                index[word.strip().casefold()] = cluster
    return index


def expand_query(query: str, glossary: dict[str, list[str]]) -> str:
    """``query`` followed by the synonym clusters of the glossary words it contains."""
    if not glossary:
        return query
    lowered = query.casefold()
    words = set(tokenize(query))
    extra: list[str] = []
    for word, cluster in glossary.items():
        if word in words or (" " in word and word in lowered):
            extra.extend(term for term in cluster if term.casefold() not in lowered and term not in extra)
    return " ".join([query, *extra]) if extra else query


def _matches_exactly(document: Document, query: str) -> bool:
    wanted = query.strip().casefold()
    return wanted in (document.id.casefold(), document.path.casefold(), document.path.rsplit("/", 1)[-1].casefold())


def _body(root: Path, document: Document) -> str:
    try:
        return parse((root / document.path).read_text(encoding="utf-8")).body
    except (OSError, UnicodeDecodeError, FrontmatterError):
        return ""


def search_documents(
    index: DocumentIndex,
    query: str,
    *,
    kinds: Collection[Kind] = (),
    history: bool = False,
    mode: SearchMode = SearchMode.AUTO,
    limit: int = DEFAULT_LIMIT,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
) -> SpecSearchResult:
    """Rank the documents of ``index`` for ``query`` under the spec search policy; ``limit`` ``0`` returns all."""
    candidates = [
        document
        for document in index.documents
        if (not kinds or document.kind in kinds) and (history or not index.is_historical(document))
    ]
    expanded = expand_query(query, load_glossary(index.root))
    pinned = [document for document in candidates if _matches_exactly(document, query)]
    ranking = SearchIndex(
        [
            SearchDocument(
                document.path, "\n".join([document.id, document.title, document.area]), _body(index.root, document)
            )
            for document in candidates
        ]
    )
    resolved = ranking.resolve_mode(mode)
    by_path = {document.path: document for document in candidates}
    shown = {document.path for document in pinned}
    hits = [SpecHit(document, None, True) for document in pinned]
    for hit in ranking.search(expanded, mode=resolved, min_similarity=min_similarity):
        if hit.id not in shown:
            hits.append(SpecHit(by_path[hit.id], hit.score, False))
    return SpecSearchResult(query, expanded, resolved, hits[:limit] if limit else hits)
