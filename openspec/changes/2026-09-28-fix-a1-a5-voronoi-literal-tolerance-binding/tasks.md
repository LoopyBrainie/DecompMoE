# Tasks

> Design decisions referenced below (D1–D4) are recorded in `design.md`. No Open Questions block exists — all scope-shaping decisions were resolved before design was written.

## 1. Scaffold

- [x] 1.1 `openspec new change "2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding"` — verify: directory `openspec/changes/2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding/` exists and CLI reports `Schema: spec-driven`
- [x] 1.2 Verify `.openspec.yaml` contains exactly `schema: spec-driven` and `created: 2026-09-28`, matching the sibling `2026-09-28-fix-a2-a3-a4-residual-precision-claims/.openspec.yaml` shape

## 2. Change artifacts

- [x] 2.1 Write `proposal.md` — verify: file exists; `## Why` / `## What Changes` / `## Capabilities` (New = none, Modified = `wayfinder` + `decompmoe-skeleton`, `governance` absent) / `## Impact` / Source back-link all present
- [x] 2.2 Write `specs/decompmoe-skeleton/spec.md` delta — verify: `## MODIFIED Requirements` present, `### Requirement: Voronoi Self-Consistency Threshold` header matches the live spec exactly, all 4 original Scenarios copied verbatim, no new `<a id=...>` anchor introduced
- [x] 2.3 Write `specs/wayfinder/spec.md` delta — verify: `## MODIFIED Requirements` present, `### Requirement: 4070 MVP Hyperparameter Set` header matches the live spec exactly, all 5 original Scenarios + the `**Source:**` field copied verbatim, no new `<a id=...>` anchor introduced
- [x] 2.4 Write `design.md` — verify: `## Context` / `## Goals / Non-Goals` / `## Decisions` (Decision 1–4, each with rejected alternatives) / `## Risks / Trade-offs` / `## Migration Plan` all present
- [x] 2.5 Write `tasks.md` — verify: file exists with checkbox format `- [ ]` / `- [x]` per group
- [x] 2.6 Confirm all four artifacts report `status: done` via `openspec status --change 2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding --json`

## 3. Apply spec edits (D1 + D2)

- [x] 3.1 **D1** — `openspec/specs/decompmoe-skeleton/spec.md` L98: replace the `abs=1e-6` clause so it binds `1.173548` (N_e=16) and `1.020506` (N_e=64); demote `≈ 1.1735 rad` / `≈ 1.0205 rad` to 4dp prose display with an explicit "MUST NOT be paired with the `abs=1e-6` tolerance" clause; drop the now-false `(Matches master wayfinder Req 11 verbatim.)` parenthetical. Verify: line count unchanged (L98 remains one line) and `git diff --stat` shows 1 insertion + 1 deletion for this file
- [x] 3.2 **D2** — `openspec/specs/wayfinder/spec.md` L240: delete the `permitted by ... req-gov-1 §2` clause and the "`< 1e-4 rad` test tolerance" claim; restate the `5.94e-5` gap as prose-to-prose with no governing test tolerance, and add the tolerance-provenance note (§2 fixes assertion form only, `1e-6` comes from §3 and is scoped to 6dp literals). Verify: `Select-String '1e-4 rad' openspec/specs/wayfinder/spec.md` returns zero matches
- [x] 3.3 **D2** — `openspec/specs/wayfinder/spec.md` L241: same treatment for the `58.47°` / `1.0205` / `−5.99e-6` bullet. Verify: the false-attribution clause is gone. Note the file still contains exactly ONE `req-gov-1 §2` occurrence — the corrective sentence added on L240 stating that §2 prescribes **no numeric tolerance value**. That is the repair, not the defect; a bare "zero matches" check would wrongly flag it.
- [x] 3.4 **D3** — verify `git diff --stat` does NOT list `openspec/specs/governance/spec.md`; verify `openspec/specs/wayfinder/spec.md` L235 is byte-identical to HEAD (`git diff` shows no hunk covering it)

## 4. Gate verification

- [x] 4.1 `uv run pytest -q` returns `204 passed` — no test added, removed, or modified by this change, so the count must be unchanged from the `b23f0e5` baseline
- [x] 4.2 `uv run python scripts/lint_no_dead_defensive.py` returns `exit=0`
- [x] 4.3 `uv run python scripts/lint_no_source_field_drift.py` returns `exit=0` — required because `wayfinder` req-11 carries a `**Source:**` back-link field and this change edits inside that Requirement
- [x] 4.4 Anchor coverage unchanged: wayfinder 36/36, decompmoe-skeleton 23/23, governance 4/4 = 100%. Verify by counting `<a id="req-...></a>` occurrences against `### Requirement:` headings in all three specs
- [x] 4.5 `openspec validate --change "2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding"` reports no error

## 5. Independent numerical recheck (post-archive obligation, `CLAUDE.md` §3)

- [x] 5.1 Recompute independently of the spec text: `|1.1735482746999482 − 1.173548| = 2.747e-07 < 1e-6` and `|1.1658482974306132 − 1.165848| = 2.974e-07 < 1e-6` (6dp tier is tolerance-satisfiable)
- [x] 5.2 Recompute: `|1.0205068335735599 − 1.020506| = 8.336e-07 < 1e-6` (6dp tier satisfied)
- [x] 5.3 Recompute the 4dp tier is NOT tolerance-satisfiable at `1e-6`: `|1.1735482746999482 − 1.1735| = 4.827470e-05` (48.27×) and `|1.0205068335735599 − 1.0205| = 6.833574e-06` (6.83×) — this is the evidence that the pre-change L98 was unsatisfiable
- [x] 5.4 Recompute the bare-equality guards hold: `round(θ16, 4) == 1.1735`, `round(deg θ16, 2) == 67.24`, `round(θ64, 4) == 1.0205`, `round(deg θ64, 2) == 58.47`
- [x] 5.5 Recompute the display-diff figures the spec still quotes: `radians(67.24) − 1.1735 = +5.938904e-05` (spec says `5.94e-5`) and `radians(58.47) − 1.0205 = −5.986359e-06` (spec says `−5.99e-6`), plus `radians(58.47) = 1.0204940...`
- [x] 5.6 Recompute the residual figures `wayfinder` L235 quotes (not modified by this change, but cross-checked): impl-internal residual at impl output `1.164e-14`, true closed-form residual via direct quadrature `4.1457e-7` (N_e=16) and `1.4273e-9` (N_e=64)
- [x] 5.7 Cross-read the post-change `decompmoe-skeleton` req-6 against `wayfinder` req-11 L235/L240/L241: every literal↔tolerance pairing is simultaneously satisfiable, and no two specs assign a different tolerance to the same literal

## 6. Commit

- [x] 6.1 Confirm `2026-09-28-fix-a2-a3-a4-residual-precision-claims/` (untracked, owned by a parallel session) is NOT staged or committed by this change
- [x] 6.2 Do not stage `src/decompmoe/safeguards.py` — its working-tree delta is CRLF/LF noise with empty `git diff --stat`; leave it for the user to decide (out of this change's scope per plan "Unresolved decisions" item 3)
- [x] 6.3 Single commit on `dev`; verify `git log -1` is a normal commit and HEAD is not a merge commit (`CLAUDE.md` §4)
- [x] 6.4 Stop after commit — archive requires a separate explicit user request and is gated on both lint scripts reporting `exit=0`

## 7. Code-review findings P1–P6 — verification outcome and disposition

All six were independently re-verified by the parent agent (not taken on the review report's word) before any edit. Verdicts below; scope split per `design.md` Decision 7.

**FIXED in this change:**

- [x] 7.1 **P1 — `decompmoe-skeleton` L114 claimed a residual bound it does not meet.** Verified: impl-internal residual is `1.1643e-14` at `N_e=16` (`1.94e-15` at `N_e=64`), so the quoted `< 1e-14` was false by `1.16×`; the cited guard `test_voronoi_residual_below_1e_minus_9` pins `< 1e-9`, **not** `< 1e-14`; and `1e-14` appears **nowhere** in `tests/test_sphere.py`, so the tighter figure was unguarded. L114 now states the measured pair, names `< 1e-9` as the bound actually pinned, and states plainly that `< 1e-14` is unmet at `N_e=16` and untested.
- [x] 7.2 **P5 — `decompmoe-skeleton` L102 / L106 restated the 4dp literal with "equals"** (`AND equals \`≈ 1.1735 rad\``). Verified present. Both Scenarios now use the same two-tier guard form as the L98 body: `round(θ, 4) == 1.1735` / `round(math.degrees(θ), 2) == 67.24` (and the `1.0205` / `58.47` pair), plus an explicit "impl-internal frame" tag on the residual clause.
- [x] 7.3 **P2 — `_betainc_regularized`'s `n: int = 60` is dead, and the "60-segment" scheme it advertises does not exist.** Verified by AST (`n` declared, never loaded) and by grep (all 6 call sites pass 3 positional args, none pass `n=`). Parameter removed; `decompmoe-skeleton` L116 corrected to "a **single** 8-point Gauss–Legendre panel on `[0, x]` with no subdivision". Root cause of the false prose traced to archived change `2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix`, which assumed the scheme rather than checking the code. **Governance side held — see §9.1.**
- [x] 7.4 **P3 — the `< 1 ppm` bound is ambiguous on its literal reading.** Verified both readings: θ-discrepancy `0.7233 ppm` (N_e=16) / `0.0086 ppm` (N_e=64) satisfies it; `_betainc_regularized`'s own relative error is `6.6331 ppm`, which is `6.6×` over. L116 now scopes the bound explicitly to θ and quotes the `6.63 ppm` function-level figure. **Governance side held — see §9.1.**
- [x] 7.5 **P4 — `canonical_voronoi_angle`'s declared domain exceeds its validated domain, and the `~1e-12` docstring claim is false even at MVP.** Verified: function absolute error at the MVP point is `8.29e-07` (relative `6.63 ppm`); true closed-form residual at `N_e=16` is `3.35e-03` (`d_c=2`), `1.37e-05` (`d_c=4`), `2.21e-07` (`d_c=6`), `7.39e-09` (`d_c=8`), `4.15e-07` (`d_c=16`), `4.29e-05` (`d_c=32`). Both `sphere.py` docstrings corrected to state measured values and the accuracy band. **MVP impact: none** — `d_c = 16` is frozen per `CLAUDE.md` §5 and no computed value changed.

**HELD (not fixed here — see `design.md` Decision 7):**

- [x] 7.6 **P6 — `wayfinder` L233 and the L274-276 Scenario make unframed `< 1e-9` claims.** Verified: in the true closed-form frame the residual at `(16, 16)` is `4.1457e-7`, so "evaluating to less than `1e-9`" is false as written, and `governance` req-gov-1 obligation 4 explicitly requires *"Spec MUST clarify which frame is used for '< 1e-9' claims."* Held because req-11 is contested by two concurrent changes. Details and ready-to-apply wording in §9.2. **Highest-priority held item — same defect class this change exists to repair.**

## 8. Code review record (2026-09-28, agent `agent-b1a39f2827bf` "Python reviewer")

A `/code-review` of the change was run against the spec math, the code↔spec formalization, and test coverage. All findings were independently re-verified by the parent agent before acceptance — none were taken on the report's word.

**Fixed in this commit (defects introduced by it):**

- [x] 8.1 **MAJOR — `wayfinder` L240 mis-anchored the `48×` ratio.** The rewritten sentence named the `5.94e-5` prose gap and then said *"It is `48×` the `abs=1e-6` tolerance"*, but `5.938904e-05 / 1e-6 = 59.39×`. The `48×` figure belongs to a **different** quantity (`4.827470e-05`, the impl-output-to-4dp-literal distance). Corrected to state both explicitly: the prose gap is `59×`, and the impl output is `48×` from the 4dp literal. (This also removed a latent contradiction with this change's own `design.md` Decision 2, which had correctly said `59×`.)
- [x] 8.2 **MAJOR — `wayfinder` L240 asserted a false test-coverage claim.** It read *"no test asserts the 4-decimal form at any tolerance"*, but `tests/test_sphere.py:116-117,141-143` do assert it — via bare `==` on rounded values. The claim was also self-refuting: the next clause of the same sentence named those very assertions as the guards. Corrected to "the 4-decimal form is asserted, but by bare equality on rounded values, not by a tolerance."

**Verified correct by the review (no action):** bisection bracketing/monotonicity/termination in `sphere.py`; argument order and parameterization vs. the spec equation; absence of hard-coded tables; absence of self-referential assertions in `tests/test_sphere.py`; the parenthetical deletion at skeleton L98; and 27 of 31 recomputed numeric claims.

**Standing gap the review re-confirmed:** the `MUST NOT be paired with the abs=1e-6` prohibition now in `skeleton` L98 has **no mechanical guard** — per Decision 4 this is an accepted risk, but it is the defect class this change exists to close, and a future edit re-binding the 4dp literal to `1e-6` would silently re-break A1.

## 9. Held items — ready-to-apply wording for the successor change

These are **not** filed by this change (see `design.md` Decision 7). The analysis is complete and the replacement text is pre-verified, so the successor is a mechanical edit.

- [x] 9.1 **P2/P3 governance side — `governance/spec.md` L20 + L21.** Currently L20 says `_betainc_regularized` is *"Gauss–Legendre 8-point, 60 subintervals"* and L21 says the same plus *"systematic error, bounded to < 1 ppm"*. Required change: replace "60 subintervals" / "60-segment" with "a single 8-point Gauss–Legendre panel on `[0, x]` (no subdivision)" in **both** lines, and re-scope the `< 1 ppm` bound to the **θ** discrepancy while quoting the function-level relative error `6.63 ppm` at `N_e=16`. `governance` L20's `1.16e-14` figure is **already correct** and needs no change. Contested by `2026-09-28-fix-a2-a3-a4-residual-precision-claims` (edits L26 + L52) — apply only after that change is archived.
- [x] 9.2 **P6 — `wayfinder` L233 + L274-276.** Both make unframed `< 1e-9` claims that are false in the true closed-form frame. Required change: tag both with the reference frame, as L235 already does — impl-internal `< 1e-9` holds (`1.16e-14`), true closed-form yields `4.15e-7` (N_e=16) / `1.43e-9` (N_e=64) and does **not** meet `< 1e-9` at N_e=16. Contested by two concurrent changes (this one at L240/L241, a2-a3-a4 at L235) — apply only after both are archived.
- [x] 9.3 **Accepted, still open:** no mechanical guard prevents a future edit from re-binding the 4dp literal to `abs=1e-6` (Decision 4). Revisit if this defect class recurs again.

