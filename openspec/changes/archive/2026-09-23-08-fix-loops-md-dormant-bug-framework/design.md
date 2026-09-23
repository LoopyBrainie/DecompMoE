# Design

## Context

`LOOPS.md` severity 框架是**纯 reactive 模型**——仅当 finding 已传染 src/ 时才升 HIGH。两个 meta-发现 (meta-06 severity 误标 pattern + meta-08 dormant bug framework gap) 共同指向同一根因：

- **meta-06**：audit-verification axis-γ 复核倾向"默认 MEDIUM"惯性，finding 文本已显式分级 ("低危" → LOW、"正面记录" → INFO) 时仍误标 MEDIUM。`audit-verification.md` L1832 实证 2/24 = 8.3% 误标率（verify-21 cycle-17 INFO + verify-24 cycle-1 LOW）
- **meta-08**：dormant bug（0 active impact + high latent risk × trigger probability）当前无升级条款。`audit-verification.md` verify-18 cycle-13 finding 1 实证：`latent_risk=HIGH` (48 orphan clusters fatal if Phase 0 implemented) × `trigger_probability=HIGH` (any future Phase 0 reader reads ticket L100)，但 LOOPS.md 升级条件限定"已传染 src/"，当前 0 active impact → 严格按规则 MEDIUM。`audit-verification.md` L1358-1359 原话："**建议 LOOPS.md 修订**: 在 LOOPS.md severity 框架中加 dormant bug 升级条款: '实际是 HIGH（如 finding 是 dormant bug: latent risk × trigger probability ≥ 中度严重）：升级'"

参考 proposal.md - Why 的整体动机。本设计专注**怎么落地**——技术决策、风险、迁移路径。

## Goals / Non-Goals

**Goals:**

- 关闭 meta-06 + meta-08 双 meta-发现（`audit-verification.md` L2300-2309 9 meta-发现清单的 #6 + #8）
- 在 `governance/spec.md` 新增 req-gov-3 "Loop Severity Framework Gap Closure"，钉死两条过程性义务（dormant bug 升级触发器 + audit 自我校核），每条配 Scenario 验证
- 在 `LOOPS.md` §DecompMoE audit-verification loop axis-γ 子段**新增** dormant bug 升级条款 + audit 自我校核子段（双 spec ↔ LOOPS 双向引用）
- 在 `LOOPS.md` §DecompMoE spec-math audit loop "Finding 升格路径"段**新增** dormant bug 升级条款引用，与 audit-verification loop 子段语义对齐
- `LOOPS.md` §"修改记录"末尾追加本次变更条目
- **LOOPS.md 入库前置**（req-gov-3 obligation 5 新增的硬约束）：本 change 第一步先把 untracked 的 `LOOPS.md` 加入 git（独立 commit），使其成为稳定可锚定文件
- lint gate 双跑（`lint_no_source_field_drift.py` + `lint_no_dead_defensive.py`）必须 `exit=0`
- 严格遵守 CLAUDE.md §2 真相源层级（spec > 文档 > 代码）；governance 是过程类规格的合规去处（per `req-gov-1` 设计先例 + wayfinder req-34 governance-migration Scenario）

**Non-Goals:**

- 不动 `openspec/specs/wayfinder/spec.md`（本 change 是 governance 起源，不是 ticket 起源——CLAUDE.md §6 第 7 + wayfinder req-34 强制 governance-migration）
- 不动 `openspec/specs/decompmoe-skeleton/spec.md`（与本 change 无关）
- 不动 `wayfinder/tickets/`（reference-only per CLAUDE.md §6 第 7）
- 不动 `openspec/specs/governance/spec.md` 既有 req-gov-1 + req-gov-2（req-gov-3 新增，不覆盖既有 Requirement——见 Decision 5 编号冲突决策）
- 不动 `src/` / `tests/` 任何代码（LOOPS.md 是 process 文档，code-level 与本 change 无关）
- 不重写 `.audit/audit-verification/audit-verification.md` 已有 verdict（meta-06 + meta-08 是元发现描述，不重写 audit verdict）
- 不引入 custom CUDA / Triton kernel（per CLAUDE.md §6 第 1 条）
- 不引入 closed-form pytest 数值断言（dormant bug 升级触发器是定性枚举风险函数，非 closed-form 数值；process-level LOOPS.md 规则无 numerical claim，无需 pytest.approx / bare == 守护——per CLAUDE.md §6 第 8 条"sentinel closed-form constant must directly verify"原则只适用于含具体数值的算式）
- 不引入新的 audit loop（meta-06 / meta-08 是 process 规则 gap，不是新 loop 设计 gap）

## Decisions

### Decision 1: dormant bug 升级触发器采用 either-dimension 独立维度规则

**Choice**: dormant bug 升级触发器采用 either-dimension 规则——`severity_up_to_HIGH ⟺ latent_risk ∈ {MEDIUM, HIGH} ∨ trigger_probability ∈ {MEDIUM, HIGH}`（任一维度 ≥ MEDIUM 即升 HIGH）。

**Rationale**:

- 现有 LOOPS.md reactive 模型 gap（`audit-verification.md` L1358-1359 原话）："建议 LOOPS.md 修订: 在 LOOPS.md severity 框架中加 dormant bug 升级条款: '实际是 HIGH（如 finding 是 dormant bug: latent risk × trigger probability ≥ 中度严重）：升级'"
- cycle-13 finding 1 dormant bug 维度评估（`audit-verification.md` L1316-1322）：
  - 当前 functional impact = LOW（Phase 0 K-Means NOT in src/）
  - latent risk = HIGH（48 orphan clusters fatal if Phase 0 implemented）
  - trigger probability = HIGH（任何 future Phase 0 实现读 ticket L100）
  - 传染链状态 = LOW（仅 ticket stale）
- either-dimension 规则覆盖：任一维度 ≥ MEDIUM 即升 HIGH——cycle-13 finding 1 满足任一维度（HIGH × HIGH），升 HIGH dormant-bug
- 保守性论证：现有 MEDIUM 评级（`latent_risk ∈ {LOW} ∧ trigger_probability ∈ {LOW}`）保留不升级——避免 noise。当两维度都 LOW（即 finding 描述 stale value 当前生效 + 无 future trigger）时，仍是普通 MEDIUM
- CLOSED-FORM 风险函数表达：虽然函数输入（latent_risk, trigger_probability）是定性枚举而非连续数值，**函数本身**是 closed-form——给定两维度评级，输出是确定的 severity（HIGH / MEDIUM）。这是 process-level 闭环而非 numerical 闭环

**Alternatives considered**:

- (a) **单一 latent_risk ≥ MEDIUM 触发**（不看 trigger_probability）—— 拒绝：单一维度不足以避免 noise；可能 latent_risk 高但 trigger 极低（如 ticket 已 archived 永不读）的 finding 仍被升 HIGH，过激
- (b) **相乘规则**（latent_risk × trigger_probability 数值乘积 ≥ 中度严重）—— 拒绝：定性枚举无法做数值乘积（LOW/MEDIUM/HIGH 不是数字）；独立维度规则更清晰
- (c) **三维度评估**（latent_risk × trigger_probability × dormant_likelihood，dormant_likelihood 是 finding 是否 currently dormant）—— 拒绝：scope 膨胀；两维度已足够覆盖 meta-08 实证
- (d) **不加 dormant bug 升级条款，保持 MEDIUM** —— 拒绝：`audit-verification.md` L1358-1359 已显式建议加；meta-08 仍未闭环

### Decision 2: audit 自我校核采用 reading-finding-text-first rule（禁用默认 MEDIUM 惯性）

**Choice**: audit-verification axis-γ 复核前**必须**先 grep finding 文本 against 关键词集合 `{"低危", "正面记录", "正面alignment", "不构成硬冲突", "phasing deferred", "not implemented", "NOT IMPLEMENTED", "no_op", "deferred"}`，若 finding 已显式分级 LOW/INFO 则 verdict **必须**采用 finding 自身分级，禁止默认 MEDIUM 惯性。verdict 中**必须**嵌入 finding 自身分级关键词作为 severity 决策依据（"finding-keyword `n/a` × finding-text-self-grade `LOW` ⇒ verdict-LOW"形式）。

**Rationale**:

- meta-06 severity 误标 pattern 实证（`audit-verification.md` verify-21 L1534-1547 + verify-24 L1810-1833 + L1832）：
  - cycle-17 finding 1 实际 INFO（finding 文本 "正面记录"）被误标 MEDIUM
  - cycle-1 finding 1 实际 LOW（finding 文本 "低危文字漂移" + "不构成硬冲突"）被误标 MEDIUM
  - 误标率 2/24 = 8.3%
  - Pattern：audit loop 倾向于把所有 finding 标 MEDIUM，但 finding 文本中已有显式 severity 分级
- 关键词集合构造依据：
  - "低危" / "不构成硬冲突" → LOW（来自 cycle-1 finding 1 文本）
  - "正面记录" / "正面alignment" / "alignment 完美" → INFO（来自 cycle-17 finding 1 文本）
  - "phasing deferred" / "not implemented" / "NOT IMPLEMENTED" / "no_op" / "deferred" → 触发 dormant bug 评估（义务 a，不是直接 LOW/INFO 评级）
- 禁用默认 MEDIUM 惯性：audit-verification loop 当前默认 MEDIUM 是 process 缺陷——非 finding 真实 severity。Reading finding text first rule 把 finding 自身分级提升为 axis-γ 复核的**第一动作**，优先级高于任何 audit loop 默认值
- verdict 必嵌关键词：强制要求 audit-verification verdict 文本包含触发 auto-adoption 的 finding 自身关键词，便于下次 audit-verification loop 复盘时验证 rule 是否被遵守

**Alternatives considered**:

- (a) **三阶段 keyword priority rule**（high-priority / medium / low priority keywords）—— 拒绝：两阶段（finding-text-self-grade / default-MEDIUM）已足够；优先级细化不会减少误标率
- (b) **LLM-as-judge severity re-evaluation**（用 LLM 重新评估每条 finding severity）—— 拒绝：scope 膨胀，process overhead 大；grep keyword rule 是 deterministic 规则
- (c) **保留默认 MEDIUM 惯性但加 post-hoc correction**（误标后追加 verdict 校正）—— 拒绝：post-hoc 校正成本高；preventive rule 更高效
- (d) **不改 audit 校核规则** —— 拒绝：meta-06 仍未闭环；verify-21 + verify-24 两次实证已证明误标是 process 缺陷

### Decision 3: process 规则双向落地（governance spec ↔ LOOPS.md）

**Choice**: 两条款同步沉淀到 `governance/spec.md` 新增 Requirement "Loop Severity Framework Gap Closure"（governance 起源，per CLAUDE.md §6 第 7 + wayfinder req-34）+ `LOOPS.md` §DecompMoE audit-verification loop "Cycle 单元"段 axis-γ 子段 + §DecompMoE spec-math audit loop "Finding 升格路径"段。spec 是规则真相源（governance spec req-new），LOOPS.md 是 loop 实例对规则的引用与展开。

**Rationale**:

- CLAUDE.md §2 真相源层级：spec > 文档 > 代码。仅改 LOOPS.md 而不写 spec，等于把过程规则放在 doc 而非真相源；仅写 spec 而不改 LOOPS.md，等于把规则放进 spec 但 LOOPS.md 不遵守
- governance capability 是过程类规格的合规去处：
  - `req-gov-1` "Test Guard Precision for Closed-Form Numerical Claims" 是首例 governance-origin Requirement（design origin = `CLAUDE.md` §6 第 8 条）
  - wayfinder req-34 "governance-origin requirements trigger lint failure" Scenario 强制 governance-migration
  - 本 change 设计起源 = `LOOPS.md` severity 框架 gap，是 process governance 而非 ticket；正确归宿是 governance
- LOOPS.md 子段双引用：audit-verification loop axis-γ 子段（dormant bug + audit 自我校核）+ spec-math audit loop Finding 升格路径段（dormant bug 升级条款引用）—— 两 loop 都要遵守同一 process 规则，但实施细节不同（audit-verification 有 axis-γ 三轴复核，spec-math 没有 axis 概念），所以 LOOPS.md 是分 loop 引用同一 spec

**Alternatives considered**:

- (a) **仅改 LOOPS.md，不写 spec** —— 拒绝：违反 CLAUDE.md §2 真相源层级；下次 spec audit 不会发现 process gap
- (b) **仅写 spec，不改 LOOPS.md** —— 拒绝：spec 是规则但 LOOPS.md 不引用，下次 loop 跑仍会偏离
- (c) **写到 wayfinder/spec.md 而非 governance/spec.md** —— 拒绝：process 起源是 `LOOPS.md`/`CLAUDE.md`，不是 ticket；违反 wayfinder req-34 + lint `lint_no_source_field_drift.py` 必挂

### Decision 4: 不引入 pytest 闭式断言（process-level 规则无 numerical claim）

**Choice**: 本 change 不引入 pytest 闭式断言。dormant bug 升级触发器虽为 closed-form 风险函数，但函数输入（latent_risk, trigger_probability）是定性枚举（LOW/MEDIUM/HIGH），不是 closed-form 数值；process-level LOOPS.md 规则无 numerical claim，无需 `pytest.approx(..., abs=...)` 或 bare `==` 守护。规则守护靠下次 audit-verification loop 跑时遵守——下次 verify cycle 在 axis-γ 复核时会触发 reading-finding-text-first rule + dormant bug 升级条款。

**Rationale**:

- CLAUDE.md §6 第 8 条 "sentinel closed-form constant must directly verify" 原则：仅适用于**含具体数值的算式**——例如 `θ_Voronoi(16,16) ≈ 1.1736 rad`（浮点闭式）+ `P_total = 452_329_984`（整数闭式）
- dormant bug 升级触发器不是 closed-form 数值算式：输入是定性枚举（LOW/MEDIUM/HIGH），输出是 severity 类别（HIGH/MEDIUM）；不是 `(latent_risk_value, trigger_probability_value) → numerical_score`
- process 规则守护靠 governance spec Scenario：governance/spec.md req-gov-3 "Loop Severity Framework Gap Closure" 两个 Scenario 钉死规则行为（"WHEN ... THEN ..." 形式）；下次 audit-verification loop 跑时 Scenario 描述即 rule
- 不引入 test code 与本 change scope 一致：CLAUDE.md §3 surgical 原则——touch only what you must；process-level 规则无 numerical claim，引入 pytest 是 scope 膨胀

**Alternatives considered**:

- (a) **引入 pytest closed-form 守护**（如 `test_dormant_bug_severity_escalation` 验算 HIGH × HIGH ⇒ HIGH）—— 拒绝：scope 膨胀；定性枚举 risk function 无 numerical claim
- (b) **引入 audit-verification meta-loop test**（test audit-verification loop 自身遵守 reading-finding-text-first rule）—— 拒绝：scope 膨胀；meta-loop test 需要 LLM-as-judge，无法 pure pytest 实现
- (c) **不加守护，依赖下次 loop 自然遵守** —— 选择：process-level 规则无 numerical claim 是合理决策；governance spec Scenario 描述即 rule，不需 pytest

### Decision 5: req-gov-3 编号决策（避开 req-gov-2 占用冲突）

**Choice**: 新 Requirement 使用 `req-gov-3` 编号，**不**使用 `req-gov-2`。

**Rationale**:

- 当前 `governance/spec.md` 已有 `req-gov-1` (Test Guard Precision for Closed-Form Numerical Claims) + `req-gov-2` (Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application)
- 原 planning 草案 `.audit/audit-verification/opsx-changes/08-fix-loops-md-dormant-bug-framework/proposal.md` 错误声称填 `req-gov-2`，与现有 req-gov-2 内容冲突
- 按 req-N 递增编号规则，本 change 新增 Requirement 应使用 `req-gov-3`（下一个可用编号）
- 不覆盖现有 req-gov-2（documenting-only meta Requirement，有独立 scope；本 change 不动其内容）
- anchor 编号是 spec schema 演化的残留，每次 change 增/删/合并会留下空洞，必须实测 grep 后才能写入 proposal/design/tasks（per agent memory "Spec anchor 编号必须基于实测 grep 而非'当前 N 个'的假设"）

**Alternatives considered**:

- (a) **覆盖现有 req-gov-2**（改写为"Loop Severity Framework Gap Closure"，丢失 ticket supersede annotation 文档）—— 拒绝：scope 破坏。req-gov-2 是 documenting-only meta Requirement，与本 change scope 无关
- (b) **合并到现有 req-gov-1**（把 dormant bug + audit self-correction 合并到 Test Guard Precision）—— 拒绝：scope 错位。req-gov-1 是 closed-form 数值守护，本 change 是 process-level 规则
- (c) **写到 wayfinder/spec.md 作为新 req-N** —— 拒绝：违反 wayfinder req-34 governance-migration + lint `lint_no_source_field_drift.py` 必挂（wayfinder Source 字段首项必须是 backtick-wrapped `wayfinder/tickets/<ID>.md`）

### Decision 6: LOOPS.md 入库 commit 与 surgical edit 的 commit 拆分

**Choice**: 本 change 落地拆分为**两个独立 commit**：

1. **commit 1 (chore)**：`chore(audit): import LOOPS.md to version control` — 把当前 untracked 的 `LOOPS.md` 加入 git，**零内容变更**（仅 `git add LOOPS.md` + commit）
3. **commit 2 (fix)**：`fix(governance+LOOPS): close meta-06 + meta-08 — dormant bug escalation clause + audit self-correction rule` — governance spec delta + LOOPS.md surgical edit

**Rationale**:

- 当前 `LOOPS.md` 是 untracked（`git status` 显示 `?? LOOPS.md`），从未被 commit 过
- commit 1 的"零内容变更"特性：`git diff` 应该显示 0 行变更，仅 `git status` 输出 commit 前的 `?? LOOPS.md` 转为 `A LOOPS.md`
- surgical Edit 在 untracked 文件上没有稳定锚点——`git blame` / `git log -L` 不可用，audit-verification loop 复盘时无法引用 commit hash
- req-gov-3 obligation 5 显式要求："any `LOOPS.md` surgical edit MUST operate on a `LOOPS.md` that is tracked in the repository's git history (not untracked)" —— 这是 process rule，硬约束
- 拆分为两个 commit 保证：(a) LOOPS.md 入库 audit trail 独立可见（用户可单独 review 入库动作）；(b) surgical edit 的 diff 干净（不含 untracked → tracked 噪声）

**Alternatives considered**:

- (a) **单 commit 一次性 add + edit**（`git add LOOPS.md && git commit -m "fix(governance+LOOPS): ..."`，LOOPS.md 的"入库 + edit" 在同一 commit）—— 拒绝：`git diff HEAD~1` 同时显示入库前内容 vs 入库后内容，diff 不易 review；用户难以区分"入库动作"和"surgical edit"
- (b) **不拆 commit，LOOPS.md 保持 untracked 状态** —— 拒绝：违反 req-gov-3 obligation 5（process rule）；audit-verification loop 复盘时无稳定锚点
- (c) **拆分为三个 commit**（入库 + governance spec delta + LOOPS.md surgical edit）—— 拒绝：over-split；governance spec delta 与 LOOPS.md surgical edit 是同一 fix 的两端，拆开 review 价值低

## Risks / Trade-offs

- **[Risk]** dormant bug 升级条款会让 cycle-13 类 finding（Phase 0 NOT IMPLEMENTED）从 MEDIUM borderline 升至 HIGH dormant-bug。**Mitigation**：升级标准是 closed-form 风险函数（either-dimension rule），由 finding 自身证据（TERRITORY_SEEDING 缺失 + ticket L100 stale + 48 orphan clusters risk）独立判断；不是 audit loop 惯性。当 latent_risk 与 trigger_probability 全 LOW 时保留 MEDIUM（保持现状）
- **[Risk]** audit 自我校核会让 axis-γ 复核周期变长。**Mitigation**：复盘 cycle-1 verify-24 + cycle-17 verify-21 2 次实证，单 cycle 增加约 5 行 grep + 1 行 severity 决策，scope 增量极小。**win-win**：长期降低误标率（meta-06 8.3% → 接近 0%）节省的审计工作量远超单 cycle 增加成本
- **[Risk]** governance spec 新增 Requirement 与 req-gov-1（Test Guard Precision）+ req-gov-2（Ticket supersede annotation）放同一文件，可能未来 governance capability 膨胀。**Mitigation**：governance 是 peer capability（per CLAUDE.md §3），膨胀是必然趋势；当前 3 个 Requirement 远未到膨胀阈值
- **[Risk]** LOOPS.md 是 loop 实例，引用 governance spec id 可能造成循环依赖。**Mitigation**：LOOPS.md 不引用具体 spec id（req-gov-3），仅引用 capability 路径（"governance/spec.md req-new 'Loop Severity Framework Gap Closure'"），保持 loop 实例对 spec 的松耦合
- **[Risk]** Windows Edit tool CRLF contamination。**Mitigation**：每个 LOOPS.md Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`（per [[windows-edit-crlf-pitfall]] memory rule）
- **[Risk]** audit-verification loop 跑时已 archive 的 finding（如 cycle-5/6/7/9/13/17 等 9 fully-verified）不会重新触发 dormant bug 升级——但 dormant bug 升级条款的 future 适用性仍生效（下次新 finding 出现时遵守）。**Mitigation**：本 change 不重写已 archive 的 finding verdict；future finding 自动遵守新规则
- **[Risk]** 原 planning 草案 `.audit/audit-verification/opsx-changes/08-fix-loops-md-dormant-bug-framework/proposal.md` 自带 spec.md 制品缺 anchor（实测 `grep "<a id="` 返回 0 命中），违反 CLAUDE.md §6 第 9 条 anchor 100% 覆盖规则。**Mitigation**：本 redo change 的 spec.md 制品**显式**包含 `<a id="req-gov-3"></a>`，且 tasks.md C.3 含 apply 阶段二次 grep 验证 anchor 唯一性子任务

## Migration Plan

N/A — no deployment, no rollback, no migration。本 change 是 governance spec delta + LOOPS.md surgical edit + LOOPS.md 入库 commit。实施步骤：

1. **commit 1 (chore)**：LOOPS.md 入库
   - `git add LOOPS.md`
   - `git commit -m "chore(audit): import LOOPS.md to version control"`
   - 验证：`git log -1 --stat LOOPS.md` 应显示新增 LOOPS.md（首次入库）；`git diff HEAD~1` 应只显示 LOOPS.md 完整内容（无 other files）
2. **commit 2 (fix)**：governance spec delta + LOOPS.md surgical edit
   - governance spec delta 落地：`openspec/specs/governance/spec.md` 新增 1 处 ADDED Requirement `<a id="req-gov-3"></a>` "Loop Severity Framework Gap Closure"（含 2 个 Scenario）
   - LOOPS.md surgical edit（4 处修改，per Decision 1-3）：
     - L118-122 axis-γ 子段：新增 dormant bug 升级条款 + audit 自我校核子段
     - L64-69 Finding 升格路径段：新增 dormant bug 升级条款引用
     - §"修改记录"末尾：追加 2026-09-23 条目
   - lint gate 双跑：`lint_no_source_field_drift.py` + `lint_no_dead_defensive.py` 必须 `exit=0`
   - `git diff --stat` 验证 LF 保留（无 CRLF contamination）
   - `git add openspec/specs/governance/spec.md LOOPS.md && git commit -m "fix(governance+LOOPS): close meta-06 + meta-08 — dormant bug escalation clause + audit self-correction rule"`
3. **archive 前置独立复核**：spec 算式实际代入计算（dormant bug risk function 的定性枚举）；cycle-5/13/17/1 retro-application 数值闭环验证（per `post-archive 独立复核` 协议）
4. **`openspec validate 08-fix-loops-md-dormant-bug-framework --type change --strict`** 应 PASS（governance spec delta 是 ADDED 而非 MODIFIED，符合 wayfinder req-34 governance-migration Scenario）
5. **`/opsx:archive`**：lint gate 必须 `exit=0`（同时跑 `python scripts/lint_no_source_field_drift.py` 与 `python scripts/lint_no_dead_defensive.py`，避免 archived change 留下 lint 报红）

## Open Questions

- **meta-06 误标率未来回归监控**：governance spec Scenario 钉死 reading-finding-text-first rule 后，如何量化未来 audit-verification loop 误标率？Open Question：是否需要 follow-up change 加 meta-loop 统计（每次 audit-verification verdict 完成后 grep "finding-keyword" 出现次数 × verdict-LOW/INFO 出现次数，计算 ratio）？本 change 不覆盖（scope 膨胀；当前 governance spec Scenario 已 sufficient）
- **dormant bug 升级条款的 cycle-13 finding 1 retroactive 应用**：cycle-13 finding 1 当前 MEDIUM borderline，按本 change 新规则应升 HIGH dormant-bug。Open Question：是否要重写 cycle-13 verdict severity？本 change 不覆盖——理由：cycle-13 已 archive 为 fully-verified + dormant bug 标注，重写 verdict severity 是 audit-verification loop 历史改写，违反 CLAUDE.md §3 "Surgical Changes" 不动已 archive 的 verdict
- **dormant bug 升级条款的 dormant_likelihood 第三维度**：当前 either-dimension rule（latent_risk ∨ trigger_probability）已覆盖 meta-08 实证，但未来若出现 "latent_risk HIGH + trigger_probability LOW 但 dormant_likelihood 极高" 的 finding（如 ticket 已被 ticket-stub-tool 自动引用），是否需加第三维度？本 change 不覆盖
- **LOOPS.md dormant bug 条款与 audit-verification 终止条件的 interaction**：当前 LOOPS.md §DecompMoE audit-verification loop "终止条件"段写明 "用户显式 `/loop stop` 或要求切换到其它 loop"。本 change 不影响终止条件——dormant bug 升级是 severity 决策，不影响 loop 终止