"""``RULE-id-convention``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from pathlib import Path

import pytest
from devkit.rules import RuleContext, Violation, evaluate_rules
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def _namespaces(*names: str) -> str:
    """``.devkit/config.toml`` registering a namespace per name, with source path ``packages/<name>``."""
    return "".join(f'[[tool.spec.namespaces]]\nname = "{name}"\npath = "packages/{name}"\n\n' for name in names)


def _has(violations: list[Violation], file: str, fragment: str) -> bool:
    return any(v.file == file and fragment in v.message for v in violations)


def _missing(violations: list[Violation], expected: dict[str, str]) -> list[tuple[str, str]]:
    return [(file, fragment) for file, fragment in expected.items() if not _has(violations, file, fragment)]


def _read(tmp_path: Path, path: str) -> str:
    return (tmp_path / path).read_bytes().decode("utf-8")


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("Example `US-010` and ``ADR-0006 ` quoted``.\n", 0),
        ("Example `US-010\nADR-0006` ends.\n", 0),
        ("````md\nUS-010\n```\nADR-0006\n````\nSee US-010\n", 6),
        ("~~~md\nUS-010\n~~~\nSee US-010\n", 4),
        ("<!-- US-010\nADR-0006 -->\n", 0),
        ("    US-010\n", 0),
        ("Example `US-010`\nSee ADR-0006\n", 2),
        ("Example `US-010`\n[old](US-010.md)\n", 2),
        ("[US-010](old.md)\n", 1),
        ("---\nrelated_stories:\n    - US-010\n---\n`ADR-0006`\n", 3),
        ("Unclosed `US-010\n", 1),
        ("~~~md\r\nUS-010\r\n~~~\r\nSee ADR-0006\r\n", 4),
    ],
    ids=[
        "inline",
        "multiline-inline",
        "backtick-fence",
        "tilde-fence",
        "comment",
        "indented-code",
        "prose",
        "link",
        "link-label",
        "frontmatter",
        "unclosed-inline",
        "crlf",
    ],
)
def test_references_skip_examples(tmp_path: Path, text: str, line: int) -> None:
    write_files(tmp_path, {"specs/2026-10/20261006-example-notes/notes.md": text})
    assert [v.line for v in check(RULE, tmp_path)] == ([line] if line else [])


def _fixture() -> dict[str, str]:
    files: dict[str, str] = {}
    files["docs/decisions/README.md"] = "# ADR ledger\nREADME files are not identifier targets.\n"
    files["docs/decisions/2026-10/20261003-alpha.md"] = "---\nid: ADR-alpha\nstatus: accepted\n---\n\n# [ADR-alpha] A\n"
    files["docs/decisions/2026-11/20261101-alpha.md"] = "---\nid: ADR-alpha\nstatus: accepted\n---\n\n# Alpha again\n"
    files["docs/decisions/ADR-0001-legacy.md"] = "---\nid: ADR-legacy\nstatus: accepted\n---\n\n# Legacy\n"
    files["docs/decisions/2026-10/20261004-beta.md"] = (
        "---\nid: ADR-wrong\nstatus: accepted\n---\n\n# [ADR-beta-old] Beta\n"
    )
    files["docs/decisions/2026-09/20261005-gamma.md"] = "---\nid: ADR-gamma\nstatus: accepted\n---\n\n# Gamma\n"
    files["specs/2026-10/20261005-delta/spec.md"] = (
        "---\nid: SPEC-20261005-delta\nstatus: planned\n---\n\n# [SPEC-20261005] D\n"
    )
    files["specs/2026-10/20261005-delta/plan.md"] = (
        "---\nid: PLAN-delta\nspec: SPEC-delta\nstatus: draft\n---\n\n# Technical Plan: [SPEC-delta] Delta\n"
    )
    files["specs/2026-10/20261005-delta/tasks.md"] = (
        "---\nid: TASKS-delta\n---\n\n# Task Breakdown: [TASKS-delta] Delta\n"
    )
    files["specs/2026-10/20261005-delta/reconcile.md"] = (
        "---\nreconcile_id: REC-other\nfeature: 2026-10/20261005-delta\nstatus: resolved\n---\n\n# Reconcile\n"
    )
    files["specs/2026-10/20261007-epsilon/reconcile.md"] = (
        "---\nfeature: 2026-10/20261007-epsilon\nstatus: resolved\n---\n\n# Reconcile without reconcile_id\n"
    )
    files["specs/2026-10/20261005-delta/notes.md"] = "ADR-0002 in a file that is not an identifier target\n"
    files["docs/capabilities/x/CAP-X-alpha.md"] = (
        "---\nid: CAP-X-alpha\narea: x\nstatus: active\n---\n\n# [CAP-X-alpha] X\n\n"
        "See ADR-0006 and SPEC-20261006-foo and PADR-0001.\n"
    )
    files["docs/materials/2026-10/old.md"] = "ADR-0001 historical material is ignored\n"
    return files


def test_dated_partitions(tmp_path: Path) -> None:
    write_files(tmp_path, _fixture())
    violations = check(RULE, tmp_path)
    assert not _missing(
        violations,
        {
            "docs/decisions/ADR-0001-legacy.md": "Invalid partition path",
            "docs/decisions/2026-10/20261003-alpha.md": "duplicated across",
            "docs/decisions/2026-11/20261101-alpha.md": "duplicated across",
            "docs/decisions/2026-10/20261004-beta.md": 'Frontmatter id is "ADR-wrong"',
            "docs/decisions/2026-09/20261005-gamma.md": "month partition",
            "specs/2026-10/20261005-delta/spec.md": 'Frontmatter id is "SPEC-20261005-delta"',
            "specs/2026-10/20261005-delta/reconcile.md": 'Frontmatter reconcile_id is "REC-other"',
            "specs/2026-10/20261007-epsilon/reconcile.md": 'Frontmatter reconcile_id is ""',
            "specs/2026-10/20261005-delta/notes.md": '"ADR-0002"',
        },
    )
    assert _has(violations, "docs/decisions/2026-10/20261004-beta.md", "Heading token [ADR-beta-old]")
    assert _has(violations, "specs/2026-10/20261005-delta/spec.md", "Heading token [SPEC-20261005]")
    capability = [
        (line, message) for file, line, message in _found(violations) if file.startswith("docs/capabilities/")
    ]
    assert capability == [
        (9, 'Date- or number-based identifier reference "ADR-0006"'),
        (9, 'Date- or number-based identifier reference "SPEC-20261006-foo"'),
        (9, 'Date- or number-based identifier reference "PADR-0001"'),
    ]
    flagged = {v.file for v in violations}
    assert not flagged & {
        "docs/decisions/README.md",
        "docs/materials/2026-10/old.md",
        "specs/2026-10/20261005-delta/plan.md",
        "specs/2026-10/20261005-delta/tasks.md",
    }


def test_only_targets_are_reported(tmp_path: Path) -> None:
    write_files(tmp_path, _fixture())
    violations = check(RULE, tmp_path, targets=["docs/capabilities/x/CAP-X-alpha.md"])
    assert {v.file for v in violations} == {"docs/capabilities/x/CAP-X-alpha.md"} and len(violations) == 3


def test_fix_is_idempotent_and_honours_dry_run(tmp_path: Path) -> None:
    write_files(tmp_path, _fixture())
    ctx = RuleContext(workspace_root=tmp_path, fix=True, dry_run=True)
    assert evaluate_rules(ctx, [RULE]).errors == []
    assert "id: SPEC-20261005-delta" in _read(tmp_path, "specs/2026-10/20261005-delta/spec.md")

    check(RULE, tmp_path, fix=True)
    spec = _read(tmp_path, "specs/2026-10/20261005-delta/spec.md")
    assert "id: SPEC-delta\n" in spec and "# [SPEC-delta] D" in spec
    beta = _read(tmp_path, "docs/decisions/2026-10/20261004-beta.md")
    assert "id: ADR-beta\n" in beta and "# [ADR-beta] Beta" in beta
    assert "reconcile_id: REC-delta\n" in _read(tmp_path, "specs/2026-10/20261005-delta/reconcile.md")
    epsilon = _read(tmp_path, "specs/2026-10/20261007-epsilon/reconcile.md")
    assert epsilon.startswith("---\nreconcile_id: REC-epsilon\nfeature:")

    files = [p for p in sorted(tmp_path.rglob("*.md")) if ".devkit" not in p.parts]
    before = {p: p.read_text() for p in files}
    violations = check(RULE, tmp_path, fix=True)
    assert {p: p.read_text() for p in files} == before
    assert [v for v in violations if v.fixable] == []


def _feedback_fixture() -> dict[str, str]:
    files: dict[str, str] = {}

    def fb(document_id: str, heading: str) -> str:
        return f"---\nid: {document_id}\nstatus: open\n---\n\n# {heading}\n"

    files["specs/2026-10/20261005-delta/spec.md"] = "---\nid: SPEC-delta\nstatus: planned\n---\n\n# [SPEC-delta] D\n"
    files["specs/2026-10/20261005-delta/feedback/good-one.md"] = fb("FB-good-one", "[FB-good-one] ok")
    files["specs/2026-10/feedback/20261006-lane-one.md"] = fb("FB-lane-one", "[FB-lane-one] ok")
    files["specs/2026-10/20261005-delta/feedback/wrong-id.md"] = fb("FB-other", "[FB-wrong-id] bad")
    files["specs/2026-10/20261005-delta/feedback/bad-h1.md"] = fb("FB-bad-h1", "[SPEC-delta] bad heading")
    files["specs/2026-10/20261005-delta/feedback/20261005-dated.md"] = fb("FB-dated", "[FB-dated] bad")
    files["specs/2026-10/feedback/nodate.md"] = fb("FB-nodate", "[FB-nodate] bad")
    files["specs/feedback/root-level.md"] = fb("FB-root-level", "[FB-root-level] bad")
    files["specs/2026-10/20261005-delta/notes.md"] = "see FB-20261006-dated-ref in prose\n"
    # The same feedback slug in another bundle is fine: feedback IDs are unique per bundle.
    files["specs/2026-10/20261008-eta/spec.md"] = "---\nid: SPEC-eta\nstatus: planned\n---\n\n# [SPEC-eta] Eta\n"
    files["specs/2026-10/20261008-eta/feedback/good-one.md"] = fb("FB-good-one", "[FB-good-one] ok")
    return files


def test_feedback(tmp_path: Path) -> None:
    write_files(tmp_path, _feedback_fixture())
    violations = check(RULE, tmp_path)
    flagged = {v.file for v in violations}
    assert not flagged & {
        "specs/2026-10/20261005-delta/feedback/good-one.md",
        "specs/2026-10/feedback/20261006-lane-one.md",
        "specs/2026-10/20261008-eta/feedback/good-one.md",
    }
    assert not _missing(
        violations,
        {
            "specs/2026-10/20261005-delta/feedback/wrong-id.md": 'Frontmatter id is "FB-other"',
            "specs/2026-10/20261005-delta/feedback/bad-h1.md": "Heading token [SPEC-delta]",
            "specs/2026-10/20261005-delta/feedback/20261005-dated.md": "without a date",
            "specs/2026-10/feedback/nodate.md": "{YYYYMMDD}-{slug}",
            "specs/feedback/root-level.md": "Feedback must be stored at",
            "specs/2026-10/20261005-delta/notes.md": "FB-20261006-dated-ref",
        },
    )

    check(RULE, tmp_path, fix=True)
    assert "id: FB-wrong-id\n" in _read(tmp_path, "specs/2026-10/20261005-delta/feedback/wrong-id.md")
    assert "# [FB-bad-h1] bad heading" in _read(tmp_path, "specs/2026-10/20261005-delta/feedback/bad-h1.md")


def _living_spec_fixture() -> dict[str, str]:
    files: dict[str, str] = {}

    def doc(document_id: str, heading: str, *, area: str | None = None, body: str = "") -> str:
        area_line = f"area: {area}\n" if area is not None else ""
        return f"---\nid: {document_id}\ntitle: T\n{area_line}status: active\n---\n\n# {heading}\n{body}"

    # valid documents
    files["docs/capabilities/README.md"] = "# Capabilities\n"
    files["docs/capabilities/harness/CAP-HARN-context-pack-slicing.md"] = doc(
        "CAP-HARN-context-pack-slicing",
        "[CAP-HARN-context-pack-slicing] Pack",
        area="harness",
        body="\nSee US-010 and ARCH-06-runtime-view and US-init-project-docs and CAP-GOV-rule-verification.\n",
    )
    files["docs/stories/README.md"] = "# Stories\n"
    files["docs/stories/delivery/US-reconcile-feature.md"] = doc(
        "US-reconcile-feature", "[US-reconcile-feature] Reconcile", area="delivery"
    )
    files["docs/architecture/README.md"] = "# Architecture\n"
    files["docs/architecture/ARCH-01-introduction-and-goals.md"] = doc(
        "ARCH-01-introduction-and-goals",
        "[ARCH-01-introduction-and-goals] Intro",
        body="\nARCH-05-1-containers and ARCH-11-risks are fine.\n",
    )
    files["docs/architecture/ARCH-05-1-containers.md"] = doc("ARCH-05-1-containers", "[ARCH-05-1-containers] C")
    files["docs/architecture/ARCH-search-pipeline.md"] = doc(
        "ARCH-search-pipeline", "Search", body="\nSee ARCH-06 for the runtime view.\n"
    )
    # invalid documents
    files["docs/capabilities/harness/CAP-HARN-001-legacy.md"] = doc("CAP-HARN-001", "Legacy", area="harness")
    files["docs/capabilities/harness/CAP-HARN-wrong-area.md"] = doc("CAP-HARN-wrong-area", "Wrong", area="governance")
    files["docs/capabilities/harness/CAP-HARN-wrong-id.md"] = doc(
        "CAP-HARN-other", "[CAP-HARN-other] Wrong id", area="harness"
    )
    files["docs/capabilities/CAP-FLAT-no-area.md"] = doc("CAP-FLAT-no-area", "Flat")
    files["docs/stories/US-flat-story.md"] = doc("US-flat-story", "Flat")
    files["docs/stories/governance/US-deterministic-rule-verification.md"] = (
        "---\nid: US-003\ntitle: Rules\nactor: agent\nstatus: active\n---\n\n# [US-003] Rules\n"
    )
    files["docs/stories/a/US-same-slug.md"] = doc("US-same-slug", "A", area="a")
    files["docs/stories/b/US-same-slug.md"] = doc("US-same-slug", "B", area="b")
    files["docs/architecture/ARCH-13-extra.md"] = doc("ARCH-13-extra", "Extra")
    files["docs/architecture/ARCH-09-decisions.md"] = doc("ARCH-09-decisions", "Decisions")
    files["docs/architecture/ARCH-07.md"] = doc("ARCH-07", "Bare")
    files["docs/architecture/ARCH-07-deployment.md"] = "# [ARCH-07-deployment] No frontmatter\n"
    # references
    files["specs/2026-10/20261005-delta/reconcile.md"] = (
        "---\nreconcile_id: REC-delta\nstatus: resolved\n---\n\n# Reconcile\n\n"
        "Touched CAP-HARN-007 and stories/US-002-reconcile.md.\n"
    )
    files["docs/materials/2026-10/old.md"] = "US-010 CAP-HARN-007 ARCH-06 are ignored in materials\n"
    return files


def test_living_spec(tmp_path: Path) -> None:
    write_files(tmp_path, _living_spec_fixture())
    violations = check(RULE, tmp_path)
    story = "docs/stories/governance/US-deterministic-rule-verification.md"
    assert not _missing(
        violations,
        {
            "docs/capabilities/harness/CAP-HARN-001-legacy.md": "not a sequence number",
            "docs/capabilities/harness/CAP-HARN-wrong-area.md": (
                'Frontmatter area is "governance" but the directory requires "harness"'
            ),
            "docs/capabilities/harness/CAP-HARN-wrong-id.md": (
                'Frontmatter id is "CAP-HARN-other" but the path requires "CAP-HARN-wrong-id"'
            ),
            "docs/capabilities/CAP-FLAT-no-area.md": "docs/capabilities/{area}/CAP-{AREA}-{slug}.md",
            "docs/stories/US-flat-story.md": "docs/stories/{area}/US-{slug}.md",
            story: 'Frontmatter id is "US-003"',
            "docs/stories/a/US-same-slug.md": "duplicated across",
            "docs/stories/b/US-same-slug.md": "duplicated across",
            "docs/architecture/ARCH-13-extra.md": 'arc42 chapter "13"',
            "docs/architecture/ARCH-09-decisions.md": 'arc42 chapter "09"',
            "docs/architecture/ARCH-07.md": "kebab-case slug",
            "docs/architecture/ARCH-07-deployment.md": "Missing YAML frontmatter; expected id: ARCH-07-deployment",
            "specs/2026-10/20261005-delta/reconcile.md": '"CAP-HARN-007"',
            "docs/architecture/ARCH-search-pipeline.md": '"ARCH-06"',
        },
    )
    assert _has(violations, story, 'Frontmatter area is "" but the directory requires "governance"')
    assert _has(violations, story, "Heading token [US-003]")
    assert _has(violations, "specs/2026-10/20261005-delta/reconcile.md", '"US-002"')
    slicing = [v.message for v in violations if v.file == "docs/capabilities/harness/CAP-HARN-context-pack-slicing.md"]
    assert slicing == ['Date- or number-based identifier reference "US-010"']
    flagged = {v.file for v in violations}
    assert not flagged & {
        "docs/stories/delivery/US-reconcile-feature.md",
        "docs/architecture/ARCH-01-introduction-and-goals.md",
        "docs/architecture/ARCH-05-1-containers.md",
        "docs/capabilities/README.md",
        "docs/stories/README.md",
        "docs/architecture/README.md",
        "docs/materials/2026-10/old.md",
    }
    for v in violations:
        if v.file in ("docs/capabilities/harness/CAP-HARN-wrong-area.md", story):
            assert v.fixable == v.message.startswith(("Frontmatter", "Heading token")), v.message


def test_living_spec_fix(tmp_path: Path) -> None:
    write_files(tmp_path, _living_spec_fixture())
    untouched = [
        "docs/stories/US-flat-story.md",
        "docs/stories/a/US-same-slug.md",
        "docs/stories/b/US-same-slug.md",
        "docs/architecture/ARCH-07-deployment.md",
    ]
    before = {path: _read(tmp_path, path) for path in untouched}
    violations = check(RULE, tmp_path, fix=True)
    story = _read(tmp_path, "docs/stories/governance/US-deterministic-rule-verification.md")
    assert story.startswith("---\nid: US-deterministic-rule-verification\narea: governance\ntitle: Rules\n")
    assert "# [US-deterministic-rule-verification] Rules" in story
    area = _read(tmp_path, "docs/capabilities/harness/CAP-HARN-wrong-area.md")
    assert "\narea: harness\n" in area and "governance" not in area
    assert "id: CAP-HARN-wrong-id\n" in _read(tmp_path, "docs/capabilities/harness/CAP-HARN-wrong-id.md")
    assert {path: _read(tmp_path, path) for path in untouched} == before
    assert [v for v in violations if v.fixable and not v.fixed] == []


def test_fix_keeps_crlf_and_quoted_values(tmp_path: Path) -> None:
    path = "docs/decisions/2026-10/20261004-beta.md"
    check(
        RULE, tmp_path, {path: '---\r\nid: "ADR-old"\r\nstatus: accepted\r\n---\r\n\r\n# `ADR-old` Beta\r\n'}, fix=True
    )
    assert _read(tmp_path, path) == "---\r\nid: ADR-beta\r\nstatus: accepted\r\n---\r\n\r\n# `ADR-beta` Beta\r\n"
    assert check(RULE, tmp_path) == []


def test_completed_bundles_are_checked_only_when_targeted(tmp_path: Path) -> None:
    spec = "specs/2026-10/20261001-done/spec.md"
    files = {
        spec: "---\nid: SPEC-old\nstatus: completed\n---\n\n# Done\n\nSee ADR-0001.\n",
        "specs/2026-10/20261001-done/notes.md": "See US-001.\n",
    }
    assert check(RULE, tmp_path, files) == []
    assert check(RULE, tmp_path, fix=True) == []
    assert "id: SPEC-old" in _read(tmp_path, spec)
    assert [v.message for v in check(RULE, tmp_path, targets=[spec])] == [
        'Frontmatter id is "SPEC-old" but the path requires "SPEC-done"',
        'Date- or number-based identifier reference "ADR-0001"',
    ]


def _living(document_id: str, area: str = "") -> str:
    area_line = f"area: {area}\n" if area else ""
    return f"---\nid: {document_id}\n{area_line}title: T\nstatus: active\n---\n# T\n"


def test_namespace_docs_roots_follow_the_living_spec_conventions(tmp_path: Path) -> None:
    root = "docs/packages/api"
    files = {
        ".devkit/config.toml": _namespaces("api"),
        f"{root}/capabilities/auth/CAP-AUTH-login.md": _living("CAP-AUTH-login", "auth"),
        f"{root}/stories/auth/US-sign-in.md": _living("US-sign-in", "billing"),
        f"{root}/architecture/ARCH-05-building-blocks.md": _living("ARCH-05-other"),
        f"{root}/capabilities/CAP-AUTH-flat.md": _living("CAP-AUTH-flat", "auth"),
        f"{root}/capabilities/auth/README.md": "# Capabilities\n",
        "docs/capabilities/auth/CAP-AUTH-login.md": _living("CAP-AUTH-login", "auth"),
        "docs/packages/web/capabilities/CAP-WEB-unregistered.md": "# not a namespace root\n",
        f"{root}/materials/notes.md": "Old US-010 survey\n",
        f"{root}/notes.md": "See US-010\n",
    }
    violations = check(RULE, tmp_path, files)
    assert sorted((v.file, v.message) for v in violations if not v.fixed) == [
        (
            "docs/capabilities/auth/CAP-AUTH-login.md",
            f"Identifier CAP-AUTH-login is duplicated across docs/capabilities/auth/CAP-AUTH-login.md,"
            f" {root}/capabilities/auth/CAP-AUTH-login.md",
        ),
        (
            f"{root}/architecture/ARCH-05-building-blocks.md",
            'Frontmatter id is "ARCH-05-other" but the path requires "ARCH-05-building-blocks"',
        ),
        (
            f"{root}/capabilities/CAP-AUTH-flat.md",
            "Invalid partition path: Capability must be stored at"
            f" {root}/capabilities/{{area}}/CAP-{{AREA}}-{{slug}}.md",
        ),
        (
            f"{root}/capabilities/auth/CAP-AUTH-login.md",
            f"Identifier CAP-AUTH-login is duplicated across docs/capabilities/auth/CAP-AUTH-login.md,"
            f" {root}/capabilities/auth/CAP-AUTH-login.md",
        ),
        (f"{root}/notes.md", 'Date- or number-based identifier reference "US-010"'),
        (f"{root}/stories/auth/US-sign-in.md", 'Frontmatter area is "billing" but the directory requires "auth"'),
    ]
    area = next(v for v in violations if v.message.startswith("Frontmatter area"))
    assert f"move the file to {root}/stories/billing/" in area.remediation

    fixed = check(RULE, tmp_path, targets=[f"{root}/stories/auth/US-sign-in.md"], fix=True)
    assert _found(fixed) == [] and "area: auth\n" in _read(tmp_path, f"{root}/stories/auth/US-sign-in.md")


def test_namespace_docs_roots_need_registration(tmp_path: Path) -> None:
    assert check(RULE, tmp_path, {"docs/packages/api/capabilities/CAP-AUTH-flat.md": "# flat\n"}) == []
    assert [v.file for v in check(RULE, tmp_path, {".devkit/config.toml": _namespaces("api")})] == [
        "docs/packages/api/capabilities/CAP-AUTH-flat.md"
    ]


def test_malformed_namespace_config_fails_the_run(tmp_path: Path) -> None:
    write_files(tmp_path, {".devkit/config.toml": '[[tool.spec.namespaces]]\nname = "global"\npath = "x"\n'})
    result = evaluate_rules(RuleContext(workspace_root=tmp_path), [RULE])
    assert [error.code for error in result.errors] == ["RULES_EXECUTION_FAILED"]
    assert "tool.spec.namespaces[0]" in str(result.errors[0])
