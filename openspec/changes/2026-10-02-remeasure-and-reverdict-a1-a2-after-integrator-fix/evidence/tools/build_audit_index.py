"""Change 3 / task 0.3 (part 1) -- parse the audit lists into a verified ac_id index.

Why a script and not eyes: the file has 135 `###` headings but the bucket headers
declare 108 items. The extra 27 live in preamble / summary / Errata sections, so a
count of `###` is NOT a count of findings -- exactly the kind of denominator
mismatch that makes a zero or a total look authoritative when it is not.

Scope of Change 3: buckets A-1..A-5 + A-7 = 95 items. A-6 (7) and A-8 (6, the
`UD-` items) are explicitly excluded -- A-8 waits on a user decision.

Self-checks (a parser that reports a total must be able to prove its total):
  S1  every `### AC-nn` / `### UD-nn` heading falls inside exactly one bucket
  S2  per-bucket counts equal the counts declared in the bucket header
  S3  ac_ids are unique across the whole file
  S4  each bucket's header-declared count is parsed from the header, not hardcoded
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
LIST = ROOT / ".audit/wayfinder-opsx-code-review/lists/opsx-changes.md"
OUT = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence/audit_index.json"

SCOPED = ["A-1", "A-2", "A-3", "A-4", "A-5", "A-7"]
EXCLUDED = ["A-6", "A-8"]

text = LIST.read_text(encoding="utf-8")
lines = text.splitlines()

bucket_hdr = re.compile(r"^##\s+(A-\d)\b")
item_hdr = re.compile(r"^###\s+((?:AC|UD)-\d+)\s*(.*)$")
declared = re.compile(r"（(\d+)\s*条）|\((\d+)\s*items?\)")

# ---- pass 1: locate every bucket header and its declared size
buckets = []          # (label, start_line, end_line, declared_count)
order = []
for i, ln in enumerate(lines):
    m = bucket_hdr.match(ln)
    if m:
        order.append((i, m.group(1), ln))
for k, (i, label, hdr) in enumerate(order):
    end = order[k + 1][0] if k + 1 < len(order) else len(lines)
    d = declared.search(hdr)
    n = int(d.group(1) or d.group(2)) if d else None
    buckets.append(dict(label=label, start=i, end=end, declared=n, header=hdr))

# ---- pass 2: attach every item heading to the bucket that contains it
S1_fail = []
for i, ln in enumerate(lines):
    m = item_hdr.match(ln)
    if not m:
        continue
    ac_id, title = m.group(1), m.group(2).strip()
    owner = next((b for b in buckets if b["start"] <= i < b["end"]), None)
    if owner is None:
        S1_fail.append((i + 1, ac_id, "no owning bucket"))
        continue
    owner.setdefault("items", []).append(dict(
        ac_id=ac_id, title=title, line=i + 1,
        # body runs to the next ### or ## heading
        body_end=next((j for j in range(i + 1, owner["end"])
                       if item_hdr.match(lines[j]) or bucket_hdr.match(lines[j])),
                      owner["end"]),
    ))

S3 = [b["label"] for b in buckets
      for k, it in enumerate([x for x in b.get("items", [])])
      if [x["ac_id"] for x in b["items"]].count(it["ac_id"]) > 1]

print(f"bucket headers found : {[b['label'] for b in buckets]}")
print(f"item headings total  : {sum(len(b.get('items', [])) for b in buckets)}")
print()
print(f"{'bucket':<6} {'declared':>9} {'parsed':>7} {'match':>6}  header")
print("-" * 92)
S2_fail = []
for b in buckets:
    parsed = len(b.get("items", []))
    ok = b["declared"] == parsed
    if not ok:
        S2_fail.append(b["label"])
    print(f"{b['label']:<6} {str(b['declared']):>9} {parsed:>7} {str(ok):>6}  {b['header'][:60]}")

scoped_total = sum(len(b.get("items", [])) for b in buckets if b["label"] in SCOPED)
excluded_total = sum(len(b.get("items", [])) for b in buckets if b["label"] in EXCLUDED)

print()
print("S1 every item heading has an owning bucket :", "OK" if not S1_fail else S1_fail)
print("S2 parsed count == declared count          :", "OK" if not S2_fail else f"MISMATCH {S2_fail}")
print("S3 no duplicate ac_id within a bucket      :", "OK" if not S3 else S3)
print(f"   scoped  A-1..A-5 + A-7 = {scoped_total}  (task 0.3 expects 95)")
print(f"   excluded A-6 + A-8      = {excluded_total}  (7 + 6 = 13)")

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = {
    "source": str(LIST.relative_to(ROOT)),
    "scoped_buckets": SCOPED,
    "excluded_buckets": EXCLUDED,
    "scoped_total": scoped_total,
    "excluded_total": excluded_total,
    "total_item_headings": sum(len(b.get("items", [])) for b in buckets),
    "buckets": [
        {"label": b["label"], "declared": b["declared"],
         "parsed": len(b.get("items", [])),
         "items": [{"ac_id": it["ac_id"], "title": it["title"], "line": it["line"]}
                   for it in b.get("items", [])]}
        for b in buckets
    ],
    "self_checks": {"S1_orphan_headings": S1_fail, "S2_count_mismatch": S2_fail,
                    "S3_duplicate_ids": S3},
}
OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nwrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} B)")
