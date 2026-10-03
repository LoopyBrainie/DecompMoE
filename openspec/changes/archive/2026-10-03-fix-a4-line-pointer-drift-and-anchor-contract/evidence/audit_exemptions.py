"""Task 9.2 precursor: name the marker behind every historical exemption.

The census exempts a WHOLE LINE if any marker substring appears anywhere on it.
`ex-` and `→` are extremely loose (`example`, any arrow), so an exemption whose
only trigger is one of those is not a nameable historical citation. This script
prints, per exempt line, which markers fired and whether the line reads as a
genuine historical citation.
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pc", HERE / "pointer_census.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

rows = []
for path in pc.iter_files():
    r = pc.rel(path)
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if "http" in line:
            continue
        if pc.classify(line) is None:
            continue
        if not pc.has_historical_marker(line):
            continue
        low = line.lower()
        fired = [m for m in pc.HISTORICAL_MARKERS if m.lower() in low]
        # A nameable historical marker is one that actually asserts history.
        substantive = [m for m in fired if m.strip() not in ("ex-", "→")]
        rows.append((r, lineno, fired, bool(substantive), line.strip()[:150]))

print(f"exempt lines: {len(rows)}")
weak = [r for r in rows if not r[3]]
print(f"  substantive marker present: {len(rows) - len(weak)}")
print(f"  ONLY loose marker (ex- / ->): {len(weak)}")
print()
for r, lineno, fired, sub, text in rows:
    flag = "OK " if sub else "WEAK"
    print(f"[{flag}] {r}:{lineno}  markers={fired}")
    print(f"        {text}")
sys.exit(0)
