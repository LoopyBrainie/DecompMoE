# FIX-006 / FIX-007 baseline evidence

**HEAD at measurement**: `3c64cdc` (`dev`, 264 commits).
**Environment**: `uv run`, torch 2.12.1+cu130; float64 where stated.
**Provenance**: the `metrics.py` line numbers below come from the git blob
`git show 3c64cdc:src/decompmoe/metrics.py`, NOT the working tree (the working
tree already carries the fix and has shifted line numbers).

## 1. `_ZERO` return sites in the pre-fix blob

`_ZERO = torch.zeros(())` is defined at line 21. `return _ZERO` sites:

| line | owner | disposition |
|---|---|---|
| `:103` | UR (N_e == 0) | untouched (FIX-025, DIR-2) |
| `:140` | **SP** (`C_t.numel() == 0`, legal `T = 0`) | **changed to `NaN`** |
| `:153` | **SP** (`not per_expert_means`) | **changed to `NaN`** |
| `:165` | D_chord (N_e < 2) | untouched (FIX-025, DIR-2) |
| `:228` | MCI / CG degenerate | untouched (FIX-025, DIR-2) |

## 2. Bit-level indistinguishability, pre-fix vs post-fix

The pre-fix all-dead return *was* `metrics._ZERO`. That module attribute still
exists after the fix, so the pre-fix behaviour stays reproducible:

```
live SP (d_c=2, assignments=[0,0,1,1])  = 0.0
metrics._ZERO                          = 0.0
torch.equal(_ZERO, live)   [PRE-FIX]   = True
repr(_ZERO)                            = tensor(0.)

SP(dead config)            [POST-FIX]  = nan
torch.equal(dead, live)    [POST-FIX]  = False
```

`0.6f + (-0.6f) == 0.0` in IEEE-754 binary32, so `SP_0 = SP_1 = 0.0` exactly.
Per-token signature norms: [1.0, 1.0, 1.0, 1.0] — all exactly 1.0.

## 3. Why `:153` (`not per_expert_means`) is unreachable for legal inputs

A pigeonhole proof, not a trace. For `T >= 1` with every entry of `assignments`
in `[0, N_e)`: pick any token `t`; then `assignments[t] = i` for some
`i in [0, N_e)`; the loop's `member = (assignments == i)` is non-empty at that
`i`, so `n_i_val >= 1`, so `i` is not skipped and `per_expert_means` is
non-empty. Hence `not per_expert_means` cannot hold. The **legal** all-dead
path is `T = 0` at `:139-140`. `:153` is reachable only via an out-of-range
assignment, `N_e = 0`, or a shape mismatch.

**Ledger correction.** The audit ledger attributed the all-dead entry to
`:152-153`; the legal entry is `:139-140`. The indistinguishability conclusion
is unaffected (both returned the same object) but the line attribution was not
exact. Registered here per the ledger's own "keep the entry, register the
discrepancy separately" discipline; deliberately NOT written back into the
ledger body, which the ledger-keeping discipline forbids.

## 4. FIX-007 numeric baselines

`‖∂logit/∂C‖₂ == β·‖c‖₂` at every angle (unit sphere, β = β_max = 32.0):

| angle | measured | verdict |
|---|---|---|
| θ =   0° | 32 | == 32.0 |
| θ =  45° | 32 | == 32.0 |
| θ =  90° | 32 | == 32.0 |
| θ = 135° | 32 | == 32.0 |
| θ = 180° | 32 | == 32.0 |

Off the sphere at `‖C‖₂ = 2`, `β = β_max`: autograd gives
`32.0`, while the superseded spec form `β·c/‖C‖` predicts
`16.0` — a factor of exactly 2. Latent on the unit sphere, visible off it.

Float64 logistic saturation: `σ(γ)` first rounds to exactly `1.0` at
`γ ≈ 36.74`. Measured gap `β_max − ‖∂logit/∂C‖₂`:
γ=10 → `0.001448192011604732`, γ=30 → `2.9807267765136203e-12`. The gaps are tiny, so
the "strictly below β_max" assertion can only be `got < β_max` — any fixed
positive margin either passes vacuously or demands a gap the parameterisation
does not produce.

`tests/` contains 11 lines / 14 occurrences of `autograd.grad`
(`test_beta.py` 7, `test_loss.py` 2, `test_distance.py` 1, `test_gating.py` 1),
and **0** of them use a centroid `c`/`c_i` as the differentiation variable.
Before this change the `c`-side gradient had zero coverage; the three tests
added here are the first in the repo to differentiate w.r.t. `c`.

*The ledger recorded "10 处 `autograd.grad`" for `tests/`. Measured at
`3c64cdc` it is 11 lines / 14 occurrences. The ledger figure was taken at
`dde0e1d`, three commits earlier; `df4a1d2` and `3c64cdc` added autograd call
sites. The load-bearing part of the claim — zero centroid-variable
differentiation — is confirmed and unchanged.*
