# Proposal

## Why

独立 review（`.audit/reviews/2026-10-03-spec-math-and-tdd-review.md`）对已归档 change
`2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline` 及其派生产物做了复核。复核在第一部分
（该 change 自身的制品）报出 3 条 finding，本 change 修其中成立的部分：

- **保真自检的措辞掩盖了键集差异（F-2）**。`build_pin_drift.py` 的 `self_check()` 只在
  `path` 出现在**并集**时逐键比较区间，因此「仅我方存在、且区间列表为空」的键恒被判为相等。
  自检随后打印 `SELF-CHECK PASSED: drift identical to the original table (60 files, 105 intervals)`
  —— 但原表只有 **48** 个键。读这句话的人会以为表结构也一致。**漂移表本身是对的**
  （105 个非空区间逐键相等，0 处不匹配），失真的只是自检报告的措辞。
- **产物文件名与内容不自洽（F-3）**。`evidence/pin_drift_95718cf.json` 读作「以 `95718cf`
  为 pin」，但内容 `"pin": "6593a06"` / `"head": "95718cfa0b7e..."`——`95718cf` 是 head 侧。
  命名沿用了 `pin_drift_<head[:7]>.json` 的旧惯例。
- **清单生成器的 ANNOT 表有重复键**（review 未单列，本 change 纳入）。`_work/_gen_listA2.py`
  的 `ANNOT` 字面量里 `AC-28` 出现两次（L80 / L90）、`AC-29` 出现两次（L56 / L94）。
  Python 的 dict 字面量**静默保留最后一次**，`ast` 层面完全合法，没有任何警告：
  - `AC-28` 的 L80 段（`[边界保留]`）在渲染产物中**确实不存在** ⇒ 真实数据丢失；
  - `AC-29` 的 L56 段（`[分桶存疑]`）在产物中**存在**，但那是 A-6 当时手术式手改保住的，
    **不是生成器渲染的** ⇒ 潜伏缺陷：谁重跑一次生成器就会把它丢掉。

### 已复核并驳回的一条

review 报出的 F-1（`基线` 三态计数自述 `23/72/13` 与机械统计 `23/74/12` 不符）**不成立**。
按 `基线:` 字段声明行统计，清单里恰有 **108** 条声明 = `touched 23 + unchanged 72 + unverifiable 13`，
与自述逐位吻合。review 的 109 来自另一种计数口径（条目块），该口径下 `###` 标题里混有 4 个非条目
小节，无法复现出它的数字。详见 `design.md` D1。驳回理由写入 design，避免下一轮重新提出。

## What Changes

- **`evidence/build_pin_drift.py`（本 change 自带副本）**：`self_check()` 改为**显式报告键集差异**
  ——分别打印「仅原表有」「仅我方有」「共有」三类键数与路径清单，并新增一条**硬断言**：
  任何「仅我方存在」的键**必须**携带空区间列表（若带非空区间，那是真问题，自检必须报红）。
  PASSED 措辞改为区分「区间逐键相等」与「键集相等」两件事，不再混用 `files=` 一词。
- **产物命名**：`--out` 默认值由 `pin_drift_<head[:7]>.json` 改为
  `drift_<pin[:7]>..<head[:7]>.json`，文件名自带双端点。重新生成并与归档表逐键比对。
- **`_work/_gen_listA2.py`**：`ANNOT` 的 `AC-28` / `AC-29` 两组重复键**合并为单条**（两段文本都保留，
  不丢任何一段），并新增**基于 `ast` 的模块级自校验**——从 `__file__` 解析自身源码，发现
  `ANNOT` 字面量里有重复键即 `raise`。这是唯一能挡住「dict 字面量静默丢键」的形态。
- **产物回填**：把 `AC-28` 丢失的 `[边界保留]` 段补进 `lists/opsx-changes.md`；`AC-29` 的对应段
  已在产物中，**只校验不重复写入**。
- **清单措辞**：`opsx-changes.md` 口径段中复述的「60 文件 / 105 区间 / 0 差异」改为如实分列。
- **追加 `## Errata (A-6 制品复验 侧)`**：与既有 4 个 `## Errata` 小节并列，记录 F-2 / F-3 /
  ANNOT 重复键三项修正。

## 不在本 change 范围

review 第二部分（spec 数学 / 实现形式化 / TDD 原理守护）的 6 条 finding **不动**，其中 2 条
阻断 archive 前门禁（F-8 / F-9）。用户已就 F-9 的修法预先裁决，该裁决连同 F-8 一并记入
`design.md` D5 作为**待办决策**，留给后续独立 change。详见 D5。

## Capabilities

### New Capabilities

无。本 change 只修 `.audit/` 下的非 capability 审计制品与本 change 自身的 evidence。

### Modified Capabilities

无。**不修改任何 requirement**，`.openspec.yaml` 声明 `skip_specs: true`，本 change 无 spec delta，
结构上不可能触发归档时的 anchor 吞并。

## Impact

- **`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md`**：补回 `AC-28` 一段角标（+1 处）、
  口径段措辞改写（1 行）、追加 1 个 Errata 小节。该文件在 `.gitignore:37` 内，**不进版本控制**。
- **`.audit/wayfinder-opsx-code-review/_work/_gen_listA2.py`**：`ANNOT` 两组重复键合并 +
  新增 AST 自校验。gitignored。
- **本 change 的 `evidence/`**：修正版 `build_pin_drift.py`、`drift_6593a06..188b9fb.json`、
  `verify_artifacts.py` 及其报告。**这是唯一进版本控制的部分**。
- **`openspec/changes/archive/**`**：**零改动**。归档制品的修正以 Errata 形式记录，不原地编辑。
- **`openspec/specs/**` / `src/**` / `tests/**`**：零改动。
