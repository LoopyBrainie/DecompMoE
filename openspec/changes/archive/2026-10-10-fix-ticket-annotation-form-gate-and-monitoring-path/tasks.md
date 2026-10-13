# Tasks

## 1. Spec delta (governance)

- [x] 1.1 MODIFIED `req-gov-2` — name `scripts/lint_ticket_annotation_form.py` as the ticket-body
      form enforcer, and record that `lint_no_line_pointers.py` `SCAN_ROOTS` omits `wayfinder/tickets`
- [x] 1.2 MODIFIED `req-gov-2` — replace the "planning draft, NOT YET proposed/applied/archived"
      paragraph with the archived fact (`openspec/changes/archive/2026-09-23-fix-claude-md-ticket-advisory-boundary`
      exists; the Requirement it produced is `req-gov-4` at `:160-174` of the same file)
- [x] 1.3 MODIFIED `req-gov-2` — correct the dead `.audit/audit-verification.md` reference in Scenario 1
- [x] 1.4 MODIFIED `req-gov-2` — transcribe the two A8-2 annotations as they exist in
      `wayfinder/tickets/A8-2.md:70,74` (`req-20-mci (#req-20-mci)`), removing the drift against the
      canonical form stated at `:70`
- [x] 1.5 MODIFIED `req-gov-2` — ADDED Scenario "ticket supersede annotation form is machine-checked
      by a dedicated lint", stating the two-tier enforcement and the code-span paren rule
- [x] 1.6 MODIFIED `req-gov-4` — clause (3) monitoring path corrected to
      `.audit/audit-verification/audit-verification.md`, naming the non-resolving bare form as a defect
- [x] 1.7 MODIFIED `req-gov-4` — ADDED Scenario "the monitoring obligation names a path that resolves"
- [x] 1.8 `openspec validate --type change --strict` passes for this change

## 2. New gate — TDD order

- [x] 2.1 RED: `tests/test_lint_ticket_annotation_form.py` written; confirmed failing before the
      lint existed (`FileNotFoundError` on the script path)
- [x] 2.2 GREEN: `scripts/lint_ticket_annotation_form.py` implemented, importing
      `scripts/pointer_scan.py`; exit 0 clean / exit 1 with `path:line` + clause
- [x] 2.3 Dry-run over `wayfinder/tickets/*.md`
- [x] 2.4 RESOLVED BY MEASUREMENT, no corpus edit needed: all **18** annotations already carry the
      `(#req-N)` anchor and legacy line-addressed annotations measure **0**, so V-ANCHOR is green on
      arrival. Provenance reconstruction for the 9 annotations that cite no change **failed with
      evidence** (β₀ written by 19 deltas; `req-22` anchor duplicated across two capabilities;
      `req-32` touched by 5 changes; and `A4-1.md` already cites a Decision containing no beta term).
      V-DECISION therefore narrowed to "a cited change must exist" — see design.md Decision 6
- [x] 2.5 Fix the gate's own coverage hole: `A8-2.md:70` quotes `` `(1/d_c, 1]` ``, whose unbalanced
      paren made naive depth counting drop that annotation from checking entirely (2 markers, 1 span).
      Paren balancing now ignores code spans; markers = spans = 18
- [x] 2.6 Lint green: `OK (23 ticket file(s) scanned, 18 annotation(s), no violations)`, with
      `annotations citing no change/Decision (reported, not a gate): 9`

## 3. CLAUDE.md §4 date stamp

- [x] 3.1 Refresh the re-verification date and the measured numbers in the `§4` status block
- [x] 3.2 Leave the aspirational characterization and all three branch rows unchanged; no branch is
      created, renamed, merged, or force-pushed by this change

## 4. Audit-side record (outside the spec delta)

- [x] 4.1 Record the UD-05 withdrawal, citing `openspec/specs/wayfinder/spec.md:680-686`
- [x] 4.2 Record UD-03 as pending-evidence: `workflows/wf_fd517ac0-d53.json` is not present in any ref
- [x] 4.3 Correct the provably wrong numbers: UD-05 Requirement pointers, UD-01 `174/174` → `261/261`
      (`git rev-list --count dev` at baseline `dde0e1d`), UD-06 "two same-named files, 201/63" →
      pure addition with no second copy (`git diff --numstat dev audit/sdd-review-2026-09-04 -- REVIEW-LEDGER.md`
      at baseline `dde0e1d`) and 1/221-behind rather than forked
      (`git rev-list --left-right --count audit/sdd-review-2026-09-04...dev`)
- [x] 4.4 Copy `REVIEW-LEDGER.md` (313 lines, blob `639a72e`) into the `.audit/` evidence library;
      byte-exact, verified by `git hash-object` match; not merged into the code tree
- [x] 4.5 Note why the UD errata is a NEW sibling file and not an append to `lists/opsx-changes.md`:
      that file is pinned to exactly 5 `## Errata` sections by the archived verifier

## 5. Verification

- [x] 5.1 `python scripts/run_gates.py --change 2026-10-10-fix-ticket-annotation-form-gate-and-monitoring-path`
      → exit 0
- [x] 5.2 Re-run the fact baseline: `git rev-list --count dev` = 261; `git merge-base main dev` exit 1;
      `git tag` empty; `git diff --numstat dev audit/sdd-review-2026-09-04 -- REVIEW-LEDGER.md` = `312 0`
- [x] 5.3 Confirm `git status` still shows `src/decompmoe/gating.py` and `wayfinder/tickets/WF-1.md`
      as uncommitted changes owned by another actor — this change must not absorb or revert them
- [x] 5.4 Independent numeric re-check of the figures this delta states: each substituted into its
      closed form and confirmed against the spec text rather than against the audit's wording