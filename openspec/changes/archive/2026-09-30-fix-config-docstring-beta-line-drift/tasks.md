# Tasks — B14 stale spec 行号

> 基线 commit：`b272787`。archive 前置 SHA256：`ee75cef81c1d0e4d2717d9ed27f250599dfdc3fd343fc5f622e08e93787382c6`

## A · 核验

- [x] A.1 确认 `wayfinder/spec.md` L122 是空行（req-7 heading 在 L121，正文自 L123 起）
- [x] A.2 确认 β_0 闭式 / narrative 的实际落点为 **L130**（含 50-digit mpmath 精度披露）
- [x] A.3 确认 Sigmoid 闭式 `β^param(γ) = β_min + (β_max−β_min)·Sigmoid(γ)` 的实际落点为 **L123**
- [x] A.4 `git grep -n "L122" -- src` 精确命中 1 处（`config.py:50`）
- [x] A.5 **计划外发现**：`decompmoe-skeleton/spec.md:508` 的 `req-7 L115` 指向 `territory_seeding`（req-2）的 Scenario 行，与 req-7 无关 —— 与 B16 同型
- [x] A.6 确认 `wayfinder/spec.md:150,156` 与 `tests/test_beta.py` 已由 `b23f0e5` 修为 `L130`，无残留
- [x] A.7 确认 `b23f0e5` 的 commit message 声称修了 `A4-1.md`，但 `--name-only` 无该文件（过度声称），登记为事实纠正

## B · 变更

- [x] B.1 `src/decompmoe/config.py:50` `L122` → `L130`
- [x] B.2 delta 程序化构造：脚本从 `git show HEAD:…` 切分 req-21 块（L479–L511），逐条替换后整体写出
- [x] B.3 delta 内 3 处替换各断言「old 恰好出现 1 次」，任一不满足即 ABORT
- [x] B.4 delta 自检：CRLF=0、anchor=1、heading=1、残留 `L122`=0、残留 `L115`=0
- [x] B.5 确认未改 `MVPConfig.beta_initial` 的值（`1.035` 正确）
- [x] B.6 确认 req-21 的三个 Scenario 内容与 tolerance 未触碰

## C · 制品

- [x] C.1 `.openspec.yaml`
- [x] C.2 `proposal.md` —— 含 A.5 计划外发现与 A.7 commit message 过度声称
- [x] C.3 `design.md` —— 4 项 Decision
- [x] C.4 `tasks.md`（本文件）
- [x] C.5 `specs/decompmoe-skeleton/spec.md`（MODIFIED Requirement `req-21`）

## D · archive 前置

- [x] D.1 主 spec 逐字节 SHA256 快照（`ee75cef8…`）
- [x] D.2 `git status --short -- openspec/specs/decompmoe-skeleton/spec.md` 为空（**恢复前提**）
- [x] D.3 `python scripts/lint_no_dead_defensive.py` exit 0
- [x] D.4 `python scripts/lint_no_source_field_drift.py` exit 0
- [x] D.5 `openspec validate --specs` 全绿（3 passed / 0 failed）
- [x] D.6 anchor 归档前基线：wayfinder 36 / skeleton 23 / governance 4
- [ ] D.7 `uv run pytest` 全绿 —— **BLOCKED（2026-09-29 20:00）**

### D.7 阻塞详情（第一轮，2026-09-29 20:00）

全量 pytest 报 **1 failed, 207 passed**：`tests/test_sphere.py::test_versine_voronoi_closed_form`，实测 `1.7840938828506125e-05` vs 字面 `1.784094e-05`，偏差 `1.17e-12` 略微超过 `abs=1e-12`。属并行 session 在途改动（本 change 从不触碰该文件）；排除该文件后 192 passed。

### D.7 阻塞详情（第二轮，2026-09-30 22:50）—— 阻塞原因已变更，D.2 恢复前提失效

24 小时后复检：

| 项 | 2026-09-29 20:00 | 2026-09-30 22:50 |
|---|---|---|
| D.2 主 spec 相对 HEAD 无未提交改动 | 满足 | **失效** —— `decompmoe-skeleton` / `governance` / `wayfinder` 三份 spec 均有未提交改动 |
| 全量 pytest | 1 failed（peer 在途断言擦边） | **1 failed, 212 passed** —— 失败点变为 `tests/test_config.py::test_total_param_estimate` |
| 失败根因 | peer 的 versine 断言容差 | **peer 遗留调试探针**：`src/decompmoe/config.py` 工作树为 `vocab_size: int = 32001  # PROBE`（HEAD 为 `32000`），改变总参数量 |
| peer 活跃度 | 在途写入 | 仍在写入（22:48 触碰 `archive/…/tasks.md`）；其 `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` 已归档 |

**D.2 失效的后果**：archive 一旦损坏 spec，`git checkout -- openspec/specs/decompmoe-skeleton/spec.md` 将**连同 peer 的未提交改动一并丢弃**，无法完整回到本 change 的归档前基线（`ee75cef8…`）。三重防护中的「恢复前提」已不成立。

**peer 未提交改动与 req-21 无交集**：其 skeleton spec 改动位于 `@@252 / @@267 / @@313 / @@323 / @@334`，均在 req-21 之前。req-21 块当前仍带 `L122`（L500、L502）与 `L115`（L525），即本 change 的 delta 仍待应用、未被他人抢先处理。

**处置（不变）**：不执行 archive；不修改、不代为清理 peer 的工作树改动；不在其活跃期间覆盖其文件。

## E · archive 与后置验证 —— 已完成（2026-09-30 23:2x）

**D.7 阻塞已解除**：并行 session 收工后全量 pytest 恢复 **215 passed**，主 spec 相对 HEAD 亦恢复干净（peer 的 `# PROBE` 遗留已由其后续 commit 清除，`config.py` 回到 `vocab_size: int = 32000`）。

归档前另做**基座漂移对账**（peer 曾重写 `openspec/specs/`）：以 `git show HEAD:` 逐行 diff 主 spec 的 req-21 块与本 change 的 delta，差异恰为 **6 changed lines = 3 处指针修正的 −/+ 对**，即「delta ≡ 当前主 spec + 3 处定点编辑」，**无基座漂移**，delta 无需重建。

- [x] E.1 `openspec archive fix-config-docstring-beta-line-drift` → 归档为 `2026-09-30-fix-config-docstring-beta-line-drift`，报 `~ 1 modified`
- [x] E.2 **anchor 逐行复算**：archive 当时报 36 / **22** / 4 —— **skeleton 丢 1 个 anchor，已修复**（详见 G 节）；最终 36 / 23 / 4
- [x] E.3 anchor 重复 id 复查：三份 spec 均 `dup=0`
- [x] E.4 主 spec SHA256 比对：归档前 `ae707fe2…`（旧快照 `ee75cef8…` 已作废，因 peer 在此期间重写过 spec）→ 修复后内容为「HEAD + 3 行」
- [x] E.5 `L122` / `L115` 全仓清零（`src` / `tests` / `openspec/specs` 均无命中），落点为 `req-7 L130` ×2 与 `req-7 L123` ×1
- [x] E.6 `uv run pytest` → **215 passed**（archive 后）
- [x] E.7 两 lint exit 0 + `openspec validate --specs` → 3 passed / 0 failed
- [x] E.8 change 目录由 `openspec archive` 自行移入 `archive/2026-09-30-…`（5 制品齐全）
- [x] E.9 提交前 `git status --short` 核对制品均为 `R`（rename）
- [x] E.10 提交后断言工作树 == commit object

## G · archive 吞 anchor 事件（本 change 归档时发生并已修复）

**现象**：`openspec archive` 报 `~ 1 modified`、`exit=0`，三处指针修正也确实落位（`L130` ×2、`L123` ×1，`L122`/`L115` 归零），**但 `decompmoe-skeleton` 的 anchor 数从 23 掉到 22** —— `<a id="req-22"></a>` 被连带吞掉，而 `req-22` 的 `### Requirement:` heading 仍在，形成**有 heading 无 anchor** 的孤儿 Requirement。

**再次印证**：`archive` 的 exit code 与 `~ N modified` 计数**都不是「spec 未被破坏」的证据**。唯一能发现的是 anchor 逐行计数。

**根因（与本仓既有观测一致）**：MODIFIED block 的尾部边界判定会吞掉**紧随其后那个** Requirement 的 anchor，每个被改的 Requirement 恰好丢 1 个。本 change 只改 `req-21`，丢的正是其后的 `req-22`。

**修复方式**：不重跑 archive（重跑会再次吞）。改为

1. `git show HEAD:openspec/specs/decompmoe-skeleton/spec.md` 还原到归档前内容（anchor 回到 23，`req-22` anchor 复位）
2. 以**确定性字符串替换**重放 3 处指针修正
3. 复算：anchors 23 / headings 23 / `dup=0` / `L122`=0 / `L115`=0 / `req-22` anchor 存在
4. `git diff --numstat` = **3 插 3 删**，即最终 spec 恰为「HEAD + 3 行定点编辑」

**遗留风险**：本仓每被改一个 Requirement 就会丢 1 个 anchor，`openspec archive` 因此**不能单独作为归档手段**，任何带 MODIFIED delta 的 change 都必须执行「归档后 anchor 复算 + 确定性重放」两步。

## F · 并发风险记录（2026-09-30 复检）

**主 spec 仍显示 `L122`（两处）与 `L115`（一处）是 pre-archive 预期状态，不是遗漏** —— 修正只存在于本 change 的 delta 中。

**并发事件结局（2026-09-30 23:2x 更新）**：F 节此前的预警**应验**。

| 修正 | 提交 | 结局 |
|---|---|---|
| `config.py:50` `L122→L130` | `a036a15` | **完好**。peer 遗留的 `vocab_size … # PROBE` 已由其后续 commit 清除，HEAD 为 `vocab_size: int = 32000` |
| `safeguards.py` B13/B16 | `f0b3aa2` | **完好**（`cfg.N_e` 锚定段 + `0b2202e` 溯源在位，`L644` 引用已清零） |
| `test_loss.py` 10 处 `actual=` | `b272787` | **一度被回退**：peer 的中途快照 commit `e50cc02`（`chore(inflight): checkpoint parallel session's in-flight work`）把工作树里 `b272787` 之前的旧副本一并提交，使 `b272787` 的效果在 HEAD 消失（`actual==0`）。**已在本 change 收尾时重放修复**，复测 `approx=10 / actual==10` |

**关于 `e50cc02` 的定性**：其 commit message 自述为「中途快照，不是完成态」，把共享工作树的残留一并提交。B15 的回退是**该快照的附带后果，非有意撤销**（其 message 未提及 `test_loss.py` 或 B15）。归档 change `2026-09-29-fix-b15-test-loss-actual-embedding` 已把重放后的状态一并纳入。

**教训**：共享工作树下「代他人提交未提交改动」这一动作会**静默吞掉已提交的历史**——`b272787` 仍在 git log 里，但其内容被后续 commit 覆盖。仅看 `git log` 会以为修改还在；必须比对 `git show HEAD:<path>` 与目标 commit 的内容才能发现。

## Out of scope / Deferred

- `wayfinder/tickets/A4-1.md:59` 的 `L122` —— 等 `fix-review-findings-voronoi-precision-and-lineage` 归档
- 该 change `tasks.md:19` 的假勾（`[x] 1.4.3` 但 edit 从未进 commit）—— 同上
- 全仓行号引用的 line-drift 抗性改造 —— 需独立 change
- `openspec archive` 吞 anchor 的工具级修复 —— 见 G 节，需在 archive 流程中固化「复算 + 确定性重放」两步
