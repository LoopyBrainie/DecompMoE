#!/usr/bin/env python3
"""Emit the bucket histogram of the audit ledger's input classification.

Source of truth for the denominators this change re-verifies against:
    .audit/gradual-review-2026-10-07/_work3/c1/classified.json

Run from the repository root:
    uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/baseline_buckets.py
"""
import json
from collections import Counter
from pathlib import Path

CLASSIFIED = Path(".audit/gradual-review-2026-10-07/_work3/c1/classified.json")


def main() -> None:
    payload = json.loads(CLASSIFIED.read_text(encoding="utf-8"))
    items = payload["items"] if isinstance(payload, dict) else payload
    histogram = Counter(item.get("bucket") for item in items)
    print(json.dumps({"total": len(items), "buckets": dict(sorted(histogram.items()))},
                     ensure_ascii=False, indent=2, sort_keys=True))
    for bucket in ("opsx-change", "direct-fix"):
        refs = sorted(str(i.get("id") or i.get("ref")) for i in items
                      if i.get("bucket") == bucket)
        print(f"\n{bucket} ({len(refs)}): " + ", ".join(refs))


if __name__ == "__main__":
    main()
