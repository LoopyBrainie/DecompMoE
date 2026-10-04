# `基线` 字段的口径（baseline basis）

This file exists because `evidence/rebaseline.py` references it, and because the
question it answers was **open in the artifact itself** before this change.

## 三个取值

| value | meaning |
|---|---|
| `touched-since-pin` | the item's pin-state line falls inside some `drift` interval of the pin→frozen diff |
| `unchanged-since-pin` | it does not |
| `unverifiable (no pin line)` | the item has no usable line number (`location_line` is 0/absent), **or** its `location_file` is not an existing repository file |

`unverifiable` is new in this change. For either of its two cases, emitting
touched/unchanged would be false precision — and `lists/direct-fixes.md` already
said so in prose (DF-02: 「漂移表对仓库外路径无覆盖能力……不是该目录已稳定的证据」).
This change encodes that warning in the field value instead of only in prose.

## The coordinate side — formerly unknown, now determined

The list's own header previously said: 「`_pin_drift.json` 的生成脚本未记录区间取的是 pin 侧还是 HEAD 侧坐标」.

It is the **HEAD side (`+`)**. Three hunks prove it independently:

| hunk in `git diff -U0 6593a06 188b9fb` | recorded as | reading |
|---|---|---|
| `@@ -496 +499 @@` (skeleton) | `[499,499]` | head side — pin side would be 496 |
| `@@ -325,0 +326,4 @@` (skeleton) | `[326,329]` | pure **insertions are included** |
| `@@ -1,80 +0,0 @@` (`fix-config-docstring-beta-line-drift/tasks.md`, deleted) | `[0,0]` | pure **deletions clamp** to `[new_start, new_start]` |

Rule: for every hunk, record `[new_start, new_start + new_count - 1]`, clamped so
`hi >= lo`. Per-hunk intervals are **not** merged (adjacent `[166,167]` and
`[168,168]` stay separate in `tests/test_loss.py`). A file with no hunk records `[]`.
A rename registers **both** paths.

## The known soundness flaw — declared, not fixed

**`drift` intervals are HEAD-side coordinates; `位置` is a pin-state line number.**
Comparing the two is not a sound "was *this* line touched" test — a pin line that
shifted is compared against a head-side interval. All 123 `基线` values (108 in
list A + 15 field instances in list B, 117 distinct items because 6
`user-decision` items are written into both lists) were produced under this
comparison, including before this change.

Redefining it would rewrite all 123 at once, which is a decision this round was
explicitly told not to make. So it is **kept and declared** rather than quietly
repaired. The correct fix (map each pin line through the diff) is left for the
round that decides to re-baseline the whole list.

## Insertions vs modifications

`evidence/build_pin_drift.py` now emits two extra views:

- `inserted` — hunks with `old_count == 0` (pure insertions)
- `modified` — hunks that replace lines (`old_count > 0` and `new_count > 0`)

Both are **data only**. The `基线` verdict still uses the legacy merged `drift`
set, so no item's status flips on an unapproved 口径 change. Measured: **0 of the
current items** would change under the inserted-only reading
(`evidence/inserted_only_diff.txt` is empty). The next round gets the data and
makes the call.

## AC-27, the case that motivated all of this

`33f7cc9` inserted 13 lines after skeleton L121 (`@@ -121,0 +122,13 @@`), so pin
L122 is the **first line of an inserted block**. That insertion happened *before*
the pin, so within pin→frozen the line is simply an unmodified line and belongs to
no hunk. The mechanical table therefore says `unchanged-since-pin`, which is what
the list now records.

The list's `+1/+13/+8` net-change figures, by contrast, are **correct** — confirmed
twice: `git diff --numstat` (3/2, 14/1, 9/1) and real line counts
(892→893, 623→636, 165→173). They are pinned to `33f7cc9` alone, not to the wider
`7bf77af..6593a06` range. Do not "fix" them.
