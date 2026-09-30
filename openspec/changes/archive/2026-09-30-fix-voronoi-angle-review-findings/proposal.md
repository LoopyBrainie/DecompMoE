# 修复 `voronoi_angle` 变更的 review findings（2 BLOCKER + 2 HIGH + 3 MEDIUM + 3 LOW）

## Why

`archive/2026-09-29-fix-voronoi-angle-measurement-layer-semantics` 落地后经 `/code-review`（Python reviewer）
判定 **FAIL**。本 change 关闭该 review 的全部 10 条 finding。

**最严重的一条不是代码 bug，而是 spec 写入了关于 `G` 的假事实。**
`voronoi_angle` 的 docstring 与三份 spec 都声称「`G` 在 `d_c = 16` 时于 `(82.8°, 90.0°)` 凹」，
并把 `θ_conv(d_c) = 81.3148° / 82.6036° / 83.7313°` 钉成 Jensen 不等式的数值前提。

独立复核（mpmath 50 位 + 解析闭式）证明这是**伪影**：

    G'(t)  = sin^(d_c−2)(t) / B((d_c−1)/2, ½)
    G''(t) = (d_c−2)·sin^(d_c−3)(t)·cos(t) / B((d_c−1)/2, ½)

`0 < t < π/2` 上每个因子皆正 ⇒ `G'' > 0` 恒成立，**区间内无零点**。解析值与 50 位有限差分在
12 位有效数字上一致。而上述三个 `θ_conv` 字面量，与仓库自有 8 点 Gauss–Legendre 求积二阶差分的
**符号翻转位置**逐位吻合：

| `d_c` | 角度 | 真实 `G″` | 仓库求积 `G″` |
|---|---|---|---|
| 16 | 82.60° | **+2.457716** | +0.005075 |
| 16 | 83.73° | **+2.149094** | **−1.933388** ← 翻转 |
| 16 | 88.00° | **+0.736597** | **−15.7288** |
| 8 | 82.60° | **+0.754902** | **−0.866322** ← 已在 81.31° 前翻转 |
| 32 | 83.73° | **+6.066314** | +0.004131（临界） |

**关键判断：这不推翻 Jensen 结论，反而让它更强。** `G` 在整个 `(0, π/2)` 严格凸 ⇒ `G⁻¹` 在
`(0, 0.5)` 凹 ⇒ 单侧界的前提从「per-d_c 角度边界」**简化为 `∀i: A_i < 0.5`**（每胞腔小于半球）。
MVP 下 `1/N_e = 0.0625`、实测最大胞腔 `≈ 0.077`，余量 `6.5×`。所以这是**文档正确性缺陷**，
不是数值回归 —— 但一个测试正钉着这个假命题，且会在求积被修正时变红，即**主动惩罚正确性**。

## Findings 与处置

| # | 级别 | Finding | 处置 |
|---|---|---|---|
| 1 | BLOCKER | `θ_conv` 是求积伪影；真实 `G` 在 `(0, π/2)` 全程严格凸。spec 声称的凹区间不存在 | docstring + 3 份 spec 改为「`G` 严格凸 ⇒ 前提 `∀i: A_i < 0.5`」 |
| 2 | BLOCKER | `test_voronoi_angle_convexity_boundary` 调私有 `_cap_area` 做有限差分，**同义反复**且钉住假命题；`G'' < 0` 断言为真命题之假 | 删除；替换为 `test_voronoi_angle_precondition_is_area_below_half`（用解析闭式） |
| 3 | HIGH | `28×` 应为 `0.028×`（漏小数点）⇒ obligation 7 自身 WHEN/THEN 矛盾 | 随 σ 修正一并改为 `13.7×`（对**修正后**的 `5σ`） |
| 4 | HIGH | `5σ` 推导忽略 `ΣA_i ≡ 1`，线性项恒消，波动为二阶；`0.0071°` 大 `486×` | 重推：`σ = 1.461e-5°`，`5σ = 7.31e-5°`；spec + docstring + 测试注释同步 |
| 5 | MEDIUM | `area == 0 → radius 0` 未被 spec 授权 | **spec 授权**（不抛错）：`test_voronoi_angle_one_sided_gap` 的见证故意传重复质心，抛错会直接推翻既有 Scenario |
| 6 | MEDIUM | 非单位范数 `centroids` 静默改变镶嵌（内积被 `‖c_j‖` 加权） | 新增 `ValueError`（`atol=1e-6`），spec 化 |
| 7 | MEDIUM | `float64` centroids 现抛 `RuntimeError`（dtype 不匹配），属**回归** | probe 块 `.to(centroids.dtype)`；spec 化 + 回归测试 |
| 8 | LOW | `31.5868°` / `38.9420°` 第 4 位小数错 | 改为 `31.5863380965°` / `38.9424412690°`（docstring） |
| 9 | LOW | `approx(90.0)` 因两站点对称而退化，检不出走了哪个分支 | 改为 spy `_cap_radius`，断言确实有 `A_i > 0.5` 被反演且半径 `> π/2` |
| 10 | LOW | runtime `0.155 s` 略乐观（实测 `0.098–0.132 s`） | archived design.md 加 supersession 注记（不改历史字节） |
| + | 建议 | `test_voronoi_measurement_layer` 的 `1.0°` 界过松（真实 gap `0.0399°`，25× 余量） | 收紧至 `0.2°`（5× 余量） |

## What changes

### 1. `src/decompmoe/sphere.py`

- docstring 凸性段整体重写：给出 `G'`/`G''` 解析闭式，说明 `(0, π/2)` 无零点，前提降为 `∀i: A_i < 0.5`；显式警告**不要**用 `_cap_area` 有限差分读曲率。
- 新增「Degenerate input」段：零面积胞腔语义 + 单位范数契约 + dtype 契约。
- 误差预算重推：`ΣA_i ≡ 1` ⇒ 一阶相消 ⇒ `1/M` 标度 ⇒ `σ = 1.461e-5°`，并记录被取代的 `0.0071°`（`486×`）。
- LOW 8 第四位小数修正。
- 实现新增单位范数校验（`ValueError`）；probe 块 `.to(centroids.dtype)`。

### 2. 三份 spec

- `decompmoe-skeleton` req-6：凸性前提、`A_i < 0.5` 前提、单位范数 + dtype 契约、零面积胞腔、单侧性 Scenario 的 σ 倍数。
- `wayfinder` req-11：指针措辞点名真实前提（本身无假数字）。
- `governance` req-gov-1：obligation 7 的 σ 推导（要求「必须尊重 `ΣA_i ≡ 1`」）+ Scenario 的 `28×`→`13.7×`、`0.0355°`→`7.31e-5°`、`1.0°`→`0.2°`。

### 3. `tests/test_sphere.py`

| 测试 | 处置 |
|---|---|
| `test_voronoi_angle_convexity_boundary` | **删除** → `test_voronoi_angle_precondition_is_area_below_half`（解析闭式三段断言） |
| `_cap_area_second_derivative` / `_convexity_boundary` | **删除** → `_cap_area_d2_closed_form` |
| `_VORONOI_MC_5SIGMA_DEG` | `0.0355` → `7.31e-5`，docstring 重写推导 |
| `test_voronoi_angle_reflected_cap_branch_n_e_2` | spy `_cap_radius`，断言 `A_i > 0.5` 被反演且 `r > π/2` |
| `test_voronoi_angle_rejects_non_unit_centroids` | **新增**（MEDIUM 6） |
| `test_voronoi_angle_honours_centroid_dtype` | **新增**（MEDIUM 7 回归守护） |
| `test_voronoi_measurement_layer` | 界 `1.0°` → `0.2°` |
| 另 3 个测试 | 修正 `28×` / `5σ` / `756σ` 注释 |

## Out of scope

- **不**改 `canonical_voronoi_angle` 的任何数值行为（6dp / 4dp pin 保持）。
- **不**引入 mpmath / scipy 作为测试依赖 —— 新的凸性测试用 `math.gamma` 闭式，零新增依赖。
- **不**重写 archived change 的字节。`archive/2026-09-29-fix-voronoi-angle-measurement-layer-semantics/design.md`
  §1.6/§1.7 与 `tasks.md` D.7 含有被取代的 σ 表、峰值位数与 runtime；改写历史记录比留下错误更糟，
  故在本 change 的 `design.md` 记录 supersession（**LOW 10 的处置**）。若审计偏好字节级更正，需另开 change。
- **不**动并行 session 在 `config.py` / `gating.py` / `test_loss.py` / `test_safeguards.py` / `test_schedule.py` 的未提交改动。
- **不**执行训练或 baseline（`CLAUDE.md` §6）。

## Impact

- **Affected files**：`src/decompmoe/sphere.py`、`tests/test_sphere.py`、`openspec/specs/{decompmoe-skeleton,wayfinder,governance}/spec.md`。
- **Test**：`213 passed` 提交态 → `215 passed`（删除 1、新增 2、改写 1）。
- **Behavior**：MEDIUM 6 是**新错误路径**（非单位范数抛 `ValueError`），由本 change 授权。MEDIUM 7 是**回归修复**。其余为文档/注释/spec 修正，数值行为零变更（float32 路径逐位不变）。
- **Lint**：两个 gate 须保持 `exit=0`；governance 新条目的 `` `CLAUDE.md` `` 主反链结构须合规。

## Capabilities

### Modified Capabilities

- `decompmoe-skeleton` — req-6 凸性前提 + 契约（单位范数 / dtype / 零面积胞腔）。
- `wayfinder` — req-11 指针措辞。
- `governance` — req-gov-1 obligation 7 推导 + Scenario 数值。

## Source back-link

- `decompmoe-skeleton` req-6 **无** `**Source:**` 字段（3 个 Requirement 中仅 4 个有），不新增。
- `wayfinder` req-11 主反链 `` `wayfinder/tickets/A5-3.md` `` 保持首位。
- `governance` req-gov-1 主反链 `` `CLAUDE.md` `` 保持首位。
- 缺陷来源：commit `33f7cc9`（2026-09-30），经 `/code-review`（Python reviewer）判定。
