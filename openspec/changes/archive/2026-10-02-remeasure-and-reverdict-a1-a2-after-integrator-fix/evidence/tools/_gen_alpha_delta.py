"""生成 Change α 的 spec delta：整块抽取 -> 定点整行替换 -> 回验。

纪律（来自本仓反复踩过的坑）：
  * MODIFIED 需求必须包含整个 block（从 `### Requirement:` 到所有 Scenario），
    否则 archive 时丢细节；
  * 替换标记若是行内片段，必须**整行替换**，否则原行尾部悬空；
  * 一个数字被 N 处引用时全 N 处都要改；
  * 回验必须**逐行 diff**，grep 命中恰恰是结构损坏时的假阴性来源。

只读主 spec，只写 change 目录。
"""
import difflib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
ALPHA = ROOT / "openspec/changes/2026-10-02-repair-spell-numeric-literal-provenance"
SPECS = ROOT / "openspec/specs"

# ---- 正确的、可复算的陈述（由 _alpha_forensics.py 实测，dps=60）--------------
NEW_RESID_N16 = "1.4635872379108090131680874e-17"
NEW_RESID_N64 = "1.9420345120803994000206689e-18"
NEW_RESID_BISECT = "4.6226242368382708792711061e-15"

# 逐条整行替换：每条断言必须恰好命中 1 行，否则拒绝继续。
#
# 锚点片段刻意只用 ASCII：这些 spec 的正文含 ½ / ² / − 等字符，把它们写进
# Python 源字面量会在写入环节损坏（第一次尝试就因此 SyntaxError）。片段只要
# 在目标行内唯一即可，生成器会强制验证「恰好命中 1 行」。
REPLACEMENTS = {
    "openspec/specs/governance/spec.md": [
        # 义务 3
        (
            "`5.01e-52` at N_e=16, `2.92e-52` at N_e=64",
            f"the measured residual at the canonical literal is "
            f"`{NEW_RESID_N16}` at N_e=16 and `{NEW_RESID_N64}` at N_e=64",
        ),
        # impl-internal reference
        (
            "| = 5.01e-52`",
            f"| = {NEW_RESID_N16}`",
        ),
        # true closed-form reference
        (
            "yields `5.01e-52`",
            f"yields `{NEW_RESID_N16}`",
        ),
    ],
    "openspec/specs/decompmoe-skeleton/spec.md": [
        (
            "is `5.01e-52` (N_e=16) / `2.92e-52` (N_e=64)",
            f"is `{NEW_RESID_N16}` (N_e=16) / `{NEW_RESID_N64}` (N_e=64)",
        ),
    ],
}

# 每处替换都要补上「这个量是什么、由什么决定」的可复算说明，否则只是把一个
# 魔法数换成另一个魔法数 —— 那正是本 change 要消灭的形态。
PROVENANCE_NOTE = (
    " This quantity is governed by the bisection stopping criterion "
    "(|G - 1/N_e| < 1e-13), not by float64 precision; provenance is "
    "mpmath betainc(a, b, 0, x, regularized=True) at dps=60, reproducible via "
    "change 2026-10-02-repair-spell-numeric-literal-provenance."
)


# ---- 整块抽取 ---------------------------------------------------------------
def block_of(path, req_id):
    """从 `### Requirement:` 标题到下一个 Requirement 之前的整块。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines)
                 if l.startswith("### Requirement:") and req_id in l)
    nxt = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("### Requirement:")
                or lines[i].startswith("## ") and not lines[i].startswith("###")), len(lines))
    # 往前吃掉紧邻的 anchor
    a = start
    while a > 0 and lines[a - 1].strip() == "":
        a -= 1
    if a > 0 and re.match(r'^\s*<a id="req-[^"]+"></a>\s*$', lines[a - 1]):
        a -= 1
    return lines[a:nxt], lines, a, nxt


results = {}
for rel, reps in REPLACEMENTS.items():
    src = SPECS.parent / rel if False else ROOT / rel
    lines = src.read_text(encoding="utf-8").splitlines()
    out = list(lines)
    for old, new in reps:
        # 整行替换：找出唯一含该子串的行，替换整行（子串->新句 + 该行其余部分）
        hits = [i for i, l in enumerate(out) if old in l]
        if len(hits) != 1:
            print(f"ABORT {rel}: 片段 {old[:60]!r} 命中 {len(hits)} 行，必须恰好 1")
            sys.exit(1)
        i = hits[0]
        out[i] = out[i].replace(old, new + PROVENANCE_NOTE)
        print(f"  {rel} L{i+1}: 已整行替换 ({len(old)} -> {len(new)} 字符 + provenance 句)")
    results[rel] = (lines, out)

# ---- 回验：逐行 diff + 失效 token 扫描 --------------------------------------
print()
print("=" * 76)
print("回验：失效 token 是否清零，以及残留的「假数字」上下文")
print("=" * 76)
for rel, (before, after) in results.items():
    d = list(difflib.unified_diff(before, after, lineterm="", n=0))
    changed = [l for l in d if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    print(f"\n  {rel}: {len(changed)} 行变更")
    for l in changed:
        print(f"    {l[:150]}")
    for tok in ("5.01e-52", "2.92e-52"):
        n_before = sum(l.count(tok) for l in before)
        n_after = sum(l.count(tok) for l in after)
        print(f"    token {tok}: {n_before} -> {n_after}"
              f"{'   <== 未清零' if n_after else '   OK'}")
        if n_after:
            for l in after:
                if tok in l:
                    for m in re.finditer(re.escape(tok), l):
                        print(f"        残留上下文: ...{l[max(0,m.start()-90):m.end()+40]}...")
                    break

(ALPHA / "evidence").mkdir(parents=True, exist_ok=True)
(ALPHA / "evidence" / "delta_apply_plan.json").write_text(
    '{\n  "note": "整行替换计划：每条片段必须恰好命中 1 行，否则生成器 abort",\n'
    + "".join(f'  "{rel}": [\n' + "".join(
        f'    {{"old": {old!r}, "new": {new!r}}},\n' for old, new in reps)
     + "  ],\n" for rel, reps in REPLACEMENTS.items())
    + '  "anchor_contract_unchanged": "两个 capability 的 anchor 不动，只改 body"\n}\n',
    encoding="utf-8")
print(f"\nwrote {ALPHA / 'evidence' / 'delta_apply_plan.json'}")
