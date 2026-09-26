## Context

See `proposal.md` "Why" section for motivation. The current state at the start of this change:

- `openspec/specs/decompmoe-skeleton/spec.md` L347-360 holds three orphan `#### Scenario:` blocks ("Parameterization endpoints" / "gamma reset for phase 4 boundary continuity" / "beta_effective is continuous at Phase 3 → 4 boundary") that are **verbatim duplicates** of L427-440 under req-3 ("Beta Parameterization Operational Domain — D1 Module-Level Constants"). The previous change `2026-09-10-fix-wayfinder-and-skeleton-spec-duplicate-requirements` deliberately retained them pending this follow-up cleanup.
- `openspec/specs/decompmoe-skeleton/spec.md` L514-517 holds a generic `SP range bound` scenario (`-1 - 1e-6 ≤ SP ≤ 1 + 1e-6`). The companion req-20 closed-form scenarios cover `SP = 1.0` (orthonormal-aligned, L504-507) and `SP = 0.5` (60° offset, L509-512), but **no closed-form scenario covers `SP = -1.0`** (the antipodal-aligned tight lower bound). `tests/test_metrics.py` mirrors this gap: `test_sp_orthonormal_aligned_inputs` (L171) and `test_sp_60_degree_offset` (L183) exist, but no `test_sp_antipodal_aligned_inputs`.

Constraints:
- `SP` implementation (`src/decompmoe/metrics.py:92-97`) is closed-form correct per `SP_i = mean_{t: a(t)=i} c_iᵀ C_t` — no code change is needed, only spec + test additions.
- Per `CLAUDE.md` §3 + `lint_no_source_field_drift.py`, every `**Source:**` line in `decompmoe-skeleton/spec.md` MUST contain a `wayfinder/tickets/<ID>.md` literal backlink (the default per-capability rule; `REQUIRED_SUBSTRING_BY_PATH_RELATIVE` only special-cases `governance/spec.md` to `CLAUDE.md`). No new `**Source:**` fields are introduced in this change, so this constraint is unchanged.
- Per `CLAUDE.md` §3, archive-gate lints (`lint_no_dead_defensive.py`, `lint_no_source_field_drift.py`) MUST exit=0 before `/opsx:archive` can complete.
- Per `CLAUDE.md` §3, spec-driven changes go through `/opsx:propose` → review → apply → archive; this design is the "how" complement to the proposal's "what".

## Goals / Non-Goals

**Goals:**
- Close the OpenSpec format violation caused by orphan `#### Scenario:` blocks at L347-360.
- Add symmetric closed-form coverage for `SP = -1.0` (antipodal-aligned) under req-20 to match the existing `SP = 1.0` and `SP = 0.5` closed-form coverage.
- Land a corresponding closed-form `pytest.approx(-1.0, abs=1e-6)` test in `tests/test_metrics.py` to drive the new spec scenario from TDD.

**Non-Goals:**
- No change to `src/decompmoe/metrics.py` — the `SP` implementation already satisfies the new scenario's closed form.
- No change to other requirements in `decompmoe-skeleton/spec.md` beyond req-20 (which gets one new scenario appended to its scenario list) and the orphan-block deletion at L347-360.
- No change to `wayfinder/spec.md` or `governance/spec.md` — this change is scoped strictly to `decompmoe-skeleton/spec.md`.
- No retuning of `β_min` / `β_max` / `γ_init` / `k` / `N_e` / `d_model` / `d_ffn` / `L` / `d_c` — all hyperparameters remain frozen at the values declared in CLAUDE.md §5.

## Decisions

### Decision 1: Express the orphan-scenario removal as a `MODIFIED Requirements` delta + an explicit apply-step file edit, not a `REMOVED Requirements` delta

**Why**: the spec-driven delta schema operates on whole `### Requirement:` blocks (`ADDED Requirements` / `MODIFIED Requirements` / `REMOVED Requirements`). The orphan Scenarios at L347-360 have NO parent Requirement — they sit between two `### Requirement:` blocks with only `---` separators between them. There is no schema entry for "remove orphan Scenario block not under any Requirement".

**Alternative considered**: write the delta as `REMOVED Requirements` with a synthetic Requirement name like "Orphan Beta Parameterization Scenarios" — rejected because that creates a fake Requirement name in the archive history just to delete three Scenarios, and the deleted content remains in the main spec at L427-440 (so the "REMOVED Requirements" with `Reason: superseded by ADDED` semantics doesn't apply either).

**Chosen approach**: the orphan-scenario removal is documented as a "Structural Cleanup" section at the end of `specs/decompmoe-skeleton/spec.md` (the delta file), explaining that the apply-step will perform a direct 14-line file edit on the main spec. The MODIFIED Requirements delta only handles req-20 (which adds the new antipodal scenario). Both edits happen in the same apply workflow.

### Decision 2: Use the symmetric `C_t = -c_{a(t)}` construction for the new antipodal scenario, matching the wording of the existing orthonormal scenario

**Why**: the existing `SP closed-form on orthonormal-aligned inputs` scenario (L504-507) reads `C_t = c_{a(t)}` for the upper-bound witness. The new antipodal scenario reads `C_t = -c_{a(t)}` for the lower-bound witness — direct symmetry, same construction style, same `pytest.approx(..., abs=1e-6)` tolerance, same `each SP_i = c_iᵀ (...)` per-expert derivation annotation.

**Alternative considered**: construct antipodal-aligned inputs by re-normalizing after negation — rejected because `c_i ∈ S^{d_c-1}` is already unit-norm, so `-c_i ∈ S^{d_c-1}` is automatic (`‖-c_i‖₂ = ‖c_i‖₂ = 1`); no re-normalization step is needed and adding one would confuse readers.

### Decision 3: Place the new antipodal scenario BETWEEN the existing `SP closed-form on 60° offset` and the generic `SP range bound`

**Why**: the existing scenarios at L504-517 are ordered upper → middle → range:
1. `SP closed-form on orthonormal-aligned inputs` → `SP = 1.0` (upper tight point)
2. `SP closed-form on 60° offset` → `SP = 0.5` (middle)
3. `SP range bound` → `SP ∈ [-1, 1]` (generic range)

Inserting the new antipodal scenario between #2 and #3 gives the ordering upper → middle → **lower** → range, which reads as a monotonic descent through the closed-form witnesses before the generic assertion. This is more intuitive than placing the antipodal scenario after the range bound (which would feel like an afterthought).

### Decision 4: One test, no test refactoring

**Why**: the existing `test_sp_*` style uses `pytest.approx(value, abs=1e-6)` against the closed-form target, with `torch.manual_seed(0)` at the top of the test (per `CLAUDE.md` §3 testing conventions). The new `test_sp_antipodal_aligned_inputs` follows the same pattern — no shared helper, no fixture changes.

**Alternative considered**: refactor `test_sp_orthonormal_aligned_inputs` / `test_sp_60_degree_offset` / new antipodal test into a single parametrized test — rejected because (a) `CLAUDE.md` §3 says "match existing style", (b) parametrization hides the per-scenario closed-form construction (each is a different geometric construction), (c) the existing tests are independently readable and the new test should be too.

## Risks / Trade-offs

- **[Risk] The 14-line edit at L347-360 could fail silently if the `---` separators have been re-flowed since the verification snapshot** — the apply step MUST re-verify the exact byte content of L347-360 before deletion (`grep -n "^---$" openspec/specs/decompmoe-skeleton/spec.md` to find separators, then `awk` or `Read` to confirm the L347-360 range matches the snapshot from the proposal's "Why" section). → **Mitigation**: the apply-step task in `tasks.md` includes a pre-deletion byte-content verification (`grep -B1 -A2 "Parameterization endpoints" openspec/specs/decompmoe-skeleton/spec.md | head -50` confirms the three orphan Scenarios sit between two `---` separators and contain the verbatim text).

- **[Risk] The new SP antipodal scenario's `C_t = -c_{a(t)}` construction could fail the `L2 normalize` postcondition test** if `c_i` is not exactly unit-norm in the test setup. → **Mitigation**: the new `test_sp_antipodal_aligned_inputs` MUST call `F.normalize(centroids, dim=-1)` before constructing the antipodal signatures (same pattern as `test_sp_orthonormal_aligned_inputs` at L171 which uses `F.normalize(torch.randn(...), dim=-1)` to seed unit-norm centroids).

- **[Risk] The MODIFIED Requirements delta for req-20 must copy the FULL block, not a partial extract** — the archive process will replace the entire req-20 block with the delta's version. Any text drift between the snapshot in the delta and the current main spec will appear as a false-positive diff in the git log. → **Mitigation**: the apply-step task MUST `diff` the delta's req-20 block against the current main spec's req-20 block (excluding the new scenario) and confirm byte-equal before archiving.

- **[Trade-off] Skipping `design.md` was allowed per the spec-driven schema's "create only if any apply" rule, but the project convention (per `2026-09-10-fix-wayfinder-and-skeleton-spec-duplicate-requirements`) does create `design.md` for similar cleanup changes.** → **Choice**: this change DOES create `design.md` (you are reading it) to match the project convention, even though the technical decisions are minimal.

## Migration Plan

This is a spec + test change with no production code impact. No deployment / rollback needed.

- **Pre-archive**: run `python scripts/lint_no_dead_defensive.py` and `python scripts/lint_no_source_field_drift.py` (both MUST exit=0). Run `uv run pytest tests/test_metrics.py -v` to confirm all existing `test_sp_*` tests still pass and the new `test_sp_antipodal_aligned_inputs` passes.
- **Archive**: `/opsx:archive fix-skeleton-spec-duplicate-and-completeness-2026-09-15 --yes` (after apply step lands the edits and all gates pass).
- **Post-archive**: re-run the three gates above on the main `decompmoe-skeleton/spec.md` to confirm the changes survived the archive merge cleanly. Total Scenario count should be 77 (76 + 1 new).

## Open Questions

None. All decisions are grounded in the existing test patterns at `tests/test_metrics.py:171` / `tests/test_metrics.py:183` and the existing spec wording at L504-507 / L509-512. No deferrable unknowns remain.