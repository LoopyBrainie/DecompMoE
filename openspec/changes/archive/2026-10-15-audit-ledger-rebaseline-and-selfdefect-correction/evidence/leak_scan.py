"""D3 leak scan: re-run over both lists' BODIES after this round's edits and
report the (a) legitimate-quotation / (b) genuine-solution-leak counts.

Scope = each file up to and excluding its own `## 附：` appendix (the appendix
enumerates pattern names and would self-hit by construction).

Two passes:
  PASS 1  the 13 primary solution patterns + 11 bypass patterns  -> raw hits,
          each printed with file:line so every hit can be adjudicated by hand.
  PASS 2  quoted-artifact detector: does any 「…」 / `…` span appear VERBATIM
          in some existing artifact? Those are (a)-class by definition.
"""
import os
import re
import subprocess

REPO = r"D:\myProject\DecompMoE"
ARCH = os.path.join(REPO, ".audit", "gradual-review-2026-10-07")
HEAD = "dde0e1d"

PRIMARY = ["should be", "should change", "fix by", "replace with", "add rtol",
           "use NaN", "建议", "改为", "修改为", "修复", "应当", "推荐", "patch"]
BYPASS = ["应当改为", "建议改", "应改", "需改", "改成", "更正为", "统一为",
          "目标值", "优先", "先改", "推荐使用"]


def body_of(rel):
    with open(os.path.join(ARCH, rel), encoding="utf-8") as f:
        out = []
        for ln in f:
            if ln.startswith("## 附："):
                break
            out.append(ln)
    return out


def git(*a):
    r = subprocess.run(["git", "-C", REPO, *a], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8", "replace")


FILES = ["lists/direct-fixes.md", "lists/opsx-changes.md"]

print("=" * 78)
print("PASS 1  raw pattern hits in each list's BODY")
print("=" * 78)
for rel in FILES:
    lines = body_of(rel)
    print(f"\n--- {rel}  ({len(''.join(lines))} chars, {len(lines)} lines) ---")
    hits = []
    for i, ln in enumerate(lines, 1):
        for p in PRIMARY + BYPASS:
            start = 0
            while (j := ln.find(p, start)) != -1:
                hits.append((i, p, ln[max(0, j - 40):j + len(p) + 40].strip()))
                start = j + len(p)
    print(f"  total raw hits = {len(hits)}")
    for i, p, ctx in hits:
        print(f"    L{i:<4} [{p}]  …{ctx}…")

print()
print("=" * 78)
print("PASS 2  quoted spans that appear VERBATIM in an existing artifact  -> (a)")
print("=" * 78)
TRACKED = [p for p in git("ls-tree", "-r", "--name-only", HEAD).splitlines()
           if p.endswith((".md", ".py"))]
BLOBS = {p: git("show", f"{HEAD}:{p}") for p in TRACKED}
# the prior audit is not tracked; index it separately
for extra in ("openspec/changes/archive/2026-08-19-add-decompoe-skeleton-with-tdd-tests/design.md",):
    pass

QUOTED = re.compile(r"「([^」]{4,300})」|`([^`\n]{6,300})`")

for rel in FILES:
    lines = body_of(rel)
    verbatim, notfound = [], []
    for i, ln in enumerate(lines, 1):
        for m in QUOTED.finditer(ln):
            q = (m.group(1) or m.group(2) or "").strip()
            # (a)-class means a PROSE span: >=4 words, contains spaces.
            # Short backticked identifiers (`opsx-change`, `archive-only`) are
            # pointers, not quotations of an artifact's own wording.
            if len(q) < 16 or len(q.split()) < 4:
                continue
            probe = q.replace(" / ", " ")          # archive uses ' / ' for wrapped lines
            hit = None
            for p, txt in BLOBS.items():
                if q in txt or probe in txt:
                    hit = p
                    break
            if hit:
                verbatim.append((i, q[:88], hit))
            else:
                notfound.append((i, q[:88]))
    print(f"\n--- {rel} ---")
    print(f"  (a) verbatim quotes of an existing artifact : {len(verbatim)}")
    for i, q, p in verbatim:
        print(f"      L{i:<4} {q!r}\n            <- {p}")
    print(f"  quoted spans NOT found verbatim in any tracked artifact : {len(notfound)}")
    for i, q in notfound[:40]:
        print(f"      L{i:<4} {q!r}")
    if len(notfound) > 40:
        print(f"      … and {len(notfound)-40} more")