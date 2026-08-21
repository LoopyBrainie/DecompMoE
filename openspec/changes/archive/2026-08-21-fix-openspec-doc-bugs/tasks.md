## 1. 主 spec `wayfinder` 修订（按 Requirement 顺序）

- [x] 1.1 Req 6 (A-3 + Q3/Q13) — 改写 `C Extraction Differentiability And Centroid Lifecycle`：引入 Driver Channel / Gradient Channel 双栏；保留 Phase 1–3 masked spherical EMA + α 序列 0.90→0.95→0.99；Phase 4 projected SGD；Source 链增 A6b-3。
- [x] 1.2 Req 7 (A-8 + Q11) — 删 "w_i is reserved for post-aggregation mixing" 末句；补 Operational-domain override（Phase-specific β^eff = 1 / Clamp / 1+31σ(γ')）；补 `β_min = 0.1` 参数化空间 vs `1.0` 运行期下界解耦论证。
- [x] 1.3 Req 11 (A-2 + A-10 / Q5 + Q12) — 补 `canonical_voronoi_angle` 闭式（Beta 函数反演）+ `voronoi_angle` 测量层；MVP 验证门槛 `θ_Voronoi(16,16) ≈ 52° > θ_{1/e}(β=16) ≈ 20.36°`；4 大口径前提（W_emb=W_lm_head、GQA→MHA、无 QKVO 偏置、边缘参数吸收）；通用公式 `P_attn/layer = 2·d_model² + 2·d_model·d_kv`；参数核验值 452.20M / 99.88M。
- [x] 1.4 Req 12 (A-1 + A-4) — 补 `L_lb = N_e·Σ_i f_i.detach()·P_i`（P_i = (1/T)·Σ_t p_i(C_t)）；L_sep 统一 Frobenius 形式 `(‖C^TC‖_F² −Ne)/(Ne(Ne−1))`，删除 `Σ_{i<j}` 等价式（用 2·Σ_{i<j} 因子正确版本替代）。
- [x] 1.5 Req 13 (A-9 / Q4) — 死专家阈值改为 `1/(2·N_e)` 参数化形式；明示 MVP `N_e=16` 下评 `1/32`；Source 链指向 A6a-2 v2。
- [x] 1.6 Req 14 (A-5 / Q3 + Q11) — 冻结集改为「梯度通道冻结集」表述；Phase 4 切换到连续重参数化 `1 + 31·σ(γ')` 与 Phase 3→4 平滑过渡公式 `γ' = ln((β_p3−1)/(32−β_p3))`。
- [x] 1.7 Req 19 (A-7 / Q7) — 补 Active-Core FLOPs = `8·d_model² + k·6·d_model·d_ffn^Expert`；Parity 约束 `d_ffn^Dense = k·d_ffn^Expert`；显式排除 Attention QK^T、Attn·V、lm_head；路由开销单列 `FLOPs_Routing = 4·d_c·H_kv·d_k + 2·N_e·d_c ≈ 66k/layer`（0.26% core）。
- [x] 1.8 Req 20 (A-4 + A-6) — 8 个指标闭式（Realtime: L_sep Frobenius, R_H, S_load, UR；Offline: SP_i, D_chord, MCI, CG）；分 Realtime/Offline 两层；**死专家 SP_i ≡ undefined，不得误报为 0**；Source 链增 A8-2 反链。
- [x] 1.9 新增不变量段 — Req 「Empty-Cell Fallback Invariant」（Invariant 1）+ Req 「Spherical Re-Projection And Zero-Vector Invariant」（Invariant 2）+ Req 「Beta Parameterization Space vs Operational Domain」（Invariant 3）+ Req 「CentroidDriver Dual-Channel Architecture Contract」（Spec Invariant 4）。
- [x] 1.10 主 spec 整体 format check — Req 编号连续、Source 反链完整、Scenario 格式（4 个 #）。

## 2. Skeleton spec `decompmoe-skeleton` 修订

- [x] 2.1 `Active FLOPs Parity Against Dense Baseline` Req — canonical 公式改为含 attention + SwiGLU 3 矩阵版；显式排除 + 路由开销单列；签名改为 `flops_per_token(cfg, arch)`。
- [x] 2.2 `Voronoi Self-Consistency Threshold` Req — 改用 `canonical_voronoi_angle(num_experts, signature_dim)` 闭式 API；删 `arctan(π / √d_c)` 错误公式；MVP `N_e=16, d_c=16` ≈ 52°；新增 `N_e=64, d_c=16` ≈ 25.45° Scenario 验证函数依赖 N_e + d_c。
- [x] 2.3 `Centroid Four-Phase Lifecycle Driver` Req — Phase 1/2/3 EMA 公式各加 ` / ‖·‖₂` 后缀；Phase 4 显式 `c_i ← (c_i − η·∇_{c_i} L_routing) / ‖·‖₂`；`should_resurrect` 阈值改为 `1/(2·N_e)`；新增 Phase-1 driver-Active-despite-gradient-Frozen Scenario。
- [x] 2.4 `Loss Composition With Staged Lambda` Req — L_lb 补 `p_per_expert` 参数 + `L_lb = N_e·Σ_i f_i.detach()·P_i` 闭式 + `P_i = (1/T)·Σ_t p_i(C_t)`；验收改 `∂L_lb / ∂P_i ≠ 0` AND `∂L_lb / ∂f_i ≡ 0`；L_sep Frobenius 形式与 `Σ_{i<j}` 因子修正。
- [x] 2.5 `Five Numerical Safeguard Helpers` Req — `should_resurrect` 默认 `threshold=1/(2·N_e)`；Source 链指向 A6a-2 v2。
- [x] 2.6 `Five-Phase Schedule State Machine` Req — `phase_step_frozen_names` Phase 2 改为 `{"c_i", "beta_i"}`（解冻 W_K/W_V/b）；Phase 3 改为 `{"c_i"}`（解冻 beta_i）；Phase 1 Scenario 补「gradient channel frozen」明示。
  - **返工记录（2026-08-21）**：初版把 Scenario 标题改名为 `Phase-1 router freeze (gradient channel)`，导致 `openspec validate --strict` 报错 `omits scenario(s) the current spec still has: "Phase-1 router freeze"`——`## MODIFIED Requirements` 是**整块替换**语义，改名等于静默删除现行 spec 已验收的 Scenario，archive 会拒绝。已把标题改回 `Phase-1 router freeze`，「gradient channel frozen」明示保留在 THEN 正文内。
- [x] 2.7 `Eight Metrics And Classification` Req — 8 个指标闭式（与主 spec Req 20 一致）；L_sep Frobenius；SP_i 死专家 undefined；D_chord 弦长公式。
- [x] 2.8 `Hard-Constraint Grep Invariants` Req — 加 2 条 grep invariant：`extraction.py` 无 `.clamp_min(ε)` 在 empty-cell 分母；无 `arctan(pi / sqrt(d_c))` 字面量。
- [x] 2.9 ADDED Requirement `Centroid Driver Invariant Test Scenarios` — 新增 3 个 Scenario：`test_empty_cell_preserves_centroid` / `test_spherical_norm_is_strictly_one` / `test_near_zero_candidate_fallback`。
- [x] 2.10 Skeleton spec 整体 format check — Req 编号连续、Scenario 4 个 #、grep invariant 列表完整。

## 3. Wayfinder Tickets 增量

> **裁决（2026-08-21）**：wayfinder 为本项目建立前的 decision map，「没有改动意义，现在以 openspec 的工作流为准」。ticket 不再作为需同步的下游制品，`wayfinder/tickets/` 整体只读。原 3.1 拟新增的 A6b-3（CentroidDriver 全生命周期契约）改由本 change 的 `design.md` Decision 2 + 主 spec ADDED Req `CentroidDriver Dual-Channel Architecture Contract` 承载；对应的落地动作即下述 3.1 的反链改写。3.2–3.5 明确作废。

- [x] 3.1 主 spec delta 反链去 wayfinder 化 — 7 处 `**Source:**`：5 处 `wayfinder/tickets/A6b-3.md`（L20/153/242/258/304）改指 `openspec/changes/fix-openspec-doc-bugs/design.md` (Decision 2)；L83 去掉不存在的 `(v3 section)` 限定并增 Decision 4/8；L129 去掉不存在的 `(v2 — …)` 限定，改为 A6a-2「historical」+ Decision 7「superseded by `1/(2·N_e)`」。验收：delta 中 `A6b-3` 0 命中，无悬空反链。
- [x] 3.2 **~~(已明确作废)~~** ~~新增 `wayfinder/tickets/A6b-3.md`~~ — 裁决作废；内容归宿见 3.1 与 `design.md` Decision 2。
- [x] 3.3 **~~(已明确作废)~~** ~~更新 `wayfinder/tickets/A6a-2.md`（v2）死专家阈值 1/128 → `1/(2·N_e)`~~ — 裁决作废；阈值裁决由主 spec Req 13 + `design.md` Decision 7 承载，A6a-2 保留为历史记录。
- [x] 3.4 **~~(已明确作废)~~** ~~更新 `wayfinder/tickets/A5-3.md`（v3）g_boundary 核验~~ — 裁决作废；核验值由主 spec Req 11 的 `canonical_voronoi_angle` 闭式表承载。
- [x] 3.5 **~~(已明确作废)~~** ~~更新 `wayfinder/tickets/A6b-1.md` 加注 Superseded~~ / ~~更新 `wayfinder/tickets/A8-2.md` 指标闭式对齐~~ — 裁决作废；「A6b-1 Phase 1 Frozen rule 被取代」已由主 spec ADDED Req 正文内的 `is hereby superseded` 声明承载，指标闭式由主 spec Req 20 承载。

## 4. Spec 层验证（必跑）

- [x] 4.1 `openspec validate fix-openspec-doc-bugs --strict` — 全 delta 通过格式校验（Req 编号、Scenario 4 个 #、Source 反链格式）。
- [x] 4.2 跨文档一致性 — 主 spec 所有 `Source:` 反链指向的文件确实存在（`wayfinder/tickets/*.md` 或本 change `design.md`），**无悬空引用**；A-13 段列入 proposal.md。
  - _原口径_：~~反链（如 A3-2、A6a-1、A6b-1、A6b-3、A8-2）的 ticket 文件确实存在~~ —— 3.1 之后 A6b-3 不再被引用，口径改为「指向目标存在」而非「必须是 ticket」。
- [x] 4.3 闭式 grep — 主 spec 中以下 keyword 全部命中：`L_lb =`、`canonical_voronoi_angle`、`L_sep`、`R_H`、`S_load`、`UR`、`SP_i`、`D_chord`、`MCI`、`CG`、`FLOPs_MoE,core`、`FLOPs_Routing`、`1/(2·N_e)`、`β^param`、`β^eff`、`Projected SGD`、`Masked Spherical EMA`、`γ'`、`CentroidDriver`。
- [x] 4.4 不变量 grep — 主 spec 中以下 token 全部命中：`Invariant 1`、`Invariant 2`、`Invariant 3`（以及 Req 标题中的「Empty-Cell」、「Spherical Re-Projection」、「Beta Parameterization」、「CentroidDriver Dual-Channel」）。
  - _原口径_：~~「不变量 1」、「不变量 2」、「不变量 3」~~ —— delta 正文实际采用英文 `Invariant N` 记法，中文 token 从未出现；口径按制品实际写法修正。
- [x] 4.5 Phase 表 grep — 主 spec 中以下 token 全部命中：`α = 0.90`、`α = 0.95`、`α = 0.99`（顺序对应 Phase 1/2/3）；表格行包含 Phase 0/1/2/3/4 五行。
- [x] 4.6 skeleton spec 验收口径 grep — `verified by source grep`、`arctan(π / √d_c)`、`arctan(pi / sqrt(d_c))`、`1/128` 在**排除 Hard-Constraint 禁令行与勘误说明行之后** 0 命中（即：不得作为**现行有效的规定**出现）。
  - _原口径_：~~上述 token 在 skeleton spec 中全部 0 命中~~ —— 该口径不可满足且自相矛盾：`Hard-Constraint Grep Invariants` Req 必须**逐字引用** `arctan(pi / sqrt(d_c))` 才能禁止它，勘误行也必须引用 `1/128` / `verified by source grep` 才能说明「已被取代」。
  - _脚注_：真正的「0 命中」断言目标是 `src/`，由下游 code-level change（见 §6）执行，不属于 spec 层。
- [x] 4.7 skeleton spec invariant grep — `test_empty_cell_preserves_centroid`、`test_spherical_norm_is_strictly_one`、`test_near_zero_candidate_fallback` 三条 Scenario 各出现 1 次。
- [x] 4.8 **~~(已明确作废)~~** ~~ticket grep — `wayfinder/tickets/A6b-3.md` 存在；A6a-2 含 `1/(2·N_e)`；A5-3 含 `exp(−16·0.384)` 与 canonical_voronoi_angle~~ — 依赖已作废的 3.2–3.5，随之作废。

## 5. Out-of-Scope 确认（必跑）

- [x] 5.1 `git status` — 确认 `src/decompmoe/*.py` 与 `tests/*.py` 0 changed（本 change spec-only）。
- [x] 5.2 `openspec status --change "fix-openspec-doc-bugs"` — 输出 `applyRequires` 仅含 `tasks`；所有 required set artifact 状态为 `done`。
- [x] 5.3 `git diff openspec/specs/wayfinder/spec.md` 不在本 change 范围（archive 阶段才合并）。
- [x] 5.4 本 change 仅写入 `openspec/changes/fix-openspec-doc-bugs/` 目录；`wayfinder/tickets/*.md` 零改动（裁决 2026-08-21 之后此条真实成立）。

## 6. Apply 阶段触发（下游，非本 change 范围）

> **状态：已移交下游**。以下 5 条不属于本 change 的执行范围，勾选表示「已明确移交」，而非「已实现」。

- [x] 6.1 **~~(已移交下游)~~** 在本 change archive 后，创建 `fix-openspec-doc-bugs-apply` code-level change（spec-only 的下游）。
- [x] 6.2 **~~(已移交下游)~~** 该 apply change 按主 spec grep keyword 同步 `src/decompmoe/{extraction,loss,beta,safeguards,metrics,distance,gating,experts}.py`。
- [x] 6.3 **~~(已移交下游)~~** 该 apply change 按 skeleton spec 3 个 invariant test scenarios 同步 `tests/test_extraction.py`。
- [x] 6.4 **~~(已移交下游)~~** 该 apply change 跑 `pytest tests/` 全绿（85 个 TDD 测试 + 新增 invariant tests）。
- [x] 6.5 **~~(已移交下游)~~** apply change 完成后由用户显式触发 `/opsx:apply` 进入 implementation 阶段（**不在本 change 范围**）。

---

## 完成度口径（2026-08-21）

本文件共 **42** 条 checkbox。全部勾选**不等于**全部实现，三类语义必须分开陈述：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行** | 32 | §1 全 10 + §2 全 10（2.6 含返工）+ §3.1 + §4.1–4.7（7）+ §5 全 4 |
| **已明确作废** | 5 | §3.2–3.5（wayfinder ticket 更新，裁决作废）+ §4.8（依赖上述作废项） |
| **已移交下游** | 5 | §6.1–6.5（移交 `fix-openspec-doc-bugs-apply` code-level change） |
| 合计 | 42 | |
