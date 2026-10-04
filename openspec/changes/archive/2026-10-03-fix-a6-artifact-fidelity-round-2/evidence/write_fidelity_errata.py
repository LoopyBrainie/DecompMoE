#!/usr/bin/env python3
"""Append `## Errata (A-6 制品复验 侧)` to lists/opsx-changes.md.

Idempotent by construction: the block is skipped when its heading is already
present, and the append is verified by reading the file back. Written this way
because the A-6 change's own writer was lost once already (see the INCIDENT
section below) and a silent partial write is how it was lost a second time.
"""

from __future__ import annotations

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    path = os.path.abspath(start)
    while True:
        if (os.path.isdir(os.path.join(path, "openspec"))
                and os.path.isdir(os.path.join(path, ".audit"))):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            raise RuntimeError("repo root not found above %s" % start)
        path = parent


REPO = _repo_root(HERE)
LIVE = os.path.join(
    REPO, ".audit", "wayfinder-opsx-code-review", "lists", "opsx-changes.md"
)

HEADING = "## Errata (A-6 制品复验 侧)"

ERRATA = """## Errata (A-6 制品复验 侧)

> 追加于 change `2026-10-03-fix-a6-artifact-fidelity-round-2`。该 change 复核了
> `2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline` 自身的制品，只改
> `.audit/` 下的审计制品与本 change 的 `evidence/`，**未触碰任何 spec / src / tests**。
> 全部修正走本 Errata，**不原地编辑归档目录**（`CLAUDE.md` §3：已消费的归档制品不可回改）。

### 已修 — 漂移表保真自检的措辞掩盖了键集差异

`evidence/build_pin_drift.py` 的 `self_check()` 原先只在 `path` 出现在
`set(原表) | set(本方)` 时逐键比较区间。因此「仅本方存在、且区间列表为空」的键
恒被判为相等，差异被完全吸收。随后打印的
`SELF-CHECK PASSED: drift identical to the original table (60 files, 105 intervals)`
里的 `60` 是**本方**的键数，而原表只有 **48** 个键——读这句话的人会以为表结构也一致。

实测（本 change 独立重算，未引用 review 的数字）：

| 口径 | 原表 | 本方 |
|---|---|---|
| drift 键数 | 48 | 60 |
| drift 区间数 | 105 | 105 |
| 仅本方存在的键 | — | **12**（**全部携带空区间列表**，非空者 0） |
| 仅原表存在的键 | — | **0** |
| 48 个共有键的区间 | — | **逐键相等，0 处不匹配** |

**漂移表本身是对的**——`基线` 判定的输入可信。失真的只是自检报告的措辞。修正版
（`2026-10-03-fix-a6-artifact-fidelity-round-2/evidence/build_pin_drift.py`）：

- 键集差异**单独计算、单独打印**，三类（仅原表 / 仅本方 / 共有）分列且路径全量输出；
- 新增**硬断言**：仅本方存在的键若携带**非空**区间 ⇒ 报红退出 1
  （空区间键合法——`git diff` 会为每个 `diff --git` 头注册键，包括无 hunk 的头）；
- PASSED 措辞拆成「区间相等」与「键集」两句，`files=` 一词不再混指两件事，并显式声明
  **键数相等不是被断言的不变量**。

### 已修 — 漂移表产物文件名与内容不自洽

`evidence/pin_drift_95718cf.json` 读作「以 `95718cf` 为 pin 的漂移表」，而内容是
`"pin": "6593a06"` / `"head": "95718cfa0b7e..."`——`95718cf` 是 **head** 侧。类型前缀
`pin_drift` 与端点挤在同一个 token 里造成歧义。

本 change 生成 `evidence/drift_6593a06..95718cf.json`（文件名自带双端点），并与归档那份
**逐键比对** `drift` / `inserted` / `modified` 三张表。归档目录里的旧文件**未改名**——
内容正确，只是名字误导，改名等于原地编辑归档制品。

### 已修 — 清单生成器 `ANNOT` 表的重复键（review 未单列，本 change 纳入）

`_work/_gen_listA2.py` 的 `ANNOT` 字面量里 `AC-28` 写了两次、`AC-29` 写了两次。
Python 的 dict 字面量**静默保留最后一次**，`ast` 层面完全合法，无任何警告：

| 键 | 被静默丢弃的那一段 | 是否已进产物 |
|---|---|---|
| `AC-28` | `[边界保留]`（check-completeness 判 borderline） | **否**——真实数据丢失 |
| `AC-29` | `[分桶存疑]`（报告 §11 第 4 条是弃权声明） | 是，但那是 A-6 手术式手改保住的，**不是生成器渲染的** ⇒ 潜伏缺陷，谁重跑生成器就会丢 |

两段文本语义不同，**都已合并保留**（`AC-28` 的两段、`AC-29` 的两段），`ANNOT` 键数仍为 19。

并新增 `_assert_no_duplicate_annot_keys()`：从 `__file__` 解析自身源码，在
`ANNOT` **字面量层面**收集 `(key, lineno)`，有重复即 `raise`，模块加载时执行。
不写成 `assert len(ANNOT) == 19`——那个硬编码数本身是会漂移的第二真相源；
也不写成遍历 `ANNOT` 查重——重复键在构造时就已经丢了，后面看不到。

### 已驳回 — review 的 F-1（`基线` 三态计数自述不符）

review 报 `opsx-changes.md` 自述 `23/72/13`（合计 108）与机械统计 `23/74/12`（合计 109）不符。
**该条不成立。** 计数单位应是 `基线:` **字段声明行**，不是条目块：

- 按字段声明行统计：恰有 **108** 条 = `touched 23` + `unchanged 72` + `unverifiable 13`，
  与自述**逐位吻合**；
- 按 `###` 条目块统计：`###` 标题共 146 个，其中含 4 个**非条目小节**
  （`基线状态字段怎么读` / `清单 B 的边界` / `对账口径速查` / `本次未做`），此口径下得
  `26/75/17/8`，**同样复现不出 109**。

即 109 在两种口径下都不可复现，字段口径与自述完全一致。**原 `基线` 计数保持 `23/72/13`。**
详见本 change `design.md` D1。

### 未修 — F-8 / F-9 等 6 条，留给后续独立 change

用户已就范围裁定本 change 只修 Part 1。review 第二部分的 6 条 finding 不动，其中 2 条
阻断 archive 前门禁：

- **F-9**：`torch.allclose(atol=1e-12)` 被隐式 `rtol=1e-5` 架空。float64 实测：在 `|b| ~ 1` 时
  漂移 `1e-12 / 1e-9 / 1e-7 / 1e-6 / 1e-5` 在默认下**全部**返回 `True`、`rtol=0` 下**全部**
  返回 `False`；全 `tests/` 49 处 `allclose` 无一写死 `rtol=`。
- **F-8**：空 cell 不变量在 `tests/test_extraction.py` 无原理级守卫，根因即 F-9。两者必须同一
  change 处理——F-9 修好之前补 F-8 是无效功。

**用户已预先裁决 F-9 的修法**：float64 守护「机器精度恒等」，float32 另设一个可达容差。
该裁决连同实测前提（生产路径基线漂移 `7.451e-09`，已超 spec 声明的 `1e-12` 三个数量级）
记入本 change `design.md` D5，不因本轮不实施而丢失。

### INCIDENT — 本 change 的一次自伤与恢复（记录在案）

为验证 `ANNOT` 修复，本 change 的一个验证脚本 **`import` 了 `_gen_listA2.py`**。
该模块在**导入时**执行写出（模块级 `io.open(OUT, "w")`），于是
`lists/opsx-changes.md` 被整份重生成覆盖：**1931 行 → 1495 行，4 个 `## Errata` 小节全丢**。

A-6 的字段修正**未丢**（生成器带 `OVERRIDE` + `a6_expected.json` 锁，`_work/classified.json`
未被触碰），丢的是手写的 Errata 叙述段。恢复方式：从 A-6 change 自己的
`evidence/_pre_edit_opsx-changes.md` 快照按结构边界取回 369 行尾巴（逐字节校验），
再用 A-6 自带的 `write_a6_errata_and_readme.py`（幂等）补回第 4 个小节。
恢复后 A-6 自带验证器 `verify_a6_errata.py` **65/65 全绿**，
本 change 的 `evidence/recover_errata_tail.py` 记录了全过程。

**已加的防线**：`_gen_listA2.py` 的 `OUT` 不再指向 live 清单。必须显式传目标路径
（`argv[1]` 或 `$A6_GEN_OUT`），否则写临时文件；**试图原地写 live 清单直接 `exit 2` 并给出
拼接指引**。`lists/opsx-changes.md` 是「生成前缀 + 手写尾巴」的拼接产物，不是生成器的完整产物——
这条性质此前只写在 `tasks.md` 的「不做」清单里，现在写进了生成器自己的 docstring 与拒绝逻辑。

### 已知副作用 — A-6 自带验证器的 `F-errata` 会报红（预期内，不要「修」）

追加本小节后，A-6 change 自带的 `verify_a6_errata.py` 从 **65/65** 变为 **64/65**，
失败的是 `F-errata`：

```
FAIL F-errata   all four Errata sections survive (A-1, A-2, A-4, A-6) | sections=5
```

**这不是回归。** 那条检查的期望值写的是「**恰好 4 个** Errata 小节」——它编码的是
写它当时的状态，不是不变量。其它 **64 条**（A-6 的全部字段级修正）逐条仍绿。

**不要为了让验证器变绿而删掉本小节。** 预期状态已被
`2026-10-03-fix-a6-artifact-fidelity-round-2/evidence/verify_artifacts.py` 的
`check_a6_verifier_state()` 钉住：总检查数 65、失败数**恰好 1**、且那一条**必须**是
`F-errata`。**出现第 2 条失败才是真回归**，届时应查 A-6 字段修正本身。

正确的长期修法是把 A-6 那条断言从「4 个」改成「≥ 4 个」，但那要改归档目录里的
验证器，属于「决定重做基线口径」那一轮，不在本 change 范围。
"""


def main():
    replace = "--replace" in sys.argv
    with io.open(LIVE, encoding="utf-8", newline="") as handle:
        text = handle.read()

    problems = []

    if HEADING in text:
        if not replace:
            print("errata: already present, skipped (use --replace to update it)")
            return 0
        # Heading-only idempotence is the SAME defect as the ANNOT duplicate keys:
        # merge once, then frozen forever, with no way to correct the content.
        # `--replace` truncates from this section's boundary and re-appends, so
        # the writer can update its own text. The section is always last, so the
        # truncation cannot touch anything else.
        idx = text.rindex("\n---\n\n" + HEADING)
        prefix = text[:idx + 1]
        # `text[idx+1:]` begins with the `---` separator, then the heading
        if not text[idx + 1:].lstrip("-\n ").startswith(HEADING):
            problems.append("boundary found is not the start of this section")
        with io.open(LIVE, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(prefix)
        text = prefix
        action = "replaced"
    else:
        action = "appended"

    if not text.endswith("\n"):
        text += "\n"
    text += "\n---\n\n" + ERRATA
    if not text.endswith("\n"):
        text += "\n"

    with io.open(LIVE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    # ---- verify by reading the file back, structurally ----
    with io.open(LIVE, encoding="utf-8", newline="") as handle:
        back = handle.read()
    if HEADING not in back:
        problems.append("heading absent after write")
    n_errata = sum(1 for l in back.split("\n") if l.startswith("## Errata"))
    if n_errata != 5:
        problems.append("expected 5 Errata sections, found %d" % n_errata)
    if not back.startswith(text[: text.index(HEADING)].rstrip("\n")):
        problems.append("existing content was not preserved as a prefix")
    # every `###` subsection of the literal must be present in the written file --
    # a truncated or partially written tail would still satisfy the checks above
    written_section = back[back.rindex("\n---\n\n" + HEADING):]
    for sub in re.findall(r"(?m)^### (.+)$", ERRATA):
        if sub not in written_section:
            problems.append("subsection %r missing from the written section" % sub)
    if problems:
        print("ERRATA WRITE VERIFICATION FAILED:")
        for p in problems:
            print("  " + p)
        return 1

    print("errata: %s and verified on read-back" % action)
    print("  file now       : %d chars, %d lines" % (len(back), len(back.split("\n"))))
    print("  Errata sections: %d" % n_errata)
    print("  subsections    : %d" % len(re.findall(r"(?m)^### ", written_section)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
