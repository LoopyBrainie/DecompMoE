# Proposal

## Why

两份审计台账（`.audit/gradual-review-2026-10-07/lists/opsx-changes.md` 与 `direct-fixes.md`）把测量基线钉在 `dde0e1d`（261 commits），而 HEAD 已是 `ded0944` —— **中间落了 7 个 commit**。其中 `opsx-changes.md` 自述「8 条均无 `status` 字段」（`:216`），于是已修复项与开放项在文本上**完全同形**，读者无法分辨死活。

本轮在 `ded0944` 逐条复验该桶 8 条（分母与逐条证据由 `evidence/reverify_opsx_changes.py` 产出），实测 **3 条已闭合、1 条收窄、3 条仍开放、1 条系条目自身陈述错误**，而台账记 0 条：

| ref | ledger 记 | `ded0944` 实测（`reverify_opsx_changes.py`） |
|---|---|---|
| FIX-001 | `tests/` 48 处调用点漏 `rtol` | `tests/` 43 处、`src/` 1 处，违规 0；`df4a1d2` 另加 `lint_no_implicit_relative_tolerance.py` |
| FIX-006 | `metrics.py:152` 全死 SP 返回 `0.0` | 现返回 `NaN`（`642d8e9`） |
| FIX-007 | req-30 一行三处缺陷 | req-30 已重写：`c ⟂ C` 降为 one WITNESS、离球面式标 WRONG、`β_max` 明定 supremum（`c568803`） |
| FIX-020 | 阈值规则是枚举白名单 | **收窄**：req-gov-1 与 pin 逐字相同；`df4a1d2` 新增的是 **req-gov-13/14/15/16**（另一条 Requirement），只覆盖了「默认值」一半，未覆盖「阈值推导」一半 |
| FIX-029 / FIX-041 / FIX-042 | 开放 | 仍开放（FIX-041 台账记的引用数在任何口径下均不可复现；`openspec/specs/` 下 pin 与 HEAD 均为 0） |
| FIX-034 | req-11 未把「带种子 MC 估计」与不等式同处 | **归 `ENTRY_MISSTATED`**（`design.md` D-1 第五值）：该陈述在 pin 时即不成立 —— req-11:263 在 pin 与 HEAD 逐字相同。属条目自身陈述错误，见下 |

更严重的是 **FIX-029 条目自身自相矛盾**：其 `evidence` 行写「`d_c=16` 绿、`d_c=64` 红，`eigvals[0] = +1.1e-08` vs `−7.5e-09`」，而实测（`HEAD = ded0944`，由 `evidence/reverify_fix029.py` 产出）是 16 → `−7.5e-09`（绿）、64 → `+1.1e-08`（红）。按字面读，该行的数字与它自己的标签**相反** —— 幅值抄对了，归属调换了。读者无论信标签还是信数字都拿不到一致结论。

在这样一份清单上动手修 L3，等于按 `dde0e1d` 距今 7 个 commit 前的现实施工，并把被污染的证据写进新 change。

## What Changes

- **台账重基线**：以 `ded0944` 重新复算 `opsx-changes.md`。该桶 8 条逐条追加 `**HEAD 复验（ded0944）**` 字段，取值域为 `design.md` D-1 的**五值闭集**；pin 由 `dde0e1d` 更新为 `ded0944`。`direct-fixes.md` 只更新 pin，条目裁定由后续 change 承接。
- **FIX-034 自缺陷更正**：条目的 problem 段与被引文本相反，且台账自身的复核段已登记该相反。不存在「修复 commit」可指名 —— `33f7cc9`（2026-09-30）是 pin（2026-10-08）的**祖先**，不在漂移窗口内；req-11:263 在 pin 与 HEAD 逐字相同。本 change 将其改判为 `ENTRY_MISSTATED`，不写入 `**修复 commit**`。
- **FIX-029 自缺陷更正**：evidence 行的数值归属对调回实测值；`problem` 段「而非由数学决定」收窄为「按绝对阈值定秩不可判定，且 `:166` 是单边断言」；`consequence` 段「红绿不可解释」收窄为仅 `d_c=64` 的红；`「1e-10` 只活在测试与散文里`」改为「两处可执行字面量」；删去「与 FIX-023 中 `0.0476` 的情形同类」（FIX-023 不在本条 `crossrefs`，且属另一份清单的 DIR-4，对象是 `wayfinder/tickets/A6b-1.md` 的 `(historical` 缺标注）。
- **`direct-fixes.md` 的同口径复验**（与上一条同等对待，非抽样）：以 `classified.json` 的 `bucket == direct-fix` 计数为分母，逐条核对渲染出的 `### ` 条目。本轮初稿曾记「标题 32 条 vs 实测 31 条，差 1」，该陈述**是错的** —— 错因是核对用的 grep 正则 `^### \(FIX\|CFL\|CTX\|OPX\)` 排除了 `ARC-002` 与两个中文小节标题（`不重不漏` / `本节明确不覆盖的范围`）。改正后实测 **32 条，与分母逐个相等，不存在差额**。该误判本身登记在案：它与 FIX-029 的 evidence 归属对调是同一类失效 —— 机械核对命令的正则写窄了，结论却按未受影响的读法写下去了。
- **BREAKING（对该制品的读法）**：`opsx-changes.md` 新增 `**HEAD 复验（ded0944）**` 字段，取值域为 `design.md` D-1 的五值闭集。既有 `**status**` 字段保持原义不动 —— 它记的是上游 ledger 是否带 status，是溯源注记而非存活裁定。任何按「有 `status` 即已裁决」解析该文件的读法需要更新。
- **BREAKING（对 pin 的读法）**：两份清单顶部的「测量基线」由 `dde0e1d` 改为 `ded0944`。任何引用旧 pin 行号的外部制品需要复核。

**不做**（明确移出本 change，理由随附）：

- **不修 L2 工作树那 3 处未提交改动**。`wayfinder/tickets/WF-1.md` 删掉了两处 `(historical, ...)` supersede 标注，而该标注是归档 change `2026-09-20-fix-ticket-a6a-2-f-threshold-supersede` 的交付物；门禁不报红（`lint_ticket_annotation_form.py` 不要求该特定标注），但它重新打开了 `req-gov-4` 监控的 ticket 污染通道。仓库无法判定这是有意撤回还是误删，需人工裁决，本 change 只登记为 Open Follow-up。
- **不修 L3 的真实 spec/test 缺陷**（FIX-029 阈值本身、FIX-041 的 `req-gov-9` 悬空引用、FIX-042 的 Source 豁免）。这些的取舍**依赖本 change 的复验输出**；在清单可信之前写 spec delta，等于用一份已知失真的输入去改真相源。它们是本 change 完成后的第一批后续 change。FIX-034 不在此列 —— 它不是缺陷，而是条目自身陈述错误，由上面的自缺陷更正处理。
- **不删两个空的 change 目录**（`fix-review-findings-voronoi-precision-and-lineage/` 完全空、`2026-09-26-followup-.../` 仅空 `specs/`）。前者被 `openspec/specs/` 活引用 2 次、archive 引用 127 次，删除会改动 `governance/spec.md`，与本 change 的 `skip_specs: true` 冲突。登记为 Open Follow-up。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。**本 change 不修改任何 requirement**，因此 `.openspec.yaml` 声明 `skip_specs: true`。副作用之一：本 change 无 spec delta，结构上不可能触发带 delta 的 change 在 archive 时吞掉 anchor 的那一类缺陷。

## Impact

- **`.audit/gradual-review-2026-10-07/lists/opsx-changes.md`**：pin 更新；8 条新增 `**status**` / `**修复 commit**`；FIX-029 的 evidence / problem / consequence / crossrefs 四处更正；文末自检小节增补本轮复核记录。该文件在 `.gitignore` 内、**不受版本控制**，故本 change 依赖 `evidence/` 下的 pre-edit 快照做结构回验（沿用 `2026-10-03-fix-a6-...` 的做法）。
- **`.audit/gradual-review-2026-10-07/lists/direct-fixes.md`**：仅 pin 更新。该文件**无生成脚本**，只能手术式改写。条目逐条裁定不在本 change —— 机械判定可完成的 9 条（判据：`dde0e1d..ded0944` 窗口内被引文件零 commit，见 `evidence/reverify_direct_fixes.txt`）已落 evidence，其余具名移交（见 `tasks.md` 的 `## Workflow follow-up`）。
- **本 change 的 `evidence/`**：只读复算脚本 + pre-edit 快照 + 复验结论，全部为只读分析或对上述两份制品的定点写入。
- **不触碰**：`openspec/specs/**`、`src/**`、`tests/**`、`wayfinder/**`、`openspec/changes/archive/**`。
- **无 API / 依赖变更**，不触碰训练执行（`CLAUDE.md` §7 out of scope）。
- **门禁现状：红**。`uv run python scripts/run_gates.py` 当前 `GATE FAIL`，唯一失败项是 `lint_no_baseline_counts.py` —— 本 change **自身**的三份制品含无基准计数。pytest 侧基线 `549 passed, 1 skipped`（`ded0944`）未变，其余 6 个 lint 均 PASS。本 change 必须先让这三份制品通过该 lint，才谈得上「门禁无感」。
