# Continuous Integration

What CI runs for devkit-spec and how a release reaches consumers. Deployment architecture: `ARCH-07-deployment`.

## 1. The CI Job

CI runs exactly what a contributor runs locally:

```bash
just ci        # lint-check, check (Pyright), test (pytest), rules-check (devkit rules check)
```

- **Runner**: one Linux job. The repository is private, so macOS runner minutes are avoided; nothing in the package
  is platform-specific (`py3-none-any`).
- **devkit**: `just init` installs it from the Git source pinned in `uv.lock` (`https://github.com/mjkimR/devkit.git`,
  public), so the job needs no second checkout.
- **Pull requests**: the governance check of a pull request judges the committed branch against its merge base:

  ```bash
  just rules-check --ci --base "$BASE_REF"   # default base: origin/main
  ```

  Check out enough history to reach the base; a missing ref fails rather than falling back.
- The job definition is not checked into this repository (there is no `.github/workflows/`).

## 2. Local Equivalent of the Gates

- `just ci` before a commit or pull request.
- `just rules-check --staged` evaluates exactly what is staged, as devkit's commit gate would.

## 3. Release

No release exists yet. Consumers install a wheel built from this repository (`uv build`) by path or URL:
`uv add --dev devkit devkit-spec` (`ARCH-07-deployment`). The package version is `pyproject.toml`'s `version` and the
bundle's `bundle.toml` `version`; `devkit spec --version` reports it.
