"""Hypothesis: M1 (raw sha256) disagrees because the worktree carries CRLF where
the HEAD blob carries LF -- a byte difference with NO content difference.

`git hash-object` and `git diff` both apply the working-tree filters, so they
normalise CRLF->LF and report "same". Raw sha256 does not.

Discriminator: count b"\\r\\n" in the worktree and in the HEAD blob, and compare
after normalising the worktree to LF. If normalised hashes match, the files are
content-identical and only the line endings differ.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()

SUSPECTS = [
    "openspec/specs/wayfinder/spec.md",
    "openspec/specs/decompmoe-skeleton/spec.md",
    "openspec/specs/governance/spec.md",
    "src/decompmoe/loss.py",
    "src/decompmoe/safeguards.py",
    "src/decompmoe/distance.py",
    "src/decompmoe/gating.py",
]


def blob(rev, path):
    return subprocess.run(["git", "cat-file", "blob", f"{rev}:{path}"],
                          cwd=ROOT, capture_output=True).stdout


print(f"{'path':<42} {'blob CRLF':>9} {'wt CRLF':>8} {'blob LF':>8} {'wt LF':>7}  {'raw==':<6} {'normLF==':<9} verdict")
print("-" * 108)
# M1 (review finding): verify_toolchain's must-absent sentinel used to be the
# sentence "REAL CONTENT DIFF for every path", which this tool emits in no
# branch -- it prints a bare verdict token per row. A clause that can never
# fire is not a check. The failure modes this tool ACTUALLY has are an empty
# blob (git cat-file failed, which would masquerade as a content diff) and a
# missing archive copy, so those are what SELF-CHECK now reports.
degraded = []
counts = {"IDENTICAL": 0, "CRLF-ONLY": 0, "REAL CONTENT DIFF": 0}
for p in SUSPECTS:
    b = blob(HEAD, p)
    wpath = ROOT / p
    if not b:
        degraded.append(f"empty blob for {p} (git cat-file {HEAD}:{p} returned nothing)")
    if not wpath.is_file():
        degraded.append(f"worktree file missing: {p}")
        continue
    w = wpath.read_bytes()
    b_crlf, b_lf = b.count(b"\r\n"), b.count(b"\n")
    w_crlf, w_lf = w.count(b"\r\n"), w.count(b"\n")
    raw_same = b == w
    norm_same = b.replace(b"\r\n", b"\n") == w.replace(b"\r\n", b"\n")
    if raw_same:
        verdict = "IDENTICAL"
        counts["IDENTICAL"] += 1
    elif norm_same:
        verdict = "CRLF-ONLY (content same)"
        counts["CRLF-ONLY"] += 1
    else:
        verdict = "REAL CONTENT DIFF"
        counts["REAL CONTENT DIFF"] += 1
    print(f"{p:<42} {b_crlf:>9} {w_crlf:>8} {b_lf:>8} {w_lf:>7}  "
          f"{str(raw_same):<6} {str(norm_same):<9} {verdict}")

print()
print(f"SELF-CHECK: {'FAIL' if degraded else 'OK'}  "
      f"(rows read {len(SUSPECTS) - len([d for d in degraded if 'worktree' in d])}/{len(SUSPECTS)}  "
      f"IDENTICAL={counts['IDENTICAL']} CRLF-ONLY={counts['CRLF-ONLY']} "
      f"REAL-CONTENT-DIFF={counts['REAL CONTENT DIFF']})")
for d in degraded:
    print(f"  degraded: {d}")

print()
print("=> Which spec content is in HEAD? Compare HEAD spec against the Change-2 archive copy.")
arch = ROOT / "openspec/changes/archive/2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard/specs"
for cap in ("wayfinder", "decompmoe-skeleton", "governance"):
    a = arch / cap / "spec.md"
    h = (ROOT / f"openspec/specs/{cap}/spec.md").read_bytes().replace(b"\r\n", b"\n")
    if not a.is_file():
        print(f"  {cap:<20} archive copy not found at {a}")
        degraded.append(f"archive copy not found for {cap}")
        continue
    ab = a.read_bytes().replace(b"\r\n", b"\n")
    print(f"  {cap:<20} HEAD-vs-worktree-norm == archive-copy : {h == ab}   "
          f"(archive sha256 {hashlib.sha256(ab).hexdigest()[:12]})")

sys.exit(1 if degraded else 0)
