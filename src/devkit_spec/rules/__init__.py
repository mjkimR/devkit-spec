"""devkit_spec.rules: the governance rules of the spec bundle, run by ``devkit rules``.

Each rule is a ``BaseRule`` subclass here; the bundle ships one directory per
rule, as devkit's own rules are laid out: ``bundle/rules/<name>/rule.py``, a
thin subclass (``devkit rules`` instantiates only the classes a rule file
defines), and ``guide.md`` beside it (``guide="guide.md"`` resolves relative to
the deployed ``rule.py``). The rule's tests sit in ``tests/test_rule.py`` of
the same folder and deploy with it: they load the folder with
``devkit.rules.testing.load_rule``, so they exercise the deployed subclass and
this implementation together, and ``devkit rules test`` runs them.
``related`` names the bundle instructions that hold a rule's judgment. The
rules read documents through ``document_index``,
which goes through the run's workspace cache: a Git snapshot run
(``check --staged``, ``--ci``) sees the snapshot, and a fix is seen by the
recheck.

Reporting follows devkit's targeting: a violation is reported for a file only
when ``ctx.is_file_targeted`` accepts it. Files of completed spec bundles are
work history and are checked only when named as explicit targets.

Document namespaces (``[[tool.spec.namespaces]]``) are read with
``namespaces(ctx)``: a namespace docs root ``docs/packages/<name>/`` holds
Living Spec documents under the same conventions as ``docs/``. A malformed
``[tool.spec]`` table is not a violation: ``SpecConfigError`` propagates and
fails the run (``RULES_EXECUTION_FAILED``, exit 2), as devkit treats its own
malformed configuration, because no document can be checked against a
namespace registry that cannot be read.
"""

from __future__ import annotations

from pathlib import Path

from devkit.rules import RuleContext

from devkit_spec.config import Namespace, read_spec_config
from devkit_spec.documents import SOURCE_DIRECTORIES, Document, DocumentIndex

FIX_COMMAND = "devkit rules fix"


def document_index(ctx: RuleContext) -> DocumentIndex:
    """The document index of the run's workspace, read through its cache."""
    root = ctx.workspace_root

    def read(path: Path) -> str:
        return ctx.cache.read_bytes(path).decode("utf-8")

    files = [
        path
        for directory in SOURCE_DIRECTORIES
        if (root / directory).is_dir()
        for path in ctx.cache.find_files(root / directory, extensions=(".md",))
    ]
    return DocumentIndex.load(root, files=files, read=read)


def namespaces(ctx: RuleContext) -> tuple[Namespace, ...]:
    """The document namespaces of the run's workspace; raises ``SpecConfigError`` for a malformed ``[tool.spec]``."""
    return read_spec_config(ctx.workspace_root).namespaces


def explicitly_targeted(ctx: RuleContext, path: str) -> bool:
    """Whether the run named ``path`` as a target (not merely a whole-workspace run)."""
    return ctx.has_targets and path in ctx.changed_files


def reportable(ctx: RuleContext, index: DocumentIndex, document: Document) -> bool:
    """Whether violations in ``document`` are reported: targeted, and current unless explicitly targeted."""
    if not ctx.is_file_targeted(document.path):
        return False
    return not index.is_historical(document) or explicitly_targeted(ctx, document.path)


def is_material(document: Document) -> bool:
    """Free-form materials (``docs/materials/``, any ``/materials/`` directory) follow no authoring convention."""
    return document.path.startswith("docs/materials/") or "/materials/" in document.path
