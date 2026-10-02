# Design

## Context

`src/decompmoe/sphere.py::_betainc_regularized` computes the regularized incomplete beta with **a single 8-point Gauss–Legendre panel on `[0, x]`, no subdivision**. Its own docstring declares a validated band; outside it the panel fails in two ways:

- **`x → 1⁻`**: `b = ½` puts an integrable `(1−t)^(−1/2)` singularity at the panel's RIGHT endpoint. Measured at `d_c = 16` against 50-digit quadrature, the absolute error rises from `7.98e-09` at `θ = 60°` to `5.74e-03` at `82.6°` to `1.57e-01` at `89.999°` — **five orders of magnitude**.
- **`x → 0`**: at `d_c = 2` the integrand `u^(a−1)` has `a = ½`, a `u^(−1/2)` singularity at the LEFT endpoint. `d_c = 2` is the only dimension that fails here; every `d_c ≥ 3` gives `a ≥ 1` and a smooth integrand.
- **`x ≥ 1.0` early return**: `math.sin(math.pi/2) ** 2` evaluates to EXACTLY `1.0` in float64, so `_cap_area(π/2, d_c)` takes that early return and yields `0.5` by construction. That is the origin of the E10 discontinuity (one-sided jump `7.870852e-02` at `d_c = 16`).

**Oracle discipline for this design** (see `design.md` verification notes in the archived Change 0): all canonical values come from a two-route mpmath oracle at `dps=60` that agrees to `6.68e-52` — route 1 `mp.quad` over `t^(a−1)(1−t)^(b−1)`, route 2 the four-argument `mp.betainc(a, b, 0, x, regularized=True)`. The three-argument `mp.betainc(a, b, x, regularized=True)` is **not** usable: it returns `1 − I_x` (measured `0.8691458` where `I_x = 0.1308542`).

## Goals / Non-Goals

**Goals:**

- Make `_betainc_regularized` meet its declared intent, so the spec can freeze a *mathematically-defined* canonical value instead of an implementation artefact.
- Collapse the two reference frames so `< 1e-9` holds in both, and turn "which frame?" from a silent choice into a checkable invariant.
- Restore dimensional honesty: an angle tolerance (radians) and an area-fraction residual are different quantities and MUST NOT be compared.
- Remove the `gating.py` no-op.

**Non-Goals:**

- Not `CLAUDE.md` §5's domain-of-validity wording (separately scoped).
- Not the 38 pseudo-guards (Change 1). Specifically: the residual test stays an impl-internal check; this change does **not** attempt to give it an independent oracle.
- Not a custom kernel. PyTorch eager / stdlib only.
- Not the 217 → 227 test-count delta; this change adds and removes no test function, it rewrites assertions.

## Decisions

### D1 — Freeze the mathematical root, not the implementation's output

`skeleton` req-6 and `governance` obligation 4 both froze `1.1735482746999482` **as "the impl bisection OUTPUT"** — a description of current behaviour promoted into a canonical requirement. That is defect F2.

**Decision**: the spec freezes the root of `½ · I_{sin²θ}(7.5, ½) = 1/N_e`, quoted at 16 decimals (`1.1735474259197175` / `1.1658476215516009` / `1.0205068247837132` / `1.0916065844205111`), and the implementation is required to match it within `abs=1e-6`.

**Alternatives rejected**: (a) keep freezing impl output and just refresh the digits after the fix — that keeps the *category* of defect alive, since the number would again be whatever the code happens to print; (b) drop to 8 decimals to reduce precision coupling — 16 is the existing convention and 8 digits lose the traceability to the previously published values without buying anything.

### D2 — Obligation 4: **narrow**, do not retire (differs from the review's A4 recommendation)

The `/code-review` report recommended retiring obligation 4, reasoning that once the integrator conforms, the impl-internal and true frames coincide so the two-frame apparatus is vacuous.

**Decision: narrow instead.** Restate it as *"the two frames MUST agree to `< 1e-9`"*, rather than *"pick one and say which"*.

Rationale: retiring deletes a genuine regression guard. A divergence between the frames is exactly the signal that `_betainc_regularized` has degraded again — and after a fix there is no other assertion in the suite that would catch that. Narrowing converts a permissive "either frame is fine" into a strict invariant that is *stronger* than what it replaces, at no cost in coverage.

**Alternatives rejected**: (a) retire per A4 — loses the only guard on integrator degradation; (b) leave obligation 4 as-is — it currently licenses the very thing F3b exploits (a residual test may declare the impl-internal frame and thereby certify itself).

### D3 — The 6dp literal, not the residual test, is the integrator's independent guard

A residual test that measures with the function under test cannot detect that function's error. After the fix this stops mattering for the *current* defect, but the structural weakness remains and must be stated.

**Decision**: obligation 4 gains an explicit consequence clause — no bisection Voronoi residual test may serve as its own independent guard; the independent guard is obligation 3's 6dp literal. This works because the truncated literal `1.173547` sits `1.275e-6` from the pre-fix output `1.1735482746999482` (so it **FAILS** at `abs=1e-6`) and `4.259e-7` from the canonical value (so it **PASSES**) — a genuine red→green. N_e=17 is the same shape (`1.297e-6` FAIL / `6.216e-7` PASS); N_e=64 is not a discriminator (`1.020506` is unchanged either way) and does not pretend to be.

### D4 — Correct the `abs=1e-6` rationale: it is a format floor, not a noise-floor margin

The old justification was *"the bisection residual is `< 1e-9`, therefore `1e-6` is strictly above the noise floor."* Once the integrator conforms, the residual falls to ~`1e-50`, and that argument becomes vacuous — it would equally justify any tolerance down to `1e-49`, including ones the 6dp literals cannot satisfy.

**Decision**: state the binding reason instead. A 6-decimal literal carries an intrinsic truncation error bounded by `5e-7`, so **no tolerance below `1e-6` can be satisfied even against the exact canonical value**. Measured: `|1.173547 − 1.1735474259197175| = 4.259e-07`, which is **426×** `1e-9`.

This is a stronger argument and — unlike the noise-floor one — does not depend on implementation quality at all.

⚠️ Note this **reverses** an earlier draft of this work that proposed tightening the tolerance to `1e-9`; that draft's reasoning asked "does the new literal pass on both sides?" instead of "does it go red before the fix and green after?", and the proposed `1e-9` would have failed the test outright.

### D5 — Fix the oracle citation (new finding F7)

`governance` obligation 4 and `skeleton` req-6 both cite "mpmath `betainc(regularized=True)`" as the true reference. Taken literally that call returns `1 − I_x`; a reader implementing the citation computes the complement and gets `3.750e-01` instead of `4.146e-07`.

The spec's **number** `4.15e-7` is correct — it was computed with the four-argument form. Only the citation is wrong. Both deltas now name `betainc(a, b, 0, x, regularized=True)` and state the three-argument form MUST NOT be used.

### D6 — Concurrent-worktree conflict: 3 of 4 new tests pin the defect

`tests/test_sphere.py` carries **uncommitted** work from a concurrent session: `test_cap_area_dc2_affine_degeneration`, `test_cap_area_pi_half_no_artificial_discontinuity`, `test_betainc_error_uniform_toward_one`, `test_spherical_l2_normalize_residual_dimension_dependent_bound`.

The first **three pin the current defective behaviour** — `test_cap_area_pi_half_no_artificial_discontinuity` asserts against `7.870852`, `8425829560490325` and `6.71e-09`. Fixing the integrator therefore turns them **red by design**.

**Decision**: these tests MUST be **rewritten to assert the absence** of the artefact, not deleted. Their entire value is disclosing a defect; once the defect is gone the disclosure becomes a regression guard against its return (the π/2 discontinuity must never reappear, and the `x→1⁻` error must never escalate again). The `d_c = 2` test's *exact-arithmetic* half stays valid untouched; only its implementation-deviation band moves.

**Gate**: `tasks.md` blocks the integrator edit on an explicit ownership ruling for these files.

#### D6.1 — Delta 级正面碰撞：两个 change 都在整块替换 `governance` / req-gov-1

实测（propose 期间，2026-10-02）：并发 session 新建了
`2026-10-02-a2-round2-spec-math-fixes`，其 `specs/governance/spec.md` 与本 change 的
delta **都**是 `## MODIFIED Requirements` 且都指向 `req-gov-1`。OpenSpec 归档时
**整块替换**该 requirement，因此**谁后归档谁就把对方对该块的改动整块回退**。

两边关心的事**不同**，这恰恰是最坏的情况——不会互相提示，只会静默回退：

| | 关心点 | 对 obligation 3/4 做了什么 |
|---|---|---|
| 本 change | F2 / F3b / F4 / F7 | 重写为 canonical 值 `1.1735474259197175`、6dp 字面量 `1.173547` / `1.165847`、`5.01e-52`、4 参 `betainc`、「两帧 MUST 一致」 |
| 并发 change | per-head 提取 MACs `33_040 → 33_168`（含 cross-head mean 项） | **未动**，delta 携带的是**旧版** obligation 3/4（`1.1735482746999482`、`4.15e-7`、三参 `betainc`） |

⇒ 两种坏结局：
1. 并发 change 先归档、本 change 后归档 ⇒ 本 change 的 delta 基于「MACs 修复前」的块，会把 `33_168` **回退**成 `33_040`。
2. 本 change 先归档、并发 change 后归档 ⇒ 并发 change 的 delta 会把 F2/F3b/F4/F7 的全部修复**回退**。

**其它两个 capability 无碰撞**（实测）：`decompmoe-skeleton` 本 change 改 `req-6`、
并发 change 改 `req-19`，不相交；`wayfinder` 只有并发 change 涉及（req-11/17/18/19），本 change 不碰。

**处置**：必须由人决定 (a) 把本 change 的 delta 重基到并发 change 的块之上（取其 MACs 修复 + 本 change 的 obligation 3/4 修复的并集），(b) 反向把本 change 的 obligation 3/4 修复合并进并发 change，或 (c) 排定归档顺序并**在后归档者 apply 前重基**。
本 change 不代为选择——`33_168` 相关的 `src/` 与 `tests/` 归属不在本 change 范围内。

### D7 — F6 gets no spec delta

`gating.py:36-40` selects exactly the entries that are already `-inf` and assigns `-inf` to them. Removing it cannot change any observable value, so per OpenSpec's rule (no behavior change → no requirement change) it produces no delta. `gating.py:41-43` (all-masked-row guard) and `:46-50` (`-inf → 0` exponent guard) are **not** no-ops and stay.

### D8 — Archive anchor gate

`openspec archive` has empirically destroyed `<a id="req-N"></a>` anchors in this repo (`git log 4f3e752 chore(opsx): archive F1-F8 fixes; repair anchors swallowed by archive`). Baseline at HEAD: wayfinder **36**, decompmoe-skeleton **23**, governance **4**, all at 100% coverage with code-span mentions excluded from the count. Capture before archive, recompute after; on mismatch restore from `git cat-file blob` and **never re-run archive**.

## Risks / Trade-offs

- **Rewriting the integrator invalidates 3 concurrent tests, plus the `sphere.py` docstrings the concurrent session just added** (which quote the very jump values E10 measured). → The docstring numbers become stale the moment the fix lands. Re-derive them after the fix rather than editing the concurrent session's prose blind; ownership first (D6).
- **The bisection search interval may need re-examination.** `_cap_radius` is unaffected only because its target `1/N_e ≤ 0.5` keeps the root below `π/2` for `N_e ≥ 3`. A corrected integrator changes `G(π/2)`'s neighbours but not the root location, so the bisection bounds should be re-verified rather than assumed.
- **`N_e = 2` targets exactly `0.5`, landing on the `π/2` plateau** and returning `1.5707963162581635` for every `d_c` — a constant that certifies nothing. This is unchanged by the fix, and the concurrent session's `d_c=2` test documents it. Left alone deliberately; it is a separate behavioural question.
- **Tightening the spec's numbers makes existing tests red before the implementation catches up.** This is intended (red→green) but means the intermediate commit state is not green. Sequence the tasks so the spec and the implementation land together.
- **Narrowing obligation 4 rather than retiring it is a judgement call against the review's advice.** If the project prefers the review's position, D2 is the single decision to revisit; the other nine decisions stand independently.
