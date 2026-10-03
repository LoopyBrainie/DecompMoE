# Spec Delta — `governance`

## ADDED Requirements
<a id="req-gov-6"></a>

### Requirement: Cross-Reference Anchor Contract

The system MUST NOT use raw line numbers as the identity of a cross-reference in any peer spec
under `openspec/specs/**`, in `src/**`, or in `tests/**`. A reference MUST resolve through a
mechanically checkable identifier instead. This Requirement exists because the absence of such a
rule let the same defect family be "fixed" five times by hand, each pass leaving siblings behind.

1. **Permitted reference forms.**

   | Target | Required form | Example |
   |---|---|---|
   | a whole Requirement | `Req N` / `req-N` / `` `#req-N` `` plus the Requirement title | `` `Req 13` Numerical Safeguards (`#req-13`) `` |
   | a table row or field block | a block-level `<a id="req-N-slug"></a>` anchor, referenced as `` `#req-N-slug` `` | `` `#req-20-mci` `` |
   | a code symbol | `module.py::symbol` | `` `safeguards.py::beta_saturation_warning` `` |
   | a test | `file::test_name` | `` `test_sphere.py::test_voronoi_canonical_N_e_dependence` `` |
   | a prose passage | Requirement number + title + a verbatim quotation of at least 8 characters | the quotation itself is greppable |

2. **Block-anchor minting rule.** A block-level anchor MUST be minted only for a target with **at
   least 2 inbound references**, established by a recorded inbound-reference census rather than by
   judgement. A target with a single inbound reference MUST instead use the Requirement number plus
   a row label or symbol name. This bounds anchor growth: each anchor is a maintenance obligation
   that must be re-checked on every rename of the thing it labels.

3. **Anchor uniqueness and namespace hygiene.** Within a single spec file every `id` MUST be
   unique, and every `### Requirement:` heading MUST be immediately preceded by its
   `<a id="req-N"></a>` anchor. An anchor literal quoted inside prose or inside a code span MUST NOT
   appear in a Requirement body — a quoted literal still occupies the id namespace when the
   document is parsed, and two Requirements sharing an id makes every anchor reference ambiguous.

4. **Resolvability.** Every `req-N`, `#req-N`, and `#req-N-slug` reference in a peer spec, in
   `src/**`, or in `tests/**` MUST resolve to an anchor that exists in the named capability.

5. **Enforcement.** `scripts/lint_no_line_pointers.py` MUST implement checks C1 (no line-number
   reference), C2 (anchor uniqueness and coverage), C3 (no anchor literal inside a code span), and
   C4 (reference resolvability), and MUST exit non-zero on any violation. It MUST be run as part
   of the `/opsx:archive` precondition alongside the existing two lint gates, per `CLAUDE.md` §3.

6. **Historical-citation exemption.** A line-number reference that records history — a
   superseded coordinate, a pre-change location, or a prior-commit citation — is exempt from
   C1 when the line carries an explicit historical marker (`pre-this-change`, `histor`, the
   original-language marker, a prior commit id, `was`, `before`, or an explicit move arrow). The
   exemption is by marker, not by a registry of exempted files, so that the exemption surface
   stays visible in the document itself.

7. **Archive copies are out of scope.** `openspec/changes/**` is NOT scanned. An archived change is
   the historical record of what a past change did; retro-editing it would falsify that record. A
   pointer introduced by a change is corrected in the live spec by the change that closes it.

**Source:** `CLAUDE.md` §3 (source reverse-link rules and archive preconditions), `CLAUDE.md` §6
(anchor coverage requirement), change
`2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract` design.md (Decisions D1-D8)

#### Scenario: a line-number reference is rejected

- **WHEN** a peer spec, `src/**` file, or `tests/**` file contains a line-number cross-reference
  such as `<capability> L<line>`, `req-<N> L<line>`, `<capability> L<first>-L<last>`, `line <number>`, or
  `<module>.py:<line>` that is not an exempt historical citation
- **THEN** `scripts/lint_no_line_pointers.py` MUST report a violation naming the file, the line,
  and the matched reference
- **AND** the lint MUST exit non-zero
- **AND** the reference MUST be rewritten to one of the permitted forms in clause (1)

#### Scenario: a technical label is not a line reference

- **WHEN** a document uses `L` followed by a digit as a technical label, for example `d_c[L2-step2]`
  or `L4-postmean`, where the digits denote a layer or step rather than a line
- **THEN** `scripts/lint_no_line_pointers.py` MUST NOT report it
- **AND** the label MUST remain greppable as its own token

#### Scenario: a single-reference target does not earn a block anchor

- **WHEN** the inbound-reference census reports exactly 1 inbound reference for a target
- **THEN** no block-level anchor MUST be minted for it
- **AND** the referring site MUST name the Requirement plus a row label or symbol name instead

#### Scenario: a quoted anchor literal is rejected

- **WHEN** a Requirement body contains an anchor literal inside prose or inside a code span, for
  example `` `<a id="req-20"></a>` ``
- **THEN** `scripts/lint_no_line_pointers.py` MUST report a C3 violation
- **AND** the id namespace of that spec MUST remain free of the duplicate
- **AND** the body MUST reference the target by `` `#req-20` `` plus its title instead

#### Scenario: the lint discriminates against the pre-change tree

- **WHEN** `scripts/lint_no_line_pointers.py` is evaluated against the repository state before this
  change
- **THEN** it MUST report C1 violations and exit non-zero
- **AND** it MUST report green only against the post-change state, so that a silently-passing
  check is itself detectable

## MODIFIED Requirements

<a id="req-gov-2"></a>

### Requirement: Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application

The system SHALL treat the ticket `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` annotation pattern, when appended to `wayfinder/tickets/A8-2.md` (or any other wayfinder ticket lineage entry), as a **CLAUDE.md §3 source-field rules application** — the annotation verbatim references the spec requirement anchor (`req-N` plus its `#req-N` anchor and title), the wayfinder ticket (`<ID>.md`), and the spec-end chain-of-authority decisions (`<change> Decision M`). The line-addressed form `(historical, <original reading>; superseded by spec req-N L### via <change> Decision M)` is **legacy**: annotations already carrying it stay as written (they are historical lineage records and rewriting them would corrupt the audit trail), but no NEW annotation may use it. This pattern is enforced by `scripts/lint_no_source_field_drift.py` (per CLAUDE.md §3 "Source reverse-link" rules) and, for the line-addressed form, rejected by `scripts/lint_no_line_pointers.py` check C1 on any NEW annotation. It matches the existing source-field convention established by `req-gov-1` Policy lineage.

**Documenting-only meta Requirement**: This Requirement does NOT introduce new governance contract. It documents the existing CLAUDE.md §3 source-field rules application pattern for ticket `(historical, ...)` supersede annotations, declared at this governance boundary because the pattern is a cross-cutting governance convention rather than a per-capability behavior. Future governance Requirements formalizing the **ticket advisory boundary** concept (advisory scope vs operational impact distinction, monitoring obligation, drift remediation protocol) are planned under `change 09-fix-claude-md-ticket-advisory-boundary` (currently a `.audit/audit-verification/opsx-changes/09-fix-claude-md-ticket-advisory-boundary/` planning draft, NOT YET proposed/applied/archived) and would be `req-gov-N` *if* and when that planned change is archived.

**Source:** `CLAUDE.md` (`governance/CLAUDE.md` back-link per `CLAUDE.md` §3 Workflow Conventions source-field rules)

#### Scenario: Ticket A8-2 L70 + L74 annotations follow CLAUDE.md §3 source-field rules verbatim

- **WHEN** `wayfinder/tickets/A8-2.md` L70 + L74 italic `(historical, ..., superseded by spec req-20 L413 ... via ...)` annotations are appended
- **THEN** each annotation contains the canonical pattern verbatim: `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` — 3 reverse-links complete (ticket + spec anchor + change Decision), backtick-wrapped, with the spec anchor (`wayfinder/tickets/A6a-2.md` for the wayfinder ticket-side lineage); the line-addressed variant `req-N L###` is legacy and MUST NOT appear in a NEW annotation
- **AND** no new `governance` operational contract is introduced (the existing `req-gov-1` integer-vs-float guard + CLAUDE.md §3 source-field rules are sufficient for this drift remediation instance; the planned `09-fix-claude-md-ticket-advisory-boundary` ticket-advisory-boundary formalization is a separate future change)
- **AND** the `.audit/` evidence file edits (`.audit/spec-math-audit.md` L524 + `.audit/audit-verification.md` verify-15 verdict) do NOT require new governance anchoring — `.audit/` is a temporary audit evidence library (per `.audit/README.md` L3), not governed by spec Requirements
- **AND** the `governance` spec.md anchor coverage remains consistent: existing `req-gov-1` anchor at L7 unchanged; this ADDED Requirement introduces `req-gov-2` as a documenting-only meta Requirement (not an operational contract); future governance contracts would be `req-gov-3`+ and are introduced by separate changes


#### Scenario: Ticket A8-2 centered-covariance supersede annotation preserved

- **WHEN** the A8-2 section carrying the `λ_j = C 分布协方差矩阵的特征值` historical definition attempt is read
- **THEN** that section preserves its original wording verbatim AND is immediately followed by an italic `(historical, centered-covariance reading; superseded by spec req-20 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — the centered reading has a `(1/d_c, 1]` upper endpoint that is unreachable at `|T| = d_c`)` annotation

#### Scenario: Ticket A8-2 convex-hull-radius supersede annotation preserved

- **WHEN** the A8-2 section carrying the `原 CV（C 分布凸包半径）` historical reading is read
- **THEN** that section preserves its original wording verbatim AND is immediately followed by an italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md Decision 5 — the `1/d_c` lower bound of CV on `S^{d_c−1}` makes the original `< 0.05` health target unreachable)` annotation

#### Scenario: the two A8-2 annotations jointly cover the req-20 Reason argument

- **WHEN** both A8-2 supersede annotations are read together
- **THEN** they jointly cover both clauses of the `wayfinder` `#req-20-mci` Reason supersede argument — the `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c` for the centered reading, and the `1/d_c` lower bound on `S^{d_c−1}` making the original `< 0.05` health target unreachable for the CV reading
- **AND** both name the **same** supersession target and the **same** chain of authority

<a id="req-gov-4"></a>

### Requirement: Ticket Advisory Boundary — Stale Contamination Monitoring

The advisory status of `wayfinder/tickets/*.md` (per `CLAUDE.md` §8 "2026-08-21 裁决") SHALL NOT be interpreted as "ticket stale has no operational impact". Specifically:

1. **Advisory non-binding scope** — tickets MAY be superseded by OpenSpec changes without amending the ticket itself; this is the ONLY meaning of "advisory". The advisory scope covers ticket-edit policy (whether ticket text may diverge from spec) and does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`.

2. **Operational impact** — ticket stale values MAY propagate to `src/` via three empirically-observed channels: (i) MVPConfig default values copied directly from ticket numbers (per `commit adf41ef` 2026-09-19 history: `MVPConfig.beta_initial = 1.0` was originally sourced from `wayfinder/tickets/A4-1.md` `β_0 ≈ 1.0`; closed by `commit adf41ef` migrating to spec closed-form `0.1 + 31.9 · Sigmoid(γ_init)`); (ii) tests `assert MVPConfig().field == stale_value` LOCKS the propagation (per `commit adf41ef` history: `tests/test_beta.py::test_beta_param_init_default` originally had `assert MVPConfig().beta_initial == 1.0`; closed by migration to `pytest.approx(expected, abs=1e-3)` deriving expected from spec closed form); (iii) any implementation reading ticket directly without consulting spec reproduces stale values (cycle-9 worst-case: ticket `A6a-2.md` `f_i^avg < 1/128` historical vs spec `1 / (2 · N_e)` parameterized form, the `src/` boundary now uses spec parameterization per `src/decompmoe/safeguards.py:34-36` `_dead_expert_threshold(N_e) = 1.0 / (2.0 * N_e)`).

3. **Monitoring obligation** — `.audit/audit-verification.md` MUST periodically verify the ticket ↔ spec ↔ src triangle for drift propagation. The empirical evidence base (cycle-9 ticket-stale pattern + remaining MEDIUM finding family across multiple cycles) establishes that "ticket-stale → src-pollution" is a recurring pattern requiring active monitoring, NOT a passive advisory. A "传染链已断" verdict (the spec is the truth source and the stale propagation has been interrupted at the `src/` boundary) does NOT exempt the project from this monitoring obligation — recurrence remains possible whenever a new contributor reads a ticket without consulting the corresponding spec.

4. **Drift remediation protocol** — when ticket stale is detected propagating to `src/`: (a) ticket MUST receive a `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` annotation preserving the decision chain (canonical form per `openspec/specs/wayfinder/spec.md` req-34 "Source Field Format Invariant for OpenSpec Specs" Scenario "every Source field contains a wayfinder ticket reference"; the line-addressed `req-N L###` variant is legacy and MUST NOT be newly written); (b) `src/` default values MUST be updated to spec canonical values; (c) tests using `assert == stale_value` MUST migrate to `pytest.approx(spec_value, abs=...)` per `CLAUDE.md` §6 第 8 条 float closed-form convention (formalized by `req-gov-1`).

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

