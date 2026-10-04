# Tasks

## 1. Freeze the baseline

- [x] 1.1 Record `git rev-parse HEAD` into `evidence/baseline_head.txt`. Verify: frozen head is `95718cf`; `pin..frozen` = 30 commits, 265 changed files.
- [x] 1.2 Snapshot the artifacts this change edits, because `.audit/` is **gitignored** and git therefore provides no before/after. Verify: `evidence/_pre_edit_opsx-changes.md` (sha `7d4f65aa…`), `_pre_edit_direct-fixes.md`, `_pre_edit_classified.json`, `_pre_edit_gen_listA2.py`.
- [x] 1.3 Confirm no other session holds ownership of the files. Verify: `2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract` is **archived**, so A-6 + the 口径 section are ours; its Errata is already in the file and must survive byte-identically.

## 2. Rebuild the missing drift-table generator

- [x] 2.1 Write `evidence/build_pin_drift.py`. Verify: emits `{pin, head, commits, drift, inserted, modified}` with a structure assertion, not eyeballing.
- [x] 2.2 **Fidelity self-check**: rebuild for `pin=6593a06, head=188b9fb` and compare key-by-key with the original `_pin_drift.json`. Verify: `SELF-CHECK PASSED … 60 files, 105 intervals`, 0 differences. A mismatch must stop the change — never edit the original table to fit the generator.
- [x] 2.3 Determine the coordinate side, which the artifact itself had recorded as unknown. Verify: head-side (`+`), proven by `@@ -496 +499 @@`→`[499,499]`, `@@ -325,0 +326,4 @@`→`[326,329]`, `@@ -1,80 +0,0 @@`→`[0,0]`. Recorded in `evidence/baseline_basis.md`.
- [x] 2.4 Generate `evidence/pin_drift_95718cf.json`. Verify: 277 files, 570 drift intervals, 283 inserted intervals.

## 3. Correct the A-6 segment's ledger

- [x] 3.1 `AC-06`: verdict `MOVED`→`FIXED_BY_COMMIT`, severity CRITICAL→MEDIUM, `fixing_commit=f6461d7`, position `sphere.py:137`→`:67`, problem rewritten. Verify: pin L67 is `def _betainc_regularized`; HEAD is adaptive 8/16-point GL and its HISTORY section quotes the audit's own pre-fix numbers `8.29e-07` / `1.57e-01`.
- [x] 3.2 `AC-26`: verdict `STILL_REAL`→`FIXED_BY_COMMIT`, `fixing_commit=315065e`, position `:166`→`:178`, problem/evidence corrected. Verify: pin blob == `b272787` blob == pin's parent blob (`6ddbdef`); `8f50659` is `7a88c63`; pin has **10** `actual=`; all three `rv:main45:*` verdicts are `FIXED_BY_COMMIT`; `e50cc02` is a descendant of pin.
- [x] 3.3 `AC-27`: `基线` `touched`→`unchanged`; **keep** `+1/+13/+8` and the position. Verify: skeleton:122 is in no drift interval; numstat and real line counts both confirm the three numbers.
- [x] 3.4 `AC-29`: position `1367`→`1336`, drop the dead key `rv:main18:math`, note the report is out-of-repo. Verify: report is 1677 lines, 「诚实边界」 at 1336; the key is absent from the 197-key json.
- [x] 3.5 `AC-30`: verdict `STILL_REAL`→`FIXED_BY_COMMIT`, `fixing_commit=a97e3a7`, position `schedule.py`→`extraction.py:90`, `origin_ids` `rv:main20:math`→`grv:gap0:math`. Verify: pin L90 is `class CentroidDriver`; HEAD's `mask` is a required parameter; the true key prefix is `grv:` (54 such keys, zero `rv:grv:`).
- [x] 3.6 `AC-50`: add `rv:main42:{source,math,impact}`; replace the "0.436% uses another denominator" claim with its real provenance `66_336/66_048 − 1`; **do not change the position** (see 5.2).
- [x] 3.7 `AC-51`: `rv:grv:gap25:math`→`grv:gap25:math`; restore the `tests/` prefix the body had dropped.
- [x] 3.8 Apply with asserted old values and verify by read-back. Verify: `applied 30 change(s) and verified read-back`.

## 4. Rebaseline the whole list

- [x] 4.1 `evidence/rebaseline.py` covering list A (102 `opsx-change` + 6 `user-decision`) and list B (9 `direct-fix`). Verify: 117 distinct items = 123 `基线` field instances.
- [x] 4.2 Three-valued verdict, with the `unverifiable` state for no-line / non-repo-path items. Verify: 19 items qualify and each was inspected, not bulk-assigned.
- [x] 4.3 Compute from the **corrected** locations, then write back with asserted old values. Verify: `applied 42 baseline_status correction(s)`.
- [x] 4.4 Keep the inserted/modified split as data only; no status flips on an unapproved 口径 change. Verify: `inserted_only_diff.txt` is empty → 0 items would flip.
- [x] 4.5 Preserve the change set, which `rebaseline.py` stops reporting once applied. Verify: `evidence/rebaseline_changes.md` (42 rows: 18 →touched, 5 →unchanged, 19 →unverifiable).
- [x] 4.6 Update list B surgically, since it has **no generator**. Verify: 8 items updated, `基线` field count still 15.
- [x] 4.7 Idempotence. Verify: two consecutive runs produce the same `rebaseline_diff.json` sha256.

## 5. Make the correction durable and self-guarding

- [x] 5.1 Patch `_work/_gen_listA2.py`: `fixing_commit` rendering, out-of-repo `位置` labeling, and the 7 `ANNOT` tags. Verify: 3 `修复 commit` lines render; the 3 prior Errata sections are untouched.
- [x] 5.2 Guard against silent reversion: `evidence/a6_expected.json` + a pre-write assertion in the generator. Verify: `A-6 lock OK: 7 items match a6_expected.json`; mutating a locked field aborts with `A-6 LOCK FAILED` and does not write.
- [x] 5.3 Extend the 口径 section rather than adding a new one: 3 values, the 1-based declaration, the coordinate-side finding, the declared (unfixed) soundness flaw, and the warning that this file is **not** a pure generator product.
- [x] 5.4 Update 「盲区 3 / 盲区 5」, which hardcoded AC-06's status and a stale touched-item list.
- [x] 5.5 Generator idempotence. Verify: two consecutive runs give the same sha256.
- [x] 5.6 Splice, do not overwrite: the three Errata sections are post-generation manual content, so a plain regeneration would delete ~370 reviewed lines. Verify: `errata tail: 370 lines preserved byte-identically`.
- [x] 5.7 Append `## Errata (A-6 侧)` following the convention of the A-1 / A-2 / A-4 sections. Verify: heading present on read-back.
- [x] 5.8 Refresh the README's baseline warning (it still said 9 commits / HEAD `188b9fb`) and add the 1-based note. Verify: both replacements assert their old text.

## 6. Verify

- [x] 6.1 `evidence/verify_a6_errata.py` re-derives every claim from git and compares against the artifacts. Verify: **65 checks, 65 passed, 0 failed**.
- [x] 6.2 Structural回验: `基线` counts 108 / 15, four Errata sections, three `修复 commit` lines, and each of the 7 items' rendered fields. Verify: included in the 65.
- [x] 6.3 Arithmetic re-computed independently. Verify: 33 168 MACs, 66 336 FLOPs, 0.197697%, 0.196838%, 0.4361% = 66 336/66 048 − 1.

## 7. Gates and archive

- [x] 7.1 `python scripts/run_gates.py --change 2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline` → `exit 0`. A `GATE RESULT INVALID` (exit 2) means a concurrent session moved HEAD or the tree: re-run, never interpret.
- [x] 7.2 `openspec validate 2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline --type change --strict` → no ERROR.
- [x] 7.3 Archive. Verify: `skip_specs: true` means this change carries **no spec delta**, so it is structurally incapable of the archive-time anchor loss that affects delta-carrying changes — no anchor ledger is needed.
