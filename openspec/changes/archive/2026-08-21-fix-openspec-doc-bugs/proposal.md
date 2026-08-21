## Why

OpenSpec 文档层存在 13 项 spec-level 缺陷（编号 A-1 ~ A-13），覆盖主 spec
`openspec/specs/wayfinder/spec.md` 与 skeleton spec
`openspec/specs/decompmoe-skeleton/spec.md` 的多处内部矛盾、公式缺失、
定义模糊与决策漂移。这些缺陷直接导致了 `add-decompoe-skeleton-with-tdd-tests`
change 中的 B-1 假绿测试（skeleton spec 的"source grep 找 `.detach()`" 验收
通过任何含 `.detach()` 的表达式）与 B-2 隐式未归一化假设，并且让 wayfinder
已裁决的决策在 ticket ↔ spec ↔ code 三层之间互相打架。本次 spec-only
修订把这 13 处 spec-level debt 一次性闭环，使后续 code-level change 的
「spec 一致性」验收环节回归可信。

## What Changes

主 spec `wayfinder` 的 8 处 Requirement 修订 + 1 处新增不变量段；skeleton
spec `decompmoe-skeleton` 的 8 处验收口径收紧 + 3 个新 test scenarios；
新增 ticket **A6b-3**（CentroidDriver 全生命周期架构契约）；更新 ticket
**A6a-2**（死专家阈值 1/128 → `1/(2·N_e)`）与 **A5-3**（v3，g_boundary
核验）。

**BREAKING**: 无；本 change 仅修改 spec 与 ticket 文本，不动
`src/decompmoe/*.py` 与 `tests/*.py`，后续 code-level change 负责把 spec
层决策同步到代码（按 §6 Hard Constraints 「改 spec 对齐 ticket」 走）。

具体修订：

- **Req 6**（A-3 / Q3 / Q13）：显式「双通道」 — Driver Channel
  (CentroidDriver) vs Gradient Channel (Autograd/AdamW) — 区分；α 序列
  `0.90 → 0.95 → 0.99` 与 Phase 1 显式为驱动 Active + 梯度 Frozen。
  新增 Source 链 A6b-3。
- **Req 7**（A-8）：删 "w_i is reserved for post-aggregation mixing" 末句，
  改「混合权重 = softmax 概率 p_i，w_i 在任何阶段都不出现」。
- **Req 11**（A-2 / A-10 / Q5 / Q12）：补 `canonical_voronoi_angle(N_e, d_c)`
  闭式（正则化不完全 Beta 函数反演）+ `voronoi_angle(centroids)` 测量层 +
  MVP 验证门槛 + 4 大口径前提（W_emb=W_lm_head、GQA→MHA 退化、无 QKVO
  偏置、边缘参数吸收）+ 通用公式 `P_attn/layer = 2·d_model² + 2·d_model·d_kv`
  + 核验值 452.20M / 99.88M。
- **Req 12**（A-1 / A-4）：补 `L_lb = N_e·Σ_i f_i.detach()·P_i`（P_i =
  `(1/T)·Σ_t p_i(C_t)`）闭式；L_sep 统一为 Frobenius 形式
  `(‖C^TC‖_F² −Ne)/(Ne(Ne−1))`，删除 `Σ_{i<j}` 等价式。
- **Req 13**（A-9 / Q4）：死专家阈值改为参数化形式 `1/(2·N_e)`。
- **Req 14**（A-5 / Q3）：冻结集改为「梯度通道冻结集」表述；新增 Phase 4
  连续重参数化 `1 + 31·σ(γ')` 与 Phase 3→4 平滑过渡公式
  `γ' = ln((β_p3−1)/(32−β_p3))`。
- **Req 19**（A-7 / Q7）：补 Active Core FLOPs = `8·d_model² + k·6·d_model·d_ffn^Expert`
  + Parity 约束 `d_ffn^Dense = k·d_ffn^Expert` + 显式排除 Attention QK^T、
  Attn·V、lm_head + 路由开销单列 `4·d_c·H_kv·d_k + 2·N_e·d_c`。
- **Req 20**（A-4 / A-6）：统一 8 个指标闭式（Realtime Tier: L_sep, R_H,
  S_load, UR；Offline Tier: SP_i, D_chord, MCI, CG），分 Realtime/Offline
  两层；**死专家 SP_i ≡ undefined，不得误报为 0**。
- **新增不变量段**（A-1 / A-3 / Q11 衍生）：不变量 1（空 Cell 显式回退）、
  不变量 2（球面回投 + 零向量保护）、不变量 3（β 参数化空间 vs 运行期
  生效域）。

Skeleton spec `decompmoe-skeleton` 同步收紧：
- L_lb Requirement 验收：从 "verified by source grep" 改为「对 P 路径梯度
  非零」。
- voronoi_angle Requirement：从「返回 arctan(π/√d_c)」改为「返回
  `canonical_voronoi_angle(centroids.shape)`」（或与主 spec 闭式一致）。
- EMA 三相位 Requirement 各加 ` / ‖·‖₂` 后缀；Scenario 期望值改归一化形式。
- L_sep Requirement 统一为 Frobenius 形式。
- Phase 1 EMA 验收改为「驱动通道 Active、梯度通道 Frozen」。
- 8 个指标 Requirement 引用主 spec Req 20 闭式。
- FLOPs canonical 公式改为含 attention + SwiGLU 3 矩阵版。
- **新增 3 个 test scenarios**：`test_empty_cell_preserves_centroid`、
  `test_spherical_norm_is_strictly_one`、`test_near_zero_candidate_fallback`。

Ticket 增量：
- **新增** `wayfinder/tickets/A6b-3.md`：CentroidDriver 全生命周期契约，
  Status = Approved，Supersedes A6b-1 中 "Phase 1 Frozen rule" 矩阵单元格。
- **更新** `wayfinder/tickets/A6a-2.md`：死专家阈值 1/128 → `1/(2·N_e)`。
- **更新** `wayfinder/tickets/A5-3.md`（v3）：g_boundary =
  `exp(−16·0.384) ≈ 0.002` 核验（与 N_e=64 行 0.205 同公式体系）。

## Capabilities

### New Capabilities

无（不引入新 spec 边界；所有修订在现有 capability 内）。

### Modified Capabilities

- `wayfinder`：Req 6/7/11/12/13/14/19/20 八处修订 + 新增不变量段；
  Source 链增 A6b-3 与 A8-2 反链；3 处新增 ticket（依赖图）。
- `decompmoe-skeleton`：8 处 Requirement 验收口径收紧 + 3 个新 test
  scenarios。

## Impact

- **Spec 层**：`openspec/specs/wayfinder/spec.md`、
  `openspec/specs/decompmoe-skeleton/spec.md` 大幅修订；这是后续
  `fix-openspec-doc-bugs-apply` 类 code-level change 的「合同」。
- **Ticket 层**：`wayfinder/tickets/A6b-3.md`（新增）、
  `wayfinder/tickets/A6a-2.md`（阈值更新）、
  `wayfinder/tickets/A5-3.md`（v3 核验）。
- **代码层**：本 change **不动** `src/decompmoe/*.py` 与 `tests/*.py`。
  受影响的代码点（后续 change 范围）：
  - `extraction.py` 空 Cell `n_i=0` 显式回退（替代
    `assignment_mask.sum().clamp_min(1e-9)`）。
  - `extraction.py` 所有相位输出 `‖c_i‖₂ = 1` 强制 L2 回投。
  - `safeguards.py` 死专家阈值常量从 `1/128` 改为 `1/(2·N_e)`。
  - `loss.py` L_lb 补 `P_i` 项（若当前实现缺失 P_i）。
  - `metrics.py` 8 个指标对齐 Req 20 闭式。
  - `distance.py` / `gating.py` / `experts.py` 三个模块与主 spec
    双通道 / Masked Spherical EMA / Projected SGD 闭式对齐。
  - `tests/test_extraction.py` 新增 3 个 test scenarios。
- **Wayfinder 附件版**：本 change **不主动同步**附件版 map.md；仓库内
  OpenSpec + tickets 始终为真理源（Q2 元约束）。附件同步方向待外部环境
  决定，本 change 不覆盖附件。

## A-13 Wayfinder 附件同步状态

仓库内 `openspec/specs/wayfinder/spec.md` 与附件版 Wayfinder map.md
存在以下差异（diff 已在 review 时记录）：
- map.md 内容不同；
- 附件多 `research/` 目录；
- 仓库多 `tickets/WF-1.md`、`WF-2.md`（自审 tickets）。

本 change **以仓库内 OpenSpec + tickets 为准**（按 §2 Truth Source
Hierarchy）；附件版同步方向待外部环境决定，不在本 change 范围内自动
覆盖。后续如需附件同步，应由人在外部环境按仓库 ticket map 重新生成
附件 map.md。

## Out of Scope（明确不动）

- 不执行训练、不跑 baseline、不读实验数据（CLAUDE.md §6）。
- 不重写 wayfinder ticket 来"调和" spec ↔ ticket 不一致——已对齐；
  残余差异按 ticket 流程走（CLAUDE.md §6 末项）。
- 不动 `src/decompmoe/*.py` 与 `tests/*.py`（Q14 spec-only 边界）；
  修复留给后续 `fix-openspec-doc-bugs-apply`。
- 不动 Wayfinder 附件版 map.md（Q8）。