## Context

本 change 是 `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/`（简称"audit change 01"）的 scope fidelity 修订。audit change 01 当前**仅是 evidence library 内的 planning 制品**（不进 git per `.audit/README.md` L5），其 apply 阶段需先把 planning 制品对齐到事实层后才能落地。

事实层 ground truth（per 上一轮事实验证脚本 `verify_numerical_claims.py`）：

- 15/15 数值闭式独立 mpmath 50-digit 复算 PASS（σ(−3.5) / σ'(−3.5) / β_0 / θ_Voronoi / 反向 γ / MVPConfig diff 等）
- 17/17 文本 verbatim grep PASS（A5-3 L62 / A4-1 L58 / A1-1 L97 / config.py L54 / test_beta.py L38 / spec L120/L122/L124/L126/L185/L247 / beta.py L30-31 / MVPConfig 11 字段等）
- 4 处 scope fidelity findings（F1-F4）—— 详见 proposal.md Why 表

本 change **仅**修订 audit change 01 的 proposal.md + design.md 文本，**不**触 spec / 代码 / 测试 / git 树。

## Goals / Non-Goals

**Goals:**
- 在 audit change 01 的 proposal.md / design.md 中**完整声明 A1-1 L97 在 scope 内**（F1 + F4 闭合）
- 把"4-file batch"改为"5-file batch"以反映真实 scope（F2）
- 在 proposal Why table 加 base convention 声明（F3）—— 哪个 base 对应哪个 relative 数字
- **不**触 audit-verification.md / spec-math-audit.md 历史 audit 报告（避免越权修改 ground truth）
- **不**触 wayfinder/tickets/A1-1.md 实际内容（apply 阶段负责）

**Non-Goals:**
- 不修改 `openspec/specs/**` —— skip_specs: true 已声明
- 不修改 src/ / tests/
- 不修改 governance/spec.md（无新 governance 条款）
- 不修改 audit-verification.md / spec-math-audit.md 历史 audit 报告（ground truth）
- 不修改 wayfinder/tickets/A1-1.md 实际内容（仅修 planning 制品的覆盖声明）
- 不引入新 MVPConfig 字段 / 新 cfg 形参 / 新算法常量
- 不重写 change 01 的算法设计（仍是 surgical spec delta + 4 文件边界修改 + 2 处 spec delta —— 但 4→5 文件，加 A1-1 L97）

## Decisions

### Decision 1: A1-1 L97 处置策略 —— 走与 A5-3 L62 平行路径

**Choice**: A1-1 L97 的 supersede annotation 与 A5-3 L62 完全平行 —— 仅追加注释不删原值；annotation 格式 `(historical, θ_Voronoi≈52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)` 与 A5-3 L62 完全相同。

**Rationale**: audit-verification.md L132 字面锁定 `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°` —— A1-1 与 A5-3 是 cycle-5 #1 finding 的**两个 ticket 端源头**（前者是 16×16=256 cell 容量表的源估算，后者是 N_e=16 → 4070 MVP 修订说明的源估算）。spec req-11 L185 bisection 真相是 `θ_Voronoi(16,16) = 1.1735474259 rad = 67.24°`，所以两条 ticket 端 stale 都走"追加 supersede annotation → 保留原 ~52° 不动"路径。

**Alternatives considered**:
- (a) 删除 A1-1 L97 `θ_Voronoi≈52°` 改 `67.24°` —— 拒绝：与 A5-3 L62 处置不一致；破坏 ticket lineage（reader 无法追溯 2026-08 A1-1 决策时为何用 ~52°）
- (b) A1-1 L97 不修，仅修 A5-3 L62 —— 拒绝：违反 audit-verification.md L132 字面锁定的完整性要求；tasks.md B1.2 已显式列出 A1-1 L97 修改（ground truth），反向对齐更稳
- (c) A1-1 L97 重写整个段落 —— 拒绝：超出 scope（CLAUDE.md §3 surgical 原则）；A1-1 L97 是 ticket 内段落说明，重写会影响其他 ticket 引用

### Decision 2: change 名 "4-file batch" → "5-file batch"

**Choice**: change 目录名保持 `01-fix-ticket-stale-numerical-4file-batch/`（**不重命名** audit 目录）；但 proposal.md / design.md 文本中"4-file batch / 4-file 边界修改"统一改"5-file batch / 5-file 边界修改"。

**Rationale**: 
- **不重命名目录**: `.audit/audit-verification/opsx-changes/01-...` 目录名已被 audit README L40 + audit-verification.md 多处引用；rename 会破坏 cross-reference。
- **修文本**: 实际 scope 是 5-file（含 A1-1），文本需对得上。

**Alternatives considered**:
- (a) 目录 rename 为 `01-fix-ticket-stale-numerical-5file-batch` —— 拒绝：cross-reference 损坏
- (b) 把 change 名改为 `01a-fix-scope-fidelity-f1-f4` —— 拒绝：本 change 是 follow-up 而非原 change 的真值替代；原 change 文本修订后即可

### Decision 3: F3 base convention 声明 —— 显式双 base 并存

**Choice**: proposal.md Why table cycle-5 #1 行写 `15.24° absolute (29% relative-to-ticket-base / 22.7% relative-to-truth-base)` 并加表头注脚说明 `audit-verification.md 用 29% (base=ticket stale 52°)、spec-math-audit.md 用 22.7% (base=spec truth 67.24°)`。

**Rationale**: 不强行统一 base —— audit-verification.md 是元审计结论（用 29% 表达"old ticket 估算偏差")、spec-math-audit.md 是初审计结论（用 22.7% 表达"相对真相偏差"）。两个 base 都是真实有用的视角。**显式声明**让 reader 知道两个数字都对，只是 base 不同。

**Alternatives considered**:
- (a) 统一用 22.7% (truth base) —— 拒绝：违反 audit-verification.md 已落盘的字面 `29% 相对`；reader 会困惑为何 proposal 数字与 audit-verification.md 数字不一致
- (b) 统一用 29% (ticket base) —— 拒绝：违反 spec-math-audit.md L134 字面 `22.7%`；同上
- (c) 不声明 base —— 拒绝：reader 无法判断哪个数字对应哪个 base，本 change 价值打折

### Decision 4: skip_specs: true —— 不引入 spec 行为变化

**Choice**: 本 change `.openspec.yaml` 设 `skip_specs: true`。

**Rationale**: 本 change 是**纯 process/scope-correction**（仅改 planning 制品文本），不引入任何 spec-anchored 行为变化。per openspec-propose skill 模板: "A change with no capabilities at all (pure refactor, tooling, docs) must set skip_specs: true in its .openspec.yaml - openspec validate rejects a zero-delta change without that marker." audit change 01 本身的 spec delta（req-7 L122 σ' precision + L126 Source 字段补齐）**不**通过本 change 实施 —— 由 audit change 01 自身的 apply 阶段负责（apply 阶段会从 audit evidence 库读到 tasks.md B1.1/B1.2/B2.1 spec delta 的 source-of-truth，已含全部 spec 改动）。

**Alternatives considered**:
- (a) 不设 skip_specs —— 拒绝：openspec validate 会拒绝 zero-delta change；本 change 确实没有 spec delta
- (b) 在本 change 内引入 spec delta —— 拒绝：超出 scope（CLAUDE.md §3 surgical）；audit change 01 的 spec delta 已在自身 apply 阶段有 source

### Decision 5: 不修改 wayfinder/tickets/A1-1.md 实际内容

**Choice**: 本 change **不**触 wayfinder/tickets/A1-1.md 文件本身（仅在 audit change 01 的 planning 制品中**声明** A1-1 L97 在 scope 内）。A1-1.md 的实际 supersede annotation 由 audit change 01 的 apply 阶段实施。

**Rationale**: 
- 本 change 是 planning 制品修订，目标是让 change 01 的 proposal/design 文本**正确反映** scope —— 不直接实施 scope。
- 涉及的 surgical Edit 操作（proposal/design 文本）落在 `.audit/audit-verification/opsx-changes/`（不进 git），**与** audit change 01 apply 阶段的 surgical Edit（落在 `wayfinder/tickets/` + `src/` + `tests/` + `openspec/specs/`，进 git）属于**不同**的操作。
- 这样分离的好处：scope fidelity 修订可单独 review/apply，不污染 git 树。

**Alternatives considered**:
- (a) 本 change 也直接改 A1-1.md —— 拒绝：scope 蔓延（CLAUDE.md §3 surgical）；apply 阶段负责实际 ticket 修改
- (b) 本 change 只声明 A1-1，不改 audit change 01 任何文件 —— 拒绝：达不到 scope fidelity 修订目标

## Risks / Trade-offs

- **[Risk]** proposal.md / design.md 多处 Edit 累积行数变化可能触 LF/CRLF 不一致（per [[windows-edit-crlf-pitfall]] memory）。**Mitigation**: 每个 Edit 后跑 `file <name> | head` 看 encoding；CRLF 必要时 `sed -i 's/\r$//'`
- **[Risk]** F3 base convention 声明可能让 reader 困惑（两个数字并存）。**Mitigation**: 表头注脚明示 base 来源；后续若用户决策统一 base convention，可另开 follow-up change
- **[Risk]** 本 change 跳过 spec delta（skip_specs: true）但 audit change 01 自己有 spec delta，可能让 audit change 01 apply 阶段跳过 spec delta 落盘。**Mitigation**: audit change 01 的 proposal.md `What Changes` §A 明确列出 2 项 spec delta（req-7 L122 σ' + L126 Source 字段）；apply 阶段按 tasks.md A1.1 + A2.1 落地。**两个 change 的 scope 完全独立**
- **[Risk]** audit change 01 的 tasks.md B1.2 "Done in propose phase" checkbox 已勾选 —— 暗示 B1.2 已在 propose 阶段实施。但实际 A1-1.md 文件未被修改。**Mitigation**: 本 change 不改 tasks.md（保持 ground truth）；apply 阶段前 audit change 01 的 tasks.md B1.2 checkbox 应 uncheck 以反映真实状态（这是 audit change 01 apply 阶段前置清理，非本 change scope）
- **[Risk]** governance compliance: skip_specs=true 触发 lint_no_source_field_drift.py 默认预期 change 含 spec delta —— 需 lint 工具支持 skip_specs 例外。**Mitigation**: 跑 `python scripts/lint_no_source_field_drift.py` 验证 skip_specs=true 通过；如工具不识别，调用方需手动确认

## Open Questions

- **F3 base convention 跨 audit 文档是否需统一**: 当前本 change 在 audit change 01 内部声明双 base 并存；但 audit-verification.md（用 29%）与 spec-math-audit.md（用 22.7%）的 base 不一致是否需要 follow-up 修订？本 change 不预先承诺 —— 待用户决策
- **audit change 01 的 tasks.md B1.2 checkbox pre-checked 问题**: tasks.md 把 A1-1 L97 的修改标为 `Done in propose phase`，但实际 A1-1.md 文件未改。apply 阶段前 audit change 01 的 maintainer 是否需手动 uncheck？本 change 不预先承诺 —— 由 audit change 01 的 apply 阶段决定
- **跨 audit 文档的 4→5 file batch 一致性**: 本 change 仅修订 audit change 01 内部一致；audit-verification.md / spec-math-audit.md / audit README 是否也需要修订 "4-file batch" 提法？本 change 不预先承诺 —— 由用户决策 follow-up scope