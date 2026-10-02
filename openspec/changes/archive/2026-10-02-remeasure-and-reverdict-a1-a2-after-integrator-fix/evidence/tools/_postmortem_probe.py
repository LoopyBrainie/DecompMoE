"""事故后取证 v2：只读。

修正 v1 的两个缺陷：
  1. ROOT 深度错（parents[4] = openspec，不是仓库根）→ 改 parents[5]
  2. 条目容器取错（抓到 excluded_items n=13）→ 显式取 data["entries"]
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve()
TOOLS = HERE.parent
EV = TOOLS.parent
CHG = EV.parent
ROOT = CHG.parents[2]          # .../openspec/changes/<name> -> repo root
# 自检：父链必须一路收敛到含 .git 与 src/ 的真实仓库根
LEDGER = EV / "ledger.json"

print("=" * 72)
print("路径自检")
print("=" * 72)
print(f"ROOT   = {ROOT}")
print(f"EV     = {EV}")
print(f"CHG    = {CHG.name}")
assert (ROOT / "src" / "decompmoe").is_dir(), f"ROOT 定位错误: {ROOT}"
assert EV in LEDGER.parents

print()
print("=" * 72)
print("A. ledger.json 实际状态（显式 entries 容器）")
print("=" * 72)
raw = LEDGER.read_bytes()
data = json.loads(raw)
print(f"bytes            = {len(raw)}")
print(f"all_pending flag = {data.get('all_pending')}")
print(f"total            = {data.get('total')}")
print(f"total_in_source  = {data.get('total_in_source')}")
print(f"counts           = {data.get('counts')}")

entries = data["entries"]
print(f"\nentries n        = {len(entries)}")
print(f"entry 字段       = {sorted(entries[0].keys())}")

vd = Counter(e.get("verdict_new") for e in entries)
print(f"\nverdict_new 分布 = {dict(vd)}")

PENDING_STATES = {None, "", "PENDING"}
pending = [e for e in entries if e.get("verdict_new") in PENDING_STATES]
filled = [e for e in entries if e.get("verdict_new") not in PENDING_STATES]
print(f"\nPENDING           = {len(pending)}")
print(f"已裁决            = {len(filled)}")

if filled:
    print("\n已裁决条目:")
    for e in filled:
        print(f"  {e.get('ac_id'):<12} {str(e.get('verdict_new')):<24} "
              f"kind={e.get('invalidation_kind')!r} status={e.get('status')!r}")
        cr = e.get("code_refs")
        print(f"      code_refs({len(cr) if cr else 0}) = {cr}")
        rem = e.get("remeasurement")
        if isinstance(rem, dict):
            for k, v in rem.items():
                print(f"      remeasure.{k} = {str(v)[:150]}")
        ve = e.get("verdict_evidence")
        print(f"      verdict_evidence = {str(ve)[:200]}")
        dep = e.get("dependency")
        print(f"      dependency = {str(dep)[:200]}")

print()
print("=" * 72)
print("B. 仓库根目录残留脚本（git status 报 untracked 的那些）")
print("=" * 72)
pat = ("_*.py", "_*.bak", "_*.txt")
found = []
for p in pat:
    found += list(ROOT.glob(p))
for p in sorted(set(found)):
    st = p.stat()
    print(f"  {p.name:<26} {st.st_size:>8} B")
if not found:
    print("  (无)")

print()
print("=" * 72)
print("C. 仓库根目录其它 untracked（git ls-files --others）")
print("=" * 72)
import subprocess
r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others",
                    "--exclude-standard"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
others = [ln for ln in r.stdout.splitlines() if ln.strip()]
print(f"untracked 总数 = {len(others)}")
for ln in others:
    print(f"  {ln}")

print()
print("=" * 72)
print("D. baseline.json 是否被重跑（mtime 对照）")
print("=" * 72)
import datetime as _dt
for name in ("ledger.json", "baseline.json", "oracle_recheck.json",
             "errata_index.json", "audit_findings.json", "audit_index.json"):
    p = EV / name
    if p.is_file():
        ts = _dt.datetime.fromtimestamp(p.stat().st_mtime)
        print(f"  {name:<24} {p.stat().st_size:>8} B  mtime={ts:%Y-%m-%d %H:%M:%S}")
