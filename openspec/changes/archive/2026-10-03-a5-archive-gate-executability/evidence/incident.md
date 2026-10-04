# Incident — `openspec archive` swallowed `<a id="req-gov-7"></a>`

## What happened

Archiving this change (`openspec archive 2026-10-03-a5-archive-gate-executability`)
dropped the `<a id="req-gov-7"></a>` line from
`openspec/specs/governance/spec.md` while leaving the `req-gov-7` Requirement
**text fully intact** — heading, body, all three Scenarios, and its
`**Source:**` field.

This is audit item **AC-19** reproducing live, on the first archive this
repository has run under the new gate. The failure mode is exactly the one
described in `req-gov-9`: `openspec archive`'s requirement-block parser
accumulates until the next Requirement heading, and this repository's style puts
the anchor between two headings, so the anchor of the Requirement *following* the
one it rewrote gets absorbed. `req-gov-7` was itself an addition.

## How it was detected

Not by the `lost` comparison. `anchor-ledger-before.json` was written with
`expect_new: []`, and a `lost` check asks "was this id in the baseline and is it
gone now?" — `req-gov-7` was in **neither** the baseline (it did not exist yet)
nor the tree afterwards. By construction that comparison is blind to it.

It was caught by the **net count**: the ledger moved 65 → 67 where 65 + 3
additions = 68. One anchor short.

## Two defects this exposed, both fixed

1. **Workflow gap (fixed in `run_gates.py`).** The plan's archive procedure
   (`write ledger → archive → compare`) never told the operator to declare what
   the archive was expected to add, so the only defect class that can arise from
   *adding* a Requirement was undetectable. `anchor-ledger --write --change <name>`
   now derives `expect_new` from that change's own `## ADDED Requirements`
   delta, so the declaration cannot be forgotten. Regression test:
   `tests/test_run_gates.py::test_verify_catches_an_anchor_the_archive_swallowed`.

2. **CRLF emission (fixed in `run_gates.py`).** The ledger writer used
   `Path.write_text`, which on Windows emits CRLF; the resulting file failed
   `git diff --check` (stray CR read as trailing whitespace). A gate tool that
   writes files its own gate rejects is a defect. The writer now passes
   `newline="\n"`.

## Repair

Per `req-gov-9`, the anchor and its following blank line were restored by a
**direct byte-level edit** at the insertion point. **The archive was not re-run**
— a second archive would have overwritten the repair.

After repair: `governance` 6 → 9 anchors, repository total 65 → 68,
`openspec validate --specs --strict` exit 0, `run_gates.py` exit 0.

## A caveat about `anchor-ledger-before.json`

The pre-archive snapshot this file originally held — captured at head `940b27c`,
**65 anchors**, `expect_new: []` — was **overwritten** when the file was
regenerated after the repair, in order to add the missing `--expect-new`
declaration. It now records the **post-repair** state (68 anchors, 3 declared-new).

The original 65-anchor snapshot is therefore **not preserved as a file**. What is
known of it is recorded here and in the `.audit` Errata: head `940b27c`, 65
anchors (wayfinder 36 / decompmoe-skeleton 23 / governance 6), `expect_new: []`.
This was an avoidable loss — the fix was applied in place instead of writing a
fresh baseline under a new name.

## Errata (2026-10-04, task 9.4 independent review)

Independently re-derived from git by a non-implementer `verifier` agent. The
numbers below are its findings, not a re-assertion of the above.

**What checked out.** `940b27c` does reconstruct to 65 anchors split 36 / 23 / 6,
and `ea802c8` to governance 9 and a repository total of 68. The self-admission
above is accurate and complete on its central point: the pre-archive snapshot is
gone, and both surviving JSONs really are post-repair (identical 68-anchor
ledger, identical `written_at_head`).

**Correction — the provenance is half-stated.** The surviving JSONs record
`"written_at_head": "850ed8a2e4b90039b9673b533b815877d5abe737"`, i.e.
`feat(lint): add the cross-reference gate, C1-C4` — two commits *after* the
`940b27c` discussed in the caveat above. `git diff --stat 940b27c 1612778 --
openspec/specs/` is empty, so the 65 figure is valid for both revisions; the
number is right, but the caveat names only one of the two heads involved.

**Not reconstructible from git.** Two statements in this file and in the
successor change's design record facts about a working tree that was never
committed, and they carry no revision:

- the `65 -> 67` ledger transition above — no commit holds a governance
  8-anchor state, so the intermediate value survives only in this prose;
- the successor change's "48 dirty entries at delivery time".

The arithmetic is self-consistent (65 + 3 = 68, 68 - 1 = 67), but self-consistency
is not evidence. Both are recorded here as **not verifiable** so a later reader
can tell them apart from the figures that do reconstruct.
