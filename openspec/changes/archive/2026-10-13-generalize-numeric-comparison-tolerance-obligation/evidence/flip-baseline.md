# Evidence · Baseline flip census @ HEAD dde0e1d (pre-change snapshot)

**Source:** HEAD = `dde0e1dfec08c4ebd7051338bd47979d1e0b992b` (261 commits), collected on a **clean `git archive dde0e1d` export** (worktree was dirty; the export is the pristine committed state, `gating.py` = HEAD 63-line version).
**Method:** monkeypatch `torch.allclose` (caller file:line keyed), run full `tests/` (383 passed, 1 skipped; git-dependent `test_pointer_scan`/`test_run_gates` deselected - export has no `.git`). torch 2.12.1+cu130 / pytest 9.1.1.
**Recompute entry point:** the collector is re-runnable; flip is recomputable from the three recorded columns via `flip = (delta_max <= atol + 1e-5*|other|) and (delta_max > atol)`.

## Per-site table (48/48 AST call sites captured)

| site | atol | abs(other)max | 1e-5*abs(other) (default-rtol band) | delta_max | FLIP |
|---|---|---|---|---|---|
| `test_extraction_phase.py:124` | 1e-06 | 15.6112 | 1.561e-04 | 1.528e+01 | |
| `test_extraction_phase.py:107` | 1e-06 | 45.9884 | 4.599e-04 | 2.419e+00 | |
| `test_a3_contract_alignment.py:386` | 1e-03 | 0.5780 | 5.780e-06 | 9.462e-01 | |
| `test_extraction_phase.py:73` | 1e-06 | 0.5769 | 5.769e-06 | 6.259e-01 | |
| `test_extraction_phase.py:150` | 1e-06 | 0.9999 | 9.999e-06 | 1.813e-01 | |
| `test_extraction_phase.py:195` | 1e-06 | 0.7205 | 7.205e-06 | 3.370e-02 | |
| `test_extraction_phase.py:241` | 1e-08 | 0.7209 | 7.209e-06 | 2.809e-02 | |
| `test_extraction_phase.py:163` | 1e-05 | 0.7362 | 7.362e-06 | 6.848e-03 | |
| `test_sphere.py:29` | 1e-05 | 1.0000 | 1.000e-05 | 3.576e-07 | |
| `test_extraction.py:148` | 1e-05 | 1.0000 | 1.000e-05 | 2.384e-07 | |
| `test_extraction.py:739` | 1e-06 | 1.0000 | 1.000e-05 | 1.788e-07 | |
| `test_extraction.py:540` | 1e-12 | 0.8115 | 8.115e-06 | 1.192e-07 | **YES** |
| `test_extraction_phase.py:215` | 1e-06 | 1.0000 | 1.000e-05 | 1.192e-07 | |
| `test_gating.py:113` | 1e-06 | 3.5020 | 3.502e-05 | 1.192e-07 | |
| `test_sphere.py:45` | 1e-06 | 0.7344 | 7.344e-06 | 1.192e-07 | |
| `test_extraction.py:304` | 1e-05 | 1.0000 | 1.000e-05 | 5.960e-08 | |
| `test_extraction.py:537` | 1e-06 | 1.0000 | 1.000e-05 | 5.960e-08 | |
| `test_extraction.py:643` | 1e-07 | 0.5986 | 5.986e-06 | 5.960e-08 | |
| `test_extraction.py:648` | 1e-07 | 1.0000 | 1.000e-05 | 5.960e-08 | |
| `test_extraction.py:681` | 1e-07 | 1.0000 | 1.000e-05 | 5.960e-08 | |
| `test_extraction_phase.py:79` | 1e-06 | 1.0000 | 1.000e-05 | 5.960e-08 | |
| `test_extraction_phase.py:189` | 1e-06 | 0.5986 | 5.986e-06 | 5.960e-08 | |
| `test_extraction_phase.py:214` | 1e-06 | 1.0000 | 1.000e-05 | 5.960e-08 | |
| `test_extraction_phase.py:226` | 1e-05 | 1.0000 | 1.000e-05 | 5.960e-08 | |
| `test_extraction_phase.py:119` | 1e-05 | 0.7225 | 7.225e-06 | 1.490e-08 | |
| `test_extraction_phase.py:244` | 1e-05 | 0.7256 | 7.256e-06 | 1.490e-08 | |
| `test_extraction.py:461` | 1e-12 | 0.8115 | 8.115e-06 | 7.451e-09 | **YES** |
| `test_extraction_phase.py:212` | 1e-05 | 0.7194 | 7.194e-06 | 7.451e-09 | |
| `test_extraction_phase.py:245` | 1e-05 | 0.7209 | 7.209e-06 | 3.725e-09 | |
| `test_experts.py:25` | 1e-05 | 0.7050 | 7.050e-06 | 0.000e+00 | |
| `test_experts.py:77` | 1e-05 | 0.6944 | 6.944e-06 | 0.000e+00 | |
| `test_extraction.py:172` | 1e-04 | 0.5594 | 5.594e-06 | 0.000e+00 | |
| `test_extraction.py:468` | 1e-06 | 1.0000 | 1.000e-05 | 0.000e+00 | |
| `test_extraction.py:566` | 1e-08 | 0.0000 | 0.000e+00 | 0.000e+00 | |
| `test_extraction.py:598` | 1e-07 | 0.0500 | 5.000e-07 | 0.000e+00 | |
| `test_extraction.py:608` | 1e-07 | 0.7205 | 7.205e-06 | 0.000e+00 | |
| `test_extraction.py:613` | 1e-07 | 1.0000 | 1.000e-05 | 0.000e+00 | |
| `test_extraction.py:636` | 1e-12 | 0.7205 | 7.205e-06 | 0.000e+00 | |
| `test_extraction.py:675` | 1e-07 | 0.7205 | 7.205e-06 | 0.000e+00 | |
| `test_extraction_phase.py:70` | 1e-05 | 0.7182 | 7.182e-06 | 0.000e+00 | |
| `test_extraction_phase.py:159` | 1e-05 | 0.7360 | 7.360e-06 | 0.000e+00 | |
| `test_extraction_phase.py:213` | 1e-05 | 0.7203 | 7.203e-06 | 0.000e+00 | |
| `test_gating.py:45` | 1e-08 | 3.4105 | 3.411e-05 | 0.000e+00 | |
| `test_gating.py:54` | 1e-06 | 1.0000 | 1.000e-05 | 0.000e+00 | |
| `test_loss.py:93` | 1e-06 | 0.0025 | 2.500e-08 | 0.000e+00 | |
| `test_loss.py:194` | 1e-06 | 0.0001 | 6.876e-10 | 0.000e+00 | |
| `test_loss.py:198` | 1e-06 | 0.0001 | 6.876e-10 | 0.000e+00 | |
| `test_metrics.py:487` | 1e-06 | 0.8976 | 8.976e-06 | 0.000e+00 | |

## Three metrics (mutually non-substitutable)

- **Currently actually flipped** (default PASS and rtol=0 FAIL): **2/48** - ['test_extraction.py:540', 'test_extraction.py:461']
- **widen** = (1e-5*abs(other))/atol: min 0.000e+00 / p25 7.225e-01 / **median 7.344** / p75 7.205e+01 / max 8.115e+06; `widen<1` (atol dominates) = **16/48**; `>=100x` = 10/48; `>=1000x` = 4/48
- **Structural**: `delta==0` (already bit-exact) = 19/48; `abs(other)==0` (rtol term structurally immune) = ['test_extraction.py:566']; remainder split 25 possibly-flippable / 23 constructively impossible (static classification).
- **atol=1e-12 group** (machine-precision identity claim): ['test_extraction.py:540', 'test_extraction.py:461', 'test_extraction.py:636']

## drift of the atol=1e-12 group (float32)

| site | drift (float32) | flipped |
|---|---|---|
| `test_extraction.py:540` | 1.192093e-07 | YES |
| `test_extraction.py:461` | 7.450581e-09 | YES |
| `test_extraction.py:636` | 0.000000e+00 | no |