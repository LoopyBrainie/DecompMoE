# design.md — 测量层语义修正的数学推导

> `CLAUDE.md` §6 末条：不以 policy + code-first 论证关闭数学语义选择，必须给出数学推导（单调性蕴含链 + worked counterexample），由数值闭式测试守护。本文件是该要求的载体。

## Decision 1 — `voronoi_angle` 返回逐胞腔等效球冠半径的均值

**状态**：已采纳。

### 1.1 记号与被求解的量

`S^{d_c−1}` 上距给定点角距不超过 `θ` 的球冠面积占比（全函数 `θ ∈ (0, π)`）：

$$
G(\theta)=\begin{cases}\tfrac12 I_{\sin^2\theta}\!\big(\tfrac{d_c-1}{2},\tfrac12\big), & 0<\theta\le\tfrac\pi2\\[5pt] 1-\tfrac12 I_{\sin^2\theta}\!\big(\tfrac{d_c-1}{2},\tfrac12\big), & \tfrac\pi2<\theta<\pi\end{cases}
$$

- 小冠分支即 spec 既有定义，故 `canonical_voronoi_angle(N_e, d_c) = G^{-1}(1/N_e)` **定义未变**。
- **反射分支不可省**：小冠分支在 `θ = π/2` 处饱和于 `G(π/2) = 0.5`。故任何 `A_i > 0.5` 的胞腔（`N_e = 2` 或退化配置）在小冠分支内**无解**。实测 `N_e = 2`、两质心相距 20° 时面积估计为 `[0.50039, 0.49961]`，确实越界。

### 1.2 定义

$$
\widehat\theta=\frac1{N_e}\sum_{i=1}^{N_e}G^{-1}(A_i),\qquad A_i=\Pr\bigl[\arg\max_j \langle y,c_j\rangle = i\bigr]
$$

`A_i` 由固定种子（`VORONOI_AREA_SEED = 20260929`）、固定样本量（`VORONOI_AREA_SAMPLES = 10^6`）的蒙特卡洛估计，故返回值确定、可 pin。

### 1.3 蕴含链（单侧性）

**Step 1 — 面积和恒等式。** 球面 Voronoi 镶嵌的胞腔两两不交且并为球面，故

$$\sum_{i} A_i = 1 \quad\Longrightarrow\quad \bar A=\frac1{N_e}\textstyle\sum_i A_i=\frac1{N_e}$$

**Step 2 — 凸性 ⇔ 凹性。** `G` 在其首个凸分支上关于 `θ` 严格凸；`G` 严格单调递增，故可逆且 `G^{-1}` 在对应面积区间上**凹**。

**Step 3 — Jensen。** 若全部 `θ̂_i = G^{-1}(A_i)` 落在同一凸分支内：

$$\widehat\theta=\frac1{N_e}\sum_i G^{-1}(A_i)\ \le\ G^{-1}\!\left(\frac1{N_e}\sum_i A_i\right)=G^{-1}\!\left(\tfrac1{N_e}\right)=G^{-1}(1/N_e)=\text{canonical\_voronoi\_angle}$$

等号成立当且仅当 `G^{-1}` 在该点取等，即 `A_1=\cdots=A_{N_e}`。故

$$D:=\text{canonical}-\widehat\theta\ \in\ [0,\ \text{canonical}]$$

即 `D` 是**单侧、有界、在等面积理想点取零**的偏离度量。

### 1.4 前提条件不是空的，也不是全局的（**关键限定**）

「`G` 在 `(0, π/2)` 上凸」这一命题**经实测为假**。以中心差分数值求 `G''` 的符号变号点（`d_c = 16`）：

| 分支 | 区间 |
|---|---|
| 凸 | `(0°, 81.9°)` |
| 凹 | `(82.8°, 90.0°)` |
| 凸 | `(90.9°, 97.2°)` |
| 凹 | `(98.1°, 179.1°)` |

二分细化的首个零点为

$$\theta_{\text{conv}}(8)=81.3148^\circ,\qquad \theta_{\text{conv}}(16)=82.6036^\circ,\qquad \theta_{\text{conv}}(32)=83.7313^\circ$$

`d_c = 8 / 32` 结构同型。**MVP 运行点** `canonical(16, 16) = 67.2394°` 落在首个凸分支内，余量 `15.36°`；实测 MVP 构型最大胞腔 `0.077`（`1/16 = 0.0625`）对应半径约 `70°`，亦在分支内。**故 MVP regime 满足前提，Step 3 的不等式在那里是可证的定理。**

超出凸分支后，不等式在全部实测构型中仍成立，但**那是观测行为，不是定理**。spec 据此不得无条件宣称全局成立；由 `test_voronoi_angle_one_sided_gap` 以方向检查方式守护，由 `test_voronoi_angle_convexity_boundary` 钉住 `θ_conv`，使 docstring 无法再次漂移成一个未验证的全局论断（被取代的 docstring 已经犯过一次）。

### 1.5 逐胞腔形式是承重的（反退化论证）

由 Step 1，`G^{-1}(\bar A) = G^{-1}(1/N_e) = canonical` 对**任意**质心集成立。故若实现写成

$$\text{（退化形式）}\quad G^{-1}\!\left(\frac1{N_e}\sum_i A_i\right)$$

则函数对任何输入都返回 canonical，包括明显损坏的输入——**它报告完美的等面积覆盖，且什么都不检测**。

$$\text{（本 change 采用）}\quad \frac1{N_e}\sum_i G^{-1}(A_i)$$

两者之差正是 Jensen gap `D`，在 `D = 0` 处退化为同一个值。实测分离度：

| 构型 | 逐胞腔 | 退化形式 | 分离 |
|---|---|---|---|
| 8 个 `e_1` 副本 + `e_2..e_9` | `40.3868°` | `67.2394°` | `26.85°` |
| 4 个副本 | `55.9021°` | `67.2394°` | `11.34°` |
| 对跖对 + 14 紧簇 | `64.7660°` | `67.2394°` | `2.47°` |
| crosspolytope(32)（等面积） | `62.5444°` | `62.5445°` | `0.0001°` |

`test_voronoi_angle_not_degenerate_mean_area_form` 以 `θ̂ < canonical − 1.0°` 阈值守护，退化形式精确返回 canonical 必然红。

### 1.6 统计误差预算

`θ̂ = (1/N_e)·Σ_i G^{-1}(A_i)`。MVP 点 `(N_e=16, d_c=16)`：`dG/dθ = 0.488421`（实测），故 `dθ/dA = 2.0474`；`A ≈ 1/16` 时 `SD(A) = √(A(1−A)/M)`。

| `M` | 单胞腔 SD | 均值 SE（N_e=16） | `5σ` |
|---|---|---|---|
| `10⁵` | `0.0898°` | `0.0224°` | `0.1122°` |
| **`10⁶`** | **`0.0284°`** | **`0.0071°`** | **`0.0355°`** |
| `2×10⁶` | `0.0201°` | `0.0050°` | `0.0251°` |

选 `M = 10⁶`：SE `0.0071°`，运行时实测 `0.155 s`（CPU，`voronoi_angle(crosspolytope)`）。种子稳定性：seed `0 / 1 / 20260929 / 42` 给出 `62.544388 / 62.544388 / 62.544390 / 62.544369°`，与 canonical 差 `6.6e-5° – 8.6e-5°`。

### 1.7 见证与信噪比（决定了测试怎么写）

crosspolytope(32) 是**精确等面积**镶嵌，真实 gap = `6.5e-5°`，而估计器 SE = `0.0071°`——**真实 gap 只有噪声的 1/109**。因此「crosspolytope 上 θ̂ ≈ canonical」这一断言**无法区分**逐胞腔形式与退化形式（两者在等面积点本就相等）。这直接决定了两个测试必须分开写：

- **等面积见证**（`abs=1e-3`，≈`28×5σ`）——证明可通约与取等；
- **反退化守护**（`θ̂ < canonical − 1.0°`）——在 gap 大的构型上区分两种形式。

把二者合并成一个测试会让反退化守护失效。

### 1.8 被取代实现的反解误差（订正 docstring）

`e(θ) = arccos(1 − 2sin(θ/2)) − θ`，`u = θ/2`，`s = sin u`：

$$\frac{de}{d\theta}=\frac{\cos u}{2\sqrt{s(1-s)}}-1=0\iff \cos^2u=4s(1-s)\iff 1-s^2=4s-4s^2\iff 3s^2-4s+1=0$$

解得 `s = 1/3`（内点）与 `s = 1`（`θ = π`，此处 `e = 0`）。故

$$\theta^*=2\arcsin\tfrac13=38.9420^\circ,\qquad e(\theta^*)=\arccos\tfrac13-2\arcsin\tfrac13=0.5512856\ \text{rad}=31.5868^\circ$$

密扫（`1.8×10⁶` 点）测得峰值 `+31.5863°` 在 `38.942°`，与闭式一致（差源于扫描网格）。两端：`e(180°) = 0`（`arg = 1−2 = −1`）、`e(0.5°) = +7.07°`、`e(179°) = +0.29°`。故被取代 docstring 的「over the whole range +8.7°…+31.4°，peaking near 45°」**两处皆误**：`+8.7…+31.4` 是那 5 个采样点的极值而非全局界，且峰值在 `38.94°` 而非 `45°`。

## Decision 2 — 保留 `voronoi_angle` 符号与签名，原地改语义

**状态**：已采纳（用户裁决 2A）。

`decompmoe-skeleton` req-6 明文锁定的是符号与签名本身（"The package SHALL also provide `voronoi_angle(centroids: Tensor) -> float`…"），两份 spec 引用的都是该符号。`voronoi_angle` 对本语义不撒谎——「（实现化的）Voronoi 角」，`canonical` 是理想、`θ̂` 是实现，正是 Req 11 的对照结构。拒绝重命名（触发两份 capability spec 同步改动，零行为收益）与 deprecation 周期（formalize-only pre-release skeleton，无外部消费者）。

## Decision 3 — 不把统计量容差折进 obligation 2，单列 obligation 7

**状态**：已采纳。

`req-gov-1` 现有二分只覆盖整数闭式与浮点闭式。蒙特卡洛导出的量两者皆非：它不是常量（裸 `==` 无意义），也不是闭式或 `canonical_voronoi_angle` 的二分导出（obligation 3 原文限定该来源，`abs=1e-6` 对采样估计量是真空或恒红）。折进 obligation 2 会让 obligation 2 的「closed-form」限定词自相矛盾，故单列 obligation 7 并在 obligation 5 的适用范围中点名。

## Decision 4 — `canonical_voronoi_angle` 委托 `_cap_radius`，且零回归

**状态**：已采纳。

计划已把此项列为**中风险**，缓解措施是「若任一 pin 变红则回退为保留原实现并另写 `_cap_radius`，不争论」。实测结果：委托后 `(16,16)` 输出仍为 `1.1735482746999482`（逐位相同），`round(θ,4) == 1.1735`、`round(degrees(θ),2) == 67.24`、`(64,16)` 的 `1.020506` 与 `58.47` 全部保持，impl-internal residual 仍为 `1.164e-14`。**回退条件未触发**，保留委托形式（消除二分逻辑重复）。7 条既有 pin 断言即回归防线。

## Risk

| 风险 | 缓解 |
|---|---|
| `_cap_radius` 委托扰动 6dp pin | Decision 4 已实测零回归；pin 断言常驻 |
| 固定 seed 掩盖真实统计波动 | 跨种子实测记录在 §1.6；容差按 `σ` 推导而非按单次观测收紧（obligation 7 (b)） |
| 凸分支外无证明 | §1.4 显式标注为观测行为；`test_voronoi_angle_convexity_boundary` 钉住 `θ_conv` |
| 「非逐胞腔即空转」被未来重构重新引入 | §1.5 反退化表 + `test_voronoi_angle_not_degenerate_mean_area_form` |
| MC 使函数不再是「纯函数」 | 模块 docstring 的纯度声明已同步改写为「确定性（固定 seed）」，不再是 blanket purity |
