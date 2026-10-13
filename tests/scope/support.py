from __future__ import annotations

import os
import subprocess
from pathlib import Path

from devkit_spec.scope import Granularity, LocalRegistry, Record, ScopePath, Source, Stage

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}
SPEC = "specs/2026-10/20261001-s"
CAP_A = "docs/capabilities/x/CAP-X-a.md"
CAP_B = "docs/capabilities/x/CAP-X-b.md"
CAP_EMPTY = "docs/capabilities/x/CAP-X-empty.md"
CAP_PLANNED = "docs/capabilities/x/CAP-X-planned.md"


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, env={**os.environ, **GIT_ENV}, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def write(root: Path, path: str, text: str) -> Path:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def make_repo(root: Path) -> Path:
    """A committed Git repository with Living Spec documents, two proposals and a spec bundle (specrig's fixture)."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main")
    write(root, ".devkit/config.toml", "")
    write(root, CAP_A, "---\nid: CAP-X-a\nstatus: active\nentrypoints:\n  - src/a/\n  - src/shared.py\n---\n")
    write(root, CAP_B, "---\nid: CAP-X-b\nstatus: active\nentrypoints:\n  - src/b/b.py\n---\n")
    write(root, CAP_EMPTY, "---\nid: CAP-X-empty\nstatus: active\n---\n")
    write(root, "docs/decisions/ADR-x.md", "---\nid: ADR-x\n---\n")
    write(root, "src/a/a.py", "a = 1\n")
    write(root, "src/b/b.py", "b = 1\n")
    write(root, "src/shared.py", "s = 1\n")
    write(root, "docs/proposals/PROP-one/proposal.md", "---\nid: PROP-one\nstatus: draft\n---\n")
    write(
        root,
        "docs/proposals/PROP-one/target-docs.md",
        f"---\nid: PROP-one-target\ntargets:\n  - file: {CAP_A}\n  - file: {CAP_EMPTY}\n  - file: {CAP_PLANNED}\n"
        "  - file: docs/decisions/ADR-x.md\n---\n",
    )
    write(root, "docs/proposals/PROP-two/proposal.md", "---\nid: PROP-two\nstatus: draft\n---\n")
    write(
        root,
        "docs/proposals/PROP-two/target-docs.md",
        f"---\nid: PROP-two-target\ntargets:\n  - file: {CAP_B}\n  - file: {CAP_PLANNED}\n---\n",
    )
    write(root, "docs/proposals/PROP-bare/proposal.md", "---\nid: PROP-bare\nstatus: draft\n---\n")
    write(root, f"{SPEC}/spec.md", "---\nid: SPEC-s\nstatus: in-progress\n---\n")
    write(
        root,
        f"{SPEC}/tasks.md",
        "- [ ] **Task 1**: t\n  - **_Boundary**: `src/a/`, `src/b/`, N/A, `docs/capabilities/`, `src/**`\n"
        "  - _Requirements: AC-01_\n",
    )
    write(
        root,
        f"{SPEC}/reconcile.md",
        f"---\nreconcile_id: REC-s\nstatus: pending\ntargets:\n  - file: {CAP_A}\n    resolution: modified\n"
        f"  - file: {CAP_B}\n    resolution: waived\n    rationale: not touched by this change at all\n---\n",
    )
    write(
        root,
        f"{SPEC}/target-docs.md",
        f"---\nid: SPEC-s-target\ntargets:\n  - file: {CAP_A}\n  - file: {CAP_EMPTY}\n---\n",
    )
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    return root


def record(task: str, worktree: str, namespace: str = "ns", hostname: str = "host-a") -> Record:
    return Record(
        namespace=namespace,
        task_id=task,
        worktree=worktree,
        hostname=hostname,
        scopes=(ScopePath(f"src/{task}", Granularity.DIR, Source.DECLARED_CODE, Stage.SPEC),),
    )


def registry(shared: Path, **kwargs: object) -> LocalRegistry:
    return LocalRegistry(shared, hostname="host-a", **kwargs)  # type: ignore[arg-type]
