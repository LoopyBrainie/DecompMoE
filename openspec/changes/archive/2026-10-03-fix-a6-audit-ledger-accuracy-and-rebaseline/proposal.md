# Proposal

## Why

审计清单 A-6 段的 7 条把**审计结论本身**当作搬运对象（裁决类、裁决时点、镜像分歧、证据可复用性），因此它们的字段一旦失真，下游会重犯同一类误判。2026-10-03 的复验发现 7 条里没有一条能整体照搬：

- **两条指向的缺陷已被归档 change 关闭**，清单仍记为未修。`AC-06` 记「`_betainc_regularized` 仍是单个 8 点 GL 面板零细分」，而 `f6461d7` 已把它改成自适应 8/16 点 GL，且其 docstring 的 HISTORY 段**逐字记录了审计引用的 pre-fix 数值**；`AC-30` 记 `CentroidDriver.step(mask=None)`，而 `a97e3a7` 已把 `mask` 改为必填位置参数。
- **一条是误合**。`AC-26` 记为 `STILL_REAL`，但源 json 三个镜的 verdict 一致是 `FIXED_BY_COMMIT`；其依赖的两条事实也不成立（pin 态 `actual=` 实测 10 处而非 0；`e50cc02` 是 pin 的**后代**，无法影响 pin 态）。
- **字段级错误成族**：`AC-27` 的 `基线` 与机械查表不符（应为 `unchanged-since-pin`）；`AC-29` 的位置差 31 行且 `origin_ids` 含一个不存在的键；`AC-30` / `AC-51` 的 `origin_ids` 键前缀写错（真键一律 `grv:`，全库零个 `rv:grv:`）；`AC-50` 的 `origin_ids` 漏收标题所指的 `rv:main42:*`。
- **全清单落后 16 个 commit**，而 `基线` 字段依赖的漂移表**只有产物、生成脚本从未记录在案**，无法重算。

## What Changes

- **A-6 段 7 条字段级更正**（`裁决` / `严重性` / `位置` / `基线` / `溯源 id` / `问题` / `证据`），并为已关闭条目新增 `修复 commit` 字段与渲染行。`AC-06` / `AC-26` / `AC-30` 改判为 `FIXED_BY_COMMIT`。
- **全清单重基线**：以冻结 commit `95718cf` 重新生成漂移表，按**未改口径**（`drift` 区间覆盖）重算 117 个条目（本文件 108 + 清单 B 15 个字段实例，其中 6 个 `user-decision` 条目同时出现在两份清单）。新增第三态 `unverifiable (no pin line)`，用于无有效行号或路径非仓库内文件的条目——对它们给出 touched/unchanged 都是虚假精度。共 42 个 `基线` 字段被更正。
- **补齐缺失的漂移表生成器** `evidence/build_pin_drift.py`，并以 `pin..188b9fb` 重跑与原表**逐键相等**（60 文件 / 105 区间 / 0 差异）作为保真自检。同时把「区间取哪一侧坐标」这一此前记为未知的问题测定为 **HEAD 侧（`+`）行号**，并把插入/修改在数据结构上分离（`inserted` / `modified`）供下一轮裁定。
- **修生成链上游**（`_work/classified.json` + `_work/_gen_listA2.py`），使更正持久、不被下次重生成覆盖；并加一条 **A-6 锁**（`evidence/a6_expected.json`），生成器写出前断言 7 条关键字段，被回退即硬失败。
- **在文末追加 `## Errata (A-6 侧)`**，与 A-1 / A-2 / A-4 三节保持同一约定。
- **BREAKING（对该制品的读法）**：`基线` 字段新增第三种取值 `unverifiable (no pin line)`。任何按「touched / unchanged 两值」解析该字段的读法需要更新。

不重定义 `基线` 的口径（重定义会同时改写全部 123 个字段）；不重新裁决其它段（A-1 ~ A-5 / A-7 / A-8）的 verdict 与严重性；不重算任何数学闭式；不重跑 lens。

## Capabilities

### New Capabilities

无。本 change 只更正 `.audit/` 下的审计记账制品，不引入任何能力。

### Modified Capabilities

无。**不修改任何 requirement**，因此 `.openspec.yaml` 声明 `skip_specs: true`。副作用之一：本 change 无 spec delta，结构上不可能触发带 delta 的 change 在 archive 时吞掉 anchor 的那一类缺陷。

## Impact

- **`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md`**：A-6 段 7 条字段更正；「基线状态字段怎么读」小节扩展（3 态定义、1-based 声明、坐标侧测定、口径未重定义的声明、以及**该文件不是生成器完整产物**的警告）；「盲区 3 / 盲区 5」更新；文末追加 A-6 Errata 小节。该文件在 `.gitignore:37` 内，**不受版本控制**，因此本 change 依赖 `evidence/_pre_edit_*.md` 快照与 `splice_with_errata_tail.py` 做结构回验。
- **`.audit/wayfinder-opsx-code-review/lists/direct-fixes.md`**：8 个 `基线` 字段改为 `unverifiable`。该文件**无任何生成脚本**，只能手术式改写。
- **`.audit/wayfinder-opsx-code-review/_work/classified.json`**：7 条 A-6 条目 + 42 个 `基线` 字段。
- **`.audit/wayfinder-opsx-code-review/_work/_gen_listA2.py`**：A-6 锁、`修复 commit` 渲染行、仓库外路径的 `位置` 渲染、`fixing_commit` 支持、口径小节与盲区文案。
- **本 change 的 `evidence/`**：8 个脚本 + 4 个产物（漂移表、重基线 diff、锁文件、快照）。全部为只读分析或对上述制品的定点写入。
- **不触碰**：`openspec/specs/**`、`src/**`、`tests/**`、`wayfinder/**`、`openspec/changes/archive/**`。AC-06 / AC-30 的真实缺陷已由 `f6461d7` / `a97e3a7` 关闭，本 change 不再改它们。
- **无 API / 依赖变更**，不触碰训练执行（`CLAUDE.md` §7 out of scope）。
- **并发**：`.audit/**` 曾被在飞 change `2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract` 的 task 9.4 声明；该 change 已归档（其 Errata 已在文件中），故本 change 取得 A-6 段 + 口径小节的所有权，并逐字保留前三个 Errata 小节。
