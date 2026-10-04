# Design

## D1. `SELF_EXCLUDE` 按前缀测，不按子串

**问题**：`in_scope` 写的是 `any(x in f for x in SELF_EXCLUDE)`，而 `SELF_EXCLUDE` 的注释写的是「The lint entries are PREFIXES」。两者不一致，且实测会分歧。

**为什么危险的不是当下的数字**：真实 tracked 文件 0 条分歧——所有条目都位于自己目录的根（`scripts/lint_`、`tests/test_lint_`），后面接文件名。**正因为今天没有分歧，它才能连过四轮复核。**

**危险的是子串测试接受的输入**：

| 路径 | 子串 | 前缀 | 后果 |
|---|---|---|---|
| `docs/scripts/lint_notes.md` | True | False | 非 lint 文档被剔出普查 |
| `notes/tests/test_lint_extra.md` | True | False | 同上 |
| `openspec/specs/wayfinder/scripts/lint_x.md` | True | False | **一个 spec 被剔出普查总体** |

第三行是关键：普查的总体由「路径里含了 lint 目录」决定，而 spec 恰恰是最不能被静默剔除的东西——剔除之后 `openspec/specs/**` 的 actionable=0 这个结论就不再覆盖那个文件了，而且**门禁不会报红**。

**决定**：`f.startswith(x)`。与注释一致，且 `scripts/pointer_scan.py`、`tests/test_pointer_scan.py` 这两条整文件条目同样正确（文件以自身路径开头）。

## D2. 普查范围的具名清单是单源真相，住在 `pointer_scan.py`

**问题**：15 进 / 4 出写在 `lint_pointer_detector.py`，7 进 / 3 出写在 `tests/test_pointer_scan.py`。后者是前者的**严格子集**。子集检测不到它所遮蔽的超集的漂移，所以门禁那份更强的 pin 没有任何测试侧镜像。

这个反模式在本仓有前科，而且 `pointer_scan.py:644-646` 的注释就写着它：

> The two tools kept separate copies of this list, they drifted, and the census reported 43 "actionable pointers" that were the detector and its own tests.

那次是 `SELF_EXCLUDE` 的两份副本漂移。**修法当时就已经定型**：`SELF_EXCLUDE` 住在 `pointer_scan.py`，`lint_no_line_pointers.py` 写 `SELF_TEST_PATTERNS = _ps.SELF_EXCLUDE` 派生，测试断言两者相等。

**决定**：把 `PINNED_IN_SCOPE` / `PINNED_OUT_OF_SCOPE` 放进 `pointer_scan.py`，紧邻 `SELF_EXCLUDE`；`lint_pointer_detector.py`（第 35 行已经 `import pointer_scan as ps`）改为 `PINNED_IN_SCOPE = ps.PINNED_IN_SCOPE`；测试直接遍历 `ps.PINNED_IN_SCOPE`。

**为什么测试不 import lint**：`lint_pointer_detector.py` 是模块级自执行的门禁（跑完 83 项 `check` 后按结果 `sys.exit`），import 它等于跑一遍门禁。清单住在 `pointer_scan.py`（测试本来就已经 import）才既单一又不引入这个副作用。

**不采用「把测试的字面量补全到 15/4」**：那只是让两份副本变成两份一样大的副本，仍然可以漂移，而漂移过一次还伪造过一次绿灯。

## D3. 先断言计数，再断言性质

改写后的 `test_census_scope_pins_known_files_in_and_out` 先断言 `len(ps.PINNED_IN_SCOPE) == 15` 与 `len(ps.PINNED_OUT_OF_SCOPE) == 4`，再遍历。

理由是本轮复核里反复出现的同一族缺陷：`all(...)` 遍历一个可能为空的列表**真空为真**。D6 的组合检查曾在一个总数被减法破坏时全部通过；`if found:` 曾让空基线 exit 0。**把两个具名清单清空，会让一个纯 `for` 循环的测试从头绿到尾。** 计数不是正确性依据（这一点第四份 change 的 D5 已经写明），但它是「这段断言不是空的」的前提，两者不冲突。

顺带断言两个集合不相交——一个文件同时被钉在内和外，说明清单本身自相矛盾。

## D4. 注释不得声称一个没被修掉的东西

`_exempt` 的 docstring 原本把 `L100 (historical, was 1/128) - but see spec.md L453` 当作 `others` 参数修好的缺陷。实测该行的 `L453` 依然 `historical=True`。

机制：裸 `L100` 前面既没有路径词也没有能力词，**不是 tracked locator**——探针输出里这一行只产出 2 个 site，都是 `L453`。`others` 收集的是「本行其它 locator 的 span」，此处没有其它 locator，于是无从跨越。`_crosses_another_locator` 本身是对称且正确的，不需要改。

**这正是 D4 要防的东西**：一段注释在解释规则时举了一个该规则并不覆盖的例子，读的人（和下一轮的复核者）会以为那个形态已经安全。注释的错误方向和代码的错误方向相反——代码漏修会留下活指针，注释误述会**让残留被当成已修而不再有人管**。

**决定**：docstring 换成真正能触发的例子（marker 在前、`marker ... A ... B`），写明跨越需要「marker 与目标之间**严格**存在另一个 tracked locator」，并明确把 `A (marker) ... B` 记为残留（那种顺序下两者之间什么都没有，判定退回 `EXEMPT_WINDOW` 与句读，与 `others` 无关）。**行为不改，注释改准。**

## D5. 归档件不可变，更正记在新 change

第四份 change 已归档。`5f3e286` 刚刚因为在归档件上追加内容被整体回滚，其提交信息里写明了原则：规则是「不要事后改写归档的散文」，**不开例外**，而当时的辩解正是「我只是追加一段 Errata，没改正文」。**追加同样改变后来者读到的字节。**

所以 B-1（errata 表缺版本列）与 B-2（D5 少枚举一个文件）**不能就地修**，记在本 change。

这也是本仓对「数字必须重算」这条规则的第二次应用：上一份 change 用 D8 立了规则，本 change 是它的第一次执行——**而执行结果是违反了它**。记在这里，而不是把归档件改对。

## 已知残留（不在本 change 修）

1. `A (marker) ... B` 形态：`B` 由 `EXEMPT_WINDOW` 与句读决定，`others` 不参与。已在 `_exempt` docstring 与 `tasks.md` 7.1 记录。
2. `path … prose … L###` 普查召回缺口（43 token，13 覆盖，14 未覆盖全在 `governance/spec.md`，9 指向 gitignored `.audit/`）。
3. `before` 作介词、`original` 关于活文件仍被当作标记。
4. `run_gates.py` 两条工具缺陷（归档后 `validate` 报 ERROR、GBK 控制台 `UnicodeEncodeError`）属并行 session，只报告不碰。
5. spec 侧 A-1 / A-2 / A-3（`wayfinder/spec.md:824` 缺钉住断言、`:253,300` 6 位有效数字、`:824` 百分比），非本 session 造成，各自需要 change。
