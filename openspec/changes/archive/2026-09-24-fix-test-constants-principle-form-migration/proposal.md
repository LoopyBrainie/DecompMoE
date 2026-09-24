# Proposal: fix-test-constants-principle-form-migration

## Why

`ad64063` (2026-09-16 22:58, `refactor(beta+test): principle-form gradient bounds + MAX_GRAD_* coverage`) 完成了 `tests/test_beta.py::test_grad_gamma_bound` (L96-172) 和 `test_max_grad_per_gamma_phase4` (L203+) 两处 autograd test 的 principle-form migration,并新增 `tests/test_safeguards.py::test_max_grad_constants_principle_form` (L644-692) 用 literal `0.25 * 2 * 31.9` / `0.25 * 2 * 31.0` + `abs=1e-12` 钉值零容差钉死 derivation chain。但 ad64063 commit **漏掉了同文件 2 处 literal 钉值 test**,形成半迁移缺口:

- **`tests/test_beta.py:187` `test_constants_exported`**(源自 `ff26208` 2026-08-24,ad64063 时已存在):`assert abs(beta.MAX_GRAD_PER_GAMMA - 15.95) < 1e-6` —— literal 钉值 `15.95`,**无 principle form**,容差 `1e-6` 偏松(`governance/spec.md req-gov-1` 浮点闭式要求 `abs=1e-12`)
- **`tests/test_beta.py:200` `test_max_grad_per_gamma_phase4_closed_form`**(源自 `c26241b` 2026-09-16 22:21,即 ad64063 之前 37 分钟):`assert beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(15.5, abs=1e-6)` —— literal 钉值 `15.5`,**无 principle form**,容差同样偏松

修复策略:两处测试断言改用 **literal principle chain**(`0.25 * 2 * 31.9` / `0.25 * 2 * 31.0`) + **钉值零容差 `abs=1e-12`**(per `governance/spec.md req-gov-1` 浮点闭式),风格对齐 `test_safeguards.py::test_max_grad_constants_principle_form`(literal principle form + `abs=1e-12`)。本 change 是 test-only surgical fix,**不修改 src/**,**不修改 spec**(test 形式层对齐,不影响 spec `req-7` / Req "Closed-Form Gradient Bound Worst Case" 已 lock 的 principle form),走 `skip_specs: true` 路径。

## What Changes

### Test refactor (literal principle-form, abs=1e-12)

- **`tests/test_beta.py:180-187` `test_constants_exported`**:L187 `assert abs(beta.MAX_GRAD_PER_GAMMA - 15.95) < 1e-6` → `assert beta.MAX_GRAD_PER_GAMMA == pytest.approx(0.25 * 2 * 31.9, abs=1e-12)`。docstring 从"import + Final[float] type guard"扩展为"principle-form factor guard"。验证:`grep "15\.95" tests/test_beta.py` scope 内 0 命中(L187 一处迁移);scope 外 0 命中(全文件仅 L187 用过"15.95")
- **`tests/test_beta.py:190-200` `test_max_grad_per_gamma_phase4_closed_form`**:L200 `assert beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(15.5, abs=1e-6)` → `assert beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(0.25 * 2 * 31.0, abs=1e-12)`。docstring 现状已写 `31·0.25·2 = 15.5` derivation chain,无需大改;把 assertion 同步到 literal principle form + 钉值零容差。验证:`grep "15\.5" tests/test_beta.py` scope 内 0 命中(L200 一处迁移);scope 外 0 命中(全文件"15.5"仅 L200 出现)

### nothing else

不动 `openspec/specs/wayfinder/spec.md` / `openspec/specs/decompmoe-skeleton/spec.md` / `openspec/specs/governance/spec.md`(已 lock principle form,test-only 形式层修复)。不动 `src/decompmoe/beta.py`(`MAX_GRAD_PER_GAMMA` / `MAX_GRAD_PER_GAMMA_PHASE4` / `SIGMA_PRIME_AT_ZERO` / `ANTIPODAL_INNER_EXTREME` 在 ad64063 后已用 module attribute principle form 定义,无 retune 需求)。不动 `tests/test_safeguards.py::test_max_grad_constants_principle_form`(ad64063 已加,literal principle form + `abs=1e-12`,作为本 change 的 reference 风格)。本 change 通过 `.openspec.yaml` `skip_specs: true` 显式标记 0 spec delta。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无。`.openspec.yaml` `skip_specs: true` —— 本 change 是 test 形式层 surgical 修复,无 REQUIREMENT 行为变化。spec `req-7` "Closed-Form Gradient Bound Worst Case" 已 lock principle form `σ'(0) · 2 · (β_max − β_min) = 15.95`,test 形式层与 spec 已 lock 的 principle form 对齐,不需要 spec delta。）

## Impact

- **Affected code**: 无(`src/decompmoe/` 0 文件改动)
- **Affected tests**: 1 文件 2 行(`tests/test_beta.py` L187 + L200);0 个 test function `def` 新增 / 重命名;现有 `test_name` 测试数不变
- **Affected specs**: 无(`openspec/specs/` 0 行改动;`.openspec.yaml` `skip_specs: true` 显式标记)
- **Affected wayfinder tickets**: 无(本 change 不动 `wayfinder/tickets/`,ticket A4-1 已 lock A4-1 L58 principle form)
- **Affected OpenSpec source 反链**: 无变化
- **Affected APIs / dependencies**: 无
- **Affected systems**: 无(推理引擎实现代码已 out-of-scope per CLAUDE.md §7)
- **Risk**:
  - **literal chain 与 module 子常量 drift**: 选 literal 而不是 module attribute(`beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN)`)的理由:test_safeguards.py::test_max_grad_constants_principle_form 已用 literal `0.25 * 2 * 31.9` + `abs=1e-12` 钉死因子值,这是"真正钉住子常量"的风格——若 module 子常量 retune(如 `SIGMA_PRIME_AT_ZERO = 0.3`),literal chain 仍断言 15.95,测试 fail,暴露 silent drift;而 module attribute chain 是 trivially-true 恒等式(`MAX_GRAD_PER_GAMMA` 本身就是这个 expression),无 testing value。**Mitigation**:本 change 沿用 test_safeguards.py 已验证风格;post-apply 二次实测 `beta.SIGMA_PRIME_AT_ZERO == 0.25` / `beta.ANTIPODAL_INNER_EXTREME == 2.0` / `beta.BETA_MAX - beta.BETA_MIN == 31.9` 验证 literal 与 module attribute 数值一致
  - **`abs=1e-12` 过严?** L187 / L200 是 module-attribute-vs-literal 比较,FP-exact 无 autograd FP 累积,`abs=1e-12` 是钉值零容差(`governance/spec.md req-gov-1` 浮点闭式明文)。但 `pytest.approx(0.25 * 2 * 31.9, abs=1e-12)` 的 `0.25 * 2 * 31.9` 在 Python float64 下 `= 15.950000000000001`(FP 累积),与 `beta.MAX_GRAD_PER_GAMMA`(`SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME * (BETA_MAX - BETA_MIN)` = `0.25 * 2.0 * 31.9`)FP 累积路径不同,可能产生 ~1e-15 偏差。**Mitigation**:`pytest.approx` `abs` 是绝对容差,1e-15 << 1e-12,测试通过;post-apply 跑 `pytest tests/test_beta.py::test_constants_exported tests/test_beta.py::test_max_grad_per_gamma_phase4_closed_form -v` PASS 验证
  - **CLAUDE.md §6 第 8 条 "formula must reflect mathematical principle"**:本 change 把 literal `15.95` 替换为 principle form `0.25 * 2 * 31.9`,**直接对齐 §6 第 8 条 + ad64063 设计意图**,无违反
  - **审计 chain 一致性**:本 change 是 ad64063 半迁移补强,不引入新 finding,只关闭 ad64063 时漏掉的 2 处 test 形式层 drift。cycle-XX audit-verification 链不增加新 finding 节点
- **Source**:
  - ad64063 commit message 显式承诺"principle-form derivation chain" + `test_safeguards.py` 新增 literal principle form test
  - `governance/spec.md` `req-gov-1`:浮点闭式 `pytest.approx(value, abs=1e-12)`;整数闭式 bare `==`
  - `tests/test_safeguards.py:644-692` `test_max_grad_constants_principle_form`:reference 风格(literal `0.25 * 2 * 31.9` + `abs=1e-12`)
  - `tests/test_beta.py:165-172` `test_grad_gamma_bound` 与 `:226-232` `test_max_grad_per_gamma_phase4`:ad64063 已迁移的 autograd test,使用 module attribute principle form(`abs=1e-6`,autograd-vs-analytic 容差,与 L187/L200 钉值零容差是不同语义层)