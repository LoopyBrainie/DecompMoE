# Design

## Context

本 change 关闭 `.audit/audit-verification/` 元审计循环 (2026-09-18/19) 锁定的 3 条**叙事层 wording drift** finding (见 `proposal.md` Why 段). 3 条 finding 均 LOW 评级, doc-level 修补, 不动算法/契约/数值.

**当前状态 (per 2026-09-22 事实验证)**:
- `openspec/specs/wayfinder/spec.md` L12 wording "preserve" 待微调为 "adopt (per CLAUDE.md §1 ...)" (NAR-1 待 apply)
- `openspec/specs/wayfinder/spec.md` L24 h 域未显式声明, 需追加 `(i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S)` 域声明 (NAR-2 待 apply)
- `openspec/specs/wayfinder/spec.md` L126 Source 字段**已含** A4-1 + A4-2 + A6b-1 (NAR-3 已满足, verify-only)

**约束** (per CLAUDE.md §3 + §6):
- surgical no-op: 仅 spec wording 微调, 不动 src/ / tests/ / tickets
- anchor 100% 覆盖守: 3 锚点 (`<a id="req-1">` / `<a id="req-2">` / `<a id="req-7">`) 不动
- 现有 197 tests (per `uv run pytest tests/ --collect-only -q` 2026-09-22 实测) 全绿即证明无 regression

## Goals / Non-Goals

**Goals:**
- 关闭 3 条 audit-verification LOW wording drift finding (cycle-1 finding 1 / cycle-2 finding 1 / cycle-7 finding 3)
- 维持 spec ↔ ticket ↔ CLAUDE.md fact 三方一致 (CLAUDE.md §2 真相源层级不变)
- NAR-1/2 wording 微调 + NAR-3 verify-only
- anchor 100% 覆盖守 (3 锚点不动)
- lint gate 2 项 (`lint_no_dead_defensive.py` + `lint_no_source_field_drift.py`) PASS
- 现有 197 tests 全绿 (无 regression 因不动 src/ / tests/)

**Non-Goals:**
- 不动 `wayfinder/tickets/` 任何文件 (CLAUDE.md §6 第 7 条 + §8 tickets reference-only)
- 不动 `src/` 任何文件 (CLAUDE.md §3 surgical 原则)
- 不动 `tests/` 任何文件 (CLAUDE.md §3 surgical 原则)
- 不动 `openspec/specs/decompmoe-skeleton/spec.md` (骨架 spec 不在改动范围)
- 不动 `openspec/specs/governance/spec.md` (governance 反链 `CLAUDE.md` 而非 `wayfinder/tickets/`)
- 不动 `MVPConfig` 任何字段 (cycle-5/6/7 数值层 finding 已在 `01-fix-ticket-stale-numerical-4file-batch/` 处理)
- 不动 wayfinder spec 其它 6 锚点 (`<a id="req-3">` ~ `<a id="req-9">`), 不动其它 Requirement 主体
- 不动 L24 末尾 code identifiers 列表 (含 `territory_seeding`, 与 cycle-15 finding 1 有关但与本 change 无关)

## Decisions

### Decision 1: NAR-1 wording 微调方向 —— "preserve" → "adopt (per CLAUDE.md §1 ...; not previously a canonical name)"

**Choice**: spec L12 `MUST preserve **GeoMoE**` → `MUST adopt **GeoMoE** as a documented alias (per CLAUDE.md §1 project-level amendment; GeoMoE was never previously a canonical name — it is a deliberate alias upgrade, not a downgrade)`.

**Rationale**: cycle-1 finding 1 (audit `audit-verification.md` L1624+ verify-22 section) 实证 spec "preserve" 暗示 GeoMoE 曾是规范名、后被降为别名. ticket `A0-1.md` L29 真实记录 GeoMoE 从未被选为规范名 (标 "考虑过的备选"). CLAUDE.md §1 amendment 行为把 GeoMoE 主动升格为 alias (而非降级). 本 change 微调:
- "preserve" → "adopt" 与 ticket `A0-1.md` L23 `**架构名定为：DecompMoE**` + L30 `3. DecompMoE（选定）` 决策叙事对齐
- 追加 `(per CLAUDE.md §1 project-level amendment; GeoMoE was never previously a canonical name)` 显式声明 GeoMoE 从未被选为 canonical
- 保留 `(only as a secondary alias inside design prose)` 语义与 spec L18 Scenario verbatim 对齐

**Alternatives considered**:
- (a) "preserve" → "retain" — 拒绝: "retain" 仍暗示曾获得再保留
- (b) "preserve" → "document" — 拒绝: 弱化 alias 语义
- (c) 删除整段 L12 重写 — 拒绝: scope 最小化 (CLAUDE.md §3 surgical)
- (d) 维持 "preserve" 不动 — 拒绝: cycle-1 finding 1 LOW 评级虽不构成硬冲突, wording drift 是真实 drift

### Decision 2: NAR-2 h 域声明方向 —— (i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S) 域补全

**Choice**: spec L24 `subscript convention (i, l, h, t) for expert / layer / head / token` → `subscript convention (i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S) for expert / layer / head / token — where the per-head index h enumerates the KV-head axis (per req-5 cross-head mean z̄_t^l = (1/H_kv) · Σ_h C_t^{l,h}), which at MVP equals the Q-head count H because H_kv = H = 8 (GQA degenerates to MHA at MVP scale per req-11 L211); when true GQA is later enabled (H_kv < H), the convention remains h ∈ 1..H_kv`.

**Rationale**: cycle-2 finding 1 (audit `audit-verification.md` L1849+ verify-25 section) 实证 spec L24 `h` 取值域未显式声明. ticket `A1-1.md` L42 显式 `h ∈ 1..H`, spec req-5 L64 实际归一化用 H_kv (per-KV-head). MVP 当前 `H_kv = H = 8` (req-11 L211 GQA 退化 MHA), 不咬人; 但**未来启用 GQA (H_kv < H) 时 h 域歧义点**.

**Cross-cycle closure 加固**: cycle-4 finding 1 (audit L2201) 已 cross-cycle closure cycle-2 finding 1 通过 req-5 L64 H_kv 语义; 本 NAR-2 是 closure 加固 (spec L24 钉死 h 域) 而非**新增** cross-reference.

**Alternatives considered**:
- (a) `h ∈ 1..H` (沿用 ticket wording) — 拒绝: spec req-5 L64 实际归一化用 H_kv, 沿用 `1..H` 仍 wording 不精确
- (b) `h ∈ 1..H_kv` 但不解释 MVP 状态 — 拒绝: 未来 GQA 启用时 reader 仍可能困惑
- (c) 不动 spec L24 wording — 拒绝: h 域未声明是真实 wording drift
- (d) 改 spec L24 + 改 ticket A1-1 L42 — 拒绝: ticket 端不变 (CLAUDE.md §6 第 7 条 + §8 tickets reference-only)

### Decision 3: NAR-3 降级为 verify-only (而非 modify spec L126)

**Choice**: 不 modify `openspec/specs/wayfinder/spec.md` L126 Source 字段. NAR-3 决议从 "modify spec" 降级为 "verify-only":
1. `grep "wayfinder/tickets/A4-2" openspec/specs/wayfinder/spec.md` 应 ≥ 1 命中 (Source 字段)
2. `grep "wayfinder/tickets/A6b-1" openspec/specs/wayfinder/spec.md` 应 ≥ 1 命中 (Source 字段)
3. `python scripts/lint_no_source_field_drift.py` 应 PASS (含 NAR-3 历史决议的 lint 兼容性)

**Rationale**: 2026-09-22 事实验证实证 live spec L126 已含 `**Source:** \`wayfinder/tickets/A4-1.md\`, \`wayfinder/tickets/A4-2.md\`, \`wayfinder/tickets/A6b-1.md\`` (3 ticket 反链, A4-1 主链在前). cycle-7 finding 3 (audit `audit-verification.md` L455-463 verify-8 section) 描述的 "Source 字段不完整" 状态已在 live spec 中消失 (推测由其它 parallel change 提前独立 apply, 或 manual edit).

**Scope 调整影响**:
- 不动 live spec.md (避免重复 modify 形成 churn)
- NAR-3 finding 3 状态: closure 仍达成 (live spec 已含 3 ticket), 但 closure 路径由 "本 change modify" → "live spec 已 modify, 本 change verify"
- 需要在 change 制品中显式声明此状态以保持 audit trail 一致性

**Alternatives considered**:
- (a) 维持原 NAR-3 modify spec L126 决议 — 拒绝: live spec 已含 3 ticket, modify 会触发重复改动或 idempotent no-op, 引入 audit drift
- (b) 删除 NAR-3 整条决议, 完全不在本 change 体现 — 拒绝: cycle-7 finding 3 closure 路径需在制品中体现 (audit trail 一致性)
- (c) NAR-3 降级为 verify-only — **采纳**: 兼顾 closure 体现 + 不引入 churn

## Risks / Trade-offs

- **[Risk]** NAR-1 wording 微调让 reader 在 ticket A0-1 L29 看到 "GeoMoE——突出几何领地...但失去分解哲学表达" 时仍可能困惑 GeoMoE 到底是 canonical 还是 alias. **Mitigation**: spec L18 Scenario "Canonical reference resolution" 仍 verbatim 钉死 DecompMoE primary + GeoMoE secondary alias, 形成第二层 narrative lock
- **[Risk]** NAR-2 h 域声明 `h ∈ 1..H_kv` 与 ticket A1-1 L42 `h ∈ 1..H` wording 不完全 verbatim. **Mitigation**: 两者**不冲突** (ticket pre-A2-2 阶段 `1..H` 包括 Q+KV; spec post-A2-2 阶段 `1..H_kv` 仅 KV, 因 gating 走 KV 路径); NAR-2 加 cross-reference 解释 (`at MVP equals the Q-head count H because H_kv = H = 8`) 让 reader 理解两者关系
- **[Risk]** NAR-3 verify-only 决议与 audit-verification meta-发现 #9 (finding 双重价值) 的 closure-by-other-change 模式混合, 需在制品中显式标注 closure 路径. **Mitigation**: proposal.md Source 段 + design.md Decision 3 显式说明 NAR-3 closure 路径已由 live spec state 满足
- **[Risk]** anchor 100% 覆盖: 2 处 wording 微调不动 anchor, 但若 Edit 工具意外破坏 anchor 字符串会触发 anchor drift. **Mitigation**: tasks.md B.1 anchor 100% 覆盖验证 (`grep -F '<a id="req-1"></a>'` 等 2 命令) + B.4 LF 校验
- **[Risk]** Windows Edit tool CRLF contamination (与既有 memory `windows-edit-crlf-pitfall` 同型). **Mitigation**: 每个 spec Edit 后 `git diff --stat` 验证 LF 保留; 必要时 `sed -i 's/\r$//'`
- **[Risk]** NAR-3 live spec 状态与 audit-verification cycle-7 finding 3 实证 baseline 不一致 (audit 时 L126 是 single ticket, 当前 live 是 3 tickets) — closure 路径非本 change 主线. **Mitigation**: design.md Decision 3 显式标注 live state, proposal.md Source 段引用 audit 文件具体行号 L455-463 (实测 verbatim)

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical spec wording 修订 + verify-only + 不动 src/tests/tickets. 实施步骤:

1. NAR-1 wording 微调: `openspec/specs/wayfinder/spec.md` L12 (`preserve` → `adopt (per CLAUDE.md §1 ...)`)
2. NAR-2 h 域声明: `openspec/specs/wayfinder/spec.md` L24 (追加 `(i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S)` + KV-head 轴解释)
3. NAR-3 verify-only: 不 modify spec.md, 跑 grep + lint gate 实证 L126 已含 3 ticket
4. lint gate 2 项验证 (`dead-defensive` + `source-field-drift`) PASS
5. `openspec validate 06-fix-spec-narrative-wording-batch --type change --strict` PASS
6. `uv run pytest tests/ -v` 全绿 (197 passed, 无 regression)
7. `git diff --stat` 验证 LF 保留 (无 CRLF contamination)
8. 单 commit on `dev`: `fix(spec): close 3 narrative-layer wording drift findings (cycle-1 GeoMoE preserve / cycle-2 h subscript domain / cycle-7 Source field verify-only) — ticket-side unchanged`
9. archive 到 `openspec/changes/archive/2026-09-22-fix-spec-narrative-wording-batch/`

## Open Questions

- **NAR-3 live spec 状态来源溯源**: live spec L126 在 audit (2026-09-18/19) 时是 single ticket, 当前 (2026-09-22) 是 3 tickets. 哪个 parallel change 触发了独立 apply? 候选: `01-fix-ticket-stale-numerical-4file-batch/` 或独立 manual edit. **Mitigation**: 本 change 不溯源 (out of scope), 仅 verify live state 满足 closure 条件
- **NAR-1 wording 选择空间**: spec 作者若希望保留 "preserve" wording 但承认 GeoMoE 从未被选为 canonical, 需要回滚本 change 的 NAR-1 决议. **Mitigation**: design.md Decision 1 已论证 "preserve" 与 ticket + CLAUDE.md 三方叙事不一致; audit-verification 三轴 fully-verified 后 LOW 评级恰当, 应修
- **NAR-2 h 域选择空间**: spec 作者若希望显式 `h ∈ 1..H` (沿用 ticket A1-1 L42 wording), 需要回滚本 change 的 NAR-2 决议. **Mitigation**: design.md Decision 2 已论证 req-5 L64 实际归一化用 H_kv, 沿用 `1..H` 仍 wording 不精确
- **Future audit**: 3 条 narrative-layer finding 关闭后, 元审计循环饱和度提升 (8 fully-verified → 11 fully-verified). Open Question: 是否开 follow-up change 处理剩余 LOW/INFO finding? 本 change 明确只覆盖 3 条 narrative-layer finding; 不预先承诺 follow-up 范围