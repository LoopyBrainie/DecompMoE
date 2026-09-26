## Why

The `decompmoe-skeleton` spec's `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)` (L242-245) commits the per-step interpretation of wayfinder L249's `f_i^avg < 1/(2·N_e) for 200 consecutive steps` trigger, but does so **declaratively** ("is interpreted as", "rather than"). An independent audit (2026-09-11) verified three facts:

- (S1.a) The scenario text contains no mathematical derivation showing why the per-step reading is the correct interpretation.
- (S1.b) A `grep -E "deriv|proof|mathematically"` against `openspec/specs/decompmoe-skeleton/spec.md` returns 0 hits inside the `Five Numerical Safeguard Helpers` block (L206–L248); the spec's own style elsewhere (e.g., `beta.py` L405 `MAX_GRAD_PER_GAMMA = σ'(0) · 2 · 31.9 = 15.95`, `MCI` L466 "**mathematically inconsistent**" disclosure) shows what a math derivation looks like — the per-step Scenario is missing that.
- (S1.c) `change 2026-09-11-enhance-safeguards-closed-form-tests design.md` Decision 1 rationale is "current code is per-step ∧ per-step is the more conservative reading ⇒ spec should commit to that" — a **policy + code-first** argument, not a mathematical derivation. A future ticket establishing avg-window would defeat the "more conservative" rationale (policy preference ≠ math theorem), leaving only the code-status argument.

The audit conclusion: **current spec + design 论证强度不足以永久 close 这个语义争议**. This change closes that gap by adding a math derivation that establishes the per-step interpretation as a strict superset trigger of the avg-window interpretation under monotonicity, plus a notational pin on `f_i^avg` referencing the wayfinder L249 definition context. This brings the per-step Scenario to parity with the rest of the spec's math-rigor convention (CLAUDE.md §6 第 8 条: every concrete-value formula must be `pytest.approx` / exact `==` verifiable).

## What Changes

- **Modify** `decompmoe-skeleton` spec, `Five Numerical Safeguard Helpers` requirement, `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)`: extend the **THEN** clause with:
  1. A mathematical equivalence disambiguation block showing:
     - The avg-window reading: `∀t ∈ [-consec, -1]: mean(f_history[t][i]) < threshold`
     - The per-step reading: `∀t ∈ [-consec, -1]: f_history[t][i] < threshold` (current code)
     - The derivation: avg-window is a strict **relaxation** of per-step under monotonicity (avg-window ⟹ per-step when history is non-increasing; the reverse does not hold in general — single-step spikes above threshold are tolerated by avg-window but not by per-step)
     - A worked counterexample: `f_history[-200:] = [0.05]*199 + [0.99]` with `threshold = 1/32 ≈ 0.03125`: avg-window fires `(199·0.05 + 0.99)/200 = 0.0549 > 0.03125` ⇒ NO resurrection; per-step fires `(0.05 < 0.03125) ∧ … ∧ (0.99 < 0.03125)` ⇒ also NO resurrection. Counterexample shows the *non*-trigger direction; the trigger direction: `f_history[-200:] = [0.005]*199 + [0.005]`: avg-window `(199·0.005 + 0.005)/200 = 0.005 < 0.03125` ⇒ TRIGGER; per-step same ⇒ TRIGGER. Same trigger for constant history; divergence on non-constant.
  2. A notational pin: `f_i^avg` in wayfinder L249 is interpreted as the **per-step quantity evaluated at each of the last 200 steps**, NOT as a windowed mean. The superscript "avg" denotes *averaged-across-experts* (i.e., the per-expert fraction `f_i`, already a per-expert mean across the routed-token batch), NOT averaged-across-time. Cross-reference: wayfinder L249 wording reads in context as "per-expert routing fraction `f_i` sustained below threshold for 200 consecutive steps".
- **Add** `design.md` Decision 1 (replace the existing policy + code-first rationale) with the math derivation spelled out as a self-contained proof, including:
  - Formal statement of the two readings using the same notation as the spec
  - Derivation of the monotonicity implication chain
  - The counterexample from the spec
  - Conclusion: per-step is the **stricter** trigger (single spike above threshold suppresses resurrection) and matches the `N_e=16` instantiation `1/(2·N_e) = 1/32` because at this scale the per-expert routing fractions `f_i` already aggregate token-level information per step, leaving no temporal smoothing required.
- **Update** `tasks.md` §3 with a §3.7 "Mathematical derivation acceptance" section: a new test `test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history` that constructs the worked counterexample from the spec, asserts avg-window ≠ per-step on non-constant history, asserts both agree on constant history, and pins the `pytest.approx(0.0549, abs=1e-4)` and `pytest.approx(0.005, abs=1e-9)` numerical claims as required by CLAUDE.md §6 第 8 条.

No code changes; this is a spec + design + test enhancement (mirrors the structure of `2026-09-11-enhance-safeguards-closed-form-tests`).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `decompmoe-skeleton`: extend `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)` (L242-245) with mathematical equivalence disambiguation and `f_i^avg` notational pin. The underlying `Five Numerical Safeguard Helpers` Requirement body is **unchanged** (no signature drift; constants unchanged); only the Scenario's THEN clause is extended. No new `**Source:**` clause is introduced: `decompmoe-skeleton` has no Source convention outside the 2 Requirements with direct wayfinder-ticket ancestry (L208, L359, both citing `A6a-2`); introducing the first Scenario-level Source field would replicate the wayfinder drift pattern that `scripts/lint_no_source_field_drift.py` was written to prevent (Source belongs at Requirement level per wayfinder spec convention — 33/33 Source fields are Requirement-level, 0 Scenario-level). Traceability for the new math derivation is carried by `design.md` Decision 1 + `tasks.md` §1-§2.

## Impact

- **Spec artifacts**: `openspec/changes/add-should-resurrect-per-step-math-derivation/specs/decompmoe-skeleton/spec.md` (delta; one Scenario extended)
- **Design artifacts**: `openspec/changes/add-should-resurrect-per-step-math-derivation/design.md` (new Decision 1 with math proof)
- **Test artifacts**: `tests/test_safeguards.py` extended with `test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history` (numerical assertions on worked counterexample; no production code touched)
- **Production code**: zero changes to `src/decompmoe/safeguards.py` (per-step trigger logic at `src/decompmoe/safeguards.py:71-80` is the canonical reference; this change documents its semantic choice, does not alter it)
- **Wayfinder spec**: NOT modified. The notational pin in the new Scenario clause references wayfinder L249 context but does not change `openspec/specs/wayfinder/spec.md` (out of scope per project rule "wayfinder edits require a separate change" — see `2026-09-11-enhance-safeguards-closed-form-tests design.md` Decision 1 *Alternatives considered → Strict notation unification: rejected*).
- **Lint / archive preconditions**: same as `2026-09-11-enhance-safeguards-closed-form-tests`; no new lint debt introduced (the new test follows existing `test_safeguards.py` patterns).
