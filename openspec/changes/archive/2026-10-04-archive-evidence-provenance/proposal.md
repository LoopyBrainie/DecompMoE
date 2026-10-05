# Proposal

## Why

本 change 的事实基础全部经 `git show` / `git log` 实测，每条带 revision。
**归档件不修改**（`openspec/specs/governance/spec.md` `req-gov-5` Scenario
「Archive copies are not retro-edited」:228-232、`req-gov-6` obligation 7:288-290），
故所有事实更正记录在**本 change** 内，而非回写
`openspec/changes/archive/2026-10-03-a5-archive-gate-executability/`。

### 计数口径声明（阅读本文件前必读）

本文件出现的所有 anchor 计数字符串，**一律为 `block_starts` 口径** ——
`scripts/run_gates.py:242-262` 定义：锚点后最近的非空行必须是 `### Requirement:`
标题，否则视为行内提及、不计入。

| 口径 | HEAD `35380cf` 的总数 |
|---|---|
| `block_starts`（本文件采用） | **69**（wayfinder 36 / decompmoe-skeleton 23 / governance 10） |
| 裸 `<a id=` 计数 | **71**（38 / 23 / 10） |

两者差 2，来自 `req-20-source` / `req-20-mci` 这类行内提及。
**读者用 `grep -c '<a id='` 得不到本文件的数字，且无从得知差在哪** —— 这本身就是缺陷 A12。

---

### A 组 — F4：幸存快照的 provenance 只记了一半

被审计对象：`archive/2026-10-03-a5-archive-gate-executability/evidence/incident.md:55`、`:61`。

| # | 事实 | 位置 / 证据 |
|---|---|---|
| A1 | 叙述把幸存快照归于 head `940b27c` | `evidence/incident.md:55`、`:61` |
| A2 | 两份幸存账本自记录 `written_at_head` = `850ed8a2e4b90039b9673b533b815877d5abe737` | `evidence/anchor-ledger-before.json:84`、`anchor-ledger-post.json:84` |
| A3 | `850ed8a` 是 `940b27c` 的**直接子提交** | `git rev-list --count 940b27c..850ed8a` = 1 |
| A4 | 两者 `openspec/specs/` **逐字节相同** | `git diff --stat 940b27c 850ed8a -- openspec/specs/` 输出为空 |
| A5 | 故 `65`（36/23/6，`block_starts`）在 `940b27c`、`850ed8a`、`1612778` **三处均成立** | 由 A3+A4 推出 |
| A6 | 幸存账本内容（36/23/9 = 68，`block_starts`）与 `ea802c8` 树**逐键无差集** | `git show ea802c8:<ledger>` 对账 |
| A7 | 账本文件全程**只有 1 个 commit**（`ea802c8`），其中已是 850ed8a / 68 锚点 | `git log --follow` |
| A9 | 字段语义解耦：`written_at_head` 记**写入时刻的 HEAD**（`scripts/run_gates.py:448`），`ledger` 内容读**磁盘工作树**（`:265` `anchor_ledger()`）；payload 仅 4 字段，**无**内容 digest | `scripts/run_gates.py:447-452` |

**正确诊断不是「归因写错了」。** A3+A4 证明 `940b27c` 处的 65 与 `850ed8a` 处的 68
各自对各自的 revision 成立，归因**不算错**。真实缺陷是三条叠加：

1. **归因欠钉死**（A5）：65 这个数字在三个相邻 revision 上都成立，无法唯一反推到 `940b27c`。
2. **字段被误命名**（A9）：`written_at_head` 记 HEAD、装工作树内容，二者在脏工作树下
   构造性解耦。读者据字段名推断「账本内容 ≡ 该 HEAD 的树」必然出错。
   **这才是 A1 与 A2 并存却看似矛盾的机制。**
3. **口径从未写明**（见上文口径声明）：`65` / `68` 均为 `block_starts` 口径，
   而文件中从未限定。

### A8 — 真正不可复算的不是 65，是 `65 → 67`

`evidence/incident.md:25-26` 的账本迁移 `65 → 67`（65 + 3 additions = 68，实得 67，缺 1）
是 "How it was detected" 整节的核心论据 —— **net count 正是靠它发现 archive 吞掉了锚点**。
下表逐 revision 给出 `governance` 锚点数（`block_starts` 口径），其中**没有 8**。

实测：**没有任何 commit 持有 `governance` = 8 锚点的状态。**

| revision | governance 锚点（`block_starts`） |
|---|---|
| `940b27c` | 6 |
| `850ed8a` | 6 |
| `1612778` | 6 |
| `ea802c8` | 9 |

即 archive 吞掉 `req-gov-7` 锚点后的那个中间态**只以散文形式存活**，git 无法重建。
算术自洽（65 + 3 = 68，68 − 1 = 67）**不构成证据**。

### A10 / A11 — `.audit` 被引作第二证人，但它永不入库

`evidence/incident.md:61` 写「recorded here and in the `.audit` Errata」。

- A10：`.gitignore:37` 排除 `.audit`；`git check-ignore -v` 确认；`git ls-files .audit` = **0 tracked**（本地共 82 个文件）。该 Errata 自身在 `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md:1780-1781` 声明「本节永不会被提交」。
- A11：即使该文件在本地，`:1779` 只记了 `940b27c`、`:1836` 只记了 65 → 68，**未**记 36/23/6 拆分 —— 而 `incident.md:61-62` 恰恰把该拆分当作共有的已知信息。

⇒ **引用一个永不入库的目录作 provenance 证人，本身即缺陷。** 这是 F4 缺陷的第四半。

---

### B 组 — F5：证据层计数缺基准

被审计对象：同一 change 归档内的 `design.md`。

| # | 事实 | 位置 / 证据 |
|---|---|---|
| B1 | `strict 48 / loose 48` **可复算** | `ea802c8` = 48/48；`27336a4` = 48/48；HEAD `f1eee9e` = 49/49 |
| B2 | 48/48 与 revision 规则**同在 `### E3`** | `design.md:163-164` 与 `:168-171`；E3 标题在 `:158` |
| B3 | `## D5`(:72-78) 主题为「零检查不是通过」；`## D7`(:105-116) 为正则决策 —— **均不含** 48/48 或该规则 | 逐节读取确认 |
| B4 | E3:168「另需更正一条元事实」是**加性框架**，受责对象被点名（`D7 的这条论证`），所列 revision 全是关于「`> **Source:**` 行是否存在」的谓词 | ⇒ **scoping artifact，非真违规** |
| B5 | `design.md:170` 的「存在（L908）」**正确** | `1526b98:openspec/specs/wayfinder/spec.md` 该行确在 L908 |
| B6 | `design.md:150`「48 个脏条目」在 **`### E2`**(:144-156)，**不在** `incident.md` | 原评审报告误标位置 |
| B7 | 该数**不可复算**（未提交工作树的瞬时观测） | 无 git 对象可重建 |

**定性下调**：原 finding 称 E3「自陈规矩又违反规矩」。经 B2–B4 复核，
E3:168 是**对 D7 单条论证的追溯更正**，受责对象被点名、所列 revision 与 48/48 无关、
末句无规范标记（MUST / 一律 / 所有）⇒ **不是自违反**。

**残留的真实缺陷应正名为「无基准计数」**（B1 + B7）：
`strict 48 / loose 48` 是一个**会漂移的计数**却未附基准 revision。
B7 则是更重的一档 —— 连基准都不可能有（未提交工作树）。

### 缺陷族：F4 与 A-5 是同构的两半

`evidence/incident.md` 的账本字段（记 HEAD、装工作树内容）与证据层裸计数
（记数值、不记基准）本质是**同一个失效模式**：
**一个制品声称的基准身份与实际内容身份解耦，且该解耦不可判定。**

`.audit` A-5 段（`:1716-1720`）已自行命名这一族：「该计数本身会漂，故必须记基准……
一个不带基准的计数，会在被测对象自身变化后静默改变真值」。**写下这句话并未阻止它复现。**
`CLAUDE.md` §3 已明文「文字断言不构成可验条款」、`req-gov-7` 已规定
「a gate that cannot fail is not a gate」。

⇒ 故本 change 的两条闭合手段必须**同时**落地为机械执行，任一退化为文字义务，
该族即保持开放。

---

## 不可复算清单（与可复算数字分区陈述）

以下数字**无任何 git 对象可重建**，任何后续读者不得当作已验证事实引用：

| 数字 | 出处 | 状态 |
|---|---|---|
| `65 → 67` 账本中间态（`block_starts`） | `evidence/incident.md:25-26` | **not reconstructible from git** |
| 「48 个脏条目」 | `design.md:150` | **not reconstructible from git** |

其余本文件所列数字均附 revision，可用 `git show <rev>:<path>` 复算。

---

## C 组 — `27336a4` 的归档内改动（**本轮搁置，待独立裁决**）

被审计对象 change 于 `ea802c8`(2026-10-03 15:44) 归档。
`27336a4`(2026-10-03 23:05) 在**归档之后**写入该归档目录内部。
`5f3e286`(2026-10-04 18:56) 只回滚了 `e8efa66`，**这一处原样留在 HEAD**。

| 路径（相对 `archive/2026-10-03-a5-archive-gate-executability/`） | `27336a4` 的动作 | 现存于 HEAD |
|---|---|---|
| `evidence/_paths.py` | **新增 110 行** | 是 |
| `evidence/gen_deltas.py` | 改 19 行 | 是 |
| `evidence/verify_deltas.py` | 改 18 行 | 是 |
| `design.md` | **+74 行**（E1–E5 节，:144-190） | 是 |

`5f3e286` 的 commit message 自身承认：「Earlier in this same round I had already
edited two scripts inside the archived `2026-10-03-a5-archive-gate-executability/evidence/`
… Narrow reading is how "never" quietly becomes "usually"」—— 但该回滚未覆盖 `27336a4`。

附带不一致：E4(`design.md:173-183`) 自称修复「已在**后续 change** 中改为按内容定位
（`evidence/_paths.py`）」，而 `_paths.py` 实际落在**本 change 的归档内**，非后续 change。

**状态：已知，待独立裁决。本轮不 revert、不改归档、不加例外说明。**
登记于此以使其可被检索到，而非在下一轮 audit 中被当作新发现重新报出。

---

## What Changes

- **`req-gov-12`（governance，新增）** —— 账本基线语义固化：账本条目 MUST 与
  `written_at_head` 并列记录写入时刻的工作树内容摘要；摘要非空或缺失时，
  **仅凭 HEAD 重建基线的比对 MUST 产出 INVALID**（三态，区别于 pass 与 violation）；
  `--write` MUST NOT 因工作树非净而拒绝。
- **`scripts/run_gates.py`（`anchor-ledger`）** —— payload 增第 5 字段
  `worktree_digest`（`null` / 摘要串 / 字段缺失 三态）；`--verify` 的判定按上表改造为三态。
  摘要配方直接复用 `req-gov-8` 已定、同文件内已有的 `worktree_snapshot()` 组件，
  **不新造轮子**。
- **`scripts/lint_no_baseline_counts.py`（新增 lint）** —— 拦截证据层「无基准的计数」。
  依赖 `req-gov-7` Scenario:352-354 的 glob 自动发现，零配置入门禁，不改 `CLAUDE.md` 清单。

**关于第三项的范围**：本轮裁决原定扫描 `.audit/**`，但实测 `.audit` 为
`git ls-files` = 0（`.gitignore:37` 排除，82 个本地文件）。对 gitignored 路径设门禁
会**通过但从未生效** —— 违反 `req-gov-8`（gate 结果须可从记录状态复现），
且使 `design.md` 的判别性测试（pre-change 红 / post-change 绿）在 git 意义上不可实现。

首版因此改写为「受版本控制的证据层」，**该判据随后被复核推翻**：被审的 change 在提交前
按构造就是 untracked，以版本控制状态筛选等于用「是否已提交」筛「是否在审」，且实现里
并无该过滤 —— 结果 `.audit`（0 tracked）被排除而本 change（同样 0 tracked）被扫描。

现按 `req-gov-7` Scenario:367 收敛为**按 `GATE_CHANGE` scope 到被归档的 change**
（+ `docs/**`）：这既满足该 Scenario 的「so that unrelated stale changes in the same
directory do not determine the result」，也与 `cmd_gates` 对 `openspec validate`
已采用的 scope 做法一致。详见 `design.md` D4。

## Capabilities

### Modified Capabilities

- `governance` —— 新增 `req-gov-12`（账本基线三态语义）

### 新增 lint

- `scripts/lint_no_baseline_counts.py` —— 由 `req-gov-7` Scenario:352-354 自动纳入门禁

## 非目标（Non-goals）

- ❌ **不改任何 `openspec/changes/archive/**` 下的文件**（`req-gov-5` / `req-gov-6` + `5f3e286`）
- ❌ **不处置 C 组的 `27336a4`**（本轮搁置）
- ❌ 不改 `65` / `68` / `48` / `48` 的**数值本身** —— 这些数字经复核是对的（各对其 revision 成立）；缺陷在**归属与口径**，不在算术
- ❌ 不运行训练或 baseline（`CLAUDE.md` §6）
