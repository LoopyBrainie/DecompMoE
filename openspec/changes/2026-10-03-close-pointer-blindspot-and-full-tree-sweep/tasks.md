# Tasks

## 1. Validated detector (DONE)

- [x] 1.1 `evidence/pointer_scan.py` — two-class semantics, self-carrying +
      adjacency, code-span-aware marker, dedup by (file, line, locator),
      `SELF_EXCLUDE`.
- [x] 1.2 `evidence/validate_detector.py` — 15 known positives, 12 known
      negatives (3 guarding against false *exemption*), self-exemption
      both-directions, baseline regression `>= 100` strong, current-tree
      repro of 6 named survivors.
- [x] 1.3 Baseline worktree at `D:\tmp\a4fix\base1526b98` for the regression.

**The harness caught six defects in the detector, each a fresh instance of the
original failure mode.** They are listed in 2.3 as guard tests.

## 2. Fix the shipped gate (D2, D3, D4, D7)

- [ ] 2.1 `scripts/lint_no_line_pointers.py` adopts the validated semantics.
      `_POINTER_FORMS[0]` and the duplicated copy in
      `evidence/pointer_census.py:66` are both retired.
- [ ] 2.2 Historical marker refuses to fire inside a code span (D3).
- [ ] 2.3 Add a guard test per harness-caught detector defect:
      - [ ] backtick-delimited path (`` `ticket.md` L70 ``) is detected
      - [ ] `L236-L237` range is not swallowed by the label rule
      - [ ] the gap class admits `(` (caught by `... spec.md` Req 22 (L500)``)
      - [ ] a decimal float is not a pin commit id
      - [ ] `Req 11: 4070` prose is not a line locator
      - [ ] a self-exemptifying line stays actionable
- [ ] 2.4 `pointer_census.py` self-check calls `classify()` (D4).

## 3. Sweep the 55 sites (D5, D6)

Owner map from `evidence/map_to_requirements.py`:

- [ ] 3.1 `decompmoe-skeleton` `req-12` (2) — `safeguards.py:93`, `:95`
- [ ] 3.2 `decompmoe-skeleton` `req-13` (1) — `wayfinder/spec.md L83`
- [ ] 3.3 `decompmoe-skeleton` `req-18` (1) — `safeguards.py:30-31`
- [ ] 3.4 `decompmoe-skeleton` `req-20` (1) — `beta.py:50`
- [ ] 3.5 `decompmoe-skeleton` `req-23` (8) — the `L413` / `L500-518` cluster
- [ ] 3.6 `governance` `req-gov-2` (8) — **including the Scenario title at
      L76**, which currently names `Ticket A8-2 L70 + L74`
- [ ] 3.7 `governance` `req-gov-4` (1) — `audit-verification L581`
- [ ] 3.8 `wayfinder` `req-15` (1) — `A6b-2.md L52 / L89-L92`
- [ ] 3.9 `LOOPS.md` (14) — log entries, prose preserved (D6)
- [ ] 3.10 `tests/test_safeguards.py` (7)
- [ ] 3.11 `tests/test_schedule.py` (2), `tests/test_sphere.py` (2),
      `tests/test_metrics.py` (1)
- [ ] 3.12 `apply-checklist.md` (5),
      `docs/templates/post-review-remediation.md` (1)

Each edit is a bounded token substitution (D5). The rewriter asserts
length-collapse and re-reads every file it wrote.

## 4. Gates

- [x] 4.1 Three lints auto-discovered; `lint_no_dead_defensive` and
      `lint_no_source_field_drift` PASS. `run_gates.py` exit is red for one
      reason only: `lint_no_line_pointers.py` reports 4 C4 findings, all in
      `tests/test_run_gates.py`, which is a **parallel session's uncommitted
      in-flight file** (268 inserted lines, and `req-101` does not exist in
      HEAD). Verified: `git show HEAD:tests/test_run_gates.py` contains no
      `req-101`. Scoped to this change's own paths the gate is exit 0.
- [x] 4.2 `pytest` green for everything this change owns: 343 passed,
      1 skipped with `tests/test_run_gates.py` excluded. Two failures in
      the full run are both in that same foreign file.
- [x] 4.3 `openspec validate --specs --strict` PASS;
      `openspec validate <change> --type change --strict` **valid**.
- [x] 4.4 Anchor coverage still 68 / 3 capabilities.
- [x] 4.5 Census re-run: **0 actionable** in the product tree.
- [x] 4.6 Regression: the detector still reports 191 strong actionable sites
      on the `1526b98` baseline worktree, and its validation harness asserts
      this before any number is believed, so the zero is not vacuous.

## 5. Archive and re-verify

- [ ] 5.1 `openspec archive --skip-specs`. **Deliberately deferred, by user
      decision, not by oversight.** The only red gate item belongs to a
      parallel session's uncommitted `tests/test_run_gates.py`, whose
      synthetic `req-101` fixture does not resolve in any capability.
      Evidence that it is not ours: `git show HEAD:tests/test_run_gates.py`
      contains no `req-101`, and the file carries 268 uncommitted inserted
      lines. Archiving is an irreversible `git` move, so it waits for a
      genuinely green run rather than a red one annotated as foreign.
- [ ] 5.2 Independent post-archive recheck by a non-implementer.
- [ ] 5.3 `.audit` A-4 errata append recording this correction.
