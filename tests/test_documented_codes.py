"""Every advisory code devkit-spec defines is documented under ``docs/``: agents branch on codes, people look them up."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = re.compile(r"""\bcode\s*(?::\s*str\s*)?=\s*["']([A-Z][A-Z0-9_]+)["']""")


def test_every_code_is_documented() -> None:
    codes = {match.group(1) for path in (ROOT / "src").rglob("*.py") for match in CODE.finditer(path.read_text())}
    assert "SPEC_ID_UNRESOLVED" in codes  # the scan works
    documented = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "docs").rglob("*.md"))
    assert sorted(code for code in codes if f"`{code}`" not in documented) == []
