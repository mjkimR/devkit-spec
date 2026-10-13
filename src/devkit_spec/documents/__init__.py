"""devkit_spec.documents: the document model of spec-driven development.

IDs (``ids``), documents and references (``model``), the parser
(``parse_document``), the Markdown body scanner (``markdown``) and the
workspace index (``DocumentIndex``). See ``docs/documents/overview.md``.
"""

from devkit_spec.documents.ids import ID_PATTERN, PREFIXES, Kind, is_id, kind_of
from devkit_spec.documents.index import SOURCE_DIRECTORIES, DocumentIndex, in_source_directory, is_document_file
from devkit_spec.documents.markdown import VisibleLine, visible_lines
from devkit_spec.documents.model import Document, Issue, Reference
from devkit_spec.documents.parse import parse_document
from devkit_spec.documents.rewrite import rewrite

__all__ = [
    "ID_PATTERN",
    "PREFIXES",
    "SOURCE_DIRECTORIES",
    "Document",
    "DocumentIndex",
    "Issue",
    "Kind",
    "Reference",
    "VisibleLine",
    "in_source_directory",
    "is_document_file",
    "is_id",
    "kind_of",
    "parse_document",
    "rewrite",
    "visible_lines",
]
