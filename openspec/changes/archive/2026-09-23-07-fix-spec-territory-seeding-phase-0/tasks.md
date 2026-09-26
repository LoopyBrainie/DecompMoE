# Tasks

## §A. wayfinder spec �?(2 MODIFIED + 1 ADDED, �?anchor 顺手修复)

### A-1 · spec req-2 L24 标识符映射注�?(MODIFIED)

- [x] A-1.1 spec delta: 编辑 `openspec/specs/wayfinder/spec.md` Requirement "Formal Symbols And Code Naming" (L20-26, anchor `<a id="req-2"></a>` L20): 在标识符映射�?`territory_seeding` 之后追加 inline 注脚 `**Note:** \`territory_seeding\` is the canonical API contract name for the Phase 0 K-Means initialization pathway. Its implementation is **deferred to the training-time caller** per req-6 Phase 0 sub-clause; the function exists as a thin contract placeholder that raises \`NotImplementedError\` with a verbatim pointer to req-6 Phase 0 (see Requirement "Territory Seeding Deferred Contract" below). Drivers and inference-time callers MUST NOT invoke this function at inference time.`
- [x] A-1.2 验证: `grep -nF "territory_seeding\` is the canonical API contract name" openspec/specs/wayfinder/spec.md` 返回 1 次命�?(确认注脚已写�?L24 附近)
- [x] A-1.3 验证: 现有 anchor `<a id="req-2"></a>` 不动 (`CLAUDE.md §6 �?8 条` anchor 100% 覆盖)
- [x] A-1.4 验证: L26 `**Source:**` 反链 `wayfinder/tickets/A1-1.md` + `wayfinder/tickets/A2-2.md` 不动;`python scripts/lint_no_source_field_drift.py` exit=0

### A-2 · spec req-6 Phase 0 deferred 声明 + anchor 顺手修复 (MODIFIED)

- [x] A-2.1 spec delta: 编辑 `openspec/specs/wayfinder/spec.md` Requirement "C Extraction Differentiability And Centroid Lifecycle" (L76-93, anchor `<a id="req-6"></a>` 当前**缺失**,需新增): �?L76 Requirement title 前新�?anchor `<a id="req-6"></a>` (一行独�?+ 一行空�? �?req-2 / req-3 现有 anchor 格式一�?
- [x] A-2.2 spec delta: 在同一 Requirement Phase 0 子句 (L81) 后追�?deferred 声明�? 改为:`- **Phase 0** �?Spherical K-Means seeding (no gradient, no EMA): \`c_i^(t+1) = KMeans(C)\` initialization. **Phase 0 K-Means implementation is deferred to the training-time caller** (MVP scope per \`CLAUDE.md §7 "Out of Scope"\` �?training execution out-of-scope). The canonical contract name in the codebase is \`territory_seeding(C_batch, N_e, *, d_c)\` (see req-2 L24 identifier map), which currently raises \`NotImplementedError\` with a verbatim pointer to this clause. Drivers and inference-time callers MUST NOT call \`territory_seeding\` at inference time; \`CentroidDriver.step\` Phase 0 (\`Phase.SEEDING\`) returns the input centroids detached as a no-op (see \`src/decompmoe/extraction.py:119-120\`).`
- [x] A-2.3 spec delta: 在同一 Requirement 末尾追加 Scenario `Phase 0 K-Means deferred to caller`:
  - **WHEN** `territory_seeding(C_batch, N_e, *, d_c)` is called with `C_batch �?R^{T × d_c}` (any finite batch of `d_c`-dimensional points, `T �?N_e`), `N_e �?ℕ⁺` (positive integer), and `d_c �?ℕ⁺`
  - **THEN** it raises `NotImplementedError` whose message contains the verbatim substring `"Phase 0"` and `"deferred to the training-time caller"` (linking back to this Requirement)
  - **AND** the error message references spec req-2 (the identifier map) by its anchor string `"req-2"`
  - **AND** drivers and inference-time callers MUST NOT invoke this function; `CentroidDriver(Phase.SEEDING).step(centroids, X, mask)` is the canonical no-op contract for the inference-time Phase 0 path
- [x] A-2.4 验证: 新增 anchor `<a id="req-6"></a>` �?L76 Requirement title �?`grep -nE '<a id="req-6"></a>' openspec/specs/wayfinder/spec.md` 返回 1 次命�?- [x] A-2.5 验证: Phase 0 子句改动仅在 L81 文字 + 后续段落追加;不动 Phase 1-4 子句 (L82-85)
- [x] A-2.6 验证: `grep -nF "Phase 0 K-Means implementation is deferred" openspec/specs/wayfinder/spec.md` 返回 1 次命�?(确认 deferred 声明已写�?
- [x] A-2.7 验证: 现有 L93 `**Source:**` 反链 `wayfinder/tickets/A3-2.md` + `change fix-openspec-doc-bugs design.md (Decision 2)` 不动;`python scripts/lint_no_source_field_drift.py` exit=0
- [x] A-2.8 验证: change 04 新增�?Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)` (L231-234) 不动;与本 change 新增�?Scenario `Phase 0 K-Means deferred to caller` 互补不冲�?
### A-3 · �?Requirement "Territory Seeding Deferred Contract" (ADDED, anchor req-10 顺手修复)

- [x] A-3.1 apply 阶段�?`grep -nE '<a id="req-[0-9]+"></a>' openspec/specs/wayfinder/spec.md | sort -t'"' -k2 -V` 确定 next-free anchor number; 2026-09-23 实测 req-6 �?req-10 各缺�?�?change 修复 req-6 (A-2.1) + 使用 req-10 (next missing after req-9 L171)�?*�?apply 阶段实测 anchor 序列变化 (e.g. 期间有别�?change 引入 anchor),改用 next missing number**
- [x] A-3.2 spec delta: �?`openspec/specs/wayfinder/spec.md` 末尾 (req-9 之后, req-11 之前) 新增 Requirement "Territory Seeding Deferred Contract"; 首行设独�?anchor `<a id="req-10"></a>` (一行独�?+ 一行空�?+ 一�?Requirement title, 与现�?anchor 格式一�?
- [x] A-3.3 Requirement 正文包含 4 �?
  - **定义**: 薄占位契�? 函数签名 `territory_seeding(C_batch: Tensor, N_e: int, *, d_c: int) -> Tensor`
  - **行为**: 函数�?`raise NotImplementedError(spec_cited_message)`, 错误消息 verbatim 包含 `"Phase 0"`, `"deferred to the training-time caller"`, `"req-2"`, `"req-6"`
  - **禁止**: drivers / inference-time callers 不得调用此函�?  - **Source**: 引用 `wayfinder/tickets/A1-1.md` + `wayfinder/tickets/A3-2.md` (literal backtick per `CLAUDE.md §3` lint 三项结构性检�?, 同时引用 `change 07-fix-spec-territory-seeding-phase-0 design.md (Decision 1)`
- [x] A-3.4 新增 Scenario `territory_seeding raises NotImplementedError with spec citations`:
  - **WHEN** `territory_seeding(C_batch, N_e, *, d_c)` is called with `C_batch = torch.randn(64, 16)` (random unit-sphere points), `N_e = 16`, `d_c = 16`
  - **THEN** it raises `NotImplementedError` with message matching `pytest.raises(NotImplementedError, match=r"Phase 0")`
  - **AND** `pytest.raises(NotImplementedError, match=r"deferred to the training-time caller")`
  - **AND** `pytest.raises(NotImplementedError, match=r"req-2")` AND `pytest.raises(NotImplementedError, match=r"req-6")`
  - **AND** the function signature `inspect.signature(decompmoe.extraction.territory_seeding)` equals `(C_batch, N_e, *, d_c)` �?keyword-only `d_c` enforced
- [x] A-3.5 新增 Scenario `territory_seeding is exported via __all__`:
  - **WHEN** the module `decompmoe.extraction` is imported
  - **THEN** `"territory_seeding" in decompmoe.extraction.__all__` evaluates to `True` (satisfies req-2 L24 identifier-map MUST-be-in-codebase contract)
  - **AND** `decompmoe.extraction.territory_seeding` is callable and resolves to the same function object as the module-level name
- [x] A-3.6 验证: anchor lint 检�?`grep -nE '<a id="req-10"></a>' openspec/specs/wayfinder/spec.md` 返回 1 次命�?- [x] A-3.7 验证: Source 反链 lint `python scripts/lint_no_source_field_drift.py` exit=0 (�?Requirement Source 反链必须�?`` `wayfinder/tickets/A1-1.md` `` + `` `wayfinder/tickets/A3-2.md` `` literal backtick, 主反链必须为第一�?top-level item)

## §B. src/ 边界�?(1 文件 surgical Edit)

### B-1 · src/decompmoe/extraction.py 薄占位函�?
- [x] B-1.1 验证插入�? apply 阶段�?`grep -nF "__all__" src/decompmoe/extraction.py` 确认 `__all__` 起始�? 2026-09-23 实测 `__all__` �?line 175,函数插入�?line 174 (line 173 raise ValueError 之后 + line 174 空行 + line 175 `__all__` 之前)
- [x] B-1.2 src/ edit: �?`src/decompmoe/extraction.py:174` 新增薄占位函�?
  ```python
  def territory_seeding(
      C_batch: Tensor,
      N_e: int,
      *,
      d_c: int,
  ) -> Tensor:
      """Canonical Phase 0 K-Means contract �?deferred to training-time caller.

      Spec (wayfinder req-6 "C Extraction Differentiability And Centroid
      Lifecycle", Phase 0 sub-clause): the Spherical K-Means initialization
      `c_i^(t+1) = KMeans(C)` is **deferred to the training-time caller**.
      MVP scope per CLAUDE.md §7 places training execution out-of-scope, so
      this function is a thin contract placeholder that satisfies req-2 L24
      identifier-map membership (`territory_seeding` MUST be a codebase
      identifier) without implementing the actual K-Means.

      Returns
      -------
      Tensor of shape (N_e, d_c)
          The K-Means centroids. **Never returned in MVP** �?this function
          unconditionally raises NotImplementedError.

      Raises
      ------
      NotImplementedError
          Always. The verbatim message references spec req-2 + req-6 Phase 0
          so future callers receive a self-locating error pointing to the
          deferred contract clause.
      """
      raise NotImplementedError(
          f"territory_seeding: Phase 0 Spherical K-Means initialization is "
          f"deferred to the training-time caller per wayfinder spec req-2 "
          f"(identifier map) and req-6 (Phase 0 sub-clause: 'Phase 0 "
          f"K-Means implementation is deferred to the training-time "
          f"caller'). Inputs were C_batch.shape={tuple(C_batch.shape)}, "
          f"N_e={N_e}, d_c={d_c}. Drivers and inference-time callers MUST "
          f"NOT invoke this function; use CentroidDriver(Phase.SEEDING)"
          f".step(centroids, X, mask) for the no-op Phase 0 contract."
      )
  ```
- [x] B-1.3 src/ edit: 修改 `src/decompmoe/extraction.py:175-179` `__all__` 列表追加 `"territory_seeding"`,使其成为 public export (满足 req-2 L24 identifier-map MUST-be-in-codebase 契约)。修改后 `__all__` �?
  ```python
  __all__ = [
      "extract_C",
      "Phase",
      "CentroidDriver",
      "territory_seeding",
  ]
  ```
- [x] B-1.4 验证: `grep -nF "def territory_seeding" src/decompmoe/extraction.py` 返回 1 次命�?(确认函数已定�?
- [x] B-1.5 验证: `grep -nF '"territory_seeding"' src/decompmoe/extraction.py` 返回 1 次命�?(`__all__` 已包�?
- [x] B-1.6 验证: `grep -nE "^def territory_seeding" src/decompmoe/extraction.py` 应只返回 1 �?(无重复定�?
- [x] B-1.7 不动现有 `Phase.SEEDING` 分支 (L119-120): `return centroids.detach()` 保留, �?spec delta 方向一�?- [x] B-1.8 不动现有 L107-108 docstring 注释 "actual k-means is owned by training-time caller": 注释现在�?spec req-6 Phase 0 deferred 声明一一对应
- [x] B-1.9 LF 校验: `git diff --stat src/decompmoe/extraction.py` 显示�?+30 �?(新增函数 + `__all__` 追加);�?[[windows-edit-crlf-pitfall]] memory rule 必要�?`sed -i 's/\r$//'`

## §C. tests/ 边界�?(1 文件新增 1 test, 既有 13 �?test 不动)

### C-1 · tests/test_extraction.py NotImplementedError contract test

- [x] C-1.1 test 新增: �?`tests/test_extraction.py` 末尾追加 `test_territory_seeding_raises_not_implemented_with_spec_citation`:
  ```python
  def test_territory_seeding_raises_not_implemented_with_spec_citation():
      """territory_seeding is a deferred Phase 0 contract (spec req-2 + req-6).

      MVP scope (CLAUDE.md §7) places training execution out-of-scope, so the
      function unconditionally raises NotImplementedError with a verbatim
      pointer to the spec clauses. This test guards the contract.
      """
      torch.manual_seed(0)
      C_batch = torch.randn(64, 16)  # 64 random 16-d points
      N_e = 16
      d_c = 16

      with pytest.raises(NotImplementedError, match=r"Phase 0"):
          decompmoe.extraction.territory_seeding(C_batch, N_e, d_c=d_c)
      with pytest.raises(NotImplementedError, match=r"deferred to the training-time caller"):
          decompmoe.extraction.territory_seeding(C_batch, N_e, d_c=d_c)
      with pytest.raises(NotImplementedError, match=r"req-2"):
          decompmoe.extraction.territory_seeding(C_batch, N_e, d_c=d_c)
      with pytest.raises(NotImplementedError, match=r"req-6"):
          decompmoe.extraction.territory_seeding(C_batch, N_e, d_c=d_c)
  ```
- [x] C-1.2 验证: test 文件首行 `import torch` + `import pytest` + `import decompmoe.extraction` 已存�?(现有 test_extraction.py 应已 import); 如未 import `decompmoe.extraction` 直接命名空间, 改用 `from decompmoe.extraction import territory_seeding`
- [x] C-1.3 不修改既�?13 �?test (test_extraction.py 当前测试列表: test_pipeline_shape / test_aggregate_across_heads_awareness / test_complexity_budget / test_full_differentiability / test_no_surrogate_in_codebase / test_extract_C_signature / test_empty_cell_preserves_centroid / test_spherical_norm_is_strictly_one / test_near_zero_candidate_fallback / test_near_zero_candidate_fallback_phase4 / test_phase_4_sgd_1_step_closed_form / test_phase_4_sgd_near_zero_candidate_fallback / test_phase_4_grad_none_preserves_legacy_l2_retraction) —�?`CLAUDE.md §3` surgical 原则
- [x] C-1.4 独立数值复�? 手工 trace `territory_seeding(C_batch, N_e, d_c=d_c)` 调用 �?进入函数�?�?`raise NotImplementedError(spec_cited_message)` �?错误消息 verbatim 包含 4 �?token (`"Phase 0"`, `"deferred to the training-time caller"`, `"req-2"`, `"req-6"`) �?
## §D. 验证与提交段 (surgical)

- [x] D.1 spec delta 验证: `grep -nE '<a id="req-[0-9]+"></a>' openspec/specs/wayfinder/spec.md` 应在�?33 anchor 基础上新�?2 �?(req-6 修复 + req-10 ADDED) = **35 �?anchor**; `CLAUDE.md §6 �?8 条` anchor 100% 覆盖
- [x] D.2 spec Source 反链验证: `grep -nE '`wayfinder/tickets/[A-Z][0-9]+-[0-9]+\.md`' openspec/specs/wayfinder/spec.md` 应在原命中数基础上至少返�?+2 次命�?(�?req-10 引用 A1-1 + A3-2); `python scripts/lint_no_source_field_drift.py` exit=0
- [x] D.3 spec dead-defensive 验证: `python scripts/lint_no_dead_defensive.py` exit=0 (新增 Scenario + Requirement 不引�?`# noqa: dead-defensive` 注释)
- [x] D.4 src/ LF 校验: 每个 src/ Edit �?`git diff --stat src/decompmoe/extraction.py` 验证行数变化符合预期 (�?+30 �?;�?[[windows-edit-crlf-pitfall]] memory rule 必要�?`sed -i 's/\r$//'`
- [x] D.5 spec/code 一致�?spot-check:
  - `inspect.signature(decompmoe.extraction.territory_seeding)` 返回 `(C_batch, N_e, *, d_c)` �?  - `"territory_seeding" in decompmoe.extraction.__all__` 返回 `True` �?  - `decompmoe.extraction.territory_seeding(torch.randn(8, 16), 4, d_c=16)` raises `NotImplementedError` �?  - 错误消息�?`"Phase 0"`, `"deferred to the training-time caller"`, `"req-2"`, `"req-6"` (4 �?token 全部命中) �?- [x] D.6 测试运行: `uv run pytest tests/test_extraction.py -v`, 期望 **13 passed** (既有) + **1 passed** (新增) = **14 passed**; �?regression
- [x] D.7 跨测试运�? `uv run pytest tests/ -v`, 期望 **198 passed** (项目实测 2026-09-23) + **1 passed** (新增) = **199 passed**; �?regression (�? 此处 198 �?`tests/test_extraction.py` 13 + 其他测试文件 185 的总和, 新增 1 个仅�?test_extraction.py)
- [x] D.8 �?commit on `dev`: `git add src/decompmoe/ tests/ openspec/changes/ && git commit -m "fix(spec,code): close meta-03 + meta-04 �?territory_seeding contract + Phase 0 deferred declaration (audit-verification meta-audit 2026-09-19, fact-verified 2026-09-23)"`
- [x] D.9 archive 准备: `openspec validate 07-fix-spec-territory-seeding-phase-0 --type change --strict` �?PASS（无 "Unknown item" �?MODIFIED-but-not-found warnings�