# Why

`scripts/lint_no_baseline_counts.py` and `scripts/run_gates.py` were audited with 13 constructed
probes. Seven findings were confirmed by re-running the loaded module, not by reading it. Four are
silent under-coverage — the gate reports a pass over material it never examined — and one is a false
positive that cost real edits. Two further defects live in the gate runner itself and were found only
because the archive precondition went red for an unrelated reason and the runner crashed while
reporting it.

Every number below was measured against the 432 archived Markdown files under
`openspec/changes/archive/`, which is the corpus this lint exists to police. The live evidence scan
is a single file (`docs/templates/post-review-remediation.md`) and reads 0 findings under every
variant tried, so it cannot discriminate between candidates; the archive can.

## What Changes

- **`lint_no_baseline_counts.py`**
  - ratio pattern stops matching prose `Phase 2/3` (false positive) while still matching real ratios
  - commit-hash baseline requires at least one digit, so `defaced` / `effaced` / `feedbac` stop
    conferring a baseline
  - `histor` exemption marker becomes `historical`, matched on word boundaries for ASCII markers
    while CJK markers keep substring matching
  - baseline scope narrows from "anywhere in the paragraph" to "on the count's own line", with the
    contiguous table run retained as its block because the header is the legitimate place for a
    table's baseline
- **`run_gates.py`**
  - the gate result records the discovered lint set as a snapshot component, so a lint appearing or
    changing mid-run is reported `INVALID` (exit 2) instead of `PASS`
  - stdout/stderr are reconfigured so a failing gate can still print its own report on a GBK console

No Requirement content changes. `skip_specs: true`.

## Non-goals

Four measured false negatives are **out of scope** — they are coverage choices rather than defects,
because the module docstring states that anything not in `COUNT_PATTERNS` is not a count:

- English counters (`3 problems`, `5 findings`, `2 tests`) are invisible
- a real count inside backticks is not detected, while a baseline inside backticks is
- an unclosed fence silently blinds the remainder of the file
- counts in headings are skipped

Also out of scope: the duplicated `_table_cell_counts` definition (the first is dead code, byte-identical
to the second), and the lint's own non-UTF-8 read. One archived file **does** carry a truncated
multi-byte sequence —
`archive/2026-09-23-07-fix-spec-territory-seeding-phase-0/tasks.md` at bytes 32-33 — so a future
un-archive would crash the lint rather than report. It is currently harmless only because
`evidence_files()` never reads the archive; that is a property of the walk, not a property of the
corpus.