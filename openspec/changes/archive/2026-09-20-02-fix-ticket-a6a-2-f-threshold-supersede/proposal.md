## Why

`wayfinder/tickets/A6a-2.md` L63 硬编码 `f_i^avg < 1/128`（N_e=64 design 时代的数值快照），但 `openspec/specs/wayfinder/spec.md` L245 已 supersede 到参数化形式 `f_threshold = 1/(2·N_e)`（at MVP N_e=16 = 1/32），spec L247 Source 也已显式标注 supersede chain。spec ↔ src/ 传染链已断（`src/decompmoe/safeguards.py` L34-36 + L29 已合规），ticket 是**唯一 stale 数值源头**，且在 MVP 下触发阈值过严、dead expert 永远进不了 resurrection 流程（audit-verification loop 唯一有 runtime impact 的 finding）。

修复方式：在 ticket L63 末尾追加 italic `(historical, ...)` supersede annotation，**保留决策链**而非替代原值；不动 spec（已完备）/ src/（已参数化）/ tests/（与 finding 无关）。这是预防性 ticket-side 闭合，防止未来"读 ticket 而不读 spec"的实现复制 stale `1/128`。

## What Changes

- `wayfinder/tickets/A6a-2.md` L63 末尾追加 italic annotation，约 1 行 inline 追加（**不动**触发描述本体；**不动** ticket 任何其他段）
- annotation 文字引用 audit-verification L853 fix recommendation verbatim（`historical, threshold 1/128 at N_e=64; superseded by spec req-13 L245 via fix-openspec-doc-bugs Decision 7`）+ spec L245 参数化公式 `f_threshold = 1/(2·N_e)`（避免与 spec 真相源脱钩）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> **Note**: 本 change 不修改任何 spec Requirement。spec L245 + L247 已正确反映 supersede chain，src/ 已合规，`tests/` 无 test LOCKS stale `1/128`。`skip_specs: true` 是 OpenSpec 约定的 docs-only change 标记。
>
> **Note**: 任何"ticket 端 supersede annotation 形式化"治理条款（per `.audit/audit-verification/opsx-changes/09-fix-claude-md-ticket-advisory-boundary/proposal.md` 计划中的 `governance/spec.md` 新增 Requirement "Ticket Advisory Boundary — Stale Contamination Monitoring"）属**独立 change 范围**（change 09，尚未 apply）。本 change 不依赖该 Requirement 是否生效；annotation 形式的法源是 audit-verification 推荐 + spec L247 已建立的 Source-field 惯例，不依赖任何 future governance Requirement。

## Impact

- **Affected code**（none）：本 change 是 ticket-only annotation，**0 文件 src/ 改动、0 文件 tests/ 改动、0 文件 spec 改动、0 文件 CLAUDE.md 改动**
- **Affected tickets**（surgical 1 处）：`wayfinder/tickets/A6a-2.md` L63 末尾追加 italic `(historical, ...)` annotation（约 1 行）
- **Affected APIs / dependencies**：无
- **Affected systems**：无（推理引擎实现代码已 out-of-scope per CLAUDE.md §7）
- **Evidence chain**（per `.audit/audit-verification/audit-verification.md` L678-L898）：
  - verify-10 (cycle-9 axis-α)：50-digit mpmath `1/(2·16) = 0.03125` exact；ticket `1/128 = 0.0078125` exact；drift 4x ratio 300%
  - verify-11 (cycle-9 axis-β)：CITE-OK×3 verbatim 命中 spec L245 + spec L247 Source + ticket L63 + src/ L29 legacy 注释
  - verify-12 (cycle-9 axis-γ)：SEVERITY-OK×3 + worst-case "MVP resurrection 永远不触发" didn't materialize（src/ 用 spec 而非 ticket）
  - L853 fix recommendation 显式建议该 annotation 形式
- **Source**：
  - spec L245 + L247 真相源（per CLAUDE.md §2 真相源层级）
  - audit-verification.md L853 fix recommendation
  - spec L747-754 "secondary references in parenthetical annotations use bare ticket IDs" 形式化原则
  - audit-verification README §"6-cycle ticket-stale pattern family"（cycle-5/6/7/9/12/13 共 6 条 MEDIUM finding 同源）
- **Risk**：
  - Risk A：annotation 文字与 spec L247 形式 drift。Mitigation：annotation 引用 audit-verification L853 verbatim + spec L245 公式片段，避免自行构造
  - Risk B：annotation 误标 ticket 为 "stale" 而非 "historical"。Mitigation：annotation 使用 `(historical, <原值>; superseded by ...)` 形式，明确"原值保留"
  - Risk C：annotation 与 ticket L63 触发描述本体的 backtick 嵌套冲突。Mitigation：外层 `*...*` italic 包覆，内层 `` `f_threshold = 1/(2·N_e)` `` + `` `fix-openspec-doc-bugs` `` backtick-wrapped 限定
  - Risk D：Windows Edit tool CRLF contamination。Mitigation：tasks.md §A.4 LF 校验（实际 wayfinder/tickets/*.md 是 CRLF，需验证 CRLF 保持而非转换为 LF）

Co-Authored-By: Claude Code <noreply@anthropic.com>