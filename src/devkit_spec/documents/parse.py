"""Read one document: its identity from the frontmatter, its references from the frontmatter and the prose.

The frontmatter follows devkit's grammar (``devkit.core.frontmatter``): a
malformed block raises ``FrontmatterError``. A document is indexed only when
its ``id`` (or, for a reconcile file, ``reconcile_id``) is a well-formed ID;
``id``, ``reconcile_id`` and ``status`` must be strings. Body references are
`` `ID` `` code spans and ``[ID]`` brackets in prose (``markdown.visible_lines``);
a heading line ``# ... ID ...`` does not reference the document's own ID.
"""

from __future__ import annotations

import re
from typing import Any

import yaml
from devkit.core import FrontmatterError
from devkit.core.frontmatter import load_header, locate

from devkit_spec.documents.ids import ID_SOURCE, kind_of
from devkit_spec.documents.markdown import visible_lines
from devkit_spec.documents.model import (
    BODY,
    LIST_FIELDS,
    PROVENANCE_FIELDS,
    SCALAR_FIELDS,
    Document,
    Issue,
    Reference,
)

_CODE_SPAN_ID = re.compile(rf"`({ID_SOURCE})`")
_BRACKET_ID = re.compile(rf"\[({ID_SOURCE})\]")
_STRING_FIELDS = ("id", "reconcile_id", "status")


def parse_document(path: str, text: str) -> Document | None:
    """The document at workspace-relative ``path``, or ``None`` when it declares no well-formed ID.

    Raises ``FrontmatterError`` for a malformed frontmatter block or a non-string ``id``, ``reconcile_id`` or
    ``status``.
    """
    block = locate(text)
    if block is None:
        return None
    data = load_header(block.header)
    header_line = text.count("\n", 0, block.header_start) + 1
    for name in _STRING_FIELDS:
        if name in data and not isinstance(data[name], str):
            raise FrontmatterError(f"{path}: frontmatter {name} must be a string", target_files=[path])
    document_id = data.get("id") or data.get("reconcile_id") or ""
    kind = kind_of(document_id)
    if kind is None:
        return None
    document = Document(id=document_id, path=path, kind=kind, frontmatter=data)
    fields = [name for name in (*LIST_FIELDS, *SCALAR_FIELDS, *PROVENANCE_FIELDS) if name in data]
    nodes = _field_nodes(block.header) if fields else {}
    line_starts = _line_starts(text) if fields else []
    for name in fields:
        refs = _field_references(document, name, data[name], nodes.get(name), line_starts, header_line)
        (document.provenance if name in PROVENANCE_FIELDS else document.references).extend(refs)
    document.references.extend(_body_references(document, text, block.end, block.body_line))
    return document


# libyaml when PyYAML has it: the header is composed again only for the positions of its values.
_COMPOSER: type[yaml.SafeLoader] = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def _line_starts(text: str) -> list[int]:
    """The offset of the first character of each line (index 0 is line 1)."""
    starts = [0]
    index = text.find("\n")
    while index >= 0:
        starts.append(index + 1)
        index = text.find("\n", index + 1)
    return starts


def _field_nodes(header: str) -> dict[str, yaml.Node]:
    root = yaml.compose(header, Loader=_COMPOSER)
    if not isinstance(root, yaml.MappingNode):
        return {}
    return {key.value: value for key, value in root.value if isinstance(key, yaml.ScalarNode)}


def _field_references(
    document: Document, name: str, value: Any, node: yaml.Node | None, line_starts: list[int], header_line: int
) -> list[Reference]:
    line = header_line + (node.start_mark.line if node is not None else 0)
    if name in LIST_FIELDS:
        if not isinstance(value, list) or not isinstance(node, yaml.SequenceNode):
            document.issues.append(Issue(line, f"{name} must be a list of IDs"))
            return []
        items = list(zip(value, node.value, strict=True))
    else:
        if not isinstance(value, str) or not isinstance(node, yaml.ScalarNode):
            document.issues.append(Issue(line, f"{name} must be one ID"))
            return []
        items = [(value, node)]
    refs = []
    for item, item_node in items:
        start, end = item_node.start_mark, item_node.end_mark
        if not isinstance(item, str):
            document.issues.append(Issue(header_line + start.line, f"{name} must contain string IDs"))
            continue
        refs.append(
            Reference(
                target=item,
                source=document.id,
                path=document.path,
                field=name,
                line=header_line + start.line,
                column=start.column + 1,
                start=line_starts[header_line + start.line - 1] + start.column,
                end=line_starts[header_line + end.line - 1] + end.column,
            )
        )
    return refs


def _body_references(document: Document, text: str, start: int, first_line: int) -> list[Reference]:
    refs: list[Reference] = []
    for line in visible_lines(text, start=start, first_line=first_line):
        heading = line.text.lstrip().startswith("# ")
        found = [(match, False) for match in _CODE_SPAN_ID.finditer(line.text)]
        found += [(match, True) for match in _BRACKET_ID.finditer(line.text)]
        for match, bracket in sorted(found, key=lambda item: item[0].start()):
            target = match.group(1)
            if heading and target == document.id:
                continue
            refs.append(
                Reference(
                    target=target,
                    source=document.id,
                    path=document.path,
                    field=BODY,
                    line=line.number,
                    column=match.start(1) + 1,
                    start=line.offset + match.start(1),
                    end=line.offset + match.end(1),
                    bracket=bracket,
                )
            )
    return refs
