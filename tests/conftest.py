from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

Write = Callable[[str, str], Path]


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / ".devkit").mkdir()
    return tmp_path


@pytest.fixture
def write(workspace: Path) -> Write:
    """Write ``text`` to the workspace-relative ``path``, creating its directories."""

    def write(path: str, text: str) -> Path:
        target = workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    return write
