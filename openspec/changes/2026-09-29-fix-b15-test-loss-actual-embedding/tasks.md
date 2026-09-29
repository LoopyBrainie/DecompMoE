# Tasks — B15 `test_loss.py` obligation 5

> 计量口径：AST，判据为「测试函数自身源码区间内是否含 `actual=`」。基线 commit `7bf77af`（实测 30/207 = 14.5%）。

## A · 核验与范围判定

- [x] A.1 定位 `req-gov-1` 第 5 条原文与义务总数（6 条），确认义务编号正确
- [x] A.2 确认义务 5 绑定范围为义务 1–3（spec 锚定闭式数值断言），preamble 限定 *spec-anchored closed-form numerical claim*
- [x] A.3 AST 复测全仓基线：**207 个测试函数 / 30 个达标 = 14.5%**（纠正计划稿的 31/208 = 14.9%）
- [x] A.4 逐文件列出达标明细（16 个文件）
- [x] A.5 判定 4 个零 `actual=` 文件为**范围外**（各 0 个 `pytest.approx`），非延后
- [x] A.6 确认 `.audit/` 全域 `actual=` 零命中（无先例承认此状态）
- [x] A.7 确认 `test_loss.py` 9 个函数中仅 6 个含 `pytest.approx`（另 3 个用 `allclose` / 结构 / 字符串断言，天然范围外）

## B · 代码变更（10 处断言）

- [x] B.1 L177 —— 唯一**完全无 message** 的盲区，新增 `f"actual={lam_start}; λ(26_000) should be 0 at the phase-3 ramp start"`
- [x] B.2 L33 / L36 / L74 —— 补 `actual=` 前缀，保留 L74 的 spec closed-form 溯源文本
- [x] B.3 L156 —— 补前缀，并把 `{parts.L_sep}`（张量 repr）改为 `{parts.L_sep.item()}`（标量），保留 `phase {phase} should have λ=0 ⇒ L_sep=0`
- [x] B.4 L178 / L179 —— 补前缀，与 L177 同用 `λ(t)` 风格
- [x] B.5 L207 / L228 / L240 —— 补前缀；L228 局部变量名为 `actual`，`f"actual={actual.item()}"` 读来自然
- [x] B.6 确认**未删除任何既有诊断信息**（9 处均为前缀追加，非替换）
- [x] B.7 确认**未新增/修改任何 `pytest.approx` 参数**（12 个 `abs=` 字面逐一比对相同）
- [x] B.8 确认 `test_loss.py` 之外的测试文件零改动

## C · 制品

- [x] C.1 `.openspec.yaml`（`schema: spec-driven` / `created: 2026-09-29`）
- [x] C.2 `proposal.md` —— 含原报告三处统计口径错误与本 change 计划稿三处数字纠正
- [x] C.3 `design.md` —— 4 项 Decision
- [x] C.4 `tasks.md`（本文件）
- [x] C.5 确认**不创建** `specs/` 目录（纯 test 侧，不触碰 `req-gov-1`）

## D · 验收

- [x] D.1 断言级：`pytest.approx` 出现 10 次 / `actual=` 出现 10 次，一一对应
- [x] D.2 `abs=` 字面 HEAD vs 改动后逐一相同（实测两串完全一致）
- [x] D.3 `uv run pytest tests/test_loss.py` → **9 passed**
- [x] D.4 `uv run pytest` → **208 passed**
- [x] D.5 `python scripts/lint_no_dead_defensive.py` → exit 0
- [x] D.6 `python scripts/lint_no_source_field_drift.py` → exit 0
- [x] D.7 `git status --short -- openspec/specs/` 为空（`req-gov-1` 零改动）
- [x] D.8 隔离口径复测：30/207 (14.5%) → 36/207 (17.4%)，`test_loss.py` 0/9 → 6/9
- [x] D.9 记录工作树污染警告：直接复测工作树得 37/208，因并行 change 的 `test_safeguards.py` 未提交改动 +1 函数，非本 change 效果
- [x] D.10 提交后断言工作树 == commit object

## Out of scope

- `tests/test_contracts.py` / `test_extraction_phase.py` / `test_merge_spec_deltas.py` / `test_lint_no_source_field_drift.py` —— 各 0 个 `pytest.approx`，已判定**范围外**（非延后）
- `req-gov-1` 本身 —— 并行 change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` 正在整块重写其 delta
- 全仓 14.5% 基线的治理（覆盖率口径定义）—— 超出本 change 范围，见 proposal「不做」节
