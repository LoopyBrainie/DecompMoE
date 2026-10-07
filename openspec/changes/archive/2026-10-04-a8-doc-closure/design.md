# Design

## 审计登记的计数约定（本 change 立，后续沿用）

本 design.md 的「审计台账登记」段与其余 evidence prose 里的**每一个计数**，二选一，不允许裸数字：

1. **可复算** → 同 block 内给出复算命令或 pinned 对象（`git …` / `Select-String …` / commit hash / `HEAD` / change 名 / `req-N` / 具名测试名）。格式：`数字（复算：`<命令>`）`。
2. **不可重建** → 同 block 内标 `not reconstructible`，且**必须带三要素**：**原因**（可判定的，不是「懒得补」）、**记录日期**、**重建所需条件**。只写四个字而无可判定理由，等于把逃生舱用成橡皮图章——下一个审计者无法区分「真的蒸发了」与「基线没补」。

依据：`scripts/lint_no_baseline_counts.py` 的判据是「block 内有 COUNT 而无 BASELINE token」；其 EXEMPTION MARKER 是 in-document 的（无登记表），所以规则在**文档里**，不在代码里。

**为什么立这条**：本次审查报出的 finding 全部落在裸计数上（复算：`GATE_CHANGE=2026-10-04-a8-doc-closure python scripts/lint_no_baseline_counts.py` 的 `without a baseline` 条数，修复前为 6）。修完后若不立约定，下一个并行 session 仍会写出新的裸计数，门禁再次变红，而那时 blame 的是本登记格式没有给后来者立规矩。**本段自身也曾触发该 lint**——它举例说「本次 N 处」时同样是无基线计数，是 lint 报出来的，不是预想到的。

## Context

见 `proposal.md` — Why。此处只记录塑形了方案的现状与约束。

`.audit/` 被 `.gitignore` 忽略、非版本化（见兄弟 change `fix-wayfinder-advisory-drift-a7` 的 design.md「Not changed by design」表）。因此本 change 的「报告面」产物在执行时可能没有可写的版本化落点——`design.md` 是**唯一一定存在**的决策记录处。

`CLAUDE.md` 共 **118** 行、§1–§9（复算：`git show 35380cf:CLAUDE.md | Measure-Object -Line` → 118；该 commit 是本 change 写作时的基线，此后 §4/§8 各有一次增补，行数已变，**故引用时必须带 commit**）。A-8 清单给的三处 `CLAUDE.md:51/52` 引用**全部落空**：`L51` 是 `dev` 分支行（与 §2/§8 无关），`main` 行在 `L52`、`release` 行在 `L53`（三处同向偏移一行）。本 change 按**内容**定位，不按行号。

`governance` req-gov-4 的 clause (1) 原文已核实：

> **Advisory non-binding scope** — tickets MAY be superseded by OpenSpec changes without amending the ticket itself; this is the ONLY meaning of "advisory". The advisory scope covers ticket-edit policy … and does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`.

## Goals / Non-Goals

**Goals:**

- 让 `CLAUDE.md` §4 与 §8 的文本不再与自身治理条款冲突。
- 把 **3** 条被封条的 hand-back 结论显式降级为「需重新取证」，使其既不被静默丢弃、也不以「已裁决」面目混入结论链（复算：`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` 的 `UD-03` 条目，其「问题」行一句话点明这三条 lens，`Select-String -Path <该文件> -Pattern 'Irreversible'` → 1 处封条标记；该文件**未被 gitignore 之外的方式版本化**，`git ls-files .audit` → 0，故此基线依赖工作树存在，消失时须改标 `not reconstructible`）。
- 让后续审计能定位到未回流的审计台账。

**Non-Goals（design 层边界）:**

- 不改任何 Requirement 正文（故 `skip_specs: true`）。
- 不把 A-8 的 6 条裁决转成代码改动或 spec 变更——UD-05 的行为面修复在兄弟 change `2026-10-04-phase2-gamma-reset-ramp-closure`。
- 不清理停在 `051f247` 的 3 条本地-only 分支。

## Decisions

### D1 (UD-04) — `CLAUDE.md` §8 引用 req-gov-4 clause (1)，而非改写 spec

矛盾早已被 `req-gov-4` clause (1) 收掉：它把 advisory 的语义显式收窄为 ticket-edit policy。所以选 **(b) 必维护制品**，动作只是让 `CLAUDE.md` 引用这个 scope 划分。

**被否决的替代方案 (a) 删掉 §8 协议 (a) 的维护义务**：成本被严重低估。删 §8 那一句并不等于删一句软话——`req-gov-4` clause (3)(4) 是已生效的硬条款（周期监控 ticket ↔ spec ↔ `src/` 三角漂移 + 三步修复协议），`req-gov-2` 文档化标注格式，`req-34` 与 `lint_no_source_field_drift.py` 三门独立检查硬卡。**动的是已生效的治理层。** 选 (a) 要先废掉这些。

**被否决的替代方案 (c) 只补执行机制**：义务会继续悬空。实测 `scripts/lint_*.py` **5 个**（`lint_no_dead_defensive` / `lint_no_line_pointers` / `lint_no_source_field_drift` / `lint_pointer_detector` / `lint_no_baseline_counts`；复算：`Select-String -Path scripts -Filter 'lint_*.py'` → 5。注意第 5 个是 2026-10-05 并行 session 的 `4b24285` 引入的，本 change 写作时不存在——`CLAUDE.md` §3 说 `run_gates.py` 按 glob 自动发现该目录，故「清单与实际门禁不可能失步」的反面是**门禁数量会在无通知的情况下增长**，任何写死数量的句子都会过期。**这 5 个无一覆盖 ticket 维护义务**——`lint_no_source_field_drift.py` 只 `glob("*/spec.md")`、`lint_no_baseline_counts.py` 只扫 `changes/**/{proposal,design,tasks}.md` + `docs/**`，**都不打开任何 ticket 文件**。但注意 `req-gov-4` clause 4 的触发条件是「ticket stale 已传播到 `src/`」这一**条件性**前提，因此无条件 lint 本就不该存在。实测 `wayfinder/tickets/` **23** 个文件中 **8** 个已有 `(historical, …)` 标注（共 **19** 处），其余 **15** 个无标注**不构成违反**（复算：`Select-String -Path wayfinder/tickets -Pattern '\(historical,'`；本仓 tickets 为 GBK/ACP 936 编码，须按字节计数，见「行数口径声明」节）。

**落点（追加到 `CLAUDE.md` §8 的 2026-08-21 裁决段末）**：

> 「参考性、非约束性」的确切含义以 `openspec/specs/governance/spec.md` 的 `req-gov-4`（Ticket Advisory Boundary — Stale Contamination Monitoring）clause (1) 为准，verbatim：「this is the ONLY meaning of "advisory"」。即 ticket 文本可不经 amendment 偏离 spec（**不得推翻 spec**），但该 advisory 范围「does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`」——§8 的三传染通道监控义务与 `(historical, …)` 标注义务**不受此限**。

**引用纪律**：按 req-gov-6 的 Cross-Reference Anchor Contract，prose passage 的引用形式是「Requirement 号 + 标题 + ≥8 字符 verbatim 引文」，**不写行号**（`lint_no_line_pointers.py` 检查 C1）。本段刻意不使用 `#req-gov-4` 锚点字面量，以规避 C3（anchor literal 不得出现在 code span 内）。且**只能引 clause (1)**——兄弟 change `fix-wayfinder-advisory-drift-a7` 的 D4 已裁定 `(historical, …)` 标注义务的治理依据是 `wayfinder` req-34，**不是** req-gov-4 clause 4(a)。

### D2 (UD-01/02) — `CLAUDE.md` §4 标「未启用」+ 事实陈述，保留三分支为 aspirational

**落点（`release` 行之后）**：

> **当前状态（2026-10-04 实测）——本节通道未启用**：本仓 `main` 的 root 是只含 `.gitignore` 与 `LICENSE` 的 Initial commit `051f247`（复算：`git log --oneline -1 main`；`git ls-tree -r main --name-only` → 2 条），与 `dev` 无任何共同祖先（`git merge-base main dev` 无输出且退出码 1），故 `dev → main` 存档通道在拓扑对齐前**不可执行**；`release` 分支**不存在**，故 `dev → release` 出埠通道与「必带 tag」义务**从未被触发**。三分支架构保留为 aspirational 规范，本节不预设将来是否建立 `release`。远端 HEAD 仍指向 `main`（一棵与开发线无关的单提交空树），**未修复**；`git remote set-head origin dev` 不是该问题的修法，理由与实测见本文件末尾的更正节。
>
> **「`release` 不存在」的证据力分级**（初稿写作「五路均不存在」，其中三腿并不能证明分支不存在，容易让复核者分不清「分支不存在 / tag 不存在 / 文件缺失」）：**决定性的两腿**是 `git for-each-ref refs/heads/release` 与 `git ls-remote --heads origin release`（穷举 loose + packed refs 与全部远端 ref，各自单独即足够）；**辅助腿**是 `git tag`（枚举的是 **tag** 不是分支，只能佐证无同名 tag）、`.git/logs/refs/heads/release` 缺失（佐证从未被创建过）、`packed-refs`（⚠️ **本仓不存在该文件**，8 个 head 全是 loose，故此腿在本仓是**空的**；即便存在也只列 packed ref，loose 的 `refs/heads/release` 不会出现在其中）。仓库 tag 数本地与远端皆为 0（复算：`git tag | Measure-Object -Line`；`git ls-remote --tags origin | Measure-Object -Line`）。

**被否决的替代方案 (b) 改写为 dev 单分支 + main 降为可选存档**：§4 三分支是专门立的规范，改写会同时牵动 L51 的 `dev` 条目（「绝对无 merge commit，保持线性」），改动面远大于加一段状态说明。

**「未进 main 的提交数」这一指标同步作废**：`git rev-list --left-right --count main...dev` 在 HEAD `4b24285` 读数为 `1 / 243`（main 仅 1 个 commit 领先、dev 领先 243），指标已**退化为 dev 全部历史**，毫无信息量。A-8 清单记录的 `174/174` 更早过期——核查期间并行 session 多次推进 HEAD。初稿在此写的 `229/229` 同样过期，且 `A/B` 这种斜杠对**不是任何 git 命令的输出形状**（`rev-list --left-right --count` 输出的是**制表符**分隔的两列）。**本段自身即示范了为什么不能引用提交数**：任何「提交计数」型数字在并发工作树下都会漂移，故 `CLAUDE.md` §4 的事实陈述**不引用任何提交数**，本 design 也只在上句给读取点以示其不可信。

### D3 (UD-06) — 台账只登记不回流，且必须同时登记 `LOOPS.md`

台账是审计制品，不在真相源层级内（既不在 `openspec/specs/**`，也不在 advisory 的 `wayfinder/map.md` + 23 tickets 决策 trail 内）。把它落进 dev 会让它看起来像受治理的制品。内容在远端安全（`audit/sdd-review-2026-09-04` 本地与 `origin` 同 SHA `f8e5b26`，`ls-remote` 确认可见），登记指针足够后续审计定位。

**A-8 清单在 UD-06 上有两处错，必须在登记时纠正**：

1. 差异量。实测 `git diff --numstat dev...audit -- REVIEW-LEDGER.md` = **312 增 0 删**（纯新增，merge-base `d52f8be` 不含该文件）。清单的「201 增 63 删」是 **`LOOPS.md`** 的 numstat，且**极性颠倒**（dev→audit 实为 63 增 / 201 删）。
2. 「两份同名文件」。全仓**只有一份** `REVIEW-LEDGER.md`（复算：`git ls-tree -r <各 ref> --name-only` 在 `dev` / `main` / `audit` / `origin/dev` 中对 `REVIEW-LEDGER` 的命中数合计 = 1）。真正的同名两份是 `LOOPS.md`（dev 侧由 `dd8b9d7 chore(audit): import LOOPS.md to version control` 引入，audit 侧由 `f8e5b26` 独立新增）——准确表述是：**audit 侧那份 `LOOPS.md` 的内容未回流**（dev 侧是 `dd8b9d7` 引入的**另一份**内容）。这是 A-8 清单的漏项。

**行数口径**：必须用**字节流**口径（`git cat-file blob` 数 `0x0A`）得 312。PowerShell 文本路径给出 310（控制台编码吞掉多字节序列的假低读数），且 CR 计数为 0 ⇒ 纯 LF。三个独立口径（raw LF / `numstat` / 字节数）须互相对账。

**登记的 verbatim 引文必须在 apply 时实读**：req-gov-6 要求 prose passage 引用含 ≥8 字符 verbatim 引文，而 `REVIEW-LEDGER.md` 不在 dev 树中。本 design **不预写**该引文——按 `CLAUDE.md` §3「不在无真相源处造值」，引文须在 apply 步骤从 `git cat-file blob audit/sdd-review-2026-09-04:REVIEW-LEDGER.md` 现场提取后写入。**禁止凭文件名或记忆编造引文。**

### D4 (UD-03) — 3 条封条进 deferred-evidence 桶；第 4 条只进脚注

A-8 清单的 4 条 hand-back 实际只有 **3 条**带封条，且来源与清单描述不同：告警不在 `journal.jsonl`（匹配数 0），而在 workflow json 的 `logs` 数组；且**只有 pin 那条同时点名两个文件**，`rv:main45:source` 与 `rv:main45:impact` 只点名 `tests/test_loss.py`。清单把三条的理由合并陈述了。

**决定采信权的关键事实**：两个目标文件现已与 HEAD 一致（各自 blob 相等），且 `tests/test_loss.py` 当前 blob `e12ac751` **既不是** d53 当时的 revert 态 `7a88c637`、**也不是** fix 态 `6ddbdefb`——该文件此后已被多次改写。**封条所保护的那份工作树状态已从树上消失，三条结论的证据基础在当前 HEAD 下不可复现。** 这比「分类器未过」更弱：前者是**负证据**（对账对象蒸发），后者是**非证据**。

⇒ 3 条全部标「需按新 HEAD 重新取证」，A-8 报告不引用其结论。重取证范围划死为**仅这 3 条 lens**，不重跑整个 `rv:main45` 批次——批内其余结论的证据基础未受 `test_loss.py` blob 变更影响，整批重跑会无谓作废仍然有效的证据。

**第 4 条 `rv:main58:source` 单独处理**：它因安全分类器限流**根本没被审查**，既无 `SECURITY WARNING` 也无放行确认，是三种状态里最弱的一档。它**不是待裁决发现、也不是待重取证项**——它从未产生任何输出，不进 deferred 桶的重取证清单，只在脚注记「无分类器输出，不构成证据；如需覆盖须重新提交分类」。

## Risks / Trade-offs

- **[风险] §4 的「未启用」注记会过期** —— 将来若建立 `release` 或完成 `main` 拓扑对齐，该段即成陈旧文本。→ 缓解：措辞用「2026-10-04 实测」并显式声明「本节不预设将来是否建立 `release`」，使其作为状态快照而非永久断言；`CLAUDE.md` 无 per-line 日期 lint，故须靠下轮 audit 复核。
- **[风险] §8 引用 req-gov-4 形成 `CLAUDE.md → spec` 的新耦合** —— 若将来 req-gov-4 clause (1) 被 supersede，该引用会悬空。→ 缓解：引用带完整 Requirement 标题与 verbatim 引文（而非行号或锚点），使 supersede 时可被 grep 检出。
- **[风险] 台账登记不回流，后续审计仍可能重复劳动** —— 这是 (a)/(b)/(c) 三选项的共同代价。→ 缓解：登记含分支名、commit SHA、精确 numstat 与分叉计数，足以让后续审计直接跳到该分支读取，无需重新测量。
- **[权衡] 选择「只登记」而非「回流」** —— 放弃了在 dev 树内可见性，换取不让审计制品冒充受治理制品。

## Open Questions

- ~~A-8 报告在执行时若不存在（`.audit/` 未被 gitignore 但工作树当前无该目录），登记与 deferred 桶落到何处？~~ **已解决**：执行时 `.audit/wayfinder-opsx-code-review/` 存在（内含 `opsx-changes.md`，即 A-8 清单所在），但**登记与 deferred 桶落在本 `design.md` 而非 `.audit/`**。依据是兄弟 change `2026-10-04-fix-wayfinder-advisory-drift-a7` 的 design.md 处置约定：「`.audit/` 被 `.gitignore` 忽略、非版本化。裁决只进本 design.md」。本 design.md 会随归档进入版本化历史，`.audit/` 下的副本不会。故此处为**唯一权威且持久**的落点。

---

## Deferred-Evidence 桶（UD-03）

A-8 清单登记了 **4** 条 hand-back（复算：workflow json 的 `logs` 数组中带 lens 前缀的条目 → `pin:baseline+delta-map` / `rv:main45:source` / `rv:main45:impact` / `rv:main58:source`），实测**只有 3 条带封条**。告警原文不在 `journal.jsonl`（对 `Irreversible` / `SECURITY WARNING` 的匹配数为 0），而在 workflow json 的 `logs` 数组（`logs[0]` / `logs[3]` / `logs[4]`；复算：`Select-String -Path <该 json> -Pattern 'Irreversible'` → 3）。清单把三条的理由合并陈述了——**只有 pin 那条同时点名两个文件**。

**索引的一处更正（2026-10-06 实测，d53 工件仍在）**：A-8 清单的「证据」行写 `logs 第 1 / 3 / 4 条`，而主工件 `wf_fd517ac0-d53.json` 的 `logs` 是 **0-based、长度 6 的字符串数组**，三条封条落在 `index 0` / `3` / `4`（`index 1` 是「Pin 阶段完成：基线 finding 7 条」、`index 2` 是 ReVerify 展开、`index 5` 是分类器那条）。故 **1-based 读法「第 1/3/4」会把第 1 条错指到无告警的条目**。上一版审查把「清单的 1/3/4」当作正解、本 design 的「0/3/4」当作可疑——**方向反了**：主工件可直接读出 0-based 下标，本文件的 `0/3/4` 是对的，差一位的是清单。

**共同失效原因（负证据，非「分类器未过」的非证据）**：`tests/test_loss.py` 与 `src/decompmoe/config.py` 现均与 HEAD 一致（各自 blob 相等）；`tests/test_loss.py` 当前 blob `e12ac751` **既不是** d53 当时的 revert 态 `7a88c637`，**也不是** fix 态 `6ddbdefb`。封条所保护的那份工作树状态**已从树上消失**，三条结论的证据基础在当前 HEAD 下不可复现。

| lens | 原结论 | 封条点名文件 | 失效原因 | 前置条件 | 重跑范围 |
|---|---|---|---|---|---|
| `pin:baseline+delta-map` | pin 态基线 + delta 映射 | `tests/test_loss.py` **与** `src/decompmoe/config.py` | 上述 blob 蒸发 | 新 HEAD 稳定后 | 仅本条 lens |
| `rv:main45:source` | `STILL_REAL` / `MINOR` | 仅 `tests/test_loss.py` | 同上 | 同上 | 仅本条 lens |
| `rv:main45:impact` | `STILL_REAL` / `MAJOR` | 仅 `tests/test_loss.py` | 同上 | 同上 | 仅本条 lens |

agent 自述（`journal.jsonl` result 字段，逐字）保留了当时自洽的证据形状，但因对账对象已消失，**不得直接引用**：

- `rv:main45:source`：verbatim「The revert exists only as uncommitted working-tree state in D:/myProject/DecompMoE, so it is fixed by `git checkout -- tests/test_loss.py`, not by any commit.」
- `rv:main45:impact`：verbatim「none — b272787 IS the fix being reverted; no commit repairs it, because the damage lives only in the uncommitted main worktree (remedy is `git checkout -- tests/test_loss.py`, not a code change)」

**重取证范围已划死为这 3 条 lens**（复算：上表 **3** 行；每行对应 workflow json `logs` 数组中一个 `[Irreversible Local Destruction]` 条目，`Select-String -Path <该 json> -Pattern 'Irreversible'` → 3），不重跑整个 `rv:main45` 批次——批内其余结论的证据基础未受该 blob 变更影响，整批重跑会无谓作废仍然有效的证据。

**脚注（非 deferred 项）**：`rv:main58:source` 因安全分类器限流**根本没被审查**（`logs[5]` 记「the safety classifier was unavailable (rate-limited)」），既无 `SECURITY WARNING` 也无放行确认。它**从未产生任何输出，不构成证据**，因此不进上表的重取证清单；如需覆盖须重新提交分类。**A-8 清单从未涵盖这第 4 条。**

## 审计台账登记（UD-06）

**不回流**，只登记位置与状态。内容在远端安全：`audit/sdd-review-2026-09-04` 本地与 `origin` 同 SHA `f8e5b26d5a34fd7d2d276e80808cf2eaff143ac7`（`ls-remote` 确认可见）。

### `REVIEW-LEDGER.md` — 纯新增，未回流

- 位置：分支 `audit/sdd-review-2026-09-04`，路径 `REVIEW-LEDGER.md`（复算：`git rev-parse audit/sdd-review-2026-09-04` → `f8e5b26d5a34fd7d2d276e80808cf2eaff143ac7`，本地与 `origin` 同 SHA，远端可见）
- 实测（字节口径 `git cat-file blob`）：**17 961 bytes、312 LF、0 CR**（纯 LF 结尾；复算：`git cat-file blob audit/sdd-review-2026-09-04:REVIEW-LEDGER.md`）
- `git diff --numstat dev...audit -- REVIEW-LEDGER.md` = **312 增 / 0 删**（三点，merge-base `d52f8be` 不含该文件；见「numstat 口径声明」）
- `git ls-tree -r dev --name-only` 对 `REVIEW-LEDGER` **零命中** ⇒ 确实从未进入 dev
- **分叉计数**：`git rev-list --left-right --count dev...audit/sdd-review-2026-09-04` = **203 / 1**，读取于 HEAD `4b24285`。⚠️ 这是**会漂**的数字——dev 在并发工作树下持续推进，故本登记**只把它当定位提示**（`203` 意味着 audit 侧落后 dev 约 200 个提交），**任何后续审计 MUST NOT 采信它而不重测**。初稿写的 `190/1` 已过期（差 13 个提交）；此处按本文件顶部的「计数约定」显式给出仪器与读取点，正是为了让它可被重算而非被信任。
- verbatim 引文（≥8 字符，req-gov-6 prose-passage 格式）：**「DecompMoE SDD math-conformance review」**（从上述 blob 现场 `Select-String` 提取，非凭文件名编造）
- **该台账自身已陈旧**：其表头声明「master, 31 Req」与「master, 22 Req」、以及「Current test baseline: `uv run pytest tests/` → **136 passed, 0 failed**」。当前实际为 wayfinder 36 Req / decompmoe-skeleton 23 Req（复算：`Select-String -Path openspec/specs -Pattern '^### Requirement'`，`governance` 另 10 条，合计 69）。**引用它时必须先按新 HEAD 重测**，不要把它当作现状基线。

### `LOOPS.md` — 两分支同名但内容不同（A-8 清单漏项）

- 位置：同一分支，路径 `LOOPS.md`；审计分支侧实测 **3 800 bytes、63 LF、0 CR**
- **dev 树中已存在 `LOOPS.md`**（由 `dd8b9d7` 引入），与审计分支侧是**两份不同内容**——这才是 A-8 清单所说的「同名文件」，而 `REVIEW-LEDGER.md` 全仓**只有一份**
- `git diff --numstat dev audit/… -- LOOPS.md` = **63 增 / 201 删**
- ⇒ **A-8 清单的「201 增 63 删」是 `LOOPS.md` 的 numstat，且极性颠倒**；两个数字都不是 `REVIEW-LEDGER.md` 的
- verbatim 引文：**「The DecompMoE SDD math-conformance review loop」**

### 行数口径声明

两个文件的行数一律用**字节流**口径（数 `0x0A`）。实测（复算：`git cat-file blob audit/sdd-review-2026-09-04:REVIEW-LEDGER.md` 后按字节数 `0x0A` → 312；该审计分支本地与远端均在 `f8e5b26`，故此基线**可复算**、无需 `not reconstructible`）。

**哪一种读法会给出假低读数 310**（2026-10-06 逐一实测，落在**未污染的原始字节文件**上）：

| 读法 | 结果 |
|---|---|
| `Get-Content <file>`（PS7 默认 UTF-8） | **312** ✅ |
| `Get-Content <file> -Encoding utf8` | **312** ✅ |
| `[System.IO.File]::ReadAllLines(<file>)` | **312** ✅ |
| `Get-Content <file> -Encoding ansi`（ACP 936） | **310** ❌ |
| `git show … \| Out-File` 之后任何文本读法 | **310** ❌（写盘时已坏） |

**成因（已定位到字节）**：恰有 **2** 个 `0x0A`（偏移 `9079` 与 `10973`）紧跟 GBK 前导字节 `0x85` / `0x92`。.NET 的 cp936 解码器在 lead byte 后**不校验 trail byte 范围**，直接吞掉后一字节，于是这两处换行消失，两对行被合并 ⇒ `312 − 2 = 310`。

⇒ **初稿的警告结论与成因均正确，错的是被点名的那个命令**（初稿写「不得用 PowerShell 文本路径的 `Get-Content`」——**默认的 `Get-Content` 恰恰是正确读法**）。引用时须标明用的是哪个口径。

### numstat 口径声明（两点 vs 三点）

登记里两个 numstat 用的是**不同**的 diff 形式，这是有意的，不是笔误：

- `REVIEW-LEDGER.md` 用**三点** `dev...audit`（merge-base `d52f8be` 不含该文件 ⇒ 纯新增 `312 增 / 0 删`）
- `LOOPS.md` 用**两点** `dev audit/…`（两点按 tree 比对，dev 侧已有该文件 ⇒ `63 增 / 201 删`）

用**同一**仪器重测这两个会得到矛盾结果：`LOOPS.md` 在**三点**下是 `63 增 / 0 删`（merge-base 无此文件）。**引用任一 numstat 必须连同其 diff 形式一起写**，否则读者用另一种形式复算会以为数字错了。

## 事实更正：`git remote set-head` 不改远端默认分支（任务 6.1 原文有误）

本 change 的任务 6.1 原文写作「`git remote set-head origin dev`（改的是**远端**默认展示分支指针，**不动任何 ref 拓扑**）」。**该描述在「远端」二字上是错的**，实测如下：

| 步骤 | 观测 | 来源 |
|---|---|---|
| 执行前 | 本地 `refs/remotes/origin/HEAD` = `refs/remotes/origin/main` | `git symbolic-ref refs/remotes/origin/HEAD` |
| 执行 | `git remote set-head origin dev` → `exit 0` | — |
| 执行后（本地） | `refs/remotes/origin/HEAD` = `refs/remotes/origin/dev` | `git symbolic-ref refs/remotes/origin/HEAD` |
| 执行后（**远端**） | **仍为** `ref: refs/heads/main	HEAD` / `051f24749770f6ceb6b3ba4d5c4961592943ba5e` | `git ls-remote --symref origin HEAD` |
| 回滚 | `git remote set-head origin main` → `exit 0`，本地恢复 `refs/remotes/origin/main`，与远端一致 | 同上两路复验 |

`git remote set-head` 写的是**本地** `refs/remotes/origin/HEAD` 这个 remote-tracking 缓存 ref；它是「远端 HEAD 是什么」的**本地副本**，不是设置远端的动作。**真正改 GitHub 仓库首页默认分支必须改远端仓库设置**：`gh repo edit <owner>/<repo> --default-branch dev`，或 GitHub 仓库 Settings → Branches → Default branch。当时（2026-10-04）本机 `gh` 已安装但**未认证**（`gh repo view` 报 `run: gh auth login`），故那一轮无法执行；认证后的完成情况见下一节。

⇒ **该执行不仅未达成目标，还使本地缓存与远端事实相反**（本地声称 `dev`、远端实为 `main`），故已回滚。任务 6.1 与 6.3 保持 `[ ]`。

### 更正的后续：2026-10-05 真正完成修复

`gh` 完成认证后（account `LoopyBrainie`，scopes 含 `repo`），改用真正的修法 **`gh repo edit LoopyBrainie/DecompMoE --default-branch dev`**，三路复验：

| 观测面 | 修复前 | 修复后 |
|---|---|---|
| GitHub API `defaultBranchRef.name` | `main` | **`dev`** |
| `git ls-remote --symref origin HEAD` | `ref: refs/heads/main	HEAD` / `051f247…` | **`ref: refs/heads/dev	HEAD`** |
| 本地 `refs/remotes/origin/HEAD`（镜像） | `refs/remotes/origin/main` | `refs/remotes/origin/dev`（`set-head` 刷新后与远端一致） |

**不变量全部未变**：release ref 本地+远端 0；tag 本地 0 / 远端 0；`git merge-base main dev` 仍 `exit 1`；`main` root 仍 `051f247`；远端 heads 仍 4 条（**未创建任何分支**）。

**两条看似相同的命令，正确处置方向相反**——值得单独记住：

| | 远端是否真的移动 | 本地与远端关系 | 正确处置 |
|---|---|---|---|
| `git remote set-head origin dev`（2026-10-04） | **否** | 相反 | **回滚**（刷新会制造假象） |
| `gh repo edit --default-branch dev` + `set-head` 刷新（2026-10-05） | **是** | 一致 | 保持（刷新是真实反映） |

判据**不是**「这条命令好不好」，而是**「刷新后本地是否与远端一致」**。`set-head` 本身永远只写本地；它是**镜像的刷新动作**，正确与否取决于它所镜像的远端事实是否已经改变。

**教训（对应 CLAUDE.md §3「GateGuard」与本 change 的「禁止预先勾选」条款）**：命令 `exit 0` 只证明**调用成功**，不证明**目标达成**。`remote set-head` 这一族命令的名字自带「设置远端」的字面暗示，而实际作用域是本地 ref——**这类作用域与名字不符的命令，必须向被作用的另一侧（此处是 `ls-remote`）取证，而不是向本地复述**。本条若被勾选，就会把「远端首页已修好」这个**未发生的副作用**写进受治理制品。
