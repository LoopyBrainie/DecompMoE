# Independent Numerical Verification — fix-spec-resurrection-math-direction-2026-09-12

**Date:** 2026-09-12 (apply phase)
**Verifier:** apply-time independent check
**Scope:** verify the three closed-form claims newly asserted in the corrected `decompmoe-skeleton` spec text (Scenario `should_resurrect semantic interpretation (per-step vs avg-window)`, L248) against hand-computed arithmetic and machine-verified pytest.approx assertions.

---

## (a) `flag_step ⟹ flag_avg` algebra proof (L248 amended text)

**Claim** (verbatim from corrected L248):
> `∀ j: H[j][i] < T` ⇒ `Σ_{j=0..consec-1} H[j][i] < consec · T` ⇒ `(1/consec) · Σ_{j=0..consec-1} H[j][i] < T`

**Implication 1**: `∀ j: H[j][i] < T` ⇒ `Σ H[j][i] < consec · T`
- Hand-verdict: **VALID**. The hypothesis asserts each of `consec` terms is strictly less than `T`. Summing `consec` strict-inequality inequalities (each term < T) preserves the strict-inequality direction: total < `consec · T`. No division-by-zero risk (consec ≥ 1).
- Algebraic identity used: sum of `n` numbers each `< c` is `< n·c` (transitivity of `<` over real addition, `n` times).

**Implication 2**: `Σ H[j][i] < consec · T` ⇒ `(1/consec) · Σ H[j][i] < T`
- Hand-verdict: **VALID**. Division by a positive constant (`consec ≥ 1`) is strictly order-preserving on real numbers.
- Algebraic identity used: if `a < b · c` and `c > 0`, then `a/c < b` (multiplication by `1/c` is monotone on `(0, ∞)`).

**Conclusion**: Both implications valid ⇒ the full chain `flag_step ⟹ flag_avg` is **universally true**, as the corrected spec now states. The previous spec text claiming "is not universally true" was mathematically incorrect; elementary algebra refutes it directly. ✅

---

## (b) Counterexample A — `H = [0.005]*199 + [0.99]` avg-window mean

**Closed-form** (per spec L250): `(199 · 0.005 + 1 · 0.99) / 200 = 1.985 / 200 = 0.009925`

**Hand-arithmetic check**:
- `199 · 0.005 = 0.995` ✓
- `1 · 0.99 = 0.99` ✓
- `0.995 + 0.99 = 1.985` ✓
- `1.985 / 200 = 0.009925` ✓ (exact, terminating decimal)

**Threshold comparison**: `0.009925 < 1/32 = 0.03125` ⇒ TRUE ⇒ avg-window TRIGGER ✅
**Per-step**: last snapshot `0.99 < 0.03125` FALSE ⇒ NO TRIGGER ✅

**Machine verification** (test 3.1 ran `pytest tests/test_safeguards.py::test_should_resurrect_per_step_is_strict_subset_of_avg_window_for_monotonic_history`):
- `avg_mean_A == pytest.approx(0.009925, abs=1e-6)` → **PASSED** ✓
- `res_A == set()` (per-step NO TRIGGER) → **PASSED** ✓

**Verdict**: Closed-form matches hand-arithmetic; machine verification passes; spec text matches. ✅

---

## (c) Counterexample B — `H = [0.05]*199 + [0.005]` avg-window mean

**Closed-form** (per spec L252): `(199 · 0.05 + 1 · 0.005) / 200 = 9.955 / 200 = 0.049775`

**Hand-arithmetic check**:
- `199 · 0.05 = 9.95` ✓
- `1 · 0.005 = 0.005` ✓
- `9.95 + 0.005 = 9.955` ✓
- `9.955 / 200 = 0.049775` ✓ (exact, terminating decimal)

**Threshold comparison**: `0.049775 < 0.03125` ⇒ FALSE ⇒ avg-window NO TRIGGER ✅
**Per-step**: first 199 snapshots `0.05 < 0.03125` FALSE ⇒ NO TRIGGER ✅

**Machine verification** (test 3.1 ran the same test):
- `avg_mean_B == pytest.approx(0.049775, abs=1e-6)` → **PASSED** ✓
- `res_B == set()` (per-step NO TRIGGER) → **PASSED** ✓

**Verdict**: Closed-form matches hand-arithmetic; machine verification passes; spec text matches. ✅

---

## Summary

| Check | Spec value | Hand-arithmetic | Machine (pytest) | Verdict |
|---|---|---|---|---|
| (a) flag_step⟹flag_avg algebra | universally true | 2 implications valid | (logical, no pytest needed) | ✅ |
| (b) Counterexample A mean | 0.009925 | 0.009925 | pytest.approx(0.009925, abs=1e-6) PASS | ✅ |
| (c) Counterexample B mean | 0.049775 | 0.049775 | pytest.approx(0.049775, abs=1e-6) PASS | ✅ |

All three closed-form claims in the corrected `decompmoe-skeleton` L248 paragraph match hand-computed arithmetic AND machine-verified pytest assertions. The math direction correction (per-step ⊊ avg-window) is self-consistent across spec text, code implementation, and pytest guard. Spec ↔ code ↔ test三方自洽达成** ✅ — ready for archive.

---

## Appendix — Review Follow-up: Sub-assertions 4 + 5 (gap-closure)

> Added post-apply per `/code-review` workflow finding (Gap A + B, both Low severity). Both pure test additions; no spec / source changes.

### (d) Sub-assertion 4 — Universal-direction positive example on non-constant H

**History**: `H = [0.001]*199 + [0.030]` (every snapshot has every f_i strictly < threshold 1/32 = 0.03125).
**Expected**: per-step TRIGGERs all 16 experts; avg-window also TRIGGERs (universal direction `flag_step ⟹ flag_avg` demonstrated on non-constant history).

**Hand-arithmetic for avg-window mean**:
- `199 × 0.001 = 0.199` ✓
- `1 × 0.030 = 0.030` ✓
- `0.199 + 0.030 = 0.229` ✓
- `0.229 / 200 = 0.001145` ✓ (exact, terminating decimal)

**Threshold comparison**: `0.001145 < 1/32 = 0.03125` ⇒ TRUE → avg-window TRIGGER ✅
**Per-step**: every snapshot has `0.001 < 0.03125` AND `0.030 < 0.03125` ⇒ TRIGGER all 16 ✅

**Machine verification**:
- `avg_mean_C == pytest.approx(0.001145, abs=1e-6)` → **PASSED** ✓
- `res_C == set(range(N_e))` (all 16 experts flagged) → **PASSED** ✓

**Verdict**: Closed-form matches hand-arithmetic; machine verification passes; spec text matches. Gap A closed. ✅

### (e) Sub-assertion 5 — Strict less-than boundary (`f_i == threshold` MUST NOT trigger)

**History**: `H = [1/32]*250` (every snapshot has every f_i EXACTLY at threshold 1/32 = 0.03125).
**Expected**: per-step NO TRIGGER (strict `<` rejects equality); avg-window NO TRIGGER (mean equals threshold, NOT strictly less). Both agree on NO-TRIGGER at the boundary, but per-step rejects equality **element-wise** (any snapshot at threshold suppresses resurrection).

**Hand-arithmetic for avg-window mean**:
- Every snapshot contributes exactly `1/32 = 0.03125`
- Mean of 250 copies of `0.03125` = `0.03125` exactly (FP-exact)

**Threshold comparison**: `0.03125 < 0.03125` ⇒ FALSE → avg-window NO TRIGGER ✅
**Per-step**: `0.03125 < 0.03125` is FALSE for every (j, i) ⇒ NO TRIGGER ✅

**Machine verification**:
- `avg_mean_boundary == pytest.approx(threshold, abs=1e-12)` (sanity: mean equals threshold exactly) → **PASSED** ✓
- `not (avg_mean_boundary < threshold)` (sanity: avg-window would NOT TRIGGER because boundary equality fails strict `<`) → **PASSED** ✓
- `res_boundary == set()` (per-step NO TRIGGER) → **PASSED** ✓

**Verdict**: Boundary semantics locked. A future regression weakening `<` to `<=` would resurrect at boundary equality and break this assertion. Gap B closed. ✅

### Updated Coverage Summary

| Check | Spec value | Hand-arithmetic | Machine (pytest) | Verdict |
|---|---|---|---|---|
| (a) flag_step⟹flag_avg algebra | universally true | 2 implications valid | (logical, no pytest needed) | ✅ |
| (b) Counterexample A mean | 0.009925 | 0.009925 | pytest.approx(0.009925, abs=1e-6) PASS | ✅ |
| (c) Counterexample B mean | 0.049775 | 0.049775 | pytest.approx(0.049775, abs=1e-6) PASS | ✅ |
| (d) Sub-assertion 4 mean (universal direction +) | 0.001145 | 0.001145 | pytest.approx(0.001145, abs=1e-6) PASS | ✅ |
| (e) Sub-assertion 5 boundary mean | 0.03125 | 0.03125 | pytest.approx(0.03125, abs=1e-12) PASS | ✅ |

**All five mathematical claims** now have both hand-arithmetic and machine-verified pytest.approx coverage. The algebra proof (a) is backed by a non-constant positive example (d); the strict less-than semantics is locked by (e). The previously open gaps (universal-direction non-constant positive case, strict less-than boundary) are closed.

**Math principle coverage**: 🟢 Strong (~95%):
- 闭式常数: 100% (5/5 sub-assertions)
- 代数方向: 100% (per-step ⊊ avg-window 三向验证 + algebra proof + positive + boundary)
- 边界严格语义: 100% (Sub-assertion 5 直接钉死)
- spec ↔ code ↔ test 三方自洽 ✅ — ready for archive.