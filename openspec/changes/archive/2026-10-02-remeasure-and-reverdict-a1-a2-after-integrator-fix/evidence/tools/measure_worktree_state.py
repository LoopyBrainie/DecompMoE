"""Change 3 tasks 5.3 + 5.4: measure worktree/HEAD tracking state from live git.

5.3: (a) archive directories present in the worktree but never committed;
     (b) change directories whose proposal.md/tasks.md are deleted in the
     worktree while HEAD still tracks them.
5.4: this change's own evidence/** tracking status (AC-23 / AC-100 subject) --
     the change must not judge others while sitting in the same state.

Anchor: `git status --porcelain` / `git ls-tree` at the time of the run. The
head_rev is recorded so a later reader can tell this is a snapshot.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

def find_repo_root(start: Path) -> Path:
    """Walk up to the directory that owns openspec/changes.

    Counting parents from this file is fragile (depth differs by layout);
    anchor on a marker that actually identifies the repo root.
    """
    for cand in [start, *start.parents]:
        if (cand / "openspec" / "changes").is_dir():
            return cand
    raise SystemExit("repo root not found: no openspec/changes above this file")


REPO = find_repo_root(Path(__file__).resolve().parent)
CHANGES = Path("openspec/changes")
ARCHIVE = CHANGES / "archive"
SELF = "2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix"


def run(args):
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"command failed: {args}\n{r.stderr}")
    return r.stdout


def tracked_at_head(rel):
    """Files git tracks at HEAD under a repo-relative directory."""
    out = run(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", rel])
    return [ln for ln in out.splitlines() if ln.strip()]


def porcelain_paths(prefix):
    out = run(["git", "status", "--porcelain=v1", "--untracked-files=all",
               "--", prefix])
    return [ln for ln in out.splitlines() if ln.strip()]


def split_porcelain(line: str):
    """porcelain v1 is exactly `XY <path>`: two status chars, one space.

    Do NOT partition on the first space -- ` D path` starts with a space, so
    partition() yields an empty code and a path prefixed with `D `.
    """
    if len(line) < 4:
        raise ValueError(f"malformed porcelain line: {line!r}")
    return line[:2], line[3:]


def main():
    head = run(["git", "rev-parse", "HEAD"]).strip()

    # --- 5.3(a) archive dirs present in worktree but with zero HEAD blobs ---
    untracked_archives = []
    if ARCHIVE.is_dir():
        for d in sorted(p for p in ARCHIVE.iterdir() if p.is_dir()):
            rel = f"{ARCHIVE.as_posix()}/{d.name}"
            if not tracked_at_head(rel):
                untracked_archives.append({
                    "dir": rel,
                    "worktree_file_count": sum(
                        1 for p in d.rglob("*") if p.is_file()),
                })

    # --- 5.3(b) HEAD-tracked files deleted in the worktree ---
    all_changes = run(["git", "ls-tree", "-r", "--name-only", "HEAD", "--",
                       CHANGES.as_posix()])
    raw_status = porcelain_paths(CHANGES.as_posix())
    deleted_by_dir = {}
    n_parsed = 0
    for line in raw_status:
        code, path = split_porcelain(line)
        if "D" not in code:
            continue
        n_parsed += 1
        d = str(Path(path).parent).replace("\\", "/")
        deleted_by_dir.setdefault(d, []).append({
            "path": path,
            "code": code,
            "tracked_at_head": path in all_changes.splitlines(),
        })

    # Cross-check the fixed-width parser against an independent regex count.
    # A classifier that silently returns 0 is indistinguishable from a clean
    # worktree, so the two methods must agree before the report is written.
    n_regex = sum(1 for ln in raw_status if re.match(r"^.[D]", ln))
    if n_parsed != n_regex:
        raise SystemExit(
            f"porcelain parser disagrees with regex: parsed={n_parsed} "
            f"regex={n_regex}\n" + "\n".join(raw_status))

    # --- 5.4 this change's own evidence tracking ---
    ev_rel = f"{CHANGES.as_posix()}/{SELF}/evidence"
    ev_head = set(tracked_at_head(ev_rel))
    ev_work = {
        p.relative_to(REPO).as_posix()
        for p in (REPO / ev_rel).rglob("*") if p.is_file()
    }
    ev_status = porcelain_paths(ev_rel)
    evidence = {
        "head_tracked_count": len(ev_head),
        "worktree_file_count": len(ev_work),
        "untracked_files": sorted(ev_work - ev_head),
        "status_lines": ev_status,
        "all_tracked": not (ev_work - ev_head),
    }

    report = {
        "head_rev": head,
        "untracked_archive_dirs": untracked_archives,
        "deleted_but_head_tracked": deleted_by_dir,
        "own_evidence": evidence,
    }
    out_path = REPO / ev_rel / "worktree_state.json"
    out_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"HEAD {head}")
    print(f"untracked archive dirs: {len(untracked_archives)}")
    for e in untracked_archives:
        print(f"   {e['dir']}  ({e['worktree_file_count']} files in worktree)")
    print(f"deleted-but-HEAD-tracked dirs: {len(deleted_by_dir)}")
    for d, items in sorted(deleted_by_dir.items()):
        print(f"   {d}: {len(items)} -> {[i['path'].rsplit('/', 1)[-1] for i in items]}")
    print(f"own evidence: head_tracked={evidence['head_tracked_count']} "
          f"worktree={evidence['worktree_file_count']} "
          f"all_tracked={evidence['all_tracked']}")
    for ln in ev_status:
        print(f"   {ln}")
    print(f"written: {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
