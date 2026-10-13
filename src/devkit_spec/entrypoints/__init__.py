"""devkit_spec.entrypoints: code entrypoints of capabilities and stories, and their derivation from spec bundles.

``paths`` holds the path contract (``RULE-code-entrypoints`` checks it), ``bundle`` reads a spec bundle's
declarations, ``derive`` joins them into document-code pairs and ``apply`` writes chosen pairs into frontmatter.
Libraries never print: ``devkit spec entrypoints derive`` renders the results. See ``docs/entrypoints.md``.
"""

from devkit_spec.entrypoints.apply import Applied, ApplyResult, apply, collapse, set_entrypoints
from devkit_spec.entrypoints.bundle import Bundle, Target, TaskBoundary, load_bundle, parse_boundaries
from devkit_spec.entrypoints.derive import (
    Pair,
    Reason,
    SkipKind,
    Skipped,
    State,
    aggregate,
    classify_boundary,
    declared_entrypoints,
    derive,
    exclude,
    select,
)
from devkit_spec.entrypoints.paths import covers, entrypoint_bearing, exists, living_path, normalize, overlaps

__all__ = [
    "Applied",
    "ApplyResult",
    "Bundle",
    "Pair",
    "Reason",
    "SkipKind",
    "Skipped",
    "State",
    "Target",
    "TaskBoundary",
    "aggregate",
    "apply",
    "classify_boundary",
    "collapse",
    "covers",
    "declared_entrypoints",
    "derive",
    "entrypoint_bearing",
    "exclude",
    "exists",
    "living_path",
    "load_bundle",
    "normalize",
    "overlaps",
    "parse_boundaries",
    "select",
    "set_entrypoints",
]
