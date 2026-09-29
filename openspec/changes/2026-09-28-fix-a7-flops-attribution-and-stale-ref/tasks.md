# Tasks

## 1. Pre-flight

- [x] 1.1 Turn-start 审计：跑 `git log --all --oneline -10`、`git reflog --date=iso -10`、`git status --short`，确认 HEAD 与分支（应为 `dev`）；确认 `src/decompmoe/safeguards.py` 标脏仍为纯 CRLF→LF 噪声（`git diff --ignore-all-space --stat -- src/decompmoe/safeguards.py` 输出为空）—— 若出现语义改动则**停下报告**，不并入本 change
      - 实测 @ `9017a94`（`dev`）。HEAD 自 propose 阶段的 `53ca016` 已推进 4 个 commit：`8765806`（本 session 的 A6）、`d6c9350` + `9017a94`（并行 session 的 skeleton-l98 apply + archive）、`0fd5358`（A2/A3/A4 apply）。`safeguards.py` `git diff --numstat` = **0 0**（纯 CRLF 噪声）。工作区另有并行 session 的**未提交残留**（6 个文件，最后写入 18:10，空闲约 4 小时）。
- [x] 1.2 **重新实测**本 change 的全部行号（`git show HEAD:openspec/specs/wayfinder/spec.md`）：Req 17 header 与其 `**Source:**` 行、Req 19 header 与其 `**Source:**` 行、cross-req note 所在行、Req 17 body 中 `65_536` 账目所在行 —— 行号均为实测于 `53ca016`，HEAD 若已推进必须重新定位；**不得**沿用 proposal / design / delta 内的行号
      - **基座已漂移 +6 行**（并行 session 在 `wayfinder` L276 插入 6 行做 R-01 frame tag）。重测结果：`req-17` anchor **L377**（原 L371）、Req 17 header **L379**、extract_C 账目 **L381**（原 L375）、Req 17 Source **L383**；`req-19` anchor **L409**（原 L403）、Req 19 header **L411**、cross-req note **L428**（原 L422）、Req 19 Source **L430**。
      - **连带发现**：proposal/tasks 中写的 `Req 17 L375`（本 change 用于替换 stale `L311` 的目标值）**自身也已 stale**。故 delta 重建脚本不再硬编码行号，改为**从当前 spec 现场推导**：`find_line("33_040 MACs = 66_080 FLOPs")` → `L381`，并断言 `req-17` anchor 行号 < 该行。

## 2. Spec delta（Req 17 + Req 19）

- [x] 2.1 应用 delta 到 Req 17：body 内 `bias `+128` MACs and per-head L2-normalize `+144` MACs are reported separately` → 逐项标注 `H_kv·d_c = 128`（bias）/ `H_kv·d_c = 128`（per-head L2）/ `d_c = 16`（final L2）并注明两个 L2 步骤合计 `+144`；验证该行仍含 `33_040 MACs = 66_080 FLOPs` 与 `~0.83%`
      - delta 已**重建**（基座漂移 +6 行，propose 阶段产物不可复用）：脚本抽取当前 block → 断言式替换（每次命中 == 1）→ **按 header 整体往返验证**（Req 17 2 edits、Req 19 4 edits，全部 `OK`）→ 结构检查（本 change authored 2 行，反引号配平、change 名 backtick-wrapped 且各出现 1 次）→ **LF-only 写盘**（`CR=0`）。应用后 spec L381 生效，该行仍含 `33_040 MACs = 66_080 FLOPs` 与 `~0.83%`。
- [x] 2.2 同上应用到 Req 19 cross-req note：a) `Req 17 L311` stale 反链 → **anchor 引用** ``Req 17 (anchored `<a id="req-17"></a>`)``，**行号整体移除**（最终形式；初版为「订正为当前行号 `L375`」，被 16 小时内两次失效推翻，见下方两条记录与 design.md Decision 2 覆写段）；b) `+144 MACs` 标注为两个 L2 步骤合计（per-head `H_kv·d_c = 128` + final `d_c = 16`）；c) `intentionally does **not** repackage ...` 补 `or the final L2-normalize`
      - (a) 首次写入 `Req 17 L375` → 复验发现 L375 已因 +6 行漂移失效 → 改写 **`Req 17 L381`**（现场推导）。复验通过：`req-17` anchor L377 < 账目行 L381，方向正确。(b)(c) 如期应用于 L428。
      - **(2026-09-29 复验：再次失效并已修正为 `Req 17 L382`)**。16 小时内基座**又漂移 +1 行**（peer 的 `9144f1b` 在 L377 上方插入 1 行），账目行由 L381 移至 **L382**。已同步修改主 spec 与 delta，复验 `账目行 L382 == 反链 Req 17 L382` **MATCH**，`req-17` anchor L378 < L382 方向正确。**⚠️ 但这一版硬编码行号最终未被采用** —— 两次连续失效直接导致改用 anchor 引用，见下一条。
      - **⚠️ 残留脆弱性 → 已消解（2026-09-29 用户决定「改为 anchor 引用，一次到位」）**：硬编码行号在 16 小时内**两次**失效（`L375 → L381 → L382`），累计 +6、+1，均由**与本 change 无关**的 commit 触发。design.md Decision 2 曾为对齐 `b23f0e5` 先例而选择行号而非 anchor 引用；该决定的负面代价现已由实测证实。**处置**：本 change 内就地改为 ``Req 17 (anchored `<a id="req-17"></a>`)``，**行号整体移除**（不是「行号 + anchor」并存 —— 保留的仍会漂移）。先例依据：主 spec L847 已有 `anchored \`<a id="req-20"></a>\``，故属沿用既有风格而非引入新风格。详见 design.md Decision 2 的覆写记录。
      - anchor 改写的三层验证（全部通过）：① 主 spec 全文 `Req 17 L\d+` 残留 **count=0**；② delta 由**编辑后的主 spec 现场抽取 block 重建**（非手抄），Req 17 block 13 行 / Req 19 block 28 行，delta 与主 spec 对应 block **逐行相等**；③ 往返验证 `HEAD spec + delta block == working tree spec` 通过。
- [x] 2.3 **数值冻结对账（最高风险防线）**：以 `git diff openspec/specs/wayfinder/spec.md` 逐值核对，以下全部**必须逐字未变**：`65_536`、`33_040`、`66_080`、`66_048`、`264_192`、`32`、`0.001968`、`0.20%`、`0.05%`、`0.3%`、`~0.83%`、`128`、`144`、`272`、`544`、`512`、`+32 FLOPs`；确认 diff 中**不出现**把 `144` 改为 `128` 的任何 hunk
      - 逐块数字多重集比对（working tree vs HEAD）：Req 17 `lost=[]  gained=['09','2026','28']`；Req 19 `lost=['311']  gained=['09','2026','28','381']`。新增 token 全部来自 Source 反链里的 change 名日期 `2026-09-28` 与订正后的 `381`；唯一消失的是**被刻意替换的 `311`**。18 个冻结值**全部存活**，`frozen_lost=[]`。无 `144 → 128` 变异。
- [x] 2.4 两处 `**Source:**` 追加本 change design.md 反链（Req 17 的 `wayfinder/tickets/A7-2.md`、Req 19 的 `wayfinder/tickets/A8-1.md`）；验证：① 首个 top-level item 仍是 backtick-wrapped ticket；② 每行反引号数为偶数；③ 无 `` `design.md` `` 重复
      - L383 = `**Source:** \`wayfinder/tickets/A7-2.md\`, change \`2026-09-28-fix-a7-…\` design.md (Decision 1 — …)`，backticks=**4**（偶数），首 item 为 backtick-wrapped ticket ✓。L430 = A8-1 同构（两个 Decision），backticks=**4** ✓。无重复 span（delta 构造的结构检查已断言）。
- [x] 2.5 验证 anchor 体系未受影响：按「整行即 anchor」（`^<a id="req-[^"]+"></a>$`）计数，确认 wayfinder 36/36、skeleton 23/23、governance 4/4
      - wayfinder **36 requirements / 36 real anchors**（inline_citations=1）、skeleton **23/23**（inline=2）、governance **4/4** —— 100% 保持。**与本 delta 相邻的两个 anchor 均存活**：`req-18` L393、`req-20` L440（这正是 CRLF delta 会误删的目标）。应用脚本另已断言「每个 anchor 跨空行后紧跟其 Requirement header」，36/36 通过；行数 `892 → 892` 未变（MODIFIED delta 不增删行）。

## 3. Test parameterization

- [x] 3.1 `tests/test_config.py` 三处硬编码的 `8` 改取 `cfg.H_kv`（三个测试各一处）；验证 `cfg.H_kv` 存在且三个测试仍全绿
      - `test_flops_routing_closed_form_66048`：`H_kv, d_k, d_c, N_e = 8, cfg.d_k, …` → `= cfg.H_kv, cfg.d_k, …`；`test_flops_routing_ratio_within_allowance`：`4 * cfg.d_c * 8 * cfg.d_k` → `cfg.H_kv`；`test_flops_routing_cross_req_net_delta_32` 同改。`src/decompmoe/config.py` 已声明 `H_kv: int = 8`。`uv run pytest -q tests/test_config.py` → **12 passed**。
- [x] 3.2 **`macs_bias_l2 = 128 + 144` 保持字面量不变**（design.md Decision 4）。仅在其上方补一行注释记录归属出处
      - `macs_bias_l2 = 128 + 144` **逐字未动**。上方补 3 行注释：bias `H_kv·d_c` = 128；144 = 两个 L2 步骤（per-head `H_kv·d_c` = 128 + final `d_c` = 16）per `decompmoe-skeleton spec.md:138`；并注明「kept as spec literals, not derived, so a change to that decomposition turns this assertion red」。
- [x] 3.3 **禁止把 `128 + 144` 改成推导式**。核对 diff 不得出现 `macs_bias =` / `macs_l2 =` / `cfg.H_kv * cfg.d_c + cfg.d_c`；六个 spec 字面量必须逐字仍以 bare `==` 出现
      - 无任何推导式（grep 唯一命中是 docstring 中解释「为何禁止 `pytest.approx(..., abs=0)`」的说明文字，非代码）。`65_536` L113 / `512` L114 / `66_048` L115 / `264_192` L117 / `66_080` L150 / `32` L151 全部仍为 bare `==`。
- [x] 3.4 跑 `uv run pytest -q tests/test_config.py -v` 验证本文件全绿且**测试数与断言数均不变**
      - `12 passed in 0.05s`。零新增/删除测试、零新增/删除断言。

## 4. Integration verification

- [x] 4.1 跑 `uv run pytest -q` 验证全量基线不变。若计数异常须停下报告，不得调整期望值迁就
      - **`206 passed, 1 warning in 4.65s`，零失败**。计数与本 change 动手前的 206 一致（204 为 A6 apply 时的旧基线；+2 来自并行 session 的 A3/A4 守护）。本 change 前后**计数无变化**。
- [x] 4.2 跑 `python scripts/lint_no_dead_defensive.py` 验证 `exit=0`
      - `lint_no_dead_defensive: OK (no anti-patterns found)` → `exit=0`。
- [x] 4.3 跑 `python scripts/lint_no_source_field_drift.py` 验证 `exit=0`。**本 change 改了两个 `**Source:**` 字段，此项必须实跑**
      - `lint_no_source_field_drift: OK (3 file(s) scanned, no violations)` → `exit=0`。两处追加的反链**通过**了「首个 top-level item 为 backtick-wrapped ticket」规则。
- [x] 4.4 跑 `openspec validate <change> --strict`；并跑 `openspec validate --all` 确认未引入新告警
      - A7 `--strict` → **valid**。`--all` → `Totals: 7 passed, 2 failed (9 items)`，2 个 failed 均为**本 change 之前就已存在**的 in-flight change 缺 `specs/` delta（`fix-review-findings-voronoi-precision-and-lineage` 与 `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure`），已列入本 change 的 Out of scope。**无新增告警**。
- [x] 4.5 复看 `git diff --stat` 确认改动面精确为 `openspec/specs/wayfinder/spec.md` + `tests/test_config.py` 两文件，**零 `src/` 变更**
      - 本 change 在 `wayfinder/spec.md` 贡献 **4 行**（L381 / L383 / L428 / L430）；该文件 `git diff` 共 13 hunk，其余 9 处（L235/L243/L255/L277/L369/L371/L584/L590/L602）属**并行 session 的未提交残留**，非本 change。`src/` 目录本 change **零改动**（`sphere.py` 的 13/4 变化属并行 session；`safeguards.py` numstat = 0 0，仅 CRLF 噪声）。`tests/test_config.py` 本 change 9 行。
- [x] 4.6 在 `dev` 上提交 —— **已完成，commit `fc6988f`**
      - **2026-09-29 14:31 提交，前提已反转。** 决定链：
        1. 用户 2026-09-28 21:54：**不 commit** —— 理由是 `openspec/specs/wayfinder/spec.md` 携带 peer `fix-b1-b3-b6-b8-b9` 的 2 个未提交 hunk，commit 该文件会把他那 2 hunk 卷进本 change（提交归属错乱；`CLAUDE.md` §2 把 `openspec/specs/**` 列为第 1 级真相源，change 制品的 Source 反链需指回本 change）。
        2. 2026-09-29 复核：peer 那 2 hunk **已从工作树消失**（`grep float32` 零命中，L370/L372 恢复原始文本），该文件 100% 只含本 change 的 4 行 —— 原始阻塞点消失。
        3. **但同一时刻发现风险方向已反转**：peer session 自 14:12 起恢复活跃写入（`sphere.py` 14:14、6 个测试文件 14:16–14:27、governance spec 14:21、其 own 制品 14:21/14:22），index 当时干净未 stage。此时若继续不提交，风险从「我 commit 卷走它」变成「**它 commit 卷走 A7**」。
        4. 用户 2026-09-29 14:28 裁决：**立即提交**。
      - **提交方式**：`git commit -F <msgfile> -- openspec/specs/wayfinder/spec.md tests/test_config.py`。`-- <paths>` 形式取工作树内容且**只**提交指定路径，忽略 index 中其他路径的暂存 —— 这正是本仓针对共享 index 的隔离手段；A7 两个文件均已跟踪，全程**未执行任何 `git add`**。
      - **提交结果复核**：`fc6988f`，2 files changed, 15 insertions(+), 12 deletions(-) —— 与归属核定完全吻合（wayfinder 4/4 + test_config 11/8），**无 peer 污染**。提交后 index 仍为 clean。
      - 数字冻结在提交态复查通过（见 4.7）。
      - **本 change 现为 18/18，可 archive。**
      - **【以下三条为历史记录，结论已被上方 2026-09-29 14:31 的提交取代】**
      - ~~用户 2026-09-28 21:54 决定：apply + 验证，但不 commit。~~ 理由：`openspec/specs/wayfinder/spec.md` 携带并行 session 遗留的未提交改动，commit 该文件会把他卷进本 change 的 commit（提交归属错乱，且本仓 `CLAUDE.md` §2 把 `openspec/specs/**` 列为第 1 级真相源、change 制品的 Source 反链需指回本 change）。**该阻塞点已于 2026-09-29 复核为不成立**（peer hunk 消失）。
      - ~~**本 task 未完成，保持 `[ ]`**。~~ 当时的处置计划（已按其字面执行，路径边界放在 commit 而非 add）：`git commit -F <msgfile> -- openspec/specs/wayfinder/spec.md tests/test_config.py`。**archive 禁令已随提交解除**（本 change 现为 18/18）。
      - **2026-09-29 复验：提交边界仍未解除，但性质已变。** HEAD 由 `9017a94` 推进到 `2456cd7`（peer 提交 `9144f1b` a2a3a4 apply + `2456cd7` governance delta 重建）。逐项归属核定：
        | 文件 | 本 change 贡献 | 他人未提交残留 |
        |---|---|---|
        | `openspec/specs/wayfinder/spec.md` | **4 行**（L382 / L384 / L429 / L431） | ~~**2 hunk**（L369-372，属 `fix-b1-b3-b6-b8-b9`）~~ → **已于 2026-09-29 复核：peer 的这 2 hunk 已从工作树消失**（`grep float32` 在 wayfinder spec 零命中；L370/L372 恢复为原始文本），`git diff` 现仅剩本 change 的 2 个 hunk |
        | `tests/test_config.py` | **11 插 / 8 删，100% 归属本 change**（已逐行读 diff 确认无 peer 污染） | 无 |
        | 其余 9 个脏文件 | 无 | 全部属 `fix-b1-b3-b6-b8-b9`（governance 1/3、sphere.py 13/4、test_extraction 177/11、test_metrics 34/24、test_safeguards 17/8、test_schedule 14/5、test_sphere 58/30、test_viz_protocols 13/2） |

        ~~peer 已 16 小时无写入（最后 21:57），其 `fix-b1-b3-b6-b8-b9` change 状态为 complete 43/43（已 apply 未 commit 未 archive）。提交 `wayfinder/spec.md` 仍会把他那 2 个 hunk 卷进本 change 的 commit —— 故保持 blocked，待用户裁决。~~ **（该判断已被 2026-09-29 14:12 的事实推翻：peer 恢复活跃写入，且其 wayfinder hunk 已从工作树消失。）**
      - **2026-09-29 全量 gate 复跑（peer 16h 残留状态下）**：`uv run pytest -q` → **206 passed, 0 failed**；`lint_no_dead_defensive` → `exit=0`；`lint_no_source_field_drift` → `exit=0`；`openspec validate <A7> --strict` → **valid**；anchor 覆盖 **36/36、23/23、4/4**；delta `CR=0`（LF-only）。本 change 的改动在 peer 最新状态下**完整存活且全绿**。

- [x] 4.7 **提交态复核（anchor 到 commit object，非工作树）** —— `fc6988f` 已生成后，凡以工作树为基准的校验都不再等价于提交态，故全部改读 `git show <commit>:<path>`：
      - commit 文件集 == 预期的 2 个路径（无第三个文件混入）✓
      - 提交态 spec 内 `Req 17 L\d+` 残留 **0** ✓
      - 提交态 anchor：standalone **36/36**、无重复 id、inline ref 仅 `req-17`(L429) 与既有先例 `req-20`(L847) ✓
      - **工作树 == commit**（两文件逐字相等）→ 证实 peer 在我提交后未再触碰这两个文件 ✓
      - **delta ≡ 提交态 spec block**：Req 17 **13 行**、Req 19 **28 行** 逐行相等；delta `CR=0` ✓
      - **数值冻结在提交态复查**：18 个冻结值全部存活（与 A7 之前的基线相比**无一丢失**）；`144 → 128` 变异 **不存在** ✓

## 5. Scope added beyond the literal task text（需 reviewer 确认）

- [x] 5.1 顺带修正 `tests/test_config.py` 三处 docstring 的 stale spec 行号与一处错误 Requirement 编号：`Spec L420` → **`L426`**（×2，另 1 处在行内注释）、`Spec L422` → **`L428`**、`Req 20's FLOPs_Routing` → **`Req 19's FLOPs_Routing`**（`FLOPs_Routing` 属 Req 19 "Six Baseline Set On 4070 MVP" L411；Req 20 是 "Eight Geometric Quantification Metrics" L442）
      - **超出 task 3.1–3.4 字面范围，主动上报。** 理由：tasks 3.1–3.4 未提及 docstring，但本 change 的立项理由就是「订正 stale spec 行号反链」；若只改归属标注而留下 `Spec L420`，等于在同一个正在编辑的测试文件里制造同类 stale 反链，且 A7-2 刚把 spec 侧的反链从 L311 订正为 L381。这 4 处与 tasks 3.1 的 `cfg.H_kv` 参数化在同一测试内、同一语义范围，故一并处理。
