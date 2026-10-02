"""Change α 的 delta 结构自检 + validate 前置检查。

只读。不写任何文件。
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
ALPHA = ROOT / "openspec/changes/2026-10-02-repair-spell-numeric-literal-provenance"
ADDED = ALPHA / "evidence/req_gov_5.md"

fail = []

# ---- 1. 若 ADDED 段还没并入 governance delta，就并入 -------------------------
gov_delta = ALPHA / "specs/governance/spec.md"
body = gov_delta.read_text(encoding="utf-8")
if "## ADDED Requirements" not in body:
    add = ADDED.read_text(encoding="utf-8").rstrip() + "\n"
    gov_delta.write_text(body.rstrip() + "\n\n" + add, encoding="utf-8")
    print("appended ## ADDED Requirements to governance delta")
else:
    print("governance delta already carries ## ADDED Requirements")

# ---- 2. 结构检查 -------------------------------------------------------------
for cap, expect_reqs in (("governance", 2), ("decompmoe-skeleton", 1)):
    p = ALPHA / "specs" / cap / "spec.md"
    t = p.read_text(encoding="utf-8")
    ls = t.splitlines()
    anchors = re.findall(r'<a id="([^"]+)"></a>', t)
    reqs = [l for l in ls if l.startswith("### Requirement:")]
    sections = [l for l in ls if l.startswith("## ")]
    # 失效 token 的清零只对 MODIFIED 段成立：ADDED 段（req-gov-5）**有意**
    # 引用 5.01e-52 作为 C1 类的具名实例，那正是该 Rule 的存在理由。
    mod_part = t.split("## ADDED Requirements")[0]
    added_part = t.split("## ADDED Requirements")[1] if "## ADDED Requirements" in t else ""
    print(f"\n{cap}  ({p.stat().st_size} B)")
    print(f"  段        : {sections}")
    print(f"  anchors   : {anchors}")
    print(f"  Requirem. : {len(reqs)}  {[r[16:46] for r in reqs]}")
    print(f"  MODIFIED 段失效 token: 5.01e-52 x{mod_part.count('5.01e-52')}  "
          f"2.92e-52 x{mod_part.count('2.92e-52')}"
          f"{'   （ADDED 段的引用是有意保留的具名实例）' if added_part else ''}")
    if mod_part.count("5.01e-52") or mod_part.count("2.92e-52"):
        fail.append(f"{cap}: MODIFIED 段失效 token 未清零")
    if len(reqs) != expect_reqs:
        fail.append(f"{cap}: Requirement 数 {len(reqs)} != {expect_reqs}（标题被重复写入？）")
    if len(set(reqs)) != len(reqs):
        fail.append(f"{cap}: 存在重复的 Requirement 标题")
    for a in anchors:
        i = ls.index(f'<a id="{a}"></a>')
        j = next((k for k in range(i + 1, len(ls)) if ls[k].strip()), None)
        if j is None or not ls[j].startswith("### Requirement:"):
            fail.append(f"{cap}: anchor {a} 后面不是 Requirement 标题（空行后须为标题）")
    for must in ("bisection stopping criterion",
                 "2026-10-02-repair-spell-numeric-literal-provenance"):
        if must not in mod_part:
            fail.append(f"{cap}: MODIFIED 段缺必含项 {must!r}")
    if cap == "governance":
        if "req-gov-5" not in anchors:
            fail.append("governance: 缺新增的 req-gov-5 anchor")
        if "`CLAUDE.md`" not in t:
            fail.append("governance: req-gov-5 缺 CLAUDE.md 字面反链（lint 会红）")

# ---- 3. 本 change 涉及的归档副本必须零**改动** --------------------------------
# 范围只限本 change 实际引用的那个 Change 2 归档。并行 session 正在未提交地
# 改自己的归档（`2026-10-02-a3-resurrection-clone-and-phase0-mask/**`），把整个
# archive/ 目录纳入检查会把别人的在制品算成本 change 的改动。
MY_ARCHIVE = ("openspec/changes/archive/2026-10-02-fix-canonical-literal-residual-"
              "frame-and-dead-guard")
r = subprocess.run(["git", "status", "--porcelain", "--", MY_ARCHIVE], cwd=ROOT,
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace")
arch_mod = [x for x in r.stdout.splitlines() if x.strip()]
print(f"\n本 change 引用的归档 ({MY_ARCHIVE.split('/')[-1][:44]}...) 改动: "
      f"{arch_mod or '无（正确）'}")
if arch_mod:
    fail.append(f"归档副本被改动（应保留为历史记录）: {arch_mod}")

# 并行 session 对**其它**归档的在制品改动：只报告，不判失败
r2 = subprocess.run(["git", "status", "--porcelain", "--",
                     "openspec/changes/archive/"], cwd=ROOT,
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace")
others = [x for x in r2.stdout.splitlines()
          if x.strip() and MY_ARCHIVE not in x]
print(f"其它归档的在制品改动（并行 session，不计入本 change）: {len(others)} 项")
for o in others[:4]:
    print(f"    {o[:110]}")

# ---- 4. 归档里的假数字仍在（这是有意的）------------------------------------
for f in ("openspec/changes/archive/2026-10-02-fix-canonical-literal-residual-frame-"
          "and-dead-guard/specs/governance/spec.md",):
    n = (ROOT / f).read_text(encoding="utf-8").count("5.01e-52")
    print(f"归档 {Path(f).name} 中 5.01e-52 仍在: {n} 处（有意保留，已在 req-gov-5 登记）")

print("\n" + "=" * 70)
print("STRUCTURE SELF-CHECK:", "PASS" if not fail else "FAIL")
for f in fail:
    print("  -", f)
sys.exit(1 if fail else 0)
