# CLAUDE.md

Project-level instructions for **DecompMoE**. Merges with the user's global `~/.claude/CLAUDE.md` (think-before-coding, simplicity-first, surgical changes, goal-driven execution). When in doubt, the global guidelines win on behavior; this file wins on what is "in scope" and where the truth lives.

## 1. Project Identity

- **Canonical name**: DecompMoE (decomposed Mixture of Experts)
- **Documented alias**: GeoMoE（design prose only, never a code identifier）
- **Architecture**: Decoder-Only Llama + Post-FFN geometric routing
- **Hardware MVP**: 4070 8 GB single-GPU
- **Language**: 中文为主，数学符号用 LaTeX
- **OpenSpec capabilities**（peer 关系，无主从）：`wayfinder/` 主 spec（数学 + 算法约定）；`decompmoe-skeleton/` Python 形式化骨架（type stubs + 纯函数原语）；`governance/` CLAUDE.md 起源的 Requirements 专用（Source 反链 `CLAUDE.md`，其它反链 `wayfinder/tickets/`）

## 2. Truth Source Hierarchy

When sources disagree, consult in this order:

1. **`openspec/specs/**/spec.md`** — OpenSpec 真相源（三个 peer capability）
2. **`openspec/changes/archive/`** — historical change log
3. **Source 反链**（per capability）— 见 §3 lint 规则
4. **`wayfinder/map.md` + 23 tickets** — 决策 trail（参考性、非约束性；详见 §8 裁决）
5. **未归档变更** — `openspec/changes/<name>/`（工作区制品，权威性低于 spec）
6. **代码层** — `src/decompmoe/**` + `tests/**`

**规则**：想修改 DecompMoE 行为？先改 OpenSpec spec，不要直接动代码。

## 3. Workflow Conventions

- **Spec-level 变更**：`/opsx:propose` → review 制品 → `/opsx:apply`（含 archive）
- **`/opsx:archive` 前置条件**：门禁由 `uv run python scripts/run_gates.py --change <name>` 统一执行并判定 `exit 0`。该入口自动发现 `scripts/lint_*.py` 下**全部** lint。**本清单不逐条枚举 lint 脚本**——新增 lint 无需改本文件，清单与实际门禁因此不可能失步（`governance/spec.md` `req-gov-7`）。三件无法从代码推断的事：① `--specs` 那条**故意不传 `--strict`**（`run_gates.py` 有整段论证：会逼人重写成熟数学契约并重编 `req-N` anchor，连带破坏三个 capability、lint 与 tests 的交叉引用）；② 运行期间工作树被改动时报 `GATE RESULT INVALID` 并 **exit 2**（区别于报红的 exit 1，「通过」与「不知道」不可混读，`req-gov-8`）；③ 归档 anchor 须走「写账本 → 归档 → 比对 → 手术式补回 → 复测」，**禁止重跑 archive** 修复被吞的 anchor（`req-gov-10`，`uv run python scripts/run_gates.py anchor-ledger --write|--verify`）
- **Source 反链**（per capability，`scripts/lint_no_source_field_drift.py` 硬卡；`governance/spec.md` `req-gov-1`）：
  - `wayfinder/` / `decompmoe-skeleton/` 的 Requirement 必须含 `` `wayfinder/tickets/<ID>.md` `` 字面反链（pure ticket 或 `(historical, <原值>; superseded by <change> Decision N)` 均可），可附加 `` `change <name> design.md (Decision N)` ``
  - `governance/` 的 Requirement 必须含 `` `CLAUDE.md` `` 字面反链
  - 设计起源是 `CLAUDE.md` amendment 但 ticket lineage 不存在的，MUST 迁到 `governance/`，不得在 `wayfinder/` 用 "(historical, ...)" 硬贴
  - lint 三项结构检查：① 子串存在 ② 反链在 backtick 内 ③ 主反链是第一个 top-level item
  - ④ **存在性**：每个 Requirement 必须有顶格 `**Source:**` 字段，除非 `(capability, anchor_id)` 在 `SOURCE_EXEMPTIONS` 登记表内（`req-gov-11`）。登记表自身也受门禁——指向已不存在 Requirement、或该 Requirement 已补字段的条目同样报红，登记表不得静默增生
- **TDD 工作流**（每个子 task 入口 `/ecc:tdd-workflow`）：
  - **依赖**：`uv sync`（`uv.sources` 拉 `pytorch-cu130`，已设 `pythonpath = ["src"]`，无需 `pip install -e`）
  - **数学约束协议（强制）**：见 §6 第 8 条
  - **测试文件约定**：命名 `test_<被测算子>_<具体属性>`；随机性 `torch.manual_seed(0)` 作首行；签名/AST 硬约束用 `inspect.signature(...)` + `ast.parse(...)`
- **Post-archive 独立复核**：每次 `/opsx:archive` 后跑独立数值自洽性 + 双 spec 交叉校对，把 spec 声称的算式实际代入算一遍、与 spec 文本对账。grep 关键词命中不是充分条件
- **GateGuard**：Edit / Write 前提供 Gate Facts（file 路径、调用方、API 影响、用户原话）
- **解释器入口（强制）**：本仓命令一律经 `uv run` 执行，测试一律 `uv run pytest`——单文件 `uv run pytest tests/test_x.py`，单函数 `uv run pytest tests/test_x.py::test_y -k "..."`。裸 `python -m pytest` 落到系统解释器（无 pytest，必失败）。唯一例外是 `scripts/` 下可 0 环境执行的脚本：它们只依赖标准库，可直接 `python scripts/<name>.py`。**`run_gates.py` 不在此例外内**——它以 `sys.executable -m pytest` 转发 pytest，裸 `python` 启动会让门禁在一个与代码无关的地方报红（lint 全过仍 `GATE FAIL`），必须 `uv run python scripts/run_gates.py`（内层循环可加 `--skip-pytest`，但那不是完整门禁结果）

## 4. Git Branch Architecture

- **`dev`**：日常工作分支，绝对无 merge commit（保持线性）
- **`main`**：关键版本存档点，仅 `dev → main` via `--no-ff`
- **`release`**：正式发版出埠口，仅 `dev → release` via `--no-ff` + tag（必带 tag）

合并顺序 main 先、release 后（release 永远在 git tree 最前端）；每次合并后立即 `git checkout dev`，避免 dev HEAD 落在 merge commit 上。

> **本节通道当前未启用**：`main` 的 root 是只含 `.gitignore` 与 `LICENSE` 的 Initial commit `051f247`，与 `dev` **无共同祖先**（`git merge-base main dev` 退出码非零），故 `dev → main` 存档通道在拓扑对齐前**不可执行**；`release` 分支不存在且 tag 为空，故出埠通道与「必带 tag」义务从未被触发。本节为 aspirational 规范。
>
> 修远端默认分支**必须向远端取证**（GitHub API / `git ls-remote --symref origin HEAD` / `gh repo view` 三路复验）。`git remote set-head origin dev` 只写本地 remote-tracking 缓存，**不是修法**——上一轮曾用它「修复」而远端纹丝未动，执行后本地与远端事实相反。判据是**是否向远端取证**，不是命令是否 `exit 0`。

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
- ❌ 写 pytest 断言不能只测功能不测原理：spec 中每个含具体数值的算式必须按数值类型二分直接对账（浮点闭式 `pytest.approx(..., abs=...)`、整数闭式 bare `==`）——完整协议与禁止项见 §3「数学约束协议」；文字断言不构成可验条款
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

> **2026-08-21 裁决**：wayfinder 不再是必改制品。本仓库以 OpenSpec 为唯一真相源；ticket 为历史决策记录（参考性、非约束性）。新变更一律走 OpenSpec 工作流，不再单独 patch tickets。
>
> **「非约束性」的确切含义**（cycle-7 audit-verification meta-洞察 boundary clarification；规范形式见 `openspec/specs/governance/spec.md` `req-gov-4` Ticket Advisory Boundary — Stale Contamination Monitoring）：advisory 限定的是**可否偏离 spec**，**不**限定「不得被维护」。故 ticket stale 仍可能经三条通道污染 `src/`——(i) `MVPConfig` 默认值直接抄 ticket 数值；(ii) tests `assert == stale_value` 锁死传染；(iii) 读者复制 stale 数值而非 spec canonical。**监控义务不因传染链已断而豁免**，audit-verification loop 须周期复核 ticket ↔ spec ↔ `src/` 三角漂移；修复协议三步（ticket 端 `(historical, …)` 标注、`src/` 默认值同步 spec canonical、tests 迁移 `pytest.approx(spec_value, abs=...)`）见 req-gov-4。

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

> **实现状态**：上图是 **spec 级算法，不是可运行调用路径**。`gating_logits` 全仓仅存在于 `contracts.py` 的 `typing.Protocol` 存根（无函数体），`distance.logit` 在 `src/` 内无调用方。本仓是 formalize-only 目的地（§7）：不要试图把它接线，也不要把「`logit` 无人调用」当成缺陷去修。

**关键不变量**（贯穿整条链）：

1. `C_t ∈ S^{d_c−1}`（球面归一贯穿）
2. `logit ∈ [−2β_max, 0]`，`‖∂logit/∂C‖₂ ≤ β_max = 32`
3. `Σ_{i∈I_k} p_i ≡ 1`，非 Top-k 梯度严格 0
4. `C_t` 禁入 KV Cache（Decode 走 SRAM/Registers，0 bytes HBM）
5. 前向公式严格 `x_out = x + Σ p_i·Expert_i(x)`（数值 stub 测试守护，见 Req "Forward Formula Numerical Verification"）
