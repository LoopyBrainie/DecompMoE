# Delta extraction evidence

**HEAD**: `3c64cdc`. The two MODIFIED blocks that carry the SP semantics are
reproduced from the main specs **mechanically**, not transcribed by hand: a
script slices each Requirement out of `openspec/specs/<capability>/spec.md`
between top-level anchors (`^<a id="req-\d+"></a>$` — sub-anchors such as
`req-20-mci` and `req-20-source` are explicitly excluded, an exclusion the
first extractor got wrong) and appends the new Scenarios at the block tail.

## Byte-identity check

| capability | anchor | main-spec lines | nonblank lines (main) | nonblank lines (delta) | verdict |
|---|---|---|---|---|---|
| `wayfinder` | `#req-20` | 462–572 | 90 | 90 | **BYTE-IDENTICAL** |
| `decompmoe-skeleton` | `#req-22` | 560–645 | 55 | 55 | **BYTE-IDENTICAL** |

Every line of the original block is reproduced verbatim, so the `#req-23`
requirement — that `decompmoe-skeleton` `#req-22` mirrors `wayfinder` `#req-20`
— cannot be silently broken by transcription drift. The appended tail is
byte-identical between the two capabilities for the same reason.

## `#req-30` scenario preservation

OpenSpec's MODIFIED block **replaces** the whole Requirement, and
`openspec validate` refuses any block that drops a scenario the current spec
has. Scenario names before:

- `gradient bound is tight at orthogonal unit vectors`
- `gamma-gradient bound is tight at antipodal config`

after:

- `gradient bound is tight at orthogonal unit vectors`
- `the boundary value is the supremum, not any finite-gamma value`
- `the derivative carries no ‖C‖ factor and is angle-independent`
- `gamma-gradient bound is tight at antipodal config`

All 2 original scenario names are preserved: True. The
`gradient bound is tight at orthogonal unit vectors` scenario asserts
`‖∂logit/∂C‖₂ == 32.0` at `β = β_max`, which coexists with the corrected
"supremum" body only because a companion scenario separates the two readings —
evaluating at the closed-range **boundary value** `β = β_max` (the scenario, = 32.0)
versus any **finite-γ-reachable** `β` (strictly `< 32.0`).

Overall byte-identity verdict: **PASS**.
