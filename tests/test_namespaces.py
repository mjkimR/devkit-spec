from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from conftest import Write
from devkit.cli import cli as devkit_cli
from devkit.core.errors import ArgumentError

from devkit_spec.config import Namespace, read_spec_config
from devkit_spec.documents import DocumentIndex
from devkit_spec.errors import SpecConfigError
from devkit_spec.namespaces import Selection, detect, docs_roots, living_path, namespace_resolver, select

API = Namespace("api", "services/api")
WEB = Namespace("web", "apps/web")
NESTED = Namespace("api-admin", "services/api/admin")
CONFIG = (
    '[[tool.spec.namespaces]]\nname = "api"\npath = "services/api"\n'
    '[[tool.spec.namespaces]]\nname = "web"\npath = "apps/web"\n'
)


def _doc(document_id: str, header: str = "") -> str:
    return f"---\nid: {document_id}\nstatus: active\n{header}---\n"


def test_config(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", CONFIG)
    assert read_spec_config(workspace).namespaces == (API, WEB)
    assert API.docs == "docs/packages/api"


@pytest.mark.parametrize(
    "entries",
    [
        '[tool.spec]\nnamespaces = "api"\n',
        '[[tool.spec.namespaces]]\nname = "api"\n',
        '[[tool.spec.namespaces]]\nname = "global"\npath = "x"\n',
        '[[tool.spec.namespaces]]\nname = "Api"\npath = "x"\n',
        '[[tool.spec.namespaces]]\nname = "api"\npath = "../x"\n',
        '[[tool.spec.namespaces]]\nname = "api"\npath = "./services/api"\n',
        '[[tool.spec.namespaces]]\nname = "api"\npath = "services//api"\n',
        '[[tool.spec.namespaces]]\nname = "api"\npath = "services/api/"\n',
        CONFIG + '[[tool.spec.namespaces]]\nname = "other"\npath = "./apps/web"\n',
        '[[tool.spec.namespaces]]\nname = "api"\npath = "x"\nextra = 1\n',
        CONFIG + '[[tool.spec.namespaces]]\nname = "api"\npath = "other"\n',
        CONFIG + '[[tool.spec.namespaces]]\nname = "other"\npath = "apps/web"\n',
    ],
)
def test_malformed_config(workspace: Path, write: Write, entries: str) -> None:
    write(".devkit/config.toml", entries)
    with pytest.raises(SpecConfigError):
        read_spec_config(workspace)


def test_non_canonical_path_names_the_canonical_form(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", '[[tool.spec.namespaces]]\nname = "api"\npath = "./services//api"\n')
    with pytest.raises(SpecConfigError) as caught:
        read_spec_config(workspace)
    assert "path = 'services/api'" in str(caught.value.fix)


def test_detect(workspace: Path) -> None:
    namespaces = (API, WEB, NESTED)
    assert detect(namespaces, workspace, workspace) is None
    assert detect(namespaces, workspace, workspace / "services/api/src") == "api"
    assert detect(namespaces, workspace, workspace / "services/api/admin/x") == "api-admin"
    assert detect(namespaces, workspace, workspace / "docs/packages/web/capabilities") == "web"
    assert detect(namespaces, workspace, workspace / "services/apix") is None
    assert detect(namespaces, workspace, workspace.parent) is None


def test_select(workspace: Path) -> None:
    assert select((API,), workspace, workspace / "services/api", None, False) == Selection("api")
    assert select((API,), workspace, workspace / "services/api", "global", False) == Selection("global")
    assert select((API,), workspace, workspace / "services/api", None, True) == Selection()
    assert select((), workspace, workspace, None, False) == Selection()  # no namespaces: nothing to narrow
    assert select((), workspace, workspace, "global", False) == Selection()
    with pytest.raises(ArgumentError):
        select((), workspace, workspace, "api", False)  # validated even when none is registered
    with pytest.raises(ArgumentError):
        select((API,), workspace, workspace, "nope", False)
    with pytest.raises(ArgumentError):
        select((API,), workspace, workspace, "api", True)


def test_selection_matches() -> None:
    assert Selection().matches("api") and Selection().matches("global")
    assert Selection("api").matches("api") and Selection("api").matches("global")
    assert not Selection("api").matches("web")
    assert Selection("global").matches("global") and not Selection("global").matches("api")


def test_namespace_of_documents(workspace: Path, write: Write) -> None:
    write("docs/packages/api/capabilities/core/CAP-API-x.md", _doc("CAP-API-x"))
    write("docs/capabilities/core/CAP-CORE-y.md", _doc("CAP-CORE-y"))
    write("specs/2026-10/20261001-a/spec.md", _doc("SPEC-a", "namespace: web\n"))
    write("specs/2026-10/20261001-a/plan.md", _doc("PLAN-a"))
    write("specs/2026-10/20261001-b/spec.md", _doc("SPEC-b", "namespace: nope\n"))
    write("docs/proposals/PROP-c/proposal.md", _doc("PROP-c", "namespace: api\n"))
    write("docs/proposals/PROP-c/decisions/PADR-c.md", _doc("PADR-c"))
    write("docs/proposals/PROP-d.md", _doc("PROP-d", "namespace: api\n"))
    write("docs/proposals/PROP-e.md", _doc("PROP-e", "namespace: nope\n"))
    index = DocumentIndex.load(workspace)
    namespace_of = namespace_resolver(index, (API, WEB))
    assert {document.id: namespace_of(document) for document in index.documents} == {
        "CAP-API-x": "api",
        "CAP-CORE-y": "global",
        "SPEC-a": "web",
        "PLAN-a": "web",
        "SPEC-b": "global",
        "PROP-c": "api",
        "PADR-c": "api",
        "PROP-d": "api",
        "PROP-e": "global",
    }


def test_living_path_and_roots() -> None:
    assert (
        living_path((API,), "docs/packages/api/capabilities/core/CAP-API-x.md") == "docs/capabilities/core/CAP-API-x.md"
    )
    assert living_path((API,), "docs/capabilities/x.md") == "docs/capabilities/x.md"
    assert docs_roots((API, WEB)) == ["docs", "docs/packages/api", "docs/packages/web"]


@pytest.fixture
def monorepo(workspace: Path, write: Write) -> Path:
    write(".devkit/config.toml", CONFIG)
    write("docs/packages/api/capabilities/core/CAP-API-search.md", _doc("CAP-API-search", "title: API search\n"))
    write("docs/packages/web/capabilities/core/CAP-WEB-search.md", _doc("CAP-WEB-search", "title: Web search\n"))
    write("docs/capabilities/core/CAP-CORE-search.md", _doc("CAP-CORE-search", "title: Core search\n"))
    (workspace / "services/api/src").mkdir(parents=True)
    return workspace


def _spec(root: Path, *args: str) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", *args, "-w", str(root)])


def _ids(result: Result) -> list[str]:
    payload = json.loads(result.stdout)
    return [item["id"] for item in payload.get("documents", payload.get("hits", []))]


def test_list_follows_the_current_directory(monorepo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(monorepo / "services/api/src")
    assert _ids(_spec(monorepo, "list", "--format", "json")) == ["CAP-API-search", "CAP-CORE-search"]
    assert _ids(_spec(monorepo, "list", "--all-namespaces", "--format", "json")) == [
        "CAP-API-search",
        "CAP-CORE-search",
        "CAP-WEB-search",
    ]
    assert _ids(_spec(monorepo, "list", "--namespace", "global", "--format", "json")) == ["CAP-CORE-search"]
    monkeypatch.chdir(monorepo)
    assert len(_ids(_spec(monorepo, "list", "--format", "json"))) == 3


def test_list_text_shows_namespaces_only_when_configured(monorepo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(monorepo)
    first = _spec(monorepo, "list", "--namespace", "web", "--limit", "1").stdout.splitlines()
    assert first[0].startswith("[DOCUMENT: CAP-CORE-search ") and " namespace=global " in first[0]
    assert first[-1].endswith("--namespace web -w " + str(monorepo) + " --limit 1 --offset 1]")


def test_search_follows_the_namespace(monorepo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(monorepo / "services/api")
    assert set(_ids(_spec(monorepo, "search", "search", "--mode", "lexical", "--format", "json"))) == {
        "CAP-API-search",
        "CAP-CORE-search",
    }
    result = _spec(monorepo, "search", "search", "--namespace", "nope")
    assert result.exit_code == 2 and "(ARGUMENT_INVALID)" in result.stderr
