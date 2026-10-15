# Design

## Context

见 `proposal.md` 的 Why。此处只记塑造方案的三条**实测约束**：

1. **两份清单不受版本控制**。`.gitignore` 覆盖 `.audit/`，`git ls-files .audit` 返回 0。因此对它们的任何写入都没有 VCS 兜底 —— 先例 `archive/2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline` 的做法是把 pre-edit 快照放进该 change 的 `evidence/`，靠字节级 diff 做结构回验。本 change 沿用。

2. **这两份文件自带一条「不得写入处置建议」的硬约束，且已被机器执行过**。`direct-fixes.md` 文末有 D3/D5 两轮 `leak_scan` 复扫（脚本在 `_work3/d5/leak_scan.py`），用 **13 个主模式 + 11 个绕过模式**扫正文，判据是 (a) 类=「逐字转述被引制品」允许、(b) 类=「把被引物说成应当改成什么」必须为 **0**。D5 实测基线：正文 575 行 / 51,874 字符，(a)=63、(b)=3 处非泄漏命中（全是 L6 性质声明里的 `目标值` / `优先` 二词，与 D3 逐条对应）。**任何新写入都必须让 (b) 保持 0**，否则文件自身的性质声明（"这是已定位问题的存目，不是处置方案表"）即被自己破坏。

3. **`**status**` 字段在这两份文件里已经存在，且含义与直觉相反**。`direct-fixes.md` 32 条里 28 条写 `**status**：ledger 无 status 字段。`、3 条写 `UNVERIFIABLE`、1 条写「ledger 无独立 status 字段；条目正文自带一条保留的 UNVERIFIABLE」（分布由 `grep -o '\*\*status\*\*：.*' … | sort | uniq -c` 复算，见 `evidence/baseline_status_field.md`）。也就是说该字段记的是「**上游 `classified.json` ledger 有没有给这一条带 status**」——一条**溯源注记**，不是「这个缺陷现在还开不开放」的裁定。`opsx-changes.md:216` 则自述「8 条均无 `status` 字段」，与 `classified.json` 全局 `NO_STATUS_FIELD 82` 一致。

## Goals / Non-Goals

**Goals:**

- 让 `opsx-changes.md` 的 8 条在 `ded0944` 各自有一个**可复算**的存活裁定，且裁定所依据的命令与输出留在本 change 的 `evidence/` 里。
- 更正 `opsx-changes.md` 两条条目自身的陈述缺陷：FIX-029（evidence 数值归属对调、problem/consequence 两处过度断言、无出处的 FIX-023「同类」类比）与 FIX-034（problem 段与被引文本相反，且无可指名的修复 commit）。
- 保持两份清单的「无处置建议」性质经机器复扫仍成立。
- 先让本 change 自身通过 `lint_no_baseline_counts.py`（该 lint 报的无基准计数全部落在本 change 自己的制品里），再谈「门禁无感」。

**Non-Goals:**

- 不修任何 spec / src / tests（见 `proposal.md` 的三条「不做」）。
- 不重判任何条目的 **severity**、**分类**或 **problem 实质**。本 change 只增「在 `ded0944` 是否仍复现」这一个正交轴。
- 不为 `.audit/` 建立生成器。先例的 `build_pin_drift.py` 解决的是「pin 相对漂移是否触达某区间」—— 那是纯机械的区间比对；本 change 要回答的是「这个缺陷的**语义**是否还成立」，两者不可互换。

## Decisions

### D-1 · 新增独立字段 `**HEAD 复验（ded0944）**`，不改写既有 `**status**`

**选择**：在每条末尾追加一个**新字段**，与既有 `**status**` 并存。

**理由**：既有 `**status**` 的语义是「上游 ledger 有没有给 status」（见 Context 约束 3）。若把新的开/闭裁定写进同一个字段名，`direct-fixes.md` 里现存的 3 条 `UNVERIFIABLE`（分布由 `grep` 复算，见 `evidence/baseline_status_field.md`）与新写入的 `UNVERIFIABLE` 会成为同一个 token 却指向两件事，任何按该字段做机械解析的读法静默失效。两个轴必须用两个字段名。

**考虑过的替代**：
- (a) 复用 `**status**` 并迁移那 4 条非「ledger 无」条目（计数同 `grep` 复算的 `evidence/baseline_status_field.md`）—— 否决：会销毁「上游 ledger 无 status」这条溯源事实，而它正是 `07-verdict-taxonomy.md` 判定旧 finding 存活状态时依赖的元信息。
- (b) 直接把裁定写进 `evidence` 行 —— 否决：`evidence` 行记的是「测于哪个 commit、看到什么」，裁定与观测混在一行会重演 FIX-029 的病因（观测值与其标签互相矛盾却无法分辨哪一半错）。

**取值域**（五值，闭集）：

| 值 | 含义 | 必带字段 |
|---|---|---|
| `STILL_REPRODUCES` | 在 `ded0944` 按 `evidence` 所记命令重跑，现象不变 | — |
| `CLOSED_BY_COMMIT` | 现象不再复现，且能指名**漂移窗口内**关闭它的 commit | `**修复 commit**` |
| `NARROWED` | 原缺陷部分被处理，残余部分被显式写明 | 残余描述写在同字段内 |
| `UNVERIFIABLE` | 本环境无法取得判定所需证据 | 缺什么证据，写明 |
| `ENTRY_MISSTATED` | 条目自身的 problem 段与被引文本相反，在 pin 时即不成立 | 台账自登记该相反的行号 |

第五值由 FIX-034 逼出。该条的缺陷陈述在 pin 时已是假的：`33f7cc9` 是 pin 的祖先（`git merge-base --is-ancestor 33f7cc9 dde0e1d` 退出 0），req-11:263 在 pin 与 HEAD 逐字相同（`diff` 两个 blob 退出 0）。因此它不是「被某个 commit 闭合」，四值闭集对它无解；若勉强归入 `CLOSED_BY_COMMIT` 则必须指名一个不在窗口内的 commit，那就重蹈了 `git log -S` 的错（见 D-6）。

`CLOSED_BY_COMMIT` 的判据因此收紧为**指名一个在 `dde0e1d..ded0944` 窗口内**的 commit，验证命令是 `git merge-base --is-ancestor <commit> dde0e1d && git log --oneline dde0e1d..HEAD -- <cited path>`（后者必须非空）。

`UNVERIFIABLE` 沿用 `direct-fixes.md` 已在用的 token 名，但因 D-1 的字段隔离，同名不同指认的风险不存在。

### D-2 · 每条裁定必须附「命令 + 观测输出」，存于 `evidence/`，正文只放一行引用

**选择**：`evidence/reverify/<REF>.md` 逐条记录实际执行的命令与其 stdout 关键行；台账正文对应字段只写取值 + 一句指向该文件的引用。

**理由**：`.audit/` 不受版本控制，正文里手抄观测值就是 FIX-029 的成因（幅值抄对了、归属调换了）。把观测与裁定物理分离到两个文件后，「数字对不对」和「标签对不对」变成两个可分别核对的事实。

**考虑过的替代**：直接在正文写数值（现状）—— 已实证失效。

### D-3 · FIX-029 的四个数值必须重跑生成，不得引用本轮对话中的任何数值

**选择**：`evidence/reverify/FIX-029.md` 由脚本在 `ded0944` 上重跑 `T = eye(d_c)` 的中心化协方差构造，覆盖 `d_c ∈ {8, 16, 32, 64}`，记录 `eigvals[0]` 与 `nonzero_count`，并记录 torch 版本。

**理由**：本 change 的整个存在理由是「不能信任转抄的数值」。若 FIX-029 的更正值本身来自一次对话里的手工运行，它就携带了与被更正对象同类的风险 —— 换了出处，性质未变。脚本重跑使其可被第三方以一条命令复现。

**已知**：`d_c` 是硬编码在 `tests/test_metrics.py:153` 的字面量，测试本身不带参数化。因此「同一构造在其它 `d_c` 上如何」只能由该脚本回答，**不是**测试的性质 —— 正文措辞须体现这一点，不得暗示测试覆盖了 `d_c` 变体。

### D-4 · 不建生成器，改用「per-item 复验记录 + 汇总断言」

**选择**：不写通用裁定脚本。`opsx-change` 桶 8 条（分母由 `evidence/baseline_buckets.py` 统计，核验命令 `grep -c '^### FIX-'`）逐条产出 per-item 记录 + 一个汇总校验（读回台账的字段取值，逐条与 `evidence/reverify/<REF>.md` 对账）。`direct-fix` 桶的 23 条具名移交后续 change（见 `tasks.md` 的 `## Workflow follow-up`）。

**理由**：这 8 条的判定口径互不相同（spec 文本措辞、脚本控制流、测试阈值语义、悬空引用计数；分母同 `grep -c '^### FIX-'`）。先例的生成器之所以成立，是因为它算的是区间漂移这一纯机械量。用一个「通用脚本」包装异质判断，只会把判断藏进脚本里，让读者无法逐条复核 —— 与本 change 的目的相反。

### D-5 · leak_scan 在每次写入后重跑，(b) 必须恒为 0

**选择**：把 `_work3/d5/leak_scan.py` 复制到本 change 的 `evidence/`，对两份台账在**每次**编辑后重跑，记录 (a)/(b) 计数。

**理由**：新写入的 `**HEAD 复验**` 字段天然带修复色彩（「已闭合」「修复 commit」），是 (b) 类泄漏的高危区。文件自身的性质声明要求这一轴可被机器检查，就不能只在写完后查一次。

**接受的变化**：字段名与取值域本身会新增 (a) 类命中（逐字转述本 change 的决策），这是允许的；(b) 才是红线。

### D-6 · 否定结果必须带正向对照

**选择**：任何 **0 命中 / 首个命中** 的机械观测，升格为关于制品的事实断言之前，必须附一条**正向对照**——证明「若该物存在，我的匹配器会命中」。缺对照的否定结果只能写 `UNVERIFIABLE`，不得升格。

**理由**：本 change 在自己的复验与写回里踩了七次同一个坑，且七次都已复现：

1. `grep -c '^### \(FIX\|CFL\|CTX\|OPX\)'` 漏掉 `ARC-002` 与两个中文小节标题 → 假的「31 vs 32 差 1」。改正后（`check_rendered_refs.py`）为 32 vs 32，MATCH。
2. `reverify_fix029.py` 初版全文件搜首个 `d_c = \d+` → 报 `:119`（属另一个测试），实为 `:153`。
3. 在截断行区间内 `grep seed` → 假的「FIX-034 缺 seeded-MC 披露」；实际该披露以**交叉引用**存在（`req-gov-1 obligation 7`），且符号 `Â` 在 `openspec/specs/` 下根本不存在。
4. `reverify_opsx_changes.py` 的 `^(\d+)\. \*\*` 漏掉不粗体的第 5 条义务 → 已污染 `evidence/reverify/FIX-020.md` 的 obligations 行。
5. `git log -S` 回答的是「哪个 commit **引入**了该字符串」，被读成「哪个 commit **相对 pin 闭合**了该缺陷」。
6. `git merge-base --is-ancestor <sha> dde0e1d` 的**退出码被读反**：该命令退出 0 意为「`<sha>` 早于 pin」，即**不在**观测窗口内，却被当作「在窗口内」的证明写进了台账三个 `修复 commit` 字段。改正后的判据是 `git merge-base --is-ancestor dde0e1d <sha>`（pin 是 sha 的祖先）加上 `git log --oneline dde0e1d..HEAD | grep -c '^<sha>'`（=1）双向确认。
7. 凭记忆把 spec 引文转述进台账时**丢掉了原文的 `**` 粗体标记**：写成「a supremum over the closed range of `β`, …」，而 spec 现文是「**supremum over the closed range of `β`, …**」。肉眼逐字读无差别，机械 `q in spec` 判据直接否证。已改为逐字形式（取证与裁定见 `evidence/leak_scan_after.md` §2–§3）。

第 1 与第 4 是同一会话内的复发，形态相同：**先写正则，再把它的输出当数**。第 5 与第 6 是它的近亲：**先跑命令，再把退出码的语义按自己需要的方向读**。第 7 是第三类：**凭记忆转述引文时丢掉了格式标记**，肉眼读起来完全一样，机械核对却否证。四类的共同缺失都是同一个 —— 拿到机器输出后没有问「这条命令实际回答的是哪个问题」。

**未计入的一类**：本会话末段还出现过一次「正则比被测对象**宽**」的假阳性（把 `tasks.md` 的任务号 `3.4`/`4.1` 当成 `.txt` 里缺失的数据值）。它**不违反** D-6 —— D-6 管的是「否定结果被升格为事实断言」，而该次假阳性在当场即被识别并弃用，未写进任何制品。记录在此是为了说明为何计数停在 7 而不是 9：**未升格的误判不计入，升格了的才计入。**

**推论（可执行的两条）**：
- 匹配器必须先由**制品的实际形态**枚举得出，再回头验证覆盖率；不得先写正则再读它的输出。
- 已被上述任一形态污染的结论，在更正前不得写进任何制品。

`07-verdict-taxonomy.md` §6 管的是「同一个量在不同口径下得到不同的**正数**」；这七次里前六次是「得到 0 或偏小的正数，然后宣称制品里没有 / 宣称差 1 / 宣称在窗口内」，第 7 次是「宣称引文逐字，实测并非」。该 taxonomy 未覆盖这一类，本 change 不改 spec（`skip_specs: true`），只在此登记。

## Risks / Trade-offs

**[台账被改坏且无 VCS 可回滚]** → `evidence/_pre_edit_opsx-changes.md` 与 `_pre_edit_direct-fixes.md` 两份 pre-edit 快照先行落盘；每次编辑后做字节级 diff 并记录。回滚 = 从快照还原。

**[部分裁定被用户否决]** → 每条裁定在 `evidence/reverify/<REF>.md` 里带命令与输出，任何一条被否决时可单独重跑该条，不必重做整轮。

**[leak_scan 因新字段措辞报出 (b) > 0]** → 把该字段的表述改回纯观测语言（「在 `ded0944` 重跑后现象不复现」而非「应修复」）。若反复触发，则该字段的取值域需重新措辞 —— 这是 D-5 的设计意图：让约束在写入前就生效。

**[本轮复验与写回自身出错]** → 已发生**七次**（逐条机制见 `design.md` D-6；取证命令为 `git merge-base --is-ancestor`、`git log -S`、`git log --oneline`，以及 `evidence/leak_scan_after.md` §3 的引文逐字核验）。已污染落盘制品者三处：`evidence/reverify/FIX-020.md` 的 obligations 行、`evidence/reverify/FIX-034.md` 的 commit 归因（由 `tasks.md` 的 2.5 / 2.6 修复），以及写回时台账三个 `修复 commit` 字段的判据命令方向（当场发现并改正）。**这本身就是本 change 存在理由的最好例证**：机械核对命令的正则写窄了或答的是另一个问题，结论却按未受影响的读法写了下去。

**[`openspec validate` 因 `skip_specs: true` 拒绝零 delta change]** → 已在 `.openspec.yaml` 声明；先例 `2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline` 是同一处理，无新增风险。

**[归档时 anchor 被吞]** → 结构上不可能：本 change 无 spec delta。沿用先例记录在案的理由。

## Migration Plan

无部署面（不触碰 `src/`、`tests/`、`openspec/specs/`）。

回滚：从 `evidence/_pre_edit_*.md` 还原两份台账；删除本 change 目录。

**apply 后的自检判据**：先跑 `uv run python scripts/lint_no_baseline_counts.py` 确认本 change 三份制品的违规清零，再跑 `uv run python scripts/run_gates.py` 要求 `GATE OK` 且 pytest 行为 `549 passed, 1 skipped`（与 `ded0944` 基线逐字一致）；`git status --porcelain` 除本 change 目录外无新增条目。

## Open Questions

无。取值域、D-3 的构造参数、D-5 的红线均已在上面定死；`proposal.md` 列出的 Open Follow-up（工作树未提交改动、两个空 change 目录、L3 的真实 spec/test 缺陷、移交的 direct-fix 条目）是**后续 change 的范围**，不是本 change 的待决问题。
