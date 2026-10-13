"""``RULE-task-coverage``, loaded by ``devkit rules`` from this synchronized copy.

The implementation is ``devkit_spec.rules.task_coverage`` in the installed devkit-spec package; the class defined here
is what ``devkit rules`` instantiates, and the guide beside this file is what ``devkit rules explain`` prints.
"""

from devkit_spec.rules.task_coverage import TaskCoverageRule as _Implementation


class TaskCoverageRule(_Implementation):
    """Acceptance criteria of active specs and the task references in tasks.md cover each other."""
