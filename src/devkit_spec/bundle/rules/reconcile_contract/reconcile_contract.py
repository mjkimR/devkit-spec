"""``RULE-reconcile-contract``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.reconcile_contract`` in the installed devkit-spec package; the class
defined here is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain``
prints.
"""

from devkit_spec.rules.reconcile_contract import ReconcileContractRule as _Implementation


class ReconcileContractRule(_Implementation):
    """A reconcile.md record has an id, a pending or resolved status and well-formed targets."""
