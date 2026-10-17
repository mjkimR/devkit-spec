# Codex native integration confirmation spike

Purpose: retain evidence for `SPEC-hook-driven-integration-cleanup` and distinguish observed UI/hook behavior from
unverified execution behavior. Collected 2026-10-17 from a separate interactive Codex CLI session and local artifacts.

## Environment and setup

- Installed CLI: `codex-cli 0.163.0`.
- Disposable Git project: `/tmp/devkit-codex-integration-spike.lGHXLf`.
- Launcher: `bash /tmp/devkit-codex-integration-spike.lGHXLf/start.sh`.
- Launcher uses `--no-daemon`, workspace-write sandbox, on-request execution approval and the user reviewer.
- A stdio Python MCP server is configured through invocation-local overrides. It advertises one
  `confirm_integration_preview` tool. No existing repository or user configuration was edited.
- The tool sends `elicitation/create` with a boolean `approve` field whose default is false. Only `action=accept`
  together with `approve=true` authorizes simulated results. The request has fixed demo branches, a placeholder
  source SHA and `push=false`; there is no real integration executor.
- Project `.codex/hooks.json` configures metadata-only lifecycle observation. Project/hook trust is separate from
  integration confirmation. Actual trust interactions were not independently recorded.

## Interactive observations

The interactive client displayed the native confirmation UI. Persisted results independently establish:

| Case | Raw UI action | Tool result | Steps | Actual mutations |
| :--- | :--- | :--- | :--- | :--- |
| Affirmative approval | `accept` | `simulated`, authority `mcp-elicitation` | All simulated | None |
| Non-approval submission | `accept` | `cancelled`, authority `none` | All `not-run` | None |

The second result is a submission without affirmative authorization. It does not establish a native `decline` or
`cancel` action: its raw `ui_action` is `accept`, and the prototype requires the boolean as well. Explicit decline
and cancel have synthetic protocol coverage only.

Raw tool results, copied without modification:

- [Approved dry run](confirmation-6e35be5db55b48bc9603ad1d50479a43.json)
- [Non-approved dry run](confirmation-e550c506484248cf9c7671f92cef92fa.json)

The fixture log contains the following events across the two turns. These counts come from the actual log, not a
synthetic test. Session/turn identifiers, prompts, transcripts and command arguments are omitted from this report.

| Event | Count |
| :--- | :--- |
| `PostToolUse` | 2 |
| `PreToolUse` | 2 |
| `SessionStart` | 1 |
| `Stop` | 2 |
| `UserPromptSubmit` | 2 |

No `PermissionRequest` event is present. This absence does not demonstrate approval-free execution for a real
merge or cleanup. Hooks observed the MCP calls; they did not dispatch an integration executor.

## Local checks

- `python3 /tmp/devkit-codex-integration-spike.lGHXLf/check.py`: seven synthetic MCP protocol cases passed:
  affirmative accept, accept without approval, decline, cancel, client error, accept with missing content, and
  client without form capability. Each ran against a separate temporary server copy.
- `bash -n /tmp/devkit-codex-integration-spike.lGHXLf/start.sh`: passed.
- `codex ... mcp get integration_spike`: reports enabled stdio server with the expected Python command and path;
  configuration inspection alone is not connection or UI evidence.
- A synthetic hook event confirmed that the logger excludes prompt and command content.

## Limits and pre-accept design findings

No real Git merge, push, branch deletion, worktree removal, post-finish extension, policy readiness check, stale
request validation, duplicate suppression, concurrent execution, restart recovery or auto dispatch was exercised.
Prompt counts and real mutation authority cannot be inferred from these results. The prototype is not a released
adapter and its approval boolean is an elicited response inside the server, not an acceptable caller-supplied flag.

Inspection of the sibling devkit public `finish` export and its implementation/docstring found that `merge=True`
fast-forwards and pushes the configured upstream. A local-only executor therefore needs an explicit public
no-network execution contract; an upstream-free fixture alone would conceal that production difference. The
existing implementation also permits merge progress before worktree removal reports dirty state, so the new
request/preflight and partial-result contract must specify what happens at each mutation boundary.

The direction can proceed to implementation without proving every host permission remedy first. Before
`plan-accept`, settle adapter/package ownership, authority binding, the public local-only operation, Unit/session
readiness and stale-request/retry semantics. Broad host support, automatic policy dispatch and remote merge paths
remain separately tracked scope, not claims made by this spike.

## Artifact provenance and reproduction limit

The raw results above are durable repository evidence. Prototype sources remain temporary local artifacts and are
not installed bundle assets; after `/tmp` cleanup the launcher is unavailable. Development must supply a maintained
adapter and real-operation tests. Source hashes at collection time:

- `server.py`: `b1b223c8b4f72605bbe50e24bbc95bc9c3589b8fcc6ad00e574bcfb2f77cf6d1`
- `hook.py`: `39682fe3418b3f0a312aaf6efe70710982e0405b001743365878624709cd7af6`
- `start.sh`: `f64eb87aaecc5f974301fa94247d7c8f497ed27eb1d69a61f51fabc089fc0e1d`
- `check.py`: `c2aad8924bddda79287c06b7db390d9093b36796c961cf0c265db936a5545c93`

## Primary references

- [Codex Hooks](https://learn.chatgpt.com/docs/hooks): project/user hook configuration, trust and event contracts.
- [Codex App Server](https://learn.chatgpt.com/docs/app-server): native MCP elicitation request/response transport.

The references establish documented mechanisms. The observations above establish only the recorded installed-client
behavior and do not imply identical behavior in other clients or versions.
