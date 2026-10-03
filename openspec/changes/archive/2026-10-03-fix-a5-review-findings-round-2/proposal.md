# Proposal

## Why

`2026-10-03-a5-archive-gate-executability` 交付后经独立 review（`agent-b1a39f2827bf`），
数学层干净（scipy + mpmath 60 dps 重算 20+ 闭式全部吻合，β₀ 差 2.6e-22、σ′ 差
3.9e-34、反事实 γ_init 差 4.1e-22），但**门禁与制品层有 1 条 CRITICAL、3 条 MAJOR
和一批 MINOR 缺陷**。CRITICAL 那条使本 change 建立的核心保障在**最常见的并发形态下
失效**。

本 change 只修 review 发现的缺陷，不扩大范围。三个失效 change
（`2026-09-26-followup-…`、`fix-review-findings-…`、`2026-10-03-close-pointer-…`）
按用户裁决不接管。

## 缺陷与本 change 的对应

### CRITICAL — 门禁快照对「同路径不同内容」碰撞

`run_gates.py` 的 `worktree_snapshot` 取 `sha256(git status --porcelain)`。porcelain
编码的是**路径 + 状态字母**，不是内容。自建 repo 实测：`b.py` 已脏、内容 A 时摘要
`97c0d2fd…`，改成完全不同的内容 B 后摘要**仍是** `97c0d2fd…`。于是 exit-2 检测在
「并发 Edit 一个已脏文件」时静默失效 —— 而这恰恰是交付时刻的常态（当时工作树 48 个
脏条目）。`req-gov-8` 只满足了前半（`HEAD` 采样确实有效）。

**修法**：拆成三个各自失效理由不同的分量 —— `head`（并发 commit）、`tracked_digest`
（`sha256(git diff HEAD)`，覆盖 staged + unstaged 的**内容**）、`untracked_digest`
（`git ls-files --others --exclude-standard` 逐文件内容哈希，解决未跟踪目录被折叠成
一行）。`status_lines` 降为诊断字段，**不计入**判等：它是同一 porcelain 串的更粗函数，
当独立信号会高估指纹的分辨力。

### MAJOR — `req-gov-9` 的前提为假，且被 review 反例证伪

原 Scenario 断言：归档吞掉 anchor 后「anchor 数与 Requirement 数保持相等，点态检查仍
报全绿」。实测**相反**：删掉 `<a id="req-gov-7"></a>` 后 governance 为 9 heading / 8
anchor，点态检查**报红**。AC-19 自己给的 36→35 就是计数下降的证据。

本 change 进一步穷举了六种形态（`tests/test_run_gates.py`）：吞 anchor **总能**被点态
检查抓到，因为 `H - A` 只因吞而增大，而新增 Requirement 自带 anchor（`H` 与 `A` 同增）
无法抵消。中间一度以为「新增可掩蔽」成立，写成测试后被测试直接判负 —— 记在
`test_a_swallow_cannot_be_masked_by_simultaneous_additions` 的 docstring 里。

**账本真正多出来的东西**（这才是它该被要求的理由，且都可实测）：**指名**哪一个
Requirement 丢了 anchor（点态只给每 capability 一个缺额数字）、检测 anchor 被
**retarget**（id 仍在但引入的是另一个标题，计数相等 ⇒ 静默绿）、以及把 `lost` 与
`never_added` 分列。

### MAJOR — evidence 脚本在归档位置失效，且是本 change 重新引入的

`gen_deltas.py` / `verify_deltas.py` 用 `parents[4]` 定位仓库根。该下标只在**归档前**
成立；归档后同一位置是 `openspec/`，实测 `FileNotFoundError: openspec\openspec\specs\...`。
父 commit `1612778` 的标题正是「make the evidence tools survive archiving」—— 本 change
把它修好了，随后的重写又把它带了回来。**交付证据的 commit 让证据不可复现**。

**修法**：新增 `evidence/_paths.py` 作为唯一定位事实源，按**内容**（含 `openspec/specs`
的目录）而非深度向上查找；change 目录在 live 与 archive 两处都查。另加 preflight：
归档后重跑 pre-archive 工具时以 exit 2 说明状态不匹配，而不是抛四条会被误读为「证据
损坏」的断言失败。

### MAJOR — Source 字段覆盖率被低估 19 倍

review 实测 `decompmoe-skeleton` 23 个 Requirement 仅 4 个有顶格 `**Source:**`（缺
19），wayfinder 缺 1（`req-34`），governance 缺 0。上一轮我只记了 `req-34`，量级低估
19 倍。

### MINOR — 其余

- `skeleton req-15` 指名 `tests/test_schedule.py::test_empty_cell_preserves_centroid`，
  实际在 `tests/test_extraction.py:438`（43 处跨 Requirement 提名中 42 处可解）。
- `declared_added_anchors` 原先收集全部 anchor，会把 ADDED 块内的块级子 anchor
  （`req-20-mci`）误报为 `never_added`。
- 三个测试用变体 key 而非字面 `actual=`（非本 change 的文件，仅记录）。
- wayfinder `req-24/26/29/33` 有闭式但提名 0 测试且无机检强制（仅记录）。

## 延后与不接管

- **AC-81**（放宽 `SOURCE_LINE_RE`）：原延后条件是「等并行 change 收工、`req-36` 处理
  方式确定」。该条件**现已满足** —— `req-36` 已 REMOVE，且实测放宽后新扫到 0 行。
  本 change 内一并修复。
- **AC-57 / AC-100**：归并行 change 的 `req-gov-2` 改写与被排除的 change 目录，不接管。
- 三个失效 change 完全不碰，只在本 change 的 Errata 记录。
- **skeleton 19 个缺失 Source 不在本 change 补写**：逐条考证设计血缘才能正确填写，
  造 lineage 比缺口更糟。改为「已登记豁免 + 任何新增即失败」。

## What Changes

- `scripts/run_gates.py`：快照改内容哈希；`declared_added_anchors` 只收 Requirement 级
  anchor；`check_anchor_coverage` docstring 写实测结论而非推断。
- 新增 `evidence/_paths.py`；两个 evidence 脚本改用它。
- `scripts/lint_no_source_field_drift.py`：新增 Source 字段**存在性**检查 + 已登记豁免
  登记表；放宽 `SOURCE_LINE_RE`（AC-81）。
- `governance` spec：`req-gov-8` 改为内容摘要语义；`req-gov-9` 假前提改写；新增
  `req-gov-10`（Source 字段存在性门禁）。
- 上一 change 的 `design.md` 追加 **Errata**（不改写 D2/D4/D7 正文）。
- `CLAUDE.md` §3 点名 `anchor-ledger` 子命令。
