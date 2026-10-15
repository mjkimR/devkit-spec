"""``devkit spec search``: find documents by meaning, not only by exact ID.

Text output: ``[SEARCH: query= mode= count=]``, then one ``[HIT: <id> score= pinned= kind= status= path= title=]``
line per document, best first; a pinned exact match comes first with ``score=-``. ``mode`` is the ranking that ran
(``auto`` resolves to ``hybrid`` with ``devkit[search]`` installed, else ``lexical``).
"""

from __future__ import annotations

import click
from devkit.core.cli import (
    FORMAT_OPTION,
    boundary,
    echo_json,
    echo_notices,
    exit_on_warnings,
    is_json,
    resolve_root,
    workspace_option,
)
from devkit.core.errors import ArgumentError
from devkit.search import SearchMode

from devkit_spec.cli.documents import ALL_NAMESPACES, NAMESPACE, NamespaceScope
from devkit_spec.cli.output import fields_line, sentinel
from devkit_spec.documents import DocumentIndex, Kind
from devkit_spec.search import DEFAULT_LIMIT, DEFAULT_MIN_SIMILARITY, search_documents


@click.command(name="search")
@click.argument("words", nargs=-1, required=True, metavar="QUERY...")
@click.option(
    "--kind",
    "kinds",
    multiple=True,
    type=click.Choice([str(kind) for kind in Kind]),
    help="Only this kind (repeatable)",
)
@click.option(
    "--history", is_flag=True, help="Include the files of completed spec bundles (their feedback is always included)"
)
@NAMESPACE
@ALL_NAMESPACES
@click.option(
    "--mode",
    type=click.Choice([str(mode) for mode in SearchMode]),
    default=str(SearchMode.AUTO),
    show_default=True,
    help="Ranking: auto (hybrid when devkit[search] is installed, else lexical), lexical, dense, hybrid",
)
@click.option("--limit", "-n", type=int, default=DEFAULT_LIMIT, show_default=True, help="Hits to return; 0 for all")
@click.option(
    "--min-similarity",
    type=float,
    default=DEFAULT_MIN_SIMILARITY,
    show_default=True,
    help="Cosine floor of the dense ranking (dense and hybrid modes)",
)
@workspace_option()
@FORMAT_OPTION
@boundary
def search_cmd(
    words: tuple[str, ...],
    kinds: tuple[str, ...],
    history: bool,
    namespace: str | None,
    all_namespaces: bool,
    mode: str,
    limit: int,
    min_similarity: float,
    workspace_root: str | None,
    output_format: str,
) -> None:
    """Rank documents for QUERY (English works best: frontmatter is the main signal).

    An exact ID, path or file name is pinned first. docs/glossary.yaml synonyms expand the query.
    """
    if limit < 0:
        raise ArgumentError(
            f"--limit {limit}: must not be negative", target_files=["--limit"], fix="Pass --limit 0 or more"
        )
    query = " ".join(words)
    if not query.strip():
        raise ArgumentError(
            "QUERY: must not be empty or only whitespace",
            target_files=["QUERY"],
            fix="Pass at least one non-blank word as QUERY",
        )
    index = DocumentIndex.load(resolve_root(workspace_root))
    scope = NamespaceScope.of(index, namespace, all_namespaces)
    result = search_documents(
        index,
        query,
        kinds={Kind(kind) for kind in kinds},
        history=history,
        mode=SearchMode(mode),
        limit=limit,
        min_similarity=min_similarity,
        accept=scope.accepts,
    )
    if is_json(output_format):
        echo_json(
            {
                "query": result.query,
                "expanded": result.expanded,
                "mode": str(result.mode),
                "namespace": scope.selection.name,
                "hits": [
                    hit.document.to_dict()
                    | {"namespace": scope.namespace_of(hit.document), "score": hit.score, "pinned": hit.pinned}
                    for hit in result.hits
                ],
                "notices": [notice.to_dict() for notice in index.problems],
            }
        )
    else:
        click.echo(fields_line("SEARCH", query=result.query, mode=str(result.mode), count=len(result.hits)))
        for hit in result.hits:
            document = hit.document
            score = None if hit.score is None else f"{hit.score:.4f}"
            click.echo(
                sentinel(
                    "HIT",
                    document.id,
                    score=score,
                    pinned=hit.pinned,
                    kind=document.kind,
                    status=document.status,
                    path=document.path,
                    **scope.fields(document),
                    title=document.title,
                )
            )
    echo_notices(index.problems)
    exit_on_warnings(index.problems)
