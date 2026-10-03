"""写出 Change β 的 governance delta（req-gov-1 整块 MODIFIED）。

区间拼接纪律
------------
这些 spec 行含 · — − ≈ ≈ 等非 ASCII 字符。把它们写进 Python 源字面量会在写入
环节损坏（已栽两次）。所以每条编辑只声明两个**纯 ASCII 端点**与一段新文本：
起点 -> 终点之间的原文由文件自己提供，不经过我的手。

  edit = (start_ascii, end_ascii, new_text)
  splice: line[:i] + new_text + line[j:]

端点必须唯一（生成器强制验证），否则 abort。
"""
import difflib
import re
import subprocess
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
BETA = ROOT / "openspec/changes/2026-10-02-corr-pytest-approx-abs-semantics"
EV = BETA / "evidence"
EV.mkdir(parents=True, exist_ok=True)

src_prov = (ROOT / "openspec/changes/archive/2026-10-02-remeasure-and-reverdict-a1-a2-after-"
            "integrator-fix/evidence/tools/_pytest_approx_semantics.py")
if not src_prov.exists():
    raise SystemExit(f"provenance source missing: {src_prov}")
shutil.copy2(src_prov, EV / "pytest_approx_semantics.py")
print(f"provenance copied -> {(EV / 'pytest_approx_semantics.py').relative_to(ROOT)}")

ENV = ("[measured on pytest 9.1.1 / python 3.14.8; pyproject.toml does not pin "
       "pytest, so this is environment-scoped; recomputable via change "
       "2026-10-02-corr-pytest-approx-abs-semantics "
       "evidence/pytest_approx_semantics.py]")

EDITS = [
    # ---- 义务 1 的理由 -------------------------------------------------------
    (
        "The reason is the `pytest.approx` effective-tolerance formula",
        "independent of magnitude.",
        " The reason is version-independence, not a formula. `pytest.approx` "
        "performs a FLOATING-POINT comparison of an integer, and its tolerance "
        "semantics depend on the pytest version. " + ENV + " When `abs` is "
        "supplied and `rel` is left at its default of `None`, the tolerance is "
        "EXACTLY `abs` -- the `tolerance` property returns before reaching the "
        "`max` branch -- so `abs=0` does NOT degenerate to a magnitude-scaled "
        "relative tolerance. Bare `==` is required because it is the only form "
        "whose zero tolerance is decidable and independent of the pytest "
        "version, at every magnitude.",
    ),
    # ---- 义务 3 的 max(...) 句 ----------------------------------------------
    (
        "Note that `pytest.approx(expected, abs=1e-6)` leaves pytest's default",
        "the tolerance is NOT tightened.",
        " Note that `pytest.approx(expected, abs=1e-6)` applies a tolerance of "
        "EXACTLY `1e-6`: the `rel` default is `None`, not `1e-6`, and the "
        "tolerance property returns the absolute tolerance before reaching the "
        "`max` branch. " + ENV + " The measured truncation diffs `4.259e-7` / "
        "`6.216e-7` / `8.248e-7` all sit below it, and the tolerance is NOT "
        "tightened.",
    ),
    # ---- 义务 3 的 5e-7 截断论断（同一行，位于上一条之前）--------------------
    (
        "and because a 6dp literal carries an intrinsic truncation error bounded",
        "the minimum the 6dp display format permits.",
        " and because a 6dp TRUNCATED literal carries a truncation error strictly "
        "below `1e-6` (`5e-7` is the round-half-up half-unit, not the truncation "
        "bound: `trunc6(0.9999999) = 0.999999` has error `9e-7`, which exceeds "
        "`5e-7`). `1e-6` is therefore a defensible guard, but it is NOT the "
        "minimum the 6dp display format permits -- measured, `abs=4.3e-7` already "
        "passes for `1.173547`.",
    ),
    # ---- L22 同步 -------------------------------------------------------------
    (
        "both outside the applied `max(1e-6, 1e-6",
        "criterion); the `(N_e=64)` literal does not discriminate",
        "both outside the applied criterion, which is exactly `1e-6` (see "
        "obligation 3); the `(N_e=64)` literal does not discriminate",
    ),
    # ---- Scenario 的 abs=0 括注（三条同形，但只有一条带尾随括注）--------------
    # 这三行的开头完全相同、只在括注处分叉：其中一条原本带
    # "(would introduce implicit `rel=1e-6` ... intent)."，另两条整行以
    # "MUST NOT appear." 结束。
    # 第一次尝试写成「对所有匹配行替换同一子串」，结果**只吃掉了子串本身**，
    # 那一行的尾巴 " (would introduce ... intent)." 悬挂在新文本之后——正是本仓
    # 记忆里记着的「substring 替换导致原行尾部悬空，产出结构已坏但检查全过」。
    # 它是被下面回验里的 dead-phrase 计数抓到的，不是被肉眼发现的。
    # 修法：多行编辑也支持**可选尾端消费**；end 为 None 时只替换子串本身。
]

MULTI_EDITS = [
    (
        "a `pytest.approx(..., abs=0)` form MUST NOT appear",
        "intent).",   # 只在该行确实带这条尾巴时消费；找不到就只换子串
        " a `pytest.approx(..., abs=0)` form MUST NOT appear (measured on pytest "
        "9.1.1 an `abs=0` tolerance is exactly 0, so it introduces no relative "
        "tolerance at all; bare `==` is nevertheless required because it is the "
        "only version-independent form -- see obligation 1).",
    ),
]

# 锚定 commit object（fd30f5b），绝不读工作树：并行 session 正在未提交地
# 重写 governance/spec.md 并把 req-gov-1 整块复制了一份。
_src = subprocess.run(["git", "show", "HEAD:openspec/specs/governance/spec.md"], cwd=ROOT,
                      capture_output=True, text=True, encoding="utf-8", errors="replace")
assert _src.returncode == 0, "cannot read HEAD governance spec"
# Base guard: refuse to splice unless HEAD carries req-gov-5.
# The base must be the post-alpha governance spec. Splicing against the
# pre-alpha base yields a delta that validates and then reverts alpha's
# edits to this same Requirement when applied.
if '<a id="req-gov-5"></a>' not in _src.stdout:
    raise SystemExit(
        "HEAD governance spec has no req-gov-5: alpha's apply is not committed "
        "at HEAD, so regenerating now would splice against the pre-alpha base")

lines = _src.stdout.splitlines()
anchor = next(i for i, l in enumerate(lines)
              if re.match(r'^\s*<a id="req-gov-1"></a>\s*$', l))
nxt = next((i for i in range(anchor + 1, len(lines))
            if re.match(r'^\s*<a id="req-', lines[i])), len(lines))
block = list(lines[anchor:nxt])
print(f"\nreq-gov-1 block: {len(block)} lines (L{anchor+1}..L{nxt})")

out_block = list(block)
for start, end, new in EDITS:
    hits = [i for i, l in enumerate(out_block) if start in l]
    if len(hits) != 1:
        print(f"ABORT: start locator hits {len(hits)} lines (need exactly 1): "
              f"{start[:60]!r}")
        sys.exit(1)
    i = hits[0]
    l = out_block[i]
    a = l.index(start)
    b = l.index(end, a) + len(end)
    out_block[i] = l[:a] + new + l[b:]
    print(f"  L{i} splice OK: [{a}:{b}] {b-a} chars -> {len(new)} chars")

n_multi = 0
for start, tail, new in MULTI_EDITS:
    for i, l in enumerate(out_block):
        if start not in l:
            continue
        a = l.index(start)
        # 尾端消费：只有该行确实带这条尾巴时才吃掉它，否则只换子串本身。
        # 不做这个判断就会在不带括注的行上截断后续内容，或在带括注的行上留下
        # 悬空尾巴 —— 两种失效都表现为「文本看起来正常、检查全过」。
        b = a + len(start)
        if tail and tail in l[b:]:
            b += l[b:].index(tail) + len(tail)
            consumed = " (with tail)"
        else:
            consumed = " (substring only)"
        out_block[i] = l[:a] + new + l[b:]
        n_multi += 1
        print(f"  block-L{i} multi-splice{consumed}: {start[:46]!r}")
if not n_multi:
    print(f"ABORT: MULTI_EDITS 定位符未命中: {MULTI_EDITS[0][0][:60]!r}")
    sys.exit(1)
n_edits = len(EDITS) + n_multi

print("\n" + "=" * 70)
print("回验")
print("=" * 70)
body = "\n".join(out_block)
bad = 0
for dead in ("max(abs, rel", "max(1e-6, 1e-6", "1.17e-6", "default of `1e-12`",
             "no tolerance below `1e-6` can be satisfied",
             "magnitude-scaling tolerance contrary", "would introduce implicit",
             "rel=1e-6` magnitude"):
    n = body.count(dead)
    print(f"  dead {dead[:44]!r}: {n}  {'OK' if n == 0 else '<== STILL PRESENT'}")
    bad += n
# 悬空尾巴检测：新文本后面若紧跟旧括注的残片，就是 substring 替换的典型损坏。
# 这一项是被回验的 dead-phrase 计数逼出来的，不是预防性检查。
for frag in ("intent).", "contrary to the"):
    for i, l in enumerate(out_block):
        k = l.find("see obligation 1).")
        if k != -1 and frag in l[k:]:
            print(f"  DANGLING TAIL at block-L{i}: {frag!r} appears after the new text")
            bad += 1
for keep in ("MUST use **bare `==` integer equality**", "4.259e-7", "6.216e-7",
             "8.248e-7", "1.275e-6", "1.297e-6", "8.34e-7",
             "MUST use `pytest.approx(value, abs=1e-6)`"):
    n = body.count(keep)
    print(f"  keep {keep[:44]!r}: {n}  {'OK' if n else '<== LOST!'}")
    if not n:
        bad += 1
if bad:
    print(f"\nABORT: {bad} problem(s)")
    sys.exit(1)

d = [l for l in difflib.unified_diff(block, out_block, lineterm="", n=0)
     if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
changed_idx = {i for i, (b, a) in enumerate(zip(block, out_block)) if b != a}
print(f"\n  splices applied: {n_edits}   distinct lines changed: {len(changed_idx)}")
# 期望值按「不同的行」算，不是按 splice 次数：同一行可被多条编辑命中
# （L10 挨了两刀），diff 只产生一次 -/+ 对。
assert len(d) == 2 * len(changed_idx), \
    f"diff has {len(d)} +/- lines but {len(changed_idx)} lines changed"
assert len(changed_idx) == 6, f"expected 6 changed lines, got {len(changed_idx)}"

out = BETA / "specs/governance/spec.md"
out.parent.mkdir(parents=True, exist_ok=True)
# Preserve the block's trailing blank line. join() consumes the final
# empty element as a separator, yielding a string that ends in a line
# TERMINATOR rather than a blank LINE -- so the separator between this
# Requirement and the next block's anchor is lost, and applying the delta
# would weld <a id="req-gov-2"></a> onto the preceding paragraph.
body_out = "\n".join(out_block)
if out_block and out_block[-1] == "":
    body_out += "\n"
out.write_text("## MODIFIED Requirements\n\n" + body_out,
               encoding="utf-8")

# --- assert the property, not the spelling of the fix -------------------
# Re-read what was written and compare the block structurally. This holds
# for any writer implementation, so a later edit cannot silently
# reintroduce the loss while keeping every token grep green.
import re as _re
_w = out.read_text(encoding="utf-8").splitlines()
_i = _w.index("## MODIFIED Requirements")
_wb = _w[_i + 2:]
if len(_wb) != len(block):
    raise SystemExit(
        f"emitted block has {len(_wb)} lines, base block has {len(block)}: "
        "the trailing separator line was lost")
if block[-1] == "" and _wb[-1] != "":
    raise SystemExit("emitted block does not end with the separator blank line")
print(f"  block round-trip: {len(_wb)} lines == base {len(block)}  OK")

print(f"\nwrote {out.relative_to(ROOT)}  ({out.stat().st_size} B)")
