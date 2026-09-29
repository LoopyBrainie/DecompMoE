# Design — B15 `test_loss.py` obligation 5 合规

## Decision 1：按「有值无 token」与「完全无值」分两类处理

**Choice**：9 处加 `actual={…}` 前缀并保留原诊断上下文；L177 新建 message。

**Alternatives**：

- **(a) 10 处统一重写为仅 `f"actual={…}"`** —— 拒绝。会把已有的 spec 溯源信息（如 L74 的 `expected α · 1.0 = 0.01 per spec closed form α · N_e · Σ (1/N_e) · (1/N_e)`）删掉。这些文本解释了**为什么**期望值是该值，删掉后失败信息会从「可诊断」退化为「可定位」。CLAUDE.md §3 要求诊断信息内嵌实际值，**不是**要求丢弃上下文。
- **(b) 只给 L177 补 message，9 处不动** —— 拒绝。obligation 5 的字面要求是 embed `f"actual={…}"` 这一形式；`f"L_sep mismatch: got {x}, expected {y}"` 语义上有值但形式上不满足义务。

**Rationale**：义务约束的是**形式**（`actual=` token，使实际值可被工具/grep 稳定提取），诊断质量约束的是**内容**。两者都要满足，故为「加前缀」而非「替换」。

## Decision 2：L156 的 `{parts.L_sep}` 改为 `{parts.L_sep.item()}`

**Choice**：L156 原消息嵌入的是张量 repr（`tensor(1.23e-17, grad_fn=...)`），改为 `.item()` 标量。

**Rationale**：该站点其余 9 处均用 `.item()`，张量 repr 在失败输出里带 `grad_fn=`，反而降低可读性。此改动**不改变断言语义**，只影响失败时的显示形式，且保留了原有 `phase {phase} should have λ=0 ⇒ L_sep=0` 的解释文本。

## Decision 3：范围限定 `test_loss.py` 单文件

**Choice**：只改 10 处，不动其余 4 个零 `actual=` 文件。

**Rationale**：`req-gov-1` obligation 5 绑定义务 1–3（spec 锚定闭式数值断言）。这 4 个文件 `pytest.approx` 计数为 0，义务不适用。**「已判定范围外」不等于「延后」** —— 若未来它们新增数值断言，届时才需补 `actual=`。

**Consequence**：`test_loss.py` 的**断言级**指标达 10/10（全部 `pytest.approx` 断言均含 `actual=`），但**函数级**指标是 **6/9** —— 该文件 9 个测试中有 3 个不含任何 `pytest.approx` 断言（`test_lb_uses_detached_fractions` 用 `assert ... is not None` 类结构断言、`test_lambda_fixed_phase_4` 用 `torch.allclose`、`test_token_vs_expert_C_notation` 用字符串包含断言），这 3 个天然在义务 5 范围外。

全仓函数级基线 **30/207 (14.5%) → 36/207 (17.4%)**。

> **工作树污染警告**：直接在当前工作树复测会得到 37/208 (17.8%)，因为并行 change 的未提交改动给 `tests/test_safeguards.py` 增加了 1 个测试函数（34→35，达标 3→4）。**该数字不可作为本 change 的效果**。隔离口径必须用 commit object（`git show HEAD:tests/…`）作基线。剩余 171 个未达标函数中绝大多数落在义务 5 范围外。

## Decision 4：不触碰 `req-gov-1`

**Choice**：不修改 `openspec/specs/governance/spec.md`，不产生 `specs/` delta。

**Rationale**：并行 change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` 正在整块重写 `req-gov-1`（其 `specs/governance/spec.md` 是一份完整的 MODIFIED Requirement）。本 change 若也写 `req-gov-1`，两个 delta 会在 archive 时争抢同一 Requirement block。

**Consequence**：本 change archive 零 anchor 风险。

## Risk

- **[Risk] `actual=` 前缀可能与既有文案重复实际值**（如 L228 的 `f"actual={actual.item()}; L_sep expected {…}"`）—— 接受。重复的是「实际值」与「期望值」两个不同量，不冗余；且该站点局部变量本就名为 `actual`，`f"actual={actual.item()}"` 读来自然。
- **[Non-Risk] 断言语义零变化** —— 全部 12 个 `abs=` 字面实测逐一相同（改动前后 diff 见 tasks.md 验收项），断言左侧与 `pytest.approx` 参数均未触碰。
- **[Risk] 未来新增数值断言时再次遗漏** —— 本 change 无法预防；根治需 spec 侧定义覆盖率口径，已登记为 deferred。
