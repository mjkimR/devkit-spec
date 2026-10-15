# Spawning a role on each host

Read this in Step 3 when you spawn an isolated subagent; skip it when the main session substitutes. `devkit sync` renders each role contract into the selected agents' native agent directories; `devkit status` reports a missing or stale one and `devkit sync` restores it before delegating.

| Host | Mechanism | Projected file |
| :--- | :--- | :--- |
| Claude Code | The subagent named `<role>` (Agent tool or `@agent-<role>`) | `.claude/agents/<role>.md` |
| Codex CLI | `collaboration.spawn_agent` with `agent_type: <role>` | `.codex/agents/<role>.toml` |
| Antigravity | `invoke_subagent` with the role name | `.agents/agents/<role>.md` |

- **Session root**: a host loads projected roles from the directory its session started in. A session started above the project (a parent workspace) has no `<role>` subagent: spawn a generic subagent, tell it to read the managed contract (`.devkit/managed/spec/subagents/<role>.md`) and follow it, and report the call as `emulated`.
- **Codex trust**: the role appears only when the project root is registered as trusted in `~/.codex/config.toml` (`[projects."<absolute git root>"] trust_level = "trusted"`). Without it the spawn tool has no `agent_type` and a plain spawn carries no role instructions: stop and ask the user to register the root.
