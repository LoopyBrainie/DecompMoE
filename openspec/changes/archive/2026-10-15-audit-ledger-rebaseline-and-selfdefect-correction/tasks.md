# Tasks

## 0. 先让本 change 自己通过门禁

- [x] 0.1 跑 `uv run python scripts/lint_no_baseline_counts.py`，把本 change 三份制品（`proposal.md` / `design.md` / `tasks.md`）里每一处无基准计数补上其基线（commit hash / `HEAD` / change 名 / `req-N` 锚点 / 可复算命令 / 「基线」）。验证：该 lint 从当前的违规状态转为 `OK (N evidence file(s) scanned, no baseline-less counts)`。**不得以撒豁免标记（`不可复算` / `不处置`）代替补基准** —— 豁免是承认不可复算，而这些数字全都可复算，只是没写出来。

## 1. 基线捕获（任何写入之前）

- [x] 1.1 把 `design.md` Context 约束 3 的实测值落盘为 `evidence/baseline_status_field.md`：`grep -o '\*\*status\*\*：.*' .audit/gradual-review-2026-10-07/lists/direct-fixes.md | sort | uniq -c` 的原始输出（预期 28 / 3 / 1）与 `opsx-changes.md:216` 的自述行。验证：该文件存在且三组计数与现场重跑逐字相等。
- [x] 1.2 记录 `classified.json` 的分桶计数为 `evidence/baseline_buckets.md`：`{total: 88, direct-fix: 32, opsx-change: 8, conflict: 22, archive-only: 12, context: 9, user-decision: 5}`，并附生成该表的脚本。验证：重跑脚本得到同一 JSON。
- [x] 1.3 落盘 pre-edit 快照 `evidence/_pre_edit_opsx-changes.md` 与 `evidence/_pre_edit_direct-fixes.md`（两份台账的逐字副本）。验证：`cmp` 两文件与现场台账相同，且记录各自的字节数与行数。
- [x] 1.4 把 `.audit/gradual-review-2026-10-07/_work3/d5/leak_scan.py` 复制到 `evidence/leak_scan.py`，对**未修改**的两份台账跑一次取基线。验证：记录 (a)/(b) 计数；与 `direct-fixes.md` 文末 D5 自述的 (a)=63、**(b)=0** 对账并记录差异（D5 测于更早的正文版本，计数本可不同——差异本身要记录，不要求相等）。

## 2. 逐条复验记录（先记录，后写回）

> 每条记录是一个 `evidence/reverify/<REF>.md`，含**实际执行的命令**与**其 stdout 关键行**（design.md D-2）。本组**只写 evidence/，不碰台账**。

- [x] 2.1 复验 `opsx-changes.md` 的 8 条（FIX-001 / 006 / 007 / 020 / 029 / 034 / 041 / 042；分母由 `evidence/baseline_buckets.py` 统计，核验命令 `grep -c '^### FIX-'`），逐条产出 evidence 记录。已在 planning 阶段完成的 4 条（001 / 006 / 007 / 020）可据此整理，但**命令与输出必须重跑一次**以确保可复现，不得从对话记录转抄。验证：8 个文件齐备，且每个文件内的命令重跑得到同样的关键输出。
- [x] 2.2 复验 `direct-fixes.md` 中**被引文件在 `dde0e1d..ded0944` 窗口内零 commit** 的条目，逐条产出 evidence 记录。命中集由 `evidence/reverify_direct_fixes.py` 产出，判据命令是 `git log --oneline dde0e1d..HEAD -- <cited path>` 返回空。注意 FIX-008 / FIX-009 / FIX-010 依赖 POSIX 行为，在 Windows 上**只能**给出 `UNVERIFIABLE` 并写明缺什么证据——沿用条目正文已有的该保留裁定，不得因本轮重跑而改判。验证：已落盘的 evidence 文件与脚本输出的机械可判集合逐条相等；每条取值落在 design.md D-1 的五值闭集内。不满足该判据的条目**不在本任务范围**，具名移交（见 `## Workflow follow-up`）。
- [x] 2.3 按 design.md D-3 写 `evidence/reverify/FIX-029.md`：脚本重跑 `T = torch.eye(d_c)` 的中心化协方差构造，`d_c ∈ {8,16,32,64}`，记录 `eigvals[0]`、`nonzero_count`、torch 版本。验证：脚本输出含四个 `d_c` 的完整行；第三方以同一条命令得到同组数值。
- [x] 2.4 为 2.3 的脚本补一条自检：确认 `d_c` 是 `tests/test_metrics.py:153` 的硬编码字面量、该测试不带参数化，因此变体扫描**不是**测试覆盖的性质。验证：脚本注释与 evidence 记录都写明这一点，正文措辞不得暗示测试覆盖了 `d_c` 变体。
- [x] 2.5 修 `evidence/reverify_opsx_changes.py` 的义务提取正则 `^(\d+)\. \*\*` → `^(\d+)\.\s`（req-gov-1 第 5 条写作 `5. Every assertion…` 无粗体，被原正则丢弃），重跑脚本，并据此把 `evidence/reverify/FIX-020.md` 的 obligations 行由 `[1,2,3,4,6,7]` 改为 `[1,2,3,4,5,6,7]`。验证：`sed -n '7,65p' openspec/specs/governance/spec.md | grep -nE '^[0-9]+\. '` 的七个编号与脚本输出逐个相等。
- [x] 2.6 改判 `evidence/reverify/FIX-034.md`：删除 `CLOSED_BY_COMMIT 33f7cc9` 这一不成立的归因（`33f7cc9` 是 pin 的祖先，不在 `dde0e1d..HEAD` 窗口内；req-11:263 在 pin 与 HEAD 逐字相同），改写为 `ENTRY_MISSTATED`，并说明 `git log -S` 回答的是「谁引入」而非「谁相对 pin 闭合」（`design.md` D-6 第 5 例）。验证：`git merge-base --is-ancestor 33f7cc9 dde0e1d` 退出 0，且记录中不再出现把该 commit 当作漂移窗口内闭合者的表述。

## 3. 写回台账

- [x] 3.1 `opsx-changes.md`：pin 由 `dde0e1d` 改为 `ded0944`（含 commit 数与日期）。验证：`grep -n '测量基线'` 显示新 pin 且 commit 数与 `git rev-list --count HEAD` 相符。
- [x] 3.2 `opsx-changes.md`：8 条各追加 `**HEAD 复验（ded0944）**` 字段；`CLOSED_BY_COMMIT` 者附 `**修复 commit**`。**不动**既有 `**status**` 字段（D-1）。验证：`grep -c 'HEAD 复验（ded0944）'` 返回 8；`grep -c '\*\*修复 commit\*\*'` 与 evidence 中 `CLOSED_BY_COMMIT` 的条数相等。
- [x] 3.3 `opsx-changes.md` FIX-029 条：更正 `evidence` 行的数值归属（用 2.3 的实测值）；把 `problem` 段「而非由数学决定」收窄为「按绝对阈值定秩不可判定 + `:166` 是单边断言」；把 `consequence` 段「红绿不可解释」收窄为仅 `d_c=64` 的红；把「`1e-10` 只活在测试与散文里」改为「两处可执行字面量」；删去 FIX-023「同类」类比。验证：逐条比对 2.3 的脚本输出，正文每个数值都能在该输出里找到；`grep -n 'FIX-023' opsx-changes.md` 不再命中 FIX-029 条目正文。
  - **实施时发现的范围外两处，按实登记而非静默扩大**：3.3 上文只点名 `evidence` / `problem` / `consequence` 三个字段，实际执行另改了两处 ——（i）**`location`**：该字段原文把 `eigvals[0] = +1.1e-08` 与 `−7.5e-09` 的 `d_c` 归属对调，与同句的「16 上绿 / 64 上红」标签自相矛盾；只在 `evidence` 更正而把 `location` 的错误原样留下，会使该条目自身不一致，且违反 3.3 的验证判据「正文每个数值都能在该输出里找到」。（ii）**`crossrefs`**：补 `FIX-029 ↔ FIX-020` 对，因本条的阈值豁免机制正是 `governance/spec.md:666` 末句所开的那条豁免（见 `evidence/reverify/FIX-020.md`）。两处均为**更正已知错误**或**记录已验证的成对关系**，不引入新主张，故按本 change 的自缺陷更正原则保留；此处登记以备复核者判断是否应回退。
- [x] 3.4 `opsx-changes.md` FIX-034 条：改判为 `ENTRY_MISSTATED`，不写 `**修复 commit**`；在条目内指向台账自身登记该相反的复核段。验证：条目内 `**修复 commit**` 不出现；取值与 `evidence/reverify/FIX-034.md`（由 2.6 在 `HEAD = ded0944` 下修完）一致。
- [x] 3.5 `opsx-changes.md`：文末自检小节增补本轮复核记录（复验口径、取值分布、与 D5 leak 计数的关系）。验证：小节存在且不含 (b) 类措辞（由 4.1 判定）。
- [x] 3.6 `direct-fixes.md`：仅 pin 更新，并登记本轮已自查捕获的误判作为可靠性注记。**不逐条追裁定** —— 机械判定可完成的条目见 `evidence/reverify/`（判据命令 `git log --oneline dde0e1d..HEAD -- <path>` 返回空），其余具名移交（见 `## Workflow follow-up`）。验证：`grep -n '测量基线'` 显示新 pin；台账**渲染出的条目标题数**与 `classified.json` 的 `bucket == direct-fix` 分母相等（由 `evidence/check_rendered_refs.py` 判定，输出 `VERDICT: MATCH`，32 vs 32）。

> **实施时订正**：本条原写的验证判据是「本 change 实际写入的条目数与 `evidence/reverify/` 中已落盘的条目数相等」。该判据**字面不可满足**：3.6 的承诺是「不逐条追裁定」，故本 change 向 `direct-fixes.md` 写入的条目级裁定为 **0** 条，而 `evidence/reverify/` 中的 direct-fix 记录为 **9** 份（机械判定可完成者，见 `evidence/reverify_direct_fixes.txt`）。`0 == 9` 不成立。判据实际验证的对象是**台账渲染出的条目标题**与 `classified.json` 分母的对应关系，两者都是 32 —— 这正是 `check_rendered_refs.py` 所做的检查。已按实际执行的检查改写判据，未改动检查本身。

## 4. 验证

- [x] 4.1 对两份台账重跑 `evidence/leak_scan.py`。验证：**(b) 类命中数 = 0**（design.md D-5 的红线）；(a) 类新增命中逐条确认均为「逐字转述本 change 决策」的允许类别。
- [x] 4.2 汇总对账：写 `evidence/final_crosscheck.md`，读回台账的 `**HEAD 复验（ded0944）**` 取值，逐条与 `evidence/reverify/<REF>.md` 对账。验证：本 change 写入的 `opsx-changes.md` 全部条目对得上，无台账有记录缺、或有记录无台账字段的情形；`direct-fixes.md` 已写的部分同样对账。
- [x] 4.3 门禁无感验证：先跑 `uv run python scripts/lint_no_baseline_counts.py` 确认 0.1 已把违规清零，再跑 `uv run python scripts/run_gates.py`。验证：输出 `GATE OK`，pytest 行仍为 `549 passed, 1 skipped`（`ded0944` 基线）；若数字变化，先查是否有 task 误触 `src/` / `tests/` / `openspec/specs/`。
- [x] 4.4 作用域验证：`git status --porcelain`。验证：除本 change 目录外**无新增条目**；工作树那 3 处既有修改（`.gitignore` / `src/decompmoe/gating.py` / `wayfinder/tickets/WF-1.md`）保持原样未被本 change 触碰。
- [x] 4.5 字节级回验：`diff` 两份 pre-edit 快照与现场台账，人工确认每一处差异都落在 task 3.1–3.6 声明的范围内。验证：无范围外差异。

## Workflow follow-up

- **具名移交：`direct-fix` 桶中本 change 未复验的条目**（`dde0e1d..ded0944` 窗口内，除已落 evidence 的机械判定条目外）。按失效机制分两类，方法不同：
  - **后续 A（被引文件已变动）** —— 须逐条读原文判定，口径异质，适用 `design.md` D-4 原样（不写通用裁定脚本）。本 change 已用 `evidence/reverify_direct_fixes.py` 产出机械脊梁（`evidence/reverify_direct_fixes.txt`），可直接作为其起点。
  - **后续 B（只引 `.audit/**` 或只引树/目录聚合计数）** —— 前者未受 git 追踪，`git log` 平凡返回 0，推理不携带信息，必须比对文件内容；后者历史有效，坏的是那个数，必须先声明计数规则再复算。**这两类不适用 D-4**，需要的是计数口径声明，正是 `lint_no_baseline_counts.py` 已在机器上执行的纪律。
- 本 change 完成后，以下各项是**后续 change 的范围**，不在本 change 内执行，也不因本 change 完成而自动开始：
  - 工作树 3 处未提交改动的归属裁决（尤其 `wayfinder/tickets/WF-1.md` 删掉的两处 `(historical, ...)` 标注是否恢复）——需人工判断意图。
  - 两个空 change 目录（`fix-review-findings-voronoi-precision-and-lineage/` 完全空、`2026-09-26-followup-spec-wording-bugs-after-precision-disclosure/` 仅空 `specs/`）的处置；前者被 `openspec/specs/` 活引用 2 次，删除会改动 `governance/spec.md`，需另起带 spec delta 的 change。
  - L3 的真实 spec/test 缺陷（FIX-029 阈值本身、FIX-041 的 `req-gov-9` 悬空引用、FIX-042 的 Source 豁免）——取舍依赖本 change 的复验输出。FIX-034 **不在**此列：它是条目自身陈述错误，已由本 change 的自缺陷更正处理。
- Archive the change after the project's review requirements are satisfied（`skip_specs: true`，archive 时不涉及 spec delta 同步；仍须走 anchor-ledger 协议以确认无 anchor 变动）。
- Verify the archived result.
