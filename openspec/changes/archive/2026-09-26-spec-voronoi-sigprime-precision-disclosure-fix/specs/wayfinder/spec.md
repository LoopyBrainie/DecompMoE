# `wayfinder/spec.md` delta — change `2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix`

> **delta type**: MODIFIED
> **affected requirements**:
> 1. `<a id="req-7"></a>` "Isotropic Squared-Chord Distance And Bounded Beta" — L144 (Scenario header) + L146 (THEN clause) + L156 (AND clause)
> 2. `<a id="req-11"></a>` "4070 MVP Hyperparameter Set" — L237 后 L239 前 (blockquote footnote)

## MODIFIED Requirement #1: Isotropic Squared-Chord Distance And Bounded Beta

### Edit 1: Scenario header (L144)

> **Original**:
> ```
> #### Scenario: σ'(−3.5) narrative precision matches 50-digit mpmath within 5 significant figures
> ```

> **Replacement**:
> ```
> #### Scenario: σ'(−3.5) narrative precision matches 50-digit mpmath within 4 significant figures (narrative form)
> ```

Only the phrase `within 5 significant figures` → `within 4 significant figures (narrative form)` is changed. The header's other wording is preserved.

### Edit 2: THEN clause (L146) — wording rewrite (A1.5 primary fix)

> **Original**:
> ```
> - **THEN** the narrative value `σ'(−3.5) ≈ 0.02845` matches the 50-digit mpmath value `0.02845302387973555984` truncated at 5 significant figures (diff `|0.028453 − 0.02845| = 3e-6`, relative `0.011%`, well below `1e-6` tolerance); this is the "healthy gradient" health-check anchor for the cold-start region `γ_init ≈ −3.5`
> ```

> **Replacement**:
> ```
> - **THEN** the narrative value `σ'(−3.5) ≈ 0.02845` matches the 50-digit mpmath value `0.02845302387973555984` rounded to 4 significant figures (round-half-up at 5dp or truncate-then-format, both yield `0.02845`); the 5-sig-fig truncation would yield `0.028453`, NOT displayed; the discrepancy is intentional — narrative precision is 4 sig figs to align with `β_0 ≈ 1.035` (4 sig fig) closed-form style elsewhere in this Requirement (per Decision 4 of change `01-fix-ticket-stale-numerical-4file-batch` proposal); this is the "healthy gradient" health-check anchor for the cold-start region `γ_init ≈ −3.5`
> ```

**What changes**:
- `truncated at 5 significant figures` → `rounded to 4 significant figures (round-half-up at 5dp or truncate-then-format, both yield 0.02845)`
- The (now-misleading) parenthetical `(diff |0.028453 − 0.02845| = 3e-6, relative 0.011%, well below 1e-6 tolerance)` is REMOVED
- A new explanation `the 5-sig-fig truncation would yield 0.028453, NOT displayed; the discrepancy is intentional` is ADDED (acknowledges the discrepancy rather than papering over it)
- A new lineage 反链 `per Decision 4 of change 01-fix-ticket-stale-numerical-4file-batch proposal` is ADDED (so future audit can trace why narrative is `0.02845` and not `0.028453`)

**What does NOT change**:
- Narrative literal `σ'(−3.5) ≈ 0.02845` (unchanged) — this is the cycle-23 Decision 4 output (changed from `0.0284` to `0.02845` in change `01-fix-ticket-stale-numerical-4file-batch`); not to be reverted
- 50-digit mpmath verbatim `0.02845302387973555984` (unchanged)
- Final clause `this is the "healthy gradient" health-check anchor ...` (unchanged)

### Edit 3: AND clause (L156) — wording sync (A1.5 secondary fix)

> **Original** (within Scenario at L153-L157):
> ```
> - **AND** a paired assertion `σ'(−3.5) == pytest.approx(0.02845, abs=1e-5)` that nails the L122 narrative 5-sig-fig precision disclosure
> ```

> **Replacement**:
> ```
> - **AND** a paired assertion `σ'(−3.5) == pytest.approx(0.02845, abs=1e-5)` that nails the L122 narrative 4-sig-fig precision disclosure
> ```

Only `5-sig-fig` → `4-sig-fig` is changed.

### Source field

UNCHANGED. req-7 Source is `**Source:** wayfinder/tickets/A4-1.md, wayfinder/tickets/A4-2.md, wayfinder/tickets/A6b-1.md` (per L134) — primary reverse-link is `A4-1.md` (first item), lint `exit=0` unaffected.

### Anchor

UNCHANGED. L144-L156 edits are within existing req-7 body and Scenario; no new `<a id="req-N">` anchor is introduced.

### Test anchors

UNCHANGED. The paired assertion `σ'(−3.5) == pytest.approx(0.02845, abs=1e-5)` at `tests/test_beta.py::test_sigma_prime_gamma_init_health_check` (verified PASS) already nails the L122 narrative 4-sig-fig form. The wording change ONLY changes the precision-claim descriptor (`4-sig-fig` vs the previous inaccurate `5-sig-fig`); the test literal `0.02845` is unchanged.

---

## MODIFIED Requirement #2: 4070 MVP Hyperparameter Set

### Edit: blockquote footnote appended after L237

> **Original** (last lines of L235-L237):
> ```
> MVP tabulated values (independent root-finding, residual `< 1e-9`):
> - `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`, `versine_Voronoi(16, 16) ≈ 0.6131`.
> - `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`, `versine_Voronoi(64, 16) ≈ 0.4771`.
>
> The canonical configuration-layer API `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` MUST return this closed-form value (computed via bisection on the equation, NOT via a hard-coded table).
> ```

> **Replacement** (same as Original but with footnote blockquote inserted between L237 and L239; the `MVP tabulated values` line itself gains an impl-internal vs mpmath frame disclosure so `< 1e-9` is not interpreted as silent reference-frame shifting per `governance/spec.md` req-gov-1 §4):
> ```
> MVP tabulated values (independent root-finding, impl-internal residual `< 1e-9` per `src/decompmoe/sphere.py::_betainc_regularized`; true closed-form residual vs mpmath at the bisection output is `≈ 4.15e-7` for `(N_e=16, d_c=16)` and `≈ 1.43e-9` for `(N_e=64, d_c=16)`, both well within the `< 1e-6` test tolerance prescribed by `governance/spec.md` req-gov-1 §3 — see the frame-disambiguation obligation in req-gov-1 §4):
> - `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`, `versine_Voronoi(16, 16) ≈ 0.6131`.
> - `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`, `versine_Voronoi(64, 16) ≈ 0.4771`.
>
> > **Display precision note**:
> > - `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`: `67.24°` (4-decimal-degree = ~4-sig-fig for angle) and `≈ 1.1735 rad` (4-decimal-rad = ~5-sig-fig for rad) are dual prose forms referring to the same impl bisection output `1.1735482746999482 rad = 67.2393145636...°`. The two displays differ by `67.24° × π/180 − 1.1735 ≈ 5.94e-5 rad` due to independent prose rounding; both lie within the `< 1e-4 rad` test tolerance permitted by `governance/spec.md` req-gov-1 §2 ("float closed-form claims must use `pytest.approx(value, abs=...)` with tolerance matching the closed-form computation's actual precision").
> > - `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`: similar dual-prose pattern; impl output `1.0205068335735599 rad = 58.47073...°`; display diff `58.47° × π/180 − 1.0205 ≈ −5.99e-6 rad` (negative: `58.47° × π/180 = 1.0204940... rad < 1.0205 rad`), magnitude `|diff| ≈ 5.99e-6 rad` well within the `< 1e-4 rad` tolerance.
> >
> > The prose-form-vs-impl-output gap and the within-form dual-display gap together demonstrate that **prose angle precision ≠ impl-bit precision**: prose `≈` 符号 已是 spec 谓词的精度披露,不等于 strict equality。
>
> The canonical configuration-layer API `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` MUST return this closed-form value (computed via bisection on the equation, NOT via a hard-coded table).
> ```

**What changes**:
- A blockquote (using markdown `>` line prefix) is appended after L237 (after the bullet list), BEFORE the existing L239 paragraph "The canonical configuration-layer API ..."
- The blockquote contains three lines: header label + two N_e-specific notes

**What does NOT change**:
- L236-237 bullet list content: `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`, `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`, versine values all unchanged (bytewise)
- L239 onward is unchanged

### Source field

UNCHANGED. req-11 Source is `**Source:** wayfinder/tickets/A5-3.md, wayfinder/tickets/A8-1.md, change fix-openspec-doc-bugs design.md (Decision 4, 8), change fix-math-consistency-audit-2026-08 design.md (Decision 1)` — primary reverse-link `A5-3.md` is first item, lint `exit=0` unaffected.

### Anchor

UNCHANGED. Footnote is appended within req-11 body; no new `<a id="req-N">` anchor is introduced.

### Test anchors

UNCHANGED. The blockquote footnote is a precision-disclosure annotation, not a behavioral test contract; no new test fixture is introduced. Existing tests `tests/test_sphere.py::test_voronoi_canonical_mvp_value` and `tests/test_sphere.py::test_voronoi_canonical_N_e_dependence` (verified PASS) continue to enforce the bisection residual at the impl output.
