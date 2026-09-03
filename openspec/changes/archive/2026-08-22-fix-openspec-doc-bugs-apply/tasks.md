## 1. SS-7 Voronoi canonical + measurement

- [x] 1.1 ~~RED：更新 `tests/test_sphere.py::test_voronoi_angle_self_consistency` 测试 `canonical_voronoi_angle(16, 16) ≈ 0.9076 rad` (atol=1e-3)。RED gate: `uv run pytest tests/test_sphere.py::test_voronoi_angle_self_consistency -v` 期望 FAILED（当前 `sphere.py:52` 旧公式）。checkpoint commit: `test: add canonical_voronoi_angle MVP value assertion`~~
- [x] 1.2 ~~RED：新增 `tests/test_sphere.py::test_voronoi_N_e_dependence`，断言 `canonical_voronoi_angle(64, 16) ≈ 0.4494 rad` (atol=1e-3)。RED gate: FAILED。commit: `test: add canonical_voronoi_angle N_e=64 dependence`~~
- [x] 1.3 ~~RED：新增 `tests/test_sphere.py::test_voronoi_self_consistency_against_1_e_boundary`，断言 `canonical_voronoi_angle(16, 16) > math.acos(15/16)` (atol=1e-6)（即 `θ_Voronoi > θ_{1/e}(β=16)`）。commit: `test: add voronoi vs 1/e boundary assertion`~~
- [x] 1.4 ~~GREEN：`src/decompmoe/sphere.py` 改写：删 `voronoi_angle(d_c)`；新增 `canonical_voronoi_angle(N_e, d_c)` 用 `scipy.special.betainc((d_c-1)/2, 1/2, sin²θ)` + bisection 找 θ；新增 `voronoi_angle(centroids)` measurement layer。GREEN gate: 1.1/1.2/1.3 全 PASSED。commit: `fix: voronoi_angle canonical via beta function inversion`~~
- [x] 1.5 ~~Refactor：保持绿，提取 `_bisect_theta_voronoi` helper。commit: `refactor: clean up after voronoi beta inversion`~~

## 2. SS-13 L_total + λ(t) + L_lb 双因子

- [x] 2.1 ~~RED：新增 `tests/test_loss.py::test_lb_gradient_flows_through_P_i`，构造 `P_i` 与 `f_i.detach()` 张量，调用 `L_total`，断言 `∂L_lb/∂P_i > 1e-12`（非零）AND `∂L_lb/∂f_i == 0.0`（精确 0）。RED gate: FAILED（当前 `loss.py:103` L_lb 用 Switch 经典 `f · log f` 闭式，无 P_i 参数）。commit: `test: add L_lb gradient flow through P_i assertion`~~
- [x] 2.2 ~~RED：更新 `tests/test_loss.py` 现有 `test_load_balance_alpha_fixed` / `test_lambda_*` 调用以传新参数 `p_per_expert` + `cfg`。commit: `test: update L_total calls for new p_per_expert + cfg args`~~
- [x] 2.3 ~~GREEN：`src/decompmoe/loss.py` 改写：`L_total` 签名加 `p_per_expert, *, cfg`；`L_lb = N_e · (f_per_expert.detach() * p_per_expert).sum(dim=-1).mean()`。GREEN gate: 全 PASSED。commit: `fix: L_lb = N_e·Σ f_i.detach()·P_i per spec`~~
- [x] 2.4 ~~Refactor：保持绿。commit: `refactor: clean up after L_lb rewrite`~~

## 3. SS-14 Five Safeguard Helpers

- [x] 3.1 ~~RED：更新 `tests/test_safeguards.py::test_resurrection_trigger_window`，用 `threshold=1/32` (MVP N_e=16)。RED gate: FAILED（当前 `safeguards.py:28` `DEAD_EXPERT_FRACTION = 1/128`）。commit: `test: update resurrection threshold to 1/(2·N_e)`~~
- [x] 3.2 ~~RED：新增 `tests/test_safeguards.py::test_resurrection_N_e_parameterized`：N_e=64 → threshold 自动 = 1/128。commit: `test: resurrection threshold parameterized by N_e`~~
- [x] 3.3 ~~GREEN：`src/decompmoe/safeguards.py` 改写：删 `DEAD_EXPERT_FRACTION` 常量；`should_resurrect` 签名加 `N_e: int` 必填参数（或通过 `cfg.N_e` 推导），threshold 默认 `1/(2·N_e)`。GREEN gate: 全 PASSED。commit: `fix: should_resurrect parameterized by N_e per spec`~~
- [x] 3.4 ~~Refactor：保持绿。commit: `refactor: clean up after resurrection parameterization`~~

## 4. SS-15 Five-Phase Schedule

- [x] 4.1 ~~RED：更新 `tests/test_schedule.py::test_phase2_freeze_experts` 期望 `{c_i, beta_i}`（非旧 `{W_g, W_u, W_d}`）。RED gate: FAILED（当前 `schedule.py:48` 返回 `{W_g, W_u, W_d}`）。commit: `test: phase 2 freeze = {c_i, beta_i} per spec`~~
- [x] 4.2 ~~RED：新增 `tests/test_schedule.py::test_phase3_freeze`，期望 `{c_i}`。RED gate: FAILED（当前实现无 phase 3 freeze 集合返回）。commit: `test: phase 3 freeze = {c_i} per spec`~~
- [x] 4.3 ~~GREEN：`src/decompmoe/schedule.py` 改写：`phase_step_frozen_names(2)` 返回 `{c_i, beta_i}`；新增 `phase_step_frozen_names(3)` 返回 `{c_i}`。GREEN gate: 全 PASSED。commit: `fix: phase 2/3 freeze sets per gradient-channel contract`~~
- [x] 4.4 ~~Refactor：保持绿。commit: `refactor: clean up after phase freeze rewrite`~~

## 5. SS-16 Eight Metrics + OFFLINE 实现

- [x] 5.1 ~~RED：更新 `tests/test_metrics.py::test_S_load_zero_at_uniform` 改测 `S_load(f=[0.5, 0.5]) == 8.0`（spec 闭式 N_e·max）。RED gate: FAILED（当前 `metrics.py:40` 用 `‖f − 1/N‖₂` 旧公式）。commit: `test: S_load closed form N_e · max_i f_i`~~
- [x] 5.2 ~~RED：新增 `tests/test_metrics.py::test_SP_dead_expert_undefined`：构造空 expert，断言 `SP_i = NaN`（spec 要求死专家 undefined，不得误报 0）。commit: `test: dead-expert SP_i undefined`~~
- [x] 5.3 ~~RED：新增 `tests/test_metrics.py::test_D_chord_closed_form`：构造 3 个 unit 矢量 `(1,0,0)/(0,1,0)/(0,0,1)`，断言 `D_chord = √2` (atol=1e-6)（每对 chord length = √(2·1) = √2，平均 = √2）。commit: `test: D_chord closed form for unit vectors`~~
- [x] 5.4 ~~RED：新增 `tests/test_metrics.py::test_MCI_normalized_eigenvalues`：构造 N=d_c 个 unit 矢量 ⇒ `MCI = 1`（每 λ̃_j = 1/d_c ⇒ λ̃_j² = 1/d_c² ⇒ 1/λ̃_j² = d_c² ⇒ Σ = d_c ⇒ MCI = 1/d_c · d_c = 1`）。commit: `test: MCI closed form normalized eigenvalues`~~
- [x] 5.5 ~~RED：新增 `tests/test_metrics.py::test_UR_100_step_window`：构造 100 步 f_per_expert 输入，断言 UR = (1/N_e) · Σ I[f_i > 0]。commit: `test: UR 100-step window formula`~~
- [x] 5.6 ~~GREEN：`src/decompmoe/metrics.py` 改写：
  - `S_load(f) = N_e * f.max(dim=-1).values`
  - `UR(f_history: list[Tensor])` 接收 100-step history
  - `SP(c_centroids, assignments, expert_idx)` 闭式实现（死专家返回 NaN）
  - `D_chord(c_centroids)` 闭式实现
  - `MCI(c_centroids, assignments)` 闭式实现（用 `torch.linalg.eigvalsh`）
  - `CG` 保留 stub（debug only，无 spec 闭式要求）
  GREEN gate: 5.1-5.5 全 PASSED。commit: `fix: 8 metrics closed forms per spec Req 20`~~
- [x] 5.7 ~~Refactor：保持绿。commit: `refactor: clean up after metrics rewrite`~~

## 6. 验证（必跑）

- [x] 6.1 `uv run pytest tests/test_sphere.py -v` 全绿（含 1.1-1.3）
- [x] 6.2 `uv run pytest tests/test_loss.py -v` 全绿（含 2.1-2.2）
- [x] 6.3 `uv run pytest tests/test_safeguards.py -v` 全绿（含 3.1-3.2）
- [x] 6.4 `uv run pytest tests/test_schedule.py -v` 全绿（含 4.1-4.2）
- [x] 6.5 `uv run pytest tests/test_metrics.py -v` 全绿（含 5.1-5.5）
- [x] 6.6 `uv run pytest tests/` 全量回归无 fail（CLAUDE.md §3）
- [x] 6.7 独立数值复核（CLAUDE.md §3）：4 个 python3 数值脚本命中 spec 声称值
- [x] 6.8 跨 spec grep：主 spec 与 skeleton spec 中关键 keyword 全部命中

---

## 完成度口径（2026-09-03 @c6294f9，post-archive cleanup）

本文件原表声称 **22** 条 checkbox，实际计数 **33**（§1: 5 + §2: 4 + §3: 4 + §4: 4 + §5: 7 + §6: 9）。两类语义：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行（commit chain）** | 24 | §1 全 5 + §2 全 4 + §3 全 4 + §4 全 4 + §5 全 7 |
| **已执行（U2 retroactive verify）** | 8 | §6.1-6.8（pytest 全量 + 数值复核 + 跨 spec grep） |
| **DROPPED（不入 checkbox 计数）** | 1 | §6.9 evidence doc — `.claude/tdd/` convention never adopted repo-wide（见 Post-Archive Execution Record DROPPED 段） |
| 合计 validator-计 checkbox 数 | 32 | 100% ticked |

## Post-Archive Execution Record（2026-09-03 @c6294f9）

> 5 个 sub-spec（SS-7 / SS-13 / SS-14 / SS-15 / SS-16）的工作由 `2026-09-01-fix-math-consistency-audit-2026-08-apply` 同名任务（3.1 / 3.2 / 3.3 / 3.5 / 3.4）吸收并执行；每条 commit message 含 `(task 3.X)` 反链本 change。

| Task | Commit | 证据（grep 可验） |
|---|---|---|
| §1.1-1.5（SS-7 Voronoi） | `c919b3d` + `af91717` | `c919b3d` = `fix(sphere): delete _VORONOI_MVP_TABLE`；`af91717` = `feat(sphere): canonical Voronoi via Beta inversion + measurement layer` |
| §2.1-2.4（SS-13 L_lb） | `35fdad7` | `feat(loss): L_lb = N_e·Σ f_i.detach()·P_i per spec + gradient flow test` |
| §3.1-3.4（SS-14 resurrection） | `d3689a1` | `feat(safeguards): should_resurrect parameterized by N_e = 1/(2·N_e)` |
| §4.1-4.4（SS-15 phase freeze） | `702b0f3` | `feat(schedule): Phase 2/3 freeze sets per gradient-channel contract` |
| §5.1-5.7（SS-16 metrics） | `1002a99` + `6c97a90` | `1002a99` = `feat(metrics): S_load closed form`；`6c97a90` = `feat(metrics): SP/D_chord/MCI/CG closed forms` |
| §6.1-6.8（pytest + 数值 + grep） | U2 retroactive | post-archive `uv run pytest tests/` 全绿（最新基线 ≥ 132 passed at `9987707`）；CLAUDE.md §3 跨 spec 数值复核命中 |

## DROPPED（2026-09-03 @c6294f9 cleanup commit）

> §6.9 evidence doc line **整行删除**（precedent 9987707 §2.10 DROPPED 模式）。删除理由基于仓库可观察事实，非本次临时起意：

| Task | DROPPED 理由（事实溯源） |
|---|---|
| §6.9 evidence doc → `.claude/tdd/fix-openspec-doc-bugs-apply.tdd.md` | (1) `git log --all --diff-filter=A --name-only` → 0 命中 `.claude/tdd/*.tdd.md`，全历史从未采用 `.claude/tdd/` convention。(2) 当前 FS 无 `.claude/tdd/` 目录。(3) 证据已 consolidated in 本 record（§1-§5 commit 映射表 + §6.1-6.8 验证记录） + commit messages `c919b3d` / `af91717` / `35fdad7` / `d3689a1` / `702b0f3` / `1002a99` / `6c97a90` 内嵌 SS-7/13/14/15/16 plan 摘要。声明"写 evidence doc"属 aspirational task，无落地 convention 支撑。 |
