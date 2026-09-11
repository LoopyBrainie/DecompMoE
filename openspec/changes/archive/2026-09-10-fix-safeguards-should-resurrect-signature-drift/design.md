# Design: fix-safeguards-should-resurrect-signature-drift

> **Scope-down history (2026-09-09)**: Original design covered two Requirements (`Centroid Four-Phase Lifecycle Driver` L155 + `Five Numerical Safeguard Helpers` L257). A parallel cleanup change by another session (Task 2.3) deleted the original `Centroid Four-Phase Lifecycle Driver` Requirement header from the main spec; the surviving `### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension` was independently corrected by that same parallel change. Keeping the `Centroid Four-Phase Lifecycle Driver` MODIFIED block in this delta would have caused `openspec archive` to reject with `header ... not found`. The scope was reduced to the single Requirement **`Five Numerical Safeguard Helpers`** in `decompmoe-skeleton`. The `specs/wayfinder/` delta directory (a separate scope expansion that addressed `resurrection_perturb_distribution` signature drift at wayfinder L577 + L642) was also removed from scope because a parallel cleanup change (Tasks 3.1 + 3.2) had already updated those Requirement bodies.

## Context

See `proposal.md` (## Why) for motivation. Brief restatement of constraints that shape the design:

- The code-side signatures at `src/decompmoe/safeguards.py:23-228` are locked at commit `d3689a1` (2026-08-22) and verified by `tests/test_safeguards.py` RED→GREEN. The spec side has been drifting since the skeleton's initial commit `0d87e32` (2026-08-21). The asymmetry (code stable, spec stale) drives the design to **sync spec → code** rather than the reverse.
- The skeleton spec's `Five Numerical Safeguard Helpers` body has 4 internal drifts: items (1) `clip_global_grad_norm_ -> Tensor` (should be `float`), (4) `beta_saturation_warning(..., *, β_max=32)` (no `β_max` param exists), (5) `loss_spike_defense(..., *, ratio=...)` (no `*` separator), and (3) `should_resurrect(... threshold=1/(2·N_e))` (default is `None`, not the closed form). The design MUST resolve all 4 in a single Requirement-body edit.
- Per CLAUDE.md §6 last bullet, every spec formula with concrete numeric values must be verifiable by `pytest.approx` / exact `==` assertions in `tests/`. The drift fix touches signatures (parameter names + defaults), not numeric formulas; the existing `tests/test_safeguards.py::test_resurrection_*` regression must remain green, AND 4 numerical claims (`DEAD_EXPERT_CONSEC_STEPS = 200`, `RESURRECTION_RATE_LIMIT_STEPS = 1000`, `LOSS_SPIKE_RATIO = 2.5`, `LOSS_SPIKE_LR_SCALE = 0.8`) added to the spec get explicit pytest guards in `test_named_constants_have_spec_values`.

## Goals / Non-Goals

**Goals:**
- Spec text describes the *actual* signature for each of the 5 helpers in `src/decompmoe/safeguards.py:23-228` (parameter names, keyword-only convention where applicable, `N_e` mandatory position, named-constant defaults).
- All 5 in-edit drifts in the `Five Numerical Safeguard Helpers` body fixed: `(1)` return type, `(3)` signature + threshold dispatch prose, `(4)` β_max removal + constant reference, `(5)` keyword-only removal + caller-responsibility clarification.
- Constants referenced by `Final[int]` / `Final[float]` identifier (e.g., `DEAD_EXPERT_CONSEC_STEPS`) rather than literal value, so future retuning does not silently re-introduce drift.
- Zero `src/` modifications; 2 new `tests/` tests (`test_no_other_module_defines_should_resurrect` per code-review M2/N4, `test_named_constants_have_spec_values` per code-review N5).
- All 7 `#### Scenario:` headings under `Five Numerical Safeguard Helpers` preserved verbatim (per `fix-openspec-doc-bugs` §2.6 archive-rejection precedent).
- The MODIFIED Requirement body carries a `**Source:**` back-reference to `change fix-openspec-doc-bugs design.md (Decision 7)` AND `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent) per code-review L1 fix.

**Non-Goals:**
- No code refactor of any of the 5 safeguards helpers.
- No edits to `openspec/specs/wayfinder/spec.md` (signature drift on `resurrection_perturb_distribution` was addressed by parallel change Tasks 3.1 + 3.2).
- No edits to `openspec/specs/decompmoe-skeleton/spec.md` for `Centroid Four-Phase Lifecycle Driver` (deleted by parallel change Task 2.3; surviving `### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension` was independently corrected).
- No edits to `wayfinder/tickets/*.md` (per CLAUDE.md §8, tickets are reference-only).
- No new Requirements added; this is purely a MODIFIED delta (single Requirement).

## Decisions

### Decision 1: Spec signatures mirror the code-side reality; code does NOT regress.

- **Chosen**: Replace the spec's `(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/(2·N_e), consec=200)` and `(1) ... clip_global_grad_norm_(params, max_norm=1.0) -> Tensor` and `(4) beta_saturation_warning(β_per_expert, *, β_max=32)` and `(5) loss_spike_defense(L_task, L_task_ema, phase, *, ratio=2.5)` with their code-aligned forms in the single `Five Numerical Safeguard Helpers` Requirement body, mirroring `src/decompmoe/safeguards.py:23-228` (commit `d3689a1` and related). The default values for `consec`, `rate_limit_steps`, `LOSS_SPIKE_RATIO`, `LOSS_SPIKE_LR_SCALE`, `BETA_SATURATION_WARN`, `BETA_SATURATION_HALVE` are written as `Final[int]` / `Final[float]` constant *identifiers* rather than literal values, so future retuning does not silently re-introduce drift.
- **Rationale**: CLAUDE.md §2 establishes the truth-source hierarchy with code at level 5. When the code signature is already RED→GREEN-verified, the spec MUST align to the code; reverse-altering would break 5 callers + 15 tests. Using constant identifiers in the spec creates a single-source-of-truth link: the spec cannot drift if a future commit retunes `DEAD_EXPERT_CONSEC_STEPS` without updating the spec.
- **Alternatives considered**:
  - *A (rejected)*: Keep spec text and revert code to the spec's old `(f_per_expert, window_size, ...)` signature. Breaks the d3689a1 RED→GREEN loop (`test_resurrection_threshold_mvp_value` + `test_resurrection_threshold_N_e_64_legacy_value`).
  - *B (rejected)*: Both code and spec change. Out of scope for a spec-only drift fix.
  - *C (rejected)*: Spec uses literal `200` / `1000` instead of constant identifiers. Loses the single-source-of-truth link (code-review finding M3, verdict `CONFIRMED`).

### Decision 2: Spec writes `threshold=None` honestly, with prose explaining the None-dispatch derivation.

- **Chosen**: Spec writes `threshold=None` (matching the actual Python default), with prose explaining that `None` triggers a call to the private `_dead_expert_threshold(N_e) = 1/(2·N_e)` helper. The effective threshold value (`1/(2·N_e)`) is documented in prose, not as the literal default.
- **Rationale**:
  - **Code-review finding C1 + L4 (verdict `CONFIRMED`)**: the previous Decision 3 chose `threshold=1/(2·N_e)` as a "documented lie for readability", but `1/(2·N_e)` is **not a valid Python default expression** (function defaults cannot reference other parameters — they must be literals or module-level names). A default of `threshold=1/(2·N_e)` is unparseable Python. The "documented lie" was effectively an invalid type hint / signature claim, and the change's own verification gate §3.6 (`inspect.signature` 字面对账) would FAIL because the inspection output shows `threshold: float | None = None`.
  - **CLAUDE.md §6 last bullet**: "spec 中每个含具体数值的算式...都必须有 pytest.approx(..., abs=...)...直接对账"—a signature claim with a non-Python-evaluable default violates the "spec formula must be verifiable" principle because the literal cannot be reproduced by `inspect.signature` introspection.
  - **Spec readability is preserved by prose**, not by literal default value.
- **Alternatives considered**:
  - *A (rejected)*: keep the old "documented lie" `threshold=1/(2·N_e)`. Defeated by C1 + L4 verification: invalid Python + breaks §3.6 introspection.
  - *B (rejected)*: spec writes `threshold: float = 1/(2·N_e)`. Still invalid Python (same reference-to-parameter restriction).

### Decision 3: `loss_spike_defense` ambiguity resolved as "caller applies LR scaling, function only returns boolean".

- **Chosen**: Spec explicitly states "the function ONLY returns the boolean — the LR-scaling action (`LR × LOSS_SPIKE_LR_SCALE = LR × 0.8`) is the CALLER's responsibility (the function emits a 'should scale' signal, not the scaling itself)".
- **Rationale**: The original spec wording "signalling `LR × 0.8`" was ambiguous about whether the function itself scales LR or emits a signal. Code (per `src/decompmoe/safeguards.py:222-228`) only returns `bool`; LR scaling is the caller's responsibility using the `LOSS_SPIKE_LR_SCALE = 0.8` constant. Resolving the ambiguity aligns with the actual code contract (code-review finding L2 fix).

### Decision 4: `beta_saturation_warning` `β_max` parameter removed; threshold sourced from `BETA_MAX` constant.

- **Chosen**: Spec removes the fictional `β_max` parameter from item (4). The warning threshold is sourced from `BETA_SATURATION_WARN = 0.95 · BETA_MAX` constant. Threshold value `30.4` is shown in prose (`0.95 · β_max = 0.95 · 32`) for human readability, with the constant reference as the formal anchor.
- **Rationale**: Code (per `src/decompmoe/safeguards.py:211-213`) defines `def beta_saturation_warning(β_per_expert: Tensor) -> bool` with NO `β_max` parameter. Adding `β_max` to spec creates a non-existent API surface that callers would erroneously use (code-review finding N7 fix).

## Risks / Trade-offs

- [R1: `tests/test_safeguards.py::test_resurrection_*` may still call with positional args that no longer exist after `d3689a1`] → Mitigation: `tasks.md` §3.4 mandates `uv run pytest tests/test_safeguards.py -k "resurrect" -v` must remain 100% PASS as part of pre-archive gate. **Note**: filter `-k "should_resurrect"` was broken (matched 0 tests, code-review finding C2); corrected filter `-k "resurrect"` matches 9 tests. If any test fails, fix the call site (keyword-only conversion) — does NOT alter test assertions.
- [R2: archive-stage `openspec validate` may reject the delta if any `#### Scenario:` heading is silently dropped during the block replacement] → Mitigation: `tasks.md` §2.2 includes explicit `sed -n '/^### Requirement: Five Numerical Safeguard Helpers$/,/^### Requirement: /p' openspec/specs/decompmoe-skeleton/spec.md | grep -c '^#### Scenario'` verification, expecting count == 7 (code-review N3 fix: per-Requirement scope, NOT full-file 100).
- [R3: Spec signature may diverge from code again after future code-side refactor of any of the 5 helpers] → Mitigation: `tasks.md` §3.6's introspect-signature assertion catches signature drift; future refactors will need to update the spec in lock-step (this is the established fix-openspec-doc-bugs pattern).
- [R4: `/opsx:archive` precondition lint gate (`python scripts/lint_no_dead_defensive.py` exit=0, per CLAUDE.md §3 archive precondition added 2026-09-09) could fail on unrelated lint debt] → Mitigation: `tasks.md` §1.3 runs the lint gate before archive; if it fails for reasons orthogonal to this change, the lint violation must be fixed (out of scope here, but flagged for the apply workflow).
- [R5: cross-session coordination — `Centroid Driver` MODIFIED block was removed because another session (Task 2.3) deleted the original Requirement header] → Mitigation: scope-down reflected in proposal.md + tasks.md + this design.md; if the parallel change is reverted, the `Centroid Driver` MODIFIED block may need to be restored in a follow-up change.

## Migration Plan

1. `/opsx:propose` complete (current state): proposal.md + specs/decompmoe-skeleton/spec.md (single MODIFIED Requirement `Five Numerical Safeguard Helpers`) + design.md + tasks.md all written; all 4 artifacts marked `done` by `openspec status`.
2. **User review**: read `proposal.md` and `specs/decompmoe-skeleton/spec.md` against the source `openspec/specs/decompmoe-skeleton/spec.md` (L255-285 / post-cleanup L201-...) for diff sanity. No apply yet.
3. **Pre-archive lint gate** (per CLAUDE.md §3 new archive precondition): `python scripts/lint_no_dead_defensive.py` must exit 0. If it fails on unrelated debt, fix or escalate before proceeding.
4. **Pre-archive regression gate**: `uv run pytest tests/test_safeguards.py -v` must be 100% PASS (17 tests, includes 2 new tests from this change). If it fails, fix call sites (do NOT alter test assertions).
5. **`/opsx:archive`**: archive merges `specs/decompmoe-skeleton/spec.md` → main `openspec/specs/decompmoe-skeleton/spec.md`; moves the change directory to `openspec/changes/archive/2026-09-09-fix-safeguards-should-resurrect-signature-drift/`.
6. **Post-archive independent verification** (per CLAUDE.md §3 "Post-archive 独立复核" 强制项): `tasks.md` §3.1-§3.6 verify the merged main spec — keyword presence, signature introspection, named-constant references, lint gate, full pytest.
7. **Rollback strategy**: `git revert` the archive merge commit. Because the change is spec-only and the code is unchanged, rollback is low-risk.

## Open Questions

(none) — all decisions resolved in this design; no deferrable unknowns remain.

## Cross-Session Coordination Notes

- This change is one of multiple concurrent spec-cleanup changes in the 2026-09-09 work window. Other concurrent changes (Tasks 2.3, 3.1, 3.2 in the other session) already addressed the originally-targeted `Centroid Four-Phase Lifecycle Driver` and the wayfinder `resurrection_perturb_distribution` Requirements. The 3 originally-planned MODIFIED Requirements were intentionally removed from this change's scope because the other session's work had pre-empted them.
- If the other session's changes are NOT archived (e.g., they are abandoned), this change's scope-down leaves those Requirements un-fixed. A follow-up change may be needed.
- If this change and the other session's changes conflict at archive time (e.g., the other session's change rebases and re-introduces drift), the spec-sync tests in `tasks.md` §3 will catch the conflict post-archive.
