## Context

上游 change `fix-math-consistency-audit-2026-08` 已 archive：master specs（`openspec/specs/wayfinder/spec.md` + `openspec/specs/decompmoe-skeleton/spec.md`）携带修正后的闭式常量与不变量。代码/测试层尚未对齐——存在 stub（metrics 4 项）、硬编码表（sphere）、系数错误（config FFN FLOPs）、恒真断言（8 处测试）。任务清单见仓库根 `apply-checklist.md`（17 项，spec-anchored）。本设计不引入新行为，只让实现服从 spec。

## Goals / Non-Goals

**Goals:**

- 17 项 checklist 任务全部落地，每项 TDD：先读 spec 锚点 → 先写失败测试 → 最小实现 → 全套件零回归
- 每个含数值的 spec 算式有 `pytest.approx(..., abs=...)` 直接对账（CLAUDE.md §3 数学约束协议）
- 基线保留：95 passed 不减；新增 ~15 tests → ≥ 110 passed, 0 failed

**Non-Goals:**

- 不改任何 spec（skip_specs: true）
- m1 `halve_lr` 改名、m2 `eps` 分母偏差、m3 `phase_id(100_000)` 边界、m5 viz 免责 — 全部 deferred
- 不执行训练 / baseline / 推理引擎实现

## Decisions

1. **Spec 驱动，不从实现反推**。所有期望值取自 spec 闭式常量或独立 root-finding（如 Voronoi 单调性常量 1.1736/1.1663 rad 来自独立求解 `½·I_{sin²θ}((d_c−1)/2, ½) = 1/N_e`），绝不以 `canonical_voronoi_angle()` 输出为期望值。替代方案（从代码输出 pin 常数）正是本次 audit 要消灭的失效模式。
2. **禁止性约束用 grep/source-inspect，算式用数值对账**（CLAUDE.md §3 适用范围）：`_VORONOI_MVP_TABLE` 不复现、`ExpertPool` 含 `nn.ModuleList` 等用 source 检查；FLOPs/MCI/SP/λ 序列等一律数值验证。
3. **β 参数化原语归位**：`phase4_inverse_temperature` 放 `beta.py`（与 `inverse_temperature` 同居）；调度期函数（`gamma_reset_for_phase4` / `phase_beta_max` / `beta_effective`）放 `schedule.py`。备选（全塞 schedule.py）被拒：破坏模块单一职责。
4. **MCI 输入是 token signatures 而非 centroids**，uncentered second moment `M = (1/|T|)·Σ C_t C_tᵀ`，归一化特征值平方求逆。这是第 3 轮 review 的关键 pin。
5. **复杂度测试不用 torch.profiler**：profiler 计数 backend-dependent，改用闭式 `H_kv·(2·d_k·d_c + d_c) + H_kv·d_c + d_c = 33_040` MACs 手工推导对账。
6. **重写不增计数**：5 个 rewrite 任务替换既有断言（保计数）；仅 new-test 任务增长计数。

## Risks / Trade-offs

- [bisection 删除查表后性能下降] → MVP 规模下可忽略；bisection 收敛阈值由 residual `< 1e-9` 测试守护
- [`phase_beta_max` 时间分段约定与既有调用不一致] → pinned convention 写入 docstring，边界精确值测试（abs=1e-9）锁定
- [metrics 闭式实现对病态输入（全零梯度、rank-1）数值不稳] → spec 场景即边界场景，测试覆盖 zero/rank-1/uniform 三类
- [重写测试时误删仍有效的断言] → 每 rewrite 仅针对 checklist 点名的恒真断言；全套件跑通为准

## Migration Plan

按 checklist §3.1→§3.17 顺序逐项提交（test+impl 同 commit）；每项后跑 `uv run pytest tests/` 确认零回归。无部署/回滚问题（纯库内变更，git 可整体 revert）。

## Open Questions

（无 — 所有决策已由 archived spec 与 apply-checklist.md 锁定。）
