## Context

See `proposal.md - Why` for motivation. The change operates on a single spec file (`openspec/specs/decompmoe-skeleton/spec.md`) at 7 textual references in body paragraphs of two Scenarios under the Requirement `Five Numerical Safeguard Helpers`. No code, test, or other spec changes.

The current references use literal line numbers (`wayfinder L249`) — a fragile citation form that drifts whenever `openspec/specs/wayfinder/spec.md` gains/loses lines. wayfinder spec already exposes stable anchors: `<a id="req-13"></a>` (L245) anchors the Requirement 13 header (`### Requirement: Numerical Safeguards`, L247). This change redirects 7 fragile citations to that stable anchor.

## Goals / Non-Goals

**Goals:**
- Replace every literal `L249` citation in `decompmoe-skeleton/spec.md` body text with a stable anchor-based reference that survives future wayfinder spec line shifts.
- Preserve all numeric math (counterexamples, threshold formulas, closed forms) byte-identically — only the citation form changes.
- Pass `scripts/lint_no_source_field_drift.py` (no `**Source:**` field touched; field already references `wayfinder/tickets/A6a-2.md`).

**Non-Goals:**
- Editing wayfinder spec (its L245 anchor + L247 title are already stable).
- Editing code (`src/decompmoe/`) — no code references `wayfinder L249`.
- Editing tests (`tests/`) — no test functions reference `wayfinder L249`.
- Touching `**Source:**` fields — already lint-clean.
- Restructuring Scenarios or Requirements — pure text rephrase.

## Decisions

### Decision 1: Reference form `wayfinder Req 13 'Numerical Safeguards' (anchor `#req-13`)`

The new citation form combines three pieces:
- **Requirement number** (`Req 13`) — semantic identifier, stable across wayfinder spec line shifts.
- **Requirement title** (`'Numerical Safeguards'`) — human-readable cross-check, helps reader locate even if anchor IDs are renumbered in the future.
- **HTML anchor** (`#req-13`) — explicit machine-parseable pointer to the `<a id="req-13"></a>` line at `openspec/specs/wayfinder/spec.md:245`.

**Alternatives considered**:
- *Bare `wayfinder Req 13`* — minimal but loses the title + anchor dual-pointer. Rejected: less defensive against future re-numbering.
- *Markdown link `[Numerical Safeguards](wayfinder/spec.md#req-13)`* — most "modern" but breaks the existing in-prose parenthetical style ("(wayfinder L249 wording)"). Rejected: style consistency with surrounding prose.
- *Pure anchor `wayfinder#req-13`* — minimal but loses semantic identifier. Rejected: ambiguous if anchor IDs are reused.

### Decision 2: Apply all 7 edits in a single PR (atomic)

All 7 `L249` references live in 2 Scenarios under the same Requirement. Splitting into multiple PRs would create an intermediate state where some references are stable-anchored and others still literal — a worse final state than today's "all literal". Atomic single PR keeps the cross-reference graph self-consistent at every commit.

**Alternatives considered**:
- *Per-Scenario PRs (2 PRs)* — Rejected: introduces cross-PR inconsistency window.
- *Per-reference PRs (7 PRs)* — Rejected: 7× review overhead for trivial rephrase.

### Decision 3: Do not add a `## Purpose` section in delta spec

The instructions in `openspec instructions specs --change ... --json` explicitly state: "Do NOT add `## Purpose` to a delta for an existing capability — that spec already has one and the delta's is ignored." `decompmoe-skeleton` already has its `## Purpose` in `openspec/specs/decompmoe-skeleton/spec.md` (overarching capability intro); the delta for the modified Requirement omits `## Purpose` per the explicit instruction.

## Risks / Trade-offs

- **[Risk] Anchor ID drift in wayfinder spec** — if `openspec/specs/wayfinder/spec.md` ever renumbers `req-13` (e.g., inserts a new Requirement before L247), the `<a id="req-13"></a>` line shifts and our citation breaks.
  - **Mitigation**: The new citation form includes the **requirement number** (`Req 13`) AND the **title** (`Numerical Safeguards`) alongside the anchor. If the anchor drifts, a reader sees the mismatch between `Req 13`/`Numerical Safeguards` and the link target — making the drift visible at lookup time, not silent.
  - **Long-term mitigation**: wayfinder spec anchors follow a stable convention (`<a id="req-N">` colocated with `### Requirement: ...`); re-numbering would also break the 30+ existing `wayfinder/tickets/A*.md` references that use `Req N` notation, so any future renumbering is itself a breaking change that requires broader audit.

- **[Risk] Line-number references still present in other files** — this change only fixes `openspec/specs/decompmoe-skeleton/spec.md`. Other docs or tickets may still reference "wayfinder L249" (verified via grep: only decompmoe-skeleton has this pattern; no other file matches `wayfinder L[0-9]+`).
  - **Mitigation**: grep `openspec/` confirms zero other `wayfinder L###` patterns after this change applies.

- **[Trade-off] More verbose references** — `wayfinder Req 13 'Numerical Safeguards' (anchor `#req-13`)` is 53 characters vs original `wayfinder L249` (15 chars). Reader scannability is slightly reduced.
  - **Justification**: Robustness > terseness; the existing surrounding prose ("wayfinder L249 wording `f_i^avg < 1/(2·N_e)`") is already in parenthetical/discussion form where verbosity is acceptable.

## Migration Plan

Single-commit migration. Steps:

1. Apply the 7 textual edits in `openspec/specs/decompmoe-skeleton/spec.md` per the proposal's `## What Changes` block (the exact delta is captured in `specs/decompmoe-skeleton/spec.md` of this change).
2. Run `python scripts/lint_no_source_field_drift.py` — must `exit=0` (existing Source field on L206 is unchanged and already lint-clean).
3. Run `python scripts/lint_no_dead_defensive.py` — must `exit=0` (no code change, no impact on this lint gate).
4. Run `openspec archive --change 2026-09-12-replace-literal-wayfinder-l249-with-anchor-ref` per OpenSpec workflow.

**Rollback**: revert the single commit. No data migration, no dependency upgrade, no downstream consumer changes.

## Open Questions

(none — all design choices are deterministic given the existing wayfinder anchor structure)
