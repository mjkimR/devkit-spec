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


class ProposalWrongWorktreeError(SpecError):
    """A handoff runs in a linked worktree whose branch is not the proposal's slug (``INPUT_ERROR``): the spec
    bundle would land on another task's branch."""

    code = "SPEC_PROPOSAL_WRONG_WORKTREE"
    input_error = True


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
    """The handoff completed but the proposal could not be removed, or the post-finish prune of the slug's empty
    proposal directories failed (``WARNING``)."""

    code = "SPEC_PROPOSAL_CLEANUP_FAILED"
    level = Level.WARNING
    fix = "Delete the proposal in [TARGET] by hand: the spec bundle replaces it"


class ProposalGateNotCarriedWarning(SpecError):
    """The handoff completed but a gate of the spec could not be recorded from the user's direction answer of the
    proposal (``WARNING``); the gates recorded before it stay."""

    code = "SPEC_PROPOSAL_GATE_NOT_CARRIED"
    level = Level.WARNING
    fix = "Record the gate in [TARGET] with devkit workflow answer --by user once the cause in [DETAIL] is resolved"


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
    """``devkit spec new``: writing the bundle failed (``MAINTENANCE``); what was written was removed, except what
    the details list when the roll-back was incomplete."""

    code = "SPEC_WRITE_FAILED"
    fix = "Fix the file system problem in [DETAIL], then rerun the command"


class SpecUnboundNotice(SpecError):
    """``devkit spec new``: the spec is not bound, ``direct-delivery`` is not available (``NOTICE``)."""

    code = "SPEC_UNBOUND"
    level = Level.NOTICE
    fix = "Bind the unit with devkit workflow bind --unit <dir> --workflow <id> once a workflow fits it"


class EntrypointsInputMissingError(SpecError):
    """``devkit spec entrypoints derive --spec``: the bundle has no ``tasks.md`` or ``reconcile.md``
    (``INPUT_ERROR``)."""

    code = "SPEC_ENTRYPOINTS_INPUT_MISSING"
    input_error = True
    fix = (
        "Write the file in [TARGET] first (tasks.md with the spec-tasks skill, reconcile.md with the spec-sync "
        "skill), then rerun the derivation"
    )


class EntrypointsInputInvalidError(SpecError):
    """``devkit spec entrypoints derive --spec``: ``tasks.md`` or ``reconcile.md`` cannot be read, or the
    frontmatter of ``reconcile.md`` is not the shape ``RULE-reconcile-contract`` checks (``MAINTENANCE``)."""

    code = "SPEC_ENTRYPOINTS_INPUT_INVALID"
    fix = (
        "Repair the file in [TARGET] (UTF-8 text; reconcile.md frontmatter with targets: [{file, resolution}]), "
        "then rerun the derivation"
    )


class EntrypointsPathError(SpecError):
    """An entrypoint path is not a literal workspace-relative path: empty, absolute, with a ``..`` segment, a glob,
    a backslash, a drive colon or a control character (``INPUT_ERROR``)."""

    code = "SPEC_ENTRYPOINTS_PATH_INVALID"
    input_error = True
    fix = "Pass a literal workspace-relative file or directory path (no glob, no leading /, no .. segment)"


class EntrypointsTargetError(SpecError):
    """``devkit spec entrypoints derive --apply --target``: the ID or path is not among the derived documents
    (``INPUT_ERROR``)."""

    code = "SPEC_ENTRYPOINTS_TARGET_UNKNOWN"
    input_error = True
    fix = "Pass the ID or path of a document that appears in the derive output without --apply"


class EntrypointsApplyError(SpecError):
    """``devkit spec entrypoints derive --apply``: some documents could not be written (``MAINTENANCE``); the
    documents in [TARGET] are unchanged, the others listed as applied were written."""

    code = "SPEC_ENTRYPOINTS_APPLY_FAILED"
    fix = "Fix the problem in [DETAIL] for each document in [TARGET], then rerun the same command with --apply"


class ScopeError(SpecError):
    """Base class of the work-scope registry errors (``devkit spec scope``)."""


class ScopeNotAWorktreeError(ScopeError):
    """The workspace is not inside a Git work tree, so it has no registry location or token (``INPUT_ERROR``)."""

    code = "SPEC_SCOPE_NOT_A_WORKTREE"
    input_error = True
    fix = "Run the command inside a Git work tree of the project, or pass it with -w"


class ScopeSpecNotFoundError(ScopeError):
    """``--spec`` names no directory in the workspace (``INPUT_ERROR``)."""

    code = "SPEC_SCOPE_SPEC_NOT_FOUND"
    input_error = True
    fix = "Pass an existing spec bundle directory: specs/<YYYY-MM>/<YYYYMMDD>-<slug>"


class ScopeInputInvalidError(ScopeError):
    """A scope input (``tasks.md``, ``reconcile.md``, ``target-docs.md``) cannot be read, or its ``targets``
    frontmatter is not a list of mappings with a string ``file`` (``MAINTENANCE``)."""

    code = "SPEC_SCOPE_INPUT_INVALID"
    fix = "Repair the file in [TARGET] (UTF-8 text; targets: [{file: <workspace-relative path>, ...}]), then rerun"


class ScopeTokenMissingError(ScopeError):
    """This worktree holds no registry token: it registered no task, or released it (``INPUT_ERROR``)."""

    code = "SPEC_SCOPE_TOKEN_MISSING"
    input_error = True
    fix = (
        "A worktree that does not take part in the registry skips scope update; to take part, register first: "
        "devkit spec scope register --spec <dir>"
    )


class ScopeTokenExistsError(ScopeError):
    """This worktree already registered a task; a second registration would orphan the first (``INPUT_ERROR``)."""

    code = "SPEC_SCOPE_TOKEN_EXISTS"
    input_error = True
    fix = (
        "Keep the registration (devkit spec scope query shows it with own=yes) and run devkit spec scope update, "
        "or run devkit spec scope release first"
    )


class ScopeTaskExistsError(ScopeError):
    """Another record of the namespace has the task ID (``INPUT_ERROR``)."""

    code = "SPEC_SCOPE_TASK_EXISTS"
    input_error = True
    fix = "Pass a distinct --task-id, or release the other record from the worktree that registered it"


class ScopeRecordMissingError(ScopeError):
    """The record of this worktree's token no longer exists: it was released or swept (``INPUT_ERROR``)."""

    code = "SPEC_SCOPE_RECORD_MISSING"
    input_error = True
    fix = "Run devkit spec scope release (it removes the orphaned token), then devkit spec scope register --spec <dir>"


class ScopeTokenMismatchError(ScopeError):
    """The token does not own the record: only the registering worktree updates or releases it (``BLOCKED``)."""

    code = "SPEC_SCOPE_TOKEN_MISMATCH"
    guardrail = True
    fix = (
        "Update or release the record from the worktree that registered it; sweep removes records of removed worktrees"
    )


class ScopeStaleRevisionError(ScopeError):
    """The record changed between the read and the write (``AUTO``); nothing was written."""

    code = "SPEC_SCOPE_STALE_REVISION"
    actor = Actor.TOOL
    retry = Retry.SAFE
    fix = "Rerun the same command: it reads the current revision"


class ScopeTimeoutError(ScopeError):
    """The operation exceeded ``[tool.spec.scope] timeout``: the namespace lock or Git stayed busy (``DEFER``)."""

    code = "SPEC_SCOPE_TIMEOUT"
    actor = Actor.NONE
    retry = Retry.SAFE
    fix = (
        "Retry once the other registry command has finished (an update with --request-id <request_id> from "
        "[SCOPE_ACK]); raise [tool.spec.scope] timeout when the registry is busy for longer"
    )


class ScopeLockUnsupportedError(ScopeError):
    """The platform has no ``fcntl.flock``: the local registry runs on Linux and macOS only (``BLOCKED``)."""

    code = "SPEC_SCOPE_LOCK_UNSUPPORTED"
    guardrail = True
    fix = "Run devkit spec scope on Linux or macOS"


class ScopeNamespaceError(ScopeError):
    """A registry namespace is empty, contains a path separator or starts with a dot (``INPUT_ERROR``)."""

    code = "SPEC_SCOPE_NAMESPACE_INVALID"
    input_error = True
    fix = "Set [tool.spec.scope] namespace to a plain name of letters, digits, '.', '_' and '-' not starting with '.'"


class ScopeSharedPathError(ScopeError):
    """The shared registry directory cannot be created, read or written (``INTERACTION``)."""

    code = "SPEC_SCOPE_SHARED_PATH_UNAVAILABLE"
    actor = Actor.USER
    retry = Retry.AFTER_FIX
    what_to_report = "The registry directory in [TARGET] and the file system error"
    fix = "Fix the permissions of the directory in [TARGET], or set [tool.spec.scope] shared_path to a writable one"


class ScopeUnsupportedError(ScopeError):
    """An adapter operation reserved by the registry contract (``claim``) is not implemented (``MAINTENANCE``)."""

    code = "SPEC_SCOPE_UNSUPPORTED"
    fix = "Do not call the reserved operation: exclusive claims are not part of the local registry"


class ScopeAckFailedError(ScopeError):
    """``devkit spec scope update`` did not apply for a cause without its own code (``MAINTENANCE``); the record is
    unchanged."""

    code = "SPEC_SCOPE_ACK_FAILED"
    fix = "Fix the cause in [DETAIL], then rerun devkit spec scope update"


class ScopeSharedWorktreeWarning(ScopeError):
    """Another task of the namespace registered the same worktree (``WARNING``): changes observed there are
    attributed to both."""

    code = "SPEC_SCOPE_SHARED_WORKTREE"
    level = Level.WARNING
    fix = "Run one registered task per worktree; release the other task's record when it is done"


class ScopeRecordInvalidWarning(ScopeError):
    """A record file of the namespace cannot be read or parsed and was left out (``WARNING``)."""

    code = "SPEC_SCOPE_RECORD_INVALID"
    level = Level.WARNING
    fix = "Delete the record file in [TARGET] once its task is known to be finished (devkit spec scope sweep lists it)"


class ScopeJournalWarning(ScopeError):
    """The event journal could not be written (``WARNING``); the operation itself succeeded or failed as reported."""

    code = "SPEC_SCOPE_JOURNAL_UNAVAILABLE"
    level = Level.WARNING
    fix = "Make journal.jsonl in [TARGET] a writable file; the registry works without it"


class ScopeJournalLineWarning(ScopeError):
    """Lines of the event journal are not JSON events and were skipped (``WARNING``)."""

    code = "SPEC_SCOPE_JOURNAL_LINE_INVALID"
    level = Level.WARNING
    fix = "Remove or repair the lines named in [DETAIL] of journal.jsonl in [TARGET]"


class ScopeRegisterFailedWarning(ScopeError):
    """``devkit spec proposal handoff`` completed in the task worktree but registering its scope failed
    (``WARNING``)."""

    code = "SPEC_SCOPE_REGISTER_FAILED"
    level = Level.WARNING
    fix = "Fix the cause in [DETAIL], then run devkit spec scope register --spec <dir> in the worktree"
