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
- **`/opsx:archive` 前置条件**：门禁由 `python scripts/run_gates.py --change <name>` 统一执行并判定 `exit 0`（`<name>` = 被归档的 change）。该入口自动发现 `scripts/lint_*.py` 下**全部** lint，另跑 `openspec validate --specs --strict`、被归档 change 自身的 `--type change --strict`、anchor 覆盖检查与 `pytest`；发现数为 0 时直接报 FAIL。**本清单不逐条枚举 lint 脚本**——新增 lint 无需改本文件，清单与实际门禁因此不可能失步（治理条款 `governance/spec.md` `req-gov-7`）。`run_gates.py` 在运行前后各采样 `HEAD` 与工作树摘要，不一致时输出 `GATE RESULT INVALID` 并 **exit 2**（区别于报红的 exit 1），「通过」与「不知道」不可混读（`req-gov-8`）。归档 anchor 必须走「写账本 → 归档 → 比对 → 手术式补回 → 复测」，**禁止重跑 archive** 修复被吞的 anchor（`req-gov-10`，用 `python scripts/run_gates.py anchor-ledger --write|--verify`）。
- **Source 反链**（per capability，`scripts/lint_no_source_field_drift.py` 硬卡；治理条款 `governance/spec.md` `req-gov-1`）：
  - `wayfinder/` / `decompmoe-skeleton/` 的 Requirement：必须含 `` `wayfinder/tickets/<ID>.md` `` 字面反链（pure ticket 或 `(historical, <原值>; superseded by <change> Decision N)` 标注均可），允许附加 `` `change <name> design.md (Decision N)` ``
  - `governance/` 的 Requirement：必须含 `` `CLAUDE.md` `` 字面反链
  - 设计起源是 `CLAUDE.md` amendment 但 ticket lineage 不存在：MUST 迁到 `governance/`，不得在 `wayfinder/` 用 "(historical, ...)" 硬贴
  - lint 三项结构性检查（每项独立报错）：① 子串存在；② 反链必须在 backtick 内；③ 主反链必须是第一个 top-level item（paren-depth-aware、code-span atomic split）
  - ④ **存在性**：每个 Requirement 必须有顶格 `**Source:**` 字段。缺失即红，除非 `(capability, anchor_id)` 在 `SOURCE_EXEMPTIONS` 登记表内（`governance/spec.md` `req-gov-11`）。登记表条目本身也受门禁：指向已不存在的 Requirement、或该 Requirement 已补上字段的条目，同样报红——登记表不得静默增生。`SOURCE_LINE_RE` 接受缩进 / `>` 引用 / 有序列表前缀，`body` 按 **match 结束偏移**切片（改回定长切片会让 `> **Source:**` 切出 `ource:**`）
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

> **当前状态（2026-10-04 实测）——本节通道未启用**：本仓 `main` 的 root 是只含 `.gitignore` 与 `LICENSE` 的 Initial commit `051f247`，与 `dev` 无任何共同祖先（`git merge-base main dev` 无输出且退出码非零），故 `dev → main` 存档通道在拓扑对齐前**不可执行**；`release` 分支在 `for-each-ref` / `git tag` / `ls-remote` / reflog / `packed-refs` 五路均不存在，仓库 tag 数本地与远端皆为 0，故 `dev → release` 出埠通道与「必带 tag」义务**从未被触发**。三分支架构保留为 aspirational 规范，本节不预设将来是否建立 `release`。
>
> **远端默认展示分支（2026-10-05 已修复）**：此前 `origin` 的远端 HEAD 指向 `main`，从 GitHub 仓库首页进入的人看到的是一棵与开发线无关的单提交空树。已执行 `gh repo edit LoopyBrainie/DecompMoE --default-branch dev`，三路复验（GitHub API `defaultBranchRef.name = dev` / `git ls-remote --symref origin HEAD` → `ref: refs/heads/dev` / `gh repo view`）确认生效，本地镜像 `refs/remotes/origin/HEAD` 已刷新为 `origin/dev`。**注意 `git remote set-head origin dev` 本身不是修法**——它只写本地 remote-tracking 缓存 ref；上一轮曾用它「修复」而远端其实纹丝未动（`ls-remote` 仍返回 `refs/heads/main`），且执行后本地与远端事实相反，必须回滚。判据是**是否向远端取证**，不是命令是否 `exit 0`。本条只改默认展示指针：`release` 仍不存在、tag 本地与远端皆为 0、`main` 与 `dev` 仍无共同祖先（`git merge-base main dev` 退出码非零）、`main` root 仍是 `051f247`、远端 heads 仍是 4 条。

## 5. MVP Hyperparameters（frozen）

```
d_model = 1024, N_e = 16, k = 2, d_ffn = 2048, L = 4
Total ≈ 452M, Active ≈ 100M, d_ffn_dense = 4096
β ∈ [0.1, 32], γ_init ≈ -3.5（β_0 ≈ 1.035）
θ_Voronoi(16,16) ≈ 67.24° (1.1735 rad) > θ_{1/e} ≈ 20.36°（β = 16, d_c=16, 球面几何自洽）
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
>
> **「非约束性」的确切含义**（`openspec/specs/governance/spec.md` 的 `req-gov-4`，Ticket Advisory Boundary — Stale Contamination Monitoring，clause (1)）：verbatim「this is the ONLY meaning of "advisory"」——ticket 文本可不经 amendment 偏离 spec（**不得推翻 spec**），但该 advisory 范围 verbatim「does NOT extend to claims about ticket-side information having no downstream effect on `src/` or `tests/`」。因此「非约束」限定的是**可否偏离 spec**，**不**限定「不得被维护」：下方三传染通道的监控义务与 `(historical, …)` 标注义务不受此限。

> **2026-09-19 边界补充**（cycle-7 audit-verification meta-洞察 boundary clarification，per `openspec/specs/governance/spec.md` `req-gov-4` 显式建议）：ticket 是 advisory non-binding，但 **advisory ≠ 无影响**。ticket stale 仍可能通过三传染通道污染 `src/`：(i) MVPConfig 默认值直接抄 ticket 数值（实证：`commit adf41ef` 2026-09-19 cycle-5/6/7 batch fix 已关闭 `MVPConfig.beta_initial: 1.0 ← ticket A4-1 β_0 ≈ 1.0` 单向污染）；(ii) tests `assert == stale_value` LOCKS 传染（同 `adf41ef`：`tests/test_beta.py::test_beta_param_init_default` 原 `assert MVPConfig().beta_initial == 1.0` 已迁移 `pytest.approx(expected, abs=1e-3)`）；(iii) reader-ticket-not-spec 复制 stale 数值（cycle-9 worst-case：`wayfinder/tickets/A6a-2.md` 历史 `f_i^avg < 1/128` vs spec `1 / (2·N_e)` 参数化，`src/decompmoe/safeguards.py::_dead_expert_threshold` 已用 spec 形式）。**监控义务**：audit-verification loop 须周期性 check ticket ↔ spec ↔ `src/` 三角漂移，**传染链已断**（per `adf41ef` cycle-5/6/7 + cycle-12 `commit d239f57` 2026-09-21 + cycle-13 `commit f077be8`）不豁免监控——剩余 cycle-9/12/13 ticket-stale family 仍需周期复核。**修复协议 (a)+(b)+(c) 三步**：ticket 端 `(historical, <原值>; superseded by spec req-N L### via <change> Decision M)` 注释；`src/` 默认值同步 spec canonical；tests `pytest.approx(spec_value, abs=...)` 迁移（遵循 `CLAUDE.md` §6 第 8 条 + `req-gov-1`）。**形式化约束**：上述 4 条 obligations 由 `openspec/specs/governance/spec.md` req-gov-4 形式化，audit-verification loop 可对照该 Requirement 复核。

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