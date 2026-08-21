## Context

OpenSpec 文档层 13 项 spec-level 缺陷（编号 A-1 ~ A-13）的修法已在
`proposal.md` Why + What Changes 段锁定。本文档聚焦**实现侧的设计决策**：
如何把 spec 文本落地到 OpenSpec 主 spec、skeleton spec 与 wayfinder
tickets 三处，并保证下一阶段 `fix-openspec-doc-bugs-apply`（code-level
change）能无歧义地按 spec 同步代码。

本 change 严格 spec-only（Q14 决议），不动 `src/decompmoe/*.py` 与
`tests/*.py`；代码层修复留给后续 change。本 design 文档因此不需要
讨论实现语法（如 PyTorch / NumPy 细节），只需要把 spec 的**架构裁决**
（特别是 Q3/Q13 双通道解耦、Q5 Beta 函数反演、Q11 β 下界解耦、Q7 FLOPs
口径）讲清楚。

## Goals / Non-Goals

**Goals:**
- 把 spec 文本组织为「主 spec 唯一形式化真相源 + skeleton spec 验收口径收紧 +
  ticket 依赖图」三层结构，每层各司其职。
- 在 spec 文本中显式标出**所有不可直接计算或自相矛盾的定义**
  （如 θ_Voronoi 闭式、`L_lb` 双因子、Phase 1 α=0.90 与 "frozen" 的解耦）。
- 让后续 `fix-openspec-doc-bugs-apply` 阶段的 code-level delta 能
  直接 grep 到每条 spec 条款的**字面 keyword**（如 `1/(2·N_e)`、
  `Masked Spherical EMA`、`β^param`、`Canonical Voronoi`）作为
  实现锚点。
- 把 Q5/Q7/Q11/Q13 的数学裁决（Beta 函数反演、SwiGLU 3-矩阵 FLOPs、
  γ' 重参数化、CentroidDriver 双通道）以**闭式**形式写入 spec，
  消除「黑盒数值 + 来源不明」的状态。

**Non-Goals:**
- 不修改 `src/decompmoe/*.py`（Q14 边界）。
- 不修改 `tests/*.py`（Q14 边界）。
- 不执行训练、不跑 baseline、不读实验数据（CLAUDE.md §6）。
- 不重写 wayfinder ticket 来"调和" spec ↔ ticket 不一致——已对齐；
  残余差异按 ticket 流程走（CLAUDE.md §6 末项）。
- 不同步 Wayfinder 附件版 map.md（Q8）；附件同步方向待外部环境决定。
- 不引入新的 capability 边界（proposal.md 已声明 New Capabilities = 空，
  所有修订在 `wayfinder` 与 `decompmoe-skeleton` 两个现有 capability 内）。

## Decisions

### Decision 1 — 主 spec 为唯一形式化真相源，skeleton spec 引用之

**Choice**：主 spec `openspec/specs/wayfinder/spec.md` 拥有所有**闭式与数学裁决**
（`L_lb` 双因子、`L_sep` Frobenius、8 个指标闭式、`θ_Voronoi` Beta 函数
反演、`β^param` vs `β^eff` 解耦等）。skeleton spec
`openspec/specs/decompmoe-skeleton/spec.md` **不重复定义**，只通过
验收口径引用主 spec（如「`flops_per_token` MUST return value matching
master Req 19」）。

**Rationale**：Q2 元规则——wayfinder decision map 是真理源；spec 文本
双份维护已经在 A-1/A-4/A-7 处造成漂移。统一到主 spec 后，skeleton spec
的修订面收缩到「验收口径 + test scenarios」两类，可读性更高，drift 风险
下降。

**Alternatives considered**：
- (a) 两份 spec 各自独立可读——会被 A-1/A-4/A-7 已发生的 drift 反例否决。
- (b) 合并为单一 spec——违反 §6 Hard Constraints「不绕过 OpenSpec 直接改
  行为」的语义边界，且 skeleton spec 的模块边界含义丢失。

### Decision 2 — `CentroidDriver` 双通道在 spec 中显式拆为两栏表

**Choice**：Q3/Q13 的核心裁决——Driver Channel（CentroidDriver，梯度-free）
与 Gradient Channel（AdamW）严格正交——在主 spec Req 6 / 14 / 20（新增
不变量段）以 **Markdown 表格** 形式呈现，每个 Phase 一行，包含四列：
Driver Channel 行为、Gradient Channel 状态、EMA α、物理语义。

**Rationale**：表格比散文更易验证 "Phase 1 既冻结 c_i 又以 α=0.90 更新
c_i" 之类的二义性表述。后续 code-level change 在 grep 「Phase 1」
时，可以直接命中表格行，零歧义。

**Alternatives considered**：
- (a) 散文描述 Driver/Gradient 双通道——容易被读者合并为单通道（Q9 的
  "Phase 1 NoOp" 就是这种合并错误）。
- (b) 状态机图（Mermaid / UML）——增加 spec 的图形依赖，违反「Markdown
  only」的 spec 约束。

### Decision 3 — `L_lb` 闭式显式写出「f_i.detach() × P_i」双因子

**Choice**：主 spec Req 12 写明 `L_lb = N_e · Σ_i f_i.detach() · P_i`，
其中 `P_i = (1/T) · Σ_t p_i(C_t)`。skeleton spec 同步，验收改为
「`∂L_lb / ∂P_i ≠ 0` AND `∂L_lb / ∂f_i ≡ 0`」（双重约束）。

**Rationale**：A-1 的根因是单 `.detach()` grep 假绿。spec 必须把
「梯度从 P_i 流回 logit」这一物理路径明确化，才能让验收环节区分「真
detach」与「假 detach」（如把 detach 放在结果上而非 f_i 上）。

**Alternatives considered**：
- (a) 仅写「`f_i.detach()` 在 L_lb 中」——已被 B-1 反例否决。
- (b) 写实现细节（如 `f_i = topk(softmax(...)).mean(0).detach()`）——
  违反 spec「行为合同，不实现计划」约束。

### Decision 4 — `θ_Voronoi` 双 API：canonical（闭式）+ measurement（离线）

**Choice**：主 spec Req 11 引入两个 API：
- `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float`——
  配置/查表层，闭式 Beta 函数反演，常量表 (16,16)→52° / (64,16)→25.45°。
- `voronoi_angle(centroids: Tensor) -> float`——测量层，对实际质心张量
  做蒙特卡洛估计，**仅离线**使用。

**Rationale**：Q5 裁决——canonical 与 measurement 的语义边界不同：
canonical 用于「配置阶段就该知道的几何下界」，measurement 用于「离线
checkpoint 评估」。如果只保留一个 API（合并或择一），MVP 几何验证
门槛的核验路径会与离线分析路径耦合，无法独立审计。

**Alternatives considered**：
- (a) 仅 canonical——损失对实际质心形态的诊断能力（A8-2 baseline 隔离
  需要 measurement）。
- (b) 仅 measurement——MVP 启动时无质心可测，几何下界无法计算。

### Decision 5 — 路由开销单列不入 parity

**Choice**：主 spec Req 19 把 Active-Core FLOPs 与 Routing FLOPs **物理
分列**。Parity 约束 `d_ffn^Dense ≡ k · d_ffn^Expert` 仅作用于 Active-Core
（attention + FFN）；Routing FLOPs 单独统计，约束「占比 ≤ 0.3%」。

**Rationale**：Q7 裁决——`FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c`
= 66_048 FLOPs/layer（MVP）= 0.26% core，与 1:1 parity 兼容但不应混淆。
如果合并入 parity，C 提取项会让 MoE 在 strict 1:1 下"超 par"（不允许）
或让 Dense 侧补一个虚假项（不一致）。

**Alternatives considered**：
- (a) parity 含 routing——parity 不可能严格 1:1（A-7 的根因）。
- (b) 隐式忽略 routing——现状，与 spec「严格 1:1」表述冲突。

### Decision 6 — β 下界「参数化空间 vs 运行期生效域」双域解耦

**Choice**：主 spec Req 7 + 新增不变量段把 β 拆为：
- 参数化空间：`β^param(γ) = 0.1 + 31.9 · σ(γ)`，理论区间 `[0.1, 32]`。
- 运行期生效域：Phase 1 = 1.0 固定；Phase 2-3 = `Clamp(β^param, 1.0, β_max(t))`；
  Phase 4 = `1 + 31 · σ(γ')`，γ' = ln((β_p3-1)/(32-β_p3)) 保证连续。

**Rationale**：Q11 裁决——避免 Phase 4 硬 clamp 在 `[1.0, 32.0]` 边界处
梯度归零（Zero-Gradient Trap / One-Way Ratchet）。同时保留 `β_min = 0.1`
的冷启动健康梯度（`σ'(−3.5) ≈ 0.0284`，下界改 1.0 会要求 γ_init ≈ -6.94，
梯度衰减 29×）。

**Alternatives considered**：
- (a) 合并为单一 β = 1 + 31·σ(γ)——与 wayfinder 原票不兼容，需重新
  grilling 裁决（Q2 元约束禁止）。
- (b) Phase 4 硬 clamp + 边界例外——已造成 One-Way Ratchet 风险。

### Decision 7 — 死专家阈值参数化为 `1/(2·N_e)`，不硬编码 `1/32`

**Choice**：主 spec Req 13 + skeleton spec Five Numerical Safeguard Helpers
Requirement 都改为 `threshold = 1/(2·N_e)`，默认参数从 `N_e` 推导；
MVP `N_e=16` 下评 `1/32`。

**Rationale**：Q4 裁决——避免后续改 N_e 时阈值 silently 漂移（A-9 的根因）。
参数化形式让"1/(2·N_e)"成为 **不可变规则**而非"1/32 是孤立数值"。

**Alternatives considered**：
- (a) 保留 1/128——N_e=64 时代产物，与 N_e=16 的设计意图脱节。
- (b) 改为 config 参数 `c/N_e`——MVP spec 不需要灵活性（Hard Constraints
  §6），spec 应锁值。

### Decision 8 — 隐含前提显式化（weight tying、GQA 退化、零 bias、四舍五入）

**Choice**：主 spec Req 11 列出 4 大前提 + 通用公式 `P_attn/layer =
2·d_model² + 2·d_model·d_kv`。

**Rationale**：A-10 的根因——452M / 100M / `4·d_model²` 这些数值依赖
**未写明**前提（weight tying + GQA 退化 + 零 bias + 边缘参数吸收）。
后续启用真 GQA 或解绑 lm_head 会让公式失效却无法审计。

**Alternatives considered**：
- (a) 仅在 code-level spec 提——与 §2 Truth Source Hierarchy「spec 在前」
  冲突。
- (b) 只在 design.md 提——spec 与 code 不一致时仍以 spec 为准，前提必须
  在 spec 内可见。

### Decision 9 — 8 个指标闭式分 Realtime / Offline 两层

**Choice**：主 spec Req 20 用 Markdown 表格分两栏：Realtime（每步）与
Offline（诊断运行）。每个指标含「Definition / Range / Notes」三列。

**Rationale**：Q6 裁决——A-2/A-8 advisory 判据依赖指标精度，特别是 R_H /
S_load / UR 三项进 Layer-2 advisory。spec 必须把闭式精确化（不仅是「名称 +
括号」），否则代码层「与 spec 一致」无意义。

**Alternatives considered**：
- (a) 仅名称 + A8-2 反链——与 A-6 现状相同，drift 风险不收敛。
- (b) 实现级签名（如 `metrics.py::L_sep`）——违反 spec 抽象层级。

### Decision 10 — 3 个 invariant test scenarios 落在 skeleton spec 的 ADDED 段

**Choice**：skeleton spec 新增一个 Requirement「Centroid Driver Invariant
Test Scenarios」，包含三个 Scenario：
- `test_empty_cell_preserves_centroid`
- `test_spherical_norm_is_strictly_one`
- `test_near_zero_candidate_fallback`

**Rationale**：Q10 / A-3 衍生——这三个 Scenario 直接对应 Q3/Q13 的核心
物理不变量（空 Cell 显式回退 + 球面回投 + 零向量保护），是 spec 层
「可测试性的合同」。后续 code-level change 写这三个 test 时直接按
Scenario 命名一一对应，零歧义。

**Alternatives considered**：
- (a) 把 Scenario 放在主 spec——主 spec 不该定义 test 命名（属于
  skeleton spec 责任）。
- (b) 散落在各 MODIFIED Requirement——后续 grep 找不到完整清单。

## Risks / Trade-offs

**[Risk 1] 隐式 baseline 漂移未被本次 change 触及**：
A-8（w_i 残留主 spec 文句）已经删除，但代码层 `contracts.py` / `distance.py`
本就没有 w_i，已经是 clean 状态——这是「现状即合规」的好情况，但未来
实现者如果按 spec 文本新增 w_i 会重新引入 bug。**Mitigation**：主 spec
Req 7 明确「`w_i` MUST NOT appear in any stage, in any formulation, in
any reserved form」，不留"reserved for later"的尾巴。

**[Risk 2] Q9 的 "Phase 1 NoOp" 表述已在 Q13 被识别为误差**：
未来 ticket A6b-3 落写时若再误用 NoOp 描述 Phase 1，会重蹈覆辙。**Mitigation**：
主 spec Req 6 + 新增不变量段都明确「Driver Channel Active」+「Gradient
Channel Frozen」二元区分；`phase_step_frozen_names` 在 skeleton spec
被修正为「gradient-channel frozen names」，强化术语。

**[Risk 3] Beta 函数反演的 `canonical_voronoi_angle` 实现依赖 scipy**
——MVP 尺度无 scipy 风险（`scipy.special.betainc` 是 stdlib），但需
确认 deployment 环境。**Mitigation**：spec 不强制 scipy 实现（可换 mpmath
或自实现 bisection），skeleton spec 的实现侧留给后续 code-level change。

**[Risk 4] `β^param` vs `β^eff` 双域语义容易在实现层混淆**：
实现者可能仍把 `β^param` 直接喂给 logit 而忽略 phase-specific `β^eff`。
**Mitigation**：主 spec Req 7 的 Invariant 3 明确「per-phase effective β
MUST be: ...」，并显式 Phase 4 = `1 + 31·σ(γ')`（而非 `Clamp(β^param, 1.0, 32)`），
避免后续回归硬 clamp。

**[Risk 5] 死专家阈值 `1/(2·N_e)` 在 Phase 0/4 边界处的语义**：
A5-3 v2 没显式讨论 Phase 0（K-Means seeding，无 f_i 概念）与 Phase 4
（已启用 Dead Expert Resurrection）的交互。**Mitigation**：当前 MVP
spec 在 Phase 0 关闭所有 safeguard（无 f_i 可观测），在 Phase 4 启用；
spec 不显式约束该边界，符合 wayfinder 原设计意图。

**[Risk 6] `L_lb = N_e · Σ_i f_i.detach() · P_i` 在 batch size = 1 时退化**：
P_i = (1/T)·Σ_t p_i(C_t) 在 T=1 时退化为单 token 概率，f_i.detach()
与 P_i 的乘积不稳定。**Mitigation**：spec 层面无 batch size 约束（属于
实现级 A8 baseline 议题），不在本次 change 范围。

**[Risk 7] Wayfinder 附件版 map.md 与仓库版差异未被同步**：
外部环境使用附件版会看不到本次 spec 修复。**Mitigation**：proposal.md
"A-13" 段明示「以仓库 OpenSpec + tickets 为真理源」，附件同步方向
待外部决定；本 change 不主动同步。

## Migration Plan

本 change 是 spec-only，无运行时迁移：

1. **apply 阶段（spec archive）**：`openspec archive-change fix-openspec-doc-bugs`
   把 delta spec 合并到 `openspec/specs/wayfinder/spec.md` 与
   `openspec/specs/decompmoe-skeleton/spec.md`。
2. **下游 change 触发**：archive 完成后立即创建
   `fix-openspec-doc-bugs-apply`（code-level change），按主 spec 的 grep
   keyword 锚点同步 `src/decompmoe/*.py` 与 `tests/*.py`。
3. **rollback**：如果下游 apply 失败，回滚手段是 `openspec archive-change`
   反向操作（从 git 历史 revert 本 change 的 spec delta）。

## Open Questions

无。所有 grilling 决策已落地到 spec 文本。