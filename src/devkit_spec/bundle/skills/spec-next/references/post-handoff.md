# Post-handoff link check

Read this immediately after every `devkit spec proposal handoff <slug>`, and run it in the same change.

The handoff creates `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`, promotes each PADR to an ADR under `docs/decisions/`, moves `materials/` (unless it holds only operating-system junk such as `.DS_Store`) to `docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/` together with every other bundle file it does not carry otherwise (junk aside), deletes `docs/proposals/PROP-<slug>/`, and rewrites what pointed into the proposal in Markdown files under `docs/` and `specs/`: relative links (`proposal.md` → `spec.md`, PADR → promoted ADR, materials and other carried files → moved path, bundle dir → spec dir) and ID references (`PROP-<slug>` → `SPEC-<slug>`, `PADR-<slug>` → `ADR-<slug>`). It reports each change as `[REWRITTEN: <path>:<line> kind=link|id from=... to=...]`. Completed spec bundles are work history and are not rewritten. What it cannot map is left untouched and reported as `[UNRESOLVED_LINK: <path>:<line> kind=... target=... reason=...]` with a `SPEC_PROPOSAL_LINK_UNRESOLVED` warning.

The proposal unit's workflow records (gate decisions `decisions/<NN>-<request>.yaml`, envelopes) are dropped, not moved; each is reported as `[DROPPED_RECORD: <path>]`. The proposal's own `gate:plan-intent` and `gate:plan-accept` records are carried into the spec under the same names (never re-labelled as another decision), each reported as `[CARRIED_GATE: <request> decision=<path>]`. `devkit workflow next --unit <spec dir>` then shows which gates still wait for the user; a `SPEC_PROPOSAL_GATE_NOT_CARRIED` warning names the answer command in its `[FIX]`.

1. Fix every `[UNRESOLVED_LINK]` line. Typical cases: `reason=unmapped` for a link to a PADR that was not promoted, into a `materials/` dir that was not moved (empty, or junk only) or to `decisions/` itself; `reason=ambiguous` for an ID several documents declare. Point it at the new spec or the promoted ADR by full ID (`` `SPEC-<slug>` ``, `` `ADR-<slug>` ``), or drop it.
2. Confirm nothing is left by searching for Markdown links to the deleted bundle (prose mentions of the old path are not links and need no change). Reference-style links and links inside fenced code blocks are not rewritten; fix those by hand if they were real references:
   ```bash
   rg -n "\]\([^)]*(PROP-<slug>/|\.\./proposal\.md)" docs specs
   ```
3. Reread every `[REWRITTEN: ... kind=id]` line outside the new spec and the promoted ADRs (the `SPEC_PROPOSAL_REFS_REWRITTEN` notice lists them). A reference that meant the proposal as an origin ("split off from `PROP-x`") now names the spec; reword the sentence so it stays true, for example "split off from the original proposal of `SPEC-x`".
4. Run `devkit rules check` and confirm `RULE-markdown-link` and `RULE-document-reference` pass.

`PROP-<slug>` references added later on another branch are fixed by `devkit rules fix` (`RULE-document-reference`), which replaces an unresolved `PROP-<slug>` with the single matching `SPEC-<slug>`.
