# Design

## Context

The audit's UD-04 verdict — "the annotation obligation has no subject, no owner, no check point, no
lint coverage" — is a *conclusion* that survives on one of its four claims and fails on the other
three. This design records why, so the next round does not re-derive it.

| UD-04 claim | Verdict | Evidence |
|---|---|---|
| "no subject" (义务没有约束对象) | **False** | `CLAUDE.md:98` and `req-gov-4` clause (1) both restrict "advisory" to ticket-edit policy. Clause (3) names a monitor, clause (4) names a protocol. The subject exists. |
| "no owner" | **False** | Clause (3) names the audit-verification loop as the owner. |
| "no check point" | **Half true** | Clause (3) names `.audit/audit-verification.md` — a path that does not resolve. The check point is named but unrunnable. |
| "no lint coverage" | **True** | `lint_no_line_pointers.py:81` `SCAN_ROOTS` omits `wayfinder/tickets`. No lint reads a ticket body. |

So the change is two fixes, not one: correct the unrunnable path, and close the coverage gap.

## Decision 1 — a new lint file rather than widening `SCAN_ROOTS`

`lint_no_line_pointers.py:81` already excludes `wayfinder/tickets`. The obvious minimal edit is to add
it to the tuple. Rejected:

- That lint's contract is C1 (no line-number reference). Its self-exemption convention
  (`:85-91`, "a lint never reports its own fixtures") and its "NO exemption table" property
  (`:50-51`) are pinned by `tests/test_lint_no_line_pointers.py`. Widening the scan set changes what
  those tests sweep, so the change would have to perturb an existing, already-green gate and its
  suite.
- A ticket tree and a spec tree have different normative shapes. `wayfinder/tickets/*.md` is
  narrative prose with embedded annotations; `openspec/specs/**` is structured Requirement text.
  Asserting annotation *form* over prose is a different job from asserting the absence of line
  pointers over specs.

Chosen: `scripts/lint_ticket_annotation_form.py`, importing `scripts/pointer_scan.py` as a library for
the marker semantics it already implements. `run_gates.py:278` discovers lints by
`LINT_GLOB = "lint_*.py"` (`:65`), so no registration is needed.

Rollback cost is correspondingly low: delete one lint and one test file. No existing gate is touched.

## Decision 2 — assertion scope is form only

The lint asserts **form**: given that an annotation exists, is it canonical?

```
(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)
```

Two violations are reported, at **different force** — see Decision 6:

- **V-ANCHOR** — the `superseded by spec req-N` clause lacks its `(#req-N)` anchor. Blocking.
- **V-DECISION** — a cited change does not exist. Blocking.

Deliberately **not** asserted:

- **Existence** — "every ticket must carry at least one annotation". Measured state is 18
  annotations across 7 of 23 tickets. There is no objective criterion for which tickets *should*
  have one, so an existence rule would encode a judgment call as a red gate.
- **Drift** — "a value superseded in spec must have a matching annotation here". This needs a
  spec↔ticket association key that does not exist, and would introduce exactly the cross-artifact
  semantic surface this change is not chartered to define.

## Decision 3 — no exemption table

`pointer_scan.py:50-51` states the governing philosophy verbatim: *"NO exemption table (not
`JUSTIFIED_EXEMPTIONS`, not per-line `# noqa`, not env var, not CLI flag). The historical exemption is
by marker on the line … Content-based rules, so they survive line shifts without exemption rot."*

A grandfather list for pre-existing violations would contradict that.

Legacy line-addressed annotations (`req-N L###`) measure **0** occurrences in the ticket tree, and
**all 18** annotations already carry the `(#req-N)` anchor — better than the change's own estimate of
"16 of 18". So V-ANCHOR is green on arrival with no corpus edit at all.

## Decision 6 — two-tier enforcement, after provenance reconstruction failed

The change was scoped to normalize the corpus so V-ANCHOR **and** a Decision-presence clause would go
green together. Reconstructing provenance for the 9 annotations that carry no decision citation was
attempted and **failed with evidence**:

| annotations | reconstruction result |
|---|---|
| `A5-3:81`, `A5-3:85` (52°) | attributable — `2026-08-23-fix-math-consistency-audit-2026-08` Decision 1, whose Rationale names `wayfinder/tickets/A5-3.md:62-67` as its own source |
| `A5-3:42`, `A5-3:68` (β₀) | **not attributable** — 19 archived deltas wrote `31.9` |
| `A3-2:45`, `A3-2:50` (req-22) | **not attributable** — anchor duplicated at `wayfinder/spec.md:610` and `decompmoe-skeleton/spec.md:560`; 2 changes touched it |
| `A6a-2:72` (req-32) | **not attributable** — 5 changes touched it |
| `A6b-1:133` | **not attributable** — composite reference to two Requirements |

The decisive finding is not that attribution is hard. It is that an annotation which **already
satisfies** the citation shape is provably wrong: `wayfinder/tickets/A4-1.md` cites
`fix-math-consistency-audit-2026-08 Decision 1` for the `β_0` supersession, and that Decision's body
contains no beta term — it is the Voronoi 52° → 67.24° decision. A red gate demanding a Decision
number would ratify a citation style already known to carry mis-attributions.

Hence: **V-ANCHOR blocks; V-DECISION is narrowed to the only part that is objectively checkable —
that a cited change exists.** An annotation citing nothing is counted in the summary and does not
fail the gate. This keeps the teeth on the failure mode that matters (invented provenance) and asks
for nothing the artifacts cannot support.

## Decision 7 — paren balancing ignores code spans

`wayfinder/tickets/A8-2.md:70` quotes `` `(1/d_c, 1]` `` — an interval closed with a square bracket.
A naive depth counter never returns to 0, so that annotation was **silently dropped and went
unchecked**: measured, `A8-2.md` showed 2 markers and 1 balanced span, and the corpus counted 17
rather than 18. A form gate that quietly skips one annotation has exactly the defect it exists to
prevent.

Parens inside backtick spans are therefore not counted. This is not a special case bolted on: it is
`pointer_scan`'s existing rule that a token inside a code span is a quotation, not a claim about the
document. After the fix, markers = spans = 18 across all 23 ticket files.

## Decision 8 — self-exemption of fixtures

The test suite must contain deliberately malformed annotations to exercise V-ANCHOR and V-DECISION.
Without a guard the lint would report its own fixtures and the suite would be unusable. This mirrors
`lint_no_line_pointers.py:85-91`. The guard is content-based (a fixture-directory marker), not a path
skip list, so it cannot rot.

## Decision 9 — audit-side records stay out of the spec delta

`req-gov-2` Scenario 1 states that `.audit/` "is a temporary audit evidence library (per
`.audit/README.md`), not governed by spec Requirements". The audit corrections (UD-05 withdrawal,
UD-03 pending-evidence, and the corrected numbers) therefore edit `.audit/**` directly and add no
Requirement. Precedent: `openspec/changes/archive/2026-10-05-audit-df-list-fact-corrections` carries
`proposal/design/tasks` with **no** `specs/` delta.

## Risk handling

- **Exit-code discipline.** `run_gates.py` uses 0 ok / 1 findings / 2 invalid (`:68-70`). Exit 2
  means `HEAD` or the worktree changed while the gate ran (`:10` documents the swallowed-anchor case
  that motivated it). It must be re-verified, never retried verbatim.
- **Shared worktree.** `src/decompmoe/gating.py` and `wayfinder/tickets/WF-1.md` are dirty from
  another actor. Stage by explicit path; `git add .` would absorb them. This matters more than
  usual here because the `WF-1.md` edit removes an annotation while leaving `< 1/128` unmarked.
