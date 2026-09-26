## Why

2026-09-18 audit-verification loop 完成 cycle-5/6/7 三条 MEDIUM finding 三轴 (α + β + γ) 复核。三条 finding 形成**同源 "ticket 端 stale 数值源头" pattern**（含 cycle-5 双 ticket 端 A5-3 L62 + A1-1 L97, per `.audit/audit-verification/audit-verification.md` L132 字面锁定 `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°`），需在同一 OpenSpec change 中批量修复 —— **5-file batch fix (A5-3 L62 + A1-1 L97 + A4-1 L58 + MVPConfig L54 + test_beta.py L38)**：

> **Base convention**: `15.24° (29% relative)` 用 ticket stale (52°) 作 base —— 15.24/52 = 29.3% (per `.audit/audit-verification/audit-verification.md` L128 `15.24° (29% 相对)`); `15.24° (22.7% relative)` 用 spec truth (67.24°) 作 base —— 15.24/67.24 = 22.7% (per `.audit/spec-math-audit/spec-math-audit.md` L134). 两个数字都对, 仅 base 不同

| finding | 源头端 | stale 值 | spec 真相 | drift |
|---|---|---|---|---|
| cycle-5 #1 | ticket `A5-3.md` L62 | `θ_Voronoi ~52°` (估算) | 67.24° (1.1735 rad, bisection < 1e-9) | 15.24° absolute (29% relative-to-ticket-base / 22.7% relative-to-truth-base) |
| cycle-5 #1 (sub) | ticket `A1-1.md` L97 | `θ_Voronoi≈52°` | 67.24° | 15.24° (同源, base 同上) |
| cycle-6 #1 | `MVPConfig.beta_initial = 1.0` (`config.py` L54) + `tests/test_beta.py` L38 钉死 stale | 1.0 | 1.035060 (闭式 `0.1 + 31.9·σ(-3.5)`, 50-digit mpmath 锁死) | 3.39% |
| cycle-7 #1 | ticket `A4-1.md` L58 | `β_0 ≈ 1.0` | 1.035060 | 3.39% |

附加两条 LOW spec delta（cycle-7 finding 2 + 3）一并处理：
- **finding 2 (LOW)**：spec req-7 L122 `σ'(−3.5) ≈ 0.0284` 精度欠一位（实际 50-digit = `0.02845302387973555984`），建议改 `≈ 0.02845` 与 β_0 精度对齐。
- **finding 3 (LOW)**：spec req-7 L126 Source 字段只列 `A4-1`（单 ticket 反链），但 req-7 正文 L120/L124 显式引用 `A4-2` (w_i 剔除) + `A6b-1` (AdamW momentum reset)，应补齐反链。

**传染链（verify-6 + verify-9 锁定）**：cycle-6 与 cycle-7 在数值上精确相同 (3.39% drift)，但**传染链结构不同**：
- cycle-7 锁定 ticket 端源头 (`A4-1.md` L58 stale)
- cycle-6 锁定 src/tests 端（`MVPConfig.beta_initial = 1.0` 直接抄 ticket L58 → `test_beta.py:38` 钉死 stale 1.0）
- 两者合起来 = 同一条 drift 的完整因果链

**D1 决策保留（沿用 fix-math-consistency-and-contract-closure-2026-09 design.md D1）**：算法常量 `β_min = 0.1` / `β_max = 32` 位于 `decompmoe/beta.py` 模块级 `Final[float]`，MVPConfig 仅承载几何常量 + `β_initial` 字段。本 change **不修改** `decompmoe/beta.py` 模块级常量，不引入新 cfg 形参，不引入新 MVPConfig 字段；仅修改 `MVPConfig.beta_initial` 默认值（从 1.0 → 1.035）。

**CLAUDE.md §6 第 8 条遵守**：浮点闭式 `β_0 = 1.035060` 用 `pytest.approx(1.035, abs=1e-6)`；50-digit mpmath 重算作为 spec 精度声明的独立证据。

## What Changes

### wayfinder spec delta（2 项）

1. **req-7 L122 σ' precision 微调（cycle-7 finding 2，LOW）** —— `σ'(−3.5) ≈ 0.0284` 改 `σ'(−3.5) ≈ 0.02845`（5 位有效数字与 `β_0 ≈ 1.035` 精度风格统一）。50-digit mpmath `σ'(−3.5) = 0.02845302387973555984`，4 位有效数字 (0.0284) 截断过早，5 位 (0.02845) 与 `β_0` 风格一致。
2. **req-7 L126 Source 字段补齐（cycle-7 finding 3，LOW）** —— `**Source:** \`wayfinder/tickets/A4-1.md\`` 改为 `**Source:** \`wayfinder/tickets/A4-1.md\`, \`wayfinder/tickets/A4-2.md\`, \`wayfinder/tickets/A6b-1.md\``。req-7 正文 L124 显式引用 A4-2 (w_i 剔除), L120 显式引用 A6b-1 (AdamW momentum reset)，但 Source 字段未列——lint req-34 `主反链必须是第一个 top-level item (paren-depth-aware, code-span atomic split)` 要求主反链 A4-1 保持首位。

### ticket 端 supersede annotation（3 项）

3. **ticket A5-3 L62（cycle-5 #1）** —— 加 `(historical, ~52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)` 注释到 θ_Voronoi ~52° 行后（**不删** 原 ~52° 字样，仅加 historical supersede 注释保持 ticket lineage 可读）。
4. **ticket A4-1 L58（cycle-7 #1）** —— 加 `(historical, β_0 ≈ 1.0 estimate; superseded by spec req-7 L122 closed-form β_0 = 1.035060 via change fix-math-consistency-audit-2026-08 Decision 1)` 注释到 β_0 ≈ 1.0 行后（**不删** 原 1.0 字样）。
5. **ticket A1-1 L97（cycle-5 #1 同源）** —— 加 `(historical, θ_Voronoi≈52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)` 注释到 θ_Voronoi≈52° 行后（**不删** 原 ≈52° 字样）。与 §B #3 (A5-3 L62) 走完全平行的路径 —— cycle-5 finding 锁定 A5-3 + A1-1 两个 ticket 端源头 (audit-verification.md L132 字面)。

### src/ 边界修改（1 文件 surgical Edit）

5. `src/decompmoe/config.py:50-54` —— `beta_initial: float = 1.0` → `beta_initial: float = 1.035`；L50-53 docstring 移除 `tracked as \`★ TODO\` in the plan §ST-02` 追踪，改 `per spec req-7 L122 closed-form β_0 = 1.035060 (verified at 50-digit mpmath: σ(γ_init=−3.5) = 0.029312230751356318865, β_0 = 1.0350601609682665718)`。

### tests/ 边界修改（1 文件）

6. `tests/test_beta.py:38` —— `assert MVPConfig().beta_initial == 1.0` 改 `assert MVPConfig().beta_initial == pytest.approx(1.035, abs=1e-6)`（per CLAUDE.md §6 第 8 条 + governance/spec.md req-gov-1 第 2 条：浮点闭式必须 `pytest.approx(value, abs=...)`；`abs=1e-6` 与 β_0 闭式 1.035060 8 位有效数字对齐）。test docstring L37 同步更新 `MVPConfig().beta_initial ≈ 1.035 (proxy for γ₀ ≈ −3.5 per spec req-7 L122)`。

### nothing else

不动 `decompmoe/beta.py` 模块级常量（`BETA_MIN = 0.1` / `BETA_MAX = 32` 保持 `Final[float]`）；不动 MVPConfig 其他字段（`d_model` / `N_e` / `k` / `d_ffn` / `L` / `d_ffn_dense` / `d_c` / `H_kv` / `d_k` / `vocab_size` 全部保留）；不动 `tests/test_sphere.py`（cycle-5 finding 已通过 `test_voronoi_canonical_mvp_value` + `test_voronoi_residual_below_1e_minus_9` + `test_versine_voronoi_closed_form` 守 canonical API，传染链已断于 src/tests/spec 三角干净）；不动 `tests/test_config.py`（req-11 已用 bare `==` 锁 452M/100M 参数整数闭式，不动）；不动 wayfinder tickets 其他文件（**仅 A5-3 + A4-1 + A1-1 三处加 supersede annotation**——5-file batch 而非 4-file batch；A1-1 L97 是 cycle-5 #1 同源 ticket 端源头）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无。Spec delta 经 ADDED Requirements header 落 `specs/wayfinder/spec.md`，append 至既有 capability。）

### Added / Modified Requirements to Existing Capabilities

- `wayfinder` (2 处 spec delta)：
  - **MODIFIED** Requirement "Isotropic Squared-Chord Distance And Bounded Beta"（wayfinder L111-134）—— L122 narrative `σ'(−3.5) ≈ 0.0284` 微调 `≈ 0.02845`；L126 Source 字段由单 ticket `A4-1` 补齐为 `A4-1` + `A4-2` + `A6b-1`（主反链 A4-1 首位保持）

无 `decompmoe-skeleton` spec delta（cycle-5/6/7 全部锁定 ticket 端 + src/config.py + tests/test_beta.py，skeleton spec 端干净）。

无 `governance` spec delta（无需新增 governance-origin 条款；CLAUDE.md §6 第 8 条已通过 governance/spec.md req-gov-1 第 2 条覆盖浮点闭式 `pytest.approx(value, abs=...)` 义务，本次 `pytest.approx(1.035, abs=1e-6)` 直接合规）。

## Impact

- **Affected code**（surgical edits per CLAUDE.md §3）：
  - `src/decompmoe/config.py:50-54` —— `MVPConfig.beta_initial` 默认值 1.0 → 1.035 + docstring TODO 移除
  - `wayfinder/tickets/A5-3.md:62` —— θ_Voronoi 行后加 historical supersede annotation（**仅追加注释，不改值**）
  - `wayfinder/tickets/A4-1.md:58` —— β_0 ≈ 1.0 行后加 historical supersede annotation（**仅追加注释，不改值**）
  - `wayfinder/tickets/A1-1.md:97` —— θ_Voronoi≈52° 行后加 historical supersede annotation（**仅追加，不改值**, 与 A5-3 L62 平行路径；cycle-5 #1 同源 ticket 端源头 per audit-verification.md L132）

- **Affected tests**（1 文件 expected）：
  - `tests/test_beta.py:37-38` —— `test_beta_param_init_default` 改 `pytest.approx(1.035, abs=1e-6)` + docstring 更新

- **Affected APIs / dependencies**：
  - `MVPConfig.beta_initial` 默认值从 1.0 → 1.035 —— **数值修改，不是 API 变更**。由于 `MVPConfig.beta_initial` 是 dead field（src/ 全树无读取，仅 tests/test_beta.py:38 assert），修改仅影响 tests 端，无 runtime 传染
  - 无新依赖
  - 无 API 签名变更

- **Affected systems**：无（推理引擎实现代码已 out-of-scope per CLAUDE.md §7）

- **Risk**：
  - **`MVPConfig.beta_initial` 1.0 → 1.035 数值变更**：cycle-6 verify-6 确认 src/ 全树无文件读取该字段（`grep -r "beta_initial" src/` 0 命中），故无 runtime 传染；唯一消费方是 `tests/test_beta.py:38` 自身，本 change 同步更新。**风险 LOW**。
  - **ticket supersede annotation 格式**：复用 spec L247 已建立的 canonical 格式 `**Source:** \`wayfinder/tickets/<ID>.md\` (historical, <原值>; superseded by <change> <doc> Decision N)`，与 cycle-9 fix (`fix-openspec-doc-bugs` Decision 7) 形式一致。**风险 LOW**。
  - **spec L122 σ' precision 0.0284 → 0.02845**：纯 narrative 精度微调，不影响 spec L115 Sigmoid 闭式 / L122 β_0 ≈ 1.035 闭式 / 梯度上界表（spec L115 完整闭式不变）。**风险 LOW**。
  - **spec L126 Source 字段 1 → 3 ticket**：需过 lint req-34（主反链必须首位 backtick-wrapped + 第一个 top-level item + paren-depth-aware），新字段顺序 `A4-1`, `A4-2`, `A6b-1` 保持 A4-1 首位。**风险 LOW**。
  - **Windows Edit tool CRLF contamination**：每个 src/ Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`（per [[windows-edit-crlf-pitfall]] memory）。**Mitigation 已规划**。
  - **tests/test_beta.py:38 bare `==` vs `pytest.approx`**：governance/spec.md req-gov-1 第 2 条硬卡 "浮点闭式 MUST `pytest.approx(value, abs=...)`，NOT bare `==`"；本 change 严格遵守。**Mitigation 已规划**。

- **Source**：
  - cycle-5 #1 finding：`.audit/spec-math-audit.md` cycle-5 req-11 axis-a finding 1 (L131-136)；三轴复核 `.audit/audit-verification/audit-verification.md` verify-1/2/3 (L11-L139)
  - cycle-6 #1 finding：`.audit/spec-math-audit.md` cycle-6 req-7 axis-b finding 1 (L208-211)；三轴复核 verify-4/5/6 (L140-L313)
  - cycle-7 #1 finding：`.audit/spec-math-audit.md` cycle-7 req-7 axis-a finding 1 (L892-895)；三轴复核 verify-7/8/9 (L314-L584)
  - cycle-7 #2 finding (LOW σ' precision)：cycle-7 finding 2 在 audit-verification.md verify-8 L402-408 复核；50-digit mpmath 数值锁死 verify-7 axis-α
  - cycle-7 #3 finding (LOW Source 字段补齐)：cycle-7 finding 3 在 audit-verification.md verify-8 L451-464 复核；lint req-34 在 `.audit/lint-archive.txt` 2026-09 段已记