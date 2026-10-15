# Continuous Integration

Configure a pull request job to check out the head with enough history to reach the base and run:

```sh
uv run devkit rules check --ci --base "$BASE_REF"
```

Set `BASE_REF` to the fetched target branch or its commit ID (default: `origin/main`). A missing ref fails rather than
silently falling back. The run evaluates the exact committed tree against its merge base, including the spec rules the
project deploys. Configure the job as required through your hosting provider's branch policy, decide whether tests
also evaluate a merge candidate, and do not expose deployment secrets to untrusted pull request jobs.

Locally, commits run through devkit's commit gate (installed by `uv run devkit sync`), whose `rules-check` gate runs
the rules on exactly what is committed, as `devkit rules check --staged` does; unstaged fixes do not count.

<!-- Add the project's build, test and deployment jobs below. -->
