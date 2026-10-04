# Tasks

## 1. 记录更正（归档不可变，记在本 change）

- [x] 1.1 B-1：第四份 change 的 errata 表无「检测器版本」列，6 行 5 行无标注；`1526b98` 行只标 old（189），measured 198 未标；`724 / 636` 整行未标，而该数版本相关（`EXT_EXTENSIONS` 与 `in_scope` 本轮均改）。D8 规则 + `tasks.md` 6.3 `[x]` 均未在制品中兑现。
- [x] 1.2 B-2：`design.md` D5 与 `tasks.md` 4.1 写「14 个必须在内」，括号枚举为 15；代码 `PINNED_IN_SCOPE` 15 项，`proposal.md` 写「15 进 / 4 出」。
- [x] 1.3 两者均不写回归档件；本 change 的 `proposal.md` 记录事实与成因。

## 2. B-3 前缀语义（D1）

- [x] 2.1 `in_scope` 的 `any(x in f ...)` → `any(f.startswith(x) ...)`。
- [x] 2.2 `in_scope` docstring 写明前缀语义 + 举出会被误剔的 spec 路径。
- [x] 2.3 `SELF_EXCLUDE` 注释写明 `in_scope` 用 `startswith` 匹配。
- [x] 2.4 守护测试 `test_self_exclude_is_a_prefix_not_a_substring`：目录前缀仍覆盖（2 条正例），仅包含子串的不覆盖（3 条反例，含一条 spec 路径）。

## 3. B-5 单源真相（D2 / D3）

- [x] 3.1 `PINNED_IN_SCOPE`（15）与 `PINNED_OUT_OF_SCOPE`（4）移入 `pointer_scan.py`，紧邻 `SELF_EXCLUDE`，附「总数抓不住减法」的成因注释。
- [x] 3.2 `lint_pointer_detector.py` 改为 `PINNED_IN_SCOPE = ps.PINNED_IN_SCOPE` / `PINNED_OUT_OF_SCOPE = ps.PINNED_OUT_OF_SCOPE`，不再持有字面量。
- [x] 3.3 守护测试改为遍历 `ps.PINNED_IN_SCOPE` / `ps.PINNED_OUT_OF_SCOPE`，**先断言计数 15 / 4**，再断言不相交，最后逐条对 `in_scope` 核对。
- [x] 3.4 `lint_pointer_detector.py` 仍 83 checks ≥ `MIN_CHECKS = 80`。

## 4. B-4 注释对齐（D4）

- [x] 4.1 `_exempt` docstring 的例子换成 marker 在前的 `marker ... A ... B`（真正能触发 `others`）。
- [x] 4.2 写明 `_crosses_another_locator` 对称（两个方向都查）。
- [x] 4.3 写明跨越需要 marker 与目标**之间严格**存在另一个 tracked locator；`A (marker) ... B` 无可跨越对象，判定退回 `EXEMPT_WINDOW` 与句读。
- [x] 4.4 明确原例子（裸 `L100` 无路径/能力词前缀）不是 tracked locator，`others` 无从跨越，该形态记为残留而非已修。**行为不改。**

## 5. B-6 反向分支守护

- [x] 5.1 `test_marker_may_not_reach_across_another_locator_to_the_right`：`old: spec.md L100 spec.md L453 (historical, was 1/64)`，断言 L100 活、L453 豁免。
- [x] 5.2 探针先于断言存在：镜像方向的实际行为经独立探针确认后才写测试，删掉 `_crosses_another_locator` 的反向子句会使其变红。

## 6. 验证

- [x] 6.1 `pytest tests/test_pointer_scan.py tests/test_lint_no_line_pointers.py` → 95 passed（原 93，+2）。
- [x] 6.2 `scripts/lint_pointer_detector.py` → 83 checks, exit 0, `DETECTOR FIT`。
- [x] 6.3 `scripts/lint_no_line_pointers.py` → exit 0, 35 files, no violations。
- [x] 6.4 baseline 数字无回归：`1526b98` 仍 224 sites / 209 actionable / 198 strong；活树仍 5 sites / 0 actionable / 5 historical / 3 files。
- [x] 6.5 全量 `run_gates.py --change <name>` → GATE OK，pytest 全绿。
      首次在主工作树跑出 `GATE RESULT INVALID`（exit 2，tracked/untracked digest 均 CHANGED）——并行 session 在门禁运行期间改动了 16 个 tracked 文件，其中 7 个在 `PINNED_IN_SCOPE` 内。改在 `git worktree add --detach` 出的静止树上重跑：`head=c7137ef dirty_entries=0` → `GATE OK`，pytest 424 passed / 1 skipped。
- [x] 6.6 `openspec validate <change> --strict` 通过（需先在 `.openspec.yaml` 声明 `skip_specs: true`，本 change 无 delta）。
- [ ] 6.7 归档后 `git ls-tree` 对活跃路径返回空。

## 7. 不做

- [ ] 7.1 A-1：`wayfinder/spec.md:824` 强制要求的 `pytest.approx(0.196901, abs=1e-3)` 在 `tests/` 与 `src/` 内零命中。既存缺陷，非本 session 造成，需独立 change（只需在 `tests/test_safeguards.py` 补一条断言）。
- [ ] 7.2 A-2 / A-3：spec 侧 6 位有效数字与百分比取整。同上。
- [ ] 7.3 `A (marker) ... B` 形态的语义收窄：无结构线索，泛化会与规范注解冲突。
- [ ] 7.4 `run_gates.py` 两条工具缺陷属并行 session，只报告不碰。
