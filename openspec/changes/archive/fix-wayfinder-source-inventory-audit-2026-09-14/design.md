## Context

See proposal.md - Why / What Changes / Fact-check results 三节。本节只补 design 层细节（audit 方法论 + 可复现验证流程）。

约束：
- 本 change 无 spec-level 行为变化（`.openspec.yaml` 已设 `skip_specs: true`）
- 本 change 不动 `openspec/specs/wayfinder/spec.md`、不动 lint script、不动 archive 资产
- 唯一资产新增：`openspec/changes/fix-wayfinder-source-inventory-audit-2026-09-14/{proposal,design,tasks}.md`

## Goals / Non-Goals

**Goals：**
1. 在本 change 留痕 2026-09-12 fact-check 的 32 处 Source 字段全量分类与偏差分析
2. 给出 archive 前 review 必须显式决议的 Decision Record（是否在旧 proposal 加勘误头注）
3. 提供 re-runnable 验证流程（任何后续 reviewer 可重跑同一脚本得到同一结果）

**Non-Goals：**
1. **不**修改 `openspec/specs/wayfinder/spec.md` 任何字符（包括 L577/L639 style drift）
2. **不**修改 `scripts/lint_no_source_field_drift.py`（rule 与 per-capability 表均冻结）
3. **不**修改任何 archived change 资产（除非 Decision Record 显式破例）
4. **不**修复原 inventory 的失误模式（仅记录失误本身，不改 producer）
5. **不**新增 / 修改任何 `wayfinder/tickets/*.md`（wayfinder arena 自 2026-08-21 裁决后非必改制品）

## Decisions

### Decision D1：审计方法 = 字符串分类 + 行号扫描

**选定方案**：
- 全量逐行扫描 `openspec/specs/wayfinder/spec.md`（683 行）
- 对每行 `startswith("**Source:**")` 的行做三态分类：
  - `pure_ticket` — 仅含 `wayfinder/tickets/`
  - `pure_change` — 仅含 `change <name> design.md`（lint 必报 violation）
  - `mixed` — 同时含两者（CLAUDE.md §3 显式允许）
- format drift 检测：
  - `(?<!\`)wayfinder/tickets/[A-Za-z0-9\-]+\.md(?!\`)` → 缺反引号
  - `line.rstrip().endswith(".")` → 行尾多 `.`
- 行号偏差 = `claimed_ln - nearest_actual_source_ln`（inventory 偏离真 Source 行的符号与幅度）

**替代方案（弃用）**：
- (a) 直接信 lint 脚本输出 → 不足，因为 lint 不分类（只查 `wayfinder/tickets/` 子串存在性）
- (b) AST 解析 spec.md → overkill，且 markdown 不是结构化语法
- (c) 抽样行扫描 → 不可证伪 inventory 偏差的精确幅度

### Decision D2：mixed 不是违规（per CLAUDE.md §3）

**论证链**：
1. CLAUDE.md §3 字面：`"每次 Spec 变更必须含 **Source:** 反链 ticket（wayfinder/tickets/<ID>.md 字面必备），允许附加 change Decision 反链"`
2. lint script `scripts/lint_no_source_field_drift.py` 第 56–60 行 `lint_file()`：违规判定 = `required not in line`，即只要 `wayfinder/tickets/` 子串在行内即通过；`change ...` 子串的有无不影响判定
3. 实测：15 处 mixed 行均含 `wayfinder/tickets/`，lint 全绿（`exit=0`）

**结论**：mixed 是合法格式，inventory 把 mixed 列为「违规」是误读规则。

### Decision D3：原 inventory 失误模式归因

**观察**：6 处 off-by 偏差单调向下（inventory 偏高 1–7 行），且偏差幅度递增（1 → 2 → 3 → 4 → 5 → 7）。

**假设**：inventory producer 在数 Source 行时按 `#### Scenario: ...` anchor 块的起始计行，而非按 `**Source:**` 行首计行。每错一次累加一段 Scenario body 的行数（典型 Scenario body 含 WHEN/THEN/AND 子句 5–10 行），所以偏差随 block 累积单调递增。

**支持证据**：
- L579 命中的是 Scenario 标题 `#### Scenario: perturbation output shape matches a single expert slot`
- L646 命中的是 Scenario 标题 `#### Scenario: same-event beta decay`
- L594 命中的是 Scenario body 内 `- **WHEN** the schedule transitions from Phase 3 to Phase 4 with \`β_{p3} = 16.0\``
- L609 命中的是 Scenario body 内 `- **THEN** \`‖∂logit/∂C‖₂ == 32.0\` within \`abs=1e-4\``
- L628 是空行（Scenario 间的分隔空行）

**未追查**：inventory producer 是否使用 grep / IDE / 手工计数（无证据，不猜）。

### Decision D4：corrigendum 决策留作 archive 前 review 显式决议

详见 proposal.md「Decision Record」。本设计仅说明流程：corrigendum 头注修改是 archive 资产变更（破例），需在 archive 前 review 由人决议（不是工具自动判断），决议结果落 `openspec/changes/fix-wayfinder-source-inventory-audit-2026-09-14/tasks.md` 的 §3 checkbox。

## Risks / Trade-offs

**[R1] 偏差分析可能误判 inventory producer 实际方法** → Mitigation：保留「未追查」一节，明确不归因到具体工具或 commit；归档后如 producer 自报方法，可补 tasks.md 附录。

**[R2] L577/L639 style drift 留作后续 change** → 风险：人审 review 可能要求本次顺手修；Mitigation：proposal 已显式声明「不在本 change 范围」，避免 reviewer 误解为遗漏。

**[R3] corrigendum Decision (a)/(b)/(c) 选错** → 风险：选 (b)/(c) 会改 archive 资产，违反「archive 不可变」仓库约定；Mitigation：本 design 与 proposal 均推荐 (a)，tasks §3 留显式 checkbox。

**[R4] 未来某次 `lint_no_source_field_drift.py` 改动可能让本 fact-check 不可复现** → 风险：脚本逻辑一变，结论可能不同；Mitigation：proposal 已嵌入 re-runnable 命令与 lint script 当前 commit 锚点（如未来 archive 后希望锚定，可在 archive 前补 git rev-parse HEAD 到 proposal 末注）。

## Migration Plan

本 change 无 deployment / rollback（纯 docs）。

**Archive 流程**：
1. archive 前 review 决议 proposal §「Decision Record」中 Decision 1（(a)/(b)/(c)）
2. 若决议 (a)：archive 不动 archive 资产，本 change 的 3 个 artifact 进 `openspec/changes/archive/`
3. 若决议 (b)：archive 同步在 `openspec/changes/archive/fix-wayfinder-spec-source-field-drift/proposal.md` 顶部加 `<!-- CORRIGENDUM 2026-09-14: ... -->` 头注
4. 若决议 (c)：archive 同步在 archive 的 proposal.md + design.md 都加头注
5. archive 前置条件（per CLAUDE.md §3）：`lint_no_dead_defensive.py` exit=0 + `lint_no_source_field_drift.py` exit=0（已实测全绿）

## Open Questions

无。所有歧义已在 proposal Decision Record 与本 design §Decisions 显式处理；reviewer 只需在 tasks §3 勾选 Decision 1 选项即可。

## Re-runnable verification

任何 reviewer 可重跑下列命令独立验证本 fact-check：

```bash
# 1. lint 验证（应输出 OK, 0 violations）
python scripts/lint_no_source_field_drift.py openspec/specs/wayfinder/spec.md

# 2. 全量分类（应输出 17 pure_ticket / 15 mixed / 0 pure_change / 0 NONE / TOTAL 32）
python -c "
import re
from pathlib import Path
lines = Path('openspec/specs/wayfinder/spec.md').read_text(encoding='utf-8').splitlines()
cats = {'pure_ticket': 0, 'pure_change': 0, 'mixed': 0, 'NONE': 0}
for line in lines:
    if line.startswith('**Source:**'):
        ht = 'wayfinder/tickets/' in line
        hc = bool(re.search(r'change\s+\S+\s+design\.md', line))
        if ht and hc: cats['mixed'] += 1
        elif hc: cats['pure_change'] += 1
        elif ht: cats['pure_ticket'] += 1
        else: cats['NONE'] += 1
for k, v in cats.items(): print(f'{k}: {v}')
print(f'TOTAL: {sum(cats.values())}')
"

# 3. 行号偏差验证（应输出 6 处 off-by：1/2/3/4/5/7）
# 见 proposal.md「Inventory 行号偏差表」
```

任何命令输出与本 fact-check 不一致 → 本 change 假设已破，请开新 change 复核（不要回头改本 archive）。

