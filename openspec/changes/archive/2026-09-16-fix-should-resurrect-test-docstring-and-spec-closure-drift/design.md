## Context

See `proposal.md` ## Why for motivation and trace. The scope-bounded audit (2026-09-16) of the `add-should-resurrect-per-step-math-derivation` lineage surfaced six drift issues (A1-A5 + B1) inside the change's own scope:

- **A1-A4**: `tests/test_safeguards.py` docstring / error-message cross-references use legacy `wayfinder L249` line-number reference and stale `should_resurrect` source line numbers (`L97-L101` — actual is `src/decompmoe/safeguards.py:71-80`).
- **A5**: `test_should_resurrect_per_step_is_strict_subset_of_avg_window_for_monotonic_history` Sub-assertion-5 docstring asserts `H = [0.03125]*200` while the code builds `H_boundary` with `range(250)` — a self-inconsistency introduced by the `e9fc2b9` follow-up commit that wrote the test bodies but introduced a docstring/code length mismatch.
- **B1**: spec scenario body L266-286 gives closed-form arithmetic for Counterexample A (`0.009925`) and B (`0.049775`), but the universal-direction positive example arithmetic `0.001145` (Sub-assertion 4) lives only in the test, not in the spec — yielding a one-directional spec ↔ test closure gap.

Constraints (inherited from CLAUDE.md §6, §8, §10):

- Spec-level change requires the OpenSpec workflow; this change is a SPEC-MODIFIED delta (one Scenario extended by one worked-example bullet) plus a TEST-EDIT (5 docstring/error-message fixes + 1 code-line length fix).
- Per CLAUDE.md §6 第 8 条, every spec formula with concrete numeric values must be `pytest.approx` / exact `==` verifiable; the spec ↔ test closure gap (B1) is the negative side of this contract — closing it brings the spec into one-direction-at-minimum compliance, ideally both-direction.
- No production code (`src/`) may be touched: this is a pure documentation/coherence change.
- No new `**Source:**` clause at the Scenario level (per `2026-09-12-add-should-resurrect-per-step-math-derivation design.md` Decision 1 governance precedent). The parent Requirement L228's `**Source:**` field already names `src/decompmoe/safeguards.py:71-80` (correctly aligned with the post-`d3689a1` signature position).
- No `add-should-resurrect-per-step-math-derivation` archived change artifact modification (those are immutable per CLAUDE.md §3 — archive history is reference-only).

## Goals / Non-Goals

**Goals:**

- Align all six cross-references inside the change's scope with the current code/spec state (`src/decompmoe/safeguards.py:71-80` for `def should_resurrect`; spec scenario L266-286 of `openspec/specs/decompmoe-skeleton/spec.md`; wayfinder spec anchor `req-13` for "Numerical Safeguards").
- Close the spec ↔ test closure gap by adding the universal-direction positive worked example (closed-form `0.001145`) to the spec scenario body as a new bullet between the existing "Both readings agree on constant history" paragraph and the "Notational pin on `f_i^avg`" paragraph.
- Eliminate the `range(250)` self-inconsistency in the Sub-assertion-5 boundary case by aligning code with the docstring (`range(200)`, matching `DEAD_EXPERT_CONSEC_STEPS = 200`); preserve the test outcome (the boundary assertion `res_boundary == set()` is invariant under window length because every snapshot has every `f_i == threshold`).
- Zero `assert` statement changes; both tests must continue to PASS (`2 passed, 28 deselected`).
- Zero `src/decompmoe/*.py` changes.

**Non-Goals:**

- No edits to `openspec/specs/wayfinder/spec.md` — the spec scenario already cross-references `wayfinder Req 13` consistently (verified by `grep wayfinder` against `openspec/specs/decompmoe-skeleton/spec.md`); the wayfinder spec itself is unchanged by this work.
- No edits to the math derivation block semantics (algebra proof, Counterexample A, Counterexample B, constant-history agreement, notational pin): all preserved verbatim from the post-`e9fc2b9` state. Only **one new bullet** is added (universal-direction positive worked example).
- No new Requirement, no new Scenario, no Scenario deletion, no Requirement rename.
- No new test; no test deletion; no new sub-assertion inside any test. The existing 5 sub-assertions remain at their current positions.
- No re-opening of the `Open follow-up` clause (L286 of the modified scenario) about future avg-window semantics; this hook is preserved verbatim.
- No edits to `wayfinder/tickets/*.md` (per CLAUDE.md §8, tickets are reference-only after the 2026-08-21 裁决).
- No edits to any archived `openspec/changes/archive/2026-09-1X-*` directory (immutable per archive contract).

## Decisions

### Decision 1: Use spec ↔ test scope atom split instead of separate changes

**Chosen**: Bundle all six fixes (A1-A5 + B1) into a single OpenSpec change titled `fix-should-resurrect-test-docstring-and-spec-closure-drift`. The change is a single SPEC-MODIFIED delta (one Scenario extended by one bullet) plus a TEST-EDIT (5 string fixes + 1 code line). No production code touched.

**Rationale**: All six fixes share the same scope (spec scenario L266-286 + the two `tests/test_safeguards.py` functions `test_should_resurrect_current_per_step_semantic_pinned` and `test_should_resurrect_per_step_is_strict_subset_of_avg_window_for_monotonic_history`), all six fixes originate from the same scope-bounded audit, all six fixes share the same risk profile (zero behavior change), and they co-evolve: A1-A4 cross-references need the spec's wayfinder `req-13` anchor to land correctly, which is the same anchor introduced by the spec change B1 is preparing. Splitting into two changes (one for A1-A5 docstring fixes, another for B1 spec addition) would create a brief inconsistency window where the docstring cross-references point to a `req-13` that the spec still hasn't fully closed-form-equiped.

**Alternatives considered**:

- *A (rejected)*: Two separate changes (`fix-should-resurrect-docstring-drift` + `add-should-resurrect-sub-assertion-4-closure`). Rejected because the two changes share the same scenario body, the same line-range (L266-286), and an immediate cross-reference dependency; splitting increases review cost without gain. Per CLAUDE.md §1 ("would a senior engineer say this is overcomplicated?"): two separate OpenSpec scaffolding operations for 6 in-scope fixes on the same scenario is overengineering.
- *B (rejected)*: Single change but split into SPEC + TEST artifacts tagged "test-only delta". Rejected because OpenSpec spec-driven schema requires either a `## MODIFIED Requirements` block (when spec behavior changes — note: adding a worked-example bullet is a spec body change, not a pure doc fix) OR `skip_specs: true` (which would forbid the B1 spec addition entirely). The artifact structure (single MODIFIED Requirements section + task list covering all six fixes) is the natural fit.

### Decision 2: Spec addition is one bullet, not a new Scenario

**Chosen**: Insert the universal-direction positive worked example as a single new bullet inside the existing `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)`, placed between the existing "Both readings agree on constant history" paragraph (L282) and the "Notational pin on `f_i^avg`" paragraph (L284). The bullet carries the closed-form arithmetic `(199·0.001 + 1·0.030) / 200 = 0.001145` together with its per-step and avg-window verdicts and the algebraic-role statement that it is the **positive complement** to Counterexample A.

**Rationale**: The math derivation block currently enumerates 3 worked examples (Counterexample A divergence, Reverse direction / Counterexample B divergence, constant-history agreement). Adding a 4th example is the natural extension; the spec's paragraph ordering already moves from "divergence on non-constant" to "agreement on constant" so a 4th example in the "universal-direction positive on non-constant" position slots in cleanly. Creating a new Scenario would split this single semantic statement across two spec artifacts (math derivation block + new scenario), which is exactly the drift pattern that `scripts/lint_no_source_field_drift.py` was written to prevent.

**Alternatives considered**:

- *A (rejected)*: New `#### Scenario: Universal-direction positive example` between the existing math derivation and the notational pin. Rejected because (a) the spec body would now contain TWO scenarios describing the same `should_resurrect` semantics — one with math derivation, one with a single worked example — which complicates grep-based discovery (`grep "should_resurrect"` would yield two irrelevant hits for tools that scan for cross-references), (b) the spec convention elsewhere (cf. L274 "Worked counterexample (per-step vs avg-window divergence on non-constant history)") treats worked examples as paragraphs INSIDE the parent's THEN clause, not as siblings.
- *B (rejected)*: Skip the spec addition entirely. Rejected because CLAUDE.md §6 第 8 条 sets up the spec ↔ test closure contract; the only-direction gap is exactly what the audit surfaced (B1 was a scope finding, not a verbose option). Leaving it unclosed would mean the spec ↔ test triple consistency remains one-directional, which violates the spirit of the project's "spec is truth source" hierarchy (§2 / §3).
- *C (rejected)*: Add a NEW Requirement for the universal-direction positive example. Rejected because the change is a substantive-but-incremental extension of an existing requirement, not a new capability or behavioral surface. Creating a new Requirement for a single bullet would inflate the spec surface for one arithmetic claim, violating CLAUDE.md §1 simplicity-first.

### Decision 3: Boundary Sub-assertion-5 length fix goes from `range(250)` to `range(200)`, not vice versa

**Chosen**: Change `H_boundary = [[threshold] * N_e for _ in range(250)]` to `range(200)` to align with docstring L767 (`H = [0.03125]*200`) and with the canonical `consec = DEAD_EXPERT_CONSEC_STEPS = 200`.

**Rationale**: The boundary assertion is invariant under window length because **every** snapshot has **every** `f_i` exactly equal to threshold `1/32 ≈ 0.03125`: per-step's strict-`<` check rejects equality element-wise for all `200·16 = 3,200` checks; avg-window's mean of `200·0.03125 = 0.03125` is exactly the threshold (boundary equality, also rejected by strict-`<`). Lengthening to 250 produces the same assertion outcome. The natural canonical length is `consec = 200` (the application default), and the docstring already says 200. Fixing the code to match the docstring preserves reader intent without affecting test behavior.

**Alternatives considered**:

- *A (rejected)*: Change docstring to `H = [0.03125]*250` to match code. Rejected because (a) `250` is a non-canonical length with no mathematical significance (not `consec`, not `2·consec`, not 1000, etc.), (b) the docstring was authored first and presumably intended `200` as the canonical window, (c) `e9fc2b9` is the commit that produced the inconsistency, and its core semantic intent was "every snapshot at threshold" — that intent is satisfied by either length; aligning with `consec = 200` makes the test's chosen window semantically meaningful (the same window the implementation looks at).
- *B (rejected)*: Leave the inconsistency as-is with a code comment explaining the discrepancy. Rejected because CLAUDE.md §1 prefers minimal code; a comment that rationalizes inconsistency adds maintenance burden without changing any behavior. If a future reader asks "why 250?", the answer ("no particular reason, just the value that wasn't 200 in the docstring") is itself a maintenance liability.

### Decision 4: All five test docstring fixes use the same single commit / single change

**Chosen**: Apply all five string edits inside `tests/test_safeguards.py` (`A1` L679-680, `A2` L682, `A3` L707 failure-message, `A4` L726 docstring, plus `A5` L907 code line) as a single task list under tasks.md §1, with one verification sub-task (§1.6) running `uv run pytest tests/test_safeguards.py -k "per_step" -v` and confirming `2 passed`.

**Rationale**: Grouping by file-edit locality (same file, related drift family) into a single task group makes the change auditable as a coherent scope unit. Each `assert` statement and each behavior is unaffected, so a single pytest invocation suffices as the verification gate.

**Alternatives considered**:

- *A (rejected)*: One task per fix (six tasks for six fixes). Rejected because the git diff will surface the six edits adjacent in the same file; readers benefit from the surrounding context (the test function name + docstring) rather than from per-line atomization. Per CLAUDE.md §1: six separate OpenSpec tasks for six trivial string edits in one file is overengineering.
- *B (rejected)*: Use a separate "Refactor: docstring sweep" change for A1-A4 plus another for A5+B1. Rejected because all six fixes share the audit lineage and the spec-test cross-reference dependency.

## Risks / Trade-offs

- **[R1] Sub-assertion-5 length change from 250 to 200 might mask an unknown edge-case where length=250 was load-bearing** → Mitigation: explicit re-verification per R1 itself: run `uv run pytest tests/test_safeguards.py::test_should_resurrect_per_step_is_strict_subset_of_avg_window_for_monotonic_history -v` against the post-edit code; the boundary assertion is invariant under window length (every snapshot at threshold, strict-`<` rejects equality regardless of count), so PASS is the math-proven outcome. If this regression fires, increase to a more conservative change (e.g. add an explicit assertion note) rather than reverting to 250.
- **[R2] Spec addition might introduce a new bullet that conflicts with the notational-pin paragraph's "no temporal averaging" claim** → Mitigation: the new bullet uses the same `H[j][i]` notation as the counterexamples (each snapshot is a per-step per-expert fraction, no temporal averaging), and its TRIGGER verdict matches both per-step and avg-window — so it does NOT introduce a windowed-mean interpretation; it only asserts that the algebra proof's universal direction holds on this non-constant history, which is mathematically consistent with the rest of the block.
- **[R3] Modifying archived changes' creation-trail via this change leaves the lineage non-monotonic** → Mitigation: this change explicitly does NOT touch any archived `openspec/changes/archive/2026-09-1X-*` directory; the audit-trail progression is `add-should-resurrect-per-step-math-derivation` → `fix-spec-resurrection-math-direction-2026-09-12` → `fix(test): 修正 Counterexample B 注释的 ⊊ 误用` (commit `0dc7ded`) → THIS CHANGE (`fix-should-resurrect-test-docstring-and-spec-closure-drift`). The new change name drops the dated prefix per CLAUDE.md §2 naming convention (subsequent fixes may either reuse or drop dated prefixes depending on scope — this change's scope is "drift cleanup", which doesn't need a date-stamped historical reference).
- **[R4] `wayfinder Req 13 (anchor #req-13)` cross-reference might not be a recognized Markdown anchor** → Mitigation: verified by `grep -n 'id="req-13"' openspec/specs/wayfinder/spec.md` — the anchor `<a id="req-13"></a>` exists at L241. The Markdown anchor is recognized by standard Markdown renderers (GitHub, GitLab, etc.) and by `openspec validate`. The parenthesized `(anchor #req-13)` form is the project's preferred citation form (per `wayfinder/spec.md` req-33 "Source Field Format Invariant" precedent — anchor #req-N in parentheses for inline cross-references).
- **[R5] Editing the docstring failure-message in L707 changes the user-visible failure string of the existing test** → Mitigation: this is intentional. The current message says "spec L206, wayfinder L249" — both stale; updating to "spec L266-286, wayfinder Req 13 (anchor #req-13)" matches the cross-references everywhere else in the codebase. The failure message content (test semantic) is unchanged; only the cross-reference location data is updated. A pre-existing tooling test that greps for the failure message would need to be updated, but the existing `tests/` has no such grep dependency (verified by `grep -r "update spec L206" tests/` returns zero matches).
- **[R6] Spec ↔ test triple consistency restoration may not be airtight** → Mitigation: this change closes only the A1-A5 + B1 scope. Remaining improvements (e.g., formal parameterized property testing, additional boundary cases like `len(H) < consec`) are explicitly out of scope per Decision 1 / Decision 4 Non-Goals and are listed in the migration plan's "future tickets" callout.

## Migration Plan

1. **OpenSpec workflow phase 1 (planning, this artifact)**: produce `proposal.md` + `specs/decompmoe-skeleton/spec.md` delta + `design.md` + `tasks.md`. `openspec status` should mark all four as `done`. Archive-precondition lints are not yet triggered at this phase.
2. **OpenSpec workflow phase 2 (apply, future task per `/opsx:apply`)**:
   - **Apply SPEC-EDIT**: append the new universal-direction positive worked example bullet to `openspec/specs/decompmoe-skeleton/spec.md` Scenario `should_resurrect semantic interpretation (per-step vs avg-window)` body, between the existing "Both readings agree on constant history" paragraph and the "Notational pin on `f_i^avg`" paragraph. The bullet is **already present** in this change's delta spec (the file under `specs/decompmoe-skeleton/spec.md` already has it inside this change directory); the apply step merges it into the main spec.
   - **Apply TEST-EDIT-1-A1**: `tests/test_safeguards.py:679-680` docstring — replace `Per wayfinder L249: ...` with `Per wayfinder Req 13 (anchor #req-13): ...`.
   - **Apply TEST-EDIT-1-A2**: `tests/test_safeguards.py:682` docstring — replace `(L97-L101)` with `(L71-80)`.
   - **Apply TEST-EDIT-1-A3**: `tests/test_safeguards.py:707` f-string failure message — replace `spec L206, wayfinder L249, and this test consistently` with `spec L266-286, wayfinder Req 13 (anchor #req-13), and this test consistently`.
   - **Apply TEST-EDIT-1-A4**: `tests/test_safeguards.py:726` docstring — replace `src/decompmoe/safeguards.py:97-101` with `src/decompmoe/safeguards.py:71-80`.
   - **Apply TEST-EDIT-1-A5**: `tests/test_safeguards.py:907` code — replace `range(250)` with `range(200)`.
3. **Apply-phase lint gates (per CLAUDE.md §3 archive precondition)**:
   - `python scripts/lint_no_dead_defensive.py` exit=0 (no defensive-code changes introduced).
   - `python scripts/lint_no_source_field_drift.py` exit=0 (no new Source fields introduced; the parent Requirement L228 already carries the correctly-aligned `src/decompmoe/safeguards.py:71-80`).
4. **Apply-phase test gates (per CLAUDE.md §3 pre-archive regression gate)**:
   - `uv run pytest tests/test_safeguards.py -k "per_step" -v` → expected `2 passed, 28 deselected`.
   - `uv run pytest tests/test_safeguards.py -v` → full test suite must PASS (no other test affected; only docstrings + one boundary-window length).
5. **OpenSpec workflow phase 3 (archive, future task per `/opsx:archive`)**: run `openspec archive fix-should-resurrect-test-docstring-and-spec-closure-drift` — this merges the delta spec into `openspec/specs/decompmoe-skeleton/spec.md`, moves the change directory to `openspec/changes/archive/fix-should-resurrect-test-docstring-and-spec-closure-drift/`, and bumps the change's merge commit on `dev` per the project's Git workflow (dev linear + main archive + release tag-out, per CLAUDE.md §4).
6. **Post-archive verification (per CLAUDE.md §3 "Post-archive 独立复核" 强制项)**:
   - Re-run `grep -n "wayfinder L249" openspec/specs/decompmoe-skeleton/spec.md tests/test_safeguards.py` — must return zero matches (closing A1).
   - Re-run `grep -n "97-101\|safeguards.py:97" tests/test_safeguards.py` — must return zero matches (closing A2 + A4).
   - Re-run `grep -n "spec L206" tests/test_safeguards.py` — must return zero matches (closing A3).
   - Re-run `grep -n "L249" tests/test_safeguards.py` — must return zero matches (closing A1 again from a different angle).
   - Re-run `grep -n "0.001145" openspec/specs/decompmoe-skeleton/spec.md` — must return ≥1 match in the math derivation block (closing B1 spec ↔ test closure).
   - Re-run `uv run pytest tests/test_safeguards.py -k "per_step" -v` — must remain `2 passed, 28 deselected`.

**Rollback strategy**: `git revert` the archive merge commit. All edits are textual / length-invariant; rollback is zero-risk.

## Open Questions

(none) — all six fixes are scope-bounded textual edits with verified target line numbers; no design ambiguity remains. The new spec bullet's wording was derived from the post-`e9fc2b9` state of the math derivation block (positive counterpart to Counterexample A); no alternative wording was considered because the spec already establishes a uniform paragraph structure for the four worked-example paragraphs.
