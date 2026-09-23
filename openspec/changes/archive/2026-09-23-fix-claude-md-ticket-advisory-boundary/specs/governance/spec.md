# Spec Delta

## ADDED Requirements

<a id="req-gov-4"></a>

### Requirement: Ticket Advisory Boundary — Stale Contamination Monitoring

The advisory status of `wayfinder/tickets/*.md` (per `CLAUDE.md` §8 "2026-08-21 裁决") SHALL NOT be interpreted as "ticket stale has no operational impact". Specifically:

1. **Advisory non-binding scope** — tickets MAY be superseded by OpenSpec changes without amending the ticket itself; this is the ONLY meaning of "advisory". The advisory scope covers ticket-edit policy (whether ticket text may diverge from spec) and does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`.

2. **Operational impact** — ticket stale values MAY propagate to `src/` via three empirically-observed channels: (i) MVPConfig default values copied directly from ticket numbers (per `commit adf41ef` 2026-09-19 history: `MVPConfig.beta_initial = 1.0` was originally sourced from `wayfinder/tickets/A4-1.md` `β_0 ≈ 1.0`; closed by `commit adf41ef` migrating to spec closed-form `0.1 + 31.9 · Sigmoid(γ_init)`); (ii) tests `assert MVPConfig().field == stale_value` LOCKS the propagation (per `commit adf41ef` history: `tests/test_beta.py::test_beta_param_init_default` originally had `assert MVPConfig().beta_initial == 1.0`; closed by migration to `pytest.approx(expected, abs=1e-3)` deriving expected from spec closed form); (iii) any implementation reading ticket directly without consulting spec reproduces stale values (cycle-9 worst-case: ticket `A6a-2.md` `f_i^avg < 1/128` historical vs spec `1 / (2 · N_e)` parameterized form, the `src/` boundary now uses spec parameterization per `src/decompmoe/safeguards.py:34-36` `_dead_expert_threshold(N_e) = 1.0 / (2.0 * N_e)`).

3. **Monitoring obligation** — `.audit/audit-verification.md` MUST periodically verify the ticket ↔ spec ↔ src triangle for drift propagation. The empirical evidence base (cycle-9 ticket-stale pattern + remaining MEDIUM finding family across multiple cycles) establishes that "ticket-stale → src-pollution" is a recurring pattern requiring active monitoring, NOT a passive advisory. A "传染链已断" verdict (the spec is the truth source and the stale propagation has been interrupted at the `src/` boundary) does NOT exempt the project from this monitoring obligation — recurrence remains possible whenever a new contributor reads a ticket without consulting the corresponding spec.

4. **Drift remediation protocol** — when ticket stale is detected propagating to `src/`: (a) ticket MUST receive `(historical, <原值 reading>; superseded by spec req-N L### via <change> Decision M)` annotation preserving the decision chain (canonical form per `openspec/specs/wayfinder/spec.md` req-34 "Source Field Format Invariant for OpenSpec Specs" Scenario "every Source field contains a wayfinder ticket reference"); (b) `src/` default values MUST be updated to spec canonical values; (c) tests using `assert == stale_value` MUST migrate to `pytest.approx(spec_value, abs=...)` per `CLAUDE.md` §6 第 8 条 float closed-form convention (formalized by `req-gov-1`).

**Source:** `CLAUDE.md` §8 (cycle-7 audit-verification L581 meta-洞察 boundary clarification, amended by this change)

#### Scenario: ticket advisory scope is bounded to ticket-edit policy

- **WHEN** a developer reads `CLAUDE.md` §8 "ticket 仅作历史决策记录（参考性、非约束性）" together with this Requirement's clause (1)
- **THEN** the advisory interpretation MUST be limited to ticket-edit policy (whether `wayfinder/tickets/*.md` text may diverge from spec), and MUST NOT be extended to claims that ticket-side numerical values have no downstream effect on `src/` or `tests/`

#### Scenario: three contamination channels are independently verifiable

- **WHEN** audit-verification loop checks ticket ↔ spec ↔ src triangle for drift propagation (per clause (3) monitoring obligation)
- **THEN** the three contamination channels enumerated in clause (2) — (i) MVPConfig default values copied from ticket, (ii) tests `assert == stale_value` LOCKS, (iii) reader-ticket-not-spec reproductions — MUST each be independently verifiable by (a) `grep` of MVPConfig dataclass fields against ticket numerical claims, (b) `grep` of `assert MVPConfig().field ==` patterns in `tests/`, (c) absence of canonical-API guards in any module reading ticket-derived constants directly

#### Scenario: drift remediation protocol enforces three-step closure

- **WHEN** a ticket-stale finding is detected propagating to `src/` (per audit-verification three-axis verdict or independent reviewer)
- **THEN** closure of that finding MUST execute the three steps enumerated in clause (4) — (a) ticket `(historical, ...)` annotation, (b) `src/` default value update, (c) tests `pytest.approx` migration — in that order, and a partial closure (e.g., step (a) without (b) and (c)) MUST NOT be considered a fully-closed finding under this Requirement

Co-Authored-By: Claude Code <noreply@anthropic.com>