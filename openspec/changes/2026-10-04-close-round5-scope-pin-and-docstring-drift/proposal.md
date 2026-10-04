# 收口第五轮复核：普查范围钉死与文档漂移

## Why

第五轮独立复核（`/code-review`，非实现者）对 `41e1663^..b361dcd` 判定 **PARTIAL**。它同时确认了三件我此前最担心的事**不成立**：第四份 change 的 errata 数字全部原样复现（`628d5c5` 102/94/89/17、`1526b98` strong=198、范围 `724/636`）；F1 架构修复真的关上了（`has_historical_marker` 不被 `check_c1` 调用，判定只经 `classify_pointer → ps.scan_line → _exempt`）；不是假绿（更宽总体上 5192 站点 / 4926 活 / 329 文件，全在 `changes/archive/` 下）。`MIN_CHECKS = 80` 也确实承重。

它报的 6 条发现**全部落在本 change scope 内**。其中两条是我自己造成的：一条违反了我上一轮亲手写下的规则，另一条让那个规则的执行者少枚举了一个文件。

## What Changes

### 记录更正（归档件不可变，只能记在这里）

**B-1 — errata 表没有「检测器版本」列，而 D8 正是为防这件事写的。**
第四份 change 的 D8 立了规则：「errata 表的每一格必须写明**测量用的工具/版本**，否则下一次更正无从判断该复现哪一个」，理由写得很清楚——D6 把第三轮检测器的 `189` 和本轮检测器的 `102/94/89` 混进了一张表，两个数字各自都对但无从分辨。然后 `tasks.md` 6.3 把这条打了 `[x]`。

而 `proposal.md` 的 errata 表是四列（量 / round 4 的 D6 所写 / 本轮实测 / 备注），没有版本列。6 行里 5 行没有任何版本标注；`1526b98` 行只标了 **old** 值（备注「189 是第三轮检测器的值」），**measured** 的 `198` 没有；范围算术 `724 / 636` 整行没有——而那个数恰恰是版本相关的，`EXT_EXTENSIONS` 与 `in_scope` 本轮都改过。表头上方那句「并写明测量工具」没有任何一处兑现。**规则写对了、任务勾了、制品没做到。**

**B-2 — D5 写「14 个必须在内」，枚举出来是 15 个。**
`design.md` D5 的括号里列的是：CLAUDE.md（1）+ 三份 spec（3）+ 6 个票据（6）+ LOOPS.md（1）+ 三个 `src/` 模块（3）+ `tests/test_safeguards.py`（1）= **15**。代码里 `PINNED_IN_SCOPE` 是 15 项，`proposal.md` 写的是「15 进 / 4 出」——只有 `design.md` D5 和 `tasks.md` 4.1 写 14。**三处 14、一处 15、代码 15。**

### 代码与守护（4 条）

**B-3 — `SELF_EXCLUDE` 注释说 PREFIX，`in_scope` 用的是子串测。**
`any(x in f for x in SELF_EXCLUDE)`。实测 3 条构造路径分歧：`docs/scripts/lint_notes.md`、`notes/tests/test_lint_extra.md`，以及 `openspec/specs/wayfinder/scripts/lint_x.md`——**一个 spec 会因为自己的路径里含了一个叫 lint 的目录而被静默剔出普查总体**。真实 tracked 文件 0 条分歧（所有条目都在自己目录的根上），所以这是潜伏隐患而非现错，也正因如此它通过了此前四轮复核。改为 `f.startswith(x)`，与注释一致。

**B-4 — `_exempt` 的 docstring 举了一个 `others` 根本没修的例子。**
原文把 `L100 (historical, was 1/128) - but see spec.md L453` 当作「没有 `others` 就会发生」的缺陷。实测：该行 `L453` 仍然 `historical=True`。原因是裸 `L100` 前面没有路径词也没有能力词，根本不是 tracked locator（探针输出里这一行只产出 2 个 site，都是 `L453`），行内**没有可跨越的对象**。`_crosses_another_locator` 本身是对称且正确的（`abs_start < e2 <= start or end <= s2 < abs_start`），逻辑无需改动，错的是注释。改注释，并把该形态明确记为残留而不是声称已修。

**B-5 — 普查范围的具名钉死有两份字面量，其中一份是另一份的严格子集。**
守护测试 `test_census_scope_pins_known_files_in_and_out` 钉 7 进 / 3 出，`scripts/lint_pointer_detector.py` 钉 15 进 / 4 出。子集检测不到它所遮蔽的超集的漂移，所以门禁那份更强的 pin 没有任何测试侧镜像。`pointer_scan.py:644-646` 的注释恰好记录过这个反模式造成的后果——两份 `SELF_EXCLUDE` 副本曾经漂移，普查把检测器和它自己的守护测试当成 43 个 actionable 指针。沿用 `SELF_EXCLUDE` 已有的单源真相模式：具名清单移入 `pointer_scan.py`，lint 派生，测试读同一份。

**B-6 — `_crosses_another_locator` 的反向分支从未被执行过。**
既有测试 `test_marker_may_not_reach_across_another_locator` 是 marker 在前、目标在后的形态，只走到 `abs_start < e2 <= start`。删掉反向的 `end <= s2 < abs_start` 不会有任何测试变红。补镜像方向的测试。

## 不在本 change scope

复核同时报了 3 条 spec 侧发现，**均非本 session 造成**，本 change 不动：

- **A-1（MEDIUM）** `openspec/specs/wayfinder/spec.md:824` 写明「This is a **float** closed form and MUST be pinned with `pytest.approx(0.196901, abs=1e-3)` against a Monte-Carlo mean」，而 `0.196901` 在 `tests/` 与 `src/decompmoe/` 内**零命中**。最接近的 `tests/test_safeguards.py:414` 钉的是另一个量（`E[ε²]=0.0025`）在另一个 `d_c`（4096 而非 16）。公式本身正确（0.196901281094），容差也够（MC 标准误 7.83e-5，约 12.8σ）。该文本早于本 session（见 `2026-10-02-a3-r1-review-remediation` 归档件），属既存缺陷。
- **A-2 / A-3（LOW）** `wayfinder/spec.md:253,300` 的 6 位有效数字偏差值与 `:824` 的 1.58% 百分比，在复核者的 60 位积分下分别为 `3.53800e-14` / `1.64580e-14` 与 `1.57%`。A-2 取决于 mpmath 调用形式，复核者自己也无法证明原值不可复现。

这两条需要各自的 change，A-1 只需在 `tests/test_safeguards.py` 补一条断言。

## 不需要 spec delta

B-3 是让代码回到它自己已声明的语义，B-4 是修正误述，B-5 是单源真相重构，B-6 是补测试。四条都不改变任何 Requirement 的规范内容，因此本 change 无 `specs/` delta。B-1 / B-2 是对归档件的事实更正，按本仓惯例记在本 change 而非改写归档。
