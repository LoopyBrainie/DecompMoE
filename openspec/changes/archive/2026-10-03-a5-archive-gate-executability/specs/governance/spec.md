## ADDED Requirements
<a id="req-gov-7"></a>
### Requirement: Archive Gate Must Be Executable

Every gate named as an `/opsx:archive` precondition MUST be a runnable command, MUST
exit non-zero on a tree that carries the defect class it claims to detect, and MUST be
reachable from a single named entry point. `CLAUDE.md` §3 MUST NOT enumerate individual
lint scripts: a list that must be edited by hand whenever a lint is added can and does
drift out of step with the scripts actually present, and a drifted list is a gate that
silently covers nothing.

**Source:** `CLAUDE.md` §3 (Workflow Conventions — the `/opsx:archive` precondition clause),
change `2026-10-03-a5-archive-gate-executability` design.md (Decision D1 — glob discovery
replaces enumeration)

#### Scenario: The gate list is not a separate list

- **WHEN** a new lint is added under `scripts/`
- **THEN** it MUST become part of the archive precondition without any edit to `CLAUDE.md`
- **AND** the precondition MUST name one entry-point command, not a per-script list

#### Scenario: A gate that cannot fail is not a gate

- **WHEN** the entry point discovers zero lints
- **THEN** it MUST exit non-zero
- **AND** it MUST NOT report a pass on the grounds that no discovered lint reported a violation

#### Scenario: The change being archived is validated as a change

- **WHEN** the archive precondition runs for a change with no spec delta and no `skip_specs`
- **THEN** the entry point MUST exit non-zero
- **AND** the reported cause MUST name the missing delta or the missing `skip_specs` marker
- **AND** the check MUST be scoped to the change being archived, so that unrelated stale changes in the same directory do not determine the result

<a id="req-gov-8"></a>
### Requirement: Gate Result Must Be Reproducible

A gate run MUST record `git rev-parse HEAD` and a digest of `git status --porcelain`
before executing, and MUST re-verify both after the last gate completes. If either
differs, the run MUST be reported as INVALID — a state distinct from both pass and
failure. An archive MUST be gated against a quiesced worktree, because a green result
computed over a tree that changed mid-run describes content that no longer exists.

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

<a id="req-gov-9"></a>
### Requirement: Spec Anchor Ledger Across Archive

`openspec archive` MUST leave the spec anchor ledger unchanged. The archive procedure
MUST be: write the ledger, archive, compare the ledger, restore any lost anchor
surgically, re-verify. Re-running the archive MUST NOT be used to repair a lost anchor,
because a second archive overwrites the first repair. A lost anchor MUST be reported by
id and by the Requirement it introduced, and MUST be listed separately from a declared-but-
never-added anchor, since the two are indistinguishable from raw counts alone.

**Source:** `CLAUDE.md` §6 (Hard Constraints — the 100% anchor coverage clause),
change `2026-10-03-a5-archive-gate-executability` design.md (Decision D4 — a ledger, not a
point-in-time count)

#### Scenario: Point-in-time coverage cannot detect the archive defect

- **WHEN** the archive drops the anchor of the Requirement following the one it rewrote
- **THEN** the anchor count and the Requirement-heading count remain equal
- **AND** a point-in-time coverage check MUST still report the tree as fully covered
- **AND** only a before/after ledger comparison MUST name the lost anchor

#### Scenario: Lost and never-added are separate classes

- **GIVEN** a baseline ledger, one anchor that disappeared, and one anchor the change declared it would add but which is absent
- **THEN** both MUST be reported
- **AND** they MUST appear in separate labelled lists
- **AND** a report giving only the net count MUST be treated as insufficient

#### Scenario: A block boundary requires the Requirement heading to follow the anchor

- **WHEN** a standalone anchor line is followed by a blank line and prose rather than a `### Requirement:` heading
- **THEN** it MUST NOT be treated as a Requirement block start
- **AND** an anchor quoted inline inside prose MUST NOT be counted as a Requirement header

#### Scenario: Repairing a lost anchor

- **WHEN** the ledger comparison reports a lost anchor
- **THEN** the anchor and its following blank line MUST be restored by direct edit
- **AND** the archive MUST NOT be re-run as the repair mechanism
