# Project loops

Reusable AI-agent workflows tailored to DecompMoE. Each entry records the loop
name, the one-sentence explanation, the exact prompt, the save date, and (for
adaptations) the source loop's URL and the modified date it showed at save
time. Treat the prompt text as the binding contract; reload the source loop
from the URL if its modified date is newer than what is recorded here and
compare before reusing.

## The DecompMoE SDD math-conformance review loop

- Saved: 2026-09-04
- Source: adapted from
  [#082 spec dev-review loop](https://signals.forwardfuture.com/loop-library/loops/spec-dev-review-loop/)
  (modified 2026-07-07) and
  [#076 product contract conformance loop](https://signals.forwardfuture.com/loop-library/loops/product-contract-conformance-loop/)
  (modified 2026-07-07). No upstream change since save — verified
  2026-09-04.
- Explanation: For one OpenSpec scope (spec + apply + code + pytest), audit
  every mathematical claim against the closed-form constant, require an
  OpenSpec `**Source:**` / `Resolution` record for every drift from
  wayfinder initial intent, and require each sub-spec pytest to assert the
  math principle — not just the function — until all three layers pass or
  a human-decision blocker is logged.
- Prompt:

  > For one OpenSpec scope (one change or one spec section), build a
  > `REVIEW-LEDGER.md` with one row per `Requirement` × {spec math claim,
  > wayfinder intent, code signature, pytest math assertion}. For each row:
  > (1) **spec math audit** — compute every closed-form numeric claim in
  > the spec (FLOPs, parameter count, `θ_Voronoi`, `σ(γ_init)`,
  > `1/(2·N_e)` threshold, α schedule, phase ratios) and check it against
  > the spec's stated constant with `pytest.approx(..., abs=...)`-grade
  > precision — not by grep-matching the source; (2) **wayfinder
  > cross-check** — compare the spec's value to the corresponding wayfinder
  > ticket decision, and if they diverge, require an OpenSpec `**Source:**`
  > + `Resolution:` record naming the ticket and the rationale; (3) **code
  > math review** — verify the code's forward formula, distance metric,
  > gating function, and hard constraints (`no w_i`, `no kv_cache_c`,
  > `C_t ∈ S^{d_c−1}`) match the spec's formal architecture, with one
  > bounded inspection per row; (4) **pytest math constraint** — verify
  > each sub-spec TDD test contains a math-principle assertion (e.g.
  > `pytest.approx(value, abs=...)` on a closed-form constant), and flag
  > any test that only smoke-tests the function. After each review slice,
  > run the project's spec-anchored tests (`uv run pytest tests/` or the
  > change's apply-checklist) and record in `REVIEW-LEDGER.md` the row
  > status (`passed` / `math-error` / `drift-no-record` /
  > `code-mismatch` / `test-no-math-assert` / `blocked`), the round number,
  > and the next bounded action. Fix only one confirmed high-impact
  > mismatch per round; do not start a new spec while a previous scope is
  > still flagged. Stop when every row is `passed`, the same `math-error`
  > or `drift-no-record` repeats for two rounds without new evidence, or a
  > human decision is required (post the blocker in `REVIEW-LEDGER.md` with
  > the affected row and proposed resolution). Never describe an errored
  > or exhausted round as passed. Finish with the ledger, the run summary,
  > and the next reviewable scope.

- Verify: every ledger row is `passed` or explicitly `blocked` with a
  human-decision owner; every math claim in the spec is computed and
  matched to the spec's stated constant; every wayfinder divergence has a
  `**Source:**` / `Resolution:` record; every sub-spec pytest has a
  math-principle assertion; failed or blocked runs are reported as such,
  never as passed.
