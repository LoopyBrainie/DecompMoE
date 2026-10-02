"""只读取证：wayfinder 为什么从 36 变成 37 个 Requirement，第 37 个是谁加的。

不写任何仓库文件。
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
SPEC_REL = "openspec/specs/wayfinder/spec.md"


def ids_at(rev):
    """(anchor ids, requirement ids) at a commit, read from the blob."""
    r = subprocess.run(["git", "show", f"{rev}:{SPEC_REL}"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        return None
    anchors = re.findall(r'<a id="req-(\d+)"></a>', r.stdout)
    heads = re.findall(r"^### Requirement:\s*(.+)$", r.stdout, re.M)
    return anchors, heads, r.stdout


print("=" * 74)
print("1. anchor / Requirement 计数沿 git 历史")
print("=" * 74)
revs = ["6593a06", "8ba7d6f", "1afac58", "a97e3a7", "HEAD"]
prev = None
for rev in revs:
    got = ids_at(rev)
    if got is None:
        print(f"  {rev:<10} (blob 不可取)")
        continue
    anchors, heads, text = got
    dup = sorted({i for i in anchors if anchors.count(i) > 1})
    marker = ""
    if prev is not None and len(anchors) != prev:
        marker = f"   <== {len(anchors) - prev:+d}"
    print(f"  {rev:<10} anchors={len(anchors):>3}  requirements={len(heads):>3}  "
          f"dupes={dup or '-'}{marker}")
    prev = len(anchors)

print()
print("=" * 74)
print("2. 第 37 个 anchor 是什么时候出现的")
print("=" * 74)
head_anchors, head_heads, _ = ids_at("HEAD")
nums = sorted(int(a) for a in head_anchors)
print(f"  HEAD anchor ids = {nums}")
gaps = [n for n in range(1, max(nums) + 1) if n not in nums]
print(f"  缺号 = {gaps or '无'}   重复 = "
      f"{sorted({i for i in nums if nums.count(i) > 1}) or '无'}")

for rev in revs:
    got = ids_at(rev)
    if got is None:
        continue
    a = sorted(int(x) for x in got[0])
    if 37 in a and 36 in a:
        pass
    print(f"  {rev:<10} 含 req-37: {37 in a}   含 req-36: {36 in a}")

print()
print("=" * 74)
print("3. 逐 commit 定位 req-37 的引入者")
print("=" * 74)
r = subprocess.run(["git", "log", "--format=%h %s", "6593a06..HEAD", "--", SPEC_REL],
                   cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                   errors="replace")
for line in r.stdout.strip().splitlines():
    h = line.split()[0]
    got = ids_at(h)
    if not got:
        continue
    a = sorted(int(x) for x in got[0])
    print(f"  {line[:70]:<72} n_anchors={len(a):>3} has37={37 in a}")

print()
print("=" * 74)
print("4. req-37 在当前 spec 里的 Requirement 标题")
print("=" * 74)
text = subprocess.run(["git", "show", f"HEAD:{SPEC_REL}"], cwd=ROOT,
                      capture_output=True, text=True, encoding="utf-8",
                      errors="replace").stdout.splitlines()
for i, ln in enumerate(text):
    if '<a id="req-37"></a>' in ln:
        for j in range(i, min(i + 6, len(text))):
            print(f"  L{j+1}: {text[j][:150]}")
        break

print()
print("=" * 74)
print("5. 这 37 个 anchor 是否都挂在 Requirement 标题之前（结构合法性）")
print("=" * 74)
bad_struct = []
i = 0
while i < len(text):
    if '<a id="req-' in text[i]:
        j = i + 1
        while j < len(text) and text[j].strip() == "":
            j += 1
        if j >= len(text) or not text[j].startswith("### Requirement:"):
            bad_struct.append((i + 1, text[i][:60], text[j][:60] if j < len(text) else "<EOF>"))
    i += 1
print(f"  结构违例 = {bad_struct or '无'}")
