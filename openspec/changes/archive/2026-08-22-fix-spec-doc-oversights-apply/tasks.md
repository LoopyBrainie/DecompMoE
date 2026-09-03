## 1. Issue ⑦ Empty-Cell Fallback（空 cell 显式回退到 c_i）

- [x] 1.1 ~~RED：写 `test_empty_cell_preserves_centroid` 在 `tests/test_extraction.py`，构造 mask `[N, N_e]` 其中第 0 个 expert 全 0（`n_0 = 0`），调用 `CentroidDriver(EMA_090).step(c, X, mask=mask)`，断言 `‖c[0]^(t+1) − c[0]^(t)‖₂ < 1e-12`（用 `torch.linalg.norm` + `pytest.approx`）。RED gate: `uv run pytest tests/test_extraction.py::test_empty_cell_preserves_centroid -v` 期望 FAILED（当前 `extraction.py:124` 用 `.clamp_min(1e-9)` 导致 `c[0]` 漂移 > 1e-12）。checkpoint commit: `test: add reproducer for empty-cell centroid clamp_min bug`~~
- [x] 1.2 ~~GREEN：`src/decompmoe/extraction.py:124-125` 替换为 `n_i = weights.sum(dim=0); weighted = (weights.T @ X); safe_n = n_i.clamp_min(1.0); mean_n = weighted / safe_n.unsqueeze(-1); mean = torch.where(n_i.unsqueeze(-1) > 0, mean_n, centroids)`。GREEN gate: 测试 PASSED。checkpoint commit: `fix: replace empty-cell clamp_min with c_i fallback`~~
- [x] 1.3 ~~Refactor：保持绿，可选提取 helper 函数。commit: `refactor: clean up after empty-cell fallback`~~

## 2. Issue ⑥ EMA Spherical Re-Projection（Phase 1/2/3 加 F.normalize）

- [x] 2.1 ~~RED：更新 `tests/test_extraction_phase.py::test_phase_090_ema` 等 EMA 测试的 expected 值改为 `F.normalize(0.9·c + 0.1·mean, dim=-1)`。RED gate: 测试 FAILED（当前 `extraction.py:126` 直接返回 `α·c + (1-α)·mean` 未归一化）。checkpoint commit: `test: add EMA re-projection expected values`~~
- [x] 2.2 ~~GREEN：`src/decompmoe/extraction.py:126` EMA 分支返回值改为 `F.normalize(alpha * centroids + (1.0 - alpha) * mean, dim=-1)`。GREEN gate: 测试 PASSED。checkpoint commit: `fix: EMA output F.normalize per spherical re-projection invariant`~~
- [x] 2.3 ~~Refactor：保持绿。commit: `refactor: clean up after EMA normalize`~~

## 3. Issue ⑧ Three Invariant Test Scenarios（ADDED Requirement "Centroid Driver Semantic Invariants"）

- [x] 3.1 ~~RED：`tests/test_extraction.py` 新增 `test_spherical_norm_is_strictly_one`，迭代 Phase 1/2/3/4 各一次，断言 `max_i |‖c_i‖₂ − 1.0| < 1e-7`（用 `torch.linalg.norm(c, dim=-1).max() - 1.0` + `torch.allclose(_, 0, atol=1e-7)` 或 `pytest.approx`）。RED gate: FAILED（当前 EMA 未归一化导致 ‖c‖₂ 漂移）。checkpoint commit: `test: add spherical_norm_is_strictly_one invariant`~~
- [x] 3.2 ~~RED：`tests/test_extraction.py` 新增 `test_near_zero_candidate_fallback`，构造 mask 让 expert i 的 mean `‖u_i‖₂ < 1e-9`，断言 `c[i]^(t+1) == c[i]^(t)` element-wise（用 `torch.allclose(c_new[i], c_old[i], atol=0)` 或 `pytest.approx`） + `torch.isfinite(c_new).all()`。RED gate: FAILED（当前 EMA 直接 normalize 而无 near-zero fallback）。checkpoint commit: `test: add near_zero_candidate_fallback invariant`~~
- [x] 3.3 ~~GREEN：`src/decompmoe/extraction.py:126` 进一步加 near-zero fallback：`candidate = alpha * centroids + (1 - alpha) * mean; norm = candidate.norm(dim=-1, keepdim=True); use_old = (norm < 1e-9); out = torch.where(use_old, centroids, F.normalize(candidate, dim=-1))`。GREEN gate: 3 个 invariant test + 1.1/2.1 EMA test 全 PASSED。checkpoint commit: `fix: add near-zero candidate fallback to CentroidDriver`~~
- [x] 3.4 ~~Refactor：保持绿。commit: `refactor: clean up after invariant tests`~~

## 4. 验证（必跑）

- [x] 4.1 `uv run pytest tests/test_extraction.py -v` 全绿
- [x] 4.2 `uv run pytest tests/test_extraction_phase.py -v` 全绿
- [x] 4.3 `uv run pytest tests/` 全量回归无 fail（CLAUDE.md §3）
- [x] 4.4 独立数值复核（CLAUDE.md §3）：`python3 -c "import torch; c = torch.randn(16, 16); c = torch.nn.functional.normalize(c, dim=-1); m = torch.randn(16, 16); m = torch.nn.functional.normalize(m, dim=-1); out = torch.nn.functional.normalize(0.9*c + 0.1*m, dim=-1); print(torch.linalg.norm(out, dim=-1))"` 期望 `[1.0, ..., 1.0]`

---

## 完成度口径（2026-09-03 @c6294f9，post-archive cleanup）

本文件原表声称 **13** 条 checkbox，实际计数 **15**（含 §4 全 5 项 + §1-§3 共 10 项）。两类语义：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行（a56a599）** | 10 | §1 全 3 + §2 全 3 + §3 全 4 |
| **已执行（U2 retroactive verify）** | 4 | §4.1-4.4 |
| **DROPPED（不入 checkbox 计数）** | 1 | §4.5 evidence doc — `.claude/tdd/` convention never adopted repo-wide（见 Post-Archive Execution Record DROPPED 段） |
| 合计 validator-计 checkbox 数 | 14 | 100% ticked |

## Post-Archive Execution Record（2026-09-03 @c6294f9）

> 模式仿 precedent 9987707：strike-through 表示"此任务的工作已在另一 archive / 另一 commit 中执行"，mapping table 提供 grep 可验的 commit SHA 锚点。

| Task | Commit | 证据（grep 可验） |
|---|---|---|
| §1.1-1.3（Issue ⑦ empty-cell） | `a56a599` | `git show a56a599 --stat` → 改 `src/decompmoe/extraction.py` + `tests/test_extraction.py`；Issue ⑦ `torch.where(n_i > 0, mean_n, centroids)` 替换 `.clamp_min(1e-9)` |
| §2.1-2.3（Issue ⑥ EMA normalize） | `a56a599` | 同上；Issue ⑥ Phase 1/2/3 EMA 输出 `F.normalize(α·c + (1-α)·mean, dim=-1)` |
| §3.1-3.4（Issue ⑧ 三 invariant test） | `a56a599` | 同上；3 个 invariant test scenarios（spherical_norm / empty_cell / near_zero_fallback） |
| §4.1-4.4（pytest + 数值复核） | U2 retroactive | post-archive 重跑 `uv run pytest tests/` 全绿（最新基线 ≥ 132 passed at `9987707`）；§4.4 数值脚本闭式对账 `torch.linalg.norm(F.normalize(α·c+(1-α)·mean, dim=-1), dim=-1) == 1.0` |

## DROPPED（2026-09-03 @c6294f9 cleanup commit）

> §4.5 evidence doc line **整行删除**（precedent 9987707 §2.10 DROPPED 模式）。删除理由基于仓库可观察事实，非本次临时起意：

| Task | DROPPED 理由（事实溯源） |
|---|---|
| §4.5 evidence doc → `.claude/tdd/fix-spec-doc-oversights-apply.tdd.md` | (1) `git log --all --diff-filter=A --name-only` → 0 命中 `.claude/tdd/*.tdd.md`，全历史从未采用 `.claude/tdd/` convention。(2) 当前 FS 无 `.claude/tdd/` 目录。(3) 证据已 consolidated in 本 record（§1-§3 commit 映射表 + §4.1-4.4 验证记录） + commit message `a56a599` 内嵌 plan 摘要。声明"写 evidence doc"属 aspirational task，无落地 convention 支撑。 |
