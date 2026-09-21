# Proposal: Fix Ticket Stale Numerical — Fact-Base Re-proposal

## Why

The original change `01-fix-ticket-stale-numerical-4file-batch` was applied and archived on 2026-09-20 (commits `adf41ef` → `2d7e85a` → `229016f` → `11bebc6`). The audit-verification snapshot at `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/` is a propose-phase artifact with three known drifts versus the actual final state:

1. **Line citation drift**: snapshot cites `.audit/audit-verification/audit-verification.md` L132 as the locus of the verbatim string `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°` (proposal.md L3 / design.md L54+L56 / tasks.md B1.2-B1.3). The actual location is L36; the archive version already corrected this. The snapshot retains the wrong citation.
2. **Verifier amendment gap**: snapshot spec.md delta has 3 Scenarios; the final live spec has 4 (cycle-09 verifier F1 CRITICAL added "MVPConfig.beta_initial default derives from spec closed-form ... NOT self-referential literal" + "σ'(−3.5) is guarded by a 50-digit mpmath pytest assertion (durable across archive of `.audit/`)").
3. **Batch size drift**: snapshot is internally inconsistent (directory name "4-file" vs body "5-file"); the actual commit is "6-file batch" (3 ticket + src/config.py + tests/test_beta.py + spec/wayfinder/spec.md).

This change is a fact-base re-proposal that re-establishes the original fix as a canonical OpenSpec change using the verified ground truth. Apply phase is **no-op** because the repo state already contains the fix — this change exists to retire the snapshot artifact and replace it with a fact-accurate OpenSpec record.

## What Changes

### Spec delta — `wayfinder` capability (1 Requirement modified)

- **MODIFIED** Requirement "Isotropic Squared-Chord Distance And Bounded Beta" (req-7, spec.md L113-153):
  - L122 narrative σ'(−3.5) precision `≈ 0.0284` → `≈ 0.02845` (5 sig-fig, matches β_0 ≈ 1.035 style)
  - L126 Source field `A4-1` → `A4-1, A4-2, A6b-1` (主反链 A4-1 首位保持; A4-2 覆盖 w_i 剔除 L124; A6b-1 覆盖 AdamW momentum reset L120)
  - L136 Scenario: σ'(−3.5) narrative precision matches 50-digit mpmath within 5 sig-fig (NEW)
  - L140 Scenario: MVPConfig.beta_initial default derives from spec closed-form β_min + (β_max−β_min)·σ(γ_init), NOT self-referential literal (NEW — cycle-09 verifier F1 CRITICAL)
  - L145 Scenario: σ'(−3.5) is guarded by a 50-digit mpmath pytest assertion (durable across archive of `.audit/`) (NEW — cycle-09 verifier F1 CRITICAL)
  - L151 Scenario: Source field lists all three referenced tickets (NEW)

### src delta (1 file, 4 lines)

- `src/decompmoe/config.py` L50-55:
  - L50-53 docstring: remove `tracked as `★ TODO` in the plan §ST-02`; rewrite as `per spec req-7 L122 closed-form β_0 = 1.035060 (verified at 50-digit mpmath: σ(γ_init=−3.5) = 0.029312230751356318865, β_0 = 1.0350601609682665718)`
  - L55: `beta_initial: float = 1.0` → `beta_initial: float = 1.035`

### tests delta (1 file, 1 test rewritten + 1 test added)

- `tests/test_beta.py`:
  - L37-52 `test_beta_param_init_default`: rewrite to derive expected from spec closed-form `expected = 0.1 + 31.9 * float(torch.sigmoid(g))` and assert `actual == pytest.approx(expected, abs=1e-3)` — guards against self-referential literal trap (cycle-09 verifier F1 CRITICAL)
  - L55-... `test_sigma_prime_gamma_init_health_check` (NEW): dual assertion `pytest.approx(0.02845302387973555984, abs=1e-15)` for 50-digit mpmath literal + `pytest.approx(0.02845, abs=1e-5)` for narrative 5-sig-fig; archive-durable guard

### Ticket supersede annotations (3 files, 3 lines)

- `wayfinder/tickets/A5-3.md` L63: append `> (historical, ~52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)` after the `θ_Voronoi ~52°` row
- `wayfinder/tickets/A4-1.md` L59: append `> (historical, β_0 ≈ 1.0 estimate; superseded by spec req-7 L122 closed-form β_0 = 1.035060 via change fix-math-consistency-audit-2026-08 Decision 1)` after `β_0 ≈ 1.0` row
- `wayfinder/tickets/A1-1.md` L98: append `> (historical, θ_Voronoi≈52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)` after `θ_Voronoi≈52°` row (cycle-5 #1 同源 ticket 端源头 per audit-verification.md L36)

**BREAKING**: none. All changes are tightening of existing precision or annotation; no behavioral semantics change.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `wayfinder`: req-7 (Isotropic Squared-Chord Distance And Bounded Beta) modified with L122 precision refinement + L126 Source-field expansion + 4 new Scenarios (closed-form derivation guard, 50-digit mpmath archive-durable guard, narrative precision match, Source-field enumeration)

## Impact

- **Affected code**: `src/decompmoe/config.py` (1 file, 5 lines, default value + docstring)
- **Affected tests**: `tests/test_beta.py` (1 file, 1 test rewritten + 1 test added)
- **Affected specs**: `openspec/specs/wayfinder/spec.md` (req-7 改 2 处 narrative + Source + 4 Scenarios)
- **Affected tickets**: `wayfinder/tickets/A5-3.md`, `A4-1.md`, `A1-1.md` (3 files, +3 lines each, supersede annotations)
- **Affected APIs/dependencies**: none. `MVPConfig.beta_initial` default value change is numerical-only, dead-field (src/ 0 readers per cycle-6 verify-6), no runtime impact
- **Affected systems**: none (inference engine out-of-scope per CLAUDE.md §7)
- **Apply phase**: no-op. Repo state already matches the proposed final state per git `adf41ef` + `2d7e85a` + `229016f`. Apply exists to re-sync OpenSpec artifacts with repo state and retire the audit-verification snapshot drift.
- **Source of truth anchor**: `verify_numerical_claims.py` (15/15 PASS) + `.audit/audit-verification/audit-verification.md` L36 (cycle-5 finding 一句话复核 blockquote) + L131-136 / L208-211 / L892-895 in `.audit/spec-math-audit/spec-math-audit.md`