## Context

`openspec/specs/wayfinder/spec.md` 当前在 3 个位置保留 legacy wording，与下游真相源不一致（详见 proposal.md Why）。当前约束：
- **真相源**：骨架 spec (`openspec/specs/decompmoe-skeleton/spec.md`) + 代码 (`src/decompmoe/*.py`) + ticket (`wayfinder/tickets/A6b-2.md`)。
- **CLAUDE.md §6 第 8 条**："写 pytest 断言不能只测功能不测原理" — 强调闭式常量必须可由测试对账；本 change 修复 spec wording 是该原则的前提。
- **CLAUDE.md §3**：`/opsx:archive` 前 `lint_no_source_field_drift.py` + `lint_no_dead_defensive.py` 双 gate 必须 `exit=0`，本 change 不动 Source 字段。
- **8-21 裁决**：wayfinder tickets 不再是必改制品，本仓库以 OpenSpec 为唯一真相源；ticket 仍可作历史决策记录引用。

## Goals / Non-Goals

**Goals:**
- 把 wayfinder master spec 的 3 个漂移项与已落地的下游真相源（skeleton spec + code + ticket）三方对齐。
- 修复方式严格 minimal：仅替换/补充 wording，不删除 requirement、不引入新 requirement、不改 Source 反链、不改 Scenario 集合。
- 让后续 `lint_no_source_field_drift.py` 与 capability-internal lint 不会再因 wording drift 误报。

**Non-Goals:**
- 不改代码层（`src/decompmoe/` 任何文件）：实现已与目标 wording 对齐。
- 不改 skeleton spec L266 的同源 `L_sep/WB` 悬空引用（用户未列入本 fix；作为 explicit follow-up 在 proposal.md Impact 节列出）。
- 不重写 ticket A3-1 / A5-1 / A6b-2.md（ticket 不再是必改制品；本 change 仅作引用）。
- 不调整其它 wayfinder requirement 的 wording 或数值（除上述 3 处）。

## Decisions

### Decision 1: L64 归一化公式 — `+ ε` → `max(‖·‖₂, ε)`

**Rationale**:
- `src/decompmoe/sphere.py:50` 实现是 `z / torch.clamp(norm, min=eps)`，语义上等价于 `z / max(‖z‖₂, ε)`。
- `decompmoe-skeleton/spec.md` L401-415 "Spherical L2 Normalization" Req 已锁定 `max(·, ε)` 形式，skeleton L309 明确指出 prior `+ ε` 形式的 `[1 − 2ε, 1]` interval bound 已 obsolete。
- L93 Invariant 2 已处理 `‖u‖ < 1e-9` 退化情形（fallback 到前一个 centroid），与 `max(·, ε)` 的 ε-safety 不冲突：前者处理归一化后数值的"全零退化"，后者处理归一化时分母"小于 eps"（即便不发生 fallback，`max(·, ε)` 也保证输出范数 ≤ 1 而非 `> 1`，避免 `+ ε` 形式下 `‖z‖ ≈ 1` 时输出 `≈ 1/(1+ε) ≈ 1-ε` 的 silent norm-loss）。

**Alternatives considered**:
- 保持 `+ ε` wording、只更新 skeleton：否决 — wayfinder 是 master spec，不一致会让下游审计读 master 时仍拿到错误公式。
- 引入新 requirement 锁定 ε 值（`ε = 1e-6`）：否决 — ε-safety 语义已在 skeleton "Spherical L2 Normalization" Req 中定义，引入第二个 ε 定义会重复且增加 drift 风险。

### Decision 2: L158 "activations" → "active parameters"（minimal replace + inline reference）

**Rationale**:
- 每个 expert 的 `3 · d_model · d_ffn` 是 W^g + W^u + W^d 三矩阵的**参数量**（参看 `src/decompmoe/experts.py:29-31`，参看 `decompmoe-skeleton/spec.md` L25/154/166 验算 6_291_456 / 100_663_296）。
- Req 10 (L174) 已自洽："alignment with Mixtral's active-parameter accounting" — 这意味着 routed token 的活跃量应该用 "active parameters" 表达。
- 选 minimal replace（只把 "activations" 改成 "active parameters" + 加 inline reference 到 Req 10），不重写整句，避免无意扩展原 requirement 范围。

**Alternatives considered**:
- 完整改写为 "per routed token activates k · 3 · d_model · d_ffn parameters"：否决 — 措辞变更幅度大于需求最小化原则；minimal 替换已足够消除术语漂移。
- 删除 "per routed token" 量词：否决 — 保留以维持原 requirement 的 k 倍数语义（active parameters 与 routed token 的对应关系是 Req 10 Mixtral-style accounting 的关键信息）。

### Decision 3: L293 `WB` — 加 inline glossary，不删除符号

**Rationale**:
- WB 不是 undefined — `wayfinder/tickets/A6b-2.md` L52, 89–92 有完整定义（"WB = 0.0476 = 软正交损失的自然 baseline"），且 `L_sep / WB > 2.0` 阈值的判定逻辑也依赖该数值。
- ticket 不再是必改制品（CLAUDE.md §8 8-21 裁决），但作为历史决策记录的引用仍然有效。把定义从 ticket 提到 master spec 的 inline glossary，可消除 reader 必须跳到 ticket 才能理解 requirement 的悬空引用问题。
- 选 inline glossary 而非单独 glossary 章节：因为这只是 advisory 信号的一个符号，不需要专门的 glossary section 架构。

**Alternatives considered**:
- 删除 `WB` 符号、只保留 `L_sep`：否决 — `WB` 是 `L_sep` 与"自然 baseline" 的归一化基准，删除会让 "L_sep 偏离 baseline 多少" 的语义丢失。
- 单独建一个 `## Glossary` 章节集中定义 `WB` / `R_β-sat` 等 advisory 信号：否决 — 当前 advisory 信号集合 (R_H, S_load, R_β-sat, L_sep/WB) 中只有 `WB` 在 master spec 缺定义，单独建 glossary 是过度架构。

## Risks / Trade-offs

- **[Risk] Req 5/9/15 之外仍有未被发现 drift** → Mitigation：本 change 是 ad-hoc fix，不声称覆盖全部 drift。Skim 后的 3 处集中在公式 / 术语 / 悬空引用三类典型 drift；其他位置已在 proposal.md Impact 节标记为 out-of-scope 留作后续 audit。
- **[Risk] L64 公式修改影响 reviewer 对 spec 信任度（"已经改过几次" 印象）** → Mitigation：spec wording 历史溯源（fix-openspec-doc-bugs 已改 skeleton，now wayfinder）是必要修复；本 change 不引入数值变更。
- **[Trade-off] L158 minimal replace 保留原 wording 风格，可能让 reader 仍感语义模糊** → Mitigation：加了 inline reference 到 Req 10 (active-parameter accounting)，明确术语语境。

## Migration Plan

无。本 change 是 spec-only archive-only 修复：
- 不涉及部署、模型权重、配置、外部依赖。
- 不引入 breaking change：所有 3 处修改都让 spec wording 与现有实现/下游 spec 对齐，已实现侧无须迁移。
- Archive 完成后：`git checkout dev` → 按 CLAUDE.md §4 走 `dev → main → release` 发版（若用户决定发版；否则仅 main 存档点）。本 change 不强制发版。

## Open Questions

无。所有决策已有充分依据（详见 proposal.md Impact + 本 design.md Decisions）。本 change 不需要在 apply 阶段额外澄清的问题。