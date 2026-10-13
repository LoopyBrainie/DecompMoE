# Evidence · Post-change flip census (HEAD dde0e1d + this change's edits)

**Source:** clean `git archive dde0e1d` export with this change's `src/decompmoe/extraction.py` + `tests/*.py` overlaid (gating.py left at HEAD). torch 2.12.1+cu130 / pytest 9.1.1; 383 passed, 1 skipped (git-dependent suites deselected).
**Purpose:** acceptance evidence for Req A — no comparison's pass condition carries an unselected default relative term.

## Result

- `tests/` declarative comparison sites: **49** = 44 `torch.allclose` + 5 `torch.equal`. (Base was 48 `allclose`; three `atol=1e-12` sites became `torch.equal`, and two previously tolerance-less sites — `test_gating.py:45`, `test_extraction.py:566` — were corrected to `torch.equal` rather than given a looser invented `atol`.)
- **Current flips = 0/48** (base 2/48: `test_extraction.py:461`, `:540`). The two previously-flipped sites are fixed at their root: `:461` by the empty-cell passthrough (`drift -> 0.0`, `torch.equal`), `:540` by the float64 reconstruction (`fallback` row `torch.equal`).
- **Missing explicit `rtol` = 0** (base 48); verified by `scripts/lint_no_implicit_relative_tolerance.py` (OK on this tree, exit 1 on HEAD: 51 violations).
- **No-tolerance comparisons = 0** (base 3).

## atol=1e-12 (machine-precision identity) group

| site | base drift (float32) | post |
|---|---|---|
| `test_extraction.py:461` | 7.450581e-09 | `torch.equal`; empty-cell passthrough makes it bit-exact |
| `test_extraction.py:540` | 1.192093e-07 | `torch.equal` on fallback row (float64); healthy rows `torch.allclose(atol=1e-12, rtol=0.0)` closed form |
| `test_extraction.py:636` | 0.000000e+00 | `torch.equal` |

## Spec-constant pinning (`:540`)

The rebuilt `:540` pins the spec constant `1e-9` from **both** sides, verified by mutation:
- `1e-9 -> 1e-3` (6 orders) -> **test FAILS** (expert 3's candidate norm ~1e-8 would wrongly take the fallback)
- `1e-9 -> 1e-18` -> **test FAILS** (expert 0's candidate ~1.6e-16 would stop falling back)

## Tolerance-tightness corrections

`test_gating.py:45` and `test_extraction.py:566` had `delta = 0.0` at HEAD. Declaring a *new* `atol` of `1e-6`/`1e-7` would have replaced an implicit `1e-8` and loosened the guard 100x/10x; both were corrected to `torch.equal` instead.

## Negative-polarity sites (delta intentionally large; rtol=0.0 narrows the equality band)

These 8 `assert not torch.allclose(...)` sites keep a large delta by design — it is the evidence that the two quantities differ. Declaring `rtol=0.0` removes the unselected band; the assertions remain satisfied (full suite green).

| site | delta | atol |
|---|---|---|
| `test_extraction_phase.py:124` | 1.53e+01 | 1e-06 |
| `test_extraction_phase.py:107` | 2.42e+00 | 1e-06 |
| `test_a3_contract_alignment.py:386` | 9.46e-01 | 1e-03 |
| `test_extraction_phase.py:73` | 6.26e-01 | 1e-06 |
| `test_extraction_phase.py:150` | 1.81e-01 | 1e-06 |
| `test_extraction_phase.py:195` | 3.37e-02 | 1e-06 |
| `test_extraction_phase.py:241` | 2.81e-02 | 1e-06 |
| `test_extraction_phase.py:163` | 6.85e-03 | 1e-05 |