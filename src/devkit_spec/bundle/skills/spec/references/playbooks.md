# Operational playbooks (Tier 2)

Read this when the user asks for an operational procedure that is not standard feature development, such as onboarding, a weekly release, a database migration or incident recovery.

1. Use the `devkit-playbook` skill (`devkit playbook search "<query>"`) to find a matching playbook.
2. If a match is found, read the path the search gives (do not reconstruct it from a slug), announce `Activating playbook: <title> (<path>)`, and follow its steps.
3. If no match is found, proceed with general best-effort assistance, and note that this novel procedure can be recorded as feedback (`spec-feedback`) for later promotion into a playbook.
