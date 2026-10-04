# Proposal

## Why

A post-archive review of change `2026-10-03-a5-archive-gate-executability` surfaced
three contract-versus-code drifts in the governance gate layer. Two of them are
latent rather than actively wrong, but all three are the same failure mode: a piece
of prose in `CLAUDE.md` or in a spec states an invariant, the code does something
else, and in two cases a test pins the wrong behaviour so it cannot be corrected
without first changing the test. Fixing them now, while the code that owns them is
still the one that shipped, is cheaper than discovering the same divergence after a
later change inherits these functions.

The three are:

1. **`status_lines` is compared although three separate artifacts say it must not
   be.** `governance` `req-gov-8` states that a derived count of changed entries
   MUST NOT be treated as an independent signal; `worktree_snapshot()`'s own
   docstring states it is "deliberately *not* among them"; the upstream `design.md`
   records the decision as "不参与判等". The code puts it in the compared tuple
   anyway. Three independent statements of intent, one dissenter.
2. **The anchor ledger reports three classes; the spec defines two.** A deliberately
   removed anchor (one the change's `## REMOVED Requirements` block deleted) is
   reported separately from a lost anchor and from a declared-but-never-added anchor,
   and is covered by three tests — but `req-gov-10` names only two classes, and the
   human-facing summary line still says "these two classes".
3. **A `CLAUDE.md` invariant has no Requirement to trace back to.** The
   `SOURCE_LINE_RE` / match-end-offset slicing rule is attributed to `req-gov-11`,
   whose text does not contain it, and it belongs to no other Requirement. Since
   `CLAUDE.md` is the reverse-link target for every `governance` Requirement, a
   reader following the pointer lands on nothing.

## What Changes

- **`scripts/run_gates.py` — remove `status_lines` from the snapshot-comparison
  tuple.** The field is still *recorded* (and still printed as `dirty_entries=`) so
  the human diagnostic survives; it is no longer *compared*. Recording and comparing
  are separated rather than the field being deleted.
- **`scripts/run_gates.py` — correct the ledger summary line** from "these two
  classes" to "these three classes", so the only line a reader sees stops
  contradicting the code above it.
- **`governance` `req-gov-10` — define the third class.** A deliberately removed
  anchor MUST be reported in its own labelled list and MUST NOT appear in the lost
  list, because restoring the anchor of a Requirement the change deliberately
  deleted is itself wrong. Adds one Scenario; preserves all six existing Scenario
  titles verbatim.
- **`governance` `req-gov-11` — add the missing Source-field slicing invariant.**
  The field body MUST be sliced at the end of the match on the field pattern, not at
  a fixed length. Adds one Scenario; preserves all three existing Scenario titles
  verbatim.
- **`tests/test_run_gates.py` — stop pinning the violation and pin the contract
  instead.** The existing `test_snapshot_differs_names_every_moved_field` asserts
  four compared fields including `status_lines`; it is corrected to three, and a new
  regression test asserts that a moved derived count alone reports no movement. A
  third assertion pins the summary line to the number of classes the code actually
  distinguishes.

No breaking change: no public API, no CLI surface, and no Requirement id is added,
removed, or renumbered.

## Capabilities

### New Capabilities

None. This change adds no new system behaviour, and `openspec validate` rejects a
change whose only justification for a new requirement would be satisfying
validation.

### Modified Capabilities

- `governance`: two Requirements change at spec level.
  - `req-gov-10` (Spec Anchor Ledger Survives Archive And Names Every Loss) — the
    report distinguishes three anchor classes; the spec says two.
  - `req-gov-11` (Spec Requirements Carry A Source Field) — gains the
    match-end-offset slicing invariant that `CLAUDE.md` already attributes to it.

## Impact

- **Code**: `scripts/run_gates.py` — `_snapshot_differs` (compared-key tuple) and the
  `anchor-ledger --verify` summary line. `worktree_snapshot()`'s return key set is
  deliberately unchanged.
- **Tests**: `tests/test_run_gates.py` — one existing assertion corrected, one
  regression test added, one assertion added to an existing test.
- **Specs**: `openspec/changes/<name>/specs/governance/spec.md` (delta only, two
  `## MODIFIED Requirements` blocks).
- **No change to**: `CLAUDE.md` (the existing attribution becomes correct once
  `req-gov-11` actually carries the clause — spec outranks prose per `CLAUDE.md` §2),
  `worktree_snapshot()`'s key set, the anchor-ledger JSON artifacts, and any file
  under `openspec/changes/archive/`.

### Non-goals

- **This change does not touch `openspec/changes/archive/**`.** Commit `5f3e286`
  established that an archived change must not be modified, admitting no exception
  for "only appending an errata". Two findings from the same review point at
  archived files and are therefore recorded here as adjudications rather than
  repaired in place:
  - The `evidence/incident.md` of `2026-10-03-a5-archive-gate-executability` names
    only revision `940b27c`, while its own surviving ledger JSONs record
    `written_at_head: 850ed8a…`. The numbers are right; the provenance is half
    recorded.
  - The same change's `design.md` E3 quotes counts ("strict 48 / loose 48") without
    naming the revision they were observed on, which the same section's own rule
    ("没有 revision 的记录无法被追认或推翻") requires. (The review attributed these
    numbers to D5/D7; they are in E3.)
  Both are left for a separate, explicitly authorised change.
- **The E5 "known unprocessed" list is not edited.** The premise was that all three
  registered changes are now closed; that is false — only one of the three is
  archived, and two remain live under `openspec/changes/`. The list is accurate and
  the file is frozen.
- **The blank lines the archive `ea802c8` inserted between six out-of-scope
  `wayfinder` blocks are not reverted.** They are whitespace-only, they are part of a
  committed archive, and reverting them would create a fresh divergence from the
  archived product.
