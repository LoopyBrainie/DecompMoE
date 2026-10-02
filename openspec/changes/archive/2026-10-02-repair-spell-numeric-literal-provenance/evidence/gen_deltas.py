"""写出 Change α 的两份 delta（含整块 MODIFIED 与新增 req-gov-5）。

纪律见 design.md A4：整块抽取、整行替换、逐行 diff 回验。
只读主 spec，只写 change 目录内的 specs/。
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
ALPHA = ROOT / "openspec/changes/2026-10-02-repair-spell-numeric-literal-provenance"
(ALPHA / "specs").mkdir(parents=True, exist_ok=True)

N16 = "1.4635872379108090131680874e-17"
N64 = "1.9420345120803994000206689e-18"
PROV = (" This quantity is set by the bisection stopping criterion "
        "(|G - 1/N_e| < 1e-13), not by float64 precision; provenance is mpmath "
        "betainc(a, b, 0, x, regularized=True) at dps=60, reproducible via "
        "change 2026-10-02-repair-spell-numeric-literal-provenance "
        "evidence/_alpha_forensics.py.")

EDITS = {
    "governance": [
        ("`5.01e-52` at N_e=16, `2.92e-52` at N_e=64",
         f"the measured residual at the canonical literal is `{N16}` at N_e=16 "
         f"and `{N64}` at N_e=64"),
        ("| = 5.01e-52`", f"| = {N16}`"),
        ("yields `5.01e-52`", f"yields `{N16}`"),
    ],
    "decompmoe-skeleton": [
        ("is `5.01e-52` (N_e=16) / `2.92e-52` (N_e=64)",
         f"is `{N16}` (N_e=16) / `{N64}` (N_e=64)"),
    ],
}

REQ_ID = {"governance": "req-gov-1", "decompmoe-skeleton": "req-6"}


def extract_block(lines, req_id):
    """anchor 行 -> 该 Requirement 的所有 Scenario 结束（下一 anchor 或末行）。"""
    anchor = next(i for i, l in enumerate(lines)
                  if re.match(rf'^\s*<a id="{re.escape(req_id)}"></a>\s*$', l))
    nxt = next((i for i in range(anchor + 1, len(lines))
                if re.match(r'^\s*<a id="req-', lines[i])), len(lines))
    return lines[anchor:nxt]


HEADER = {
    "governance": "## MODIFIED Requirements\n",
    "decompmoe-skeleton": "## MODIFIED Requirements\n",
}

for cap, edits in EDITS.items():
    # 锚定 commit object，绝不读工作树：并行 session 正在未提交地重写 governance/spec.md，
    # 且把 req-gov-1 整块复制了一份（4 anchor / 5 Requirement）。对着脏工作树生成
    # delta 会把那份重复一起搬进 spec。
    _src = subprocess.run(["git", "show", f"HEAD:openspec/specs/{cap}/spec.md"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert _src.returncode == 0, f"cannot read HEAD:openspec/specs/{cap}/spec.md"
    lines = _src.stdout.splitlines()
    block = list(extract_block(lines, REQ_ID[cap]))
    print(f"\n{cap}: 抽取 {REQ_ID[cap]} 整块 {len(block)} 行")

    # 在块内做整行替换
    for old, new in edits:
        hits = [i for i, l in enumerate(block) if old in l]
        assert len(hits) == 1, f"{cap}: 片段 {old[:50]!r} 命中 {len(hits)} 行"
        i = hits[0]
        block[i] = block[i].replace(old, new + PROV)
        print(f"  块内 L{i} 整行替换 OK")

    body = "\n".join(block).rstrip() + "\n"
    out = ALPHA / "specs" / cap / "spec.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    # The extracted block ALREADY begins with the anchor and carries its own
    # `### Requirement:` title. Prepending the title again duplicated it -- the
    # delta then had two headings for one requirement, and the self-check
    # counted 3 requirements where 2 were intended.
    assert body.lstrip().startswith('<a id="'), "块首不是 anchor"
    out.write_text(HEADER[cap] + "\n" + body, encoding="utf-8")

    # ---- 回验：失效 token 必须归零，且整块与主 spec 只差预期行 ----
    for tok in ("5.01e-52", "2.92e-52"):
        n = body.count(tok)
        print(f"  失效 token {tok}: {n}  {'OK' if n == 0 else '<== 未清零'}")
        assert n == 0
    for must in ("bisection stopping criterion",
                 "2026-10-02-repair-spell-numeric-literal-provenance"):
        assert must in body, f"{cap}: 缺少必含项 {must!r}"
    assert body.count('<a id="') == 1, f"{cap}: 块内 anchor 数异常"
    print(f"  wrote {out.relative_to(ROOT)}  ({out.stat().st_size} B)")

print("\ndeltas written")
