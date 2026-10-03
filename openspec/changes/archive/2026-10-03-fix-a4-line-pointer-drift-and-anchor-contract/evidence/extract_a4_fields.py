"""Extract the A-4 section's own self-declared fields, for the Errata cross-check.

Prints, per entry: source id, origin_ids, cited `位置`, any `真实位置` the entry
claims, and the `基线` field. This is the list's self-report; the Errata records
where it disagrees with git, so both sides are shown side by side rather than
only the conclusion.
"""

import re
import sys
from pathlib import Path

LIST = Path(".audit/wayfinder-opsx-code-review/lists/opsx-changes.md")
t = LIST.read_text(encoding="utf-8")
a4 = t[t.index("## A-4 "):t.index("## A-5 ")]
entries = re.split(r"(?m)^### ", a4)[1:]

print(f"A-4 entries: {len(entries)}")
for e in entries:
    ac = e.split(" ")[0]
    def g(pat, default="-"):
        m = re.search(pat, e)
        return m.group(1) if m else default
    src = g(r"\*\*源 id\*\*：`([^`]+)`")
    oid = g(r"\*\*溯源 id\*\*（`origin_ids`）：`([^`]+)`")
    loc = g(r"\*\*位置\*\*：`([^`]+)`")
    base = g(r"\*\*基线\*\*：`([^`]+)`")
    reals = re.findall(r"真实位置[^）)]*[）)]?\s*L(\d+)", e)
    verdict = g(r"\*\*裁决\*\*：([A-Z_]+)")
    print(f"  {ac:8s} verdict={verdict:11s} src={src:6s} origin={oid:9s}")
    print(f"           loc={loc}")
    print(f"           base={base:22s} claimed_real_lines={reals}")

ids = {}
for e in entries:
    m = re.search(r"\*\*源 id\*\*：`([^`]+)`", e)
    if m:
        ids.setdefault(m.group(1), []).append(e.split(" ")[0])
print("\nsource ids used more than once:", {k: v for k, v in ids.items() if len(v) > 1})
orig = {}
for e in entries:
    m = re.search(r"\*\*溯源 id\*\*（`origin_ids`）：`([^`]+)`", e)
    if m:
        orig.setdefault(m.group(1), []).append(e.split(" ")[0])
print("origin ids used more than once:", {k: v for k, v in orig.items() if len(v) > 1})
sys.exit(0)
