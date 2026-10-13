## MODIFIED Requirements

### Requirement: Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application

The system SHALL treat the ticket `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` annotation pattern, when appended to `wayfinder/tickets/A8-2.md` (or any other wayfinder ticket lineage entry), as a **CLAUDE.md §3 source-field rules application** — the annotation verbatim references the spec requirement anchor (`req-N` plus its `#req-N` anchor and title), the wayfinder ticket (`<ID>.md`), and the spec-end chain-of-authority decisions (`<change> Decision M`). The line-addressed form `(historical, <original reading>; superseded by spec req-N L### via <change> Decision M)` is **legacy**: annotations already carrying it stay as written (they are historical lineage records and rewriting them would corrupt the audit trail), but no NEW annotation may use it. This pattern is enforced by `scripts/lint_no_source_field_drift.py` (per CLAUDE.md §3 "Source reverse-link" rules); the ticket-body form of the annotation is enforced by `scripts/lint_ticket_annotation_form.py`, which scans `wayfinder/tickets/*.md` directly (no existing lint scans that tree: `scripts/lint_no_line_pointers.py` `SCAN_ROOTS` is `("openspec/specs", "src", "tests")`); and the line-addressed form is rejected by `scripts/lint_no_line_pointers.py` check C1 on any NEW annotation. It matches the existing source-field convention established by `req-gov-1` Policy lineage.

**Documenting-only meta Requirement**: This Requirement does NOT introduce new governance contract. It documents the existing CLAUDE.md §3 source-field rules application pattern for ticket `(historical, ...)` supersede annotations, declared at this governance boundary because the pattern is a cross-cutting governance convention rather than a per-capability behavior. The **ticket advisory boundary** concept (advisory scope vs operational impact distinction, monitoring obligation, drift remediation protocol) that this Requirement anticipated has since been formalized as `req-gov-4` ("Ticket Advisory Boundary — Stale Contamination Monitoring") in this same file, applied by `change 09-fix-claude-md-ticket-advisory-boundary` and archived at `openspec/changes/archive/2026-09-23-fix-claude-md-ticket-advisory-boundary`. This paragraph previously described that change as a "planning draft, NOT YET proposed/applied/archived"; the archived state supersedes it.

**Source:** `CLAUDE.md` (`governance/CLAUDE.md` back-link per `CLAUDE.md` §3 Workflow Conventions source-field rules)

#### Scenario: Ticket A8-2 supersede annotations follow CLAUDE.md §3 source-field rules verbatim

- **WHEN** `wayfinder/tickets/A8-2.md` supersede annotations italic `(historical, ..., superseded by spec req-20-mci (#req-20-mci) ... via ...)` annotations are appended
- **THEN** each annotation contains the canonical pattern verbatim: `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` — 3 reverse-links complete (ticket + spec anchor + change Decision), backtick-wrapped, with the spec anchor (`wayfinder/tickets/A6a-2.md` for the wayfinder ticket-side lineage); the line-addressed variant `req-N L###` is legacy and MUST NOT appear in a NEW annotation
- **AND** no new `governance` operational contract is introduced (the existing `req-gov-1` integer-vs-float guard + CLAUDE.md §3 source-field rules are sufficient for this drift remediation instance; the ticket-advisory-boundary formalization is the separate, already-archived change `09-fix-claude-md-ticket-advisory-boundary`, applied as `req-gov-4`)
- **AND** the `.audit/` evidence file edits (`.audit/spec-math-audit.md` verify-14 entry + `.audit/audit-verification/audit-verification.md` verify-15 verdict) do NOT require new governance anchoring — `.audit/` is a temporary audit evidence library (per `.audit/README.md`), not governed by spec Requirements
- **AND** the `governance` spec.md anchor coverage remains consistent: existing `req-gov-1` anchor unchanged; this Requirement is `req-gov-2`, a documenting-only meta Requirement (not an operational contract); the next governance contract introduced by a separate change was `req-gov-3`, and the ticket advisory boundary formalization is `req-gov-4`

#### Scenario: Ticket A8-2 centered-covariance supersede annotation preserved

- **WHEN** the A8-2 section carrying the `λ_j = C 分布协方差矩阵的特征值` historical definition attempt is read
- **THEN** that section preserves its original wording verbatim AND is immediately followed by an italic `(historical, centered-covariance reading; superseded by spec req-20-mci (#req-20-mci) uncentered second moment via `fix-openspec-doc-bugs` design.md Decision 8 + `fix-math-consistency-audit-2026-08` design.md Decision 5 — the centered reading has a `(1/d_c, 1]` upper endpoint that is unreachable at `|T| = d_c`)` annotation

#### Scenario: Ticket A8-2 convex-hull-radius supersede annotation preserved

- **WHEN** the A8-2 section carrying the `原 CV（C 分布凸包半径）` historical reading is read
- **THEN** that section preserves its original wording verbatim AND is immediately followed by an italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20-mci (#req-20-mci) uncentered second moment via `fix-openspec-doc-bugs` design.md Decision 8 + `fix-math-consistency-audit-2026-08` design.md Decision 5 — the `1/d_c` lower bound of CV on `S^{d_c−1}` makes the original `< 0.05` health target unreachable)` annotation

#### Scenario: the two A8-2 annotations jointly cover the req-20 Reason argument

- **WHEN** both A8-2 supersede annotations are read together
- **THEN** they jointly cover both clauses of the `wayfinder` `#req-20-mci` Reason supersede argument — the `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c` for the centered reading, and the `1/d_c` lower bound on `S^{d_c−1}` making the original `< 0.05` health target unreachable for the CV reading
- **AND** both name the **same** supersession target and the **same** chain of authority

#### Scenario: ticket supersede annotation form is machine-checked by a dedicated lint

- **WHEN** the gate set is discovered (`scripts/run_gates.py` `LINT_GLOB = "lint_*.py"`) or `wayfinder/tickets/*.md` is scanned directly
- **THEN** `scripts/lint_ticket_annotation_form.py` MUST report `path:line` plus the violated clause and exit 1 on any violation, exit 0 otherwise, over two clauses enforced at **different force**:
  - **V-ANCHOR (blocking)** — the `superseded by spec req-N` clause of a NEW (non-legacy) annotation MUST carry its `(#req-N)` anchor
  - **V-DECISION (blocking, existence only)** — where an annotation carries a `... Decision N` chain of authority, the change name it cites MUST resolve to an existing change under `openspec/changes/archive/` (date prefixes normalised away on both sides)
- **AND** whether the cited **Decision number** is the one that actually produced the supersession MUST NOT be asserted as a gate condition: that is not recoverable from the artifacts (the `β_0` closed form was written by 19 archived deltas, `req-22`'s anchor is duplicated across two capabilities, `req-32` was touched by 5 changes), and at least one annotation that satisfies the shape — `wayfinder/tickets/A4-1.md`, citing `fix-math-consistency-audit-2026-08 Decision 1` for the `β_0` supersession — cites a Decision whose body contains no beta term at all. An annotation carrying **no** citation MUST be reported in the lint's summary count and MUST NOT fail the gate
- **AND** the gate set MUST contain no exemption table, per-line `# noqa`, environment variable or CLI flag that exempts a pre-existing annotation — the lint is content-driven so that line drift cannot rot an exemption, mirroring the "NO exemption table" design of `scripts/lint_no_line_pointers.py`
- **AND** the lint MUST NOT report deliberately malformed text inside its own test fixtures, mirroring the self-exemption convention of `scripts/lint_no_line_pointers.py`
- **AND** parenthesis balancing MUST ignore parentheses inside backtick code spans, so that an annotation quoting deliberately unbalanced math (e.g. `` `(1/d_c, 1]` `` in `wayfinder/tickets/A8-2.md`) is still located and checked rather than silently dropped

---

### Requirement: Ticket Advisory Boundary — Stale Contamination Monitoring

The advisory status of `wayfinder/tickets/*.md` (per `CLAUDE.md` §8 "2026-08-21 裁决") SHALL NOT be interpreted as "ticket stale has no operational impact". Specifically:

1. **Advisory non-binding scope** — tickets MAY be superseded by OpenSpec changes without amending the ticket itself; this is the ONLY meaning of "advisory". The advisory scope covers ticket-edit policy (whether ticket text may diverge from spec) and does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`.

2. **Operational impact** — ticket stale values MAY propagate to `src/` via three empirically-observed channels: (i) MVPConfig default values copied directly from ticket numbers (per `commit adf41ef` 2026-09-19 history: `MVPConfig.beta_initial = 1.0` was originally sourced from `wayfinder/tickets/A4-1.md` `β_0 ≈ 1.0`; closed by `commit adf41ef` migrating to spec closed-form `0.1 + 31.9 · Sigmoid(γ_init)`); (ii) tests `assert MVPConfig().field == stale_value` LOCKS the propagation (per `commit adf41ef` history: `tests/test_beta.py::test_beta_param_init_default` originally had `assert MVPConfig().beta_initial == 1.0`; closed by migration to `pytest.approx(expected, abs=1e-3)` deriving expected from spec closed form); (iii) any implementation reading ticket directly without consulting spec reproduces stale values (cycle-9 worst-case: ticket `A6a-2.md` `f_i^avg < 1/128` historical vs spec `1 / (2 · N_e)` parameterized form, the `src/` boundary now uses spec parameterization per `src/decompmoe/safeguards.py::_dead_expert_threshold` `_dead_expert_threshold(N_e) = 1.0 / (2.0 * N_e)`).

3. **Monitoring obligation** — `.audit/audit-verification/audit-verification.md` MUST periodically verify the ticket ↔ spec ↔ src triangle for drift propagation. The empirical evidence base (cycle-9 ticket-stale pattern + remaining MEDIUM finding family across multiple cycles) establishes that "ticket-stale → src-pollution" is a recurring pattern requiring active monitoring, NOT a passive advisory. A "传染链已断" verdict (the spec is the truth source and the stale propagation has been interrupted at the `src/` boundary) does NOT exempt the project from this monitoring obligation — recurrence remains possible whenever a new contributor reads a ticket without consulting the corresponding spec. The path named in this clause is the one that exists in the repository (`.audit/audit-verification/audit-verification.md`); the bare `.audit/audit-verification.md` form previously named here does not resolve.

4. **Drift remediation protocol** — when ticket stale is detected propagating to `src/`: (a) ticket MUST receive a `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` annotation preserving the decision chain (canonical form per `openspec/specs/wayfinder/spec.md` req-34 "Source Field Format Invariant for OpenSpec Specs" Scenario "every Source field contains a wayfinder ticket reference"; the line-addressed `req-N L###` variant is legacy and MUST NOT be newly written); (b) `src/` default values MUST be updated to spec canonical values; (c) tests using `assert == stale_value` MUST migrate to `pytest.approx(spec_value, abs=...)` per `CLAUDE.md` §6 第 8 条 float closed-form convention (formalized by `req-gov-1`).

**Source:** `CLAUDE.md` §8 (cycle-7 audit-verification meta-洞察 boundary clarification, amended by this change)

#### Scenario: ticket advisory scope is bounded to ticket-edit policy

- **WHEN** a developer reads `CLAUDE.md` §8 "ticket 为历史决策记录（参考性、非约束性）" together with this Requirement's clause (1)
- **THEN** the advisory interpretation MUST be limited to ticket-edit policy (whether `wayfinder/tickets/*.md` text may diverge from spec), and MUST NOT be extended to claims that ticket-side numerical values have no downstream effect on `src/` or `tests/`

#### Scenario: three contamination channels are independently verifiable

- **WHEN** audit-verification loop checks ticket ↔ spec ↔ src triangle for drift propagation (per clause (3) monitoring obligation)
- **THEN** the three contamination channels enumerated in clause (2) — (i) MVPConfig default values copied from ticket, (ii) tests `assert == stale_value` LOCKS, (iii) reader-ticket-not-spec reproductions — MUST each be independently verifiable by (a) `grep` of MVPConfig dataclass fields against ticket numerical claims, (b) `grep` of `assert MVPConfig().field ==` patterns in `tests/`, (c) absence of canonical-API guards in any module reading ticket-derived constants directly

#### Scenario: drift remediation protocol enforces three-step closure

- **WHEN** a ticket-stale finding is detected propagating to `src/` (per audit-verification three-axis verdict or independent reviewer)
- **THEN** closure of that finding MUST execute the three steps enumerated in clause (4) — (a) ticket `(historical, ...)` annotation, (b) `src/` default value update, (c) tests `pytest.approx` migration — in that order, and a partial closure (e.g., step (a) without (b) and (c)) MUST NOT be considered a fully-closed finding under this Requirement

#### Scenario: the monitoring obligation names a path that resolves

- **WHEN** a reader resolves the path named in clause (3) against the repository tree
- **THEN** the named path MUST exist as a readable file; a monitoring obligation pointing at a path that does not resolve leaves the obligation without an executable referent and MUST be reported as a defect
