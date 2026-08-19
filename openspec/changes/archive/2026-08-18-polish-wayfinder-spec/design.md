## Context

`openspec/changes/introduce-wayfinder-decompoe-spec/` 已通过 WF-1 审计（PASS-WITH-WARNINGS），3 项 warning 均为文档级 polish；本次 polish 还附加一项 WF-1 后由 21 ticket 逐条 deep-check 发现的 precision drift（A4-1 γ 梯度上界被 spec 简化为统一 ≤32）。本次 design 给出全部 4 项 polish 的"操作方法"——每项一个具体的、可机械校验的修法，以及修法之间的相对顺序。详见 `proposal.md - Why` 与 `proposal.md - What Changes`。

约束：
- 仅修改 `openspec/changes/introduce-wayfinder-decompoe-spec/{proposal,specs/wayfinder/spec,design,tasks}.md` 4 个文件。
- 不动 `openspec/specs/`（主 spec 尚未从 change 落出，本次也不提前落）。
- 不动 `wayfinder/` 下任何 ticket / map（formalize-only 本就承诺不动 trail）。

## Goals / Non-Goals

**Goals:**
- WF-1 的 3 项 warning 全部收敛 + A4-1 precision drift 修复，共 4 项 polish，每项留下可 grep / 可 length 校验的 mechanical marker。
- polish 后原 change 的 4 个 artifact 在语义上、形式上都与 WF-1 审计前的状态一致（仅 polish 文字层 + A4-1 单点数学精度修正）。
- 给出明确的 apply 顺序（先 spec.md 加锚点 → 再 A4-1 精度修正 → 再 design.md 改引用 → 再 tasks.md 改描述 → 最后 proposal.md 加 R/S 数），避免 apply 阶段出现"锚点已加但引用未改"的中间态。

**Non-Goals:**
- 不改任何 Requirement 标题、Scenario 内容、Source 反链、`**WHEN/THEN**` 文案；A4-1 仅在 `Isotropic Squared-Chord Distance And Bounded Beta` Requirement 体内修改"all three gradient magnitudes"一句的 per-component 表达，不动该 Requirement 的标题与 Scenario。
- 不调整 `## Purpose` 段、不调整 `## ADDED Requirements` 顺序（顺序变化会让锚点编号漂移）。
- 不引入新 Requirement、不引入新 Scenario。
- 不动 `wayfinder/tickets/WF-1.md` 的 Resolution（warning 描述保持历史记录原貌）。
- A4-1 γ 梯度上界精度修正不构成行为契约扩张：15.95 ⊂ 32，spec 由"≤32"收紧到"≤15.95"是文本精度提升，非数学保证变更。

## Decisions

### Decision 1: 锚点编号 = Requirement 在 spec.md 中出现的顺序（1..21）

为每个 `### Requirement:` 标题补 `<a id="req-N"></a>` 紧贴标题前一行（N = 1..21，按 spec.md 中自上而下出现顺序编号）。

**Why:** 锚点编号必须稳定且可预测，下游 design.md 与未来 docs / PR review 才能放心引用。顺序与 spec.md 章节顺序绑定的方案最简单、零歧义；只要 `## Purpose` 与 `## ADDED Requirements` 段的位置不动，编号就稳定。

**Alternatives considered:**
- 按 Requirement 标题的 kebab-case slug 命名（如 `#req-naming-and-alias-convention`）—— 更语义化，但 21 个 slug 都要手写、易拼写错；polish 阶段不值得。
- 按 ticket id 命名（如 `#req-a0-1`）—— 让锚点直接对应 ticket id 可读性更好；**但** A2-2 与 A5-3 在 spec 里映射到不同 Requirement，无法一一对应；**否决**。

### Decision 2: design.md 引用 spec.md 用相对路径 + `#req-N`

把对 spec.md 的 Requirement 引用从自然语言名称（如 `Naming And Alias Convention`）改为 Markdown 链接：`[Naming And Alias Convention](../specs/wayfinder/spec.md#req-1)`。

**Why:** Markdown 渲染时该链接是可点击的，PR review 时 reviewer 可一键跳到对应 Requirement；同时锚点稳定（Decision 1）保证链接不漂移。

**Alternatives considered:**
- 仍用纯文本名称但加粗（如 `**Naming And Alias Convention**`）—— 当前状态；漂移风险高，polish 必须替换。
- 用绝对路径（如 `/openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md#req-1`）—— 跨平台路径在 Windows 下表现差；**否决**。

### Decision 3: tasks.md 2.4 描述拆分判定路径

把 tasks.md 2.4 当前文本中的"appear only in `## Purpose` exclusion list or in `Source:` references to 'Future Work' sections inside tickets"改为两段独立判定：
- "appear only in `## Purpose` exclusion list"（spec 内部硬约束）
- "Future Work references inside ticket bodies are accepted audit sources via grep `Future Work` section titles"（reviewer 操作路径）

**Why:** 原文本把"spec 内排除项"与"ticket 内 Future Work"混在一条 OR 子句里，reviewer 不清楚该 grep 哪个文件、判定什么关键词。拆分后两条都是 mechanical 操作（前者 grep spec.md 排除列表；后者 grep `wayfinder/tickets/*.md` 中 `## Future Work` 段标题）。

**Alternatives considered:**
- 直接删除 2.4 项（认为 reviewer 不需要明确指引）—— 不可：WF-1 已确认 2.4 是 reviewer 的关键判断路径。
- 把指引移到 CONTRIBUTING.md—— 超范围：本次 change 是 polish 原 change 制品，不扩 OpenSpec 边界。

### Decision 4: proposal.md 的 R/S 数行只放在 Impact 段

在 `proposal.md` 的 Impact 段末尾追加一行 `本 change 交付 21 Requirements × 34 Scenarios（grep spec.md 验证）`，不再散布到 Why / What Changes。

**Why:** Impact 段是 reviewer 关注数字的天然落点（与"代码库 / 依赖 / 风险"并列）；Why 段保持简短叙述，What Changes 保持 bullet 化操作列表。

**Alternatives considered:**
- 加在 Capabilities 段—— Capabilities 已声明"无 New Capabilities / 无 Modified Capabilities"；追加数字会破坏段落的"是否产生新 spec"语义。
- 加在 Why 段开头—— Why 是 1-2 句 motivation，不放具体数字。

### Decision 5: A4-1 γ 梯度上界文本精度修正（21 ticket deep-check by-product）

把 `Isotropic Squared-Chord Distance And Bounded Beta` Requirement 的"MUST bound all three gradient magnitudes (with respect to `C`, `c_i`, and `γ`) by ≤ β_max = 32 as a hard numerical-stability guarantee"按 `wayfinder/tickets/A4-1.md` 的实际数学拆分：
- `‖∂logit/∂C‖₂` ≤ β_max = 32
- `‖∂logit/∂c_i‖₂` ≤ β_max = 32
- `|∂logit/∂γ_i|` ≤ 0.5(β_max − β_min) = 15.95

**Why:** ticket A4-1 的梯度上界表显式给出三梯度各自的精确上界（32 / 15.95 / 32）；spec.md 当前用"all three ... by ≤ 32"统一表达，把 15.95 替换成了较松的 32。这不是 behavior 变化（数学上 15.95 ⊂ 32），但 spec 文本与 ticket body 数学脱节。21 ticket deep-check 发现该 drift 后，要求 spec 文本与 ticket 一致。

**Alternatives considered:**
- 保留"≤ 32"统一表达（现状）—— 简化但 spec 与 ticket 数学 drift；polish 应修正。
- 用 15.95 覆盖所有三梯度（错误）—— C / c_i 梯度数学上是 ≤ 32 而非 15.95；不能用统一 15.95。
- 把 γ 梯度上界公式保留为参数化形式（`|∂logit/∂γ_i| ≤ 0.5(β_max − β_min)` 而不写 = 15.95）—— 接受；不过保留具体数值让 reviewer 直接看到"15.95"更直观，最终选用 15.95 显式数值。

## Risks / Trade-offs

- **[Risk] apply 阶段锚点未加但 design.md 已改引用 → design.md 链接断裂**。**Mitigation:** apply 阶段严格按顺序：先 spec.md 锚点 → 再 A4-1 精度修正 → 再 design.md 引用 → 再 tasks.md 描述 → 最后 proposal.md R/S 数；tasks.md 第 1.0 项加一条新的"锚点完整性"check 强制顺序。
- **[Risk] req-N 编号与 Requirement 标题顺序错位**。**Mitigation:** apply 阶段使用 `grep -n '^### Requirement:' spec.md` 校验编号顺序与 Requirement 数 (21) 一一对应；不依赖手工计数。
- **[Risk] polish 后 spec.md 失去"零 anchor"原貌（reviewer 可能对比 WF-1 决议中的引用方式）**。**Mitigation:** 在 tasks.md 第 1.x 项中加一行注释说明 polish 是 WF-1 的 Resolution 第 2/3 项 warning 的执行动作，不是 spec 文本扩张；reviewer 应在对比 WF-1 后再 sign-off。
- **[Risk] polish 期间原 change 的 archive 操作被打断**。**Mitigation:** 文档级明确"polish 必须在 archive 之前完成"；tasks.md 第 0 段加一条"archive gate"先决条件。
- **[Risk] A4-1 γ 梯度上界精度修正被误读为行为变化（reviewer 可能要求走 capability modification 流程）**。**Mitigation:** tasks.md 第 7 组的 R/S 行明确标注"行为契约范围未扩张（15.95 ⊂ 32）"；apply agent 在执行前向 reviewer 用单行注释说明"spec 文本由 32 收紧到 15.95 是数学精度提升，非系统行为变更"。

## Migration Plan

1. apply 阶段开始前确认 `openspec/specs/` 为空（原 change 未 archive）。
2. 按 Decisions 顺序修改 4 个文件（含 A4-1 精度修正作为 Decision 5）。
3. 跑 `openspec validate introduce-wayfinder-decompoe-spec --strict` 确认 polish 后仍 valid。
5. 跑 `openspec validate polish-wayfinder-spec --strict` 确认本 change 自身 valid。
4. archive 顺序：先 archive `polish-wayfinder-spec`（把 polish 落入 change log），再 archive `introduce-wayfinder-decompoe-spec`（拿到 polished 版本落主 spec）。

## Open Questions

无。3 项 WF-1 warning + 1 项 A4-1 precision drift 的修法均已明示，仅缺 mechanical 执行。