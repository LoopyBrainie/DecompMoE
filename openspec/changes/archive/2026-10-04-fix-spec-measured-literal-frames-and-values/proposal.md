# Proposal: 2026-10-04-fix-spec-measured-literal-frames-and-values

## Why

一轮三轴审计（spec 数学 / 代码 ↔ 形式化 / pytest 原理约束）报出 `decompmoe-skeleton/spec.md` 的 req-6 有 4 处缺陷：3 处 **measured 字面量与实现不符**，2 处**残差字面量未标 frame**。本 change 只处理 spec 文字，**不改任何 Requirement 的规范声明、不改数值容差、不改不等式**——变的只有「实测值的引用」与「相对/绝对的 frame 标注」。

**为什么这些字面量本该是可信的**：`voronoi_angle` 是**确定性**的（`VORONOI_AREA_SEED = 20260929`、`VORONOI_AREA_SAMPLES = 1_000_000` 均为模块常量），所以它不是随机量，任何人都应能逐位复现 spec 里写的数。实测与文字不符，说明这些数字是在某次实现变更之前写下、之后没人回来同步的。

**为什么这次要重新测量而不是照抄审计报告**：审计给出的数字本身是**一处对、两处错**（见下），所以全部重测。重测使用 `tests/test_sphere.py` 自己的 fixture 构造函数（`_great_circle_centroids` / `_dup_centroids` / `_antipodal_cluster_centroids`）与模块常量，不重新实现构造。

**审计报告本身被驳回的一条**：审计称 `:140` 的「same-argument residual `≤ 3.23e-16`」低估约 3%（实为 `3.33e-16`）。**该结论不成立**——审计用的是 2001 点稠密 sweep，而 spec 指的是本 Scenario 自己声明的 9 点 sweep。实测在**该 9 点 sweep 上 max = 3.2294e-16 @81.34°**，与 spec 字面量精确相符。稠密 sweep 的 `3.3798e-16` 只比它高 4.6%，且与「float64 噪声底」的说法不矛盾。本 change 因此**不改这个数**，改为把 sweep 点位写进 spec（消除「the whole sweep」的歧义），并附上稠密 sweep 值以免下轮再被当成缺陷。

## What Changes

`MODIFIED` `decompmoe-skeleton` req-6（Voronoi Self-Consistency Threshold），3 个 Scenario 的实测引用：

### 1. Scenario「…on an exactly equal-area tessellation」

| 量 | 改前 | 改后（实测） |
|---|---|---|
| crosspolytope(32) gap | `6.5e-5°` | `6.4561e-5°` |
| great-circle(16) gap | `1.0e-4°` | `2.4817e-5°` |
| great-circle(8) gap | `0.0°` | `2.2667e-5°` |

后两项是**实质偏差**（4× 与「声称精确为 0」）。三者仍在 `abs=1e-3` 度的容差内，等面积见证的**不等式与断言不受影响**；被改的只是引用值。同时补上 seed，使该行可复现。

### 2. Scenario「…is one-sided and not the degenerate mean-area form」

| 量 | 改前 | 改后（实测） |
|---|---|---|
| `dup8_of_e1` gap | `26.8525°` | `26.8528°` |
| `dup4_of_e1` gap | `11.3372°` | `11.3373°` |
| `antipodal_pair_plus_14` gap | `2.4734°` | `2.5047°` |
| σ 倍数 | `3.7e5×` / `1.6e5×` / `3.4e4×` | `3.67e5×` / `1.55e5×` / `3.43e4×` |
| separations | `26.85°` and `2.47°` | `26.85°` and `2.50°` |

前两项差在第 4 位（无害），第三项差 **0.031°（1.3%）**，是可感知的漂移。σ 倍数只是补上有效数字以与新的 gap 自洽。`2.47°` → `2.50°` 后仍远高于 `1.0°` 阈值，单侧性方向断言与退化形式守卫均不受影响。

### 3. Scenario「d_c = 2 affine degeneration」

| 量 | 改前 | 改后 |
|---|---|---|
| same-argument 包络 | 「flat at `≤ 3.23e-16` across the whole sweep `θ ∈ (0°, 90°)`」 | 数值不变；**点名 sweep 的 9 个点**并给出实测 max `3.2294e-16` @81.34°，另附稠密 sweep `≤ 3.3798e-16` |
| `89.99999°` 处的偏差 | `7.60e-11`（**未标 frame**） | `7.60e-11` **relative to `θ/π`**（absolute `3.7976e-11`） |
| `N_e = 2` 的偏差 | `6.71e-9`（**未标 frame**） | `6.71e-9` **relative to `π/N_e`**（absolute `1.0537e-8`） |

后两处是**同一段自己警告过的失败模式**：该段已写明「**Units are not interchangeable.** §3 的 `< 1e-6` 是**弧度角容差**，而残差是**无量纲面积占比**」，却把两个**相对**偏差写成了裸字面量。读者按绝对量读会把残差**低估 2×**。

## 不改什么

- **不改任何规范声明**：闭式、容差、不等式、Scenario 的 WHEN/THEN 结构、`abs=1e-3` / `abs=1e-4` / `abs=1e-6` 一律不动。
- **不改 `≤ 3.23e-16`**：实测证明它在自己的 sweep 上是对的。
- **不改 `≈ 4.46e-14` / `rel_dev / N_e = 1.42e-14`**：实测 `4.4631e-14`–`4.4645e-14` / `1.4206e-14`–`1.4211e-14`，与文字相符，且原文已明确标注 absolute / RELATIVE。
- **不改 `src/` 与 `tests/`**：同批的代码/测试修复在独立 commit 中完成（`metrics.py` float64、`sphere.py` docstring frame、`test_distance.py` 梯度量与断言形态、`test_gating.py` 掩码 arity），与本 change 的 spec delta 解耦。

## 复现方式

```
uv run python <tmp>/remeasure_spec.py   # 载入 tests/test_sphere.py 的 fixture + 跑 voronoi_angle
uv run python <tmp>/measure_b1b2.py    # d_c=2 的 b1/b2 两个残差
```

`voronoi_angle` 的确定性由 `sphere.py:245` / `sphere.py:259` 的模块常量保证，因此这些值不是「某次运行的样本」，而是可逐位复现的事实。
