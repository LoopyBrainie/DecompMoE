## Why

`openspec/specs/wayfinder/spec.md` 当前 33 个 `**Source:**` 字段中,7 行未含 `wayfinder/tickets/` 字面(6 处 pure change + 1 处 pure CLAUDE.md/test/archive 引用),与 `CLAUDE.md` §2 rule 3「`Source:` 字段反链到 `wayfinder/tickets/*.md`」及 §3「每次 Spec 变更必须含 `**Source:**` 反链 ticket」字面抵触。根因是 2026-08-21 §8 裁决(OpenSpec 唯一真相源,wayfinder ticket 仅作历史决策记录)之后,治理工具未跟上,导致后续 archived change(`fix-openspec-doc-bugs`、`fix-math-consistency-audit-2026-08`、`tighten-closed-form-eq-integer-checks`)的 design.md 反链被批量注入 spec 而无 ticket 兜底。此漂移未在 archive 时刻被捕获,因为 `scripts/lint_no_dead_defensive.py` 只覆盖 dead-defensive anti-pattern,不覆盖 Source 字段格式。

## What Changes

- **修补 `openspec/specs/wayfinder/spec.md` 中 6 处 pure change Source**(L525/L543/L558/L594/L609/L628):每行配 ticket 反链并采用 L251 已有的 `(historical, <原值>; superseded by <change> Decision N)` 标注格式;annotation 必须诚实(基于 audit 后的真实设计先驱,非事后追认)。
- **L678 留 pure CLAUDE.md/test/archive 引用**:该 Req 是「Test Guard Precision for Closed-Form Numerical Claims」,其设计先驱是 `CLAUDE.md` §6 第 8 条(经 `bec147d` + `83a0503` 两个 commit 修订),非任何 `wayfinder/tickets/*.md`。lint 落地后将使 L678 在 archive 时触发失败,逼迫后人显式决定其历史 origin(要么配 A* ticket 并诚实标注,要么重构至 `openspec/specs/governance/spec.md` 新 capability)——**此失败是有意的设计信号,不是被忽略的 bug**。
- **`CLAUDE.md` §2 L19 + §3 L31 措辞微调**:保留「必须含 ticket」字面,允许附加 `change <name> design.md (Decision N)` 反链作为补充;统一 `(historical, <原值>; superseded by <change> Decision N)` 标注语法。
- **新增 `scripts/lint_no_source_field_drift.py`**:独立脚本(不污染 db14222 的 `JUSTIFIED_EXEMPTIONS` 注册表语义),按纯字符串规则 `**Source:**` 行必须含 `wayfinder/tickets/` 字面。零豁免,与文件内容同寿(不依赖行号)。
- **挂入 archive 前置条件**:`CLAUDE.md` §3 现有「lint gate 必须 `exit=0`」条目扩展为同时跑 `lint_no_dead_defensive.py` 与 `lint_no_source_field_drift.py`。

不修改 spec.md 内 Req/Semantics 的具体内容(行为不变),仅修补 Source 字段格式 + 治理工具。**BREAKING**:无(纯格式修正与治理硬化,无 API/接口/语义变化)。

## Capabilities

### New Capabilities

无(本 change 不引入新 capability;仅治理工具与 spec 字段格式修正)。

### Modified Capabilities

- `wayfinder`:修补 6 处 Source 字段格式(L525/L543/L558/L594/L609/L628,详见 `tasks.md` §2.1–§2.6);L678 留待 lint 失败后由后续 change 闭环(本 change 不修 L678,见 `tasks.md` §2.7)。

## Impact

- `openspec/specs/wayfinder/spec.md`:6 行 Source 字段文本修补(L525/L543/L558/L594/L609/L628)。
- `CLAUDE.md`:§2 L19 + §3 L31 措辞微调(共 ~6 行)。
- `scripts/lint_no_source_field_drift.py`:新文件,预计 ~80 行(纯字符串 grep,零豁免注册表,exit code 与 db14222 风格一致)。**informational-only**(见 docstring `KNOWN_OPEN_VIOLATIONS` 节):不接入 `/opsx:archive` 前置条件,等 L678 follow-up 闭环后原子化接线。
- `openspec/changes/archive/` 流程:**本次不扩展** lint 前置条件；19543eb 的 archive 门禁保持单脚本状态。
- 代码层:零影响(无 `src/decompmoe/` 改动)。
- 测试层:零影响(无 `tests/` 改动)。

## Open Follow-ups

### `migrate-l678-source` — 闭环 L678 governance-origin Source line

**背景**:本次 apply 阶段 discover L678(`Test Guard Precision for Closed-Form Numerical Claims`)的 design lineage 源自 `CLAUDE.md` §6 第 8 条(`bec147d` + `83a0503` 两个 commit 修订),不是任何 `wayfinder/tickets/*.md` ticket。`scripts/lint_no_source_field_drift.py` 对其仍报 violation(exit=1,唯一一条),informational-only 模式允许本次 change archive,但不接入 gate。

**强制决策要求**:follow-up change `migrate-l678-source` 必须在 `proposal.md` 中包含 **2.7 决策记录**(Decision Record),从以下 4 个候选选项中**显式选定 1 个并写理由**(不允许"选 a 或 b 后续再说"):

- **(a) 拆 capability 迁移**:把 L678 从 `openspec/specs/wayfinder/spec.md` 移到新建 `openspec/specs/governance/spec.md`,新 capability 内的 Source 反链可指向 governance lineage (CLAUDE.md 修订 commit + 后续变更)。**推荐选项**——与设计 Decision 4 一致,字面承认 governance lineage 是一等公民。
- **(b) 强配 ticket + 诚实 `(historical, ...)` 标注**:给 L678 配 `wayfinder/tickets/A8-3.md` 或 `WF-1.md` 并写明 "test precision guard" 与 ticket 的弱连接(及 connection rationale)。接受 WEAK 标注(类比本 change §2.3/§2.6 的处理),不拆 capability。
- **(c) 重写 ticket 反向适配**:为 L678 撰写新 ticket `A?-N.md`(归属 arena 待定,需 wayfinder 流程先 claim),然后 L678 Source 反链新 ticket。**不推荐**——CLAUDE.md §6 第 6 条禁止重写 wayfinder ticket 来调和 spec 与 ticket 不一致;新 ticket 是创建不是重写,但本质仍是用 ticket 掩盖 governance lineage 的真源,违反 A3 决策精神。
- **(d) 接受永久 informational-only**:把 L678 永久留在 lint 违规表,CLAUDE.md §3 lint gate bullet 也永久不接 `lint_no_source_field_drift.py`。**不推荐**——退化为"装了锁不上门",违反本 change 闭环要求。

**强制同步接线**:follow-up change 完成 L678 解决后,**同一 change 内**必须:

1. (若选 a 或 b)重跑 `python scripts/lint_no_source_field_drift.py` 验证 exit=0;
2. 修改 `CLAUDE.md` §3 lint gate bullet,把 `python scripts/lint_no_source_field_drift.py` 加入 archive 前置条件;
3. 同一 commit 删除 `scripts/lint_no_source_field_drift.py` docstring 中的 `KNOWN_OPEN_VIOLATIONS` 节(已无 known violation)。

**不允许**把"L678 解决"和"gate 接线"拆成两个独立 change——中间态(脚本存在但 gate 未接)会重蹈本 change 闭环前的覆辙,CLAUDE.md §3 bullet 与脚本行为的对应关系会再次漂移。

## 验证语义(修订后)

本 change apply 完成后预期签名(供任何后续手动跑脚本时参考):
- `python scripts/lint_no_source_field_drift.py` → exit=1,**恰好 1 violation on L678**;
- 任何**其他**signature(0/33 PASS、2+ violations、新出现 FAIL 行)即视为 regression,需立即调查。

接入 archive 前置条件是 follow-up change 的范围,不是本 change 的范围。

**Source:** `openspec/changes/fix-wayfinder-spec-source-field-drift/proposal.md` is itself a change artifact (not a main-spec field), so it is out of scope for the lint rule; recorded here for traceability only.
