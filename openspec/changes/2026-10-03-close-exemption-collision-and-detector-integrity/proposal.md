# 关闭豁免碰撞族与检测器完整性缺陷

## Why

上一轮 change `2026-10-03-close-pointer-blindspot-and-full-tree-sweep` 修好了**检测**盲区：门禁的正则要求能力词后紧跟空白，因此 `wayfinder/spec.md L83` 与 `` `wayfinder/tickets/A8-2.md` L70 `` 永不匹配，树里 75 处活指针被报告为 0。

归档后独立复核推翻了它的收口声明。本轮独立核实确认：**缺陷不在检测，在于豁免。** 检测器能找到的站点，被一条按错误文本单位书写的规则丢弃了。三个互相独立的机制：

1. **code span 掩码只数单反引号奇偶性。** 双反引号 span 贡献四个反引号（偶数），于是它的**内容**被判为「在 code span 之外」。`wayfinder/spec.md` 第 898 行引用示例中的 `historical` 因此成为一个有效标记，遮住了 `openspec/specs/wayfinder/spec.md` L251 —— 该 `**Source:**` 字段实际在第 335 行，**偏差 84 行**。即使对单反引号，旧实现也只标记定界符、从不标记定界符之间的内容。

2. **豁免粒度是行。** 标记只要出现在行内任何位置，就豁免该行**全部** locator。`governance/spec.md` 第 133 行是一个 2000 字符的 `**Source:**` 字段，其中一个子句里的 `原` 把同行的 12 个 locator 全部豁免——包括指向当前文件当前状态的指针。`CLAUDE.md` 第 94 行同构。

3. **标记集把技术名词当断言。** `\bhistor\w*` 接受名词 `history`，于是 `history stacked by metrics.UR per src/decompmoe/metrics.py:83` —— 一个指向**当前** docstring 的指针 —— 自行豁免。

三者叠加的代价是可度量的：修正后的检测器在清扫前的基线树 `1526b98` 上报出 **189 个 strong actionable**，而旧检测器报 100。

此外三项独立缺陷：

- **归档提交 `42d161b` 并未真正归档。** `git ls-tree -r HEAD` 同时含活跃目录与归档目录；删除只作为 15 个未暂存的 ` D` 条目存在于工作树。新克隆该 commit 仍视此 change 为 active。归档副本亦缺 `.openspec.yaml`（92 个归档目录中 86 个带）。
- **验证 harness 自身不可复现。** `evidence/validate_detector.py` 用 `HERE.parents[3]/'scripts'`，归档后解析为 `openspec/scripts`（不存在）→ `ModuleNotFoundError` exit 1。且**无任何门禁调用它**，并硬编码 `D:\tmp\a4fix\base1526b98` 与 `D:\myProject\DecompMoE`，基线 worktree 不在时**静默 SKIP** 唯一在规模化证明非真空的段落。
- **普查范围与语法不自洽。** `tracked_files()` 只 glob `*.md`/`*.py`，而 `EXT` 枚举 11 种扩展。

## The defect

不是「漏了几处指针」，而是**一条按错误单位书写的豁免规则可以在门禁全绿的情况下隐藏任意数量的活指针**。本轮不把它当作清单问题处理。

## Scope

- `scripts/pointer_scan.py` — 豁免模型（指针局部 + 正确 code span 掩码 + 标记集）、`Site` 位置追踪、普查范围。
- `scripts/lint_no_line_pointers.py` — `has_historical_marker` 改调共享实现的新谓词。
- `scripts/lint_pointer_detector.py` — **新增**。harness 从 change 的 `evidence/` 迁到 `scripts/lint_*.py`，路径自派生、基线按 revision 从对象库直读、基线不可读即 FAIL。`run_gates.py` 按 glob 发现，无需改动该文件。
- `tests/test_pointer_scan.py` — 每个新缺陷形态一例守护测试。
- `openspec/specs/**` — 14 处活指针清扫（3 份 delta，5 个 Requirement）。
- `CLAUDE.md` — 2 处。

## What Changes

1. **豁免改为指针局部。** `Site` 携带 locator 在行内的字符跨度；标记必须落在该 locator 前后 `EXEMPT_WINDOW = 40` 字符内、且中间无句读断点。`;` 不再是断点——本仓规范注解 `(historical, <值>; superseded by spec req-N L###)` 是被分号隔开的**一个**单位，把 `;` 当子句边界切断了标记与它所注解的 locator，把九个正当的历史注解报成活指针。
2. **重写 `code_span_mask`。** 扫描反引号**连续段**：N 个反引号开启，恰好 N 个闭合，**两者之间的内容属于 span**。同时标记括号引文。
3. **窗口以尾部余量读取。** 窗口约束的是标记**起点**的位置；文本按窗口先截断会把 `**pre-edit**` 切成 `**pre`，任何模式都匹配不上，于是那行无缘无故保持 actionable。
4. **标记集按「是否断言过去态」重建。** 形容词/副词/分词算数（`historical`、`historically`、`superseded`、`formerly`、`originally`、`pre-edit`/`pre-migration`/…）；**裸名词 `history` 不算**。另设 `RE_PIN_COMMIT`：`at commit \`d3689a1\`` 是结构化 token，其反引号是排版而非引文，该规则不查 code span 掩码（十六进制字母要求仍挡住十进制浮点）。
5. **普查范围从 `EXT` 派生。** `EXT_EXTENSIONS` 由 `removeprefix("(?:")`/`removesuffix(")")` 生成。此前 `EXT[3:-2]` 把 `ini` 切成 `in`。
6. **`SELF_EXCLUDE` 条目改为前缀。** `scripts/lint_` 覆盖将来新增的 lint，无需第二次编辑；逐个列文件名正是本仓上一次清单漂移的成因。
7. **14 处活指针清扫为稳定标识符。** 包括一处**断链**：`CLAUDE.md` 指向的 `.audit/audit-verification.md` 是目录而非文件，该文件不存在；义务本身已形式化在 `req-gov-4`。以及 95 行以上的漂移：`beta_saturation_warning` 被引作 `safeguards.py:211`，实际在 306。
8. **归档补正。** 暂存那 15 个 ` D` 条目并提交，归档副本补 `.openspec.yaml`。blob 同一性已逐个核验：3 份 delta 与 4 个 evidence 脚本与被替换的活跃副本**逐字节相同**；`proposal.md` 与 `tasks.md` 的差异仅是归档工具自身改写（`## What` → `## What Changes`；`- [ ]` → `- [x`）。

## Impact

- 门禁从 3 个 lint 增至 4 个，且新增的那个**验证检测器本身**。这是本仓第一次有门禁断言「检测器没有瞎」。
- `openspec/specs/**` 5 个 Requirement 文本变更，全部是行号定位符换成符号名 / 段名 / Requirement 锚点。**无行为变更、无数学变更、无数值变更。**
- 已知副作用：`governance` 第 133 行三个 `LOOPS.md` 定位符改为段名引用后，第 135 行的 `pre-edit` Note 仍保留行号（它是关于 pre-edit 位置的历史陈述，改掉反而失真）。该 Note 记录的行号现已过期（`## 修改记录` 实际在 L180 而非 L178），本轮**不**改它——它自述为 pre-edit 位置，修正它属于另一件事。

## Errata on the archived record

归档件不可变。以下更正记于此（见 `design.md` D7）。
