# Design: fix-ticket-a5-2-cascading-correction

## Context

2026-09-18 audit-verification cycle-17 verify-20 axis-β 实证 **ticket drift cascading** —— audit-verification loop 自 2026-08-21 开始以来第 1 次发现 drift 通过 ticket 内部 cross-reference 链跨 ticket 传播。See proposal.md - Why for motivation and What Changes for scope.

**当前状态（事实基线）**：
- `openspec/specs/wayfinder/spec.md` req-14 (anchor `<a id="req-14">` at L289, content L293) 已 lock "five phases" + 5 阶段（Phase 0 / 1 / 2 / 3 / 4） + phase ratios `1% / 5% / 20% / 30% / 44%` + boundary timestamps `1 K / 6 K / 26 K / 56 K / 100 K` —— spec 是真相源
- `wayfinder/tickets/A3-2.md` 文字层 "4 阶段" 出现 5 次 / 3 unique lines (L25/L33/L83) vs spec "five phases"
- `wayfinder/tickets/A5-2.md` 文字层 "4 阶段" 出现 2 次 / 2 unique lines (L56/L63) vs spec "five phases"
- A3-2 L66-70 表格 3 行（Phase 0 / Phase 1-3 / Phase 4）描述 3 种 c_i 更新策略，与 spec 5 阶段双轨表述（Phase 1-3 共享更新策略但属 3 个独立 phase）
- `openspec/changes/archive/` 无 cycle-16 归档目录；`.audit/audit-verification/findings/` 无 cycle-16-finding-2 目录；cycle-16 finding 2 仅以间接文字提及存在于 cycle-17 audit-verification.md (L1459 / L1483 / L1491) 的 cross-cycle 回溯归因

**关键约束**：
- CLAUDE.md §2 真相源层级：spec #1，archive #2，source 反链 #3，wayfinder map/tickets #4，code #5
- CLAUDE.md §6 第 7 条："不要重写 wayfinder ticket 来'调和' spec 与 ticket 不一致——应改 spec 来对齐 ticket"（旧表述）
- CLAUDE.md §8 (2026-08-21 裁决)：OpenSpec 为唯一真相源；ticket 仅作历史决策记录；新变更一律走 OpenSpec 工作流
- §6 第 7 条 与 §8 真相源层级 **冲突**：§6 第 7 条假设 ticket 是真相源（2026-08-21 之前的旧模型），§8 翻转真相源到 spec。本 change 适用 §8 优先解释

## Goals / Non-Goals

**Goals:**
- 关闭 cycle-16 (回溯归因) + cycle-17 finding 2 ticket drift cascading，5 unique lines / 7 occurrences 文字修订（A3-2 3 lines / 5 occurrences + A5-2 2 lines / 2 occurrences）
- ticket 文字与 spec req-14 L293 "five phases" 闭式一致（grep "4 阶段" wayfinder/tickets/A3-2.md A5-2.md → 0 命中；grep "5 阶段" → ≥7 命中）
- 0 spec delta，0 src/ 改动，0 tests 改动（CLAUDE.md §3 surgical 原则 + `skip_specs: true` 标记）
- audit chain 完整性闭环：cycle-17 finding 2 标记 "closed by change 05"

**Non-Goals:**
- 不重写 ticket A3-2 整体结构（保留表格 L66-70 不变、保留 Phase 0/1-3/4 章节结构）
- 不改 spec req-14 或新增任何 OpenSpec Requirement
- 不动 `src/decompmoe/` / `tests/` / `MVPConfig` / `contracts.py` / `design.md`
- 不重写 LOOPS.md（仅在 cycle-16/17 归档条目交叉引用本 change ID，不修改 LOOPS.md severity 表）
- 不引入 "ticket lint" 新工具（CLAUDE.md §3 简单性原则）
- 不修复其他 ticket 中可能存在的 "4 阶段" 残留（**实测**：grep "4 阶段" / "four-stage" / "four stage" / "四阶段" 在 9 unique tickets 共 10 处命中 —— A4-1.md:92, A4-2.md:82, A5-3.md:97, A5-3.md:124, A6a-1.md:113, A6a-2.md:101, A6b-1.md:14 + L1 标题 "四阶段演进逻辑", A8-3.md:72, WF-1.md:43 —— A6b-1 是 spec req-14 `Source:` ticket 但本身存在内部 inconsistency "四阶段标题" vs "5 阶段编排 Resolution"）。这些 ticket 位置**不在本 change scope**（per Decision 6 surgical + CLAUDE.md §8 ticket 仅历史决策记录），cycle-18+ audit-verification 应独立 finding 提案闭环
- 不修改 CLAUDE.md（§6 第 7 条与 §8 真相源层级冲突的彻底解决归独立 change scope，如 `09-fix-claude-md-ticket-advisory-boundary`）

## Decisions

### Decision 1: ticket-only 修复（不改 spec / code / tests）

**Choice**: 仅修改 `wayfinder/tickets/A3-2.md` (3 unique lines / 5 occurrences) 与 `wayfinder/tickets/A5-2.md` (2 unique lines / 2 occurrences) 文字，0 spec delta，0 src/ 改动，0 tests 改动。

**Rationale**:
1. **spec 是真相源**（CLAUDE.md §2 真相源层级 #1，`openspec/specs/wayfinder/spec.md` req-14 L293 "five phases" 闭式已 lock，5 阶段 (Phase 0 / 1 / 2 / 3 / 4) + phase ratios 1% / 5% / 20% / 30% / 44% + boundary 1 K / 6 K / 26 K / 56 K / 100 K），ticket 漂移属于 ticket 内部一致性维护，不构成 spec 修订需求
2. **CLAUDE.md §8 裁决 (2026-08-21)**："OpenSpec 为唯一真相源；ticket 仅作历史决策记录（参考性、非约束性）"。本 change 把 ticket 文字拉回到 spec 已 lock 的术语，符合"以 OpenSpec 为唯一真相源"的精神
3. **CLAUDE.md §6 第 7 条 vs §8 冲突解决**：§6 第 7 条原文 "不要重写 wayfinder ticket 来'调和' spec 与 ticket 不一致——应改 spec 来对齐 ticket" 是 2026-08-21 之前的旧表述（旧模型：ticket 是真相源）。§8 翻转真相源到 spec 后，本 change 适用 §8 优先解释（spec 是真相源 → ticket drift 同步到 spec）。本 change 不是"调和"（用 ticket 改 spec），是"正向同步"（用 spec 校 ticket）
4. **数学不变性**：ticket 文字层 "4 阶段" vs "5 阶段" 不影响 `pytest.approx(..., abs=...)` 闭式测试（CLAUDE.md §6 第 8 条"sentinel closed-form constant must directly verify" 适用于算式，不适用于 ticket 文字 drift）—— 本 change 不触发任何测试改动
5. **audit chain 完整性原则**：cycle-17 finding 2 报告了 A5-2 传染端，cycle-16 finding 2 通过 cycle-17 回溯归因被定位为 A3-2 源端，本 change 关闭两端；不预先承诺关闭未来 cycle-18+ 可能发现的其他 ticket drift（每个 finding 单独 fix 是 CLAUDE.md §3 surgical 原则）

**Alternatives considered**:
- (a) 改 spec req-14 把 "five phases" 改为 "four phases" 与 ticket 对齐 —— 拒绝：spec 数值（1% / 5% / 20% / 30% / 44% phase ratios + 5 phase boundary timestamps 1K/6K/26K/56K/100K）显式是 5 阶段；改 spec 会破坏 `MVPConfig` phase boundary 实现与 `decompmoe/training_phases.py` 数值守门
- (b) 修改 spec + 改代码 + 改 ticket 三向对齐到 "4 阶段" —— 拒绝：与 MVP 阶段切分矛盾；scope 极大膨胀；违反 CLAUDE.md §6 第 8 条
- (c) 仅文档化 ticket drift 不修复 —— 拒绝：drift 传播链会继续传染到 N+1 个 ticket；audit chain 完整性要求"发现即关闭"
- (d) 引入 "ticket lint" 工具自动守门 ticket 文字与 spec 一致性 —— 拒绝：CLAUDE.md §3 简单性原则；ticket 文字同步是 audit-verification loop 自身职责（grep + Read + Edit），不需要新工具

### Decision 2: A3-2 表格 L66-70 保持不动

**Choice**: 仅修订 A3-2.md L25/L33/L83 3 lines / 5 occurrences 文字层 "4 阶段" → "5 阶段"；表格 L66-70（Phase 0 / Phase 1-3 / Phase 4 共 3 行）保持原样。

**Rationale**:
- 表格描述的是 **3 种 c_i 更新策略**（Spherical K-Means / Masked Spherical EMA / Projected SGD），不是 "4 阶段" 或 "5 阶段"
- spec req-14 L293 显式列 Phase 0 / 1 / 2 / 3 / 4 共 **5 个 phase**（α schedule 区分 Phase 1/2/3）：Phase 1 α=0.90 / Phase 2 α=0.95 / Phase 3 α=0.99 —— 这 3 个 phase 共享 Masked Spherical EMA 更新策略但 α 不同
- A3-2 表格用 "Phase 1-3" 合并行表达这一事实（与 spec req-14 的 5 阶段表述**双轨一致**），文字层 "5 阶段" 与表格 "Phase 1-3" 无矛盾
- 修改表格会破坏 ticket 自身的内部逻辑（表格行数 ≠ 阶段数 = 策略数，强行改表格为 5 行会引入冗余：Phase 1/2/3 共享公式但 α 不同，3 行 vs 1 行合并表达取舍不同）

**Alternatives considered**:
- (a) 改表格为 5 行（Phase 0 / Phase 1 / Phase 2 / Phase 3 / Phase 4）—— 拒绝：会引入冗余（Phase 1-3 共享公式仅 α 不同）；破坏 ticket 自身叙事（"4 阶段" vs "5 阶段" 是文字层 drift，表格是结构化表达，结构化层无错）
- (b) 删表格 —— 拒绝：表格提供 3 种 c_i 更新策略的对比（"鸡生蛋问题解法"），是 ticket 关键信息载体
- (c) 在表格上方加 "5 阶段按更新策略归并为 3 类" 注释 —— 超出 scope（CLAUDE.md §3 surgical 原则；本 change 仅文字层同步）

### Decision 3: A5-2 L63 同步修订（虽然 cycle-17 finding 2 仅点名 L56）

**Choice**: A5-2 L63 "A6b-1 (4 阶段)" 同步修订为 "A6b-1 (5 阶段)"，虽然 cycle-17 finding 2 仅点名 L56。

**Rationale**:
- A5-2 L63 引用 `A6b-1 (4 阶段)`，A3-2 L83 引用 `A6b-1 (4 阶段)`，spec req-14 L293 引用 `five phases` —— 2 处 ticket 引用 `A6b-1` 阶段数应全部统一为 "5 阶段"
- 仅修 L56 不修 L63 会留下 ticket 内部不一致（A5-2.md 内 L56 "5 阶段" vs L63 "4 阶段" 自相矛盾）
- 同步修 L63 是 audit chain 完整性原则（"发现即关闭"）的具体体现：单 change 内全 ticket 内一致

**Alternatives considered**:
- (a) 仅修 L56 不动 L63 —— 拒绝：A5-2.md 内部会出现 "5 阶段" + "4 阶段" 自相矛盾；audit chain 完整性要求同一文件内 cross-ref 一致
- (b) 把 L63 修订放到 follow-up change —— 拒绝：本 change 范围已限定 ticket 文字同步；拆分会增加审计 trace 复杂度

### Decision 4: 行号 anchor 偏差溯源与治理

**Choice**: 本 change 在所有制品中采用 **当前实测 spec 码位 L289 (anchor) / L293 (content) + 当前实测 ticket 码位 A3-2 L25/L33/L83 + A5-2 L56/L63**，不使用 planning 阶段早期 draft 的 L265 / L269 (spec) 或 L63 / L57 (ticket) 错误码位。

**Rationale**:
- spec.md 在 2026-09-13 ~ 09-18 期间被插入 ~24 行内容，导致 req-14 anchor 从 L265 → L289、req-14 content 从 L269 → L293 偏移
- A5-2 L57 在 cycle-17 audit-verification.md 中被记录为 "A3-2 4 阶段" 行，但实测 A5-2 L56 才是该行（L57 是空行），这是 cycle-17 audit-verification.md 的 off-by-one 错误，本 change 不继承
- A3-2 planning draft 声称 "L63 含 A6b-1 (4 阶段)"，实测 L83 才是该行（planning draft 把同一文件内的 "A6b-1 (4 阶段)" 行号 L83 与 spec 引用行号 L63 混淆）
- 本 change 所有引用码位以**当前实测**为准，避免 post-archive 复核时出现 audit trail 错位

**Alternatives considered**:
- (a) 在制品内保留 planning 阶段 draft 的错误码位以求与历史一致 —— 拒绝：post-archive 独立复核（CLAUDE.md §3）会复核 spec req-14 L293 实际位置而非声称位置，错位会导致复核失败
- (b) 在制品内同时列出 "plan 阶段码位" + "实测码位" 两套 —— 拒绝：增加制品复杂度；audit trail 应单一真相源

### Decision 5: cycle-16 finding 2 间接证据链显式承认

**Choice**: 本 change 在 proposal / design / tasks 制品中显式承认 cycle-16 finding 2 仅以间接文字提及存在于 cycle-17 audit-verification.md (L1459 / L1483 / L1491) 的 cross-cycle 回溯归因，仓库无独立 `cycle-16-finding-2/` 制品目录、`openspec/changes/archive/` 也无 cycle-16 归档。

**Rationale**:
- 接受间接证据链作为传播链源端锚点符合 audit-verification loop 的工作模式（loop 负责发现 + 追溯，不强求每个 cycle 都有独立制品目录）
- 显式承认证据链薄弱可避免 post-archive 复核时被误判为"凭空独立审计"
- 如未来 cycle-18+ audit 发现独立 cycle-16 制品，可升级证据链

**Alternatives considered**:
- (a) 不显式承认间接证据链 —— 拒绝：违反 CLAUDE.md §3 surgical 原则 + audit chain 完整性原则；post-archive 复核会追究 cycle-16 独立制品缺失
- (b) 拒绝接受间接证据链，要求 cycle-16 独立制品 —— 拒绝：超出本 change scope（重建 cycle-16 制品是独立 effort）；drift 修复不应被阻塞于证据链完整性

### Decision 6: 不修复未来 cycle-18+ 可能发现的其他 ticket drift

**Choice**: 本 change 范围严格限定 cycle-16 (回溯归因) + cycle-17 finding 2 涉及的 5 unique lines / 7 occurrences；不预先承诺 follow-up 关闭未来 cycle 发现的 ticket drift。

**Rationale**:
- CLAUDE.md §3 surgical 原则：每个 finding 单独 fix 是 trace 完整性的体现
- audit-verification loop 每次 verify cycle 都会发现新 finding（这是 loop 能力扩展的体现），预先承诺 follow-up 范围会破坏 "每个 finding 独立证据链" 原则
- cycle-18 finding 1+ 的 ticket drift 修复应在对应的 change 提案中独立处理

**Alternatives considered**:
- (a) 在本 change 末尾加 "TODO: 全文 ticket `4 阶段` 残留扫描 follow-up" —— 拒绝：本 change scope-limited 闭环（A3-2 + A5-2 共 7 occurrences / 5 unique lines 全部修订为 "5 阶段"）；**scope 外实测**：其他 9 tickets 共 10 处 "4 阶段"/"四阶段" 残留由 cycle-18+ audit-verification 独立 finding 提案闭环，本 change 不预先承诺
- (b) 在 `scripts/` 下加新 ticket-lint 工具全局扫描 —— 拒绝：CLAUDE.md §3 简单性原则；超出本 change scope

## Risks / Trade-offs

- **[Risk]** ticket 文字修订可能影响其他 ticket 引用 "4 阶段" 文字的位置。**Mitigation**: `grep -rn "4 阶段" wayfinder/tickets/` 全文搜索（tasks.md 3.1）scope-limited 验证：本 change scope (A3-2.md + A5-2.md) 内 0 命中；**scope 外实测**（2026-09-22 post-apply）：其他 9 tickets 共 10 处 "4 阶段"/"四阶段" 残留—— A4-1.md:92, A4-2.md:82, A5-3.md:97, A5-3.md:124, A6a-1.md:113, A6a-2.md:101, A6b-1.md:14 + L1 "四阶段演进逻辑", A8-3.md:72, WF-1.md:43。这些位置**不在本 change scope**（per Decision 6），单独评估（不预先承诺 follow-up 范围；cycle-18+ audit-verification 独立 finding 提案）
- **[Risk]** A3-2 表格 vs 文字层 "5 阶段" 表述差异引发读者困惑。**Mitigation**: spec req-14 L293 闭式已 lock 5 阶段；表格下方 L72 "关键设计" 段已写 "Phase 1-3 不接路由梯度" 明确 Phase 1-3 是策略共享；文字与表格双轨表述与 spec 一致（Decision 2 已论证）
- **[Risk]** CLAUDE.md §6 第 7 条 vs §8 真相源层级冲突。**Mitigation**: design.md Decision 1 + 4 已显式论证本 change 适用 §8 优先解释（spec 是真相源，ticket drift 同步到 spec）；§6 第 7 条原文 "应改 spec 来对齐 ticket" 是 §8 之前的旧模型，2026-08-21 §8 裁决后已不适用；彻底解决 §6 / §8 冲突归独立 change `09-fix-claude-md-ticket-advisory-boundary` scope
- **[Risk]** cycle-16 finding 2 间接证据链薄弱。**Mitigation**: Decision 5 已显式承认；不阻塞本 change apply；如未来 cycle-18+ 发现独立 cycle-16 制品将升级证据链
- **[Risk]** Windows Edit tool CRLF contamination。**Mitigation**: 每个 ticket Edit 后跑 `git diff --stat` 验证 LF 保留（tasks.md C.1）；必要时 `sed -i 's/\r$//'` 恢复 LF（按 [[windows-edit-crlf-pitfall]] memory rule）
- **[Risk]** audit chain 一致性（LOOPS.md cycle-16/17 归档条目更新）。**Mitigation**: 本 change 不直接改 LOOPS.md（避免 scope 膨胀到 LOOPS.md 重写）；LOOPS.md 更新由 audit-verification loop 在 cycle-18 归档条目中独立处理（加 "closed by 05-fix-ticket-a5-2-cascading-correction" 引用）
- **[Risk]** 5 lines / 7 occurrences 文字修订跨多行（A3-2 L83 含 3 次 "4 阶段"，跨多字符 verbatim），Edit 工具若按行号 anchor 可能因 LF/CRLF 偏移错位。**Mitigation**: tasks.md A-TKT-1.1~A-TKT-2.2 每处都给出**完整 verbatim 旧文字 + 完整 verbatim 新文字**，Edit 工具用 unique string match 而非行号 anchor

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical ticket 文字同步（2 文件，5 unique lines / 7 occurrences 修订），无代码 / 数值 / 契约变更。实施步骤：

1. ticket 文字修订落地（per tasks.md §A）：
   - `wayfinder/tickets/A3-2.md` 3 lines / 5 occurrences（tasks.md A-TKT-1.1~A-TKT-1.3）
   - `wayfinder/tickets/A5-2.md` 2 lines / 2 occurrences（tasks.md A-TKT-2.1~A-TKT-2.2）
2. 跨 ticket 引用一致性验证（per tasks.md §B）：grep + spot-check
3. `git diff` 全文 review：5 lines / 7 occurrences 修订逐行核对（tasks.md C.2），确保只改 "4" → "5"
4. LF 校验：`git diff --stat` 验证（tasks.md C.1）
5. lint gate 验证：`python scripts/lint_no_dead_defensive.py` 与 `python scripts/lint_no_source_field_drift.py` exit=0（tasks.md C.6）
6. 单 commit on `dev`：`fix(ticket): close cycle-17 finding 2 ticket drift cascading (A3-2 + A5-2 '4 阶段' → '5 阶段')`（tasks.md C.7）
7. archive 准备：本 change 通过 `.openspec.yaml` `skip_specs: true` 标记 0 spec delta，`openspec validate fix-ticket-a5-2-cascading-correction --type change --strict` 应 PASS（无 "Unknown item" 或 MODIFIED-but-not-found warnings）

## Open Questions

- **future ticket drift 守门**: audit-verification cycle-18+ 是否会发现其他 ticket "4 阶段" 残留？本 change 闭环了 cycle-16 finding 2 (回溯归因) + cycle-17 finding 2，但不预先承诺全 ticket 字符串扫描。**Mitigation**: audit-verification loop 每次 cycle 都应做 `grep -rn "4 阶段" wayfinder/tickets/` 守门（已纳入 LOOPS.md 流程）；future finding 走独立 change 提案
- **A3-2 表格 3 行 vs spec 5 阶段 长期表述**: 本 change 决定保留表格 "Phase 0 / Phase 1-3 / Phase 4" 3 行结构（决策依据：表格描述 3 种更新策略而非 5 个阶段）。若未来 cycle 发现 spec 要求 5 行独立表达，需独立 change 修订表格
- **A6b-1 ticket 阶段数定义**: A3-2 L83 引用 `A6b-1 (5 阶段)` —— A6b-1 自身 ticket 内容未在本 change 范围检查。**Mitigation**: 若 A6b-1.md 也含 "4 阶段" 残留，cycle-18+ audit-verification 独立 finding 提案
- **ticket drift cascading 的 meta-pattern**: cycle-17 finding 2 报告 ticket drift cascading 是 audit-verification loop 第 1 次实证（meta-05 标签）。此 pattern 的更广泛含义（"所有 ticket 文字层与 spec 的术语一致性"是否需要全局 lint？）留待 future audit cycle 评估
- **CLAUDE.md §6 vs §8 冲突彻底解决**: Decision 1 + 4 仅论证本 change 适用 §8 优先解释，未彻底解决 §6 第 7 条文字表述与 §8 真相源层级冲突。该彻底解决归独立 change `09-fix-claude-md-ticket-advisory-boundary` scope