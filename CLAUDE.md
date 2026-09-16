# CLAUDE.md

Project-level instructions for **DecompMoE**. Merges with the user's global `~/.claude/CLAUDE.md` (think-before-coding, simplicity-first, surgical changes, goal-driven execution). When in doubt, the global guidelines win on behavior; this file wins on what is "in scope" and where the truth lives.

## 1. Project Identity

- **Canonical name**: DecompMoE (decomposed Mixture of Experts)
- **Documented alias**: GeoMoE (use only in design prose, never as a code identifier)
- **Architecture**: Decoder-Only Llama + Post-FFN geometric routing
- **Hardware MVP**: 4070 8 GB single-GPU
- **Language**: 中文为主，数学符号用 LaTeX
- **OpenSpec capabilities**（peer 关系，无主从）:
  - `wayfinder/` — 主 spec（数学 + 算法约定）
  - `decompmoe-skeleton/` — Python 形式化骨架（type stubs + 纯函数原语）
  - `governance/` — CLAUDE.md 起源的 Requirements 专用；Source 反链 `CLAUDE.md`，其它反链 `wayfinder/tickets/`

## 2. Truth Source Hierarchy

When sources disagree, consult in this order:

1. **`openspec/specs/**/spec.md`** — OpenSpec 真相源（三个 peer capability）
2. **`openspec/changes/archive/`** — historical change log
3. **Source 反链**（per capability）— 见 §3 lint 规则
4. **`wayfinder/map.md` + 23 tickets** — 决策 trail（参考性、非约束性；详见 §8 裁决）
5. **代码层** — `openspec/changes/<name>/proposal.md`

**规则**：想修改 DecompMoE 行为？先改 OpenSpec spec，不要直接动代码。

## 3. Workflow Conventions

- **Spec-level 变更**：`/opsx:propose` → review 制品 → `/opsx:apply`（含 archive）
- **`/opsx:archive` 前置条件**：lint gate 必须 `exit=0`（同时跑 `python scripts/lint_no_dead_defensive.py` 与 `python scripts/lint_no_source_field_drift.py`），避免 archived change 留下 lint 报红（参见 `db14222` 修复的 12f673d 漏洞）。`lint_no_source_field_drift.py` 按 capability 区分 Source 反链规则，仍为纯内容子串检查（无豁免注册表、无 CLI 开关、无环境变量）。
- **Source 反链**（per capability，`scripts/lint_no_source_field_drift.py` 硬卡；治理条款 `wayfinder/spec.md` req-33）：
  - `wayfinder/` / `decompmoe-skeleton/` 的 Requirement：必须含 `` `wayfinder/tickets/<ID>.md` `` 字面反链（pure ticket 或 `(historical, <原值>; superseded by <change> Decision N)` 标注均可），允许附加 `` `change <name> design.md (Decision N)` ``
  - `governance/` 的 Requirement：必须含 `` `CLAUDE.md` `` 字面反链
  - 设计起源是 `CLAUDE.md` amendment 但 ticket lineage 不存在：MUST 迁到 `governance/`，不得在 `wayfinder/` 用 "(historical, ...)" 硬贴
  - lint 三项结构性检查（每项独立报错）：① 子串存在；② 反链必须在 backtick 内；③ 主反链必须是第一个 top-level item（paren-depth-aware、code-span atomic split）
- **TDD 工作流**（每个子 task 入口：`/ecc:tdd-workflow` → 红 / 绿 / 重构 + 数学约束）：
  - **依赖**：`uv sync`（pyproject.toml 用 `uv.sources` 拉 `pytorch-cu130`，已设 `pythonpath = ["src"]`，无需 `pip install -e`）
  - **数学约束协议（强制）**：spec 中每个含具体数值的算式必须有 `pytest.approx(..., abs=...)`（浮点闭式）或精确 `==`（整数闭式）直接对账——按数值类型二分（详见 `governance/spec.md` req-gov-1）：
    - **整数闭式**：**bare `==`**（禁止 `pytest.approx(..., abs=0)`，其 `rel=1e-12` 默认随量级缩放，违背"钉值零容差"意图）
    - **浮点闭式**：`pytest.approx(value, abs=...)`，bisection Voronoi 一律 `abs=1e-6`
    - 文字断言（"正确"/"合理"）不构成可验条款；失败信息必带 `f"actual={...}"` 内嵌值
  - **测试文件约定**：函数命名 `test_<被测算子>_<具体属性>`；随机性 `torch.manual_seed(0)` 作首行；签名/AST 硬约束用 `inspect.signature(...)` + `_ast.parse(...)`
- **Post-archive 独立复核**：每次 `/opsx:archive` 后必须跑一次独立数值自洽性 + 双 spec 交叉校对，把 spec 声称的算式实际代入算一遍、与 spec 文本对账。grep 关键词命中不是充分条件。
- **GateGuard**：Edit / Write 前需提供 Gate Facts（file 路径、调用方、API 影响、用户原话）

## 4. Git Branch Architecture

- **`dev`**：日常工作分支，绝对无 merge commit（保持线性）
- **`main`**：关键版本存档点，仅 `dev → main` via `--no-ff`
- **`release`**：正式发版出埠口，`dev → release` via `--no-ff` + tag（必带 tag）

合并顺序：main 先、release 后（release 永远在 git tree 最前端）。每次合并后立即 `git checkout dev`，避免 dev HEAD 落在 merge commit 上。

## 5. MVP Hyperparameters（frozen）

```
d_model = 1024, N_e = 16, k = 2, d_ffn = 2048, L = 4
Total ≈ 452M, Active ≈ 100M, d_ffn_dense = 4096
β ∈ [0.1, 32], γ_init ≈ -3.5（β_0 ≈ 1.0）
θ_Voronoi(16,16) ≈ 67.24° (1.1736 rad) > θ_{1/e} ≈ 20.36°（β = 16, d_c=16, 球面几何自洽）
Phase ratios: 1/5/20/30/44% on 100K steps
Phase boundaries (cumulative cutpoints): 1 K / 6 K / 26 K / 56 K / 100 K
```

## 6. Hard Constraints（违反前需 explicit ticket）

- ❌ 不要为 MVP 引入 custom CUDA / Triton kernel（PyTorch eager 即可）
- ❌ 不要把 `C_t` 写入 KV Cache（Decode 走 SRAM/Registers，0 bytes HBM）
- ❌ 不要引入 shared expert（pure geometric routing，A5-2 决议）
- ❌ 不要在 logit 中使用 `w_i`（A4-2 彻底剔除，混合权重 = Softmax 概率 `p_i`）
- ❌ 不要执行训练或跑 baseline（formalize-only destination）
- ❌ 不要绕过 OpenSpec 直接改 DecompMoE 行为
- ❌ 不要重写 wayfinder ticket 来"调和" spec 与 ticket 不一致——应改 spec 来对齐 ticket
- ❌ 写 pytest 断言不能只测功能不测原理：spec 中每个含具体数值的算式必须有 `pytest.approx(..., abs=...)`（浮点闭式）或精确 `==`（整数闭式）直接对账——按数值类型二分（详见 `governance/spec.md` req-gov-1）；整数闭式必须 bare `==`，禁止 `pytest.approx(..., abs=0)`；浮点闭式 `pytest.approx(value, abs=...)`（bisection Voronoi 一律 `abs=1e-6`）；文字断言不构成可验条款
- ❌ spec anchor 不全：`wayfinder/spec.md` 与 `decompmoe-skeleton/spec.md` 的每个 Requirement MUST 在首行设独立 anchor `<a id="req-N"></a>`，**100% 覆盖**；缺 anchor 等价于 spec 未交付，无法被反链 lint 通过
- ❌ 用 policy + code-first 论证 close 一个数学语义选择（如 `should_resurrect` 的 per-step vs avg-window 触发器）：必须给出数学 derivation（单调性蕴含链 + worked counterexample），由数值闭式测试守护

## 7. Out of Scope（OpenSpec 与 wayfinder 已锁）

- 训练执行 / baseline 结果 / 实验数据
- ArXiv 论文写作（实验 / ablation / 相关工作综述）
- Linear Attention / SSM / RNN 替代方案
- Checkpoint 兼容性 / dense → MoE 转换工具
- 数据集选型 / 数据 pipeline
- 推理引擎实现代码（spec 算法，code 留给后续 effort）

## 8. Wayfinder Arena Index

> **2026-08-21 裁决**：wayfinder 不再是必改制品。本仓库以 OpenSpec 为唯一真相源；ticket 仅作历史决策记录（参考性、非约束性）。新变更一律走 OpenSpec 工作流，不再单独 patch tickets。

## 9. Key Data Flow（几何路由一次完整 forward）

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