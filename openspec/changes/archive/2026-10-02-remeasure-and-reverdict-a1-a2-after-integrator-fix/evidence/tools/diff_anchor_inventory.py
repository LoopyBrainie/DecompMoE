"""Diff post-apply anchor inventories against the pre-apply snapshot.

D7 observed that archiving a change WITH a delta swallows anchors. That
happened for real on the alpha apply (governance 4 -> 3, skeleton 23 -> 22).
tasks.md 7.4 forbids re-running the archive, so recovery must be surgical:
name the exact anchors that went missing, and say which are *lost* (were in
the base and vanished) versus *never added* (an ADDED Requirement that shipped
without its anchor).

Both failure shapes look identical in a raw count, and they need different
fixes, so they are reported separately.
"""
import json
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for cand in [start, *start.parents]:
        if (cand / "openspec" / "changes").is_dir():
            return cand
    raise SystemExit("repo root not found")


REPO = find_repo_root(Path(__file__).resolve().parent)
EV = (REPO / "openspec" / "changes" / "archive"
      / "2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix"
      / "evidence")
PRE = EV / "truth_source_snapshot.pre-alpha-apply.json"
POST = EV / "truth_source_snapshot.json"


def main():
    pre = json.loads(PRE.read_text(encoding="utf-8"))["specs"]
    post = json.loads(POST.read_text(encoding="utf-8"))["specs"]

    report = {"lost": {}, "added_without_anchor": {}, "retained": {}}
    for cap in pre:
        pre_ids = [a["id"] for a in pre[cap]["anchor_inventory"]]
        post_ids = [a["id"] for a in post[cap]["anchor_inventory"]]
        lost = [a for a in pre[cap]["anchor_inventory"] if a["id"] not in post_ids]
        new = [a for a in post[cap]["anchor_inventory"] if a["id"] not in pre_ids]
        report["lost"][cap] = lost
        report["added_without_anchor"][cap] = new
        report["retained"][cap] = [i for i in pre_ids if i in post_ids]

        print(f"=== {cap}")
        print(f"  pre : {len(pre_ids)} anchors, {pre[cap]['line_count']} lines")
        print(f"  post: {len(post_ids)} anchors, {post[cap]['line_count']} lines")
        if lost:
            for a in lost:
                print(f"  LOST  {a['id']}  (was line {a['line']}) "
                      f"heading={a['heading']!r}")
        if new:
            for a in new:
                print(f"  NEW   {a['id']}  (line {a['line']}) "
                      f"heading={a['heading']!r}")
        if not lost and not new:
            print("  unchanged")

    out = EV / "anchor_loss_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"\nwritten: {out.relative_to(REPO)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
