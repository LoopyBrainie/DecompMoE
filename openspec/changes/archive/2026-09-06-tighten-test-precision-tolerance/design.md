## Context

The `/code-review` audit of the DecompMoE test suite surfaced 4 LOW-severity precision gaps in `tests/test_config.py` and `tests/test_sphere.py` that violate `CLAUDE.md` §6 第 8 条. See proposal.md - Why for the audit's motivation and the list of findings.

Current state (verbatim line refs):

- `tests/test_config.py::test_total_param_estimate` (L53-67): 3 raw `==` integer checks at L64 (`total == 452_329_984`), L65 (`active == 100_008_448`), L67 (`_router_params_per_layer(cfg) == 32_896`). L64/L65 embed `f"total {total} != ..."` and `f"active {active} != ..."` — not the canonical `f"actual={...}"` form.
- `tests/test_config.py::test_flops_per_layer_exact_33554432` (L70-86): 2 raw `==` integer checks at L80 (`per_layer * 4 == 134_217_728`) and L81 (`per_layer == 33_554_432`). No failure message.
- `tests/test_sphere.py::test_voronoi_monotone_in_ne` (L88-93): 2 bisection asserts at L90 (`pytest.approx(1.173547, abs=1e-4)`) and L91 (`pytest.approx(1.165848, abs=1e-4)`). **L90 literal `1.173547` is a 6dp truncation error** — actual bisection is `1.1735482746999482` (run via `PYTHONPATH=src uv run python`), `1.1735482747 - 1.173547 = 1.27e-6 > abs=1e-6` upper bound. L91 literal `1.165848` is fine (`2.97e-7` off bisection `1.1658482974`, within `abs=1e-6`).
- `tests/test_sphere.py::test_voronoi_canonical_N_e_dependence` (L138-152): 1 bisection assert at L148 (`pytest.approx(1.020507, abs=1e-4)`). Literal `1.020507` is fine (`1.66e-7` off bisection `1.0205068336`, within `abs=1e-6`).

The bisection precision witness already exists: `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` (L64-74) proves `|½ · I_{sin²θ}(7.5, 0.5) − 1/N_e| < 1e-9` for N_e ∈ {16, 17, 64}. Through the implicit function theorem on `f(θ) = ½·I_{sin²θ}(7.5, 0.5) − 1/N_e` with numerical derivative `f'(θ*) ≈ 0.488` at `θ* ≈ 1.17355 rad` (verified via `mpmath` 30-decimal-precision finite difference; the originally claimed closed form `f'(θ*) ≈ sin(2θ*)/(2 sin θ*)` evaluates to `0.387` and is **wrong** — the correct closed form is `f'(θ) = sin^{14}(θ) / B(7.5, 0.5)` ≈ 0.488, matching the numerical value to 13+ digits), a 1e-9 residual bound on `f` translates to `|Δθ| ≈ 1e-9 / |f'(θ*)| ≈ 2.05e-9` on `θ`. Therefore `abs=1e-6` is comfortably 3 decades above the bisection noise floor.

The spec-vs-bisection tension (post spec reversion): `wayfinder/spec.md` L189 currently states `θ_Voronoi(16, 16) ≈ 67.24° (1.1736 rad)` per the degree-to-radian conversion-consistency perspective; the bisection returns `1.1735482747 rad`. The two literals differ by `|1.1736 - 1.1735482747| = 5.17e-5`, which is an **independent rounding artifact at 4dp**: the spec literal rounds `67.24° × π/180 = 1.1735593890` to `1.1736`, while the bisection rounds `1.1735482747` to `1.1735`. This tension is the explicit motivation for `test_voronoi_rad_precision_alignment` asserting the conversion identity at `abs=1e-4` rather than bisection-precision at `abs=1e-6`. Both perspectives coexist in the test suite; this change brings the LOW-3 and LOW-4 sites into the bisection-precision perspective.

## Goals / Non-Goals

**Goals:**
- Replace raw integer `==` with `pytest.approx(value, abs=0)` in 2 test functions (5 assertions total: L64, L65, L67, L80, L81 of `tests/test_config.py`).
- Tighten `pytest.approx(..., abs=1e-4)` to `abs=1e-6` in 2 test functions (3 assertions total: L90, L91, L148 of `tests/test_sphere.py`); additionally correct L90's literal `1.173547` → `1.173548` to fix the 6dp truncation error (the literal at `1.173547` is `1.27e-6` off actual bisection `1.1735482747`, which would silently break `abs=1e-6` tightening).
- Normalize the failure-message convention to `f"actual={...}"` per `CLAUDE.md` §3 across the 5 integer assertions touched (the 3 bisection assertions already use `f"got {actual}"` — kept as-is, since `pytest.approx` failure output already shows the comparison cleanly; tightening the convention only for integer guards where `actual=` is most useful).
- Make all 4 changes independently verifiable by running `uv run pytest tests/test_config.py tests/test_sphere.py -v` (8 touched assertions) and `uv run pytest tests/ -v` (full regression).

**Non-Goals:**
- Not adding new tests (no `test_voronoi_with_tighter_tolerance` etc.) — surgical change only, per `CLAUDE.md` §3 ("Touch only what you must").
- Not refactoring the production arithmetic (no `compute_total_and_active` / `flops_per_token` / `canonical_voronoi_angle` rewrite).
- Not changing the bisection algorithm or its tolerance.
- Not touching `test_voronoi_residual_below_1e_minus_9` (it already enforces `< 1e-9` and is the precision witness).
- Not touching `test_voronoi_rad_precision_alignment` (it addresses the spec-degree-conversion-identity perspective — `1.1736 rad = 67.24° × π/180` — at `abs=1e-4`; this is a complementary perspective to the bisection-precision perspective tightened by LOW-3/LOW-4, and they coexist).
- Not touching other tests in `tests/test_config.py` or `tests/test_sphere.py` that already meet the precision bar (e.g. `test_flops_total_exact_134217728` L84-86 uses `==` on `134_217_728` — see Risks for why this is left out of scope of this change).
- Not modifying the `wayfinder/spec.md` spec literal for `θ_Voronoi(16, 16) ≈ 67.24° (1.1736 rad)` (L189) — the conversion-consistency perspective is intentional, per the post-reversion audit, and `test_voronoi_rad_precision_alignment` enforces it.

## Decisions

### Decision 1: `abs=0` for closed-form integer claims (LOW-1, LOW-2)

**Choice**: Replace `assert int_value == constant` with `assert int_value == pytest.approx(constant, abs=0)`, embedding `f"actual={int_value}"` in the message.

**Rationale**: `CLAUDE.md` §6 第 8 条 requires `pytest.approx(..., abs=...)` for all spec-anchored closed-form numerical claims. For integer-valued exact claims, `abs=0` is mathematically equivalent to `==` but expresses the contract as "spec says this exact value" rather than "Python int comparison happens to hold". If a future refactor of `compute_total_and_active` or `flops_per_token` returns `float` (e.g. via `P_emb + L * (4 * d_model**2 + ...) / 1.0`), `pytest.approx(..., abs=0)` produces a clear failure message (`actual=452329984.0 != 452329984 (abs=0)`) whereas raw `==` would either fail with a generic assertion error or, worse, coerce silently and pass despite the algorithmic change. `abs=0` is the canonical pytest idiom for "exact integer equality" and aligns with `tests/test_loss.py`'s `pytest.approx(value, abs=...)` style for closed-form `α=0.01`, `N_e=16`, etc.

**Alternatives considered**:
- (a) Leave as `==` — rejected: violates `CLAUDE.md` §6 第 8 条.
- (b) `pytest.approx(..., abs=1)` — too loose, accepts wrong answers.
- (c) Convert constants to `float` and use `rel=...` — over-engineered; `abs=0` on `int == int` is the canonical pytest form.

### Decision 2: `abs=1e-6` for bisection Voronoi angles (LOW-3, LOW-4), with literal correction for LOW-3 (16,16)

**Choice**: Tighten `abs=1e-4` to `abs=1e-6` for `pytest.approx(theta, ...)` on bisection outputs. Also correct L90's literal from `1.173547` to `1.173548` (the 6dp bisection value `1.1735482746999482` rounded), since `1.173547 - 1.1735482747 = -1.27e-6` exceeds the new `abs=1e-6` upper bound.

**Rationale**: The bisection witness `test_voronoi_residual_below_1e_minus_9` proves `|residual| < 1e-9` for N_e ∈ {16, 17, 64}. Via implicit function theorem, the bisection precision on `θ` itself is also ~1e-9. Therefore `abs=1e-6` is 3 decades above the noise floor and provides robust detection of any bisection regression (e.g., accidental tolerance widening in the implementation, wrong literal in a future refactor). The new `abs=1e-6` tolerance, paired with bisection-6dp literals (`1.173548`, `1.165848`, `1.020507` — each within `3e-7` of actual bisection output), distinguishes the **bisection-precision perspective** from the **spec-degree-conversion perspective** (`1.1736 rad = 67.24° × π/180`, asserted separately at `abs=1e-4` by `test_voronoi_rad_precision_alignment`). The two perspectives are mathematically different (bisection rounds to `1.1735` at 4dp; spec-degree-conversion rounds to `1.1736` at 4dp), and both perspectives are needed: bisection-precision tests catch bisection regressions; conversion-identity tests catch spec-degree-rounding regressions.

**Literal correction specifics**: The existing test literal `1.173547` (L90) was a 6dp truncation of the actual bisection value `1.1735482747` — i.e., the original test author wrote `1.173547` but the bisection's true 6dp round is `1.173548` (since `1.1735482747` is closer to `1.173548` than to `1.173547`). The original `abs=1e-4` tolerance masked this truncation (`|1.1735482747 - 1.173547| = 1.27e-6 < 1e-4` ✓), but tightening to `abs=1e-6` exposes the bug: the literal `1.173547` is now `1.27e-6 > 1e-6` away from bisection, which would fail. The fix is to correct the literal to `1.173548` (the bisection 6dp round). This is a **bug fix** disguised as a tightening — the original test was silently relying on a loose tolerance to mask a literal error.

**Alternatives considered**:
- (a) `abs=1e-7` — too tight, couples test to implementation noise floor; if bisection tolerance is ever relaxed to `1e-8` for performance, tests start flaking.
- (b) `abs=1e-8` — same risk.
- (c) `abs=1e-5` — too loose, would accept `1.1736 rad` spec-degree-conversion literal.
- (d) `abs=1e-9` — matches witness exactly but locks test to bisection precision, fragile.
- (e) Keep literal `1.173547` and use `abs=5e-6` (just above the truncation gap) — rejected: explicitly accepts the literal error rather than fixing it; the test would still mask future 6dp-truncation errors.

### Decision 3: `f"actual={...}"` embedded in integer guards only (not bisection)

**Choice**: Embed `f"actual={...}"` in the 5 integer assertions touched by LOW-1, LOW-2. Do NOT modify the 3 bisection assertions' existing `f"got {actual}"` messages.

**Rationale**: `CLAUDE.md` §3 ("失败时优先看 assert 内嵌的 `f"actual={...}"` 输出") establishes this as the project's standing convention for numerical assertions. The integer assertions are the higher-value normalization target because:
1. `pytest.approx(value, abs=0)` failures on `int` vs `float` mismatches benefit most from an explicit `actual=` marker (otherwise pytest's diff shows `<class 'float'> 452329984.0 != 452329984`, which is harder to grep than `actual=452329984.0`).
2. The 3 bisection assertions already embed `f"got {actual}"` (e.g. `f"got {theta_16}"`) and pytest's `assert` rewriting for `pytest.approx` already produces a side-by-side comparison in the failure output — adding `f"actual={...}"` would be redundant noise. Surgical-change principle (`CLAUDE.md` §3) wins: don't touch what already meets the convention.

**Alternatives considered**:
- (a) Leave existing message formats — rejected for LOW-1, LOW-2 (inconsistent with project convention; integers are most error-prone to debug).
- (b) Use `pytest.fail(f"actual={...}, expected={...}")` instead of `assert` — over-engineered; pytest's `assert` rewriting already produces a comparison diff, and `pytest.fail` would lose pytest's auto-diff.
- (c) Unify all 8 touched assertions on `f"actual={...}"` — rejected per surgical-change principle; bisection messages are already useful.

### Decision 4: `test_flops_total_exact_134217728` left untouched

**Choice**: Do NOT tighten `tests/test_config.py::test_flops_total_exact_134217728` (L84-86, `assert config.flops_per_token(...) == 134_217_728`) in this change.

**Rationale**: This test is functionally equivalent to the LOW-2 assertion `per_layer * 4 == 134_217_728` at L80 of the same file (both verify the same closed-form constant `134_217_728`), and would be a natural follow-up — but it was NOT in the audit findings (the audit named only `test_flops_per_layer_exact_33554432`, not `test_flops_total_exact_134217728`). Touching it would expand the change scope beyond the audit's LOW-1..LOW-4 envelope, violating `CLAUDE.md` §3 ("Touch only what you must"). It is a candidate for a follow-up change if and when the user reviews this delta.

**Alternatives considered**:
- (a) Include `test_flops_total_exact_134217728` in LOW-2 — rejected: not in audit findings; would expand scope.
- (b) Submit a separate follow-up change for `test_flops_total_exact_134217728` — out of scope for this propose workflow; left as future-work note in design.

**Tension with `CLAUDE.md` §6 第 8 条 acknowledged**: This decision is in tension with the global `CLAUDE.md` §6 第 8 条 rule that "`spec 中每个含具体数值的算式都必须有 `pytest.approx(..., abs=...)` 直接对账`". Under a strict reading of §6 第 8 条, `test_flops_total_exact_134217728` L86's raw `==` on `134_217_728` is a `CLAUDE.md` violation regardless of audit scope, and the same logic applies to other pre-existing `==` integer checks across the test suite. This change deliberately narrows the §6 第 8 条 enforcement to the LOW-audited sites (L80/L81) to keep the change scope bounded per `CLAUDE.md` §3 ("Touch only what you must"); the remaining `==` integer checks (including `test_flops_total_exact_134217728` L86 and any pre-existing integer `==` outside the audit envelope) remain a `CLAUDE.md` §6 第 8 条 violation until a future change audits them. The new `Test Guard Precision for Closed-Form Numerical Claims` requirement applies **prospectively** to NEW tests authored after this requirement is archived; pre-existing `==` integer checks are exempt under the "existing tests that already meet the precision bar are not required to be tightened" clause in the requirement's prose. A future change should be opened to systematically tighten all remaining `==` integer checks across `tests/test_config.py` (and other test modules) for full §6 第 8 条 compliance — this is recorded as `tasks.md` §4.1 follow-up.

### Decision 5: LOW-3 literal correction (`1.173547` → `1.173548`) IS in scope

**Choice**: The LOW-3 (16,16) literal correction is treated as part of LOW-3 (no separate audit ID), because (a) the literal `1.173547` is a 6dp-truncation bug that the original `abs=1e-4` tolerance silently masked, and (b) the abs tightening to `abs=1e-6` necessarily exposes the bug, so the literal fix is bundled into the LOW-3 apply cycle.

**Rationale**: Per `CLAUDE.md` §3 ("When your changes create orphans: Remove imports/variables/functions that YOUR changes made unused. ... The test: Every changed line should trace directly to the user's request"), the literal correction is a direct consequence of the abs tightening — without the fix, the LOW-3 apply step would fail. Bundling keeps the change atomic (one task per LOW site) rather than fragmenting into a separate "fix LOW-3 literal" task that would itself need a separate audit ID.

**Alternatives considered**:
- (a) Keep literal `1.173547` and use `abs=2e-6` (just above the truncation gap) — rejected: preserves the literal error rather than correcting it; the test continues to silently mask the 6dp-truncation bug.
- (b) Open a separate audit item for the literal correction — rejected: over-formalization; the literal correction is a single-line change with clear technical justification (bisection 6dp round).

## Risks / Trade-offs

- **[Risk]** `pytest.approx(int_value, abs=0)` raises `TypeError` if a non-numeric is passed — but this is true of `==` too and is desirable behavior. → No mitigation needed.
- **[Risk]** A future `compute_total_and_active` refactor returns `float` instead of `int` (e.g. via `P_emb + L * (4 * d_model**2 + N_e * P_expert + P_router/layer) / 1.0`) — then `abs=0` correctly catches the regression with a clear `actual=452329984.0 != 452329984 (abs=0)` message. → This is the intended guard, not a bug.
- **[Risk]** `abs=1e-6` couples the test to bisection precision. If bisection is later replaced with Newton's method achieving `1e-12`, no test change is needed (1e-6 still passes). If bisection tolerance widens to `1e-7` for performance, the test would fail. → Mitigation: bisection tolerance is not in scope for this change; if it's later relaxed, the witness `test_voronoi_residual_below_1e_minus_9` (currently `< 1e-9`) is the natural place to widen alongside, and `abs=1e-6` remains safely above.
- **[Risk]** The proposal changes 8 assertions across 2 test files — combined diff size is small (≤ 20 lines changed including message normalization and 1 literal correction), so merge conflict risk is low. → No mitigation needed.
- **[Risk]** `test_flops_total_exact_134217728` (L84-86) is left with a raw `==` integer comparison on the same closed-form constant `134_217_728` that this change tightens at L80 of `test_flops_per_layer_exact_33554432`. The two tests will have inconsistent guard strength on the same constant. → Mitigation: noted as future work; both tests still pass on the current implementation, so no functional regression today.
- **[Risk]** The LOW-3 literal correction `1.173547` → `1.173548` is not in the original audit findings (LOW-3 audit only named the `abs=1e-4` → `abs=1e-6` tightening). The literal correction is treated as part of the LOW-3 apply step (per Decision 5) because the abs tightening necessarily exposes the bug. → Mitigation: Decision 5 documents the bundling rationale; if the user prefers separate audit IDs for literal corrections, future changes can split them out.
- **[Risk]** The spec-vs-bisection tension (`1.1736` vs `1.1735482747` ↔ `1.1735` at 4dp) means a future contributor might "fix" the apparent discrepancy by changing EITHER the spec literal OR the bisection literal, breaking the conversion-identity / bisection-precision duality. → Mitigation: `test_voronoi_rad_precision_alignment` enforces the conversion-identity perspective at `abs=1e-4`; this change's `test_voronoi_monotone_in_ne` enforces the bisection-precision perspective at `abs=1e-6`. Both tests must pass for the dual-perspective invariant to hold. The new `Test Guard Precision for Closed-Form Numerical Claims` requirement documents the duality.
