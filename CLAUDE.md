# CLAUDE.md

Project-level instructions for **DecompMoE**. Merges with the user's global `~/.claude/CLAUDE.md` (think-before-coding, simplicity-first, surgical changes, goal-driven execution). When in doubt, the global guidelines win on behavior; this file wins on what is "in scope" and where the truth lives.

## 1. Project Identity

- **Canonical name**: DecompMoE (decomposed Mixture of Experts)
- **Documented alias**: GeoMoE (use only in design prose, never as a code identifier)
- **Architecture**: Decoder-Only Llama + Post-FFN geometric routing
- **Hardware MVP**: 4070 8 GB single-GPU
- **Language**: 中文为主，数学符号用 LaTeX

## 2. Truth Source Hierarchy

When sources disagree, consult in this order:

1. **`openspec/specs/wayfinder/spec.md`** — OpenSpec 真相源（21 Requirements × 34 Scenarios）
2. **`openspec/changes/archive/`** — historical change log（每个 spec-level delta 在此）
3. **`openspec/specs/wayfinder/spec.md` 中的 `**Source:**` 字段** — 反链到 `wayfinder/tickets/*.md`
4. **`wayfinder/map.md` + 23 tickets** — 决策 trail 与 rationale
5. **代码层（未来）** — `openspec/changes/<name>/proposal.md`

**规则**：想修改 DecompMoE 行为？先改 OpenSpec spec，不要直接动代码。

## 3. Workflow Conventions

- **Spec-level 变更**：`/opsx:propose` → review 制品 → `/opsx:apply`（含 archive）
- **Ticket 级设计**：`/wayfinder`（claim → resolve → close → append 到 map.md Decisions-so-far）
- **代码实现**：仅在 apply 阶段显式触发后
- **每次 Spec 变更**必须含 `**Source:**` 反链 ticket，确保可追溯
- **TDD 工作流**（每个子 task 入口：`/ecc:tdd-workflow` → 红 / 绿 / 重构 + 数学约束）：
  - **依赖**：`uv sync`（pyproject.toml 用 `uv.sources` 拉 `pytorch-cu130`，已设 `pythonpath = ["src"]`，无需 `pip install -e`）
  - **命令速查**：
    - `uv run pytest tests/` 跑全部
    - `uv run pytest tests/test_<module>.py::<name> -v` 单测（含 verbose）
    - `uv run pytest tests/ -k "<pattern>"` 表达式匹配（如 `-k "phase1 or phase2"`)
    - `uv run pytest tests/test_X.py -x` 首个失败即停（调试用）
    - 失败时优先看 `assert` 内嵌的 `f"actual={...}"` 输出，定位算式错
  - **数学约束协议（强制）**：spec 中每个含具体数值的算式（FLOPs / 参数 / `θ_Voronoi` / `σ(γ)` / 阈值 `1/(2·N_e)` / α 序列 / 相位覆盖）都必须有 `pytest.approx(..., abs=...)` 直接对账；文字断言（"正确"/"合理"/"≈"无数字）不构成可验条款——理由见 §6 第 8 条
  - **测试文件约定**（与已有 `tests/` 风格一致）：
    - 模块 docstring 第一行：`"""Tests for decompmoe.<m>: <一句话>。\n\nST-XX / Req N — <spec 场景标题>。"""`（反链 spec 锚点）
    - 函数命名：`test_<被测算子>_<具体属性>`（如 `test_beta_endpoints`、`test_logit_zero_at_aligned`）
    - 随机性：`torch.manual_seed(0)` 作为第一行
    - 数值容差：math 性质用 `pytest.approx(value, abs=...)`；梯度 / 球面类用 `<= bound + 1e-3`（避免 abs=0 在 autograd 数值下误杀）
    - 签名/AST 级硬约束：`inspect.signature(...)` 检查参数名 + `_ast.parse(inspect.getsource(...))` 验证禁止符号（如 `w_i`）；源文件 grep 用 `Path(module.__file__).read_text()`
    - 算式约束必须**数值对账**（`pytest.approx(value, abs=...)` 直接验算 spec 声称的闭式常量）；源码 grep 只可用于**禁止性**约束（如 `distance.py` 不得出现 `w_i`）或常量删除验证（如 `_VORONOI_MVP_TABLE` 不复现），**不得**用于验证前向/闭式算式本身（见 Req "Forward Formula Numerical Verification"）
- **Post-archive 独立复核**：每次 `/opsx:archive` 后必须跑一次独立数值自洽性 + 双 spec 交叉校对，把 spec 声称的算式实际代入算一遍、与 spec 文本对账。grep 关键词命中不是充分条件。
- **GateGuard**：Edit / Write 前需提供 Gate Facts（file 路径、调用方、API 影响、用户原话）

## 4. Git Branch Architecture

- **`dev`**：日常工作分支，绝对无 merge commit（保持线性）
- **`main`**：关键版本存档点，仅 `dev → main` via `--no-ff`
- **`release`**：正式发版出埠口，`dev → release` via `--no-ff` + tag（必带 tag）

合并顺序：main 先、release 后（release 永远在 git tree 最前端）。每次合并后立即 `git checkout dev`，避免 dev HEAD 落在 merge commit 上。

## 5. MVP Hyperparameters（frozen 2026-08）

```
d_model = 1024, N_e = 16, k = 2, d_ffn = 2048, L = 4
Total ≈ 452M, Active ≈ 100M, d_ffn_dense = 4096
β ∈ [0.1, 32], γ_init ≈ -3.5（β_0 ≈ 1.0）
θ_Voronoi ≈ 52° > θ_{1/e} ≈ 20.36°（β = 16，球面几何自洽）
Phase ratios: 1/5/20/30/44% on 100K steps
```

## 6. Hard Constraints（违反前需 explicit ticket）

- ❌ 不要为 MVP 引入 custom CUDA / Triton kernel（PyTorch eager 即可）
- ❌ 不要把 `C_t` 写入 KV Cache（Decode 走 SRAM/Registers，0 bytes HBM）
- ❌ 不要引入 shared expert（pure geometric routing，A5-2 决议）
- ❌ 不要在 logit 中使用 `w_i`（A4-2 彻底剔除，混合权重 = Softmax 概率 `p_i`）
- ❌ 不要执行训练或跑 baseline（formalize-only destination）
- ❌ 不要绕过 OpenSpec 直接改 DecompMoE 行为
- ❌ 不要重写 wayfinder ticket 来"调和" spec 与 ticket 不一致——应改 spec 来对齐 ticket
- ❌ 写 pytest 断言不能只测功能不测原理。spec 中每个含具体数值的算式（FLOPs / 参数核算 / `θ_Voronoi` / `σ(γ)` 值 / 阈值 `1/(2·N_e)` / α 序列 / 相位覆盖范围）都必须有 `pytest.approx(..., abs=...)` 直接验算该数值与 spec 声称值对账。文字断言（"正确"、"合理"、"≈"无数字）不构成可验条款——这一条的直接经验：`fix-openspec-doc-bugs` archive 后独立复核才发现 5 条 spec-level 算式错误（如 FLOPs 0.26% 算错、γ_init ≈ −6.94 与 β_0 ≈ 1.035 自相矛盾）。

## 7. Out of Scope（OpenSpec 与 wayfinder 已锁）

- 训练执行 / baseline 结果 / 实验数据
- ArXiv 论文写作（实验 / ablation / 相关工作综述）
- Linear Attention / SSM / RNN 替代方案
- Checkpoint 兼容性 / dense → MoE 转换工具
- 数据集选型 / 数据 pipeline
- 推理引擎实现代码（spec 算法，code 留给后续 effort）

## 8. Wayfinder Arena Index

| Arena | 内容 | 关键 ticket |
|---|---|---|
| A0 | 命名 | A0-1 |
| A1 | 符号与术语 | A1-1 |
| A2 | 拓扑挂载 + Head 聚合 | A2-1, A2-2 |
| A3 | C 签名提取 + 生命周期 | A3-1, A3-2 |
| A4 | 距离度量 + 门控函数 | A4-1, A4-2 |
| A5 | 专家结构 + 超参 | A5-1, A5-2, A5-3 |
| A6a | 损失与数值稳定 | A6a-1, A6a-2 |
| A6b | 阶段调度与触发器 | A6b-1, A6b-2 |
| A7 | 推理增量 | A7-1, A7-2, A7-3 |
| A8 | baseline + 指标 + 可视化 | A8-1, A8-2, A8-3 |
| W | 自审 | WF-1, WF-2 |

> **2026-08-21 裁决**：wayfinder 不再是必改制品。本仓库以 OpenSpec 为唯一真相源；ticket 仅作历史决策记录（参考性、非约束性）。新变更一律走 OpenSpec 工作流，不再单独 patch tickets。

## 9. Current State（2026-08-24）

- ✅ OpenSpec 主 spec 已 archive：`openspec/specs/wayfinder/spec.md`（**31 Req / 69 Scen**，commit `f45a42c`）
- ✅ Skeleton spec 已 archive：`openspec/specs/decompmoe-skeleton/spec.md`（**22 Req / 76 Scen**）
- ✅ 9 changes archived（见 `openspec/changes/archive/`，含 `fix-math-consistency-audit-2026-08` 与 `2026-09-01-fix-math-consistency-audit-2026-08-apply`）
- ⏭ 代码层 delta：候选 `add-decompoe-mvp-module` / `add-decompoe-router`；`fix-math-consistency-audit-2026-08` 的代码层 apply 入口见 `apply-checklist.md`（17 项 spec-anchored 任务，按 spec 闭式常量驱动 TDD，**不得**用 `src` 输出反推测试）

## 10. Code Architecture & Module Map

> 阅读 `src/decompmoe/` 全部 14 个模块前，可先看本表建立"大图"。模块按几何路由链顺序排列（提取 → 距离 → 门控 → 专家 → 训练辅助）。

### 10.1 源码模块（`src/decompmoe/`）

| 模块 | 一句话职责 | 对应 Spec / Req |
|---|---|---|
| `__init__.py` | 包入口（无业务逻辑） | — |
| `contracts.py` | `typing.Protocol` 桩：`GeometricRouter` / `TerritoryHolder` / `BlockAdapter`；**硬约束**：无 `kv_cache_c`、无 `w_i` 参数 | Req 3, 4, 16, 17 |
| `config.py` | `MVPConfig` 数据类（d_model=1024, N_e=16, k=2, d_ffn=2048, L=4, β_min=0.1, β_max=32） | §5 frozen hyperparams |
| `sphere.py` | 球面工具（L2 normalize / antipode / geodesic 距离辅助） | Req 4 几何基础 |
| `beta.py` | `inverse_temperature(γ) = β_min + (β_max−β_min)·σ(γ)`；`MAX_GRAD_PER_C = β_max` 梯度上界 | Req 7 (A4-1) |
| `distance.py` | `squared_chord(C, c_i) = 1 − Cᵀc_i ∈ [0, 2]`；`logit = β·(Cᵀc − 1) ∈ [−2β, 0]`；**A4-2 签名无 `w_i`** | Req 7 (A4-1) |
| `extraction.py` | `extract_C(K, V)`：per-head 投影 → 球面归一 → cross-head mean → 最终球面归一；`O(d_c·d_k)` per token、stateless | Req 17 (A3-1, A7-2) |
| `gating.py` | `topk_mask_with_neg_inf` + `local_softmax`；非 Top-k 梯度严格为 0（闭式 `x_out = x + Σ p_i·Expert_i(x)` 由数值 stub 测试守护，见 Req "Forward Formula Numerical Verification"） | Req 8 (A4-2) |
| `experts.py` | `SwiGLU Expert`：`(SiLU(xW^g) ⊙ xW^u) W^d`，每专家 3·d_model·d_ffn 参数 | Req 5 (A5-1, A5-2) |
| `loss.py` | `L_total = L_CE + α·L_lb + λ(t)·L_sep`；α=0.01 固定；`L_lb = N_e·Σ f_i.detach()·P_i`；`L_sep = (‖CᵀC‖_F² − N_e)/(N_e(N_e−1))` | Req 9, 10 (A6a-1) |
| `safeguards.py` | 5 项：global grad clip / NaN 三级 escalation / **splitting resurrection** (clone + 0.85 协同衰减) / β saturation guard / loss spike defense | Req 11 (A6a-2) |
| `schedule.py` | 5 阶段 P0–P4（1/5/20/30/44% step）；β_max(t) 分段线性；P0 K-Means → P1-3 EMA → P4 projected SGD；Time-Driven 硬切 + State-Driven advisory | Req 12, 13 (A6b-1, A6b-2) |
| `metrics.py` | 4 实时指标（L_sep, R_H, S_load, UR）+ 4 离线（SP, D_chord, MCI, CG）；**`S_load = N_e · max_i f_i` 闭式** | Req 14, 15 (A8-2) |
| `viz.py` | 6 模块：3D PCA / D_chord 热力图 / 2D Voronoi / 轨迹动画 / TensorBoard / plantuml | Req 19 (A8-3) |

### 10.2 链式数据流（几何路由一次完整 forward）

```
x ─► Attention(K,V) ─► extract_C(K,V) ─► C_t ∈ S^{d_c−1}
                                        │
                                        ▼
                         gating_logits(C_t) = β·(C_tᵀc_i − 1)  (无 w_i)
                                        │
                                        ▼
                    topk_mask + local_softmax ─► p_i (top-k active set)
                                        │
                  x ─────────────────────┴──── Σ p_i·Expert_i(x)
                  │                                │
                  └───────── x_out = x + Δx ◄──────┘
```

**关键不变量**（贯穿整条链）：

1. `C_t ∈ S^{d_c−1}`（球面归一贯穿）
2. `logit ∈ [−2β_max, 0]`，`‖∂logit/∂C‖₂ ≤ β_max = 32`
3. `Σ_{i∈I_k} p_i ≡ 1`，非 Top-k 梯度严格 0
4. `C_t` 禁入 KV Cache（Decode 走 SRAM/Registers，0 bytes HBM）
5. 前向公式严格 `x_out = x + Σ p_i·Expert_i(x)`（数值 stub 测试守护，见 Req "Forward Formula Numerical Verification"）

### 10.3 测试文件映射（`tests/`）

| 测试文件 | 覆盖 spec 场景 | 关键硬约束测试 |
|---|---|---|
| `test_config.py` | hyperparams frozen | `MVPConfig().beta_initial == 1.0`, `k == 2` |
| `test_contracts.py` | Req 3, 4, 16, 17 协议形状 | `kv_cache_c` 不暴露、`w_i` 不入 `logit` |
| `test_sphere.py` | 球面归一 / 反极点 | `‖c‖₂ = 1`, `d(c, −c) = 2` |
| `test_beta.py` | Req 7 β 参数化 | σ(γ) endpoints、单调性、`MAX_GRAD_PER_C` 守恒 |
| `test_distance.py` | Req 7 距离 + logit | `d ∈ [0, 2]`、logit 范围、梯度上界 |
| `test_extraction.py` | Req 17 stateless 提取 | `C_t` 单位球面、stateless |
| `test_extraction_phase.py` | P0 K-Means → P1+ EMA 切换 | 阶段参数连续性 |
| `test_gating.py` | Req 8 top-k + softmax | −∞ sentinel、Σ p=1、greedy 公式字面 |
| `test_experts.py` | Req 5 SwiGLU 形状 | 参数计数 = 3·d_model·d_ffn |
| `test_loss.py` | Req 9, 10 L_lb / L_sep | `pytest.approx(..., abs=)` 对账 `α` / `N_e` / `f_i.detach()` |
| `test_safeguards.py` | Req 11 5 项 guard | `should_resurrect` 用 `1/(2·N_e)` 阈值 |
| `test_schedule.py` | Req 12, 13 阶段 | 1/5/20/30/44% 切点、β_max(t) 分段线性 |
| `test_metrics.py` | Req 14, 15 指标 | `S_load = N_e·max_i f_i` 闭式 |
| `test_viz_protocols.py` | Req 19 可视化接口 | Protocol shape（mock 即够，不真渲染） |

> 想要新增模块？先在 `openspec/specs/wayfinder/spec.md` 找到对应 Req / Scenario 锚点，**复用本表的列结构**补一行；测试文件命名严格 `test_<module>.py` + 函数 `test_<op>_<property>`。