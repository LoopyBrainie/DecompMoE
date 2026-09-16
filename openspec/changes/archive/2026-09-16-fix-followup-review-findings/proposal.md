## Why

`/code-review` on the just-completed opsx apply of `2026-09-05-follow-up-review-fixes` identified 7 actionable findings (F1.2 rad↔deg bijection asymmetry, F1.7 tolerance-clause semantic ambiguity, F2.1/F2.2 beta.py constants collapse `σ'(0)·2` into `0.5`, F2.3/F2.4 test_beta.py references constants not principle chains, F2.7 missing principle-form coverage in test_safeguards.py). Verdict was PASS (the 3 surgical spec edits are mathematically correct, not in regression), but the findings collectively flag a recurring `CLAUDE.md §6 第 8 条` risk area: **principle-form expressions in constants and tests vs. collapsed literals that silently absorb future sigmoid / inner-product retunes**. Pre-existing defects adjacent to the same risk area as `follow-up-review-fixes`; this change resolves them in one pass to prevent recurring reviewer findings.

## What Changes

### Spec text refinements
- **`openspec/specs/wayfinder/spec.md` L185** (F1.2): `≈ 67.24° (1.1735 rad)` → `≈ 67.24° (≈ 1.1735 rad)`. Add `≈` to rad for rad↔deg bijection awareness; symmetrize with `decompmoe-skeleton/spec.md` L98 + L102 (which already use `≈` for both).
- **`openspec/specs/decompmoe-skeleton/spec.md` L98** (F1.7): rephrase `(within abs=1e-4 rad on the residual < 1e-9 criterion)` → `(within abs=1e-4 rad, with the bisection residual < 1e-9)`. Separates the two tolerance constraints (value tolerance vs. equation residual) for syntactic clarity.

### Code refactor (principle-form constants)
- **`src/decompmoe/beta.py`**: add module-level sub-constants `SIGMA_PRIME_AT_ZERO: Final[float] = 0.25` and `ANTIPODAL_INNER_EXTREME: Final[float] = 2.0` (position ~L30-L34).
- **`src/decompmoe/beta.py` L36** (F2.1): `MAX_GRAD_PER_GAMMA: Final[float] = 0.5 * (BETA_MAX - BETA_MIN)` → `MAX_GRAD_PER_GAMMA: Final[float] = SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME * (BETA_MAX - BETA_MIN)`.
- **`src/decompmoe/beta.py` L50** (F2.2): `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0  # = 7.75·2 = 15.5` → `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME * 31.0`. Style-consistent with L46 `_MAX_GRAD_BETA_PHASE4_INTERNAL = 31.0 * 0.25`.

### Test refactor (principle-form assertions)
- **`tests/test_beta.py` L148-153** `test_max_grad_per_gamma_phase4` (F2.3): replace `pytest.approx(beta.MAX_GRAD_PER_GAMMA_PHASE4, abs=1e-3)` (references constant) with `pytest.approx(31.0 * beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME, abs=1e-12)` (references principle chain).
- **`tests/test_beta.py` L111-114** `test_grad_gamma_bound` (F2.4): replace `pytest.approx(beta.MAX_GRAD_PER_GAMMA, abs=1e-3)` with `pytest.approx(beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN), abs=1e-12)`.
- **`tests/test_beta.py` L98-99 docstring** (F2.4 follow-on): fix misleading `0.5·31.9·0.5·2 = 15.95` expression (the `·0.5·2` pair multiplies to 1, making the expression look like 4 factors when only 2 are real). Replace with principle form `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95`.

### New principle-form test
- **`tests/test_safeguards.py` add `test_max_grad_constants_principle_form`** (F2.7): assert `beta.MAX_GRAD_PER_GAMMA == pytest.approx(0.25 * 2 * 31.9, abs=1e-12)`, `beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(0.25 * 2 * 31.0, abs=1e-12)`, `beta.MAX_GRAD_PER_C == 32.0` (integer closed-form per `governance spec.md req-gov-1`, bare `==`), `beta._MAX_GRAD_BETA_PHASE4_INTERNAL == pytest.approx(31.0 * 0.25, abs=1e-12)`. Complements `test_named_constants_have_spec_values` which only covers non-MAX_GRAD_* named constants.

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 — frontmatter `skip_specs: true`；本 change 是 spec 文本精度统一 + 代码 principle-form 重构 + 测试 principle-form 化，无 REQUIREMENT 行为变化；现有 spec L446 已正确写出 principle form `0.25 · 2 · 31 = 15.5`，本次只是把 code 端对齐 spec 端已存在的 principle form）

## Impact

- 反链：code-review 报告 on `2026-09-05-follow-up-review-fixes` opsx apply（findings F1.2/F1.7/F2.1-F2.4/F2.7）
- 验收基线：`uv run pytest tests/ -v` 全过（refactor + text edits + 测试数 +1，行为不变；principle-form 重对账已确保数值等价）
- 无破坏性变更
- CLAUDE.md §6 第 8 条 risk area 一次性闭环