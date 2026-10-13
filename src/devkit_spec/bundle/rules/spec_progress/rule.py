"""``RULE-spec-progress``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.spec_progress`` in the installed devkit-spec package; the class defined
here is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain`` prints.
"""

from devkit_spec.rules.spec_progress import SpecProgressRule as _Implementation


class SpecProgressRule(_Implementation):
    """A draft or planned spec with checked tasks is marked in-progress."""
