"""Append the A-4 Errata section to the audit list.

Append-only, per the file's own "只增不减" rule: existing entries are not
rewritten, so the audit trail stays intact and the corrections are readable
alongside the claims they correct.

Every number below was re-derived from git by `evidence/derive_a4_errata.py`
against the blobs this list cites (pin `6593a06`, audit HEAD `188b9fb`) — not
copied from the list and not taken from an earlier review pass. The measurement
basis is stated in the section, because an Errata that does not name the rev it
measured at goes stale in exactly the way it documents.

The file is LF with no BOM, so the append is written with newline="".
"""

import sys
from pathlib import Path

LIST = Path(".audit/wayfinder-opsx-code-review/lists/opsx-changes.md")
HEADING = "## Errata (A-4 段)"

SECTION = """

---

## Errata (A-4 段)

> 本节在实施 change `2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract`
> 时写入。按上文「只增不减」规则**只追加**，不改动 AC-34…AC-90 任一原条目。
>
> **测量基准**：全部坐标经 `evidence/derive_a4_errata.py` 从 git 重新派生，
> 对照 blob 为 pin `6593a06` 与 audit HEAD `188b9fb`；`基线` 字段一节的
> commit 计数测于 `850ed8a`。逐项可复算，不引用本清单的 `基线` 自述字段，
> 也不引用本 change 早前的复核结论。

### A4-E1 — AC-34 的行内坐标是 0-based，且其所称的「漂移」在该坐标上不成立

AC-34 正文称「wayfinder L413 实际是空行——MCI 行在 L460、Source 在 L463、两个
MCI Scenario 在 L497/L501」。在 pin `6593a06` 实测（1-based）：

| 清单所称 | 1-based 实测该行 | 1-based 实测下一行 |
|---|---|---|
| L413 是空行 | `### Requirement: Six Baseline Set On 4070 MVP` | `''`（空行） |
| MCI 行在 L460 | `\| \`D_chord\` \| …`（相邻指标行） | `\| \`MCI\` \| \`MCI = 1 / (d_c · Σ λ̃_j²)\` …` |
| Source 在 L463 | `''`（空行） | `**Source:** \`wayfinder/tickets/A8-2.md\`…` |
| Scenario 在 L497 | `''`（空行） | `#### Scenario: MCI closed-form on uniform token distribution` |
| Scenario 在 L501 | `''`（空行） | `#### Scenario: MCI closed-form on rank-1 token distribution` |

**五个坐标全部恰好少 1**，且「L413 是空行」只在 0-based 读法下为真 ⇒ AC-34 的行内
坐标按 0-based 书写。**更关键**：pin `6593a06` 与 audit HEAD `188b9fb` 的
wayfinder spec 在上述每个坐标上**逐字相同**（两版均 894 行），即该区间**没有发生
任何漂移**。AC-34 对 req-36「多数已漂移」的裁决，有一部分证据是这个基准差，而不是漂移。

同一读法问题波及 AC-88（聚合记录，直接引用 req-36 的 L434-505 / L450 / L453 / L454 /
L456 / L416 / L413 坐标族）与 AC-59（「skeleton L242 引 wayfinder L249 实为 L315」），
二者应与 AC-34 一并按 0-based 复核后再采信。

### A4-E2 — `基线` 字段在文件级读法下 15/15 全错（不是部分错）

A-4 全部 15 条的 `基线` 一律写 `unchanged-since-pin`，整齐得反常。按「该文件自 pin
起是否被改动过」读法实测（`git log 6593a06..850ed8a -- <file>`）：

| 文件 | pin 后 commit 数 | 覆盖的 A-4 条目 |
|---|---|---|
| `openspec/specs/wayfinder/spec.md` | 8 | AC-34 / AC-88 / AC-89 / AC-90 |
| `openspec/specs/decompmoe-skeleton/spec.md` | 8 | AC-59 / AC-63 / AC-70 / AC-71 |
| `src/decompmoe/sphere.py` | 5 | AC-72 |
| `tests/test_safeguards.py` | 4 | AC-67 |
| `tests/test_extraction.py` | 4 | AC-69 |
| `src/decompmoe/metrics.py` | 3 | AC-68 |
| `src/decompmoe/schedule.py` | 2 | AC-66 |
| `src/decompmoe/config.py` | 1 | AC-65 |

**无一个文件自 pin 起零改动** ⇒ 15/15 的 `基线` 标注均不成立。

**该计数本身会漂，故必须记基准**：本 change 在 apply 起点（`1526b98`）实测为 **14/15**，
唯一例外是 `src/decompmoe/config.py`（当时 pin 后 0 commit）；本 change 的清扫提交
`a1f0caa` 随后改动了该文件，例外消失。**这正是本 Errata 记录的那一族缺陷**：一个不带
基准的计数，会在被测对象自身变化后静默改变真值。

### A4-E3 — AC-88 是 AC-34 / AC-89 / AC-90 的聚合记录，且重复对字段值比对不可见

AC-88 标题自称「（聚合记录）」，其 `origin_ids` 为 `main44`、`main72`、`main74`、
`main77` 四个；而这四个 id 分别就是 AC-90（`main77`）、AC-34（`main72`）、
AC-89（`main74`）与 AC-88 自身（`main44`）。

**因此 AC-34 + AC-89 + AC-90 的内容已被 AC-88 整体重述一遍**。任何按 `origin_ids`
**字段值**做去重的检查都发现不了：AC-88 把四个 id 塞进一个字段，字段值与那三条各自
的单 id 值不相等。只有把该字段拆成 id 列表再比对，重复才显形。

另：AC-34 与 AC-88 的 `位置` **完全相同**（均为 `openspec/specs/wayfinder/spec.md:847`
pin 态），`源 id` 却分别是 `W12` 与 `W13`，条目间无任何交叉引用。

### A4-E4 — AC-70 的 `位置` 指向空行；AC-59 / AC-70 不是重复项

pin `6593a06` 的 skeleton spec 实测：L240 = `''`（**空行**），L241 =
`#### Scenario: L_sep closed form`，L242 = 该 Scenario 的 `- **WHEN**` 子句。
故 AC-70 的 `位置` `skeleton:240` 指向空行，内容在 241 起。

**AC-59 与 AC-70 不是同一条**：AC-59 是 spec→spec 指针（skeleton 引 wayfinder
`L249`），AC-70 是 spec→code 指针（skeleton req-12 引 `safeguards.py:211/:222`），
目标不同，只是 `位置` 相隔 2 行。本 change 早前一轮复核曾把二者登记为重复项，
**该判断错误，此处更正**。

### A4-E5 — AC-63 的「零命中」属实，但清单把它归错了原因

AC-63 主张 `arctan(pi/sqrt(d_c))` 这一形式在 spec 中零命中。实测零命中为真
（`evidence/pointer_census.py` 的分类器自检以 `wayfinder L249` = 10 作阳性对照，
确认分类器未失效）。

但清单把「3.58」当作该不变量的组成部分之一。**`3.58` 与 arctan 无关**：它是
`sphere._betainc_regularized` 自身 docstring 在 `θ = 82.6036°` 处报告的求积误差
`3.58e-16`，与该 token 无关。因此「`3.58` 缺失」这条证据对 arctan 不成立，
零命中**只**证明该字面 token 不存在，不能证明其数学内容未被以其他写法引入。

清单所称偏离幅度亦只有 1/3 可复现：实测 `5.078e-01`（`N_e=16`）与 `5.001e-01`
（17）可复现，`1.53e-05` 不可复现（`N_e=64` 实测 `3.547e-01`）。

### A4-E6 — 本段的 4 条处置汇总

1. **基准错误 1 族**：AC-34 / AC-88 / AC-59 的行内坐标为 0-based（A4-E1）。
2. **`基线` 字段 15/15 错**，且该计数自身随被测对象漂移（A4-E2）。
3. **静默重复计数 1 处**：AC-88 聚合 AC-34/89/90，字段值比对不可见（A4-E3）。
4. **`位置` 指向空行 1 条**：AC-70（A4-E4）；AC-59/AC-70 非重复，本段更正了
   本 change 早前一轮复核的错误登记。

**AC-34 的处置变更**：其「req-36 整段行号指针失效」的**实体**经本 change 独立确认
成立（req-36 的 Scenario 标题本身含行号，无法以 MODIFIED 改写，已按
`## REMOVED Requirements` 移除并迁移其 4 条保障）；但其**证据中的坐标基准**须按
A4-E1 更正后重述，本 change 未据其坐标数字施工。
"""


def main() -> int:
    text = LIST.read_text(encoding="utf-8")
    problems = []
    if HEADING in text:
        print(f"ABORT: {HEADING!r} already present; this append is not idempotent")
        return 1
    before = text
    if not text.endswith("\n"):
        text += "\n"
    with LIST.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + SECTION.lstrip("\n"))

    # Read back: the append must be present, the original must be byte-identical
    # as a prefix, and the line endings must still be LF-only.
    after = LIST.read_text(encoding="utf-8")
    if not after.startswith(before):
        problems.append("the original content is not a prefix of the result")
    if HEADING not in after:
        problems.append(f"{HEADING!r} missing after write")
    raw = LIST.read_bytes()
    crlf = raw.count(b"\r\n")
    if crlf:
        problems.append(f"{crlf} CRLF introduced into an LF file")
    added = after.count("\n") - before.count("\n")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"appended {HEADING}: +{added} lines, {len(before)} -> {len(after.splitlines())} lines, LF preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
