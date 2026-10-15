# Baseline: `classified.json` bucket denominators (task 1.2)

**Captured at**: `HEAD = ded0944`.

The two ledgers' entry counts are denominators this change re-verifies against.
Both files were generated from the same `classified.json`, so any rendered-entry
count that disagrees with these numbers is a defect — which is precisely the
check that was botched during planning (see `check_rendered_refs.txt`).

## Script

`evidence/baseline_buckets.py` — prints the histogram and the per-bucket ref list.

```
uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/baseline_buckets.py
```

## Observed output (verbatim)

`evidence/baseline_buckets.txt`

```json
{
  "buckets": {
    "archive-only": 12,
    "conflict": 22,
    "context": 9,
    "direct-fix": 32,
    "opsx-change": 8,
    "user-decision": 5
  },
  "total": 88
}

opsx-change (8): FIX-001, FIX-006, FIX-007, FIX-020, FIX-029, FIX-034, FIX-041, FIX-042

direct-fix (32): ARC-002, FIX-002, FIX-003, FIX-004, FIX-005, FIX-008, FIX-009, FIX-010,
FIX-012, FIX-013, FIX-014, FIX-015, FIX-016, FIX-017, FIX-018, FIX-019, FIX-021, FIX-023,
FIX-025, FIX-026, FIX-027, FIX-028, FIX-030, FIX-031, FIX-032, FIX-035, FIX-036, FIX-038,
FIX-040, FIX-043, FIX-044, FIX-045
```

(The ref lists are re-wrapped for readability here; the `.txt` capture holds the
script's own single-line formatting.)

## Scope of this change

Only the `opsx-change` (8) and `direct-fix` (32) buckets are in scope — 40 entries
total, matching the task list's groups 2 and 4.2. The other four buckets
(`archive-only` 12, `conflict` 22, `context` 9, `user-decision` 5, totalling 48)
are explicitly **not** re-verified by this change; `proposal.md` scopes them out.
Their ids are recorded here only so a later change does not mistake the 88-item
total for this change's workload.

## The planning-phase miscount, recorded

While drafting `proposal.md` the drafted text claimed `direct-fixes.md` renders 31
entries against a denominator of 32. That claim was **false**. The ad-hoc grep
used at the time was

```
grep -c '^### \(FIX\|CFL\|CTX\|OPX\)' direct-fixes.md
```

which silently excluded `ARC-002` (the token is not one of the four alternates)
and the two Chinese section headings (`不重不漏（本桶内，实测）` /
`本节明确不覆盖的范围`). Corrected check: **32 rendered vs 32 expected, MATCH**.

The failure mode is the same as the one this change was created to repair
(`FIX-029`'s swapped evidence values): a mechanical check whose matcher was too
narrow, combined with a conclusion written as if the check had been sound. The
corrected check is now a script rather than a shell one-liner so the matcher
lives in reviewable code.
