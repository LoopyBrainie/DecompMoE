# `governance/spec.md` delta — change `2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix`

> **delta type**: MODIFIED
> **affected requirement**: `<a id="req-gov-1"></a>` "Test Guard Precision for Closed-Form Numerical Claims"
> **affected lines** (approximate, pre-apply): L17-L19 段 (现有第 3 款 + 第 4 款)

## MODIFIED Requirement: Test Guard Precision for Closed-Form Numerical Claims

### Section §4 — frame disclosure (NEW, inserted before existing §4)

> **Original wording** (lines prior to insertion, for reference):
> ```
> 3. **Bisection-derived Voronoi angles** (specialized float case) — claims whose test values come from `canonical_voronoi_angle(N_e, d_c)` (which solves `½ · I_{sin²θ}((d_c − 1)/2, 1/2) = 1/N_e` via bisection) MUST use `pytest.approx(value, abs=1e-6)` — NOT `abs=1e-4` or wider — because the bisection implementation achieves residual `|½ · I_{sin²θ}(7.5, 0.5) − 1/N_e| < 1e-9` (proven by `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`); ...
> [ends at line L17 end of existing §3]
>
> 4. Every assertion described in obligations 1, 2, and 3 MUST embed `f"actual={...}"` in its failure message ...
> [existing §4, will shift to §5]
> ```

### Replacement

After this delta is applied, the ordering becomes:

- `1. **Closed-form integer claims** ...` (unchanged)
- `2. **Closed-form float claims** ...` (unchanged)
- `3. **Bisection-derived Voronoi angles** (specialized float case) ...` (unchanged — still binds impl-internal `< 1e-9` claim to `test_voronoi_residual_below_1e_minus_9` PASS witness)
- **NEW §4 — `**Residual frame disambiguation**`** (inserted):
  > Claims of "< 1e-9" or similar precision bounds on bisection Voronoi output MUST specify the reference regularized incomplete beta implementation:
  > - **impl-internal reference**: `_betainc_regularized` (Gauss-Legendre 8-point, 60 subintervals) at the canonical value `1.1735482746999482 rad` yields `|½·I_{sin²θ}(7.5, ½) − 1/16| = 1.16e-14` (impl-internal `< 1e-9` ✓).
  > - **true closed-form reference** (mpmath `betainc(regularized=True)`) at the same θ yields `4.15e-7` (NOT `< 1e-9`; impl-systematic-error bound).
  > Spec MUST clarify which frame is used for "< 1e-9" claims. Either frame is acceptable as long as the frame is explicit — avoid silent reference-frame shifting.
- `5. Every assertion described in obligations 1, 2, and 3, AND the frame-disambiguation obligation 4 MUST embed `f"actual={...}"` ...` ← OLD §4 renumbered, with conjunction `4` added; other wording unchanged

### Source field

UNCHANGED. The existing `**Source:**` field of req-gov-1 (L23) already carries `CLAUDE.md` reference (governance-lineage reverse-link); no new reverse-link needed for this delta.

### Anchor

UNCHANGED. New §4 is appended within existing req-gov-1 Requirement body; no new `<a id="req-gov-N">` anchor is introduced.

### Test anchors

UNCHANGED. The new §4 is a wording constraint that any future Spec-derived test claiming "< 1e-9" must conform to; it does NOT introduce a new test fixture. The existing `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` remains the bound witness.
