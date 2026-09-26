# `decompmoe-skeleton/spec.md` delta — change `2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix`

> **delta type**: MODIFIED
> **affected requirement**: `<a id="req-6"></a>` "Voronoi Self-Consistency Threshold"
> **affected lines** (approximate, pre-apply): insertion between L106 (end of `Scenario: N_e dependence of voronoi_angle`) and L108 (start of `Scenario: no hard-coded table values`)

## MODIFIED Requirement: Voronoi Self-Consistency Threshold

### Section — new Scenario appended

After the existing `Scenario: N_e dependence of voronoi_angle` (lines L104-L106) and BEFORE the existing `Scenario: no hard-coded table values` (lines L108-L110), insert a new Scenario:

```
#### Scenario: Bisection output + narrative precision disclosure

- **WHEN** reviewing the MVP self-consistency Scenario above (`≈ 1.1735 rad`) and the N_e-dependence Scenario above (`≈ 1.0205 rad`)
- **THEN** the reader understands:
  - `≈ 1.1735 rad` / `≈ 1.0205 rad` are narrative prose at ~4-decimal precision; NOT exact bisection values
  - The impl bisection OUTPUT is `1.1735482746999482 rad` (N_e=16) / `1.0205068335735599 rad` (N_e=64) at 16-digit precision
  - The impl-internal residual vs `_betainc_regularized` at the impl output is `< 1e-14` (per `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`)
  - The true closed-form residual vs mpmath `betainc(regularized=True)` at the impl output is `4.15e-7` (N_e=16) / `1.43e-9` (N_e=64); the N_e=64 impl output sits just above the `< 1e-9` reference floor at `1.43e-9` (close to the bisection noise floor; NOT below it, despite the small magnitude), while the N_e=16 impl output has larger residual (~`4e-7`) but still well within the `< 1e-6` spec tolerance per `openspec/specs/governance/spec.md` req-gov-1 §3
  - The discrepancy `~8.49e-7 rad` (N_e=16) / `~8.79e-9 rad` (N_e=64) between mpmath true bisection solve and impl output reflects Gauss–Legendre 8-point 60-segment systematic error in `_betainc_regularized`, bounded to < 1 ppm
```

### Source field

UNCHANGED. The req-6 Source field (`(Matches master wayfinder Req 11 verbatim.)` reference inside the body, per L98) is unchanged. The req-6 Source field for `openspec/specs/decompmoe-skeleton/spec.md` is verified separately via `scripts/lint_no_source_field_drift.py` and remains compliant with the `wayfinder/tickets/` primary reverse-link substring.

### Anchor

UNCHANGED. New Scenario is appended within existing req-6 Requirement body; no new `<a id="req-N">` anchor is introduced.

### Test anchors

UNCHANGED. The new Scenario is a wording/disclosure constraint, NOT a behavioral test contract; it does NOT introduce a new test fixture. Existing test `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` continues to enforce the residual bound at impl output.
