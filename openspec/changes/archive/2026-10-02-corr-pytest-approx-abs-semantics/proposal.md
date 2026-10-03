# 勘误 `pytest.approx` 的容差语义陈述（governance req-gov-1）

## Why

`governance/spec.md` req-gov-1 用 `pytest.approx` 的**有效容差公式**作为它三条数值纪律的论证支点。该公式陈述**是错的**，且错在 pytest 源码的一个反直觉短路分支上。

pytest 9.1.1 的 `_pytest/python_api.py::ApproxScalar.tolerance`：

```python
absolute_tolerance = set_default(self.abs, self.DEFAULT_ABSOLUTE_TOLERANCE)
...
# If the user specified an absolute tolerance but not a relative one,
# just return the absolute tolerance.
if self.rel is None:
    if self.abs is not None:
        return absolute_tolerance          # ← 直接返回，不进 max()
...
relative_tolerance = set_default(self.rel, self.DEFAULT_RELATIVE_TOLERANCE) * abs(self.expected)
return max(relative_tolerance, absolute_tolerance)
```

**`rel` 的默认值是 `None`，不是 `1e-6`。** `DEFAULT_RELATIVE_TOLERANCE = 1e-6` 确实存在于源码，但它只在短路**之后**的分支里被 `set_default` 引用，因此给定 `abs` 时它根本不生效。

裁决构造（`evidence/_pytest_approx_semantics.py`，本 change 的 provenance）：

| 构造 | 结果 |
|---|---|
| `pytest.approx(1.0, abs=1e-9).tolerance` | `1e-09` |
| 若为 `max(abs, rel·|x|)` | `1e-06` |
| `1.0 + 1e-8` vs `approx(1.0, abs=1e-9)` | **FAIL** |

⇒ **真实容差恰为 `abs` 本身。**

## 错在哪几处，以及后果

| 位置 | 现陈述 | 事实 | 后果 |
|---|---|---|---|
| L13（义务 1） | 「有效容差公式是 `max(abs, rel·\|expected\|)`」；「`abs=0` 且 `rel` 留在 pytest 默认 `1e-12` 时退化为 `1e-12·\|expected\|`」 | 公式本身不适用于给了 `abs` 的情形；`rel` 默认是 `None` 不是 `1e-12`；`abs=0` 的容差**恰为 0** | **这条最危险**：它声称 `abs=0` 会退化成相对容差，于是读者可能（a）以为 `abs=0` 是「伪零容差」而拒绝使用，或（b）反过来误以为 `abs=0` 仍随量级缩放而写出更弱的守卫。两种误读都源于同一个假陈述 |
| L17（义务 3） | 「`abs=1e-6` 保留 pytest 默认 `rel=1e-6`，实际判据是 `max(1e-6, 1e-6·\|expected\|)` = `1.17e-6`」 | 实际判据就是 `1e-6` | 引证数字错；**判别力结论不受影响**（见下） |
| L17（同句） | 「6dp 字面量固有截断误差以 `5e-7` 为界 ⇒ 任何 `< 1e-6` 的容差都不满足 ⇒ `1e-6` 是显示格式允许的最小值」 | 6dp **截断**误差恒 `< 1e-6`，`5e-7` 是四舍五入半单位而非截断界（反例 `trunc6(0.9999999) = 0.999999`，误差 `9e-7 > 5e-7`）；实测 `abs=4.3e-7` 对 `1.173547` 直接通过 | 两处皆假。该断言是 A-2 勘误 E13 的原始论断，Change α 已在 design 登记其死亡 |
| L22 | 同一 `max(1e-6, 1e-6·\|expected\|)` 判据 | 同上 | 同上 |
| L37 / L42（Scenario） | 「`abs=0` 会引入隐式 `rel=1e-6` 的量级缩放容差」 | `abs=0` 的容差恰为 0，不会引入任何相对容差 | 规则本身（整数闭式用 bare `==`）**仍然正确**，须保留；错的只是理由 |
| `tests/test_sphere.py:98-99` | docstring 复制了 L17 的 `5e-7` / 「任何 `< 1e-6` 的界都会在真值上失败」 | 同上 | 测试代码里的错误论断会被后来者当权威引用 |

**不改变的部分（必须原样保留）**：

- 整数闭式必须 bare `==`、浮点闭式必须 `pytest.approx(..., abs=...)` 的**规则本身**正确；
- 判别力分析正确且稳健：`1.275e-6` / `1.297e-6` 在 `abs=1e-6` 与 `max` 两种读法下都判 FAIL，`8.34e-7` 两种读法下都判 PASS。**错的只是理由，不是守卫**；
- 三个 6dp 字面量的实测差 `4.259e-7` / `6.216e-7` / `8.248e-7` 正确。

## Why 拆成独立 change（排在 α 之后）

α 与 β 同在 `governance` 真相源，但风险面不同：

- **α 优先**：`5.01e-52` 是一条 MUST（`bisection residual < 1e-9`）的**支点**，它污染引证链——任何引用它的下游 change 都会继承假前提。
- **β 其次**：判别力结论不受影响，属措辞修复。

但 β **不得拖过下一个迭代**，理由见上表第一行：义务 1 的 `abs=0` 论断会直接误导人写测试。

## What Changes

1. `governance/spec.md` 四处（L13 / L17 / L22 / L37+L42）改成经实测的语义陈述，并注明**实测环境 pytest 9.1.1**（`pyproject.toml` 未 pin pytest 版本，故必须标环境）。
2. `tests/test_sphere.py:98-99` 的 docstring 副本同步更正。
3. 引入 **`req-gov-1` 义务 1 的正确理由**：整数闭式用 bare `==` 的根据不是「`abs=0` 会退化」，而是「`approx` 对整数做浮点比较、且其类型/容差语义随 pytest 版本变化，裸 `==` 在所有量级上给出**可判定的**零容差」。

## Impact

- **Affected specs**: `governance`（req-gov-1 整块）
- **Affected tests**: `tests/test_sphere.py`（仅 docstring，**不改任何断言**）
- **行为变化**: 无。`pytest -q` 应保持全绿且**测试数量不变**——本次只改散文与 docstring。
- **不做的事**：不收紧 `abs=1e-6`（收紧到 `4.3e-7` 虽然对当前三个字面量可行，但会削弱对实现退化的余量，且属独立的数值决策，不在本 change）。
