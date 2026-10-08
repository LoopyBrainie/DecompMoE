# Design

## Measurement method

Every decision below was taken by loading the real lint with `importlib` and re-running
`find_unbaselined_counts` over a corpus with candidate patterns swapped in. Reading the code was
used to locate the patterns, never to conclude what they match.

**Corpus**: 432 Markdown files under `openspec/changes/archive/`. This is deliberate and it is also a
limitation worth stating plainly: after `313a5bf` every change is archived, so the lint's own file walk
returns exactly one file and reports 0 findings under every variant. The archive is not walked by the
lint — `evidence_files()` excludes it, since req-gov-5 makes archived artefacts read-only and a report
demanding an edit to one would be nonsense. It is used here purely as the representative body of
evidence prose.

**One number in this file is larger than it looks.** The `+450` in D2 is measured against prose written
before this lint existed and never written to satisfy it. It bounds the cost, not the expected cost
for future evidence, which will have been authored with the lint in place. That argument is not
evidence, so the number is reported as measured and the tightening is defended on the defect, not on
the delta.

## D1 — ratio pattern matched prose `Phase 2/3`

`COUNT_PATTERNS[0]` is `\b\d+\s*/\s*\d+\b`. It matched `Phase 2/3`, where the slash means "Phase 2
and Phase 3", not a ratio. This is the only false positive found, and it had already forced three
workarounds: `34b445a` replaced the slash with an en-dash (`Phase 2–3`) in three places rather than
touch the lint.

| variant | corpus findings | `Phase 2/3` | `3/16 = 0.1875` | `2/3` |
|---|---|---|---|---|
| current `\b\d+\s*/\s*\d+\b` | 505 | **fires** | fires | fires |
| **D1-a** `(?<!Phase\s)(?<!Step\s)(?<!阶段\s)…` | **504 (−1)** | silent | fires | fires |
| D1-b `\b\d+\s+\/\s+\d+\b` | 461 (−44) | silent | **silent** | **silent** |
| *measured on* | `2026-10-07-lint-count-baseline-scope-and-gate-set-integrity` | | | |

**D1-a adopted.** D1-b is rejected on evidence, not taste: requiring whitespace around the slash also
discards `3/16`, which is a live ratio at `openspec/specs/wayfinder/spec.md` (`N_e = 16` experts active
is `3/16 = 0.1875`). A narrowing that loses a true positive on the spec's own text is a trade, not a
fix. D1-a removes exactly one finding, which is the one false positive.

The three `Phase 2–3` workarounds are **left as they are**. Reverting them is legal after this change
but is not required, and reverting would put the prose back through a pattern that no longer needs to
be avoided — for no gain.

## D3 — pure-hex English words conferred a baseline

`BASELINE_PATTERNS[0]` is `\b[0-9a-f]{7,40}\b`. `defaced`, `effaced` and `feedbac` are all seven or
eight characters drawn from `[a-f]`, so any paragraph containing one of them was treated as baselined
and its real counts went unreported.

| variant | corpus findings | `defaced` | `82b84d6` | full 40-char | `abcdef1` |
|---|---|---|---|---|---|
| current | 505 | matches | matches | matches | matches |
| **D3-a** requires ≥1 digit | **505 (±0)** | **no** | matches | matches | matches |

**D3-a adopted**, at zero corpus cost. The known cost is an all-letter hash: `deadbee` no longer
counts as a baseline. `abcdef1` — the realistic near-miss — still matches because it ends in a digit.
The trade is stated rather than hidden: a 7-hex-digit token with no digit anywhere is roughly a
1-in-268-million event among real short hashes, and the alternative is that English prose silently
disables the rule.

## D4 — `histor` was a bare substring an order of magnitude wider than intended

`EXEMPTION_MARKERS` contained `"histor"`, and `has_exemption` tested `m in text.lower()`. Confirmed:
`histor`, `historical`, `history` and `historian` all granted an exemption.

| variant | corpus findings | `histor` | `historical` | `history` | `historian` | `不可复算` |
|---|---|---|---|---|---|---|
| current | 505 | exempt | exempt | exempt | exempt | exempt |
| D4-a `historical`, substring kept | 510 (+5) | exempt | exempt | exempt | exempt | exempt |
| **D4-b** `historical` + ASCII word boundary | **510 (+5)** | **no** | exempt | **no** | **no** | exempt |

**D4-b adopted.** D4-a recovers 5 findings but leaves `historical` matching inside longer words, which
is the same defect one level down. D4-b costs the same and stops there.

**CJK markers keep substring matching, deliberately.** `\b` is an ASCII word boundary; CJK characters
are word characters, so `\b不可复算\b` would never match and every Chinese exemption would silently
die. That would be a far worse regression than the one being fixed, and it is the reason the two
marker classes are handled by different code paths rather than one uniform rule.

## D2 — one baseline blessed every count in its paragraph

`find_unbaselined_counts` computed `_block_bounds` and tested exemption and baseline against the whole
block. A paragraph stating five counts and naming one command anywhere was fully baselined, so gate
coverage shrank as paragraphs grew longer — the opposite of the intent.

Controlled probes (block vs per-line):

| probe | block | per-line |
|---|---|---|
| 5 counts, baseline on the LAST line | **0 — passes** | 1 — reported |
| 1 count, baseline on its OWN line | 0 | 0 |
| 1 count, no baseline | 1 | 1 |
| table row, baseline in the header | 0 | 0 |
| *measured on* | `2026-10-07-lint-count-baseline-scope-and-gate-set-integrity` | |

Corpus, as landed: block-level 505 → per-line **955 (+450)**.

**Two intermediate implementations of this decision were wrong, and both were caught by the lint on
this change's own `tasks.md`.** Recorded rather than deleted, because the sequence is the point:

- **943** — read the scope from `_block_bounds`' block *start* instead of the count's own line. In a
  list `_block_bounds` extends upward across every non-blank line, so the start is the previous item
  and one item's baseline silenced the next.
- **857** — fixed the above but kept the per-block dedup *before* the baseline check, so the first
  count in a block decided the fate of every later count in it. That is the block-wide rule this
  decision exists to remove, reintroduced through the dedup rather than through the baseline lookup.

The landed order evaluates the baseline for every count first and dedups only the *reporting*, which
keeps one finding per block (unchanged triage burden) while judging each count on its own terms.
`test_one_baseline_no_longer_blesses_a_whole_paragraph` pins the list case in both directions.

**Per-count scope adopted.** Report granularity is unchanged (one finding per offending block), so the
triage burden does not grow with the finding count.

**The table exception is retained on a prior claim, not on a measurement.** `_block_bounds` already
documents that a table row's block is the whole contiguous `|` run *including its header*, because the
header is where a table's baseline would be named. Two variants were built — per-line with and without
that exception — and they produced **identical** counts (943 both). The exception changes nothing on
this corpus. It is kept because the design rationale predates this change and removing it would require
positive evidence that tables never name a baseline in their header, which this corpus cannot supply.
What is *not* kept is any stronger claim: the exception is not free, it is merely unmeasured.

`find_unbaselined_counts`'s docstring states "One report per offending BLOCK" while describing
per-count baselining. The implementation is changed here and the docstring corrected in the same edit,
because a docstring that describes the rule this change replaces is the same defect class as the rule.

## D5 — the gate did not record which lints it ran

`cmd_gates` called `discover_lints()` and *then* took `worktree_snapshot()`, whose components are
`head`, `tracked_digest`, `untracked_digest` and `status_lines`. The discovered set was not among them,
and the run printed only a count: `f"{len(lints)} lint(s) discovered"`.

**The race**: commit a new `scripts/lint_*.py` between those two lines and the gate runs without it,
while both snapshots record the same post-commit HEAD. The comparison agrees, the run reports PASS, and
one lint silently never executed. This is the AC-25 failure mode again — a green describing coverage
that does not exist — applied to the gate set rather than the worktree.

**Fix**: `gate_digest`, a sha256 over the sorted lint filenames and their bytes, added as a fourth
snapshot component and compared in `_snapshot_differs`. A lint appearing or changing mid-run now
yields `GATE RESULT INVALID` (exit 2), which is the same answer the tree-content components already
give. The printed count is replaced by the recorded names.

Printing a bare count is the same pattern `req-gov-8` rejects when it refuses `git status --porcelain`
line counts as a signal: a derived count is not an independent witness.

## D6 — the runner crashed while reporting its own failure

`run_gates.py` printed through a GBK console. openspec decorates issues with `⚠` (U+26A0), which
cp936 cannot encode, so the runner died with `UnicodeEncodeError` at the exact moment it was printing
a FAIL line, destroying the report. `lint_no_baseline_counts.main` already reconfigures stdout and
documents why: "a crashed gate is indistinguishable from a green one". The gate runner was violating a
rule it already knew.

Found by accident: the archive precondition went red for an unrelated reason, and the crash hid the
actual cause for a full diagnostic round.

## D7 — `--strict` on the specs path enforced a rule openspec exempts

`openspec validate --specs --strict` failed on 58 requirements, and the runner then crashed (D6) before
naming the cause. Investigated rather than bypassed:

- `MAX_REQUIREMENT_TEXT_LENGTH = 500` is a hardcoded constant with no env var and no config key
- with and without `--strict` the issue sets are **byte-identical** (58 items, delta empty in both
  directions); the only difference is `valid: false`
- all 58 are the same `REQUIREMENT_TOO_LONG` advisory
- openspec's own validator applies that limit to a delta's **ADDED** requirements and explicitly skips
  it for **MODIFIED**, stating why at `dist/core/validation/validator.js:255-258`: *"MODIFIED is left
  alone: its text is the existing requirement, which the specs instruction says to keep whole."*

So `--strict` over the specs path asks openspec to enforce retroactively the rule it declines to
enforce on an existing requirement. Paying it means rewriting 58 of 70 requirements, several past 3000
characters, carrying the worked examples the governance specs depend on — and splitting a requirement
to fit renumbers every downstream `req-N` anchor, breaking references across all three capabilities,
the lints and the tests.

Structural validity is not relaxed: `openspec validate --specs` reports `3 passed, 0 failed`. The
change-level check keeps `--strict`, because that is where a new overlong requirement can still be
caught before it lands.

## Test obligations

Each pattern change carries a **bidirectional** test — the defect is caught, and the non-defect is not
flagged — as a hard equality, per CLAUDE.md §6. D5 asserts the snapshot key exists and that two
different lint sets yield different digests. The D7 invocation list is pinned by an exact assertion on
the argv recorded during a gate run.