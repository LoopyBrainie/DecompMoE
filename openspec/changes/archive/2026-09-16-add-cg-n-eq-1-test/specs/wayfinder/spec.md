# wayfinder Specification (delta)

## ADDED Requirements

<a id="req-34"></a>
### Requirement: CG n=1 boundary behavior

The `CG = ‖∇_{W^{K, V, b}} L_total‖₂` metric MUST satisfy the L2-norm identity at the `n=1` boundary: for any single-element gradient tensor `g` with `‖g‖₂ = |g.item()|`. When `g.numel() == 1`, the metric MUST return `abs(g.item())` (no special-case branch — the L2 norm definition handles it directly). The behavior is dimension-agnostic: `g` may be 1D, 2D, or N-D so long as `g.numel() == 1`.

**Source:** `wayfinder/tickets/A8-2.md` (Eight Metrics design lineage — `CG = ‖∇_{W^{K, V, b}} L_total‖₂` defined as debug-only stability probe in the Eight Metrics table); `openspec/specs/wayfinder/spec.md` Req 20 (CG) (parent requirement anchor — the top-level Eight Metrics definition the new boundary Scenarios extend); `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` (assertion anchor — closed-form L2-norm guard for `numel()==1` inputs covering 1D and multi-dim); `CLAUDE.md §2` 真相源层级 (`spec > wayfinder > code` — 想修改 DecompMoE 行为,先改 OpenSpec spec); `/code-review max` LOW 7 (audit trigger — CRIT-3 fix in `change 2026-09-05-fix-metrics-cg-closed-form` silently changed CG behavior at `n=1` from `0.0` mean-pairwise to `abs(value)` L2 norm; the new behavior is mathematically correct but the boundary was never documented in the active spec).

#### Scenario: CG n=1 positive value
- **WHEN** `CG(torch.tensor([5.0]))` is called with a single-element positive tensor
- **THEN** the result equals `5.0` exactly within `abs=1e-12` (L2 norm of `[5.0]` is `5.0`)

#### Scenario: CG n=1 negative value
- **WHEN** `CG(torch.tensor([-5.0]))` is called with a single-element negative tensor
- **THEN** the result equals `5.0` exactly within `abs=1e-12` (L2 norm is magnitude-invariant)

#### Scenario: CG n=1 zero value
- **WHEN** `CG(torch.tensor([0.0]))` is called with a single-element zero tensor
- **THEN** the result equals `0.0` exactly within `abs=1e-12` (L2 norm of `[0.0]` is `0.0`)
