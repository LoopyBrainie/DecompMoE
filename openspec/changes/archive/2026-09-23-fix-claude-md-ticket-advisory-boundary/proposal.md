## Why

`CLAUDE.md` §8 当前裁决（"ticket 仅作历史决策记录（参考性、非约束性）"）只声明了 ticket **advisory** 的语义边界，但**未明确** advisory 与 operational impact 的区分。`.audit/audit-verification/audit-verification.md` L530 实证：cycle-7 finding "ticket stale → src/ 单向污染"——advisory 不等于无影响。本次变更在 `CLAUDE.md` §8 末尾追加边界补充段，并新增 governance Requirement 形式化 monitoring obligation 与 remediation protocol，让 lint 可守护（per `CLAUDE.md` §3 `/opsx:archive` 前置条件 + `wayfinder/spec.md` req-34 L778-783 治理 Scenario）。

**关键 evidence**（实测 2026-09-23 状态）：

1. cycle-7 audit-verification L581 显式建议 "建议更新 CLAUDE.md §8 加一句'ticket stale 仍可能传染 src/, 需以 cycle-6/7 模式监控'"
2. cycle-5/6/7 MEDIUM finding 4-file batch fix **已由 commit `adf41ef`（2026-09-19 21:12:30）关闭**（按 `git log --oneline adf41ef`）：`MVPConfig.beta_initial: 1.0 → 1.035`、`tests/test_beta.py` `assert == 1.0 → pytest.approx(expected, abs=1e-3)`、A4-1 L58/A5-3 L62/A1-1 L97 + req-7 L130 narrative 精度升级、Source 字段扩展
3. 剩余 ticket-stale MEDIUM finding family：cycle-9 (A6a-2 L63 `f_threshold = 1/128` historical, src/ 已用 `1/(2·N_e)` 参数化 at `src/decompmoe/safeguards.py:34-36`，传染链已断) + cycle-12 (A8-2 L74 CV/凸包半径，已由 `d239f57` 2026-09-21 supersede annotation 关闭) + cycle-13 (A6b-1 L100 `N_e=64` dormant bug，已由 `f077be8` 关闭)
4. 当前 `openspec/specs/governance/spec.md` 有 `req-gov-1/2/3` 三个 Requirement，实测 `grep -nE '<a id="req-gov-[0-9]+"></a>'` 序列 = `[1, 2, 3]`；本次新增 Requirement 选 `req-gov-4`（实测 next-free），避免覆盖 `req-gov-2` (Ticket `(historical, ...)` supersede annotation pattern — 当前 spec.md L51，commit `d239f57` 引入)

## What Changes

- `CLAUDE.md` §8 末尾追加 1 段新引用块（约 12 行中文 + 英文 evidence ID），**保留原 2026-08-21 裁决 verbatim 不变**，仅追加。边界补充段明确 "advisory non-binding scope" vs "advisory ≠ 无影响" 的 operational 区分，并列出三传染通道 (MVPConfig 默认值直接抄 ticket / tests `assert == stale_value` LOCKS / reader-ticket-not-spec) + 监控义务 + 修复协议 (a)+(b)+(c) 三步
- `openspec/specs/governance/spec.md` 末尾追加 1 个 ADDED Requirement（**`req-gov-4` anchor**），4 条 obligations 形式化：(1) advisory scope 边界；(2) 三传染通道；(3) monitoring obligation；(4) drift remediation protocol (a)+(b)+(c)
- `wayfinder/spec.md` / `decompmoe-skeleton/spec.md` 不变；`src/decompmoe/` / `tests/` / `wayfinder/tickets/*.md` 全部不变（per `CLAUDE.md` §3 surgical + §7 Out of Scope）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `governance` (1 处 ADDED Requirement)：
  - **ADDED** Requirement "Ticket Advisory Boundary — Stale Contamination Monitoring"（`openspec/specs/governance/spec.md` 末尾，anchor `req-gov-4`）—— 形式化 `CLAUDE.md` §8 cycle-7 边界补充；Source 反链 `\`CLAUDE.md\`` §8（per `wayfinder/spec.md` req-34 L748 governance-origin reverse-link rule）

## Impact

- **Affected code**（无）：本 change 是 doc-level + spec-level 形式化，**0 文件 `src/` 改动**、**0 文件 `tests/` 改动**、**0 文件 ticket 改动**
- **Affected docs**（surgical 1 处）：`CLAUDE.md` §8 末尾追加 1 段新引用块（约 12 行）
- **Affected specs**（surgical 1 处）：`openspec/specs/governance/spec.md` 末尾追加 1 个 ADDED Requirement（约 30-50 行）
- **Affected APIs / dependencies**：无
- **Affected systems**：无（推理引擎实现代码已 out-of-scope per `CLAUDE.md` §7）
- **Risk**：
  - **Risk A**：`CLAUDE.md` §8 文字修订可能与既有裁决冲突。Mitigation：保留原 2026-08-21 裁决 verbatim 不变，仅追加新引用块（不修改、不删除原裁决）
  - **Risk B**：`req-gov-4` anchor 选择需实测 grep（per `CLAUDE.md` §6 第 8 条 spec anchor 100% 覆盖原则 + 我自身 agent memory lesson "Spec anchor 编号必须基于实测 grep"），避免与 `req-gov-1/2/3` 冲突。已实测确认序列 = `[1, 2, 3]`，`req-gov-4` 为 next-free
  - **Risk C**：`req-33 L678` / `req-7 L122` 等历史线号引用可能漂移。Mitigation：新 Requirement body 与 `Source:` 字段不引用任何线号（line-drift 抗性），仅引用 capability 路径与 commit SHA
  - **Risk D**：Windows Edit tool CRLF contamination（per agent memory "Edit tool on Windows can introduce CRLF in non-ASCII files"）。Mitigation：每个 Edit 后跑 byte-level 检查 `($bytes | Where-Object { $_ -eq 13 }).Count` 必须 0；`.gitattributes` `*.md text eol=lf` 是 commit-time safety net
  - **Risk E**：audit-verification loop 后续 cycle 可能对本 change 边界文字本身做复核（meta-meta-audit）。Mitigation：边界文字明确引用 audit-verification evidence（`commit adf41ef` 2026-09-19 + 剩余 cycle-9/12/13 family + 当前 spec 实测 grep），evidence 可独立验证

- **Source**（evidence 链）：本 change 由 audit-verification loop cycle-7 finding #1 axis-γ follow-up 段（`.audit/audit-verification.md` L581）显式触发
  - `commit adf41ef`（2026-09-19 21:12:30）：cycle-5/6/7 MEDIUM finding 4-file batch fix 已关闭（`fix(spec,ticket,code): close cycle-5/6/7 MEDIUM findings`）
  - 剩余 ticket-stale MEDIUM finding family：cycle-9 (A6a-2 L63, src/ 已参数化) + cycle-12 (A8-2 L74, `d239f57` 2026-09-21 关闭) + cycle-13 (A6b-1 L100, `f077be8` 关闭)
  - 当前 test 数量：**199 tests collected**（per `uv run pytest tests/ --collect-only -q`，2026-09-23 实测）

Co-Authored-By: Claude Code <noreply@anthropic.com>