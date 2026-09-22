# Proposal: fix-ticket-a5-2-cascading-correction

## Why

2026-09-18 audit-verification cycle-17 verify-20 axis-β 实证 **ticket drift cascading** —— audit-verification loop 自 2026-08-21 开始以来第 1 次发现 drift 通过 ticket 内部 cross-reference 链跨 ticket 传播：

- **传播链源端**：cycle-17 audit-verification record 回溯定位 cycle-16 ticket `wayfinder/tickets/A3-2.md` 文字层声明 "c_i 走 **4 阶段**生命周期"（"4 阶段" 出现 5 次 / 3 unique lines：L25 锁定行 + L33 标题 + L83 行含 3 次重复），与 `openspec/specs/wayfinder/spec.md` Requirement "Five-Phase Time-Driven Schedule" (req-14, anchor `<a id="req-14">` at L289) 闭式 "five phases" (L293) 不一致（**注意**：行号 L289 / L293 是当前 spec 实测位置，planning 阶段曾以 L265 / L269 锚定 spec，因 spec 在 2026-09-13 ~ 09-18 期间被插入 ~24 行内容而偏移）
- **传播链传染端**：cycle-17 finding 2 (LOW, 2026-09-18) 实证 ticket `wayfinder/tickets/A5-2.md` L56 引用 `"A3-2 4 阶段生命周期"`、`L63` 引用 `"A6b-1 (4 阶段)"`（**注意**：实际 L56/L63，planning 阶段曾以 L57/L63 记录，与 cycle-17 audit-verification.md L1459 / L1481 / L1492 同源 off-by-one；A5-2 L57 实际是空行）—— cross-reference 把 cycle-16 drift 传染到 A5-2，形成 `ticket A3-2 → ticket A5-2` 漂移传播链
- **修复策略**：单点 ticket 文字修订（不改 spec code，不改 src/，不改 tests/）。理由：(a) spec req-14 是真相源（CLAUDE.md §2 真相源层级 #1），已 lock "five phases" 与 5 阶段（Phase 0 / 1 / 2 / 3 / 4），闭式 1% / 5% / 20% / 30% / 44% (L293) + boundary 1K / 6K / 26K / 56K / 100K (L293)；(b) CLAUDE.md §8 2026-08-21 裁决 OpenSpec 为唯一真相源、ticket 仅作历史决策记录；(c) CLAUDE.md §6 第 7 条 "不要重写 wayfinder ticket 来'调和' spec 与 ticket 不一致——应改 spec 来对齐 ticket" 文字表述与 §8 真相源层级冲突，本 change 适用 §8 优先解释（spec 是真相源 → ticket drift 同步到 spec）；(d) 修复纯文字层，0 spec delta，0 src/ 改动，0 tests/ 改动，0 数值变更
- **不引入 spec delta**：spec req-14 已 lock；本 change 不动 `openspec/specs/wayfinder/spec.md` 任何 Requirement。本 change 通过 `.openspec.yaml` `skip_specs: true` 标记纯文字层 sync
- **不引入代码 delta**：0 文件 `src/decompmoe/` 改动，0 文件 `tests/` 改动，0 文件 `MVPConfig` / `contracts.py` 改动
- **cycle-16 finding 2 证据链说明**：仓库无独立 `cycle-16-finding-2/` 制品目录、`openspec/changes/archive/` 也无 cycle-16 归档。cycle-16 finding 2 仅以间接文字提及存在于 cycle-17 audit-verification.md (L1483 / L1491) 的 cross-cycle 回溯归因，评级 MEDIUM 来自 cycle-17 verify-20 的归因而非独立 cycle-16 制品。本 change 接受此间接证据链作为传播链源端锚点

## What Changes

### wayfinder tickets 文字修订（2 文件，0 spec delta）

1. **`wayfinder/tickets/A3-2.md`**（3 unique lines / 5 occurrences）
   - **L25 锁定行**: `**锁定：C 提取全可微（D 路径）+ c_i 走 4 阶段生命周期**` → `**锁定：C 提取全可微（D 路径）+ c_i 走 5 阶段生命周期**`
   - **L33 标题**: `### c_i 更新策略：4 阶段生命周期（球面几何约束贯穿）` → `### c_i 更新策略：5 阶段生命周期（球面几何约束贯穿）`
   - **L83 后续 ticket 影响行**: `- A6b-1 (4 阶段)：c_i 生命周期的 4 阶段与训练 4 阶段对齐` → `- A6b-1 (5 阶段)：c_i 生命周期的 5 阶段与训练 5 阶段对齐`（本行 "4 阶段" 出现 3 次，Edit 工具以 verbatim unique match 一次性替换）
   - **L66-70 表格内部不动**: 表格列 Phase 0 / Phase 1-3 / Phase 4 共 3 行，描述 3 种 c_i 更新策略（Spherical K-Means / Masked Spherical EMA / Projected SGD），与 spec req-14 L293 的 5 阶段闭式不冲突（Phase 1-3 共享 Masked Spherical EMA 更新策略，α schedule 区分）
2. **`wayfinder/tickets/A5-2.md`**（2 unique lines / 2 occurrences）
   - **L56 Caveat 训练充分分化行**: `- 训练充分分化：A3-2 4 阶段生命周期 + A6b 退火调度` → `- 训练充分分化：A3-2 5 阶段生命周期 + A6b 退火调度`（**注意**：实际 L56，planning 阶段曾以 L57 记录，与 cycle-17 audit-verification.md 同源 off-by-one）
   - **L63 后续 ticket 影响行**: `- A6b-1 (4 阶段)：无需为 shared expert 单独设计阶段，所有专家同步生命周期` → `- A6b-1 (5 阶段)：无需为 shared expert 单独设计阶段，所有专家同步生命周期`

### 修复传播链一致性

| 文件 | 行 | 修改前 | 修改后 | 引用源 |
|---|---|---|---|---|
| `wayfinder/tickets/A3-2.md` | L25 | "c_i 走 4 阶段生命周期" | "c_i 走 5 阶段生命周期" | spec req-14 L293 "five phases" |
| `wayfinder/tickets/A3-2.md` | L33 | "4 阶段生命周期" | "5 阶段生命周期" | spec req-14 L293 "five phases" |
| `wayfinder/tickets/A3-2.md` | L83 | "A6b-1 (4 阶段)" + "c_i 生命周期的 4 阶段" + "训练 4 阶段对齐" (3 occurrences) | "A6b-1 (5 阶段)" + "c_i 生命周期的 5 阶段" + "训练 5 阶段对齐" | spec req-14 L293 "five phases" |
| `wayfinder/tickets/A5-2.md` | L56 | "A3-2 4 阶段生命周期" | "A3-2 5 阶段生命周期" | spec req-14 L293 "five phases" |
| `wayfinder/tickets/A5-2.md` | L63 | "A6b-1 (4 阶段)" | "A6b-1 (5 阶段)" | spec req-14 L293 "five phases" |

### nothing else

不动 `openspec/specs/wayfinder/spec.md` req-14 任何 Requirement 文字（已 lock "five phases"）；不动 `openspec/specs/decompmoe-skeleton/spec.md`；不动 `governance/spec.md`；不动 `src/decompmoe/`；不动 `tests/`；不动 `MVPConfig` / `contracts.py` / `design.md`；不动 `LOOPS.md` 主体结构（仅在 cycle-17 finding 2 归档条目中交叉引用本 change ID，不单独修改 severity 表）。本 change 通过 `.openspec.yaml` `skip_specs: true` 显式标记 0 spec delta。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无。spec delta 无新增 —— 见下 "Added / Modified Requirements to Existing Capabilities" 说明）

### Added / Modified Requirements to Existing Capabilities

（无 spec delta。本 change 是 doc-level ticket 同步，不修改任何 OpenSpec Requirement。理由：spec req-14 已 lock "five phases" 5 阶段（Phase 0 / 1 / 2 / 3 / 4），ticket 文字漂移属于 ticket 内部一致性维护，不构成 spec 修订需求。CLAUDE.md §8 裁决"wayfinder 不再是必改制品"，ticket 仅作历史决策记录，本 change 把 ticket 文字拉回到 spec 已 lock 的术语。`.openspec.yaml` 设 `skip_specs: true` 显式标记 0 spec delta。）

## Impact

- **Affected code**: 无（`src/decompmoe/` 0 文件改动）
- **Affected tests**: 无（`tests/` 0 文件改动；本 change 不涉及数学闭式，不触发 `pytest.approx` 闭式测试守护）
- **Affected specs**: 无（`openspec/specs/wayfinder/spec.md` 0 行改动；req-14 已 lock "five phases" 5 阶段；本 change 通过 `skip_specs: true` 标记 0 spec delta）
- **Affected tickets**: 2 文件，5 unique lines / 7 occurrences 文字修订（`wayfinder/tickets/A3-2.md` 3 lines / 5 occurrences + `wayfinder/tickets/A5-2.md` 2 lines / 2 occurrences）
- **Affected OpenSpec source 反链**: 无变化（`Source:` 反链仍指向 `wayfinder/tickets/A5-2.md` / `wayfinder/tickets/A3-2.md`；ticket 文件路径未变，content 仅文字修订）
- **Affected APIs / dependencies**: 无
- **Affected systems**: 无（推理引擎实现代码已 out-of-scope per CLAUDE.md §7）
- **Risk**:
  - **doc-level only risk**: 文字修订可能影响其他 ticket 引用 "4 阶段" 文字的位置。Mitigation：`grep -rn "4 阶段" wayfinder/tickets/` 全文搜索 **scope-limited 验证**（post-apply 2026-09-22）：本 change scope (A3-2.md + A5-2.md) 内 0 命中（5 lines / 7 occurrences 全修订）；**scope 外实测** 9 unique tickets 共 10 处 "4 阶段"/"四阶段" 残留 —— A4-1.md:92, A4-2.md:82, A5-3.md:97, A5-3.md:124, A6a-1.md:113, A6a-2.md:101, A6b-1.md:14 + L1 标题 "四阶段演进逻辑", A8-3.md:72, WF-1.md:43。这些位置**不在本 change scope**（per Decision 6），单独评估是否需要 fix（cycle-18+ audit-verification 独立 finding 提案）
  - **A3-2 表格 vs 文字层 "5 阶段" 表述差异引发读者困惑**: Mitigation：表格 L66-70 描述 3 种 c_i 更新策略，spec req-14 L293 闭式已 lock 5 阶段（Phase 1-3 共享 Masked Spherical EMA，α schedule 区分）；表格下方 L72 "关键设计" 段已写 "Phase 1-3 不接路由梯度" 明确 Phase 1-3 是策略共享
  - **CLAUDE.md §6 第 7 条 vs §8 真相源层级冲突**: 本 change 适用 §8 优先解释（spec 是真相源，ticket drift 同步到 spec），§6 第 7 条原文 "应改 spec 来对齐 ticket" 是 §8 之前的旧表述，2026-08-21 §8 裁决后已不再适用。Mitigation：design.md Decision 1 已显式论证
  - **cycle-16 finding 2 间接证据链**: Mitigation：本 change 接受 cycle-17 audit-verification.md 的 cross-cycle 回溯归因为传播链源端锚点；如未来 cycle-18+ audit 发现独立 cycle-16 制品将升级证据链
  - **Windows Edit tool CRLF contamination**: 5 lines 文字修订均跨多行文本，Edit 工具可能把整文件转 CRLF。Mitigation：每个 ticket Edit 后跑 `git diff --stat` 验证 LF 保留，必要时 `sed -i 's/\r$//'` 恢复（按 [[windows-edit-crlf-pitfall]]）
  - **audit chain 一致性**: cycle-17 finding 2 已记录 A5-2 drift 传染；cycle-16 finding 2 间接来自 cycle-17 回溯归因。本 change 关闭这两条 finding，LOOPS.md cycle-16/17 归档条目交叉引用本 change ID，但本 change 不直接改 LOOPS.md（避免 scope 膨胀）
- **Source**:
  - A3-2 L25/L33/L83 "4 阶段" drift: spec req-14 L293 "five phases" 闭式 (anchor L289); ticket A3-2 L66-70 表格自身只列 3 种更新策略
  - A5-2 L56/L63 "4 阶段" / "A6b-1 (4 阶段)" cross-ref: cycle-17 finding 2 (2026-09-18); ticket A5-2 L56 verbatim 引用 "A3-2 4 阶段生命周期"; spec req-14 L293 "five phases"
  - 传播链: A3-2 (cycle-16 drift via cycle-17 回溯归因) → A5-2 (cycle-17 finding 2 传染); evidence 见 audit-verification.md L1459/L1481-1498 表