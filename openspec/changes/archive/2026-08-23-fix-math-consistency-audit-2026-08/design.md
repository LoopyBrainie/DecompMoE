# Design — `fix-math-consistency-audit-2026-08`

## Context

This change is **spec-only**. The `wayfinder` and `decompmoe-skeleton` specs are revised to be self-consistent and to declare closed-form invariants; code/test rewrites are explicitly out of scope and handed off to a paired `fix-math-consistency-audit-2026-08-apply` change (mirroring the `fix-openspec-doc-bugs` → `fix-openspec-doc-bugs-apply` precedent). The spec is the only artifact this change owns.

See `proposal.md` — Why / What Changes for motivation and full scope; this document focuses on the architectural / methodology decisions behind the spec delta.

## Goals / Non-Goals

**Goals:**
- Spec becomes self-consistent: every Req with a concrete number has a closed-form invariant the implementation can be measured against.
- Every tautological test (M5) has a new Scenarios that pins the spec-derived constant it should assert.
- Voronoi table corrected; FLOPs coefficient pinned to absolute value; β operational domain formalized with worked example; 4 offline metrics declared with closed-form invariants; `ExpertPool` shape contract upgraded.
- Apply-phase handoff is explicit: tasks.md marks every code/test edit as `~~(已移交下游)~~` (mirrors archived pattern).

**Non-Goals:**
- No code changes (apply phase).
- No test rewrites (apply phase).
- No addition of new requirements on the routing math itself — only invariants on existing requirements.
- No `viz.py` numerical work (m5 deferred per proposal).

## Decisions

### Decision 1 — Single Voronoi definition; the equation is authoritative

**Choice**: The spec keeps only the equation `½ · I_{sin²θ}((d_c−1)/2, 1/2) = 1/N_e` with the unique root in `(0, π/2]`. The 67.24° / 58.47° tabulated values are the *outputs* of the equation at `(N_e=16, d_c=16)` and `(N_e=64, d_c=16)`. The 52° / 25.45° entries are deleted. The `r_Voronoi` row updates to `0.6127 / 0.4776`. The "unique `θ ∈ (0, π)`" wording is replaced with `(0, π/2]` (the equation is symmetric about `π/2`; the half-cap interpretation requires `θ ≤ π/2`).

**Rationale**: Author confirmed (`wayfinder/tickets/A5-3.md:62-67`) that the 52° figure is an *unverified estimate* ("16 个点在 S^15 上的等距划分上界"), not a separately defined concept. Independent root-finding of the equation yields 67.24°, which fails the same equation by 14.7× at the spec's table value. There is no dual definition to preserve; preserving a deliberately wrong table alongside a correct equation invites future audits to fail again.

**Alternatives considered**:
- (a) Dual definitions (preserve 52° as "nearest-neighbor half-angle") — rejected because A5-3 has no derivation; the future audit would not know which definition to use.
- (b) Mark 52° as "unknown / pending wayfinder verification" — rejected because the user explicitly chose "replace with computed values" (Q1 answer).

### Decision 2 — γ' reset formula and β^eff continuity are pinned via worked example

**Choice**: The spec declares the worked example `gamma_reset_for_phase4(16.0) = ln(15/16) ≈ −0.0645385...` (within `abs=1e-4`) and the closed-form `β^eff(Phase 4, t=0) = 1 + 31 · σ(ln(15/16)) = 16.0` exactly. These are pinned as ADDED Requirements on both `wayfinder` and `decompmoe-skeleton` deltas.

**Rationale**: Spec text already contained the formula but no worked number; the missing numeric anchor is what made the apply-phase implementation testable. The `0.0645` value also appears in master `wayfinder/spec.md:473` ("Scenario: Phase 3 → 4 transition is continuous") but without a tight bound — tightening to `abs=1e-4` makes the test discriminating.

**Alternatives considered**:
- (a) Leave spec as formula-only, let apply phase pick the bound — rejected because then any reasonable bisection would pass; no closed-form anchor.
- (b) Use a different value (e.g. `β_p3 = 8`) — rejected because `β_p3 = 16` is the spec's Phase 3 terminal `β_max` and the only value where continuity is exercised at runtime.

### Decision 3 — `phase_beta_box(2) == (1.0, 4.0)` as a Scenario, not just a description

**Choice**: The spec adds an ADDED Requirement (`Phase 2 β Box Equality`) that pins `phase_beta_box(2) == (1.0, 4.0)` and `phase_beta_box(3) == (4.0, 16.0)` as exact-equal Scenarios. The current spec text describes the box but does not pin it as an assertion; without this Scenario, the code-level bug (`phase_beta_box(2)` falls through to `(1.0, 32.0)`) is invisible to the test suite.

**Rationale**: Description-as-prose vs Scenario-as-assertion is exactly the difference between `fix-openspec-doc-bugs` (which moved M5 tautologies from prose to Scenarios) and `fix-spec-doc-oversights` (which caught the FLOPs `0.26%` arithmetic error by checking prose). Pinning as Scenario makes the apply phase have a target assertion.

**Alternatives considered**:
- (a) MODIFY the existing Req 14 with whole-block replacement (adding the Scenario inline) — rejected because that bloats the delta by ~80 lines and forces re-assertion of all original Scenarios. The ADDED-Requirement pattern is cleaner and aligns with Decision 5's approach.

### Decision 4 — Resurrection perturbation contract: per-expert shape, not whole-vector

**Choice**: The spec declares `resurrection_perturb_distribution(target_idx, *, eps_std=0.05)` returns shape `(d_c,)` (centroid perturbation) or `(d_model · d_ffn,)` (expert-weight perturbation), NOT `(N_e,)`. The accompanying `β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}` mutation is part of the same event. The current code `torch.randn_like(f_per_expert)` ignores `target_idx` and returns the wrong shape; the spec previously said only "perturb clone with ε ~ N(0, 0.05² I)" without pinning shape.

**Rationale**: The semantic distinction (centroid vs whole routing frequency) is the entire point of Resurrection; without the shape contract, an implementation that returns a routing-frequency perturbation can pass the "any random tensor" grep test but break Dead Expert Resurrection functionally. The β decay is half of the resurrection event — splitting it across two function calls would lose the rate-limit guarantee.

**Alternatives considered**:
- (a) Keep shape-flexible ("returns a tensor") — rejected because the apply-phase test would need to check shape anyway; better to pin it in spec.
- (b) Separate `perturb_centroid(target_idx)` and `decay_beta(target_idx, donor_idx)` — rejected because the rate-limit guarantee requires the operation to be atomic.

### Decision 5 — ADDED Requirements for closed-form invariants (not MODIFIED whole-block)

**Choice**: For each existing Requirement that needs a new Scenario (Req 7, 13, 14, 20, 24 in `wayfinder`), the spec adds a *new* ADDED Requirement that captures the closed-form invariant — rather than MODIFIED-whole-block replacement of the existing Requirement. The MODIFIED path is reserved for Reqs with actual text changes (Req 11 Voronoi table; multiple `decompmoe-skeleton` Reqs).

**Rationale**: MODIFIED-whole-block replacement requires copying every original Scenario verbatim (≈80 lines per Req for Req 14, 24). ADDED Requirements are self-contained, name the invariant explicitly (`"Operational Domain γ' Reset Closed-Form Worked Example"`), and the apply-phase test maps 1:1 to the ADDED Requirement name. This trades bulk for clarity.

**Alternatives considered**:
- (a) MODIFIED-whole-block for all 6 wayfinder Reqs — rejected because the delta would balloon to ≈600 lines vs the current ≈250 lines; the apply-phase review would have to scroll past already-verified Scenarios.
- (b) ADDED Requirements for everything, including Req 11 — rejected because Req 11 has actual text changes (Voronoi table values, domain), not just new Scenarios.

### Decision 6 — Tightest possible closed-form for gradient bounds

**Choice**: The spec adds `‖∂logit/∂C‖₂ == 32.0` (at `C=e_1, c=e_2, β=β_max`) and `|∂logit/∂γ| == 15.95` (at `γ=0, c=−C`) as Scenarios. These are the *attained* (worst-case) values, not loose bounds like `≤ β_max`.

**Rationale**: The existing tests `test_grad_C_bound` and `test_grad_gamma_bound` assert `≤ 32` and `≤ 15.95` respectively, but the actual gradient norm on random unit vectors is `≈ 8` and `≈ 6` — the tests are tautological (pass even if the formula is wrong by 4×). Tightening to the attained value at the worst-case configuration makes the test discriminating.

**Alternatives considered**:
- (a) Use loose bounds (`≤ β_max`) — rejected because they pass under formula errors.
- (b) Use unit-vector random sampling — rejected because the worst-case configuration is known and deterministic (`e_1, e_2` for the C-gradient; `−e_1` for the γ-gradient).

### Decision 7 — Numerical forward-formula verification (replace source-grep test)

**Choice**: The spec adds `x_out == x + Σ_{i ∈ I_k} p_i · E_i` within `abs=1e-6` as a Scenario using stub experts. The current `tests/test_gating.py::test_forward_formula_strictness` only checks that the source file contains the literal substring `"x_out"` (which is satisfied by any docstring or comment).

**Rationale**: Source-grep is a structural test, not a numerical one. The forward formula is a runtime equality; the only meaningful test is to verify it numerically with controlled inputs. Stub experts (returning fixed `E_i`) make the test deterministic and reproducible.

**Alternatives considered**:
- (a) Keep source-grep + add a numerical test — rejected because the source-grep adds no value once the numerical test exists.
- (b) Numerical test against real `SwiGLUExpert` — rejected because the expert's nonlinearity makes the assertion hard to predict without running the actual computation; stub experts let the test pin the *gate* layer independently.

## Risks / Trade-offs

**[Risk 1] Voronoi table update breaks existing visual aids and historical tickets**: The 67.24° figure may appear in design diagrams, wayfinder prose, or historical wayfinder tickets that weren't surveyed. The wayfinder source of intent (`wayfinder/tickets/A5-3.md:62` with `~52° (估算)`, `wayfinder/map.md` with `25.75°`) still carries the prior estimates — since the spec deltas backlink to A5-3 as Source, a future audit rereading the ticket would re-derive the wrong value. **Mitigation**: post-archive, run `grep -F "52.00\|25.45\|25.75\|0.9076\|0.4494\|0.380\|0.0971" docs/ README.md openspec/specs/wayfinder/tickets/ openspec/specs/wayfinder/map.md` repo-wide; flag any non-spec references for the next doc-only change. Per `CLAUDE.md §8` (2026-08-21 ruling), wayfinder tickets are **historical decision trail only** (not required-sync downstream artifacts), so ticket-level edits are out of this change's scope — but the grep above ensures the audit-friendly path is documented for the next reviewer.

**[Risk 2] ADDED-Requirement pattern may orphan Scenarios from their parent Req**: An apply-phase reader of the merged spec will see "Operational Domain γ' Reset Closed-Form Worked Example" as a sibling of Req 7, not nested inside it. **Mitigation**: each ADDED Requirement includes the literal phrase `(References Req 7 Invariant 3 / Req 24)` or similar — the cross-link is text-searchable.

**[Risk 3] Closed-form invariants make the spec brittle to small parameter changes**: If `β_min` or `β_max` ever shifts, every closed-form pin (`1.035`, `16.05`, `0.0645`) must be re-derived. **Mitigation**: pin values are tied to the current `MVPConfig` defaults; a future `MVPConfig` change is itself a change requiring spec revision.

**[Risk 4] `metrics.OFFLINE` name change (`D_c` → `D_chord`) ripples through `metrics.py` exports**: If apply phase renames the function, callers (tests, downstream modules) must update. **Mitigation**: the existing skeleton spec already uses `"D_chord"` (line 287-288); only the implementation is mis-named. The rename is local to `metrics.py`.

**[Risk 5] Worst-case gradient Scenario assumes `‖C‖₂ = 1` strictly**: An implementation that maintains `‖C‖₂ ≤ 1 + 1e-6` (i.e., not strictly on the sphere) will have `‖∂logit/∂C‖₂ = β · ‖c‖ / ‖C‖ < β`, never attaining the worst case. **Mitigation**: the orthogonal Scenario's value `32.0` is asserted with `abs=1e-4`, well above FP-error magnitude; an off-sphere `‖C‖ = 1.0001` still yields `‖∂‖ ≈ 31.997` which fails the assertion. This is the intended discrimination.

## Migration Plan

1. **Spec archive**: After `openspec validate --strict` passes and `openspec archive --yes` succeeds, the merged `openspec/specs/wayfinder/spec.md` and `openspec/specs/decompmoe-skeleton/spec.md` carry the new Scenarios. The post-archive independent self-consistency check (CLAUDE.md §3) substitutes each new closed-form constant back into its equation and compares to the spec claim — catches any B1/B4/B6/B7-style regression at archive time.

2. **Apply change creation**: User creates `fix-math-consistency-audit-2026-08-apply` (code-only change) with `Modified Capabilities: 无`. Its `proposal.md` references this change as source of truth; its `tasks.md` mirrors this change's `## 3. Apply 阶段触发` section verbatim.

3. **Apply change archive**: After all 17 task sub-items (3.1–3.17) pass `uv run pytest tests/` with `≥ 95 + 8 new` tests green, the apply change archives independently.

4. **No data migration**: this change touches only Markdown files; no JSON/YAML/binary migration.

## Open Questions

**Resolved (with explicit two-stage split — Major 6 audit finding)**: The original review's AskUserQuestion answers (Q1 Voronoi: replace; Q2 offline metrics: implement; Q3 ExpertPool: `nn.Module` + `ModuleList`; Q4 scope: Blockers + Major) are *spec-level* decisions: they answer "should the spec require these?" (yes), not "where does the code land?" The code implementation of Q2 (offline metrics closed forms, MCI formula `1/(d_c·Σλ̃²)`, CG invariants, SP aggregation) and Q3 (`ExpertPool(nn.Module)` + `nn.ModuleList`, `100_663_296` param count) lives in the downstream `fix-math-consistency-audit-2026-08-apply` change. The two-stage split is deliberate and mirrors the `fix-openspec-doc-bugs` → `fix-openspec-doc-bugs-apply` precedent; it is NOT a contradiction of the original answers. `tasks.md §3` (17 items, all strike-through + `[ ]`) is the explicit apply-phase handoff.

**Still open (Minor findings m1–m5)**: m1 `nan_ladder` rename `halve_lr` → `decay_lr`; m2 `spherical_l2_normalize` `eps`-denominator bias; m3 wayfinder-vs-skeleton `phase_id(100_000)` boundary inconsistency; m4 ~~now resolved~~ (consolidated into the `Beta Parameterization Operational Domain` Requirement's explicit `MAX_GRAD_PER_GAMMA` domain label and the new `MAX_GRAD_PER_GAMMA_PHASE4 = 15.5` operational-domain counterpart in apply §3.8 / §3.10); m5 `viz.py` Protocol stub免责. m1, m2, m3, m5 remain open for a future change that explicitly owns them.
