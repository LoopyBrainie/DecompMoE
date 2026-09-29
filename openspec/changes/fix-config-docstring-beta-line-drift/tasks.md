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

### D.7 阻塞详情

全量 pytest 报 **1 failed, 207 passed**：

```
tests/test_sphere.py::test_versine_voronoi_closed_form
E  AssertionError: actual=1.7840938828506125e-05
E  assert 1.7840938828506125e-05 == 1.784094e-05   (abs=1e-12)
```

**该失败与本 change 无关**：

- 本 change 从不触碰 `tests/test_sphere.py`（`git diff --numstat -- tests/test_sphere.py` 显示该文件的 21 插 / 5 删全部来自并行 session）
- 该文件 mtime = **20:00 前的两分钟内**，即并行 session 在本 change 落盘期间恢复写入
- 排除该文件后 `uv run pytest --ignore=tests/test_sphere.py` → **192 passed**
- 失败机理：并行 change 新增的断言 `assert dev_16_16 == pytest.approx(1.784094e-5, abs=1e-12)`，实测 `1.7840938828506125e-05`，偏差 `1.17e-12` 略微超过 `abs=1e-12`

**处置**：不修改、不提交、不代为修复该文件（属并行 session 的在途工作）。按 CLAUDE.md §3「archive 前 lint gate 必须 exit=0」与本 change 的前置条件，**在门禁恢复全绿前不执行 archive**。

## E · archive 与后置验证 —— 未执行

> 全部阻塞于 D.7。以下保持未勾状态，待门禁恢复后按序执行。

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

## Out of scope / Deferred

- `wayfinder/tickets/A4-1.md:59` 的 `L122` —— 等 `fix-review-findings-voronoi-precision-and-lineage` 归档
- 该 change `tasks.md:19` 的假勾（`[x] 1.4.3` 但 edit 从未进 commit）—— 同上
- 全仓行号引用的 line-drift 抗性改造 —— 需独立 change
