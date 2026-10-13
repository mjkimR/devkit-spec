"""Errors, warnings and notices of devkit-spec: ``AdvisoryError`` subclasses with ``SPEC_`` codes.

Each class carries the code and the Agent Advisory Protocol fields that fit
its condition, so a caller branches on ``error.code`` and the CLI boundary
renders the error as it is. devkit's own errors (``ARGUMENT_INVALID``,
``CONFIG_INVALID``, ``FRONTMATTER_INVALID``, ...) pass through unchanged.
"""

from __future__ import annotations

from devkit.advisory import Actor, AdvisoryError, Level, Retry
from devkit.core.errors import ConfigError


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


class SpecConfigError(SpecError, ConfigError):
    """The ``[tool.spec]`` table of ``.devkit/config.toml`` is malformed (``INPUT_ERROR``)."""

    code = "SPEC_CONFIG_INVALID"
    target_files = (".devkit/config.toml",)
    fix = "Correct the [tool.spec] table in .devkit/config.toml (devkit spec policy shows the effective values)"


class GlossaryInvalidError(SpecError):
    """``docs/glossary.yaml`` cannot be read or does not hold ``terms: [{primary, synonyms}]`` (``INPUT_ERROR``)."""

    code = "SPEC_GLOSSARY_INVALID"
    input_error = True
    target_files = ("docs/glossary.yaml",)
    fix = "Correct docs/glossary.yaml: terms is a list of {primary: <term>, synonyms: [<term>, ...]}"


class ProposalSlugError(SpecError):
    """A proposal slug or PADR title keeps no letter or digit after normalization (``INPUT_ERROR``)."""

    code = "SPEC_PROPOSAL_SLUG_INVALID"
    input_error = True
    fix = "Pass a slug or title with at least one letter or digit (for example login-flow)"


class ProposalExistsError(SpecError):
    """The proposal or PADR to create already exists (``INPUT_ERROR``)."""

    code = "SPEC_PROPOSAL_EXISTS"
    input_error = True
    fix = "Choose another slug or PADR title, or edit the existing file named in [TARGET]"


class ProposalSlugConflictError(SpecError):
    """A spec already uses the proposal's slug (``INTERACTION``): a handed-off ``PROP`` ID maps to one ``SPEC``."""

    code = "SPEC_PROPOSAL_SLUG_CONFLICT"
    actor = Actor.USER
    what_to_report = "Which unused slug the proposal takes, or whether it duplicates the existing spec in [TARGET]"
    fix = "Rerun with the unused slug the user chose; the existing spec keeps its ID"


class ProposalNotFoundError(SpecError):
    """No proposal bundle or single-file proposal has the slug (``INPUT_ERROR``)."""

    code = "SPEC_PROPOSAL_NOT_FOUND"
    input_error = True
    fix = "Pass the slug of an existing proposal (devkit spec list proposal shows them)"


class ProposalInvalidError(SpecError):
    """A proposal file or PADR cannot be read, or its frontmatter does not parse (``MAINTENANCE``)."""

    code = "SPEC_PROPOSAL_INVALID"
    fix = "Correct the file in [TARGET] (UTF-8 text, devkit's frontmatter grammar), then rerun the command"


class ProposalNotApprovedError(SpecError):
    """The proposal is not approved for handoff (``INTERACTION``)."""

    code = "SPEC_PROPOSAL_NOT_APPROVED"
    actor = Actor.USER
    what_to_report = "The proposal's status, and that its handoff needs the user's approval of its direction"
    fix = (
        "After the user approves, set status: accepted in the proposal, or rerun with --direction-chosen when the "
        "user chose the direction of a draft or reviewing proposal"
    )


class ProposalWorkflowError(SpecError):
    """The proposal's ``handoff_workflow`` cannot be resolved or does not validate (``MAINTENANCE``)."""

    code = "SPEC_PROPOSAL_WORKFLOW_INVALID"
    fix = (
        "Set the proposal's handoff_workflow field to the id of a valid workflow (devkit workflow validate), or "
        "remove the field to use direct-delivery, then rerun the handoff"
    )


class ProposalTargetExistsError(SpecError):
    """A file or directory the handoff would create already exists (``BLOCKED``); nothing was written."""

    code = "SPEC_PROPOSAL_TARGET_EXISTS"
    guardrail = True
    fix = "Move or remove the path in [TARGET] (or rename the PADR whose ADR it is), then rerun the handoff"


class ProposalHandoffError(SpecError):
    """Writing the handoff failed (``MAINTENANCE``); the files it had written were removed and the proposal kept."""

    code = "SPEC_PROPOSAL_HANDOFF_FAILED"
    fix = "Fix the file system problem in [DETAIL], then rerun the handoff"


class ProposalCleanupWarning(SpecError):
    """The handoff completed but the proposal could not be removed (``WARNING``)."""

    code = "SPEC_PROPOSAL_CLEANUP_FAILED"
    level = Level.WARNING
    fix = "Delete the proposal in [TARGET] by hand: the spec bundle replaces it"


class ProposalLinkUnresolvedWarning(SpecError):
    """Links or ID references into the removed proposal have no new target (``WARNING``)."""

    code = "SPEC_PROPOSAL_LINK_UNRESOLVED"
    level = Level.WARNING
    fix = (
        "Edit each [UNRESOLVED_LINK] location by hand: point it at the spec, ADR or material that replaced the "
        "target, or remove it"
    )


class ProposalReferencesRewrittenNotice(SpecError):
    """ID references to the proposal or its PADRs now name the spec or the ADRs (``NOTICE``)."""

    code = "SPEC_PROPOSAL_REFS_REWRITTEN"
    level = Level.NOTICE
    fix = (
        "Reread the sentence at each [REWRITTEN ... kind=id] location: one that names the proposal as an origin may "
        "need rewording"
    )


class ProposalUnboundNotice(SpecError):
    """A new proposal or handed-off spec is not bound to a workflow: its default workflow is not available
    (``NOTICE``)."""

    code = "SPEC_PROPOSAL_UNBOUND"
    level = Level.NOTICE
    fix = "Bind the unit with devkit workflow bind --unit <dir> --workflow <id> once a workflow fits it"


class SpecSlugError(SpecError):
    """A spec slug keeps no letter or digit after normalization (``INPUT_ERROR``)."""

    code = "SPEC_SLUG_INVALID"
    input_error = True
    fix = "Pass a slug with at least one letter or digit (for example login-flow)"


class SpecExistsError(SpecError):
    """``devkit spec new``: the slug is taken by a spec or a proposal, or the bundle directory exists
    (``INPUT_ERROR``)."""

    code = "SPEC_EXISTS"
    input_error = True
    fix = (
        "Choose an unused slug; for a proposal of the same slug, hand it off with devkit spec proposal handoff "
        "<slug> instead"
    )


class SpecWorkflowError(SpecError):
    """``devkit spec new --workflow`` names a workflow that does not resolve or validate (``INPUT_ERROR``)."""

    code = "SPEC_WORKFLOW_INVALID"
    input_error = True
    fix = "Pass the id of a valid workflow (devkit workflow validate), or omit --workflow for direct-delivery"


class SpecWriteError(SpecError):
    """``devkit spec new``: writing the bundle failed (``MAINTENANCE``); what was written was removed."""

    code = "SPEC_WRITE_FAILED"
    fix = "Fix the file system problem in [DETAIL], then rerun the command"


class SpecUnboundNotice(SpecError):
    """``devkit spec new``: the spec is not bound, ``direct-delivery`` is not available (``NOTICE``)."""

    code = "SPEC_UNBOUND"
    level = Level.NOTICE
    fix = "Bind the unit with devkit workflow bind --unit <dir> --workflow <id> once a workflow fits it"
