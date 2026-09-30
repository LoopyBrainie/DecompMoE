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

## E · archive 与后置验证 —— 仍未执行

> 阻塞于 D.7（两轮）。待主 spec 恢复为相对 HEAD 干净、且全量 pytest 全绿后按序执行。

- [ ] E.1 `openspec archive fix-config-docstring-beta-line-drift`
- [ ] E.2 **anchor 逐行复算**（基准取 commit object）：wayfinder 36 / skeleton 23 / governance 4
- [ ] E.3 复算同时检查 anchor 重复 id
- [ ] E.4 主 spec SHA256 与归档前快照（`ee75cef8…`）比对
- [ ] E.5 确认 delta 内 `L122` / `L115` 归零且落到正确的 spec 行
- [ ] E.6 `uv run pytest` 全量全绿（archive 后）
- [ ] E.7 两 lint + `openspec validate --specs` archive 后复跑
- [ ] E.8 用 `Move-Item -LiteralPath` + `git add -A -- <旧> <新>` 移入 archive（本机 `git mv` 会 Permission denied）
- [ ] E.9 `git status --short` 确认 5 个制品均被识别为 `R`（rename）
- [ ] E.10 提交后断言工作树 == commit object

## F · 并发风险记录（2026-09-30 复检）

**主 spec 仍显示 `L122`（两处）与 `L115`（一处）是 pre-archive 预期状态，不是遗漏** —— 修正只存在于本 change 的 delta 中。

本 change 已提交的两处修正状态：

| 修正 | 提交 | HEAD | 工作树 |
|---|---|---|---|
| `config.py:50` `L122→L130` | `a036a15` | 已生效 | 叠加了 peer 的 `vocab_size … # PROBE`（与本行无关） |
| `test_loss.py` 10 处 `actual=` | `b272787` | 已生效（`approx=10 / actual==10`） | **被整段回退**（worktree `actual==0`，diff 为该提交的纯逆操作：−16 / +10） |

回退只发生在工作树，未进入任何 commit。**若 peer 以当前工作树提交，将连带撤销 `b272787` 的 B15 修正**，需在该提交前确认。

## Out of scope / Deferred

- `wayfinder/tickets/A4-1.md:59` 的 `L122` —— 等 `fix-review-findings-voronoi-precision-and-lineage` 归档
- 该 change `tasks.md:19` 的假勾（`[x] 1.4.3` 但 edit 从未进 commit）—— 同上
- 全仓行号引用的 line-drift 抗性改造 —— 需独立 change
