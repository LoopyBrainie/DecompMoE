"""事故后取证：只读。核实 ledger.json 真实状态 + 根目录残留脚本清单。

不写任何仓库文件。输出 UTF-8。
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[4]
EV = Path(__file__).resolve().parents[1]
LEDGER = EV / "ledger.json"

print("=" * 70)
print("A. ledger.json 实际状态")
print("=" * 70)
raw = LEDGER.read_bytes()
print(f"bytes            = {len(raw)}")
print(f"all_pending flag = {json.loads(raw).get('all_pending')}")

data = json.loads(raw)
print(f"top-level keys   = {sorted(data.keys())}")

# 找条目容器
entries = None
for k, v in data.items():
    if isinstance(v, list) and v and isinstance(v[0], dict):
        entries = v
        print(f"entries container= {k!r}  n={len(v)}")
        break
if entries is None:
    print("!! 未找到条目容器")
    raise SystemExit(1)

pending = [e for e in entries if e.get("verdict_new") in (None, "", "PENDING")]
done = [e for e in entries if e not in pending]
print(f"\nPENDING           = {len(pending)}")
print(f"已裁决(非PENDING)  = {len(done)}")
print(f"verdict_new 分布  = {dict(Counter(e.get('verdict_new') for e in entries))}")

if done:
    print("\n已裁决条目 id:")
    for e in done:
        print(f"  {e.get('id'):<12} {str(e.get('verdict_new')):<22} "
              f"invalidation_kind={e.get('invalidation_kind')!r} "
              f"n_code_refs={len(e.get('code_refs') or [])}")
        rem = e.get("remeasurement")
        if isinstance(rem, dict):
            print(f"                 remeasurement keys={sorted(rem.keys())}")

print("\n" + "=" * 70)
print("B. 根目录残留脚本（审阅者可能留下的）")
print("=" * 70)
for p in sorted(ROOT.glob("_*.py")) + sorted(ROOT.glob("_*.bak")) + sorted(ROOT.glob("_*.txt")):
    st = p.stat()
    print(f"  {p.name:<28} {st.st_size:>8} B  mtime={st.st_mtime_ns}")

print("\n" + "=" * 70)
print("C. evidence/ 目录清单")
print("=" * 70)
for p in sorted(EV.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(EV).as_posix():<48} {p.stat().st_size:>8} B")

print("\n" + "=" * 70)
print("D. TEMP 沙箱残留（审阅者自称的恢复素材）")
print("=" * 70)
import os
for base in (os.environ.get("TEMP"), r"C:\Windows\Temp"):
    if not base:
        continue
    d = Path(base) / "dmrev"
    if d.is_dir():
        for p in sorted(d.rglob("*")):
            if p.is_file():
                print(f"  {p}  {p.stat().st_size} B")
