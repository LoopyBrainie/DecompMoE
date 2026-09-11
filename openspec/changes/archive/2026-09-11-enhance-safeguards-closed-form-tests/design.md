## Context

The `Five Numerical Safeguard Helpers` Requirement (`decompmoe-skeleton` L204) has the existing post-`d3689a1` signature description committed in working dir (verified by `git diff openspec/specs/decompmoe-skeleton/spec.md`), but this session's review surfaced two gaps (see `proposal.md` — Why):

1. **Spec ambiguity on `should_resurrect` semantics** — wayfinder L249's `f_i^avg < 1/(2·N_e)` wording admits two interpretations (per-step strict less-than vs literal mean-over-window); current implementation uses (a) but the spec body did not commit to either reading.
2. **Closed-form test guards missing** — per `CLAUDE.md §6` last bullet, every spec formula with concrete numeric values MUST have a `pytest.approx` (float closed-form) or exact `==` (integer closed-form) direct guard; 0 such guards existed for the 6 closed-form spec claims (`1/(2·16)=1/32`, `1/(2·64)=1/128`, `0.95·32=30.4`, `0.90·32=28.8`, `0.1=LR÷10`, `0.8=LR×4/5`) and 4 boundary semantics were untested.

This change is **enhancement-only**: zero production code changes (`src/decompmoe/safeguards.py` already matches the chosen per-step interpretation); the work is pure spec addition + test guard expansion.

## Goals / Non-Goals

**Goals:**
- Pin the per-step strict-less-than interpretation of `should_resurrect` in the spec body so downstream callers can rely on the trigger behavior for non-constant history
- Add 10 new pytest functions + extend 1 existing test that exhaustively assert the closed-form spec claims per `CLAUDE.md §6` last bullet
- Document the open follow-up (avg-window reading) as a separate ticket marker so a future decision can update spec + code + test atomically
- Maintain `openspec validate --strict` clean and `python scripts/lint_no_dead_defensive.py` exit 0 at archive time

**Non-Goals:**
- Deciding the avg-vs-per-step semantic question (deferred to a separate ticket per `proposal.md` Impact)
- Modifying `src/decompmoe/safeguards.py` (current implementation is correct under the chosen interpretation)
- Modifying `src/decompmoe/{beta,schedule,...}.py` (out of Issue 2 scope)
- Retroactive correction of the botched `archive/2026-09-10-fix-safeguards-should-resurrect-signature-drift/` apply stage (separate concern)
- Updating `archive/2026-09-10-.../tasks.md` to acknowledge the apply-stage caveat (would mutate a historical record)

## Decisions

### Decision 1: Per-step strict-less-than is the canonical interpretation (deferred decision is documented)

The current code at `src/decompmoe/safeguards.py:97-101`:
```python
recent = f_history[-consec:]
flagged = set()
for i in range(N_e):
    if all(snap[i] < threshold for snap in recent):
        flagged.add(i)
return flagged
```

implements "expert `i` is dead iff every per-step `f_i` in the last `consec` snapshots was below threshold" — i.e. the per-step reading of wayfinder L249's `f_i^avg < 1/(2·N_e) for 200 consecutive steps` (interpretation: "per-step `f_i < threshold` sustained over the 200-snapshot window").

**Rationale**:
- The current code's behavior is unambiguous and matches wayfinder's stricter trigger (any single `f_i` above threshold in the window suppresses resurrection, which is the more conservative reading).
- `f_i^avg` could also be read as literal "moving average over the window" but the code clearly implements the per-step reading, so the spec should commit to that.
- A future change to avg-window semantics would require spec + code + test alignment atomically — hence the explicit **Open follow-up** note in the new Scenario and the new guard test `test_should_resurrect_current_per_step_semantic_pinned`.

**Alternatives considered**:
- Avg-window reading: `mean(f_history[-consec:][j][i]) < threshold` — would be more lenient (allows occasional spikes); rejected for this change because (a) the current code does not implement it, (b) deciding avg-vs-per-step is explicitly out of scope per the proposal's Goals/Non-Goals.
- Strict notation unification: rewrite wayfinder L249 to use unambiguous wording — rejected because (a) this change is `decompmoe-skeleton`-only, (b) wayfinder edits would require a separate change.

### Decision 2: Closed-form test guards use `pytest.approx(value, abs=1e-12)` for floats, bare `==` for integers

Per `CLAUDE.md §6` last bullet ("integer claims MUST use bare `==` integer equality ... NOT `pytest.approx(...)` in any form") and the same bullet's float half ("float claims ... `pytest.approx` with `abs=1e-12`").

**Rationale**: CLAUDE.md §6 last bullet is a hard constraint; the new tests use the prescribed tolerance pattern. The choice of `abs=1e-12` matches the canonical "钉值零容差" tolerance already used in the existing `test_named_constants_have_spec_values` (LOSS_SPIKE_RATIO and LOSS_SPIKE_LR_SCALE assertions), preserving consistency.

**Alternatives considered**:
- `pytest.approx(value, rel=1e-12)` — rejected because the "effective-tolerance formula `max(abs, rel·|expected|)` scales with magnitude and defeats '钉值零容差'" per the existing test's inline rationale (L353-355 of `test_named_constants_have_spec_values`).
- Bare `==` for floats — rejected because FP literals are not exact except for limited representable values; `0.95 * 32.0 == 30.4` happens to be exact but `1.0 / (2.0 * 64.0) == 0.0078125` is also exact only for these specific values; `pytest.approx(..., abs=1e-12)` is the canonical safer choice.

### Decision 3: 50% / 30.4 boundary cases pinned with companion pairs

For each strict-greater-than boundary (wayfinder L249: "more than 50% of `β_i > 28.8`"; "warning at `β_i > 30.4`"), the new tests come in **pairs**: one test asserts the at-boundary case returns the strict-less-than result (`False`), one test asserts the just-past-boundary case returns True. This pairing makes the strict-vs-non-strict comparator unambiguous to anyone reading the tests.

**Rationale**: a single test for `>50%` (e.g. `β[:9] = 30.0` ⇒ True) does not establish the boundary semantics; a future code change to `>= n/2` would silently pass the existing test and break the strict-boundary guarantee. Pair tests pin both sides.

**Alternatives considered**:
- Parametrize (`@pytest.mark.parametrize("count, expected", [(8, False), (9, True)])`) — rejected because the test docstrings serve as the canonical narrative for each boundary case; parametrization hides the WHY behind a tuple. A future reviewer reading the test file linearly should see the at-boundary comment + the just-past-boundary comment as paired narrative.

### Decision 4: `_dead_expert_threshold` is private but tested directly

The function is named with leading underscore (`_dead_expert_threshold` at `src/decompmoe/safeguards.py:34-36`) which is Python convention for "package-private". Despite this, the new tests import it directly: `safeguards._dead_expert_threshold(16)`.

**Rationale**:
- The function is the **canonical source** of the spec's `1/(2·N_e)` closed-form claim; testing it directly is the cleanest expression of "this constant value at N_e=16 is exactly 1/32".
- Calling through the public API `should_resurrect(f_history, current_step, last_resurrection_step, *, N_e=N_e)` would only assert *implicit* derivation — that path includes FP arithmetic that could silently drift without the threshold test catching it.
- The leading underscore is a soft convention, not enforced by Python; tests within the same package routinely call private helpers.

**Alternatives considered**:
- Test through `should_resurrect` only — rejected because the threshold's correctness is independent of the surrounding code (consec, rate-limit, history length checks); testing the closed form requires the threshold value to be directly observable.
- Make `_dead_expert_threshold` public (rename to `dead_expert_threshold`) — out of scope; this is a pure test enhancement, not a refactor.

## Risks / Trade-offs

- [Risk] **The 2 new Scenarios make the spec body longer and harder to scan** → Mitigation: the new Scenarios are syntactically grouped (NaN default at L209, per-step semantic at L228 — between existing Scenarios) and the **Open follow-up** note in the latter is bolded to call attention.
- [Risk] **Test file grows by ~250 lines** → Mitigation: each new test has a docstring explaining WHY (the closed-form claim or boundary semantics it pins), so the file remains navigable. No existing test was modified except `test_named_constants_have_spec_values` (extended with 4 additional asserts that follow the existing pattern).
- [Risk] **The new test `test_should_resurrect_current_per_step_semantic_pinned` uses a non-constant history that tests behavior, not just constants** → Mitigation: the test docstring explicitly documents the semantic ambiguity and references the pending ticket; the test is intended as a *guard against accidental semantic drift*, not as a frozen contract. The test is required to be updated alongside any future avg-window semantics adoption.
- [Risk] **`_dead_expert_threshold` is tested via direct import (private-by-convention)** → Mitigation: documented in Decision 4. Future refactors that move the threshold derivation into a different module would break this test loudly, which is the desired behavior — the closed-form derivation must remain directly observable.
- [Risk] **The 4 new boundary tests + 2 new Scenarios + extended `test_named_constants_have_spec_values` slightly increase the test surface area that downstream reviewers must understand** → Mitigation: the test names are descriptive (`test_<op>_<property>` per CLAUDE.md convention); the docstrings cite the spec scenario they implement; the boundary pairing convention (Decision 3) makes the strict-vs-non-strict semantics self-documenting.

## Migration Plan

This change is **pure addition** (zero existing code or spec body changes); the migration plan is:

1. Apply phase: `git add` the 2 modified files (`openspec/specs/decompmoe-skeleton/spec.md` + `tests/test_safeguards.py`); commit on `dev` per offshore-git-workflow.
2. Run `uv run pytest tests/ -q` to confirm `164 passed` (the count after this change; was `154 passed` pre-change). Verify `openspec validate --specs --strict` returns `2 passed, 0 failed`.
3. Run `python scripts/lint_no_dead_defensive.py` to confirm `exit 0` (CLAUDE.md §3 archive-precondition).
4. Run `/opsx:archive` per `CLAUDE.md §3` "Spec-level 变更" workflow; the archive moves this change dir to `openspec/changes/archive/2026-09-11-enhance-safeguards-closed-form-tests/`.
5. Optional: merge to `main` (`--no-ff`) for key-change archival, then merge to `release` (`--no-ff`) + tag for the next release per `CLAUDE.md` §4. Out of scope for this change.

**Rollback** (if a future regression is detected): `git revert <archive-merge-commit>`; the 2 new Scenarios and 10 new tests are additive, so rollback is surgical and zero-risk.

## Open Questions

- None. The avg-vs-per-step semantic decision is explicitly out of scope (per `proposal.md` Goals/Non-Goals and Decision 1) and is documented as a follow-up ticket marker inside the new `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)`.
- The new test `test_should_resurrect_current_per_step_semantic_pinned` is a guard against accidental semantic drift, not a frozen contract — its docstring explicitly notes that it MUST be updated alongside any future avg-window semantics adoption.