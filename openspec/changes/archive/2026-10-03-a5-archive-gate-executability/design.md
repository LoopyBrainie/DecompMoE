# Design

## D1 — lint 以通配发现，不逐条枚举

**决策**：`run_gates.py` 用 `scripts/lint_*.py` 发现门禁；`CLAUDE.md` §3 改为指向
单一入口，不再列举脚本名。

**理由**：AC-20 与 AC-21 的根因是「清单」与「实际门禁」是两份可以失步的东西。
只要 §3 列举脚本，加一个 lint 就有三件事可能出错：忘记加、加错名字、加了但忘了改
文档。把发现交给 glob 之后，这个失败模式不再存在。

**代价**：§3 不再显式说明「有哪些 lint」。接受 —— 门禁清单的价值在于「门禁覆盖什么
缺陷类别」，而不是「脚本叫什么」，而这一点由 `governance` 的 Requirement 承载。

**协调**：并行 change `2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract`
的 task 8.4 也要改 §3 加它自己的 lint。本设计让那次编辑变成**不必要**：它的
`lint_no_line_pointers.py` 落地后自动被本 change 的 glob 吸收，§3 无需第二次修改，
两个 session 在同一行的写冲突消失。

## D2 — exit 2 表示「结果未知」，与 exit 0/1 区分

**决策**：门禁运行前后各采样 `git rev-parse HEAD` 与 `git status --porcelain` 的
SHA-256；不一致时输出 `GATE RESULT INVALID` 并 exit 2。

**理由**：AC-25 的失效机制不是「门禁跑错了」，而是**「通过」与「不知道」共用同一个
exit 0**。两次采样都全绿，第二次的 pass 描述的是第一次采样时不存在的文件内容。
把第三种状态单列出来，读脚本的人就无法把一次不可复现的运行读成绿灯。

**为什么用 SHA-256 而不是文件数**：两个不同的脏状态可以有相同的文件数。计数相同
不代表状态相同 —— 这与 D5 的 anchor 账本是同一条纪律。

**为什么 `HEAD` 也要采样**：并发 commit 可能在门禁运行中途落库，使工作树内容在
`git status` 视角下不变而实际基线已移。

## D3 — change 级校验只校验被归档的那个

**决策**：`--change <name>` 只对该 change 跑
`openspec validate <name> --type change --strict`，不遍历全部未归档 change。

**理由**：AC-49 要求把 change 级校验纳入归档前置条件。但若实现为「扫描整个
`openspec/changes/`」，本 change 落地第一天门禁就会报红 —— 因为两个陈旧的
`2026-09-26-followup-…` 与 `fix-review-findings-…` 至今 `exit 1`
（"Change must have at least one delta"），而它们与本次归档无关。

**语义上这也是更正确的**：归档前置条件关心的就是**被归档的那个 change 制品是否
合法**，而不是目录里所有历史遗留物是否干净。让无关的陈旧 change 决定门禁红绿，
是「门禁被关掉」最常见的实际路径。

**明确不做**：不去接管那两个 change（用户裁决），也不把「目录里没有非法 change」
写成门禁条件。

## D4 — anchor 用账本比对，不用点态计数

**决策**：`anchor-ledger --write` 产出 `{capability: {anchor_id: requirement_title}}`；
`--verify` 与当前树比对并**分列** `lost` 与 `never_added`。

**理由（AC-19）**：`openspec archive` 的 requirement block 解析器累积到下一个
Requirement 标题或二级标题为止，而本仓风格把 anchor 放在两个标题之间，于是它吞掉
被改 Requirement **之后那一个**的 `<a id>` 与其后一行空行。吞掉之后
`anchors == headings` **依然成立** —— 所以点态检查在这个缺陷上恒为绿。它只能查
「新写的 Requirement 忘了加 anchor」，查不了「anchor 被吞了」。

**为什么必须分列 `lost` 与 `never_added`**：只报计数时，`4+1-1=4`（丢一个、加一个、
丢一个）与 `4-1=3`（丢一个、没加）在原始计数上无法分辨出「是不是同一个 anchor
轮换了」。必须给逐条清单。

**块边界规则**：只有「anchor 行之后第一个非空行是 `### Requirement:`」才算块起点。
用「下一行是标题」会把块切成一行的空壳；且新插入的块级 anchor 会截断它自己的
Requirement（本仓已复现三次：req-20 因 `<a id="req-20-mci">` 发出时 0 个 Scenario）。
本 change 的 `block_starts()` 实现了该规则并有专门测试。

## D5 — 零检查不是通过

**决策**：门禁发现数为 0 时直接 exit 1，不执行「跑完所有发现的 lint，若无失败则通过」。

**理由**：`all([])` 在 Python 中恒为真。glob 静默匹配不到任何文件时，最自然的实现
会报告一次没有任何检查的绿灯。本 change 的 `test_zero_discovered_lints_is_a_failure_not_a_pass`
把这条钉死。

## D6 — AC-24：保留 marker，新增 form 检查

**决策**：不动 `DEFAULT_REQUIRED_SUBSTRING = "wayfinder/tickets/"`，新增
`REQUIRED_FORM_PATTERNS` 与检查 ①b，要求至少一个 backtick code span 匹配
`wayfinder/tickets/<ID>.md`。

**理由**：checks ②（backtick 包裹）与 ③（primary-first 顺序）是按
`len(marker)` 在 body 上做定长索引定义的。把 marker 换成正则会**静默改变这两条的
语义**。因此 marker 与 form 分离：marker 服务 ②③，form 服务 ①。

**为什么 form 挂在 marker 上而不是另建一张 path 表**：`required_form_pattern_for()`
从 `required_substring_for()` 解析出的 marker 查表。per-capability 的分派因此只有
**一个** 事实源；两张并行的 path 表是可以漂移的。

**为什么 fallback 走严格形式**：`REQUIRED_FORM_PATTERNS` 里没有的 marker 落到
`DEFAULT_REQUIRED_FORM_PATTERN`（严格 ticket 形式），而不是宽松的目录前缀 ——
一个未映射的新 capability 不该因此跳过 ①。

**`<ID>` 的形态**：`[A-Za-z0-9]+-[0-9A-Za-z]+`，覆盖本仓 23 个 ticket 的实际命名
（`A0-1.md`、`A4-1.md`、`A6a-2.md`、`A6b-1.md`、`A8-3.md`）。实测 23/23 匹配。

**对活体树的影响**：实测 45 个 `**Source:**` 行全部已使用完整文件名形式，收紧后
`lint_no_source_field_drift.py` 仍 exit 0，且 `governance` 的 `CLAUDE.md` 形式不受
影响（其 form pattern 即该字面量 —— 治理来源没有文件名可要求）。

## D7 — 明确不动 `SOURCE_LINE_RE`（AC-81 延后）

**决策**：本 change **不**修改 `lint_no_source_field_drift.py:75` 的
`SOURCE_LINE_RE = re.compile(r"^\*\*Source:\*\*")`。

**理由**：AC-81 指出行首锚定可被缩进或 `>` 前缀绕过，判定为覆盖面缺口。**该判断在
本仓当前形态下是错的**：`openspec/specs/wayfinder/spec.md` 中那行
`> **Source:**` 是 `req-19` 内对 `req-20` Source 字段的**逐字引用副本**（真字段在其
后 12 行）。若放宽正则使其接受 `>` 前缀，lint 会立刻判该行违规并 exit 1，把当前
绿灯打红 —— 修一个不存在的漏洞，制造一个真实的回归。

用户已裁决：等并行 change 收工、`req-36` 处理方式确定后重新梳理。
