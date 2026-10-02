"""定点修补：把 ledger.json 里两条 X- 条目的 bucket 从 A-1 改到 A-3。

为什么不用 `build_ledger.py --rebuild`：
  H1 修复后 builder 默认 verify-only；--rebuild 会重建 all-PENDING 骨架，
  抹掉 A-3 桶 17 条已裁决 verdict。而这两处只是一个枚举字段。

安全约束：
  1. 先断言现值 == 期望的旧值，不符即 abort（防止覆盖别人的改动）
  2. 只改 `bucket` 这一个键，其余字段逐键比对必须完全一致
  3. 改前把原文件另存 .pre-xbucket，便于回退
  4. 写回后重新统计，确认只有 2 个条目变化、总条目数不变
"""
import copy
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
LEDGER = TOOLS.parent / "ledger.json"
MOVES = {"X-D1-02": ("A-1", "A-3"), "X-D2-02": ("A-1", "A-3")}

doc = json.loads(LEDGER.read_text(encoding="utf-8"))
entries = doc["entries"]
print(f"before: {len(entries)} entries, buckets {dict(Counter(e['bucket'] for e in entries))}")

# ---- 1. 断言现值 -----------------------------------------------------------
targets = {}
for e in entries:
    if e["ac_id"] in MOVES:
        targets[e["ac_id"]] = e
missing = set(MOVES) - set(targets)
if missing:
    print(f"ABORT: ledger has no {sorted(missing)}")
    sys.exit(1)
for ac, (old, new) in MOVES.items():
    got = targets[ac].get("bucket")
    if got != old:
        print(f"ABORT: {ac} bucket is {got!r}, expected {old!r}. Someone else changed it; "
              f"re-read before patching.")
        sys.exit(1)
    print(f"  {ac}: {old} -> {new}  (current value confirmed)")

# ---- 2. 备份 + 只改一个键 --------------------------------------------------
shutil.copy2(LEDGER, LEDGER.with_suffix(".json.pre-xbucket"))
patched = copy.deepcopy(entries)
for e in patched:
    if e["ac_id"] in MOVES:
        e["bucket"] = MOVES[e["ac_id"]][1]

# 逐键确认：除 bucket 外没有任何字段被改动
# 字段差异是 4 元组 (ac_id, key, before, after)；顺序差异是 3 元组。
# 上一版把过滤条件写成 len(d) == 3，于是把两条正当的 bucket 改动判成「意外」
# 并 abort —— 守卫拦住了写入，但它的判据是错的。两种元组必须分别处理。
diffs, order_moves = [], []
for before, after in zip(entries, patched):
    if before["ac_id"] != after["ac_id"]:
        order_moves.append((before["ac_id"], after["ac_id"]))
        continue
    for k in set(before) | set(after):
        if before.get(k) != after.get(k):
            diffs.append((after["ac_id"], k, before.get(k), after.get(k)))
expected_changes = {ac for ac in MOVES}
field_changes = {d[0] for d in diffs}
allowed = all(d[1] == "bucket" for d in diffs) and field_changes == expected_changes
print(f"  field changes: {[(d[0], d[1], d[2], d[3]) for d in diffs]}")
print(f"  order changes: {order_moves or 'none'}")
if not allowed or order_moves:
    print(f"ABORT: expected exactly one 'bucket' change on {sorted(expected_changes)}; "
          f"got fields={sorted(field_changes)}, order={order_moves}")
    sys.exit(1)

doc["entries"] = patched
LEDGER.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ---- 3. 写回后核对 ---------------------------------------------------------
after_doc = json.loads(LEDGER.read_text(encoding="utf-8"))
after = after_doc["entries"]
print(f"after : {len(after)} entries, buckets {dict(Counter(e['bucket'] for e in after))}")
assert len(after) == len(entries), "条目数变了"
vd = Counter(e.get("verdict_new") for e in after)
print(f"verdict distribution unchanged: {dict(vd)}")
for ac, (_, new) in MOVES.items():
    got = next(e["bucket"] for e in after if e["ac_id"] == ac)
    assert got == new, f"{ac} is {got}"
print("\nOK -- only the two bucket fields moved; verdicts, remeasurements, "
      "provenance and dependency all byte-identical.")
print(f"backup: {LEDGER.with_suffix('.json.pre-xbucket').name}")
