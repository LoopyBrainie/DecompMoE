## ADDED Requirements

### Requirement: Eight Geometric Quantification Metrics — Ticket A8-2 L70/L74 Supersede Annotation Closure

The system SHALL maintain the existing spec Requirement **"Eight Geometric Quantification Metrics"** (`openspec/specs/wayfinder/spec.md` L394-466, anchored `<a id="req-20"></a>`) — specifically the `MCI` row at L413 — as the **钉死真相源** (canonical truth source) for the closed-form `uncentered second moment` definition that supersedes the historical centered-covariance and CV/convex-hull-radius readings. This change does NOT modify the spec Requirement; it documents that the spec's existing supersede annotation (via L413 Reason narrative + L416 Source field) is the canonical reference against which ticket-side and audit-side supersede annotations MUST be aligned.

**Spec L413 verbatim closed-form (钉死真相源, unchanged by this change)**:

> `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / \|T\|) · Σ_{t ∈ T} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`) | effective-dimensionality fraction; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `\|T\| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range); `MCI = 1.0` when `M` is proportional to identity (uniform token-distribution across the `d_c` basis), `MCI = 1/d_c` when `M` is rank-1

**Spec L416 Source verbatim (3 反链齐, unchanged by this change)**:

> **Source:** `wayfinder/tickets/A8-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 8), change `fix-math-consistency-audit-2026-08` design.md (Decision 5)

**Spec Scenarios verbatim (uncentered 闭式两端守护, unchanged by this change)**:

- L450 `MCI closed-form on uniform token distribution` — abs=1e-12 守护 `MCI = 1.0` upper endpoint
- L454 `MCI closed-form on rank-1 token distribution` — abs=1e-12 守护 `MCI = 1/d_c` lower endpoint

**Ticket-side supersede annotations (this change, additive, NOT spec modifications)**:

- `wayfinder/tickets/A8-2.md` L70 (`λ_j = C 分布协方差矩阵的特征值`) — italic `(historical, centered-covariance reading; superseded by spec req-20 L413 uncentered second moment ...)` annotation appended; **original stale数字 verbatim retained**
- `wayfinder/tickets/A8-2.md` L74 (`**关键修正**：原 CV（C 分布凸包半径）在 S^{d_c-1} 下界为 1/d_c = 0.0625（健康值不可达），故替换`) — italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 L413 uncentered second moment ...)` annotation appended; **original stale数字 verbatim retained**

**Source:** `wayfinder/tickets/A8-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 8), change `fix-math-consistency-audit-2026-08` design.md (Decision 5)

#### Scenario: Spec L413 is the unchanging canonical closed-form for MCI

- **WHEN** `MCI(token_signatures)` is called from `src/decompmoe/metrics.py` per spec L413 closed form
- **THEN** the implementation uses `M = (1/|T|) · Σ C_t C_tᵀ` uncentered second moment verbatim (NOT centered covariance, NOT convex hull radius), with eigenvalues `λ_j` extracted from `M`, normalized to `λ̃_j = λ_j / Σ_r λ_r`, and the result is `1 / (d_c · Σ λ̃_j²)` — all per spec L413 verbatim (no drift)
- **AND** the result lies in `MCI ∈ [1/d_c, 1]` closed range, with both endpoints attainable (uniform distribution ⇒ `MCI = 1.0`; rank-1 distribution ⇒ `MCI = 1/d_c`)
- **AND** the spec text at `openspec/specs/wayfinder/spec.md` L413 verbatim contains the uncentered second moment closed form AND the L413 Reason supersede narrative AND the L413 Range `MCI ∈ [1/d_c, 1]` AND the L416 Source 3-反链 — all unchanged by this change

#### Scenario: Ticket A8-2 L70 historical supersede annotation preserved

- **WHEN** `wayfinder/tickets/A8-2.md` L70 is read for the `λ_j = C 分布协方差矩阵的特征值` historical definition attempt
- **THEN** the line preserves the original `λ_j = C 分布协方差矩阵的特征值` text AND a subsequent italic annotation `(historical, centered-covariance reading; superseded by spec req-20 L413 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — centered reading has (1/d_c, 1] upper endpoint unreachable at |T| = d_c)` follows immediately (the original stale定义 is retained for ticket lineage traceability; supersede annotation tells future readers that the定义 is historical, not current spec truth)

#### Scenario: Ticket A8-2 L74 historical supersede annotation preserved

- **WHEN** `wayfinder/tickets/A8-2.md` L74 is read for the `原 CV（C 分布凸包半径）` historical definition attempt
- **THEN** the line preserves the original `**关键修正**：原 CV（C 分布凸包半径）在 S^{d_c-1} 下界为 1/d_c = 0.0625（健康值不可达），故替换` text AND a subsequent italic annotation `(historical, geometric convex hull radius CV reading; superseded by spec req-20 L413 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — CV lower bound 1/d_c on S^{d_c-1} makes original < 0.05 health target unreachable)` follows immediately (the original stale定义 is retained for ticket lineage traceability; supersede annotation tells future readers that the定义 is historical, not current spec truth)

#### Scenario: Ticket L70 + L74 dual annotations jointly cover spec L413 Reason's dual supersede argument

- **WHEN** both `wayfinder/tickets/A8-2.md` L70 (centered-covariance) and L74 (CV/convex-hull) supersede annotations are read jointly
- **THEN** they jointly cover spec L413 Reason's dual supersede argument verbatim:
  - L70 annotation verbatim cites "centered reading has `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`" (matches spec L413 Reason's centered-covariance clause)
  - L74 annotation verbatim cites "CV lower bound `1/d_c` on `S^{d_c-1}` makes original `< 0.05` health target unreachable" (matches spec L413 Reason's CV/convex-hull clause)
  - both annotations reference the **same** supersession target: "spec req-20 L413 uncentered second moment" with the **same** chain of authority: "fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5"
- **AND** the joint coverage forms a complete reverse-absorption chain: spec L413 Reason (钉死真相) → ticket L70 + L74 (历史 lineage) → audit `.audit/spec-math-audit.md` L524 evidence段 (审计 trail)