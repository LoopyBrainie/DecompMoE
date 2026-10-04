# Proposal

## Why

`wayfinder` req-14（`spec.md` 的 "Five-Phase Time-Driven Schedule"）要求 operational β 在 Phase 2 ramping `1.0 → 4.0`、Phase 3 ramping `4.0 → 16.0`；req-24（"Beta Parameterization Space vs Operational Domain"）规定 `β^eff = Clamp(β^param(γ), 1.0, β_max(t))`，而 Phase 3 的 `β_max(t)` **就是**那条 ramp。两条要同时成立，`β^eff` 必须逐点 `≡ cap(t)`；而 `Clamp(x, ·, cap) ≡ cap` 当且仅当 `x ≥ cap`，此时 `∂β^eff/∂γ = 0`。**ramp 与非零梯度在 req-24 的公式下结构互斥**，必须裁决哪条是 normative。

当前实现两条都没交付。Phase 2 是**确定违反**：`phase_step_frozen_names(2)` 返回 `{"c_i", "beta_i"}`，γ 被冻结、无 weight decay、`β^param ≡ β^param(γ_init) = 1.035060`；`cap` 越过 1.035（step `6_000 + 20_000·(0.035/3) = 6_233`）后 `β^eff` 钉死在 1.035，**剩余约 19 767 步完全平**，与超参无关。Phase 3 的违反程度依赖未指定量：`phase_step_frozen_names(3)` 返回 `{"c_i"}`，β_i 解冻，decoupled weight decay 的不动点是 `γ = 0`，`β^param` 最终会越过 cap —— 但**越过时刻由规范未 pin 的 `lr` 与 weight-decay 系数决定**。

本 change 裁决 ramp 为 normative，并交付一个确定性的机制。

## What Changes

- **Phase-2 入口 γ reset**：进入 Phase 2（`step = 6_000`）时 `γ` reset 为 `gamma_reset_for_phase2() = 0.0`，使 `β^param(0) = 0.1 + 31.9·σ(0) = 16.05` 落在 Phase-2/3 的 cap 饱和区。饱和不等式：`16.05 > phase_beta_max(3, 55_999) = 15.9996`，裕量 `5.04e-2`。该 reset 与已 spec 的 `gamma_reset_for_phase4` 完全同构，是仓库内已有模式的复用。
- **`req-24` 加 2 个 Scenario**（**只加，不改正文**）：Phase-2 入口 γ reset 的闭式与逐点 `β^eff ≡ cap(t)` 契约；γ 梯度通路自 Phase 4 起存在的契约，并显式区分三个易混梯度量。`req-14`、`req-29` 一字不动 —— req-14 的 ramp 主张不变，它第一次被真正交付。
- **`src/` 改动**：新增 **1 个**公开符号 `gamma_reset_for_phase2()`。**不新增** operational 读取路径（`beta_effective_operational` 在实现阶段被否决，理由见 `design.md` D2：它在 ramp=normative 语义下零可计算内容，且与 `beta_effective` 构成永久命名漂移风险）。`beta_effective` **签名与函数体不动**，只补 docstring 契约声明（排程层 helper、`float` 入参 + 叶子张量出参、non-differentiable by design、精度帧声明）；`beta.py` 补饱和区梯度推导注释。**既有 0 条测试断言被削弱或删除**；5 条 req-1 计数断言按 bump 后的新契约重新钉定（见 Capabilities → `decompmoe-skeleton`）。
- **不新增导出常量**：`31.9·σ′(γ) ≤ 31.9·0.25 = 7.975` 只作推导注释写入，logit 侧 ×2 回到 req-7 已钉的 `15.95`，不新增界。

**为何新增函数而不改 `beta_effective`**：`test_schedule.py::test_beta_effective_phase_2_3_use_inverse_temperature` 显式传 `γ = −5.0` 并期望下界饱和得 1.0，`test_a3_contract_alignment.py::test_beta_effective_at_100k_is_unchanged` 同理。若让 `beta_effective` 忽略传入 γ，这两条立刻变红，且需连带修改 `decompmoe-skeleton` req-20/req-33 的签名契约。故 Phase-2 入口 γ 的**重置值**由新函数 `gamma_reset_for_phase2()` 承载，而「`β^eff` 逐点 `≡ cap(t)`」这个不变量则完全由既有符号 `beta_effective` + `phase_beta_max` 承载（写成 `req-24` 的 Scenario，不引入第三个函数名）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder`: req-24 新增 2 个 Scenario，固定 Phase-2 入口 γ reset 的**饱和闭式与精度帧**（float32 帧内 bit-exact；float64 帧偏移只作文档），以及 γ 梯度通路的相位边界。正文语义不变。
- `decompmoe-skeleton`: req-1 的三个公开面计数随新公开符号 bump —— 去重 union `75 → 76`、未去重 per-module sum `76 → 77`、包级 `__all__` `78 → 79`。去重规则与「唯一碰撞是 `flops_per_token`」不变（新符号无跨模块同名碰撞），并新增一条 Scenario 把「公开符号 MUST 在 `__all__` 上」与「计数 MUST 被任何增减公开符号的 change 重新钉定」写成可验条款。

## Impact

- **规范面**：`openspec/specs/wayfinder/spec.md` 的 `req-24` 增加 2 个 Scenario（正文语义不动）。`req-14` / `req-24` 正文 / `req-29` 不动。`openspec/specs/decompmoe-skeleton/spec.md` 的 `req-1` 三个公开面计数 bump（`75→76` / `76→77` / `78→79`）并新增 1 条 Scenario；其 `:492` 声明 `beta_effective` 签名 "exactly 3 positional args" 而代码为 3 位置 + `total_steps` 默认参，属**已登记的既有漂移**，**不在本 change 范围**。
- **实现**：`src/decompmoe/schedule.py`（新增 1 个符号 + 模块 docstring + `__all__` 登记 + `beta_effective` docstring）、`src/decompmoe/__init__.py`（再导出 + `__all__` + 模块 docstring 计数）、`src/decompmoe/beta.py`（仅注释）。
- **测试**：`tests/test_schedule.py` 新增 3 个测试函数 / 10 条断言——`test_gamma_reset_for_phase2_is_zero`（1）、`test_saturation_margin_holds_in_float32_frame`（3，严格 `>` 无容差 + `round(...,4)==15.9996` 精确舍入钉法 + 裕量 `>0.05`）、`test_beta_effective_saturated_branch_is_bit_exact_with_float32_cap`（1 条 `torch.equal`，6 点 pinned grid，逐点无容差）、`test_gamma_gradient_exists_only_from_phase_4`（5 条，Phase 2–3 梯度 bare `== 0`，Phase 4 `grad_fn is not None` + `≈ 240/31`）。`tests/test_a3_contract_alignment.py` 的 5 条 req-1 计数断言 `75/76/78 → 76/77/79` 重新钉定（**整数闭式 bare `==`，容差不动**），陈旧注释 `beta_param = 15.5` 更正为 `0.1 + 31.9·σ(0) = 16.05`。
- **不受影响**：`req-29` 的 `|jump| < 5e-4` 在本 change 下原样成立（Phase-3 出口 attained = `15.9996`，Phase-4 入口 `1 + 31·σ(ln(15/16)) = 16.0`，`4e-4 < 5e-4`）。
- **不做**：不执行训练或 baseline（formalize-only），不引入训练循环，不改 `openspec/changes/**` 以外的任何面。
