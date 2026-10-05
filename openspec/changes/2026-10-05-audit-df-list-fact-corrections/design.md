# Design

本文逐条记录 B-1「DF 段」9 条 finding 在 HEAD 的实测结果。裁决口径：`CONFIRMED` / `PARTIALLY_TRUE` / `FALSE`。

**裁决时点**：`5f611b6`（分支 `dev`）。清单原文的基线为 pin 态，两者的差在 D6 单列。

---

## D1 裁决总表

| 条目 | 裁决 | 一句话依据 |
|---|---|---|
| DF-01 | `PARTIALLY_TRUE` | 目录与变异属实，但引用的文件路径不存在，且范围低报数倍 |
| DF-02 | `PARTIALLY_TRUE` | 文件数精确；`.git` 是指针文件而非子树 |
| DF-03 | `PARTIALLY_TRUE` | 两个计数精确；「3 个伴生脚本」含一个编译产物 |
| DF-04 | `PARTIALLY_TRUE` | 字节数与时间戳精确；路径写法错 |
| DF-05 | `PARTIALLY_TRUE` | 溯源缺陷为真；报告行号错，引用的证据文件不存在 |
| DF-06 | `CONFIRMED` | 两条伴生路径的存在性、大小、时间戳全对 |
| DF-07 | `CONFIRMED` | 四类分支残留逐类复现 |
| DF-08 | `FALSE` | 被断言的缺陷已在源头根除，行号与前提均错 |
| DF-09 | `FALSE` | 被断言的实体在 HEAD 不存在且从未入库 |

## D2 DF-01 / DF-02 / DF-03 / DF-04：变异副本

**实测**（`Get-ChildItem -Recurse -File -Force`）：

```
mut1  files=476  mut4 files=476  mut7 files=476
pin6593a06 files=476
```

476 这个数精确。变异经与 pin 逐文件比对确认，三处分别是 `metrics.py`（改为 MUTATION-2 last-step-only reduction）、`sphere.py`（`_cap_radius` 硬编码 `16` 而非 `signature_dim`）、`gating.py`（softmax max-subtraction 改写为保留计算图的均匀 `1/k`）。

**纠正一：清单引用的路径全部不存在。**
`audit/mut1/metrics.py`、`audit/mut4/sphere.py`、`audit/mut7/gating.py` 三者 `Test-Path` 均为 False。真实路径带 `src/decompmoe/` 一层。清单 DF-01 的「位置」字段因此是死锚点。同一错误路径在报告 §11 第 9 条正文中也存在，属继承而非新增。

**纠正二：范围低报。**
审计根下实有 **13 棵**非 pin 的完整仓库副本树（每棵含 `src/decompmoe/`，且 `src/` 树哈希逐个不同于 pin），清单只列 3 棵。按清单清理会剩下 10 棵，其中 `_mut065_a`、`scratch/mut067_a`、`scratch/mut067_b` 同样是 476 文件的完整副本。

**纠正三：这些不是「目录副本」，其中 6 棵是 git worktree 指针。**
`mut1` / `mut4` / `mut7` / `_mut065_a` / `scratch/mut067_a` / `scratch/mut067_b` 的 `.git` 是 57 字节文件，内容 `gitdir: D:/myProject/DecompMoE/.git/worktrees/pin6593a06`；其余 7 棵无 `.git`。**关键区分**：这 6 棵在 `git worktree list` 中**没有注册**（在册的只有 `pin6593a06` 与 `worktree-quiet-forest-039d`）。因此
  - 删除它们不触及 git 注册表，走可恢复删除即可，不需要 `git worktree remove`
  - 反之，**绝不能**在这 6 棵内部执行任何 git 命令——它们的 gitdir 指向 pin 的 admin dir，git 指令会作用在审计基线上

**纠正四：DF-02 的「`.git` 子树」不成立**（见上，`.git` 是指针文件）。

**纠正五：DF-03 的「3 个伴生脚本」含一个 `.pyc`。**
`_mut4_scripts/` 的三个文件是 `probe_calls.json`(359 B)、`probe_plugin.py`(1035 B)、`__pycache__/probe_plugin.cpython-313-pytest-9.1.1.pyc`(2113 B)。手写脚本为 2 个。

**措辞约束**：这 13 棵只比对了 `src/` 树哈希，**未逐棵打开确认携带有意意变异**——从不同 commit 复制的部分拷贝会产生同样的哈希差异信号。因此本 change 的删除理由表述为「审计残留 + 假阴性通道」，**不是**「已确认携带变异」。

## D3 DF-05：报告 §11 第 9 条

**纠正一：行号错。** 清单给 `_final_report_full.md:1652`，实际文本在 **1662** 行；1652 行是无关的 §11 另一条（cache-manifest 142/143 off-by-one）。
> 基线：审计根下的 `_final_report_full.md`，取自审计 pin `6593a06` 对应的运行产物。复现命令 `Select-String -Path <audit>/_final_report_full.md -Pattern 'PreToolUse'`（该串只出现在第 9 条）。该文件位于 `.claude/projects/…/audit`，不在版本控制内，故行号以该次运行的落盘副本为准。

**纠正二：引用的证据文件不存在。** 清单把 `check-completeness.json` 当作验证来源，该文件在审计根下不存在（递归过滤 `*completeness*` 无命中）。

**纠正三：溯源错链为真。** `f_main/063.json`、`065.json`、`067.json` 三者的 `agent` 与 `dimension` 均为 `find:TEST-GUARD`，内容分别是 UR 闭式测试、Voronoi 硬编码表值、`spherical_l2_normalize` 的 eps 默认值——没有一条与变异副本清理相关。对应 verdict 亦如此。**该字段指向错误，引用本条不能凭 `origin_ids` 定位原始证据。**

**纠正四：「4 个 agent」无出处。** 报告 §11 第 9 条自己的括号枚举是 `mutate:1` / `mutate:4` / `mutate:7`，共 3 个。磁盘上另有 `mut066_39982` 与 mut062/065/067/068 系列 scratch 树，但报告正文未引用它们。标题的「4」与正文的「3」不一致，本 change 按正文记 3。
> 基线：同 D3 纠正一，审计 pin `6593a06` 的 `_final_report_full.md`。复现命令 `Select-String -Path <audit>/_final_report_full.md -Pattern 'mutate:1'`。该报告不在版本控制内，行号不可由 git 重建。

## D4 DF-06：伴生脚本

`_mut4_scripts/`（3 文件）与 `_ur_probe_plugin.py`（807 B，时间戳 `2026/10/1 0:18:52`）均存在，大小与时间戳与清单逐字相符。旁证：`probe_plugin.py` 为 1035 B / `0:18:22`，`probe_calls.json` 为 359 B / `0:18:41`，三者同属一次 00:18 的变异会话。

保留二者：它们是变异测试的唯一可复现入口，而副本不是原始证据。

未验证项：未读取也未执行这两个脚本来确认它们确实能重建对应变异。

## D5 DF-08：0.83% 浮点比率（推翻）

**行号错 19 行。** 清单给 `wayfinder/spec.md:382`；382 行是 req-15 的一条 scenario（`WHEN an advisory signal crosses any threshold`）。`0.83` 字符串实际在 **401** 行，所属 Requirement 正确（req-17，anchor 在 397 行）。

> 基线：`openspec/specs/wayfinder/spec.md` @ `92a937a`。复现命令：`Select-String -Path openspec/specs/wayfinder/spec.md -Pattern '0\.83'`（唯一命中即该行）。行号随该文件的编辑移动，但 Requirement 归属由 `<a id="req-17"></a>` 锚点固定。

**实体缺陷已在源头根除。** req-17 正文把该值逐字标为 prior：

> …bring the full extract_C pipeline to `33_168 MACs = 66_336 FLOPs` per the skeleton spec, ~1.22% above the projection-only figure …; the prior `33_040 MACs = 66_080 FLOPs` / `~0.83%` omitted the step-(3) cross-head mean)
> 上引为 `openspec/specs/wayfinder/spec.md` @ `92a937a` 中 req-17 正文的逐字引用，非本 change 的计算结果。两个百分比都是该 spec 的既有文本：`~1.22%` 对应 live 闭式，`~0.83%` 是同句中被显式标注为 prior 的旧值。

live 闭式是 `33_168 MACs = 66_336 FLOPs` / `~1.22%`，且已有守护：`tests/test_extraction.py:283` 的 `pytest.approx(0.001977, abs=1e-6)`、`tests/test_config.py:163` 的 `assert extract_c_flops == 66_336`。finding 写于 pin（`6593a06`，当时 `33_040` 仍是 canonical），change `f6461d7 fix(a2-errata)` 重算了它。清单称「实体缺陷位置未变」不成立——它不是位置漂移，是被从源头消除。

**清单的前提也是假的。** 清单称同组 0.20% 与 0.05% 都有守护、只缺 0.83%：
- 0.20% —— 确有守护（`tests/test_config.py:130-131`）
- 0.05% —— **不存在**，且该数值已从 live spec 移除；它连同其测试被 `f6461d7` **故意删除**（`0.0005 → 0.004360`，测试改名 `test_flops_routing_cross_req_net_delta_32` → `..._288`，见 `2026-10-02-audit-a2-errata-and-spec-math-fixes/tasks.md:32`）。清单断言存在的那个守护被删了。

**提交归因方向相反。** 清单称 `33f7cc9` 造成 +1 位移。`33f7cc9` 存在（`33f7cc9ae181abb03b44f8d0ba9368c0d6a29963`，2026-09-30），但它是 `git log -- openspec/specs/wayfinder/spec.md` 里**最老**的一个。该行在 `33f7cc9` 处为 382、在 `f6461d7` 处为 381、在 HEAD 为 400/401。`33f7cc9` 之后的净位移不是 +1。`+1` 是 `rv:main18:source` 描述的 pin 窗口 `7bf77af..6593a06` 内的性质，被清单复述成了当前文件的属性。

## D6 根因：pin 漂移

`_pin_drift.json` 的 `head` 为 `188b9fb`，落后实测 HEAD。这张表本身也是 pin 态产物，**不能**当作「当前无漂移」的证据——它恰好错过了根除 DF-08 的 `f6461d7`。

`STILL_REAL` / `MOVED` / `unchanged-since-pin` / `unverifiable (no pin line)` 这类裁决只在 pin 那一刻成立。据此，本 change 的每一条裁决都重新在 HEAD 实测，不继承清单的 verdict 字段。

## D7 DF-07：分支与 worktree

四类残留逐类复现：

| 类别 | 分支 | 实测 |
|---|---|---|
| 孤儿 ×2 | `worktree-agent-aaca167863d597599`、`worktree-agent-ae19e963fe5074bcf` | 均停在 `051f247 Initial commit`；`git worktree list` 无登记 |
| 已合未删 | `feat/auto-20260904-b6fca17d` @ `d52f8be` | `git branch --merged dev` 列出 |
| 已合 + worktree 在册 | `worktree/quiet-forest-039d` @ `d52f8be` | 已合 dev；worktree 注册在 `C:/Users/LamKo/.herdr/worktrees/DecompMoE/worktree-quiet-forest-039d` |

锚点 `CLAUDE.md:52` 与 `f_main/015.json`（W1-GIT-05）的 `file=CLAUDE.md line=52` 相符。

**该 worktree 的 123 条 modified 是纯行尾差异。** `git diff --stat` 报 15336 增 / 15336 删，覆盖 123 个文件（含 LICENSE、pyproject.toml、全部 `src/`、全部 `tests/`）；而 `git diff --stat --ignore-cr-at-eol` 输出为**空**。最新 mtime 停在 `2026/9/4 16:26:08`。即 CRLF 翻转，无一行实质内容。**该分支的 worktree 可安全移除**。

清单的 `suggested_fix` 是 `git worktree remove <quiet-forest-039d>`。执行顺序必须先 remove worktree 再 `git branch -d`：git 会拒绝删除正被 worktree 检出的分支，而该 `suggested_fix` 同时列了这两步，顺序不定会失败。

两个孤儿分支停在 `051f247`，与 `dev` **无共同祖先**（`git merge-base main dev` 退出非零），故 `git branch -d` 必然因未合入而拒绝，须用 `-D`。这是预期行为而非遗漏合入，需在提交信息中记明。

范围更正：`review/fix-math-consistency-audit-2026-08`（`532f853`）同样在 `git branch --merged dev` 列表中且未删除，属同类「已合未删」，但它已推 origin，删除影响远端，本轮不处理。

## D8 DF-09：`_staged/`（推翻）

- `Test-Path D:\myProject\DecompMoE\_staged` → False
- `git log --all --oneline -- '_staged'` → 空；`git ls-files '_staged'` → 空。**从未入库**
- `git ls-files --others --exclude-standard` 中过滤 `spec\.md` → **0 命中**

即清单断言的「含 spec.md 完整重复副本」这一后果不成立：未跟踪文件里没有任何 `spec.md` 副本，单一真相源风险已消失。

**清单自身数字也已漂移。** 报告称 31 个未跟踪垃圾文件 / 751,813 字节；实测 48 个 / 177,011 字节（取样于写 `.gitignore` 之前）。
> 两组数字的基线互不相同，不可混用：报告侧取自审计 pin `6593a06` 的运行产物 `<audit>/_final_report_full.md`（不在版本控制内）；实测侧为仓库 @ `5f611b6`，命令 `git ls-files --others --exclude-standard` 可重算，并在本 change 的 `.gitignore` 提交 `92a937a` 落地后归零。差额是时间推移，不是任一侧的计量错误。

**残留部分仍然成立**：仓库根下确有大量未跟踪 scratch 文件且 `.gitignore` 无任何模式覆盖它们。结合 CLAUDE.md §3.1 记录的日常命令是无差别的 `git add .`，一次常规提交就会把它们扫进版本控制。`tasks.md` 为此补 root-anchored 模式。

## D9 结构性发现：校正轨迹两头都不在版本控制

本条不在 DF 清单内，是本轮实测新发现：

- 记录 A-1 校正的 `.audit/.../lists/opsx-changes.md`（含 5 段 `## Errata`）被 `.gitignore:37` 的 `.audit` 覆盖 → 从未入库
- 执行并自归档该校正的 change `2026-10-01-audit-errata-a1-numeric-guard-list` 位于 `openspec/changes/archive/`，**不在** ignore 范围，却从未 commit

即：校正的「记录」被忽略，校正的「过程」未入库。这也是本 change 存在的原因——把校正放进会入库的位置，而不是只写回被忽略的目录。

该 change 已于本 change 之前单独补录（`00ed706`），其 26 项 task 全部完成、`.openspec.yaml` 声明 `skip_specs: true` 故无 delta 子目录，符合该类变更的形态。anchor 未受损：三条 live spec 的 anchor 计数在补录前后一致。
