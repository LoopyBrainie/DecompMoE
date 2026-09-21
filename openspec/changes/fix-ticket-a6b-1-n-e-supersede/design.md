# Design: fix-ticket-a6b-1-n-e-supersede

## Context

2026-09-18 audit-verification loop 完成 cycle-13 MEDIUM finding #1 三轴 (α + β + γ) 复核。本 change 锁定 cycle-13 finding #1（ticket A6b-1 L100 `N_e = 64` stale）+ cycle-13 finding #2（LOW ticket A6b-1 L131 γ' reset formula coverage gap）。

- **cycle-13 #1**：ticket `A6b-1.md` L100 verbatim `Spherical k-means 聚 N_e = 64 类` vs spec req-11 `N_e = 16`（MVP target）—— **4.0x ratio / 300% relative drift**（整数闭式，bare `==` 对账 trivially exact）。这是 ticket-stale pattern family 中**唯一 dormant bug finding**：当前 src/ 未实现 Phase 0 K-Means（`src/decompmoe/extraction.py:107-108` deferred to caller；spec req-2 L24 列出的 7 个 code identifier 中 `territory_seeding` 是**唯一**在 src/ 中不存在的标识符，Grep 0 matches），future 实现读 ticket A6b-1 L100 会复制 `N_e = 64` stale value → 致命 48 orphan clusters（4.0x ratio 下 `64 − 16 = 48` 个 cluster 永远得不到 routing 概率质量，因 MVP `k = 2` top-k 仅取 `N_e = 16` 中概率最高的 2 个专家）。
- **cycle-13 #2**：ticket `A6b-1.md` L131 verbatim `**Phase 4 切换瞬间重置 Adam 动量状态**（EMA 状态对 Projected SGD 无效）` 仅 narrative 描述，无显式 formula；spec req-7 已显式 `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`。该 finding 是 **coverage gap**（非 drift）：spec 已含 formula，ticket 故意省略避免重复。本 change 仅在 ticket L131 后追加 annotation 声明 "ticket 故意省略 formula as design-prose"，**不视为** supersede。

**传染链状态（verify-16 + verify-17 cross-validation）**：

| 路径 | 状态 | 证据 |
|---|---|---|
| `spec ↔ ticket A6b-1 L100` | ⚠️ STALE（`N_e = 64`） | L100 verbatim `Spherical k-means 聚 N_e = 64 类` |
| `spec ↔ src/` Phase 0 K-Means | ⚠️ NOT IMPLEMENTED | `extraction.py:107-108` deferred to caller |
| `spec ↔ src/` Phase 4 γ' reset | ✓ CLEAN | spec 显式 formula, src/ 走 spec 实现 |
| `spec ↔ src/` 五阶段编排 (req-14) | ✓ CLEAN | 完整对齐 ticket L54-58 phase table |
| `spec req-2 L24 TERRITORY_SEEDING` | ❌ DOES NOT EXIST | Grep 0 matches in src/ |
| `ticket ↔ src/` | N/A (Phase 0 not in src/) | — |

**双重缓解**：
1. 当前 src/ 未实现 Phase 0 K-Means，ticket L100 stale value 不传染到 runtime（latent risk 而非 active risk）
2. spec ↔ src/ Phase 4 γ' reset 已对齐（spec 显式 formula），ticket L131 coverage gap 不构成 spec 端问题

**决策保留（沿用之前 change 的 design 决策 + ticket supersede canonical 格式）**：ticket 端走 "追加 supersede annotation 而非删除原值"（与之前 change 01 ticket A5-3 L62 + A4-1 L58 同构），spec 端走 "新增 Scenario 警告而非修改主闭式"。本 change **不修改** spec `N_e = 16` 主闭式（integer pinned MVP truth），**不修改** spec req-11 Source 字段（已含 `\`wayfinder/tickets/A5-3.md\`` 主反链首位 + backtick-wrapped，lint req-34 已合规），**不引入** TERRITORY_SEEDING 模块（独立处理），**不引入** Phase 0 K-Means 实现（独立处理）。

## Goals / Non-Goals

**Goals:**
- 关闭 cycle-13 MEDIUM finding #1（ticket A6b-1 L100 `N_e = 64` stale + dormant bug 警告 Scenario）+ cycle-13 LOW finding #2（ticket A6b-1 L131 γ' formula coverage gap），每项有独立的 ticket-spec 对账点
- 维持 design 决策：算法常量位于使用点，不引入 cfg 形参，不引入 MVPConfig 新字段，不引入 Phase 0 K-Means 实现（TERRITORY_SEEDING 缺失独立处理）
- 3-file 边界修改（ticket A6b-1 L100 + ticket A6b-1 L131 + spec req-11 新 Scenario）
- **不删 ticket 原 stale 值 / narrative**——仅追加 `(historical, ...; superseded by ...)` 注释保持 lineage 可读
- spec 端新增 Scenario 不动 MVP `N_e = 16` 主闭式数字（integer MVP truth）
- 不修改 spec req-11 Source 字段（已 lint req-34 合规）
- tests/ 0 文件修改（dormant bug 当前无 active runtime）
- 现有 196 tests 全绿（无新增、无修改）

**Non-Goals:**
- 不动 `src/decompmoe/extraction.py:107-108` Phase 0 deferred placeholder（独立处理）
- 不动 spec req-2 L24 code identifier 列表（TERRITORY_SEEDING 缺失独立处理）
- 不动 spec req-7 γ' formula（已 verbatim 完整；cycle-13 finding #2 LOW 仅 ticket 端 annotation）
- 不动 spec req-14 五阶段编排段（已 CITE-OK verbatim）
- 不动 spec req-11 Source 字段（已合规）
- 不动 spec `N_e = 16` 主闭式（integer MVP pinned）
- 不动 `decompmoe/beta.py` 模块级常量（`BETA_MIN = 0.1` / `BETA_MAX = 32` 保持 `Final[float]`）
- 不动 MVPConfig 字段集合（11 个字段保持不变）
- 不重写 wayfinder ticket 内容（仅追加 annotation）
- 不动 `tests/test_extraction.py`（无 Phase 0 测试用例）
- 不引入 custom CUDA/Triton kernel
- 不把 C_t 写入 KV Cache
- 不引入 shared expert
- 不在 logit 中使用 w_i

## Decisions

### Decision 1: ticket 端修复方向 —— 追加 supersede annotation 而非删除原值

**Choice**: ticket `A6b-1.md` L100 `Spherical k-means 聚 N_e = 64 类` 行后追加 `(historical, N_e = 64 K-Means design from N_e=64 时代; superseded by spec req-11 MVP N_e = 16 — any future Phase 0 K-Means implementation MUST use spec N_e = 16 to avoid 48 orphan clusters fatal drift)`；ticket `A6b-1.md` L131 `**Phase 4 切换瞬间重置 Adam 动量状态**` 行后追加 `(historical, narrative-only; closed-form γ' = ln((β_{p3} − 1) / (32 − β_{p3})) lives in spec req-7 — ticket deliberately omits explicit formula as design-prose; supersede path: spec req-7 + req-14 "Five-Phase Time-Driven Schedule" Phase 4 transition Scenario)`。

**Rationale**: 复用之前 change ticket A5-3 L62 + A4-1 L58 + spec canonical `(historical, ...; superseded by ...)` 格式。删除原 stale 数字会破坏 ticket 的决策 trail（reader 无法追溯当时为何写 `N_e = 64`），且 spec 是钉死真相（spec MVP `N_e = 16`），ticket stale 不构成 spec 端问题。L131 annotation **不是** supersede（spec 已显式 formula），仅声明 "ticket 故意省略 formula" 的 metadata。

**Alternatives considered**:
- (a) 删除 ticket L100 原 `N_e = 64` 改 `N_e = 16` —— 拒绝：破坏 ticket 历史决策 trail；ticket 是 advisory non-binding，无必要重写历史
- (b) ticket 完全不动改 spec —— 拒绝：spec 已 MVP `N_e = 16` 真相，ticket stale 不构成 spec 端问题；本 change 新增 Scenario 已足够反向吸收 dormant bug 警告
- (c) ticket 整文件废弃 —— 拒绝：ticket 是 advisory 参考，废弃超出 scope（CLAUDE.md §3 surgical 原则）
- (d) ticket L131 γ' formula 显式补全 —— 拒绝：spec 已是 single source of truth；ticket 故意省略避免重复

### Decision 2: spec 端修复方向 —— 新增 Scenario 警告而非修改主闭式数字

**Choice**: spec req-11 在 `Voronoi angle is N_e- and d_c-dependent` Scenario **之后**新增 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)`，Scenario body 用 **WHEN/THEN/AND** Markdown 结构（与现有 Scenario 风格一致），Scenario 标题加 `(dormant bug warning)` 标记。

**Rationale**: spec MVP `N_e = 16` 是主闭式（integer pinned），不可修改（任何修改都会破坏 spec ↔ src/test 三角）；dormant bug 警告通过新增 Scenario 实现，而非修改主闭式数字。这与之前 change Decision 4（spec σ' precision 微调）同 pattern：**不破坏主闭式**，**仅新增周边 Scenario 警告**。新 Scenario 引用 ticket A6b-1 L100 stale value 作为反例，明文钉死 spec 真相与 ticket stale 边界，避免 future Phase 0 K-Means 实现误用 stale 数字。

**Alternatives considered**:
- (a) 修改 spec `N_e = 16` 强调主闭式 —— 拒绝：spec 已 verbatim 完整 `N_e = 16`，强调只是 narrative 噪音；Scenario 警告更结构化
- (b) 修改 spec req-14 Phase 0 段强调 `N_e = 16` —— 拒绝：spec req-14 已 "Phase 0 MUST be Spherical K-Means seeding (driver Active, gradient Frozen)"，但 req-14 不直接说 K-Means 簇数 = N_e（K-Means 簇数隐式由 spec req-11 N_e 决定）；新 Scenario 在 req-11 上下文更准确
- (c) 在 spec req-14 五阶段编排段新增 Scenario —— 拒绝：cycle-13 finding #1 的 stale value 在 ticket 端而非 spec 五阶段编排段；req-11 是 N_e 真相源，warning 应紧邻 `N_e = 16` 主闭式

### Decision 3: Scenario body 内容 —— 显式 48 orphan clusters fatal drift 警告

**Choice**: 新 Scenario body 显式包含三段：(i) **WHEN** any future implementation of Phase 0 Spherical K-Means seeding references ticket A6b-1.md L100 historical `N_e = 64` value；(ii) **THEN** implementation MUST use MVP `N_e = 16` from spec req-11 (and `d_c = 16`) — NOT ticket's historical `N_e = 64`. The historical 4.0x ratio (64/16) would produce `N_e = 64` clusters of which `64 − 16 = 48` are "orphan clusters" never receiving any routing probability mass under the MVP `k = 2` top-k routing, a fatal topology bug；(iii) **AND** the `territory_seeding` code identifier from spec req-2 L24 is the canonical name for the Phase 0 seeding module (track via a separate change for the Phase 0 K-Means implementation; this Scenario pins only the `N_e = 16` value, not the module name).

**Rationale**: 三段结构 (WHEN/THEN/AND) 与现有 Scenario 风格一致。**关键不变量**：Scenario 钉死 MVP `N_e = 16` + 48 orphan clusters 警告 + territory_seeding 标识符引用，三者组合确保 future Phase 0 实现工程师：(a) 不会复制 ticket L100 stale value；(b) 知道 4.0x ratio 下 48 orphan clusters 是 fatal topology bug；(c) 知道 territory_seeding 是 canonical code identifier（即使模块 deferred）。

**Alternatives considered**:
- (a) Scenario body 只说 "use spec `N_e = 16`" 不警告 orphan clusters —— 拒绝：reader 可能不理解为何 ticket L100 stale value 危险；48 orphan clusters fatal topology bug 量化是 spec 真相的一部分
- (b) Scenario body 不引用独立 change —— 拒绝：territory_seeding 模块 deferred 是真实状态，不引用会让 reader 误以为该模块已实现
- (c) Scenario body 显式给出 50-digit 整数闭式对账 —— 拒绝：整数闭式 trivially exact（`16 == 16` + `64 == 64`），无需 50-digit 精度声明

### Decision 4: 整数闭式 bare `==` 强制条款遵守（governance req-gov-1 第 1 条）

**Choice**: 本 change 无新算式，但 cycle-13 finding #1 整数闭式对账通过 bare `==` 实现：`N_e_spec == 16`（spec verbatim, exact int）+ `N_e_ticket == 64`（ticket L100 verbatim, exact int）+ `ratio == 64 // 16 == 4`（integer division, exact int）+ `orphan == 64 - 16 == 48`（integer subtraction, exact int）。

**Rationale**: governance/spec.md req-gov-1 第 1 条硬卡"Closed-form integer claims ... MUST use **bare `==` integer equality** (Python `int == int`) — NOT `pytest.approx(...)` in any form"。理由：`pytest.approx` effective-tolerance formula `max(abs, rel·|expected|)` 在 `abs=0` 且 `rel=1e-12`（pytest 默认）下退化为 `1e-12 · |expected|`，量级越大 tolerance 越大（违背"钉值零容差"意图）。Bare `==` 给出跨量级 zero tolerance，与 magnitude 独立。本 change 所有整数数字（`N_e = 16` / `N_e = 64` / ratio = 4 / orphan = 48）都是 exact integer，无浮点误差；bare `==` 严格对账。

**Alternatives considered**:
- (a) 用 `pytest.approx(16, abs=0)` —— 拒绝：违反 governance/spec.md req-gov-1 第 1 条硬卡；整数闭式必须 bare `==`
- (b) 用 `int(N_e) == int(N_e)` 显式类型 cast —— 拒绝：spec / ticket L100 都是 verbatim int literal，无需 cast；cast 是冗余代码

### Decision 5: 跨 change scope boundary 严格遵守

**Choice**: 本 change 仅处理 (i) ticket A6b-1 L100 supersede annotation + (ii) ticket A6b-1 L131 coverage-gap annotation + (iii) spec req-11 新 Scenario dormant bug warning。**不处理**：TERRITORY_SEEDING 标识符缺失（独立 change）、Phase 0 K-Means 实现（独立 change）、LOOPS.md severity 框架 dormant bug 升级条款（独立 change）、spec req-7 γ' formula（已 verbatim 完整，cycle-13 finding #2 LOW 仅 ticket 端 annotation）、spec req-11 Source 字段（已 lint req-34 合规）。

**Rationale**: 严格 scope boundary 是 CLAUDE.md §3 surgical 原则的核心——"Touch only what you must. Clean up only your own mess."。cycle-13 finding #1 涉及 4 个相关 drift（ticket stale + TERRITORY_SEEDING missing + Phase 0 not implemented + LOOPS.md dormant bug 条款），但只有 ticket stale + spec warning 在本 change scope；其余 3 个独立处理。混改会破坏 change atomicity，让单个 PR diff 跨 ≥ 3 个 capability，难以 review 和 revert。

**Alternatives considered**:
- (a) 单 change 闭合全部 4 个 cycle-13 related drift —— 拒绝：scope 膨胀（4 文件 / 4 capability），违反 CLAUDE.md §3 surgical 原则
- (b) 仅处理 ticket stale 不新增 spec Scenario —— 拒绝：dormant bug 警告必须在 spec 端有显式 anchor，否则 future reader 仍可能复制 stale value；spec Scenario 是 dormant bug 反向吸收的必要条件
- (c) 把 spec Scenario 归并到 TERRITORY_SEEDING change —— 拒绝：spec Scenario 引用 MVP `N_e = 16` 真相是 spec req-11 上下文，与 TERRITORY_SEEDING 模块 deferred 无关；强行合并会破坏 req-11 ↔ req-14 分离

## Risks / Trade-offs

- **[Risk]** ticket L100 supersede annotation 加错位置 → reader 读到 stale 数字而非 supersede 注释。Mitigation：annotation 加 stale 数字**紧邻下一行**（不内嵌原文中间），并明示 `(historical, N_e = 64 ...)` + `(superseded by spec req-11 MVP N_e = 16 ...)` 两段；与之前 change 01 ticket A5-3 L62 + A4-1 L58 supersede annotation 风格一致
- **[Risk]** ticket L131 γ' formula coverage gap annotation 被误读为 supersede。Mitigation：annotation 开头显式 `narrative-only;` + `ticket deliberately omits explicit formula as design-prose;` 两段，明示**不是** supersede；spec 已是 single source of truth
- **[Risk]** spec req-11 新增 Scenario 与现有 4 个 Scenario 风格不一致。Mitigation：复用现有 `Voronoi angle is N_e- and d_c-dependent` / `Voronoi closed-form residual is bounded` Scenario 的 **WHEN/THEN/AND** Markdown 结构；Scenario 标题用 `(dormant bug warning)` 标记
- **[Risk]** spec req-11 新增 Scenario 破坏现有 `Voronoi closed-form residual is bounded` Scenario。Mitigation：新 Scenario 插入 `Voronoi angle is N_e- and d_c-dependent` 之后、`Voronoi closed-form residual is bounded` 之前；Scenario 数量从 4 → 5；现有 Scenario 一字不动
- **[Risk]** spec req-11 新增 Scenario 触发 lint req-34 误报（Source 字段漂移）。Mitigation：本 change **不修改** spec req-11 Source 字段（已 verbatim 完整 `\`wayfinder/tickets/A5-3.md\`, ...`）；新 Scenario 不涉及 Source 反链变更
- **[Risk]** dormant bug warning Scenario 引用独立 change → change 未实际 propose 时 warning Scenario 引用 dangling reference。Mitigation：warning Scenario 是 spec-side anchor（dormant bug 钉死 `N_e = 16`），独立 change 是 territory_seeding 模块；两者独立；即使独立 change 永远不 propose，warning Scenario 仍能正确防止 ticket stale 复制
- **[Risk]** Windows Edit tool CRLF contamination（ticket + spec 三个文件）。Mitigation：每个 Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`（per [[windows-edit-crlf-pitfall]] memory）
- **[Risk]** future Phase 0 K-Means 实现工程师忽略 warning Scenario。Mitigation：warning Scenario 显式包含 48 orphan clusters fatal topology bug 量化（4.0x ratio + `64 − 16 = 48` integer arithmetic），reader 不易忽略；Scenario 标题加 `(dormant bug warning)` 标记显式提示
- **[Trade-off]** 新增 Scenario 让 req-11 长 8 行 —— reader 阅读成本略增。Justification：dormant bug 风险权重高于阅读成本；spec 是 single source of truth，warning 必须显式

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical ticket annotation + spec Scenario delta。实施步骤：

1. spec delta 落地：`openspec/specs/wayfinder/spec.md` 1 处 MODIFIED（req-11 新增 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)`）
2. ticket 端 supersede annotation：`wayfinder/tickets/A6b-1.md` L100 + L131 各加一行注释（**追加不删原值**）
3. 不动 src/（Phase 0 K-Means deferred to caller，独立处理）
4. 不动 tests/（无 Phase 0 测试用例）
5. `uv run pytest tests/ -v` 全绿（196 passed，无新增无修改）
6. `git diff --stat` 验证 LF 保留（无 CRLF contamination）
7. `python scripts/lint_no_dead_defensive.py` + `python scripts/lint_no_source_field_drift.py` 双 lint gate exit=0
8. 单 commit on `dev`：`fix(spec,ticket): close cycle-13 MEDIUM finding #1 (A6b-1 L100 N_e=64 stale + dormant bug warning) + LOW finding #2 (L131 γ' formula coverage gap)`

## Open Questions

- **TERRITORY_SEEDING 模块 deferred 状态**: 独立 change 是否在最终落地前 actual propose？还是 deferred to caller 长期保持？本 change 不预先承诺推进时间表；warning Scenario 钉死 `N_e = 16` + 引用独立 change 是 cross-change scope boundary 声明，不依赖独立 change 实际 propose
- **future Phase 0 K-Means 实现的 K-Means 算法选择**: spec req-14 仅说 "Spherical K-Means seeding"，未规定 K-Means 算法变体（sklearn / 自实现 / scipy）；future 实现可自行选择，但 K-Means 簇数 = `N_e = 16` 是 spec 真相。本 change 不预先承诺 K-Means 算法选择
- **Phase 0 K-Means runtime cost**: 1K steps Phase 0 是 spec req-14 时间驱动边界；future 实现 Phase 0 K-Means 计算 cost 是否影响 1K step 时间预算？本 change 不预先承诺 Phase 0 K-Means runtime cost 评估