"""``RULE-spec-lifecycle``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.spec_lifecycle`` in the installed devkit-spec package; the class defined
here is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain`` prints.
"""

from devkit_spec.rules.spec_lifecycle import SpecLifecycleRule as _Implementation


class SpecLifecycleRule(_Implementation):
    """A spec bundle's spec status, tasks progress and reconcile status agree."""
