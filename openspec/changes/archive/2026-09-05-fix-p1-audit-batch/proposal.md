## Why

Pi adversarial review (round 3) flagged that the original `fix-p1-audit-batch` proposal claimed credit for 4 spec edits (`or True` removal, MAJ-M1/M2 versine precision, MAJ-M3 FLOPs scope note) that had ALREADY been applied in the same session. This violates CLAUDE.md §3 "Surgical Changes". The proposal now lists ONLY actual new work — changes whose diff appears in this commit/change for the first time.

Additionally, Pi review identified two missing pytest guards and one spec typo that the original audit missed entirely.

## What Changes (actual new work only)

| # | finding | change | new work? |
|---|---|---|---|
| 1 | **MAJ-C2** test guard | `tests/test_safeguards.py::test_resurrection_perturb_default_requires_dim` — pytest.raises(TypeError) on `dim=None` | ✅ new test |
| 2 | **MAJ-M1/M2** closed-form test | `tests/test_sphere.py::test_versine_voronoi_closed_form` — `1 − cos(canonical_voronoi_angle(16, 16)) ≈ 0.61312` and `(64, 16) ≈ 0.47707` | ✅ new test |
| 3 | **MAJ-typo** (audit-missed) | `openspec/specs/wayfinder/spec.md:299` "but nots NOT advance the phase" → "but does NOT advance the phase" | ✅ new spec edit |
| 4 | **MAJ-C2 spec/code reconcile** | `openspec/specs/wayfinder/spec.md:582` scenario signature updated: `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` (explicit `dim` required; `dim=None` raises `TypeError`) | ✅ new spec edit |

## Already-Applied Earlier (NOT in this change's diff)

The following 4 spec/code edits were applied earlier in this session; this change does not re-claim them:

- MAJ-T1: `tests/test_extraction.py:321-324` — `or True` already removed (audit finding moot)
- MAJ-M1: `openspec/specs/wayfinder/spec.md:189` — `versine_Voronoi(16, 16) ≈ 0.6131` already in spec
- MAJ-M2: `openspec/specs/wayfinder/spec.md:190` — `versine_Voronoi(64, 16) ≈ 0.4771` already in spec
- MAJ-M3: `openspec/specs/wayfinder/spec.md:317, 362` — `projection-only` scope annotation already added

## Why these are essential

Per CLAUDE.md §6 第 8 条 ("spec 中每个含具体数值的算式都必须有 `pytest.approx(..., abs=...)` 直接对账"), the versine spec values (`0.6131`, `0.4771`) MUST be enforced by closed-form pytest tests; without `test_versine_voronoi_closed_form`, future spec/code drift would slip through (the original audit was triggered by exactly this failure mode). Similarly, MAJ-C2's TypeError contract is meaningless without a test that exercises the `dim=None` path.

The spec typo at `wayfinder/spec.md:299` ("nots NOT") was missed by both audit A and audit B; reader parsing the Scenario would interpret it as ambiguous. Fixing it preserves the OpenSpec-as-truth-source principle.

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder` — Requirement 28 scenario signature (line 582) updated to match new code signature; Scenario typo at line 299 corrected

## Impact

- 受影响文件：`tests/test_safeguards.py` (new test, +12 lines)、`tests/test_sphere.py` (new test, +10 lines)、`openspec/specs/wayfinder/spec.md` (2 spec edits at L299 + L582)
- 反链：Pi review round 3 (2026-09-05)
- 验收基线：`uv run pytest tests/ -v` 全过（140 passed including 3 new tests）
- 无破坏性变更（new tests + 2 spec text edits）