# Design

本文件记录 `2026-10-04-archive-evidence-provenance` 的决策。
`proposal.md` 是事实底座（每条带 revision）；本文件只记录**为什么这样做**。

---

## D1 — 归档只读，无例外

事实更正不得落在 `openspec/changes/archive/**`。依据三重：

1. `openspec/specs/governance/spec.md` `req-gov-5` Scenario「Archive copies are not
   retro-edited」:228-232 —— 归档副本 MUST 保持逐字节相同
2. `req-gov-6` obligation 7:288-290 —— retro-editing would falsify that record
3. `5f3e286` 的 commit message 确立**无例外**原则，并点名了被自己否掉的窄读法：
   「Appending still changes the bytes a later reader sees」

**后果**：`incident.md:55/:61` 与 `design.md:163-164` 的文字**都不改**。
本 change 以 `proposal.md` 承载全部更正。

**已发生的两次违反**（登记，非本轮处置）：
`27336a4`（10-03 23:05）与 `e8efa66`（10-04 12:11）。
后者已被 `5f3e286` 回滚；**前者仍留在 HEAD** —— 见 `proposal.md` C 组。

## D2 — `worktree_digest` 是溯源标记，不是拒写闸门

**先定一个决定设计方向的事实**：ledger 写入时刻工作树脏是**合法常态**。
opsx 流程中 ledger 写在 archive 之前、change 的 spec delta 已 apply 但尚未 commit
—— 此时工作树必然脏。

⇒ 故 `--write` **禁止**实现为 quiesced 前置门（「脏即拒绝」）。那样会把合法流程卡死。
`worktree_digest` 只回答「这个条目的基准是什么」，不回答「现在能不能写」。

三态取值：

| 情形 | `worktree_digest` | 语义 |
|---|---|---|
| 写入时工作树**干净** | `null` | 账本内容 ≡ 该 `written_at_head` 的树内容 |
| 写入时工作树**脏** | 摘要串（非空） | **该条目基准是工作树，不是 HEAD** |
| 旧格式账本（无此字段） | 字段缺失 | **基准未知** |

**配方**：`worktree_snapshot()` 已在本文件内提供 `req-gov-8` 定下的两个内容敏感分量 ——
`sha256(git diff HEAD)`（覆盖 staged + unstaged **内容**）与逐文件 untracked bytes 摘要。
直接复用，不新造轮子、不引入新依赖。

**`--verify` 的三态判定**（把 `req-gov-8` 的「『通过』与『不知道』不可混读」延伸到账本层）：

| 账本形态 | 允许的结论 |
|---|---|
| `worktree_digest` = `null` | 可对 `written_at_head` 做 pass / fail 比对 |
| `worktree_digest` 非空 | **仅凭 HEAD 重建基线的比对 MUST 产出 INVALID** —— 不得产出 pass，不得产出 violation |
| 字段缺失（旧格式） | 同上 —— 基准未知，MUST NOT 对 HEAD 做 pass/fail |

这条把 A9 的机制从「读者需要自己发现」变成「工具强制拒绝给出无根据的结论」。

**落盘纪律**：payload 写出 MUST 保持 `newline="\n"`。
现有代码注释已记录：Windows 默认文本模式发 CRLF，会让该文件过不了本仓自己的
`git diff --check`（游离 CR 被读成 trailing whitespace）。

## D3 — 新 Requirement 取 `req-gov-12`，不取 `req-gov-9`

现有 governance Requirement id 为 1–8、10、11。`req-gov-9` 曾被使用后
`## REMOVED`（由 `req-gov-10` 取代，见 `req-gov-6` 记录的 Scenario 标题重写）。

**不得复用 9**，理由是 `req-gov-6` obligation 3（`governance/spec.md:266-271`）：
同一 spec 内 `id` 必须唯一。两个 Requirement 共用 `req-gov-9` 会让所有指向该 id 的
anchor 引用产生歧义 —— 而 anchor 引用正是本仓的寻址方式。

> 首版给出的理由是「账本将无法区分已删除与新增」。复核证明该理由**不是承重墙**：
> 删除路径 `removed_anchors()` 是**按 Requirement 标题**匹配的
> （`run_gates.py` 的 `deliberate` 用 `title in removed_titles`），
> id 复用对删除逻辑基本无害。结论不变，论证换成上述更强的这一条。

Source 反链按 `req-34`（`wayfinder/spec.md`）的 per-capability dispatch：
governance 的 primary 反链 MUST 是 backtick 包裹的 `CLAUDE.md` 引用。

## D4 — lint 的扫描域 scope 到**被归档的 change**（首版判据有误，已修正）

裁决原定扫描 `.audit/**`。**实测该目标无法提供机械闭合**：

- `.gitignore:37` 排除 `.audit`；`git ls-files .audit` = **0 tracked**（本地 82 个文件）
- 对 gitignored 路径设门禁，其结果依赖**未受版本控制的本地状态** ⟹ 违反 `req-gov-8`
- 「pre-change 红 / post-change 绿」对 gitignored 路径**在 git 意义上不可实现**
- 把 `.audit` 确立为门禁对象，等于**制度化 `proposal.md` A10 要修的缺陷本身**

首版据此把扫描目标写成「**受版本控制的**证据层」。**该判据是错的**，两个原因：

1. **它会排除掉被门禁的那个 change 本身。** 被审的 change 在提交前按构造就是
   untracked 的 —— 以版本控制状态为判据，等于用「是否已提交」来筛「是否在审」。
2. **实现里根本没有这个过滤**，只有路径约定。实测后果：`.audit`（0 tracked）因路径
   被排除，而本 change（同样 0 tracked）却被扫描。同一谓词、相反结果 ——
   正是本 change 要消灭的那类「叙述与规则不对账」。

**修正后的判据**（`run_gates.py` 经环境变量 `GATE_CHANGE` 传递）：

| 模式 | 触发 | 扫描范围 |
|---|---|---|
| scoped | `GATE_CHANGE` 已设 | 该 change 的 `proposal.md` / `design.md` / `tasks.md` + `docs/**` |
| repo-wide | `GATE_CHANGE` 未设 | 全部未归档 change + `docs/**` |

这同时满足 `req-gov-7` Scenario:367 —— 「the check MUST be scoped to the change being
archived, **so that unrelated stale changes in the same directory do not determine the
result**」 —— 与 `cmd_gates` 对 `openspec validate` 已有的 scope 做法保持一致。

`.audit` 的排除理由改为**它不属于任何 change**，且永不入库（此理由独立成立）。

**传输机制**：环境变量，**不是位置参数**。另两个 lint（`lint_no_line_pointers`、
`lint_no_source_field_drift`）的 `main(argv)` 把位置参数当作待扫描路径，
传 change 名会让它们去找一个叫该名字的文件。

**仍排除 `openspec/specs/**`**：spec 内的计数由 `req-gov-5` 的溯源义务管
（Scenario :228-232），是另一套机制；混扫会产生重复且不一致的判定。

**`GATE_CHANGE` 指向不存在的 change** 时，lint 打印警告且不报绿 ——
「扫了零个文件并输出 OK」是 `req-gov-7` 的 `all([])` 失效形态，只是换了条路进来。

## D5 — 判别性测试是**合并前置条件**

`scripts/lint_no_line_pointers.py` 的 docstring 自陈了本族为何回归五次：

> The same defect family was "fixed" by hand five times in this repository, each
> pass leaving siblings behind, because **no check could say whether the fix was complete**.

一个从未红过的 lint 无法回答「修复是否完整」。

⇒ 故**本条写入本 change 的硬性验收**：`lint_no_baseline_counts.py`
对 **pre-change** 证据树必须**红**（能检出真实存在的无基准计数），
对 **post-change** 树必须**绿**。二者缺一，本 change 不得归档。

> 注：`lint_no_line_pointers.py` 的 **C4 = Cross-Reference Resolvability**（:216-275
> 一组可解析性测试），**不是**判别性测试。勿去找不存在的「C4 判别性测试」。

## D6 — 豁免走 marker，不走登记表

沿用 `req-gov-6` obligation 6 的历史标记豁免哲学：`pre-this-change`、`histor`、
显式 commit id 等 marker 即豁免，且**豁免面 MUST 可见于文档本身**。

**禁止 exemption registry** —— 那正是 `req-gov-11` 刚防过的
「登记表静默增生」换个名字回来。

## D7 — 召回偏置：宁可多报，勿漏报

沿用 `lint_no_line_pointers.py` C1 的既有立场：

> over-inclusion costs a line of triage, under-inclusion is how this family
> returned five times

故 lint 的默认立场是**高召回**。分诊成本是一行；漏报成本是下一次 audit 的一个 finding。

## D8 — 数值闭式的二分（`CLAUDE.md` §6 第 8 条）

- anchor 计数等**整数闭式**：**bare `==`**
  ❌ 禁止 `pytest.approx(..., abs=0)` —— 其 `rel=1e-12` 默认随量级缩放，
  违背「钉值零容差」意图
- 摘要等**浮点闭式**：`pytest.approx(value, abs=...)`
- 文字断言（「正确」「合理」）**不构成**可验条款
- 每个计数断言 MUST 同时断言**口径**（`block_starts`）并带 **revision**

**本 change 的适用范围**：`req-gov-12` 本身**无任何算式**（治理层，非数学层），
故上述纪律在 spec delta 上无作用对象。它在本 change 中约束的是**测试**里的
整数/字符串闭式，已落为：

| 闭式 | 断言位置 |
|---|---|
| `_EMPTY_SHA256 == sha256(b"")` | `test_empty_sha256_is_the_digest_of_no_input` |
| digest 长度为 64 | `test_ledger_written_on_dirty_worktree_verifies_as_unknown` |
| payload 键集恰为 5 项 | `test_written_payload_carries_exactly_the_five_declared_fields` |
| marker 集合与覆盖集合相等 | `test_marker_set_is_fully_covered_by_the_cases_above` |

> 首版把 D8 写在这里却没有对象，属悬空条款。复核指出后已补上对应闭式，
> D8 从「继承的纪律」变成**本 change 内可验的义务**。

## D9 — 共享工作树与门禁执行

- ❌ 禁用 `git commit --amend`（共享 index 上会改写**他人**的 commit）
- ❌ 禁用 `reset --hard` / `checkout --`
- ✅ 门禁 MUST 跑在 detached worktree（`run_gates.py` 采样 HEAD 与工作树摘要，
  不一致即 `GATE RESULT INVALID` / **exit 2**；主工作树下几乎必然因并行 session 触发）
- ⚠️ **exit 0 与 exit 2 在肉眼上极易混淆**，且 exit 2 时子检查可能全 PASS。
  exit 2 **不是**通过。exit 2 有**两个**成因（工作树在跑动中变化 / 账本无声明基准），
  已写入模块 docstring 的退出码表。

## D10 — `req-gov-12` 的两处内部矛盾（复核发现，已消除）

1. **「MUST record a digest」与「digest MUST be `null`」自相矛盾。** 首版义务 1 要求
   MUST 记录摘要，同一张表又要求净树时该字段 MUST 为 `null`。读者无从判断 `null`
   是「已记录的值」还是「没记」。
   **修正**：`null` 明确定义为**已记录的值**，其含义是「内容**就是**该 base 的内容」；
   并区分三种「没有内容摘要」的情形 —— 空串/异类型（baseline 未知）、字段缺失
   （早于本契约）、以及 `null`（baseline 就是 base）。第 4 种 entry 形态已补进表与测试。
2. **legacy Scenario 的「MUST NOT report a violation on the grounds that the entry is
   malformed」与代码冲突。** 实测：缺 `ledger` 键的文件经 `_load_ledger` 抛
   `ValueError`，被 `main()` 捕获后返回 **EXIT_FAIL**（violation），且被既有测试
   `test_verify_rejects_a_file_that_is_not_a_ledger` 钉死。
   **修正**：该禁止**限定为 anchor 级判定**——它要防的是「缺 baseline 字段被误报成
   锚点漂移」。另加 Scenario 规定：根本不是账本的文件是**调用方错误**，
   且必须让该区别可见，使「你的输入不是账本」永远不被读成「你的锚点漂移了」。

## D11 — 不得在被扫描文件里复述检测器的输出数字

**这是本 change 自身犯过的错，记在这里以免复发。**

首版 `tasks.md` §6.2 写下「lint 报 15 处违规，本 change 自身 0 处」
（该数字**不可复算** —— 它描述的是当时的工作树状态，无任何 git 对象可重建）。
三行后该文件又新增了符合定义的计数（引用 lint 自身的输出与分布）⇒
实际数字与所写不符，而**没有任何东西会报这个不一致**。
独立复核实跑发现，我报告给用户的那句「本 change 自身 0 处」是**假的**。

机制：写入动作**改变了被测量对象**。`tasks.md` 就在 `openspec/changes/<name>/` 下，
而 lint 扫该目录 —— 于是记录 lint 的输出这件事本身制造了新的违规。
（本 change 要消灭的正是这一族：制品声称的事实与工具输出对不上。）

**规则**：任何**位于检测器扫描范围内**的文件，都不得复述该检测器的实时输出数字。
改为**记录产出该数字的命令**，让数字随命令走：

```bash
GATE_CHANGE=<change> uv run python scripts/lint_no_baseline_counts.py
```

这样制品里没有会在自己编辑下失效的数字。
