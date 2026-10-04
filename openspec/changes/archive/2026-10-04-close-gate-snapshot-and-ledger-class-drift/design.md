# Design

## Context

See `proposal.md` — Why / What Changes for motivation. This document records the
technical decisions behind the three fixes and the reasoning that the change record
must not overstate.

All three defects share one shape: an invariant was written down in more than one
place, the code drifted from it, and in two of the three cases a test asserts the
drifted behaviour.

All evidence in this change was collected against `HEAD = 5f3e286` on branch `dev`,
and that revision is named here so the observations can be re-derived rather than
taken on trust. `dev` has since advanced under concurrent sessions (`c7137ef`,
`fb79453`); the three findings were re-confirmed present and unchanged against those
later revisions, and none of them depends on the intervening commits, which touched
`scripts/lint_pointer_detector.py`, `scripts/pointer_scan.py`,
`tests/test_pointer_scan.py`, and `wayfinder/` only.

## Goals / Non-Goals

**Goals**

- Make the code match the invariant that is already written down, in the direction
  the written invariant points. Where a spec and a docstring already agree, neither
  is edited.
- Restore the reverse-link path from `CLAUDE.md` to a Requirement that actually
  carries the clause it is credited with.
- Leave every test asserting a *contract* rather than a *current implementation*.

**Non-Goals** (see `proposal.md` for the full list with rationale)

- No new Requirement, hence no new anchor, hence no anchor-numbering collision.
  `req-gov-9` is a historical gap left by an earlier removal and is deliberately not
  reused: a reused id would make old references to the retired Requirement resolve
  to a different one.
- No file under `openspec/changes/archive/**` is modified.
- No change to the key set returned by `worktree_snapshot()`.

## Decisions

### D1 — A deliberate anchor removal is a third class, not a loss

**Decision.** `req-gov-10` gains a third report class, `removed`, defined alongside
the existing `lost` and `never-added`.

**Rationale.** The behaviour already exists in code and is covered by three tests.
The spec defines two classes, so the code has no requirement authorising it — the
worst combination available: behaviour that is argued for, pinned by tests, and
required by nobody. The fix belongs in the spec, not in the code.

**Alternatives considered.**

- *Fold "three classes" into the existing `Lost and never-added are separate classes`
  Scenario.* Rejected: the validator requires a `MODIFIED` block to keep existing
  Scenario titles character-for-character, and that title is literally about two
  classes. Rewriting it is not available; a new Scenario is.
- *Delete the behaviour and the three tests.* Rejected: the behaviour is correct.
  A `## REMOVED Requirements` block carries no anchor of its own, so without the
  exclusion every removal-architecture change emits a false "restore surgically, do
  NOT re-run archive" instruction forever — and obeying that instruction would
  resurrect a Requirement the change deliberately deleted. The gate would cry wolf
  on a whole class of legitimate changes, which trains readers to ignore it.
- *Treat the removed set as a filter applied to `lost` with no separate report.*
  Rejected: the existing test `test_genuine_loss_is_still_reported_when_a_removal_is_also_declared`
  requires a genuine loss alongside a declared removal to surface both. Silent
  filtering would also hide the exclusion itself, leaving a reader unable to tell a
  clean archive from a filtered one.

**Scope note.** The removed-id lookup MUST stay scoped by capability. Anchor ids are
per-capability; an unscoped match against another capability's ledger is not a hit.
The spec states this because the flat-set version of this bug shipped once already.

### D2 — Slice the Source-field body at the match end, never at a fixed length

**Decision.** `req-gov-11` gains the slicing invariant that `CLAUDE.md` already
attributes to it, plus a Scenario pinning it.

**Rationale.** The clause lives in the gate implementation and in `CLAUDE.md`, and in
no Requirement. Because `CLAUDE.md` is the reverse-link target for every `governance`
Requirement, a reader who follows the pointer to `req-gov-11` finds nothing, and the
one artefact that documents the rule cannot be traced to anything checkable. The
spec is the fix: adding the clause makes the existing attribution correct, and
spec outranks prose under `CLAUDE.md` §2. Editing `CLAUDE.md` to re-point elsewhere
was rejected for the same reason — it would leave the invariant documented in
implementation and in prose but still unowned.

**Alternatives considered.**

- *Re-point `CLAUDE.md` to a different Requirement.* Rejected: no other Requirement
  contains the clause, so there is nothing to point at. The search over the whole
  `governance` spec for `SOURCE_LINE_RE`, the match-end wording, and the offset
  wording returns zero hits.
- *Delete the clause from `CLAUDE.md` as unspec'd detail.* Rejected: it is a real
  invariant with a real failure mode. A fixed-length slice cuts a
  `> **Source:**` field at the wrong offset and reports a correctly formed field as a
  violation — a false positive that would force a source field to be rewritten in a
  form the gate still rejects.

### D3 — Separate "recorded" from "compared" rather than deleting the field

**Decision.** `status_lines` is removed from the tuple compared in
`_snapshot_differs` and is still returned by `worktree_snapshot()` and still printed
as `dirty_entries=`.

**Rationale.** Three independent artefacts already agree that the derived count must
not act as an independent signal: the `req-gov-8` Scenario, the `worktree_snapshot`
docstring ("deliberately *not* among them"), and the upstream design decision
("不参与判等"). The code was the sole dissenter, so there is no design choice to make
— only a code edit. The one genuine design question is *how far* to remove it, and
the two ends of that range are not equivalent:

- *Delete the field entirely.* Would also remove the human diagnostic that tells a
  reader how busy the tree was when a run comes back INVALID, and would break
  `test_worktree_snapshot_has_all_components`, which asserts the four-key set. That
  test is asserting a reasonable contract; the count is worth keeping precisely
  because it is excluded from comparison.
- *Keep it in the tuple and add a spec clause permitting it.* Rejected: it would
  contradict `req-gov-8` as already written, and the code's own docstring. The fix
  would be a third document asserting what two documents deny.

The comment added at the comparison site states the exclusion at the place a future
reader edits, because the docstring's word "deliberately" is exactly the kind of
claim that decays when the next person cannot reconstruct the reasoning.

**Limits of this decision, stated honestly — and a correction.** An earlier draft of
this document justified the removal by saying `status_lines` "is a strictly coarser
function of the same porcelain string, so it adds no information the compared signals
do not already carry." **That argument was malformed in two ways and is withdrawn.**

1. It is self-referential. `status_lines` *is* the length of the porcelain string it is
   derived from, so calling it a coarser function of that string says nothing.
2. Repaired to mean the compared digests, it becomes *false*. `tracked_digest` is
   `sha256(git diff HEAD)` and `untracked_digest` is
   `sha256(ls-files --others --exclude-standard + per-file bytes)`. Neither is a
   function of the porcelain output — `_tracked_content_digest`'s own comment says
   porcelain encodes path and status letter, not content. Coarser-function redundancy
   only holds between signals sharing one source, and these do not share one.

The argument that actually holds is a **surjectivity** claim: every porcelain line
denotes a change event that at least one compared digest already reflects, so the line
count is determined by a multiset the digests already determine. That is a statement
about how three specific git commands behave together.

It was tested. A harness replaying 11 state transitions against verbatim copies of the
digest functions found **zero counterexamples** — no transition moved `status_lines`
with `head`, `tracked_digest`, and `untracked_digest` all fixed. The two least obvious
transitions, `--assume-unchanged` and `--skip-worktree` applied to an already-dirty
file, both moved the line count *and* both moved `tracked_digest`.

So the **conclusion survives and the reasoning did not**, which is the point worth
recording: a correct result reached by a broken argument is one refactor away from
being "corrected" in the wrong direction. The status remains *empirically supported,
not proven* — a finite transition set is not a proof over all worktree states. The
regression test added in `tasks.md` therefore asserts the contract directly rather than
asserting the absence of a hypothetical counterexample, so the guard does not depend on
this argument being complete.

The malformed sentence was also copied into two comments in `scripts/run_gates.py`
(the `worktree_snapshot` docstring and the comparison site). Both now carry the
surjectivity form and the "empirical, not a theorem" caveat, because a comment that
states a wrong reason is worse than no comment: the next reader reconstructs the wrong
reasoning and trusts it.

### D4 — Correct the ledger summary line together with the spec

**Decision.** The summary line printed when any class is non-empty changes from
"these two classes" to "these three classes".

**Rationale.** This is the same defect as D1 seen from its other side, and it was not
in the original review. The code distinguishes three classes, and a summary that says
two contradicts the tool's own vocabulary — while being the one line a reader is
guaranteed to read. Correcting `req-gov-10` while leaving this line would make the
change half-done in the most visible place: the spec would define three classes and the
tool would still tell its user there are two.

Note the three labelled lists are each **conditional** (`if lost:` / `if
expected_removals:` / `if never_added:`), so a lost-only run prints one list and still
says "three". That is correct — the sentence is a statement about how many classes the
report can distinguish, not a count of what a given run happened to print. The test for
it therefore derives the expected number from the lists the code actually emitted
rather than hard-coding a word.

## Risks / Trade-offs

- **[A `MODIFIED` block that rewrites an existing Scenario title makes the archive
  refuse to run]** → Mitigation: the six `req-gov-10` and three `req-gov-11` titles
  are copied character-for-character from the live spec, and the delta is verified
  against the live spec by script before the archive is attempted, not by eye.

- **[Correcting the test that pins the violation could be mistaken for weakening
  coverage]** → Mitigation: the corrected test keeps its original intent — every
  *compared* field is named — and a new test is added for the case the old assertion
  got wrong. Net test count rises; none is deleted.

- **[Touching an archived file would break the freeze established by `5f3e286`]** →
  Mitigation: the proposal states the freeze as a Non-goal, and the change is checked
  for archive-path modifications before commit.

- **[Running the gate while commands that create untracked files are in flight makes
  the run report INVALID with exit 2]** → Mitigation: the untracked-file set is
  enumerated before the gate runs and no artifact-producing command is interleaved.
  A `GATE RESULT INVALID` must never be read as a pass.

- **[Three unrelated-looking findings bundled into one change make review harder]**
  → Mitigation: they share one gate, one ledger flow, and one review round, matching
  the `fix-a5-review-findings-round-2` / `fix-a6-artifact-fidelity-round-2` precedent
  in this repository.

## Migration Plan

None. This change touches no persisted data, no CLI surface, and no public API. The
snapshot key set is unchanged, so any consumer of `worktree_snapshot()` continues to
receive the same four keys. The behaviour change is confined to what the gate
*compares*, which only affects the INVALID verdict in the case D3 describes.

## Open Questions

- `CLAUDE.md:38` may warrant a trailing reference to this change once the clause is
  owned by `req-gov-11`. This is cosmetic and depends on whether
  `lint_no_source_field_drift.py` demands a more specific reverse-link form for
  `governance`; the gate run answers it. It does not change the specs, the approach,
  or the task breakdown either way.
