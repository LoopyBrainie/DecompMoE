# governance spec delta — NOT APPLICABLE

This change `01-fix-ticket-stale-numerical-4file-batch` does **NOT** require any new `governance` capability Requirement or delta.

**Rationale** (per CLAUDE.md §6 第 8 条 + governance/spec.md req-gov-1):

本 change 的浮点闭式断言 `tests/test_beta.py:38` `assert MVPConfig().beta_initial == pytest.approx(1.035, abs=1e-6)` **直接合规**于现有 governance/spec.md req-gov-1 第 2 条:

> "Closed-form float claims ... MUST use `pytest.approx(value, abs=...)` with the tolerance matching the closed-form computation's actual precision — NOT bare `==`."

无需新增 governance Requirement。governance/spec.md req-gov-1 第 2 条已为本 change 的 test 形式提供 spec 级别背书。

**Governance 适用性**（不需要本 change 新增条款）：
- governance/spec.md req-gov-1 第 1 条（整数闭式 bare `==`）—— 不适用（本 change 不引入新整数闭式）
- governance/spec.md req-gov-1 第 2 条（浮点闭式 pytest.approx）—— 直接合规（D1.1 已落实）
- governance/spec.md req-gov-1 第 3 条（bisection Voronoi `abs=1e-6`）—— 不适用（本 change 不修改 Voronoi 测试）
- governance/spec.md req-gov-1 第 4 条（`f"actual={...}"` 失败信息）—— 直接合规（D1.1 已嵌入 f-string）

**结论**: 本 change 不动 `governance` capability spec。本 placeholder 文件存在仅为 audit trail 完整性，明确"不适用"理由。