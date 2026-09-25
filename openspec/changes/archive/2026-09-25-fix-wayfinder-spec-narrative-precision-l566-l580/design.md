# Design

## Context

Live `openspec/specs/wayfinder/spec.md` 在 req-24 (Beta Parameterization Space vs Operational Domain) 保留两处与同 spec 内其他 Requirement 不一致的 narrative 精度：
- L566 body `σ'(−3.5) ≈ 0.0284`（4 位有效数字）
- L580 Scenario `γ' = ln(15/16) ≈ −0.0645`（3 位有效数字）

同 spec 内已有锚点：
- L130/L146/L155-156 `σ'(−3.5) ≈ 0.02845`（5 位，由 `adf41ef` 2026-09-19 cycle-5/6/7 batch fix 落地）
- L614 `≈ −0.064538...`（6 位）
- L620 `≈ −0.0645385...`（7 位）

本 change 把 req-24 内两处 narrative 升级到与同 spec 内既有锚点一致的精度（5 位 / 7 位），消除"同 spec 内同常数 3 处精度不同"的串扰根因（per CLAUDE.md §6 第 8 条"sentinel closed-form constant 必须在 spec 内一致披露"原则 + req-gov-1 第 3 条 "spec narrative 必须与闭式精度一致"）。

本 change **非** 算法/语义变更（`σ'(−3.5) = 0.02845302...`、`ln(15/16) = −0.06453852...` 是数学事实，narrative 改不改数学不变）；亦 **非** API/签名/字段改动；仅 spec narrative 字符级精度统一。

## Goals / Non-Goals

**Goals:**
- 升级 L566 narrative 精度 4 位 → 5 位，与同 spec L130/L146/L155-156 对齐
- 升级 L580 Scenario narrative 精度 3 位 → 7 位，与同 spec L614/L620 对齐
- 保持 req-24 其余 body / Scenario / Source / Anchor 完全不变
- 保持 spec 内 `β_0 ≈ 1.035` narrative 风格（4 位有效数字）不变
- 保持 spec 内 `θ_{1/e}(β=16) = arccos(15/16) ≈ 20.36°` narrative 精度不变

**Non-Goals:**
- 不动 `decompmoe/beta.py` 模块级常量（`SIGMA_PRIME_AT_ZERO = 0.25`、`ANTIPODAL_INNER_EXTREME = 2.0`、`BETA_MIN = 0.1`、`BETA_MAX = 32` 等保持 Final 不变）
- 不动 `MVPConfig` 字段集合（11 个字段保持不变）
- 不动 `tests/test_beta.py`（既有 `test_sigma_prime_gamma_init_health_check` + `test_gamma_reset_for_phase4_boundary_continuity` 已守 50-digit + 5/7 位精度）
- 不动 ticket `A4-1.md` / `A6b-1.md` / 其他 ticket（narrative 精度统一是 spec 端单边工作）
- 不动 req-7（L130/L146/L155-156 已在 adf41ef 落地）
- 不动 req-25 body / L614/L620
- 不动 wayfinder spec 其他 Requirement
- 不动 decompmoe-skeleton spec（spec 端干净）
- 不动 governance spec（无需新增 governance-origin 条款）
- 不引入新 cfg 形参、不引入新 MVPConfig 字段
- 不引入 custom CUDA/Triton kernel
- 不重写 ticket 内容

## Decisions

### Decision 1: 升级精度方向 — L566 → 5 位 (0.02845)，L580 → 7 位 (−0.0645385...)

**Choice**:
- L566: `σ'(−3.5) ≈ 0.0284` → `σ'(−3.5) ≈ 0.02845`
- L580: `γ' = ln(15/16) ≈ −0.0645` → `γ' = ln(15/16) ≈ −0.0645385...`

**Rationale**:
- L566 → 5 位：与同 spec L130/L146/L155-156 字面 `0.02845` 完全一致；与 50-digit mpmath `0.02845302387973555984` 5 位截断一致；reader 在 req-7 与 req-24 之间切换不会困惑"为什么同一常数两处精度不同"
- L580 → 7 位：与同 spec L614 字面 `−0.064538...` / L620 字面 `−0.0645385...` 完全对齐到 7 位；与 `ln(15/16) = −0.0645385211...` 7 位截断一致；与 decompmoe-skeleton L458 字面 `−0.0645385...` 完全一致
- 升级方向是"加精度"（粗 → 细），不构成"删除精度"，**不破坏**既有 reader familiarity
- 升级后 narrative 与既有 50-digit mpmath 锚点（`σ'(−3.5) = 0.02845302387973555984` / `ln(15/16) = −0.0645385211...`）在 narrative 字面精度内一致

**Alternatives considered**:
- (a) L566 升 6 位 (`0.028453`) / L580 升 6 位 (`−0.064538`) —— 拒绝：5 位 / 7 位是与同 spec 内其他位置 narrative 风格一致的最小变更；6 位会让 narrative 与 req-7/L130 narrative `0.02845` 不齐
- (b) 完全删除 narrative 精度披露 —— 拒绝：spec reader 需要在 narrative 与闭式之间的"快速心算锚点"，删除会破坏 spec 的不变量信息（如 cycle-7 finding 1 "healthy gradient" health-check）
- (c) 改 narrative 为 50-digit 闭式锚点（如 L155-156 风格）—— 拒绝：req-24 narrative 当前是 4 位 / 3 位粗 narrative，不是 50-digit 闭式测试守护；改成 50-digit 闭式会改变 spec 风格（narrative → formal-anchor）

### Decision 2: anchor 编号策略 — 保留 req-24 现有 anchor `<a id="req-24"></a>` 不变

**Choice**: L562 anchor `<a id="req-24"></a>` 完全保留；L582 anchor `<a id="req-25"></a>` 完全保留；其他 anchor 不动

**Rationale**:
- anchor 是 cross-reference + 反链 + lint 检查（CLAUDE.md §6 第 8 条 "spec anchor 100% 覆盖" + lint req-33）的关键基础设施
- 改 anchor 会破坏所有引用 `req-24` 的反链（proposal/design/tasks/decompmoe-skeleton/A4-1.md/A6b-1.md 等）
- 本 change **不**新增 requirement、**不**重命名 requirement、**不**合并 requirement，仅 narrative 精度升级，anchor 必须保持不变

**Alternatives considered**:
- (a) 重编号 req-24 → req-24' —— 拒绝：破坏现有反链
- (b) 新增 anchor `<a id="req-24-l566-updated"></a>` —— 拒绝：anchor 必须唯一对应一个 Requirement body；同一 Requirement 不能有两个 anchor
- (c) 完全移除 anchor —— 拒绝：违反 CLAUDE.md §6 第 8 条 "spec anchor 100% 覆盖" 硬卡

### Decision 3: Source 字段保留 — 不补 A4-2 / A6b-1 (区别于 cycle-7 finding 3)

**Choice**: L572 Source 字段 `**Source:** \`wayfinder/tickets/A4-1.md\`, \`wayfinder/tickets/A6b-1.md\`` 保持不变（**不**补 A4-2）

**Rationale**:
- req-24 (Beta Parameterization Space vs Operational Domain) 主体引用 ticket A4-1（β 参数化 origin）+ A6b-1（AdamW momentum reset on Phase 4 entry）；**不**引用 A4-2（w_i 剔除是 req-7 / req-24-L124 后续 Scenario 主题，但 req-24 body 不显式引用）
- adf41ef cycle-7 finding 3 仅针对 **req-7** Source 字段补 A4-2 / A6b-1（req-7 L120/L124 显式引用这两个 ticket）；req-24 Source 字段保持 2 ticket 是**正确的 spec 范围**，**不**需要补 A4-2
- 本 change 仅精度升级，**不**改 Source 字段语义（Source 反链保持当前 2 ticket 即可）

**Alternatives considered**:
- (a) 复制 adf41ef pattern 给 req-24 Source 补 A4-2 —— 拒绝：req-24 body 不显式引用 A4-2；补 A4-2 会构成"应链未引用"（违反 CLAUDE.md §3 Source 反链硬卡："主反链必须在第一个 top-level item, paren-depth-aware, code-span atomic split"）
- (b) 移除 A6b-1 —— 拒绝：req-24 body L570 显式引用 A6b-1（AdamW momentum reset on Phase 4 entry），移除会断反链

## Risks / Trade-offs

- **[Risk]**: L566 narrative 升级 `0.0284 → 0.02845` 引入新精度披露，**可能**让 reader 把 L566 narrative 误认为"5 位精度 vs 50-digit 闭式测试守护"是 spec 全部精度层级。Mitigation: spec 现有 L155-156 Scenario 已显式建立 50-digit + 5 位双层精度披露框架（`pytest.approx(0.02845302387973555984, abs=1e-30)` + `pytest.approx(0.02845, abs=1e-5)`），L566 升级到 5 位与该框架对齐。
- **[Risk]**: L580 narrative 升级 `−0.0645 → −0.0645385...` 引入 7 位精度，**可能**让 reader 把 L580 narrative 误认为"7 位精度 vs L614 6 位 narrative"是不一致。Mitigation: L614 6 位是 body narrative 的过渡披露；L620 是 Scenario 的 7 位精度；L580 升级到 7 位与 L620 Scenario 对齐；L614 body narrative 升级到 7 位**不**在本 change scope（但可作为未来 follow-up）。
- **[Risk]**: Windows Edit tool CRLF contamination（spec.md 含 non-ASCII: `σ'` `'` `⁻⁹` `≥` `²` `³` `₁` 等字符）。Mitigation: 每个 Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`（per [[windows-edit-crlf-pitfall]] memory）。
- **[Risk]**: L566 升级后 `0.02845` 在 50-digit `0.02845302387973555984` 4 位截断内（diff `0.000003`，relative `0.011%`）；L580 升级后 `−0.0645385...` 在 `ln(15/16) = −0.0645385211...` 7 位截断内（diff `< 1e-7`）。**不**引入新 drift。
- **[Risk]**: 50-digit mpmath 重算脚本 `.audit/verify_*.py` 在 2026-09 cycle-5/6/7 已锁死；本 change 无需重跑，仅 spec narrative 字符级更新。

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical spec delta（2 处 character-level update）。实施步骤：

1. spec delta 落地：`specs/wayfinder/spec.md` 1 处 MODIFIED Requirement（req-24 L566 + L580）
2. `git diff --stat` 验证 LF 保留（无 CRLF contamination）；按 [[windows-edit-crlf-pitfall]] 必要时 `sed -i 's/\r$//'`
3. `grep -F` 验证：
   - `grep -F "σ'(−3.5) ≈ 0.02845" openspec/specs/wayfinder/spec.md` 应在 L130 + L566 各 1 次（共 2 次）
   - `grep -F "γ' = ln(15/16) ≈" openspec/specs/wayfinder/spec.md` 应在 L580 1 次
   - `grep -F "ln(15/16) ≈ −0.0645385" openspec/specs/wayfinder/spec.md` 应在 L580 + L620 各 1 次（共 2 次；L614 是 6 位 `−0.064538...` 不命中）
4. lint gate 双跑：`python scripts/lint_no_dead_defensive.py` + `python scripts/lint_no_source_field_drift.py` 双 exit=0（req-34 Source 字段 anchor + paren-depth-aware atomic split 三项独立报错检查 pass；req-24 Source 不动故不触发风险）
5. 全量测试：`uv run pytest tests/ -v` 全绿（既有 tests 全部覆盖 4/5/6/7/50-digit 五档精度，本 change 升级 L566/L580 narrative 与既有 5/7 位精度对齐，无 test regression）
6. archive 前置：`openspec validate --strict --type change` 应 PASS（无 "Unknown item" 或 "MODIFIED-but-not-found" warnings）；双 lint gate exit=0

## Open Questions

- **Future follow-up**: req-25 L614 body narrative `≈ −0.064538...`（6 位）与 L620 Scenario narrative `≈ −0.0645385...`（7 位）仍存在 6/7 位精度不一致；本 change **不**处理（scope 限于 req-24）；可作为 future spec-narrative-precision follow-up change。Mitigation: 6 位 `−0.064538...` 与 7 位 `−0.0645385...` 数值差 `0.0000005`，远低于 50-digit 闭式锚点 `−0.0645385211...` 7 位截断容差，**不构成新 drift**。
- **A1.5-revised follow-up**: `WB = 0.0476` 无 closed-form derivation 仍是真问题（finding 原提 `1/(d_c·√N_e) ≈ 0.0496` 数学错，需独立 investigation work item）；本 change **不**处理（scope 限于 req-24 narrative 精度；WB closed-form 需要 ticket 数学推导 + 数值验证 + spec/code/test 三角落地，独立 change）。
- **A1.3 / A1.4 / A1.6 finding 复核 evidence 入 audit trail**：见 proposal.md Impact 段；本 change 不修复（finding 本身错），但 archive 后应在 audit trail 显式记录 evidence 防止下一轮 cycle 误判。