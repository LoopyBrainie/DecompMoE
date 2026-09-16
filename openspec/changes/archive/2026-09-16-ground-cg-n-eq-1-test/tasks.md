## 1. Spec Sync (delta → active wayfinder spec)

- [x] 1.1 ADDED Requirement `CG n=1 boundary behavior` 同步入 `openspec/specs/wayfinder/spec.md` L442-463(`req-34` anchor + Requirement body + 4 Scenarios + lint-compliant Source)。**执行者:** `commit b8c149c` (2026-09-16, `2026-09-16-add-cg-n-eq-1-test` apply 阶段)。verify `grep -A2 "CG n=1 boundary" openspec/specs/wayfinder/spec.md` 命中 ADDED Requirement 标题 + 4 个 Scenario 标题(positive / negative / zero / multi-dim numel==1)。✅
- [x] 1.2 `openspec validate ground-cg-n-eq-1-test --strict` 通过——本 change delta 已与 active spec 一致(4 Scenarios、lint-compliant Source、`req-34` anchor)。verify 输出 `Valid change: ground-cg-n-eq-1-test`,无 strict 错误,无 schema violation。✅

## 2. Test Docstring Fix (active spec anchor on L174)

- [x] 2.1 `tests/test_metrics.py` `test_cg_n_eq_1_returns_magnitude` docstring L174 反链字符串直接指向 `openspec/specs/wayfinder/spec.md` Req 20 (CG) + ADDED Requirement "CG n=1 boundary behavior"(active spec 锚点,非 archive-only delta 路径)。**注:** `b8c149c` 在 add-cg-n-eq-1-test apply 时一次性写好了正确 docstring,**ground 原 propose 的"把 delta 路径反链改为 active spec 锚点"surgical edit 不再需要**(已被 b8c149c 覆盖)。test 函数本体定义于 L171-211,5 个 `pytest.approx(..., abs=1e-12)` 断言(1D positive / 1D negative / 1D zero / 2D positive / 3D negative),每个断言失败消息嵌入 `f"actual={...}"`(`governance/spec.md` req-gov-1 obligation 4)。✅

## 3. Verify (post-apply baseline)

- [x] 3.1 `uv run pytest tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude -v` 5 个断言 abs=1e-12 全部 PASS。✅
- [x] 3.2 `uv run pytest tests/ -v` 全套 188 passed,1 warning(`pytest-asyncio` 无关警告);base line 142 → 188 = +46 tests(部分来自 `b8c149c` 本 change,部分来自同期其它 in-flight change)。无回归。✅
- [x] 3.3 `git diff --stat` 变更 scope 限于:`openspec/specs/wayfinder/spec.md`(+23 行 ADDED Requirement 段)+ `tests/test_metrics.py`(+38 行 test 函数)。verify `openspec/changes/archive/2026-09-05-add-cg-n-eq-1-test/` 与 `openspec/changes/archive/2026-09-16-add-cg-n-eq-1-test/` 物理文件均未触碰(`git status` 不含这些路径)。✅
- [x] 3.4 lint gate:`python scripts/lint_no_source_field_drift.py` exit=0(3 file(s) scanned, no violations);`python scripts/lint_no_dead_defensive.py` exit=0(no anti-patterns found)。✅

## 4. Archive (finalize as no-op post-apply)

- [ ] 4.1 `openspec archive ground-cg-n-eq-1-test --yes`,verify change 移入 `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/`。sync 阶段 CLI 判定 delta 与 main spec 一致,no drift,no-op(无需 main spec 改写)。原 `add-cg-n-eq-1-test` 两条 archive (`2026-09-05-` 与 `2026-09-16-`) 物理均未动。