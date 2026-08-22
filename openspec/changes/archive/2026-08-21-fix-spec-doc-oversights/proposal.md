## Why

Post-archive independent numerical review of
`openspec/specs/wayfinder/spec.md` 与
`openspec/specs/decompmoe-skeleton/spec.md`（按 CLAUDE.md §3 独立复核口径）
发现 **9 项 spec-level 缺陷**：其中 5 项（①②③④⑤）来自用户分析中的硬
错 / 恒真 / 不可机验，4 项（⑥⑦⑧⑨）来自同一轮复核的扩展发现。其中
①②③④⑤⑨ 是 spec 文本自身缺陷（含算式错、用词不当、措辞重复计数），
⑥⑦⑧ 是 reference skeleton `src/decompmoe/extraction.py` 与
`tests/test_extraction*.py` 违反 spec 已声明不变式的实现 / 测试缺口。

**本 change 仅修 spec（user-locked 决议，与 `fix-openspec-doc-bugs` 严格
spec-only 边界一致）。** ⑥⑦⑧ 三项实现 / 测试缺口显式 hand-off 到下游
code-level change `fix-spec-doc-oversights-apply`，不在本 change 范围
内执行。

## What Changes

主 spec `wayfinder` 三处修订 + skeleton spec `decompmoe-skeleton` 三处
修订 + 1 处 ADDED Requirement。具体修订：

- **Issue ①**（wayfinder L359 / skeleton L46 — 算式硬错）：
  "`≈ 0.26%` of `FLOPs_MoE,core`" → "`≈ 0.20%` of `FLOPs_MoE,core`"。
  数值依据：66_048 / (8·d_model² + k·6·d_model·d_ffn^Expert) = 66_048 / 33_554_432
  ≈ 0.001968 → 0.20%（仍在 0.3% allowance 内）。原 0.26% 的分母实为 FFN-only
  分母（25_165_824），与同段 `FLOPs_MoE,core` 定义不一致。修法选择**改数字**
  而非**改口径**，避免与同段 core 定义打架。

- **Issue ②**（skeleton L128 — 用词与实现不符）：Phase 0 (SEEDING) 行由
  `c_i ← KMeans(C) initialization` 改为 `c_i ← c_i.detach()`（driver
  no-op，与 `extraction.py:112-113` 实现一致）；新增一句明确上游约束：
  "Driver is no-op; upstream spherical KMeans is assumed to have produced
  L2-normalized seeds." Scenario "Phase-0 non-differentiable" 与实现
  一致，**不改**。

- **Issue ③**（skeleton L322-335 — grep 与语义层混淆）：把 Requirement
  "Hard-Constraint Grep Invariants" 拆为两层：
  - **grep-verifiable 层**（保留原 Requirement，bullet 1-5：STE、w_i、
    shared、triton/cpp_extension、kv_cache_c）。
  - **semantic-invariant 层**（新增 ADDED Requirement "Centroid Driver
    Semantic Invariants"）：bullet 6（`.clamp_min(ε)` denominator）与
    bullet 7（`arctan(pi / sqrt(d_c))` literal）移入此层，明示语义
    不变式由 skeleton spec 已声明的 3 个 invariant test scenarios
    (`test_empty_cell_preserves_centroid` /
    `test_spherical_norm_is_strictly_one` /
    `test_near_zero_candidate_fallback`) 验证。

- **Issue ④**（wayfinder L459 — 反事实算式不自洽）：`γ_init ≈ −6.94`
  改为 `γ_init ≈ −6.785`，`29×` 改为 `25×`（user 选择 option (a)）。
  数值依据：反事实参数化 `β = 1.0 + 31·σ(γ)` 下，`σ(−6.785) ≈ 1.128e-3`，
  `1.0 + 31·1.128e-3 = 1.03497 ≈ 1.035`（保留基线 β₀ ≈ 1.035 目标自洽）；
  `σ'(−6.785) ≈ 1.128e-3`，`σ'(−3.5)/σ'(−6.785) = 0.0284/1.128e-3 ≈ 25.2`。
  定性论点（梯度饥饿一个数量级）不变。

- **Issue ⑤**（wayfinder L467-469 — 恒真式断言）：从 Scenario
  "Parameterization floor preserves cold-start gradient" 的 THEN 合取项
  中删除 `; the [0.1, 32] parameterization interval is preserved`。
  该合取项对任意 γ 恒成立（β = 0.1 + 31.9·σ(γ)，σ ∈ (0,1) ⇒ β ∈ (0.1, 32)），
  零判别力。`β^param` 值域开区间属性已由 skeleton spec "Endpoint agreement"
  Scenario 覆盖。

- **Issue ⑨**（wayfinder L359 — 子公式措辞重复计数）：重写 FLOPs_Routing
  子项措辞。原文 `where 4 · d_c · H_kv · d_k accounts for W^K, W^V
  low-rank projections (each 2 · H_kv · 2 · d_k · d_c)` 中子项字面写
  `2·8·2·128·16 = 65_536` 已是两者之和，单个应为 `H_kv·d_k·d_c = 32_768`
  （含 forward-GEMM factor 2）。改为明确表达：每个低秩投影 forward GEMM
  是 `2 · H_kv · d_k · d_c`，两个投影之和 = `4 · d_c · H_kv · d_k`，与
  外部公式一致。总数 66_048 不变。

- **ADDED Requirement**（skeleton spec）：新增 "Centroid Driver Semantic
  Invariants" Requirement，三条 Scenario（`test_empty_cell_preserves_centroid` /
  `test_spherical_norm_is_strictly_one` / `test_near_zero_candidate_fallback`）
  在该 Requirement 下重新 anchor，**Scenario 标题与正文不变**，仅显式
  路由 invariant 测试责任。

**BREAKING**: 无。本 change 仅修改 spec 文本（含 ADDED 1 个 Requirement），
不动 `src/decompmoe/*.py` 与 `tests/test_*.py`。

## Capabilities

### New Capabilities

无（不引入新 spec 边界；Issue ③ 新增的 "Centroid Driver Semantic
Invariants" Requirement 落在现有 capability `decompmoe-skeleton` 内）。

### Modified Capabilities

- `wayfinder`：3 处 MODIFIED Requirement（"Six Baseline Set On 4070 MVP"
  L359 — 算式修正 + ⑨ 子公式措辞修正；"Beta Parameterization Space vs
  Operational Domain" L459 + L467-469 — γ_init 自洽 + 删恒真合取项）。
- `decompmoe-skeleton`：3 处 MODIFIED Requirement（"Active FLOPs Parity
  Against Dense Baseline" L46 — 算式修正；"Centroid Four-Phase Lifecycle
  Driver" L128 — Phase 0 用词；"Hard-Constraint Grep Invariants" L322-335 —
  grep/semantic 拆分）+ 1 处 ADDED Requirement（"Centroid Driver Semantic
  Invariants"）。

## Impact

- **Spec 层**：`openspec/specs/wayfinder/spec.md` 与
  `openspec/specs/decompmoe-skeleton/spec.md` 各 3 处修订 + skeleton
  新增 1 个 Requirement。本 change 是后续 `fix-spec-doc-oversights-apply`
  code-level change 的「合同」。
- **代码层**：本 change **不动** `src/decompmoe/*.py` 与 `tests/test_*.py`。
- **Ticket 层**：本 change **不动** `wayfinder/tickets/*.md`（按 CLAUDE.md
  §8 2026-08-21 裁决，wayfinder 不再是必改制品）。
- **附件版 Wayfinder map.md**：本 change **不主动同步**附件版（与
  `fix-openspec-doc-bugs` 一致，按 §2 Truth Source Hierarchy 以仓库内
  OpenSpec + tickets 为准）。

## Downstream Hand-off（⑥⑦⑧ — 不在本 change 范围）

下列 3 项 spec-level oversights 是实现 / 测试缺陷，**本 change spec-only
不修**，按 `fix-openspec-doc-bugs` → `fix-openspec-doc-bugs-apply` 先例
模式，由 archive 后用户显式触发的下游 code-level change
`fix-spec-doc-oversights-apply` 处理：

- **Issue ⑥**：skeleton spec L129-131 要求 Phase 1/2/3 EMA 输出
  `Normalize(α·c_i + (1−α)·m_i) / ‖·‖₂`，但 `src/decompmoe/extraction.py:126`
  当前实现 `return alpha * centroids + (1.0 - alpha) * mean`，**无归一化**。
  Apply 修复：把 EMA 分支返回值改为
  `F.normalize(alpha * centroids + (1.0 - alpha) * mean, dim=-1)`，并
  同步更新 `tests/test_extraction_phase.py::test_phase_090_ema` 等
  EMA expected 值到归一化形式。

- **Issue ⑦**：`src/decompmoe/extraction.py:124-125` 当前实现
  `denom = weights.sum(dim=0).clamp_min(1e-9); mean = (weights.T @ X) / denom.unsqueeze(-1)`，
  在 `n_i = 0` 时 `denom = 1e-9` 而非回退到 `c_i`，违反 spec 明确的
  "Empty-Cell Invariant" 与 "no clamp_min(ε) denominator"。Apply 修复：
  ```python
  n_i = weights.sum(dim=0)             # no clamp_min
  weighted = (weights.T @ X)            # zero when n_i = 0
  safe_n = n_i.clamp_min(1.0)          # only used to divide
  mean_n = weighted / safe_n.unsqueeze(-1)
  mean = torch.where(n_i.unsqueeze(-1) > 0, mean_n, centroids)
  ```
  并删除 skeleton spec L322 "no `.clamp_min(1e-9)` ... denominator" 的
  grep invariant 与 code 同步生效。

- **Issue ⑧**：skeleton spec L337-351 列出的 3 个 invariant test scenarios
  (`test_empty_cell_preserves_centroid` /
  `test_spherical_norm_is_strictly_one` /
  `test_near_zero_candidate_fallback`) 在 `tests/` 目录**完全不存在**
  （grep 0 命中）。Apply 修复：在 `tests/test_extraction.py` 中新增这
  3 个 test，断言与 spec Scenario 严格对齐（`‖c_i^(t+1) − c_i^(t)‖₂ <
  10⁻¹²`、`max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`、近零 candidate 回退 + 无 NaN）。

## Out of Scope（明确不动）

- 不执行训练、不跑 baseline、不读实验数据（CLAUDE.md §6）。
- 不重写 wayfinder ticket（CLAUDE.md §8 2026-08-21 裁决）。
- 不动 `src/decompmoe/*.py` 与 `tests/test_*.py`（本 change spec-only；
  Issue ⑥⑦⑧ 移交给下游 `fix-spec-doc-oversights-apply`，见上文
  "Downstream Hand-off" 段）。
- 不同步 Wayfinder 附件版 map.md。
