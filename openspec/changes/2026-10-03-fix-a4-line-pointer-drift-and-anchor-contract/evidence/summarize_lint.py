"""Summarise a lint_no_line_pointers run: violation counts by check, reference and file."""

import collections
import re
import sys
from pathlib import Path

run = Path(sys.argv[1])
lines = run.read_text(encoding="utf-8", errors="replace").splitlines()
print(lines[0] if lines else "(empty report)")

by_check = collections.Counter()
by_ref: collections.Counter = collections.Counter()
by_file: collections.Counter = collections.Counter()
samples: dict[tuple, str] = {}
REASON = re.compile(r"reference '([^']+)' does not resolve in capability '([^']+)'")
FILE = re.compile(r"^(.*?):(\d+): (C[1-4])")

for i, line in enumerate(lines):
    m = FILE.match(line.strip())
    if not m:
        continue
    path, lineno, check = m.group(1), m.group(2), m.group(3)
    by_check[check] += 1
    by_file[path] += 1
    r = REASON.search(line)
    if r:
        key = (r.group(1), r.group(2))
        by_ref[key] += 1
        samples.setdefault(key, lines[i + 1].strip()[:150] if i + 1 < len(lines) else "")

print("\nby check:", dict(by_check))
print("\nby file:")
for k, n in by_file.most_common():
    print(f"  {n:4d}  {k}")
print("\nby reference (top 20):")
for (ref, cap), n in by_ref.most_common(20):
    print(f"  {n:4d}  ref={ref:16s} cap={cap}")
    print(f"        e.g. {samples[(ref, cap)]}")
sys.exit(0)
