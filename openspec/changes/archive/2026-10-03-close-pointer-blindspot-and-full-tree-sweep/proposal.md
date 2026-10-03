# Close the pointer-detector blind spot and sweep the full tracked tree

## Why

The previous change
(`2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract`, archived as
`628d5c5`) reported **"actionable 97 → 0"** and shipped
`scripts/lint_no_line_pointers.py` as the standing gate. Both numbers were
false. The post-archive independent recheck returned **FAIL**; this change
re-does the work with a detector that is validated before it is trusted.

## The defect

`scripts/lint_no_line_pointers.py:96` and `evidence/pointer_census.py:66`
carried the same regex:

```
\b(wayfinder|skeleton|decompmoe-skeleton|spec)\s+(?:spec\s+)?L?(\d{1,4})
```

`\s+` requires whitespace **immediately** after the capability word. Two very
common forms therefore never match:

| form | char after the capability word |
|---|---|
| `` `wayfinder/tickets/A8-2.md` L70 `` | `` ` `` |
| `wayfinder/spec.md L83` | `/` |

The minimal repro is `tests/test_schedule.py:64`: the sweep re-anchored
`req-13` to the Requirement title two lines above and left
`wayfinder/spec.md L83` in place directly underneath it.

Two further defects turned the "0" into a hard guarantee rather than an
accident:

1. **Self-exemptifying marker.** `governance/spec.md:78` carries the literal
   token `historical` *inside the quoted annotation template the line itself
   documents*, so the historical marker fired on the documentation of the
   marker.
2. **Vacuous self-check.** `pointer_census.py:332-362` counts substrings in a
   pinned blob and never calls `classify()`. Neutering `classify` to return
   `None` leaves the self-check printing `OK`.

## Scope

Full tracked tree (`git ls-files *.md *.py`, archive excluded). Validated
census at `95718cf`: **55 actionable sites across 10 files**.

| file | sites |
|---|---|
| `LOOPS.md` | 14 |
| `openspec/specs/decompmoe-skeleton/spec.md` | 13 |
| `openspec/specs/governance/spec.md` | 9 |
| `tests/test_safeguards.py` | 7 |
| `apply-checklist.md` | 5 |
| `tests/test_schedule.py` | 2 |
| `tests/test_sphere.py` | 2 |
| `tests/test_metrics.py` | 1 |
| `docs/templates/post-review-remediation.md` | 1 |
| `openspec/specs/wayfinder/spec.md` | 1 |

`CLAUDE.md:93` was in the raw scan but is correctly exempted by its `原`
marker and needs no edit.

## What Changes

1. Replace the regex with the validated two-class semantics in
   `evidence/pointer_scan.py` (self-carrying forms + adjacency search) and
   make `scripts/lint_no_line_pointers.py` import or mirror it exactly.
2. Make the historical marker refuse to fire on a token inside a code span.
3. Make the census self-check actually exercise `classify()`.
4. Rewrite all 55 sites to point at a Requirement anchor, a Requirement
   title, or a symbol name — never a line number.
5. Add guard tests so the blind-spot form can never be reintroduced.

## Impact

- Affected capabilities: `decompmoe-skeleton` (req-12, 13, 18, 20, 23),
  `governance` (req-gov-2, req-gov-4), `wayfinder` (req-15).
- Affected code: `tests/test_safeguards.py`, `tests/test_schedule.py`,
  `tests/test_sphere.py`, `tests/test_metrics.py`.
- Affected tooling: `scripts/lint_no_line_pointers.py`, and the evidence
  tools of the archived change (their own pointer semantics must match).
- No new dependency, no kernel, no training. Docs and tests only, plus the
  one gate script.
