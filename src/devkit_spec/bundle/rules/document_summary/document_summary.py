"""``RULE-document-summary``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.document_summary`` in the installed devkit-spec package; the class defined
here is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain`` prints.
"""

from devkit_spec.rules.document_summary import DocumentSummaryRule as _Implementation


class DocumentSummaryRule(_Implementation):
    """Searchable documents carry a short English summary."""
