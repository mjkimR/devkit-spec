"""``RULE-traceability-link``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.traceability_link`` in the installed devkit-spec package; the class
defined here is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain``
prints.
"""

from devkit_spec.rules.traceability_link import TraceabilityLinkRule as _Implementation


class TraceabilityLinkRule(_Implementation):
    """Stories and capabilities record their M:N links in both directions by exact ID."""
