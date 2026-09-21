# Proposal: fix-ticket-a6b-1-n-e-supersede

## Why

2026-09-18 audit-verification loop 完成 cycle-13 MEDIUM finding #1 三轴 (α + β + γ) 复核（`.audit/audit-verification/audit-verification.md` verify-16/17/18）。本 change 锁定 cycle-13 finding #1（ticket A6b-1 L100 `N_e = 64` stale）+ cycle-13 finding 2（LOW ticket A6b-1 L131 γ' reset formula coverage gap），配合 spec req-11 dormant bug 标注，共同形成 "ticket 端 stale 数值源头" 同源 pattern family 的新一条修复。

| finding | 源头端 | stale 值 | spec 真相 | drift | 类型 |
|---|---|---|---|---|---|
| cycle-13 #1 | ticket `A6b-1.md` L100 | `Spherical k-means 聚 N_e = 64 类` | `N_e = 16` (MVP, spec req-11) | **4.0x ratio / 300% relative** (整数漂移) | MEDIUM dormant |
| cycle-13 #2 | ticket `A6b-1.md` L131 γ' reset | 仅 narrative，无显式 formula | `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` (spec req-7) | coverage gap（非 drift）| LOW |

附加 cycle-13 finding 3（INFO 五阶段编排 spec ↔ ticket 高度对齐，**CITE-OK 无需修复**）作为 cross-validation 旁注。

**cycle-13 是 ticket-stale pattern 中最特殊的一条**（verify-18 axis-γ meta 发现）：

1. **当前 src/ 未实现 Phase 0 K-Means** —— `src/decompmoe/extraction.py:107-108` "Phase 0 (SEEDING): no-op (returns centroids detached — actual k-means is owned by training-time caller)"；spec req-2 L24 列出的 7 个 code identifier 中 `territory_seeding` 是**唯一**在 src/ 中不存在的标识符（Grep 0 matches）—— 意味着 Phase 0 K-Means 整段 deferred
2. **future implementation 必须显式用 spec `N_e = 16`** 而非 ticket `N_e = 64` —— 任何实现 TERRITORY_SEEDING 模块的工程师都大概率读 ticket A6b-1 L100（这是 ticket 唯一 explicit spec），会复制 `N_e = 64` stale value → 致命 48 orphan clusters（4.0x ratio 下 `64 − 16 = 48` 个 cluster 永远得不到 routing 概率质量，因 MVP `k = 2` top-k 仅取 `N_e = 16` 中概率最高的 2 个专家）
3. **当前无 active functional impact** —— latent risk 而非 active risk，但 dormant bug 模式（spec ↔ src/ 干净，但 ticket ↔ future 实现脆弱）

**TERRITORY_SEEDING 标识符缺失 + Phase 0 K-Means not implemented 归入独立 change**（`fix-spec-territory-seeding-phase-0`，per `.audit/audit-verification/opsx-changes/README.md`）。本 change 仅处理 ticket 端 stale 标注 + spec 端 dormant bug 警告，不触及 spec req-2 L24 code identifier 列表，不触及 `src/decompmoe/extraction.py`。

**CLAUDE.md §6 第 8 条 + governance/spec.md req-gov-1 第 1 条遵守**：整数闭式（spec `N_e = 16` vs ticket `N_e = 64`）必须 bare `==` 对账（governance 第 1 条硬卡 "Closed-form integer claims ... MUST use **bare `==` integer equality** ... NOT `pytest.approx(...)` in any form"），不使用 `pytest.approx(..., abs=0)`（其默认 `rel=1e-12` 随量级缩放，违背"钉值零容差"意图）。spec narrative `N_e = 16` 与 ticket verbatim `N_e = 64` 通过 `16 == 16`（int）+ `64 == 64`（int）独立验证。

## What Changes

### ticket 端 supersede annotation（2 项）

1. **ticket A6b-1 L100（cycle-13 finding #1, MEDIUM dormant）** —— 在 `Spherical k-means 聚 N_e = 64 类` 行后追加注释（**仅追加，不删原值**）：`(historical, N_e = 64 K-Means design from N_e=64 时代; superseded by spec req-11 MVP N_e = 16 — any future Phase 0 K-Means implementation MUST use spec N_e = 16 to avoid 48 orphan clusters fatal drift)`。复用 change 01 ticket A5-3 L62 + A4-1 L58 supersede annotation canonical 格式。
2. **ticket A6b-1 L131（cycle-13 finding #2, LOW）** —— 在 `**Phase 4 切换瞬间重置 Adam 动量状态**（EMA 状态对 Projected SGD 无效）` 行后追加注释（**仅追加，不删原值**）：`(historical, narrative-only; closed-form γ' = ln((β_{p3} − 1) / (32 − β_{p3})) lives in spec req-7 — ticket deliberately omits explicit formula as design-prose; supersede path: spec req-7 + req-14 'Five-Phase Time-Driven Schedule' Phase 4 transition Scenario (L301-303 'Adam momentum reset on Phase 4 entry'))`。该 annotation 不视作 supersede（spec 已显式 formula），仅显式 "ticket 故意省略 formula" 的 metadata。

### wayfinder spec delta（1 项）

3. **req-11 新增 dormant bug 警告 Scenario（cycle-13 finding #1, MEDIUM dormant）** —— 在现有 Scenario `Voronoi angle is N_e- and d_c-dependent` (L227-229) **之后**、Scenario `Voronoi closed-form residual is bounded` (L231-233) **之前**新增 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)`，明文钉死 spec 真相与 ticket stale 边界：

   **WHEN** any future implementation of Phase 0 Spherical K-Means seeding (per spec req-14 'Five-Phase Time-Driven Schedule' Phase 0 description (L293)) references wayfinder ticket A6b-1.md L100 (which historically stated `Spherical k-means 聚 N_e = 64 类`)
   **THEN** the implementation MUST use the MVP `N_e = 16` from spec req-11 (and `d_c = 16` from spec req-11) — NOT the ticket's historical `N_e = 64` value. The historical 4.0x ratio (64/16) would produce `N_e = 64` clusters of which `64 − 16 = 48` are "orphan clusters" never receiving any routing probability mass under the MVP `k = 2` top-k routing (per spec req-11 `k = 2`), a fatal topology bug.

   **AND** the `territory_seeding` code identifier from spec req-2 L24 is the canonical name for the Phase 0 seeding module (track via separate change `fix-spec-territory-seeding-phase-0`; this Scenario pins only the `N_e = 16` value, not the module name).

**重要边界**：spec MVP `N_e = 16` 主闭式数字不动一字；本 change 仅在其后新增 Scenario 作为 dormant bug 警告，**不改主闭式数字**（与之前 change 01/02/03 同 pattern：只改 spec 周边 narrative，不动 spec 主闭式数字）。

### nothing else

不动 `openspec/specs/wayfinder/spec.md` req-14 Phase 0 段（"Phase 0 MUST be Spherical K-Means seeding" 已是 spec 真相，已足够明确；本 change 不重复强调）。不动 `openspec/specs/wayfinder/spec.md` req-11 Source 字段（已含 `\`wayfinder/tickets/A5-3.md\`` 主反链首位 + backtick-wrapped，lint req-34 已合规）。不动 `wayfinder/tickets/A6b-1.md` L100/L131 之外的其他行（仅追加注释不删原值）。不动 `src/decompmoe/extraction.py`（Phase 0 K-Means deferred to caller，归独立 change scope）。不动 `tests/test_extraction.py`（无 Phase 0 测试用例，因 deferred）。不动 `openspec/specs/decompmoe-skeleton/spec.md`（cycle-13 无 skeleton 端 finding；spec req-2 L24 TERRITORY_SEEDING 缺失归独立 change）。不动 `openspec/specs/governance/spec.md`（CLAUDE.md §6 + governance req-gov-1 第 1 条整数闭式 bare `==` 条款已合规；本 change 无新算式）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder`：Requirement "4070 MVP Hyperparameter Set" 末尾新增 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)`，作为 cycle-13 finding #1 MEDIUM dormant finding 的 spec-side 反向吸收 + ticket stale supersede annotation 的 spec-side 锚点。无 Scenario 数量削减（保留 "Voronoi angle is N_e- and d_c-dependent" + "Voronoi closed-form residual is bounded" 等现有 Scenario）；无 Requirement 数量变化；无 `**Source:**` 字段变化。

### Added / Modified Requirements to Existing Capabilities

- `wayfinder` (1 处 spec delta)：
  - **MODIFIED** Requirement "4070 MVP Hyperparameter Set" —— 在现有 Scenario "Voronoi angle is N_e- and d_c-dependent" 之后、"Voronoi closed-form residual is bounded" 之前**新增** Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)`，明文钉死 MVP `N_e = 16` 为 Phase 0 K-Means 唯一真相；引用 ticket A6b-1 L100 stale value 作为反例。主闭式数字（`N_e = 16`）+ Voronoi 表 + canonical API + parameter accounting 全部不动一字

无 `decompmoe-skeleton` spec delta（cycle-13 finding #1 仅锁定 ticket 端 + spec req-11 警告，skeleton spec 端干净；spec req-2 L24 TERRITORY_SEEDING 缺失归独立 change）。

无 `governance` spec delta（无需新增 governance-origin 条款；CLAUDE.md §6 + governance/spec.md req-gov-1 第 1 条整数闭式 bare `==` 义务已合规覆盖，本 change 无新算式）。

## Impact

- **Affected code**（surgical edits per CLAUDE.md §3）：
  - `wayfinder/tickets/A6b-1.md:100` —— `Spherical k-means 聚 N_e = 64 类` 行后追加 historical supersede annotation（**仅追加，不删原值**）
  - `wayfinder/tickets/A6b-1.md:131` —— `**Phase 4 切换瞬间重置 Adam 动量状态**` 行后追加 coverage-gap 注释（**仅追加，不删原值**）
  - `openspec/specs/wayfinder/spec.md` —— 在 req-11 内 `Voronoi angle is N_e- and d_c-dependent` Scenario 之后、`Voronoi closed-form residual is bounded` Scenario 之前新增 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)`

- **Affected tests**（0 文件）：本 change 不涉及 test 修改 —— dormant bug 当前无 active runtime，TERRITORY_SEEDING 模块 deferred to caller；未来 Phase 0 K-Means 实现需自带 test（独立 change scope）

- **Affected APIs / dependencies**：
  - 无 API 签名变更
  - 无新依赖
  - 无模块新增（TERRITORY_SEEDING deferred；归独立 change scope）

- **Affected systems**：无（推理引擎实现代码已 out-of-scope per CLAUDE.md §7）

- **Risk**：
  - **ticket L100 `N_e=64` supersede annotation 加错位置**：Mitigation —— annotation 加 `Spherical k-means 聚 N_e = 64 类` 行**紧邻下一行**（不内嵌原文中间），并明示 `(historical, N_e = 64 ...)` + `(superseded by spec req-11 MVP N_e = 16)` 两段；与之前 change 01 ticket A5-3 L62 + A4-1 L58 supersede annotation 风格一致
  - **ticket L131 γ' formula coverage gap annotation**：Mitigation —— 该 annotation **不视为** supersede（spec 已显式 formula，ticket 故意省略避免重复）；annotation 仅声明 "ticket 故意省略 formula as design-prose; spec is single source of truth"，避免 future reader 误读 "ticket 缺 formula → spec 缺 formula"
  - **spec req-11 新增 dormant bug Scenario 与现有 Scenario 风格对齐**：Mitigation —— 复用现有 `Voronoi angle is N_e- and d_c-dependent` Scenario 的 **WHEN/THEN/AND** Markdown 结构；Scenario 标题加 `(dormant bug warning)` 标记与 cycle-13 verify-18 axis-γ meta 发现对齐
  - **spec req-11 新增 Scenario 不破坏现有 `Voronoi closed-form residual is bounded` Scenario**：Mitigation —— 新 Scenario 插入前者之后、后者之前；Scenario 数量从 4 → 5；现有 Scenario 一字不动
  - **Windows Edit tool CRLF contamination**（ticket + spec 三个文件）：Mitigation —— 每个 Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`（per [[windows-edit-crlf-pitfall]] memory）

- **Source**：
  - cycle-13 finding #1 主 finding：`.audit/spec-math-audit.md` cycle-13 req-14 axis-a finding 1（L587-590）；三轴复核 `.audit/audit-verification/audit-verification.md` verify-16/17/18
  - cycle-13 finding #2 LOW finding：cycle-13 finding 2 在 audit-verification.md verify-17 复核；spec γ' formula 与 ticket L131 narrative coverage gap
  - cycle-13 meta 发现（dormant bug + TERRITORY_SEEDING）：audit-verification.md verify-16；TERRITORY_SEEDING 缺失归独立 change，本 change 仅处理 ticket 端 + spec 端 warning
  - 整数闭式对账 bare `==` 强制条款：governance/spec.md req-gov-1 第 1 条（"Closed-form integer claims ... MUST use **bare `==` integer equality** ... NOT `pytest.approx(...)` in any form"）；本 change 所有整数数字（`N_e = 16` / `N_e = 64` / ratio = 4 / orphan = 48）都是 exact integer，bare `==` 严格对账