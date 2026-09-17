## 1. Pre-flight validation

- [x] 1.1 Run `openspec validate --change fix-wayfinder-and-skeleton-spec-duplicate-requirements` and verify exit=0（确认 proposal/specs delta 已对齐，无 lint / schema 错误）

## 2. Remove 5 old Reqs from `decompmoe-skeleton/spec.md`

> 每个任务都用 Edit 删除对应 Req 块（含 `<a id="..."></a>` anchor、`### Requirement:` header、body、所有 `#### Scenario:`），保留 L436 / L440 / L444 orphan Scenarios（Decision 2）。完成后用 `grep -n '^### Requirement:' openspec/specs/decompmoe-skeleton/spec.md` 复核行号列表。

- [x] 2.1 Remove Req "Frozen MVP Hyperparameter Set" (L20) and verify the next Req header is "Canonical Package And Version Identifier" (formerly L8)
- [x] 2.2 Remove Req "Spherical L2 Normalization" (L94) and verify orphan Scenarios under former L94 remain on disk (git diff should show only Req-block deletion, not Scenario deletion)
- [x] 2.3 Remove Req "Centroid Four-Phase Lifecycle Driver" (L145) and verify orphan content under former L145 is intact
- [x] 2.4 Remove Req "Eight Metrics And Classification" (L307) and verify orphan content under former L307 is intact
- [x] 2.5 Remove Req "Beta Parameterization Operational Domain" (L432) and verify L436 / L440 / L444 Scenarios remain as orphan Scenarios（不在任何 Req header 下，但行内容存在）

## 3. Modify 2 Reqs in `wayfinder/spec.md`

- [x] 3.1 Modify Req "Resurrection Perturbation Per-Expert Contract" body (L577) and verify the body now reads `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)`（与 L582 Scenario 描述一致）
- [x] 3.2 Modify Req "Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper" body (L642) and verify the body now reads `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)`（与 L650 Scenario 描述一致），同时保留 L644 的 `resurrect_expert(i, j_star, β_per_expert, cfg)` wrapper 说明不变

## 4. Post-apply verification

- [x] 4.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0（archive 前置条件，见 `19543eb` 修复的 `12f673d` 漏洞）
- [x] 4.2 Run `grep -n '^### Requirement:' openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md` and verify (a) wayfinder still has Req "Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper" (L640), (b) skeleton has no "Spherical L2 Normalization" / "Centroid Four-Phase Lifecycle Driver" / "Eight Metrics And Classification" / "Frozen MVP Hyperparameter Set" / "Beta Parameterization Operational Domain" plain entries（仅保留"— D1 / — Phase-4 / — CG / — max(…z…, ε)"后缀的 ADDED 版本）
- [x] 4.3 Run `openspec status --change fix-wayfinder-and-skeleton-spec-duplicate-requirements` and verify `isComplete: true`，确认所有 artifacts 都已落盘

## 5. Post-review audit adjustments (R-F1/R-F4/R-F5/R-F7/R-F11/R-F12/R-F13, F-3)

> Code + test scope added after `code-review max` audit. Full rationale in `proposal.md` "Post-Review Adjustments" + "Spec Amendment" sections.

- [x] 5.1 **R-F1**: Append "Post-Review Adjustments" + "Spec Amendment" sections to `proposal.md` documenting the 4 code + 2 test file changes plus the spec amendment motivation (truth-source chain via `loss.py:88` / `metrics.py:83` / pre-existing test_safeguards.py:177)
- [x] 5.2 **F-3**: Add docstring to `phase_beta_box` clarifying the `return (1.0, 32.0)` fallback applies to phases the spec does not constrain (Phase 0/5+); MVP never hits this fallback
- [x] 5.3 **R-F4**: Rename `gamma_reset_for_phase4(beta_exit)` → `gamma_reset_for_phase4(beta_p3)` (matches spec ADDED L393 canonical parameter name); update `tests/test_schedule.py:138` keyword call to `beta_p3=16.0`
- [x] 5.4 **F-5**: Replace magic `31.0 + 1.0 - beta_exit` in `gamma_reset_for_phase4` with module-level `BETA_MAX - beta_p3` per design.md Decision 1
- [x] 5.5 **R-F11**: Move `from decompmoe.beta import BETA_MAX` to module-top-level imports in `schedule.py` (remove in-function runtime import)
- [x] 5.6 **R-F7**: Rename `MAX_GRAD_BETA_PHASE4 = 7.75` → `_MAX_GRAD_BETA_PHASE4_INTERNAL` and remove from `__all__` in `beta.py` (spec skeleton ADDED L393 only mandates exporting `MAX_GRAD_PER_C` / `MAX_GRAD_PER_GAMMA` / `MAX_GRAD_PER_GAMMA_PHASE4`)
- [x] 5.7 **R-F12**: Update `tests/test_beta.py::test_max_grad_beta_phase4` to import `_MAX_GRAD_BETA_PHASE4_INTERNAL` directly (single source of truth, no inline literal)
- [x] 5.8 **F-13**: Remove dead-defensive `try/except (TypeError, ValueError)` blocks from `beta_effective` (caught by lint gate `db14222`)
- [x] 5.9 **R-F5 + R-F13**: Spec amendment — revise wayfinder Req 28/32 body to `shape (..., N_e)` (trailing axis = N_e, leading dims arbitrary per `loss.py:88 (B, N, N_e)` + `metrics.py:83 (T, ..., N_e)` convention); replace single "perturbation output shape matches a single expert slot" Scenario with 5 shape-specific Scenarios (1-D (N_e,) / batched (B, N, N_e) / history-stacked (T, ..., N_e) / 0-D scalar reject / wrapper pair-check)
- [x] 5.10 **R-F5 + R-F13** (corrected in 2026-09-17 re-apply round): Code two-layer shape enforcement — Layer 1 (primitive) `f_per_expert.ndim < 1` → ValueError applied at `src/decompmoe/safeguards.py:143`; Layer 2 (wrapper `resurrect_expert`) `f_per_expert.shape[-1] != cfg.N_e` → ValueError applied at `src/decompmoe/safeguards.py:233` (anchored on `cfg.N_e`, NOT the originally-proposed `β_per_expert.shape[0]` — the latter was a vacuous self-check given `f_per_expert = β_per_expert.detach()` inside the wrapper, where `shape[-1] == shape[0]` identically; corrected by commit `0b2202e`); wrapper threads `β_per_expert.detach()` as the leading positional arg of the perturbation primitive (applied at `src/decompmoe/safeguards.py:232`).
- [x] 5.11 Final verification: **75 tests passed** (73 perturbation/schedule/beta/loss/gating baseline + 2 new shape-specific Scenarios tests added in round 2: `test_resurrection_perturbation_rejects_0d_scalar` + `test_resurrection_perturbation_accepts_history_stacked`; 3 existing tests strengthened in-place by M1/M2/M4 without adding new tests) + `lint_no_dead_defensive` exit=0 + `lint_no_source_field_drift` exit=0 + `openspec validate` pass (fix-wayfinder-and-skeleton-spec-duplicate-requirements)

## 6. Round-2 audit corrections (2026-09-17 re-apply)

> Triggered by independent verifier review of the 2026-09-17 first-apply output, which surfaced 1 CRITICAL spec/code contradiction + 3 HIGH test coverage gaps + 4 MEDIUM test assertion weaknesses + 4 LOW structural issues. Full rationale in `proposal.md` §"Subsequent Audit Correction".

- [x] 6.1 **CRITICAL fix**: Update `openspec/changes/.../specs/wayfinder/spec.md` delta body L7 (Req 28) + L13 (Req 32): replace vacuous `f_per_expert.shape[-1] == β_per_expert.shape[0]` pair-check description with `f_per_expert.shape[-1] == cfg.N_e`, splitting the two-layer enforcement across the two Reqs (Layer 1 stays in Req 28, Layer 2 stays in Req 32), with forward references between them. Verified `openspec validate --changes --strict` passes.
- [x] 6.2 **HIGH fix (H1)**: Add `tests/test_safeguards.py::test_resurrection_perturbation_rejects_0d_scalar` — Layer 1 closed-form pytest guarding `f_per_expert.ndim == 0` → `ValueError`. Spec Scenario 4 ("perturbation rejects 0-D scalar f_per_expert") had no pytest in the original archive.
- [x] 6.3 **HIGH fix (H2)**: Add `tests/test_safeguards.py::test_resurrection_perturbation_accepts_history_stacked` — pytest guarding `(T, ..., N_e)` shape (e.g. `(100, cfg.N_e)`) accepts and returns `(cfg.d_c,)`. Spec Scenario 3 ("perturbation accepts history-stacked (T, ..., N_e) f_per_expert") had no pytest in the original archive.
- [x] 6.4 **HIGH fix (H3)**: Remove the duplicate `Scenario: perturbation output shape matches a single expert slot` from Req 32 in live `openspec/specs/wayfinder/spec.md` (it was present in both Req 28 and Req 32, identical text). After this edit, Req 28 retains the generic Scenario as the single-authority primitive-shape contract; Req 32 replaces it with the 5 shape-specific Scenarios per the delta. OpenSpec MODIFIED validation now passes.
- [x] 6.5 **MEDIUM fix (M1)**: Strengthen `tests/test_safeguards.py::test_resurrection_perturb_distribution` (L210) — replace `assert eps.dim() == 1` (weak closure) with `assert eps.shape == (16,)` (integer closure, bare `==`, per CLAUDE.md §6). Now matches spec Scenario 1 ("returned tensor has shape `(d_c,)`").
- [x] 6.6 **MEDIUM fix (M2)**: Strengthen `tests/test_safeguards.py::test_resurrection_perturbation_eps_std_scale` (L322) — replace statistical `assert abs(eps.std().item() - 0.05) < 0.01` with closed-form `assert (eps ** 2).mean().item() == pytest.approx(0.0025, abs=5e-4)` (E[ε²] = ε_std² = 0.05² = 0.0025 closed-form, with 2σ-容差 at d_c=4096). Now matches the spec's `ε ~ N(0, 0.05²·I)` distribution via a closed-form expectation identity rather than a sample statistic.
- [x] 6.7 **MEDIUM fix (M4)**: Update `tests/test_safeguards.py::test_resurrection_perturbation_shape_per_expert` (L307) — replace hard-coded `N_e=8` legacy input with `cfg = MVPConfig(); f = torch.randn(4, 3, cfg.N_e)`. Aligns the test fixture with the MVP-aligned spec Scenario 2 example `(4, 3, 16) at MVP`.
- [x] 6.8 **LOW fix (L1)**: Req 28 body Layer 2 sentence replaced with forward reference to Req 32 — Req 28 (primitive contract) no longer describes wrapper-side enforcement details.
- [x] 6.9 **LOW fix (L2)**: Source field in delta updated to reference both commit `263ac19` (original perturbation contract) and commit `0b2202e` (cfg.N_e correction). Verified `lint_no_source_field_drift` exit=0.
- [x] 6.10 **LOW fix (L3)**: Req 32 body (L13) "same resurrection event" phrasing replaced with forward reference to Req 13 ("The β double-write semantic is defined in Req 13; this wrapper additionally guarantees same-call-stack execution"). Reduces spec internal redundancy between Req 13 and Req 32.
- [x] 6.11 Final verification (round 2): `pytest tests/test_safeguards.py tests/test_schedule.py tests/test_beta.py tests/test_loss.py tests/test_gating.py` = **75 passed** + `lint_no_dead_defensive` exit=0 + `lint_no_source_field_drift` exit=0 + `openspec validate --changes --strict` pass + `openspec validate --archived` pass.
