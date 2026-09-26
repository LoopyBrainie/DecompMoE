# decompmoe-skeleton spec delta — anchor insertion (Finding 1)

## MODIFIED Requirements

### Requirement: Five-Phase Schedule State Machine

The package SHALL provide `phase_id(step: int) -> int` returning `0` for `step ∈ [0, 999]`, `1` for `[1_000, 5_999]`, `2` for `[6_000, 25_999]`, `3` for `[26_000, 55_999]`, `4` for `[56_000, 100_000]`. The package SHALL provide `phase_step_frozen_names(phase: int) -> set[str]` returning the **gradient-channel** parameter-name set to freeze per phase (`{"c_i", "beta_i", "W_K", "W_V", "b"}` for phase 1; `{"c_i", "beta_i"}` for phase 2 — `W_K/W_V/b` are unfrozen in phase 2 to allow them to train under the EMA; `{"c_i"}` for phase 3 — `beta_i` is unfrozen; empty for phases 0/4). The package SHALL provide `should_reset_adam(prev_phase: int, next_phase: int) -> bool` returning `True` exactly when `prev_phase == 3 and next_phase == 4`. The advisory signals (`R_H`, `S_load`, `R_β-sat`, `L_sep/WB`) SHALL be exposed via `advisory_signals(...)` but SHALL NEVER trigger phase transitions (state-machine invariance under perturbed advisory is asserted).

#### Scenario: Phase boundaries at 100K
- **WHEN** `total_steps == 100_000`
- **THEN** the phase boundaries are `(1_000, 6_000, 26_000, 56_000, 100_000)` and phase `0 / 1 / 2 / 3 / 4` step ratios are `1% / 5% / 20% / 30% / 44%`

#### Scenario: Phase-1 router freeze
- **WHEN** `phase_step_frozen_names(1)` is called
- **THEN** the result equals `{"c_i", "beta_i", "W_K", "W_V", "b"}` (the gradient-channel frozen set; driver channel still updates `c_i` via EMA at `α = 0.90`)

#### Scenario: Phase-2 expert freeze
- **WHEN** `phase_step_frozen_names(2)` is called
- **THEN** the result equals `{"c_i", "beta_i"}` (gradient-channel frozen; `W_K/W_V/b` are unfrozen to learn under the driver-channel EMA at `α = 0.95`)

#### Scenario: Adam reset boundary
- **WHEN** `should_reset_adam(3, 4)` is called
- **THEN** it returns `True`; for every other `(prev, next)` pair it returns `False`

## Delta-only annotation (not part of main spec)

**This delta re-states the existing Requirement body verbatim (no semantic change).** The only modification on the canonical main spec `openspec/specs/decompmoe-skeleton/spec.md` is:

- **Insert `<a id="req-13"></a>` as a new line above the existing `### Requirement: Five-Phase Schedule State Machine` heading** (formerly at L293; after insertion at L292 with 1 blank line separator).
- No Requirement body text modified.
- No Scenario text modified.
- No Phase boundaries values modified (still `(1_000, 6_000, 26_000, 56_000, 100_000)`).
- No `phase_step_frozen_names` set literals modified (phase 0/4 still empty per spec narrative).

**Why this anchor was missing (audit context)**:

`openspec/specs/decompmoe-skeleton/spec.md` carried 23 `### Requirement:` headings but only 22 `<a id="req-N"></a>` anchors. The missing slot was `req-13`, between `req-12` (L226, "Five Numerical Safeguard Helpers") and `req-14` (L313, "Six Visualization Module Protocol Stubs"). The "Five-Phase Schedule State Machine" Requirement at L293 had full body content (narrative + 4 Scenarios) but no anchor — a 100% anchor coverage violation per `CLAUDE.md` §6 第 8 条.

**Audit root cause**: schema evolution gap. A previous change consumed the `req-13` slot without re-anchoring the existing Requirement at L293. Per agent memory lesson "spec 文件的 anchor 序列是 schema 演化的残留（每次 change 增/删/合并都会留下空洞）", such gaps are detectable only by实测 `grep -nE '<a id="req-([0-9]+)"></a>'` and reconciling anchor count against `### Requirement:` count — no shortcut via "现有 N 个 anchor, next = N+1".

**Why MODIFIED (not ADDED)**: the Requirement body is unchanged; only the reverse-linkable anchor metadata is added. Using `## ADDED Requirements` would create a new Requirement body that doesn't exist on canonical spec (orphan), violating the delta archive contract. `## MODIFIED Requirements` re-states the existing body verbatim, with the body diff being only the metadata addition above the heading (which doesn't appear in the Requirement body itself).

**Cascade impact**: zero. The new `<a id="req-13"></a>` fills the existing schema gap; no downstream `req-14..23` references are affected. No `**Source:**` field, no ticket annotation, no test docstring needs to migrate.

## Acceptance check

- `grep -nE '<a id="req-([0-9]+)"></a>' openspec/specs/decompmoe-skeleton/spec.md | wc -l` returns **23** (was 22)
- `grep -c '^### Requirement:' openspec/specs/decompmoe-skeleton/spec.md` returns **23** (unchanged)
- Anchor-to-Requirement count reconciliation: 23 anchors / 23 Requirements = **100% coverage** (was 96%)
- `wayfinder/spec.md` already 36/36 (100%, unchanged)
- **decompmoe-skeleton/wayfinder/governance** total anchor coverage: 23+36+4 = 63 anchors / 63 Requirements = 100%
- python `scripts/lint_no_dead_defensive.py` exit=0
- python `scripts/lint_no_source_field_drift.py` exit=0
- byte-level CRLF count on `openspec/specs/decompmoe-skeleton/spec.md` = 0 (LF preserved)
- The post-state `<a id="req-13"></a>` is positioned 1 blank line above the existing `### Requirement: Five-Phase Schedule State Machine` heading, preserving the project's "anchor 1 blank line above heading" layout convention (verified against all 22 pre-existing anchor+heading pairs)
- All existing pytest still passes: `uv run pytest tests/` → 199 passed (no test file modified by spec delta; only by the 2 principle test changes documented separately in proposal.md / tasks.md)