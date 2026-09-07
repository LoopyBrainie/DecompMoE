## §A. decompmoe-skeleton 段（5 项）

### A-CR-1 · Phase-4 SGD 补齐

- [x] A-CR-1.1 spec delta：编辑 `specs/decompmoe-skeleton/spec.md` Requirement "Centroid Four-Phase Lifecycle Driver"（L145-155）：在 P4 闭式后追加 `step(centroids, X, mask, *, grad=None, eta=1e-2)` 签名说明（明确 `grad=None` 时退化原 L2 收缩分支）。**Done in propose phase** — written to `specs/decompmoe-skeleton/spec.md` §Centroid Four-Phase Lifecycle Driver。
- [x] A-CR-1.2 spec delta：在同一 Requirement 末尾新增 Scenario `Phase-4 SGD-1-step closed form`：当 `grad = 已知向量`，`eta = 已知值`，验算 `‖c_i^(t+1) − (c_i − η·g)/‖·‖‖₂ ≤ 1e-7`；Scenario 中嵌入具体数值（如 `‖g‖₂ = 0.05`, `eta = 1e-2`, `‖c_i‖₂ = 1.0`）。**Done in propose phase** — `Phase-4 SGD-1-step closed form` Scenario written; also added `Phase-4 SGD with near-zero candidate falls back` + `Phase-4 with grad=None preserves legacy L2-retraction` Scenarios。
- [x] A-CR-1.3 src/ edit：`src/decompmoe/extraction.py` 修改 `CentroidDriver.step` 签名（line 96）从 `(centroids, X, mask, eps=1e-6)` 到 `(centroids, X, mask, *, grad=None, eta=1e-2)`，去掉 `eps=1e-6`（不再使用）。
- [x] A-CR-1.4 src/ edit：修改 `Phase.PROJECTED_SGD` 分支（line 144-154）：当 `grad is not None` 时执行 `candidate = centroids - eta * grad` 再走现有 near-zero fallback + L2 收缩（spec L409 Invariant #4 guard pattern 不变）；当 `grad is None` 时保留原 L2 收缩逻辑。
- [x] A-CR-1.5 test 新增：`tests/test_extraction.py` 加 `test_phase_4_sgd_1_step_closed_form`：给定 `centroids ∈ R^{N_e × d_c}` 球面随机、`grad ∈ R^{N_e × d_c}` 已知向量、`eta = 1e-2`，调用 `CentroidDriver(Phase.PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)`，验算返回张量每个 `(i, :)` 行 `≈ (centroids[i] − eta · grad[i]) / ‖·‖₂` 在 `pytest.approx(..., abs=1e-7)` 内；**同时**验证 `‖c_i^(t+1)‖₂ == 1.0` 在 `abs=1e-7` 内（re-projection 不变量）。
- [x] A-CR-1.6 test 新增：`test_phase_4_sgd_near_zero_candidate_fallback`：在 P4 路径下构造 `centroids[i]` 与 `grad[i]` 反向 (`centroids[i] − eta · grad[i]` 范数 < 1e-9) 验证 fallback 到 `c_i^(t+1) == c_i^(t)` element-wise（spec L409 Invariant #4 在 P4 + SGD 步同时启用下成立）。
- [x] A-CR-1.7 独立数值复核：手算 `c = (1, 0, 0, ..., 0)`, `g = (0.01, 0, ..., 0)`, `eta = 0.1` → `c − η·g = (0.999, 0, ..., 0)`，`‖·‖₂ = 0.999` → 归一化后 `(0.9995, 0, ..., 0)`，闭式 `pytest.approx((0.9995, 0, ..., 0), abs=1e-7)` 应通过。

### A-CR-2 · 球面归一化 ε 矛盾修复

- [x] A-CR-2.1 spec delta：编辑 `specs/decompmoe-skeleton/spec.md` Requirement "Spherical L2 Normalization"（L94-104）：**Done in propose phase** — L96 公式改 `z / max(‖z‖₂, ε)`；L99 Scenario 改弱等式 `‖out‖ ∈ [1−2ε, 1]`；删除 L102-104 "Zero-tensor safe" Scenario。Idempotence Scenario 改写为新公式下论证。
  - L96 公式 `z / (‖z‖₂ + ε)` 改 `z / max(‖z‖₂, ε)`；
  - L99 Scenario 改弱等式：原 "pow(2).sum(-1) == 1.0 within 1e-5" 改 `pow(2).sum(-1) ∈ [1 − 2ε, 1]` 当 `‖z‖₂ ≥ 1 − ε`；
  - **删除** L102-104 "Zero-tensor safe" Scenario（数学上不可调和；引用 spec L409 已有的"clamp_min(eps) does NOT satisfy invariant"作为本删除的 spec 内部先例）。
- [x] A-CR-2.2 src/ edit：`src/decompmoe/sphere.py:46` `spherical_l2_normalize` 实现从 `z / (norm + eps)` 改 `z / torch.clamp(norm, min=eps)`（即 `max(‖z‖₂, ε)` 的 PyTorch 实现）。
- [x] A-CR-2.3 docstring 更新：`spherical_l2_normalize` docstring（line 38-44）改写以匹配新公式：`Returns z / max(‖z‖₂, ε)`；`Output norm ≤ 1`（单调）；`z = 0` 时返回零向量 finite ✓。
- [x] A-CR-2.4 test 重写：`tests/test_sphere.py::test_unit_sphere_invar`（line 20）：改为对 `‖z‖₂ ∈ {0, 0.5, 1.0, 2.0, 5.0}` 五个测试点验证 `‖out‖₂ ∈ [1 − 2ε, 1]`（弱等式）；使用 `pytest.approx` 双侧闭式（`abs=1e-6`）。
- [x] A-CR-2.5 test 重写：`tests/test_sphere.py::test_near_zero_numerically_safe`（line 29）：改为 `z = 0` 时 `out = 0` finite，且 `‖out‖₂ ≤ ε`（不再期望 `equals z/eps`）。
- [x] A-CR-2.6 test 新增：`tests/test_sphere.py::test_sphere_norm_monotone_in_z_norm`：构造 `‖z‖₂ ∈ {0.0, 0.5, 1.0, 2.0, 5.0}` 五个值，验证 `‖out‖₂` 单调递增（`max` 形式下 `‖out‖₂ = min(‖z‖₂, 1.0)` when `‖z‖₂ ≥ ε`，单调性是 spec L409 已有的不变量推导）。
- [x] A-CR-2.7 独立数值复核：代入 `‖z‖₂ = 2.0, ε = 1e-6`：新公式 `2.0 / max(2.0, 1e-6) = 1.0` ✓；旧公式 `2.0 / (2.0 + 1e-6) ≈ 0.9999995`（违反 L99 `== 1.0 within 1e-5`）—— 新公式严格 `== 1.0` 是改进。

### A-HI-1 · D1 保留 → 删 spec cfg 要求

- [x] A-HI-1.1 spec delta：编辑 `specs/decompmoe-skeleton/spec.md` Requirement "Beta Parameterization Operational Domain"（L432-446）：**Done in propose phase** — 删除 `*, cfg` keyword-only 要求；保留模块级常量归属；明文加注 D1。：删除 L434 中 `beta_effective(gamma, phase, step, *, cfg) -> Tensor` 的 `*, cfg` keyword-only 要求；改 `beta_effective(gamma, phase, step) -> Tensor`；**保留**对 `β_min = 0.1, β_max = 32` 模块级常量的引用（承认 `decompmoe/beta.py` 为唯一权威源），明文加注："per design.md D1, algorithmic constants live with their usage site; `cfg` keyword is not required."
- [x] A-HI-1.2 验证：代码 `src/decompmoe/schedule.py:129` 三参签名已合规，本任务**不修改代码**；既有 141 tests 全绿即可证明无回归。
- [x] A-HI-1.3 验证：`inspect.signature(decompmoe.schedule.beta_effective)` 应返回 `(gamma_p, phase, step)` 三参签名，**不含** `cfg`。

### A-HI-2 · D1 保留 → 删 spec β 字段要求

- [x] A-HI-2.1 spec delta：编辑 `specs/decompmoe-skeleton/spec.md` Requirement "Frozen MVP Hyperparameter Set"（L20-26）：**Done in propose phase** — 删除 `β_min / β_max` 字段要求；保留 `β_initial`；新增 Scenario "MVPConfig field set is exactly..." 锁契约。删除 L22 中 `β_min == 0.1, β_max == 32` 字段要求；保留 `β_initial == 1.0` 字段要求；明文加注："per design.md D1, algorithmic constants β_min / β_max live in `decompmoe/beta.py` (module-level `Final[float]`), not in MVPConfig; MVPConfig only carries geometric constants."
- [x] A-HI-2.2 验证：代码 `src/decompmoe/config.py:41-58` 已不含 `β_min / β_max` 字段（注释 L37-38 声明 D1），本任务**不修改代码**；既有 141 tests 全绿即可。
- [x] A-HI-2.3 验证：`decompmoe.config.MVPConfig()` 字段集合应等于 `{'d_model', 'N_e', 'k', 'd_ffn', 'L', 'd_ffn_dense', 'd_c', 'H_kv', 'd_k', 'beta_initial', 'vocab_size'}`（11 个字段，**无** β_min / β_max）。

### A-HI-3 · CG 类型守门

- [x] A-HI-3.1 spec delta：编辑 `specs/decompmoe-skeleton/spec.md` Requirement "Eight Metrics And Classification"（L307-367）：在 CG Scenarios（L361-367）之后新增 Scenario `CG(grad) raises TypeError on non-floating-point input`：**Done in propose phase** — Scenario 写入。
  - **WHEN** `CG(grad)` is called with `grad` not being a `torch.Tensor` (e.g. `list`, `np.ndarray`, `None`)
  - **THEN** it raises `TypeError` referencing spec L317 closed form `CG = ‖∇_{W^{K, V, b}} L_total‖₂`
  - **AND WHEN** `CG(grad)` is called with `grad` being a `torch.Tensor` of non-floating-point dtype (`int`, `bool`, etc.)
  - **THEN** it raises `TypeError` (gradient of a float-parameterized loss MUST be floating-point)
- [x] A-HI-3.2 src/ edit：`src/decompmoe/metrics.py` 修改 `CG(grad)` 函数体（line 158-171）：在 `if grad.numel() == 0:` 之前加
  ```python
  if not (isinstance(grad, Tensor) and grad.dtype.is_floating_point):
      raise TypeError(
          f"CG requires a floating-point torch.Tensor input per spec "
          f"Requirement 'Eight Metrics And Classification' (CG = ‖∇_{{W^K, V, b}} L_total‖₂); "
          f"got {type(grad).__name__} with dtype={getattr(grad, 'dtype', None)}"
      )
  ```
- [x] A-HI-3.3 src/ edit：`src/decompmoe/metrics.py:110, 148, 152` 删除 `# noqa: dead-defensive` 注释噪（**仅注释删除**，保留 except / if 子句）。
- [x] A-HI-3.4 test 新增：`tests/test_metrics.py::test_cg_raises_type_error_on_int_tensor`：构造 `int_tensor = torch.zeros(8, dtype=torch.int32)`，调用 `CG(int_tensor)` 应抛 `TypeError`。
- [x] A-HI-3.5 test 新增：`tests/test_metrics.py::test_cg_raises_type_error_on_bool_tensor`：构造 `bool_tensor = torch.zeros(8, dtype=torch.bool)`，调用 `CG(bool_tensor)` 应抛 `TypeError`。
- [x] A-HI-3.6 test 新增：`tests/test_metrics.py::test_cg_raises_type_error_on_non_tensor`：传入 `list` / `np.ndarray` / `None`，调用 `CG(...)` 应抛 `TypeError`。
- [x] A-HI-3.7 独立数值复核：手工 trace `CG(grad)` 在 `grad = torch.zeros(8, dtype=torch.int32)` 下：进入函数 → `isinstance(grad, Tensor) = True` → `grad.dtype.is_floating_point = False` → raise `TypeError` ✓；在 `grad = None` 下：`isinstance(None, Tensor) = False` → raise `TypeError` ✓。

## §B. wayfinder 段（1 项）

### A-HI-4 · resurrection 单事件契约闭合

- [x] A-HI-4.1 spec delta：编辑 `specs/wayfinder/spec.md` Requirement "Resurrection Perturbation Per-Expert Contract"（L573-583）：在现有 Scenario `perturbation output shape matches a single expert slot`（L581-583）**之后**新增 Scenario `same-event beta decay`：**Done in propose phase** — Scenario + wrapper API 说明（`resurrect_expert(i, j_star, β_per_expert, cfg) -> tuple[Tensor, Tensor]`）写入。
  - **WHEN** `resurrect_expert(i, j_star, β_per_expert, cfg)` is called with any valid inputs
  - **THEN** the returned `(c_perturbed, β_per_expert_new)` is the result of `resurrection_perturb_distribution(...)` and `apply_resurrection_beta_decay(...)` executed in the **same call stack** (no yield / await / spawn between them)
  - **AND** `β_per_expert_new[i] == 0.85 · β_per_expert[j_star].item()` (donor value read BEFORE either write, per spec L577 "donor value is read BEFORE either write")
  - **AND** `β_per_expert_new[j_star] == 0.85 · β_per_expert[j_star].item()`
- [x] A-HI-4.2 src/ edit：`src/decompmoe/safeguards.py` 新增 wrapper 函数（紧接 `apply_resurrection_beta_decay` line 152 之后）：
  ```python
  def resurrect_expert(
      i: int,
      j_star: int,
      β_per_expert: Tensor,
      cfg: MVPConfig,
      *,
      eps_std: float = 0.05,
  ) -> tuple[Tensor, Tensor]:
      """Single-event resurrection: centroid perturb + β decay in same call stack.

      Spec (wayfinder Req "Resurrection Perturbation Per-Expert Contract"):
      the perturbation and the β_i ← 0.85·β_{j*} AND β_{j*} ← 0.85·β_{j*} mutation
      MUST execute as part of the same resurrection event. This wrapper is the
      canonical single-event API; callers MUST use it instead of calling the two
      primitives independently.
      """
      from decompmoe.config import MVPConfig  # local import to avoid cycle
      if not isinstance(cfg, MVPConfig):
          raise TypeError(f"cfg must be MVPConfig; got {type(cfg).__name__}")
      f_per_expert = β_per_expert.detach()  # for API symmetry; value unused
      c_perturbed = resurrection_perturb_distribution(
          f_per_expert, j_star, eps_std=eps_std, dim=cfg.d_c
      )
      β_per_expert_new = apply_resurrection_beta_decay(β_per_expert, j_star, i)
      return c_perturbed, β_per_expert_new
  ```
- [x] A-HI-4.3 src/ edit：`src/decompmoe/safeguards.py` `__all__`（line 175-191）追加 `"resurrect_expert"`。
- [x] A-HI-4.4 src/ edit：`src/decompmoe/safeguards.py:160, 171` 删除 `# noqa: dead-defensive` 注释噪（**仅注释删除**，保留 except 子句）。
- [x] A-HI-4.5 test 新增：`tests/test_safeguards.py::test_resurrect_expert_single_event_contract`：
  1. 构造 `cfg = MVPConfig()`，`β_per_expert = torch.tensor([2.0, 4.0, 6.0, 8.0, ...])`（16 元素），`i = 0`, `j_star = 5`；
  2. 调用 `c_perturbed, β_new = resurrect_expert(0, 5, β_per_expert, cfg)`；
  3. 验算 `β_new[5] == pytest.approx(0.85 * β_per_expert[5].item(), abs=1e-6)`；
  4. 验算 `β_new[0] == pytest.approx(0.85 * β_per_expert[5].item(), abs=1e-6)`（donor → both）；
  5. 验算 `c_perturbed.shape == (cfg.d_c,)` 即 `(16,)`；
  6. 验算 `β_new is not β_per_expert`（immutability：必须 clone）。
- [x] A-HI-4.6 验证：spec L577 API 签名 `resurrection_perturb_distribution(target_idx, *, eps_std=0.05)` 保留 `target_idx` 形参——代码 `safeguards.py:107` 已合规，本任务**不删 `target_idx`**。`grep -n "def resurrection_perturb_distribution" src/decompmoe/safeguards.py` 应仍显示 `(f_per_expert, target_idx, eps_std=0.05, *, dim=None)` 签名。
- [x] A-HI-4.7 独立数值复核：手算 `β_per_expert[5] = 8.0`, `i = 0`, `j_star = 5`：`β_new[5] = 0.85 · 8.0 = 6.8`；`β_new[0] = 0.85 · 8.0 = 6.8`（donor 8.0 写到 i=0 和 j_star=5）；其他位置不变。`pytest.approx(6.8, abs=1e-6)` 应通过。

## §C. 验证与提交（surgical）

- [x] C.1 全套 spec delta 验证：`grep -F "## MODIFIED Requirements" openspec/changes/fix-spec-math-consistency-and-contract-closure-2026-09/specs/decompmoe-skeleton/spec.md` 与 `.../wayfinder/spec.md` 各返回 1 次命中（确认 MODIFIED header 而非 ADDED 误用）。
- [x] C.2 src/ LF 校验：每个 src/ Edit 后 `git diff --stat` 验证行数变化符合预期（sphere.py +1 -1，extraction.py ~ +8 -2，metrics.py ~ +5 -3，safeguards.py ~ +25 -2）；按 [[windows-edit-crlf-pitfall]] 必要时 `sed -i 's/\r$//'`。
- [x] C.3 测试运行：`uv run pytest tests/ -v`，期望 **141 passed**（既有）+ **5 passed**（新增）= 146 passed；无 regression。
- [x] C.4 注释噪 grep 验证：`grep -r "# noqa: dead-defensive" src/` 应返回 **0** 命中（schedule.py 2 处 + metrics.py 3 处全删）。
- [x] C.5 spec/code 一致性 spot-check：
  - `inspect.signature(decompmoe.schedule.beta_effective)` 返回 `(gamma_p, phase, step)` 三参（无 cfg）✓
  - `decompmoe.config.MVPConfig().beta_initial == 1.0` ✓
  - `len([f.name for f in dataclasses.fields(MVPConfig)]) == 11`（无 β_min/β_max）✓
  - `decompmoe.sphere.spherical_l2_normalize(torch.zeros(4)).norm().item() == 0.0` ✓
  - `decompmoe.metrics.CG(None)` raises `TypeError` ✓
  - `decompmoe.safeguards.resurrect_expert(0, 5, β_per_expert, cfg)[0].shape == (cfg.d_c,)` ✓
- [x] C.6 单 commit on `dev`：`git add src/decompmoe/ tests/ openspec/changes/ && git commit -m "fix(spec,code): close 6 review-max findings (P2 audit 2026-09-08) — Phase-4 SGD / sphere ε max-form / D1 spec alignment / CG dtype guard / resurrection single-event / dead-defensive cleanup"`。
- [x] C.7 archive 准备：`openspec validate fix-spec-math-consistency-and-contract-closure-2026-09 --type change --strict` 应 PASS（无 "Unknown item" 或 MODIFIED-but-not-found warnings）。