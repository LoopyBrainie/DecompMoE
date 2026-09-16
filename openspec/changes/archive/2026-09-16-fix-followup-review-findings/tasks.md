## 1. Spec Text Refinement (F1.2 + F1.7)

- [x] 1.1 `openspec/specs/wayfinder/spec.md` L185：`≈ 67.24° (1.1735 rad)` → `≈ 67.24° (≈ 1.1735 rad)` (F1.2 rad↔deg bijection awareness；验证：与 `decompmoe-skeleton/spec.md` L98 + L102 `≈ 1.1735 rad (≈ 67.24°)` 风格对称)
- [x] 1.2 `openspec/specs/decompmoe-skeleton/spec.md` L98：`(within abs=1e-4 rad on the residual < 1e-9 criterion)` → `(within abs=1e-4 rad, with the bisection residual < 1e-9)` (F1.7 分离 value tolerance 与 equation residual；验证：`Select-String -Path spec.md -Pattern "abs=1e-4 rad, with the bisection residual < 1e-9"` 应在 L98 命中)

## 2. Code Refactor — Principle-Form Constants (F2.1 + F2.2)

- [x] 2.1 `src/decompmoe/beta.py`：在 module-level `Final[float]` 区段（约 L30-L34 `MAX_GRAD_PER_C` 附近）新增子常量 `SIGMA_PRIME_AT_ZERO: Final[float] = 0.25` + `ANTIPODAL_INNER_EXTREME: Final[float] = 2.0` (F2.1 + F2.2 前提；验证：`Select-String -Path beta.py -Pattern "SIGMA_PRIME_AT_ZERO|ANTIPODAL_INNER_EXTREME"` 各 1 处定义 + 多处引用)
- [x] 2.2 `src/decompmoe/beta.py` L36：`MAX_GRAD_PER_GAMMA: Final[float] = 0.5 * (BETA_MAX - BETA_MIN)` → `MAX_GRAD_PER_GAMMA: Final[float] = SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME * (BETA_MAX - BETA_MIN)` (F2.1；验证：表达式不含字面 `0.5`)
- [x] 2.3 `src/decompmoe/beta.py` L50：`MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0  # = 7.75·2 = 15.5` → `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME * 31.0` (F2.2；验证：表达式不含字面 `0.5`；comment 可保留 `= σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` 形式说明)
- [x] 2.4 `src/decompmoe/beta.py` L46：`_MAX_GRAD_BETA_PHASE4_INTERNAL: Final[float] = 31.0 * 0.25  # = 7.75` 视情况改 `_MAX_GRAD_BETA_PHASE4_INTERNAL: Final[float] = 31.0 * SIGMA_PRIME_AT_ZERO`（风格统一，非 finding 强制；验证：与 L36/L50 风格对称）

## 3. Test Refactor — Principle-Form Assertions (F2.3 + F2.4)

- [x] 3.1 `tests/test_beta.py` L148-153 `test_max_grad_per_gamma_phase4`：替换 `pytest.approx(beta.MAX_GRAD_PER_GAMMA_PHASE4, abs=1e-3)` → `pytest.approx(31.0 * beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME, abs=1e-12)` (F2.3；验证：assert 行不含 `beta.MAX_GRAD_PER_GAMMA_PHASE4` 引用，仅含原理链)
- [x] 3.2 `tests/test_beta.py` L111-114 `test_grad_gamma_bound`：替换 `pytest.approx(beta.MAX_GRAD_PER_GAMMA, abs=1e-3)` → `pytest.approx(beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN), abs=1e-12)` (F2.4；验证：同上)
- [x] 3.3 `tests/test_beta.py` L98-99 docstring：替换误导性 `0.5·31.9·0.5·2 = 15.95` → `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95` (F2.4 follow-on；验证：grep `0\.5·31\.9·0\.5·2` 0 命中)

## 4. New Principle-Form Test (F2.7)

- [x] 4.1 `tests/test_safeguards.py` 在 `test_named_constants_have_spec_values`（L498-566）附近新增 `test_max_grad_constants_principle_form`：assert `beta.MAX_GRAD_PER_GAMMA == pytest.approx(0.25 * 2 * 31.9, abs=1e-12)` + `beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(0.25 * 2 * 31.0, abs=1e-12)` + `beta.MAX_GRAD_PER_C == 32.0`（整数闭式 bare `==` per `governance/spec.md req-gov-1`）+ `beta._MAX_GRAD_BETA_PHASE4_INTERNAL == pytest.approx(31.0 * 0.25, abs=1e-12)` (F2.7；验证：`uv run pytest tests/test_safeguards.py::test_max_grad_constants_principle_form -v` PASS)

## 5. Validate & Archive

- [x] 5.1 `openspec validate 2026-09-16-fix-followup-review-findings`（验证：frontmatter `skip_specs: true` + zero delta accepted）
- [x] 5.2 `uv run pytest tests/ -v` 全过（验证：终端输出 `189 passed` 或更多；新增 1 个 test function `test_max_grad_constants_principle_form` 使总数 +1；无 principle-form 闭式对账失败）
- [x] 5.3 `openspec archive 2026-09-16-fix-followup-review-findings --yes`（验证：`openspec list --json` 不再出现该 change；archive 目录由 CLI 写入）