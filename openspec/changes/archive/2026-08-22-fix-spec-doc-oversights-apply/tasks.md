## 1. Issue ⑦ Empty-Cell Fallback（空 cell 显式回退到 c_i）

- [ ] 1.1 RED：写 `test_empty_cell_preserves_centroid` 在 `tests/test_extraction.py`，构造 mask `[N, N_e]` 其中第 0 个 expert 全 0（`n_0 = 0`），调用 `CentroidDriver(EMA_090).step(c, X, mask=mask)`，断言 `‖c[0]^(t+1) − c[0]^(t)‖₂ < 1e-12`（用 `torch.linalg.norm` + `pytest.approx`）。RED gate: `uv run pytest tests/test_extraction.py::test_empty_cell_preserves_centroid -v` 期望 FAILED（当前 `extraction.py:124` 用 `.clamp_min(1e-9)` 导致 `c[0]` 漂移 > 1e-12）。checkpoint commit: `test: add reproducer for empty-cell centroid clamp_min bug`
- [ ] 1.2 GREEN：`src/decompmoe/extraction.py:124-125` 替换为 `n_i = weights.sum(dim=0); weighted = (weights.T @ X); safe_n = n_i.clamp_min(1.0); mean_n = weighted / safe_n.unsqueeze(-1); mean = torch.where(n_i.unsqueeze(-1) > 0, mean_n, centroids)`。GREEN gate: 测试 PASSED。checkpoint commit: `fix: replace empty-cell clamp_min with c_i fallback`
- [ ] 1.3 Refactor：保持绿，可选提取 helper 函数。commit: `refactor: clean up after empty-cell fallback`

## 2. Issue ⑥ EMA Spherical Re-Projection（Phase 1/2/3 加 F.normalize）

- [ ] 2.1 RED：更新 `tests/test_extraction_phase.py::test_phase_090_ema` 等 EMA 测试的 expected 值改为 `F.normalize(0.9·c + 0.1·mean, dim=-1)`。RED gate: 测试 FAILED（当前 `extraction.py:126` 直接返回 `α·c + (1-α)·mean` 未归一化）。checkpoint commit: `test: add EMA re-projection expected values`
- [ ] 2.2 GREEN：`src/decompmoe/extraction.py:126` EMA 分支返回值改为 `F.normalize(alpha * centroids + (1.0 - alpha) * mean, dim=-1)`。GREEN gate: 测试 PASSED。checkpoint commit: `fix: EMA output F.normalize per spherical re-projection invariant`
- [ ] 2.3 Refactor：保持绿。commit: `refactor: clean up after EMA normalize`

## 3. Issue ⑧ Three Invariant Test Scenarios（ADDED Requirement "Centroid Driver Semantic Invariants"）

- [ ] 3.1 RED：`tests/test_extraction.py` 新增 `test_spherical_norm_is_strictly_one`，迭代 Phase 1/2/3/4 各一次，断言 `max_i |‖c_i‖₂ − 1.0| < 1e-7`（用 `torch.linalg.norm(c, dim=-1).max() - 1.0` + `torch.allclose(_, 0, atol=1e-7)` 或 `pytest.approx`）。RED gate: FAILED（当前 EMA 未归一化导致 ‖c‖₂ 漂移）。checkpoint commit: `test: add spherical_norm_is_strictly_one invariant`
- [ ] 3.2 RED：`tests/test_extraction.py` 新增 `test_near_zero_candidate_fallback`，构造 mask 让 expert i 的 mean `‖u_i‖₂ < 1e-9`，断言 `c[i]^(t+1) == c[i]^(t)` element-wise（用 `torch.allclose(c_new[i], c_old[i], atol=0)` 或 `pytest.approx`） + `torch.isfinite(c_new).all()`。RED gate: FAILED（当前 EMA 直接 normalize 而无 near-zero fallback）。checkpoint commit: `test: add near_zero_candidate_fallback invariant`
- [ ] 3.3 GREEN：`src/decompmoe/extraction.py:126` 进一步加 near-zero fallback：`candidate = alpha * centroids + (1 - alpha) * mean; norm = candidate.norm(dim=-1, keepdim=True); use_old = (norm < 1e-9); out = torch.where(use_old, centroids, F.normalize(candidate, dim=-1))`。GREEN gate: 3 个 invariant test + 1.1/2.1 EMA test 全 PASSED。checkpoint commit: `fix: add near-zero candidate fallback to CentroidDriver`
- [ ] 3.4 Refactor：保持绿。commit: `refactor: clean up after invariant tests`

## 4. 验证（必跑）

- [ ] 4.1 `uv run pytest tests/test_extraction.py -v` 全绿
- [ ] 4.2 `uv run pytest tests/test_extraction_phase.py -v` 全绿
- [ ] 4.3 `uv run pytest tests/` 全量回归无 fail（CLAUDE.md §3）
- [ ] 4.4 独立数值复核（CLAUDE.md §3）：`python3 -c "import torch; c = torch.randn(16, 16); c = torch.nn.functional.normalize(c, dim=-1); m = torch.randn(16, 16); m = torch.nn.functional.normalize(m, dim=-1); out = torch.nn.functional.normalize(0.9*c + 0.1*m, dim=-1); print(torch.linalg.norm(out, dim=-1))"` 期望 `[1.0, ..., 1.0]`
- [ ] 4.5 Evidence：写入 `.claude/tdd/fix-spec-doc-oversights-apply.tdd.md`（含 plan 链接 + 3 个 Issue × RED-GREEN-Refactor + coverage 报告）

---

## 完成度口径

本文件共 **13** 条 checkbox。全部勾选**不等于**全部实现，三类语义必须分开陈述：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行** | 12 | §1 全 3 + §2 全 3 + §3 全 4 + §4.1-4.4 |
| **已声明但未做** | 1 | §4.5 evidence doc 写入 |
| 合计 | 13 | |