# Tasks — 数值字面量 provenance 修复

## 0. 门禁（apply 开工前）

- [ ] 0.1 **先复现缺陷，不先改文本**。跑 `evidence/_alpha_forensics.py`，确认四组残差（canonical N_e=16 / N_e=64 / 二分停点 / spec 声称值）逐位复现，且量纲论证段落给出的位数（50.1 位十进制 vs float64 约 16 位有效）成立。验证：脚本 exit 0，且打印的四行数与本文件 A1 表逐位相符；**若复现失败，停止并重新定位**——不得在未复现的状态下改真相源。
- [ ] 0.2 定位全部出现点。`git grep -n -F '5.01e-52' HEAD --` 与 `2.92e-52` 同跑，分类为「真相源」与「Change 2 归档副本」两桶。验证：真相源恰为 4 行（governance L17/L20/L21 + skeleton L114）、归档恰为 4 行；两桶计数之和等于 `git grep` 总命中数。

## 1. 真相源修正

- [ ] 1.1 用 `evidence/_gen_alpha_delta.py` 生成两份 delta。**禁止手抄**（这两份 spec 的 body 是单行数千字符）。验证：生成器对每条片段报「恰好命中 1 行」；逐行 `unified_diff` 回验显示 4 行变更；`5.01e-52` 与 `2.92e-52` 计数 **3→0 / 1→0 / 1→0 / 1→0**。
- [ ] 1.2 每处替换必须含三要素：**真值 + 「该量由二分停止判据而非 float64 精度决定」+ provenance 脚本路径**。验证：逐处 grep 到 `bisection stopping criterion` 与 `2026-10-02-repair-spell-numeric-literal-provenance`；**缺任一要素即退回**——只换数字不改说明等于把一个魔法数换成另一个。
- [ ] 1.3 **不改归档副本**。验证：`git status` 中 `openspec/changes/archive/**` 零改动；`req-gov-5` 的 Policy lineage 显式记录「归档保留原值属历史记录」。

## 2. 新增 `governance` Requirement `req-gov-5`

- [ ] 2.1 写 `req-gov-5`「数值字面量 provenance 义务」，含 A3 的三类可机检反例（C1 量纲不可能 / C2 bracket 冒充根 / C3 默认值当判据）与各自的机检手段。验证：`openspec validate --strict` 通过；anchor `<a id="req-gov-5"></a>` 置于 `### Requirement:` 标题**之前**且中间空行。
- [ ] 2.2 给每条 Rule 配至少一个 Scenario，Scenario 的数值断言必须是**裸整数 `==`**（整数闭式）或 `pytest.approx(..., abs=...)`（浮点闭式），并在失败信息内嵌 `f"actual={...}"`。**禁止文字断言**（「正确」「合理」不构成可验条款）。
- [ ] 2.3 同步 `build_baseline.py` 的 `EXPECT_ANCHORS["governance"]` = 5，并跑一次确认 **覆盖** 契约通过（每条 Requirement 恰一个独立 anchor、无重复）。验证：`anchor coverage : True`；绝对计数漂移被报为 drift 而非缺陷。
- [ ] 2.4 **为新 Rule 写一个会红的检查**：把 C1 的位数判据做成 `evidence/tools/check_numeric_provenance.py`，并在 `verify_toolchain.py` 的 CONTRACT 里加一条 must-appear + must-not（must-not 必须取一个该工具**可能打印**的失败串，不能是永不可能出现的句子——本仓刚修过一个这样的死哨兵）。验证：向脚本喂入 `5.01e-52` 与一个量纲自洽的 `1.46e-17`，前者必须红后者必须绿。

## 3. 回归与交付

- [ ] 3.1 `pytest -q` 全绿。验证：`tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` 仍通过——它断言 `< 1e-9`，`1.46e-17` 与 `5.01e-52` 都远低于该界，**本次修改不得改变任何测试行为**。
- [ ] 3.2 `openspec validate <change> --type change --strict` exit 0；`scripts/lint_no_dead_defensive.py` 与 `scripts/lint_no_source_field_drift.py` 均 exit 0（`req-gov-5` 的 Source 反链须含 `` `CLAUDE.md` `` 字面反链，否则第二条 lint 必红）。
- [ ] 3.3 archive 后按本仓协议复算三份 spec 的 anchor **覆盖**，并预期 archive 仍会吞 1 个 anchor —— 若发生，从 `git cat-file blob` 恢复且**绝不重跑 archive**。验证：覆盖 100%、0 重复。
- [ ] 3.4 交付说明：登记本 change **未**修的两处相邻缺陷——`governance` 义务 1/3 的 `pytest.approx` 语义错误（属 Change β）、`tests/test_sphere.py:98-99` 同一错误论断的 docstring 副本（属 Change β）。验证：两条都在 tasks 或 design 中有具名登记，不以「已一并处理」含糊带过。
