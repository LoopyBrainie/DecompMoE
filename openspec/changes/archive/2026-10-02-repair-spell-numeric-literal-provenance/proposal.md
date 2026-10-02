# 修正真相源里的不可复算数值字面量（provenance 修复）

## Why

三份 peer spec 里有一个被反复引用、但**量纲上不可能成立**的数值：

`governance/spec.md` L17（义务 3）、L20、L21 与 `decompmoe-skeleton/spec.md` L114 都声称，二分 Voronoi 角在 canonical 根处的残差
`|½·I_{sin²θ}(7.5, ½) − 1/N_e|` 是 `5.01e-52`（N_e=16）/ `2.92e-52`（N_e=64）。

这个数字**不是**「canonical 根处残差」。实测（`evidence/_alpha_forensics.py`，mpmath dps=60）：

| θ 的来源 | N_e | 实测残差 |
|---|---|---|
| spec 的 canonical 字面量 `1.1735474259197175` | 16 | `1.4635872379108090131680874e-17` |
| spec 的 canonical 字面量 `1.0205068247837132` | 64 | `1.9420345120803994000206689e-18` |
| `sphere._cap_radius` 的二分停点（`break < 1e-13`） | 16 | `4.6226242368382708792711061e-15` |
| **spec 声称** | 16 | `5.01e-52` ← 比真值小 **35 个数量级** |

量纲自洽性反证：若残差真是 `5.01e-52`，则 `I_x` 必须与 `1/16 = 0.0625` 吻合到第 **50.1 位十进制**。float64 单次运算的舍入误差下界约 `1e-16`；`1e-52` 需要约 170 位尾数。即便用 mpmath dps=60 直接求值，真值也是 `1.46e-17` 而非 `1e-52`。**该数字是 oracle 自身二分 bracket 的收敛残差，被误标成了「canonical 根处残差」。**

## Why this is governance-first, not cosmetic

结论本身仍然成立（`abs=1e-6` 的论证与 6dp 判别性不依赖它），所以这不是「结论错了」，而是**引证错了**。但它落在 peer 真相源里，而且是「测试必须用它论证 `bisection residual < 1e-9`」这一整条义务的支点。任何下游 change 引用它，都会再生产出一批「结论对、引证错」的副本。

本仓已实证这是**同一类坑的第三次出现**：

1. 第一版 oracle 用了 mpmath **3 参** `betainc(a,b,x)`，它返回补值 `1−I_x` 而非 `I_x`；
2. `pytest.approx` 语义被写成 `max(abs, rel·|x|)`，而 pytest 9.1.1 在给定 `abs` 时**短路**（`rel` 默认是 `None` 不是 `1e-6`）；
3. 本次：`5.01e-52`。

三次的共同形态是「**一个看起来像证据的数字**」——它存在于源码里、位数齐全、能自洽地参与推理，但没有任何 provenance 说明它是怎么来的。

## What Changes

1. **四处字面量换成可复算陈述**（不是换成另一批魔法数）。每处都写明：
   - 该量的真值（附 mpmath dps=60 与 4 参 `betainc` 的调用形式）；
   - 该量由**什么决定**——二分停止判据 `|G − 1/N_e| < 1e-13`，不是 float64 精度下界；
   - provenance 指向本 change 的 `evidence/_alpha_forensics.py`。
2. **新增 `governance` Requirement `req-gov-5`：数值字面量 provenance 义务**。规则：
   > 任何进入 spec 的数值字面量，落盘时必须附 provenance（推导链或可复算脚本）；
   > 否则不得入 spec。
   并给出三条可机检的反例类别：量纲不可能（本次）、被上游 bracket 容差冒充的根处残差（本次）、把 API 默认值当判据的推论（pytest 事件）。
3. **不修改 Change 2 归档副本**。`openspec/changes/archive/2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard/specs/**` 里另有 4 处同样的字面量，但那是该 change 的**历史记录**；改写归档等于伪造历史。已在 design.md 登记为有意保留。

## Impact

- **Affected specs**: `governance`（L17 / L20 / L21 + 新增 `req-gov-5`）、`decompmoe-skeleton`（L114）
- **Affected tests**: 无。`tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` 断言的是 `< 1e-9`，`1.46e-17` 与 `5.01e-52` 都远低于该界，测试行为不变。
- **Anchor 影响**: `governance` 由 4 增至 **5**（新增 `req-gov-5`）。`build_baseline.py` 的 `EXPECT_ANCHORS["governance"]` 须同步为 5；因契约已改为检查**覆盖**（每条 Requirement 恰一个独立 anchor、无重复）而非绝对值，本次新增不构成结构漂移。
- **不做的事**：不修 `governance/spec.md` 义务 1/3 里的 `pytest.approx` 语义错误（那是 Change β 的范围，拆开是因为优先级与风险面不同）。
