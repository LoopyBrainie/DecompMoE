# -*- coding: utf-8 -*-
"""Durable record of what the rebaseline changed.

`rebaseline.py` reports the CURRENT state, so once `--apply` has run it reports
0 differences -- which would erase the only record of what moved. This diffs the
pre-edit snapshot against the corrected classified.json and writes the full
before/after table, which is what the change's evidence should carry.
"""
import io
import json
import os
import sys

REPO = r"D:/myProject/DecompMoE"
EVIDENCE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(EVIDENCE, "_pre_edit_classified.json")
NEW = os.path.join(REPO, ".audit", "wayfinder-opsx-code-review", "_work", "classified.json")
OUT = os.path.join(EVIDENCE, "rebaseline_changes.md")


def index(path):
    data = json.load(io.open(path, encoding="utf-8"))
    out = {}
    for bucket in ("opsx-change", "user-decision", "direct-fix"):
        for item in data.get(bucket, []):
            out.setdefault(item["bucket_id"], item)
    return out


def main():
    old, new = index(OLD), index(NEW)
    rows = []
    for bid in sorted(set(old) & set(new)):
        o, n = old[bid].get("baseline_status"), new[bid].get("baseline_status")
        if o != n:
            rows.append((bid, new[bid].get("location_file"),
                         new[bid].get("location_line"), o, n))

    counts = {}
    for _b, _f, _l, _o, n in rows:
        counts[n] = counts.get(n, 0) + 1

    lines = [
        "# Rebaseline change set (pin `6593a06` -> frozen `95718cf`)",
        "",
        "Baseline recomputed with the **unchanged** legacy 口径 (`drift` interval containment).",
        "Diffed from `evidence/_pre_edit_classified.json` against the corrected",
        "`_work/classified.json`, so it survives the fact that `rebaseline.py` now reports",
        "0 differences once applied.",
        "",
        "**%d `基线` fields changed.** New values: %s" % (
            len(rows),
            ", ".join("`%s` %d" % (k, v) for k, v in sorted(counts.items()))),
        "",
        "| item | file | pin line | before | after |",
        "|---|---|---|---|---|",
    ]
    for bid, path, line, o, n in rows:
        lines.append("| %s | `%s` | %s | `%s` | `%s` |" % (
            bid, path, line, o, n))
    lines += [
        "",
        "## Not changed by design",
        "",
        "- 纯插入是否应算 `touched-since-pin`：**未重定义**。漂移表已把 `inserted` / `modified`",
        "  分离成两个视图，但判定仍按旧的 merged 口径。实测现有条目中 0 条会因此改变状态",
        "  （见 `evidence/inserted_only_diff.txt`）。",
        "- 其它段的 `verdict_class` / `severity`：未动，只重算了 `基线`。",
        "",
    ]
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("wrote %s ; %d changed" % (OUT, len(rows)))
    for k, v in sorted(counts.items()):
        print("  %-30s %d" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
