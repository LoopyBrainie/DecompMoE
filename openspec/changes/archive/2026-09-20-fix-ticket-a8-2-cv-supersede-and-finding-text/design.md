## Context

cycle-12 finding #1 from `.audit/spec-math-audit.md` L524 (MEDIUM severity) reached **PARTIALLY-VERIFIED** verdict after the audit-verification loop's three-axis review (`.audit/audit-verification.md` L899-L1137). The user selected **Option A** (recommended): accept a finding-text 微调 (`协方差矩阵` → `centered covariance + CV (凸包半径)`, precise two-line distinction) and ticket A8-2 L70 + L74 supersede annotation. This design covers the HOW for closing the finding under Option A — the WHY is in `proposal.md`, and the spec-level contract is in `specs/*/spec.md`.

The central mathematical observation (proven independently by `verify-13 axis-α` with numpy linear algebra + mpmath 30-digit precision + rank-reduction-by-centering mathematical proof):

- **centered covariance** reading `M_centered = (1/|T|) Σ (C_t − μ)(C_t − μ)ᵀ` has `rank(M_centered) ≤ d_c − 1` when `|T| = d_c` (centering subtracts one degree of freedom), so the upper endpoint `MCI = 1` is **unreachable**
- **CV (convex hull radius)** reading has lower bound `1/d_c = 0.0625` on `S^{d_c-1}`, so the original `< 0.05` health target is **unreachable**
- **uncentered second moment** reading `M = (1/|T|) Σ C_t C_tᵀ` has `rank(M) ≤ min(|T|, d_c)`, achievable at both endpoints (`MCI = 1.0` uniform; `MCI = 1/d_c` rank-1), so `MCI ∈ [1/d_c, 1]` closed range with both endpoints attainable

Spec `openspec/specs/wayfinder/spec.md` L413 is already the canonical uncentered second moment reading; spec L413 Reason narrative already supersedes CV (lower bound on `S^{d_c-1}`) + centered covariance (upper endpoint unreachable at `|T| = d_c`) explicitly. Spec L416 Source 3-反链齐 (`wayfinder/tickets/A8-2.md` + `fix-openspec-doc-bugs` Decision 8 + `fix-math-consistency-audit-2026-08` Decision 5). Spec L450/L454 Scenarios (`MCI closed-form on uniform token distribution` + `MCI closed-form on rank-1 token distribution`) use `abs=1e-12` to guard both endpoints. The **only** stale ends are the ticket-side definitions at `wayfinder/tickets/A8-2.md` L70 + L74 (no supersede annotation) and the audit-side narrative in `.audit/spec-math-audit.md` L524 (finding CITE-MISALIGNED on ticket L74) + `.audit/audit-verification.md` L1092 (`FLAWED: ticket-A8-2-L74 转述` marker).

## Goals / Non-Goals

**Goals:**

- Close cycle-12 finding #1 (MEDIUM) per Option A: ticket A8-2 L70 + L74 supersede annotation (append-only, do not delete) + `.audit/spec-math-audit.md` L524 finding-text 微调 + `.audit/audit-verification.md` verify-15 verdict FLAWED cleanup + finding-status promote (PARTIALLY-VERIFIED → fully-verified)
- Do not modify `openspec/specs/wayfinder/spec.md` L413 closed-form (already canonical truth source) — single source of truth + ticket reverse-absorption (mirror spec L413 Reason + L416 Source form)
- Maintain CLAUDE.md §6 hard constraints: no new CUDA/Triton kernel, no `C_t` in KV cache, no shared expert, no `w_i` in logit, no training/baseline run, all closed-form numerical claims continue to use `pytest.approx(..., abs=...)` (float) or bare `==` (integer) per CLAUDE.md §6 第 8 条 integer-vs-float binary exemption (formalized by `req-gov-1`)
- 0 files `src/` changed, 0 files `tests/` changed, 0 files spec Requirement changed (the 3 ADDED meta-Requirements in `specs/*/spec.md` are documenting-only — they declare the spec不变 state, they do not modify spec behavior)
- Existing 193 tests remain green (spec/code/test triangle unchanged)

**Non-Goals:**

- Do not modify `openspec/specs/wayfinder/spec.md` (any spec Requirement, including the new documenting-only ADDED meta-Requirement itself) — spec is already钉死真相源
- Do not modify `openspec/specs/decompmoe-skeleton/spec.md` (any spec Requirement) — its `req-22` (L500-518) already verbatim mirrors wayfinder Req 20 closed-forms including the MCI uncentered second moment reading; the mirror is aligned
- Do not modify `openspec/specs/governance/spec.md` (any existing req-gov-N) — existing `req-gov-1` (L7-L23 with anchor L7 unchanged) covers the integer-vs-float assertion-form discipline; this change's ticket `(historical, ...)` annotation pattern is a CLAUDE.md §3 source-field rules application, not a new governance Requirement. The planned `09-fix-claude-md-ticket-advisory-boundary` (currently a `.audit/.../opsx-changes/` planning draft, NOT yet proposed/applied/archived) is a separate future change that *would* introduce `req-gov-2` when archived; this change does NOT depend on `09` being live
- Do not modify `src/decompmoe/metrics.py` `MCI(token_signatures)` implementation (already spec-aligned)
- Do not modify `tests/test_metrics.py` `test_mci_closed_form_*` (already spec-aligned)
- Do not rewrite ticket A8-2 content (only append supersede annotation, lineage preserved)
- Do not touch other wayfinder tickets (A8-1, A8-3, A6a-2, A4-1, A5-3, A6b-1, etc.)
- Do not introduce custom CUDA/Triton kernel
- Do not put `C_t` in KV cache
- Do not introduce shared expert
- Do not use `w_i` in logit

## Decisions

### Decision 1: ticket-side fix direction — append-only supersede annotation (L70 + L74) rather than delete-and-replace

**Choice**: Append italic `(historical, centered-covariance reading; superseded by spec req-20 L413 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — centered reading has (1/d_c, 1] upper endpoint unreachable at |T| = d_c)` to `wayfinder/tickets/A8-2.md` L70 after the existing `λ_j = C 分布协方差矩阵的特征值` text; append italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 L413 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — CV lower bound 1/d_c on S^{d_c-1} makes original < 0.05 health target unreachable)` to L74 after the existing `**关键修正**：原 CV（C 分布凸包半径）在 S^{d_c-1} 下界为 1/d_c = 0.0625（健康值不可达），故替换` text. **Both annotations verbatim reference spec L413 Reason + L416 Source field canonical form**.

**Rationale**: Reuse the spec-end canonical format already established by `openspec/specs/wayfinder/spec.md` L413 Reason (CV supersede) + L413 Reason (centered-covariance supersede) + L416 Source (`wayfinder/tickets/A8-2.md` + `fix-openspec-doc-bugs` Decision 8 + `fix-math-consistency-audit-2026-08` Decision 5). Deleting the original stale values would destroy the ticket's decision trail (reader cannot trace why the historical centered-covariance + CV/convex-hull definitions were originally attempted), and the spec does not consume ticket-side numerical values (the spec is a closed-form truth source), so the stale values pose no runtime risk — only the supersede annotation needs to be added so future readers know the stale numbers are historical definition attempts, not current spec truth.

**Why dual annotation (L70 + L74) rather than single annotation (L74 only)**:

- ticket L70 holds the centered-covariance reading (statistical 量)
- ticket L74 holds the CV/convex hull radius reading (geometric 量)
- these are **different mathematical quantities** (statistical covariance vs geometric convex hull radius), and spec L413 Reason **supersedes both** in dual argument form ("replaces CV..." + "centered-covariance reading...")
- therefore L70 + L74 must each receive an independent annotation, reflecting the different mathematical defects (centered is upper endpoint unreachable, CV is lower endpoint unreachable)
- the dual annotation aligns verbatim with spec L413 Reason, forming a complete spec/ticket supersede chain

**Alternatives considered**:

- (a) Annotate only L74 (CV supersede), leave L70 (centered-covariance supersede) unannotated — rejected: L70 remains a stale end (spec L413 Reason explicitly supersedes centered-covariance); a single annotation cannot fully cover the spec supersede chain
- (b) Delete the original stale values and replace with `λ_j = uncentered second moment ...` — rejected: destroys the ticket's historical decision trail; ticket is advisory non-binding (CLAUDE.md §8 裁决) and there is no need to rewrite history
- (c) Leave ticket untouched, modify spec — rejected: spec is already uncentered second moment truth, ticket staleness is not a spec-side problem
- (d) Discard the entire ticket — rejected: ticket is advisory reference material, discard exceeds scope (CLAUDE.md §3 surgical principle)

### Decision 2: audit-side finding-text 微调 direction — evidence sub-段 precise two-line distinction, finding主体不动

**Choice**: `.audit/spec-math-audit.md` L524 cycle-12 finding 1 evidence 段 微调 (finding title `【MEDIUM】ticket A8-2 L74 MCI 定义 stale (covariance → uncentered second moment)` is **unchanged** — the title serves as the cross-finding reference identifier per `.audit/audit-verification.md` L1371 audit-trail-table; only the evidence sub-段 gets the precise two-line distinction):

- "ticket 说 `λ_j = C 分布协方差矩阵的特征值`（centered covariance）" → "ticket L70 说 `λ_j = C 分布协方差矩阵的特征值`（centered covariance, statistical 量）, ticket L74 说 `原 CV（C 分布凸包半径）`（geometric 量）"
- "(spec L413 显式 supersede 到 `λ_j = M = (1/|T|) · Σ C_t C_tᵀ` 的特征值（uncentered second moment）" unchanged
- supersede-reason sub-段 gains: "spec L413 Reason 段双论证：CV 在 `S^{d_c-1}` 下界 `1/d_c` 不可达（健康值目标）+ centered covariance 在 `|T| = d_c` upper endpoint 不可达"
- fix path: "ticket A8-2 L74 改为 `λ_j = uncentered second moment M = (1/|T|) · Σ C C^T 的特征值` + (historical, 协方差矩阵 reading; ...)" → "ticket A8-2 L70 + L74 各加一行 supersede annotation（**仅追加，不删原 stale 数字**）"

**Rationale**: finding主体 (title) is the cross-finding reference identifier (per `.audit/audit-verification.md` L1371 "cycle-12 MEDIUM ticket A8-2 covariance"), changing the title would break all cross-finding reference consistency; the evidence sub-段 is the finding's own narrative description, which can be made precise without abandoning the finding ID. Option A's finding-text 微调 (per user decision) is limited to the evidence sub-段 — the title, severity, and infection-chain status are unchanged.

**Why micro-adjust the evidence sub-段 rather than rewriting it**: the evidence sub-段 is part of the audit trail historical record (per `.audit/audit-verification.md` L1106 rule "CITE-MISALIGNED 不直接改 finding, 标记 FLAWED + 等用户决策"); the 微调 retains the original evidence's trace (an evidence sub-段 footnote "注: 原 evidence 转述 L74 为 '协方差矩阵' 实际为 '凸包半径 CV', 用户选项 A applied 后 finding 文字精确化" serves as audit trail).

**Alternatives considered**:

- (a) Rewrite finding 1 evidence sub-段 completely (delete original text) — rejected: destroys audit trail history; `.audit/audit-verification.md` L1106 rule requires "不直接改 finding, 标记 FLAWED + 等用户决策"; this change is the close of Option A, evidence sub-段 精确化 is part of the close, not a rewrite
- (b) Add a footnote in finding 1 evidence sub-段 explaining the CV vs covariance distinction (Option C path) — rejected: Option A was user-selected for finding-text 微调; the footnote path is conservative but does not fundamentally resolve the issue
- (c) Maintain finding evidence sub-段 original text, finding remains PARTIALLY-VERIFIED status (Option B path) — rejected: Option A was user-selected, finding text-layer description accuracy can be improved, conservative skip is not appropriate

### Decision 3: `.audit/audit-verification.md` verify-15 verdict FLAWED cleanup direction — REMEDIATED marker replace + finding-status promote

**Choice**: `.audit/audit-verification.md` verify-15 verdict sub-段:

- L1092 `FLAWED: ticket-A8-2-L74 转述` marker → replaced with `REMEDIATED via 选项 A finding 文字微调 + ticket A8-2 L70 + L74 supersede annotation per cycle-12 axis-γ follow-up`
- finding status: PARTIALLY-VERIFIED → fully-verified (α+β+γ all three axes OK)
- "下一步" sub-段 update: "cycle-12 finding 1 已 closed（选项 A applied, finding 文字微调 + ticket supersede annotation 合并）; cycle-12 finding 1 = fully-verified"
- audit-trail description retained: "β 轴曾 PARTIAL due to CITE-MISALIGNED on ticket L74, 用户选项 A applied 后 fully-verified"

**Rationale**: verify-15 verdict sub-段 is the audit-trail verdict-status record; the FLAWED marker is the LOOPS.md rule-required mechanism for "不直接改 finding, 标记 FLAWED + 等用户决策". With Option A applied, verdict status upgrades from PARTIALLY-VERIFIED to fully-verified, FLAWED marker is cleaned (NOT deleted — evidence chain retains audit trail), REMEDIATED marker preserves cross-verification traceability.

**Why do not delete the audit trail (verify-13/14 evidence sub-段s)**: verify-13/14 evidence sub-段s are audit-trail historical records (per `.audit/audit-verification.md` L1106 rule); evidence is not rewritten, only verdict status is promoted + FLAWED marker is cleaned.

**Alternatives considered**:

- (a) Completely delete verify-15 verdict sub-段 (along with FLAWED marker) — rejected: destroys audit trail history, violates `.audit/` as audit-evidence-library design
- (b) Maintain verify-15 verdict sub-段 original text (PARTIALLY-VERIFIED status) — rejected: Option A applied leaves status inconsistent; audit trail and verdict status must update together
- (c) Delete verify-15 sub-段 and create a new verify-15.1 Option A applied verdict sub-段 — rejected: audit granularity is too fine, would bloat `.audit/audit-verification.md`; verdict status promote within the original sub-段 is sufficient

### Decision 4: 0 files src/ + 0 files tests/ + 0 spec Requirement 行为 changes

**Choice**: This change does not modify any `src/` file, any `tests/` file, any existing spec Requirement behavior, or any governance existing Requirement behavior. The 3 ADDED meta-Requirements in `specs/*/spec.md` are **documenting-only**: they declare the spec-already-aligned state (wayfinder Req 20 is钉死真相源; decompmoe-skeleton req-22 verbatim mirrors wayfinder Req 20; governance req-gov-1 (L7-L23) + CLAUDE.md §3 source-field rules cover the annotation pattern). They do not introduce any new behavior — they are reverse-absorption declarations of spec/code/test triangle cleanliness.

**Rationale**: per verify-13/14 evidence:

- spec L413 closed-form `uncentered second moment` is钉死真相源 ✓
- spec L413 Reason dual supersede argument (CV + centered covariance) is complete ✓
- spec L416 Source 3-反链齐 ✓
- spec L450 `MCI closed-form on uniform token distribution` abs=1e-12 guard ✓
- spec L454 `MCI closed-form on rank-1 token distribution` abs=1e-12 guard ✓
- `src/` `MCI(token_signatures)` uses spec L413 uncentered reading implementation ✓
- `tests/` `test_mci_closed_form_*` uses spec closed-form abs=1e-12 guard ✓
- MVPConfig / `config.py` / `beta.py` has no MCI-related fields ✓

The **only** stale ends in the infection chain are ticket A8-2 L70 + L74 + audit finding evidence; spec/src/tests three-way clean. This change only does reverse-absorption (ticket + audit align with spec), does not touch spec/src/tests.

**Alternatives considered**:

- (a) Simultaneously modify spec to strengthen spec L413 Reason dual-argument verbatim intensity — rejected: spec L413 Reason is already verbatim complete dual argument ("replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `\|T| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable"), no strengthening needed
- (b) Add spec L413 Reason mathematical derivation explicit sub-段 (rank reduction by centering derivation) — rejected: exceeds scope (CLAUDE.md §3 surgical); spec L413 Reason narrative already covers mathematical conclusions; derivation lives in design.md (this document) + `.audit/audit-verification.md` verify-13 independent recalculation

## Risks / Trade-offs

- **[Risk]** ticket supersede annotation placed at wrong line (L70 vs L74), causing reader to see stale number instead of supersede comment. **Mitigation**: annotation placed **immediately adjacent** to the stale number (same-line trailing), explicitly marked with `(historical, centered-covariance reading)` / `(historical, geometric convex hull radius CV reading)` two distinct phrases; `tasks.md` §C.1 enforces grep verification
- **[Risk]** annotation text drifts from spec L413 Reason (drift between spec/ticket annotation). **Mitigation**: annotation verbatim cites spec L413 Reason text + audit-verification verify-13/14 evidence IDs; `tasks.md` §C.2 enforces character-by-character alignment
- **[Risk]** annotation mislabels ticket as "stale" instead of "historical". **Mitigation**: annotation uses canonical form `(historical, <原值 reading>; superseded by spec req-N L### via <change> Decision M)` (per CLAUDE.md §3 source-field rules formalized pattern), explicitly "原值 retained" rather than "deleted"
- **[Risk]** annotation nested-backtick conflict with ticket L70/L74 trigger description本体 (markdown rendering issue). **Mitigation**: annotation uses outer `*...*` italic wrap, inner `` `uncentered second moment` `` and `` `fix-openspec-doc-bugs` `` backtick-wrapped for formula and change name; markdown parsing is unambiguous
- **[Risk]** after finding-text 微调 cycle-12 finding 1 transitions to fully-verified, but `.audit/audit-verification.md` has already recorded CITE-MISALIGNED history (must preserve evidence chain). **Mitigation**: `.audit/audit-verification.md` verify-15 verdict sub-段 retains audit-trail description ("β 轴曾 PARTIAL due to CITE-MISALIGNED on ticket L74, 用户选项 A applied 后 fully-verified"), evidence is not erased
- **[Risk]** audit files (`.audit/spec-math-audit.md` + `.audit/audit-verification.md`) may not be git-tracked, post-edit may not be recorded. **Mitigation**: per `.audit/README.md` L3, `.audit/` is a temporary evidence library (not git-tracked); this change's audit-text 微调 is **audit-stage evidence correction**, does not enter git permanent documentation, but the OpenSpec change artifacts (`proposal.md` + `tasks.md` + `design.md` + `specs/` at `openspec/changes/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/`) are **permanent plan draft**
- **[Risk]** Windows Edit tool CRLF contamination. **Mitigation**: `tasks.md` §C.5 LF verification enforces `git diff --stat wayfinder/tickets/A8-2.md` validates +2 lines, 0 deletions; `file wayfinder/tickets/A8-2.md` validates LF; if necessary `sed -i 's/\r$//' wayfinder/tickets/A8-2.md`
- **[Risk]** audit finding evidence 微调 后 cross-finding reference breaks (per `.audit/audit-verification.md` L1371 "cycle-12 MEDIUM ticket A8-2 covariance"). **Mitigation**: finding主体 (title `【MEDIUM】ticket A8-2 L74 MCI 定义 stale (covariance → uncentered second moment)`) **unchanged** — retains finding short name for cross-finding reference; evidence sub-段 is the finding's own narrative description, can be made precise without abandoning finding ID
- **[Risk]** governance spec delta references planned-but-not-applied `09-fix-claude-md-ticket-advisory-boundary`, creating a circular dependency perception. **Mitigation**: governance ADDED Requirement explicitly disambiguates: the ticket `(historical, ...)` annotation pattern is a CLAUDE.md §3 source-field rules application, NOT contingent on `09` being live; `09` would introduce `req-gov-2` *if* archived, but this change does not depend on it

## Migration Plan

N/A — no deployment, no rollback, no migration. This change is surgical ticket annotation + audit text 微调. Implementation steps:

1. ticket annotation landing: `wayfinder/tickets/A8-2.md` L70 + L74 each append one-line italic comment (**append-only, no deletion**)
2. audit finding text 微调: `.audit/spec-math-audit.md` L524 cycle-12 finding 1 evidence sub-段 精确化转述 ticket L70 + L74
3. audit verdict state update: `.audit/audit-verification.md` verify-15 verdict sub-段 FLAWED marker → REMEDIATED + finding status promote
4. spec delta不动 for behavior changes (the 3 ADDED meta-Requirements are documenting-only, written into `specs/*/spec.md` at change-scaffold time)
5. `src/` surgical edit不动 (`src/` already spec-aligned)
6. `tests/` modification不动 (`tests/` already spec-aligned)
7. `git diff --stat` validate LF preserved (no CRLF contamination)
8. `python scripts/lint_no_dead_defensive.py` exit=0 + `python scripts/lint_no_source_field_drift.py` exit=0 dual lint gate
9. single commit on `dev`: `fix(ticket,audit): close cycle-12 MEDIUM finding 1 (选项 A) — ticket A8-2 L70 centered-covariance + L74 CV supersede annotation + finding text 微调`

## Open Questions

- **cycle-12 finding 1 fully-verified 后 meta-audit cumulative status update**: cycle-12 finding 1 transitions to fully-verified 后, audit-verification loop meta-audit cumulative count upgrades from "5 fully-verified + 1 partially-verified" to "6 fully-verified + 0 partially-verified". Whether to synchronously update `.audit/audit-verification.md` meta-audit cumulative sub-段s (per L1371 + L2059 + L2291 three locations)? **This change does NOT cover** — meta-audit cumulative sub-段s are audit-loop summary, not in cycle-12 finding 1 direct close scope
- **6-cycle ticket-stale pattern family closure**: this change closes cycle-12 后, 6-cycle ticket-stale pattern family (cycle-5/6/7/9/12/13) completes 5 closure lines (cycle-5/6/7/9/12), the remaining cycle-13 finding 1 (ticket A6b-1 L100 N_e=64) is handled by planned change `04-fix-ticket-a6b-1-n-e-supersede` (per `.audit/audit-verification/opsx-changes/README.md` L43). Whether meta-audit can explicitly point out family 5/6 closure in a verify cycle after cycle-12 closes? **This change does NOT pre-commit**
- **future audit CITE-MISALIGNED finding text 微调 templating**: cycle-12 is audit-verification loop's 1st CITE-MISALIGNED finding (per `.audit/audit-verification.md` L1000 "这是 audit-verification loop 第 1 次 CITE-MISALIGNED verdict!"), Option A is the 1st finding-text 微调 close. Whether to formalize the "Option A pattern" as a LOOPS.md rule? **This change does NOT cover** — this change is cycle-12 finding 1 close, single-change scope
- **ticket annotation and spec Reason dual-source maintenance**: ticket L70 + L74 dual annotation now aligns verbatim with spec L413 Reason. But if spec text evolves in the future, must ticket annotation update synchronously? **Current CLAUDE.md §3 source-field rules already specify future drift fix path**; this change does NOT pre-commit follow-up mechanism strengthening
- **finding evidence sub-段 footnote form**: this Decision Decision 2 mentions "evidence sub-段 add footnote explaining CV vs covariance distinction as audit trail", but `tasks.md` §B1.2 / §B1.3 actually 微调 evidence sub-段 主文 rather than adding footnote — the footnote path is rejected (任务文 markdown 主文 精确化 is sufficient, no extra footnote needed). Whether to add a verbatim footnote in evidence sub-段 "注: 此 evidence sub-段 经 audit-verification cycle-12 axis-β verify-14 CITE-MISALIGNED 复核 后 微调 (选项 A)"? **This change does NOT cover** — `tasks.md` §B1.1 already makes evidence sub-段 精确化 explicit, footnote is optional