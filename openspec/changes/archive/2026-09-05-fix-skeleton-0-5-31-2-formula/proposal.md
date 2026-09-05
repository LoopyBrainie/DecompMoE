## Why

`openspec/specs/decompmoe-skeleton/spec.md` L434 在说明 `MAX_GRAD_PER_GAMMA_PHASE4` 常量推导时使用了字面算式 `0.5 · 31 · 2 = 15.5`，但 `0.5 · 31 · 2` 的闭式代入结果为 `31`，并非 `15.5`。该 spec 文本已被审计独立 verifier 确认与 `src/decompmoe/beta.py:39` 的实际导出 `0.5 * 31.0 = 15.5`（无 `· 2`）不一致——即 code 数值对但 spec 推导链断。后果：(a) 后续读者无法从 spec 文本自身复算 15.5；(b) 若 code 重构修改 31.0，spec 字面算式会立即与 code 暴露矛盾而非保护 code。

## What Changes

- `openspec/specs/decompmoe-skeleton/spec.md` L434：「the **operational-domain Phase 4** worst case is `0.5 · 31 · 2 = 15.5` for `γ' = 0, inner = −1`」改为「the **operational-domain Phase 4** worst case is `0.5 · 31 = 15.5` at `γ' = 0`」（删除多余的 `· 2` 与 `inner = −1`，与 `src/decompmoe/beta.py:37-39` docstring 对齐）
- 无 code 改动（数值已正确，常量 `MAX_GRAD_PER_GAMMA_PHASE4 = 0.5 * 31.0 = 15.5` 保持）
- 无 test 改动（既有 `test_beta.py::test_constants_exported` 已用 `pytest.approx` 对账 15.5）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `decompmoe-skeleton` — Requirement `Beta Parameterization Operational Domain` 的文本描述（推导链字面算式）修正；常量数值 `MAX_GRAD_PER_GAMMA_PHASE4 = 15.5` 与语义不变

## Impact

- 受影响文件：`openspec/specs/decompmoe-skeleton/spec.md`（L434）
- 反链：审计报告 `.audit/audit-report.md` 中 CRIT-1（已确认）；`REVIEW-LEDGER.md (commit f8e5b26)` A-Finding-1（仅 docstring label 修复，**用户决策"仅记录"**——本次 spec 文本修复未涉及 docstring label，沿用户原决策不主动修改 `beta.py:38` / `test_beta.py:134, 137`）
- 验收基线：`uv run pytest tests/test_beta.py -v` 全过；spec 文本与 code `beta.py:39` 字面一致
- 无破坏性变更（数值不变；下游消费者无影响）