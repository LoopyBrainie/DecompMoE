# Design

## Context

The A-4 audit bucket found 15 cross-reference / line-pointer defects. Verified
independently at `HEAD = 16b2f46`: `STALE_FIXED = 0` — none has been fixed since
the pin commit `6593a06`. Four are `LOCATION_MISLABELED` (the Requirement
attribution is wrong even though the defect is real), two are `PARTIAL`.

The operative fact is not the 15 items. It is that this family has been
"fixed" by hand **five times** and every pass left siblings behind.

| archived change | what it fixed | what it left behind (measured) |
|---|---|---|
| `2026-09-12-replace-literal-wayfinder-l249-with-anchor-ref` | 7 `wayfinder L249` pointers in `decompmoe-skeleton/spec.md` | its own proposal scopes out "wayfinder spec、code 或 tests" ⇒ the 10 pointers in `tests/test_safeguards.py` survive to this day |
| `2026-10-01-fix-f1-f2-f3-f8-precision-and-pointer-drift` | `tests/test_schedule.py` `spec line 495` | the same stale `line 495` still sits in `src/decompmoe/schedule.py:151,168` — tests side fixed, src side missed |
| `2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351` | anchor coverage holes | patched coverage; added no rule forbidding line pointers |
| `2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293` | more coverage holes | same |
| `2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` | orphan anchors | same |

The pattern: each pass worked from a finding list. The finding list is itself
incomplete — `src/decompmoe/config.py:50` (`per spec req-7 L130 closed-form`) is
a live pointer that the A-4 list does not mention. So a sixth hand-pass would
fail the same way. Hence: census decides scope, lint prevents recurrence.

## Goals / Non-Goals

**Goals**

- Every line-number cross-reference in live specs / `src` / `tests` resolves
  through a mechanically checkable identifier.
- No defect can be re-introduced without a gate failure.
- The drift amplifier (`req-36`) stops defining truth by pointer.
- The one dangling guard in the family (AC-63) gets a real, named guard.

**Non-Goals**

- No change to any mathematical or numerical semantics.
- No retouch of `openspec/changes/archive/**` (governance's "Archive copies are
  not retro-edited").
- No fix of the two pre-existing `openspec validate` failures (they belong to
  two other stale no-tasks changes).
- No cleanup of the other session's untracked `_*.py` scratch files.
- Not A-1 / A-2 / A-3 items.

## Decisions

### D1 — The census, not the audit list, defines scope

`evidence/pointer_census.py` scans `openspec/specs/**`, `src/**`, `tests/**`
and emits `evidence/pointer_census.json`. Result: **117 pointer lines, 20
historical-marker exemptions, 97 actionable, across 14 files**.

The plan's §1.1 figure of 237 came from the loose regex `\bL\d{1,4}\b`, which
is an **upper bound, not a detector**: it also matches technical labels such as
`d_c[L2-step2]` and `L4-postmean`, where "L2" means *layer 2*. Migrating those
would corrupt meaning. An intermediate over-correction (allowing `at <n>` /
`per <n>` as context) pushed the count to 322 by matching ordinary prose. The
shipped detector requires a capability or requirement token *adjacent* to the
number.

**Classifier self-check** (plan §0.2): the detector is asserted against a known
positive — `wayfinder L249` must yield exactly 10 sites, all in
`tests/test_safeguards.py` — and the run aborts if it does not. This fired twice
during development and caught a real bug both times: first a wrong repo root
(`parents[4]` vs `parents[3]`) that reported **0 pointers**, then a
`classify()` that no longer returned `None` and reported **11 791**. A zero or
absurd count was the counter being broken, not the repository being clean.

**Denominator cross-check**: 10/10 independently known A-4 sites are detected
with correct Requirement attribution (`config.py:95/96`→`req-11`,
`config.py:50`→`req-7`, `schedule.py:148/151/168`→`Req 20`,
`metrics.py:203`→`Req 20`, `test_extraction.py:404`→`req-7`,
`wayfinder/spec.md:24`→`req-11`).

### D2 — The census is authoritative for counts and sites, NOT for attribution

Where a pointer carries an explicit `req-N` / `Req N`, the census attributes
reliably. Where it is a bare `spec L###`, attribution resolves by *line number*,
and the referenced line usually now sits inside a **different** Requirement:

- the 18-site `spec L413` cluster resolves to `req-18`, but the text is
  "spec L413 Reason" — it means **`req-20`'s** Reason narrative;
- the 12-site `spec L206` cluster resolves to `req-9`, but the text is
  "Five Numerical Safeguard Helpers" / `clip_global_grad_norm_` — it means
  **`decompmoe-skeleton` `req-11`**.

This is not a bug in the census; it is the defect itself, observed. Consequence:
**block anchors are minted from adjudicated intent, not from the census's
automatic key.** The census supplies the candidate list; a human resolves which
Requirement each bare pointer meant.

### D3 — Block anchors only where inbound ≥ 2, and only for table rows / fields

Ten targets reach inbound ≥ 2. Minting is limited to targets that are *table
rows or field blocks*, because those have a stable label to point at:
`#req-20-mci` (the `MCI` table row) and `#req-20-source` (the Source field).
Single-inbound targets get "Requirement number + row label / symbol name"
instead, e.g. `safeguards.py::beta_saturation_warning` for the 6 sites that
pointed at `safeguards.py:211`.

Each anchor is a maintenance obligation re-checked on every rename of the thing
it labels, so the count is deliberately kept at 2 rather than 10.

### D4 — Mixed replacement forms

Table rows / fields → block anchor. Whole Requirements → `Req N` + title +
`#req-N`. Code → `module.py::symbol`. Tests → `file::test_name`. Prose
passages → Requirement number + title + a verbatim quotation of ≥ 8 characters,
which stays greppable. This is recorded as the ADDED `governance` Requirement
"Cross-Reference Anchor Contract".

### D5 — req-36 is removed, not rewritten, and its guarantees move

`req-36` is the root cause: it declares itself the canonical truth source while
expressing its whole body as line pointers, **contradicting itself** (body says
`L453`, Scenarios say `L413`), verbatim-duplicating `req-20`'s closed form, and
writing the anchor literal `<a id="req-20"></a>` into its prose. Its Scenarios
then *mandate* that the spec's own line numbers not change — so editing `req-20`
breaks `req-36`, and fixing `req-36` requires editing the spec. Self-sustaining
drift.

**The first plan said "rewrite it thinner", and that turned out to be
infeasible.** `openspec validate` rejects a `MODIFIED` block whose Scenario
titles differ from the live ones — "archive refuses to drop them". `req-36`'s
four Scenario titles *are* the defect (`Spec L413 is the unchanging canonical
closed-form for MCI`). So the titles cannot be kept, and the body cannot be
rewritten in place. Removal is the only shape that clears both constraints, and
it is also the stronger outcome: a Requirement that exists solely to point at
another Requirement should not exist at all.

The four guarantees are redistributed, none weakened:

| guarantee | new home | why there |
|---|---|---|
| (a) the `MCI` closed form is the canonical, unchanging truth | `wayfinder` `req-20`, new Scenario | `req-20` already holds the row, its Reason, and both endpoint Scenarios |
| (b) A8-2 centered-covariance annotation preserved verbatim + followed by its italic annotation | `governance` `req-gov-2` | the capability that owns the ticket supersede-annotation pattern |
| (c) A8-2 convex-hull-radius annotation preserved | `governance` `req-gov-2` | same |
| (d) the two annotations jointly cover the `req-20` Reason argument | `governance` `req-gov-2` | it already registers the annotation's Source lineage |

(b)(c)(d) also belong in governance rather than wayfinder: they are guards over
*ticket* text, and keeping ticket coordinates out of the mathematical capability
is what prevents this drift from recurring there.

Two of the four original Scenario titles carry their own historical marker
(`... historical supersede annotation preserved`), so C1 exempts them by marker
rather than needing an exemption registry.

### D6 — The governance ticket-annotation form is a hard prerequisite

`governance` currently **mandates** the line-addressed form twice: the
"Ticket `(historical, ...)` supersede annotation pattern" Requirement body and
its Scenario, plus `req-gov-4` clause 4(a). Left alone, every existing ticket
annotation becomes an unavoidable C1 violation and the gate can never go green.
Both are re-anchored to `req-N <title> (#req-N)`, with the `L###` variant
declared **legacy**: existing annotations are not rewritten (they are historical
lineage records and rewriting them would corrupt the audit trail), but no new
annotation may use it.

The new Requirement is numbered **`req-gov-6`**, not `req-gov-5` — `req-gov-5`
is already taken by "Numeric Literal Provenance in Specs" at `governance`
L175. Colliding with a live anchor would have reintroduced exactly the
duplicate-anchor defect this change exists to close.

### D7 — One lint, four checks, no exemption registry

`scripts/lint_no_line_pointers.py`, structured like the existing
`lint_no_source_field_drift.py` (independent checks, content-only, non-zero
exit):

| check | content |
|---|---|
| C1 | no line-number reference in `openspec/specs/**`, `src/**`, `tests/**`; exempt only via historical marker |
| C2 | every anchor id unique per file; every `### Requirement:` immediately preceded by its anchor |
| C3 | no anchor literal inside a code span (the `req-17` / `req-20` duplicate cause) |
| C4 | every `req-N` / `#req-N` / `#req-N-slug` reference resolves |

C1's exemption is by **marker** (`pre-this-change`, `histor`, `原`, a prior
commit id, `was`, `before`, `→`) rather than a registry, matching the house
style of `lint_no_source_field_drift.py` and keeping the exemption surface
visible in the document.

C1 must not match technical labels. The lint reuses the census detector rather
than re-implementing it, so the detector stays in one place and the Scenario
"A technical label is not a line reference" is testable.

**C2 needed a subtlety**: a block anchor sits *inside* a Requirement, so a naive
"anchor delimits a block" rule truncated `req-20` at its MCI row and silently
dropped all 14 of its Scenarios. Block boundaries are therefore anchors whose
next non-empty line is a `### Requirement:` heading. This was caught by the
block diff, not by inspection.

**Regression validity**: the lint must report red against the pre-change tree
and green against the post-change tree. A check that passes on the existing 117
is broken, not helpful.

### D8 — AC-63 gets an explicit guard, and the audit's magnitude was wrong

`req-15` claims the `arctan(pi / sqrt(d_c))` invariant was "restated under
Requirement 'Centroid Driver Semantic Invariants' (req-16) and enforced by the
corresponding named test scenario". `req-16` has no such invariant and
`arctan` has zero hits in `src`/`tests` (positive control:
`canonical_voronoi_angle` = 35 hits, so the zero is real, not a broken counter).

There were three readings on the table:

1. the guard is missing → add one;
2. the invariant is *implicitly* locked by `test_voronoi_canonical_N_e_dependence`
   plus the three 6dp value pins, so this is a pointer bug, not a guard bug
   (`.audit/wayfinder-opsx-code-review/context/05-mutation-evidence.md`);
3. both.

`evidence/ac63_numeric_verification.py` computes the discriminating magnitude
from first principles. Substituting the forbidden closed form moves the result
outside the normative `abs=1e-6` literal guard by **5.08e5×** (N_e=16),
**5.00e5×** (17), **3.55e5×** (64) — so the existing literal pins *do*
discriminate. The plan forbade importing the audit's `5.08e5 / 3.55e5 / 1.53e5`;
only the first agrees, so the audit figure is **partly unreproducible** and is
not used.

**This change adopts reading 3**: keep the value pins *and* add the explicit
named guard, because `CLAUDE.md` §6 holds that a prose assertion is not a
verifiable clause. The value pins answer "is the number right?"; they never
name the forbidden form, so nothing prevents its re-introduction. The new
Scenario states the substitution margin explicitly so the guard discriminates
rather than merely passing.

Two errors were caught and fixed while producing this evidence, both of the
"confidently wrong number" kind and both worth recording:

- the residual-frame check called `_betainc_regularized(a, b, x)`; the
  signature is `(x, a, b)`. The wrong call returned a plausible-looking
  residual of **0.44**. With the correct order the residuals are
  `1.74e-14` / `1.59e-14` / `2.67e-15`, all `< 1e-9`.
- the audit's unexplained **"3.58"** is `3.58e-16`, the quadrature error
  reported in `sphere._betainc_regularized`'s own docstring at θ = 82.6036°.
  It was swept into the arctan zero-hit check, so its absence proved nothing
  about arctan. It is not used in any assertion.

### D9 — the delta is script-generated, and the harness must fail loudly

`openspec instructions specs` requires a `MODIFIED` block to carry the whole
Requirement. This repo has Requirement bodies of 15 413 chars with a single
6 691-char line, so hand-transcription is both impractical and unsafe.
`evidence/gen_deltas.py` extracts each block from the live spec by anchor,
applies pointer edits, emits the delta, and `evidence/verify_deltas.py`
re-derives every block from the delta and diffl-unifies it against the live one.

The harness earned its keep. It caught **five** distinct classes of defect during
this run, none of which inspection would have found:

1. **Block anchors truncate their own Requirement.** Inserting
   `<a id="req-20-mci">` made it a block boundary, so `req-20` was emitted with
   **0 of its 14 Scenarios** and no Source field. Fixed by accepting an anchor
   as a boundary only when the next non-empty line is a `### Requirement:`
   heading.
2. **Truncated replacements.** `replace_line` swaps the *whole* line, and three
   replacements supplied only a tail fragment — silently destroying the rest of
   the line (`wayfinder` req-2 1766→374 chars, `skeleton` req-16 297→178,
   `skeleton` req-21 ×3). Two were caught by the Source-field and Scenario
   checks; the `req-2` one surfaced only as an unrelated-looking RFC-2119
   warning. Fixed by adding a **length-collapse check** (any replaced line that
   shrinks below 70% of its original is reported) and by introducing
   `substitute_line`, which rewrites one bounded pointer token and carries the
   surrounding prose over verbatim — removing hand-transcription for that class
   entirely.
3. **A built-but-unregistered block.** `req-23` was computed and never added to
   the build dict, so its 5 pointer fixes would have silently not shipped.
4. **The contract violating itself.** The new governance Requirement quoted real
   line pointers as examples of what to reject, so C1 flagged its own text.
   Fixed by using placeholder notation.
5. **A claim about the repo that is false.** `req-gov-5` was already taken by
   "Numeric Literal Provenance in Specs" at `governance` L175. The new
   Requirement is `req-gov-6`; colliding would have reintroduced precisely the
   duplicate-anchor defect this change exists to close.

The residual-pointer scan (re-running the census classifier over the generated
deltas) is the check that catches a *partial* sweep, which is the failure mode
that let this family return five times. It must stay part of the harness.

### D10 — Fail-loud harness, not fail-quiet

The census's first self-check asserted `all(...)` over a result that was empty,
where `all([])` is vacuously `True` — the check reported success while the
detector was completely broken and had found **0 pointers**. The check now
asserts the count first and aborts the run. A harness that can report green
while measuring nothing is worse than no harness, because it is believed.

| risk | severity | mitigation |
|---|---|---|
| Governance ticket-annotation form conflicts with C1 | high | D6: changed in the same batch as C1; lint turns green only after the sweep |
| 97-site migration is large and review-heavy | high | one commit per file group; each group independently verified |
| C1's historical-marker word list is a tuning knob | medium | narrow word list false-positives (governance `pre-this-change`); wide one leaks. Tune against real lines in §4.1 and record the marker for every exemption |
| Detector recall/precision tension | medium | biased toward recall (bare `line <n>` accepted even without a capability token, tagged weak) because under-inclusion is what let the family return five times; over-inclusion only costs triage |
| Another session edits the same specs | high | exclusive file list; confirm its work is committed before starting; never `git add .` |
| Lint turns red mid-migration | medium | lint is added and turned green only after the sweep completes (gate ordering) |

## Migration Plan

1. Mint the two block anchors in `req-20` and add its "single canonical source"
   Scenario; remove `req-36` and land its four guarantees in `req-20` (one) and
   `governance` `req-gov-2` (three); strip the two anchor literals quoted in
   prose (C2/C3).
2. Apply the `governance` delta (D6) — it is a prerequisite for a green C1.
3. Sweep the 97 actionable sites, per file, guided by
   `evidence/pointer_census.json`. src/tests edits are comments and docstrings
   only; no assertion value, no signature, no constant changes.
4. Add `test_canonical_voronoi_angle_not_arctan_shortcut` (D8).
5. Write the lint + its tests, then wire it into the `CLAUDE.md` §3 archive
   precondition. **Only now** may it be expected to pass.
6. Run all three lint gates, `pytest`, and `openspec validate --strict`.

## Open Questions Deferred

- Whether the two existing ticket annotations in `wayfinder/tickets/A8-2.md`
  should be modernised. This change keeps them (historical record); a future
  change may rewrite them, at the cost of altering the ticket audit trail.
- Whether `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` may be
  edited to correct its own 0-based coordinates and baseline fields. This
  change appends an Errata section rather than rewriting entries; if the audit
  directory is treated as a read-only snapshot, the corrections move into this
  change's `evidence/` instead.
