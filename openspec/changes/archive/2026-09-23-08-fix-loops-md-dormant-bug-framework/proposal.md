# Proposal

## Why

`LOOPS.md` severity 框架在两类过程性场景下失灵：(a) **dormant bug**（当前 0 active impact 但 latent risk × trigger probability 高）的 proactive risk 没有升级条款（meta-08，cycle-13 finding 1 即典型）；(b) **audit self-correction**——audit-verification axis-γ 复核倾向"默认 MEDIUM"惯性，但 finding 文本已显式分级（"低危" → LOW、"正面记录" → INFO）的实例被误标（meta-06，2/24 = 8.3% 误标率）。

本次重做相对 `.audit/audit-verification/opsx-changes/08-fix-loops-md-dormant-bug-framework/` 原 planning 草案的关键修正：(1) **anchor 编号改用 `req-gov-3`**——避开当前 `req-gov-2` 已被占用的 "Ticket `(historical, ...)` supersede annotation pattern" Requirement；(2) **proposal 自带 spec.md 制品补 anchor**（per CLAUDE.md §6 第 9 条 anchor 100% 覆盖规则）；(3) **LOOPS.md 入库路径明确化**——本 change 第一步先把 LOOPS.md 从 untracked 状态 commit 进 git，后续 surgical Edit 才有稳定锚点。

## What Changes

- **governance spec delta**（ADDED Requirement）：在 `openspec/specs/governance/spec.md` 末尾**新增** `<a id="req-gov-3"></a>` Requirement "Loop Severity Framework Gap Closure"，钉死：(a) dormant bug 升级触发器——`latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}` ⇒ severity 升至 `HIGH dormant-bug`；(b) audit 自我校核——axis-γ 复核前**必须**先 grep finding 文本 against `{"低危", "正面记录", "正面alignment", "不构成硬冲突", "phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}`，匹配则采用 finding 自身分级。每条配 Scenario 验证（retro-application 至 cycle-5/13/17/24）。
- **LOOPS.md 入库 commit**：把当前 untracked 的 `LOOPS.md` 加入 git（独立 commit `chore(audit): import LOOPS.md to version control`），使其成为稳定可锚定文件。
- **LOOPS.md surgical edit（4 处）**：
  - L118-122（audit-verification loop "Cycle 单元"段 axis-γ 子段）：新增 dormant bug 升级条款 + "Reading finding text first rule" 子段
  - L64-69（spec-math audit loop "Finding 升格路径"段）：新增 dormant bug 升级条款引用
  - L178-194（"修改记录"段末尾）：追加 2026-09-23 fix-loops-md-dormant-bug-framework 条目
  - 不动其他任何 LOOPS.md 内容（CLAUDE.md §3 surgical）
- **lint gate 双跑**：`scripts/lint_no_source_field_drift.py` + `scripts/lint_no_dead_defensive.py` 必须 `exit=0`
- **不引入 pytest 数值断言**：本 change 是 process-level 规则无 numerical claim（dormant bug 升级触发器是定性枚举风险函数，不是 closed-form 数值算式）；规则守护靠 governance spec Scenario 钉死 + 下次 audit-verification loop 跑时遵守

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `governance`：新增 1 处 ADDED Requirement `req-gov-3` "Loop Severity Framework Gap Closure"（governance 起源，per `CLAUDE.md` §6 第 7 + wayfinder req-34 "governance-origin requirements trigger lint failure" Scenario 强制 governance-migration）

> **req-gov-3 编号依据**：当前 `governance/spec.md` 已有 `req-gov-1`（Test Guard Precision for Closed-Form Numerical Claims）+ `req-gov-2`（Ticket `(historical, ...)` supersede annotation pattern——documenting-only meta Requirement）。本 change 不覆盖既有 req-gov-2，新增 Requirement 按现有 req-gov-N 递增编号规则使用 `req-gov-3`，避免与 req-gov-2 内容冲突。

## Impact

- **Affected code**：无（LOOPS.md 是 process 文档；code-level 与本 change 无关）
- **Affected tests**：无（LOOPS.md 规则守护靠下次 loop 跑时遵守；process-level 规则无 numerical claim，无需 pytest.approx / bare == 守护——per CLAUDE.md §6 第 8 条"sentinel closed-form constant must directly verify"原则只适用于含具体数值的算式）
- **Affected APIs / dependencies**：无
- **Affected specs**：`openspec/specs/governance/spec.md` 新增 1 处 ADDED Requirement（含 2 个 Scenario）
- **Affected process docs**（surgical Edit per CLAUDE.md §3）：
  - `LOOPS.md` L64-69（Finding 升格路径段）
  - `LOOPS.md` L118-122（audit-verification loop axis-γ 子段）
  - `LOOPS.md` §"修改记录"末尾
  - `LOOPS.md` 入库 commit（独立 chore commit，先于 spec delta）
- **Risk**：
  - **req-gov-2 占用误读**：原 planning 草案声称填 `req-gov-2`，与现有 `req-gov-2` 冲突。Mitigation：本 change 改用 `req-gov-3`，理由写进 proposal "Capabilities" 段
  - **LOOPS.md 入库 commit 与 surgical edit 的耦合**：LOOPS.md 入库前 surgical edit 没有 git 锚点。Mitigation：split 成两个 commit——(1) `chore(audit): import LOOPS.md to version control` (纯入库，无内容变更)；(2) `fix(governance+LOOPS): close meta-06 + meta-08` (surgical edit)
  - **dormant bug 升级条款的 cycle-13 finding 1 retroactive 应用**：cycle-13 finding 1 当前 MEDIUM borderline，按新规则应升 HIGH dormant-bug。Mitigation：本 change **不重写已 archive 的 verdict**（CLAUDE.md §3 surgical 原则），仅 future finding 遵守新规则
  - **audit 自我校核的 axis-γ 复核周期变长**：需先 grep finding 自身文本。Mitigation：复盘 cycle-1 verify-24 + cycle-17 verify-21 2 次实证，单 cycle 增加约 5 行 grep + 1 行 severity 决策，scope 增量极小；长期降低误标率（meta-06 8.3% → 接近 0%）节省的审计工作量远超单 cycle 增加成本
  - **CLAUDE.md §2 真相源层级**：本 change 把过程规则放在 `governance/spec.md`（spec > 文档）+ `LOOPS.md`（loop 实例引用）双向落地，遵守 spec > doc > code 层级
- **Source**：
  - meta-06：`.audit/audit-verification/audit-verification.md` L1832（2/24 = 8.3% 误标率）+ L1837（meta-发现 #7 severity 误标 pattern）+ L2300-2309（9 meta-发现清单 #6 severity 误标 pattern）
  - meta-08：`.audit/audit-verification/audit-verification.md` L1306-1359（cycle-13 dormant bug 维度评估 + L1358-1359 "建议 LOOPS.md 修订" 原话）+ L2300-2309（9 meta-发现清单 #8 dormant bug）
  - cycle-17 INFO 误标：L1534-1564（verify-21 evidence）
  - cycle-1 LOW 误标：L1795-1833（verify-24 evidence）
  - cycle-5 LOW × LOW no-op boundary：L1349（维度评估表 cycle-5 row）
  - wayfinder spec.md req-34：L742-778（Source Field Format Invariant + governance-origin requirements trigger lint failure Scenario）