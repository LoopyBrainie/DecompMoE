# Proposal

## Why

`openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` L5 ships `<a id="req-34">` as the anchor for the "CG n=1 boundary behavior" Requirement, but `openspec/specs/wayfinder/spec.md` (live spec) has carried the same Requirement under `<a id="req-35">` since commit `f16cb12` (2026-09-16, applied by `change 2026-09-16-fix-cg-n-1-test-anchor-collision-and-math-coverage`). The reorder commit relocated `req-34` to the "Source Field Format Invariant for OpenSpec Specs" Requirement at live L740 and relabeled "CG n=1 boundary behavior"'s anchor to `req-35`. Consequence: the archive spec delta is **permanently drifted** from the live spec anchor numbering — anyone grep `<a id="req-34">` in `openspec/specs/wayfinder/spec.md` lands on Source Field Format Invariant, while `<a id="req-34">` in the archive file still points at CG n=1. The drift bleeds into 8 prose references in `tasks.md` / `design.md` / `proposal.md` (only `proposal.md` L19 was partially patched by commit `889d81c` "post-archive drift closure" H7). This change closes the drift with a surgical 4-file fix; no Requirement semantics change, no live spec change, no code change, no test change. Archive files are immutable audit-trail records, but editing their **anchor text** to match live spec (with a `(historical, ...; superseded by ...)` annotation block recording the original state) is the documented convention from `openspec/changes/archive/2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian/` which closed an analogous drift in `2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md`.

## What Changes

- **Anchor relabel in archive spec delta**: replace `<a id="req-34"></a>` with `<a id="req-35"></a>` at `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` L5. The Requirement body (verbatim copy of live spec L498-518), 4 Scenarios, and lint-compliant `**Source:**` field are preserved unchanged.
- **Historical annotation block**: prepend a `(historical, ...; superseded by ...)` annotation to the same archive spec delta file, before the existing `## ADDED Requirements` header. Mirrors the pattern from `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` precedent (`fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` Decision 2). Records (i) original anchor was `req-34` at L442 of live spec at archive apply-time (commit `b8c149c` 2026-09-16), (ii) commit `f16cb12` reordered to `req-35` and moved `req-34` anchor to live L740 (Source Field Format Invariant Requirement), (iii) this archive corrective change (2026-09-24) edits anchor text to match post-reorder live spec for grep consistency.
- **Prose consistency in 8 prose references** across `tasks.md` (L3, L4), `design.md` (L7, L12, L76, L88), `proposal.md` (L7, L24): update all stale `req-34` references (when referring to "CG n=1 boundary behavior" Requirement) to `req-35`, matching the live spec anchor. `proposal.md` L19 was already patched to `req-35` by commit `889d81c` H7 — preserved as-is. Line-number references like "L442" are post-relabel intentionally stale (they refer to the apply-time state, distinct concern from anchor naming).
- **(Post-review MINOR-1) Comment accuracy fix in `tests/test_metrics.py:350-364`**: review by the Python reviewer agent flagged the docstring's false claim "pins the implementation path: any rewrite to sum/max identity would break here". Empirically at numel==1 the bare `==` assertion `actual == torch.linalg.norm(g).item()` evaluates to `5.0 == 5.0` regardless of implementation (L2/abs(sum)/abs(max) all coincidentally return `abs(value)` for single-element tensors). Rewrite the comment (a) to acknowledge this numel==1 coincidence explicitly, (b) to reference `test_cg_l2_norm_closed_form` (req-20 sibling test at L286-310 in `tests/test_metrics.py`) as the actual L2-vs-other-norms discriminator at numel≥2 where `CG([3,4])==5.0` is uniquely L2. Keep the bare `==` assertion itself (L360-364) since it remains FP-exact `actual == torch.linalg.norm(g).item()` documentation and would catch numerical regressions. Scope: 1 file (`tests/test_metrics.py`), comment block only — no test logic change, no assertion count change.
- **(Post-review INFO-1) Test-side precision tightening in `test_cg_n_eq_1_returns_magnitude`**: tighten `pytest.approx(abs=1e-12)` to `pytest.approx(abs=1e-15)` for the 5 boundary assertions at L327, L332, L337, L344, L348. Reviewer's INFO-1 noted `sqrt(x²)` is bitwise-exact in IEEE-754 binary64 for `|value| ≤ 2^26` (verified `math.sqrt(25.0) == 5.0` bit-equal; `math.sqrt(0.0) == 0.0` bit-equal), so `abs=1e-15` is achievable. **Scope-bounded**: only the 5 boundary assertions in `test_cg_n_eq_1_returns_magnitude` (out of 12 total `abs=1e-12` instances in the file) — other tests' tolerance choices are out of scope. **Spec body NOT touched**: archive spec.md retains `abs=1e-12` in its 4 Scenarios to preserve verbatim-equivalence with live `openspec/specs/wayfinder/spec.md` L506, L510, L514, L518 (a separate change to tighten live + archive simultaneously is tracked elsewhere — out of this change's scope). "Test stricter than spec" is a valid testing pattern: test verifies implementation achieves tighter bound than spec requires.

No source-code changes. No ticket changes (per `CLAUDE.md` §8 "wayfinder tickets are advisory non-binding"). No change to live `openspec/specs/wayfinder/spec.md` (already authoritative at `<a id="req-35">` L496, kept verbatim-equivalent with archive spec body so the two stay in lock-step).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — see `skip_specs: true` rationale in `.openspec.yaml`)

### `skip_specs` rationale

This change is **pure spec-hygiene** with **no observable behavior change**:

- The anchor relabel in `archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` L5 (single-line edit + annotation prepend) is **historical record surgery** — archive files are immutable audit-trail records, but the convention is to keep them editable for drift annotations (precedent: `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` was annotated post-archive by `fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian`). The archive is non-canonical; live `openspec/specs/wayfinder/spec.md` has carried `<a id="req-35">` for "CG n=1 boundary behavior" since `f16cb12`.
- The 8 prose updates in archive `tasks.md` / `design.md` / `proposal.md` are **descriptive references**, not Requirements. Updating them improves grep consistency without changing any requirement text, scenario, or assertion anchor.

Per the OpenSpec spec-driven workflow rule "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation.", this change sets `skip_specs: true`. The `apply` phase directly edits the 4 archive text files without producing a `specs/<capability>/spec.md` delta.

## Impact

- **Affected files** (all under `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/`):
  - `specs/wayfinder/spec.md` (1 anchor-line replacement at L5 + ~10-15 line annotation block prepended)
  - `proposal.md` (L7 `req-34` → `req-35`; L24 `req-34` → `req-35`)
  - `design.md` (L7 `req-34` → `req-35`; L12 `req-34` → `req-35`; L76 `req-34` → `req-35`; L88 `req-34` → `req-35`)
  - `tasks.md` (L3 `req-34` → `req-35`; L4 `req-34` → `req-35`)
- **Affected code/APIs/dependencies**: none.
- **Lint**: `python scripts/lint_no_source_field_drift.py` exit=0 (no governance reverse-link violation; archive files are not in the live lint scan set, but we re-run for hygiene confirmation).
- **OpenSpec validate**: `openspec validate --specs` and `openspec validate --change fix-archive-ground-cg-n-eq-1-test-stale-anchor` both pass post-change.
- **Downstream grep**: after this change, `grep -nE '<a id="req-35"' openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` returns 1 hit at L5 (matches live spec anchor for "CG n=1 boundary behavior"); `grep -nE 'req-35' openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/*.md` returns consistent hits across all 4 archive files (was previously intra-doc inconsistent: line 19 said `req-35`, lines 7+24 said `req-34`).
- **Audit trail**: future cycles can `grep -nE '<a id="req-35"' openspec/specs/wayfinder/spec.md openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` and correctly conclude both files describe the same Requirement ("CG n=1 boundary behavior") under the same anchor.
