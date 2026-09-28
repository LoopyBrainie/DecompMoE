# Proposal

## Why

`decompmoe-skeleton` req-6 的 SHALL 句在 commit `b23f0e5`（2026-09-27）收紧容差时被改成了**字面不可满足**的状态：同一句里既要求 `canonical_voronoi_angle(N_e=16, d_c=16)` 返回 4 位小数的 prose literal `≈ 1.1735 rad`，又要求它落在 `abs=1e-6` 之内。实测实现输出 `1.1735482746999482`，与该 literal 相差 `4.827470e-05` —— **超出 `1e-6` 达 48.27 倍**。`N_e=64` 同理（`6.833574e-06`，超 6.83 倍）。任何实现都无法同时满足这两条约束，Requirement 事实上处于空转状态。

同一 change 引入的 `wayfinder` 侧则存在**反向的错误授权**：`spec.md:240` / `:241` 声称 4dp↔4dp 的 prose 舍入差 `5.94e-5 rad`「lies within the `< 1e-4 rad` test tolerance permitted by req-gov-1 §2」，但 `governance/spec.md:15` 的 §2 原文**根本没有指定任何数值容差**，只要求「tolerance matching the closed-form computation's actual precision」。这是把不存在的授权当成了依据；而若把 `1e-4` 机械替换为 `1e-6`，又会反向造假（`5.94e-5` 比 `1e-6` 大 59 倍）。

两者属**同族缺陷的第二次出现**：`3dd1104`（2026-09-25）删光了 Voronoi 字面量留下 `X == X` 恒等断言，`b23f0e5` 恢复守护时又把容差绑到了错误的 literal 精度层级。真正的规则（6dp 测试 literal 与 4dp canonical spec literal 之分）一直正确地写在 `governance/spec.md:17`，只是**引用方**没有引用对。

## What Changes

### In scope

| Audit 项 | 位置 | 变更 |
|---|---|---|
| **A1** | `openspec/specs/decompmoe-skeleton/spec.md:98` | SHALL 句中的 `abs=1e-6` 改绑 **6 位小数 literal**（`1.173548` / `1.020506`）；`≈ 1.1735 rad` / `≈ 1.0205 rad` 显式降级为 4dp prose display，并显式声明 **MUST NOT** 与 `abs=1e-6` 配对，改由 `round(θ, 4) ==` / `round(math.degrees(θ), 2) ==`（bare `==`）守护 |
| **A5** | `openspec/specs/wayfinder/spec.md:240` | 删除对 `req-gov-1 §2` 的虚假授权引用与「`< 1e-4 rad` test tolerance」管辖声明；改述为「prose-to-prose 舍入差，**不受任何测试容差管辖**」，并指明实际守护（`round(·,4) ==` bare `==` + `pytest.approx(1.173548, abs=1e-6)`），同时点明 §2 本身不规定任何数值容差、`1e-6` 来自 §3 |
| **A5'** | `openspec/specs/wayfinder/spec.md:241` | 同款改写（`1.020506` / `1.0205` / `58.47` 一组） |

净效果：3 行长散文单行的替换（3 删 3 增），**不引入任何新数字** —— `1.173548` / `1.020506` / `1.165848` 已在 `governance/spec.md:17` 定义，`4.83e-5` 与 `48×` 是本 change 的实测值。

### Out of scope

- **`openspec/specs/governance/spec.md` 零改动**。`governance:17` 的 6dp/4dp disambiguation 段与 `governance:53` 的禁宽条款（angle claim 用 `abs=1e-4` 或更宽须审计）**本身正确且完整**；`skeleton L98` 未引用它、wayfinder L240/L241 误引 §2，都是**引用方缺陷**。规则正确时只修引用方（`CLAUDE.md` §3 surgical）。
- **`wayfinder/spec.md:235` 零改动**。该行的 `4.15e-7` / `1.43e-9` residual 数值经复核正确，且已自带指向 `req-gov-1 §4` 的 frame-disambiguation 交叉引用。
- **不新增防回归测试或 lint 规则**（显式决策）。「扫 `openspec/specs/**` 检测 literal 精度 ≤ 容差的不匹配声明」需新增 lint 脚本并接入 gate，属治理条款级扩展，超出本次措辞修正 scope。记为 future scope。
- **不改 `fix-review-findings-voronoi-precision-and-lineage`**。该 change 全部 task 已 `[x]` 且带完整 `Deviation record`；A1 溯源到其 task `1.3.1`，但追加等于重开已完成 task，故另开 follow-up change。
- **不触碰并行 session 的 change 目录**（`2026-09-28-fix-a2-a3-a4-residual-precision-claims` 等，均 untracked）。
- **两份被争抢的文本**（理由见 `design.md` Decision 7）：`governance` req-gov-1 L20/L21 的「60 subintervals / < 1 ppm」措辞，以及 `wayfinder` L233 + L274-276 的未标参考系 `< 1e-9` 声明。二者分别被 `a2-a3-a4` 与本 change 同时占用 full-block delta，叠第三份会在 archive 时静默覆盖。分析已完成、替换措辞已预先核实，作为**挂起项**记录在 `tasks.md` §9，留给后继 change 做机械替换。

### 2026-09-28 code review 后的范围扩展（P1–P5）

Code review 另报 6 项缺陷（P1–P6），全部经 parent agent 独立复算确认。其中落在本 change 无冲突区域的部分**并入本 change**——P1/P3/P5 位于 `decompmoe-skeleton` req-6，而本 change 已有该 Requirement 的 full-block `MODIFIED` delta，另开 change 会产生两份竞争 delta 并在 archive 时互相覆盖：

| Finding | 位置 | 修复 |
|---|---|---|
| **P1** | `decompmoe-skeleton:114` | 声称 `< 1e-14` 实际 `1.1643e-14`（N_e=16）不满足；引用的 guard 实为 `< 1e-9`；`1e-14` 在 `tests/` 中零出现。改为陈述实测值 + 指明真正被钉住的界 |
| **P2** | `src/decompmoe/sphere.py:58` + `skeleton:116` | 删除从未被读取的 `n: int = 60` 死参数（6 个调用点均不传）；把「60-segment」改为「single 8-point Gauss–Legendre panel，无分段」 |
| **P3** | `skeleton:116` | `< 1 ppm` 的字面读法下不成立——函数自身相对误差为 `6.63 ppm`。改为显式限定该界作用于 **θ 偏差**，并列出函数级数值 |
| **P4** | `src/decompmoe/sphere.py` docstring | 「accurate to ~1e-12」在 MVP 处即为假（实测绝对误差 `8.29e-07`）。改为实测值，并记录 `signature_dim` 声明域 > 验证域的实测精度带 |
| **P5** | `skeleton:102` / `:106` | 两个 Scenario 仍以 "equals `≈ 1.1735 rad`" 复述 4dp literal。改用与 L98 一致的双层守护措词 |
| **P6** | `wayfinder:233` / `:274-276` | **挂起**（req-11 被两份 change 争抢），见 `tasks.md` §9.2 |

## Capabilities

### New Capabilities

（无。本 change 不引入新 capability。）

### Modified Capabilities

- `decompmoe-skeleton`: Requirement **req-6（Voronoi Self-Consistency Threshold）** 的数值声明与容差绑定关系变更 —— `abs=1e-6` 唯一绑定 6dp 测试 literal，4dp canonical prose literal 改由 bare `==` 守护。
- `wayfinder`: Requirement **req-11（4070 MVP Hyperparameter Set）** 的 `Display precision note` 两条 bullet 变更 —— 移除对 `req-gov-1 §2` 的虚假容差授权引用，改为陈述 prose 舍入差不受测试容差管辖并指明真实守护。

（`governance` **不在** Modified 列表内 —— 见 Out of scope。）

## Impact

- **Affected files（apply 阶段总账）**：
  - `openspec/specs/decompmoe-skeleton/spec.md` — edit L98（req-6 body，绑定重定向）+ L102 / L106（Scenario 守护措词）+ L114 / L116（residual 与 quadrature 描述）
  - `openspec/specs/wayfinder/spec.md` — edit 2 行（L240、L241，req-11 `Display precision note`）
  - `src/decompmoe/sphere.py` — 删 `_betainc_regularized` 的死参数 `n: int = 60`；两处 docstring 的精度声明改为实测值
  - `openspec/changes/2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding/` 下的 4 类制品（proposal / specs ×2 / design / tasks）+ `.openspec.yaml` — create
- **代码 / API / 依赖**：**行为零变更**。`canonical_voronoi_angle` 的返回值、`_betainc_regularized` 的数值输出、公开 API 签名均不变；删除的 `n` 是从未被读取的私有参数，且全部 6 个调用点（`sphere.py` 1 处 + `tests/test_sphere.py` 5 处）均不传它。无新增依赖。
- **测试**：`uv run pytest -q` 基线 `204 passed` 必须保持——本 change **零新增/零修改测试**，删除死参数后调用方不受影响。
- **Lint gate**：`lint_no_dead_defensive.py` 与 `lint_no_source_field_drift.py` 必须保持 `exit=0`（`CLAUDE.md` §3 archive 前置条件）。本次不修改 lint 脚本，也不修改任何 `**Source:**` 反链字段。
- **Anchor coverage**：wayfinder 36/36、skeleton 23/23、governance 4/4 = 100%，必须不变（不新增/删除 Requirement，只改 body 措辞）。
- **Git**：单 commit on `dev`（`CLAUDE.md` §4）。

## Source back-link

- **`CLAUDE.md`** §3（source 反链 + lint gate + TDD 工作流）、§5（`θ_Voronoi(16,16) ≈ 67.24° (1.1735 rad)` 的 4dp 冻结形式 —— 本 change 的 4dp display 层不得解冻）、§6 第 8 条（浮点闭式必须 `pytest.approx(..., abs=...)` 直接对账）
- change `fix-review-findings-voronoi-precision-and-lineage` — `tasks.md` task `1.3.1`（A1 的直接引入点：把 `decompmoe-skeleton` L98 的 `abs=1e-4` 改为 `abs=1e-6` 而未同步 literal）
- commit `b23f0e5`（2026-09-27 18:58:09）— A1 引入 commit
- `openspec/specs/governance/spec.md` req-gov-1 §2（float closed-form 断言形式，本 change 据以判定「§2 不规定数值容差」）、§3（bisection Voronoi angle 的 `abs=1e-6` 权威条款 + 6dp/4dp disambiguation 原文）、§4（residual frame 消歧义）、§5（`f"actual="` 强制）
- change `3dd1104` 相关历史（同族缺陷第一次出现：删除 Voronoi 字面量留 `X == X` 恒等断言）
