## Why

2026-09-18 audit-verification loop 完成 cycle-12 finding #1 三轴复核（α 算术 / β 文本 / γ severity），在 `.audit/audit-verification/audit-verification.md` L899-L1137 给出 **PARTIALLY-VERIFIED** verdict — α/γ OK + β PARTIAL（3 OK + 1 CITE-MISALIGNED on ticket A8-2 L74 转述）。用户已选 **选项 A**（推荐）：接受 finding 文字微调 + ticket A8-2 L70 + L74 supersede annotation 合并处理。本 change 是选项 A 的真正 OpenSpec 制品（从 `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/` 升级上来），关闭 cycle-12 finding #1。

**核心 finding**（per `.audit/spec-math-audit.md` L524 cycle-12 finding 1）：

> ticket A8-2 L70/L74 MCI 定义 stale（centered covariance reading + CV/convex hull radius reading → uncentered second moment）：ticket L70 说 `λ_j = C 分布协方差矩阵的特征值`（centered covariance，statistical 量），ticket L74 说 `原 CV（C 分布凸包半径）`（geometric 量），spec L408 显式 supersede 到 `λ_j = M = (1/|T|) · Σ C_t C_tᵀ` 的特征值（uncentered second moment，statistical 量）。

**关键 evidence 链**（per verify-13/14/15）：

1. **verify-13 axis-α**（L899-971）—— VERIFIED：numpy linear algebra + mpmath 30-digit 独立复算；rank reduction by centering 数学证明；centered covariance 在 `|T| = d_c` 时 `rank ≤ d_c − 1`，upper endpoint `MCI = 1` 不可达；uncentered second moment 两端可达（uniform ⇒ `MCI = 1.0`，rank-1 ⇒ `MCI = 1/d_c`）。
2. **verify-14 axis-β**（L974-1052）—— PARTIAL：spec L408 + L408 Reason + L411 Source verbatim CITE-OK × 3；ticket L74 CITE-MISALIGNED × 1（finding 转述为 "协方差矩阵"，ticket 实际为 "凸包半径 CV"，statistical vs geometric **不同数学量**）。finding 结论不变（supersede 仍合理），fix chain 不变：ticket A8-2 L70 + L74 仍需 supersede annotation（两处 stale 端）。
3. **verify-15 axis-γ**（L1056-1138）—— SEVERITY-OK + 用户决策选项 A。

**传染链状态**（per verify-15 L1128-1129）：

| 路径 | 状态 |
|---|---|
| `spec ↔ src/` | ✓ CLEAN（`MCI(token_signatures)` 用 spec L408 uncentered reading） |
| `spec ↔ tests/` | ✓ CLEAN（`test_mci_closed_form_*` 用 spec 闭式，abs=1e-12 守护） |
| `spec L408 Reason` | ✓ CLEAN（CV + centered covariance 双 supersede 论证） |
| `spec L411 Source` | ✓ CLEAN（3 反链齐：A8-2.md + fix-openspec-doc-bugs Decision 8 + fix-math-consistency-audit-2026-08 Decision 5） |
| `ticket A8-2 L70` (centered covariance) | ⚠️ STALE（无 supersede annotation） |
| `ticket A8-2 L74` (CV/convex hull) | ⚠️ STALE（无 supersede annotation） |
| `.audit/spec-math-audit.md` L524 finding 1 evidence 段 | ⚠️ FLAWED（finding 转述 L74 为 "协方差矩阵"） |
| `.audit/audit-verification.md` verify-15 verdict FLAWED 标记 | ⚠️ pending clear |

**CLAUDE.md §6 关键约束遵守**：

- §6 第 8 条：spec 算式必须直接对账生产代码；本 change 不引入新算式（spec L408 已是 uncentered second moment 钉死真相源），仅 ticket annotation + audit 文字微调，spec 不动
- §6 7 条：不动 wayfinder tickets 内容（仅追加 supersede annotation，**不删原 stale 数字**）；tickets 已 reference-only（per CLAUDE.md §8 裁决）
- §6 5 条：不执行训练或跑 baseline（formalize-only destination）
- §6 第 6 条：spec anchor 100% 覆盖已合规（wayfinder spec req-20 L389 + decompmoe-skeleton spec req-20 L442 等 anchor 齐）
- §6 第 8 条数学约束：spec L408 闭式 + L445/L449 Scenarios abs=1e-12 守护端点 `1/d_c` 与 `1.0`，本 change 不修改 spec 闭式

## What Changes

### 1. `wayfinder/tickets/A8-2.md` L70 + L74 各追加 italic supersede annotation（surgical Edit, 2 处；仅追加不删）

- **L70**（当前 verbatim `- λ_j = C 分布协方差矩阵的特征值`）末尾追加：italic `(historical, centered-covariance reading; superseded by spec req-20 L408 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — centered reading has (1/d_c, 1] upper endpoint unreachable at |T| = d_c)`
- **L74**（当前 verbatim `- **关键修正**：原 CV（C 分布凸包半径）在 S^{d_c-1} 下界为 1/d_c = 0.0625（健康值不可达），故替换`）末尾追加：italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 L408 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — CV lower bound 1/d_c on S^{d_c-1} makes original < 0.05 health target unreachable)`

### 2. `.audit/spec-math-audit.md` L524 cycle-12 finding 1 evidence 段微调（finding 主体不动，仅 evidence 子段精确化转述 ticket L70 + L74）

- 原文：`ticket 说 \`λ_j = C 分布协方差矩阵的特征值\`（centered covariance）... 修复路径：ticket A8-2 L74 改为 ... + (historical, 协方差矩阵 reading; ...)` → 微调后：精确区分 ticket L70（centered covariance）与 L74（CV/convex hull），并改 "修复路径" 为 `ticket A8-2 L70 + L74 各加一行 supersede annotation（仅追加，不删原 stale 数字）`
- finding 标题【MEDIUM】`ticket A8-2 L74 MCI 定义 stale (covariance → uncentered second moment)` 不动（保留 cross-finding 引用标识符）

### 3. `.audit/audit-verification.md` verify-15 verdict 段 FLAWED 标记清理 + finding 状态 promote

- L1092 `FLAWED: ticket-A8-2-L74 转述` 标记 → 替换为 `REMEDIATED via 选项 A finding 文字微调 + ticket A8-2 L70 + L74 supersede annotation per cycle-12 axis-γ follow-up`
- finding 状态 PARTIALLY-VERIFIED → fully-verified（α+β+γ 三轴全 OK）
- "下一步" 段更新：`cycle-12 finding 1 已 closed（选项 A applied, finding 文字微调 + ticket supersede annotation 合并）; cycle-12 finding 1 = fully-verified`
- audit trail 描述保留：`β 轴曾 PARTIAL due to CITE-MISALIGNED on ticket L74, 用户选项 A applied 后 fully-verified`（evidence 不抹除）

### 4. nothing else

per CLAUDE.md §3 surgical + §7 Out of Scope：

- **不动** `openspec/specs/wayfinder/spec.md` —— spec L408（uncentered second moment 闭式钉死真相源）+ L408 Reason（CV + centered covariance 双 supersede 论证）+ L408 Range（`MCI ∈ [1/d_c, 1]`）+ L411 Source（3 反链齐）+ L407-459 共 12 Scenarios（含 L445/L449 MCI closed-form abs=1e-12 守护）全部已合规
- **不动** `openspec/specs/decompmoe-skeleton/spec.md` —— 该 capability verbatim 复述了 wayfinder Req 20 全部 8 个 metric closed-form（L500-518 + L560-568 含 MCI closed-form + Scenarios），已与 wayfinder spec 对齐；本 change 不引入新 metric 行为
- **不动** `openspec/specs/governance/spec.md` —— 现有 req-gov-1（Test Guard Precision for Closed-Form Numerical Claims, anchor L7 unchanged + body L9-L25 drifted +2）已形式化整数/浮点对账二分原则；本 change 的 ticket annotation 模式属于该 req-gov-1 之外、CLAUDE.md §3 source-field rules 涵盖的另一个 governance concern（ticket advisory boundary），由 planned change `09-fix-claude-md-ticket-advisory-boundary`（当前为 `.audit/.../opsx-changes/` planning 草案）形式化
- **不动** `src/decompmoe/metrics.py` —— `MCI(token_signatures)` 用 spec L408 uncentered reading 实现，与 spec 完全对齐
- **不动** `tests/` —— 既有 `tests/test_metrics.py::test_mci_*` 用 spec 闭式 + abs=1e-12 守护（无 test LOCKS stale），传染链已断于 src/tests/spec 三角干净
- **不动** 其他 wayfinder tickets（A8-1, A8-3, A6a-2, A4-1, A5-3, A6b-1 等）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder`: ADDED Requirement "Eight Geometric Quantification Metrics — Ticket A8-2 L70/L74 Supersede Annotation Closure"（documenting-only：声明 spec L408 是钉死真相源，spec 不动；通过 L408 Reason + L411 Source + L407-459 Scenarios 形式化 reference chain）
- `decompmoe-skeleton`: ADDED Requirement "No decompmoe-skeleton spec changes required for cycle-12 finding 1 closure"（documenting-only：声明 decompmoe-skeleton L502-568 verbatim 复述 wayfinder Req 20 8 metric closed-form，本 change 不引入新 metric 行为）
- `governance`: ADDED Requirement "Governance advisory note — ticket A8-2 L70/L74 supersede annotation"（documenting-only：声明 ticket annotation 模式对齐 CLAUDE.md §3 source-field rules；planned change `09-fix-claude-md-ticket-advisory-boundary` 形式化 ticket advisory boundary 的完整 governance contract）

**为什么不需要 spec Requirement delta**：spec L408 已是 uncentered second moment 钉死真相源；spec L408 Reason 双论证 supersede CV + centered covariance 已完整；spec L411 Source 3 反链齐；spec L445/L449 Scenarios abs=1e-12 守护两端点。三个 capability 的 ADDED Requirements 是 documenting-only 形式，把 "spec 不变"+"本 change 不动 spec"+"spec 是钉死真相源" 显式纳入 spec 文档，让 future reader 能直接 grep 到本 change 的 spec-level 锚点（per CLAUDE.md §3 source-field rules + governance req-gov-1 policy lineage discipline）。

## Impact

- **Affected code**（none per CLAUDE.md §3 surgical）：本 change 是 ticket + audit 文字微调，**0 文件 src/ 改动**、**0 文件 tests/ 改动**、**0 文件 spec Requirement 改动**（仅 documenting-only ADDED meta-Ref-Adequirements 显式声明）
- **Affected tickets**（surgical 2 处）：
  - `wayfinder/tickets/A8-2.md` L70 末尾追加 italic `(historical, centered-covariance reading; superseded by spec req-20 L408 ...)` annotation
  - `wayfinder/tickets/A8-2.md` L74 末尾追加 italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 L408 ...)` annotation
- **Affected audit files**（surgical 2 处）：
  - `.audit/spec-math-audit.md` L524 cycle-12 finding 1 evidence 段文字微调（精确化转述 ticket L70 + L74）
  - `.audit/audit-verification.md` verify-15 verdict FLAWED 标记清理 + finding 状态 promote
- **Affected spec files**（documenting-only delta 3 处）：`openspec/specs/wayfinder/spec.md` + `openspec/specs/decompmoe-skeleton/spec.md` + `openspec/specs/governance/spec.md` 各追加 1 个 ADDED meta-Requirement，**不修改**任何既有 Requirement 文字
- **Affected APIs / dependencies**：无
- **Affected systems**：无（推理引擎实现代码已 out-of-scope per CLAUDE.md §7）
- **Risk**：
  - **Risk A**：annotation 文字与 spec L408 Reason 不一致（drift between spec/ticket annotation）。Mitigation：annotation verbatim 引用 spec L408 Reason 文字 + audit-verification verify-13/14 evidence IDs；tasks.md §C.2 强制 `grep "superseded by spec req-20 L408" wayfinder/tickets/A8-2.md` 验证
  - **Risk B**：annotation 误标 ticket 为 "stale" 而非 "historical"。Mitigation：annotation 使用 canonical 形式 `(historical, <原值 reading>; superseded by spec req-N L### via <change> Decision M)`（per CLAUDE.md §3 source-field rules 形式化 pattern），明确"原值保留"而非"删除"
  - **Risk C**：annotation 与 ticket L70/L74 触发描述本体的 backtick 嵌套冲突（markdown 渲染问题）。Mitigation：annotation 使用外层 `*...*` italic 包覆，内层 `` `uncentered second moment` `` 与 `` `fix-openspec-doc-bugs` `` backtick-wrapped 限定公式与 change 名，markdown 解析无歧义
  - **Risk D**：finding 文字微调后 cycle-12 finding 1 转 fully-verified，但 audit-verification.md 已记录 CITE-MISALIGNED 历史（需保留 evidence 链）。Mitigation：`.audit/audit-verification.md` verify-15 verdict 段保留 audit trail 描述（"β 轴曾 PARTIAL due to CITE-MISALIGNED on ticket L74, 用户选项 A applied 后 fully-verified"），不抹除 evidence
  - **Risk E**：audit 文件（`.audit/spec-math-audit.md` + `.audit/audit-verification.md`）在 `.gitignore` 或不进 git 追踪，编辑后可能不被记录。Mitigation：per `.audit/README.md` L3 ".audit/ 是临时证据库 (与 .audit/audit-report.md 同位, 不进 git 追踪)"，本 change 的 audit 文字微调是**审计阶段证据修正**，不进 git 永久文档，但本 OpenSpec change 制品（proposal.md + tasks.md + design.md + specs/）在 `openspec/changes/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/` 是**永久 plan 草案**
  - **Risk F**：Windows Edit tool CRLF contamination。Mitigation：tasks.md §C.5 LF 校验强制 `git diff --stat wayfinder/tickets/A8-2.md` 验证 +2 行、0 删除；`file wayfinder/tickets/A8-2.md` 验证 LF；必要时 `sed -i 's/\r$//' wayfinder/tickets/A8-2.md`
  - **Risk G**：三个 ADDED meta-Ref-Adequirements 在 spec 内引入新 anchor，触发 CLAUDE.md §6 第 6 条 "spec anchor 100% 覆盖" lint 监控。Mitigation：每个 ADDED Requirement 首行 `<a id="..."></a>`（per spec-driven schema convention），tasks.md §C.7 lint gate 强制 `python scripts/lint_no_source_field_drift.py` exit=0
  - **Risk H**：governance ADDED Requirement 引用 planned `09-fix-claude-md-ticket-advisory-boundary` 但该 change 未 apply。Mitigation：governance Requirement Source 反链字段同时声明 `CLAUDE.md` §3（已存在 governance contract 的权威源）+ 标注 planned 09 为 advisory note，**不**将 planned 09 当作已形式化 contract

- **Source**：本 change 由 audit-verification loop cycle-12 finding #1 axis-γ follow-up（`.audit/audit-verification/audit-verification.md` L1094-1110）显式触发（用户决策选项 A）+ CLAUDE.md §3 source-field rules 形式化条款（governance/CLAUDE.md back-link）。evidence 链：
  - verify-13 (cycle-12 axis-α)：numpy linear algebra + mpmath 30-digit matrix ops + rank reduction by centering 数学证明
  - verify-14 (cycle-12 axis-β)：CITE-OK × 3 verbatim 命中 spec L408 + L408 Reason + L411 Source + **CITE-MISALIGNED × 1** on ticket L74
  - verify-15 (cycle-12 axis-γ)：SEVERITY-OK + 用户决策选项 A/B/C
  - 6-cycle ticket-stale pattern family (cycle-5/6/7/9/12/13) per `.audit/audit-verification/README.md` §"6-cycle ticket-stale pattern family"