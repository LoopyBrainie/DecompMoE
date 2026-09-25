# Design

## Context

See `proposal.md` for motivation. Current state:

- `wayfinder/tickets/A6b-1.md` L1（标题）= `# A6b-1: 四阶段演进逻辑` —— "四阶段" 字面
- `wayfinder/tickets/A6b-1.md` L14（Question 段第一行）= `4 阶段训练 pipeline 的具体排法：` —— "4 阶段" 字面
- ticket 自身 L48（Resolution）已锁定为 **`锁定：5 阶段编排（Phase 0–4） + ...`**（phase boundaries `1 K / 6 K / 26 K / 56 K / 100 K`，durations `1 K / 5 K / 20 K / 30 K / 44 K`），与 spec 一致
- ticket L52–58 阶段总表 + L98–132 各阶段详细动作（Phase 0/1/2/3/4 = 5 phase）已与 spec req-14 verbatim 对齐（per `.audit/spec-math-audit/spec-math-audit.md` L592 finding 2）
- `openspec/specs/wayfinder/spec.md` req-14（`<a id="req-14">` anchor at L319；Requirement title at L321 `### Requirement: Five-Phase Time-Driven Schedule`；body at L323 "**five phases** with the fixed duration ratios `1% / 5% / 20% / 30% / 44%` (i.e., 1 K / 5 K / 20 K / 30 K / 44 K steps under a 100 K total)"；Source 字段 at L325 `change \`fix-openspec-doc-bugs\` design.md (Decision 2)`）—— spec 端已是真相源
- ticket 端已有 supersede annotation 范式：
  - L101：`> (historical, N_e = 64 K-Means design from N_e=64 时代; superseded by spec req-11 MVP N_e = 16 — ...)`（引用 spec req-11 + N_e=64 → 16 change lineage）
  - L133：`> (historical, narrative-only; closed-form γ' = ln((β_{p3} − 1) / (32 − β_{p3})) lives in spec req-7 — ticket deliberately omits explicit formula as design-prose; supersede path: spec req-7 + req-14 ...)`（双反链 req-7 + req-14）

唯一 stale end 是 ticket L1（标题）+ L14（Question 段）的 "四阶段 / 4 阶段" 字面未带 historical annotation。spec ↔ src ↔ tests 三角干净，仅 ticket 头部两处 narrative 缺 supersede 标记。

## Goals / Non-Goals

**Goals:**

- 在 `wayfinder/tickets/A6b-1.md` L1（标题）+ L14（Question 段）追加 italic `(historical, ...)` supersede annotation，与 ticket 既有 L101 / L133 范式平行
- 严格遵守 `openspec/specs/governance/spec.md` req-gov-2（governance L51-67）canonical form：`<原值 reading>; superseded by spec req-N L### via <change> Decision M`，3-反链齐（ticket + spec anchor + change Decision）
- Annotation 文本以 spec req-14 L321（"Five-Phase Time-Driven Schedule"）+ L325 Source 字段（`change \`fix-openspec-doc-bugs\` design.md (Decision 2)`）为权威反链
- 完全保留 ticket L1 / L14 原措辞（"四阶段演进逻辑" / "4 阶段训练 pipeline"）verbatim —— 不删 ticket 原 narrative，符合 audit-verification cycle-7+9 决策："ticket annotation 保留决策链，禁止删除 stale 字面"
- L1 / L14 两处 annotation 文本保持**完全一致**（同 form、同 spec 反链、同 change 反链），便于 `grep` cross-validation

**Non-Goals:**

- 不修改 `openspec/specs/{wayfinder,decompmoe-skeleton,governance}/spec.md`（`skip_specs: true`；req-14 已是真相源，body / Source 字段已 verbatim 正确反映 5-phase）
- 不修改 `src/decompmoe/**` —— 无 src 端 stale，5-phase 编排已隐式按 spec req-14 实现
- 不修改 `tests/**` —— 无 test LOCKS stale 4-phase 字面
- 不修改 `CLAUDE.md`、MVPConfig、wayfinder/tickets 其他文件
- 不修复 `.audit/spec-math-audit/README.md` L223 A2.1 finding 本身的行号错误（L17 / L91 / req-14 L261 三处行号错指）—— finding text 的 fact-error 记录在 commit body / tasks.md §证据链段
- 不引入新 test（ticket annotation 是 non-executable docstring，无法 unit-test；与 `2026-09-22-fix-ticket-a6a-2-f-threshold-supersede` Decision 5 一致）
- 不触及其他 ticket 端 stale pattern（`.audit/spec-math-audit/spec-math-audit.md` L590 finding 1 N_e=64 stale ticket 端 MEDIUM —— 单独 change 处理；本文仅 scope ticket L1 / L14）

## Decisions

### Decision 1: ticket-only annotation，no spec / src / tests edits

**Choice**：仅 `wayfinder/tickets/A6b-1.md` L1 + L14 各加一行 italic `(historical, ...)` annotation；不动其他文件。

**Rationale**：

- spec req-14 L319/L321/L323/L325 已是真相源（5-phase + change 反链 `fix-openspec-doc-bugs Decision 2` 完整）
- spec ↔ src ↔ tests 三角干净（per audit-verification verify-12 + cycle-7/9 多次独立 re-verification）：src 端 Phase 0–4 编排实现无 stale；tests 无 `assert == 4` 类 LOCKS
- 唯一 stale end 是 ticket L1（标题）+ L14（Question 段）字面"四阶段 / 4 阶段"未带 historical annotation
- Edit spec / src / tests 属 scope-creep（per CLAUDE.md §3 surgical）；annotation 仅追加不删除，符合 req-gov-2 "preserve decision chain" 语义

**Alternatives considered**：

- (a) Edit spec req-14 —— rejected：spec 已正确（per audit-verification L592 finding 2 verbatim 对齐）；edit 反而破坏 spec 真相源完整性
- (b) Edit `src/decompmoe/` 任何文件 —— rejected：src 无 stale 4-phase 残留
- (c) Edit `tests/` 加新 test 守 ticket annotation —— rejected：annotation non-executable，test 不能 probe 注释；与 `2026-09-22-fix-ticket-a6a-2-f-threshold-supersede` Decision 5 同
- (d) Ticket-only annotation L1 + L14 —— chosen

### Decision 2: annotation form verbatim from req-gov-2 L55 canonical form

**Choice**：annotation 文本采用 req-gov-2 L55（governance L51-67）canonical form：

```
*(historical, "四阶段演进逻辑" / "4 阶段训练 pipeline" framing in title + Question section; superseded by spec req-14 L321 `Five-Phase Time-Driven Schedule` via `fix-openspec-doc-bugs` design.md Decision 2)*
```

具体 L1 标题处：

```
# A6b-1: 四阶段演进逻辑 *(historical, "四阶段演进逻辑" framing; superseded by spec req-14 L321 `Five-Phase Time-Driven Schedule` via `fix-openspec-doc-bugs` design.md Decision 2)*
```

L14 Question 段：

```
4 阶段训练 pipeline 的具体排法： *(historical, "4 阶段训练 pipeline" framing; superseded by spec req-14 L321 `Five-Phase Time-Driven Schedule` via `fix-openspec-doc-bugs` design.md Decision 2)*
```

**Rationale**：3-反链齐 per req-gov-2 Scenario L61-67：

1. **Ticket-side 反链**：`wayfinder/tickets/A6b-1.md` —— L1 / L14 本身即 ticket 端，annotation 上下文已含
2. **Spec-side 反链**：`req-14 L321 \`Five-Phase Time-Driven Schedule\`` —— spec anchor + 当前 title（不引用历史 L211，因 req-14 title line 漂移需 grep-confirm，apply 阶段二次核对）
3. **Change-side 反链**：`` `fix-openspec-doc-bugs` design.md Decision 2 `` —— spec req-14 Source 字段 L325 verbatim

`<原值 reading>` slot：L1 = `"四阶段演进逻辑" framing`（保留 ticket 原标题 8 字）；L14 = `"4 阶段训练 pipeline" framing`（保留 Question 段原措辞 8 字）。两者不同是因为 L1 / L14 原 narrative 字面不同。

**Alternatives considered**：

- (a) Bare `(historical, 4 阶段)` 单段 —— rejected：缺 spec anchor + change Decision 链，不满足 req-gov-2 L62 3-反链齐
- (b) 仅引用 req-14 不引用 `fix-openspec-doc-bugs` Decision 2 —— rejected：缺 change-side 反链；req-gov-2 Scenario L64 显式要求 3-反链齐
- (c) Markdown block quote `> Superseded by ...` —— rejected：req-gov-2 L55 canonical form 是 italic inline annotation，非 block quote
- (d) Inline italic `*...*` + 内部 backtick-wrapped 3 反链 —— chosen

### Decision 3: italic `*...*` wrapping + 保留原措辞 verbatim

**Choice**：annotation 文本外层 `*...*` italic wrap；ticket L1 / L14 原措辞（"四阶段演进逻辑" / "4 阶段训练 pipeline"）**verbatim 保留**，不删除、不替换。

**Rationale**：

- 保留原措辞 verbatim 是 audit-verification cycle-7+9+12+13 决策链约定（"ticket annotation 保留决策链，禁止删除 stale 字面"），避免破坏 ticket 的历史可读性
- italic `*...*` 与 ticket 既有的 `*(historical, ...)*` 范式（L133 实例）对齐，markdown 视觉上与正文区分
- 外层 italic + 内层 backtick-wrapped `\`Five-Phase Time-Driven Schedule\`` + `` `fix-openspec-doc-bugs` ``：三层 markdown inline 元素（italic 是 emphasis；backtick 是 code span），按 CommonMark 解析规则无歧义

**Alternatives considered**：

- (a) 删除原 "四阶段 / 4 阶段" 字面替换为 "5 阶段 / five phases" —— rejected：破坏决策链；与 L101 / L133 annotation 范式冲突（既有 annotation 都 verbatim 保留原值）
- (b) 改为 bold `**...**` —— rejected：与 ticket 既有 `*(historical, ...)*` italic 范式不一致
- (c) Plain text（无 italic wrap）—— rejected：markdown 视觉上与正文无区分，难以 grep 识别
- (d) Italic `*...*` + 原措辞 verbatim —— chosen

### Decision 4: L1 / L14 annotation 文本完全一致（除原措辞 slot）

**Choice**：L1 与 L14 两处 annotation 的 `<原值>` slot 不同（原 narrative 字面不同），但其余结构（spec 反链 / change 反链 / italic wrap 形式）必须 verbatim 一致。

**Rationale**：

- 便于 `grep -nE "\(historical, .* superseded by spec req-14 L321 \`Five-Phase Time-Driven Schedule\` via \`fix-openspec-doc-bugs\` design.md Decision 2\)" wayfinder/tickets/A6b-1.md` cross-validation：应返回 ≥2 hits（L1 + L14）
- 两处对称 annotation 形式防止 reviewer 误读"只 L1 修了"或"只 L14 修了"为"完整 fix"

**Alternatives considered**：

- (a) L1 / L14 各自不同 annotation 文本 —— rejected：失去 cross-validation grep 锚点
- (b) L1 / L14 共用同一 annotation 模板（除 `<原值>` slot）—— chosen

### Decision 5: skip_specs: true；no spec Requirement / Scenario added

**Choice**：`.openspec.yaml` 已设 `skip_specs: true`。无 `specs/<capability>/spec.md` delta 文件创建。

**Rationale**：

- spec req-14（`<a id="req-14">` anchor at L319；title at L321；body at L323 "five phases"；Source at L325）已正确反映 5-phase —— 无 spec-level behavior 改动
- audit-verification cycle-7 L592 finding 2 显式记录 "req-14 是'已对齐 req'" —— spec 端干净，ticket 端 L1/L14 是历史决策链记录缺漏
- `openspec validate` 接受 `skip_specs: true` 用于纯 documentation / tooling / refactor 变更；本 change 属纯 documentation ticket-annotation

**Alternatives considered**：

- (a) 加 Scenario "ticket L1 + L14 historical annotation mirrored" 到 wayfinder spec —— rejected：spec 已正确，scope-creep
- (b) 加 Requirement 在 governance spec formalize ticket-advisory-boundary —— rejected：与 change 09-fix-claude-md-ticket-advisory-boundary（per `openspec/specs/governance/spec.md` L57 NOT YET proposed/applied/archived）scope 重复；本文走 req-gov-2 已 active form
- `skip_specs: true` —— chosen

### Decision 6: 无新 test

**Choice**：无新 test 加入 `tests/`。

**Rationale**：

- ticket annotation non-executable，unit test 无法 probe 注释（与 Decision 1 (c) 同源）
- 数学 claim "five phases 1%/5%/20%/30%/44%" 已有 spec req-14 L323 verbatim 闭式 + audit-verification L592 finding 2 实证 verbatim 对齐（bare `==` 守护），ticket annotation 仅为决策链记录，不引入新行为
- Annotation form 合规（req-gov-2 canonical 形式）由 `tasks.md` §C `grep` cross-validation 守护

**Alternatives considered**：

- (a) `test_a6b1_supersede_annotation_50digit` —— rejected：annotation 非 executable
- (b) `test_phase_count_five_from_a6b1` —— rejected：phase count 已是 spec 真相源 L323 verbatim，无 test 必要
- (c) 无新 test —— chosen

## Risks / Trade-offs

- **[Risk 1]** annotation 文本与 spec req-14 Source 字段 (L325) 字面漂移。**Mitigation**：annotation 引用 `req-14 L321` (Requirement title) + `\`Five-Phase Time-Driven Schedule\`` (anchor + title verbatim) + `` `fix-openspec-doc-bugs` design.md Decision 2 `` (Source 字段 verbatim)；apply 阶段 tasks.md §B.3 grep cross-validate spec L325 ↔ ticket L1 ↔ ticket L14 三方文本 verbatim 一致（除 `<原值>` slot）。

- **[Risk 2]** annotation 误把 "四阶段 / 4 阶段" 标为 "stale" 而非 "historical"。**Mitigation**：annotation 文本用 `(historical, ...; superseded by ...)` 形式，verbatim 保留原措辞（"四阶段演进逻辑" / "4 阶段训练 pipeline"），不替换、不删除；"stale" 暗示该删，"historical" 暗示该保留 —— 形式 wording 强制后者（per audit-verification cycle-7 L895 finding 1 同模式）。

- **[Risk 3]** markdown italic / backtick / 中文嵌套渲染歧义。**Mitigation**：outer `*...*` italic + inner `` `...` `` code span；两层 CommonMark inline 元素独立解析无歧义；tasks.md §B.4 markdown-render manual check（cat 文件 / 渲染预览）。

- **[Risk 4]** Windows Edit tool CRLF 污染 ticket 文件（per memory lesson "Edit tool on Windows can introduce CRLF in non-ASCII files" 2026-09-23 + agent-memory-tail "CRLF pitfalls"）。**Mitigation**：apply 阶段 tasks.md §B.5 byte-level CRLF check (`[System.IO.File]::ReadAllBytes` + `$_ -eq 13` 计数)，与 apply 前 CRLF count diff = 0；`.gitattributes` `*.md text eol=lf` 提交时自动 normalize（pre-existing ticket 文件 LF 数=167 lines per audit-verification CRLF lesson）。

- **[Risk 5]** `.audit/spec-math-audit/README.md` L223 A2.1 finding 自身的 fact-error（"L17 / L91 / req-14 L261" 行号错指）未在本次 fix 范围。**Mitigation**：commit body 显式记录 fact-verification 结论（A2.1 finding 4 项事实错误：L17 无 annotation / L91 非 table / 4→5 阶段错位 / req-14 L261 错指）作为 audit chain；finding README L223 不修改（fact-verification 在 commit body，不污染 finding text 编号）；后续 cycle audit-verification 应 re-issue finding 或 close with 备注。

- **[Risk 6]** ticket 其他位置的 stale narrative（如 `.audit/spec-math-audit/spec-math-audit.md` L590 N_e=64 stale finding 1）被误包含本 change scope。**Mitigation**：本文 Decision 1 explicit scope: **仅 L1 + L14**；tasks.md §B.6 显式枚举本 change scope = {L1, L14}，其他 stale pattern（cycle-9 1/128、cycle-7 β_0、cycle-12 covariance、cycle-13 N_e=64）由各自独立 OpenSpec change 处理。

- **[Risk 7]** audit-verification 下次 cycle 发现 L1 / L14 annotation 与 spec req-14 line drift（spec 后续编辑 line 漂移）。**Mitigation**：annotation 引用 req-14 L321 (anchor + title verbatim) + Source 字段 L325 (decision verbatim)，line ref 在 apply 阶段二次 `grep -n "<a id=\"req-14\">" openspec/specs/wayfinder/spec.md` + `grep -n "### Requirement: Five-Phase Time-Driven Schedule" openspec/specs/wayfinder/spec.md` 验证；若 spec 后续被编辑 line 漂移，由后续 cycle audit-verification re-verification 决定是否 refresh annotation。

## Migration Plan

N/A —— 无 deployment、无 rollback、无 migration。Surgical 2 处 inline annotation：

1. Edit `wayfinder/tickets/A6b-1.md` L1：标题 `# A6b-1: 四阶段演进逻辑` 行末追加 italic `(historical, ...)` annotation。
2. Edit `wayfinder/tickets/A6b-1.md` L14：`4 阶段训练 pipeline 的具体排法：` 行末追加 italic `(historical, ...)` annotation。
3. `git diff --stat wayfinder/tickets/A6b-1.md` 应为 +2 insertions / 0 deletions（每行 inline appendix）。
4. LF / CRLF validation per tasks.md §B.5。
5. `grep` cross-validation per tasks.md §B.3。
6. `python scripts/lint_no_dead_defensive.py` exit 0（无 src edits）。
7. `python scripts/lint_no_source_field_drift.py` exit 0（无 spec edits）。
8. `uv run pytest tests/ -v` all green（无 test edits）。
9. 单条 `fix(ticket): A6b-1 L1 + L14 supersede annotation per A2.1 fact-correction (4 阶段 → 5 阶段)` commit on `dev`，Co-Authored-By trailer。
10. Commit body 含：A2.1 finding fact-correction 记录（4 项错误：L17 / L91 / 4→5 阶段错位 / req-14 L261）、spec req-14 L321 + L325 反链 verbatim、req-gov-2 canonical form 引用。

## Open Questions

- **A2.1 finding 自身 fact-error 的后续 cycle 处理** —— `.audit/spec-math-audit/README.md` L223 A2.1 finding 文本含 4 项 fact-error（L17 / L91 / 4→5 阶段错位 / req-14 L261），本 change 仅在 commit body 记录 fact-correction，不修改 finding README 文本（保持 finding 编号稳定 + 防止破坏 audit-verification chain）。后续 cycle-17+ audit-verification 是 close finding with备注还是 re-issue？Open：scope-creep 风险高，**不在本 change scope**。
- **其他 ticket 端 stale pattern 批量处理时机** —— `.audit/spec-math-audit/spec-math-audit.md` L590 finding 1（MEDIUM N_e=64 stale）、cycle-9 1/128、cycle-7 β_0、cycle-12 covariance、cycle-13 N_e=64 各自有 ticket 端 stale；当前 ticket 端 stale 修复已分散在 `2026-09-22-fix-ticket-a6a-2-f-threshold-supersede` (archived)、`2026-09-23-01-fix-ticket-stale-numerical-4file-batch` (planning)、`2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation` (本文)。是否在 LOOPS.md 累积阈值触发"批量 OpenSpec change"合并？Open：本文不 batch。
- **req-14 spec anchor line drift 后续维护** —— annotation 引用 `req-14 L321` (Requirement title) + Source 字段 L325 verbatim。spec 后续编辑 line 漂移（per agent-memory-tail "Spec migration leaves orphan anchor" lesson）会导致 annotation line ref 漂移。是否在 LOOPS.md 加 periodic re-grep 条款？Open：本文不 batch。

Co-Authored-By: Claude Code <noreply@anthropic.com>