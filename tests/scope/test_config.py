from __future__ import annotations

from pathlib import Path

import pytest
from conftest import Write

from devkit_spec.config import ScopeConfig, read_spec_config
from devkit_spec.errors import SpecConfigError


def test_scope_defaults(workspace: Path) -> None:
    assert read_spec_config(workspace).scope == ScopeConfig(shared_path=None, namespace=None, timeout=10)


def test_scope_table(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", '[tool.spec.scope]\nshared_path = "~/scope"\nnamespace = "team.a"\ntimeout = 300\n')
    scope = read_spec_config(workspace).scope
    assert scope == ScopeConfig(shared_path=Path("~/scope").expanduser(), namespace="team.a", timeout=300)


@pytest.mark.parametrize(
    "table",
    [
        'shared_path = "relative/dir"',
        'shared_path = ""',
        "shared_path = 3",
        'namespace = ".hidden"',
        'namespace = "a/b"',
        'namespace = ""',
        "timeout = 0",
        "timeout = 301",
        "timeout = true",
        "timeout = 1.5",
        'other = "x"',
    ],
)
def test_invalid_scope_table(workspace: Path, write: Write, table: str) -> None:
    write(".devkit/config.toml", f"[tool.spec.scope]\n{table}\n")
    with pytest.raises(SpecConfigError):
        read_spec_config(workspace)


def test_scope_must_be_a_table(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", '[tool.spec]\nscope = "x"\n')
    with pytest.raises(SpecConfigError):
        read_spec_config(workspace)
