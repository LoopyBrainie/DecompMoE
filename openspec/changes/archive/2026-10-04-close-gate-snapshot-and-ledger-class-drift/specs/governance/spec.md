# Spec Delta — `governance`

## MODIFIED Requirements

<a id="req-gov-10"></a>

### Requirement: Spec Anchor Ledger Survives Archive And Names Every Loss

`openspec archive` MUST leave the spec anchor ledger unchanged. The archive
procedure MUST be: write the ledger, archive, compare the ledger, restore any lost
anchor surgically, re-verify. Re-running the archive MUST NOT be used to repair a
lost anchor, because a second archive overwrites the first repair.

A point-in-time coverage check MUST NOT be treated as sufficient on its own. It
does detect a swallowed anchor, because a swallow removes one Requirement's
block-start anchor while leaving the heading count alone, and a simultaneously
added Requirement carries its own anchor, so the deficit cannot be cancelled. What
it cannot do is name anything: it reports a per-capability deficit rather than the
anchor id or the Requirement that lost it, it cannot see an anchor id that
survived but was re-attached to a different Requirement, and it cannot separate a
lost anchor from one the change declared and never added. The ledger comparison
MUST supply those three, and MUST report a lost anchor by id and by the Requirement
it introduced, in a list separate from the declared-but-never-added one and from the
deliberately-removed one.

A deliberately removed anchor is a **third** class, distinct from both of the
others. A `## REMOVED Requirements` block carries no anchor of its own — the block
is a Requirement heading plus Reason and Migration — so the removed anchor id MUST
be recovered by matching the removed Requirement's title against the *baseline*
ledger, never by taking the delta's own word for it: the ledger exists to report
what the archive actually did, not to re-assert what the delta asked for. A
deliberately removed anchor MUST NOT be reported as lost. Reporting it would emit a
permanent false "restore surgically, do NOT re-run archive" instruction, and
following that instruction is itself wrong — restoring the anchor of a Requirement
the change deliberately deleted resurrects a Requirement that was supposed to be
gone. The lookup MUST be scoped by capability, because anchor ids are
per-capability and an unscoped id match against another capability's ledger MUST NOT
be treated as a hit. A deliberate removal MUST still be disclosed in its own
labelled list even when it accompanies a genuine loss, so that the exclusion cannot
be applied over-broadly. When any of the three classes is non-empty, the report MUST
state that counts alone cannot separate **three** classes, not two.

**Source:** `CLAUDE.md` §6 (Hard Constraints — the 100% anchor coverage clause), change `2026-10-03-a5-archive-gate-executability` design.md (Decision D4 — a ledger, not a point-in-time count), corrected by change `2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D2 — the D4 premise was measured and is false), extended by change `2026-10-04-close-gate-snapshot-and-ledger-class-drift` design.md (Decision D1 — a deliberate removal is a third class, not a loss)

#### Scenario: A swallowed anchor is a count deficit, not an invisible loss

- **WHEN** the archive drops the anchor of the Requirement following the one it rewrote
- **THEN** the Requirement-heading count and the block-start anchor count diverge
- **AND** a point-in-time coverage check MUST report the uncovered Requirement
- **AND** the deficit MUST NOT be cancellable by any simultaneous addition, because an added Requirement carries its own anchor and moves both counts together

#### Scenario: Naming what a count cannot

- **GIVEN** a baseline ledger and a current ledger taken across one archive
- **THEN** a before/after comparison MUST name each lost anchor id and the Requirement title it introduced
- **AND** it MUST report an anchor id whose id is unchanged but whose introduced title changed, which a count-based check reports as fully covered
- **AND** only a before/after comparison is permitted to make that claim

#### Scenario: Lost and never-added are separate classes

- **GIVEN** a baseline ledger, one anchor that disappeared, and one anchor the change declared it would add but which is absent
- **THEN** both MUST be reported
- **AND** they MUST appear in separate labelled lists
- **AND** a report giving only the net count MUST be treated as insufficient

#### Scenario: A block boundary requires the Requirement heading to follow the anchor

- **WHEN** a standalone anchor line is followed by a blank line and prose rather than a `### Requirement:` heading
- **THEN** it MUST NOT be treated as a Requirement block start
- **AND** an anchor quoted inline inside prose MUST NOT be counted as a Requirement header

#### Scenario: A section sub-anchor is not a declared Requirement

- **GIVEN** an `## ADDED Requirements` delta block whose Requirement also carries a block-level section anchor such as `req-20-mci`
- **THEN** only the anchor that introduces the `### Requirement:` heading MUST be collected as a declared addition
- **AND** the section anchor MUST NOT be reported as a declared-but-never-added anchor, because the declared set is compared against block starts, which never contain it

#### Scenario: Repairing a lost anchor

- **WHEN** the ledger comparison reports a lost anchor
- **THEN** the anchor and its following blank line MUST be restored by direct edit

#### Scenario: A deliberately removed anchor is a third class, not a loss

- **GIVEN** a baseline ledger naming a Requirement that the change's `## REMOVED Requirements` block deletes, alongside a genuinely swallowed anchor and a declared-but-absent anchor
- **THEN** the deliberate removal MUST be reported in its own labelled list
- **AND** it MUST NOT appear in the lost list, because restoring the anchor of a deliberately deleted Requirement is itself wrong
- **AND** the report MUST state that counts alone cannot separate **three** classes, not two
- **AND** a removed anchor id that another capability still uses MUST NOT be excluded, because the lookup MUST be scoped by capability

<a id="req-gov-11"></a>

### Requirement: Spec Requirements Carry A Source Field

Every Requirement in a capability spec MUST carry a top-level `**Source:**` field. A
Requirement that ships without one MUST fail the gate. Requirements that predate this
Requirement and have no field MUST be listed in a registry of justified exemptions,
and the registry MUST be an explicit, reviewable list of anchor ids rather than a count
or a prefix, so that a newly authored Requirement without a field fails immediately.

A registry entry MUST record the capability and the anchor id it exempts. An entry that
names an anchor id which no longer exists, or which now carries a field, MUST itself be
reported, so the registry cannot silently outlive the defect it was written to excuse.

The gate MUST locate the `**Source:**` field with a pattern that accepts a leading
indent, a `>` quote marker, or an ordered-list marker ahead of the field, and MUST
slice the field body from the **end of that pattern's match**. A fixed-length slice
MUST NOT be used: because the field marker is not at a constant offset once those
prefixes are permitted, a fixed-length slice cuts the body at the wrong place and
reports a correctly formed field as a violation. A line yielded as a Source-field
line but not matched by the pattern MUST be reported as an internal inconsistency
rather than silently skipped, so a future change to the field generator cannot turn
a body-slicing bug into a silently absent check.

**Source:** `CLAUDE.md` §3 (Source 反链 requirement) and §6 (the ban on unverifiable clauses), change `2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D4 — grandfather, do not fabricate lineage), extended by change `2026-10-04-close-gate-snapshot-and-ledger-class-drift` design.md (Decision D2 — slice the field body at the match end, never at a fixed length)

#### Scenario: A new Requirement without a Source field

- **WHEN** a Requirement is added to a capability spec without a top-level `**Source:**` field
- **THEN** the Source-field gate MUST report the capability and the Requirement title
- **AND** it MUST exit non-zero

#### Scenario: A pre-existing Requirement with no field is exempt by id

- **GIVEN** a Requirement whose anchor id appears in the justified-exemption registry
- **THEN** the existence check MUST NOT report it
- **AND** the registry MUST be reported separately from the violation list, so a green run does not imply full coverage

#### Scenario: A stale exemption is itself a finding

- **GIVEN** a registry entry whose anchor id no longer exists, or whose Requirement now carries a `**Source:**` field
- **THEN** the gate MUST report the stale entry
- **AND** it MUST exit non-zero, so the registry must be pruned rather than accumulate

#### Scenario: The Source field body is sliced at the match end, not at a fixed length

- **GIVEN** a `**Source:**` field preceded by an indent, a `>` quote marker, or an ordered-list marker
- **THEN** the field body MUST be sliced at the end of the pattern match on the field marker
- **AND** a fixed-length slice MUST NOT be used, because it cuts the body at the wrong offset and reports a correctly formed field as a violation
