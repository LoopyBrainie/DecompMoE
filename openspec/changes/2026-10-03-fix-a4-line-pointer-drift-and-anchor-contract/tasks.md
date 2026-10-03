# Tasks

> Scope authority: `evidence/pointer_census.json` (97 actionable sites, 20
> historical exemptions, 14 files). **The A-4 audit list is NOT the work list** —
> it is incomplete (`src/decompmoe/config.py:50` is a live pointer it never
> mentions), which is precisely why five previous hand-passes each left
> siblings behind. Where a task says "N sites", re-derive N from the census
> rather than from this file.
>
> **Apply-phase correction to the scope instrument.** The census exempted a whole
> LINE on any marker substring, and its marker list contained `ex-` and `→`. Both
> fire on ordinary vocabulary — `-> Tensor` return annotations, math arrows like
> `c ∈ [1, 2] → ("skip", 1.0, False)`, and `ex-` inside ordinary words — so lines
> that also carried a *live* pointer were silently exempted, and a "0 actionable"
> reading was reachable while pointers remained. `evidence/measure_marker_tightening.py`
> measured the effect: 4 lines flipped. The marker set is now substantive-only
> (`pre-this-change`, `histor`, `原`, `was `, `before`, or a prior commit id), and
> task 9.2's "whose marker is nameable" clause is what forced the change. The
> census self-check also moved off the live tree onto the pinned pre-change blob
> in `evidence/baseline_head.txt`, because its known positive (`wayfinder L249` =
> 10) legitimately reaches 0 the moment the sweep lands.

## 1. Re-verify the census before touching anything

- [x] 1.1 Confirm the parallel session's work is committed and none of this change's exclusive files is dirty; run `git status --short` and record the result. Verify: no exclusive file appears as modified by another session.
- [x] 1.2 Re-run `python evidence/pointer_census.py` and confirm the self-check passes (`wayfinder L249` == 10 sites, all in `tests/test_safeguards.py`). Verify: exit 0 and `self-check OK` printed. A count of 0 or of thousands means the classifier broke, not that the repo is clean.
- [x] 1.3 Record `git rev-parse HEAD` into `evidence/baseline_head.txt` and diff the census totals against design.md D1 (117 / 20 / 97 / 14). Verify: any difference is explained by a recorded commit before proceeding.

## 2. Anchor layer in `wayfinder` (structural prerequisite)

- [x] 2.1 Apply the `wayfinder` delta: mint `<a id="req-20-mci"></a>` on the `MCI` table row and `<a id="req-20-source"></a>` on the Source field, and append the "req-20 is the single canonical source for the MCI closed form" Scenario. Verify: both ids exist exactly once; `req-20` still has all 14 pre-existing Scenarios (15 after) and its `**Source:**` field.
- [x] 2.2 **Remove `req-36`** per the `## REMOVED Requirements` block, and land its four guarantees: (a) in `req-20` (done in 2.1); (b)(c)(d) in `governance` `req-gov-2` (task 3.1). Verify: `req-36` no longer appears in `openspec/specs/wayfinder/spec.md`; its `**Source:**` ticket lineage is now carried by `req-gov-2`, whose Source already cites `CLAUDE.md`; and no guarantee is lost — diff the removed Scenarios against the new homes one by one.
- [x] 2.3 Strip the anchor literals quoted in prose. Verify: in `wayfinder/spec.md` the id count equals 36 Requirement anchors plus the 2 block anchors (`req-20-mci`, `req-20-source`) = 38, with no duplicate id and no anchor token outside a standalone anchor line; `req-36`'s removal in 2.2 lowered the heading count from 37 to 36, so the "37" this task originally quoted is stale. The same check applies to `decompmoe-skeleton/spec.md` (23) and `governance/spec.md` (6 Requirement anchors, 0 block anchors) — the new `req-gov-6` states the rule without emitting an anchor element, and `req-23` quoted `<a id="req-22">` **without a closing tag**, a shape a well-formed `<a id="X"></a>` pattern misses.
- [x] 2.4 Apply the `req-2` / `req-6` / `req-13` / `req-32` pointer fixes (`per req-11 L211` → `#req-11`; `extraction.py:119-120` / `safeguards.py:98-102` / `loss.py:88` → `file.py::symbol`). Verify: `python evidence/verify_deltas.py` reports 0 collapsed lines, 0 dropped Scenarios and 0 dropped Source fields.

## 3. `governance` delta (hard prerequisite for a green lint)

- [x] 3.1 Re-anchor the ticket supersede annotation pattern in the "Ticket `(historical, ...)`" Requirement body and in its Scenario, and in `req-gov-4` clause 4(a): `req-N L###` → `req-N <title> (#req-N)`, declaring the `L###` form legacy. **Also land the three ticket-annotation guarantees migrated from the removed `req-36`** (A8-2 centered-covariance preserved; A8-2 convex-hull-radius preserved; the two jointly cover the `#req-20-mci` Reason argument). Verify: no `L###` remains in those three places; `req-gov-2` has 4 Scenarios (was 1); the three legacy ticket annotations in `wayfinder/tickets/A8-2.md` are left byte-identical.
- [x] 3.2 Add the new Requirement "Cross-Reference Anchor Contract" as **`req-gov-6`** (NOT `req-gov-5`, which is taken by "Numeric Literal Provenance in Specs"). Verify: `<a id="req-gov-6"></a>` exists exactly once, `anchors == headings` in `governance/spec.md`, and `python scripts/lint_no_source_field_drift.py` still exits 0 (the new Source field must contain `` `CLAUDE.md` `` in backticks, as the first top-level item).
- [x] 3.3 Confirm the new Requirement does not violate its own C1: it quotes *placeholder* pointer forms (`<capability> L<line>`, `<module>.py:<line>`), never a real one. Verify: run the census classifier over `openspec/specs/governance/spec.md` and confirm no ACTIONABLE hit in the new Requirement.

## 4. `decompmoe-skeleton` delta

- [x] 4.1 Apply the `req-16` addition: the new Scenario "Voronoi closed form is not the arctan shortcut", and extend the Requirement intro to say it is the landing site for the two invariants `req-15` removed from grep scope. Verify: `req-16` now has 2 Scenarios (was 1) and the original 4 invariants are preserved verbatim.
- [x] 4.2 Apply the `req-18` / `req-21` / `req-23` pointer fixes (`wayfinder L413`, `safeguards.py:71-80`, `req-7 L130` ×2, `req-7 L123`, `L504`, `L394-466`, `L560-563` ×2, `wayfinder L450/L454`). Verify: `python evidence/verify_deltas.py` reports 0 dropped Source fields for `req-18`; the census classifier finds no ACTIONABLE site in `openspec/specs/decompmoe-skeleton/spec.md`.

## 5. `src/` sweep (comments and docstrings only)

- [x] 5.1 `src/decompmoe/schedule.py` (≈7 sites): `wayfinder L491-507` and the three per-phase `line 495/496/497` comments → `Req 24` / `#req-24-betaeff`. This is the sibling the 2026-10-01 change left behind. Verify: `git grep -nE 'L[0-9]{2,4}|line [0-9]+' -- src/decompmoe/schedule.py` returns nothing actionable and `pytest tests/test_schedule.py` passes.
- [x] 5.2 `src/decompmoe/config.py` (3 sites): `req-11 L245` ×2 → `#req-11` totals; `req-7 L130` → `#req-7` closed form. Verify: both literals `452_329_984` / `100_008_448` unchanged and `pytest tests/test_config.py` passes.
- [x] 5.3 `src/decompmoe/extraction.py` (≈2), `src/decompmoe/metrics.py` (1: `Req 20 L394` → `#req-20`), `src/decompmoe/sphere.py` (3), `src/decompmoe/beta.py` (1), `src/decompmoe/safeguards.py` (1). Verify: the census classifier reports 0 actionable in `src/`, and `pytest` is green. No executable statement, signature, constant, or assertion value may change — diff each file and confirm only comment/docstring/string lines moved.
- [x] 5.4 `src/decompmoe/sphere.py` docstring: it points at `test_voronoi_angle_equal_area_witness_crosspolytope`, which does not exist; the real name is `..._equal_area_configurations`. Verify: `git grep -c 'witness_crosspolytope' -- src tests` returns 0 and the referenced test exists.

## 6. `tests/` sweep (docstrings and assertion messages only)

- [x] 6.1 `tests/test_safeguards.py` (≈34 sites): the 10 `wayfinder L249` → `wayfinder Req 13 Numerical Safeguards (#req-13)` and the 16 `spec L206` / `skeleton spec L208` → `decompmoe-skeleton Req 12 Five Numerical Safeguard Helpers (#req-12)`. These are the 10 that survived the 2026-09-12 change's explicit scope cut. **Correction**: this task originally mapped `skeleton spec L206` to `Req 11`; the five helpers are **req-12**, and the mechanical line→Requirement resolution is worse than useless here — `spec L206` resolves to wayfinder req-9 (SwiGLU FFN) and `skeleton L206` to skeleton req-10 (SwiGLU Expert), neither of which mentions a safeguard. Verify: the census classifier reports 0 actionable in the file and `pytest tests/test_safeguards.py` passes unchanged.
- [x] 6.2 `tests/test_metrics.py` (≈10) and `tests/test_extraction.py` (≈2): `spec L413` → `wayfinder Req 20 MCI row (#req-20-mci)`; `spec Req 20 L394` → `wayfinder Req 20` CG row; `spec req-7 L100` → `decompmoe-skeleton Req 7 C Extraction Four-Step Pipeline (#req-7)`. **Correction**: this task originally mapped `req-7 L100` to `#req-6`; `eps=1e-6` is the `extract_C(..., *, H_kv, d_c, eps=1e-6)` signature in `decompmoe-skeleton` **req-7**, not req-6 (Voronoi Self-Consistency Threshold), and the audit list's "skeleton L126" is also wrong. Every target was resolved against the Requirement's body text rather than the cited line number, because all cited coordinates predate this change's own edits. Verify: `pytest tests/test_metrics.py tests/test_extraction.py` passes; no expected value changed.
- [x] 6.3 `tests/test_sphere.py` (≈7), `tests/test_beta.py` (≈6), `tests/test_config.py` (≈3), `tests/test_schedule.py` (≈1). Verify: full `pytest` green and the census reports 0 actionable in `tests/`.

## 7. AC-63 guard (test first, then the spec handoff sentence)

- [x] 7.1 Add `tests/test_sphere.py::test_canonical_voronoi_angle_not_arctan_shortcut`, following `evidence/ac63_numeric_verification.py`: assert `canonical_voronoi_angle(16,16)` is `pytest.approx(1.173547, abs=1e-6)` (float closed form per `CLAUDE.md` §6 clause 8 / `req-gov-1` obligation 3) with `f"actual={...}"` embedded, assert the residual frame `< 1e-9` against the impl-internal reference, and assert the forbidden `arctan(pi/sqrt(d_c))` substitution is rejected by at least `1e5` tolerances (measured `5.078e-01`, i.e. `507_773×`). A fourth axis inspects the implementation's own source for an inverse-trigonometric token, which is the only axis that catches a body that reaches the *right* value by bypassing bisection. Verify: `evidence/verify_ac63_guard.py` injects three defects in memory — the shortcut as the return value, an approximate value, and an exact-value body that calls `atan` — and each is rejected, while the real implementation passes.
- [x] 7.2 Confirm the residual check calls `_betainc_regularized(x, a, b)` — **x first**. Verify: residual `< 1e-9` (`1.74e-14` at N_e=16). A residual near `0.44` means the argument order is wrong, not that the integrator is broken.
- [x] 7.3 Update `req-15`'s handoff sentence to name `test_canonical_voronoi_angle_not_arctan_shortcut` and the `req-16` Scenario, so the claim resolves in both directions. Verify: no guard is named in one file and absent from the other. `req-15` was **not** in this change's delta, so a `MODIFIED` block carrying the whole Requirement was appended to `specs/decompmoe-skeleton/spec.md`; without it, archive would have reverted the edit.

**Correction found while applying 7.1.** The Scenario's `THEN` clause asserted that the root of the defining equation is `0.665773750028 rad` — the *forbidden token's* value, substituted into both slots — while its own next line required `pytest.approx(1.173547, abs=1e-6)`. The delta carried the identical corruption, so both copies were fixed together (`evidence/fix_root_value_corruption.py`); leaving the delta alone would have reintroduced it at archive time. This is the "the defect is in the step that turns data into an artifact" family: the number was right, and the sentence that carried it was wrong.

**Archive must run with `--skip-specs`.** The delta was applied to the live specs during the apply phase (`evidence/apply_deltas.py`), then edited further — so re-applying it at archive time would (a) refuse the `governance` `ADDED` block because `req-gov-6` already exists, (b) revert every post-apply fix, and (c) make the `REMOVED` req-36 block a no-op at best. `openspec validate --strict` reports the refusal as INFO and still returns valid. The delta is kept as the record of what the change specified; the live specs are the record of what it produced.

## 8. The lint and its gate

- [ ] 8.1 Write `scripts/lint_no_line_pointers.py` with checks C1 (no line-number reference), C2 (anchor uniqueness + Requirement coverage), C3 (no anchor literal in a code span), C4 (reference resolvability), reusing the census detector for C1. C2's block boundary rule MUST require the next non-empty line after an anchor to be a `### Requirement:` heading, or block anchors truncate their own Requirement. Verify: `python scripts/lint_no_line_pointers.py` exits 0 on the migrated tree.
- [ ] 8.2 **Regression validity**: point the lint at the pre-change tree and confirm it reports C1–C4 violations and exits non-zero. Verify: non-zero exit and a non-empty violation list. A lint that passes on the pre-change tree is broken.
- [ ] 8.3 Write `tests/test_lint_no_line_pointers.py` mirroring `tests/test_lint_no_source_field_drift.py` (importlib load via `_REPO_ROOT`, never putting `scripts/` on `sys.path`): synthetic-line unit tests for each check — including a technical label (`d_c[L2-step2]`) that must NOT be flagged, a historical marker that must be exempt, and a quoted anchor literal that must be flagged — plus one assertion over the live tree. Verify: `pytest tests/test_lint_no_line_pointers.py` passes.
- [ ] 8.4 Document the new gate in `CLAUDE.md` §3 alongside the two existing lints. Verify: the archive precondition names all three scripts and `CLAUDE.md` still parses.

## 9. Integration gates

- [ ] 9.1 Run all three lint gates and full `pytest`. Verify: `lint_no_dead_defensive`, `lint_no_source_field_drift`, `lint_no_line_pointers` all exit 0, and `pytest` is green.
- [ ] 9.2 Re-run `python evidence/pointer_census.py`. Verify: 0 actionable sites across `openspec/specs/**` + `src/**` + `tests/**`; every remaining hit is an EXEMPT historical citation whose marker is nameable.
- [ ] 9.3 Verify anchor coverage across all three capabilities. Verify: `anchors == Requirement headings` in each, with no duplicate id, and 100% coverage per `CLAUDE.md` §6.
- [ ] 9.4 Append an Errata section to `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` recording the A-4 corrections — the 6 zero-based "真实位置" coordinates, the `基线` field being wrong for 14/15 under the file-level reading, and the AC-88 ⊃ AC-34/89/90 plus AC-59/70 duplication. Append only; do not rewrite entries, so the audit trail stays intact. Verify: original entries byte-identical; Errata appended below them.
- [ ] 9.5 Post-archive independent review by someone other than the implementer: recompute every number in design.md D1 from git, not from this change's evidence files, and re-verify each A-4 item's closure. Verify: reviewer reports their own counts, and any divergence from the census is explained rather than averaged away.
