# 修复 B.4 治理义务缺口 B15 — `tests/test_loss.py` obligation 5 合规

## Why

`governance` spec `req-gov-1` 第 5 条义务（`openspec/specs/governance/spec.md:24`）：

> Every assertion **described in obligations 1, 2, and 3** (and the frame-disambiguation obligation 4) MUST embed `f"actual={...}"` in its failure message so a numerical regression surfaces the actual computed value at the assertion site.

原 reviewer 报「`test_loss.py` 0/10 (0%)，执行率极不均衡」。经核验，**finding 成立但全部数字错误，且真实缺陷形态与报告不同**。

### 真实缺陷形态：不是「0% 合规」，是 9 处缺 token + 1 处完全盲区

AST 复测（口径：测试函数自身源码区间内是否含 `actual=`）后逐条打开 `tests/test_loss.py` 的 10 个 `pytest.approx` 断言：

| 行 | 改动前 | 分类 |
|---|---|---|
| L33 | `f"L_lb_raw(uniform) = {…}, expected 1.0"` | **有值，缺 `actual=` token** |
| L36 | `f"L_lb = α · 1.0 must equal 0.01; got {…}"` | **有值，缺 token** |
| L74 | `f"L_lb(uniform) = {…}, expected α · 1.0 = 0.01 per …"` | **有值，缺 token** |
| L156 | `f"phase {phase} should have λ=0 ⇒ L_sep=0; got {parts.L_sep}"` | **有值，缺 token** |
| **L177** | **无 message** | **完全盲区** |
| L178 | `f"λ(41_000)={lam_mid}"` | 有值，缺 token |
| L179 | `f"λ(55_999)={lam_end}"` | 有值，缺 token |
| L207 | `f"L_sep(orthonormal basis) = {…}, expected 0"` | 有值，缺 token |
| L228 | `f"L_sep mismatch: got {…}, expected {…}"` | 有值，缺 token |
| L240 | `f"L_sep pair-wise form mismatch: got {…}, expected {…}"` | 有值，缺 token |

**这个区分决定工作量与风险**：报成「0% 合规」会让人以为要补 10 处消息；实际是 **9 处加前缀 + 1 处新建 message**。后者是一次机械的前缀操作，前者是重新设计诊断文案。

**只有 L177 是真正的诊断盲区** —— `assert lam_start == pytest.approx(0.0, abs=1e-12)` 失败时 pytest 只报断言本身，不报任何计算值。它也是本 change 唯一需要新写文案而非改前缀的站点。

### 原报告的统计口径错误

原报告报出：`test_loss.py 0/10 (0%)`、`test_schedule.py 2/17`、`test_metrics.py 5/25`、`test_safeguards.py 13/56`、`test_sphere.py 122%`、`test_extraction.py 300%`、`test_config.py 267%`。

三处问题：

1. **分母不存在**：报告的分母 10 / 25 / 56 在本仓无对应。`git grep -c "^def test_"` 实际为 **9 / 29 / 35**。
2. **`>100%` 是未标注的比值**：`122%` / `300%` / `267%` = 「`actual=` 出现次数 ÷ 测试函数数」。一个测试函数含多条断言时该比值天然可超 1。报告在同一份表里把「出现次数 ÷ 测试数」（`0/10` 形式）和「达标测试数 ÷ 测试数」混用而未标注。
3. **零命中文件漏报 3 个**：实际有 5 个零 `actual=` 文件（报告只提 `test_loss.py`）。

**诚实基线（AST 口径，基线 commit `7bf77af`）**：

| 指标 | 值 |
|---|---|
| 测试函数总数 | **207** |
| 达标（自身区间含 `actual=`） | **30（14.5%）** |

达标明细（`达标 / 测试数`）：`test_sphere.py` 8/16、`test_config.py` 6/12、`test_schedule.py` 3/17、`test_beta.py` 3/13、`test_safeguards.py` 3/34、`test_extraction.py` 2/14、`test_distance.py` 1/6、`test_experts.py` 1/9、`test_gating.py` 1/6、`test_metrics.py` 1/29、`test_viz_protocols.py` 1/3、`test_loss.py` **0/9**、`test_contracts.py` 0/6、`test_extraction_phase.py` 0/7、`test_merge_spec_deltas.py` 0/8、`test_lint_no_source_field_drift.py` 0/18。

> **本 change 计划稿的数字纠正**：计划稿把基线记作 31/208 (14.9%)、把 `test_loss.py` 修复后达标率记作 9/9、把全仓修复后记作「约 19%」。三处均经 AST 复测修正为 **30/207 (14.5%)**、**6/9**、**36/207 (17.4%)**（见下）。差额来源见 design.md Decision 3。

## 范围判定：为什么只改 `test_loss.py`

`req-gov-1` 第 5 条**显式绑定义务 1–3**，而义务 1–3 只覆盖「spec 锚定的闭式数值断言」；preamble（`:11`）进一步限定为 *"every **spec-anchored** closed-form numerical claim"*。

对其余 4 个零 `actual=` 文件逐一判定：

| 文件 | 测试数 | `pytest.approx` 数 | 判定 |
|---|---|---|---|
| `tests/test_contracts.py` | 6 | 0 | **范围外** —— 纯签名 / 结构断言 |
| `tests/test_extraction_phase.py` | 7 | 0 | **范围外** —— 无 `pytest.approx` |
| `tests/test_merge_spec_deltas.py` | 8 | 0 | **范围外** —— delta 合并结构断言 |
| `tests/test_lint_no_source_field_drift.py` | 18 | 0 | **范围外** —— anchor / 反链 lint 守卫 |

**这些是「已判定范围外」，不是「延后处理」**。把它们拉进来「顺手补齐」会产生无意义的噪声 diff —— 没有 `pytest.approx` 断言的文件，义务 5 根本不适用。

`.audit/` 全域 `actual=` **零命中**，即本状态此前无任何先例被承认。

## What changes

对 `tests/test_loss.py` 的 10 处断言：

- **L177**：新增 message（唯一完全盲区），采用与同函数 L178/L179 一致的 `λ(t)` 风格
- **其余 9 处**：在消息中**补入 `actual={…}` 前缀，保留全部原有诊断上下文**

**不删除任何既有诊断信息**。例：L156 原为 `f"phase {phase} should have λ=0 ⇒ L_sep=0; got {parts.L_sep}"`，改为 `f"actual={parts.L_sep.item()}; phase {phase} should have λ=0 ⇒ L_sep=0"` —— 语义等价且 `actual=` 前置，同时把张量 repr 换成标量以利诊断。

## 明确不做（Non-goals）

- **不改任何 `pytest.approx` 的 `abs=` 字面**（实测改动前后 12 个 `abs=` 值逐一相同）
- 不改断言的比较对象、不改 `test_loss.py` 之外的任何测试文件
- **不触碰 `req-gov-1`** —— 并行 change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` 正在整块重写该 Requirement 的 delta，触碰会冲突
- 不用本 change 的测试文案反向 close 任何 spec Requirement —— 失败信息是纯诊断内容，不构成可验条款
- 不新增整数闭式断言（obligation 1 用 bare `==`）；本文件现状无整数闭式断言

## 无 spec delta

纯 test 侧变更，`test_loss.py` 是 obligation 5 的**守门对象**而非义务的**定义源**。义务定义在 `governance` spec，不因本文件合规而改变。故**不创建 `specs/` 目录**，archive 零 anchor 风险。
