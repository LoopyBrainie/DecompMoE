#!/usr/bin/env python3
"""4.2 汇总对账：台账 `**HEAD 复验（ded0944）**` 字段 <-> evidence/reverify/<REF>.md。

三桶分流。双向性是本脚本存在的理由（design.md D-7）：
  - 正向：台账每个 `**HEAD 复验（ded0944）**` 必须有对应的 evidence 记录；
  - 反向：每个 opsx-change 的 evidence 记录必须在台账里有同值字段。
单向检查无法发现「evidence 已落盘但台账漏写」——该失效模式在本轮真实发生过：
一次批量编辑把 6 条的裁定按**文件位置**而非按 **ref** 落到错误条目上，
所有正向检查都会通过，只有双向 + 按 ref 索引才拦得住。

direct-fix 桶相反：3.6 承诺「仅 pin 更新、不逐条追裁定」，故其 evidence 记录
存在而台账**不得**出现 HEAD 复验字段；带记录与否本身受下述判据约束：
判据是「被引文件在 dde0e1d..ded0944 窗口内零 commit」。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVERIFY = HERE / "reverify"

AUDIT = ".audit/gradual-review-2026-10-07"
# Anchor on the artifact, not on a path depth. A fixed `parents[N]` is correct
# only until the change is archived: this file moves from
# `openspec/changes/<name>/evidence/` to `openspec/changes/archive/<name>/evidence/`,
# one level deeper, and the hard-coded index silently starts resolving one level
# too high (it reached `openspec/` and looked for `openspec/.audit/...`). Locating
# the repo by the presence of the audit tree keeps the script runnable in both
# locations and after any future re-nesting.
_candidates = [HERE, *HERE.parents]
REPO = next(
    (c for c in _candidates if (c / AUDIT / "lists").is_dir()),
    None,
)
if REPO is None:
    raise SystemExit(
        f"repo root not found: no ancestor of {HERE} contains {AUDIT}/lists"
    )
LISTS = REPO / AUDIT / "lists"
CLASSIFIED = REPO / AUDIT / "_work3/c1/classified.json"

OPSX, DIRECT = "opsx-change", "direct-fix"
FIELD_RE = re.compile(r"^### ((?:FIX|ARC)-\d+) — .+$", re.M)
VERDICT_RE = re.compile(r"^- \*\*HEAD 复验（ded0944）\*\*：`([A-Z_]+)`", re.M)
COMMIT_RE = re.compile(r"^- \*\*修复 commit\*\*：`([0-9a-f]{7,40})`", re.M)
EV_VERDICT_RE = re.compile(r"\*\*Verdict\*\*: `([A-Z_]+)`")
CLOSED = "CLOSED_BY_COMMIT"


def ledger_fields(path: Path) -> dict[str, dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    marks = list(FIELD_RE.finditer(text))
    out: dict[str, dict[str, object]] = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        block = text[m.start() : end]
        out[m.group(1)] = {
            "verdict": VERDICT_RE.search(block),
            "commit": COMMIT_RE.search(block),
            "n": len(re.findall(r"^- \*\*HEAD 复验", block, re.M)),
        }
    return out


def main() -> int:
    items = json.loads(CLASSIFIED.read_text(encoding="utf-8"))["items"]
    bucket = {i["ref"]: i["bucket"] for i in items}
    opsx = sorted(r for r, b in bucket.items() if b == OPSX)
    led = ledger_fields(LISTS / "opsx-changes.md")
    direct = ledger_fields(LISTS / "direct-fixes.md")
    records = sorted(p.stem for p in REVERIFY.glob("*.md"))

    failures: list[str] = []
    print(f"classified.json  bucket {OPSX} = {len(opsx)}  bucket {DIRECT} = "
          f"{sum(1 for b in bucket.values() if b == DIRECT)}")
    print(f"opsx-changes.md  entries carrying a HEAD 复验 field = {len(led)}")
    d_with = sorted(r for r, e in direct.items() if e["n"])
    print(f"direct-fixes.md  entries carrying a HEAD 复验 field = {len(d_with)}  (must be 0)")
    print(f"evidence/reverify/*.md = {len(records)}")
    print()

    print("--- opsx-change: ledger <-> evidence (bidirectional, keyed by ref) ---")
    print(f"{'ref':<9} {'ledger':<20} {'evidence':<20} {'commit':<9} ok")
    for ref in sorted(set(opsx) | set(led) | set(records) & set(opsx)):
        e = led.get(ref)
        lv = e["verdict"].group(1) if e and e["verdict"] else "MISSING"
        lc = e["commit"].group(1) if e and e["commit"] else "—"
        rec = REVERIFY / f"{ref}.md"
        if ref in opsx and ref in records:
            m = EV_VERDICT_RE.search(rec.read_text(encoding="utf-8"))
            ev = m.group(1) if m else "UNPARSED"
        else:
            ev = "NO RECORD" if ref in opsx else "STRAY RECORD"
        ok = lv == ev and ref in opsx and e is not None and e["n"] == 1
        if not ok:
            failures.append(f"{ref}: ledger={lv} evidence={ev} n_fields="
                            f"{e['n'] if e else 0} in_bucket={ref in opsx}")
        print(f"{ref:<9} {lv:<20} {ev:<20} {lc:<9} {'OK' if ok else '*** FAIL ***'}")

    print()
    print("--- direct-fix: records exist, ledger must NOT carry per-entry verdicts ---")
    drecs = sorted(r for r in records if bucket.get(r) == DIRECT)
    for ref in drecs:
        leaked = ref in direct and direct[ref]["n"] > 0
        if leaked:
            failures.append(f"{ref}: direct-fix entry carries a HEAD 复验 field "
                            f"but 3.6 scopes this change to pin-update only")
        print(f"  {ref:<9} record=yes  ledger_verdict_field={'LEAKED' if leaked else 'none (ok)'}")
    if not drecs:
        failures.append("no direct-fix records found — reverify_direct_fixes.py output missing")

    print()
    # D-1 invariant: the commit column is mandatory for, and exclusive to, CLOSED_BY_COMMIT
    for ref, e in led.items():
        v = e["verdict"].group(1) if e["verdict"] else "MISSING"
        has = bool(e["commit"])
        if (v == CLOSED) != has:
            failures.append(f"{ref}: verdict={v} commit-field={has} "
                            f"(D-1: column present iff CLOSED_BY_COMMIT)")
    n_closed = sum(1 for e in led.values() if e["verdict"] and e["verdict"].group(1) == CLOSED)
    n_commit = sum(1 for e in led.values() if e["commit"])
    print(f"CLOSED_BY_COMMIT = {n_closed} ; 修复 commit fields = {n_commit} ; "
          f"D-1 invariant: {'OK' if n_closed == n_commit else 'FAIL'}")
    print(f"value distribution: "
          f"{ {v: sum(1 for e in led.values() if e['verdict'] and e['verdict'].group(1) == v) for v in sorted({e['verdict'].group(1) for e in led.values() if e['verdict']})} }")
    print()
    if failures:
        print("CROSSCHECK FAILED")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("CROSSCHECK OK — bidirectional, no orphans on either side, D-1 invariant holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
