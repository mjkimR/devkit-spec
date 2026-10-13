"""``[tool.spec]`` in devkit's commented config template reads back as ``read_spec_config``'s defaults."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from conftest import Write
from devkit.core.config_template import check_tables, render_tool_template, uncomment

from devkit_spec.config import Namespace, ScopeConfig, SpecConfig, read_spec_config, template


def test_the_template_renders() -> None:
    assert [table.path for table in check_tables(template())] == [(), ("namespaces",), ("scope",)]


def test_uncommented_defaults_are_the_defaults(workspace: Path, write: Write) -> None:
    """The keys with a default, uncommented, configure what an empty ``[tool.spec]`` does."""
    tables = [
        replace(table, keys=tuple(key for key in table.keys if key.default is not None))
        for table in template()
        if not table.array
    ]
    write(".devkit/config.toml", uncomment(render_tool_template("spec", [table for table in tables if table.keys])))
    assert read_spec_config(workspace) == SpecConfig()


def test_uncommented_examples_are_valid(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", uncomment(render_tool_template("spec", template())))
    config = read_spec_config(workspace)
    assert config.namespaces == (Namespace("api", "services/api"),)
    assert config.scope == ScopeConfig(shared_path=Path("/srv/devkit-spec-scope"), namespace="team", timeout=10)
