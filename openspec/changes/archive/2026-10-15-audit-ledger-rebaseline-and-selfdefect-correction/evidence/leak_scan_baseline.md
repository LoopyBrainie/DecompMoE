# Baseline: `leak_scan.py` on the UNMODIFIED ledgers (task 1.4)

**Captured at**: `HEAD = ded0944`, before any ledger edit.
**Detector**: `evidence/leak_scan.py`, a byte-identical copy of
`.audit/gradual-review-2026-10-07/_work3/d5/leak_scan.py`
(`cmp` → IDENTICAL, 4072 bytes). It is deliberately **not** edited: an
unmodified detector is what makes the red line in `design.md` D-5 meaningful.
Note it hard-codes `HEAD = "dde0e1d"` for its PASS-2 blob index, which is what
keeps its counts directly comparable with the D3/D5 record inside
`direct-fixes.md`.

Full output: `evidence/leak_scan_baseline.txt`.

```
PYTHONIOENCODING=utf-8 uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/leak_scan.py
```

## Body sizes

| file | lines | chars |
|---|---|---|
| `lists/direct-fixes.md` | 629 | 54,343 |
| `lists/opsx-changes.md` | 212 | 18,933 |

## PASS 1 — raw pattern hits (13 primary + 11 bypass)

| file | raw hits |
|---|---|
| `lists/direct-fixes.md` | **6** |
| `lists/opsx-changes.md` | **6** |

All 12 are enumerated below and adjudicated. Every one is a **false positive by
construction**: it sits in a line that *enumerates the categories this file
excludes*, or describes the absence of a priority declaration in a pinned
artifact. The D3 record in `direct-fixes.md` establishes this adjudication
convention; it is applied here unchanged.

### `lists/direct-fixes.md`

| line | pattern | context | class |
|---|---|---|---|
| L6 | `目标值` | 「…全文不给出改法、目标值、优先级或处理顺序」 | non-leak: property declaration enumerating excluded categories |
| L6 | `优先` | same line | non-leak: same |
| L55 | `改成` | 「…**不回答**怎么改、改成什么值、先做哪条…」 | non-leak: classification section restating the exclusion |
| L55 | `目标值` | same line | non-leak: same |
| L55 | `优先` | same line | non-leak: same |
| L572 | `优先` | 「…`34b445a` / 仓外 `f8e5b26`）无优先级声明，见 CFL-017」 | non-leak: describes a *missing declaration* inside a pinned artifact; "优先级声明" ≠ a priority directive |

### `lists/opsx-changes.md`

| line | pattern | context | class |
|---|---|---|---|
| L6 | `修复` | 「…不是修复方案表」 | non-leak: property declaration |
| L6 | `目标值` | 「…全文不给出改法、目标值、优先级或处理顺序」 | non-leak: same |
| L6 | `优先` | same line | non-leak: same |
| L31 | `改成` | 「…**不回答**怎么改、改成什么值、先做哪条…」 | non-leak: classification section |
| L31 | `目标值` | same line | non-leak: same |
| L31 | `优先` | same line | non-leak: same |

**(b) class = 0 at baseline.**

## PASS 2 — (a) verbatim quotes of a tracked artifact

| file | (a) | not-found quoted spans |
|---|---|---|
| `lists/direct-fixes.md` | **63** | 70 |
| `lists/opsx-changes.md` | **7** | 38 |

## Deltas against the D5 record inside `direct-fixes.md`

D5 recorded: body **575 lines / 51,874 chars**, raw hits **3**, (a) **63**.

- Body grew **575 → 629 lines / 51,874 → 54,343 chars** (+54 lines / +2,469 chars).
- (a) is **unchanged at 63** — the growth added zero new verbatim quotations.
- Raw hits grew **3 → 6**. The three additions are all in the **L55
  classification section** (`改成` / `目标值` / `优先`), which did not exist when
  D5 ran; each is the same property-declaration enumeration already present at
  L6. Adjudicated non-leak, per the convention above.

So D5's in-file numbers are stale on two axes (body size, raw-hit count) and
current on one ((a) = 63). The red line for task 4.1 is therefore expressed
against **this** baseline, not against D5's: after the edits, PASS 1 must produce
no hit outside the L6 / L31 / L55 / L572 property-declaration contexts enumerated
above.

## Reproduction

```
cmp .audit/gradual-review-2026-10-07/_work3/d5/leak_scan.py openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/leak_scan.py
PYTHONIOENCODING=utf-8 uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/leak_scan.py
```

The first must print nothing (identical). The second must reproduce
`evidence/leak_scan_baseline.txt` while the two ledgers are unmodified.
