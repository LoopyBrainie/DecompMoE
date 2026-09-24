<!--
(historical, anchor was <a id="req-34"> at L442 of live openspec/specs/wayfinder/spec.md when this change was archived by commit b842a53 on 2026-09-16; superseded by fix-cg-n-1-test-anchor-collision-and-math-coverage commit f16cb12 which relabeled "CG n=1 boundary behavior" Requirement's anchor to <a id="req-35"> at live L496 and moved req-34 anchor to live L740 "Source Field Format Invariant for OpenSpec Specs" Requirement).

This archive spec delta was edited to <a id="req-35"> for grep consistency with live spec; the original req-34 anchor identity is preserved in this annotation block per archive corrective change fix-archive-ground-cg-n-eq-1-test-stale-anchor (2026-09-24, parent pattern from fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian Decision 2).

Mirrors the ticket-side `(historical, ...; superseded by ...)` annotation pattern from `wayfinder/tickets/A8-2.md` L70 + L74 (per `governance/spec.md` req-gov-2 "Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application").
-->

# wayfinder Specification (delta)

## ADDED Requirements

<a id="req-35"></a>
### Requirement: CG n=1 boundary behavior

The `CG = ‖∇_{W^{K, V, b}} L_total‖₂` metric MUST satisfy the L2-norm identity at the `n=1` boundary: for any single-element gradient tensor `g` with `‖g‖₂ = |g.item()|`. When `g.numel() == 1`, the metric MUST return `abs(g.item())` (no special-case branch — the L2 norm definition handles it directly). The behavior is dimension-agnostic: `g` may be 1D, 2D, or N-D so long as `g.numel() == 1`.

**Source:** `wayfinder/tickets/A8-2.md` (Eight Metrics design lineage — `CG = ‖∇_{W^{K, V, b}} L_total‖₂` defined as debug-only stability probe in the Eight Metrics table); `openspec/specs/wayfinder/spec.md` Req 20 (CG) (parent requirement anchor — the top-level Eight Metrics definition the new boundary Scenarios extend); `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` (assertion anchor — closed-form L2-norm guard for `numel()==1` inputs covering 1D and multi-dim); `CLAUDE.md §2` 真相源层级 (`spec > wayfinder > code` — 想修改 DecompMoE 行为,先改 OpenSpec spec); `/code-review max` LOW 7 (audit trigger — CRIT-3 fix in `change 2026-09-05-fix-metrics-cg-closed-form` silently changed CG behavior at `n=1` from `0.0` mean-pairwise to `abs(value)` L2 norm; the new behavior is mathematically correct but the boundary was never documented in the active spec).

#### Scenario: CG n=1 positive value
- **WHEN** `CG(torch.tensor([5.0]))` is called with a single-element positive 1D tensor
- **THEN** the result equals `5.0` exactly within `abs=1e-12` (L2 norm of `[5.0]` is `5.0`)

#### Scenario: CG n=1 negative value
- **WHEN** `CG(torch.tensor([-5.0]))` is called with a single-element negative 1D tensor
- **THEN** the result equals `5.0` exactly within `abs=1e-12` (L2 norm is magnitude-invariant)

#### Scenario: CG n=1 zero value
- **WHEN** `CG(torch.tensor([0.0]))` is called with a single-element zero 1D tensor
- **THEN** the result equals `0.0` exactly within `abs=1e-12` (L2 norm of `[0.0]` is `0.0`)

#### Scenario: CG n=1 multi-dim numel==1
- **WHEN** `CG(torch.tensor([[5.0]]))` or `CG(torch.tensor([[[-5.0]]]))` is called with a multi-dimensional tensor whose `numel()` equals `1`
- **THEN** the result equals the absolute value of the sole element (`5.0` or `-5.0` → `5.0`) exactly within `abs=1e-12` (L2 norm is dimension-agnostic when `numel()==1`)