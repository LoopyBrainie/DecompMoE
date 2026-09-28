# Design

## Context

See `proposal.md` § Why for motivation. The design-relevant facts:

- Two distinct literal precisions coexist in this repo's governance model, and they are deliberately different things:
  - **6-decimal test literal** (`1.173548`, `1.020506`, `1.165848`) — the bisection output truncated to 6dp, per `openspec/specs/governance/spec.md` req-gov-1 §3. This is what `pytest.approx(..., abs=1e-6)` is scoped to.
  - **4-decimal canonical spec literal** (`1.1735`, `1.0205`, `67.24°`, `58.47°`) — the prose display form, frozen at project level in `CLAUDE.md` §5 and declared in `wayfinder` req-11 L236-237.
- Their separation is already authoritative. `governance/spec.md:17` states verbatim: *"These test literals are distinct from the **canonical spec literal** `67.24° (≈ 1.1735 rad)` declared in Requirement 11 of `wayfinder/spec.md` (the bisection-perspective 4dp form of `1.1735482746999482`)."*
- The two tiers are **not interchangeable** because their measured distances from the impl output differ by orders of magnitude:

  | tier | literal | distance from impl `1.1735482746999482` | carries |
  |---|---|---|---|
  | 6dp test | `1.173548` | `2.747e-07` | `pytest.approx(..., abs=1e-6)` |
  | 4dp spec | `1.1735` | `4.827470e-05` | bare `==` on `round(θ, 4)` |

  So a 4dp literal is **structurally incapable** of carrying a `1e-6` tolerance — not by policy, but by arithmetic. This is the single fact that makes the fix deterministic rather than a matter of taste.
- The governance rules themselves are sound. `governance:17` gives the disambiguation; `governance:53` forbids `abs=1e-4` or wider on an **angle** claim. Neither needs editing. The defect is entirely on the citing side.
- Baseline is green: `204 passed`, both lint gates `exit=0`, anchor coverage 100%. Nothing is currently red; this is a contract-satisfiability repair, not a regression fix.

## Goals / Non-Goals

**Goals:**

- Make every literal↔tolerance pairing in `decompmoe-skeleton` req-6 and `wayfinder` req-11 **empirically satisfiable** — a reader must be able to write the assertion the spec describes and have it pass.
- Make the tolerance's **provenance** unambiguous: a reader must be able to grep which governance clause grants a given tolerance and find that it actually says so.
- **Zero new numbers.** Every figure introduced already exists in `governance:17` or is a measured impl value from this change's verification.
- Zero drift surface: the two specs must point at the same authoritative disambiguation rather than restating it independently.

**Non-Goals:**

- Not changing `openspec/specs/governance/spec.md`. The rules are correct; the citations were wrong.
- Not changing `src/`, `tests/`, `scripts/`, or `CLAUDE.md`. This is a pure prose-contract repair.
- Not adding a mechanical guard against this defect class (see Decision 4).
- Not normalizing the 4dp prose form into the 6dp literal form, or vice versa. Both are canonical at their own tier.

## Decisions

### Decision 1 — Adopt a two-tier literal contract (ADOPTED)

**Decision.** `abs=1e-6` binds **exclusively** to the 6dp test literal. The 4dp canonical prose literal is explicitly declared to be *forbidden* from pairing with that tolerance, and is guarded instead by bare integer equality on `round(θ, 4)` / `round(math.degrees(θ), 2)`.

**Rationale.** It is the only option that (a) restores satisfiability, (b) preserves the `CLAUDE.md` §5 frozen 4dp form, and (c) needs no new authority — the rule is quoted verbatim from `governance:17`, so the change is a *citation repair*, not a *policy invention*.

**Alternatives considered and rejected:**

| alternative | why rejected |
|---|---|
| Revert `abs=1e-6` → `abs=1e-4` on `decompmoe-skeleton` L98 (i.e. undo `b23f0e5` task `1.3.1`) | Directly contradicts `governance:53`: *"Any test verifying a bisection-derived value with `abs=1e-4` or wider tolerance on an **angle** claim is out of scope for this Scenario and MUST be audited by a future change."* It would trade one spec conflict for another. |
| Promote the literal to the exact impl value `1.1735482746999482` | Requires unfreezing the 4dp canonical form in `CLAUDE.md` §5 **and** rewriting `wayfinder` req-11 L236-237, creating a brand-new three-site divergence to fix a two-site one. Also discards the deliberate display-precision disclosure the `≈` symbol exists to express. |
| Keep `1.1735` and just soften `1e-6` to "approximately" | Leaves the clause formally unsatisfiable; prose hedging does not make `|θ − 1.1735| = 4.83e-5 < 1e-6` true. |

**Note on the two-tier shape.** This is not a new invention — `tests/test_sphere.py` has implemented exactly this shape since `b23f0e5` (`approx(1.173548, abs=1e-6)` for one tier, `round(θ, 4) == 1.1735` for the other). The change makes the spec describe the tests that already exist.

### Decision 2 — Delete the false authorization rather than retarget the number (ADOPTED)

**Decision.** `wayfinder` L240/L241's clause *"both lie within the `< 1e-4 rad` test tolerance permitted by `openspec/specs/governance/spec.md` req-gov-1 §2"* is **removed**, replaced by a statement that the gap is prose-to-prose and not bounded by any test tolerance, plus an explicit note that §2 prescribes no numeric value while `1e-6` comes from §3.

**Rationale.** The clause commits a *category error*, not just a stale number: it frames a documentation-internal rounding discrepancy as something a test tolerance governs. No test asserts the 4dp form at any tolerance, so there is no tolerance to point at. Retargeting is impossible; deletion plus restatement is the honest repair.

**Alternatives considered and rejected:**

| alternative | why rejected |
|---|---|
| Mechanically change `1e-4` → `1e-6` (the obvious "make the specs agree" fix) | **Would invert the defect into a new falsehood.** `5.94e-5` is `59×` larger than `1e-6`; the rewritten sentence would be false in the opposite direction. This is the trap the audit item implicitly invites and the one this decision exists to avoid. |
| Change `1e-4` → some intermediate value (e.g. `1e-4` → `1e-3`) | Still invents a tolerance no test uses and no governance clause grants. |
| Leave L240/L241 alone as "documentation only" | Preserves a claim that cites a nonexistent authorization, and leaves `decompmoe-skeleton` and `wayfinder` contradicting each other. |

### Decision 3 — Do not touch `governance` (ADOPTED)

**Decision.** `openspec/specs/governance/spec.md` is left byte-identical. This change produces exactly **two** capability deltas: `wayfinder` and `decompmoe-skeleton`.

**Rationale.** `governance:17` (the 6dp/4dp disambiguation) and `governance:53` (the angle-tolerance prohibition) are both correct and complete — verified by reading them, not assumed. Every observed failure was a *citing* failure: `decompmoe-skeleton` L98 cited §3 without adopting its two-tier structure; `wayfinder` L240/L241 cited §2 for a tolerance §2 never grants. Per `CLAUDE.md` §3 (surgical changes), when the rule is right you fix the reference, not the rule.

**Alternatives considered and rejected:**

| alternative | why rejected |
|---|---|
| Add an explicit "§2 prescribes no numeric tolerance" sentence to `governance:15` | Defensible, but scope expansion: it makes `governance` a third modified capability for a statement this change already states at the citation site. Re-evaluate only if the misattribution recurs. |
| Rewrite `governance:17` to be even more explicit | The paragraph is already precise and already names the `wayfinder` req-11 relationship. Nothing is ambiguous in it. |

### Decision 4 — Ship no mechanical guard (ADOPTED)

**Decision.** No new test, no new lint rule, no new Scenario. The change is pure spec prose.

**Rationale.** Both literals are already guarded: `approx(1.173548, abs=1e-6)` covers the 6dp tier, `round(θ, 4) == 1.1735` covers the 4dp tier. A third guard would only re-assert what the corrected prose now says. Per `CLAUDE.md` §2 ("nothing speculative"), the addition is not justified by the current evidence.

**Explicitly deferred, with the trigger to revisit:** a mechanism that scans `openspec/specs/**` for declarations where literal precision ≤ declared tolerance. That requires a new `scripts/` rule plus gate wiring — a governance-level change of the kind Decision 3 declines today. **If this defect class recurs a third time, that mechanism is the right fix and should be proposed then.** The precedent chain is already recorded: `3dd1104` (literals deleted, tautology left) → `b23f0e5` (literals restored, tolerance misbound) → this change (tolerance retargeted).

## Scope extension: P1–P5 (2026-09-28 code-review follow-up, same change)

The 2026-09-28 code review surfaced six further defects (P1–P6). All six were independently re-verified by the parent agent before acceptance. Because P1, P3, and P5 live in `decompmoe-skeleton` req-6 — a Requirement this change already carries a full-block `MODIFIED` delta for — filing them in a *second* change would produce two competing deltas on the same Requirement, and OpenSpec archive merges by overwrite, so the later archive would silently discard the earlier one. **P1/P3/P5 are therefore amended into this change rather than split out.** The code-side items (P2, P4) touch no other change at all.

### Decision 5 — Remove the dead `n` parameter and correct the "60-segment" claim (ADOPTED)

**Decision.** `src/decompmoe/sphere.py::_betainc_regularized` drops its `n: int = 60` parameter, which an AST walk shows is never read in the body; and `decompmoe-skeleton` L116 is corrected from "Gauss–Legendre 8-point **60-segment**" to "a **single** 8-point Gauss–Legendre panel on `[0, x]` with no subdivision".

**Rationale.** The signature advertised a segmented quadrature that was never implemented. The claim entered the spec from the archived change `2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix`, which *assumed* "Gauss-Legendre 8-point 60-subinterval is an impl design choice, not a bug" and wrote the assumption into three spec locations without checking the implementation. The trap is concrete: a maintainer tuning accuracy would reach for `n=` and see no behavioural change, and no test would fail. Verified safe to remove — all 6 call sites (`sphere.py:144` plus 5 in `tests/test_sphere.py`) pass exactly three positional arguments.

**Alternatives considered and rejected:**

| alternative | why rejected |
|---|---|
| Implement the segmentation | Would change every residual figure in the spec (`1.16e-14`, `4.15e-7`, `~8.49e-7 rad`, …) and silently alter `canonical_voronoi_angle` output. Behaviour change, not a defect repair. |
| Leave the parameter, fix only the prose | Leaves the trap armed. The parameter is the thing a maintainer would actually touch. |
| Fix `governance` L20/L21 too | **Contested** — see Decision 7. |

### Decision 6 — State measured accuracy instead of an aspirational one (ADOPTED)

**Decision.** Both `sphere.py` docstrings are corrected: `_betainc_regularized` no longer claims "accurate to ~1e-12" (measured absolute error at the MVP point is `8.29e-07`, relative `6.63 ppm`), and `canonical_voronoi_angle` gains an explicit accuracy band showing the true closed-form residual across `d_c` at `N_e = 16` (`d_c=2 → 3.35e-03` … `d_c=8 → 7.39e-09` … `d_c=16 → 4.15e-07` … `d_c=32 → 4.29e-05`).

**Rationale.** The impl-internal residual is always ~`1e-15`–`1e-14` because it is measured against `_betainc_regularized` itself — a self-referential frame that is satisfied for *every* input, including `d_c = 2` where the true error is `3.35e-03`. A reader had no way to know the declared domain (`signature_dim >= 2`) exceeds the validated domain. Recording the measured band makes the boundary explicit without changing any behaviour.

**MVP impact: none.** `d_c = 16` is frozen per `CLAUDE.md` §5, and this change alters no computed value.

### Decision 7 — Hold the contested remainder (ADOPTED)

**Decision.** Two items are **deliberately not fixed** by this change and are recorded as held:

| held item | location | why held |
|---|---|---|
| P2/P3 governance side | `governance/spec.md` L20 + L21 — "Gauss–Legendre 8-point, **60 subintervals**" and the `< 1 ppm` attribution | `governance` req-gov-1 is owned by the concurrent change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` (edits L26 + L52). A third full-block `MODIFIED` delta would silently overwrite one of the two. |
| P6 — unframed `< 1e-9` claims | `wayfinder/spec.md` L233 and the L274-276 Scenario | Both sit inside req-11, which is contested by **two** other unarchived changes: this one (L240/L241) and a2-a3-a4 (L235). |

**Consequence accepted:** after this change, `decompmoe-skeleton` L116 correctly says "single panel" while `governance` L20/L21 still say "60 subintervals" — a **temporary, deliberate inconsistency** in the truth source. It is recorded in `tasks.md` §9.1 with the exact wording required, so the follow-up change is a mechanical, pre-verified edit rather than fresh analysis.

**P6 is the highest-priority held item** because it is the same defect class this change exists to repair: in the true closed-form frame the residual at `(16, 16)` is `4.1457e-7`, so the claim "evaluating to less than `1e-9`" is false as written, and `governance` req-gov-1 obligation 4 explicitly requires "Spec MUST clarify which frame is used for '< 1e-9' claims."

## Risks / Trade-offs

**[A future agent re-binds the 4dp literal to `1e-6`]** → The corrected `decompmoe-skeleton` L98 now carries an inline prohibition (*"MUST NOT be paired with the `abs=1e-6` tolerance"*) plus the measured justification (`4.83e-5` / `48×`), and `design.md` Decision 1 records both rejected alternatives with reasons. A future agent grepping `1.1735` in the spec sees the constraint rather than having to rediscover it.

**[`decompmoe-skeleton` L98 and `wayfinder` req-11 now read differently, inviting future "these should match" edits]** → They are not meant to match verbatim. The new `decompmoe-skeleton` text drops the old `(Matches master `wayfinder` Req 11 verbatim.)` parenthetical and instead states that both derive from `governance` req-gov-1 §3 — making the shared authority explicit, and removing the false verbatim claim that the divergence would otherwise contradict. *(This parenthetical adjustment is a mechanical consequence of Decision 1: once the two paragraphs legitimately differ, asserting they match verbatim would itself be a false statement.)*

**[`wayfinder` L235 says `< 1e-6` while L240/L241 now say "no test tolerance" — a reader may see a new contradiction]** → There is no contradiction: L235's `4.15e-7` / `1.43e-9` are *equation residuals* (governed by req-gov-1 §4 frame rules), whereas L240/L241's `5.94e-5` is a *prose display gap* (governed by nothing). L235 is explicitly listed as not-modified in this change's delta metadata, with its figures independently recomputed as correct.

**[Long single-line prose readability]** → Unchanged in kind from the existing style: L98 and L240/L241 are already single-line prose paragraphs in these specs. This change lengthens them but introduces no new formatting convention.

**[`openspec validate` rejects the delta shape]** → Mitigated by validating before commit (task 3.5). If the validator objects to full-block `MODIFIED` with verbatim-copied scenarios, the fallback is to keep the delta as-is and let archive do the merge — the delta content is already the complete post-change requirement text, so no information is lost either way.

## Migration Plan

Not applicable in the deployment sense — this change edits specification prose only, with no code, data, or API surface.

Apply sequence:

1. Apply the two delta bodies to the live specs (`decompmoe-skeleton` L98; `wayfinder` L240 + L241) — three line replacements, no line-count change.
2. Verify gates: `pytest` (204 passed), both lint scripts (`exit=0`), anchor coverage (100%), `openspec validate`.
3. Commit once on `dev`.
4. Archive is a **separate, later action** requiring explicit user initiation, gated on both lint scripts reporting `exit=0` per `CLAUDE.md` §3.

**Rollback:** `git revert <commit>` restores the prior spec text. There is no state to unwind, no migration to reverse, and no consumer of the changed contract outside the repository's own audit tooling.

## Open Questions

None. All four scope-shaping decisions were resolved by the user before this design was written (2026-09-28). The deferred items in Decision 4 and the `wayfinder` L235 §3-vs-§4 attribution granularity are recorded as accepted non-goals with revisit triggers, not as open questions — neither would change the specs, the approach, or the task breakdown.
