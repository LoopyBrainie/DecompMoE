# Design

## Context

ad64063 (2026-09-16 22:58) 完成 principle-form migration,但**漏** `tests/test_beta.py` 2 处 literal 钉值 test:`test_constants_exported` (L187) 与 `test_max_grad_per_gamma_phase4_closed_form` (L200)。本 change 是 ad64063 半迁移补强,test-only surgical fix,补齐 L187 / L200 到 literal principle form + `abs=1e-12` 钉值零容差,风格对齐 `tests/test_safeguards.py::test_max_grad_constants_principle_form`(ad64063 同 commit 加的 reference)。

不动 src/ 不动 spec 不动 ticket。当前 `tests/test_beta.py` L187 + L200 的具体形态详见 proposal.md "What Changes" 段。

## Goals / Non-Goals

**Goals:**
- L187 / L200 两处 literal `15.95` / `15.5` 钉值替换为 literal principle chain `0.25 * 2 * 31.9` / `0.25 * 2 * 31.0`
- 容差由 `abs=1e-6` 收紧到 `abs=1e-12`(per `governance/spec.md req-gov-1` 浮点闭式钉值零容差)
- 风格对齐 `tests/test_safeguards.py:644-692` `test_max_grad_constants_principle_form`(ad64063 已建立的 project 原则)
- 不引入新 test function;现有 `test_name` 数不变;test 形式层 surgical,test 断言语义层完全对齐 ad64063 设计意图

**Non-Goals:**
- 不修改 `src/decompmoe/beta.py`(`MAX_GRAD_PER_GAMMA` / `MAX_GRAD_PER_GAMMA_PHASE4` / `SIGMA_PRIME_AT_ZERO` / `ANTIPODAL_INNER_EXTREME` 在 ad64063 已用 module attribute principle form 定义,无 retune 需求)
- 不修改 `tests/test_safeguards.py::test_max_grad_constants_principle_form`(ad64063 reference 风格,不动)
- 不修改 `tests/test_beta.py::test_grad_gamma_bound` 与 `test_max_grad_per_gamma_phase4`(ad64063 已迁移,autograd-vs-analytic 容差 `abs=1e-6` 是另一种语义层)
- 不修改 spec(`.openspec.yaml` `skip_specs: true`,spec `req-7` 已 lock principle form)
- 不引入 shared expert / training / baseline(per CLAUDE.md §6 / §7)

## Decisions

### Decision 1: literal principle form vs module attribute form

**选择**:literal form `0.25 * 2 * 31.9` / `0.25 * 2 * 31.0`(本 change 采用)

**理由**:literal form 真正钉住子常量值。若未来 `SIGMA_PRIME_AT_ZERO` retune 为 `0.3`(虽 spec 不允许,但 code 端可能因修改引入),literal chain `0.25 * 2 * 31.9` 仍断言 15.95,测试 fail,**暴露 silent drift**。而 module attribute form `beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN)` 是 trivially-true 恒等式(`MAX_GRAD_PER_GAMMA` 本身在 `beta.py:45` 就是这个 expression,改任何一边都同步改),**无 testing value**。

**alternatives considered**:
- module attribute form `beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN)`:与 `test_grad_gamma_bound` (L165-172) 风格一致,但 L165-172 是 autograd-vs-analytic 比较(autograd 引入 FP 累积误差,需要 `abs=1e-6` 容差),而 L187 是 module-attribute-vs-literal(FP-exact 无 FP 累积),用 module attribute 是 trivially-true,无意义
- mixed form(L187 module attribute / L200 literal):两个测试覆盖不同维度,但风格不统一,与 reference `test_safeguards.py` 不一致
- 拆 L187 = `beta.MAX_GRAD_PER_GAMMA == pytest.approx(beta.MAX_GRAD_PER_GAMMA, abs=0)` trivially-true,直接拒绝

### Decision 2: 容差 `abs=1e-12` vs `abs=1e-6`

**选择**:`abs=1e-12`(本 change 采用)

**理由**:`governance/spec.md` `req-gov-1` 明文要求浮点闭式 `pytest.approx(value, abs=1e-12)`("钉值零容差")。L187 / L200 是 module-attribute-vs-literal 比较(FP-exact,无 autograd FP 累积),`abs=1e-6` 是 ad64063 给了 autograd-vs-analytic 的容差(autograd 有 ~1.9e-7 FP 累积,需要宽松容差),但 L187 / L200 不属于这个语义层。

**alternatives considered**:
- `abs=1e-6`:与 ad64063 autograd tests 数值一致,但**错位**——把 autograd 容差套到 FP-exact 比较,会掩盖 silent drift(子常量若 retune `1e-7`,`abs=1e-6` 仍能 pass)
- `abs=1e-3`:原 `test_max_grad_per_gamma_phase4_closed_form` (c26241b 加)的初始容差,过松,已被 ad64063 收紧到 `1e-6`,本 change 再收紧到 `1e-12`

### Decision 3: docstring 修改范围

**选择**:仅 L187 `test_constants_exported` docstring 扩展(原 docstring 只说"import + Final[float] type guard",新 docstring 反映 principle-form factor guard)。L200 `test_max_grad_per_gamma_phase4_closed_form` docstring **不改**(c26241b 加时已写 `31·0.25·2 = 15.5` derivation chain,principle form 已隐含;改 literal assertion 即可,docstring 已正确)

**alternatives considered**:
- 两处 docstring 都改:对 L200 重复,scope 膨胀,违反 CLAUDE.md §3 "Surgical Changes"

## Risks / Trade-offs

- **[Risk] FP 累积路径不同**:`pytest.approx(0.25 * 2 * 31.9, abs=1e-12)` 的字面 `0.25 * 2 * 31.9` 在 Python float64 下 = `15.950000000000001`;`beta.MAX_GRAD_PER_GAMMA` = `SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME * (BETA_MAX - BETA_MIN)` = `0.25 * 2.0 * 31.9` FP 累积路径不同,可能产生 ~1e-15 偏差 → **Mitigation**:`pytest.approx` `abs` 是绝对容差,1e-15 << 1e-12,测试通过;tasks.md §2.1 / §2.2 post-apply 跑 `pytest tests/test_beta.py::test_constants_exported tests/test_beta.py::test_max_grad_per_gamma_phase4_closed_form -v` PASS 验证
- **[Risk] literal 与 module sub-constant drift**:若 beta.py 子常量被 retune(如 `SIGMA_PRIME_AT_ZERO = 0.3`),literal chain `0.25 * 2 * 31.9` 仍断言 15.95,测试 fail → 这是 literal form 的**设计意图**(测试要 fail 来暴露 drift),不是 bug。Mitigation:本 change 不主动 retune beta.py,仅 fix test;若 post-apply 真有 silent drift,会立刻暴露
- **[Risk] `abs=1e-12` 过严反而引入 false negative**:若未来 `pytest` / Python / `torch` FP 实现升级改变 `0.25 * 2 * 31.9` 字面 FP 值,可能 fail → Mitigation:Python float64 实现稳定几十年,这种风险 < 1e-12 数量级;且 `pytest.approx` 容差是 soft,不会引入 hard fail
- **[Risk] 与 test_safeguards.py 部分重复**:改完后 L187 / L200 与 `test_safeguards.py::test_max_grad_constants_principle_form` (L644-692) 部分断言重叠(`MAX_GRAD_PER_GAMMA == pytest.approx(0.25 * 2 * 31.9, abs=1e-12)`) → **Mitigation**:这是测试责任分层,每个测试 focus 不同(`test_metrics.py` 测试 import + Final[float] type + value chain;`test_safeguards.py` 测试 principle-form factor-collapse guard);ad24863 的设计就是同一 derivation chain 从不同角度测,与 ad64063 autograd test 与 safeguards test 重叠一致
- **[Risk] Windows Edit tool CRLF contamination**:Edit tool on Windows + 非 ASCII 文件可能引入 CRLF(per memory `Edit tool on Windows can introduce CRLF in non-ASCII files` 2026-09-23 lesson)→ Mitigation:tasks.md §3 二次 byte-level 检查 `($bytes | Where-Object { $_ -eq 13 }).Count == 0` 验证 LF 保留
- **Trade-off [literal form 缺点 trade-off]**:literal chain grep 不指向 module 子常量(`grep "0\.25 \* 2 \* 31\.9"` 不能直接看到 `beta.SIGMA_PRIME_AT_ZERO` 引用)→ Mitigation:docstring 中说明 derivation chain 数学语义;reference test_safeguards.py 已建立该 trade-off 接受