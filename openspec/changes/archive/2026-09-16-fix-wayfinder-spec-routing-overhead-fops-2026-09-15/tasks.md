## 1. Spec Edit

- [x] 1.1 In `openspec/specs/wayfinder/spec.md` Req 19 ("Six Baseline Set On 4070 MVP"), insert the cross-req consistency note paragraph immediately after the routing-overhead evaluation sentence (L356) and before the `**Source:** ` line; verify the paragraph contains (a) backtick-wrapped `wayfinder/tickets/A7-2.md` referencing Req 17, (b) the explicit decomposition `+128 MACs` bias add + `+144 MACs` L2-normalize = `+544 FLOPs`, (c) the `+32 FLOPs` net figure with the directionality "Req 17 is 32 FLOPs higher", and (d) the constraint "does NOT enter the parity equation under either spec".
- [x] 1.2 Run `git diff openspec/specs/wayfinder/spec.md` and verify only one paragraph was inserted and no other lines in Req 19 were modified (formula `66_048`, ratio `0.20%`, source field, scenarios all unchanged).

## 2. Lint Gates

- [x] 2.1 Run `python scripts/lint_no_source_field_drift.py` and verify exit code = 0 (Req 19 Source field must remain backtick-wrapped `wayfinder/tickets/A8-1.md` and the new note's `wayfinder/tickets/A7-2.md` reference must also be backtick-wrapped).
- [x] 2.2 Run `python scripts/lint_no_dead_defensive.py` and verify exit code = 0.

## 3. Independent Numerical Verification

- [x] 3.1 Independently recompute `(128 + 144) · 2 − 2 · N_e · d_c` with `N_e=16, d_c=16` and confirm the result equals `32` exactly; verify the inserted text matches this arithmetic by reading the file and confirming the inserted values are `544 − 512 = 32`.
- [x] 3.2 Independently recompute Req 19's `FLOPs_Routing^(l)` as `4 · 16 · 8 · 128 + 2 · 16 · 16` and confirm it equals `66_048` (this is the canonical figure Req 19 keeps; the change must NOT modify this value).