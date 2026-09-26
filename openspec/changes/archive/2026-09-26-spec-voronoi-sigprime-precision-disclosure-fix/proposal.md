## Why

本会话内 `对 A.1 Spec 数学错误清单进行 4-source 对账` 时 (`Plan` 文件 `C:\Users\LamKo\.minimax\v2\sessions\2026\09\25\16-02-36-158-session_bXZzX2Y2ZWJlYjVjZjg3NzQ4N2ZiYzYzM2MyODU1ZDYyOTQ3\artifacts\plan.md`),用户清单列了 5 项 spec 数学错误,本会话验证后实际严重度为:

| # | 清单严重度 | 实际严重度 | 性质 |
|---|-----------|-----------|------|
| A1.1 governance L17 | MAJOR | **MEDIUM 措辞歧义** | impl vs mpmath 参考帧歧义,impl 内部 residual -1.16e-14 OK,PASS test |
| A1.2 skeleton L102 | MAJOR | **LOW precision-disclosure** | residual < 1e-9 绑定到 bisection output,非 narrative 1.1735 字面 |
| A1.3 skeleton L106 | MAJOR | **LOW precision-disclosure** | 同 A1.2 (N_e=64) |
| A1.4 wayfinder L236-237 | MEDIUM | **LOW display precision** | `67.24°` 与 `1.1735 rad` 都 ≈ true bisection,差 5.94e-5 |
| A1.5 wayfinder L146 | MEDIUM | **MEDIUM 硬 wording bug** | spec 自己 quote "\|0.028453−0.02845\| = 3e-6" 内 self-acknowledge |

**事实判定**:
- **A1.5 唯一真 bug**:`wayfinder L146` 写 "truncated at 5 significant figures" 但 narrative `0.02845` 实际是 4 sig figs(5-sig truncation 0.0284530238... = `0.028453`,不是 `0.02845`)。spec 内 self-quoted diff = 3e-6 表明 wording 矛盾客观存在。L156 "5-sig-fig precision disclosure" 同源同 bug。
- **A1.1 措辞歧义**:规范 `(residual < 1e-9)` 未明示参考帧。实测 impl-internal (`_betainc_regularized`) = 1.164e-14 ✓;mpmath `betainc(regularized=True)` 真值参考 = 4.15e-7 ✗。两参考都是合理,spec 必须 explicit 选一个,避免 silent reference-frame shifting。
- **A1.2/A1.3 是 prose rounding**:`≈ 1.1735 rad`/`≈ 1.0205 rad` 是 narrative ~4-decimal prose;impl 实际输出 `1.1735482746999482 rad`/`1.0205068335735599 rad`。reader 易把 ≈ 字面代入算 residual。
- **A1.4 dual-display**:`67.24°` 与 `1.1735 rad` 各自 `≈`,prose 双重显示,差 5.94e-5 rad 是 dual-prose-precision,需要 footnote 解释。

**传染链分析**:
- A1.5 wording bug 是 `2026-09-25-fix-wayfinder-spec-narrative-precision-l566-l580` archive 引入 (该 archive 加 L146 "5 sig figs" 措辞,但 narrative 字面 0.02845 是 cycle-23 `01-fix-ticket-stale-numerical-4file-batch` Decision 4 改的 4-sig form) —— **单点 wording 矛盾**,无传染。
- A1.1 措辞歧义是历史习惯(impl-internal residual claim 没 explicit frame disclosure),不是新引入。
- A1.2/A1.3/A1.4 是叙事精度披露,非数值错误。

## What Changes

### governance spec delta（1 项）

1. **`req-gov-1` 加 §4 frame disclosure** —— 在原 §4(`f"actual={...}"` 嵌入义务)前插入新 §4 `Residual frame disambiguation`:明确 `< 1e-9` 类精度 claims 必须 explicit 选参考帧(impl-internal vs mpmath true),避免 silent reference-frame shifting。原 §4 顺位 §5。**req-gov-1 主反链仍为 `CLAUDE.md` (不变,lint 不受影响)**。

### decompmoe-skeleton spec delta（1 项）

2. **`req-6` 加新 Scenario `Bisection output + narrative precision disclosure`** —— 在 `Scenario: N_e dependence of voronoi_angle` (L104-L106) 与 `Scenario: no hard-coded table values` (L108-L110) 之间,加新 Scenario 让 reader 知道:
   - `≈ 1.1735 rad` / `≈ 1.0205 rad` 是 prose ~4-decimal
   - impl bisection 输出是 `1.1735482746999482 rad`(N_e=16)/`1.0205068335735599 rad`(N_e=64),16-digit
   - impl-internal residual `< 1e-14`(per `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`)
   - mpmath true closed-form residual `4.15e-7` (N_e=16) / `1.43e-9` (N_e=64); N_e=64 impl 输出 just above `< 1e-9` reference floor at `1.43e-9` (NOT below, despite the small magnitude), N_e=16 impl 输出 residual 较大 (~4e-7) 但仍在 `< 1e-6` spec tolerance 内 (per req-gov-1 §3)

### wayfinder spec delta（2 项）

3. **`req-7` 改 L146 wording(A1.5 主修)**:`Scenario: σ'(−3.5) narrative precision ... within 5 significant figures` 改 ... within 4 significant figures(narrative form);THEN 子句 "matches the 50-digit mpmath value 0.02845302387973555984 truncated at 5 significant figures (diff |0.028453−0.02845| = 3e-6, relative 0.011%, well below 1e-6 tolerance)" → "matches the 50-digit mpmath value `0.02845302387973555984` rounded to 4 significant figures (round-half-up 或 truncate-then-format 同产 `0.02845`);the 5-sig-fig truncation 会产 `0.028453`,NOT displayed;discrepancy intentional — narrative precision is 4 sig figs to align with `β_0 ≈ 1.035` (4 sig fig) per Decision 4 of change `01-fix-ticket-stale-numerical-4file-batch` proposal"。

4. **`req-7` 改 L156 wording (5-sig-fig → 4-sig-fig)**:Scenario L153-157 "AND a paired assertion `σ'(−3.5) == pytest.approx(0.02845, abs=1e-5)` that nails the **L122 narrative 5-sig-fig precision disclosure**" → "the **L122 narrative 4-sig-fig precision disclosure**"。**req-7 主反链仍为 `wayfinder/tickets/A4-1.md`(不变)**。

5. **`req-11` L236-L237 加 blockquote footnote(A1.4 dual-display)**:在 L237 后 L239 前加 `> **Display precision note** ...` 同时覆盖 N_e=16 行 (`67.24°` ≈ 4-decimal-degree) 和 N_e=64 行 (`58.47°` ≈ 4-decimal-degree)。footnote 不改原 wording。

### nothing else

- **不动 `src/decompmoe/sphere.py`**(impl 内部 residual -1.16e-14 PASS,行为零变更)
- **不动 `tests/test_sphere.py`**(PASS,不重写)
- **不动 `tests/test_beta.py`**(PASS;`pytest.approx(0.02845, abs=1e-5)` 已合规,narrative 字面 0.02845 不变)
- **不动 `wayfinder/tickets/`**(per CLAUDE.md §8 D6 决策 (a): advisory ticket 不污染 spec,本 change 不引入 supersede annotation)
- **不动 `_betainc_regularized` 实现**(Gauss-Legendre 8-point 60-subinterval 是 impl design choice,不是 bug)
- **不动 `scripts/lint_*.py`**

## Capabilities

### New Capabilities

(无)

### Modified Capabilities

(无。Spec delta 经 ADDED/MODIFIED Requirements 形式 append 至既有 capability。)

### Added / Modified Requirements to Existing Capabilities

- `governance`:  **MODIFIED** Requirement "Test Guard Precision for Closed-Form Numerical Claims"(`governance/spec.md` L9-L48) —— req-gov-1 加新 §4 frame disclosure,原 §4 顺位 §5(req-gov-1 主反链不变:`CLAUDE.md`)
- `decompmoe-skeleton`: **MODIFIED** Requirement "Voronoi Self-Consistency Threshold"(`decompmoe-skeleton/spec.md` L94-L110) —— req-6 加新 Scenario "Bisection output + narrative precision disclosure"(req-6 主反链不变:`wayfinder/tickets/A5-3.md`,`wayfinder/tickets/A8-1.md`,per plan 暂时不动 Source)
- `wayfinder`: **MODIFIED** Requirement "Isotropic Squared-Chord Distance And Bounded Beta"(`wayfinder/spec.md` L119-L160) —— req-7 L146 wording 重写(5 sig figs → 4 sig figs)+ L156 wording 同步对齐(5-sig-fig → 4-sig-fig)(主反链仍 `wayfinder/tickets/A4-1.md`)
- `wayfinder`: **MODIFIED** Requirement "4070 MVP Hyperparameter Set"(`wayfinder/spec.md` L229-L247) —— req-11 L236-L237 后加 blockquote footnote(主反链仍 `wayfinder/tickets/A5-3.md`,`wayfinder/tickets/A8-1.md`)

## Impact

- **Affected code**: 无 (`src/` 零变更)
- **Affected tests**: 无 (`tests/` 零变更,所有现存测试 PASS 不变)
- **Affected APIs / dependencies**: 无 API 签名变更;无依赖变更
- **Affected systems**: 无 (spec narrative-only wording fix,无 runtime 行为变更)
- **Risk**:
  - **wording 改后 lint regression**:`scripts/lint_no_source_field_drift.py` 按 capability-aware substring 校验 — 本 change 不改任何 `**Source:**` 字段也不新增 anchor,lint 风险 LOW。Mitigation: `/opsx:apply` 后跑 lint gate `exit=0`。
  - **wayfinder L146 wording 与 cycle-23 Decision 4 决策一致性**:cycle-23 `01-fix-ticket-stale-numerical-4file-batch` Decision 4 改 narrative `0.0284 → 0.02845`(4 sig fig)。本 change 在 L146 wording 里 explicit 反链 Decision 4,确保 cycle-23 决策产物不被回退。
  - **CRLF contamination**:governance / skeleton / wayfinder 三个 spec.md 均含 non-ASCII(`<`/`≤`/`≈` 等)。Mitigation:每个 spec edit 后跑 byte-level CRLF check(per memory lesson `Edit tool on Windows can introduce CRLF in non-ASCII files`)。
  - **anchor 100% 覆盖**:本 change 不引入新 anchor(only editing existing Scenario wording + adding new Scenario within existing Requirement body)。Mitigation:apply 阶段二次 grep 验证。

## Source

- 4-source 对账:`Plan` 文件 `C:\Users\LamKo\.minimax\v2\sessions\2026\09\25\16-02-36-158-session_bXZzX2Y2ZWJlYjVjZjg3NzQ4N2ZiYzYzM2MyODU1ZDYyOTQ3\artifacts\plan.md` 中 `"Current State and Fact Base"` 段
- mpmath 80-digit empirical:`Plan` 文件中 `"Verification Record"` 段
- git history:`adb4df7 chore(archive): sync 2026-09-25-fix-wayfinder-spec-narrative-precision-l566-l580 delta to main spec` (引入 L146 "5 sig figs" wording bug);`adf41ef` cycle-23 batch(0.0284 → 0.02845 narrative);`34b37be` migrate-l678-source(req-33 → req-gov-1)
- test 验证:`tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` PASS(impl-internal -1.164e-14)
- 用户 A.1 清单 (session message)
