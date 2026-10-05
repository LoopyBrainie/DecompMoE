# Spec Delta — `governance`

## ADDED Requirements

<a id="req-gov-12"></a>

### Requirement: Ledger Baseline Identity Must Be Declared And Judgmentable

A ledger entry produced by the gate entry point MUST carry a field recording, alongside
the committed base it was written at, **which tree its anchors were read from**. The
field MUST be present on every entry, and MUST NOT be named after the committed base,
because the content a ledger entry actually holds is read from the working tree while
the base it names is read from `git rev-parse HEAD`. On a dirty worktree those two are
**constructionally decoupled**: both values are correct, and the entry is
self-contradictory to any reader who infers the content from the field name.

The field's value is the digest of the working tree's content at write time when the
tree differed from the committed base, and `null` when it did not. `null` is a recorded
value stating that the content **is** the committed base's content — not an omitted
field. Absence of the field is a third, distinct state and means the entry predates the
contract.

A comparison whose baseline is reconstructed **from the committed base alone** MUST NOT
return a pass or a violation when the entry's declared baseline is the working tree, and
MUST NOT return a pass or a violation when the digest field is absent. Both cases MUST
return a third outcome — *unknown* — distinct from both pass and violation. This extends
`req-gov-8`'s rule that a pass and a "do not know" must never be read as the same thing
from the gate layer down to the ledger layer.

The baseline shapes and their verdicts are:

| Entry shape | Declared baseline | Permitted verdict for a HEAD-only comparison |
|---|---|---|
| field present, value `null` | the committed base | pass / violation |
| field present, value a digest string | the working tree | **unknown** |
| field present, value of any other type or an empty string | **unknown** | **unknown** |
| field absent (legacy entry) | **unknown** | **unknown** |

Writing a ledger entry MUST NOT be refused because the working tree is dirty. The
archive procedure writes the ledger before the archive runs, at a point where the
change's spec delta has been applied but not yet committed, so a dirty working tree is
the **normal** state of that procedure rather than an anomaly. A digest records which
tree the entry came from; it is a **provenance marker, not a write gate**. Turning it
into a precondition would deadlock the legal procedure.

A count of anchors MUST be qualified by the counting rule that produced it. A bare
count is not self-describing: counting only anchors immediately followed by a
Requirement heading and counting every anchor element yield different totals on the same
tree, and a reader who recomputes with the other rule cannot tell which the number meant.
A legacy entry or prose figure MUST additionally be recorded as *not reconstructible*
when no version-controlled object can rebuild it, so that it is never cited alongside
figures that can be recomputed.

**Source:** `CLAUDE.md` §3 (archive precondition and ledger precondition; "文字断言不构成可验条款" — a text-only obligation is not an enforceable clause), `CLAUDE.md` §6 (bare-`==` for integer closed forms, `pytest.approx(..., abs=...)` for float), change
`2026-10-04-archive-evidence-provenance` design.md (Decision D2 — digest is a provenance marker not a write gate; Decision D4 — the lint's scan target is version-controlled evidence only), change
`2026-10-04-a5-archive-gate-executability` design.md (Decision D2 — `req-gov-8`'s
content-sensitive digests, reused verbatim as the ledger digest recipe)

#### Scenario: The ledger was written while the worktree was dirty

- **WHEN** a ledger entry is written while the working tree has tracked modifications or untracked files
- **THEN** the entry MUST carry a non-empty working-tree content digest
- **AND** the entry MUST NOT be rejected, refused, or skipped
- **AND** a later comparison that reconstructs the baseline from the committed base alone MUST report the outcome as *unknown*, not as a pass and not as a violation

#### Scenario: A legacy ledger entry carries no digest field

- **WHEN** a comparison is run against a file that parses as a ledger entry but has no working-tree digest field
- **THEN** the tool MUST report the outcome as *unknown*
- **AND** it MUST NOT report a pass on the grounds that no rule was violated
- **AND** it MUST NOT report an anchor-level violation on the grounds that the missing field makes the entry malformed

#### Scenario: The input is not a ledger entry at all

- **WHEN** a comparison is run against a file that does not parse as a ledger entry
- **THEN** the tool MUST reject the input as a caller error
- **AND** it MUST NOT present that rejection as an anchor-level verdict
- **AND** the distinction MUST remain visible, so that "your input was not a ledger" is never read as "your anchors drifted"

> The previous wording of the legacy scenario forbade *any* violation for a malformed
> entry, which collided with this one: a file with no `ledger` key is rejected before
> the three-state logic is reached, and that rejection is a parse failure, not a
> comparison. The prohibition is now scoped to anchor-level verdicts, where it
> protects the property that matters — a missing baseline field can never be
> misreported as anchor drift.

#### Scenario: A clean worktree makes the two values coincide

- **WHEN** a ledger entry is written while the working tree is clean
- **THEN** the digest field MUST be `null`
- **AND** a comparison against the committed base MUST still be able to return an ordinary pass or violation

#### Scenario: A dirty worktree is the normal state of the archive procedure

- **WHEN** the ledger is written as part of the archive precondition, at a point where the change's delta has been applied but not yet committed
- **THEN** the write MUST proceed
- **AND** the entry MUST record that its baseline is the working tree rather than the committed base

#### Scenario: A bare anchor count with no stated counting rule

- **WHEN** evidence text states an anchor count without naming the counting rule that produced it
- **THEN** the gate MUST report the entry as lacking a declared baseline
- **AND** a recomputation under the other counting rule MUST NOT be treated as a contradiction of the stated figure
