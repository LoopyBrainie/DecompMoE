# Proposal

## Why

`openspec/specs/wayfinder/spec.md` 在 `req-24`（Beta Parameterization Space vs Operational Domain）内保留两处与同 spec 内其他 Requirement 不一致的 narrative 精度，造成"同 spec 内同常数 3 处精度不同"的串扰，违反 CLAUDE.md §6 第 8 条"sentinel closed-form constant 必须在 spec 内一致披露"原则：

1. **L566** `σ'(−3.5) ≈ 0.0284`（4 位有效数字）vs 同 spec 内 **L130 / L146 / L155-156** `σ'(−3.5) ≈ 0.02845`（5 位有效数字，与 50-digit mpmath `0.02845302387973555984` 5 位截断一致）。L566 数字 0.0284 是早期 4 位截断风格残留，L130 已被 `adf41ef` (cycle-5/6/7 batch fix, 2026-09-19) 升级到 5 位，但 L566 **未在 adf41ef scope 内**——造成 req-24 数值锚点滞后于 req-7。

2. **L580** `γ' = ln(15/16) ≈ −0.0645`（3 位有效数字）vs 同 spec 内 **L614** `≈ −0.064538...`（6 位）和 **L620** `≈ −0.0645385...`（7 位）。L580 是 req-24 Scenario 段，与 req-25 body + scenario 字面精度不对齐。`−0.0645` 仅 3 位有效数字，与 `ln(15/16)` 的实际闭式 `−0.0645385211...` 的偏差 `0.0000385` 在 6% 相对误差级，远超 narrative 风格可接受容差。

两个 finding 经 2026-09-25 mpmath 实测 + archive 复核 + 代码测试守护**确认数值方向正确**（spec 真相不是 stale），仅需 narrative 精度统一。**A1.3 / A1.4 / A1.6 三项 finding 经同期复核判定 finding 本身错（spec 数值正确，非 stale）——不纳入本 change scope，evidence 入 audit trail。**

## What Changes

- **`openspec/specs/wayfinder/spec.md` L566** (req-24 body)：narrative `σ'(−3.5) ≈ 0.0284` 微调 `σ'(−3.5) ≈ 0.02845`（5 位有效数字，与同 spec 内 L130/L146/L155-156 精度对齐；同 50-digit mpmath `σ'(−3.5) = 0.02845302387973555984` 5 位截断）。
- **`openspec/specs/wayfinder/spec.md` L580** (req-24 Scenario "Phase 3 → 4 transition is continuous")：narrative `γ' = ln(15/16) ≈ −0.0645` 升级 `γ' = ln(15/16) ≈ −0.0645385...`（7 位有效数字，与同 spec 内 L614/L620 精度对齐；同 `ln(15/16) = −0.0645385211...` 7 位截断）。
- 无 code 改动。
- 无 test 改动（既有 `tests/test_beta.py::test_gamma_reset_for_phase4_boundary_continuity` 已用 `pytest.approx(ln(15/16), abs=1e-4)` 对账闭式精度，narrative 微调不破坏 4 位以下测试守护；既有 `tests/test_beta.py::test_sigma_prime_gamma_init_health_check` 已用 `pytest.approx(0.02845302387973555984, abs=1e-30)` 钉 50-digit + `pytest.approx(0.02845, abs=1e-5)` 钉 narrative 5 位）。
- 无 MVPConfig 改动。
- 无 ticket 改动。
- 无 baseline 改动。
- 无 API 签名变更。

## Capabilities

### New Capabilities

（无。spec narrative 精度统一走 MODIFIED Capabilities 路径。）

### Modified Capabilities

- `wayfinder` — Requirement `Beta Parameterization Space vs Operational Domain`（req-24, L562-570）的 2 处 narrative 精度微调：
  - L566 body `σ'(−3.5) ≈ 0.0284` → `≈ 0.02845`
  - L580 Scenario `γ' = ln(15/16) ≈ −0.0645` → `≈ −0.0645385...`

无其他 capability 改动（req-7 L130/L146/L155-156 + req-25 L614/L620 已合规）。

## Impact

- **Affected code**：无。
- **Affected tests**：无（既有测试覆盖 4 位/5 位/6 位/7 位/50-digit 五档精度，本 change 升级 L566/L580 narrative 与既有 5/7 位精度对齐，无需新增 test）。
- **Affected APIs / dependencies**：无。
- **Affected systems**：无（推理引擎实现代码已 out-of-scope per CLAUDE.md §7）。
- **Risk**：
  - **spec narrative 精度升级不引入新数值风险**：升级方向是 narrative 字面 `0.0284 → 0.02845` / `−0.0645 → −0.0645385...`，与 mpmath 闭式更接近，**不构成新 drift**。
  - **同 spec 内跨 Requirement 数值对齐**：升级 L566 + L580 后，spec 内 `σ'(−3.5)` 全部 5 位一致（L130/L146/L155-156/L566），`γ' = ln(15/16)` 全部 7 位一致（L580/L614/L620），reader 不会再困惑"为什么 req-24 比其他 Requirement 字面精度更粗"。
  - **无 lint 风险**：L566 在 req-24 body 内（非 Source 字段），L580 在 Scenario 内（非 Source 字段），均不触发 `scripts/lint_no_source_field_drift.py` 任何结构性检查。
  - **Windows Edit tool CRLF contamination**：每个 Edit 后跑 `git diff --stat` 验证 LF 保留（per [[windows-edit-crlf-pitfall]] memory）；必要时 `sed -i 's/\r$//'`。

- **Source**：
  - adf41ef (cycle-5/6/7 batch fix, 2026-09-19) 已升级 req-7 L122 + req-7 Source field 但**未触及 req-24**
  - decompmoe-skeleton/spec.md L458 已有 7 位 `ln(15/16) ≈ −0.0645385...` 精度披露 + `pytest.approx(abs=1e-4)` 闭式测试
  - 50-digit mpmath 锚点：`σ'(−3.5) = 0.02845302387973555984`（cycle-7 verify-7 axis-α 锁死），`ln(15/16) = −0.0645385211...`（手算 + mpmath 30-digit 复核）
  - A1.3 / A1.4 / A1.6 finding 复核 evidence（不入 scope，但 record 在 audit trail）：
    - A1.3：mpmath bisection 实测 `versine_Voronoi(64,16) = 0.4770659854...` → L235 `0.4771` **正确**；archive `2026-09-05-fix-p1-audit-batch` MAJ-M2 PASS
    - A1.4：SwiGLU 3-matrix 数学推导（W_gate d_model×d_ffn + W_up d_model×d_ffn + W_down d_ffn×d_model）合计 `3·d_model·d_ffn` 正确，无 ×2 缺失；`tests/test_config.py::test_param_totals_locked` 已守 452_329_984 整数闭式
    - A1.6：decompmoe-skeleton L446 字面已含完整 `σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` chain；src/decompmoe/beta.py:50 docstring 同步；archive `2026-09-05-fix-skeleton-0-5-31-2-formula` + `2026-09-16-fix-followup-review-findings` 已固化