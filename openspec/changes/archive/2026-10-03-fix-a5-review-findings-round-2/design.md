# Design

## D1 — 快照按内容哈希，不按 porcelain 摘要（AC-19 的 CRITICAL 缺口）

**决策**：`worktree_snapshot` 返回三个分量，各自失效理由不同：

| 分量 | 内容 | 抓什么 |
|------|------|--------|
| `head` | `git rev-parse HEAD` | 并发 commit 落库，基线移动而工作树内容可能未变 |
| `tracked_digest` | `sha256(git diff HEAD)` | **已脏文件被再次编辑**——porcelain 对此完全失明 |
| `untracked_digest` | `git ls-files --others --exclude-standard` 逐文件内容哈希 | 未跟踪目录内新增文件（porcelain 默认把目录折叠成一行） |

`status_lines` 保留但**不参与判等**。

**理由**：`git status --porcelain` 编码的是**路径 + 状态字母**，不是内容。自建 repo
实测：`b.py` 已脏、内容 A 时摘要 `97c0d2fd…`，改成完全不同的内容 B 后摘要**仍是**
`97c0d2fd…`。于是 exit-2 检测在「并发 Edit 一个已脏文件」时静默失效——而交付时刻
工作树有 48 个脏条目，这恰恰是最常见形态。`--porcelain` 还会把未跟踪**目录**折叠成
一行（需要 `-uall`），目录内新增文件不改变输出。

**为什么 `status_lines` 不能当第四个信号**：它是同一 porcelain 串的**更粗函数**
（条目数），把它计入等于声称两个派生自同一来源的量互相独立。docstring 里原来把它
列为「三个彼此独立的分量之一」是过度声称。现在它只在 INVALID 输出里供人参考。

**测试**：`test_porcelain_digest_collides_which_is_why_content_is_hashed`、
`test_tracked_digest_detects_content_change_in_already_dirty_file`、
`test_untracked_digest_detects_new_file_inside_untracked_dir`。

## D2 — D4 的前提经实测为假，因此 `req-gov-9` 整体 REMOVE 并以 `req-gov-10` 重写

**被推翻的前提**（原 D4）：「`anchors == headings` 显然成立，所以点态覆盖检查在缺
anchor 时仍为绿，只靠账本对比才能指名哪一个 Requirement 丢了 anchor」。

**实测**：删掉 `governance/spec.md` 的 `<a id="req-gov-7"></a>` 一行后，9 个
Requirement heading 对 8 个 anchor，**点态检查报红**。AC-19 自己给的 36→35 就是计数
下降的证据。

**本轮又穷举了六种形态**（`tests/test_run_gates.py`）：

| 形态 | H | A | 点态检查 |
|------|---|---|---------|
| 单独吞一个 anchor | 2 | 1 | 红（1 uncovered） |
| 新增带 anchor + 吞一个 | 3 | 2 | 红 |
| 新增带块级子 anchor + 吞一个 | 3 | 2 | 红 |
| 删除一个 Requirement + 吞一个 | 2 | 1 | 红 |
| anchor 被 **retarget**（id 仍在，标题换了） | 2 | 2 | **绿** |
| 两个 heading 共用一个 id | 2 | 2 | 红（duplicate 分支） |

**算术**：`H - A` 只因吞而**增大**；新增 Requirement 自带 anchor，`H` 与 `A` 同增，
无法抵消。所以任何正常归档操作序列都会留下非零缺额。

**过程中的一次自我翻车（记下来，因为它有教学价值）**：中途我以为「新增可掩蔽」成立，
并写成了测试 `test_swallow_is_masked_when_the_archive_also_adds_a_requirement`——
**测试把它直接判负**。若当时没有构造这个反例而是照直觉写进 spec，真相源会多出一条
比原假断言更隐蔽的错误断言。现在该反例以
`test_a_swallow_cannot_be_masked_by_simultaneous_additions` 的形式留在套件里，作为
D2 修正所依赖的否定式断言。

**账本真正多出来的东西**（`req-gov-10` 现在写的是这些，不是「抓不到」）：

1. **指名**——点态只给每 capability 一个缺额数字，不给 anchor id、不给 Requirement 标题；
2. **retarget 检测**——id 存活但引入的是另一个标题，计数相等 ⇒ 静默绿（上表第 5 行）；
3. **`lost` / `never_added` 分列**——只给净计数不足以区分二者。

**为什么必须 REMOVE + ADD 而不是就地改 Scenario**：`MODIFIED` 块必须逐字保留现存
`#### Scenario:` 标题，否则 archive 拒绝（"omits scenario(s) the current spec still
has"）。而 `req-gov-9` 的标题本身就是错的那一半
（"Point-in-time coverage cannot detect the archive defect"），保留它会让 spec 自相
矛盾。故 `## REMOVED Requirements` + `## ADDED Requirements` 以 `req-gov-10` 重写，
并同步更新 `CLAUDE.md` §3 与 `scripts/run_gates.py` docstring 中的引用。

## D3 — evidence 工具按内容定位，不按深度（重新引入的 MAJOR 缺陷）

**决策**：新增 `evidence/_paths.py` 作为唯一定位事实源；两个脚本改为
`find_repo_root()`（向上找含 `openspec/specs` 的目录）+ `find_change_dir()`（live 与
archive 两处都查）；归档后运行时以 **exit 2** 说明状态不匹配。

**被推翻的做法**：`REPO = Path(__file__).resolve().parents[4]`

```
归档前  evidence/gen_deltas.py   [0]=evidence [1]=<name> [2]=changes  [3]=openspec [4]=REPO  ✓
归档后  archive/<name>/evidence  [0]=evidence [1]=<name> [2]=archive  [3]=changes  [4]=openspec ✗
```

归档后解析成 `openspec/`，实测 `FileNotFoundError: openspec\openspec\specs\wayfinder\spec.md`。

**这是同一仓库第二次犯**。父 commit `1612778` 的标题正是「make the evidence tools
survive archiving」——本 change 修好了它，随后的重写又带了回来。**交付证据的 commit
让证据不可复现**，比没有证据更糟：它看起来是可复现的。

**为什么不能换一个 N**：`parents[N]` 的深度在归档前后**按构造就不同**，且 change 目录
会移动。改深度索引只能修好其中一种状态。

**为什么加 preflight**：路径修好后重跑会得到 4 条红——3 条 `anchor collision` 加
1 条 Scenario `8 -> 8`（工具要求 `live + 1`）。这些红**读起来像证据损坏**，而实际是
状态不匹配。`refuse_if_archived` 以 exit 2（不是 1）报出，并说明原因。exit 1 在本仓
是「检查失败」，复用它会让调用方把用法错误读成证据损坏。

**测试**：`tests/test_a5_evidence_paths.py` 11 项，含
`test_depth_index_approach_is_wrong_in_the_archived_layout`——把原缺陷**可执行地**
钉住，而不是只在新代码上断言通过。

## D4 — 20 个缺失 Source 字段：登记豁免，不造 lineage

**决策**：新增检查 ④（存在性）+ `SOURCE_EXEMPTIONS` 登记表（20 条 `(capability,
anchor_id)` 对，由实测生成而非手打）+ 陈旧条目双向检查。

**实测**：`decompmoe-skeleton` 19/23 缺、`wayfinder` 1/36 缺（`req-34`）、`governance`
0/9 缺，合计 20。上一轮只记了 `req-34`，量级低估 19 倍。

**为什么登记而不补写**：正确填写需要逐条考证每个 Requirement 的设计血缘。**造 lineage
比缺口更糟**——它会满足检查 ①a 而指向虚无。登记表的语义是「已承认的缺口」，不是
「已满足的要求」。

**登记表必须会死**（否则绿灯不再说明任何事）：

- 不在登记表内且无字段 ⇒ 违规（**任何新写的 Requirement 立即红**）；
- 条目指向已不存在的 Requirement ⇒ 违规；
- 条目指向的 Requirement **已补上字段** ⇒ 违规（必须剪枝）。

**粒度是 `(capability, anchor_id)` 而非裸 id**：裸 id 登记表会让新 capability 的
`req-1` 静默通过，与 AC-81 的前缀绕过是同一类漏洞。有测试专门守这一点。

**`check_registry_stale` 与 `check_source_presence` 必须分开**：「条目指向的
Requirement 是否还存在」只在**整份 capability spec** 上可判。合进单文件检查后，任何
针对单文件的调用都会把该 capability 的其余条目全报成 stale——这正是第一版实现被
自己新写的测试判负的地方。

## D5 — AC-81：`SOURCE_LINE_RE` 放宽，`body` 必须按 match 结束偏移切片

**决策**：`SOURCE_LINE_RE` 从 `^\*\*Source:\*\*` 改为
`^[\s>]*(?:\d+\.\s*)?\*\*Source:\*\*`；`body` 从 `line[len("**Source:**"):]` 改为
`line[m.end():]`。

**为什么现在能改**：D7 当初延后的唯一理由是 `wayfinder/spec.md` 里那行
`> **Source:**`（`req-19` 内对 `req-20` Source 字段的逐字引用副本）会被新正则判违规。
该行已随 `req-36` 被并行 change REMOVE。**实测放宽后新增可见行数 = 0**（strict 48 /
loose 48），即这次修改关闭了一个绕过而没有引入任何违规。

**为什么两处必须一起改**（这是本次最容易漏的耦合）：`body` 原先按**定长** 10 切片。
只放宽正则而不改切片，`> **Source:** …` 会被从行首切掉 10 字符，得到 body
`ource:** …`，然后因**错误的原因**违反每一条检查。`test_source_body_is_sliced_at_the_match_end_not_a_fixed_length`
对每种前缀直接断言「body 必须以反链开头」，把这个不变量本身钉住，而不是只断言症状。

## D6 — 校验脚本的断言要结构化，不要子串化

`verify_deltas.py` 第一版有四条**假红**，全部是断言比被测物粗：

1. `"**Reason**:" not in removed`——`removed` 是**列表**，`in` 测的是元素相等，不是
   子串。带 Reason 的块也会通过这条检查。**假绿**。
2. `assert token not in delta`——替换文本**故意复用**了 `git status --porcelain` 这个
   短语来解释它为何不足。
3. 同上，`... no longer exists.` 是新句的**前缀**，按设计仍在。
4. ADDED anchor 碰撞检查把 MODIFIED 块的 anchor 也算进去——MODIFIED 按构造就会重发
   活体 anchor，必然碰撞。

**改法**：从「子串在不在」换成**结构比对**——delta 块必须是活体块 + 7 行追加 + 恰好
2 行就地替换，逐位置比对。子串测试无法区分「被编辑」与「被复用」，序列比对可以。

另外，生成器自己的 `text.count("### Requirement:")` 也踩了同一个坑：它把 Scenario
散文里反引号内的 `` `### Requirement:` `` 也数进去，虚增 2。计数断言改成 `^` 行首锚定。

## D7 — 记下来的东西必须带观测 revision

review 指出我关于 `> **Source:**` 的论证「是捏造的」。复核结论：**理由当时为真**，
但我没记下观测对象是哪一��� commit，于是后来者无法区分「当时为真」与「凭空编造」。

实测：`1526b98`（我做决定时的 HEAD）该行 1 命中（L908）；`940b27c` / `ea802c8` /
`HEAD` 均 NONE——被并行 change 连同 `req-36` 逐字副本移除。

**规则**：任何「我查过，X 不存在 / X 存在」的说法，必须同时记下 commit。缺陷会在
并行 session 手里消失，而没有 revision 的记录无法被追认或推翻。

## D8 — 归档暴露了本工具自身的新缺陷：有意 REMOVE 的 anchor 被报成 LOST

**发现时机**：归档**本 change 自身**时。`anchor-ledger --verify` 输出：

```
anchor-ledger: 1 LOST anchor(s) — restore surgically, do NOT re-run archive:
  lost          governance: req-gov-9 (Spec Anchor Ledger Across Archive)
anchor-ledger: 1 NEVER-ADDED anchor(s) — declared by the change but absent:
  never-added   req-gov-10
```

**两条里只有一条是真的**。`req-gov-9` 是本 change 的 `## REMOVED Requirements`
**有意删除**的，archive 做得完全正确；而 `req-gov-10` 才是真正被吞的那个 anchor
（第四次复现该缺陷，正文落地、`<a>` 被吞，已按协议手术式补回，**未重跑 archive**）。

**为什么必须修**：协议自己的指令是「手术式补回，**不要**重跑 archive」。若被刻意
删除的 anchor 永远报 LOST，这条指令就**不可执行**——补回一个已被删除的
Requirement 的 anchor 本身是错的。而且一个在每个「带删除的 change」上都误报的信号，
训练出来的读者反应是忽略它。

**修法**：新增 `removed_anchors(change_name)`，从 change 自己的 delta 的
`## REMOVED Requirements` 块取 `### Requirement:` 标题，再用标题去**基线账本**里
找对应 anchor id。不能直接把 delta 里的 id 传给 `--verify`——那是循环论证：账本的
职责是报告 archive **实际做了什么**，不是复述 delta **要求做什么**。

**实现中踩到的两个坑（都被自己的测试抓住）**：

1. `deliberate` 最初是**扁平 id 集合**，于是 `before[cap][aid]` 在另一 capability
   下抛 `KeyError`——anchor id 是 per-capability 的。改为 `(capability, id)` 二元组，
   并加 `test_removed_anchor_lookup_is_scoped_per_capability` 钉住：同名 id 在
   governance 里被有意删除，在 wayfinder 里没有，两者的处置必须不同。
2. 修法最容易出的错是**过度过滤**——若把排除条件写成「本次 change 有 REMOVED 块时
   放行所有缺失项」，真实丢失就被静默吞掉。`test_genuine_loss_is_still_reported_when_a_removal_is_also_declared`
   强制两类同时出现：既报 `lost req-c`，也披露 `removed req-a`，且 `req-a` 不得
   出现在 `lost` 列表里。

**为什么归档能当自测环境**：这个缺陷在 3 项合成测试里写不出来，因为「archive 删掉一个
Requirement」这件事本身只有真的跑一次 archive 才发生。协议的价值就在这里——它把工具
放进了工具自己声称能处理的状态。
