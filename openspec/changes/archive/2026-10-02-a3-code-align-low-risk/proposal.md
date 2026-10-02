# Proposal

## Why

A-3 重判（`2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix` tasks
3.1–3.5）判定 5 条缺陷属于「spec 已是真相源、代码单方面偏离」，且**改动不改变
路由数学的行为契约**——因此与改变数值输出的 C4 分开交付，以便单独回滚。

5 条各自的实测依据（全部来自台账 `verdict_evidence`，此处不复述）：

1. **AC-73 死守卫**：`clip_global_grad_norm_` 里的 `pre_norm.dim() == 0` 恒真，
   `else pre_norm` 分支不可达；若触达则 `float(多元素张量)` 抛 `ValueError`。
   违反 `CLAUDE.md` §2「不为不可能场景写错误处理」。

2. **AC-75 签名漂移**：`extract_C` 的投影参数名是 `W_K/W_V/b`，而
   `decompmoe-skeleton` req-7 明文声明 `proj_W_K/proj_W_V/proj_b`——**按 spec
   写法以关键字调用会 `TypeError`**，即 spec 声明的签名不可执行。风险低于原评级：
   5 处真实调用全部按位置传参，重命名对调用点零破坏。

3. **AC-78 公共面缺失**：`decompmoe.__all__` 只有 3 个 dunder，docstring 声称的
   「populated lazily by submodules」从未发生（`__init__.py` **零 import**），
   `from decompmoe import *` 从来不能工作。重判同时定位了审计「76 个公开符号」
   的来源：**13 个子模块求和 = 76，去重并集 = 75**，唯一冲突是
   `flops_per_token` 同在 `config` 与 `metrics`。

4. **AC-79 probe 强制 CPU**：`torch.randn(..., generator=)` 无 `device=`，探针矩阵
   恒建在 CPU（`d_c=16` 时 64 MB）。审计的**治理理由（越权）已被证伪**——该守卫
   由 `33f7cc9` 早于 pin 引入，且归档 proposal 明列 `sphere.py` 为 affected file。

5. **AC-44 调度错位**：`loss._lambda_at` 与 `schedule.beta_effective` 都**没有**
   `total_steps` 形参，而 `phase_id` / `phase_boundaries` / `phase_beta_max` 都有。
   非 100K 运行时前者按 100K 窗口爬坡、后者已重标定——静默错位。

## What Changes

- `safeguards.py`：删除不可达分支，返回 `float(pre_norm)`（0 维张量，torch 契约保证）。
- `extraction.py`：投影参数重命名为 `proj_W_K` / `proj_W_V` / `proj_b`，与 req-7
  逐字一致。
- `__init__.py`：导入 13 个子模块的公开名，`__all__` 填 **75 + 3 = 78** 项；
  `flops_per_token` 显式绑定到 `config`（`metrics` 镜像仍可达）。
- `sphere.py`：探针加 `device=centroids.device`。
- `loss.py` / `schedule.py`：`total_steps` 一路贯通到
  `_lambda_at` / `L_total` / `beta_effective` → `phase_beta_max`；删除被本次改动
  变成孤儿的 `_PHASE_BOUNDS`（其值现由 `phase_boundaries()` 派生）。
- 测试：新增 `tests/test_a3_contract_alignment.py`（15 条）；更新
  `test_extract_C_signature`（跟随 req-7 新签名）与
  `test_no_other_module_defines_should_resurrect`（区分**再导出**与**二次定义**）。

**不改动**：任何 spec（契约已由 C1/C2 收口）、`sphere.py` 的求积路径、路由数学。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——`skip_specs: true`。本 change 只让代码对齐已在 C1/C2 定稿的契约。）

## Impact

- **受影响模块**：`safeguards` / `extraction` / `__init__` / `sphere` / `loss` /
  `schedule`。
- **行为契约不变**：100K 默认预算下 `phase_boundaries(100_000)` 与被删除的
  `_PHASE_BOUNDS` 逐项相同，故 λ(t) 与 β^eff 的读数**逐位不变**；新测试对此有
  钉值断言。
- **`from decompmoe import *` 首次真正生效**（此前从未工作过）——这是本 change
  风险最高的一项，因为它把一条从未被执行过的路径变成可用路径。已实测 13 个子模块
  无循环 import，75 个名称全部可解析。
- **共享工作树隔离**：`src/decompmoe/gating.py` 在本轮开工前即为 modified-uncommitted
  （`baseline.json` 的 `worktree_state` 登记在案，其 diff 是 `local_softmax` 的
  `torch.where`，与本 change 无关）。全程选择性暂存，**未**将其纳入。
