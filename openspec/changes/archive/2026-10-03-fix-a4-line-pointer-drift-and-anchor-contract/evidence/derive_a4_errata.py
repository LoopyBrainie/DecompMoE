"""Re-derive the A-4 Errata's coordinate claims from git, not from the list.

Two questions, both answered against the PINNED blobs the list cites:

  1. Is the inline coordinate in an entry's prose 0-based or 1-based? Decided by
     taking a semantically unambiguous construct and seeing which reading makes
     the entry's sentence true. AC-34's "L413 是空行 / MCI 行在 L460" is the
     test case: if the entry is right that L413 is blank, and the MCI row is one
     line below whatever the entry calls it, that pins the base.
  2. Under a FILE-level reading, is `基线: unchanged-since-pin` correct? Decided
     by `git log <pin>..HEAD -- <file>`: if the file moved at all, then no line
     coordinate in it is unchanged.
"""

import subprocess
import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

ROOT = REPO
PIN = "6593a06"
AUDIT_HEAD = "188b9fb"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True,
        encoding="utf-8", check=True,
    ).stdout


def blob(rev: str, path: str) -> list[str]:
    return git("show", f"{rev}:{path}").splitlines()


WF = "openspec/specs/wayfinder/spec.md"
SK = "openspec/specs/decompmoe-skeleton/spec.md"

print(f"pin = {PIN}   audit HEAD = {AUDIT_HEAD}\n")

print("=== Q1: what is at the coordinates AC-34 names (wayfinder) ===")
for rev, label in ((PIN, "pin"), (AUDIT_HEAD, "audit-HEAD")):
    ls = blob(rev, WF)
    print(f"\n  -- {label} ({rev}), {len(ls)} lines --")
    for n in (413, 414, 460, 461, 463, 464, 497, 498, 501, 502):
        if 1 <= n <= len(ls):
            print(f"    L{n}: {ls[n-1].strip()[:78]!r}")

print("\n=== Q2: file-level truth of `基线: unchanged-since-pin` ===")
files = sorted({
    "openspec/specs/wayfinder/spec.md",
    "openspec/specs/decompmoe-skeleton/spec.md",
    "src/decompmoe/config.py", "src/decompmoe/schedule.py",
    "src/decompmoe/metrics.py", "src/decompmoe/sphere.py",
    "tests/test_safeguards.py", "tests/test_extraction.py",
})
for f in files:
    out = git("log", "--oneline", f"{PIN}..HEAD", "--", f).strip()
    n = len(out.splitlines()) if out else 0
    print(f"  {n:3d} commit(s) after pin  {f}")

print("\n=== Q3: the two same-coordinate pairs ===")
print("  AC-34 loc = wayfinder:847 ; AC-88 loc = wayfinder:847  (identical)")
print("  AC-59 loc = skeleton:242  ; AC-70 loc = skeleton:240  (same file, 2 apart)")
for rev, label in ((PIN, "pin"),):
    ls = blob(rev, SK)
    for n in (240, 241, 242, 243):
        if 1 <= n <= len(ls):
            print(f"    skeleton {label} L{n}: {ls[n-1].strip()[:90]!r}")
sys.exit(0)
