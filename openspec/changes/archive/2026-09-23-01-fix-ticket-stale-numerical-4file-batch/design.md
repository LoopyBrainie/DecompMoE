## Context

2026-09-18 audit-verification loop 完成 cycle-5/6/7 三条 MEDIUM finding 三轴 (α + β + γ) 复核（`.audit/audit-verification/audit-verification.md` L11-L677）。三条 finding 形成**同源 "ticket 端 stale 数值源头" pattern**：
- **cycle-5 #1**：ticket `A5-3.md` L62 θ_Voronoi ~52°（估算）vs spec req-11 L185 bisection 67.24°（残差 < 1e-9）—— **15.24° drift (29% relative)**，50-digit mpmath Lentz CF 独立复算验证 `θ_Voronoi(16,16) = 1.1735474259 rad = 67.239315°`（verify-1 axis-α）
- **cycle-6 #1**：`MVPConfig.beta_initial = 1.0`（src/config.py L54）vs spec req-7 L122 β_0 = 1.035060（闭式 `0.1 + 31.9·σ(−3.5)`）—— **3.39% drift**，50-digit mpmath 锁死 `β_0 = 1.0350601609682665718`，反向 γ 反推 `−3.5393477201429725472`（verify-4 axis-α）
- **cycle-7 #1**：ticket `A4-1.md` L58 `β_0 ≈ 1.0` vs spec req-7 L122 β_0 = 1.035060 —— **3.39% drift**（数值与 cycle-6 精确相同但传染链结构不同，cycle-7 锁定 ticket 端源头 cycle-6 锁定 src/tests 端）

附加两条 LOW spec delta（cycle-7 finding 2 + 3）：
- **finding 2 (LOW)**：spec req-7 L122 `σ'(−3.5) ≈ 0.0284` 精度欠一位（实际 50-digit = `0.02845302387973555984`），与 `β_0 ≈ 1.035` 精度风格不对齐
- **finding 3 (LOW)**：spec req-7 L126 Source 字段只列 A4-1，但 req-7 正文 L120/L124 显式引用 A4-2 + A6b-1

**传染链状态（verify-6 + verify-9 横向 lock-down）**：

| 路径 | 状态 |
|---|---|
| `spec ↔ src/decompmoe/beta.py` | ✓ CLEAN（用 spec L115 Sigmoid 闭式，不读 MVPConfig.beta_initial） |
| `spec ↔ src/decompmoe/sphere.py` | ✓ CLEAN（用 `canonical_voronoi_angle` API，无 52° 硬编码） |
| `spec ↔ tests/test_sphere.py` | ✓ CLEAN + GUARDED（`test_voronoi_canonical_mvp_value` 等守 canonical API） |
| `spec ↔ ticket A5-3 L62 / A1-1 L97` | ⚠️ STALE（仅 ticket 端 stale，spec 钉死 67.24°） |
| `spec ↔ ticket A4-1 L58` | ⚠️ STALE |
| `spec ↔ MVPConfig.beta_initial` | ⚠️ STALE（1.0 vs 1.035060） |
| `MVPConfig.beta_initial ↔ src/` | ⚠️ DEAD FIELD（src/ 全树 0 读取，仅 tests/test_beta.py:38 assert） |
| `MVPConfig.beta_initial ↔ tests/test_beta.py` | ⚠️ LOCKS STALE（`assert == 1.0` 钉死） |
| `ticket A4-1 L58 ↔ MVPConfig.beta_initial` | ⚠️ SAME SOURCE（config.py L50-53 docstring 直接抄 ticket L58 "proxy for γ₀ ≈ −3.5"） |

**CLAUDE.md §2 真相源层级在元审计视角下 cross-validated**：spec 是钉死真相（含完整闭式 + 50-digit 数值锚点），ticket 是手算摘要（信息量少，缺失 σ'(−3.5) ≈ 0.02845 健康度信息等），MVPConfig 默认值直接抄 ticket stale 值——形成 `ticket → MVPConfig → tests` 三级传染链。**advisory 不等于无影响**（CLAUDE.md §8 tickets 已 reference-only，但 ticket stale 仍可传染 src/）。

## Goals / Non-Goals

**Goals:**
- 关闭 3 条 MEDIUM finding + 2 条 LOW finding（cycle-5/6/7 + cycle-7 finding 2/3），每项有独立的 spec/code 对账点（CLAUDE.md §6 第 8 条"sentinel closed-form constant must directly verify"原则）
- 维持 `design.md` Decision 1（D1）：算法常量 `β_min = 0.1` / `β_max = 32` 位于 `decompmoe/beta.py` 模块级 `Final[float]`，MVPConfig 仅承载几何常量 + `beta_initial` 字段
- **5-file 边界修改**（ticket A5-3 L62 + ticket A1-1 L97 + ticket A4-1 L58 + MVPConfig L54 + test_beta.py L38）+ 2 处 spec delta（req-7 L122 + L126）
- **不删 ticket 原 stale 值**——仅追加 `(historical, ...; superseded by ...)` 注释保持 lineage 可读（与 spec L247 supersede annotation canonical 格式一致）
- tests/ 1 文件 1 个 test 修改（`test_beta_param_init_default` 改 `pytest.approx(1.035, abs=1e-6)`），**不修改**其他既有 tests
- 现有 tests 全绿 + 修改 test 全绿

**Non-Goals:**
- 不动 `decompmoe/beta.py` 模块级常量（`BETA_MIN` / `BETA_MAX` / `MAX_GRAD_PER_C` / `MAX_GRAD_PER_GAMMA` 等保持 Final 不变）
- 不动 MVPConfig 其他字段（11 个字段集合保持不变）
- 不重写 wayfinder ticket 内容（仅追加 supersede annotation）
- 不动 `tests/test_sphere.py`（cycle-5 finding 传染链已断于 src/tests/spec 三角干净）
- 不动 `tests/test_config.py`（req-11 整数闭式 bare `==` 锁 452M/100M 已合规）
- 不引入新 cfg 形参、不引入新 MVPConfig 字段
- 不引入 custom CUDA/Triton kernel
- 不把 C_t 写入 KV Cache
- 不引入 shared expert
- 不在 logit 中使用 w_i

## Decisions

### Decision 1: ticket 端修复方向 —— 追加 supersede annotation 而非删除原值

**Choice**: ticket `A5-3.md` L62 θ_Voronoi ~52° 行后追加 `(historical, ~52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)`；ticket `A1-1.md` L97 θ_Voronoi≈52° 行后追加 `(historical, θ_Voronoi≈52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)`（与 A5-3 L62 平行, 同属 cycle-5 #1 同源 ticket 端源头 per audit-verification.md L132）；ticket `A4-1.md` L58 β_0 ≈ 1.0 行后追加 `(historical, β_0 ≈ 1.0 estimate; superseded by spec req-7 L122 closed-form β_0 = 1.035060 via change fix-math-consistency-audit-2026-08 Decision 1)`。

**Rationale**: 复用 spec L247 已建立的 canonical 格式（`fix-openspec-doc-bugs` Decision 7 处理 ticket A6a-2 L63 1/128 stale 同样走"保留原值 + 加 supersede annotation"路径）。删除原 stale 数字会破坏 ticket 的决策 trail（reader 无法追溯当时为何写 ~52° / ≈ 1.0），且 spec 不消费 ticket 数值（spec 是闭式真相），故原 stale 值不构成 runtime 风险——仅追加注释让 future reader 知道 stale 数字是历史估算而非当前真相。A1-1 L97 包含在 scope 内是 cycle-5 finding 的源头完整性要求 —— audit-verification.md L132 字面锁定 `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°`，属 ticket → spec 闭式 supersede annotation 路径，与 A5-3 L62 决策路径完全平行。

**Alternatives considered**:
- (a) 删除原 stale 数字改 67.24° / 1.035060 —— 拒绝：破坏 ticket 历史决策 trail；ticket 是 advisory non-binding（CLAUDE.md §8），无必要重写历史
- (b) ticket 完全不动改 spec —— 拒绝：spec 已经是 67.24° / 1.035060 真相，ticket stale 不构成 spec 端问题
- (c) ticket 整文件废弃 —— 拒绝：ticket 是 advisory 参考，废弃超出 scope（CLAUDE.md §3 surgical 原则）

### Decision 2: MVPConfig.beta_initial 默认值修改方向 —— 1.0 → 1.035 + docstring 移除 TODO

**Choice**: `src/decompmoe/config.py:50-54` `beta_initial: float = 1.0` → `beta_initial: float = 1.035`；L50-53 docstring `tracked as \`★ TODO\` in the plan §ST-02` 移除，改 `per spec req-7 L122 closed-form β_0 = 1.035060 (verified at 50-digit mpmath: σ(γ_init=−3.5) = 0.029312230751356318865, β_0 = 1.0350601609682665718)`。

**Rationale**: MVPConfig.beta_initial 是 dead field（src/ 仅 config.py:54 定义，grep verify 无任何文件读取），修改无 runtime 传染。**1.0 vs 1.035060 选择**：选 `1.035` (3 位有效数字) 与 spec req-7 L122 `β_0 ≈ 1.035` narrative 风格对齐；**不选** `1.035060` (6 位有效数字) 因 MVPConfig 字段是"概略初始值"而非"精确闭式锚点"。docstring 移除 TODO 追踪是 follow-up（cycle-6 已 trace TODO 是"已知但未修复 drift"的信号）；改后 docstring 明文"per spec req-7 L122 closed-form"建立 spec → src 权威链。

**Alternatives considered**:
- (a) 默认值改 `1.035060` (6 位有效数字) —— 拒绝：MVPConfig 字段风格是 narrative 概略，与 spec narrative 风格一致更重要
- (b) 不修改默认值仅改 docstring —— 拒绝：MVPConfig.beta_initial 1.0 与 spec req-7 L122 1.035060 仍 drift 3.39%，未解决 cycle-6 finding
- (c) 删除 `beta_initial` 字段（dead field） —— 拒绝：会破坏 tests/test_beta.py:38 caller 与可能的外部 import 链；超出 scope

### Decision 3: tests/test_beta.py:38 修复方向 —— bare `==` 改 `pytest.approx(1.035, abs=1e-6)`

**Choice**: `tests/test_beta.py:38` `assert MVPConfig().beta_initial == 1.0` 改 `assert MVPConfig().beta_initial == pytest.approx(1.035, abs=1e-6)`；L37 docstring `MVPConfig().beta_initial == 1.0 (proxy for γ₀ ≈ −3.5 per plan §ST-02)` 改 `MVPConfig().beta_initial ≈ 1.035 (per spec req-7 L122 closed-form; proxy for γ₀ ≈ −3.5)`。

**Rationale**: governance/spec.md req-gov-1 第 2 条硬卡"Closed-form float claims MUST `pytest.approx(value, abs=...)`, NOT bare `==`"。`abs=1e-6` 与 spec L122 β_0 narrative 风格（`≈ 1.035`）+ bisection Voronoi `abs=1e-6` 一致。**嵌入 `f"actual={...}"` 失败信息**（per CLAUDE.md §3 TDD convention + governance/spec.md req-gov-1 第 4 条）保证 regression 时 surface actual computed value。

**Alternatives considered**:
- (a) `pytest.approx(1.035, abs=1e-4)` —— 拒绝：abs=1e-4 比 bisection 噪声阈值宽，与 cycle-5 voronoi `abs=1e-6` 风格不对齐
- (b) `pytest.approx(1.035060, abs=1e-6)` —— 等价（spec L122 narrative 用 1.035060 6 位有效数字）；选 `1.035` 与 spec narrative `≈ 1.035` 一致更直接
- (c) 保留 bare `==` 改 1.0 → 1.035060 —— 拒绝：违反 governance/spec.md req-gov-1 第 2 条硬卡

### Decision 4: spec req-7 L122 σ' precision 微调方向 —— 0.0284 → 0.02845

**Choice**: spec req-7 L122 narrative `σ'(−3.5) ≈ 0.0284` 微调 `σ'(−3.5) ≈ 0.02845`（5 位有效数字）。

**Rationale**: 50-digit mpmath（verify-7 axis-α）`σ'(−3.5) = 0.02845302387973555984`，spec 当前 4 位有效数字 `0.0284` 截断过早（diff = 0.000053 = 0.18% relative）。β_0 narrative 用 4 位 `≈ 1.035`，σ' 改 5 位 `≈ 0.02845` 与 β_0 narrative 精度风格一致。**不改 L122 β_0 闭式**（`0.1 + 31.9·σ(−3.5) ≈ 1.035` 已合规），仅改 σ' narrative 字面。

**Alternatives considered**:
- (a) 改 `σ'(−3.5) ≈ 0.028453` (6 位有效数字) —— 拒绝：与 β_0 narrative `≈ 1.035` (4 位) 不对齐，5 位 0.02845 是最佳折衷
- (b) 完全删除 σ' narrative（避免精度披露） —— 拒绝：σ' 健康度是 cycle-7 finding 1 的关键不变量（"healthy gradient"），删除会破坏 spec 的不变量信息
- (c) 改 `σ'(−3.5) = 0.02845302387973555984` (18 位) —— 拒绝：spec 是 narrative 风格不是 50-digit 闭式；18 位会让 reader 误以为 spec 是 50-digit 锚点

### Decision 5: spec req-7 L126 Source 字段补齐方向 —— 1 → 3 ticket（A4-1 + A4-2 + A6b-1）

**Choice**: `**Source:** \`wayfinder/tickets/A4-1.md\`` 改 `**Source:** \`wayfinder/tickets/A4-1.md\`, \`wayfinder/tickets/A4-2.md\`, \`wayfinder/tickets/A6b-1.md\``。

**Rationale**: req-7 正文 L120 显式引用 A6b-1 (AdamW momentum reset on Phase 4 entry)，L124 显式引用 A4-2 (w_i 剔除) + CLAUDE.md §6 —— Source 字段应反映 spec 实际引用的所有 ticket。**主反链 A4-1 必须首位**（per req-34 lint "主反链必须是第一个 top-level item, paren-depth-aware, code-span atomic split"）。三 ticket 顺序： A4-1（主来源，β 参数化闭式）→ A4-2（w_i 剔除，与 L124 narrative 直接关联）→ A6b-1（AdamW momentum reset，与 L120 narrative 直接关联）—— 按 spec 引用密度排序。

**Alternatives considered**:
- (a) 改 `A4-1, A6b-1, A4-2`（按 ticket ID 字母排序） —— 拒绝：与 spec L120/L124 引用顺序不对齐，破坏 reader traceability
- (b) 改 `A4-1, A4-2, A6b-1` 但用 `(historical, ...)` 标注 A4-2 / A6b-1 —— 拒绝：A4-2 与 A6b-1 不是 historical superseded ticket，它们是当前 spec 仍引用的现行 ticket
- (c) 仅补 A6b-1（不补 A4-2）—— 拒绝：cycle-7 finding 3 明确指出两 ticket 都漏报；A4-2 与 L124 w_i 引用直接关联

## Risks / Trade-offs

- **[Risk]** ticket supersede annotation 加错位置（A5-3 L62 / A4-1 L58）导致 reader 读到 stale 数字而非 supersede 注释。Mitigation：annotation 加 stale 数字**紧邻行**（同一行末尾或下一行），并明示 `(historical, ...)` 与 `(superseded by ...)` 两段
- **[Risk]** MVPConfig.beta_initial 1.0 → 1.035 影响下游 caller。Mitigation：verify-6 已 grep verify src/ 全树无读取该字段；tests/test_beta.py:38 是唯一 caller，本 change 同步更新
- **[Risk]** spec req-7 L122 σ' precision 微调破坏 cycle-7 finding 4（Phase 4 连续性）50-digit 闭式测试。Mitigation：σ'(−3.5) 微调是 narrative 精度，不影响 L115 Sigmoid 闭式本身（σ' = σ(1-σ) 数学闭式不变）；Phase 4 连续性验证用 γ=ln(15/16) 而非 σ'(−3.5)
- **[Risk]** spec req-7 L126 Source 字段 1 → 3 ticket 触发 req-34 lint failure（主反链非首位）。Mitigation：新顺序 A4-1 首位 + A4-2 第二 + A6b-1 第三，符合 req-34 paren-depth-aware atomic split
- **[Risk]** tests/test_beta.py:38 `pytest.approx(1.035, abs=1e-6)` 与现有 141 tests 行为冲突。Mitigation：cycle-6 verify-6 已确认该 test 是唯一消费方；修改后 test 全绿即可
- **[Risk]** Windows Edit tool CRLF contamination（src/ + ticket + tests + spec）。Mitigation：每个 Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`（per [[windows-edit-crlf-pitfall]] memory）
- **[Risk]** 50-digit mpmath 重算脚本 `.audit/verify_beta0_alpha.py` 与 `.audit/verify_ticket_a41_alpha.py` 在 verify-4/7 已锁死；本 change 无需重跑，仅 spec/ticket/src/tests 四端对齐到 50-digit 锚点

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical spec delta + 5-file 边界修改。实施步骤：
1. spec delta 落地：`specs/wayfinder/spec.md` 2 处 MODIFIED（req-7 L122 σ' precision + L126 Source 字段）
2. ticket 端 supersede annotation：`wayfinder/tickets/A5-3.md` L62 + `wayfinder/tickets/A1-1.md` L97 + `wayfinder/tickets/A4-1.md` L58 各加一行注释（**追加不删原值**）
3. src/ surgical edit：`src/decompmoe/config.py:50-54` MVPConfig.beta_initial 默认值 1.0 → 1.035 + docstring 移除 TODO 改 spec ref
4. tests/ 1 test 修改：`tests/test_beta.py:37-38` 改 `pytest.approx(1.035, abs=1e-6)` + docstring 更新
5. `uv run pytest tests/ -v` 全绿（141 passed + 1 modified passed = 142 passed；无 regression）
6. `git diff --stat` 验证 LF 保留（无 CRLF contamination）
7. `python scripts/lint_no_dead_defensive.py` + `python scripts/lint_no_source_field_drift.py` 双 lint gate exit=0
8. 单 commit on `dev`：`fix(spec,ticket,code): close cycle-5/6/7 MEDIUM findings (ticket stale numerical 5-file batch)`

## Open Questions

- **Future audit**: cycle-9/12/13 也有 MEDIUM ticket stale findings（verify-10 axis-α 已锁定 cycle-9 f_threshold 1/128 stale 但 spec L245 已 supersede，**实际不是 stale**——是 cycle-9 finding 错判；需在后续 audit-verification 轮次中正式撤销 cycle-9 MEDIUM 评级）；cycle-12 (ticket A8-2 covariance) + cycle-13 (ticket A6b-1 N_e=64) 同源 pattern 是否也需 batch fix？本 change 明确只覆盖 cycle-5/6/7 + cycle-7 finding 2/3；不预先承诺 follow-up 范围
- **ticket 重写 vs annotation 边界**: 当前 Decision 1 选"追加 annotation 而非删除原值"基于 CLAUDE.md §3 surgical 原则；但若未来 ticket stale 数字被外部 reader 误读为"现行真相"，可能需要更激进的 ticket 重写策略。本 change 不预先承诺 follow-up ticket 重写
- **MVPConfig.beta_initial dead field 处置**: 当前 Decision 2 选"修改默认值 + 改 docstring"；若未来 src/ 真有 caller 读取该字段，可能需要再 batch fix（但当前 verify-6 已锁死 src/ 无读取）。本 change 不预先承诺 dead field 删除