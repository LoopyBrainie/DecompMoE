## Why

Archived OpenSpec change `fix-wayfinder-spec-source-field-drift` 在其 `proposal.md` 中声称 `openspec/specs/wayfinder/spec.md` 有 **7 处 Source 字段违规**（6 处 pure change + 1 处 pure CLAUDE.md/test/archive 引用）。2026-09-12 的独立 audit 用同一 lint 脚本 `scripts/lint_no_source_field_drift.py` 跑 spec.md 输出 `OK, 0 violations`，并对原文逐行（L1–L683）扫描得到完全不同的清单：

- 实际 `**Source:**` 字段数 = **32**（不是 inventory 隐含的 33+）
- `pure_change` = **0**（inventory 声称 8，**8/8 全错**——6 实为 mixed，2 不是 Source 行）
- `mixed` = **15**（inventory 声称 7，**漏报 6 处**，且 mixed 本身是 CLAUDE.md §3 显式允许的合法格式）
- format drift = **2**（L577/L639：缺反引号 + 行尾多 `.`，inventory 此处分类正确但本质仍属 mixed 行）

原始 inventory 在 **分类、行号、遗漏** 三处存在结构性偏差。本次 change 不回头改 archived `proposal.md` 正文（archive 是不可变历史记录），改以新 change 形式留痕；并就「是否在旧 proposal 加勘误头注」做显式 Decision Record，由 archive 前 review 决议。

**为什么是现在**：2026-09-12 完成的 `2026-09-12-migrate-l678-source` archive 已将 req-33 移出 `wayfinder` capability 并把 lint script 接入 archive gate；新 gate 上线后任何 wayfinder-spec.md 的 Source 字段编辑都会被自动拦截。本次 audit 是新 gate 上线后的第一次 post-archive independent re-verification（per CLAUDE.md §3「Post-archive 独立复核」约定），偏差发现 = 偏差已留痕。

## What Changes

- **写入事实清单**：本 proposal.md「Fact-check results (2026-09-12)」一节记录 32 处 Source 字段全量分类 + 与原 inventory 的逐行偏差表。
- **不修改 `openspec/specs/wayfinder/spec.md`**：lint 全绿（`exit=0, 0 violations`），除 L577/L639 两处 style drift 外无任何 spec-level 违规；style drift 属于人审可见但 lint 不报，**不在本 change 的 audit 目标范围**（如需修补，留作后续 change；本 change 不绑 spec edit）。
- **不修改 archive 历史**：`openspec/changes/archive/fix-wayfinder-spec-source-field-drift/{proposal,design,tasks,specs}.md` 保持原样。
- **Decision Record**（见本文末）：3 个候选动作（不加勘误 / 在旧 proposal 加头注 / 在旧 proposal + design 都加头注），由 archive 前 review 显式决议。
- **新增 `openspec/changes/fix-wayfinder-source-inventory-audit-2026-09-14/`**：proposal.md + design.md + tasks.md 共 3 个 artifact（specs/ 因 `skip_specs: true` 不存在）。

**BREAKING**：无。纯文档 / audit 闭环，无 API / 接口 / spec 语义变化。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。

> 本 change 是 pure docs / audit（无 spec-level 行为变化），按 `openspec validate` 规则 `.openspec.yaml` 已设 `skip_specs: true`，不要求 spec delta 文件。

## Impact

| 资产 | 改动 |
|---|---|
| `openspec/changes/fix-wayfinder-source-inventory-audit-2026-09-14/{proposal,design,tasks}.md` | 新增（3 个 artifact） |
| `openspec/changes/fix-wayfinder-source-inventory-audit-2026-09-14/.openspec.yaml` | 新增（含 `skip_specs: true`） |
| `openspec/specs/wayfinder/spec.md` | **零改动** |
| `scripts/lint_no_source_field_drift.py` | **零改动** |
| `openspec/changes/archive/fix-wayfinder-spec-source-field-drift/{proposal,design}.md` | **零改动**（除非 Decision Record 显式决议加勘误头注） |
| 代码层（`src/decompmoe/`） | 零影响 |
| 测试层（`tests/`） | 零影响 |
| Archive gate 行为 | 零变化（lint 仍 `exit=0`） |

## Post-archive human checklist (不在 tasks.md §4，因为 archive 后该文件变不可写)

archive 命令 `openspec archive fix-wayfinder-source-inventory-audit-2026-09-14 --skip-specs --yes` 完成后，archiver / reviewer 需手动跑以下 3 步（非 openspec apply 跟踪，纯人工验证）：

1. **`openspec list` 不再显示该 change**：确认目录已移出 `openspec/changes/`（应在 `openspec/changes/archive/` 下）；命令：`openspec list`
2. **git 提交可见**：命令：`git log --oneline -- openspec/changes/archive/fix-wayfinder-source-inventory-audit-2026-09-14/` 应至少含 archive commit
3. **后续 follow-up 独立 change**：如需修 L577/L639 style drift，**新开 change**（建议名 `fix-wayfinder-spec-l577-l639-style-drift-2026-09-14` 或类似），**禁止**回头 bundle 到本 archive

> Decision 1 = (a)，故无 corrigendum apply 步骤；本 checklist 不含「验证 corrigendum 头注可见」项。

---

## Fact-check results (2026-09-12)

### 全量分类（对 spec.md L1–L683 全文扫描）

| 分类 | 数量 | 行号 |
|---|---|---|
| `pure_ticket` | **17** | L14, L26, L38, L54, L66, L128, L144, L160, L176, L231, L295, L307, L319, L335, L364, L451, L499 |
| `mixed`（clean） | **13** | L95, L202, L251, L275, L396, L463, L479, L525, L543, L557, L591, L605, L623 |
| `mixed` + drift | **2** | L577, L639（缺反引号 + 行尾多 `.`） |
| `pure_change` | **0** | — |
| `NONE`（lint 违规） | **0** | — |
| **TOTAL** | **32** | |

> 「mixed」指同一 `**Source:**` 行内同时含主反链 `wayfinder/tickets/<ID>.md` 与次反链 `change <name> design.md (Decision N)`，按 CLAUDE.md §3 字面属合法格式，不触发 `lint_no_source_field_drift.py` 任何 violation。

### 与原 inventory 的偏差汇总

| Inventory 桶 | 原声称 | 实测 | 偏差结论 |
|---|---|---|---|
| `pure_change` | 8 处 | 0 处 | **8/8 错**（6 处实为 mixed，2 处不是 Source 行而是 Scenario 标题 / WHEN-THEN 子句） |
| `mixed` | 7 处 | 15 处（13 clean + 2 drift） | **行号 7/7 对，分类 6 处漏报** |
| `format_drift` | 2 处 | 2 处 | **2/2 对**（drift 类型描述正确） |
| **合计声称违规** | **17** | **0 lint + 2 style drift** | — |

### Inventory 行号偏差表（6 处 off-by 单调向下）

| Inventory 声称 | 真 Source 行 | 偏差 | 真 Source 内容片段 |
|---|---|---|---|
| L558 | L557 | -1 | `**Source:** \`wayfinder/tickets/A6b-1.md\` (historical, A6b-1 phase-ramp design intent (1.0→4.0 Phase 2, 4.0→16.0 Phase 3); ...), change ... Decision 3)` |
| L579 | L577 | -2 | `**Source:** wayfinder/tickets/A6a-2.md (initial A6a-2 design intent); change ... Decision 4 ...)`（mixed+drift 行） |
| L594 | L591 | -3 | `**Source:** \`wayfinder/tickets/A6b-2.md\` (historical, ...), change ... Decision 2)` |
| L609 | L605 | -4 | `**Source:** \`wayfinder/tickets/A4-1.md\` (historical, ...), change ... Decision 6)` |
| L628 | L623 | -5 | `**Source:** \`wayfinder/tickets/A2-2.md\` (historical, ...), \`wayfinder/tickets/A4-2.md\` (historical, ...), change ... Decision 7)` |
| L646 | L639 | -7 | `**Source:** wayfinder/tickets/A6a-2.md (initial A6a-2 design intent); change ... Decision 4 ...)`（mixed+drift 行） |

> 偏差方向单调向下（inventory 偏高 1–7 行），与 inventory 漏报 6 处真 mixed 行（漏报的 6 行恰好是 L525/543/557/591/605/623）的现象共同指向同一失误模式：**inventory 疑似按 anchor 块（`#### Scenario: ...` 起始）计行而非按 `**Source:**` 行首计行**，且漏算了 block 内 Scenario body 的累计行数。L579/L646 命中的是 Scenario 标题行，本身印证此假设。

### Lint 验证（re-runnable 复现命令）

```bash
$ python scripts/lint_no_source_field_drift.py openspec/specs/wayfinder/spec.md
lint_no_source_field_drift: OK (1 file(s) scanned, no violations)
```

> 0 violations 与本 audit 的「pure_change=0 / NONE=0」统计一致。15 处 mixed 行均含 `wayfinder/tickets/` 主反链字面，满足 lint hard check。

### 残留 style drift 详情（人审可见 / lint 不报）

| 行号 | drift 类型 | 行内容片段 |
|---|---|---|
| L577 | 缺反引号 + 行尾多 `.` | `**Source:** wayfinder/tickets/A6a-2.md (initial A6a-2 design intent); change \`fix-math-consistency-audit-2026-08\` design.md (Decision 4 ...); signature mirrors \`src/decompmoe/safeguards.py:105-133\` ... .` |
| L639 | 缺反引号 + 行尾多 `.` | 同 L577（同一段 `perturbation output shape matches a single expert slot` Requirement 的 Source 副本） |

> 这 2 处仍属 mixed 行（双反链齐全），drift 是叠加的 style 问题，不影响 lint。修补需后续独立 change，本 change 不绑。

---

## Decision Record (待 review 决议)

### Decision 1：是否在旧 proposal.md 加勘误头注

| 选项 | 推荐 | 备注 |
|---|---|---|
| **(a) 不加，旧 proposal.md 保持原样** | ✅ **推荐** | archive 是不可变历史；事实清单已在本 change proposal 留痕；下游 reader 通过 `git log` / `openspec list` 可追溯 |
| (b) 在 `openspec/changes/archive/fix-wayfinder-spec-source-field-drift/proposal.md` 顶部加 `<!-- CORRIGENDUM 2026-09-14: ... -->` 头注 | — | 仅当 review 要求显式标注偏差时选；会修改 archive 资产，违反「archive 不可变」约定，需先决议是否破例 |
| (c) 同时在 `openspec/changes/archive/fix-wayfinder-spec-source-field-drift/design.md` 加头注 | — | 与 (b) 配对；同 (b) 的破例约束 |

> **本 change 的立场**：选 (a)。理由——「archive 是历史记录」是仓库治理约定（CLAUDE.md §9「9 changes archived」+ 你本人 2026-09-14 回复明示）；新 change 形式留痕即满足「更正可追溯」需求；改 archive 等于历史被覆盖，与 wayfinder arena 的「wayfinder 不再是必改制品（2026-08-21 裁决）」精神相悖。

---

## Source

本次 audit 自身的 `**Source:**` 反链：因本 change 不改 spec.md（无 spec-level 行为变化），无需追加 `**Source:**` 到任何 capability 的 spec 文件——但本 change 的设计 lineage 留痕如下，供 archive 后追溯：

- `wayfinder/tickets/A4-2.md` — 决定「`w_i` 彻底剔除，混合权重 = Softmax 概率 `p_i`」，是 CLAUDE.md §3 显式允许 `change ... design.md (Decision N)` 次反链的源头
- `wayfinder/tickets/A5-3.md` — 决定「专家结构 + 超参」命名，与 L543/L623 Source 行的 ticket 选择同源
- `openspec/changes/2026-09-12-migrate-l678-source/design.md` (Decision 1) — 决定「任何 governance-origin Requirement 必须迁移到独立 capability，不与 wayfinder 共存」；本次 audit 不动 governance，呼应此决策

