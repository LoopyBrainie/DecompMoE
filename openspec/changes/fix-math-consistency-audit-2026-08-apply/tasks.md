# Tasks: fix-math-consistency-audit-2026-08-apply

> Mirror of `apply-checklist.md`（17 项）。每项 TDD：读 spec 锚点 → 先写失败测试 → 最小实现 → `uv run pytest tests/` 零回归 → test+impl 同 commit。期望值一律来自 spec 闭式常量或独立 root-finding，不从实现输出反推。

## 1. 前置

- [ ] 1.1 确认基线：`uv run pytest tests/` → 95 passed, 0 failed（记录为回归基线）

## 2. 代码改动 + 配套测试（8 项）

- [x] 3.1 `src/decompmoe/sphere.py`：删除 `_VORONOI_MVP_TABLE` 及命中分支，全部输入走 bisection
  - Spec 锚点：skeleton "Voronoi Self-Consistency Threshold"（no hard-coded table / MVP self-consistency / N_e dependence, residual < 1e-9）
  - 新测试：`test_no_hardcoded_table_values`（grep 禁止性）、`test_voronoi_residual_below_1e_minus_9`（N_e ∈ {16,17,64}）、`test_voronoi_monotone_in_ne`（≈1.1736 / ≈1.1663 rad, abs=1e-4，独立 root-finding 常数）
  - Verify：`grep -F "_VORONOI_MVP_TABLE" src/decompmoe/sphere.py` → 0 hits

- [x] 3.2 `src/decompmoe/config.py`：FFN FLOPs 系数 `2 * 2 → 3 * 2`（L122/L133；attention `4*2*d²` 不动）
  - Spec 锚点：wayfinder "4070 MVP Hyperparameter Set" — Closed-form parameter totals（per-layer 33_554_432, total 134_217_728 exact）
  - 新测试：`test_flops_per_layer_exact_33554432`、`test_flops_total_exact_134217728`
  - Verify：`grep -F "3 * 2" src/decompmoe/config.py` → ≥ 2 hits

- [x] 3.3 `src/decompmoe/schedule.py`：新增 `gamma_reset_for_phase4` / `phase_beta_max` / `beta_effective`；修复 `phase_beta_box(2)` 落空
  - Spec 锚点：skeleton "Beta Parameterization Operational Domain"
  - pinned convention：`phase_beta_max(phase, step) = lo + (hi−lo)·(step−start)/(end−start)`，end exclusive（Phase 2 `[6_000,26_000)`、Phase 3 `[26_000,56_000)`）；`gamma_reset_for_phase4(16.0) == ln(15/16)` abs=1e-4
  - 新测试：`test_phase_beta_box_phase2_exact`（(1.0, 4.0)）、`test_phase_beta_max_is_time_varying`（(2,6_000)=1.0、(2,16_000)=2.5、(3,26_000)=4.0、(3,41_000)=10.0，abs=1e-9）、`test_gamma_reset_for_phase4_boundary_continuity`
  - Verify：`grep -E "gamma_reset_for_phase4|phase_beta_max|beta_effective" src/decompmoe/schedule.py` → ≥ 3 hits

- [x] 3.4 `src/decompmoe/metrics.py`（最复杂）：SP / D_c→D_chord / MCI / CG 四 stub 换闭式实现
  - MCI：输入 token signatures，uncentered `M=(1/|T|)·Σ C_t C_tᵀ`，`MCI = 1/(d_c·Σ λ̃_j²)`；uniform→1.0 exact、rank-1→1/d_c、range `[1/d_c, 1]`
  - CG：zero→0.0、positive homogeneity `|CG(2g)−2CG(g)|<1e-6`
  - SP：跳过空专家（mean over `‖T_i‖₁>0`）；aligned→1.0、60°→0.5、containment `[-1−1e-6, 1+1e-6]`
  - D_chord：orthonormal basis→√2 abs=1e-6、`√(2·versine)` 关系成立；`OFFLINE = frozenset({"SP","D_chord","MCI","CG"})`
  - 新测试：8 个 closed-form 测试（对应 wayfinder ADDED Requirements）
  - Verify：`grep -F "torch.tensor(0.0)" src/decompmoe/metrics.py` → 0 hits；`grep -F "D_chord"` → ≥ 2 hits

- [x] 3.5 `src/decompmoe/experts.py`：`ExpertPool(nn.Module)` + `nn.ModuleList` + `super().__init__()`
  - Spec 锚点：skeleton "Standard SwiGLU Expert With No Shared Branch"（param 总数 == 100_663_296 exact）
  - Verify：`inspect.getsource(ExpertPool)` 含 `nn.Module` 与 `nn.ModuleList`

- [x] 3.6 `src/decompmoe/extraction.py`：Phase 4 分支补近零 candidate fallback `torch.where(‖c‖<1e-9, prev_c, normalize(c))`
  - Spec 锚点：skeleton "Centroid Driver Semantic Invariants" invariant #4

- [x] 3.7 `src/decompmoe/safeguards.py`：resurrection perturb 返回单专家形状 `(d_c,)` 或 `(d_model·d_ffn,)`；同事件内 β_i ← 0.85·β_{j*} 且 β_{j*} ← 0.85·β_{j*}
  - Spec 锚点：wayfinder ADDED "Resurrection Perturbation Per-Expert Contract"

- [x] 3.8 `src/decompmoe/beta.py`：新增 `phase4_inverse_temperature(gamma_p) = 1 + 31·σ(gamma_p)`；`MAX_GRAD_PER_GAMMA = 15.95` 加显式域标签；新增 `MAX_GRAD_PER_GAMMA_PHASE4 = 15.5`
  - Spec 锚点：skeleton ADDED "Beta Parameterization Operational Domain"
  - Verify：`grep -F "phase4_inverse_temperature" src/decompmoe/beta.py` → ≥ 1 hit

## 3. 测试重写（5 项，替换恒真断言，不增计数）

- [ ] 3.9 `tests/test_loss.py`：`test_sep_formula`（正交基 L_sep==0, abs=1e-12）、`test_load_balance_alpha_fixed`（uniform f=P=1/16 → L_lb_raw==1.0, L_lb==0.01）、`test_lambda_cosine_ramp_phase_3`（λ(26_000)==0.0、λ(41_000)≈5e-4、λ(55_999)≈0.001）

- [x] 3.10 `tests/test_beta.py`：`test_grad_C_bound`（e_1 vs e_2, β=32 → ‖∂logit/∂C‖==32.0, abs=1e-4）、`test_grad_gamma_bound`（γ=0, c=−e_1 → ==15.95, abs=1e-3）、新 `test_max_grad_per_gamma_phase4`（γ'=0, c=−C → ==15.5, abs=1e-3）

- [x] 3.11 `tests/test_extraction.py`：重写 `test_complexity_budget` 用闭式 `H_kv·(2·d_k·d_c+d_c)+H_kv·d_c+d_c`（MVP == 33_040 MACs exact），禁 torch.profiler；加 d_c 加倍 scaling sanity 测试

- [x] 3.12 `tests/test_gating.py`：重写 `test_forward_formula_strictness` 为数值验证——stub experts `E_i(x)=E_i` 固定输出，断言 `x_out == x + Σ_{i∈I_k} p_i·E_i`（abs=1e-6），非 source-grep

- [x] 3.13 `tests/test_config.py`：重写 `test_total_param_estimate` 断言精确值 `total == 452_329_984`、`active == 100_008_448`、`P_router/layer == 32_896`

## 4. 新测试文件/用例（4 组）

- [x] 3.14 `tests/test_experts.py`：`test_expert_pool_is_nn_module`、`test_expert_pool_param_count == 100_663_296`

- [x] 3.15 `tests/test_extraction.py`：`test_near_zero_candidate_fallback_phase4`（‖c‖₂<1e-9 → 保留 prev、无 NaN）

- [x] 3.16 `tests/test_schedule.py`：`test_phase_beta_box_phase2`（(1.0,4.0)）、`test_phase_beta_max_is_time_varying` 边界精确值（abs=1e-9）、`test_beta_effective_phase_4_continuity`（beta_effective(ln(15/16),4,56_000)==16.0 within 1e-6；`phase_beta_max(3,55_999) ≈ 15.9996` limit-continuity witness）

- [x] 3.17 `tests/test_metrics.py`：8 项 closed-form 测试（MCI uniform/rank-1 abs=1e-12；CG zero/homogeneity；SP aligned/60°/containment/range bound）— 若 3.4 已含则此处核对齐全即可

## 5. 验收 gate

- [ ] 5.1 全套件：`uv run pytest tests/` → ≥ 110 passed, 0 failed（95 基线保留 + ~15 new；rewrite 不双计）
- [ ] 5.2 §4 grep 检查全过（metrics 无 stub、sphere 无表、ExpertPool nn.Module、phase_beta_box(2)==(1.0,4.0)、compute_total_and_active==(452_329_984, 100_008_448)、flops_per_token MOE==134_217_728）
- [ ] 5.3 Post-archive 独立复核（CLAUDE.md §3）：逐条代入 spec 数值算式与声称值对账，全部通过
