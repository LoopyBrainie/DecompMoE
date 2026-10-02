"""Change 3 / task 0.1 -- anchor BOTH ends, re-verify with three INDEPENDENT methods.

Why three methods: the previous probe reported `differs_from_head: true` for the
three spec files while `git diff HEAD -- openspec/specs/` is empty. A single
method cannot tell "the probe is wrong" from "the file really differs". So each
path is checked by:
  M1  sha256 of raw HEAD blob bytes  vs  sha256 of raw worktree bytes
  M2  git blob sha1: `git rev-parse <rev>:<path>` vs `git hash-object <path>`
  M3  `git diff --quiet <rev> -- <path>`  (exit 0 == identical)

Binary-safe: everything goes through subprocess with bytes. No PowerShell text
round-trip (that is what mangles CJK / math glyphs into a false "differs").
"""
import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
PIN = "6593a06"

PATHS = [
    "openspec/specs/wayfinder/spec.md",
    "openspec/specs/decompmoe-skeleton/spec.md",
    "openspec/specs/governance/spec.md",
    "src/decompmoe/sphere.py",
    "src/decompmoe/gating.py",
    "src/decompmoe/loss.py",
    "src/decompmoe/schedule.py",
    "src/decompmoe/metrics.py",
    "src/decompmoe/config.py",
    "src/decompmoe/extraction.py",
    "src/decompmoe/safeguards.py",
    "src/decompmoe/distance.py",
    "src/decompmoe/beta.py",
    "tests/test_sphere.py",
    "tests/test_gating.py",
    "tests/test_loss.py",
    "tests/test_config.py",
    "tests/test_extraction.py",
    "tests/test_metrics.py",
    "tests/test_beta.py",
]


def git(*args, text=False):
    p = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=text, check=False
    )
    return p


def head_blob_bytes(rev, path):
    p = git("cat-file", "blob", f"{rev}:{path}")
    if p.returncode != 0:
        return None
    return p.stdout


def git_blob_sha(rev, path):
    p = git("rev-parse", f"{rev}:{path}", text=True)
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def worktree_bytes(path):
    f = ROOT / path
    return f.read_bytes() if f.is_file() else None


def worktree_blob_sha(path):
    p = git("hash-object", path, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def m3_identical(rev, path):
    p = git("diff", "--quiet", rev, "--", path)
    if p.returncode == 0:
        return True, 0
    if p.returncode == 1:
        return False, 1
    return None, p.returncode


HEAD = git("rev-parse", "HEAD", text=True).stdout.strip()
print(f"pin  = {PIN}")
print(f"head = {HEAD}")
print()

rows = []
print(f"{'path':<44} {'M1 sha256':<8} {'M2 blobsha':<8} {'M3 diff':<8} verdict")
print("-" * 92)
for path in PATHS:
    hb, wb = head_blob_bytes(HEAD, path), worktree_bytes(path)
    h1 = hashlib.sha256(hb).hexdigest() if hb is not None else None
    w1 = hashlib.sha256(wb).hexdigest() if wb is not None else None
    m1 = "MISSING" if (h1 is None or w1 is None) else ("same" if h1 == w1 else "DIFF")

    g1, g2 = git_blob_sha(HEAD, path), worktree_blob_sha(path)
    m2 = "MISSING" if (g1 is None or g2 is None) else ("same" if g1 == g2 else "DIFF")

    ok3, rc3 = m3_identical(HEAD, path)
    m3 = "ERR%d" % rc3 if ok3 is None else ("same" if ok3 else "DIFF")

    # Only trust "same" when all three agree.
    agree = (m1 == m2 == m3)
    verdict = ("IDENTICAL" if m1 == "same" else "DIFFERS") if agree else "DISAGREE"
    rows.append(
        dict(path=path, m1=m1, m2=m2, m3=m3, verdict=verdict,
             head_sha256=h1, wt_sha256=w1, head_blob=g1, wt_blob=g2)
    )
    print(f"{path:<44} {m1:<8} {m2:<8} {m3:<8} {verdict}")

print()
disagree = [r for r in rows if r["verdict"] == "DISAGREE"]
differs = [r for r in rows if r["verdict"] == "DIFFERS"]
print(f"total={len(rows)}  identical={len(rows) - len(differs) - len(disagree)}  "
      f"differs={len(differs)}  disagree={len(disagree)}")
if disagree:
    print("!! METHODS DISAGREE (probe unreliable, do not trust any of these rows):")
    for r in disagree:
        print("   ", r["path"], r["m1"], r["m2"], r["m3"])

# Control: a path we KNOW differs, and a path we KNOW matches, per `git status`.
print()
print("control: gating.py must be DIFFERS, sphere.py must be IDENTICAL")
g = next(r for r in rows if r["path"].endswith("gating.py"))
s = next(r for r in rows if r["path"].endswith("sphere.py"))
print(f"  gating.py -> {g['verdict']}  {'OK' if g['verdict'] == 'DIFFERS' else 'CONTROL FAILED'}")
print(f"  sphere.py -> {s['verdict']}  {'OK' if s['verdict'] == 'IDENTICAL' else 'CONTROL FAILED'}")
