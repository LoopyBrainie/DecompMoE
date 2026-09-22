# Design

## Context

`openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/`（新 change 03 制品）由 audit-verification loop cycle-12 finding 1 触发，apply 阶段已完成 verifier F1/F2/F3 修复（line drift + principle-form pytest 守护 + test count 142→193 修正），archive 后产物完整。但 2026-09-22 独立事实验证发现：

1. **archive 制品自身 line drift 未修干净**：F1 修复做了"sync commit +19 行 drift 校准"，但 sync 之后又发生 +5 行的 drift（例如 `req-20` anchor L389 → L394），archive 制品上所有 `L389/L407/L408/L411/L445/L449` 引用全错。
2. **archive 制品 governance 元描述 self-contradict**：archive 制品声称 `req-gov-2 would only be introduced by planned 09-fix-claude-md-ticket-advisory-boundary`，但 archive 制品自身**已在** `openspec/specs/governance/spec.md` L51 添加 `req-gov-2` 锚点（documenting-only meta Requirement）——planned change 09 至今仍是 `.audit/audit-verification/opsx-changes/09-fix-claude-md-ticket-advisory-boundary/` planning 草案，未 archive。
3. **ticket A8-2 L70 + L74 引用 L408 错误**：ticket annotation 自身引用 `spec req-20 L408`，但 L408 是 SP_i 行（MCI 行在 L413）——这是 archive 制品 + ticket annotation 共同的事实错误。
4. **清单 03 主文 4 处新错误**：上一回合事实验证发现的清单 03 主文（`.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/`）4 处新事实错误（spec 行号偏差 ~24 行 + test 命名错引 + 测试数错误 142 vs 197 + 已 applied 状态）。

约束：
- 真 spec（`openspec/specs/`）行为不变——archive 制品的 fact corrections 是 audit-trail 范畴，不影响 spec-level 行为
- `.audit/` 主文 4 个文件（proposal.md + design.md + tasks.md + specs/*/spec.md）按 `.audit/README.md` L3 audit trail 完整性原则**不修改**——清单 03 主文保留作 audit-trail 历史记录，事实错误在新 change 制品的 findings.md 中记录
- archive 制品的修改本身是 post-archive fact correction（修正 verifier F1 修复留下的二次 drift），新 change 制品提供这次 fact correction 的正当理由与 audit trail

## Goals / Non-Goals

**Goals:**
- 把 archive 制品（`openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/`）5 个文件中所有过时的 spec 行号引用修正到当前真 spec 实际位置
- 把 ticket A8-2 L70 + L74 annotation 中的 `spec req-20 L408` → `spec req-20 L413`
- 把 archive 制品 governance 元描述从"req-gov-2 由 planned 09 引入"修正为"req-gov-2 由本 archive change 引入（L51 documenting-only meta），与 planned change 09 无关"
- 在新 change 制品 `findings.md` 中记录清单 03 主文 4 处新事实错误（不修改 .audit/ 主文）

**Non-Goals:**
- 不修改真 spec（`openspec/specs/`）任何 Requirement 文字
- 不修改 `src/decompmoe/` 生产代码
- 不修改 `tests/` test 行为
- 不修改 `.audit/` 主文 4 个文件（清单 03 主文 + KNOWN-DRIFT.md）
- 不修改其他 archive 制品（除本 archive 制品的目标 5 个文件外）
- 不引入新 capability
- 不修改其他 8 个 planning 草案（change 04 / 05 / 06 / 07 / 08 / 09 等）

## Decisions

### Decision 1: archive 制品修改 scope —— 5 个文件全部修正

**Choice**: 修正 archive/2026-09-20-.../ 下的 5 个文件中所有引用 archive 制品历史 spec 行号的位置：`proposal.md` + `design.md` + `tasks.md` + `specs/wayfinder/spec.md` + `specs/governance/spec.md`。

**Rationale**: archive 制品是 change-level audit trail，行号引用是 audit trail 的一部分。当前 archive 制品中的行号引用全部 stale（drift 5 行），不修正会误导 future reader（read archive 制品 + cross-check 真 spec 时会发现"行号对不上"，需要再次事实验证）。verifier F1 修复做了 sync commit +19 行 drift 校准，但 sync 之后又发生 +5 行 drift（cycle-9/12/13 spec 同步加场景测试 + governance spec req-gov-2 添加）——这是 verifier F1 修复的盲点。

**Alternatives considered**:
- (a) 仅修 `specs/wayfinder/spec.md` + `specs/governance/spec.md`（archive 制品的 delta spec 文件），不动 proposal/design/tasks —— 拒绝：proposal/design/tasks 引用更多行号（L389/L407/L408/L411/L445/L449），漏修会留下更多 stale 引用
- (b) 不修改 archive 制品，仅在新 change 制品的 findings.md 中记录事实错误 —— 拒绝：archive 制品的 stale 行号引用误导 future reader（grep spec-L389 会命中 archive 制品的 stale 引用而非真 spec）；fact correction 应直接修正 archive 制品
- (c) 删除 archive 制品并以新 change 替代 —— 拒绝：archive 是 audit trail，删除违反 `.audit/README.md` L72 audit trail 完整性原则

### Decision 2: ticket A8-2 annotation L408 → L413 同步进行

**Choice**: 修正 `wayfinder/tickets/A8-2.md` L70 + L74 annotation 中 `spec req-20 L408` → `spec req-20 L413`。

**Rationale**: archive 制品声称 spec `req-20` L408 是 MCI row，但 L408 实际是 SP_i row（MCI row 在 L413）。ticket annotation 引用 `spec req-20 L408` 是从 archive 制品 spec/wayfinder/spec.md L5 复制过来的——archive 制品的 stale 行号引用 → ticket annotation 的 stale 行号引用。修正 archive 制品的同时必须同步修正 ticket annotation，否则 archive 制品与 ticket annotation 之间产生新的不一致。

**Alternatives considered**:
- (a) 仅修 archive 制品，不动 ticket annotation —— 拒绝：ticket annotation 是 supersede annotation 的实际执行点，archive 制品是 audit trail，两者的 spec-req 行号必须指向真 spec 同一行（MCI 行 L413）
- (b) ticket annotation 改 `spec req-20 L408` → `spec req-20 L408 (SP_i row; actual MCI row at L413)` —— 拒绝：annotation 必须简洁（per CLAUDE.md §3 source-field rules canonical 形式 `(historical, ...; superseded by spec req-N L### via ...)`），注释复杂会破坏 markdown 渲染

### Decision 3: governance req-gov-2 元描述 self-contradiction 修正

**Choice**: archive 制品的 governance spec delta 与 proposal.md 中"req-gov-2 would only be introduced by planned 09"统一改为"req-gov-2 由本 archive change 引入（L51 documenting-only meta），与 planned change 09 无关"。

**Rationale**: archive change 03 已在 `openspec/specs/governance/spec.md` L51 添加 `req-gov-2` 锚点（documenting-only meta），这是 archive 制品自身的 ADDED Requirement（governance spec delta）。但 archive 制品 governance 元描述同时声称"req-gov-2 由 planned 09 引入"——这是 self-contradiction。verifier review 时未察觉这个矛盾（因为当时 planned 09 已被分类为 planned change，archive 制品写"would only be introduced by planned 09"是 forward-looking 假设，但 archive change 自身实际已添加 req-gov-2，forward-looking 假设变成 false）。

**Alternatives considered**:
- (a) 删除 archive 制品中的 governance 元描述 —— 拒绝：governance 元描述是 audit trail 的一部分（记录 archive change 03 知道 planned change 09 存在但不依赖它），删除其失证据
- (b) 把 archive 制品中的 governance 元描述改为"req-gov-2 由本 archive change 引入 + planned change 09 是独立 future governance 增强" —— 接受（实际选择）：保留 forward-looking 上下文（planned 09 仍是独立 future governance 增强），但修正"req-gov-2 由 planned 09 引入"的 self-contradict 措辞

### Decision 4: 清单 03 主文 4 处错误**不修改** `.audit/` 主文，在新 change 制品 `findings.md` 中记录

**Choice**: 新 change 制品下新增 `findings.md`（documenting-only），记录清单 03 主文事实验证发现的 4 处新事实错误（F1 行号偏差 / F2 test 命名 / F3 测试数 / F4 已 applied 状态）。**不修改** `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/` 下的 4 个主文件（proposal.md / design.md / tasks.md / specs/*/spec.md）。

**Rationale**: `.audit/README.md` L3 明确"`.audit/` 不进 git 追踪"+ L72 audit trail 完整性原则。清单 03 主文是 audit-trail 历史记录，按用户决策"在 opsx 流程内使用正确的内容即可，.audit 下标注"保留作 planning-draft 参照。fact correction 以新 change 制品的 findings.md + KNOWN-DRIFT-style 文档替代，不修改 .audit/ 主文。

**Alternatives considered**:
- (a) 在新 change 制品中直接修正 `.audit/` 主文 4 处错误 —— 拒绝：违反 `.audit/` 不进 git 追踪 + audit trail 完整性原则
- (b) 不记录清单 03 主文错误，仅修 archive 制品 —— 拒绝：Q2 用户决策"两者皆包含"明确要求把清单 03 主文 4 处新错误也纳入新 change
- (c) 在新 change 制品的 findings.md 中记录清单 03 主文错误 + 在 .audit/.../03-.../KNOWN-DRIFT.md 中追加 4 处新错误 —— 接受（实际选择）：findings.md 作为新 change 制品的 audit trail（openspec 流程内），KNOWN-DRIFT.md 作为 .audit/ 主文的 audit trail（.audit/ 流程内）；两者并行记录确保两套流程都有 evidence

### Decision 5: skip_specs = true（不修改真 spec）

**Choice**: `.openspec.yaml` 设 `skip_specs: true`。

**Rationale**: 本 change 是 archive 制品的 fact correction（行号引用 + governance 元描述），**不动**真 spec（`openspec/specs/`）。spec-driven schema 要求每个 change 必须有 spec-level delta（或显式 skip_specs），本 change 是 pure docs / archive-correction，符合 skip_specs 触发条件。

**Alternatives considered**:
- (a) 在 `openspec/specs/wayfinder/spec.md` 追加一个 documenting-only Requirement "Archive 03 line drift correction" —— 拒绝：spec 是功能规格，记录 factual drift 不在 spec 职责范围；spec 已用 `req-20 L413` + `req-22 L500` 等 anchor 描述真 spec 行为，archive 制品 drift 是 audit-trail 范畴不应污染 spec
- (b) skip_specs = false + 空 specs/ delta —— 拒绝：openspec validate 拒绝 zero-delta change

## Risks / Trade-offs

- **[Risk]** archive 制品修改被误读为"篡改历史 audit trail"。Mitigation：本次 fact correction 在新 change 制品的 findings.md + KNOWN-DRIFT-style 文档中显式记录"correction of archive 制品 line drift"作为正当理由；新 change 制品本身有完整 audit trail（proposal.md / design.md / tasks.md + findings.md）；archive 制品修改范围**限于**行号引用 + governance 元描述，不修改任何 requirement 文字、不修改任何 ticket annotation 文字（仅修 spec-req 行号）

- **[Risk]** ticket A8-2 annotation 改 "L408" → "L413" 引入新的不一致（如果 spec 又发生 drift）。Mitigation：L413 是当前真 spec 中 MCI 行的实际位置（已独立 grep 验证）；annotation 引用 spec-req 行号必须与真 spec 一致才能履行"supersede annotation 引导 reader 到 spec 真相源"的作用；若 spec 后续 drift，应通过新 change 再修正（每次 archive 制品 + ticket annotation 同步修正）

- **[Risk]** findings.md 引用清单 03 主文 4 处错误，与 `.audit/` 主文存在事实不一致。Mitigation：清单 03 主文是 audit-trail 历史记录，findings.md 是新 change 的 audit-trail 历史记录；两者都是 evidence 文档而非真相源，真相源是当前 `openspec/specs/`（行为不变）；未来 read-ticket-not-spec 实现可能同时碰到 .audit/ 主文与新 change findings，findings 的事实描述更准确

- **[Risk]** apply 阶段 archive 制品修改被 git 拒绝（archive 制品已 archive，git 视为历史 commit 不可变）。Mitigation：openspec apply 流程在新 change proposal.md / tasks.md 中显式说明 archive 制品修改范围（surgical Edit 5 个文件），apply executor 不直接 modify archive commit，而是新 change commit 与 archive commit 并列存在；future reader 通过 git log + 新 change 制品 proposal.md 追溯 archive 制品的事实修正

- **[Risk]** archive 制品中某些 spec 行号引用是 cross-reference（如 "decompmoe-skeleton spec L500-L518"），需手动核对每个 cross-reference 是否 stale。Mitigation：apply 阶段对 archive 制品中所有数字行号引用逐一独立 grep 验证（per CLAUDE.md §6 第 8 条 spec 算式必须直接对账生产代码的精神延伸至 spec 行号引用对账）

## Migration Plan

按 proposal.md What Changes 顺序执行（apply 阶段由独立 Agent 触发）：

1. archive 制品 5 个文件行号引用 fact correction：surgical Edit 替换所有 `L389` → `L394`、`L408` → `L413`、`L411` → `L416`、`L445` → `L450`、`L449` → `L454`、`L7-L25` → `L7-L23`；每个 Edit 后 `git diff --stat <file>` 验证仅目标行被修改、0 删除、LF 保留
2. ticket A8-2 L70 + L74 annotation 中 `spec req-20 L408` → `spec req-20 L413`：surgical Edit 替换 2 处；LF 保留
3. archive 制品 governance 元描述 self-contradiction 修正：surgical Edit 替换 `would only be introduced by planned 09` → `由本 archive change 引入（L51 documenting-only meta），与 planned change 09 无关`
4. 新 change 制品下新增 `findings.md`：documenting-only，记录清单 03 主文 4 处新事实错误（F1/F2/F3/F4）
5. 验证：`python scripts/lint_no_source_field_drift.py` exit=0（archive 制品不在 lint 监控范围；新 change 制品不动真 spec）+ `uv run pytest tests/ -q --no-header` 期望 197 passed 全绿（本 change 不动 src/tests/spec）
6. 单 commit on `dev`：`fix(archive-a8-2): correct archive 2026-09-20 line drift (req-20 L389→L394, MCI L408→L413, Source L411→L416, Scenarios L445/L449→L450/L454) + governance req-gov-2 meta self-contradiction + ticket A8-2 L408→L413 + findings on list-03 main text drift`

rollback: 本 change 是 audit-trail 范畴的 fact correction，rollback 即 revert commit；archive 制品回到 line drift 状态（仅影响 audit trail，不影响真 spec 行为）。

## Open Questions

（无）