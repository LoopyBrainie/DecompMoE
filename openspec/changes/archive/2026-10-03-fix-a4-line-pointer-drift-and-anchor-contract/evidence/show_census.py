"""Render the census JSON: per-file counts, then the remaining actionable sites."""

import json
import sys
from collections import defaultdict
from pathlib import Path

p = Path(__file__).resolve().parent / "pointer_census.json"
data = json.loads(p.read_text(encoding="utf-8"))

print("totals:", json.dumps(data["totals"], ensure_ascii=False))
print("\n--- per file (all pointer lines) ---")
for f, n in data["per_file"].items():
    print(f"  {n:3d}  {f}")

print("\n--- remaining ACTIONABLE sites ---")
sites = data["sites"]
if not sites:
    print("  (none)")
for s in sites:
    print(f"  {s['file']}:{s['line']}  kind={s['target_kind']}  "
          f"owner={s['target_requirement']}  lines={s['referenced_lines']}")
    print(f"      {s['text'][:150]}")
sys.exit(0)

