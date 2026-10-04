# 清单 B：可直接修的条目

> 本文件由 `D:/myProject/DecompMoE/.audit/wayfinder-opsx-code-review/_work/classified.json` 的 `direct-fix`（9 条）与 `user-decision`（6 条）两个桶搬运而成，共 15 条。
> 本轮为**纯整理**：未重新判断任何 finding 的对错，未重算任何数学，未复核 pin→HEAD 漂移的事实。
> 本文件**只做定位与问题分析**，不含任何修复方案（无替换文本、无新函数/参数/常量名、无步骤序列、无祈使修法）。

---

## 本文件的读法

这一层收录的是**不需要新的数学或语义裁决**就能落地的条目。它们在整份审计里处在两个极端的交界处：

- **DF 段（可直接修）**——缺陷是**二值的**：磁盘上有不该有的东西、断言缺失、分支拓扑与规范文字不符。要不要处理没有争议，争议只可能在「谁来处理、什么时候处理」。这批条目不需要开 OpenSpec change，不需要新的 Decision 记录。
- **UD 段（用户裁决）**——缺陷是**规范层面的空洞**：规范自己留了未定义处、分支拓扑与规范文字不符、治理条款与非约束制品的义务互相拉扯。这类条目**无法靠「直接修」消解**，因为改哪一边、改成什么，本身就是需要人来拍板的语义选择。把它们和 DF 段放在一起，是为了明确区分「可以直接动手」与「必须先有人决定」。

阅读时的两条纪律：

1. **所有 file:line 都是 pin 态（6593a06）的行号**。仓库 HEAD 已是 188b9fb，pin 之后又落了 9 个 commit，改动了 8 个 src/tests 文件与全部 3 份 spec。本文件不重新定位，因此行号在 HEAD 上很可能已漂移。基线状态一律按 `_pin_drift.json` 机械查表：条目所在文件的该行若落在 `drift` 区间内记 `touched-since-pin`，否则记 `unchanged-since-pin`。**这个标签只描述「pin 之后该行有没有被动过」，不构成「已修复」或「仍存在」的断言。**
2. **本文件不重复论证**。每条的「问题」是既有裁决的搬运与压缩，权威全文在 `_final_report_full.md`（§1 L11 / §2 L23 / §3 L76 / §4 L1255 / §5 L1379 / §6 L1412 / §7 L1511 / §8 L1537 / §9 L1565 / §10 L1606 / §11 L1647）与各 finding 原文（`_all108.txt`、`f_main/000..080.json`、`f_gap/000..026.json`）。真相源优先级沿用既有结论：`openspec/specs/**/spec.md` > `openspec/changes/archive/` > `wayfinder/map.md` + 23 tickets（advisory）> 代码层。

### 基线查表结果总览

15 条**全部**为 `unchanged-since-pin`。逐条查表依据：

| 条目 | 所在文件 | pin 态行 | 查表结果 |
|---|---|---|---|
| DF-08 | `openspec/specs/wayfinder/spec.md` | 382 | drift 区间为 130/146/155-157/246/318/329-330/334/586/642/677/737，**L382 不在其中** |
| UD-05 | `src/decompmoe/schedule.py` | 171 | `schedule.py` 整文件不在 drift 表中 |
| DF-07 / UD-01 / UD-02 / UD-04 | `CLAUDE.md` | 51 / 52 | `CLAUDE.md` 不在 drift 表中 |
| DF-09 | `.gitignore` | 37 | 不在 drift 表中 |
| DF-01…DF-06、UD-03、UD-06 | 审计工作区 / 仓库外路径 / 未进入 dev 的分支 | — | 不在仓库树内，drift 表按仓库文件生成，故不覆盖 |

---

## B-1　DF 段：可直接修的条目

### DF-01 — 三个变异源码副本因 hook 阻塞未清理，至今仍在磁盘上

- **位置**：`audit/mut1/metrics.py:0`（pin 态；`line=0` 为占位，该路径在仓库之外，不受 pin 漂移影响）
- **Requirement / 归属**：无 Requirement 归属；对应报告 §11 第 9 条
- **问题**：变异测试的 mutate:1 / mutate:4 / mutate:7 三个 agent 在收尾删除自建的变异源码副本时，被 Fact-Forcing Gate 的 PreToolUse hook 阻塞，删除动作未执行。三个目录此刻仍在磁盘上，各含一份完整的仓库副本（apply-checklist.md、CLAUDE.md、docs、src、tests、openspec、wayfinder、scripts 等）。其中 `mut1/metrics.py`、`mut4/sphere.py`、`mut7/gating.py` 带变异。副本本身是惰性的（`audit/pin6593a06` 经 SHA-256 复核未变），但在这三个目录里跑 pytest 会得到错误结果——这是一条**假阴性通道**：任何后续的 pytest 运行都可能读到变异源码而得出「缺陷已修」的相反结论。
- **证据**：报告 §11 第 9 条（`_final_report_full.md` L1647 起）；`_exec_summary.txt` 末段；三个目录的 ls 实测
- **严重性**：MAJOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin

### DF-02 — 报告 §11.2 的变异副本目录 mut1 仍存在于磁盘，含 476 个文件

- **位置**：`C:/Users/LamKo/.claude/projects/D--myProject-DecompMoE/a553f54e-8635-46b2-a435-55d871698d88/audit/mut1:0`（pin 态；目录级定位，`line=0` 为占位）
- **Requirement / 归属**：无 Requirement 归属；报告 §11.2 第 9 条（mutate:1）
- **问题**：报告 §11.2 第 9 条记录 mutate:1 的清理步骤被 hook 阻塞，遗留的变异源码副本在磁盘上。目录内 `mut1/src/decompmoe/metrics.py` 是报告点名的带变异文件，完整副本含 `.git` / `.codegraph` / `.pytest_cache` / `.claude` 子树。路径在仓库之外，因此不落入 `_pin_drift.json`，基线状态只能记 unchanged-since-pin——**漂移表对仓库外路径无覆盖能力，这是机械查表的结构性盲区，不是该目录已稳定的证据。**
- **证据**：报告 §11.2 第 9 条；`ls` / `find` 于 `audit/mut1`
- **严重性**：MEDIUM ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin

### DF-03 — 变异副本目录 mut4 仍存在，含 476 个文件与 3 个伴生脚本

- **位置**：`.../audit/mut4:0`（pin 态；目录级定位）
- **Requirement / 归属**：无 Requirement 归属；报告 §11.2 第 9 条（mutate:4）
- **问题**：报告 §11.2 第 9 条记录 mutate:4 的清理被 hook 阻塞。目录内 `mut4/src/decompmoe/sphere.py` 为报告点名的带变异文件。同一 agent 另建的伴生脚本目录 `_mut4_scripts`（3 个文件）二者均未清理——**同一次阻塞留下了两类残留（副本 + 伴生脚本），而清理门禁只对其中一类生效过一次。**
- **证据**：报告 §11.2 第 9 条；`ls` / `find` 于 `audit/mut4` 与 `audit/_mut4_scripts`
- **严重性**：MEDIUM ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin

### DF-04 — 变异副本目录 mut7 仍存在，含 476 个文件与伴生探针脚本

- **位置**：`.../audit/mut7:0`（pin 态；目录级定位）
- **Requirement / 归属**：无 Requirement 归属；报告 §11.2 第 9 条（mutate:7）
- **问题**：报告 §11.2 第 9 条记录 mutate:7 的清理被 hook 阻塞。目录内 `mut7/src/decompmoe/gating.py` 为报告点名的带变异文件。同一 agent 另建的伴生探针脚本 `_ur_probe_plugin.py`（807 字节）也在。报告已指出：若后续有人在这些目录里跑 pytest 会得到错误结果。mut7 的特殊性在于被变异的 `gating.py` 直接参与门禁逻辑——在副本目录里跑出来的门禁相关测试结果，其可信度是负的。
- **证据**：报告 §11.2 第 9 条；`ls` / `find` 于 `audit/mut7`；`ls` 于 `audit/_ur_probe_plugin.py`
- **严重性**：MEDIUM ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin

### DF-05 — 4 个 agent 的变异源码副本未能清理，仍在磁盘上

- **位置**：`_final_report_full.md:1652`（pin 态；报告文本自身的行号，不在仓库漂移表内）
- **Requirement / 归属**：无 Requirement 归属；报告 §11 第 9 条
- **问题**：这条与 DF-01…DF-04 描述的是**同一个实体**——报告 §11 第 9 条本身的一段文字，只是从「报告文本」这一层做的记录。三个目录（`audit/mut1/`、`audit/mut4/`、`audit/mut7/`）经 SHA-256 复核 pin6593a06 未变故为惰性，其中 `mut1/metrics.py`、`mut4/sphere.py`、`mut7/gating.py` 带变异。把它单列出来的意义在于：**报告 §11 第 9 条这段文字本身就是问题的一部分**——它是审计报告里少数「结论正确但动作未落地」的位置，读者若只读报告正文会以为清理已完成。
- **证据**：报告 §11 第 9 条
- **严重性**：MEDIUM ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin
- **溯源缺陷（来自 `check-completeness.json` content_accuracy_flags）**：本条 `origin_ids` 写的是 `rv:main63:source` / `rv:main65:source` / `rv:main67:source`，这三个键指向 test-guard 类 finding，与本条内容无关。**该字段的溯源指错，引用本条时不能凭 origin_ids 定位原始证据。**

### DF-06 — 三个变异副本的伴生脚本目录 _mut4_scripts 与探针脚本 _ur_probe_plugin.py 均在磁盘上

- **位置**：`.../audit/_mut4_scripts:0`（pin 态；目录级定位）
- **Requirement / 归属**：无 Requirement 归属；报告 §11.2 第 9 条
- **问题**：报告 §11.2 第 9 条在列举被阻塞的清理时，除三个 mut 目录外还点名了两个伴生路径：mutate:4 的 `_mut4_scripts/` 与 mutate:7 的 `_ur_probe_plugin.py`。两者均仍存在（前者 3 个文件，后者 807 字节，时间戳 Oct 1 00:18）。这两处与 DF-02…DF-04 同属同一批未清理的审计自建制品，区别在于**它们不是完整仓库副本，因此不会被误认为「另一个 checkout」而天然低优先级，但在溯源上它们是变异测试的唯一可复现入口——副本没了，伴生脚本还在，两者都不是原始证据。**
- **证据**：报告 §11.2 第 9 条；`ls` 于 `audit/_mut4_scripts` 与 `audit/_ur_probe_plugin.py`
- **严重性**：MINOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin

### DF-07 — 4 个陈旧分支与一个未清理的 worktree 注册

- **位置**：`CLAUDE.md:52`（pin 态；对应 §4 分支收尾约定那一段的行号锚点）
- **Requirement / 归属**：`CLAUDE.md §4` 分支收尾约定；报告 §10 Batch D-2 git 卫生
- **问题**：两个 `worktree-agent-*` 分支停在 main 的空根 commit 且无对应 worktree 登记（孤儿分支）；一个 feat 分支已完全合入 dev 却未删除；另一个 worktree 分支已合并且其 worktree 仍注册在仓库外的目录里未 prune。这四类残留的共同后果是：**`git branch -a -vv` 给出的分支清单与实际状态脱节**，而分支拓扑正是本仓库两项硬约束（`main`/`release` 只接受 `dev` 的 `--no-ff`、dev 必须线性）的判读依据。清单失真会直接污染后续每一次「dev 是否有 merge commit」「某分支是否已合入」的判断。
- **证据**：`f_main/015.json`（W1-GIT-05）；`_handoff_verdicts_all.json` key=`rv:main15:source`（STILL_REAL）；报告 §10 Batch D-2 git 卫生
- **严重性**：MINOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin

### DF-08 — req-17 的 0.83% 浮点比率 claim 在 tests 全目录无对账

- **位置**：`openspec/specs/wayfinder/spec.md:382`（pin 态）
- **Requirement 归属**：wayfinder req-17
- **问题**：req-17 的浮点闭式 claim「~0.83%」（66_080 相对 65_536 的增幅）在 `tests/` 全目录无任何断言守护，**是该组 FLOPs 比率 claim 中唯一未被 `pytest.approx` 直接对账的一个**——同段的 0.20% / 0.05% 都有守护。数学依据：0.83% 是含除法的实数闭式，属于 CLAUDE.md §6 第 8 条与 governance req-gov-1 义务 2 明确要求对账的类型；同组另两个比率已对账，使这一条成为**组内不一致的例外而非全组缺漏**，这类例外最难被「整组都有」的心智模型发现。该 finding 的行号被 33f7cc9 的 +1 位移冲掉，实体缺陷位置未变。
- **证据**：finding main18 [FLOPs-GUARD-01]（`rv:main18:source`，verdict=MOVED）；报告 §2.2 第 3 类 MOVED 说明
- **严重性**：MINOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin
- **⚠ 桶冲突（来自 `check-completeness.json` bucket_conflicts #2，严重性：中）**：本条 locus 是 `openspec/specs/wayfinder/spec.md`，而 `classified.json` 自身的分桶规则写明「凡涉及 spec / governance spec / ticket annotation / change 制品 / archive 流程 / 门禁脚本的取 opsx-change」。按该规则本条应落 opsx-change。**本文件按 classified 的原判定收录，但它在执行口径上与报告 §10 Batch D-1 存在缺口：Batch D-1 批的是 opensx change 路径，而本条落 direct-fix，两条路径的清单各自看不到对方。** 另：同一 locus（`wayfinder/spec.md:382`）还有 opsx-change 侧的 W02（main42：33_040 漏算第 (3) 步 128 MACs），两者是**不同实体、不同问题**，按 classified 的合并规则不合并是正确的，但同处一行会让按行号检索的人误以为已覆盖。

### DF-09 — 未跟踪的 _staged/ 含 wayfinder spec.md 重复副本

- **位置**：`.gitignore:37`（pin 态）
- **Requirement 归属**：涉及 `openspec/specs/wayfinder/spec.md` 的真相源唯一性
- **问题**：一批未跟踪垃圾文件均未被 `.gitignore` 覆盖，其中 `_staged/` 目录含 `openspec/specs/governance/spec.md` 与 `openspec/specs/wayfinder/spec.md` 的**完整重复副本**。数学/逻辑依据：CLAUDE.md §3.1 记录的日常提交命令是无差别的 `git add .`，因此「未跟踪 + 该工作流」这一组合意味着一次常规提交就会把 wayfinder spec 的两个副本一起纳入版本控制。真相源层级一旦出现两个内容不同的同名 spec，§2 的优先级裁决（spec > archive > wayfinder > 代码）就失去唯一性——**读者无法从文件本身分辨哪一份是真相源。** 复验镜只判 PARTIALLY_REAL（HEAD 态的 `_staged/` 内容与 spec 有差异且已过期），但那说的是副本内容的漂移，不是这条组合本身的结构性风险。
- **证据**：finding main13 [W1-GIT-03]（`rv:main13:math`=UNVERIFIABLE，`rv:main13:source`=STILL_REAL MINOR）
- **严重性**：MINOR ｜ **裁决**：PARTIALLY_REAL ｜ **基线**：unchanged-since-pin
- **⚠ 桶冲突（来自 `check-completeness.json` bucket_conflicts #6/#7，严重性：低）**：报告 §10 Batch D-2 把 main13 放进 opensx change 批次，classified 落 direct-fix。**同一问题在两处口径下分属不同执行路径，任一路径单独执行都会漏掉另一半。**

---

## B-2　UD 段：需要用户裁决的条目

> 这一段的共同特征：缺陷不是「某处写错了」，而是「规范没有定义 / 规范两处互相矛盾 / 规范的前提在仓库中不成立」。改哪一边、改成什么是语义选择，不是实现细节。

### UD-01 — main 与 dev 无共同祖先，dev → main --no-ff 当前不可执行

- **位置**：`CLAUDE.md:51`（pin 态；对应 §4 分支架构表 main 行）
- **Requirement 归属**：`CLAUDE.md §4` 分支架构 / main 行
- **问题**：main 的 root 是一个只含 2 个文件的 Initial commit，与 dev 无任何共同祖先，因此 CLAUDE.md §4 定义的「dev → main 存档」通道在**当前拓扑下根本跑不通**——要跑通需要规范未授权的 unrelated-histories 开关。连带后果：常被引用的「dev 上未进 main 的提交数」实为 dev 的全部历史（classified 抽取时口径 174/174），这条指标因分母退化为全量而失去意义。**注意这条与 §4 的另一条硬约束（main/release 只接受 dev 的 --no-ff 合并）方向相反：规范假定 main 是 dev 的下游，实际是两条无血缘的平行线。** 项目记忆记录用户此前已选择「仅 push dev」而非自动修复，属**已登记的推迟项**——即用户已看过并暂缓，不是新问题。
- **证据**：`f_main/011.json`（W1-GIT-01）；`_handoff_verdicts_all.json` key=`rv:main11:source`（STILL_REAL, MAJOR）/ `:impact`；报告 §10 Batch D-2 git 卫生
- **严重性**：MAJOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin
- **交叉核查备案**：`check-completeness.json` bucket_conflicts #8 记为 `already-aligned`——报告 §10 Batch D-2 对 main11 标注「需用户裁决」，classified 落 user-decision，两处方向一致。

### UD-02 — release 分支与任何 tag 都不存在

- **位置**：`CLAUDE.md:52`（pin 态；对应 §4 分支架构表 release 行）
- **Requirement 归属**：`CLAUDE.md §4` 分支架构 / release 行
- **问题**：release 分支在本地与远端均不存在，仓库 tag 数为零，正式出埠口从未建立。逻辑依据：CLAUDE.md §4 的核心语义是「release 永远是 git tree 最前端」，而**合并顺序约束（main 先、release 后）与禁止清单（禁止 release → main、禁止未打 tag 就合并到 release）全部以该分支存在为前提**。前提不成立时，这些约束不是「被违反」而是「无对象」——读规范的人会以为存在一个可以接收合并的 release 出口。裁决被定为 PARTIALLY_REAL：分支缺失是硬事实，但远端/历史层面是否存在过等价出埠动作是独立问题。
- **证据**：`f_main/012.json`（W1-GIT-02）；`_handoff_verdicts_all.json` key=`rv:main12:source`（PARTIALLY_REAL）/ `:impact`（STILL_REAL）；报告 §10 Batch D-2 git 卫生
- **严重性**：MAJOR ｜ **裁决**：PARTIALLY_REAL ｜ **基线**：unchanged-since-pin

### UD-03 — run d53 的 pin agent hand-back 触发了不可逆本地销毁告警

- **位置**：`workflows/wf_fd517ac0-d53.json:0`（pin 态；journal log 级定位，`line=0` 为占位）
- **Requirement / 归属**：无 Requirement 归属；workflow journal 的第 1 / 3 / 4 条 hand-back
- **问题**：run d53 的 journal log 里，pin agent 与 `rv:main45:source` / `rv:main45:impact` 三条 hand-back 都被 hook 判为 SECURITY WARNING [Irreversible Local Destruction]，理由是这些 hand-back 指向父 workflow 去执行 `git checkout -- tests/test_loss.py` 与 `git checkout -- src/decompmoe/config.py`（会丢弃未提交改动）。后果不在于命令本身，而在于**这三条 agent 的输出带了一层「未经用户授权不得执行」的封条，其结论能否直接采纳成为悬而未决的问题**——被封条的输出在流程上既不算通过也不算作废，处于灰区。（此处引用的命令是 hook 告警文本的原样转述，是问题证据的一部分，不是本文件的操作建议。）
- **证据**：`workflows/wf_fd517ac0-d53.json` logs 第 1 / 3 / 4 条（pin:baseline+delta-map、rv:main45:source、rv:main45:impact）
- **严重性**：MAJOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin
- **⚠ 溯源瑕疵（来自 `check-completeness.json` bucket_conflicts #5，严重性：低）**：本条 `origin_ids` 含 `rv:main45`，而 main45（LIFECYCLE-01）在 archive-only 的 O-22 里，报告 §10 Batch A 明确把 FIXED_BY_COMMIT 的 LIFECYCLE-01 排除在批外。**本条引用的是一个已被判定为「已被 commit 修复」的 finding，用它作为 MAJOR 行动项的证据链存在口径落差；check 记录为「应移除或记为有意引用」，本文件不替其裁决。**
- **污染检查备案**：`check-contamination.json` 的 `patterns_actively_confirmed_clean` 明确把 ud-03 引用的 `git checkout -- tests/test_loss.py` 判为「hook 警告文本的原样转述，不是祈使修法」，故原样保留。

### UD-04 — CLAUDE.md 对 ticket 同时声明非约束与必须维护

- **位置**：`CLAUDE.md:51`（pin 态；§2 真相源优先级 / §8 裁决 / governance req-gov-4 三个落点共用此行区）
- **Requirement 归属**：`CLAUDE.md §2` / `§8` / `governance req-gov-4`
- **问题**：CLAUDE.md §2 的真相源优先级把 `wayfinder/map.md` + 23 tickets 定为「参考性、非约束性」第 4 档，§8 的 2026-08-21 裁决同向；但 §8 的三步修复协议 (a) 又要求 ticket 端**必须**维护 `(historical, …)` 标注，并按 governance req-gov-4 把它形式化为硬义务。**同一个制品同时被声明为「非约束」与「必须被维护」——这不是措辞瑕疵，而是义务没有约束对象：非约束制品的维护义务没有责任人、没有检查点、也没有 lint 覆盖。** 本轮 8 类「无 Decision 记录」中至少 6 类落在 ticket/map 端，它们共享的根因就是这两条规则的张力。报告 §1 对 wayfinder 层的定性是「累积了两年漂移的散文」——散文体裁本身决定了它无法承载规范级的义务。
- **证据**：报告 §7「无 Decision 记录（必须点名，共 8 类）」整节；报告 §1 wayfinder 段定性；`origin_ids` = main28 / main29 / main30 / main31 / main33 / main34
- **严重性**：MAJOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin
- **⚠ 跨桶实体（来自 `check-completeness.json` bucket_conflicts #3，严重性：中）**：本条 `origin_ids` 里的 6 个 finding 同时是 opsx-change 侧 map.md 与 ticket 漂移条目的来源（W22 / W23 / W24 / W25 / W26 / W28）。**同一批 finding 同时支撑「用户裁决项」与「opensx change 项」，会被两批分别计数——若按两个清单各自推进，同一批证据会被处理两次。** check 给出的方向是把 origin_ids 收窄到只承载本条自身的 finding，或显式登记这 6 条的双桶归属；本文件不替其裁决，仅登记。

### UD-05 — beta_effective 对 γ 不可微，训练性论证依赖该通路

- **位置**：`src/decompmoe/schedule.py:171`（pin 态）
- **Requirement 归属**：wayfinder Req 7 L123/L130、Req 24 L586、skeleton L471-473
- **问题**：`beta_effective` 以 `gamma_p: float` 入参并返回 `requires_grad=False, grad_fn=None`；叠加 Phase 2–3 对 `β_max(t)` 的硬 clamp，γ→loss 的梯度通路在 spec 所设计的 AdamW 训练下**在 Phase 1–3 看似不存在**。这是数学层面的问题：若 γ 不可微，则以 γ 调控门禁强度是 policy 式论证而非训练式论证，而 CLAUDE.md §6 明确禁止用 policy + code-first 论证关闭数学语义选择（须给数学 derivation）。三条反驳使 math 镜降级为 PARTIALLY_REAL：(1) Phase 3 的 cap 是严格递增 ramp，上界在 `phase_end` 排他约定下不可达故总会释放；(2) 在 `γ_init ≈ -3.5` 处 `dβ/dγ = 0.9077` 存活；(3) Phase-4 的 γ reset 重开通路，`dβ_eff/dγ' = 7.742`。**但「梯度通路在 Phase 1–3 不存在」这一解读本身仍需 spec 侧澄清**——三条反驳证明的是「不是恒为零」，不等于「非零被设计并被记录」。
- **证据**：`_merged_verdicts` gap2（ADV-03）；报告 §8 偏离表第 3 行
- **严重性**：MINOR ｜ **裁决**：PARTIALLY_REAL ｜ **基线**：unchanged-since-pin
- **归属说明**：本条与其它 5 条 UD 条目的性质不同——它的**可执行部分可能落在代码侧，但「Phase 1–3 梯度不存在是否是设计意图」是 spec 语义问题**。classified 归 user-decision 是因为裁决权在 spec 而非实现。

### UD-06 — 312 行审计台账从未回流主干且与主干分叉

- **位置**：`REVIEW-LEDGER.md:0`（pin 态；文件级定位，该文件不在 dev 树中故 `line=0`）
- **Requirement / 归属**：无 Requirement 归属；报告 §10 Batch D-2 git 卫生
- **问题**：`audit/sdd-review-2026-09-04` 分支上的 `REVIEW-LEDGER.md` 从未进入 dev（dev 树中任何路径下都不存在该文件），该分支与 dev 已分叉，两份同名文件的差异量达 201 增 63 删。内容已推到远端未丢失，**所以这不是数据丢失问题，而是可读性问题**：后续任何一轮审计若只读 dev 树，就读不到这份台账，对该轮已做过的复核会重复劳动，且「同名文件内容不同」这一点在 dev 树内不可见（dev 树里它根本不存在）。
- **证据**：`f_main/016.json`（W1-GIT-06）；`_handoff_verdicts_all.json` key=`rv:main16:source`（STILL_REAL）
- **严重性**：MINOR ｜ **裁决**：STILL_REAL ｜ **基线**：unchanged-since-pin

---

## 交叉核查结果的反映

### `check-contamination.json`（方案污染扫描）

- 扫描范围覆盖全部 193 条 problem 字段，结论 **WARN**：`clean_count=192 / contaminated=1 / borderline=7`。
- **被点名的 1 条 contaminated（AO-31）与 7 条 borderline（AO-25 / AO-61 / AO-62 / AO-70 / AO-72 / AC-06 / AC-29）全部不在本文件的两个桶内**——它们分属 archive-only 与 opsx-change。因此本文件**没有因污染扫描而被要求改写的条目**。
- 结构性证据：classified.json 每条记录只有 12 个字段，**无 `suggested_fix` / `fix` / `solution` 字段**；`code_fence_triple_backtick_hits = 0`；`imperative_fix_regex_hits = 0`。
- 仍然做的动作：15 条 problem 文本在搬运时逐条按禁令清单复核（无替换文本、无三反引号代码块、无新函数/参数/常量名、无步骤序列、无祈使修法）。唯一保留的命令串是 UD-03 中的 `git checkout -- ...`，其为 hook 告警原文转述且已被污染扫描判为 clean。

### `check-completeness.json`（完整性）

与本文件相关的 issue 已在各条目的「⚠ 桶冲突」「⚠ 溯源缺陷」小节逐条反映，汇总如下：

| check 类别 | 涉及本文件的条目 | 已在本文件何处反映 |
|---|---|---|
| bucket_conflicts #2（W07 违反 classified 自身分桶规则） | DF-08 | DF-08 条目下的「⚠ 桶冲突」 |
| bucket_conflicts #3（W44 与 opsx-change 跨桶共享 6 个 finding） | UD-04 | UD-04 条目下的「⚠ 跨桶实体」 |
| bucket_conflicts #4（mut 副本残留 6 条同实体） | DF-01…DF-06 | 「DF 段」导语下的「同实体 6 条」说明 |
| bucket_conflicts #5（P05 溯源指向 FIXED_BY_COMMIT 的 finding） | UD-03 | UD-03 条目下的「⚠ 溯源瑕疵」 |
| bucket_conflicts #6/#7（W43 / main13 在 §10 Batch D-2 与 direct-fix 两处口径） | DF-09 | DF-09 条目下的「⚠ 桶冲突」 |
| bucket_conflicts #8（main11 已对齐） | UD-01 | UD-01 条目下的「交叉核查备案」 |
| bucket_conflicts #9（W07 与 W02 同 locus 不同实体） | DF-08 | DF-08 条目下的「⚠ 桶冲突」 |
| bucket_conflicts #10（除上述 6 组外无跨桶重复） | 全部 | 无需反映 |
| content_accuracy_flags（DF-05 origin_ids 指错） | DF-05 | DF-05 条目下的「溯源缺陷」 |
| content_accuracy_flags（DF-01 origin_ids 为空数组） | DF-01 | 「DF 段」导语下的「同实体 6 条」说明 |
| misplaced_evidence_insufficient（§11 第 9 条落 direct-fix 正确但被拆成 6 条） | DF-01…DF-06 | 「DF 段」导语下的「同实体 6 条」说明 |

**关于「同实体 6 条」的处理口径**：classified.json 把报告 §11 第 9 条的变异副本残留拆成 6 条（DF-01 总量视角、DF-02/03/04 分目录视角、DF-05 报告文本视角、DF-06 伴生脚本视角），本文件**按 classified 原样保留 6 条、不做合并裁定**——合并与否是分类阶段的决定，不是搬运阶段该做的事。但读者须知：这 6 条不是 6 个独立缺陷，**按条计数的严重性汇总会重复计算同一个实体**（DF-01 MAJOR 与 DF-02/03/04 MEDIUM 指向同一批目录）。其中 DF-01 的 `origin_ids` 是空数组、DF-05 的 `origin_ids` 指向无关的 test-guard finding，两者的溯源链是断的。

---

## 本文件的盲区

本文件**没有**覆盖以下内容：

1. **§3 的 18 条遗漏 finding，无一属于本主题。** `check-completeness.json` 列出的 sub_type_A（9 条：D1-02 / D1-07 / D2-02+gap4 / D2-05 / D3-01 / main36 / main38 / main73 / main78）与 sub_type_B（7 条：D1-03 / D1-04 / D1-05 / D3-02 / D3-03 / main37 / main41）全部是**数学语义层或 spec 文本层**的问题（Voronoi 数值、frame 校准、跨 spec 内部矛盾、行号指针错），其归属是 opsx-change / 清单 A。**本文件未收录任何一条，因为它们不属于「可直接修」或「用户裁决」这两个桶。** 其中最接近本主题的是 main36 / main73（wayfinder req-23 的交叉引用写成行号且 Requirement 号错）与 main38（skeleton Req 7 与 Req 19 的范数断言互相矛盾）——但这两条的根因是 spec 文本，属清单 A 域。
2. **DF 段 6 条的漂移状态在机制上不可验证。** DF-01…DF-06 与 UD-03、UD-06 的 location 全部在**仓库之外**（审计工作区、workflow 目录、未合入 dev 的分支），`_pin_drift.json` 按仓库文件生成，**对这 8 条没有任何覆盖**。它们的 `unchanged-since-pin` 是「查表无记录」的默认值，不是「已确认未变」。DF-02 条目正文已就此点明。
3. **本文件不含任何数学重算。** UD-05 的 `dβ/dγ = 0.9077`、`dβ_eff/dγ' = 7.742`、Phase-3 ramp 严格递增性等均为既有裁决的搬运，**本轮未复算、未验证**。DF-08 的 0.83% 数值（66_080 / 65_536 增幅）同理。
4. **本文件不含任何「已修复」判定。** `unchanged-since-pin` 只表示「pin 之后该行没被 pin→HEAD 的 9 个 commit 动过」。pin 之后新增的 change 目录（`openspec/changes/archive/2026-10-01-*` 等）与 pending change 是否有部分覆盖了这些条目，**本轮未核对**。
5. **桶冲突未在本层解决。** DF-08 与 DF-09 各自被登记为「classified 口径 vs 报告 §10 批次口径」的分歧，UD-04 被登记为跨桶双计风险。本文件只登记，不裁决——裁决需要在 classified 层面做，超出本轮范围。
6. **`dropped`（41 条）与 `conflicts`（29 条）两桶未纳入。** 其中 conflicts 记录的是合并时成员不一致的条目，多数为 archive-only 的裁决性说明；与「可直接修 / 用户裁决」无交集。
