"""``RULE-code-entrypoints``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.code_entrypoints`` in the installed devkit-spec package; the class
defined here is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain``
prints.
"""

from devkit_spec.rules.code_entrypoints import CodeEntrypointsRule as _Implementation


class CodeEntrypointsRule(_Implementation):
    """Every entrypoints path of a capability or story exists in the workspace."""
