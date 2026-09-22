# Tasks: fix-ticket-a5-2-cascading-correction

## 1. ticket 文字同步段（2 文件，5 unique lines / 7 occurrences）

- [x] 1.1 Edit `wayfinder/tickets/A3-2.md` L25 锁定行：将 `**锁定：C 提取全可微（D 路径）+ c_i 走 4 阶段生命周期**` 替换为 `**锁定：C 提取全可微（D 路径）+ c_i 走 5 阶段生命周期**`（verbatim unique match；本行 "4 阶段" 1 次）。**Done in propose phase** — 写入 ticket 文字。
- [x] 1.2 Edit `wayfinder/tickets/A3-2.md` L33 二级标题：将 `### c_i 更新策略：4 阶段生命周期（球面几何约束贯穿）` 替换为 `### c_i 更新策略：5 阶段生命周期（球面几何约束贯穿）`（verbatim unique match；本行 "4 阶段" 1 次）。**Done in propose phase** — 写入 ticket 文字。
- [x] 1.3 Edit `wayfinder/tickets/A3-2.md` L83 后续 ticket 影响行：将 `- A6b-1 (4 阶段)：c_i 生命周期的 4 阶段与训练 4 阶段对齐` 替换为 `- A6b-1 (5 阶段)：c_i 生命周期的 5 阶段与训练 5 阶段对齐`（verbatim unique match；本行 "4 阶段" 3 次，一次 Edit 全部替换）。**Done in propose phase** — 写入 ticket 文字。
- [x] 1.4 验证：`grep -n "4 阶段" wayfinder/tickets/A3-2.md` 应返回 **0** 命中（3 lines / 5 occurrences 全修订）；`grep -n "5 阶段" wayfinder/tickets/A3-2.md` 应返回 **3** 命中（L25/L33/L83 全部 "5 阶段"）。
- [x] 1.5 验证（不修改）：A3-2.md L66-70 表格内容（Phase 0 / Phase 1-3 / Phase 4 共 3 行）保持不变 —— 表格描述 3 种 c_i 更新策略，文字层 "5 阶段" 与表格不冲突（Phase 1-3 共享 Masked Spherical EMA，α schedule 区分，spec req-14 L293 闭式已 lock 5 阶段）。
- [x] 1.6 独立文本复核：手读 A3-2.md 全文，3 lines 修订与 spec req-14 L293 "five phases" 闭式一致；表格 L66-70 描述 3 种 c_i 更新策略，文字层 5 阶段与表格双轨表述无内部矛盾。

## 2. wayfinder/tickets/A5-2.md 修订（关闭 cycle-17 drift 传染端）

- [x] 2.1 Edit `wayfinder/tickets/A5-2.md` L56 Caveat 训练充分分化行：将 `- 训练充分分化：A3-2 4 阶段生命周期 + A6b 退火调度` 替换为 `- 训练充分分化：A3-2 5 阶段生命周期 + A6b 退火调度`（verbatim unique match；**注意**：实际 L56，cycle-17 audit-verification.md L1459/L1481/L1492 同源 off-by-one 曾记为 L57）。**Done in propose phase** — 写入 ticket 文字。
- [x] 2.2 Edit `wayfinder/tickets/A5-2.md` L63 后续 ticket 影响行：将 `- A6b-1 (4 阶段)：无需为 shared expert 单独设计阶段，所有专家同步生命周期` 替换为 `- A6b-1 (5 阶段)：无需为 shared expert 单独设计阶段，所有专家同步生命周期`（verbatim unique match）。**Done in propose phase** — 写入 ticket 文字。
- [x] 2.3 验证：`grep -n "4 阶段" wayfinder/tickets/A5-2.md` 应返回 **0** 命中（2 lines / 2 occurrences 全修订）；`grep -n "5 阶段" wayfinder/tickets/A5-2.md` 应返回 **2** 命中（L56/L63 全部 "5 阶段"）。
- [x] 2.4 独立文本复核：手读 A5-2.md 全文，L56 引用 "A3-2 5 阶段生命周期" 与已修订的 A3-2.md 文字一致（传播链闭合：cycle-16 源 + cycle-17 传染端双端修订）；L63 "A6b-1 (5 阶段)" 与 A3-2.md L83 修订一致（2 处 ticket 引用 "A6b-1 (5 阶段)" 全部统一）。
- [x] 2.5 验证（不修改）：A5-2.md 其他 L27/L32/L37-40/L42-45/L47-49 等 forward equation + 3 数学保证 verbatim 文字保持原样（cycle-17 finding 1 axis-β CITE-OK×10 全部已 verified，本 change 不动 finding 1 的 10 处 verbatim 命中）。

## 3. 跨 ticket 引用一致性验证

- [x] 3.1 全量 `grep` 扫描（scope-limited 验证）：`grep -rn "4 阶段\|four-stage\|four stage" wayfinder/tickets/` 应返回 **0** 命中（**限本 change scope**：`wayfinder/tickets/A3-2.md` + `wayfinder/tickets/A5-2.md` 内 0 命中）。**完整 grep 实测结果**（2026-09-22 post-apply 全 tickets）："4 阶段" / "four-stage" / "four stage" 在 9 unique tickets 共 10 处命中 —— A4-1.md:92 / A4-2.md:82 / A5-3.md:97 / A5-3.md:124 / A6a-1.md:113 / A6a-2.md:101 / A6b-1.md:14 / A8-3.md:72 / WF-1.md:43 (9 lines) + A6b-1.md:1 ("四阶段演进逻辑" 标题, 中文数字 "four-stage", 1 hit) = 10 hits total。这些命中**不在本 change scope**，per Decision 6 (CLAUDE.md §3 surgical + §8 ticket 仅历史决策记录)；cycle-18+ audit-verification 独立 finding 提案闭环其他 ticket 残留。
- [x] 3.2 反向 `grep` 验证（scope-limited 验证）：`grep -rn "5 阶段\|five phases\|five-stage\|five phase" wayfinder/tickets/` 应至少返回 **7** 命中（**限本 change scope**：A3-2 5 occurrences (L25×1, L33×1, L83×3) + A5-2 2 occurrences (L56×1, L63×1) = 7 occurrences within scope）。**完整 grep 实测结果**（2026-09-22 post-apply）：7 + 3 pre-existing "5 阶段" hits in A1-1.md:82 + A6b-1.md:48 + (search "five phases" 0 hits in tickets, all English "Five-Phase" 表述在 spec 内) = 10 hits total in wayfinder/tickets/ for "5 阶段" 字符串。本 change 仅承诺 7 within scope; pre-existing 3 是其他 ticket 的 prior 修订产物。
- [x] 3.3 spec 一致性 spot-check：`grep -n "five phases\|5 阶段" openspec/specs/wayfinder/spec.md` 应返回 ≥1 命中（req-14 L293 "five phases" 闭式仍在原位，anchor L289），与 ticket 修订后文字一致。
- [x] 3.4 跨 ticket 引用一致性 spot-check：`grep -n "A3-2\|A6b" wayfinder/tickets/A5-2.md` 应保留 L56 + L63 两处 "A3-2" / "A6b" cross-reference，引用方向正确（A5-2 → A3-2 → spec req-14，drift 传播链反向）。
- [x] 3.5 audit-verification 引用闭环：cycle-17 finding 2 (audit-verification.md L1459/L1481-1498) 引用本 change ID `fix-ticket-a5-2-cascading-correction`；cycle-16 finding 2 通过 cycle-17 verify-20 axis-β cross-cycle 回溯归因（无独立 cycle-16 制品，本 change 接受此间接证据链）；ticket 修订后这两条 finding 在 audit chain 上标记 "closed by change 05"（不在本 change scope 内改 audit 文件，仅作交叉引用一致性验证）。

## 4. 验证与提交（surgical）

- [x] 4.1 LF 校验：每个 ticket Edit 后 `git diff --stat wayfinder/tickets/A3-2.md wayfinder/tickets/A5-2.md` 验证行数变化：A3-2 3 lines 文字修订（共 +0 -0，每行仅 "4" 替换为 "5"，A3-2 L83 含 3 次替换），A5-2 2 lines 文字修订（共 +0 -0，每行仅 "4" 替换为 "5"）。必要时 `sed -i 's/\r$//'` 恢复 LF（按 [[windows-edit-crlf-pitfall]]）。**实际发生 CRLF 污染并已修复**：Edit 工具引入 CRLF 后用 PowerShell `[System.IO.File]::WriteAllText` 重新写为 LF（无 BOM），`git diff --stat` 现显示 A3-2 6 行 markers / A5-2 4 行 markers，CRLF warning 消失。
- [x] 4.2 `git diff wayfinder/tickets/A3-2.md wayfinder/tickets/A5-2.md` 全 diff review：5 lines / 7 occurrences 修订逐行核对，确保只改 "4" → "5"（字符级精确），无其他文字连带修改（CLAUDE.md §3 surgical 原则）。
- [x] 4.3 spec 0 改动验证：`git diff openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md openspec/specs/governance/spec.md` 应返回 **0** 命中（本 change 不动 OpenSpec spec，通过 `.openspec.yaml` `skip_specs: true` 标记）。
- [x] 4.4 src/ 0 改动验证：`git diff src/` 应返回 **0** 命中（本 change 不动 `src/decompmoe/` 任何文件）。
- [x] 4.5 tests/ 0 改动验证：`git diff tests/` 应返回 **0** 命中（本 change 是 doc-level，无测试改动）。
- [x] 4.6 lint gate 验证：`python scripts/lint_no_dead_defensive.py` 与 `python scripts/lint_no_source_field_drift.py` 应仍 **exit=0**（ticket 文字修订不触发 `Source:` 反链漂移，wayfinder ticket 反链规则仍合规；tickets 自身不在 `Source:` 字段守门范围内）。
- [x] 4.7 单 commit on `dev`：`git add wayfinder/tickets/A3-2.md wayfinder/tickets/A5-2.md && git commit -m "fix(ticket): close cycle-17 finding 2 ticket drift cascading (A3-2 L25/L33/L83 + A5-2 L56/L63 '4 阶段' → '5 阶段')"`。**实际 commit hash**：`66752e6` on `dev`，2 files / 5 insertions / 5 deletions。
- [x] 4.8 archive 准备：本 change 通过 `.openspec.yaml` `skip_specs: true` 标记 0 spec delta，`openspec validate fix-ticket-a5-2-cascading-correction --type change --strict` 应 PASS（无 "Unknown item" 或 MODIFIED-but-not-found warnings）；ticket 文字同步不触发任何 spec 校验失败。**实际验证**：`valid: True` + skip_specs INFO 备注，isPlanningComplete=True, isComplete=True。