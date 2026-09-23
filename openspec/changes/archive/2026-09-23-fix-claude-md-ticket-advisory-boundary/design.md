# Design

## Context

`.audit/audit-verification/audit-verification.md` L581 (cycle-7 audit-verification loop finding #1 axis-γ follow-up) 显式建议 "更新 CLAUDE.md §8 加一句 'ticket stale 仍可能传染 src/, 需以 cycle-6/7 模式监控'"。`CLAUDE.md` §8 当前裁决（2026-08-21）只声明 ticket advisory 性质，但**未明确** advisory scope vs operational impact 的区分，导致 audit-verification loop 在同源 ticket-stale MEDIUM finding 上反复做边际验证。cycle-5/6/7 MEDIUM finding 4-file batch fix 已由 `commit adf41ef`（2026-09-19 21:12:30）关闭，剩余 cycle-9/12/13 ticket-stale family 仍需 monitoring 框架守护。

## Goals / Non-Goals

**Goals:**

- 关闭 cycle-7 audit-verification L581 meta-洞察（process-level closure，不替代 cycle-5/6/7/9/12/13 各 finding 的 numerical fix）
- `CLAUDE.md` §8 末尾追加 1 段边界补充，**保留原 2026-08-21 裁决 verbatim 不变**（不重写、不删除原裁决）
- `openspec/specs/governance/spec.md` 末尾追加 1 个 ADDED Requirement（anchor `req-gov-4`，**实测 next-free**，避免覆盖 `req-gov-2` — 当前 Ticket `(historical, ...)` supersede annotation pattern meta Requirement）形式化：(1) advisory scope 边界; (2) 三传染通道 (MVPConfig / tests LOCKS / reader-ticket-not-spec); (3) monitoring obligation; (4) drift remediation protocol (a)+(b)+(c)
- spec delta 单源真相：governance Requirement 的 `**Source:**` 字段反链 `CLAUDE.md` §8（per `wayfinder/spec.md` req-34 L778-783 governance-origin reverse-link rule + CLAUDE.md §3 "Source 反链" lint 三项结构性检查）
- 现有 199 tests 全绿（per `uv run pytest tests/ --collect-only -q`，2026-09-23 实测；无 regression）
- 单 commit on `dev`（per 项目 git branch architecture §4）

**Non-Goals:**

- 不修复 cycle-9/12/13 ticket-stale 数值（这些 fix 是 ticket 端 supersede annotation + src/ 默认值清理 + tests `pytest.approx` 迁移，需各自 OpenSpec change，本 change 仅 process clarification）
- 不修复 `LOOPS.md` severity 框架 dormant bug 升级条款（已由 change `08-fix-loops-md-dormant-bug-framework` 的 `req-gov-3` 形式化关闭，本 change 不重复）
- 不引入 `tests/test_audit_verification_loop.py`（governance Requirement Scenario 实证 anchor 是 "future addition"，out of scope per `CLAUDE.md` §3 surgical）
- 不批量修复 audit-verification loop 其他 finding（cycle-12 finding 文字微调 "协方差矩阵" → "CV (凸包半径)" 等已在 `d239f57` 2026-09-21 关闭，cycle-13 dormant bug 已在 `f077be8` 关闭）
- 不重写 `CLAUDE.md` §8 整段（保留原 2026-08-21 裁决 verbatim，仅追加新引用块）

## Decisions

### Decision 1: `CLAUDE.md` §8 仅追加，不重写

**Choice**: 在原 2026-08-21 裁决引用块**末尾**追加第 2 个引用块，**保留**原裁决 verbatim 不变。

**Rationale**: `CLAUDE.md` §8 裁决有明确时间戳（2026-08-21）+ 文档级 audit trail 价值。重写整段会丢失原裁决历史，违反 `CLAUDE.md` §2 真相源层级（"CLAUDE.md 是项目级真相源；其裁决是累积的"）。**追加策略**让新引用块与原裁决共存：读者阅读 §8 时同时看到 (i) 2026-08-21 裁决的 "ticket advisory" 边界声明 + (ii) 2026-09-19 边界补充的 "advisory ≠ 无影响" operational 区分。时间戳明确（`2026-09-19`）让 audit trail 可追溯，文字 verbatim 引用 audit-verification evidence IDs (`commit adf41ef` 2026-09-19 + 剩余 cycle-9/12/13 family + 当前 spec 实测 grep) 而非 narrative，evidence 链可独立 cross-validate。

**Alternatives considered**:
- (a) 重写 `CLAUDE.md` §8 整段 —— 拒绝：丢失 2026-08-21 裁决历史，违反累积真相源语义
- (b) 在 §1/§2/§6 等其他段添加 process 条款 —— 拒绝：§8 是 "Wayfinder Arena Index"，boundary clarification 与 ticket/tickets/scope 主题一致，§8 是 natural location
- (c) 在新独立 § 段（如 §10）追加 —— 拒绝：scope 漂移到 `CLAUDE.md` 末尾，破坏 §1-§9 的现有结构

### Decision 2: `governance/spec.md` 新增 Requirement 而非 `wayfinder/spec.md`

**Choice**: 在 `openspec/specs/governance/spec.md` 末尾追加新 Requirement（anchor `req-gov-4`，实测 next-free），**不**在 `openspec/specs/wayfinder/spec.md` 用 `(historical, ...)` 硬贴。

**Rationale**: per `wayfinder/spec.md` req-34 L778-783 "governance-origin requirements trigger lint failure" Scenario：

> "any such requirement whose honest annotation cannot be written (because no A* ticket is its legitimate design predecessor) MUST be migrated to a separate governance capability (e.g. `openspec/specs/governance/spec.md`) before archive"

本 Requirement 的设计起源是 `CLAUDE.md` §8 修订（cycle-7 audit-verification meta-洞察），**无对应 ticket**（audit-verification 是 `.audit/` 而非 `wayfinder/tickets/`），故放 `governance/` 是 spec-lint 强制约束。

**Alternatives considered**:
- (a) 在 `wayfinder/spec.md` 用 `(historical, ...)` 硬贴 —— 拒绝：违反 req-34 governance-migration rule
- (b) 不形式化（仅 `CLAUDE.md` 修订）—— 拒绝：spec-level 形式化让 lint 守护 monitoring obligation 与 remediation protocol 是项目级价值
- (c) 在 `decompmoe-skeleton/spec.md` 形式化 —— 拒绝：skeleton capability 是 type stubs + 纯函数原语，不承载 governance 规则

### Decision 3: `req-gov-4` 而非 `req-gov-2` 或 `req-gov-3`（实测 next-free）

**Choice**: 新 Requirement anchor = `req-gov-4`。

**Rationale**: 实测 2026-09-23 `grep -nE '<a id="req-gov-[0-9]+"></a>' openspec/specs/governance/spec.md` 序列 = `[1, 2, 3]`，`req-gov-4` 为 next-free。**关键 anti-pattern 避免**：

1. 不能用 `req-gov-2`：现有 `req-gov-2`（当前 spec.md L51，commit `d239f57` 2026-09-21 引入）是 "Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application" documenting-only meta Requirement，且正文明文写 "would be `req-gov-N` *if* and when that planned change is archived" —— 现有 req-gov-2 已主动保留 anchor 选择权给本次 change
2. 不能用 `req-gov-3`：现有 `req-gov-3`（commit `d9cb0b0`）的 Source 字段明文写 "`req-gov-2` (Ticket `(historical, ...)` supersede annotation pattern — pre-existing meta Requirement, NOT modified by this delta; **`req-gov-3` chosen to avoid anchor collision**)" —— req-gov-3 设计时已主动避开 req-gov-2，本 change 必须延续此约定
3. 不能跳跃到 `req-gov-N+`：实测确认 next-free 必须是 `req-gov-4`

**Alternatives considered**:
- (a) 用 `req-gov-2` —— 拒绝：覆盖现有 documenting-only meta Requirement + 与 req-gov-3 的"避免冲突"约定冲突
- (b) 用 `req-gov-3` —— 拒绝：覆盖现有 Loop Severity Framework Gap Closure Requirement
- (c) 跳过中间用 `req-gov-5` —— 拒绝：违反"实测 next-free"原则，留下空洞

### Decision 4: line-drift 抗性 — 不引用任何线号

**Choice**: 新 Requirement body 与 `Source:` 字段**不引用任何 spec line number**（如 `req-7 L122` / `req-33 L678` / `req-13 L268` 等历史线号）。仅引用 capability 路径（如 `openspec/specs/wayfinder/spec.md`）+ commit SHA（如 `commit adf41ef`）+ test 路径（如 `tests/test_beta.py`）。

**Rationale**: `openspec/specs/wayfinder/spec.md` 自 2026-09-19 起经历多次 spec 同步提交（`adf41ef` + `229016f` + `d239f57` + `07c4ef7` + `d204846` 等），线号持续漂移。任何 line reference 在 archive 时都可能 stale。**capability 路径 + commit SHA + test 路径** 是 stable identifier，跨多次 spec 同步仍有效。

**Anti-pattern 避免**：本次 re-proposal 的事实基础里发现，前一版 draft 的事实错误（如 "spec L122 钉死 β_0=1.035060"、"req-33 L678 治理条款"、"req-13 L268" 等）正是基于 pre-sync 线号引用，导致 fact-verification 时全部 stale。本次修正为 line-drift-resistant。

**Alternatives considered**:
- (a) 引用当前 L###（如 req-7 L130 / req-34 L744+）—— 拒绝：spec 同步后立即 stale
- (b) 引用 `<historical, L###>` 标记 + 同步日期 —— 拒绝：增加 spec delta 复杂度，且仍需 future 读者 grep 当前 L### 才能定位
- (c) 不引用线号（本次选择）—— 接受：spec 路径 + commit SHA + test 路径足够 audit trail

### Decision 5: Source 反链 backtick-wrapped + governance rule

**Choice**: 新 Requirement 的 `**Source:**` 字段 verbatim：`**Source:** \`CLAUDE.md\` §8 (cycle-7 audit-verification L581 meta-洞察 boundary clarification, amended by this change)`

**Rationale**: per `wayfinder/spec.md` req-34 L748 governance-origin reverse-link rule：

> "`openspec/specs/governance/spec.md` — primary reverse-link MUST be a backtick-wrapped `CLAUDE.md` reference (governance-origin lineage)"

本 Requirement 主反链 `CLAUDE.md` §8 用 backtick-wrapped，符合 req-33 + req-34 lint 规则 + `CLAUDE.md` §3 "Source 反链" 三项结构性检查（① 子串存在 ② backtick-wrapped ③ 主反链必须是第一个 top-level item）。

**Alternatives considered**:
- (a) 反链 `change fix-claude-md-ticket-advisory-boundary design.md (Decision 1)` 而非 `CLAUDE.md` —— 拒绝：governance capability 的 Source 反链规则（per req-34 + `CLAUDE.md` §3）是 "必须含 `CLAUDE.md` literal backtick 反链"，change-name 反链是 wayfinder/decompmoe-skeleton capability 的 pattern
- (b) 双反链 `\`CLAUDE.md\` §8, \`change audit-verification meta-advisory\`` —— 拒绝：本 change 不是 wayfinder ticket 设计起源，change-name 反链不适用 governance capability
- (c) 不写 `Source:` 字段 —— 拒绝：违反 req-34 lint 强制要求

### Decision 6: 测试 anchor out of scope

**Choice**: governance Requirement 末尾 Scenario 实证 anchor **不**在本 change 引入 `tests/test_audit_verification_loop.py`。

**Rationale**:
- 本 change 是 process clarification，不是 test addition（per `CLAUDE.md` §3 surgical + proposal "What Changes" 段）
- governance spec 已有的 `req-gov-1/2/3` Scenario 都引用既有 tests（`tests/test_config.py::test_total_param_estimate` 等），新 Requirement 引用未来 `tests/test_audit_verification_loop.py` 是不诚实（test 不存在）
- future test addition 应作为独立 change 处理

**Alternatives considered**:
- (a) 本 change 同时引入 `tests/test_audit_verification_loop.py` —— 拒绝：scope 膨胀，违反 §3 surgical
- (b) Scenario 引用 `.audit/audit-verification.md` 既有 verbatim 段（如 L530-531）—— 可接受备选，但 governance spec convention 是引用 test path 而非 narrative 段
- (c) Scenario 用 commit SHA 引用历史 evidence（本次选择）：更稳定、跨 spec 同步仍有效

## Risks / Trade-offs

- **[Risk 1]** `CLAUDE.md` §8 文字修订可能与既有裁决语义冲突 —— **Mitigation**：保留原 2026-08-21 裁决 verbatim 不变，仅追加新引用块
- **[Risk 2]** governance Requirement 可能与 `req-gov-1` (Test Guard Precision for Closed-Form Numerical Claims) 数值约束规则冲突 —— **Mitigation**：本 Requirement 不涉及具体数值闭式（无 `pytest.approx(..., abs=...)` 强制断言），仅声明 monitoring obligation + remediation protocol，`req-gov-1` 第 4 条的 `f"actual={...}"` 约束不适用
- **[Risk 3]** `req-gov-4` anchor 选择可能仍与未来 change 冲突 —— **Mitigation**：实测 next-free + 引用现有 `req-gov-2` 正文的 `req-gov-N` placeholder 措辞 + 引用 `req-gov-3` 的 "avoid anchor collision" 注释，三重防错
- **[Risk 4]** line-drift 抗性可能让 audit trail 模糊化 —— **Mitigation**：用 commit SHA + capability 路径 + test 路径替代线号，audit trail 反而更强（commit SHA 永久锚定）
- **[Risk 5]** Windows Edit tool CRLF contamination —— **Mitigation**：`CLAUDE.md` Edit 后跑 byte-level 检查 `($bytes | Where-Object { $_ -eq 13 }).Count` 必须 0；`.gitattributes` `*.md text eol=lf` 是 commit-time safety net
- **[Risk 6]** audit-verification loop 后续 cycle 可能对本 change 边界文字本身做复核（meta-meta-audit）—— **Mitigation**：边界文字明确引用 audit-verification evidence (`commit adf41ef` 2026-09-19 + 剩余 cycle-9/12/13 family) 而非 narrative，evidence 可独立验证
- **[Risk 7]** cycle-5/6/7 已由 `adf41ef` 关闭，本 change 文字若仍描述其为待办会误导 reader —— **Mitigation**：本 change 文字明确区分 "已关闭" (adf41ef 2026-09-19) vs "remaining" (cycle-9/12/13)，让 reader 看到 current state

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical doc-level + spec-level 形式化。实施步骤：

1. **`CLAUDE.md` §8 修订**：Edit `CLAUDE.md` §8 末尾（原 2026-08-21 裁决引用块后）追加 1 段新引用块（约 12 行中文 + 英文 evidence ID）
2. **`openspec/specs/governance/spec.md` 形式化**：Edit `openspec/specs/governance/spec.md` 末尾追加 1 个 ADDED Requirement（anchor `req-gov-4`，约 30-50 行）
3. **验证**（per `CLAUDE.md` §3 `/opsx:archive` 前置条件）：`python scripts/lint_no_dead_defensive.py` + `python scripts/lint_no_source_field_drift.py` 全 exit 0
4. **测试**：`uv run pytest tests/ -v` 全绿（既有 199 tests，无 regression）
5. **LF 校验**：每个 Edit 后 byte-level 检查 `($bytes | Where-Object { $_ -eq 13 }).Count` 必须 0
6. **不变性 spot-check**：`git diff --stat src/ tests/ wayfinder/tickets/ openspec/specs/{wayfinder,decompmoe-skeleton}/spec.md` 应全 0 改动
7. **单 commit on `dev`**：`process(claude): CLAUDE.md §8 boundary clarification (cycle-7 audit-verification meta-advisory)` + Co-Authored-By trailer

## Open Questions

- **Future test addition**：governance Requirement 的 Scenario 实证 anchor (`tests/test_audit_verification_loop.py`) 是 "future addition"。Open Question：是否在后续 audit cycle 引入该 test？建议**独立 change**处理，本 change 不覆盖
- **剩余 ticket-stale family 批量修复**：cycle-9/12/13 各 finding 的 4-file batch fix（per audit-verification verify-9 follow-up "选项 C"）需独立 OpenSpec change。本 change 仅 process clarification，不替代
- **meta-meta-audit**：audit-verification loop 后续 cycle 可能对本 change 边界文字本身做复核。Open Question：是否需要在 boundary 文字中预留 "本边界声明可被后续 audit cycle 复核与修订" 元条款？本 change 选择**不预留**（保持 boundary 文字简洁；如需修订按 (a) 单行 Edit + git commit pattern 处理）

Co-Authored-By: Claude Code <noreply@anthropic.com>