## 1. Actual New Work (Pi-remediated subset)

- [ ] 1.1 修 `wayfinder/spec.md:299` "but nots NOT advance the phase" → "but does NOT advance the phase"（已完成）

- [ ] 1.2 修 `wayfinder/spec.md:582` scenario signature 协调：spec 写 `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` 与 code 一致（已完成）

- [ ] 1.3 `tests/test_safeguards.py` 新增 `test_resurrection_perturb_default_requires_dim`（TypeError on `dim=None`，已完成）

- [ ] 1.4 `tests/test_sphere.py` 新增 `test_versine_voronoi_closed_form`（闭式对账 0.61312 / 0.47707，已完成）

## 2. Verification

- [ ] 2.1 跑 `uv run pytest tests/ -v` 确保 140 passed（已完成；含 3 个新测试）

- [ ] 2.2 跑 `openspec validate fix-p1-audit-batch`（已完成：valid）

## 3. Apply & Archive

- [ ] 3.1 跑 `openspec archive fix-p1-audit-batch --yes`（user 已 explicit 同意 archive 这三个）

- [ ] 3.2 archive 后独立复核：spec L299 + L582 字面正确；3 个新测试仍 pass

## 4. Already-Applied Earlier (NOT in this change's diff)

MAJ-T1 / MAJ-M1 / MAJ-M2 / MAJ-M3 已在本会话前段 applied；此 change 不重新 claim。

## 6. Design Note (Design.md skipped — warning only)

本 change `design.md` 未写（status: ready）。Design 在 spec-driven schema 下为可选 advisory artifact，不阻塞 archive。后续如需补，可创建 `design.md` 描述 P1 batch 的 5 子项 fix 在 codebase 中的协调策略（spec/code/test 三方关系）。