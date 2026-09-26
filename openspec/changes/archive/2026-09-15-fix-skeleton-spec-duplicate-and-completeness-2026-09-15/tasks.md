## 1. Pre-flight verification (snapshot + lint gates baseline)

- [x] 1.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0 (baseline gate before any edits; per CLAUDE.md §3 archive precondition)
- [x] 1.2 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0 (baseline gate; per CLAUDE.md §3 archive precondition)
- [x] 1.3 Run `uv run pytest tests/test_metrics.py -k "test_sp_" -v` and verify all 4 existing `test_sp_*` tests pass (`test_sp_orthonormal_aligned_inputs` / `test_sp_60_degree_offset` / `test_sp_skips_empty_experts` / `test_sp_range_containment`) — establish green baseline before adding the 5th test
- [x] 1.4 Verify L347-360 still contains the three orphan Scenarios verbatim (proposal's "Why" section is the snapshot): run `Select-String -Path openspec/specs/decompmoe-skeleton/spec.md -Pattern '^#### Scenario: (Parameterization endpoints|gamma reset for phase 4 boundary continuity|beta_effective is continuous at Phase 3 → 4 boundary)$'` and confirm 6 matches total (3 orphans at L349/L353/L357 + 3 canonical at L427/L432/L437 under req-3)

## 2. Remove orphan Scenarios (L347-360)

- [x] 2.1 Edit `openspec/specs/decompmoe-skeleton/spec.md` to delete the 14-line range L347-360 inclusive (the `---` separator at L347, the three `#### Scenario:` blocks at L349-352 / L353-355 / L357-360, and the trailing `---` separator at L361-362); verify the deletion succeeded by running `Select-String -Path openspec/specs/decompmoe-skeleton/spec.md -Pattern '^#### Scenario: (Parameterization endpoints|gamma reset for phase 4 boundary continuity|beta_effective is continuous at Phase 3 → 4 boundary)$'` and confirming exactly 3 matches (the canonical L413/L418/L423 instances under req-3, NOT 6 matches as before — orphans removed)
- [x] 2.2 Run `grep -n '^### Requirement:' openspec/specs/decompmoe-skeleton/spec.md` and verify req count stays `22` (orphan Scenarios are NOT under any Requirement, so no Requirement was deleted)
- [x] 2.3 Run `Select-String -Path openspec/specs/decompmoe-skeleton/spec.md -Pattern '^#### Scenario:'` and verify the count is now `79` (was `82` before deletion = `79 + 3 orphans`; net `-3` from orphan deletion; the actual numbers were higher than my pre-edit estimate of 77/76)

## 3. Add new `SP closed-form on antipodal-aligned inputs` scenario to req-20

- [x] 3.1 Edit `openspec/specs/decompmoe-skeleton/spec.md` to insert the new scenario immediately AFTER `#### Scenario: SP closed-form on 60° offset` and BEFORE `#### Scenario: SP range bound`; new scenario lands at L500 (header), L502 WHEN, L503 THEN (verified)
- [x] 3.2 Verify the inserted scenario is byte-identical to the proposed delta; run `Select-String -Path openspec/specs/decompmoe-skeleton/spec.md -Pattern 'SP closed-form on antipodal-aligned inputs'` and confirm exactly 1 match
- [x] 3.3 Run `Select-String -Path openspec/specs/decompmoe-skeleton/spec.md -Pattern '^#### Scenario:'` and verify the count is now `80` (was `79` after orphan deletion; +1 new scenario = `80` net)
- [x] 3.4 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0 (no `**Source:**` field added with the new scenario, so no new violation should appear)

## 4. TDD: add `test_sp_antipodal_aligned_inputs` (red → green)

- [x] 4.1 Add `def test_sp_antipodal_aligned_inputs() -> None:` to `tests/test_metrics.py` immediately AFTER `test_sp_60_degree_offset` (L183) (no `torch.manual_seed(0)` — mirrors existing `test_sp_orthonormal_aligned_inputs` pattern); construct `centroids = F.normalize(torch.randn(N_e, d_c), dim=-1)`, `assign = torch.randint(0, N_e, (T,))`, `C = -centroids[assign]` (antipode), assert `sp.item() == pytest.approx(-1.0, abs=1e-6)` — test PASSES on first try
- [x] 4.2 Run `uv run pytest tests/test_metrics.py::test_sp_antipodal_aligned_inputs -v` and verify the new test passes with the expected `≈ -1.0 within abs=1e-6` assertion
- [x] 4.3 Run `uv run pytest tests/test_metrics.py -k "test_sp_" -v` and verify all 5 `test_sp_*` tests pass (4 existing + 1 new) — confirm no regression

## 5. Post-edit verification gates (archive precondition)

- [x] 5.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0 (final gate; per CLAUDE.md §3 archive precondition + per `db14222` fix preventing archived change with lint red) — exit=0 ✓
- [x] 5.2 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0 (final gate; per CLAUDE.md §3 archive precondition) — exit=0 ✓
- [x] 5.3 Run `openspec validate fix-skeleton-spec-duplicate-and-completeness-2026-09-15 --type change --strict` and verify exit=0 (delta + main spec are consistent) — pass ✓
- [x] 5.4 Run `uv run pytest tests/test_metrics.py -v` and verify all `test_metrics.py` tests pass (no regression in non-`test_sp_*` tests like `test_l_sep_*` / `test_r_h_*` / `test_mci_*` / `test_d_chord_*` / `test_cg_*`) — 25/25 passed ✓
- [x] 5.5 Run `openspec status --change fix-skeleton-spec-duplicate-and-completeness-2026-09-15` and verify `isComplete: true` + all artifacts `done` (proposal + specs + design + tasks all present and reachable) — `isPlanningComplete: true`, `isComplete: true`, artifacts: `proposal=done, specs=done, design=done, tasks=done` ✓

## 6. Archive

- [x] 6.1 Run `openspec archive fix-skeleton-spec-duplicate-and-completeness-2026-09-15 --yes` and verify the change moves to `openspec/changes/archive/2026-09-15-fix-skeleton-spec-duplicate-and-completeness-2026-09-15/` with the delta merged into `openspec/specs/decompmoe-skeleton/spec.md` (req-20 picks up the new antipodal scenario; the L347-360 orphan Scenarios are permanently removed); total spec scenario count for `decompmoe-skeleton` is `80` (final post-archive count, NOT the `77` I had estimated in the task description — pre-edit was `82 = 79 + 3 orphans`, post-edit is `79` after orphan removal, post-archive is `80` after the new antipodal scenario is merged in via MODIFIED Requirements)
- [x] 6.2 Post-archive: re-run all three gates (`lint_no_dead_defensive.py`, `lint_no_source_field_drift.py`, `uv run pytest tests/test_metrics.py`) and verify exit=0 on the archived state — all 3 gates pass (lint_no_dead_defensive exit=0, lint_no_source_field_drift exit=0, pytest 25/25 passed)