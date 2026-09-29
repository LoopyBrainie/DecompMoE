# 修复 B.3 `src/` 文档漂移 B13 + 新发现 B16

## Why

Python reviewer 批次 B.3 报出 2 项 `src/` 文档漂移。经 Explore agent + 直测逐条核验：

| Finding | 位置 | 报告 severity | 核验结论 | 真实 severity |
|---|---|---|---|---|
| **B13** | `src/decompmoe/safeguards.py` docstring | MEDIUM | 成立，但根因比报告更深 | MEDIUM |
| **B16** | `src/decompmoe/safeguards.py:233` | **（报告未列）** | **本次核验新发现** | MEDIUM |

B16 属 B.3 同类（`src/` 内 stale spec 行号），原报告与 Explore 核验**双双漏判**，本 change 一并修复。

### B13 — docstring 把 vacuous self-check 写成现行契约

`resurrection_perturb_distribution` 的 docstring 以现在时陈述：`resurrect_expert` "verifies `f_per_expert.shape[-1] == β_per_expert.shape[0]`"。而实际守卫是 `f_per_expert.shape[-1] != cfg.N_e`。**同文件 `resurrect_expert` 内的注释直接否认 docstring**：

> `NOT against the input's own shape[0] (which would be a vacuous self-check for any 1-D tensor — shape[-1] == shape[0])`

即同一份文件同时陈述与否认同一个检查。

### B16 — `Req 32 L644` 是双重错误引用

原注释写 `spec Req 28 / Req 32 L644`。但 `openspec/specs/wayfinder/spec.md` 的 **L644 实为 γ 参数化 Requirement 的 `Source:` 行**（Phase 4 边界 `γ' = ln((β_p3−1)/(32−β_p3))`），与 resurrection 毫无关系。真实位置：Req 28 anchor L670、Req 32 anchor L728、`cfg.N_e` pair-check 叙事在 L732。

性质比 B14（指到同 Requirement 内的空行）更严重——**指到完全无关的 Requirement**。

## 对原报告的事实纠正

原报告含四处不准确，若不纠正会让错误数字与错误根因进入仓库认知。以下均以 `git show HEAD:<path>` 实测为准（基线 commit `7bf77af`）：

| 报告原文 | 实测 |
|---|---|
| docstring 在 `L129-130` | docstring 范围 **L112–136**，断言句在 **L128–129** |
| 权威记录在 `wayfinder` **L719**，中文「是早期草稿，已由 0b2202e 改为锚定 cfg.N_e」 | 该记录是**英文**，在 **L732**（Req 32，anchor L728）。中文字符串 `早期草稿` **全仓零命中**（`git grep -n "早期草稿"` 无输出） |
| L233 是「实际守卫」所在 | L233 确在 `resurrect_expert` 内，但**不在** `resurrection_perturb_distribution` 内——报告把两个函数的边界混为一谈 |
| （未提及） | **`0b2202e` 同时引入了这段 stale docstring** —— 这是 finding 的真正根因，报告未识别 |

### 根因：`0b2202e` 的 diff 同时做了两件事

`git show 0b2202e -- src/decompmoe/safeguards.py`（`0b2202e60d668f398aae48f1a2f106eb655ce46a`，2026-09-16 15:12:42 +0800，subject `fix(safeguards): replace vacuous β-length self-check with cfg.N_e meaningful guard`）：

1. 把 layer-2 守卫从 `!= N`（`N = β_per_expert.shape[0]`）换成 `!= cfg.N_e` —— **正确的修复**
2. **在同一批 hunk 中新增了 L123–135 那段 docstring**，其中把**被删掉的形态**写成了现行契约

所以这不是「修复时漏改旧文档」，而是「修复的同一笔把被删除的形态写进了文档」。这决定了修法：

- ❌ 删掉该行 docstring —— 会丢掉 layer-2 契约的权威说明，且与 `resurrect_expert` 内的注释失去对照
- ✅ **重写**该段为 `cfg.N_e` 锚定 + 显式标注 vacuous 形态为「早期草稿 / superseded history」

## What changes

### B13 — 重写 docstring 的 layer-2 契约段

保留正确前提（trailing axis = `N_e` 由 canonical call site 强制），把校验声明从 `β_per_expert.shape[0]` 改为 `cfg.N_e` 锚定，并追加一段说明为何 `shape[0]` 形态是 vacuous（`f_per_expert = β_per_expert.detach()` 时 `shape[-1] == shape[0]` 对任意 1-D 张量恒真）。

**不删除任何诊断信息** —— 新段落的价值之一就是防止后人再次把 vacuous 形态写回来。

### B16 — `Req 32 L644` 改为 anchor 引用

裸行号 `L644` 已被证实指错对象，且裸行号本身会随 spec 增长再次漂移（本仓已因此产生 B14）。改为引用 capability 路径 + anchor id + commit SHA：

```
(spec `wayfinder` Req 28 / Req 32, anchors `<a id="req-28">` / `<a id="req-32">`; `cfg.N_e` anchor introduced by commit `0b2202e`)
```

### 交叉引用形式：capability 路径 + anchor id + commit SHA，不写裸行号

依仓库既有 line-drift 抗性先例（`archive/2026-09-23-fix-claude-md-ticket-advisory-boundary/design.md` Decision —— 新 Requirement body 与 `Source:` 字段不引用任何 spec line number，仅引 capability 路径 + commit SHA）。

## 无 spec delta

`decompmoe-skeleton` spec 对 `resurrection_perturb_distribution` / `resurrect_expert` **完全没有 Requirement**（`git grep` 零命中），其 resurrection 覆盖仅 `should_resurrect`（Req 12）。权威源只有 `wayfinder` Req 28 / Req 32，而它们已正确表述 `cfg.N_e` 锚定。

**结论：修 `src/` 即为向 spec 对齐，本 change 不产生 spec delta，不触碰任何 spec 文件。** 这是本 change archive 零风险的根本原因。

## 不做（Non-goals）

- 不改任何可执行语句 —— 纯 docstring / 注释
- 不改写 `resurrect_expert` 内 L234–240 的其余注释（经核验内容正确）
- 不动 `wayfinder/tickets/A4-1.md`、不动任何 spec 行号（属 B14，见 change `fix-config-docstring-beta-line-drift`）
- 不处理 `src/decompmoe/safeguards.py` 工作树 CRLF 与 blob LF 的 checkout 形态差异（`.gitattributes` 的 `*.py text eol=lf` 在提交时归一化，blob 本身已是 LF；diff 纯内容，无 EOL 混入）
