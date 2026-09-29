# 修复 `voronoi_angle` 测量层语义（反解缺陷 + 口径缺陷）

## Why

`src/decompmoe/sphere.py::voronoi_angle` 自 commit `af91717`（2026-08-22）起同时带有两个缺陷，2026-09-29 的评审轮如实记录了它们但**刻意推迟**修复（`archive/2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity` proposal.md 移交项 1-2）。本 change 认领并关闭该移交项。

| 缺陷 | 位置 | 事实（实测，非推断） |
|---|---|---|
| **1. 反解错误** | `sphere.py:237` | 平均弦长 `c` 被喂进只接受 versine `1−cos θ` 的槽位，算 `arccos(1 − c)` 而非 `arccos(1 − c²/2)`。采样网格上误差 `+24.3416° / +31.4300° / +30.0000° / +17.0586° / +8.7253°`（真值 10/45/60/120/150°） |
| **1b. docstring 数值表述被证伪** | `sphere.py:203-204` | 原文称误差「over the whole range +8.7°…+31.4°，peaking near 45°」。180 万点密扫证伪：真峰值 `+31.5868°` 在 `θ* = 2·arcsin(1/3) = 38.9420°`，且误差**两端归零**（`e(180°)=0`、`e(0.5°)=+7.07°`）。`+8.7…+31.4` 只是那 5 个采样点的极值 |
| **2. 平均口径错误** | `sphere.py:232-236` | 对全部 `i<j` 成对取平均。crosspolytope(32)（精确等面积）上返回 `115.6651°`，canonical 是 `62.5445°` |

**为什么「换成最近邻内切半径」不是正解**（实测排除，非论证排除）：最近邻内切半径与 canonical 在数学上不可通约——`canonical` 解的是**球冠面积**方程 `½·I_{sin²θ}((d_c−1)/2, ½) = 1/N_e`，内切半径是**到最近刻面距离**。随机点集 `d_c=16` 下比值恒在 ~48% 且不随 `N_e → ∞` 收敛（`N_e = 16/64/256/1024/4096` → `48.9/47.6/48.6/48.0/48.2%`）。crosspolytope 胞腔面积经 4×10⁶ 采样实测 `0.031250 = 1/32`（等面积成立），但半径 45° 的球冠面积仅 `0.000751`，差 41 倍——半腔腔质量位于最近刻面之外，内切半径把它全丢掉了。

因此采用**逐胞腔等效球冠半径**：`θ̂ = (1/N_e)·Σ_i G⁻¹(A_i)`，使测量层与 canonical 真正可通约，`D := canonical − θ̂` 成为单侧、有界、在等面积理想点取零的偏离度量——这是 Req 11 中 "self-consistency" 唯一站得住的数学形式。

## What changes

### 1. `src/decompmoe/sphere.py`

- 抽出 `_cap_area(θ, d_c)`（球冠面积函数 `G`，含 `θ > π/2` 反射分支）与 `_cap_radius(area, d_c)`（`G` 在 `(0, π)` 上的二分反解）。
- `canonical_voronoi_angle` 改为委托 `_cap_radius(1/N_e, d_c)`。**数值零回归**：`(16,16)` 输出仍为 `1.1735482746999482`，6dp 字面量差 `2.747e-7`，impl-internal residual 仍为 `1.164e-14`。
- `voronoi_angle` 改为逐胞腔等效球冠半径均值，签名不变。模块常量 `VORONOI_AREA_SAMPLES = 1_000_000`、`VORONOI_AREA_SEED = 20260929`。
- 删除 clamp 后永不可达的 `try/except`（`sphere.py:238-241`）。
- docstring 三处订正：模块级（语义 + 纯度声明）、函数级（Jensen 推导 + 凸分支前提 + 峰值订正）、纯度声明（新增固定 seed 与显式 `M`）。

### 2. `openspec/specs/decompmoe-skeleton/spec.md` — req-6

`voronoi_angle` 契约句从「realized half-angle」收窄为逐胞腔等效球冠半径均值，逐条写入 `G` 的两个分支、MC 估计口径、单侧性的**凸分支前提**、以及「逐胞腔形式是承重的」反退化声明。新增 2 个 Scenario。

⚠️ skeleton req-6 **本就没有 `**Source:**` 字段**（23 个 Requirement 中仅 4 个有），`lint_no_source_field_drift.py` 只检查已存在的 Source 行。新增 Source 属扩大范围且缺 `wayfinder/tickets/` 主反链，故不新增；change 血缘记录在 Scenario 与本 proposal 中。

### 3. `openspec/specs/wayfinder/spec.md` — req-11

L245 对应契约句同步收窄为「与 canonical 可通约」，细节指向 skeleton req-6 与 governance req-gov-1 obligation 7。`Source` 追加 change 引用（主反链 `wayfinder/tickets/A5-3.md` 保持首位，lint 规则③不破）。

### 4. `openspec/specs/governance/spec.md` — req-gov-1

新增 **obligation 7（蒙特卡洛导出的统计量容差）**：此类断言既非整数闭式（obligation 1）、非闭式浮点（obligation 2）、也非 `canonical_voronoi_angle` 的二分导出（obligation 3 原文限定该来源），此前**无任何条款覆盖**。要求按估计器自身标准误 `σ` 推导容差、禁止裸 `==`、禁止 `abs=1e-6`，并载明 `σ` 推导、样本量与 seed。obligation 5 的适用范围同步扩至 obligation 7。新增 1 个 Scenario。

### 5. `tests/test_sphere.py`

| 测试 | 处置 |
|---|---|
| `test_voronoi_measurement_layer` | 重写。`abs(theta−canonical) < π/2` 在新语义下恒真；改为 `1.0°` 可通约性界（被取代的统计量在此处偏离 `46.72°`，是 47 倍） |
| `test_voronoi_angle_known_answer_crosspolytope` | 见证换值 `115.6651° → pytest.approx(62.5444, abs=1e-3)`；`53.1206°` 断言改为 `< 1e-3`；新增回归守护：两个被取代的输出（`115.6651°` / `91.5415°`）均须偏离 > `1°` |
| `test_voronoi_angle_equal_area_witness_equal_area_configurations` | **新增**。crosspolytope32 + greatcircle16 + greatcircle8 三种精确等面积镶嵌 |
| `test_voronoi_angle_not_degenerate_mean_area_form` | **新增**。反退化守护 |
| `test_voronoi_angle_one_sided_gap` | **新增**。单侧性，gap 达 756σ/319σ/70σ |
| `test_voronoi_angle_convexity_boundary` | **新增**。钉住 `θ_conv(d_c)` |
| `test_voronoi_angle_reflected_cap_branch_n_e_2` | **新增**。`N_e=2` 触发 `A_i > 0.5` 反射分支 |

## 实施中发现并修正的计划缺陷

计划原文为 `test_voronoi_measurement_layer` 规定 `assert theta <= canonical + 1e-9`（单侧性）。**实测证伪该阈值**：该夹具真实 gap 为 `0.0399°`，超过估计器 `5σ = 0.0355°`，且其符号翻转的量级与真实 gap 相同，因此**任何基于 σ 的阈值都无法在该夹具上判定单侧性**。处置：该测试改为可通约性界（`1.0°`），单侧性移交给 3 个 gap 达 70σ–756σ 的高信噪比构型。此为计划的实质修正，非机械调整。

## Out of scope

- **不改** `canonical_voronoi_angle` 的任何数值行为（6dp / 4dp 全部 pin 保持）。
- **不**引入 scipy / 球面 Delaunay / 球面 Voronoi 精确解。
- **不**新增 `nearest_neighbor_inradius`（回答的是另一个问题；`CLAUDE.md` §2 简洁优先）。
- **不**改 `CLAUDE.md` §6 第 8 条（把整数/浮点二分扩为三分需 explicit ticket）。
- **不**动 `tests/test_extraction.py` / `test_safeguards.py` / `test_schedule.py` / `test_loss.py`（并行 session 在途）。
- **不**清理 `_tmp_*.py` / `_bk/` / `_patches/` / `_staged/`（本 workspace 批量删除通道不可用）。
- **不**把 `VORONOI_AREA_SAMPLES` 提升为函数参数（签名不变是已裁决决策）。

## Impact

- **Affected files**：`src/decompmoe/sphere.py`、`tests/test_sphere.py`、`openspec/specs/decompmoe-skeleton/spec.md`、`openspec/specs/wayfinder/spec.md`、`openspec/specs/governance/spec.md`。
- **Lint**：两个 gate 须保持 `exit=0`；governance 新条款的 `CLAUDE.md` 主反链结构须过规则②③（沿用 req-gov-1 既有 Source 行，追加在其后）。
- **Test**：`208 passed` 基线 → `213 passed`（新增 5 个测试，改写 2 个）。
- **Behavior**：本次是**行为变更**，由本 change 承载，符合 `CLAUDE.md` §6。

## Capabilities

### Modified Capabilities

- `decompmoe-skeleton` — req-6 测量层契约 + 2 个新 Scenario。
- `wayfinder` — req-11 测量层契约同步为「可通约」。
- `governance` — req-gov-1 新增 obligation 7 + 1 个新 Scenario。

## Source back-link

- `decompmoe-skeleton` req-6 无 Source 字段（仓内既有状态），血缘见本 proposal 与 Scenario 内的 change 引用。
- `wayfinder` req-11 Source 主反链 `wayfinder/tickets/A5-3.md` 保持首位，追加 `` `change 2026-09-29-fix-voronoi-angle-measurement-layer-semantics design.md (Decision 1)` ``。
- `governance` req-gov-1 Source 主反链 `` `CLAUDE.md` `` 保持首位。
- 缺陷血缘：`openspec/changes/archive/2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity/proposal.md` 移交项 1-2；缺陷诞生于 commit `af91717`（2026-08-22）。
