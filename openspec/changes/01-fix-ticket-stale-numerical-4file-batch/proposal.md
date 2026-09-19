## Why

`2026-09-18` audit-verification loop 完成 cycle-5 / cycle-6 / cycle-7 三条 MEDIUM finding 的三轴 (α + β + γ) 复核，三条 finding 形成**同源 "ticket 端 stale 数值源头" pattern**：cycle-5 锁定 `wayfinder/tickets/A5-3.md` L62 + `wayfinder/tickets/A1-1.md` L97（θ_Voronoi 估算 ~52° vs spec req-11 L185 bisection 67.24°，drift 15.24°）；cycle-6 锁定 `src/decompmoe/config.py:54` `MVPConfig.beta_initial = 1.0`（vs spec req-7 L122 闭式 β_0 = 1.035060，drift 3.39%），传染到 `tests/test_beta.py:38` `assert == 1.0` 钉死 stale；cycle-7 锁定 `wayfinder/tickets/A4-1.md` L58 `β_0 ≈ 1.0`（同源 3.39% drift，cycle-6 锁 src/tests 端、cycle-7 锁 ticket 端源头）。来源字面见 `.audit/audit-verification/audit-verification.md` L36（cycle-5 一句话复核 block）。

附 cycle-7 finding 2 / 3 两条 LOW：`specs/wayfinder/spec.md` L122 narrative `σ'(−3.5) ≈ 0.0284` 精度欠一位（50-digit mpmath = `0.02845302387973555984`，应改 `≈ 0.02845` 与 β_0 narrative 精度风格对齐）；`specs/wayfinder/spec.md` L126 Source 字段只列 `A4-1`，但 req-7 正文 L120 / L124 显式引用 `A6b-1` (AdamW momentum reset) + `A4-2` (w_i 剔除)，应补齐反链。

**传染链状态**（verify-6 + verify-9 lock-down）：`spec ↔ src/decompmoe/beta.py` ✓ CLEAN（用 spec L115 Sigmoid 闭式，不读 `MVPConfig.beta_initial`）；`spec ↔ src/decompmoe/sphere.py` ✓ CLEAN（用 `canonical_voronoi_angle` API，无 52° 硬编码）；`spec ↔ tests/test_sphere.py` ✓ CLEAN + GUARDED（`test_voronoi_canonical_mvp_value` 等守 canonical API）；`spec ↔ ticket` ⚠️ STALE（仅 ticket 端 stale，spec 钉死 67.24°）；`spec ↔ MVPConfig.beta_initial` ⚠️ STALE（1.0 vs 1.035060）；`MVPConfig.beta_initial ↔ src/` ⚠️ DEAD FIELD（`src/` 全树 0 读取，仅 `tests/test_beta.py:38` assert）。

**D1 决策保留**（沿用 `fix-math-consistency-and-contract-closure-2026-09` design.md D1）：算法常量 `β_min = 0.1` / `β_max = 32` 位于 `decompmoe/beta.py` 模块级 `Final[float]`，MVPConfig 仅承载几何常量 + `beta_initial` 字段。本 change **不修改** `decompmoe/beta.py` 模块级常量，不引入新 cfg 形参，不引入新 MVPConfig 字段；仅修改 `MVPConfig.beta_initial` 默认值（从 1.0 → 1.035）。

**CLAUDE.md §6 第 8 条遵守**：浮点闭式 `β_0 ≈ 1.035` 用 `pytest.approx(1.035, abs=1e-6)`；50-digit mpmath 重算作为 spec 精度声明的独立证据。

## What Changes

### wayfinder spec delta（2 项）

1. **req-7 L122 σ' precision 微调** —— `σ'(−3.5) ≈ 0.0284` 改 `σ'(−3.5) ≈ 0.02845`（5 位有效数字与 β_0 ≈ 1.035 narrative 风格对齐）。50-digit mpmath `σ'(−3.5) = 0.02845302387973555984`，4 位截断过早，5 位与 β_0 一致。
2. **req-7 L126 Source 字段补齐** —— `**Source:** \`wayfinder/tickets/A4-1.md\`` 改 `**Source:** \`wayfinder/tickets/A4-1.md\`, \`wayfinder/tickets/A4-2.md\`, \`wayfinder/tickets/A6b-1.md\``。req-7 正文 L120 显式引用 A6b-1 (AdamW momentum reset)、L124 显式引用 A4-2 (w_i 剔除)，Source 字段未列——补齐以满足 lint req-34（三项结构性检查：子串存在 + backtick-wrapped + 第一个 top-level item）。**主反链 A4-1 必须首位**。

### ticket 端 supersede annotation（3 项，**追加不删原值**保持 lineage 可读）

3. **ticket `A5-3.md` L62** —— 在 `~52° (估算)` 行后追加 `(historical, ~52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)`。复用 spec L247 已建立的 canonical 格式。
4. **ticket `A1-1.md` L97** —— 在 `θ_Voronoi≈52°` 行后追加 `(historical, θ_Voronoi≈52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)`。与 A5-3 L62 走完全平行路径——cycle-5 finding 锁定 A5-3 + A1-1 两个 ticket 端源头。
5. **ticket `A4-1.md` L58** —— 在 `β_0 ≈ 1.0` 行后追加 `(historical, β_0 ≈ 1.0 estimate; superseded by spec req-7 L122 closed-form β_0 = 1.035060 via change fix-math-consistency-audit-2026-08 Decision 1)`。

### src/ 边界修改（1 文件 surgical Edit）

6. `src/decompmoe/config.py:50-54` —— `beta_initial: float = 1.0` → `beta_initial: float = 1.035`；L50-53 docstring 移除 `tracked as \`★ TODO\` in the plan §ST-02` 追踪，改 `per spec req-7 L122 closed-form β_0 = 1.035060 (verified at 50-digit mpmath: σ(γ_init=−3.5) = 0.029312230751356318865, β_0 = 1.0350601609682665718)`。

### tests/ 边界修改（1 文件）

7. `tests/test_beta.py:37-38` —— `assert MVPConfig().beta_initial == 1.0` 改 `assert MVPConfig().beta_initial == pytest.approx(1.035, abs=1e-6), f"actual={MVPConfig().beta_initial}"`（per CLAUDE.md §6 第 8 条 + `governance/spec.md` req-gov-1 第 2 条：浮点闭式 MUST `pytest.approx(value, abs=...)`；`abs=1e-6` 与 spec L122 β_0 narrative + bisection Voronoi `abs=1e-6` 风格一致；嵌入 `f"actual={...}"` 失败信息 per governance/spec.md req-gov-1 第 4 条）。test docstring L37 同步更新。

### nothing else

- 不动 `decompmoe/beta.py` 模块级常量（`BETA_MIN` / `BETA_MAX` 保持 `Final[float]`）。
- 不动 MVPConfig 其他字段（11 个字段集合不变）。
- 不动 `tests/test_sphere.py`（cycle-5 传染链已断于 src/tests/spec 三角干净）。
- 不动 `tests/test_config.py`（req-11 已用 bare `==` 锁 452M / 100M 参数整数闭式）。
- 不引入新 cfg 形参、不引入新 MVPConfig 字段。
- 不引入 custom CUDA / Triton kernel。
- 不把 `C_t` 写入 KV Cache。
- 不引入 shared expert。
- 不在 logit 中使用 `w_i`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

`wayfinder`（2 处 spec delta，L122 narrative + L126 Source 字段）。无 `decompmoe-skeleton` spec delta（cycle-5/6/7 全部锁定 ticket 端 + `src/config.py` + `tests/test_beta.py`，skeleton spec 端干净）。无 `governance` spec delta（CLAUDE.md §6 第 8 条已通过 `governance/spec.md` req-gov-1 第 2 条覆盖浮点闭式 `pytest.approx(value, abs=...)` 义务）。

## Impact

- **Affected code**（surgical edits per CLAUDE.md §3）：
  - `src/decompmoe/config.py:50-54` —— `MVPConfig.beta_initial` 默认值 1.0 → 1.035 + docstring TODO 移除
  - `wayfinder/tickets/A5-3.md:62` —— θ_Voronoi 行后加 historical supersede annotation（**仅追加，不改值**）
  - `wayfinder/tickets/A1-1.md:97` —— θ_Voronoi≈52° 行后加 historical supersede annotation（**仅追加，不改值**）
  - `wayfinder/tickets/A4-1.md:58` —— β_0 ≈ 1.0 行后加 historical supersede annotation（**仅追加，不改值**）

- **Affected tests**（1 文件）：
  - `tests/test_beta.py:37-38` —— `test_beta_param_init_default` 改 `pytest.approx(1.035, abs=1e-6)` + docstring 更新

- **Affected APIs / dependencies**：
  - `MVPConfig.beta_initial` 默认值 1.0 → 1.035 —— **数值修改，不是 API 变更**。该字段是 dead field（`src/` 全树无读取，verify-6 lock-down），修改仅影响 tests 端，无 runtime 传染。
  - 无新依赖。
  - 无 API 签名变更。

- **Risk**：
  - `MVPConfig.beta_initial` 1.0 → 1.035 数值变更：verify-6 已 lock-down `src/` 无读取，唯一消费方是 `tests/test_beta.py:38`，本 change 同步更新。**风险 LOW**。
  - ticket supersede annotation 格式：复用 spec L247 canonical 格式 + 与 cycle-9 `fix-openspec-doc-bugs` Decision 7 形式一致。**风险 LOW**。
  - spec L122 σ' precision 微调：纯 narrative 精度，不影响 L115 Sigmoid 闭式 / L122 β_0 闭式 / 梯度上界表。**风险 LOW**。
  - spec L126 Source 字段 1 → 3 ticket：新顺序 `A4-1`, `A4-2`, `A6b-1` 保持 A4-1 首位，满足 lint req-34（主反链首位 + backtick-wrapped + code-span atomic split）。**风险 LOW**。
  - Windows Edit tool CRLF contamination：每个 src/ Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`（per `[[windows-edit-crlf-pitfall]]` memory）。**Mitigation 已规划**。
  - `tests/test_beta.py:38` `pytest.approx` vs bare `==`：`governance/spec.md` req-gov-1 第 2 条硬卡"浮点闭式 MUST `pytest.approx(value, abs=...)`"；本 change 严格遵守。**Mitigation 已规划**。

- **Source**：
  - cycle-5 #1 finding：`.audit/spec-math-audit.md` cycle-5 req-11 axis-a finding 1（L131-136）；三轴复核 `.audit/audit-verification/audit-verification.md` verify-1/2/3（L11-L139）
  - cycle-6 #1 finding：`.audit/spec-math-audit.md` cycle-6 req-7 axis-b finding 1（L208-211）；三轴复核 verify-4/5/6（L140-L313）
  - cycle-7 #1 finding：`.audit/spec-math-audit.md` cycle-7 req-7 axis-a finding 1（L892-895）；三轴复核 verify-7/8/9（L314-L584）
  - cycle-7 #2 finding（LOW σ' precision）：verify-8 L402-408 复核；50-digit mpmath 数值锁死 verify-7 axis-α
  - cycle-7 #3 finding（LOW Source 字段补齐）：verify-8 L451-464 复核；lint req-34 在 `.audit/lint-archive.txt` 2026-09 段已记