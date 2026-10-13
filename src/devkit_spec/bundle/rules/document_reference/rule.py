"""``RULE-document-reference``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.document_reference`` in the installed devkit-spec package; the class
defined here is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain``
prints.
"""

from devkit_spec.rules.document_reference import DocumentReferenceRule as _Implementation


class DocumentReferenceRule(_Implementation):
    """Documents reference each other by exact, resolvable full IDs."""
