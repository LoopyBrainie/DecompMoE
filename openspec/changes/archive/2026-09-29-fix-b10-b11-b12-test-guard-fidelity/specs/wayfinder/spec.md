# Spec Delta — `wayfinder`

## MODIFIED Requirements

<a id="req-13"></a>

### Requirement: Numerical Safeguards

The system MUST execute the standard training step as `Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i)`, which is a first-order Riemannian SGD equivalent on the spherical constraint. The system MUST implement all five safeguards: (1) Global Gradient Clipping at threshold `1.0` covering all learnable parameters; (2) NaN Detection & Escalation with `1 skip → 3 consecutive NaN trigger LR ÷ 10 → 10 consecutive NaN halt training`; (3) Dead Expert Splitting Resurrection triggered when `f_i^avg < 1 / (2 · N_e)` for 200 consecutive steps (clones `j* = argmax f_j^avg`, perturbs with `ε ~ N(0, 0.05² I)`, sets `β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`, rate-limited to once per 1000 steps). At MVP scale `N_e = 16`, `1/(2 · N_e) = 1/32`; the rule is `f_threshold = 1/(2 · N_e)` parameterized by `N_e`, not a hardcoded `1/128` from a prior `N_e = 64` design; (4) β Saturation Guard with warning at `β_i > 30.4` (95% of `β_max`) and global `LR ÷ 2` when more than 50% of experts have `β_i > 28.8` (90% of `β_max`); (5) Loss Spike Defense in Phase 3+ with `L_task > 2.5 · EMA(L_task)` triggering `LR × 0.8`.

**Source:** `wayfinder/tickets/A6a-2.md` (historical, threshold `1/128`), change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold superseded by `1/(2·N_e)`); change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` design.md (Decision 4 — rate-limit window edge pinned as exclusive (`Δ = R` not deferred) and the per-window-quota reading corrected to the implemented per-call deferral gate)

#### Scenario: Standard step ordering
- **WHEN** a training step completes
- **THEN** the order is `Backward → clip(1.0) → step → L2_norm(c_i)` and `c_i` lies on the unit sphere after the step

#### Scenario: NaN escalation ladder
- **WHEN** consecutive NaN step counts are 1, 3, and 10 respectively
- **THEN** the responses are: skip + zero_grad (+ AMP scaler decay); `LR ÷ 10`; halt and alert

#### Scenario: Resurrection respects rate limit
- **WHEN** `should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, ...)` is called with `Δ := current_step − last_resurrection_step` and `R := RESURRECTION_RATE_LIMIT_STEPS` (at MVP `R = 1000`)
- **THEN** the call is **deferred** — it returns `set()` at the rate-limit guard — **if and only if `Δ < R`**. The window edge is **exclusive**: `Δ = R` is **not** deferred and the call proceeds to the dead-expert trigger. The normative formalization (monotone single-jump predicate, the per-pair window equivalence, and the `R`-aligned counterexample that fixes the edge) is `openspec/specs/decompmoe-skeleton/spec.md` req-12 Scenario "Resurrection rate-limited"; guarded by `tests/test_safeguards.py::test_should_resurrect_rate_limit_boundary`. **Scope correction**: the prior wording — "two experts meet the dead-expert trigger within the same 1000-step window … only one resurrection event executes; the second is deferred" — described a **per-window quota of one resurrection**, which `should_resurrect` does **not** implement: it returns **every** expert satisfying the per-step trigger in the call (`src/decompmoe/safeguards.py:98-102`, no one-per-window clipping). The rate limit is a **per-call deferral gate** only, and this Scenario is restated to match the implemented contract; the superseded reading is recorded here rather than silently dropped.

#### Scenario: Beta saturation guard
- **WHEN** any single executor reaches `β_i > 30.4` or more than 50% of experts cross `β_i > 28.8`
- **THEN** the system logs a warning or halves the global learning rate respectively