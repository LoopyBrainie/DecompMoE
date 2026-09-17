## Why

`/code-review` audit of `tests/test_config.py` and `tests/test_sphere.py` surfaced 4 LOW-severity precision gaps that violate `CLAUDE.md` §6 第 8 条 ("spec 中每个含具体数值的算式都必须有 `pytest.approx(..., abs=...)` 直接对账"). Two test functions use raw `assert int_value == constant` for closed-form integer claims (parameter totals `452_329_984` / `100_008_448`, router per-layer `32_896`, per-layer FLOPs `33_554_432`, total FLOPs `134_217_728`); two use `pytest.approx(..., abs=1e-4)` for bisection-derived Voronoi angles where the bisection implementation already achieves `|½ · I_{sin²θ}(7.5, 0.5) − 1/N_e| < 1e-9` (proven by `test_voronoi_residual_below_1e_minus_9`). Tightening to `abs=0` (integers) and `abs=1e-6` (bisection) aligns test guard strength with the actual precision of the closed-form computation and detects future regressions 3-4 decades earlier.

## What Changes

- **`tests/test_config.py::test_total_param_estimate`** (L53-67): replace 3 integer `==` assertions (`total=452_329_984`, `active=100_008_448`, `router=32_896`) with `pytest.approx(value, abs=0)`; embed `f"actual={...}"` in each failure message per CLAUDE.md §3 TDD convention.
- **`tests/test_config.py::test_flops_per_layer_exact_33554432`** (L70-86): replace 2 integer `==` assertions (`per_layer=33_554_432`, `total=134_217_728`) with `pytest.approx(value, abs=0)`; embed `f"actual={...}"`.
- **`tests/test_sphere.py::test_voronoi_monotone_in_ne`** (L88-93): tighten 2 bisection asserts from `abs=1e-4` to `abs=1e-6` for `theta_16 ≈ 1.173548` (also correcting the existing literal `1.173547` which is `1.27e-6` off the actual bisection value `1.1735482746999482` — a 6dp truncation error in the original test) and `theta_17 ≈ 1.165848`.
- **`tests/test_sphere.py::test_voronoi_canonical_N_e_dependence`** (L138-152): tighten 1 bisection assert from `abs=1e-4` to `abs=1e-6` for `theta_64 ≈ 1.020507` (literal already within `1.66e-7` of actual bisection `1.0205068335735599`, so no literal change needed).

No production-code changes. No new tests added. No changes to the closed-form **VALUES** in `wayfinder` Req 11 (`4070 MVP Hyperparameter Set` — numerical constants themselves are unchanged; the spec literal for `(16, 16)` remains `1.1736 rad` per the `67.24° × π/180` conversion-consistency perspective post-revision); only the test guards that pin them tighten, and the LOW-3 literal is corrected to match bisection at 6dp precision. The new `Test Guard Precision for Closed-Form Numerical Claims` Requirement (Req 32) added to `wayfinder` is new test-side policy text — it does NOT modify the Req 11 closed-form values themselves.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `wayfinder` — adds Requirement `Test Guard Precision for Closed-Form Numerical Claims` (3 Scenarios) to the `wayfinder` capability. This requirement codifies the `CLAUDE.md` §6 第 8 条 convention for spec-anchored closed-form numerical tests in `tests/test_config.py` and `tests/test_sphere.py`. Existing Requirement 11 (`4070 MVP Hyperparameter Set`) is unchanged; the closed-form values themselves are unchanged.

## Impact

- 反链: `CLAUDE.md` §6 第 8 条 (closed-form `pytest.approx` mandate); `CLAUDE.md` §3 (TDD `f"actual={...}"` convention); `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` (bisection residual `< 1e-9` witness — proves `abs=1e-6` is safely achievable); `tests/test_sphere.py::test_voronoi_rad_precision_alignment` (separately guards the spec literal `1.1736 rad` ↔ `67.24°` conversion identity at `abs=1e-4`, distinguishing it from bisection-precision testing at `abs=1e-6`).
- 验收基线: `uv run pytest tests/test_config.py tests/test_sphere.py -v` 8 个收紧断言全过（含 LOW-3 的 literal 修正 `1.173547` → `1.173548`）; `uv run pytest tests/ -v` 全套仍过; 整数闭式与 bisection Voronoi 角值在 `abs=0` 与 `abs=1e-6` 下严格满足 spec 声称。
- 无破坏性变更: 所有现行值在 `abs=0` (整数) 与 `abs=1e-6` (bisection) 下严格满足 spec 声称, 仅 LOW-3 (16,16) 的 literal 修正 `1.173547` → `1.173548`（因原 test 用 6dp 截断值 `1.173547` 与实际 bisection `1.1735482747` 相差 `1.27e-6` > `abs=1e-6` 上限，必须修正 literal 才能收紧 tolerance）。
- 不需要运行训练或 baseline。
- 不引入新依赖, 不修改 production code, 不修改 `compute_total_and_active` / `flops_per_token` / `canonical_voronoi_angle` 任何实现。
