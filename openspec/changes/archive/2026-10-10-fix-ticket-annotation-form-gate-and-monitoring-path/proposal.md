# Why

An audit round (`.audit/wayfinder-opsx-code-review`) filed UD-04 as a MAJOR finding: `CLAUDE.md`
declares `wayfinder/tickets/*.md` both non-binding (§2 / §8) and subject to a mandatory
`(historical, …)` maintenance protocol (§8 (a), formalized by `req-gov-4` clause 4), allegedly
leaving the obligation "without a subject, without an owner, without a check point, without lint
coverage".

Verification against the repository shows the premise is wrong but it points at a real, narrower
defect:

- **The tension is a deliberate semantic layering, not a contradiction.** `CLAUDE.md:98` and
  `req-gov-4` clause (1) both restrict "advisory" to *ticket-edit policy* (whether ticket text may
  diverge from spec). Neither extends it to "ticket-side data has no downstream effect". So
  "you may not amend" and "you must monitor" are compatible by construction.
- **The real defect is that the monitoring obligation names a path that does not resolve.**
  `req-gov-4` clause (3) requires `.audit/audit-verification.md`; the file that exists is
  `.audit/audit-verification/audit-verification.md` (`Test-Path` on the bare form returns `False`).
  The same dead path recurs in `req-gov-2` Scenario 1 (`.audit/audit-verification.md` verify-15
  verdict). A MUST with no executable referent is not a weaker obligation — it is an unrunnable one.
- **Lint coverage of the annotation form is genuinely absent.** `scripts/lint_no_line_pointers.py:81`
  declares `SCAN_ROOTS = ("openspec/specs", "src", "tests")`; `wayfinder/tickets` is absent, so no
  lint has ever read a ticket body. `scripts/pointer_scan.py` already carries the needed machinery
  (`RE_TICKET_L` at `:97-98`, the clause-level historical-marker rules at `:329-334`) — it was simply
  never pointed at the ticket tree. The gap is **scope**, not capability.

Two further self-describing statements in the same file are stale on their face:

- `req-gov-2` (`:72`) describes `09-fix-claude-md-ticket-advisory-boundary` as "currently a planning
  draft, NOT YET proposed/applied/archived". It was archived at
  `openspec/changes/archive/2026-09-23-fix-claude-md-ticket-advisory-boundary`, and the Requirement
  it produced (`req-gov-4`) sits at `:160-174` of this same file.
- `req-gov-2` (`:80`, `:82`) says "future governance contracts would be `req-gov-3`+". `req-gov-3`
  and `req-gov-4` both exist.

`req-gov-2` Scenario 1 and Scenarios 2–3 additionally transcribe the two A8-2 annotations with
`req-20` and no `(#req-N)` anchor, while the canonical form the same Requirement mandates at `:70`
*requires* the anchor, and the real `wayfinder/tickets/A8-2.md:70,74` carry
`req-20-mci (#req-20-mci)`. Left uncorrected, a form-gate Scenario would contradict the Requirement
that states the form.

## What Changes

- `openspec/specs/governance/spec.md`:
  - **MODIFIED `req-gov-2`** — (i) name `scripts/lint_ticket_annotation_form.py` as the enforcer of
    the ticket-body form, and state why no existing lint covers it (the `SCAN_ROOTS` omission);
    (ii) replace the "NOT YET proposed/applied/archived" paragraph with the archived fact and the
    `req-gov-4` pointer; (iii) correct the two dead `.audit/audit-verification.md` references;
    (iv) transcribe the A8-2 annotations as they actually exist (`req-20-mci (#req-20-mci)`);
    (v) add Scenario "ticket supersede annotation form is machine-checked by a dedicated lint".
  - **MODIFIED `req-gov-4`** — (i) clause (3) monitoring path corrected to the path that resolves,
    with the non-resolving bare form explicitly named as a defect; (ii) add Scenario "the monitoring
    obligation names a path that resolves".
- `scripts/lint_ticket_annotation_form.py` — **new gate**, discovered automatically by
  `scripts/run_gates.py` (`LINT_GLOB = "lint_*.py"`, `discover_lints()` at `:278`). Scans
  `wayfinder/tickets/*.md` and asserts form at two different strengths: **V-ANCHOR blocks** (the
  `superseded by spec req-N` clause must carry its `(#req-N)` anchor) and **V-DECISION blocks on
  existence only** (a cited change must resolve to a real directory under
  `openspec/changes/archive/`). Whether the cited *Decision number* is the right one is **not**
  asserted — see design.md Decision 6. Reuses `scripts/pointer_scan.py` as a library. **Existence**
  and **drift** assertions are explicitly out of scope: they would require a cross-artifact
  association rule this change does not authorize.
- `tests/test_lint_ticket_annotation_form.py` — paired test suite for the new lint.
- `wayfinder/tickets/*.md` — **no edit required**. Measured: all **18** annotations already carry the
  `(#req-N)` anchor (better than the change's own estimate of "16 of 18"), and legacy line-addressed
  annotations measure 0, so the gate is green on arrival with zero corpus changes. 9 annotations carry
  no change citation; per design.md Decision 6 they are reported in the summary and do not fail the
  gate.
- `CLAUDE.md` §4 — refresh the re-verification date stamp only. **No git-history surgery**; the
  three-branch architecture stays aspirational exactly as `:57-59` already states.
- `.audit/wayfinder-opsx-code-review/**` — audit-side record: UD-05 withdrawn, UD-03 marked
  pending-evidence, and the provably wrong numbers in the audit artifacts corrected. `.audit/` is a
  temporary audit evidence library, not governed by spec Requirements (`req-gov-2` Scenario 1), so
  these edits stay outside the spec delta.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `governance` — 2 MODIFIED Requirements, 2 ADDED Scenarios, 0 new anchors.
  - **MODIFIED** `req-gov-2` "Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3
    source-field rules application": form enforcer named; archived-change status corrected; two dead
    `.audit/` paths corrected; A8-2 transcription corrected; form-gate Scenario added.
  - **MODIFIED** `req-gov-4` "Ticket Advisory Boundary — Stale Contamination Monitoring": clause (3)
    monitoring path corrected; path-resolves Scenario added. **Clause (1) advisory scope, clause (2)
    contamination channels, and clause (4) remediation protocol are unchanged.**

## Impact

- **Affected code**: 0 lines in `src/decompmoe/`. Two new tooling files under `scripts/` and
  `tests/`.
- **Affected docs**: `CLAUDE.md` §4 date stamp (one block). `wayfinder/tickets/*.md` — annotation
  form only.
- **Affected specs**: `openspec/specs/governance/spec.md` — 2 Requirements modified, 2 Scenarios
  added. No Requirement added, removed, or renamed; no anchor added, removed, or moved.
- **Affected APIs / dependencies**: none. The new lint imports only the existing
  `scripts/pointer_scan.py`; no third-party dependency.
- **Risk**:
  - **Risk A — the new lint is stricter than the historical corpus.** Resolved by measurement: all 18
    annotations carry the anchor, legacy line-addressed annotations are 0, so V-ANCHOR is green with no
    corpus edit. The Decision clause was narrowed for a separate reason (design.md Decision 6):
    provenance reconstruction failed and one existing citation is provably mis-attributed. A
    grandfather list remains forbidden — it would contradict the "NO exemption table" design of
    `scripts/pointer_scan.py`.
  - **Risk B — the gate silently skipping an annotation.** Found and fixed during implementation:
    `wayfinder/tickets/A8-2.md:70` quotes `` `(1/d_c, 1]` ``, whose unbalanced paren defeated naive
    depth counting and dropped that annotation from checking entirely (2 markers, 1 span). Paren
    balancing now ignores code spans (design.md Decision 7); markers = spans = 18.
  - **Risk C — shared worktree.** `src/decompmoe/gating.py` and `wayfinder/tickets/WF-1.md` carry
    uncommitted changes owned by another actor. The `WF-1.md` diff *removes* a `(historical, …)`
    annotation while leaving the superseded `< 1/128` value in place unmarked — exactly the
    contamination pattern `req-gov-4` clause (2) describes. This change MUST NOT stage, revert, or
    otherwise absorb that edit; stage by explicit path only.
  - **Risk D — gate exit codes are not interchangeable.** `scripts/run_gates.py` distinguishes exit 1
    (findings) from exit 2 (`GATE RESULT INVALID`, `HEAD` or worktree moved mid-run). Exit 2 must
    be re-verified, not retried verbatim.
  - **Risk E — audit artifact is pinned.** `lists/opsx-changes.md` may NOT receive the UD errata: the
    archived verifier `verify_artifacts.py:255` asserts exactly 5 `## Errata` sections and `:333`
    asserts the A-6 verifier still reports 65 checks. Measured green at baseline
    (`PASS 5 Errata sections -- count=5`, `PASS A-6 verifier still runs 65 checks`). The UD errata
    therefore lives in a new sibling file rather than appended to that one.
  - **Risk F — anchor accounting at archive.** Per `req-gov-10`, the anchor ledger workflow is
    "write ledger → archive → compare → surgical restore → retest". Re-running archive to repair a
    swallowed anchor is prohibited.
