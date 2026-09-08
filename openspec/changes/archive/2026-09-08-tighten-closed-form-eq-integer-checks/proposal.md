## Why

CLAUDE.md §6 第 8 条强制 spec 中每个含具体数值的算式（FLOPs / 参数 / `θ_Voronoi` / `σ(γ)` / `1/(2·N_e)` / α 序列 / 相位覆盖）都必须有 `pytest.approx(..., abs=...)` 直接对账，文字断言不构成可验条款。但当前 3 处整数 closed-form 测试用裸 `==` 与字面常量对账，形式上违反该条款——尽管整数运算不会引入浮点误差，`abs=0` 等价于严格相等，仍需 formalize 进 spec 才算"条款与代码一致"。直接改 spec 是单源真相修复路径（CLAUDE.md §2）。

## What Changes

- **spec**: formalize `openspec/specs/wayfinder/spec.md` §6 第 8 条，澄清"含具体数值的算式（含整数 closed-form 常量）均须用 `pytest.approx(..., abs=...)` 直接对账"，新增对"整数 closed-form：`abs=0` 等价严格相等，但**形式上**仍需 `pytest.approx` 包装"的明示条款。
- **tests**: 3 处测试断言由裸 `== <int literal>` 改为 `pytest.approx(<int literal>, abs=0)`（参见 tasks.md §1）：
  - `tests/test_config.py:89` —— `flops_actual == 134_217_728`（位于函数 `test_flops_per_layer_exact_33554432` 内，LOW-2 site by archive/2026-09-06）
  - `tests/test_extraction.py:104` —— `expected == 33_040` (per-head MACs closed form; in function `test_complexity_budget`)
  - `tests/test_experts.py:101` —— `total == 100_663_296` (N_e·3·d_model·d_ffn params)
- **principle-compliance intent**: 本 change **只解决 §6 第 8 条形式合规**（raw `==` → `pytest.approx(..., abs=0)`）；principle 层（即"spec 算式必须直接对账 production code，不只是 helper function"）在 Finding #6 中揭示，由 design Decision 4 Addendum + tasks.md §6 显式记录为 out-of-scope future follow-up。本 change **不**意图修复 principle 层合规——超出 surgical test-only scope per CLAUDE.md §3。
- **nothing else**: 不动源码模块、不动 wayfinder tickets（CLAUDE.md §6 第 7 条 + §8 tickets 已 reference-only）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无。Spec delta 经 §7 修正后转为 ADDED Requirements — see `openspec/changes/tighten-closed-form-eq-integer-checks/specs/wayfinder/spec.md`；append to 既有 `wayfinder` capability 的 spec.md，不创建新 capability。）

### Added Requirements to Existing Capability

- `wayfinder`: ADDED Requirement "Test Guard Precision for Closed-Form Numerical Claims" — formalize §6 第 8 条的 integer closed-form obligation（"整数 closed-form 常量均须 `pytest.approx(..., abs=0)` 包装，禁止裸 `== <int literal>`"）+ 4 个 Scenario（parameter totals / FLOPs totals / per-head MACs / expert params）。**Note**: spec delta 在 propose 阶段 originally 写为 MODIFIED（假设主 spec 已有此 Requirement），但 post-§6 commit audit 发现主 spec 不含此 Requirement header（grep verify `openspec/specs/wayfinder/spec.md` No matches found）；通过 `/opsx:update` §7 改为 ADDED Requirements，archive 会 append 新 Requirement 到主 spec。

## Impact

- **Affected code**: 仅 3 个测试文件，surgical edits（line numbers reflect post-commit `ae14868` state，2026-09-07）:
  - `tests/test_config.py:89` (`flops_actual == 134_217_728`, LOW-2 site)
  - `tests/test_extraction.py:104` (`expected == 33_040`, per-head MACs)
  - `tests/test_experts.py:101` (`total == 100_663_296`, expert params)
- **§5 follow-up (commit `ae14868`)**:
  - `tests/test_config.py:94` (`config.flops_per_token(...) == 134_217_728`, the originally-named carve-out target)
  - `tests/test_config.py:87` (`per_layer == 33_554_432`, LOW-2 site missed by archive/2026-09-06)
  - `tests/test_config.py:57-58` (docstring hygiene)
- **§6 follow-up (planned, commit pending)**: `tests/test_experts.py:100` raw == → `pytest.approx(expected, abs=0)` (Finding #7) + `tests/test_extraction.py:98` hardcoded literals → `MVPConfig.H_kv/d_k/d_c` (Finding #13). See tasks.md §6.
- **Affected APIs / dependencies**: 无
- **Affected systems**: 无
- **Risk**: 极低 —— `abs=0` 在整数运算下与 `==` 严格等价，语义零变化；形式一致性的修复
- **Source**: 反链至清单 2 P2 审计（2026-09-07），原始证据链：
  - `tests/test_config.py:94` `config.flops_per_token(config.MVPConfig(), "MOE") == 134_217_728`
  - `tests/test_extraction.py:104` `expected == 33_040` (per-head MACs)
  - `tests/test_experts.py:100` `total == 100_663_296` (N_e·3·d_model·d_ffn)

## Deferred Items

Items acknowledged as defects but deferred from this change's scope. Tracking lives here (rather than in a separate change) because the unsuppression triggers are tied to this change's spec contract — extracting them to a new change would add ceremony without adding tracking value.

- **B1** — `tests/test_extraction.py::test_complexity_budget` L106 helper tautology. The form `expected = macs(cfg_hkv, cfg_dk, cfg_dc); assert expected == 33_040` re-states the closed-form formula in the test — does NOT verify the impl actually has 33_040 MACs. The current test invocation of `extract_C(...)` (L107-120) verifies shape + spherical invariant only. The strengthened Scenario "Closed-form per-head extraction MACs use bare `==`" (spec delta, clause 3.iii) requires NEW tests to derive MACs from impl-level measurement (profiler / hook / AST analysis are all acceptable); B1 is the explicit pre-existing-state carve-out for the current test.
  - **Unsuppress trigger**: any future refactor of `extract_C` (new einsum pattern, additional projection, fused kernel, etc.) OR any change to the MACs closed-form formula MUST first land the verification infra (AST or profiler baseline for `extract_C` MAC count). Without this, a future refactor could silently double the impl's MACs while the helper-tautology assertion still passes — and the principle-level guard mandated by Scenario 3.iii would be unfulfilled.
- **B2** — `tests/test_extraction.py::test_complexity_budget` L122-139 scaling helper tautologies (`assert m2 == 2 * m1`, `assert (m4 - m3) == d_k_step_contrib`). Same principle gap as B1: algebraic identities of the `macs(...)` helper function, not impl-level checks. Shares infra with B1.
  - **Unsuppress trigger**: same as B1 — any `extract_C` refactor or MACs formula change requires the AST/profiler baseline to land first.
- **C1** — `tests/test_sphere.py:90` 1-unit rounding typo (`1.173547` should be `1.173548`). Already noted in spec delta obligation 3 (bisection angles) as "out of scope" per A3(b) annotation. Same source typo as the spec delta's 6dp reference; tracked here so the typo is not separately re-investigated.
  - **Unsuppress trigger**: when the spec delta's Scenario "Bisection Voronoi angles use pytest.approx(abs=1e-6)" is actually applied (the test currently uses `abs=1e-4`), the test literal MUST be corrected to `1.173548` first; otherwise the tolerance tightening would fail and the principle gap would surface as a different kind of bug.

**Co-deferral note**: B1 and B2 share verification infra and should land together when the unsuppress trigger fires. C1 is a single-character fix that should ride along with any future tolerance-tightening change that touches `tests/test_sphere.py`.