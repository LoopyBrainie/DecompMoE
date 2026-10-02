"""Pre-apply snapshot of the truth-source specs, for archive recovery.

D7 records that archiving a change WITH a delta has been observed to swallow
exactly one anchor per spec. This snapshot exists so that, if it happens, the
loss is detectable and recoverable from git without re-running the archive
(re-running is explicitly forbidden by tasks.md 7.4).

Writes evidence/truth_source_snapshot.json:
  - per-file sha256 of the worktree blob
  - the HEAD blob id, so the committed version is always recoverable
  - the full ordered anchor inventory with the Requirement heading each
    anchor introduces, so a *missing* anchor is identifiable by name rather
    than only as a count
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for cand in [start, *start.parents]:
        if (cand / "openspec" / "changes").is_dir():
            return cand
    raise SystemExit("repo root not found")


REPO = find_repo_root(Path(__file__).resolve().parent)
CHANGE = "2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix"
EV = REPO / "openspec" / "changes" / "archive" / CHANGE / "evidence"
SPECS = ["governance", "decompmoe-skeleton", "wayfinder"]


def head_blob_id(path):
    r = subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=REPO,
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()

    snap = {"head_rev": head, "specs": {}}
    for cap in SPECS:
        rel = f"openspec/specs/{cap}/spec.md"
        p = REPO / rel
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        lines = text.splitlines()

        # ordered anchor inventory: id -> the first Requirement heading that
        # follows it, so a lost anchor is nameable, not just countable
        anchors = []
        pending = None
        for i, ln in enumerate(lines):
            m = re.search(r'<a id="([^"]+)"></a>', ln)
            if m:
                pending = {"id": m.group(1), "line": i + 1, "heading": None}
                anchors.append(pending)
            h = re.match(r"^###\s+Requirement:\s*(.+?)\s*$", ln)
            if h and pending is not None and pending["heading"] is None:
                pending["heading"] = h.group(1)

        ids = [a["id"] for a in anchors]
        snap["specs"][cap] = {
            "path": rel,
            "sha256_worktree": hashlib.sha256(raw).hexdigest().upper(),
            "head_blob_id": head_blob_id(rel),
            "line_count": len(lines),
            "anchor_count": len(anchors),
            "unique_anchor_count": len(set(ids)),
            "duplicate_ids": sorted({i for i in ids if ids.count(i) > 1}),
            "anchor_inventory": anchors,
        }

    out = EV / "truth_source_snapshot.json"
    out.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    for cap, s in snap["specs"].items():
        print(f"{cap:<18} anchors={s['anchor_count']:>3} "
              f"unique={s['unique_anchor_count']:>3} "
              f"dups={s['duplicate_ids']} lines={s['line_count']}")
        print(f"{'':<18} sha256={s['sha256_worktree'][:16]}… "
              f"head_blob={str(s['head_blob_id'])[:12]}")
    print(f"snapshot: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
