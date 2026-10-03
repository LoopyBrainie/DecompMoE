## MODIFIED Requirements

<a id="req-gov-8"></a>

### Requirement: Gate Result Must Be Reproducible

A gate run MUST record `git rev-parse HEAD` and three content-sensitive components: the committed base (`git rev-parse HEAD`), a digest of the *content* of every tracked modification staged or unstaged (`sha256(git diff HEAD)`), and a digest of every untracked file's bytes enumerated individually, so that a new file inside an untracked directory counts
before executing, and MUST re-verify both after the last gate completes. If either
differs, the run MUST be reported as INVALID — a state distinct from both pass and
failure. An archive MUST be gated against a quiesced worktree, because a green result
computed over a tree that changed mid-run describes content that no longer exists. A digest of `git status --porcelain` does not satisfy this Requirement: porcelain encodes a path and a status letter, not content, so two worktrees differing only in the bytes of an already-dirty file produce byte-identical porcelain and therefore a byte-identical digest.

**Source:** `CLAUDE.md` §3 (Workflow Conventions), change
`2026-10-03-a5-archive-gate-executability` design.md (Decision D2 — exit code 2 reserved
for an unstable worktree)

#### Scenario: The worktree changes while the gates run

- **WHEN** the post-run `git rev-parse HEAD` or worktree digest differs from the pre-run value
- **THEN** the entry point MUST report `GATE RESULT INVALID`
- **AND** it MUST exit with a code distinct from both the pass code and the violation code
- **AND** it MUST NOT print a pass summary for that run

#### Scenario: A dirty state with an unchanged file count is still a change

- **GIVEN** two different dirty worktrees that contain the same number of changed entries
- **THEN** the run MUST still detect the change
- **AND** the comparison MUST NOT rely on a changed-entry count alone

#### Scenario: A stable run is reported normally

- **WHEN** every gate completes and the pre-run and post-run snapshots are identical
- **THEN** the result MUST be reported as pass or violation according to the gates alone

#### Scenario: Two worktrees differing only in the bytes of a dirty file

- **GIVEN** one tracked file already modified, whose content then changes again without its path or its status changing
- **THEN** a digest of `git status --porcelain` MUST be identical for both states
- **AND** the run MUST still detect the change, from tracked content rather than from porcelain
- **AND** a derived count of changed entries MUST NOT be treated as an independent signal, because it is a coarser function of the same porcelain string

## REMOVED Requirements

### Requirement: Spec Anchor Ledger Across Archive

**Reason**: The Requirement's central Scenario was titled "Point-in-time coverage cannot detect the archive defect" and its body asserted that after a swallow "the anchor count and the Requirement-heading count remain equal" and a point-in-time check "MUST still report the tree as fully covered". Measured, both halves are false: removing one anchor line from a spec with 9 Requirement headings leaves 8 anchors, and the coverage check reports the uncovered Requirement. A Scenario title cannot be corrected in place, because `MODIFIED` blocks must retain the existing Scenario headings verbatim or the archive refuses to drop them -- so a spec that kept the old title would contradict its own body.

**Migration**: Superseded by `req-gov-10`, which carries the same archive-procedure obligations with the false premise replaced by the measured behaviour, and adds the two defects a count-based check provably cannot see (an anchor id re-attached to a different Requirement, and a section sub-anchor miscounted as a declared addition). Cross-references to `req-gov-9` in `CLAUDE.md` and in `scripts/run_gates.py` were updated to `req-gov-10` in the same change.

## ADDED Requirements

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
it introduced, in a list separate from the declared-but-never-added one.

**Source:** `CLAUDE.md` §6 (Hard Constraints — the 100% anchor coverage clause), change `2026-10-03-a5-archive-gate-executability` design.md (Decision D4 — a ledger, not a point-in-time count), corrected by change `2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D2 — the D4 premise was measured and is false)

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

**Source:** `CLAUDE.md` §3 (Source 反链 requirement) and §6 (the ban on unverifiable clauses), change `2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D4 — grandfather, do not fabricate lineage)

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
