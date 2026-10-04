# -*- coding: utf-8 -*-
"""Append the A-6 Errata section and refresh the README's baseline warning.

Idempotent by construction: the errata block is skipped when its heading is
already present, and the README replacements assert the old text so a drifted
README aborts instead of being silently rewritten.
"""
import io
import os
import sys

REPO = r"D:/myProject/DecompMoE"
# self-locating so this keeps working after `openspec archive` moves the dir
AUDIT = os.path.join(REPO, ".audit", "wayfinder-opsx-code-review")
LIST_A = os.path.join(AUDIT, "lists", "opsx-changes.md")
README = os.path.join(AUDIT, "README.md")

HEADING = "## Errata (A-6 侧)"

ERRATA = """## Errata (A-6 侧)

> **由实施 change `2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline` 产出。**
> **正文已就地更正**，本节记录**更正依据与可复算的判据**；`基线` 字段同时按新漂移表重算。
> 所有当前判断以冻结 commit `95718cf` 为准（pin 仍是 `6593a06`）。
>
> 全部判据由 `evidence/verify_a6_errata.py` 从 git 重新推导，不采信任何转述。

### 前置：这一段为什么必须重算

- **清单落后 21 个 commit。** 审计快照 HEAD 是 `188b9fb`（pin 后 9 个 commit），冻结 commit 是 `95718cf`（pin 后 **30** 个）。
- **漂移表没有生成脚本。** 原 `_pin_drift.json` 只存在于仓库外的 session 目录，`清单正文 L43` 自己也承认「生成脚本未记录」。
  本 change 补出 `evidence/build_pin_drift.py`，并以 `pin..188b9fb` 重跑、与原表**逐键相等**（60 文件 / 105 区间 / 0 差异）作为保真自检。
- **坐标侧此前记为未知，现已测定**：漂移表记录 hunk 的 **HEAD 侧（`+`）行号**，纯删除 hunk 钳位为 `[n, n]`，整文件删除记作 `[0, 0]`。
  判据是三条互相印证的 hunk：`@@ -496 +499 @@` → `[499,499]`（非 pin 侧 496）、`@@ -325,0 +326,4 @@` → `[326,329]`（纯插入计入）、
  `@@ -1,80 +0,0 @@` → `[0,0]`（纯删除钳位）。
- **`基线` 口径未重定义。** 表内区间是 HEAD 侧坐标而 `位置` 是 pin 态行号，两者不同坐标系；全部 123 个字段都在该口径下产生。
  重定义会同时改写 123 条，本轮不擅自做。插入与修改已在漂移表的 `inserted` / `modified` 两个视图中分离，
  但**计入判定时仍按旧的 merged 口径**；实测现有条目中 **0 条**会因该差别改变状态。

### 行号是怎么定的（给下一轮的判据）

本段的行号**全部**由 `git grep -n` 与 Python 的 `git show` 双重确认，不采信 PowerShell 的 `Select-Object -Skip N` 标号：
后者在本次实测中**静默丢了一个空行**，导致每个标号偏移 1——第一版更正因此把 AC-26 锚到 177（实为 178）、
把 AC-50 的 `spec.md:383` 误判为「空行、正文在 382」而改错。`evidence/verify_a6_errata.py` 的
`B-AC26-anchor` / `B-AC50-anchor` 两项当场抓到了这两处，改正后重跑全绿。

两个独立方法一致才算数：pin 态 `tests/test_config.py:69` 由 `git grep -n` 与 Python 双双命中
`assert router_per_layer == 32_896`，而按 0-based 读同一断言会落到 L70（空行）——**基准是 1-based**。

### 逐条更正

| 条目 | 字段 | 原值 | 现值 | 判据 |
|---|---|---|---|---|
| AC-06 | 裁决 / 严重性 | `MOVED` / CRITICAL | `FIXED_BY_COMMIT` / MEDIUM | pin `sphere.py:67` docstring 记「via Gauss–Legendre 8-point」；冻结 commit 的 `sphere.py:141` 已是自适应 8/16 点 GL，HISTORY 段逐字含 pre-fix 值 `8.29e-07`(6.633 ppm) / `1.57e-01` |
| AC-06 | 位置 | `sphere.py:137` | `sphere.py:67` | pin L137 实为 `VORONOI_AREA_SAMPLES` 的 docstring 行；`_cap_area` 在 L151 |
| AC-26 | 裁决 | `STILL_REAL` | `FIXED_BY_COMMIT` | `rv:main45:{source,math,impact}` 三键 verdict 一致为 `FIXED_BY_COMMIT`（`fixingCommit=315065e`） |
| AC-26 | 位置 | `test_loss.py:166` | `test_loss.py:178` | pin L167 是 `test_lambda_cosine_ramp_phase_3` docstring 续行；**L178** 才是该函数内承载 `actual=` 的断言消息行（L177 是 `assert` 行本身） |
| AC-27 | 基线 | `touched-since-pin` | `unchanged-since-pin` | skeleton 区间 `[98,98][132,132][255,255][270,271][326,329][340,340][499,499][501,501][524,524]` 不含 122；122 是 `@@ -121,0 +122,13 @@` 插入块首行，在 pin→冻结区间内不属于任何 hunk |
| AC-27 | `+1/+13/+8` | — | **保持不变（已双口径验证为真）** | `git diff --numstat`（3/2、14/1、9/1）与真实行数（892→893、623→636、165→173）互证；`33f7cc9` 是区间内唯一触及三份 spec 的 commit |
| AC-29 | 位置 | `_final_report_full.md:1367` | `:1336` | 报告实测 1677 行；「诚实边界」逐字命中 L1336，L1367 是「环 7 修复顺序」表的第 4 行 |
| AC-29 | 溯源 | 含 `rv:main18:math` | 删除 | 该键在 `_handoff_verdicts_all.json` 的 197 个 key 中不存在（只有 `rv:main18:source`） |
| AC-30 | 裁决 | `STILL_REAL` | `FIXED_BY_COMMIT` | 冻结 commit `extraction.py:104` 的 `mask: Tensor` 已无默认值；L118 逐字记录旧默认值被移除，L137-141 缺 mask 即抛错 |
| AC-30 | 位置 | `src/decompmoe/schedule.py`（line=0） | `src/decompmoe/extraction.py:90` | `CentroidDriver` 类定义在 pin L90 / 冻结 commit L98；`schedule.py` 全文仅 1 处散提及 |
| AC-30 | 溯源 | `rv:main20:math` | `grv:gap0:math` | 全库 54 个治理类 key 一律 `grv:` 前缀，**零个** `rv:grv:` / `rv:gap0:`；原键 verdict 是 `UNVERIFIABLE` 且 finding 为 `territory_collapse` |
| AC-50 | 位置 | `wayfinder/spec.md:383` | **不变（已复核为正确）** | pin L383 **就是 Req 17 正文**（anchor L379、标题 L381、L382 空行）。本轮一次基于错误行号的「更正」曾把它改到 382，复核后已撤回 |
| AC-50 | 证据 | 「0.436% 用的是另一个分母」 | `0.436% = 66_336/66_048 − 1` | **量纲错配**：相对增幅去比占 `33_554_432` 分母的 allowance。这才是驳回成立的真理由 |
| AC-50 | 溯源 | `rv:main18:source` / `rv:main17:source` | 追加 `rv:main42:{source,math,impact}` | 三键确实存在（verdict 均 `STILL_REAL`），标题指向 main42 却未收录 |
| AC-51 | 溯源 | `rv:grv:gap25:math` | `grv:gap25:math` | 真键无 `rv:` 前缀；其 verdict 是 `UNVERIFIABLE`，支撑「WB 无闭式」的是 evidence 文本 |
| AC-51 | 正文指针 | `test_config.py:69` | `tests/test_config.py:69` | 与本条「位置」字段自相矛盾（清单原文少了 `tests/` 前缀） |

### 全清单重基线（117 个条目 / 123 个字段实例）

- 42 个 `基线` 字段被更正；分布由「10 touched / 98 unchanged」变为 **23 touched / 75 unchanged / 19 unverifiable**（本文件 108 条口径）。
- 新增第三态 **`unverifiable (no pin line)`**：该条没有可用行号（`line=0` 的目录级定位），或其 `location_file` 不是现存的仓库内文件
  （change 已归档、路径不复存在，或指向仓库外的审计报告）。**19 条**属此类。对它们给出 touched/unchanged 都是虚假精度——
  清单 B 的 DF-02 正文其实早已写明「漂移表对仓库外路径无覆盖能力……不是该目录已稳定的证据」，本轮只是把该警告编码进字段值。
- 清单 B（`lists/direct-fixes.md`）8 条改为 `unverifiable`（DF-01 ~ DF-06、UD-03、UD-06）。该文件**无任何生成脚本**，只能手术式改写。

### 本节不做的事

- **不重定义 `基线` 口径。** 「纯插入是否应算 `touched`」留待下一轮裁定；数据已由漂移表的 `inserted` 视图留存。
- **不重新裁决其它段。** A-1 ~ A-5 / A-7 / A-8 的 verdict 与严重性未动，只重算了它们的 `基线`。
- **不重算任何数学闭式**，不重跑 lens，不重放变异测试。
- **不碰 `openspec/specs/**`、`src/**`、`tests/**`**：AC-06 / AC-30 的真实缺陷已由 `f6461d7` / `a97e3a7` 关闭。
"""

README_OLD_TABLE = (
    "| `context/07-baseline-drift.md` | pin `6593a06` 到 HEAD `188b9fb` 的 9 个 commit 改了什么 |"
)
README_NEW_TABLE = (
    "| `context/07-baseline-drift.md` | pin `6593a06` 到审计快照 HEAD `188b9fb` 的 9 个 commit 改了什么 |"
)
README_OLD_WARN = (
    "本议题所有 `file:line` 均为 pinned commit `6593a06` 的行号。\n"
    "此后仓库又落了 9 个 commit，改动了 8 个 `src/` 与 `tests/` 文件以及全部 3 份 spec。\n"
    "**动手前必须按 `context/07-baseline-drift.md` 的漂移表重新定位。**"
)
README_NEW_WARN = (
    "本议题所有 `file:line` 均为 pinned commit `6593a06` 的行号，行号基准为 **1-based**。\n"
    "审计快照 HEAD 是 `188b9fb`（pin 后 9 个 commit）；此后仓库又前移，**pin 后已 30 个 commit**，"
    "累计改动 265 个文件（`src/` 9、`tests/` 13、`openspec/specs/` 3、`openspec/changes/` 235）。\n"
    "**动手前必须重新定位。** 漂移表已可重生成：`2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline` 的 "
    "`evidence/build_pin_drift.py`（以 `pin..188b9fb` 与原表逐键相等自检），"
    "`基线` 字段的三态定义与坐标侧测定见清单 A 的「基线状态字段怎么读」小节。"
)


def main():
    problems = []

    # ---- 1. append the A-6 errata ----
    with io.open(LIST_A, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if HEADING in text:
        print("errata: already present, skipped")
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n---\n\n" + ERRATA
        with io.open(LIST_A, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        with io.open(LIST_A, encoding="utf-8", newline="") as handle:
            back = handle.read()
        if HEADING not in back or "0.436% = 66_336/66_048" not in back:
            problems.append("errata append did not verify on read-back")
        else:
            print("errata: appended and verified on read-back")

    # ---- 2. README baseline warning ----
    with io.open(README, encoding="utf-8", newline="") as handle:
        readme = handle.read()
    for old, new, label in (
        (README_OLD_TABLE, README_NEW_TABLE, "table row"),
        (README_OLD_WARN, README_NEW_WARN, "baseline warning"),
    ):
        if new in readme:
            print("README %s: already updated" % label)
            continue
        if old not in readme:
            problems.append("README %s: old text not found (README drifted?)" % label)
            continue
        readme = readme.replace(old, new, 1)
    if not problems:
        with io.open(README, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(readme)
        with io.open(README, encoding="utf-8", newline="") as handle:
            back = handle.read()
        if README_NEW_TABLE not in back or README_NEW_WARN not in back:
            problems.append("README write did not verify on read-back")
        else:
            print("README: updated and verified on read-back")

    if problems:
        print("PROBLEMS:")
        for line in problems:
            print("  " + line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
