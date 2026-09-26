# Design

## Context

2026-09-19 audit-verification 在 cycle-13 收尾后整理出 9 个 meta-发现。其中 meta-03 (TERRITORY_SEEDING identifier 缺失) + meta-04 (Phase 0 K-Means 当前 src/ 未实现) 构成同一 spec/code 漂移的两面 (`audit-verification.md` L1192-1204, L1222, meta-03 / meta-04 桶 README 各自独立证据链)。2026-09-23 事实验证复核确认:

- **meta-03**: `grep -rn "territory_seeding" src/decompmoe/` **仍 0 命中**;`openspec/specs/wayfinder/spec.md` L24 列 `territory_seeding` 为 MUST-exist identifier (snake_case 7 个之一),标识符契约完全缺失。
- **meta-04**: `src/decompmoe/extraction.py:107-108` docstring 注释 `"actual k-means is owned by training-time caller"`;spec L78-93 (req-6) Phase 0 子句 (L81) 以**活跃合同**形式规定 `"c_i^(t+1) = KMeans(C) initialization"`,**未明文声明 deferred**;两者在"合同是否需要执行"层面互斥。

**Severity 评级 MEDIUM dormant**: 当前 MVP 范围 (`CLAUDE.md §7 "Out of Scope"` —— 训练执行 out-of-scope) 下不触发 active failure;但形成 latent contract gap:推理引擎实现代码或未来 Phase 0 启用时会撞上 "spec 要求 K-Means 但 src/ 无实现"。

**DEPRECATED.md 与 change 04 合并覆盖的不一致澄清**:此前 `.audit/audit-verification/opsx-changes/07-.../DEPRECATED.md` 声称 "scope 全部并入 `04-fix-ticket-a6b-1-n-e-supersede`",但 change 04 design.md 第 103 行**明确声明** "**不处理**: TERRITORY_SEEDING 标识符缺失 (独立 change)、Phase 0 K-Means 实现 (独立 change)"。change 04 仅在 `openspec/specs/wayfinder/spec.md` req-11 末尾 (L231-234) 新增 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)` 作为间接引用警告;**未实施** spec 一等公民 deferred 声明,亦未添加 `territory_seeding` 函数至 `src/decompmoe/extraction.py`。meta-03 + meta-04 **仍 OPEN**,本 change 是 change 04 explicitly carved-out 的独立 change scope。

## Goals / Non-Goals

**Goals:**

- 关闭 meta-03 + meta-04 两 finding,通过单次 spec/code delta 在同一 change 内同步 close
- 维持 MVP 范围:不实现真正的 Spherical K-Means,不引入 custom CUDA / Triton kernel (per `CLAUDE.md §6 第 1 条`)
- spec 单源真相:把 deferred 状态从代码注释 (`extraction.py:107-108`) 提升到 spec 一等公民 (req-6 Phase 0 sub-clause 显式声明)
- 代码侧薄占位函数 `territory_seeding` 满足 spec req-2 L24 identifier-map MUST-be-in-codebase 契约
- 顺手修复 spec anchor 缺失: req-6 anchor (`<a id="req-6"></a>` 当前在 `openspec/specs/wayfinder/spec.md` L76 Requirement title 前缺失) + new Requirement anchor `<a id="req-10"></a>` 顺手补齐 req-9 (L171) → req-11 (L197) 间的 req-10 anchor 缺失
- Source 反链含 literal backtick (per `CLAUDE.md §3` lint 三项结构性检查)
- tests/ 1 文件新增 1 个 test (NotImplementedError contract + 错误消息 verbatim 4-token 锁契约),不修改既有 13 个 test (2026-09-23 实测 `tests/test_extraction.py` 共 13 个测试函数)

**Non-Goals:**

- 不实现真正的 Spherical K-Means (`c_i^(t+1) = KMeans(C)` 实际算法) —— MVP 范围外 (训练执行 out-of-scope per `CLAUDE.md §7`)
- 不动 `CentroidDriver.step` Phase 0 (SEEDING) 分支 (`extraction.py:119-120`) 的 no-op 行为 —— 与 spec delta 方向一致, no-op 是 deferred 状态下的正确 contract
- 不动 `wayfinder/tickets/A1-1.md` / `A2-2.md` / `A3-2.md` —— `CLAUDE.md §6 第 7 条` + §8 tickets 已 reference-only
- 不动 `extract_C` 4-step pipeline —— 与本次 finding 无关
- 不动 Phase 1-4 任何分支 (EMA + projected SGD) —— 仅 Phase 0 标 deferred
- 不动 MVPConfig / beta / schedule / gating / loss / experts / viz 等其他模块
- 不动 `openspec/specs/decompmoe-skeleton/spec.md` (decompmoe-skeleton L392 Phase 0 注释已为 "caller's responsibility",与 wayfinder Phase 0 deferred 声明自洽,无需 delta)
- 不动 change 04 在 `openspec/specs/wayfinder/spec.md` req-11 末尾 (L231-234) 新增的 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)` —— 该 Scenario 引用 `territory_seeding` 为 "track via a separate change",本 change 正是该 separate change 的实现,与 req-6 Phase 0 新增 Scenario `Phase 0 K-Means deferred to caller` 互补不冲突
- 不引入 PyTorch 之外的 K-Means 库 (e.g. `faiss`, `scikit-learn`) —— deferred 状态不需要

## Decisions

### Decision 1: 修复方向 —— spec 显式声明 deferred + 代码侧薄占位标识符, 不实现 K-Means

**Choice**: 合并 meta-03 + meta-04 为单次 delta, 双向修复:

1. **spec req-6 Phase 0 sub-clause 追加 deferred 声明段**, 把 "deferred to training-time caller" 从代码注释 (`extraction.py:107-108`) 提升到 spec 一等公民;**顺手补齐 req-6 anchor 缺失** (在 `openspec/specs/wayfinder/spec.md` L76 Requirement title 前新增 `<a id="req-6"></a>`)
2. **spec req-2 L24 identifier map 追加 inline 注脚**, 保留 `territory_seeding` 标识符但明文承认 deferred
3. **新增 Requirement "Territory Seeding Deferred Contract"** (anchor `<a id="req-10"></a>`, next-free 实测确认 — req-9 (L171) → req-11 (L197) 间断),把薄占位函数的契约固化;顺手补齐 req-10 anchor 缺失
4. **代码侧 `src/decompmoe/extraction.py:174` 新增薄占位函数 `territory_seeding(C_batch, N_e, *, d_c) -> Tensor`** (line 174 为 `__all__` line 175 之前的空行,apply 阶段二次 `grep -nF "__all__" src/decompmoe/extraction.py` 验证插入点), 函数体 `raise NotImplementedError(spec_cited_message)`

**Rationale**:

**(a) spec/code 双向对齐 vs 单边修改**: 若仅修 spec (删除 `territory_seeding` 标识符 + Phase 0 K-Means 条款), 等于承认 spec L24 / L81 是错的, 需要把 finding 升级为 HIGH (合同条款与代码现状互斥); 若仅修代码 (实现 K-Means), 等于把 deferred 状态变成 active 状态, 触发 `CLAUDE.md §7 "Out of Scope"` 边界 (训练执行不在本仓库范围)。**双向修复既满足 spec 单源真相 + 代码侧 identifier-map MUST-be-in-codebase 契约, 又不超出 MVP 范围**。

**(b) 薄占位函数 vs 删除标识符**: spec req-2 L24 列 `territory_seeding` 为 MUST-map, 删除会破坏 L24 identifier map 完整性 (req-2 还有 6 个其他标识符, 一并删除破坏 spec 整体结构); 薄占位函数保留标识符, 但函数体 raise NotImplementedError, 把 deferred 状态编码在契约里 —— future caller 误调会得到清晰的 spec-cited 错误消息。

**(c) 错误消息 verbatim 引用 spec req-2 / req-6**: 错误消息包含 4 个 verbatim token: `"Phase 0"`, `"deferred to the training-time caller"`, `"req-2"`, `"req-6"`。test 用 `pytest.raises(NotImplementedError, match=...)` 4 次分别 match, 保证 spec 引用未被未来 refactor 误删 (锁契约)。

**(d) Anchor 编号精确性**: 当前 spec 锚点序列实测为 req-1/2/3/4/5 → req-7 (L111) → req-8 (L155) → req-9 (L171) → req-11 (L197) (req-6 与 req-10 各缺失 1 个)。本 change 三处锚点操作:
- 修复 req-6 缺失 → 在 `openspec/specs/wayfinder/spec.md` L76 Requirement title 前新增 `<a id="req-6"></a>`
- new Requirement anchor `<a id="req-10"></a>` (next missing after req-9 L171)
- apply 阶段必须 `grep -nE '<a id="req-[0-9]+"></a>' openspec/specs/wayfinder/spec.md | sort -t'"' -k2 -V` 二次确认 anchor 唯一性

**Alternatives considered**:

- (a) 仅修 spec (删除 `territory_seeding` + Phase 0 K-Means 条款) —— 拒绝: 破坏 req-2 L24 identifier map 完整性 + req-6 Phase 0 是 MVP 阶段描述的核心机制 (K-Means → EMA → projected SGD 序列)
- (b) 仅修代码 (实现真正的 K-Means) —— 拒绝: 触发 `CLAUDE.md §7 "Out of Scope"` 边界 (训练执行不在本仓库范围)
- (c) 仅修代码, 把 `CentroidDriver.step` Phase 0 改为真正的 K-Means —— 拒绝: 同 (b), 且 `CentroidDriver` 不持有训练侧 batch 数据 (`C_batch`), K-Means 需要 caller 提供 batch
- (d) 在 `decompmoe/` 新增 `clustering.py` 模块承载真正的 K-Means —— 拒绝: scope 膨胀, 触发 §7 边界
- (e) spec 改"Phase 0 not in MVP scope", 标记整个 Phase 0 条款删除 —— 拒绝: 破坏 spec 5-phase 时间驱动调度完整性 (req-6 是 5-phase 时间线的源头)
- (f) new Requirement anchor 使用 `<a id="req-7"></a>` —— 拒绝: `openspec/specs/wayfinder/spec.md` L111 已有 `<a id="req-7"></a>`,anchor 冲突
- (g) new Requirement anchor 使用 `<a id="req-6"></a>` —— 拒绝: 与本 change 顺手修复的 req-6 anchor 冲突 (同一 anchor 不能两个 Requirement 共用)
- (h) new Requirement anchor 使用任意高数 (e.g. `<a id="req-100"></a>`) —— 拒绝: 制造非连续 anchor 序列,违反 CLAUDE.md §6 第 8 条 anchor 100% 覆盖率的设计意图 (anchor 应连续)

### Decision 2: 薄占位函数签名 —— `territory_seeding(C_batch, N_e, *, d_c) -> Tensor`

**Choice**: 函数签名 `(C_batch: Tensor, N_e: int, *, d_c: int) -> Tensor`, 错误消息 verbatim 包含 4 个 spec token (`"Phase 0"`, `"deferred to the training-time caller"`, `"req-2"`, `"req-6"`)。

**Rationale**:

- **`C_batch: Tensor`** —— Phase 0 K-Means 输入是 batch of `d_c`-dim points, 形状 `(T, d_c)` (T 个 token)。spec L81 `c_i^(t+1) = KMeans(C)` 中 `C` 是 spherical unit-sphere points 集合。
- **`N_e: int`** —— 输出 centroids 数量, 与 MVPConfig `N_e` 字段对齐。
- **`d_c: int`** —— keyword-only, 与 MVPConfig `d_c` 字段对齐; `*` keyword-only 强制调用方显式声明, 避免误传 position。
- **`-> Tensor`** —— 输出形状 `(N_e, d_c)`, 与 `CentroidDriver.step` 输出形状一致; MVP 范围内 `raise NotImplementedError`, 但签名契约声明返回 `(N_e, d_c)` 张量, future 实现时签名不变。
- **错误消息 verbatim token** —— 4 个 token 让 future maintainer / caller 拿到错误时能直接跳到 spec 条款; `pytest.raises(match=...)` 4 次 match 锁契约。

**Alternatives considered**:

- (a) 签名 `(C_batch, N_e)` 不带 keyword-only `d_c` —— 拒绝: `d_c` 是 spec 维度 (`S^{d_c-1}`), 必须显式声明避免与 `C_batch.shape[-1]` 混淆
- (b) 签名 `(C_batch, N_e, d_c)` 全部 positional —— 拒绝: spec 维度 `d_c` 是 spec-level 契约, 应 keyword-only 强调
- (c) 返回 `None` 而不是 `Tensor` —— 拒绝: 与 `CentroidDriver.step` 输出形状契约不一致, future 切换到 active 实现时签名不一致
- (d) 错误消息简短 ("not implemented") —— 拒绝: 失去 spec-cited self-locating 价值, test 无法用 `pytest.raises(match=...)` 锁契约

### Decision 3: 新 Requirement anchor 编号 —— `<a id="req-10"></a>` (next-free 实测确认)

**Choice**: 
- 修复缺失 anchor `<a id="req-6"></a>` 在 `openspec/specs/wayfinder/spec.md` L76 Requirement title 前
- 新 Requirement "Territory Seeding Deferred Contract" 使用 `<a id="req-10"></a>` (next missing number after req-9 L171)
- apply 阶段 tasks.md A-3.1 必须 `grep -nE '<a id="req-[0-9]+"></a>' openspec/specs/wayfinder/spec.md` 二次确认 anchor 唯一性

**Rationale**: `CLAUDE.md §6 第 8 条 "spec anchor 不全: wayfinder/spec.md 与 decompmoe-skeleton/spec.md 的每个 Requirement MUST 在首行设独立 anchor, 100% 覆盖"`。当前 spec 锚点序列: req-1/2/3/4/5 → req-7 → req-8 → req-9 → req-11 → req-12 → req-13 → req-14 → req-15 → req-17 → req-18 → req-19 → req-20 → req-35 → req-22 → req-23 → req-24 → req-25 → req-26 → req-27 → req-28 → req-29 → req-30 → req-31 → req-32 → req-33 → req-34 → req-36 (req-6 与 req-10 各缺失 1 个)。本 change:
- 修复缺失 req-6 → 顺手把 req-6 anchor 补齐
- new Requirement anchor = req-10 → 顺手把 req-10 anchor 补齐
- apply 阶段必须二次确认 anchor 唯一性

**Alternatives considered**:

- (a) 复用现有 anchor (e.g. 把 deferred 契约追加到 req-6) —— 拒绝: 现有 req-6 L76-93 篇幅已大, 追加 deferred 契约会模糊 Phase 0 / Phase 1-4 / Phase 4 主线;但**Scenario `Phase 0 K-Means deferred to caller` 仍放在 req-6 下**(作为 Phase 0 deferred 声明的 scenario 守护,与 spec L81 deferred 声明就近)
- (b) 使用 req-NEW / req-NEW-2 占位 anchor —— 拒绝: lint 期望确定 number, 占位无法 grep
- (c) 把 deferred 契约作为 req-6 的 Scenario 子节点 (无 anchor) —— 拒绝: anchor 100% 覆盖要求 Scenario 所属 Requirement 必须有 anchor, 子 Scenario 不需要独立 anchor;但本 change 把 deferred 契约作为独立 Requirement (req-10) + 把 deferred 行为 scenario 作为 req-6 子 Scenario (覆盖双向)
- (d) new Requirement anchor 使用 `<a id="req-6"></a>` —— 拒绝: 与本 change 顺手修复的 req-6 anchor 冲突
- (e) new Requirement anchor 使用 `<a id="req-7"></a>` —— 拒绝: L111 已有 `<a id="req-7"></a>`,冲突
- (f) new Requirement anchor 使用任意高数 (e.g. `<a id="req-100"></a>`) —— 拒绝: 制造非连续 anchor 序列,违反 anchor 100% 覆盖率的设计意图

### Decision 4: Source 反链 —— 引用 A1-1 + A3-2 tickets

**Choice**: 新 Requirement "Territory Seeding Deferred Contract" 的 Source 反链包含 `` `wayfinder/tickets/A1-1.md` `` + `` `wayfinder/tickets/A3-2.md` `` (literal backtick per `CLAUDE.md §3` lint 三项结构性检查),同时引用 `change 07-fix-spec-territory-seeding-phase-0 design.md (Decision 1)`。

**Rationale**:

- **`wayfinder/tickets/A1-1.md`** —— req-2 L26 已引用的 ticket, 描述 formal symbols + naming convention, 是 `territory_seeding` 标识符的票面起源
- **`wayfinder/tickets/A3-2.md`** —— req-6 L93 已引用的 ticket, 描述 centroid lifecycle (5-phase 时间驱动), 是 Phase 0 K-Means 条款的票面起源
- 同时附加 `change 07-fix-spec-territory-seeding-phase-0 design.md (Decision 1)` 引用本次 change

**Alternatives considered**:

- (a) 仅引用 A1-1 (req-2 反链) —— 拒绝: 漏掉 A3-2 (req-6 Phase 0 反链), spec 与 ticket lineage 断裂
- (b) 引用 A2-2 (head-aggregation) —— 拒绝: A2-2 描述 head subscript elision, 与 Phase 0 K-Means 无直接关系
- (c) 不引用 ticket, 仅引用 change —— 拒绝: 违反 `CLAUDE.md §3` lint 三项结构性检查 (子串存在 + 反链必须在 backtick 内 + 主反链必须是第一个 top-level item)

## Risks / Trade-offs

- **[Risk]** 薄占位函数引入 `NotImplementedError`, future caller 误调会得到清晰错误, 但同时增加 src/ 代码行数 (约 +30 行)。Mitigation: 新增函数严格满足 spec req-2 L24 identifier-map MUST-be-in-codebase 契约; 函数体仅 1 行 `raise NotImplementedError(spec_cited_message)` + docstring 解释; 无新依赖。
- **[Risk]** spec req-6 Phase 0 sub-clause 追加 deferred 声明段会扩大 L76-93 篇幅。Mitigation: 追加段落放在 Phase 0 子句 (L81) 之后, Phase 1-4 子句不动, Scope 增量 ≤ 8 行。
- **[Risk]** 新 Requirement anchor 编号 `req-10` 需要 apply 阶段 grep 验证, 当前 proposal 基于 2026-09-23 实测。Mitigation: tasks.md A-3.1 明确 "apply 阶段先 grep 确认 anchor 唯一性,硬编码 `<a id="req-10"></a>` 是 best-guess"。
- **[Risk]** Source 反链引用 A1-1 + A3-2 tickets 但 tickets 已 reference-only (`CLAUDE.md §8` 2026-09-21 裁决: tickets 不再是必改制品)。Mitigation: reference-only 意味着 lint 不强制 tickets 与 spec 一致, 但 spec 反链引用是历史 lineage 记录, 不是修改 ticket; spec/source/反链/ticket 四者构成 reference graph, source 字段记录引用方向不影响 ticket 本身。
- **[Risk]** Windows Edit tool CRLF contamination。Mitigation: 每个 src/ Edit 后跑 `git diff --stat` 验证 LF 保留; 必要时 `sed -i 's/\r$//'` (per [[windows-edit-crlf-pitfall]] memory rule)。
- **[Risk]** 测试覆盖不全 —— 仅 1 个新增 test (NotImplementedError contract), 未测薄占位函数签名本身。Mitigation: `inspect.signature(decompmoe.extraction.territory_seeding)` 返回 `(C_batch, N_e, *, d_c)` 由 tasks.md D.5 spot-check 守护; 1 个 test + 1 个 spot-check 已足够锁契约 (signature 是静态可分析, 无需 runtime 重复测)。
- **[Risk]** `territory_seeding` 标识符与未来 active 实现 (e.g. PyTorch 自带 K-Means 或 sklearn 包装) 命名冲突。Mitigation: 标识符在 spec req-2 L24 已锁定, future 实现必须沿用此名, 不能改名 (`<historical, was X; superseded by territory_seeding>` 模式允许, 但改名需 ticket 走 spec 反链流程)。
- **[Risk]** spec req-2 L24 identifier map 当前列 7 个标识符 (`GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding`, `territory_collapse`), future 实现可能让某几个标识符也走 deferred 路径。Mitigation: 本 change 不预先 scope 膨胀, 仅处理 `territory_seeding` 一个; future finding 由独立 OpenSpec change 处理。
- **[Risk]** DEPRECATED.md "scope 全部并入 change 04" 描述与 change 04 design.md L103 "不处理 TERRITORY_SEEDING 标识符缺失 (独立 change)" 矛盾,可能导致看走档案和未来 reviewer 误以为本 change 是重复工作。Mitigation: proposal.md "Why" 段 + design.md Context 段均显式声明"meta-03 + meta-04 仍 OPEN,本 change 是 change 04 explicitly carved-out 的独立 change scope",避免歧义。
- **[Risk]** proposal 旧版本 (`.audit/audit-verification/opsx-changes/07-.../proposal.md`) 包含多处事实错误 (test count 17→13, anchor req-7→req-10, 行数虚高等),可能误导 reviewer 走错 reference。Mitigation: 本 change 的 proposal/design/tasks 全部基于 2026-09-23 实测事实,与旧版 `.audit/audit-verification/opsx-changes/07-...` 互不交叉;`openspec validate` 通过是充分条件;reviewer 应只看本目录制品。

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical spec delta + 1 文件 src/ 薄占位 + 1 文件 1 个新增 test。实施步骤:

1. spec delta 落地: `openspec/specs/wayfinder/spec.md` 2 处 MODIFIED (req-2 L20-26 + req-6 L76-93) + 1 处 ADDED (新 Requirement "Territory Seeding Deferred Contract", anchor `<a id="req-10"></a>`)
2. spec anchor 顺手修复: 在 req-6 Requirement title (L76) 前新增 `<a id="req-6"></a>` (修复当前缺失的 req-6 anchor)
3. src/ surgical edit: `src/decompmoe/extraction.py:174` 新增 `territory_seeding` 函数 + `__all__` (line 175-179) 追加
4. tests/ 1 个新 test: `tests/test_extraction.py::test_territory_seeding_raises_not_implemented_with_spec_citation`
5. `uv run pytest tests/test_extraction.py -v` 全绿 (13 既有 + 1 新增 = 14 passed)
6. `python scripts/lint_no_dead_defensive.py` exit=0
7. `python scripts/lint_no_source_field_drift.py` exit=0 (新 Requirement Source 反链含 literal backtick)
8. `git diff --stat` 验证 LF 保留 (无 CRLF contamination)
9. 单 commit on `dev`: `fix(spec,code): close meta-03 + meta-04 — territory_seeding contract + Phase 0 deferred declaration (audit-verification meta-audit 2026-09-19, fact-verified 2026-09-23)`

## Open Questions

- **Future Phase 0 active 实现**: 若未来 MVP 范围扩展 (e.g. `CLAUDE.md §7 "Out of Scope"` 修订允许训练执行), 需要 follow-up change 把 `territory_seeding` 从 deferred 切换到 active, 实现真正的 Spherical K-Means。本 change 不预先承诺 follow-up 范围; spec req-6 Phase 0 deferred 声明 + 新 Requirement "Territory Seeding Deferred Contract" 给 future change 提供明确的 spec-anchor 反向引用点 (req-10 + req-6 L81 deferred 声明)。
- **`CentroidDriver.step` Phase 0 no-op 行为是否需要 spec Scenario 守护**: 当前 `extraction.py:119-120` 返回 `centroids.detach()`, 这是 deferred 状态下的正确 contract。Open Question: 是否需要在 req-6 Phase 0 sub-clause 追加 Scenario `Phase 0 no-op returns centroids detached` 守护此行为? 本 change 不预先 scope 膨胀, 由独立 follow-up 处理 (decompmoe-skeleton spec L392 已为 "caller's responsibility" 注释,可视为现有守护)。
- **identifier map 其他 6 个标识符 (`GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_collapse`) 是否也存在 deferred 状态**: audit-verification meta-audit 仅枚举 meta-03 (territory_seeding), 未触及 L24 其他标识符。Open Question: 是否需要 audit pass 验证 L24 全 7 个标识符的 spec/code 一致性? 本 change 不预先 scope 膨胀。
- **proposal 旧版本与本 change 的 reference 一致性**: 旧版 `.audit/audit-verification/opsx-changes/07-.../proposal.md` 包含多处事实错误 (test count 17→13, anchor req-7→req-10, 行数虚高等); reviewer 若以旧版为 reference 可能误判。Open Question: 是否在 apply 阶段保留旧版作 audit trail (DEPRECATED.md 当前选择保留) + 在 README 顶部明确"旧版已 deprecated, 仅作 audit trail, 实施以本目录制品为准"? 本 change 不预先 scope 膨胀, 由独立 follow-up 处理。