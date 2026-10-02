# 勘误第二轮：修复第一轮自己引入的 spec 数学错误

## Why

change `2026-10-02-audit-a2-errata-and-spec-math-fixes` 已 archive（`openspec/changes/archive/2026-10-02-audit-a2-errata-and-spec-math-fixes/`）。事后对它的产物做了一次独立 code review，复算后发现**第一轮自己引入了 3 个规范性条款错误**，其中 2 个是数学错误：

1. **`4·eps_f64` 被写成普适界，但它不是。** 第一轮把 `decompmoe-skeleton` req-19 的 `pow(2).sum(-1) == 1.0`（bare `==`）改成 `|pow(2).sum(-1) − 1.0| ≤ 4·eps_f64 ≈ 8.88e-16`，量词是「for **any** `z` with `‖z‖₂ ≥ ε`」。长度 `d` 的平方和相对误差是 `γ_{d−1} ≈ d·u`，**与维数成正比**，因此不存在维度无关的常数界。实测（torch，seed 0，20×256 行）该常数在 `d=512` 恰好触界（1.00×），`d=1024` 达 1.12×、`d=4096` 达 1.75×、`d=16384` 达 3.00×；float32 在 `d=4096` 首次越界。**第一轮的测试只扫 `{8,16,32,128}`，结构上无法发现这个失效。**
2. **`wayfinder` req-18 同一句里出现两个互相矛盾的总数。** 文本先说 `z, ẑ, z̄, C`「each `4·d_c·4 = 256 B`, `1_024 B` for all four」，隔两个子句又说该集合「sums to at most `1_600 B`」。`4×256 = 1024 ≠ 1600`。正确分解是 `z, ẑ, z̄` **逐头**（`H_kv·d_c·4 = 512 B` 各）、`C` **均值后**（`d_c·4 = 64 B`），合计 `1_600 B`。
3. **`governance/spec.md` req-gov-1 —— 本仓数值协议本身 —— 仍写死 `33_040` 并点名 `tests/test_extraction.py::test_complexity_budget`。** 第一轮把该测试与两份 spec 都改成了 `33_168`，唯独漏了协议。governance 是 peer 真相源，下一个按 req-gov-1 重新推导的审计者会把 spec「修回」`33_040`。

另有 4 条中低severity：`decompmoe-skeleton` req-6 的 d_c=2 偏差带两端都偏低且把上确界误记在 `N_e=32`；req-19 的 Scenario 引用了它自己没用到的 `abs=1e-6` 且有逐字重复子句；四条 `**Source:**` 的 Decision 标签全部指错 decision；`tests/test_extraction.py` 硬编码 MVP 维度常量。

**为什么必须开新 change 而不能直接改**：`CLAUDE.md` §2 的真相源层级 + §6「不要绕过 OpenSpec 直接改 DecompMoE 行为」要求 `openspec/specs/**` 只经 `openspec archive` 落地。

## What Changes

| Finding | capability | Requirement | 修正 |
|---|---|---|---|
| F1 | `decompmoe-skeleton` | req-19 | 规范界改为维度相关 `γ_{d_c} = (d_c−1)·u/(1−(d_c−1)·u) ≤ d_c·eps`；`4·eps` 降级为**仅 MVP 宽度 `d_c=16`** 的经验包络并给出越界维数；删除逐字重复子句；Scenario 标题去掉 "equals 1.0"；守卫测试名改为 `test_spherical_l2_normalize_residual_dimension_dependent_bound` |
| F2 | `wayfinder` | req-18 | 张量集按逐头/均值后分解，`1_024 B` 与 `1_600 B` 的矛盾消除 |
| F3 | `governance` | req-gov-1 | 义务 1 与 L46–47 Scenario 的 extraction MAC 字面量同步到四项闭式 `33_168`；`pytest.approx(33_040, abs=0)` 示例同步；`Source:` 追加本 change 的 Decision 引用 |
| F4 | `wayfinder` | req-11/17/18/19 | 四条 `**Source:**` 的 Decision 标签按被引 change 的 design.md 实际编号校正（D4→D6、D3→D5、D5→D4 表 E12、D5→D4 表 E11+E12+D5） |
| F5 | `decompmoe-skeleton` | req-6 | d_c=2 偏差带改为开区间实测 `3.63%`–`6.52%`（最小 `3.6300% @ 81.337°`，最大 `6.5174% @ 89.99999°`）；canonical 角偏差改为**随 `N_e` 单调递增**、上确界 `5.3994%`，不再误记在 `N_e=32` |

**测试侧**（直接编辑，不经 archive）：
- `tests/test_sphere.py::test_spherical_l2_normalize_residual_dimension_dependent_bound` —— 断言改为维度相关界 `worst ≤ d·eps` 并扫到 `d=4096`（旧的无量纲形式在 `d≥1024` 会红，已实证）；`4·eps` 包络**仅**在 MVP 宽度断言。
- `tests/test_sphere.py::test_cap_area_dc2_affine_degeneration` —— 扫到 `89.99999°`、带收紧到 `0.036..0.0652`、canonical 加到 `N_e=64` 并新增**单调性断言**。
- `tests/test_extraction.py::test_complexity_budget` —— `flops_routing` / `active_core` 全部改从 `cfg` 派生，并补 `active_core == 33_554_432` 闭式断言。

## Impact

- **不影响任何可执行代码**：`src/` 零改动（与第一轮一致）。
- 两份 spec 的行号会位移，仓库内任何 `req-N L###` 裸行号引用需重新按 anchor 区间校验。
- 治理面受益：req-gov-1 不再与被它点名的测试矛盾。
- 本 change 的 delta 仍是**非连续 requirement 子集**，因此落地**不使用** `openspec archive` 的 spec-update（见 `design.md` D6）。
