# Recipe parameters reach the shell as positional arguments, so quoting survives ("$@").
set positional-arguments

# Print available commands
default:
    @just --list

# Create or update the environment (devkit comes from its GitHub main, pinned in uv.lock)
init:
    uv sync --no-active

# Run ruff format and lint with automatic fixes
lint:
    uv run --no-active ruff check --fix .
    uv run --no-active ruff format .

# Check linting and formatting without modifying files
lint-check:
    uv run --no-active ruff check .
    uv run --no-active ruff format --check .

# Run pyright static type checking over sources and tests
check:
    uv run --no-active pyright

# Run pytest
test *args:
    uv run --no-active pytest "$@"

# Run pytest with a coverage report
test-cov *args:
    uv run --no-active pytest --cov --cov-config=pyproject.toml "$@"

# Run the rule engine check (devkit rules check)
rules-check *args:
    uv run --no-active devkit rules check "$@"

# Everything CI runs
ci: lint-check check test rules-check

# Run a command against an unpushed devkit checkout at ../devkit, e.g. `just local-devkit pytest`
local-devkit *args:
    uv run --no-active --with-editable ../devkit/packages/devkit --with-editable ../devkit/packages/devkit-advisory "$@"
