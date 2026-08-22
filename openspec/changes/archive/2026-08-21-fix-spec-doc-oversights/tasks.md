## 1. 主 spec `wayfinder` 修订

- [ ] 1.1 改 wayfinder Req 19 (L359) FLOPs 数字 0.26% → 0.20%，并补 Issue ⑨ 子公式措辞修正；verify `grep "≈ 0.20%" openspec/changes/fix-spec-doc-oversights/specs/wayfinder/spec.md` 命中 1 次、`grep "≈ 0.26%"` 命中 0 次、`grep "each projection is a forward GEMM of 2 · H_kv · d_k · d_c"` 命中 1 次
- [ ] 1.2 改 wayfinder Req 24 (L459) γ_init 反事实 −6.94 → −6.785、29× → 25×；verify `grep "−6.785" spec.md` 命中 1 次、`grep "25×" spec.md` 命中 1 次、`grep "−6.94" spec.md` 命中 0 次（除历史 commit message）
- [ ] 1.3 删 wayfinder Req 24 Scenario "Parameterization floor preserves cold-start gradient" 的 THEN 合取项 `[0.1, 32] parameterization interval is preserved`；verify `grep "\[0.1, 32\] parameterization interval is preserved" spec.md` 命中 0 次
- [ ] 1.4 wayfinder spec delta 整体 format check；verify `openspec validate fix-spec-doc-oversights --strict` 在仅 wayfinder delta 时不报 Req 编号 / Scenario 4-# 格式 / Source 反链 错误

## 2. Skeleton spec `decompmoe-skeleton` 修订

- [ ] 2.1 改 skeleton FLOPs Requirement (L46) 数字 0.26% → 0.20%；verify `grep "≈ 0.20%" spec.md` 命中 1 次、`grep "≈ 0.26%"` 命中 0 次
- [ ] 2.2 改 skeleton CentroidDriver Requirement (L128) Phase 0 行 `c_i ← KMeans(C)` → `c_i ← c_i.detach()`，并新增"Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds"；verify `grep "c_i ← c_i.detach()" spec.md` 命中 1 次、`grep "c_i ← KMeans(C)" spec.md` 命中 0 次、`grep "spherical KMeans is assumed to have produced L2-normalized" spec.md` 命中 1 次
- [ ] 2.3 改 skeleton "Hard-Constraint Grep Invariants" Requirement — 移除 bullets 6 (`.clamp_min(ε)` empty-cell denominator) 与 7 (`arctan(pi / sqrt(d_c))` literal)；verify grep 层 bullet 数 = 5（`grep -c "^- " spec.md | grep -A 1000 "Hard-Constraint Grep Invariants"` 或人工逐 bullet 数），且 `.clamp_min(1e-9)` 与 `arctan(pi / sqrt(d_c))` 在此 Requirement 内 0 命中
- [ ] 2.4 ADDED Requirement "Centroid Driver Semantic Invariants" 含 3 条 invariant 路由 + 1 条 Scenario；verify `grep "### Requirement: Centroid Driver Semantic Invariants" spec.md` 命中 1 次、`grep "test_empty_cell_preserves_centroid" spec.md` 命中 ≥1 次、`grep "test_spherical_norm_is_strictly_one" spec.md` 命中 ≥1 次、`grep "test_near_zero_candidate_fallback" spec.md` 命中 ≥1 次、`grep "#### Scenario: Semantic invariants are enforced" spec.md` 命中 1 次
- [ ] 2.5 skeleton spec delta 整体 format check；verify `openspec validate fix-spec-doc-oversights --strict` 在仅 skeleton delta 时不报 Req 编号 / Scenario 4-# / ADDED Requirement 格式 错误

## 3. Spec 层验证（必跑）

- [ ] 3.1 `openspec validate fix-spec-doc-oversights --strict` — 全 delta 通过格式校验；verify CLI exit 0 + stdout "valid"
- [ ] 3.2 跨文档一致性 — 主 spec / skeleton spec 所有 delta 不悬空；verify 无 `**Source:**` 指向不存在的文件（人工 review）
- [ ] 3.3 Issue ① 数值复核 — 重新计算 `66_048 / (8·1024² + 2·6·1024·2048) = 66_048 / 33_554_432 ≈ 0.001968`；verify spec 文本新值 `0.20%` 与独立计算一致（Python `python3 -c "print(f'{66048/33554432*100:.4f}%')"` 输出 `0.1968%`，四舍五入到 `0.20%`）
- [ ] 3.4 Issue ④ 数值复核 — 反事实参数化 `β = 1.0 + 31·σ(γ)` 下，`γ = −6.785` → β ≈ 1.035；verify `python3 -c "import math; print(1.0 + 31 * (1 / (1 + math.exp(6.785))))"` 输出 `≈ 1.03497`（与 spec 1.035 一致），σ'(−6.785) ≈ 1.128e-3，`σ'(−3.5)/σ'(−6.785) ≈ 25.2`（与 spec 25× 一致）
- [ ] 3.5 Issue ⑤ grep — 验证 THEN 合取项不再含恒真陈述；verify `grep "\[0.1, 32\] parameterization interval is preserved" openspec/specs/wayfinder/spec.md` 输出空（archive 之后）
- [ ] 3.6 Issue ⑨ 措辞 grep — 验证不再含字面重复计数；verify `grep "2 · H_kv · 2 · d_k · d_c" openspec/specs/wayfinder/spec.md` 输出空（archive 之后），`grep "each projection is a forward GEMM of 2 · H_kv · d_k · d_c"` 命中 1 次

## 4. Out-of-Scope 确认（必跑）

- [ ] 4.1 `git status` — 确认 `src/decompmoe/*.py` 与 `tests/test_*.py` 0 changed（本 change spec-only）；verify `git status --short` 中无 `src/` 或 `tests/` 路径
- [ ] 4.2 `openspec status --change "fix-spec-doc-oversights"` — 输出 `applyRequires` 仅含 `tasks`；所有 required set artifact 状态为 `done`
- [ ] 4.3 `git diff openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md` 不在本 change 范围（archive 阶段才合并）；verify 这两个文件在 git status 中显示未修改（archive 前）
- [ ] 4.4 本 change 仅写入 `openspec/changes/fix-spec-doc-oversights/` 目录；`wayfinder/tickets/*.md` 零改动（CLAUDE.md §8 裁决）；verify `git status --short` 中无 `wayfinder/tickets/` 路径

## 5. Downstream Hand-off（已明确移交，不在本 change 执行）

> **状态：已移交下游**。以下 6 条不属于本 change 的执行范围，勾选表示「已
> 明确移交」，而非「已实现」。

- [x] 5.1 **~~(已移交下游)~~** 在本 change archive 后，创建 `fix-spec-doc-oversights-apply` code-level change（spec-only 的下游）
- [x] 5.2 **~~(已移交下游)~~** 该 apply change 按 proposal.md "Downstream Hand-off" 段修复 Issue ⑥：替换 `extraction.py:126` EMA 公式为 `F.normalize(alpha * centroids + (1.0 - alpha) * mean, dim=-1)`，并同步 `tests/test_extraction_phase.py::test_phase_090_ema` 等 EMA 期望值到归一化形式
- [x] 5.3 **~~(已移交下游)~~** 该 apply change 修复 Issue ⑦：替换 `extraction.py:124` 的 `denom = weights.sum(dim=0).clamp_min(1e-9)` 为 `n_i = weights.sum(dim=0); weighted = (weights.T @ X); safe_n = n_i.clamp_min(1.0); mean_n = weighted / safe_n.unsqueeze(-1); mean = torch.where(n_i.unsqueeze(-1) > 0, mean_n, centroids)`
- [x] 5.4 **~~(已移交下游)~~** 该 apply change 修复 Issue ⑧：在 `tests/test_extraction.py` 新增 3 个 test — `test_empty_cell_preserves_centroid` / `test_spherical_norm_is_strictly_one` / `test_near_zero_candidate_fallback`（断言与 skeleton spec Scenario L341-351 严格对齐）
- [x] 5.5 **~~(已移交下游)~~** 该 apply change 跑 `pytest tests/` 全绿（85 个 TDD 测试 + 新增 invariant tests）；新测试须通过 ⑥⑦⑧ 三处修复后才可绿
- [x] 5.6 **~~(已移交下游)~~** apply change 完成后由用户显式触发 `/opsx:apply` 进入 implementation 阶段（**不在本 change 范围**）

## 6. Archive 触发（spec 层锁定）

- [ ] 6.1 `openspec archive-change fix-spec-doc-oversights` 把 delta 合并到 `openspec/specs/wayfinder/spec.md` 与 `openspec/specs/decompmoe-skeleton/spec.md`；verify archive CLI 成功，git status 显示两个 spec 文件 modified
- [ ] 6.2 archive 后跑 §3 全部 grep 复核（3.5 / 3.6 依赖 archive 后状态）；verify 所有 grep 命中数符合 3.5 / 3.6 描述
- [ ] 6.3 archive 后由用户显式触发 `/opsx:propose fix-spec-doc-oversights-apply` 启动下游 code-level change（按 §5 hand-off 合同）；verify 新 change 目录 `openspec/changes/fix-spec-doc-oversights-apply/` 出现

---

## 完成度口径

本文件共 **27** 条 checkbox。全部勾选**不等于**全部实现，三类语义必须分开陈述：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行** | 21 | §1 全 4 + §2 全 5 + §3 全 6 + §4 全 4 + §6 全 3 |
| **已明确移交** | 6 | §5 全 6（移交 `fix-spec-doc-oversights-apply` code-level change） |
| 合计 | 27 | |
