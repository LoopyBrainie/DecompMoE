"""Two defects to root-cause, measured not guessed.

D1: `^###\\s+Requirement:` returned 0 hits on a file where grep finds them at
    lines 10/22/34. A zero count is the most dangerous output shape -- it looks
    like clean negative evidence. So: dump the raw bytes of the heading line and
    find what actually differs from my pattern.

D2: `req-17` and `req-20` each occur TWICE in the wayfinder spec at HEAD.
    Change 2's completion recomputed 0 duplicates. So either f6461d7 introduced
    them or the baseline was wrong. Locate every occurrence with its line number
    and its surrounding context, and diff the pin version to see if the dupes
    predate the pin.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
PIN = "6593a06"


def blob(rev, path):
    return subprocess.run(["git", "cat-file", "blob", f"{rev}:{path}"],
                          cwd=ROOT, capture_output=True).stdout


def norm(b):
    return b.replace(b"\r\n", b"\n").decode("utf-8", "replace")


P = "openspec/specs/wayfinder/spec.md"
live = norm(blob(HEAD, P))

print("D1  why did my `^###\\s+Requirement:` pattern return 0?")
for i, line in enumerate(live.splitlines()[:12], 1):
    if "Requirement" in line:
        b = line.encode("utf-8")
        print(f"  line {i}: repr of first 30 chars -> {line[:30]!r}")
        print(f"           raw bytes  -> {b[:30]!r}")
        print(f"           codepoints -> {[hex(ord(c)) for c in line[:8]]}")
        print(f"           startswith('### ') -> {line.startswith('### ')}")
        print(f"           bool(re.match(r'^###\\s+Requirement:', line)) -> "
              f"{bool(re.match(r'^###\\s+Requirement:', line))}")
        break
print(f"  live.count('### Requirement:') = {live.count('### Requirement:')}")
print(f"  live.count('### Requirement:') with re.M findall = "
      f"{len(re.findall(r'^### Requirement:', live, re.M))}")
print()

print("D2  every occurrence of the duplicated anchor ids")
for rid in ("req-17", "req-20"):
    print(f"  --- {rid} ---")
    lines = live.splitlines()
    hits = [n for n, l in enumerate(lines, 1) if f'<a id="{rid}">' in l]
    print(f"  lines: {hits}")
    for n in hits:
        print(f"    L{n}: {lines[n-1][:130]}")
        for k in range(n, min(n + 3, len(lines) + 1)):
            print(f"    L{k}:   {lines[k-1][:130]}")
print()

print("D3  did the duplicates predate the pin? (pin vs head anchor-id multiset)")
for rev, label in ((PIN, "pin "), (HEAD, "head")):
    txt = norm(blob(rev, P))
    ids = re.findall(r'<a\s+id="(req-[0-9A-Za-z\-]+)"></a>', txt)
    dupes = {k: ids.count(k) for k in set(ids) if ids.count(k) > 1}
    print(f"  {label} total={len(ids)}  unique={len(set(ids))}  duplicates={dupes}")
