"""Carry a proposal's body into the spec it is handed off to, section by section.

The body after the frontmatter and the first H1 is split into H2 sections, each classified by keywords of its
heading (case-insensitive):

- no heading (text before the first H2), ``background``, ``hypothesis``, ``problem``, ``motivation``, ``origin``:
  the problem statement, headings demoted one level;
- ``non-goal``, ``non goal``, ``scope excluded``, ``out of scope``: the non-goals, body only;
- ``acceptance``: the acceptance criteria, body only, given ``[AC-NN]`` IDs (``ensure_ac_ids``);
- anything else: carried notes, headings demoted one level.

Bodies are kept verbatim apart from heading levels; leading and trailing blank lines and trailing horizontal rules
are trimmed. Fenced code is never read as a heading.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from devkit.core.frontmatter import locate

_H1 = re.compile(r"^ {0,3}# +.+$")
_H2 = re.compile(r"^ {0,3}## +(.+?)\s*$")
_H3 = re.compile(r"^ {0,3}### +(.+?)\s*$")
_HEADING = re.compile(r"^( {0,3})(#{1,6})( +.*)$")
_AC_TAG = re.compile(r"\[(AC-[0-9]{2,})\]")
_LIST_ITEM = re.compile(r"^(?:[-*+]|[0-9]+[.)]) +\S")

_NON_GOAL = ("non-goal", "non goal", "scope excluded", "out of scope")
_ACCEPTANCE = ("acceptance",)
_PROBLEM = ("background", "hypothesis", "problem", "motivation", "origin")


@dataclass
class CarriedProposal:
    """Proposal body text regrouped into spec sections; each part ends with a blank line when not empty."""

    problem: str = ""
    non_goals: str = ""
    acceptance: str = ""
    notes: str = ""


@dataclass
class _Section:
    heading: str
    body: list[str] = field(default_factory=list)


def _fence(line: str) -> bool:
    return line.strip().startswith(("```", "~~~"))


def _sections(text: str) -> list[_Section]:
    """The body of ``text`` without frontmatter and first H1, split at H2 headings outside fenced code."""
    text = text.replace("\r\n", "\n")
    block = locate(text)
    body = text[block.end :] if block is not None else text
    sections: list[_Section] = []
    current = _Section("")
    seen_h1 = in_fence = False
    for line in body.split("\n"):
        if _fence(line):
            in_fence = not in_fence
        if not in_fence:
            if not seen_h1 and _H1.match(line) and not line.strip().startswith("##"):
                seen_h1 = True
                continue
            match = _H2.match(line)
            if match:
                sections.append(current)
                current = _Section(match.group(1))
                continue
        current.body.append(line)
    sections.append(current)
    return [s for s in sections if s.heading or "\n".join(s.body).strip()]


def classify(heading: str) -> str:
    """``problem``, ``non-goals``, ``acceptance`` or ``notes`` for an H2 heading (``problem`` when empty)."""
    lowered = heading.lower()
    if not heading:
        return "problem"
    if any(key in lowered for key in _NON_GOAL):
        return "non-goals"
    if any(key in lowered for key in _ACCEPTANCE):
        return "acceptance"
    if any(key in lowered for key in _PROBLEM):
        return "problem"
    return "notes"


def trim_blank(lines: list[str]) -> list[str]:
    """``lines`` without leading blank lines and trailing blank lines or horizontal rules."""
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and lines[end - 1].strip() in ("", "---", "***"):
        end -= 1
    return lines[start:end]


def demote_headings(lines: list[str]) -> list[str]:
    """Every heading outside fenced code one level deeper (at most H6)."""
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _fence(line):
            in_fence = not in_fence
        match = None if in_fence else _HEADING.match(line)
        if match and len(match.group(2)) < 6:
            out.append(f"{match.group(1)}{match.group(2)}#{match.group(3)}")
        else:
            out.append(line)
    return out


def carry_proposal_body(text: str) -> CarriedProposal:
    """Regroup the sections of a proposal (the whole file text) by heading keywords."""
    carried = CarriedProposal()

    def add(part: str, heading: str, body: list[str], demote: bool) -> None:
        body = trim_blank(body)
        if not body and not heading:
            return
        if demote:
            body = demote_headings(body)
        out = f"### {heading}\n\n" if heading and demote else ""
        if body:
            out += "\n".join(body) + "\n"
        if out:
            setattr(carried, part, getattr(carried, part) + out + "\n")

    for section in _sections(text):
        kind = classify(section.heading)
        if kind == "problem":
            add("problem", section.heading, section.body, True)
        elif kind == "non-goals":
            # The spec has its own Non-Goals heading: carry the list only.
            add("non_goals", "", section.body, True)
        elif kind == "acceptance":
            add("acceptance", "", section.body, False)
        else:
            add("notes", section.heading, section.body, True)
    return carried


def ensure_ac_ids(body: str) -> tuple[str, list[str]]:
    """An acceptance-criteria body every H3 of which carries exactly one ``[AC-NN]`` ID, and its IDs in order.

    An H3 with one tag keeps it; another H3 becomes ``### Scenario <n> [AC-NN]: <text without tags>`` whose ID is
    its position, or the next number after it that no single-tag H3 of the body uses. A body
    without H3 gets a tagged scenario heading before each top-level list item (or one before everything when it has
    none), and an empty body one placeholder scenario.
    """
    lines = trim_blank(body.replace("\r\n", "\n").split("\n"))
    ids: list[str] = []

    has_h3 = False
    taken: set[str] = set()
    in_fence = False
    for line in lines:
        if _fence(line):
            in_fence = not in_fence
            continue
        match = None if in_fence else _H3.match(line)
        if match is not None:
            has_h3 = True
            tags = _AC_TAG.findall(match.group(1))
            if len(tags) == 1:
                taken.add(tags[0])

    def next_id() -> str:
        number = len(ids) + 1
        while f"AC-{number:02d}" in taken:
            number += 1
        taken.add(f"AC-{number:02d}")
        ids.append(f"AC-{number:02d}")
        return ids[-1]

    out: list[str] = []
    in_fence = False
    if has_h3:
        for line in lines:
            if _fence(line):
                in_fence = not in_fence
            match = None if in_fence else _H3.match(line)
            if match is None:
                out.append(line)
                continue
            tags = _AC_TAG.findall(match.group(1))
            if len(tags) == 1:
                ids.append(tags[0])
                out.append(line)
                continue
            text = " ".join(_AC_TAG.sub("", match.group(1)).split())
            number = len(ids) + 1
            out.append(f"### Scenario {number} [{next_id()}]: {text}")
    elif lines:
        wrapped = False
        for line in lines:
            if _fence(line):
                in_fence = not in_fence
            if not in_fence and _LIST_ITEM.match(line):
                number = len(ids) + 1
                if out and out[-1].strip():
                    out.append("")
                out.append(f"### Scenario {number} [{next_id()}]: Carried from proposal")
                wrapped = True
            out.append(line)
        if not wrapped:
            out = [f"### Scenario 1 [{next_id()}]: Carried from proposal", "", *out]
    if not ids:
        return (
            f"### [{next_id()}] <scenario>\n- **Given** <precondition>\n- **When** <action>\n- **Then** <expected result>\n",
            ids,
        )
    return "\n".join(out) + "\n", ids
