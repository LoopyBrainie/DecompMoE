"""Print the exact block-level diff and settle the 59-vs-58 line question.

A one-line length difference between the base block and the delta block is
either (a) the writer's `.rstrip()` dropping a trailing blank line, which is
harmless, or (b) real content loss, which would mean archiving beta DELETES a
line of req-gov-1. Those look identical in a count, so settle it by diffing.
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"D:\myProject\DecompMoE")
BETA = ROOT / "openspec/changes/2026-10-02-corr-pytest-approx-abs-semantics"
GOV = "openspec/specs/governance/spec.md"


def head_blob(path):
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"cannot read {path}")
    return r.stdout


def block_of(lines, anchor_id):
    a = next(i for i, l in enumerate(lines)
             if re.match(rf'^\s*<a id="{anchor_id}"></a>\s*$', l))
    n = next((i for i in range(a + 1, len(lines))
              if re.match(r'^\s*<a id="req-', lines[i])), len(lines))
    return lines[a:n], a, n


base_lines = head_blob(GOV).splitlines()
base, a, n = block_of(base_lines, "req-gov-1")

delta_lines = (BETA / "specs/governance/spec.md").read_text(
    encoding="utf-8").splitlines()
i = delta_lines.index("## MODIFIED Requirements")
# skip the header and its blank line
beta = delta_lines[i + 2:]

print(f"base block: {len(base)} lines (file L{a+1}..L{n})")
print(f"beta block: {len(beta)} lines")
print(f"base last 3 (repr): {[l[-30:] for l in base[-3:]]}")
print(f"beta last 3 (repr): {[l[-30:] for l in beta[-3:]]}")

# Is the length difference purely trailing whitespace?
def rstrip_cmp(x, y):
    n = min(len(x), len(y))
    mism = [k for k in range(n) if x[k] != y[k]]
    return mism, x[len(y):] if len(x) > len(y) else y[len(x):]


mism, tail_diff = rstrip_cmp(base, beta)
print()
if mism:
    print(f"CONTENT MISMATCH at block indices: {mism}")
else:
    print("the two blocks are IDENTICAL over their common length")
if tail_diff:
    print(f"EXTRA TAIL present in the longer block: {tail_diff!r}")
else:
    print("no tail difference")

print()
print("=" * 70)
print("line-level diff (beta block vs base block)")
print("=" * 70)
for l in difflib.unified_diff(base, beta, lineterm="", n=0):
    if l.startswith(("+++", "---", "@@")):
        continue
    tag = l[0]
    body = l[1:]
    # show only the first 110 chars; these lines run to thousands of chars
    print(f"  {tag} {body[:110]}{'...' if len(body) > 110 else ''}")
