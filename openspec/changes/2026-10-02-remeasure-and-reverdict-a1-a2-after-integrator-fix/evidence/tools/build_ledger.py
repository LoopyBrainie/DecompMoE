"""Change 3 / task 0.3 -- the 95-item ledger skeleton, all status PENDING.

Schema is fixed by tasks.md 0.3 and must not drift:
  {ac_id, bucket, title,
   dependency: {depends, derivation, code_refs},
   invalidation_kind: numeric|coordinate|provenance|none,
   remeasurement: {old, new, method},
   verdict_old, verdict_new, verdict_evidence, status}

The verification is a set-diff against the source file, NOT a count. A count
cannot distinguish "the right 95" from "95 of something else", and this repo has
already produced a count that lied (135 `###` headings vs 108 findings).

That set-diff is done along a SECOND, INDEPENDENT extraction path. The index
built for task 0.3's input walks bucket headers then items; this one walks items
and derives the bucket from the nearest preceding `## A-n` header. If both agree,
a shared parsing bug is much less likely -- reusing the same extraction to check
itself would prove nothing.

Per D3, the audit's 裁决 / 基线 fields are transcribed into clearly-marked
non-authoritative slots and are never the basis for a new verdict.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
EV = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence"
LIST = ROOT / ".audit/wayfinder-opsx-code-review/lists/opsx-changes.md"

SCOPED = ["A-1", "A-2", "A-3", "A-4", "A-5", "A-7"]
EXCLUDED = ["A-6", "A-8"]

text = LIST.read_text(encoding="utf-8")
lines = text.splitlines()

# ---------- INDEPENDENT extraction: item-first, bucket derived from last header
cur = None
extracted = []            # (ac_id, bucket, title, line)
for i, ln in enumerate(lines):
    b = re.match(r"^##\s+(A-\d)\b", ln)
    if b:
        cur = b.group(1)
        continue
    m = re.match(r"^###\s+((?:AC|UD)-\d+)\s*(?:—|--|-)?\s*(.*)$", ln)
    if m and cur:
        extracted.append((m.group(1), cur, m.group(2).strip(), i + 1))

scoped = [e for e in extracted if e[1] in SCOPED]
excluded = [e for e in extracted if e[1] in EXCLUDED]

# ---------- second opinion: the index built earlier
idx = json.loads((EV / "audit_index.json").read_text(encoding="utf-8"))
idx_pairs = {(it["ac_id"], b["label"])
             for b in idx["buckets"] for it in b["items"]}
ext_pairs = {(e[0], e[1]) for e in extracted}
setdiff = idx_pairs ^ ext_pairs

print(f"independent extraction : {len(extracted)} items total, {len(scoped)} scoped, {len(excluded)} excluded")
print(f"index (earlier run)    : {len(idx_pairs)} pairs")
print(f"symmetric difference   : {len(setdiff)}  {'OK' if not setdiff else sorted(setdiff)}")
print()

assert not setdiff, f"extraction paths disagree: {setdiff}"
assert len(scoped) == 95, f"scoped is {len(scoped)}, expected 95"
assert len(excluded) == 13, f"excluded is {len(excluded)}, expected 13"
ids = [e[0] for e in scoped]
assert len(ids) == len(set(ids)), "duplicate ac_id in scoped set"

# ---------- provenance fields, for the per-item derivations that follow
prov = {}
cur = None
buf = None
for ln in lines:
    b = re.match(r"^##\s+(A-\d)\b", ln)
    if b:
        cur = b.group(1)
        buf = None
        continue
    m = re.match(r"^###\s+((?:AC|UD)-\d+)\s*(?:—|--|-)?", ln)
    if m and cur:
        buf = {"bucket": cur, "lines": [ln]}
        prov[m.group(1)] = buf
        continue
    if buf is not None:
        buf["lines"].append(ln)
for k, v in prov.items():
    blk = "\n".join(v["lines"])
    g = lambda p: (re.search(p, blk).group(1).strip() if re.search(p, blk) else None)
    v["location"] = g(r"\*\*位置\*\*[：:]\s*`?([^`（(\n]+)")
    v["requirement"] = g(r"\*\*Requirement\*\*[：:]\s*(.+)")
    v["audit_verdict"] = g(r"\*\*裁决\*\*[：:]\s*`?([A-Z_]+)")
    v["audit_baseline"] = g(r"\*\*基线\*\*[：:]\s*`?([\w-]+)")
    v["severity"] = g(r"\*\*严重性\*\*[：:]\s*([A-Z]+)")
    v["problem"] = g(r"\*\*问题\*\*[：:]\s*(.+)")
    del v["lines"]

ledger = []
for ac_id, bucket, title, line in scoped:
    p = prov[ac_id]
    ledger.append({
        "ac_id": ac_id,
        "bucket": bucket,
        "title": title,
        "source_line_at_pin": line,
        "dependency": {
            "depends": None,              # decided in 1.x..6.x by three-step derivation
            "derivation": None,           # D1 step 1->2->3, must cite a file:line
            "code_refs": None,
        },
        "invalidation_kind": None,       # numeric | coordinate | provenance | none
        "remeasurement": {"old": None, "new": None, "method": None},
        "verdict_old": p["audit_verdict"],
        "verdict_new": None,
        "verdict_evidence": None,
        "status": "PENDING",
        "provenance": {
            "location_at_pin": p["location"],
            "requirement": p["requirement"],
            "severity": p["severity"],
            "audit_verdict_claim": p["audit_verdict"],
            "audit_baseline_claim": p["audit_baseline"],
            "problem_statement": p["problem"],
            "authority_note": ("audit 裁决/基线 are transcribed for traceability ONLY; per design.md "
                               "D3 they are never the basis for verdict_new, which must be "
                               "re-derived from `git show` / measurement"),
        },
    })

# ---------------------------------------------------------- 9 unregistered (D9)
# Blind spot 1 registers 9 upstream findings with NO entity in classified.json.
# They are table rows, not `###` headings, so they have no ac_id, no bucket and
# NO pin coordinate. They are a SEPARATE set: the "ids == source `###` headings"
# assertion stays exact over the 95, and gets its own criterion over the 9. Weakening
# the 95 assertion into a subset test would make the exception invisible.
errata = json.loads((EV / "errata_index.json").read_text(encoding="utf-8"))
x_src = errata["unregistered_findings"]
X = []
for u in x_src["entries"]:
    X.append({
        "ac_id": u["ac_id"],
        "bucket": u["bucket"],
        "title": u["statement"].split("。")[0][:90],
        "source_line_at_pin": None,
        "in_source_as_heading": False,
        "dependency": {"depends": None, "derivation": None, "code_refs": None},
        "invalidation_kind": None,
        "remeasurement": {"old": None, "new": None, "method": None},
        "verdict_old": None,
        "verdict_new": None,
        "verdict_evidence": None,
        "status": "PENDING",
        "provenance": {
            "upstream_id": u["upstream_id"],
            "origin": "盲区 1（classified.json 中无实体）",
            "source_ref": u["source_ref"],
            "bucket_rationale": u["bucket_rationale"],
            "nearest_existing_item": u["nearest_existing_item"],
            "pin_coordinate": None,
            "pin_coordinate_note": u["pin_coordinate_note"],
            "authority_note": ("无 裁决/基线 字段可转抄；且 D8 禁止引用勘误作为依据。"
                               "verdict_new 必须由 D1 三段推导从零建立，"
                               "第 3 步的 file:line 亦须自行定位。"),
        },
    })
ledger += X

# ------------------------------------------------------------ set invariants
src_ids = {e[0] for e in scoped}                       # the 95, from the source
x_ids = {e["ac_id"] for e in X}                        # the 9, from errata_index
led_ids = [e["ac_id"] for e in ledger]
bid = (src_ids | x_ids) - set(led_ids)                 # in scope, missing from ledger
bex = set(led_ids) - (src_ids | x_ids)                 # in ledger, not in scope
overlap = src_ids & x_ids                              # namespaces must not cross
problems = []
if len(ledger) != 104:
    problems.append(f"ledger has {len(ledger)} entries, expected 104")
if len(led_ids) != len(set(led_ids)):
    problems.append("duplicate ac_id in ledger")
if overlap:
    problems.append(f"X- and AC-/UD- namespaces overlap: {sorted(overlap)}")
if bid or bex:
    problems.append(f"ledger/scope mismatch  missing={sorted(bid)} extra={sorted(bex)}")

by_bucket = {}
for e in ledger:
    by_bucket[e["bucket"]] = by_bucket.get(e["bucket"], 0) + 1

doc = {
    "schema": ["ac_id", "bucket", "title", "source_line_at_pin", "in_source_as_heading",
               "dependency{depends,derivation,code_refs}", "invalidation_kind",
               "remeasurement{old,new,method}", "verdict_old", "verdict_new",
               "verdict_evidence", "status", "provenance"],
    "scoped_buckets": SCOPED,
    "excluded_buckets": EXCLUDED,
    "excluded_items": [dict(ac_id=e[0], bucket=e[1], title=e[2])
                       for e in excluded],
    "counts": by_bucket,
    "total": len(ledger),
    "total_in_source": len(src_ids),
    "total_unregistered": len(x_ids),
    "all_pending": all(e["status"] == "PENDING" for e in ledger),
    "verification": {
        "independent_extraction_total": len(extracted),
        "scoped_in_source": len(src_ids),
        "unregistered_outside_source": len(x_ids),
        "excluded": len(excluded),
        "setdiff_vs_earlier_index": len(setdiff),
        "missing_from_ledger": sorted(bid),
        "extra_in_ledger": sorted(bex),
        "namespace_overlap": sorted(overlap),
        "ac_ids_unique": len(led_ids) == len(set(led_ids)),
        "all_status_pending": all(e["status"] == "PENDING" for e in ledger),
        "two_criteria": {
            "criterion_a": ("95 条源内 ac_id 与源文件 `### AC-`/`### UD-` 标题集合逐字相等"
                            "——该断言保持严格，未放宽为子集包含"),
            "criterion_b": ("9 条 X- 条目逐条出现在 evidence/errata_index.json 的无实体表中，"
                            "且均不出现在源文件的 `###` 标题集合中"),
        },
        "problems": problems,
    },
    "entries": ledger,
}
(EV / "ledger.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")

print(f"per-bucket counts : {by_bucket}  total={sum(by_bucket.values())}")
print(f"  in source        : {len(src_ids)}   (A-1..A-5 + A-7)")
print(f"  unregistered (X-): {len(x_ids)}   (盲区 1, 不在源文件 `###` 标题中)")
print(f"  excluded         : {len(excluded)}   (A-6 + A-8)")
print(f"  95 + 9 + 13      = {len(src_ids) + len(x_ids) + len(excluded)} 条经手")
print(f"missing_from_ledger: {sorted(bid)}   extra_in_ledger: {sorted(bex)}")
print(f"namespace overlap  : {sorted(overlap)}")
print(f"all status PENDING : {doc['all_pending']}")
print(f"wrote evidence/ledger.json ({(EV / 'ledger.json').stat().st_size} B)")
print()
print("X- entries (blind spot 1 -> D9 bucket):")
for e in X:
    print(f"  {e['ac_id']:<12} {e['bucket']:<4} {e['title'][:52]}")
print()
print("ac_id set, in ledger order (diff target for every later bucket task):")
for i in range(0, len(led_ids), 12):
    print("  " + " ".join(f"{x:<8}" for x in led_ids[i:i + 12]))
sys.exit(1 if problems else 0)

