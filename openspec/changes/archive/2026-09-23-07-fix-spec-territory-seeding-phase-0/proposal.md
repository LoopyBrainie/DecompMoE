# Proposal

## Why

2026-09-19 audit-verification (`.audit/audit-verification/audit-verification.md` cycle-13 finding + L1192-1204 / L1222) 暴露 spec/code 双面漂移:

- **meta-03 (TERRITORY_SEEDING missing)** —— `openspec/specs/wayfinder/spec.md` L24 Requirement "Formal Symbols And Code Naming" (anchor `<a id="req-2"></a>`) 将 `territory_seeding` 列为 MUST-exist 的 code identifier (snake_case 7 个标识符之一),但 `grep -rn "territory_seeding" src/decompmoe/` 在 2026-09-23 实测**仍 0 命中**(与 2026-09-19 audit-verification 时一致,中间 4 天内未被任何 archived change 修复)。
- **meta-04 (Phase 0 K-Means not implemented)** —— `src/decompmoe/extraction.py:107-108` docstring 明文 `"actual k-means is owned by training-time caller"`,但 spec L78-93 Requirement "C Extraction Differentiability And Centroid Lifecycle" (req-6) Phase 0 子句 (L81) 仍以**活跃合同**形式规定 `"c_i^(t+1) = KMeans(C) initialization"`,**未明文声明 deferred**。两 finding 在"合同是否需要执行"层面互斥:dormant bug 模式,当前 MVP 范围 (CLAUDE.md §7 "Out of Scope" — 训练执行 out-of-scope) 下不触发 active failure,但形成 latent contract gap。

**DEPRECATED 状态澄清 (事实验证结果)**: 此前 `.audit/audit-verification/opsx-changes/07-.../DEPRECATED.md` 声称 "scope 全部并入 `04-fix-ticket-a6b-1-n-e-supersede`"——经 2026-09-23 事实验证,change 04 design.md 第 103 行**明确声明** "**不处理**: TERRITORY_SEEDING 标识符缺失 (独立 change)、Phase 0 K-Means 实现 (独立 change)"。change 04 仅在 `wayfinder/spec.md` req-11 末尾新增 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)`(L231-234)作为间接引用警告,**未实施** spec 一等公民 deferred 声明,亦未添加 `territory_seeding` 函数至 `src/decompmoe/extraction.py`。meta-03 + meta-04 仍 OPEN。

**Severity 评级 MEDIUM dormant**: 当前 Phase 0 K-Means 的 "deferred to caller" 在 MVP 范围下**不触发 active failure**,但形成 dormant contract gap。LOOPS.md "dormant bug pattern" 框架(per `.audit/audit-verification/README.md` "9 个 meta-发现元审计增值" 第 3、4 条)将 latent risk 而非 active rating 分类; 走"spec 显式声明 deferred + 代码侧薄占位标识符" 路径而非"补全 K-Means 实现"。

**修复方向 (合并)**: (a) `src/decompmoe/extraction.py` 末尾 (`__all__` 之前,line 174) 新增薄占位函数 `territory_seeding(C_batch, N_e, *, d_c) -> Tensor`,签名符合 spec req-2 L24 的标识符契约;函数体 `raise NotImplementedError(...)` 显式指向 spec req-6 Phase 0 deferred 条款,实现代码与 `extraction.py:107-108` 注释保持一致;(b) spec req-6 Phase 0 子句 (L81) 追加 deferred 声明段,把 deferred 状态从代码注释提升到 spec 一等公民;(c) spec req-2 L24 identifier map 保留 `territory_seeding`,但追加 inline 注脚说明 deferred contract;(d) 新 Requirement "Territory Seeding Deferred Contract" (anchor **`<a id="req-6"></a>`**,**next-free 实测确认**——当前 spec anchors: req-1/2/3/4/5 → **req-7** 跳跃,req-6 anchor 当前缺失)。

## What Changes

### wayfinder spec delta (2 处 MODIFIED, 1 处 ADDED)

1. **MODIFIED** Requirement "Formal Symbols And Code Naming" (req-2, L20-26, anchor `<a id="req-2"></a>`): 标识符映射表保留 `territory_seeding`,追加 inline 注脚,明文承认 `territory_seeding` 是 canonical API contract name,函数体在 MVP 范围内显式 deferred to training-time caller (per Phase 0 spec 条款)。保持标识符映射完整性,避免 future maintainer 误以为标识符缺失 = 必删条目。

2. **MODIFIED** Requirement "C Extraction Differentiability And Centroid Lifecycle" (req-6, L76-93, anchor **当前缺失需新增 `<a id="req-6"></a>`**): Phase 0 子句 (L81) 追加 deferred 声明段,原 `"Phase 0 — Spherical K-Means seeding (no gradient, no EMA): c_i^(t+1) = KMeans(C) initialization."` 改为该文本 + 追加 `"Phase 0 K-Means implementation is deferred to the training-time caller (MVP scope per CLAUDE.md §7 'Out of Scope' — training execution out-of-scope). The canonical contract name in the codebase is territory_seeding(C_batch, N_e, *, d_c) (see req-2 L24 identifier map), which currently raises NotImplementedError with a verbatim pointer to this clause. Drivers and inference-time callers MUST NOT call territory_seeding at inference time; CentroidDriver.step Phase 0 (Phase.SEEDING) returns the input centroids detached as a no-op (see src/decompmoe/extraction.py:119-120)."`。**新增 Scenario `Phase 0 K-Means deferred to caller`**: 验算 `territory_seeding(C_batch, N_e, d_c=16)` raises `NotImplementedError` 且错误消息字面引用 spec req-2 + req-6 Phase 0 clause。

3. **ADDED** 新 Requirement "Territory Seeding Deferred Contract" (anchor `<a id="req-10"></a>`,**next-free 实测确认**——当前 spec anchors: req-1/2/3/4/5 → **req-7** 跳跃(req-6 当前缺失,本 change 顺手在 req-6 Requirement title L76 前补齐 `<a id="req-6"></a>`);req-9 (L171) → **req-11** (L197) 跳跃,req-10 anchor 缺失;new Requirement 使用 next-free = req-10。tasks.md A-3.1 apply 阶段必须 `grep -nE '<a id="req-[0-9]+"></a>' openspec/specs/wayfinder/spec.md` 二次确认 anchor 唯一性): 单独把 `territory_seeding` deferred 契约固化,源反链引用 req-2 L24 + req-6 Phase 0 (literal backtick per CLAUDE.md §3 lint 三项结构性检查)。Scenario 复述 `pytest.raises(NotImplementedError)` 行为 + 错误消息 verbatim 对账。**这是为了 spec anchor 100% 覆盖率 (CLAUDE.md §6 第 8 条) + 让 deferred 契约有一条独立的、可被 lint 守门的 Requirement + 顺手补齐 req-6 与 req-10 两个 anchor 缺失**。

### src/ 边界修改 (1 文件 surgical Edit)

- `src/decompmoe/extraction.py:174` (即 `__all__` line 175 之前的空行) —— 新增薄占位函数 `territory_seeding` (函数体 `raise NotImplementedError` + spec-cited message)
- `src/decompmoe/extraction.py:175-179` `__all__` 列表追加 `"territory_seeding"` (满足 req-2 L24 identifier-map MUST-be-in-codebase 契约)
- **不修改**: 现有 `Phase.SEEDING` 分支逻辑 (line 119-120) 保持不变 (`return centroids.detach()`), 与现有 `tests/` 不冲突
- **不修改**: 现有 docstring L107-108 关于"actual k-means is owned by training-time caller"的注释,与 spec delta 方向一致

### tests/ 边界修改 (1 文件新增 1 test)

- `tests/test_extraction.py` 末尾追加 `test_territory_seeding_raises_not_implemented_with_spec_citation` (2026-09-23 实测 `tests/test_extraction.py` 当前 **13 个测试函数**,非 17 个——proposal 旧版本数错; apply 阶段期望 13 passed + 1 new passed = 14 passed)
- **不修改**: 既有 13 个 test (test_pipeline_shape / test_aggregate_across_heads_awareness / test_complexity_budget / test_full_differentiability / test_no_surrogate_in_codebase / test_extract_C_signature / test_empty_cell_preserves_centroid / test_spherical_norm_is_strictly_one / test_near_zero_candidate_fallback / test_near_zero_candidate_fallback_phase4 / test_phase_4_sgd_1_step_closed_form / test_phase_4_sgd_near_zero_candidate_fallback / test_phase_4_grad_none_preserves_legacy_l2_retraction) 全部保持现状

### nothing else

- 不动 `wayfinder/tickets/A1-1.md` / `A2-2.md` / `A3-2.md` (CLAUDE.md §6 第 7 条 + §8 tickets 已 reference-only)
- 不引入 custom CUDA / Triton kernel (CLAUDE.md §6 第 1 条)
- 不把 `C_t` 写入 KV Cache (CLAUDE.md §6 第 2 条)
- 不引入 shared expert (CLAUDE.md §6 第 3 条)
- 不在 logit 中使用 `w_i` (CLAUDE.md §6 第 4 条)
- 不执行训练或跑 baseline (CLAUDE.md §6 第 5 条)
- 不实现真正的 K-Means (deferred 状态是 spec 显式合同,非功能缺失)
- 不动 `openspec/specs/decompmoe-skeleton/spec.md` (decompmoe-skeleton L392 Phase 0 注释已为"caller's responsibility",与 wayfinder Phase 0 deferred 声明自洽,无需 delta)
- 不动 change 04 在 `openspec/specs/wayfinder/spec.md` req-11 末尾新增的 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)` (该 Scenario 引用 `territory_seeding` 为 "track via a separate change",本 change 正是该 separate change 的实现)

## Capabilities

### New Capabilities

(无)

### Modified Capabilities

- `wayfinder`: 2 处 MODIFIED (req-2 L20-26 identifier map inline footnote + req-6 L76-93 Phase 0 sub-clause deferred declaration + 锚点 `<a id="req-6"></a>` 当前缺失需新增) + 1 处 ADDED (新 Requirement "Territory Seeding Deferred Contract",anchor `<a id="req-10"></a>` next-free 实测确认,apply 阶段 grep 二次确认;Anchor conflict 风险已在 Risk 段显式标注)

### Added / Modified Requirements to Existing Capabilities

- `wayfinder` (2 处 MODIFIED + 1 处 ADDED):
  - **MODIFIED** Requirement "Formal Symbols And Code Naming" (req-2 L20-26) —— 标识符映射表保留 `territory_seeding`,追加 inline 注脚说明 deferred contract
  - **MODIFIED** Requirement "C Extraction Differentiability And Centroid Lifecycle" (req-6 L76-93,anchor 当前缺失需新增 `<a id="req-6"></a>`) —— Phase 0 子句 (L81) 追加 deferred 声明;新增 Scenario `Phase 0 K-Means deferred to caller`
  - **ADDED** Requirement "Territory Seeding Deferred Contract" (anchor `<a id="req-10"></a>`,next-free 实测确认,apply 阶段 grep 二次确认) —— 把 `territory_seeding` deferred 契约固化;Scenario 验算 `pytest.raises(NotImplementedError)` + 错误消息 verbatim 对账 spec

## Impact

- **Affected code** (surgical edits per CLAUDE.md §3):
  - `src/decompmoe/extraction.py:174` —— 新增薄占位函数 `territory_seeding` (函数体 `raise NotImplementedError` + spec-cited message)
  - `src/decompmoe/extraction.py:175-179` —— `__all__` 列表追加 `"territory_seeding"`

- **Affected tests** (1 文件,1 新增 test):
  - `tests/test_extraction.py` —— 新增 1 个 test (territory_seeding NotImplementedError contract);既有 13 test 全部不动

- **Affected APIs / dependencies**:
  - 新增 `territory_seeding(C_batch: Tensor, N_e: int, *, d_c: int) -> Tensor` public API (通过 `__all__` 导出)
  - 调用方在 MVP 范围内不应调用此函数 (spec req-6 Phase 0 Scenario 明确禁止 inference-time call)
  - 无新依赖

- **Affected systems**: 无 (推理引擎实现代码已 out-of-scope per CLAUDE.md §7)

- **Risk**:
  - **薄占位函数引入** —— `territory_seeding` 函数体 raise NotImplementedError,future caller 误调会得到清晰错误。Mitigation: 错误消息 verbatim 引用 spec req-2 + req-6 + Phase 0 deferred clause;新增 test 锁契约
  - **spec req-2 L24 标识符映射注脚** —— inline 注脚是 spec 单源真相的一部分,可能被未来 lint 误报为 "off-topic prose"。Mitigation: 注脚使用 spec 标准 footnote 格式 (`**Note:** ...`),与现有 spec 风格一致
  - **新 Requirement anchor 编号 (CRITICAL)** —— 当前 spec anchors 序列为 req-1/2/3/4/5 → **req-7** 跳跃(req-6 当前缺失,本 change 顺手补齐 `<a id="req-6"></a>` 给既有 req-6 Requirement title),req-9 → **req-11** 跳跃(req-10 缺失);**new Requirement anchor 计划使用 `<a id="req-10"></a>`** (next missing number after req-9 L171),apply 阶段必须 `grep -nE '<a id="req-[0-9]+"></a>' openspec/specs/wayfinder/spec.md` 二次确认 anchor 唯一性。若 anchor 已存在或冲突则改用 req-9 后最小 next-free。Mitigation: tasks.md A-3.1 显式声明 "apply 阶段先 grep 确认 anchor 唯一性,硬编码 `<a id="req-10"></a>` 是 best-guess"
  - **CLAUDE.md §6 第 8 条 spec anchor 100% 覆盖** —— 新 Requirement 必须首行 anchor;`req-6` anchor 顺手补齐当前缺失的 anchor。Mitigation: 在 proposal 阶段明确 anchor `<a id="req-6"></a>` 占位,apply 阶段 grep verify
  - **CLAUDE.md §6 第 8 条 Source 反链** —— 新 Requirement 的 Source 反链必须含 `wayfinder/tickets/<ID>.md` literal backtick;Mitigation: 引用 `wayfinder/tickets/A1-1.md` + `wayfinder/tickets/A3-2.md`(分别对应 req-2 L26 与 req-6 L93 已有的 ticket 反链)
  - **test_extraction.py 测试计数** —— 当前实测 13 test,proposal 旧版本错为 17。Mitigation: 本 proposal 已纠正为 13 + 1 = 14
  - **change 04 已有 Scenario 不冲突** —— change 04 在 req-11 末尾 (L231-234) 新增的 Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)` 引用 `territory_seeding` 为 "track via a separate change";本 change 正是该 separate change,Scenario 不动,与本 change 新增的 req-6 Phase 0 Scenario `Phase 0 K-Means deferred to caller` 互补不冲突
  - **Windows Edit tool CRLF contamination** —— 修 src/ 后跑 `git diff --stat` 验证 LF 保留, 必要时 `sed -i 's/\r$//'` (per [[windows-edit-crlf-pitfall]] memory rule)

- **Source**: 清单 2 元审计 (`audit-verification.md` 2026-09-19 + 2026-09-23 事实验证复核) meta-03 + meta-04, 每项独立证据链:
  - meta-03: `grep -rn "territory_seeding" src/decompmoe/` 返回 0 命中 (2026-09-23 实测);spec L24 标识符映射表 `territory_seeding` 列入 MUST-map 列表
  - meta-04: `src/decompmoe/extraction.py:107-108` docstring 注释 "actual k-means is owned by training-time caller";spec L81 Phase 0 子句 "c_i^(t+1) = KMeans(C) initialization" 未明文声明 deferred;双向对照
  - 合并修复: spec 显式声明 deferred + 代码侧薄占位函数满足 req-2 标识符映射 = 两个 finding 在一次 delta 中同步 close
  - change 04 合并覆盖证明: change 04 design.md L103 显式声明 "不处理 TERRITORY_SEEDING 标识符缺失 (独立 change)" —— 写背景是 meta-03/meta-04 的 OPEN state,本 change 是 change 04 explicitly carved-out 的独立 change scope