# WF-1: Audit OpenSpec Docs Completeness

- **Arena**: W (Wayfinder self-audit; not part of A0–A8)
- **Type**: grilling (audit-as-decision)
- **Status**: closed
- **Blocks**: —
- **Blocked by**: —
- **File**: tickets/WF-1.md
- **Resolved**: 2026-08-18

## Question

由 `/opsx:propose` 引入的 OpenSpec 制品（`openspec/changes/introduce-wayfinder-decompoe-spec/{proposal,specs/wayfinder/spec,design,tasks}.md`）相对于 `wayfinder/map.md` 自报 CHART COMPLETE 的 21 ticket 决策，是否完备？

具体验收维度（与 `tasks.md` 的 checklist 互为对照，但本 ticket 是 audit 视角）：

1. **决策覆盖**：21 ticket 是否 1:1 映射到至少一个 Requirement？每个 ticket 的关键数字（β ∈ [0.1, 32]、FLOPs ≈ 65.5K/token、W_proj ≈ 64 KB、Phase 时长 1/5/20/30/44%、Resurrection 阈值 1/128 over 200 steps 等）是否都被保留？
2. **形式合规**：`openspec validate --strict` 是否通过？每个 Requirement 是否有 `#### Scenario`（4 个 #，非 3 个）？`## Purpose` 段 ≥ 50 字符？
3. **制品间一致性**：proposal 声明的 capability `wayfinder` 与 spec 主 spec 对齐；design.md 提到的"单 capability / ADDED-only / formalize-only design / tasks 不含代码"与 tasks.md 的 5 组 checkbox 类别对应；tasks.md 的具体数字与 spec.md 的 Requirement 文本一致。
4. **可追溯性**：每个 Requirement 是否带 `**Source:**` 反链 ticket id？design.md 的 Risks 是否引用 spec.md 的 Requirement？

## Resolution

**审计结论：PASS-WITH-WARNINGS** —— 制品在 4 个验收维度上主体完备，但有 3 项 minor warnings 不影响 archive。

### 1. 决策覆盖（PASS）

| Ticket | 映射到的 Requirement | Source 反链 |
|---|---|---|
| `A0-1` 命名 | Naming And Alias Convention | ✓ |
| `A1-1` 符号 | Formal Symbols And Code Naming | ✓ |
| `A2-1` 拓扑挂载 | Post-FFN Geometric Mount Point | ✓ |
| `A2-2` 路由特征 + head 聚合 | Layer-Wise Head-Aggregated Routing + Formal Symbols | ✓ |
| `A3-1` C 提取算子 | Spherical Normalized C Extraction | ✓ |
| `A3-2` C 可微性 + c_i 生命周期 | C Extraction Differentiability And Centroid Lifecycle | ✓ |
| `A4-1` 距离度量 | Isotropic Squared-Chord Distance And Bounded Beta | ✓ |
| `A4-2` 门控函数 | Top-K Sparse Mask With Local Softmax Gating | ✓ |
| `A5-1` 专家内部结构 | Standard SwiGLU FFN Expert | ✓ |
| `A5-2` 共享专家 | No Shared Expert (Pure Geometric Routing) | ✓ |
| `A5-3 v2` 4070 MVP 超参 | 4070 MVP Hyperparameter Set | ✓ |
| `A6a-1` 损失构成 | Loss Composition | ✓ |
| `A6a-2` 数值异常恢复 | Numerical Safeguards | ✓ |
| `A6b-1` 4 阶段演进 | Five-Phase Time-Driven Schedule | ✓ |
| `A6b-2` 阶段切换触发器 | Hybrid Three-Layer Phase Triggers | ✓ |
| `A7-1` Prefill vs Decode | Prefill And Decode Share The Same Algorithm | ✓ |
| `A7-2` 增量更新律 | Stateless Per-Frame C Recomputation | ✓ |
| `A7-3` 硬件友好度 | Hardware And Kernel Friendliness | ✓ |
| `A8-1` Baseline | Six Baseline Set On 4070 MVP | ✓ |
| `A8-2` 几何量化指标 | Eight Geometric Quantification Metrics | ✓ |
| `A8-3` 可视化工具链 | Six-Module Visualization Toolchain | ✓ |

**21 / 21 ticket 全部映射，每个 Requirement 至少有一个 Source 反链。**

关键数字保留抽查：
- β ∈ [0.1, 32] ✓（Spec: Isotropic Squared-Chord Distance Requirement）
- C 提取 ≈ 65.5 K FLOPs/token at `H_kv=8, d_k=128, d_c=16` ✓（Stateless Per-Frame C Recomputation）
- W_proj ≈ 64 KB BF16 100% L2-resident ✓（Hardware And Kernel Friendliness）
- 激活 ≈ 4 KB 100% SRAM/RF-resident ✓
- 0 bytes HBM delta ✓
- Phase ratios 1/5/20/30/44% ✓（Five-Phase Time-Driven Schedule）
- Phase boundaries 1 K / 6 K / 26 K / 56 K / 100 K ✓
- Resurrection `< 1/128` for 200 steps, rate-limited 1000 steps ✓（Numerical Safeguards）
- β Saturation Guard 30.4 / 28.8 ✓
- Loss Spike 2.5 × EMA ✓
- Perturbation `N(0, 0.05² I)`, decay 0.85 ✓

### 2. 形式合规（PASS）

- `openspec validate introduce-wayfinder-decompoe-spec --strict` → `Change 'introduce-wayfinder-decompoe-spec' is valid`
- 21 Requirements × 34 Scenarios（实测，所有 Scenario 标题均为 `#### Scenario:` 4 个 #，grep 验证无 3-hash 退化）
- `## Purpose` 段完整文本（`specs/wayfinder/spec.md` 第 1–3 行）字面约 280 字符，远超 50 字符阈值
- 无 "TBD Update Purpose after archive" 占位符

### 3. 制品间一致性（PASS-WITH-WARNING）

- proposal 的 New Capability `wayfinder` ↔ spec 主 spec 路径 `specs/wayfinder/spec.md` ↔ design.md Decision 1（单 capability `wayfinder`）三方一致 ✓
- design.md Decision 4 声明"tasks.md 不含实现代码任务" ↔ tasks.md 5 组均为文档 / 校验 / 一致性 / 引用矩阵 / archive 验证 ✓
- tasks.md 第 2.1 项列出的所有具体数字与 spec.md 各 Requirement 文本字面一致 ✓

**Warning 1：proposal.md 中没有显式给出 Requirement / Scenario 数量**（仅声明 21 ticket 全覆盖）；audit 时直接 grep spec.md 得到 `21 / 34`，与 proposal 的语义对齐，但 proposal 本身可读性可增强——下次类似 propose 可在 proposal 里加一行 "X 个 Requirement × Y 个 Scenario"。
- **建议**：可忽略（archive 前不影响）；如要修，加一行到 `proposal.md` 的 Impact 段。

### 4. 可追溯性（PASS-WITH-WARNING）

- 每个 Requirement 都带 `**Source:**` 反链 ✓（grep 计数 21，与 Requirement 数 1:1）
- design.md 的 Risks 部分引用了 spec.md 的 Requirement 名称（如 `Naming And Alias Convention`、`Hardware And Kernel Friendliness`）✓

**Warning 2：design.md 引用 spec.md 的 Requirement 时使用了"spec 第一个 Requirement `Naming And Alias Convention` 锁住命名层级"这种自然语言引用**，而非硬链接 / anchor。OpenSpec 不强制 anchor 链接，但若未来 spec 章节顺序调整，design.md 引用可能漂移。
- **建议**：保持现状（自然语言引用在 spec-driven 项目中是常规做法），可在 archive 后给 spec.md 各 Requirement 加 `<a id="req-X"></a>` 锚点并把 design.md 改为相对链接——非阻塞。

**Warning 3：tasks.md 2.4 Scope-Lock 一致性检查项描述 Linear Attention / SSM / RNN / Pre-Attention Dynamic Bias / checkpoint 转换的来源**是"`## Purpose` 排除列表或 `Source:` 引用 'Future Work' 段"——但 `Source:` 字段引用的是整个 ticket 文件，不一定能定位到 "Future Work" 段。
- **建议**：tasks.md 2.4 是 checklist 中的审计动作，审计人 grep ticket body 中 "Future Work" 段即可，**无需修改**；保留为 reviewer 的判断项。

### 审计总结

| 维度 | 结论 |
|---|---|
| 1. 决策覆盖 | PASS |
| 2. 形式合规 | PASS |
| 3. 制品间一致性 | PASS-WITH-WARNING (minor) |
| 4. 可追溯性 | PASS-WITH-WARNING (minor) |
| **总计** | **PASS-WITH-WARNINGS（不影响 archive）** |

**Action：可进入 `/opsx:archive` 阶段**——所有 3 个 warning 都是增强建议（不阻塞），spec 是 archive-ready 的：
- `openspec/specs/wayfinder/spec.md` 落点已通过 strict 验证
- 21 Requirement 全部带 Source 反链（traceability 完整）
- 所有 map 决策都被 spec 承载（无 orphan ticket）

### 后续 ticket 触发（不在本 ticket 解决）

- Warning 1（proposal 显式声明 R/S 数量）可在下一次 propose 时改进流程；不作为独立 ticket。
- Warning 2（spec 锚点 + design 链接）可在 archive 后做一次"spec polish" change；视作者偏好决定是否成 ticket。
- Warning 3（tasks 2.4 描述精度）保留为 reviewer 经验，无需 ticket。
