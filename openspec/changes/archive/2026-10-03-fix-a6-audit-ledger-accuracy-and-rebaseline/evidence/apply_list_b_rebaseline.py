# -*- coding: utf-8 -*-
"""Surgically update the `基线` field of 8 list-B items in lists/direct-fixes.md.

WHY SURGICAL
------------
No script generates `lists/direct-fixes.md` (unlike list A, whose generator
`_gen_listA2.py` is preserved). It is a hand-maintained artifact, so the rebaseline
cannot be propagated by re-running anything.

WHY BLOCK-SCOPED
----------------
The replacement is bound to a specific `### <ID>` block and asserts the old value
first. A whole-file "replace all `unchanged-since-pin`" would corrupt the 7 items
whose value is genuinely still correct.
"""
import io
import os
import re
import sys

REPO = r"D:/myProject/DecompMoE"
TARGET = os.path.join(REPO, ".audit", "wayfinder-opsx-code-review", "lists", "direct-fixes.md")
SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "_pre_edit_direct-fixes.md")

OLD_VALUE = "unchanged-since-pin"
NEW_VALUE = "unverifiable (no pin line)"
ITEM_IDS = ["DF-01", "DF-02", "DF-03", "DF-04", "DF-05", "DF-06", "UD-03", "UD-06"]

# In list B the field is inline at the end of the severity/verdict line, not on
# a line of its own:
#   - **严重性**：MAJOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin
BASELINE_RE = re.compile(r"^(.*\*\*基线\*\*：)(.+?)(\s*)$")
HEADING_RE = re.compile(r"^###\s+([A-Z]{2,3}-\d+)\b")


def substitute_baseline(line, new_value):
    """Return the line with only the 基线 value swapped, or None if absent."""
    match = BASELINE_RE.match(line)
    if not match:
        return None
    return match.group(1) + new_value + match.group(3)


def main():
    with io.open(TARGET, encoding="utf-8", newline="") as handle:
        text = handle.read()
    with io.open(SNAPSHOT, encoding="utf-8", newline="") as handle:
        snapshot = handle.read()
    if text != snapshot:
        print("ABORTED: lists/direct-fixes.md differs from the pre-edit snapshot.")
        return 1

    lines = text.split("\n")

    # map each item id -> index of its own baseline line
    owner = {}
    current = None
    for i, line in enumerate(lines):
        heading = HEADING_RE.match(line)
        if heading:
            current = heading.group(1)
            continue
        if current and BASELINE_RE.match(line):
            owner[current] = i

    problems = []
    for item in ITEM_IDS:
        if item not in owner:
            problems.append("%s: no `### %s` block with a 基线 line" % (item, item))
    if problems:
        print("ABORTED:")
        for line in problems:
            print("  " + line)
        return 1

    for item in ITEM_IDS:
        index = owner[item]
        match = BASELINE_RE.match(lines[index])
        if match.group(2) != OLD_VALUE:
            problems.append("%s: 基线 is %r, expected %r" % (item, match.group(2), OLD_VALUE))
    if problems:
        print("ABORTED (old-value assertion failed):")
        for line in problems:
            print("  " + line)
        return 1

    before_count = len([l for l in lines if BASELINE_RE.match(l)])
    for item in ITEM_IDS:
        index = owner[item]
        replaced = substitute_baseline(lines[index], NEW_VALUE)
        if replaced is None or replaced == lines[index]:
            problems.append("%s: substitution produced no change" % item)
        lines[index] = replaced

    if problems:
        print("ABORTED (substitution failed):")
        for line in problems:
            print("  " + line)
        return 1

    out = "\n".join(lines)
    with io.open(TARGET, "w", encoding="utf-8", newline="") as handle:
        handle.write(out)

    # ---- read back and verify ----
    with io.open(TARGET, encoding="utf-8", newline="") as handle:
        after = handle.read().split("\n")
    after_owner = {}
    current = None
    for i, line in enumerate(after):
        heading = HEADING_RE.match(line)
        if heading:
            current = heading.group(1)
            continue
        if current and BASELINE_RE.match(line):
            after_owner[current] = i

    fails = []
    for item in ITEM_IDS:
        value = BASELINE_RE.match(after[after_owner[item]]).group(2)
        if value != NEW_VALUE:
            fails.append("%s: 基线 is %r after write" % (item, value))
    after_count = len([l for l in after if BASELINE_RE.match(l)])
    if after_count != before_count:
        fails.append("基线 field count changed: %d -> %d" % (before_count, after_count))
    if fails:
        print("READ-BACK FAILED:")
        for line in fails:
            print("  " + line)
        return 1

    print("updated %d list-B items; 基线 field count unchanged at %d" % (
        len(ITEM_IDS), after_count))
    for item in ITEM_IDS:
        print("  %-6s %s -> %s" % (item, OLD_VALUE, NEW_VALUE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
