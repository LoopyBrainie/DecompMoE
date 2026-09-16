## 1. Spec Delta (ADDED Requirement)

- [x] 1.1 新增 `openspec/changes/add-cg-n-eq-1-test/specs/wayfinder/spec.md`：ADDED Requirement `CG n=1 boundary behavior` + 3 个 Scenario（positive / negative / zero）+ **`**Source:**` 字段**（治理 req-33 + `scripts/lint_no_source_field_drift.py` 硬约束）

## 2. Test

- [x] 2.1 新增 `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` 闭式对账：
  - `CG(torch.tensor([5.0])) == pytest.approx(5.0, abs=1e-12)`（正元素；**浮点闭式 abs=1e-12**，CLAUDE.md §6 req-gov-1）
  - `CG(torch.tensor([-5.0])) == pytest.approx(5.0, abs=1e-12)`（负元素 magnitude）
  - `CG(torch.tensor([0.0])) == pytest.approx(0.0, abs=1e-12)`（zero）
- [x] 2.2 docstring 反链 `wayfinder Req 20 (CG) L390` + ADDED "CG n=1 boundary behavior"（CLAUDE.md §3 测试需 spec 锚点；原 change 写 L394，现已漂移到 L390）
- [x] 2.3 位置：紧跟 `test_cg_l2_norm_closed_form` 之后（保持 CG 测试闭环）；具体插入点为 L169（`test_cg_l2_norm_closed_form` 函数体结束于 L168，下一函数 `test_sp_orthonormal_aligned_inputs` 定义于 L171）

## 3. Verify

- [x] 3.1 跑 `uv run pytest tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude -v` 通过（3 个断言 abs=1e-12 全部 PASS）—— 实际 `1 passed in 3.16s`
- [x] 3.2 跑全量 `uv run pytest tests/ -v` 确保 **187 → 188 passed**（当前 baseline 187 已因 commit `0554567 fix(spec,test): remove orphan Scenarios + add SP antipodal closed-form` (2026-09-15) 增加 SP antipodal 测试，与原 change 写的 142 → 143 不再匹配）—— 实际 `188 passed, 1 warning in 5.12s`（post-C1 fix：初次运行因 `lint_no_source_field_drift.py` 触发 `tests/test_lint_no_source_field_drift.py::test_no_violations_after_pre_archive_patch` FAIL，实测 `1 failed, 187 passed`；C1 修复 Source 字段首项为 `wayfinder/tickets/A8-2.md` 后重新跑确认 `188 passed`）
- [x] 3.3 跑 `python scripts/lint_no_source_field_drift.py` 确保 exit=0（验证 ADDED Requirement Source 字段结构合规：① 子串存在 ② 反链在 backtick 内 ③ 主反链为第一个 top-level item）—— 实际 `OK (3 file(s) scanned, no violations)`

## 4. Apply & Archive

- [x] 4.1 `openspec validate --strict add-cg-n-eq-1-test`（确认 design artifact 不被强制要求——单测 + spec delta 不满足 design.md 适用条件）—— 实际 `valid: true, no issues`
- [x] 4.2 `python scripts/lint_no_source_field_drift.py` exit=0（archive gate 之一，CLAUDE.md §3）—— 实际 OK
- [x] 4.3 `python scripts/lint_no_dead_defensive.py` exit=0（archive gate 之一，CLAUDE.md §3）—— 实际 `OK (no anti-patterns found)`