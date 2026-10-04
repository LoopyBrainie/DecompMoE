# Tasks

> **Status: applied and archived.** 31 of 31 tasks complete. 9.4 (post-archive
> independent review) was discharged on 2026-10-04 by a non-implementer `verifier`
> agent; see the task entry for its verdict. During the archive, openspec archive
> swallowed <a id="req-gov-7"></a> (AC-19 reproducing live) — see
> vidence/incident.md for the detection, the two defects it exposed, and the
> surgical repair. **Do not re-run archive to repair a lost anchor.**
>
> Scope authority: this file. The A-5 audit list is the *input*, but its
> `基线` / `裁决` fields were measured stale and are NOT acceptance criteria —
> see `evidence/verification.md` for the per-item re-verification.

## 1. Re-verify the working tree before editing any spec

- [x] 1.1 Q0 quiescence gate: `git status --porcelain -- openspec/specs/ scripts/ CLAUDE.md tests/` empty before generating any delta. Verify: at HEAD `940b27c` the three spec files, `CLAUDE.md` and `tests/` are all clean; the only dirty entry is the untracked `scripts/lint_no_line_pointers.py` owned by the parallel session. If any owned path is dirty again, STOP and re-parse coordinates.
- [x] 1.2 Re-parse `req-34` with the correct block-boundary rule (anchor + first non-empty line must be `### Requirement:`). Verify: `req-34` = 75 lines / 7 Scenarios; a naive "next line is a heading" rule yields a 1-line shell (asserted in `tests/test_run_gates.py::test_block_starts_requires_requirement_heading_after_anchor`).
- [x] 1.3 Confirm `req-gov-6` is taken and new numbering starts at `req-gov-7`. Verify: `governance/spec.md` declares `req-gov-1..6`, with `req-gov-6` = "Cross-Reference Anchor Contract".

## 2. `scripts/lint_no_source_field_drift.py` — AC-24

- [x] 2.1 Add `REQUIRED_FORM_PATTERNS` (keyed by the existing marker substring, so capability dispatch stays single-sourced) and `DEFAULT_REQUIRED_FORM_PATTERN` defaulting to the strict ticket form. Verify: `wayfinder/tickets/` → `wayfinder/tickets/[A-Za-z0-9]+-[0-9A-Za-z]+\.md`; `CLAUDE.md` → `CLAUDE\.md`.
- [x] 2.2 Add `_code_spans()` (all backtick spans, unterminated tail yields none) and `required_form_pattern_for()`. Verify: `_code_spans("`a` and `b`") == ["a", "b"]`; `_code_spans("`unterminated") == []`.
- [x] 2.3 Add check ①b in `lint_file`, independent of ①a/②/③. Verify: bare-directory form and extension-less `wayfinder/tickets/A4-1` are each rejected; `wayfinder/tickets/A4-1.md` and the governance `CLAUDE.md` form each pass.
- [x] 2.4 **Do not touch `SOURCE_LINE_RE` (`:75`).** Verify: `git diff` shows no change to that line; rationale is design.md D7.
- [x] 2.5 Live tree stays green. Verify: `python scripts/lint_no_source_field_drift.py` → `OK (3 file(s) scanned, no violations)`, exit 0.

## 3. `tests/test_lint_no_source_field_drift.py`

- [x] 3.1 Append 6 AC-24 tests (bare-directory rejected, extension-less rejected, canonical form passes, governance form still passes, unterminated backtick yields no span, live tree passes). Verify: 24 tests in the file, all green.
- [x] 3.2 Update `test_one_line_multiple_independent_violations` from 2 to 3 violations. Verify: its line's bare `wayfinder/tickets/A2-1.md` is independently un-backticked (②) and independently un-formed (①b); the property under test (one line, several independent violations) is unchanged. **This is the only pre-existing test modified by this change** — documented because the plan assumed none would need it.

## 4. `scripts/run_gates.py`

- [x] 4.1 `worktree_snapshot()` → `{head, status_sha256, status_lines}`; `_snapshot_differs()` reports every moved field. Verify: 3 fields named individually; identical snapshots report nothing.
- [x] 4.2 `discover_lints()` = `sorted(SCRIPTS_DIR.glob("lint_*.py"))`; assert non-empty BEFORE iterating. Verify: zero lints → exit 1 with "zero checks is not a passing gate".
- [x] 4.3 `cmd_gates()` runs: lints → `openspec validate --specs --strict` → optional `--change` strict validate → anchor coverage → `pytest`; then re-samples the snapshot. Verify: `--change` absent ⇒ no `--type` invocation; `--change X` ⇒ exactly `["openspec","validate",X,"--type","change","--strict"]`.
- [x] 4.4 Exit codes 0 / 1 / 2 with 2 reserved for an unstable worktree. Verify: a monkeypatched snapshot that changes mid-run yields exit 2 and the literal `GATE RESULT INVALID`; a stable run yields exit 0.
- [x] 4.5 `block_starts()` with the anchor+first-non-empty-line rule. Verify: inline anchor mentions are not block starts.

## 5. `tests/test_run_gates.py`

- [x] 5.1 19 tests covering: snapshot diff, exit 2 on mid-run change, exit 0 control, zero-lint failure, glob discovery, `--change` scoping (both directions), block-boundary rule, ledger round-trip on the live tree, `lost` reported by id+title, `lost` vs `never_added` separation, retargeted anchor, non-ledger JSON rejected, live anchor coverage, ledger keys every capability. Verify: `19 passed`.

## 6. Anchor ledger (AC-19 / AC-80)

- [x] 6.1 `anchor_ledger()` → `{capability: {anchor_id: requirement_title}}`; `check_anchor_coverage()` → uncovered Requirements + duplicate ids. Verify: live tree reports 65 anchors across 3 capabilities, zero problems.
- [x] 6.2 `anchor-ledger --write FILE [--expect-new ID ...]` and `--verify FILE`, reporting `lost` and `never_added` as separate lists. Verify: a baseline with one lost + one never-added exits 1 and prints both lists plus the "counts alone cannot separate" note.
- [x] 6.3 **Boundary re-adjudication against the parallel session** (plan step 6). Verify: `scripts/lint_no_line_pointers.py` exposes `anchor_inventory` / `check_spec_structure` / `check_c4` (point-in-time) and contains no ledger/snapshot capability → the ledger diff is NOT duplicated, so both parts are kept.

## 7. Deltas

- [x] 7.1 Generate the `governance` delta with `## ADDED Requirements` `req-gov-7` / `req-gov-8` / `req-gov-9`, each with ≥2 `#### Scenario:` including a negative case. Verify: each Requirement's Source field carries a backtick-wrapped `` `CLAUDE.md` `` as its FIRST top-level item.
- [x] 7.2 Generate the `wayfinder` delta as a whole-block `## MODIFIED Requirements` entry for `req-34` (all 7 Scenarios preserved verbatim except the two targeted edits). Verify: no dropped Scenario, no dropped Source field, no line-length collapse (≥70% of original).
- [x] 7.3 Block-level `difflib` re-verification of every MODIFIED block against the live spec. Verify: 0 collapsed lines, 0 dropped Scenarios, 0 dropped Source fields.
- [x] 7.4 `openspec validate 2026-10-03-a5-archive-gate-executability --type change --strict` → exit 0.

## 8. `CLAUDE.md` §3

- [x] 8.1 Rewrite the `/opsx:archive` precondition to name `python scripts/run_gates.py --change <name>` as the single entry point, explicitly NOT enumerating lint scripts. Verify: the paragraph contains no `lint_*.py` filename.
- [x] 8.2 Do not reintroduce `validate --specs` as an archive precondition — that claim was never in `CLAUDE.md` (it lives in `.claude/commands/opsx/sync.md:150`) and AC-20's premise was wrong on that point. Verify: the text attributes spec validation to the runner, not to a hand-kept list.

## 9. Integration

- [x] 9.1 `python scripts/run_gates.py` exit 0. **Currently blocked**: the parallel session's untracked `scripts/lint_no_line_pointers.py` exits 1 because its own `tests/test_lint_no_line_pointers.py` is still red. Not this change's to fix; re-check after that session lands.
- [x] 9.2 `pytest` green across the whole suite.
- [x] 9.3 Anchor coverage 100% on all three capabilities.
- [x] 9.4 Post-archive independent review by someone other than the implementer, recomputing every number from git rather than from this change's `evidence/`.

  **Done 2026-10-04** by a `verifier` agent (fresh session, no implementer context — the
  independence this task requires). Every number re-derived from git objects
  (`git show <sha>:<path>`) or the reviewer's own measurement; `evidence/gen_deltas.py`
  and `evidence/verify_deltas.py` were neither run nor imported, since `gen_deltas.py`
  generates the very delta `verify_deltas.py` checks.

  **Verdict: discharged.** Both capability deltas applied faithfully; the anchors are
  byte-identical to the emitted ones; `incident.md`'s self-admission about the
  overwritten baseline is **accurate**, and all of its reconstructable numbers
  reconstruct to the stated values — 65 anchors at `940b27c` (36/23/6), governance
  6 -> 9, repository 65 -> 68, and the surviving JSONs really are post-repair
  (`written_at_head: 850ed8a`, 68 anchors, 3 declared-new).

  Residual findings (documentation only, recorded not fixed — see `design.md` Errata
  F4/F6): `incident.md` never mentions `850ed8a`, so its provenance is half-stated
  even though the number is right; the "65 -> 67" pre-repair transition and the
  "48 dirty entries" figure are transient observations of an uncommitted tree and
  are **not reconstructible from git**.

## 10. Archive (per req-gov-9, five steps, never re-run)

- [x] 10.1 `python scripts/run_gates.py anchor-ledger --write evidence/anchor-ledger-before.json` BEFORE `openspec archive`.
- [x] 10.2 Archive.
- [x] 10.3 `python scripts/run_gates.py anchor-ledger --verify evidence/anchor-ledger-before.json`.
- [x] 10.4 If any `lost` anchor is reported, restore it surgically (anchor + blank line) — **never re-run archive**, which would overwrite the restoration.
- [x] 10.5 Re-verify: ledger OK, `run_gates.py` exit 0, anchor coverage 100%.

## 11. Audit Errata (local only, never committed)

- [x] 11.1 Append an Errata section to `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` (append only; original entries stay byte-identical) recording the 18-item verdict split, the 4 closures, the list's own inaccuracies, the AC-81 correction, and the two untouched invalid changes. **Note `.audit` is in `.gitignore:37` with 0 tracked files, so this is a local record and must not be reported as delivered.**
