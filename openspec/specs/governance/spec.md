## Purpose

OpenSpec governance specs whose design origin is a `CLAUDE.md` amendment (or a commit amending `CLAUDE.md`) rather than any `wayfinder/tickets/*.md` ticket. This capability exists as a peer of `wayfinder` and `decompmoe-skeleton` so governance-origin Requirements do not have to lie about their `**Source:**` lineage by pointing at an unrelated `wayfinder/tickets/` entry. The `Source:` field convention for this capability is established in its first Requirement; future governance-origin Requirements MUST be filed under `governance`, not `wayfinder`, per the migration rule in `wayfinder/spec.md` req-34 "governance-origin requirements trigger lint failure" Scenario.

## Requirements

<a id="req-gov-1"></a>

### Requirement: Test Guard Precision for Closed-Form Numerical Claims

The system MUST guard every spec-anchored closed-form numerical claim such that the **assertion form matches the numerical type** of the claim, per `CLAUDE.md` §6 第 8 条's "对账方式依数值类型二分" (amended by commit `bec147d` 2026-09-07 21:21:31 to introduce the integer-vs-float binary exemption; sync-amended in `CLAUDE.md` §3 by commit `83a0503` 2026-09-07 22:02:52). Concrete obligations:

1. **Closed-form integer claims** — claims whose values are exact integers (e.g. `P_total = 452_329_984`, `P_active = 100_008_448`, `P_router/layer = 32_896`, per-layer MoE FLOPs `33_554_432`, total MoE FLOPs `134_217_728 = 4 × 33_554_432`, per-head extraction MACs `33_168 = macs(8, 128, 16) = H_kv·(2·d_k·d_c + d_c[bias]) + H_kv·d_c[L2-step2] + H_kv·d_c[cross-head mean, step 3] + d_c[L2-step4]`, expert parameters `N_e · 3 · d_model · d_ffn = 16 · 3 · 1024 · 2048 = 100_663_296`) MUST use **bare `==` integer equality** (Python `int == int`) — NOT `pytest.approx(...)` in any form.  The reason is version-independence, not a formula. `pytest.approx` performs a FLOATING-POINT comparison of an integer, and its tolerance semantics depend on the pytest version. [measured on pytest 9.1.1 / python 3.14.8; pyproject.toml does not pin pytest, so this is environment-scoped; recomputable via change 2026-10-02-corr-pytest-approx-abs-semantics evidence/pytest_approx_semantics.py] When `abs` is supplied and `rel` is left at its default of `None`, the tolerance is EXACTLY `abs` -- the `tolerance` property returns before reaching the `max` branch -- so `abs=0` does NOT degenerate to a magnitude-scaled relative tolerance. Bare `==` is required because it is the only form whose zero tolerance is decidable and independent of the pytest version, at every magnitude.

2. **Closed-form float claims** — claims whose values carry floating-point rounding (e.g. bisection-derived Voronoi angles `θ_Voronoi(16, 16) ≈ 1.1735 rad`, FLOPs ratios involving divisions, percentile invariants from sampling) MUST use `pytest.approx(value, abs=...)` with the tolerance matching the closed-form computation's actual precision — NOT bare `==`. Bare `==` on a float closed-form claim would coerce silently and defeat the spec's "数值直接对账, 禁止文字断言" intent. **Exception — 4-decimal spec display literals**: a spec value displayed at 4 decimals is a *display form*, not a higher-precision claim, and is pinned at its own precision by exact `round(x, 4) == literal` — the rule `decompmoe-skeleton` req-6 already mandates for `θ_Voronoi` (`round(θ, 4) == 1.1735`). Such a literal MUST NOT be paired with an `abs=` tolerance wider than the 4dp half-unit `5e-5`, which is `2×` over-wide and admits values that do not round to the literal. The underlying higher-precision claim, where one is separately stated, is still guarded per this obligation.

3. **Bisection-derived Voronoi angles** (specialized float case) — claims whose test values come from `canonical_voronoi_angle(N_e, d_c)` (which solves `½ · I_{sin²θ}((d_c − 1)/2, 1/2) = 1/N_e` via bisection) MUST use `pytest.approx(value, abs=1e-6)` — NOT `abs=1e-4` or wider — because the bisection residual `|½ · I_{sin²θ}(7.5, 0.5) − 1/N_e|` at the canonical root is `< 1e-9` (measured the measured residual at the canonical literal is `1.4635872379108090131680874e-17` at N_e=16 and `1.9420345120803994000206689e-18` at N_e=64 This quantity is set by the bisection stopping criterion (|G - 1/N_e| < 1e-13), not by float64 precision; provenance is mpmath betainc(a, b, 0, x, regularized=True) at dps=60, reproducible via change 2026-10-02-repair-spell-numeric-literal-provenance evidence/_alpha_forensics.py.; `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`),  and because a 6dp TRUNCATED literal carries a truncation error strictly below `1e-6` (`5e-7` is the round-half-up half-unit, not the truncation bound: `trunc6(0.9999999) = 0.999999` has error `9e-7`, which exceeds `5e-7`). `1e-6` is therefore a defensible guard, but it is NOT the minimum the 6dp display format permits -- measured, `abs=4.3e-7` already passes for `1.173547`. The **canonical Voronoi half-angle** for `(N_e=16, d_c=16)` is `1.1735474259197175 rad`, the root of the defining equation rather than any implementation's output. The **spec-referenced test literals** are this canonical value **truncated** to 6dp (truncation, not rounding-half-up: `1.1735474259197175` truncates at the 7th decimal to `1.173547`, diff `4.259e-7`, within the `1e-6` tolerance).  Note that `pytest.approx(expected, abs=1e-6)` applies a tolerance of EXACTLY `1e-6`: the `rel` default is `None`, not `1e-6`, and the tolerance property returns the absolute tolerance before reaching the `max` branch. [measured on pytest 9.1.1 / python 3.14.8; pyproject.toml does not pin pytest, so this is environment-scoped; recomputable via change 2026-10-02-corr-pytest-approx-abs-semantics evidence/pytest_approx_semantics.py] The measured truncation diffs `4.259e-7` / `6.216e-7` / `8.248e-7` all sit below it, and the tolerance is NOT tightened. Of the three literals only TWO discriminate against a defective integrator: measured against the pre-fix outputs, `1.173547` is `1.275e-6` away and `1.165847` is `1.297e-6` away, both outside the applied criterion, whereas `1.020506` is only `8.34e-7` from its pre-fix output `1.0205068335735599` and therefore passes either way. The guard's discriminating power comes from the `(N_e=16)` and `(N_e=17)` literals; a regression that moves only the `(N_e=64)` value MUST be caught by the `round(θ, 4) == 1.0205` display guard or by the true-frame residual, not by this literal; the `(N_e=64, d_c=16)` literal is `1.0205068247837132` truncated to `1.020506`, and the `(N_e=17, d_c=16)` literal is `1.165847`. These literals are pinned at `tests/test_sphere.py::test_voronoi_monotone_in_ne` and `tests/test_sphere.py::test_voronoi_canonical_N_e_dependence` (restored by change `fix-review-findings-voronoi-precision-and-lineage`, after commit `3dd1104` had deleted them and left a tautological self-check). These test literals are distinct from the **canonical spec literal** `67.24° (≈ 1.1735 rad)` declared in Requirement 11 of `wayfinder/spec.md` (the bisection-perspective 4dp form of `1.1735474259197175`). This obligation's `abs=1e-6` scopes **angle** literals only: the derived `versine` `1 − cos θ` is not an angle claim, and is instead governed by the 4-decimal-display exception in obligation 2.

4. **Residual frame disambiguation** — claims of "< 1e-9" or similar precision bounds on bisection Voronoi output MUST specify the reference regularized incomplete beta implementation:
   - **impl-internal reference**: `src/decompmoe/sphere.py::_betainc_regularized` at the canonical value `1.1735474259197175 rad` yields `|½·I_{sin²θ}(7.5, ½) − 1/16| = 1.4635872379108090131680874e-17` This quantity is set by the bisection stopping criterion (|G - 1/N_e| < 1e-13), not by float64 precision; provenance is mpmath betainc(a, b, 0, x, regularized=True) at dps=60, reproducible via change 2026-10-02-repair-spell-numeric-literal-provenance evidence/_alpha_forensics.py. (`< 1e-9` ✓, verified by `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`).
   - **true closed-form reference** (mpmath, 4-argument form `betainc(a, b, 0, x, regularized=True)` — the 3-argument `betainc(a, b, x, regularized=True)` returns the COMPLEMENT `1 − I_x`, not `I_x`, and MUST NOT be used) at the same θ yields `1.4635872379108090131680874e-17` This quantity is set by the bisection stopping criterion (|G - 1/N_e| < 1e-13), not by float64 precision; provenance is mpmath betainc(a, b, 0, x, regularized=True) at dps=60, reproducible via change 2026-10-02-repair-spell-numeric-literal-provenance evidence/_alpha_forensics.py. (`< 1e-9` ✓).
   The two frames **MUST agree to `< 1e-9`**: the frames coincide exactly when `_betainc_regularized` conforms to its declared intent, so a divergence between them is itself a defect signal rather than a matter of which one to quote. Spec MUST still name the frame it uses — avoid silent reference-frame shifting. **Consequence**: no bisection Voronoi residual test may serve as its own independent guard on the integrator; the independent guard is the 6dp literal test of obligation 3, whose `(N_e=16)` and `(N_e=17)` truncated literals fail against a defective integrator (measured `1.275e-6` and `1.297e-6`, both outside the applied criterion, which is exactly `1e-6` (see obligation 3); the `(N_e=64)` literal does not discriminate — see obligation 3 for the split and for which guard covers it instead.

5. Every assertion described in obligations 1, 2, 3 and 7 (and the frame-disambiguation obligation 4) MUST embed `f"actual={...}"` in its failure message so a numerical regression surfaces the actual computed value at the assertion site (per `CLAUDE.md` §3 TDD convention).

6. **Tightening a test literal MUST NOT silently invalidate a stated proximity bound.** When a Scenario pins a 6dp test literal against a stated proximity bound, changing that literal MUST either (a) leave the bound satisfied, or (b) realign the bound to the actual precision the Scenario prescribes. A Scenario that carries a proximity bound numerically tighter than its own normative `pytest.approx(..., abs=...)` tolerance is **inconsistent with its own guard** — the bound is prose-only, carries no separate assertion, and MUST therefore be stated at the same magnitude as the normative tolerance rather than at an unverified tighter value. (For the bisection Voronoi Scenario the normative tolerance is `abs=1e-6`, so any stated proximity bound MUST be `1e-6`; the measured literal-to-canonical diffs are `4.259e-7` / `6.216e-7` / `8.248e-7` for `1.173547` / `1.165847` / `1.020506` respectively, so the third literal would violate a `3e-7` bound.)

7. **Monte-Carlo-derived statistical claims** (specialized non-closed-form case) — claims whose test values come from a RANDOMIZED ESTIMATOR rather than from a closed-form or deterministic root-find MUST use a **statistical tolerance derived from that estimator's own standard error**, and MUST NOT use bare `==` (the value is a random variable, not a constant to be pinned) and MUST NOT use the `abs=1e-6` of obligation 3 (which is calibrated to a deterministic bisection noise floor of `< 1e-9` and is therefore meaningless for a sampling estimator — it would be either vacuous or permanently red). Specifically the assertion MUST: (a) state, in a comment or docstring adjacent to the assertion, the estimator's standard error `σ` and the resulting tolerance, including the sample count and seed that produce it; (b) derive `σ` from the estimator's own structure rather than from an observed run, so the tolerance does not shrink to fit whatever the code happened to print; and (c) carry an `f"actual={...}"` message per obligation 5. Worked instance: `src/decompmoe/sphere.py::voronoi_angle` samples `VORONOI_AREA_SAMPLES = 1_000_000` probes and returns `θ̂ = (1/N_e)·Σ_i G⁻¹(A_i)`; at the MVP point `(N_e=16, d_c=16)` the derivation MUST respect the exact constraint `Σ_i A_i ≡ 1` — every probe is assigned to exactly one `argmax` owner, so `Σ_i n_i = M` identically and `Σ_i ε_i ≡ 0` for `ε_i := A_i − 1/N_e`. The first-order term of `θ̂ − G⁻¹(1/N_e)` therefore cancels EXACTLY; the leading fluctuation is second order, `(1/(2N_e))·g''·Σ_i ε_i²` with `g'' = [G⁻¹]'' = −G''/G'³ = −24.6207` and `G'(θ₀) = 0.488436` at the operating point, so `Var(Σ_i ε_i²) ≈ 2·N_e·(A(1−A)/M)²` and the spread scales as `1/M`, NOT `1/√M`. That gives a mean standard error of `1.461e-5°` and `5σ = 7.31e-5°`, corroborated by a measured cross-seed SD of `1.353e-5°` over 8 seeds. Treating the `N_e` cell areas as INDEPENDENT — which is what an earlier revision of this Obligation did — yields `5σ = 0.0355°`, `486×` too large, and MUST NOT be reintroduced. Obligations 1, 2 and 3 do not cover this class: obligation 1 is scoped to exact integers, obligation 2 to closed-form floats, and obligation 3 to values coming from `canonical_voronoi_angle` — the measurement layer is none of these, which is why this obligation is stated separately rather than folded into obligation 2.

**Policy lineage** (for future audit): `CLAUDE.md` §6 第 8 条 was amended by commit `bec147d` (2026-09-07 21:21:31) to introduce the integer-vs-float binary exemption ("pytest.approx(..., abs=...)（浮点闭式）或精确 `==`（整数闭式）"), and re-synced in `CLAUDE.md` §3 by commit `83a0503` (2026-09-07 22:02:52) which migrated the remaining `pytest.approx(..., abs=0)` integer sites to bare `==`. This change `tighten-closed-form-eq-integer-checks` originally proposed `pytest.approx(..., abs=0)` as the canonical integer-closed-form form; the **policy reversal in commits `bec147d` + `83a0503` is the authoritative outcome** per `CLAUDE.md` §2 truth-source hierarchy (`CLAUDE.md` §6 第 8 条 > this spec delta > wayfinder tickets > code). This Requirement formalizes the post-`83a0503` state so future audit trails can trace the integer-vs-float binary exemption to its policy commits. Additionally, obligation 6 was added by change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` (Decision 1) in response to a stale-bound defect in the bisection Voronoi Scenario: that Scenario originally stated each 6dp test literal lies "within `3e-7`" of the corresponding bisection output — a bound that was valid for the then-current `N_e=64` literal `1.020507` (measured diff `1.664e-7`) but went stale when change `fix-review-findings-voronoi-precision-and-lineage` (task 4.1.4, commit `b23f0e5`, 2026-09-27) corrected that literal to the 6dp truncation `1.020506` (measured diff `8.336e-7`, i.e. `2.78×` the stale bound) without realigning the bound. The bound is realigned to `1e-6`. **Superseded in part**: change `2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard` corrects `sphere._betainc_regularized` to its declared intent, moving the bisection outputs onto their canonical values (`1.1735482746999482 → 1.1735474259197175`; `1.1658482974306132 → 1.1658476215516009`; `1.0205068335735599 → 1.0205068247837132`) and truncating the first two 6dp literals to `1.173547` / `1.165847`. The measured diffs therefore become `4.259e-7` / `6.216e-7` / `8.248e-7`. The sentence above's claim that the compared bisection outputs are unchanged is **true as of `b23f0e5` and false afterwards** — it is retained as the historical record of that commit, not as a present-tense claim.

**Source:** `CLAUDE.md` §6 第 8 条 (amended by `bec147d` 2026-09-07 21:21:31), `CLAUDE.md` §3 (sync-amended by `83a0503` 2026-09-07 22:02:52); change `fix-wayfinder-spec-source-field-drift` design.md (Decision 4 — L678 intentional debt + governance-migration signal); change `migrate-l678-source` design.md (Decision 1 — option (a) governance-capability migration per `fix-wayfinder-spec-source-field-drift/proposal.md` "Open Follow-ups → migrate-l678-source" section). Test anchors unchanged from the pre-migration form (in `openspec/specs/wayfinder/spec.md` req-33 L662-L704 pre-this-change): `tests/test_config.py` (`test_total_param_estimate`, `test_flops_per_layer_exact_33554432`, `test_flops_total_exact_134217728`), `tests/test_extraction.py::test_complexity_budget` (per-head MACs), `tests/test_experts.py::test_expert_pool_param_count` (expert params), `tests/test_sphere.py` (`test_voronoi_monotone_in_ne`, `test_voronoi_canonical_N_e_dependence`, `test_voronoi_residual_below_1e_minus_9` bisection precision witness), `archive/2026-09-06-tighten-test-precision-tolerance/design.md` Decision 4 (the original carve-out being closed — now superseded by `bec147d` + `83a0503` policy reversal), change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` design.md (Decision 1 — stale proximity bound realignment + obligation 6).; change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` design.md (Decision 2 — 4dp `versine` display pinned by exact `round(v, 4)` under a new 4-decimal-display exception in obligations 2/3, superseding the `abs=1e-4` blessing per obligation 6), change `2026-10-02-a2-round2-spec-math-fixes` design.md (Decision D1 — the per-head extraction MAC literal synced to the four-term closed form `33_168`, superseding the three-term `33_040` form)

#### Scenario: Closed-form parameter totals use bare `==`

- **WHEN** a test verifies any of `P_total == 452_329_984`, `P_active == 100_008_448`, `P_router/layer == 32_896` (closed-form integer parameter claims from Requirement 11 "Closed-form parameter totals")
- **THEN** the assertion uses exact `==` integer equality, embeds `f"actual={...}"` in its failure message, and  a `pytest.approx(..., abs=0)` form MUST NOT appear (measured on pytest 9.1.1 an `abs=0` tolerance is exactly 0, so it introduces no relative tolerance at all; bare `==` is nevertheless required because it is the only version-independent form -- see obligation 1).

#### Scenario: Closed-form FLOPs totals use bare `==`

- **WHEN** a test verifies per-layer MoE FLOPs `33_554_432` or total MoE FLOPs `134_217_728 = 4 × 33_554_432` at any of `tests/test_config.py::test_flops_per_layer_exact_33554432` or `tests/test_config.py::test_flops_total_exact_134217728`
- **THEN** the assertion uses exact `==` integer equality, embeds `f"actual={...}"` in its failure message, and  a `pytest.approx(..., abs=0)` form MUST NOT appear (measured on pytest 9.1.1 an `abs=0` tolerance is exactly 0, so it introduces no relative tolerance at all; bare `==` is nevertheless required because it is the only version-independent form -- see obligation 1)..

#### Scenario: Closed-form per-head extraction MACs use bare `==`

- **WHEN** a test verifies per-head extraction MACs `33_168 = macs(8, 128, 16) = H_kv·(2·d_k·d_c + d_c[bias]) + H_kv·d_c[L2-step2] + H_kv·d_c[cross-head mean, step 3] + d_c[L2-step4]` at `tests/test_extraction.py::test_complexity_budget`
- **THEN** the assertion (1) uses bare `==` integer equality (NOT `pytest.approx(...)` of any form), (2) embeds `f"actual={...}"` in its failure message, AND (3) the test MUST back this assertion by (i) calling `extract_C(...)` on real inputs and verifying output shape `(B, N, d_c)`, (ii) verifying the spherical invariant `‖C‖₂ = 1`, AND (iii) deriving the MACs count from measurement of the implementation itself — acceptable mechanisms include `torch.profiler`, custom hooks, or `inspect.getsource` / AST analysis; deriving the count from a helper function in the test that re-states the closed-form formula constitutes a **tautology** and does not satisfy this Scenario. (`tests/test_extraction.py::test_complexity_budget` no longer uses the helper-tautology form: it reads `extract_C`'s own source via `inspect.getsource` / AST analysis and pins the OPERATOR SET the closed form accounts for — 2 projections, 1 bias add, 2 spherical normalizations, 1 cross-head reduction. The MAC MAGNITUDE `33_168` is the spec literal's responsibility and is pinned by a bare `==` integer comparison; the operator census is a structural guard, not a magnitude measurement, because every magnitude factor (`H_kv`, `d_k`, `d_c`) is supplied by the caller rather than read from the source. Closed by change `2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity` task 4; any NEW test verifying the same claim MUST satisfy clause (3).)

#### Scenario: Closed-form expert parameter count uses bare `==`

- **WHEN** a test verifies expert parameter total `N_e · 3 · d_model · d_ffn = 16 · 3 · 1024 · 2048 = 100_663_296` at `tests/test_experts.py::test_expert_pool_param_count`
- **THEN** the assertion uses exact `==` integer equality (both the `expected = cfg.N_e * 3 * cfg.d_model * cfg.d_ffn` structural-identity check AND the literal `100_663_296` check), embeds `f"actual={...}"` in its failure message, and  a `pytest.approx(..., abs=0)` form MUST NOT appear (measured on pytest 9.1.1 an `abs=0` tolerance is exactly 0, so it introduces no relative tolerance at all; bare `==` is nevertheless required because it is the only version-independent form -- see obligation 1)..

#### Scenario: Bisection Voronoi angles use pytest.approx(abs=1e-6)

- **WHEN** a test verifies a bisection-derived Voronoi half-angle at `tests/test_sphere.py::test_voronoi_monotone_in_ne` or `tests/test_sphere.py::test_voronoi_canonical_N_e_dependence` — using the bisection-6dp test literals `1.173547 rad`, `1.165847 rad`, and `1.020506 rad` (each within `1e-6` of the canonical values `1.1735474259197175` / `1.1658476215516009` / `1.0205068247837132`; the bound is stated at `1e-6` rather than a tighter unverified figure because `1e-6` is the normative tolerance of this Scenario, and the measured diffs `4.259e-7` / `6.216e-7` / `8.248e-7` are all below it while the third exceeds `3e-7`)
- **THEN** the assertion uses `pytest.approx(value, abs=1e-6)` and embeds `f"actual={...}"` per obligation 5. `tests/test_sphere.py::test_versine_voronoi_closed_form` instead pins the spec's 4dp `versine` literals `0.6131` / `0.4771` with EXACT `round(v, 4) == literal`, under the 4-decimal-display exception added to obligations 2 and 3 (and per `decompmoe-skeleton` req-6, which already mandates `round(θ, 4) == 1.1735` for the analogous `θ` display). `versine` is a **derived non-angle** quantity, so the `angle`-claim scoping of this Scenario never applied to it. The two deviations the rounding decision rests on — `1.70583e-5` (at `0.6131`) and `3.40146e-5` (at `0.4771`), quoted to 6 significant figures — are each strictly below the 4dp half-unit `5e-5`; that strict bound is what makes `round(v, 4)` a decision on the display form rather than a coincidence, and both the quoted figures and the strict bound are pinned numerically by the same test (at `abs=1e-10`). This **supersedes** this Scenario's earlier `abs=1e-4` blessing, recorded per obligation 6: `abs=1e-4` is `2×` the 4dp half-unit and admits values that do not round to the literal. Any test verifying a bisection-derived **angle** claim with `abs=1e-4` or wider tolerance remains out of scope for this Scenario and MUST be audited by a future change.

#### Scenario: Monte-Carlo Voronoi equal-area witnesses use a derived statistical tolerance

- **WHEN** a test verifies a value produced by `src/decompmoe/sphere.py::voronoi_angle` — the Monte-Carlo measurement layer of `decompmoe-skeleton` req-6 — the assertion MUST use `pytest.approx(value, abs=...)` with `abs` at or above the estimator's derived `5σ`, and MUST NOT use `abs=1e-6` or narrower
- **THEN** the exactly-equal-area witnesses at `tests/test_sphere.py::test_voronoi_angle_known_answer_crosspolytope` and `tests/test_sphere.py::test_voronoi_angle_equal_area_witness_equal_area_configurations` use `abs=1e-3` degrees, which is `13.7×` the derived `5σ = 7.31e-5°` and `23.8×` the measured cross-seed spread of `4.20e-5°` (8 seeds: 0 / 1 / 7 / 42 / 123 / 999 / 20260929 / 31337), and the adjacent comment states the `σ` derivation, the sample count and the seed
- **AND** the one-sidedness guard `tests/test_sphere.py::test_voronoi_angle_one_sided_gap` MUST use configurations whose true gap exceeds `5σ` by at least an order of magnitude (measured `26.8525°` / `11.3372°` / `2.4734°` against `5σ = 7.31e-5°`, i.e. `3.7e5×` / `1.6e5×` / `3.4e4×`) so that a strict `≥ 0` assertion is decidable rather than noise-limited
- **AND** the commensurability bound in `tests/test_sphere.py::test_voronoi_measurement_layer` is a DEGREE-SCALE bound (`0.2°`), NOT a statistical one: that fixture's true gap `0.0399°` is a real deviation of ~`2730×` its own standard error, so a `5σ` bound would reject a real signal, and the `0.2°` bound keeps `5×` headroom over that gap instead of the `25×` the previous `1.0°` bound carried, and the property that test protects is commensurability rather than direction

<a id="req-gov-2"></a>

### Requirement: Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application

The system SHALL treat the ticket `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` annotation pattern, when appended to `wayfinder/tickets/A8-2.md` (or any other wayfinder ticket lineage entry), as a **CLAUDE.md §3 source-field rules application** — the annotation verbatim references the spec requirement anchor (`req-N` plus its `#req-N` anchor and title), the wayfinder ticket (`<ID>.md`), and the spec-end chain-of-authority decisions (`<change> Decision M`). The line-addressed form `(historical, <original reading>; superseded by spec req-N L### via <change> Decision M)` is **legacy**: annotations already carrying it stay as written (they are historical lineage records and rewriting them would corrupt the audit trail), but no NEW annotation may use it. This pattern is enforced by `scripts/lint_no_source_field_drift.py` (per CLAUDE.md §3 "Source reverse-link" rules) and, for the line-addressed form, rejected by `scripts/lint_no_line_pointers.py` check C1 on any NEW annotation. It matches the existing source-field convention established by `req-gov-1` Policy lineage.

**Documenting-only meta Requirement**: This Requirement does NOT introduce new governance contract. It documents the existing CLAUDE.md §3 source-field rules application pattern for ticket `(historical, ...)` supersede annotations, declared at this governance boundary because the pattern is a cross-cutting governance convention rather than a per-capability behavior. Future governance Requirements formalizing the **ticket advisory boundary** concept (advisory scope vs operational impact distinction, monitoring obligation, drift remediation protocol) are planned under `change 09-fix-claude-md-ticket-advisory-boundary` (currently a `.audit/audit-verification/opsx-changes/09-fix-claude-md-ticket-advisory-boundary/` planning draft, NOT YET proposed/applied/archived) and would be `req-gov-N` *if* and when that planned change is archived.

**Source:** `CLAUDE.md` (`governance/CLAUDE.md` back-link per `CLAUDE.md` §3 Workflow Conventions source-field rules)

#### Scenario: Ticket A8-2 supersede annotations follow CLAUDE.md §3 source-field rules verbatim

- **WHEN** `wayfinder/tickets/A8-2.md` supersede annotations italic `(historical, ..., superseded by spec req-20 <Requirement title> (#req-20) ... via ...)` annotations are appended
- **THEN** each annotation contains the canonical pattern verbatim: `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` — 3 reverse-links complete (ticket + spec anchor + change Decision), backtick-wrapped, with the spec anchor (`wayfinder/tickets/A6a-2.md` for the wayfinder ticket-side lineage); the line-addressed variant `req-N L###` is legacy and MUST NOT appear in a NEW annotation
- **AND** no new `governance` operational contract is introduced (the existing `req-gov-1` integer-vs-float guard + CLAUDE.md §3 source-field rules are sufficient for this drift remediation instance; the planned `09-fix-claude-md-ticket-advisory-boundary` ticket-advisory-boundary formalization is a separate future change)
- **AND** the `.audit/` evidence file edits (`.audit/spec-math-audit.md` verify-14 entry + `.audit/audit-verification.md` verify-15 verdict) do NOT require new governance anchoring — `.audit/` is a temporary audit evidence library (per `.audit/README.md`), not governed by spec Requirements
- **AND** the `governance` spec.md anchor coverage remains consistent: existing `req-gov-1` anchor unchanged; this ADDED Requirement introduces `req-gov-2` as a documenting-only meta Requirement (not an operational contract); future governance contracts would be `req-gov-3`+ and are introduced by separate changes

#### Scenario: Ticket A8-2 centered-covariance supersede annotation preserved

- **WHEN** the A8-2 section carrying the `λ_j = C 分布协方差矩阵的特征值` historical definition attempt is read
- **THEN** that section preserves its original wording verbatim AND is immediately followed by an italic `(historical, centered-covariance reading; superseded by spec req-20 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — the centered reading has a `(1/d_c, 1]` upper endpoint that is unreachable at `|T| = d_c`)` annotation

#### Scenario: Ticket A8-2 convex-hull-radius supersede annotation preserved

- **WHEN** the A8-2 section carrying the `原 CV（C 分布凸包半径）` historical reading is read
- **THEN** that section preserves its original wording verbatim AND is immediately followed by an italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — the `1/d_c` lower bound of CV on `S^{d_c−1}` makes the original `< 0.05` health target unreachable)` annotation

#### Scenario: the two A8-2 annotations jointly cover the req-20 Reason argument

- **WHEN** both A8-2 supersede annotations are read together
- **THEN** they jointly cover both clauses of the `wayfinder` `#req-20-mci` Reason supersede argument — the `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c` for the centered reading, and the `1/d_c` lower bound on `S^{d_c−1}` making the original `< 0.05` health target unreachable for the CV reading
- **AND** both name the **same** supersession target and the **same** chain of authority

<a id="req-gov-3"></a>

### Requirement: Loop Severity Framework Gap Closure

The system MUST close two severity-framework gaps observed in the DecompMoE audit-verification loop (per `.audit/audit-verification/audit-verification.md` 9 meta-发现清单 #6 severity 误标 pattern + #8 dormant bug framework gap, both surfaced after verify-30 三轴收官 2026-09-19): (a) the current `LOOPS.md` severity framework is **pure reactive** — only upgrading to HIGH when finding has already infected `src/`, leaving dormant bugs (0 active impact but high latent risk × trigger probability) unaddressed; (b) the audit-verification loop has a **default-MEDIUM inertia** bias — when finding text already contains explicit severity keywords (`低危`/`正面记录`/`不构成硬冲突`), audit-verification verdicts still tend to use MEDIUM rather than adopting the finding's self-graded severity.

Concrete obligations:

1. **Dormant bug escalation trigger** — if a finding's `latent_risk ∈ {MEDIUM, HIGH}` OR `trigger_probability ∈ {MEDIUM, HIGH}` (either-dimension rule, per independent-dimension criterion), the audit-verification verdict severity MUST escalate to `HIGH dormant-bug`, even when the current functional impact is 0. The dormant-bug classification is **proactive risk management**, distinct from the reactive HIGH-upgrade rule (which requires "已传染 src/"); the two rules coexist and are applied independently.

   - `latent_risk ∈ {LOW, MEDIUM, HIGH}` evaluation criteria:
     - `LOW` — finding stale value not currently in any foreseeable code path (e.g. doc-level only)
     - `MEDIUM` — finding stale value will affect a deferred feature with limited blast radius (e.g. optional debug metric, optional aux loss)
     - `HIGH` — finding stale value will cause fatal error or 10x+ performance regression if the deferred feature is implemented (e.g. 48 orphan clusters, NaN propagation, security bug)
   - `trigger_probability ∈ {LOW, MEDIUM, HIGH}` evaluation criteria:
     - `LOW` — finding stale value lives in an unused stub / never-read dead code / explicitly-archived ticket
     - `MEDIUM` — finding stale value lives in a ticket that may be read for related-but-not-immediate work
     - `HIGH` — finding stale value lives in the ONLY explicit spec for a deferred feature that the next implementer will read first
   - **Escalation rule**: severity up to `HIGH dormant-bug` ⟺ `latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}` (either-dimension rule — conservative, max coverage). When both dimensions are `LOW`, finding retains its current MEDIUM (no escalation).

2. **Audit self-correction (reading-finding-text-first rule)** — before the audit-verification loop decides verdict severity in axis-γ 复核, the loop MUST first grep the finding text against the keyword set `{"低危", "正面记录", "正面alignment", "不构成硬冲突", "phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}`. If any keyword matches, the loop MUST adopt the finding's self-graded severity:
   - `{"低危", "不构成硬冲突"}` → verdict-LOW
   - `{"正面记录", "正面alignment"}` → verdict-INFO
   - `{"phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}` → trigger dormant-bug assessment (per obligation 1)

   The verdict text MUST cite which keyword triggered the auto-adoption (e.g. `finding-keyword "低危文字漂移" → verdict-LOW`). The loop MUST NOT default to MEDIUM if finding-text-explicit severity is detectable from keywords. This rule is **preventive** (applied before default-MEDIUM inertia kicks in), not post-hoc.

3. **Verdict embedding obligation** — every audit-verification verdict MUST embed in its severity-decision text the form `finding-keyword "<kw>" × finding-text-self-grade "<grade>" ⇒ verdict-<severity>` (e.g. `finding-keyword "低危文字漂移" × finding-text-self-grade "LOW" ⇒ verdict-LOW`; for dormant-bug case, `finding-keyword "NOT IMPLEMENTED" × latent_risk "HIGH (48 orphan clusters fatal)" × trigger_probability "HIGH (any Phase 0 reader reads ticket L100)" ⇒ verdict-HIGH dormant-bug`). The embedded form is the audit trail that the rule was honored.

4. **`LOOPS.md` reference binding** — `LOOPS.md` §DecompMoE audit-verification loop "Cycle 单元"段 axis-γ 子段 and §DecompMoE spec-math audit loop "Finding 升格路径"段 MUST each reference this Requirement as the single source of truth for the dormant-bug escalation and audit self-correction clauses. `LOOPS.md` MUST NOT restate the rule in different wording (drift risk); instead it cites this Requirement by capability path (`governance/spec.md` req `Loop Severity Framework Gap Closure`) and Scenario ID.

5. **LOOPS.md version-control prerequisite** — any `LOOPS.md` surgical edit MUST operate on a `LOOPS.md` that is tracked in the repository's git history (not untracked). The change that first adds new content to `LOOPS.md` MUST split into two commits: (i) `chore(audit): import LOOPS.md to version control` (pure import with no content change), then (ii) the substantive edit commit. This prerequisite ensures the audit-verification loop has stable anchors when grepping `LOOPS.md` line numbers in future cycles.

**Source:** `CLAUDE.md` §3 (LOOPS.md is a project-level process doc parallel to `CLAUDE.md`, both governance-origin); `CLAUDE.md` §2 (truth-source hierarchy — spec > doc > code, so process rules live in spec not in LOOPS.md); change `08-fix-loops-md-dormant-bug-framework` design.md (Decision 1 — closed-form dormant-bug risk function `latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}` ⇒ HIGH dormant-bug; Decision 2 — reading-finding-text-first rule). Test anchors unchanged from the meta-finding surface (in `.audit/audit-verification/audit-verification.md` `verify-30` 三轴收官 evidence): meta-06 (severity 误标 pattern, 2/24 = 8.3% 误标率, verify-21 + verify-24 实证 cycle-17 INFO + cycle-1 LOW 双误标); meta-08 (dormant bug framework gap, verify-18 实证 cycle-13 latent_risk=HIGH × trigger_probability=HIGH ⇒ dormant-bug, 原话建议 L1358-1359 "建议 LOOPS.md 修订: 在 LOOPS.md severity 框架中加 dormant bug 升级条款"); cycle-5 retro-application as no-op boundary case (L1349 latent_risk=LOW + spec 已 supersede ⇒ MEDIUM retained); cycle-17 finding-keyword "正面记录" → verdict-INFO (L1542); cycle-1 finding-keyword "低危文字漂移" → verdict-LOW (cycle-1 finding-1 record); `LOOPS.md` "Finding 升格路径" 段 (scope of LOOPS-B edit); `LOOPS.md` "audit-verification loop axis-γ" 子段 (scope of LOOPS-A edit); `LOOPS.md` "修改记录" 段 (scope of LOOPS-C edit); `openspec/specs/wayfinder/spec.md` req-34 "governance-origin requirements trigger lint failure" Scenario (governance-migration justification for this Requirement living in `governance/spec.md` not `wayfinder/spec.md`); `openspec/specs/governance/spec.md` req-gov-1 (Test Guard Precision for Closed-Form Numerical Claims — design precedent for governance-origin Requirement); `openspec/specs/governance/spec.md` req-gov-2 (Ticket `(historical, ...)` supersede annotation pattern — pre-existing meta Requirement, NOT modified by this delta; `req-gov-3` chosen to avoid anchor collision).

> **Note**: The `LOOPS.md` line ranges (L64-69, L118-122, L178-198) reference **pre-edit** positions; post this change's surgical edits, those sections shift to L64-70 (Finding 升格路径 +1 bullet for dormant bug 升级条款), L118-124 (axis-γ 子段 +1 line for Reading finding text first rule + 1 line for dormant bug HIGH bullet), L180-201 (修改记录段 + 1 entry). Future readers using these references should `git log --follow LOOPS.md` for line-range history.

#### Scenario: Dormant bug latent risk × trigger probability escalates to HIGH

- **WHEN** an audit-verification loop's axis-γ 复核 finds that a finding satisfies the dormant-bug risk function (`latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}`, the either-dimension rule)
- **THEN** the audit-verification verdict severity MUST escalate to `HIGH dormant-bug`, distinct from the reactive HIGH (传染 src/) upgrade
- **AND** the verdict MUST cite both `latent_risk` value and `trigger_probability` value explicitly with reasoning (e.g. `latent_risk=HIGH (48 orphan clusters fatal if Phase 0 implemented) × trigger_probability=HIGH (any future Phase 0 reader reads ticket `wayfinder/tickets/A6b-1.md`) ⇒ HIGH dormant-bug`)
- **AND** the cited reasoning MUST be retrievable from the finding's own evidence section (no external reference required); the audit trail is self-contained
- **AND** when both `latent_risk` and `trigger_probability` are `LOW`, finding retains its current MEDIUM (no escalation); this case is the no-op boundary that distinguishes dormant-bug from ordinary stale-finding
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` cycle-13 finding 1 (verify-18 evidence L1316-1322): `latent_risk=HIGH` (48 orphan clusters fatal if Phase 0 implemented) × `trigger_probability=HIGH` (any future Phase 0 reader reads ticket `A6b-1.md` "各阶段详细动作" 段) ⇒ dormant-bug HIGH upgrade (was MEDIUM borderline + dormant bug 标注 pre-this-change, becomes HIGH dormant-bug post-this-change)
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` historical cycle-5 finding 1 (verify-18 evidence L1349): `latent_risk=LOW` (spec 已 supersede) × `trigger_probability=LOW` (ticket 已 deprecated for forward Phase 0 — **inferred**; source L1349 comparison table has only `finding / 当前 impact / latent risk / severity 评级` 4 columns and **no `trigger_probability` column**; inference: cycle-5 stale claim is doc-level θ_Voronoi drift (52° vs 67.24°) per the table's "低 (spec 已 supersede)" annotation, AND cycle-5 ticket has been superseded by spec req-1 L184-L185 verbatim (verify-2 axis-β CITE-OK×4 records this supersede), so trigger_probability meets the LOW criterion "explicitly-archived ticket" from this Requirement's obligation 1 evaluation criteria — cross-referenced from cycle-13 evidence base showing the same author flagged `trigger_probability` as inferable from spec/ticket state) ⇒ MEDIUM retained (no dormant-bug escalation); cycle-5 is the no-op boundary case

#### Scenario: Audit self-correction reads finding-text-explicit severity before defaulting to MEDIUM

- **WHEN** audit-verification axis-γ 复核 begins for any finding
- **THEN** the loop MUST grep finding text against the keyword set `{"低危", "正面记录", "正面alignment", "不构成硬冲突", "phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}` BEFORE deciding verdict severity (preventive step)
- **AND** if `{"低危", "不构成硬冲突"}` matches, the verdict MUST adopt `LOW` (not MEDIUM)
- **AND** if `{"正面记录", "正面alignment"}` matches, the verdict MUST adopt `INFO` (not MEDIUM)
- **AND** if `{"phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}` matches, the verdict MUST trigger dormant-bug assessment per Scenario above (not direct MEDIUM)
- **AND** the verdict text MUST cite which keyword triggered the auto-adoption (e.g. `finding-keyword "低危文字漂移" → verdict-LOW`; `finding-keyword "正面记录" → verdict-INFO`; `finding-keyword "NOT IMPLEMENTED" → trigger dormant-bug assessment`)
- **AND** the loop MUST NOT default to MEDIUM if finding-text-explicit severity is detectable from keywords (preventive override)
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` cycle-17 finding 1 (verify-21 evidence L1534-1564): finding text contains `正面记录` + `alignment 完美` ⇒ verdict MUST be INFO (was MEDIUM 误标 pre-this-change, becomes INFO post-this-change via finding-keyword "正面记录" auto-adoption)
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` cycle-1 finding 1 (verify-24 evidence L1795-1813): finding text contains `不构成硬冲突` + `低危文字漂移` ⇒ verdict MUST be LOW (was MEDIUM 误标 pre-this-change, becomes LOW post-this-change via finding-keyword "低危文字漂移" auto-adoption)
- **AND** the scenario's mislabeling-rate target is 0% (was 8.3% = 2/24 pre-this-change, per verify-21 + verify-24 evidence); future audit-verification loops MUST track this metric and any regression to >0% indicates reading-finding-text-first rule violation

<a id="req-gov-4"></a>

### Requirement: Ticket Advisory Boundary — Stale Contamination Monitoring

The advisory status of `wayfinder/tickets/*.md` (per `CLAUDE.md` §8 "2026-08-21 裁决") SHALL NOT be interpreted as "ticket stale has no operational impact". Specifically:

1. **Advisory non-binding scope** — tickets MAY be superseded by OpenSpec changes without amending the ticket itself; this is the ONLY meaning of "advisory". The advisory scope covers ticket-edit policy (whether ticket text may diverge from spec) and does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`.

2. **Operational impact** — ticket stale values MAY propagate to `src/` via three empirically-observed channels: (i) MVPConfig default values copied directly from ticket numbers (per `commit adf41ef` 2026-09-19 history: `MVPConfig.beta_initial = 1.0` was originally sourced from `wayfinder/tickets/A4-1.md` `β_0 ≈ 1.0`; closed by `commit adf41ef` migrating to spec closed-form `0.1 + 31.9 · Sigmoid(γ_init)`); (ii) tests `assert MVPConfig().field == stale_value` LOCKS the propagation (per `commit adf41ef` history: `tests/test_beta.py::test_beta_param_init_default` originally had `assert MVPConfig().beta_initial == 1.0`; closed by migration to `pytest.approx(expected, abs=1e-3)` deriving expected from spec closed form); (iii) any implementation reading ticket directly without consulting spec reproduces stale values (cycle-9 worst-case: ticket `A6a-2.md` `f_i^avg < 1/128` historical vs spec `1 / (2 · N_e)` parameterized form, the `src/` boundary now uses spec parameterization per `src/decompmoe/safeguards.py::_dead_expert_threshold` `_dead_expert_threshold(N_e) = 1.0 / (2.0 * N_e)`).

3. **Monitoring obligation** — `.audit/audit-verification.md` MUST periodically verify the ticket ↔ spec ↔ src triangle for drift propagation. The empirical evidence base (cycle-9 ticket-stale pattern + remaining MEDIUM finding family across multiple cycles) establishes that "ticket-stale → src-pollution" is a recurring pattern requiring active monitoring, NOT a passive advisory. A "传染链已断" verdict (the spec is the truth source and the stale propagation has been interrupted at the `src/` boundary) does NOT exempt the project from this monitoring obligation — recurrence remains possible whenever a new contributor reads a ticket without consulting the corresponding spec.

4. **Drift remediation protocol** — when ticket stale is detected propagating to `src/`: (a) ticket MUST receive a `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` annotation preserving the decision chain (canonical form per `openspec/specs/wayfinder/spec.md` req-34 "Source Field Format Invariant for OpenSpec Specs" Scenario "every Source field contains a wayfinder ticket reference"; the line-addressed `req-N L###` variant is legacy and MUST NOT be newly written); (b) `src/` default values MUST be updated to spec canonical values; (c) tests using `assert == stale_value` MUST migrate to `pytest.approx(spec_value, abs=...)` per `CLAUDE.md` §6 第 8 条 float closed-form convention (formalized by `req-gov-1`).

**Source:** `CLAUDE.md` §8 (cycle-7 audit-verification meta-洞察 boundary clarification, amended by this change)

#### Scenario: ticket advisory scope is bounded to ticket-edit policy

- **WHEN** a developer reads `CLAUDE.md` §8 "ticket 仅作历史决策记录（参考性、非约束性）" together with this Requirement's clause (1)
- **THEN** the advisory interpretation MUST be limited to ticket-edit policy (whether `wayfinder/tickets/*.md` text may diverge from spec), and MUST NOT be extended to claims that ticket-side numerical values have no downstream effect on `src/` or `tests/`

#### Scenario: three contamination channels are independently verifiable

- **WHEN** audit-verification loop checks ticket ↔ spec ↔ src triangle for drift propagation (per clause (3) monitoring obligation)
- **THEN** the three contamination channels enumerated in clause (2) — (i) MVPConfig default values copied from ticket, (ii) tests `assert == stale_value` LOCKS, (iii) reader-ticket-not-spec reproductions — MUST each be independently verifiable by (a) `grep` of MVPConfig dataclass fields against ticket numerical claims, (b) `grep` of `assert MVPConfig().field ==` patterns in `tests/`, (c) absence of canonical-API guards in any module reading ticket-derived constants directly

#### Scenario: drift remediation protocol enforces three-step closure

- **WHEN** a ticket-stale finding is detected propagating to `src/` (per audit-verification three-axis verdict or independent reviewer)
- **THEN** closure of that finding MUST execute the three steps enumerated in clause (4) — (a) ticket `(historical, ...)` annotation, (b) `src/` default value update, (c) tests `pytest.approx` migration — in that order, and a partial closure (e.g., step (a) without (b) and (c)) MUST NOT be considered a fully-closed finding under this Requirement

<a id="req-gov-5"></a>

### Requirement: Numeric Literal Provenance in Specs

**Source:** `CLAUDE.md` §6 (Hard Constraints), `CLAUDE.md` §2 (Truth Source Hierarchy), change `2026-10-02-repair-spell-numeric-literal-provenance` design.md (Decision A2 magnitude self-consistency, Decision A3 three machine-checkable defect classes)

The system MUST NOT admit a numeric literal into any peer spec under `openspec/specs/**` unless the literal carries provenance, and MUST NOT let a literal without provenance carry a proof obligation.

Concretely: a spec numeric literal MUST state (a) the value, (b) **what determines that value** — the governing equation, convergence criterion, or estimator whose property it is — and (c) a recomputation entry point (a derivation chain, or a named script/change whose evidence reproduces it). A literal that satisfies (a) alone is a magic number and MUST NOT enter a spec.

Three defect classes are named because they are machine-checkable without re-running an oracle, and because this repository has produced one instance of each:

1. **C1 — magnitude impossibility.** The literal's decimal precision exceeds what its claimed computation path can produce. Discriminator: if the literal is a residual of magnitude `r`, the compared quantities must agree to `-log10(r)` decimal places; a single float64 operation has a rounding floor near `1e-16` (53-bit mantissa). A literal demanding agreement far below that floor is impossible on the claimed path and MUST be replaced, not restated. Repository instance: a bisection residual quoted as `5.01e-52`, which would require 50.1 decimal places of agreement — 35 orders of magnitude below the float64 floor.
2. **C2 — a bracket tolerance presented as a root property.** A value produced by a solver's internal convergence criterion MUST NOT be labelled as the value at the mathematical root unless it is evaluated at that root by the definition equation. If it is a bracket tolerance, the spec MUST say so. Repository instance: the same `5.01e-52`, which is the oracle's own bisection bracket residual, not the residual at the canonical root (measured `1.4635872379108090131680874e-17` at N_e=16 and `1.9420345120803994000206689e-18` at N_e=64, mpmath `betainc(a, b, 0, x, regularized=True)` at dps=60).
3. **C3 — an API default read as an API semantic.** A statement about what a library call *does* MUST be established by reading the library's source and by a behavioural construction, not by its documentation wording or by a remembered default. Repository instance: a claim that `pytest.approx(expected, abs=T)` applies `max(T, rel*|expected|)`; on pytest 9.1.1 the `rel` default is `None`, not `1e-6`, and the `abs` branch returns before the `max`, so the tolerance is exactly `T`.

#### Scenario: A magnitude-impossible literal is detected without re-deriving it

- **WHEN** a numeric literal in a peer spec is a residual of magnitude `r` and its text names a float64 computation path
- **THEN** the required decimal agreement `-log10(r)` MUST be at most 16 decimal places
- **AND** if `-log10(r) > 16`, the literal MUST fail the check and MUST NOT be restated into another literal; the defect class MUST be recorded as C1
- **AND** the failure message MUST embed the actual magnitude as `f"actual={...}"`

#### Scenario: A bracket tolerance is labelled as such

- **WHEN** a spec literal is produced by a solver's convergence criterion rather than evaluated at a mathematical root
- **THEN** the spec MUST label it as the convergence criterion's tolerance and MUST NOT describe it as the value at the root
- **AND** if the spec claims a root value, that value MUST be obtained by evaluating the governing definition equation at the root
- **AND** the two MUST NOT be interchanged in the same Requirement

#### Scenario: An API-semantics claim is settled by source and behaviour, not by wording

- **WHEN** a spec states what a third-party API call does with a given argument combination
- **THEN** the claim MUST be accompanied by a source reference and by a behavioural construction that discriminates between the candidate readings
- **AND** if two candidate readings give the SAME result for the claim at hand, the spec MUST state which reading it used rather than leaving it implicit
- **AND** the environment in which the claim was measured MUST be named, because library defaults are version-dependent

#### Scenario: Archive copies are not retro-edited

- **WHEN** a defective literal also appears inside `openspec/changes/archive/**`
- **THEN** the archived copy MUST be left byte-identical, because it is the historical record of what a past change did
- **AND** this Requirement's Source field MUST register the retained occurrence so a later auditor can distinguish "deliberately retained history" from "missed fix"

#### Scenario: Numeric assertions inside this Requirement obey the discipline it states

- **WHEN** a Scenario of this Requirement asserts a numeric value
- **THEN** an integer closed form MUST use bare `==` and a float closed form MUST use `pytest.approx(value, abs=...)`
- **AND** the failure message MUST embed the computed value as `f"actual={...}"`
- **AND** `pytest.approx(..., abs=0)` MUST NOT appear on an integer closed form

<a id="req-gov-6"></a>

### Requirement: Cross-Reference Anchor Contract

The system MUST NOT use raw line numbers as the identity of a cross-reference in any peer spec
under `openspec/specs/**`, in `src/**`, or in `tests/**`. A reference MUST resolve through a
mechanically checkable identifier instead. This Requirement exists because the absence of such a
rule let the same defect family be "fixed" five times by hand, each pass leaving siblings behind.

1. **Permitted reference forms.**

   | Target | Required form | Example |
   |---|---|---|
   | a whole Requirement | `Req N` / `req-N` / `` `#req-N` `` plus the Requirement title | `` `Req 13` Numerical Safeguards (`#req-13`) `` |
   | a table row or field block | a block-level HTML anchor on that row, referenced as `` `#req-N-slug` `` | `` `#req-20-mci` `` |
   | a code symbol | `module.py::symbol` | `` `safeguards.py::beta_saturation_warning` `` |
   | a test | `file::test_name` | `` `test_sphere.py::test_voronoi_canonical_N_e_dependence` `` |
   | a prose passage | Requirement number + title + a verbatim quotation of at least 8 characters | the quotation itself is greppable |

2. **Block-anchor minting rule.** A block-level anchor MUST be minted only for a target with **at
   least 2 inbound references**, established by a recorded inbound-reference census rather than by
   judgement. A target with a single inbound reference MUST instead use the Requirement number plus
   a row label or symbol name. This bounds anchor growth: each anchor is a maintenance obligation
   that must be re-checked on every rename of the thing it labels.

3. **Anchor uniqueness and namespace hygiene.** Within a single spec file every `id` MUST be
   unique, and every `### Requirement:` heading MUST be immediately preceded by an HTML anchor
   element on its own line, whose `id` attribute is that Requirement's id. An anchor element
   quoted inside prose or inside a code span MUST NOT
   appear in a Requirement body — a quoted literal still occupies the id namespace when the
   document is parsed, and two Requirements sharing an id makes every anchor reference ambiguous.

4. **Resolvability.** Every `req-N`, `#req-N`, and `#req-N-slug` reference in a peer spec, in
   `src/**`, or in `tests/**` MUST resolve to an anchor that exists in the named capability.

5. **Enforcement.** `scripts/lint_no_line_pointers.py` MUST implement checks C1 (no line-number
   reference), C2 (anchor uniqueness and coverage), C3 (no anchor literal inside a code span), and
   C4 (reference resolvability), and MUST exit non-zero on any violation. It MUST be run as part
   of the `/opsx:archive` precondition alongside the existing two lint gates, per `CLAUDE.md` §3.

6. **Historical-citation exemption.** A line-number reference that records history — a
   superseded coordinate, a pre-change location, or a prior-commit citation — is exempt from
   C1 when the line carries an explicit historical marker (`pre-this-change`, `histor`, the
   original-language marker, a prior commit id, `was`, `before`, or an explicit move arrow). The
   exemption is by marker, not by a registry of exempted files, so that the exemption surface
   stays visible in the document itself.

7. **Archive copies are out of scope.** `openspec/changes/**` is NOT scanned. An archived change is
   the historical record of what a past change did; retro-editing it would falsify that record. A
   pointer introduced by a change is corrected in the live spec by the change that closes it.

**Source:** `CLAUDE.md` §3 (source reverse-link rules and archive preconditions), `CLAUDE.md` §6
(anchor coverage requirement), change
`2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract` design.md (Decisions D1-D8)

#### Scenario: a line-number reference is rejected

- **WHEN** a peer spec, `src/**` file, or `tests/**` file contains a line-number cross-reference
  such as `<capability> L<line>`, `req-<N> L<line>`, `<capability> L<first>-L<last>`, `line <number>`, or
  `<module>.py:<line>` that is not an exempt historical citation
- **THEN** `scripts/lint_no_line_pointers.py` MUST report a violation naming the file, the line,
  and the matched reference
- **AND** the lint MUST exit non-zero
- **AND** the reference MUST be rewritten to one of the permitted forms in clause (1)

#### Scenario: a technical label is not a line reference

- **WHEN** a document uses `L` followed by a digit as a technical label, for example `d_c[L2-step2]`
  or `L4-postmean`, where the digits denote a layer or step rather than a line
- **THEN** `scripts/lint_no_line_pointers.py` MUST NOT report it
- **AND** the label MUST remain greppable as its own token

#### Scenario: a single-reference target does not earn a block anchor

- **WHEN** the inbound-reference census reports exactly 1 inbound reference for a target
- **THEN** no block-level anchor MUST be minted for it
- **AND** the referring site MUST name the Requirement plus a row label or symbol name instead

#### Scenario: a quoted anchor literal is rejected

- **WHEN** a Requirement body contains an anchor literal inside prose or inside a code span, for
  example — any Requirement's own anchor element, whichever id it carries —
- **THEN** `scripts/lint_no_line_pointers.py` MUST report a C3 violation
- **AND** the id namespace of that spec MUST remain free of the duplicate
- **AND** the body MUST reference the target by `` `#req-20` `` plus its title instead

#### Scenario: the lint discriminates against the pre-change tree

- **WHEN** `scripts/lint_no_line_pointers.py` is evaluated against the repository state before this
  change
- **THEN** it MUST report C1 violations and exit non-zero
- **AND** it MUST report green only against the post-change state, so that a silently-passing
  check is itself detectable

<a id="req-gov-7"></a>

### Requirement: Archive Gate Must Be Executable

Every gate named as an `/opsx:archive` precondition MUST be a runnable command, MUST
exit non-zero on a tree that carries the defect class it claims to detect, and MUST be
reachable from a single named entry point. `CLAUDE.md` §3 MUST NOT enumerate individual
lint scripts: a list that must be edited by hand whenever a lint is added can and does
drift out of step with the scripts actually present, and a drifted list is a gate that
silently covers nothing.

**Source:** `CLAUDE.md` §3 (Workflow Conventions — the `/opsx:archive` precondition clause),
change `2026-10-03-a5-archive-gate-executability` design.md (Decision D1 — glob discovery
replaces enumeration)

#### Scenario: The gate list is not a separate list

- **WHEN** a new lint is added under `scripts/`
- **THEN** it MUST become part of the archive precondition without any edit to `CLAUDE.md`
- **AND** the precondition MUST name one entry-point command, not a per-script list

#### Scenario: A gate that cannot fail is not a gate

- **WHEN** the entry point discovers zero lints
- **THEN** it MUST exit non-zero
- **AND** it MUST NOT report a pass on the grounds that no discovered lint reported a violation

#### Scenario: The change being archived is validated as a change

- **WHEN** the archive precondition runs for a change with no spec delta and no `skip_specs`
- **THEN** the entry point MUST exit non-zero
- **AND** the reported cause MUST name the missing delta or the missing `skip_specs` marker
- **AND** the check MUST be scoped to the change being archived, so that unrelated stale changes in the same directory do not determine the result

<a id="req-gov-8"></a>

### Requirement: Gate Result Must Be Reproducible

A gate run MUST record `git rev-parse HEAD` and three content-sensitive components: the committed base (`git rev-parse HEAD`), a digest of the *content* of every tracked modification staged or unstaged (`sha256(git diff HEAD)`), and a digest of every untracked file's bytes enumerated individually, so that a new file inside an untracked directory counts
before executing, and MUST re-verify both after the last gate completes. If either
differs, the run MUST be reported as INVALID — a state distinct from both pass and
failure. An archive MUST be gated against a quiesced worktree, because a green result
computed over a tree that changed mid-run describes content that no longer exists. A digest of `git status --porcelain` does not satisfy this Requirement: porcelain encodes a path and a status letter, not content, so two worktrees differing only in the bytes of an already-dirty file produce byte-identical porcelain and therefore a byte-identical digest.

**Source:** `CLAUDE.md` §3 (Workflow Conventions), change
`2026-10-03-a5-archive-gate-executability` design.md (Decision D2 — exit code 2 reserved
for an unstable worktree)

#### Scenario: The worktree changes while the gates run

- **WHEN** the post-run `git rev-parse HEAD` or worktree digest differs from the pre-run value
- **THEN** the entry point MUST report `GATE RESULT INVALID`
- **AND** it MUST exit with a code distinct from both the pass code and the violation code
- **AND** it MUST NOT print a pass summary for that run

#### Scenario: A dirty state with an unchanged file count is still a change

- **GIVEN** two different dirty worktrees that contain the same number of changed entries
- **THEN** the run MUST still detect the change
- **AND** the comparison MUST NOT rely on a changed-entry count alone

#### Scenario: A stable run is reported normally

- **WHEN** every gate completes and the pre-run and post-run snapshots are identical
- **THEN** the result MUST be reported as pass or violation according to the gates alone

#### Scenario: Two worktrees differing only in the bytes of a dirty file

- **GIVEN** one tracked file already modified, whose content then changes again without its path or its status changing
- **THEN** a digest of `git status --porcelain` MUST be identical for both states
- **AND** the run MUST still detect the change, from tracked content rather than from porcelain
- **AND** a derived count of changed entries MUST NOT be treated as an independent signal, because it is a coarser function of the same porcelain string

<a id="req-gov-10"></a>

### Requirement: Spec Anchor Ledger Survives Archive And Names Every Loss

`openspec archive` MUST leave the spec anchor ledger unchanged. The archive
procedure MUST be: write the ledger, archive, compare the ledger, restore any lost
anchor surgically, re-verify. Re-running the archive MUST NOT be used to repair a
lost anchor, because a second archive overwrites the first repair.

A point-in-time coverage check MUST NOT be treated as sufficient on its own. It
does detect a swallowed anchor, because a swallow removes one Requirement's
block-start anchor while leaving the heading count alone, and a simultaneously
added Requirement carries its own anchor, so the deficit cannot be cancelled. What
it cannot do is name anything: it reports a per-capability deficit rather than the
anchor id or the Requirement that lost it, it cannot see an anchor id that
survived but was re-attached to a different Requirement, and it cannot separate a
lost anchor from one the change declared and never added. The ledger comparison
MUST supply those three, and MUST report a lost anchor by id and by the Requirement
it introduced, in a list separate from the declared-but-never-added one.

**Source:** `CLAUDE.md` §6 (Hard Constraints — the 100% anchor coverage clause), change `2026-10-03-a5-archive-gate-executability` design.md (Decision D4 — a ledger, not a point-in-time count), corrected by change `2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D2 — the D4 premise was measured and is false)

#### Scenario: A swallowed anchor is a count deficit, not an invisible loss

- **WHEN** the archive drops the anchor of the Requirement following the one it rewrote
- **THEN** the Requirement-heading count and the block-start anchor count diverge
- **AND** a point-in-time coverage check MUST report the uncovered Requirement
- **AND** the deficit MUST NOT be cancellable by any simultaneous addition, because an added Requirement carries its own anchor and moves both counts together

#### Scenario: Naming what a count cannot

- **GIVEN** a baseline ledger and a current ledger taken across one archive
- **THEN** a before/after comparison MUST name each lost anchor id and the Requirement title it introduced
- **AND** it MUST report an anchor id whose id is unchanged but whose introduced title changed, which a count-based check reports as fully covered
- **AND** only a before/after comparison is permitted to make that claim

#### Scenario: Lost and never-added are separate classes

- **GIVEN** a baseline ledger, one anchor that disappeared, and one anchor the change declared it would add but which is absent
- **THEN** both MUST be reported
- **AND** they MUST appear in separate labelled lists
- **AND** a report giving only the net count MUST be treated as insufficient

#### Scenario: A block boundary requires the Requirement heading to follow the anchor

- **WHEN** a standalone anchor line is followed by a blank line and prose rather than a `### Requirement:` heading
- **THEN** it MUST NOT be treated as a Requirement block start
- **AND** an anchor quoted inline inside prose MUST NOT be counted as a Requirement header

#### Scenario: A section sub-anchor is not a declared Requirement

- **GIVEN** an `## ADDED Requirements` delta block whose Requirement also carries a block-level section anchor such as `req-20-mci`
- **THEN** only the anchor that introduces the `### Requirement:` heading MUST be collected as a declared addition
- **AND** the section anchor MUST NOT be reported as a declared-but-never-added anchor, because the declared set is compared against block starts, which never contain it

#### Scenario: Repairing a lost anchor

- **WHEN** the ledger comparison reports a lost anchor
- **THEN** the anchor and its following blank line MUST be restored by direct edit

<a id="req-gov-11"></a>

### Requirement: Spec Requirements Carry A Source Field

Every Requirement in a capability spec MUST carry a top-level `**Source:**` field. A
Requirement that ships without one MUST fail the gate. Requirements that predate this
Requirement and have no field MUST be listed in a registry of justified exemptions,
and the registry MUST be an explicit, reviewable list of anchor ids rather than a count
or a prefix, so that a newly authored Requirement without a field fails immediately.

A registry entry MUST record the capability and the anchor id it exempts. An entry that
names an anchor id which no longer exists, or which now carries a field, MUST itself be
reported, so the registry cannot silently outlive the defect it was written to excuse.

**Source:** `CLAUDE.md` §3 (Source 反链 requirement) and §6 (the ban on unverifiable clauses), change `2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D4 — grandfather, do not fabricate lineage)

#### Scenario: A new Requirement without a Source field

- **WHEN** a Requirement is added to a capability spec without a top-level `**Source:**` field
- **THEN** the Source-field gate MUST report the capability and the Requirement title
- **AND** it MUST exit non-zero

#### Scenario: A pre-existing Requirement with no field is exempt by id

- **GIVEN** a Requirement whose anchor id appears in the justified-exemption registry
- **THEN** the existence check MUST NOT report it
- **AND** the registry MUST be reported separately from the violation list, so a green run does not imply full coverage

#### Scenario: A stale exemption is itself a finding

- **GIVEN** a registry entry whose anchor id no longer exists, or whose Requirement now carries a `**Source:**` field
- **THEN** the gate MUST report the stale entry
- **AND** it MUST exit non-zero, so the registry must be pruned rather than accumulate
