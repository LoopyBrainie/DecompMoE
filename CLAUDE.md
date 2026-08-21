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
- **TDD 工作流**：
  - `uv sync` 安装依赖（pyproject.toml 用 `uv.sources` 拉 `pytorch-cu130`）
  - `uv run pytest tests/` 跑全部；`uv run pytest tests/test_xxx.py::name -k expr` 跑单测
  - pyproject.toml 已设 `pythonpath = ["src"]`，无需 `pip install -e`
  - **断言必须约束数学原理**（见 §6 Hard Constraints）
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

## 9. Current State（2026-08-21）

- ✅ OpenSpec 主 spec 已 archive：`openspec/specs/wayfinder/spec.md`（**25 Req / 52 Scen**，commit `41ac06b`）
- ✅ Skeleton spec 已 archive：`openspec/specs/decompmoe-skeleton/spec.md`（**20 Req / 58 Scen**）
- ✅ 4 changes archived：`polish-wayfinder-spec` + `introduce-wayfinder-decompoe-spec` + `add-decompoe-skeleton-with-tdd-tests` + `fix-openspec-doc-bugs`
- ⏭ Post-archive 独立复核发现 5 条 spec-level oversights（FLOPs 0.26% 算错、Phase 0 归一化用词、grep Scenario 分层表述、`γ_init ≈ −6.94` 与 `β_0 ≈ 1.035` 自相矛盾、恒真式断言），下一 change `fix-spec-doc-oversights` 合并修
- ⏭ 代码层 delta：候选 `add-decompoe-mvp-module` / `add-geometric-router`