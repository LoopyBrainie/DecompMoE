## Context

`wayfinder/tickets/A6a-2.md` L63 触发描述 `f_i^avg < 1/128` 持续 200 steps 与 `openspec/specs/wayfinder/spec.md` L245 参数化形式 `f_threshold = 1/(2·N_e)` 不一致。spec L247 Source 已含 `(historical, threshold 1/128)` supersede 注释；`src/decompmoe/safeguards.py` L34-36 已参数化 + L29 含 legacy 注释 "Previously hardcoded to 1/128 (N_e=64 legacy)"。ticket 端是**唯一 stale 数值源头**。

跨传染链：spec ✓ CLEAN、src/ ✓ CLEAN、tests/ ✓ CLEAN（无 test LOCKS stale `1/128`，per audit-verification verify-6 + verify-12 worst-case claim）。修复方向：在 ticket L63 末尾追加 italic `(historical, ...)` annotation，保留决策链。spec ↔ src/ 修复不影响 src/ runtime（worst-case "MVP resurrection 永远不触发" 没发生）。

详细 motivation 见 `proposal.md - Why`；evidence chain 见 `.audit/audit-verification/audit-verification.md` L678-L898（verify-10/11/12 三轴闭环）。

## Goals / Non-Goals

**Goals:**
- 在 ticket A6a-2 L63 末尾追加 1 行 italic annotation，verbatim 引用 audit-verification L853 fix recommendation + spec L245 公式片段
- annotation 形式与 spec L747-754 "secondary references in parenthetical annotations use bare ticket IDs" 形式化原则一致（外层 italic、内层 backtick-wrapped 公式 + change 名）
- 单 commit on `dev`（per CLAUDE.md §4 git branch architecture）
- 0 文件 src/ 改动、0 文件 tests/ 改动、0 文件 spec 改动、0 文件 CLAUDE.md 改动
- LF 校验确保 CRLF 保持（wayfinder/tickets/*.md 项目惯例是 CRLF）

**Non-Goals:**
- 不修改 spec L245（参数化形式已完备）或 spec L247（Source 注释已完备）
- 不修改 src/decompmoe/safeguards.py（已合规参数化 + legacy 注释）
- 不引入新 test（ticket 不是 executable code，annotation 精度可独立 cross-validate via audit-verification scripts）
- 不修复 cycle-5/6/7/12/13 各自 ticket-stale finding（属各自独立 change 范围）
- 不依赖尚未 apply 的 governance Requirement（per `.audit/audit-verification/opsx-changes/09-fix-claude-md-ticket-advisory-boundary/proposal.md` 计划中的 `governance/spec.md` "Ticket Advisory Boundary — Stale Contamination Monitoring"）

## Decisions

### Decision 1: ticket-only annotation 而非 spec/src/ 修改

**Choice**: 仅修改 `wayfinder/tickets/A6a-2.md` L63 末尾追加 italic annotation，**不动** spec / src/ / tests/。

**Rationale**: cycle-9 三轴 evidence chain 确认**唯一 stale 端 = ticket A6a-2 L63**：
- spec L245 ✓ CLEAN（参数化形式 `1/(2·N_e)`）
- spec L247 Source ✓ CLEAN（`(historical, threshold 1/128)` 注释）
- src/ L34-36 ✓ CLEAN（参数化 `_dead_expert_threshold(N_e)`）
- src/ L29 ✓ CLEAN（legacy 注释）
- **唯一 stale 端 = ticket L63**

传染链已断于 src/（per verify-12 worst-case claim "src/ 用 spec 而非 ticket"），MVP runtime 无 current functional impact。本 change 是**预防性** ticket-side supersede annotation。

**Alternatives considered**:
- (a) 修改 spec L245 (e.g., 改回 hardcoded `1/128`) —— 拒绝：spec L245 是 audit-verification 反复 cross-validate 的稳定锚点（L799 "spec L245 是新发现的稳定锚点"）
- (b) 修改 src/decompmoe/safeguards.py (e.g., 改回 hardcoded `1/128`) —— 拒绝：src/ 已合规参数化 + legacy 注释
- (c) 删除 ticket A6a-2 L63 触发描述本体 —— 拒绝：违反 CLAUDE.md "annotation preserving the decision chain" 原则，ticket 内容是决策历史不应删除

### Decision 2: annotation 形式 verbatim 引用 audit-verification L853 + spec L245

**Choice**: annotation 文字 verbatim：
```
*(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L245 `f_threshold = 1/(2·N_e)` via `fix-openspec-doc-bugs` design.md Decision 7)*
```

**Rationale**: annotation 拼接两处权威来源：
1. **audit-verification L853**（fix recommendation）：`(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L245 via fix-openspec-doc-bugs Decision 7)`
2. **spec L245**（参数化公式片段）：`f_threshold = 1/(2·N_e)`

annotation 内嵌 `` `f_threshold = 1/(2·N_e)` `` 公式 + `` `fix-openspec-doc-bugs` `` change 名 backtick-wrapped，符合 spec L747-754 形式化原则。

**Alternatives considered**:
- (a) 仅加 `(historical, threshold 1/128)` —— 拒绝：缺失 supersede chain
- (b) 链接 `[superseded by fix-openspec-doc-bugs](...)` —— 拒绝：markdown 不支持跨文件 link，spec L747-754 用 paren annotation 形式
- (c) 仅用 spec L247 Source field 形式（短式 `(historical, threshold 1/128), change ...`）—— 拒绝：spec L247 是 Source field 形式（嵌入在 `**Source:**` 字段里），不适合直接 inline 追加到 ticket L63 bullet 行末。长式更易 inline

### Decision 3: annotation 使用 italic (`*...*`) 而非 bold 或 plain text

**Choice**: annotation 用 `*...*` italic 单星号包覆，与 ticket L63 原 bullet `- **触发**：`f_i^avg < 1/128` 持续 200 steps` 中 bold `**触发**` 区分。

**Rationale**: markdown 约定：
- bold `**...**` —— bullet label（结构性 marker）
- italic `*...*` —— inline annotation（补充说明）
- code `` `...` `` —— formula / identifier（不可 toggle 语义）

annotation 内嵌两个 backtick-wrapped 元素（公式 + change 名），符合 spec L747-754 原则。

**Alternatives considered**:
- (a) plain text —— 拒绝：与 bullet label 视觉无区分
- (b) bold `**...**` —— 拒绝：与原 `**触发**` bold label 同级混淆
- (c) code fence ` ``` ... ``` ` —— 拒绝：annotation 是 inline 注释，过度格式化

### Decision 4: 不引入新 spec Requirement / Scenario（skip_specs=true）

**Choice**: 本 change 不修改任何 spec Requirement；`.openspec.yaml` 设 `skip_specs: true`。

**Rationale**:
- spec L245 + L247 已正确反映 supersede chain
- src/ 已合规
- 本 change 是 ticket-level 实际修复，无 spec-level 行为变化
- "ticket 端 supersede annotation 形式化"属 change 09 范围（尚未 apply），本 change 不依赖其生效

**Alternatives considered**:
- (a) 在 wayfinder/spec.md req-13 加 Scenario `supersede annotation mirrored on ticket side` —— 拒绝：scenario 是 spec-level 形式化守护，本 change 是 ticket-level 实际修复
- (b) 在 governance/spec.md 新增 Requirement —— 拒绝：本 change 不依赖 change 09 apply；待 change 09 apply 后由独立 change 跟进
- (c) skip_specs=true + 不引入新 spec —— 选择：本 change scope 限定 ticket-only

## Risks / Trade-offs

- **[Risk 1]** annotation 文字与 audit-verification L853 不一致 —— **Mitigation**：annotation 文字 verbatim 引用 L853 + spec L245 公式片段
- **[Risk 2]** annotation 误标 ticket 为 "stale" 而非 "historical" —— **Mitigation**：annotation 显式使用 `(historical, <原值>; superseded by ...)` 形式，`<原值>` verbatim 保留 `1/128 at N_e=64` 而非删除
- **[Risk 3]** annotation 与 ticket L63 触发描述本体的 backtick 嵌套冲突 —— **Mitigation**：外层 `*...*` italic 包覆，内层双 backtick-wrapped 公式 + change 名；markdown 解析无歧义
- **[Risk 4]** Windows Edit tool CRLF contamination —— **Mitigation**：tasks.md §A.4 强制 CRLF 保持验证（项目惯例：wayfinder/tickets/*.md 是 CRLF，109 个 CRLF 行 vs 0 LF-only）
- **[Risk 5]** annotation 形式与 spec L747-754 lint 三项结构性检查冲突 —— **Mitigation**：annotation 是 inline italic 注释而非 `**Source:**` 字段，不触发 lint
- **[Risk 6]** audit-verification loop 后续 cycle 复核 annotation 文字（meta-meta-audit）—— **Mitigation**：annotation 文字 verbatim 引用 audit-verification evidence IDs，未来 audit cycle 可独立 cross-validate

## Migration Plan

N/A — no deployment, no rollback, no migration。实施步骤：

1. **ticket L63 annotation 追加**：Edit `wayfinder/tickets/A6a-2.md` L63 末尾追加 italic annotation（约 1 行 inline 追加）
2. **LF 校验**：Edit 后 `file wayfinder/tickets/A6a-2.md` 或 `head -1 ... | od -c` 验证 CRLF 保持；必要时 `sed -i 's/\r$//' ...` 仅为 CRLF 污染兜底（项目惯例是 CRLF，正常 Edit 不应破坏）
3. **cross-validation**：`grep -n "historical, threshold 1/128 at N_e=64" wayfinder/tickets/A6a-2.md` 应返回 1 hit
4. **lint gate**：`python scripts/lint_no_dead_defensive.py` + `python scripts/lint_no_source_field_drift.py` 全 exit 0（不修改 src/ spec）
5. **既有 test 全绿**：`uv run pytest tests/ -v`（不引入新 test）
6. **单 commit on `dev`**：`fix(ticket): A6a-2 L63 supersede annotation per cycle-9 audit-verification (1/128 → 1/(2·N_e))` + Co-Authored-By trailer

## Open Questions

- **Change 09 apply 时序**：governance req-gov-2 "Ticket Advisory Boundary" 是否在 change 02 apply 之前落地？本 change **不依赖** change 09 apply；annotation 形式基于 audit-verification 推荐 + spec L747-754 原则，与 governance 形式化独立
- **spec L753 stale `L251` 行号**：spec req-34 canonical live example 段 L753 引用 `L251`，实际 canonical example 在 L247（差 4 行）。这是 spec 端 stale 引用，非本 change 范围；未来 spec 清理时可一并修复
- **6-cycle family 其他 5 条 fix**：cycle-5/6/7/12/13 ticket-stale finding 的实际修复属各自范围（per audit-verification README §"6-cycle ticket-stale pattern family"），本 change 仅 cycle-9 ticket-side closure

Co-Authored-By: Claude Code <noreply@anthropic.com>