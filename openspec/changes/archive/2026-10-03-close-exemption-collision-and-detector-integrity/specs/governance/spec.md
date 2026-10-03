# Spec Delta — `governance`

## MODIFIED Requirements

<a id="req-gov-3"></a>

### Requirement: Loop Severity Framework Gap Closure

The system MUST close two severity-framework gaps observed in the DecompMoE audit-verification loop (per `.audit/audit-verification/audit-verification.md` 9 meta-发现清单 #6 severity 误标 pattern + #8 dormant bug framework gap, both surfaced after verify-30 三轴收官 2026-09-19): (a) the current `LOOPS.md` severity framework is **pure reactive** — only upgrading to HIGH when finding has already infected `src/`, leaving dormant bugs (0 active impact but high latent risk × trigger probability) unaddressed; (b) the audit-verification loop has a **default-MEDIUM inertia** bias — when finding text already contains explicit severity keywords (`低危`/`正面记录`/`不构成硬冲突`), audit-verification verdicts still tend to use MEDIUM rather than adopting the finding's self-graded severity.

Concrete obligations:

1. **Dormant bug escalation trigger** — if a finding's `latent_risk ∈ {MEDIUM, HIGH}` OR `trigger_probability ∈ {MEDIUM, HIGH}` (either-dimension rule, per independent-dimension criterion), the audit-verification verdict severity MUST escalate to `HIGH dormant-bug`, even when the current functional impact is 0. The dormant-bug classification is **proactive risk management**, distinct from the reactive HIGH-upgrade rule (which requires "已传染 src/"); the two rules coexist and are applied independently.

   - `latent_risk ∈ {LOW, MEDIUM, HIGH}` evaluation criteria:
     - `LOW` — finding stale value not currently in any foreseeable code path (e.g. doc-level only)
     - `MEDIUM` — finding stale value will affect a deferred feature with limited blast radius (e.g. optional debug metric, optional aux loss)
     - `HIGH` — finding stale value will cause fatal error or 10x+ performance regression if the deferred feature is implemented (e.g. 48 orphan clusters, NaN propagation, security bug)
   - `trigger_probability ∈ {LOW, MEDIUM, HIGH}` evaluation criteria:
     - `LOW` — finding stale value lives in an unused stub / never-read dead code / explicitly-archived ticket
     - `MEDIUM` — finding stale value lives in a ticket that may be read for related-but-not-immediate work
     - `HIGH` — finding stale value lives in the ONLY explicit spec for a deferred feature that the next implementer will read first
   - **Escalation rule**: severity up to `HIGH dormant-bug` ⟺ `latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}` (either-dimension rule — conservative, max coverage). When both dimensions are `LOW`, finding retains its current MEDIUM (no escalation).

2. **Audit self-correction (reading-finding-text-first rule)** — before the audit-verification loop decides verdict severity in axis-γ 复核, the loop MUST first grep the finding text against the keyword set `{"低危", "正面记录", "正面alignment", "不构成硬冲突", "phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}`. If any keyword matches, the loop MUST adopt the finding's self-graded severity:
   - `{"低危", "不构成硬冲突"}` → verdict-LOW
   - `{"正面记录", "正面alignment"}` → verdict-INFO
   - `{"phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}` → trigger dormant-bug assessment (per obligation 1)

   The verdict text MUST cite which keyword triggered the auto-adoption (e.g. `finding-keyword "低危文字漂移" → verdict-LOW`). The loop MUST NOT default to MEDIUM if finding-text-explicit severity is detectable from keywords. This rule is **preventive** (applied before default-MEDIUM inertia kicks in), not post-hoc.

3. **Verdict embedding obligation** — every audit-verification verdict MUST embed in its severity-decision text the form `finding-keyword "<kw>" × finding-text-self-grade "<grade>" ⇒ verdict-<severity>` (e.g. `finding-keyword "低危文字漂移" × finding-text-self-grade "LOW" ⇒ verdict-LOW`; for dormant-bug case, `finding-keyword "NOT IMPLEMENTED" × latent_risk "HIGH (48 orphan clusters fatal)" × trigger_probability "HIGH (any Phase 0 reader reads ticket L100)" ⇒ verdict-HIGH dormant-bug`). The embedded form is the audit trail that the rule was honored.

4. **`LOOPS.md` reference binding** — `LOOPS.md` §DecompMoE audit-verification loop "Cycle 单元"段 axis-γ 子段 and §DecompMoE spec-math audit loop "Finding 升格路径"段 MUST each reference this Requirement as the single source of truth for the dormant-bug escalation and audit self-correction clauses. `LOOPS.md` MUST NOT restate the rule in different wording (drift risk); instead it cites this Requirement by capability path (`governance/spec.md` req `Loop Severity Framework Gap Closure`) and Scenario ID.

5. **LOOPS.md version-control prerequisite** — any `LOOPS.md` surgical edit MUST operate on a `LOOPS.md` that is tracked in the repository's git history (not untracked). The change that first adds new content to `LOOPS.md` MUST split into two commits: (i) `chore(audit): import LOOPS.md to version control` (pure import with no content change), then (ii) the substantive edit commit. This prerequisite ensures the audit-verification loop has stable anchors when grepping `LOOPS.md` line numbers in future cycles.

**Source:** `CLAUDE.md` §3 (LOOPS.md is a project-level process doc parallel to `CLAUDE.md`, both governance-origin); `CLAUDE.md` §2 (truth-source hierarchy — spec > doc > code, so process rules live in spec not in LOOPS.md); change `08-fix-loops-md-dormant-bug-framework` design.md (Decision 1 — closed-form dormant-bug risk function `latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}` ⇒ HIGH dormant-bug; Decision 2 — reading-finding-text-first rule). Test anchors unchanged from the meta-finding surface (in `.audit/audit-verification/audit-verification.md` `verify-30` 三轴收官 evidence): meta-06 (severity 误标 pattern, 2/24 = 8.3% 误标率, verify-21 + verify-24 实证 cycle-17 INFO + cycle-1 LOW 双误标); meta-08 (dormant bug framework gap, verify-18 实证 cycle-13 latent_risk=HIGH × trigger_probability=HIGH ⇒ dormant-bug, 原话建议 L1358-1359 "建议 LOOPS.md 修订: 在 LOOPS.md severity 框架中加 dormant bug 升级条款"); cycle-5 retro-application as no-op boundary case (L1349 latent_risk=LOW + spec 已 supersede ⇒ MEDIUM retained); cycle-17 finding-keyword "正面记录" → verdict-INFO (L1542); cycle-1 finding-keyword "低危文字漂移" → verdict-LOW (cycle-1 finding-1 record); `LOOPS.md` "Finding 升格路径" 段 (scope of LOOPS-B edit); `LOOPS.md` "audit-verification loop axis-γ" 子段 (scope of LOOPS-A edit); `LOOPS.md` "修改记录" 段 (scope of LOOPS-C edit); `openspec/specs/wayfinder/spec.md` req-34 "governance-origin requirements trigger lint failure" Scenario (governance-migration justification for this Requirement living in `governance/spec.md` not `wayfinder/spec.md`); `openspec/specs/governance/spec.md` req-gov-1 (Test Guard Precision for Closed-Form Numerical Claims — design precedent for governance-origin Requirement); `openspec/specs/governance/spec.md` req-gov-2 (Ticket `(historical, ...)` supersede annotation pattern — pre-existing meta Requirement, NOT modified by this delta; `req-gov-3` chosen to avoid anchor collision).

> **Note**: The `LOOPS.md` line ranges (L64-69, L118-122, L178-198) reference **pre-edit** positions; post this change's surgical edits, those sections shift to L64-70 (Finding 升格路径 +1 bullet for dormant bug 升级条款), L118-124 (axis-γ 子段 +1 line for Reading finding text first rule + 1 line for dormant bug HIGH bullet), L180-201 (修改记录段 + 1 entry). Future readers using these references should `git log --follow LOOPS.md` for line-range history.

#### Scenario: Dormant bug latent risk × trigger probability escalates to HIGH

- **WHEN** an audit-verification loop's axis-γ 复核 finds that a finding satisfies the dormant-bug risk function (`latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}`, the either-dimension rule)
- **THEN** the audit-verification verdict severity MUST escalate to `HIGH dormant-bug`, distinct from the reactive HIGH (传染 src/) upgrade
- **AND** the verdict MUST cite both `latent_risk` value and `trigger_probability` value explicitly with reasoning (e.g. `latent_risk=HIGH (48 orphan clusters fatal if Phase 0 implemented) × trigger_probability=HIGH (any future Phase 0 reader reads ticket `wayfinder/tickets/A6b-1.md`) ⇒ HIGH dormant-bug`)
- **AND** the cited reasoning MUST be retrievable from the finding's own evidence section (no external reference required); the audit trail is self-contained
- **AND** when both `latent_risk` and `trigger_probability` are `LOW`, finding retains its current MEDIUM (no escalation); this case is the no-op boundary that distinguishes dormant-bug from ordinary stale-finding
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` cycle-13 finding 1 (verify-18 evidence L1316-1322): `latent_risk=HIGH` (48 orphan clusters fatal if Phase 0 implemented) × `trigger_probability=HIGH` (any future Phase 0 reader reads ticket `A6b-1.md` "各阶段详细动作" 段) ⇒ dormant-bug HIGH upgrade (was MEDIUM borderline + dormant bug 标注 pre-this-change, becomes HIGH dormant-bug post-this-change)
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` historical cycle-5 finding 1 (verify-18 evidence L1349): `latent_risk=LOW` (spec 已 supersede) × `trigger_probability=LOW` (ticket 已 deprecated for forward Phase 0 — **inferred**; source L1349 comparison table has only `finding / 当前 impact / latent risk / severity 评级` 4 columns and **no `trigger_probability` column**; inference: cycle-5 stale claim is doc-level θ_Voronoi drift (52° vs 67.24°) per the table's "低 (spec 已 supersede)" annotation, AND cycle-5 ticket has been superseded by spec req-1 L184-L185 verbatim (verify-2 axis-β CITE-OK×4 records this supersede), so trigger_probability meets the LOW criterion "explicitly-archived ticket" from this Requirement's obligation 1 evaluation criteria — cross-referenced from cycle-13 evidence base showing the same author flagged `trigger_probability` as inferable from spec/ticket state) ⇒ MEDIUM retained (no dormant-bug escalation); cycle-5 is the no-op boundary case

#### Scenario: Audit self-correction reads finding-text-explicit severity before defaulting to MEDIUM

- **WHEN** audit-verification axis-γ 复核 begins for any finding
- **THEN** the loop MUST grep finding text against the keyword set `{"低危", "正面记录", "正面alignment", "不构成硬冲突", "phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}` BEFORE deciding verdict severity (preventive step)
- **AND** if `{"低危", "不构成硬冲突"}` matches, the verdict MUST adopt `LOW` (not MEDIUM)
- **AND** if `{"正面记录", "正面alignment"}` matches, the verdict MUST adopt `INFO` (not MEDIUM)
- **AND** if `{"phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}` matches, the verdict MUST trigger dormant-bug assessment per Scenario above (not direct MEDIUM)
- **AND** the verdict text MUST cite which keyword triggered the auto-adoption (e.g. `finding-keyword "低危文字漂移" → verdict-LOW`; `finding-keyword "正面记录" → verdict-INFO`; `finding-keyword "NOT IMPLEMENTED" → trigger dormant-bug assessment`)
- **AND** the loop MUST NOT default to MEDIUM if finding-text-explicit severity is detectable from keywords (preventive override)
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` cycle-17 finding 1 (verify-21 evidence L1534-1564): finding text contains `正面记录` + `alignment 完美` ⇒ verdict MUST be INFO (was MEDIUM 误标 pre-this-change, becomes INFO post-this-change via finding-keyword "正面记录" auto-adoption)
- **AND** the scenario is verified by retro-application to `.audit/audit-verification/audit-verification.md` cycle-1 finding 1 (verify-24 evidence L1795-1813): finding text contains `不构成硬冲突` + `低危文字漂移` ⇒ verdict MUST be LOW (was MEDIUM 误标 pre-this-change, becomes LOW post-this-change via finding-keyword "低危文字漂移" auto-adoption)
- **AND** the scenario's mislabeling-rate target is 0% (was 8.3% = 2/24 pre-this-change, per verify-21 + verify-24 evidence); future audit-verification loops MUST track this metric and any regression to >0% indicates reading-finding-text-first rule violation


<a id="req-gov-4"></a>

### Requirement: Ticket Advisory Boundary — Stale Contamination Monitoring

The advisory status of `wayfinder/tickets/*.md` (per `CLAUDE.md` §8 "2026-08-21 裁决") SHALL NOT be interpreted as "ticket stale has no operational impact". Specifically:

1. **Advisory non-binding scope** — tickets MAY be superseded by OpenSpec changes without amending the ticket itself; this is the ONLY meaning of "advisory". The advisory scope covers ticket-edit policy (whether ticket text may diverge from spec) and does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`.

2. **Operational impact** — ticket stale values MAY propagate to `src/` via three empirically-observed channels: (i) MVPConfig default values copied directly from ticket numbers (per `commit adf41ef` 2026-09-19 history: `MVPConfig.beta_initial = 1.0` was originally sourced from `wayfinder/tickets/A4-1.md` `β_0 ≈ 1.0`; closed by `commit adf41ef` migrating to spec closed-form `0.1 + 31.9 · Sigmoid(γ_init)`); (ii) tests `assert MVPConfig().field == stale_value` LOCKS the propagation (per `commit adf41ef` history: `tests/test_beta.py::test_beta_param_init_default` originally had `assert MVPConfig().beta_initial == 1.0`; closed by migration to `pytest.approx(expected, abs=1e-3)` deriving expected from spec closed form); (iii) any implementation reading ticket directly without consulting spec reproduces stale values (cycle-9 worst-case: ticket `A6a-2.md` `f_i^avg < 1/128` historical vs spec `1 / (2 · N_e)` parameterized form, the `src/` boundary now uses spec parameterization per `src/decompmoe/safeguards.py::_dead_expert_threshold` `_dead_expert_threshold(N_e) = 1.0 / (2.0 * N_e)`).

3. **Monitoring obligation** — `.audit/audit-verification.md` MUST periodically verify the ticket ↔ spec ↔ src triangle for drift propagation. The empirical evidence base (cycle-9 ticket-stale pattern + remaining MEDIUM finding family across multiple cycles) establishes that "ticket-stale → src-pollution" is a recurring pattern requiring active monitoring, NOT a passive advisory. A "传染链已断" verdict (the spec is the truth source and the stale propagation has been interrupted at the `src/` boundary) does NOT exempt the project from this monitoring obligation — recurrence remains possible whenever a new contributor reads a ticket without consulting the corresponding spec.

4. **Drift remediation protocol** — when ticket stale is detected propagating to `src/`: (a) ticket MUST receive a `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` annotation preserving the decision chain (canonical form per `openspec/specs/wayfinder/spec.md` req-34 "Source Field Format Invariant for OpenSpec Specs" Scenario "every Source field contains a wayfinder ticket reference"; the line-addressed `req-N L###` variant is legacy and MUST NOT be newly written); (b) `src/` default values MUST be updated to spec canonical values; (c) tests using `assert == stale_value` MUST migrate to `pytest.approx(spec_value, abs=...)` per `CLAUDE.md` §6 第 8 条 float closed-form convention (formalized by `req-gov-1`).

**Source:** `CLAUDE.md` §8 (cycle-7 audit-verification meta-洞察 boundary clarification, amended by this change)

#### Scenario: ticket advisory scope is bounded to ticket-edit policy

- **WHEN** a developer reads `CLAUDE.md` §8 "ticket 仅作历史决策记录（参考性、非约束性）" together with this Requirement's clause (1)
- **THEN** the advisory interpretation MUST be limited to ticket-edit policy (whether `wayfinder/tickets/*.md` text may diverge from spec), and MUST NOT be extended to claims that ticket-side numerical values have no downstream effect on `src/` or `tests/`

#### Scenario: three contamination channels are independently verifiable

- **WHEN** audit-verification loop checks ticket ↔ spec ↔ src triangle for drift propagation (per clause (3) monitoring obligation)
- **THEN** the three contamination channels enumerated in clause (2) — (i) MVPConfig default values copied from ticket, (ii) tests `assert == stale_value` LOCKS, (iii) reader-ticket-not-spec reproductions — MUST each be independently verifiable by (a) `grep` of MVPConfig dataclass fields against ticket numerical claims, (b) `grep` of `assert MVPConfig().field ==` patterns in `tests/`, (c) absence of canonical-API guards in any module reading ticket-derived constants directly

#### Scenario: drift remediation protocol enforces three-step closure

- **WHEN** a ticket-stale finding is detected propagating to `src/` (per audit-verification three-axis verdict or independent reviewer)
- **THEN** closure of that finding MUST execute the three steps enumerated in clause (4) — (a) ticket `(historical, ...)` annotation, (b) `src/` default value update, (c) tests `pytest.approx` migration — in that order, and a partial closure (e.g., step (a) without (b) and (c)) MUST NOT be considered a fully-closed finding under this Requirement
