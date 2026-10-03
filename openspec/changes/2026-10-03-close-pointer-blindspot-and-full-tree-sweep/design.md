# Design

## D1 — Census, and the errata on the previous census

The authoritative census is produced by `evidence/pointer_scan.py`, which is
validated by `evidence/validate_detector.py` **before** its output is used.
The harness is not decoration: it caught six defects in the detector during
this change, each of which had reproduced the original failure mode.

Measured at the current tree `95718cf`:

```
sites=82  actionable=55  historical-exempt=27  files=17
```

Measured at the baseline `1526b98` (the tree the previous change measured):

```
sites=267  actionable=232 (strong=221, weak=11)  historical-exempt=35  files=28
```

### Errata on `2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract` D1

That change's D1 records **117 sites / 97 actionable / 20 historical-exempt /
14 files** at `1526b98`, and its plan reads "sweep the 97 actionable sites".

**The 97 / 20 split does not reproduce and the totals undercount the
population.** Three independent checks:

| source | pointer lines | actionable | exempt | files |
|---|---|---|---|---|
| archived D1 record | 117 | 97 | 20 | 14 |
| its own shipped classifier, replayed at `1526b98` | 117 | 100 | 17 | 14 |
| this change's validated detector at `1526b98` | 267 | 232 | 35 | 28 |

`117` and `14` reproduce under the old semantics; `97 / 20` does not reproduce
under that same classifier at any of `a1f0caa`, `1612778`, `95718cf`, nor at
the audit pin `6593a06`. Marker drift is ruled out: the marker set is
byte-identical between `a1f0caa` and `95718cf`.

The larger population is the real story: the old semantics never saw the
path-carrying forms at all, so its baseline was already an undercount before
the marker split is considered.

**The archived change is not edited.** Per the user's decision, archival
artifacts are immutable; this errata is the correction of record. Two further
claims in that D1 are also inaccurate and are corrected here:

- it credits the census self-check with "asserted against a known positive …
  and the run aborts if it does not". The self-check never calls
  `classify()`; it counts substrings in a pinned blob. Both bugs it is
  credited with catching were caught by the separate `if not raw` guard.
- it attributes the `spec L206` cluster to `decompmoe-skeleton` `req-11`; the
  text is `req-12` (already corrected in place at `95718cf`).

## D2 — Two-class detector semantics

A site is a **locator** preceded on the same line by a **reference**, where
only bridge characters and up to three lowercase connector words separate
them. References come in two classes:

- **self-carrying** — the reference is inside the match, so no adjacency
  search is needed: `<path>.<ext> L###`, `<path>.<ext>:###`,
  `req-N L###`, `Req <n> L###`, `Ticket <ID> L###`, `Decision <n> L###`.
- **bare capability words** — `wayfinder`, `spec`, `skeleton`, `governance`,
  `CLAUDE`, `LOOPS`, `src`, `tests`, `audit`, and `req-N` ids. These require
  the adjacency search.

Recall is favoured over precision. A false positive costs minutes of
adjudication; a false negative silently certifies a broken tree, which is the
failure this change exists to repair. The trade is explicit: **11 weak sites**
on the baseline are `line NNN` with no reference token at all, and they are
reported separately rather than silently folded into the actionable count.

## D3 — A historical marker may not exempt its own documentation

`HISTORICAL_MARKERS` no longer includes a bare `historical`, and no marker may
fire on a token that falls inside a code span or a quoted string.
`governance/spec.md:78` is the case that forced this: it documents the
`(historical, ...)` annotation format, so the word it documents exempted the
line.

The guard test asserts both directions, because over-correcting is equally a
defect: a genuine `before` marker must still exempt.

## D4 — A self-check that cannot fail is not a self-check

The census self-check is replaced by one that runs a synthetic
self-exemptifying line and a synthetic live pointer through the **real**
`classify()`, and asserts the classification. The pinned `wayfinder L249`
substring count is kept as an additional assertion, not as the classifier's
guard.

## D5 — What a site rewrites TO

| form | replacement |
|---|---|
| `wayfinder/spec.md L413` (wayfinder-internal) | `wayfinder` `#req-20` MCI row, by title |
| `wayfinder/spec.md L83` | `wayfinder` `#req-6` seeding Requirement |
| `src/decompmoe/safeguards.py:93-94` | the function name / constant identifier |
| `Ticket A8-2 L70 + L74` | `wayfinder/tickets/A8-2.md` by scenario heading |
| `Code L265` | the function or constant the sentence is about |
| `line 495` with no reference | the symbol named in the same sentence |

Every replacement is made with a **bounded token substitution**, never a
whole-line replacement built from a fragment. An earlier change silently
destroyed four lines that way; the rewriter asserts a length-collapse guard
and re-reads every file it wrote.

## D6 — `LOOPS.md` is a log, and is still swept

`LOOPS.md` holds 14 sites, all inside dated audit-log entries. Rewriting
`config.py L54` to `MVPConfig.beta_initial` default makes the log entry
**more** accurate over time rather than falsifying it: the entry records
*what was wrong*, not *which line it was on*. The date and the prose are
untouched.

## D7 — The detector excludes itself

`SELF_EXCLUDE` covers `scripts/lint_no_line_pointers.py` and
`tests/test_lint_*`. Those files must spell out `req-11 L245` in order to test
for it; counting them would make the detector unable to ever pass. The
exclusion is declared in one place and asserted by a test so it cannot grow
silently.

## D8 — `run_gates.py` is not this change's to fix

The recheck found that `run_gates.py --change <archived-name>` exits 1 with
`Change must have at least one delta`, because `openspec validate` resolves
only active changes — and that `run_gates.py:431` raises `UnicodeEncodeError`
on a GBK console while printing its own failure report, where
`lint_no_line_pointers.py:511-515` re-encodes stdout to UTF-8.

`run_gates.py` was last committed by a parallel session (`ea802c8`) and is not
in this change's ownership. Both defects are reported for that session's owner
and **not** touched here.

## D9 — Known findings this change does NOT fix

Recorded so they are not lost, deliberately out of scope:

- 19 Requirements carry **no** `**Source:**` line at all (18 in
  `decompmoe-skeleton`, 1 in `wayfinder`). The governing lint only inspects
  lines that exist, so it structurally cannot detect absence. Different
  defect family; needs its own change.
- Anchor coverage is 68/68 across the three capabilities with 0 violations,
  including the unclosed-tag variant. Confirmed clean; nothing to do.
- `wayfinder L249` positive control: 10/10 denominator confirmed against
  `git show 1526b98:tests/test_safeguards.py`.
