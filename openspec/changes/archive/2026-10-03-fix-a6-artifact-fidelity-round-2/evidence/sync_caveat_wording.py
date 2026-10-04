"""Surgically carry the generator's corrected 口径 wording into the live list.

The live `lists/opsx-changes.md` must not be regenerated (it carries hand-appended
Errata sections). But the 口径 section IS generator-produced, so changing the
generator alone would leave the live file stale -- and nothing would detect the
drift. This script copies one specific passage from a fresh generator run into
the live file, then asserts the two now agree, so the next reader can tell
whether the wording is in sync.
"""

from __future__ import annotations

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The authoritative way to count `基线` declarations: the FIELD DECLARATION line,
# not the entry block. Counting entry blocks mixes in the 4 non-entry `###`
# headings and yields a different number, which is how the review's F-1 went
# wrong. See design.md D1.
BASELINE_RE = re.compile(r"^\s*[-*]?\s*\**`?基线`?\**\s*[:：]\s*(\S+)", re.M)


def _repo_root(start):
    path = os.path.abspath(start)
    while True:
        if (os.path.isdir(os.path.join(path, "openspec"))
                and os.path.isdir(os.path.join(path, ".audit"))):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            raise RuntimeError("repo root not found above %s" % start)
        path = parent


REPO = _repo_root(HERE)
LIVE = os.path.join(
    REPO, ".audit", "wayfinder-opsx-code-review", "lists", "opsx-changes.md"
)
PREFIX = sys.argv[1]

# The old passage, as it currently stands in the live list.
OLD = (
    "   因此整文件删除记作 `[0, 0]`。原先缺失的生成脚本已补齐为 "
    "`evidence/build_pin_drift.py`，并以 `pin..188b9fb` 重跑、\n"
    "   与原表**逐键相等**（60 文件 / 105 区间 / 0 差异）作为自检。"
)

# The new passage is taken from the generator run, not retyped here, so the two
# cannot drift apart by transcription.
MARK_START = "   因此整文件删除记作 `[0, 0]`。"
MARK_END = "   旧版自检把键集差异折进区间比较后打印"


def read(path):
    with io.open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


live = read(LIVE)
prefix = read(PREFIX)

problems = []

# Counts captured BEFORE the write: this edit is surgical, so the invariant is
# that nothing else moves. Comparing against a hardcoded number with a different
# regex would just re-introduce the F-1 counting-unit mistake.
before_errata = sum(1 for l in live.split("\n") if l.startswith("## Errata"))
before_baseline = len(BASELINE_RE.findall(live))
before_items = live.count("### AC-")

# ---- pull the corrected passage out of the fresh prefix ----
lines = prefix.split("\n")
try:
    start = next(i for i, l in enumerate(lines) if l.startswith(MARK_START))
except StopIteration:
    print("ABORTED: marker %r not found in the generated prefix" % MARK_START)
    sys.exit(1)
end = next((i for i, l in enumerate(lines) if l.startswith(MARK_END)), None)
if end is None:
    print("ABORTED: end marker %r not found in the generated prefix" % MARK_END)
    sys.exit(1)
# the end marker's line plus the next one (the 旧版 sentence is the final line)
new = "\n".join(lines[start:end + 1])
if OLD in live:
    updated = live.replace(OLD, new, 1)
    action = "replaced"
elif new in live:
    updated = live
    action = "already in sync"
else:
    print("ABORTED: neither the old passage nor the new one is present in the live file.")
    print("  The list drifted; re-read and patch by hand.")
    sys.exit(1)

with io.open(LIVE, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(updated)

# ---- read back and assert the RESULT, not just that a write happened ----
back = read(LIVE)
after_errata = sum(1 for l in back.split("\n") if l.startswith("## Errata"))
after_baseline = len(BASELINE_RE.findall(back))
after_items = back.count("### AC-")

if OLD in back:
    problems.append("old passage still present after write")
if new not in back:
    problems.append("new passage absent after write")
if after_errata != before_errata:
    problems.append("Errata section count moved: %d -> %d"
                    % (before_errata, after_errata))
if after_baseline != before_baseline:
    problems.append("基线 declaration count moved: %d -> %d"
                    % (before_baseline, after_baseline))
if after_items != before_items:
    problems.append("item heading count moved: %d -> %d" % (before_items, after_items))

if problems:
    print("WRITE VERIFICATION FAILED:")
    for p in problems:
        print("  " + p)
    sys.exit(1)

print("口径 passage: %s" % action)
print("  live file      : %d chars, %d lines" % (len(back), len(back.split("\n"))))
print("  Errata sections: %d (unchanged)" % after_errata)
print("  基线 fields    : %d (unchanged)" % after_baseline)
print("  item headings  : %d (unchanged)" % after_items)
