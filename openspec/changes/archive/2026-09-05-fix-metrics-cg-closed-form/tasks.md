## 1. Code Fix

- [ ] 1.1 修改 `src/decompmoe/metrics.py:144-156` `CG` 函数实现：`mean pairwise |g_i − g_j|` → `torch.linalg.norm(grad)`（已完成）
- [ ] 1.2 docstring 同步：mean pairwise → L2 norm per spec Req 20（已完成）

## 2. Test Fix

- [ ] 2.1 在 `tests/test_metrics.py` 新增 `test_cg_l2_norm_closed_form` 闭式对账（已完成）
- [ ] 2.2 验证：跑 `uv run pytest tests/test_metrics.py -v` 确保 18 passed（含新测试）

## 3. Apply & Archive

- [ ] 3.1 跑 `openspec validate fix-metrics-cg-closed-form`
- [ ] 3.2 跑 `openspec archive fix-metrics-cg-closed-form --yes`
- [ ] 3.3 archive 后独立复核：跑 `uv run pytest tests/test_metrics.py -v` 全过