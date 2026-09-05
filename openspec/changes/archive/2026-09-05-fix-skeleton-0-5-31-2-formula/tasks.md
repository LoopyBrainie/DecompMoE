## 1. Spec Text Correction

- [ ] 1.1 修改 `openspec/specs/decompmoe-skeleton/spec.md` L434 字面算式 `0.5 · 31 · 2 = 15.5 for γ' = 0, inner = −1` → `0.5 · 31 = 15.5 at γ' = 0`（已完成）

- [ ] 1.2 验证 spec 文本与 `src/decompmoe/beta.py:39` 字面一致：跑 `uv run pytest tests/test_beta.py::test_constants_exported -v`，确保 `MAX_GRAD_PER_GAMMA_PHASE4 == 15.5` 通过

- [ ] 1.3 跑全量测试 `uv run pytest tests/test_beta.py -v` 确保无回归

## 2. Apply & Archive

- [ ] 2.1 跑 `openspec validate fix-skeleton-0-5-31-2-formula` 确保 change 通过 schema 校验

- [ ] 2.2 跑 `openspec archive fix-skeleton-0-5-31-2-formula --yes` 把 delta 合并回 main spec，archive 到 `openspec/changes/archive/2026-09-04-fix-skeleton-0-5-31-2-formula/`

- [ ] 2.3 archive 后独立复核：读 archive 后的 `openspec/specs/decompmoe-skeleton/spec.md` L434，确认字面算式 `0.5 · 31 = 15.5` 与 `beta.py:39` 一致