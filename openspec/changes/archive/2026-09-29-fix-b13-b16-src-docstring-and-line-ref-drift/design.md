# Design — B13 docstring 重写 + B16 行号引用修正

## Decision 1：B13 用「重写」而非「删行」

**Choice**：把 docstring 的 layer-2 契约段整体重写为 `cfg.N_e` 锚定表述，并**追加**一段显式标注 `shape[0]` 形态为早期草稿 / superseded history。

**Alternatives**：

- **(a) 只删掉 L128–129 两行** —— 拒绝。docstring 会退化成只说「由 canonical call site 强制」而不说强制的是什么；且 `resurrect_expert` 内的 L237–238 注释（解释为何不用 `shape[0]`）将失去 docstring 侧的对照，读者无从得知 primitive 与 wrapper 的分工依据。
- **(b) 只把 `β_per_expert.shape[0]` 替换为 `cfg.N_e`，其余不动** —— 拒绝。会让读者以为这是一个「自检」而非「外部锚定」，而两者的健壮性差异（vacuous vs meaningful）恰恰是 B13 的核心。删掉理由等于删掉防复发信息。
- **(c) 删掉整个 docstring 段，改为指向 spec** —— 拒绝。违反 CLAUDE.md §3「文档/契约写得越细越好」；且 spec 用英文、docstring 是该 primitive 的就近契约说明，就近信息有价值。

**Rationale**：`0b2202e` 的根因是「修复的同一笔把被删形态写进文档」。若只做替换，未来仍可能因不了解原因而改回；显式记录 vacuous 机理（`detach()` 使两轴同形）才能形成闭环。

## Decision 2：B16 改用 anchor id 而非修正后的裸行号

**Choice**：`(spec \`wayfinder\` Req 28 / Req 32, anchors \`<a id="req-28">\` / \`<a id="req-32">\`; \`cfg.N_e\` anchor introduced by commit \`0b2202e\`)`

**Alternatives**：

- **(a) `L644` → `L732`** —— 形式上最小改动，但**与 B14 的修法哲学冲突**：B14 之所以要改，就是因为裸行号会随 spec 增长漂移（本仓已实证两次）。在同一个 change 里对两个同类引用采取两种策略，会让「哪些行号可信」失去统一口径。
- **(b) 写 `L670 / L728`** —— 同 (a) 的问题。

**Rationale**：anchor id 是 spec 制品的稳定标识（CLAUDE.md §6 硬约束要求每个 Requirement MUST 设独立 anchor，100% 覆盖），裸行号不是。仓库已有明确先例采纳 anchor / SHA 形式（`archive/2026-09-23-fix-claude-md-ticket-advisory-boundary/design.md`）。

**Note**：本 change 的 B13 段与 B16 段一致采用 capability 路径 + anchor id + commit SHA，三处引用形式统一。

## Decision 3：不产生 spec delta

**Choice**：本 change 只改 `src/decompmoe/safeguards.py`，**不创建 `specs/` 目录**。

**Rationale**：`decompmoe-skeleton` spec 对 `resurrection_perturb_distribution` / `resurrect_expert` 无任何 Requirement（零命中）；权威源 `wayfinder` Req 32 已正确表述 `cfg.N_e` 锚定并明确 `shape[0]` 形态为 early draft。**漂移在 `src/` 侧单方面**，改 `src/` 即闭合。

**Consequence**：本 change 不触碰任何 spec 文件 → archive 时无 MODIFIED block 边界判定风险 → archive 零 anchor 损坏风险。这是把它排在三个 change 首位执行的理由。

## Decision 4：CRLF 处理

**Choice**：不触碰工作树 `src/decompmoe/safeguards.py` 的 CRLF 形态，让 `.gitattributes` 的 `*.py text eol=lf` 在提交时归一化。

**Evidence**：`git cat-file blob HEAD:src/decompmoe/safeguards.py` 显示 blob 的 CR 字节数 = **0**（LF）。工作树是 CRLF（CR=289），属 checkout 形态。`git hash-object --path=src/decompmoe/safeguards.py`（应用 attributes 滤镜后）等于 `git rev-parse HEAD:...` → 提交不会产生整文件 EOL 改写。

**Rationale**：「顺手统一 EOL」超出请求范围，且会污染 diff、增加 review 成本。已实测 `git diff --numstat` 为 21 插 / 10 删（纯内容），确认无 EOL 混入。

## Risk

- **[Risk] 未来 spec 再增行，anchor id 稳定但 L-number 漂移** —— 本 change 已规避（不写裸行号）。
- **[Risk] docstring 变长（+11 行）** —— 接受。信息增量是 vacuous 机理说明，属契约正确性内容，非冗余。
- **[Non-Risk] 行为零变化** —— 改动全部落在 docstring 与注释内，无可执行语句被触碰；`uv run pytest` 应与改动前逐项一致。
