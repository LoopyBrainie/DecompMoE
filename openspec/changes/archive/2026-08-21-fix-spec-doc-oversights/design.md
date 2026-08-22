## Context

OpenSpec 文档层 9 项 spec-level oversights（编号 ①~⑨）的修法已在
`proposal.md` Why + What Changes 段锁定。本文档聚焦**实现侧的设计决策**：
如何把 spec 文本落地到 OpenSpec 主 spec（`wayfinder`）与 skeleton spec
（`decompmoe-skeleton`）两处，并保证下一阶段 `fix-spec-doc-oversights-apply`
（code-level change）能无歧义地按 spec 同步代码。

本 change 严格 spec-only（user-locked 决议，与 `fix-openspec-doc-bugs`
边界一致），不动 `src/decompmoe/*.py` 与 `tests/test_*.py`；代码层修复
留给后续 change。Issues ⑥⑦⑧ 在 `proposal.md` "Downstream Hand-off"
段已明确列出后续 apply change 的具体改动，本 design 不再重复实现细节。

## Goals / Non-Goals

**Goals:**
- 把 9 项 spec-level oversights 拆为 6 项**in-scope**（①②③④⑤⑨，全部
  spec 文本修订 + 1 个 ADDED Requirement）与 3 项**out-of-scope**
  （⑥⑦⑧，下游 code-level change）。
- 在 spec 文本中显式标出 spec 不可直接验证的语义不变式（grep 与
  semantic 双层分离），防止 reader 把 grep 当作唯一验证手段。
- 让后续 `fix-spec-doc-oversights-apply` 阶段的 code-level delta 能直接
  grep 到每条 spec 条款的**字面 keyword**（如 `Normalize`、`clamp_min`、
  `test_empty_cell_preserves_centroid`、`Phase 0`）作为实现锚点。
- 把 4 项数值错（①算式 + ④反事实 + ⑤恒真式 + ⑨子公式措辞）的**数字
  修正路径**在 design.md 中以 `Decision X` 形式显式化，便于 post-archive
  独立复核（CLAUDE.md §3）反验。

**Non-Goals:**
- 不修改 `src/decompmoe/*.py`（user-locked spec-only）。
- 不修改 `tests/test_*.py`（user-locked spec-only）。
- 不执行训练、不跑 baseline、不读实验数据（CLAUDE.md §6）。
- 不重写 wayfinder ticket（CLAUDE.md §8 2026-08-21 裁决）。
- 不同步 Wayfinder 附件版 map.md。
- 不引入新的 capability 边界（proposal.md 已声明 New Capabilities = 空，
  所有修订在 `wayfinder` 与 `decompmoe-skeleton` 两个现有 capability 内）。

## Decisions

### Decision 1 — spec-only scope 镜像 `fix-openspec-doc-bugs` 先例

**Choice**：本 change 严格 spec-only，与 `fix-openspec-doc-bugs` archive
（commit `41ac06b`）完全镜像——spec 文本修订 + ADDED Requirement，不动
代码与测试。

**Rationale**：Issue ⑥⑦⑧ 是实现 / 测试缺陷，按先例模式由 archive 后用户
显式触发的下游 change `fix-spec-doc-oversights-apply` 处理。本 change 仅
做 spec-side 的"合同" 修订，apply 阶段按 spec 同步代码。

**Alternatives considered**：
- (a) 把 ⑥⑦⑧ 一起混进本 change（user 已否决）—— 会让 archive 触发时
  代码 / 测试也被同步，与 spec-only 边界冲突。
- (b) 不动 spec 只写 hand-off doc——失去 spec 合同价值，下游 apply 失去
  锚点。

### Decision 2 — ① 算式修法选择「改数字」而非「改口径」

**Choice**：spec 文本中的 `≈ 0.26%` 改为 `≈ 0.20%`，保留 "of
`FLOPs_MoE,core`" 的口径（与同段 `FLOPs_MoE,core^(l) = 8·d_model² +
k·6·d_model·d_ffn^Expert` 定义对齐）。

**Rationale**：`66_048 / 33_554_432 ≈ 0.001968` 四舍五入到 `≈ 0.20%`
（在 0.3% allowance 内）。原 0.26% 是 `66_048 / 25_165_824 ≈ 0.002625`
的分母，对应"仅 expert FFN"而非"FLOPs_MoE,core"。修法选择**改数字**而
非**改口径**，原因：
- 同段已经定义了 `FLOPs_MoE,core^(l)` 含 attention + SwiGLU 3 矩阵版；
  改口径会让"FLOPs_MoE,core" 与"Routing 是其 0.20%"两句话不一致。
- 改数字（0.20%）保留 FLOPs_MoE,core 定义不变，结论（0.3% allowance
  内）不变，仅数值自洽。

**Alternatives considered**：
- (a) 改口径为 "of expert-FFN FLOPs"（user 已不推荐）—— 与同段 core
  定义打架。
- (b) 改 FLOPs_MoE,core 公式为 FFN-only——破坏 active-core 完整性，
  失去 attention 项。

### Decision 3 — ② Phase 0 改为 `c_i ← c_i.detach()` + 上游约束

**Choice**：skeleton spec L128 的 Phase 0 行从
`c_i ← KMeans(C) initialization` 改为
`c_i ← c_i.detach()`（driver no-op），并新增一句"Driver is no-op;
upstream spherical KMeans is assumed to have produced L2-normalized seeds."

**Rationale**：`extraction.py:112-113` 的实际实现是
`if self.phase == Phase.SEEDING: return centroids.detach()`，与"KMeans
initialization" 不一致。原 spec 文本是 driver 内部做 KMeans 的描述，但
driver 实际只做 detach，KMeans 是 training-time caller 的责任。修法
选择**让 spec 文本与实现一致**，并显式把"上游已归一化"作为 driver
的前置条件写出，避免 ‖c_i‖₂ ≡ 1.0 不变式在 Phase 0 失守。

**Alternatives considered**：
- (a) 改实现让 driver 内部做 KMeans——违反 Driver Channel
  "gradient-free / 确定性" 约束（KMeans 引入随机性），且 scope 超出
  spec-only。
- (b) 删掉 Phase 0 的 spec 行——失去 SEEDING 相位的语义锚点，下游
  apply 无法 grep 锚点。

### Decision 4 — ③ grep 与 semantic 双层分离（NEW Requirement）

**Choice**：原 "Hard-Constraint Grep Invariants" Requirement 的 7 条
bullet 中，bullet 6（`.clamp_min(ε)` empty-cell denominator）与 bullet 7
（`arctan(pi / sqrt(d_c))` literal）**字面 grep 不可判定**：
- bullet 6 需要数据流分析（`.clamp_min` 的结果是否用作分母），grep
  只能判"有无 `.clamp_min`"，判不了"用作分母"。
- bullet 7 可以被"等价的非字面表达"绕过（如 `math.atan(1 / sqrt(d))`
  改写为 `numpy.arctan(...)`）。

把这两条 bullet **移出** grep Requirement，**移入** 新 ADDED Requirement
"Centroid Driver Semantic Invariants"，由对应的 3 个 invariant test
scenario 验证。

**Rationale**：让 grep 层只保留可机验的字面 token 限制；让 semantic
层显式承担需要 runtime observation 的不变式。读者不再误以为 "grep
通过 ⇒ 不变式成立"。

**Alternatives considered**：
- (a) 保留 7 条全部在 grep Requirement，加注释说明后两条不可机验——
  与"grep invariants" 标题语义冲突。
- (b) 把 semantic 验证散落到各 MODIFIED Requirement——后续 grep 找不到
  完整清单。

### Decision 5 — ④ 反事实算式选 option (a) (γ_init → −6.785, 29× → 25×)

**Choice**：保留 target `β₀ ≈ 1.035`（与基线 γ_init = −3.5 自洽），
γ_init 反事实值由 `−6.94` 改为 `−6.785`，梯度饥饿倍率由 `29×` 改为
`25×`。

**Rationale**：反事实下的参数化是 `β = 1.0 + 31·σ(γ)`（floor 提到 1.0）：
- `γ = −6.785`：`1.0 + 31·σ(−6.785) = 1.0 + 31·0.001128 = 1.03497`
  ≈ 1.035 ✓（保留基线 target）
- `γ = −6.94`：`1.0 + 31·σ(−6.94) = 1.0 + 31·0.000966 = 1.030`（target
  偏离基线）

σ'(γ) 比值：`σ'(−3.5) / σ'(−6.785) = 0.0284 / 0.001128 = 25.2`，即
25×（spec 写 29× 是与 −6.94 自洽的，但 γ 错了）。定性论点（梯度饥饿
一个数量级）不变。

**Alternatives considered**：
- (b) 保留 −6.94 与 29×，把 β₀ 改为 ≈ 1.030（user 已不选）—— target
  偏离基线，与 wayfinder L459 "γ_init ≈ −3.5 gives β_0 ≈ 1.035"
  不一致。

### Decision 6 — ⑤ 恒真式直接删除（不替换为独立 range scenario）

**Choice**：从 Scenario "Parameterization floor preserves cold-start
gradient" 的 THEN 合取项中删除 `; the [0.1, 32] parameterization interval
is preserved`。

**Rationale**：
- 该合取项对任意 γ 恒成立（β = 0.1 + 31.9·σ(γ)，σ ∈ (0,1) ⇒ β ∈ (0.1, 32)），
  零判别力。
- `β^param` 值域开区间属性已由 skeleton spec "Endpoint agreement" Scenario
  覆盖（`γ → −∞ ⇒ β ≈ 0.1`，`γ → +∞ ⇒ β ≈ 32`）。
- 单独写一个"β^param 值域为 (0.1, 32)"的 range scenario 引入冗余
  （与 Endpoint agreement 重复），且让 spec 多 1 条无新增判别力的
  scenario。

**Alternatives considered**：
- (a) 移出为独立 range scenario——见上，引入冗余。
- (b) 改为"σ ∈ (0, 1) ⇒ β ∈ (0.1, 32)"的恒等陈述——仍是恒真。

### Decision 7 — ⑥⑦⑧ 下游 apply hand-off 合同

**Choice**：Issues ⑥⑦⑧ 在 proposal.md "Downstream Hand-off" 段已列出
具体代码 / 测试改动，本 change 不实施；archive 后用户触发
`fix-spec-doc-oversights-apply` change，按 hand-off 合同同步实现。

**Rationale**：
- ⑥：`extraction.py:126` 当前 `return alpha * centroids + (1.0 - alpha)
  * mean` 缺 `F.normalize(..., dim=-1)`，违反 spec Phase 1/2/3 EMA 输出
  `Normalize(...) / ‖·‖₂`。
- ⑦：`extraction.py:124` 的 `denom = weights.sum(dim=0).clamp_min(1e-9)`
  违反 spec "no clamp_min(ε) denominator"，应在 `n_i = 0` 时显式回退
  到 `c_i`。
- ⑧：skeleton spec L337-351 列出的 3 个 invariant test scenarios
  (`test_empty_cell_preserves_centroid` /
  `test_spherical_norm_is_strictly_one` /
  `test_near_zero_candidate_fallback`) 在 `tests/` 目录完全不存在
  （grep 0 命中）。

**Alternatives considered**：仅 (a) 与 (b)，无实质差异——见 Decision 1。

### Decision 8 — ⑨ 子公式措辞修正

**Choice**：spec 文本原 `each 2 · H_kv · 2 · d_k · d_c` 改为
`each projection is a forward GEMM of 2 · H_kv · d_k · d_c; two projections
sum to 4 · d_c · H_kv · d_k`，显式区分"单投影 forward GEMM"与"两个
投影之和"。

**Rationale**：
- 单个低秩投影（`W^K` 或 `W^V`）的 forward GEMM 是
  `2 · H_kv · d_k · d_c`（factor 2 来自 GEMM 的乘加）。
- 两个投影之和 = `4 · d_c · H_kv · d_k`，与外部公式
  `FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c` 第一项
  一致。
- 总数 `66_048 FLOPs/layer` 不变。

**Alternatives considered**：
- (a) 保留原文不加解释——读者需自行换算，易误解。
- (b) 直接改为 `H_kv · d_k · d_c`（去掉 factor 2）—— 与"两个投影之和
  = 4·d_c·H_kv·d_k" 不一致。

## Risks / Trade-offs

**[Risk 1]** 0.20% vs 0.26% 数字漂移历史：`fix-openspec-doc-bugs` archive
时未发现 0.26% 的分母歧义，本 change 修正后下游 apply change 会让
recompute 走 `0.20%` 路径。任何 `tests/test_flops.py` 或
`src/decompmoe/flops.py` 中的 "0.26%" 字面值需同步更新。**Mitigation**：
本 change 不动代码；下游 apply change 显式 grep `0.26%` 作为锚点。

**[Risk 2]** Phase 0 spec 改为 "no-op + 上游已归一化" 后，`extraction.py:107-108`
的 docstring 已说 "actual k-means is owned by training-time caller"，但
**没**说"上游已 L2 归一化"。**Mitigation**：下游 apply change 在 docstring
补一句 "upstream spherical KMeans MUST produce L2-normalized seeds"，
与 spec 对齐。

**[Risk 3]** grep / semantic 双层分离后，未来若有"用 `torch.clamp`
代替 `clamp_min`"或"用 `math.atan` 代替 `arctan`"的实现绕过，spec 不再
有 grep 防线。**Mitigation**：semantic 层由 3 个 test scenario 验证；且
canonical Voronoi API（`canonical_voronoi_angle`）的存在已把
`arctan(...)` 的所有改写路径锁在命名空间里。

**[Risk 4]** γ_init 由 −6.94 改为 −6.785 后，任何引用 −6.94 字面值的
实现 / 测试需要同步更新。**Mitigation**：grep `−6.94` 在 spec / code
中应该 0 命中（除历史 commit message）。

**[Risk 5]** "[0.1, 32] preserved" 合取项删除后，Scenario 的 THEN 变为
单合取，reduction in conjunction-chain 长度。**Mitigation**：保持 THEN
有 ≥1 项；spec 不要求 THEN 多合取。

**[Risk 6]** Issue ⑥⑦⑧ 的 apply change 涉及 `extraction.py` 的核心
driver 实现，必须保证 backward-compatible（即现有 14 个 extraction
相关测试不能因 EMA 归一化或 clamp_min 替换而 break）。**Mitigation**：
apply change 按 hand-off 合同明确替换逻辑（`F.normalize`、`torch.where`
回退）；现有测试若固化了违规行为（如 `test_extraction_phase.py` 期望
未归一化输出），按 spec 修订测试期望值。

**[Risk 7]** ADDED Requirement "Centroid Driver Semantic Invariants" 引入了
新的 Source 反链需求。**Mitigation**：本 change 不写 Source 反链（该
Requirement 是 spec 内部路由，不依赖外部 ticket / change artifact）。

## Migration Plan

本 change 是 spec-only，无运行时迁移：

1. **apply 阶段（spec archive）**：`openspec archive-change fix-spec-doc-oversights`
   把 delta spec 合并到 `openspec/specs/wayfinder/spec.md` 与
   `openspec/specs/decompmoe-skeleton/spec.md`。
2. **下游 change 触发**：archive 完成后立即创建
   `fix-spec-doc-oversights-apply`（code-level change），按 proposal.md
   "Downstream Hand-off" 段列出 ⑥⑦⑧ 改动同步
   `src/decompmoe/extraction.py` 与 `tests/test_extraction.py` +
   `tests/test_extraction_phase.py`。
3. **rollback**：如果下游 apply 失败，回滚手段是 `openspec archive-change`
   反向操作（从 git 历史 revert 本 change 的 spec delta）。

## Open Questions

无。所有 grilling 决策已落地到 spec 文本（与 Decision 1-8 对应）。下游
apply change 可能在执行 Decision 7 hand-off 时遇到的小问题（如
`tests/test_extraction_phase.py` 期望值冲突）由 apply 阶段自行处理，
不影响本 change 的 spec 合同。
