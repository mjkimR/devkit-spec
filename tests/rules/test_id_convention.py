from __future__ import annotations

from pathlib import Path

import pytest
from conftest import Write
from devkit.rules import RuleContext, Violation, evaluate_rules
from rules.support import found, run

from devkit_spec.rules.id_convention import IdConventionRule

RULE = IdConventionRule()


def _has(violations: list[Violation], file: str, fragment: str) -> bool:
    return any(v.file == file and fragment in v.message for v in violations)


def _missing(violations: list[Violation], expected: dict[str, str]) -> list[tuple[str, str]]:
    return [(file, fragment) for file, fragment in expected.items() if not _has(violations, file, fragment)]


def _read(workspace: Path, path: str) -> str:
    return (workspace / path).read_bytes().decode("utf-8")


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
def test_references_skip_examples(workspace: Path, write: Write, text: str, line: int) -> None:
    write("specs/2026-10/20261006-example-notes/notes.md", text)
    assert [v.line for v in run(RULE, workspace)] == ([line] if line else [])


def _fixture(write: Write) -> None:
    write("docs/decisions/README.md", "# ADR ledger\nREADME files are not identifier targets.\n")
    write("docs/decisions/2026-10/20261003-alpha.md", "---\nid: ADR-alpha\nstatus: accepted\n---\n\n# [ADR-alpha] A\n")
    write("docs/decisions/2026-11/20261101-alpha.md", "---\nid: ADR-alpha\nstatus: accepted\n---\n\n# Alpha again\n")
    write("docs/decisions/ADR-0001-legacy.md", "---\nid: ADR-legacy\nstatus: accepted\n---\n\n# Legacy\n")
    write(
        "docs/decisions/2026-10/20261004-beta.md",
        "---\nid: ADR-wrong\nstatus: accepted\n---\n\n# [ADR-beta-old] Beta\n",
    )
    write("docs/decisions/2026-09/20261005-gamma.md", "---\nid: ADR-gamma\nstatus: accepted\n---\n\n# Gamma\n")
    write(
        "specs/2026-10/20261005-delta/spec.md",
        "---\nid: SPEC-20261005-delta\nstatus: planned\n---\n\n# [SPEC-20261005] D\n",
    )
    write(
        "specs/2026-10/20261005-delta/plan.md",
        "---\nid: PLAN-delta\nspec: SPEC-delta\nstatus: draft\n---\n\n# Technical Plan: [SPEC-delta] Delta\n",
    )
    write(
        "specs/2026-10/20261005-delta/tasks.md", "---\nid: TASKS-delta\n---\n\n# Task Breakdown: [TASKS-delta] Delta\n"
    )
    write(
        "specs/2026-10/20261005-delta/reconcile.md",
        "---\nreconcile_id: REC-other\nfeature: 2026-10/20261005-delta\nstatus: resolved\n---\n\n# Reconcile\n",
    )
    write(
        "specs/2026-10/20261007-epsilon/reconcile.md",
        "---\nfeature: 2026-10/20261007-epsilon\nstatus: resolved\n---\n\n# Reconcile without reconcile_id\n",
    )
    write("specs/2026-10/20261005-delta/notes.md", "ADR-0002 in a file that is not an identifier target\n")
    write(
        "docs/capabilities/x/CAP-X-alpha.md",
        "---\nid: CAP-X-alpha\narea: x\nstatus: active\n---\n\n# [CAP-X-alpha] X\n\n"
        "See ADR-0006 and SPEC-20261006-foo and PADR-0001.\n",
    )
    write("docs/materials/2026-10/old.md", "ADR-0001 historical material is ignored\n")


def test_dated_partitions(workspace: Path, write: Write) -> None:
    _fixture(write)
    violations = run(RULE, workspace)
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
    capability = [(line, message) for file, line, message in found(violations) if file.startswith("docs/capabilities/")]
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


def test_only_targets_are_reported(workspace: Path, write: Write) -> None:
    _fixture(write)
    violations = run(RULE, workspace, "docs/capabilities/x/CAP-X-alpha.md")
    assert {v.file for v in violations} == {"docs/capabilities/x/CAP-X-alpha.md"} and len(violations) == 3


def test_fix_is_idempotent_and_honours_dry_run(workspace: Path, write: Write) -> None:
    _fixture(write)
    ctx = RuleContext(workspace_root=workspace, fix=True, dry_run=True)
    assert evaluate_rules(ctx, [RULE]).errors == []
    assert "id: SPEC-20261005-delta" in _read(workspace, "specs/2026-10/20261005-delta/spec.md")

    run(RULE, workspace, fix=True)
    spec = _read(workspace, "specs/2026-10/20261005-delta/spec.md")
    assert "id: SPEC-delta\n" in spec and "# [SPEC-delta] D" in spec
    beta = _read(workspace, "docs/decisions/2026-10/20261004-beta.md")
    assert "id: ADR-beta\n" in beta and "# [ADR-beta] Beta" in beta
    assert "reconcile_id: REC-delta\n" in _read(workspace, "specs/2026-10/20261005-delta/reconcile.md")
    epsilon = _read(workspace, "specs/2026-10/20261007-epsilon/reconcile.md")
    assert epsilon.startswith("---\nreconcile_id: REC-epsilon\nfeature:")

    files = [p for p in sorted(workspace.rglob("*.md")) if ".devkit" not in p.parts]
    before = {p: p.read_text() for p in files}
    violations = run(RULE, workspace, fix=True)
    assert {p: p.read_text() for p in files} == before
    assert [v for v in violations if v.fixable] == []


def _feedback_fixture(write: Write) -> None:
    def fb(document_id: str, heading: str) -> str:
        return f"---\nid: {document_id}\nstatus: open\n---\n\n# {heading}\n"

    write("specs/2026-10/20261005-delta/spec.md", "---\nid: SPEC-delta\nstatus: planned\n---\n\n# [SPEC-delta] D\n")
    write("specs/2026-10/20261005-delta/feedback/good-one.md", fb("FB-good-one", "[FB-good-one] ok"))
    write("specs/2026-10/feedback/20261006-lane-one.md", fb("FB-lane-one", "[FB-lane-one] ok"))
    write("specs/2026-10/20261005-delta/feedback/wrong-id.md", fb("FB-other", "[FB-wrong-id] bad"))
    write("specs/2026-10/20261005-delta/feedback/bad-h1.md", fb("FB-bad-h1", "[SPEC-delta] bad heading"))
    write("specs/2026-10/20261005-delta/feedback/20261005-dated.md", fb("FB-dated", "[FB-dated] bad"))
    write("specs/2026-10/feedback/nodate.md", fb("FB-nodate", "[FB-nodate] bad"))
    write("specs/feedback/root-level.md", fb("FB-root-level", "[FB-root-level] bad"))
    write("specs/2026-10/20261005-delta/notes.md", "see FB-20261006-dated-ref in prose\n")
    # The same feedback slug in another bundle is fine: feedback IDs are unique per bundle.
    write("specs/2026-10/20261008-eta/spec.md", "---\nid: SPEC-eta\nstatus: planned\n---\n\n# [SPEC-eta] Eta\n")
    write("specs/2026-10/20261008-eta/feedback/good-one.md", fb("FB-good-one", "[FB-good-one] ok"))


def test_feedback(workspace: Path, write: Write) -> None:
    _feedback_fixture(write)
    violations = run(RULE, workspace)
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

    run(RULE, workspace, fix=True)
    assert "id: FB-wrong-id\n" in _read(workspace, "specs/2026-10/20261005-delta/feedback/wrong-id.md")
    assert "# [FB-bad-h1] bad heading" in _read(workspace, "specs/2026-10/20261005-delta/feedback/bad-h1.md")


def _living_spec_fixture(write: Write) -> None:
    def doc(document_id: str, heading: str, *, area: str | None = None, body: str = "") -> str:
        area_line = f"area: {area}\n" if area is not None else ""
        return f"---\nid: {document_id}\ntitle: T\n{area_line}status: active\n---\n\n# {heading}\n{body}"

    # valid documents
    write("docs/capabilities/README.md", "# Capabilities\n")
    write(
        "docs/capabilities/harness/CAP-HARN-context-pack-slicing.md",
        doc(
            "CAP-HARN-context-pack-slicing",
            "[CAP-HARN-context-pack-slicing] Pack",
            area="harness",
            body="\nSee US-010 and ARCH-06-runtime-view and US-init-project-docs and CAP-GOV-rule-verification.\n",
        ),
    )
    write("docs/stories/README.md", "# Stories\n")
    write(
        "docs/stories/delivery/US-reconcile-feature.md",
        doc("US-reconcile-feature", "[US-reconcile-feature] Reconcile", area="delivery"),
    )
    write("docs/architecture/README.md", "# Architecture\n")
    write(
        "docs/architecture/ARCH-01-introduction-and-goals.md",
        doc(
            "ARCH-01-introduction-and-goals",
            "[ARCH-01-introduction-and-goals] Intro",
            body="\nARCH-05-1-containers and ARCH-11-risks are fine.\n",
        ),
    )
    write("docs/architecture/ARCH-05-1-containers.md", doc("ARCH-05-1-containers", "[ARCH-05-1-containers] C"))
    write(
        "docs/architecture/ARCH-search-pipeline.md",
        doc("ARCH-search-pipeline", "Search", body="\nSee ARCH-06 for the runtime view.\n"),
    )
    # invalid documents
    write("docs/capabilities/harness/CAP-HARN-001-legacy.md", doc("CAP-HARN-001", "Legacy", area="harness"))
    write("docs/capabilities/harness/CAP-HARN-wrong-area.md", doc("CAP-HARN-wrong-area", "Wrong", area="governance"))
    write(
        "docs/capabilities/harness/CAP-HARN-wrong-id.md",
        doc("CAP-HARN-other", "[CAP-HARN-other] Wrong id", area="harness"),
    )
    write("docs/capabilities/CAP-FLAT-no-area.md", doc("CAP-FLAT-no-area", "Flat"))
    write("docs/stories/US-flat-story.md", doc("US-flat-story", "Flat"))
    write(
        "docs/stories/governance/US-deterministic-rule-verification.md",
        "---\nid: US-003\ntitle: Rules\nactor: agent\nstatus: active\n---\n\n# [US-003] Rules\n",
    )
    write("docs/stories/a/US-same-slug.md", doc("US-same-slug", "A", area="a"))
    write("docs/stories/b/US-same-slug.md", doc("US-same-slug", "B", area="b"))
    write("docs/architecture/ARCH-13-extra.md", doc("ARCH-13-extra", "Extra"))
    write("docs/architecture/ARCH-09-decisions.md", doc("ARCH-09-decisions", "Decisions"))
    write("docs/architecture/ARCH-07.md", doc("ARCH-07", "Bare"))
    write("docs/architecture/ARCH-07-deployment.md", "# [ARCH-07-deployment] No frontmatter\n")
    # references
    write(
        "specs/2026-10/20261005-delta/reconcile.md",
        "---\nreconcile_id: REC-delta\nstatus: resolved\n---\n\n# Reconcile\n\n"
        "Touched CAP-HARN-007 and stories/US-002-reconcile.md.\n",
    )
    write("docs/materials/2026-10/old.md", "US-010 CAP-HARN-007 ARCH-06 are ignored in materials\n")


def test_living_spec(workspace: Path, write: Write) -> None:
    _living_spec_fixture(write)
    violations = run(RULE, workspace)
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


def test_living_spec_fix(workspace: Path, write: Write) -> None:
    _living_spec_fixture(write)
    untouched = [
        "docs/stories/US-flat-story.md",
        "docs/stories/a/US-same-slug.md",
        "docs/stories/b/US-same-slug.md",
        "docs/architecture/ARCH-07-deployment.md",
    ]
    before = {path: _read(workspace, path) for path in untouched}
    violations = run(RULE, workspace, fix=True)
    story = _read(workspace, "docs/stories/governance/US-deterministic-rule-verification.md")
    assert story.startswith("---\nid: US-deterministic-rule-verification\narea: governance\ntitle: Rules\n")
    assert "# [US-deterministic-rule-verification] Rules" in story
    area = _read(workspace, "docs/capabilities/harness/CAP-HARN-wrong-area.md")
    assert "\narea: harness\n" in area and "governance" not in area
    assert "id: CAP-HARN-wrong-id\n" in _read(workspace, "docs/capabilities/harness/CAP-HARN-wrong-id.md")
    assert {path: _read(workspace, path) for path in untouched} == before
    assert [v for v in violations if v.fixable and not v.fixed] == []


def test_fix_keeps_crlf_and_quoted_values(workspace: Path, write: Write) -> None:
    path = "docs/decisions/2026-10/20261004-beta.md"
    write(path, '---\r\nid: "ADR-old"\r\nstatus: accepted\r\n---\r\n\r\n# `ADR-old` Beta\r\n')
    run(RULE, workspace, fix=True)
    assert _read(workspace, path) == "---\r\nid: ADR-beta\r\nstatus: accepted\r\n---\r\n\r\n# `ADR-beta` Beta\r\n"
    assert run(RULE, workspace) == []


def test_completed_bundles_are_checked_only_when_targeted(workspace: Path, write: Write) -> None:
    spec = "specs/2026-10/20261001-done/spec.md"
    write(spec, "---\nid: SPEC-old\nstatus: completed\n---\n\n# Done\n\nSee ADR-0001.\n")
    write("specs/2026-10/20261001-done/notes.md", "See US-001.\n")
    assert run(RULE, workspace) == []
    assert run(RULE, workspace, fix=True) == []
    assert "id: SPEC-old" in _read(workspace, spec)
    assert [v.message for v in run(RULE, workspace, spec)] == [
        'Frontmatter id is "SPEC-old" but the path requires "SPEC-done"',
        'Date- or number-based identifier reference "ADR-0001"',
    ]
