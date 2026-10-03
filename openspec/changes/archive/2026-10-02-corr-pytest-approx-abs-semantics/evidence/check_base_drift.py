"""并行 session 的在制品体检：governance/spec.md 当前的 Requirement 块结构。

只读。不写任何文件。
"""
import re
import subprocess
import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
BASE_REV = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
GOV = ROOT / "openspec/specs/governance/spec.md"


def report(label, lines):
    print(f"\n{'='*70}\n{label}\n{'='*70}")
    anchors = [(i, re.match(r'^\s*<a id="([^"]+)"></a>\s*$', l).group(1))
               for i, l in enumerate(lines) if re.match(r'^\s*<a id="', l)]
    reqs = [(i, l) for i, l in enumerate(lines) if l.startswith("### Requirement:")]
    print(f"  anchors   ({len(anchors)}): {[a for _, a in anchors]}")
    for i, l in reqs:
        print(f"  L{i+1:<4} {l[:78]}")
    titles = [l for _, l in reqs]
    dup = {t for t in titles if titles.count(t) > 1}
    ids = [a for _, a in anchors]
    dup_a = {a for a in ids if ids.count(a) > 1}
    print(f"  duplicate titles : {sorted(dup) or 'none'}")
    print(f"  duplicate anchors: {sorted(dup_a) or 'none'}")
    print(f"  coverage (anchors == requirements): {len(anchors)} vs {len(reqs)} "
          f"-> {'OK' if len(anchors) == len(reqs) and not dup_a and not dup else 'MISMATCH'}")
    return dup, dup_a


# --- HEAD（已提交、稳定）---
head_txt = subprocess.run(["git", "show", "HEAD:openspec/specs/governance/spec.md"],
                          cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout
report("HEAD (fd30f5b) — stable base for delta generation", head_txt.splitlines())

# --- 工作树（并行 session 在制品）---
report("WORKING TREE — parallel session's in-flight edit", GOV.read_text(encoding="utf-8").splitlines())

# --- 假数值在两个版本里的分布 ---
print(f"\n{'='*70}\nfake literals: HEAD vs WORKTREE\n{'='*70}")
wt = GOV.read_text(encoding="utf-8")
for tok in ("5.01e-52", "2.92e-52"):
    print(f"  {tok}: HEAD x{head_txt.count(tok)}   WORKTREE x{wt.count(tok)}")

# --- 本会话已生成的 α delta 是否还对着当前基线 ---
print(f"\n{'='*70}\nChange alpha delta still matching the worktree base?\n{'='*70}")
alpha = (ROOT / "openspec/changes/archive/2026-10-02-repair-spell-numeric-literal-provenance"
         "/specs/governance/spec.md").read_text(encoding="utf-8")
mod = alpha.split("## ADDED Requirements")[0]
for frag in ("bisection stopping criterion",
             "2026-10-02-repair-spell-numeric-literal-provenance"):
    print(f"  delta MODIFIED block contains {frag!r}: {frag in mod}")
# 抽取 delta 里的 MODIFIED req-gov-1 块，逐行与工作树同块比对
d_lines = mod.splitlines()
d_anchor = next(i for i, l in enumerate(d_lines)
                if re.match(r'^\s*<a id="req-gov-1"></a>\s*$', l))
d_nxt = next((i for i in range(d_anchor + 1, len(d_lines))
              if re.match(r'^\s*<a id="req-', d_lines[i])), len(d_lines))
d_block = d_lines[d_anchor:d_nxt]

w_lines = wt.splitlines()
w_anchor = next(i for i, l in enumerate(w_lines)
                if re.match(r'^\s*<a id="req-gov-1"></a>\s*$', l))
w_nxt = next((i for i in range(w_anchor + 1, len(w_lines))
              if re.match(r'^\s*<a id="req-', w_lines[i])), len(w_lines))
w_block = w_lines[w_anchor:w_nxt]
print(f"  delta block {len(d_block)} lines; worktree block {len(w_block)} lines; "
      f"line-for-line equal: {d_block == w_block}")
if d_block != w_block:
    import difflib
    for l in list(difflib.unified_diff(w_block, d_block, "worktree", "alpha-delta",
                                       lineterm="", n=0))[:12]:
        print(f"    {l[:150]}")
