"""Errors, warnings and notices of devkit-spec: ``AdvisoryError`` subclasses with ``SPEC_`` codes.

Each class carries the code and the Agent Advisory Protocol fields that fit
its condition, so a caller branches on ``error.code`` and the CLI boundary
renders the error as it is. devkit's own errors (``ARGUMENT_INVALID``,
``CONFIG_INVALID``, ``FRONTMATTER_INVALID``, ...) pass through unchanged.
"""

from __future__ import annotations

from devkit.advisory import Actor, AdvisoryError, Level, Retry


class SpecError(AdvisoryError):
    """Base class of every devkit-spec error; on its own an internal defect (``MAINTENANCE``)."""

    actor = Actor.DEVELOPER
    retry = Retry.AFTER_FIX


class DocumentInvalidWarning(SpecError):
    """A file under ``docs/`` or ``specs/`` could not be read as a document and was left out (``WARNING``)."""

    code = "SPEC_DOCUMENT_INVALID"
    level = Level.WARNING
    fix = "Correct the file's frontmatter (devkit's frontmatter grammar; id, reconcile_id and status are strings)"


class UnresolvedIdError(SpecError):
    """A document ID given to a command names no document (``INPUT_ERROR``)."""

    code = "SPEC_ID_UNRESOLVED"
    input_error = True
    fix = "Pass the exact ID of an existing document (devkit spec list shows them)"


class DuplicateIdError(SpecError):
    """More than one document declares the ID (``MAINTENANCE``); references to it are ambiguous."""

    code = "SPEC_ID_DUPLICATE"
    fix = "Give each document its own ID: the ID follows the document's path (RULE-id-convention)"
