# 修复 F4/F5/F6/F7 — loss 闭合式接线与 pytest 守护保真度

## Why

Python reviewer review 本 session 修复内容后判定**零回归**，另报 9 条 findings。本 change 处理其中 4 条，全部集中在 `src/decompmoe/loss.py` 与 `tests/test_loss.py`，主题是**「spec 闭合式在代码里算对了，但没有 pytest 钉住它真的被算」**。

`decompmoe-skeleton` 硬性要求每个子 spec 的 TDD 工作流「对数学原理进行约束，以保证与 spec 的一致，不能只管功能不管原理」。本 change 处理的正是该要求被违反的四个点：接线可以**静默**改错而测试全绿。

## 核验事实

### F4 — `N_e` 由张量宽度反推，而非取 spec 权威值

`wayfinder` req-12 闭合式：`L_lb = N_e · Σ_i f_i.detach() · P_i`。其中 `N_e` 是**模型级常量**（MVP `N_e = 16`）。

`src/decompmoe/loss.py:115` 原为：

```python
L_lb_raw = (f_det.mean(dim=(0, 1)) * P_mean).sum() * f_per_expert.shape[-1]
```

`f_per_expert.shape[-1]` 是**运行时观测值**，不是 spec 常量。函数签名已有 `cfg`（`MVPConfig`，含权威 `N_e`）却完全未用于该乘子；docstring 甚至把 `cfg` 描述为「reserved for future spec requirements; current L_lb / L_sep closed forms are N_e-derived and do not need cfg」——把「不需要 cfg」写成了既成事实。

后果：spec 闭合式的 `N_e` 由调用方传入的张量形状决定。正确调用下二者由 `N_e` 不变量恒等，因此**缺陷不可见**；但它使 spec 承诺退化为数据依赖。

### F5 — `L_sep_raw` 与 `L_total` 接线均无独立钉子

两处**恒等自指**，接线回归可静通：

1. `test_sep_formula_non_degenerate` / `test_sep_formula_orthonormal_degenerate` 直接调 `compute_L_sep`，**绕过 `L_total`** ⇒ 把 `loss.py:118` 的 `L_sep_raw = compute_L_sep(c_centroids)` 换成 `torch.zeros(())`，两测**照过**。
2. `test_lambda_fixed_phase_4` 断言 `parts1.L_sep ≈ 0.001 * parts1.L_sep_raw` —— 两边**来自同一个 `LossParts`**，无论 `L_sep_raw` 被换成什么都自洽。
3. `L_total = L_CE + α·L_lb + λ(t)·L_sep` 的三项组合**无任何测试**。把 `L_total_t` 改成 `L_CE + L_lb`（丢掉分离项）全绿。

### F6 — 两条裸 `torch.allclose` 无 `actual=`

`tests/test_loss.py:199-200` 的 `assert torch.allclose(...)` 无失败消息。违反 `governance` req-gov-1「失败信息必带内嵌值」。

### F7 — 死脚手架

`tests/test_loss.py:169-173`：`c = normalize(randn(16,16))` → `ref = compute_L_sep(c).item()` → `assert ref > 0` → `del ref`。`ref` 建后即删，`c` 因 `del ref` 而无人消费；该测试只验 `_lambda_at`，与 `L_sep_raw` 无关。`ref` 删除后 `c` 变 unused，故连 `c` 一并删除（不留下新的未用变量）。docstring 尾句「(via L_sep = λ·L_sep_raw with a known L_sep_raw)」随之失真，同步改写。

## What changes

| 文件 | 改动 |
|---|---|
| `src/decompmoe/loss.py` | 乘子改 `N_e = cfg.N_e if cfg is not None else f_per_expert.shape[-1]`；`cfg` docstring 由「reserved for future」改为如实描述其唯一职责 |
| `tests/test_loss.py` | 新增 `test_sep_raw_wired_into_l_total`：由 `c` **独立重推** spec 闭合式，钉 `L_sep_raw`、`L_sep = λ·L_sep_raw`、`L_total = L_CE + L_lb + L_sep` 三段 |
| `tests/test_loss.py` | 新增 `test_lb_N_e_comes_from_cfg_not_tensor_width`：以**故意不一致**的 cfg / 张量宽度钉 `cfg` 优先级 |
| `tests/test_loss.py` | F6：两条 `allclose` 补 `actual=` |
| `tests/test_loss.py` | F7：删死脚手架 + 同步 docstring |

## 为何 `test_lb_N_e_comes_from_cfg_not_tensor_width` 故意传入不一致的 cfg

要区分「乘子取自 `cfg.N_e`」与「取自 `shape[-1]`」两种实现，**唯一办法是让两者不等**。正确调用下二者由 `N_e` 不变量恒等，任何用匹配宽度的测试在两种实现下都通过 —— 即测试无效。

该测试因此显式记录「本调用是刻意的 caller 契约检查，不是正常用法」。取舍：它把「cfg 优先」这条 spec 保真决策变成可执行断言，代价是承认一个不一致的调用不会被拒绝。**不采用 raise ValueError 的替代方案**，因为 `L_total` 目前对 `f_per_expert` / `p_per_expert` / `c_centroids` 的形状一律不做校验，新增单点校验会与「本函数不校验输入形状」的现状不一致，且属于本 change 范围外的防御性扩张（`lint_no_dead_defensive` 亦对该类模式敏感）。

## 明确不做（non-goals）

- **不改任何闭合式本身**。`compute_L_sep` 与 `L_lb` 的公式经 mpmath 独立复算均正确 —— F4 改的是 `N_e` 的**来源**，不是 `N_e` 的值。
- **不给 `compute_L_sep` 加 `cfg` 参数**。`compute_L_sep` 是纯函数，其 `N_e` 由 `c_centroids.shape[0]` **定义性**得出（`C ∈ R^{N_e×d_c}`），不存在「权威值 vs 观测值」的分歧。
- **不改 `ALPHA` / `_lambda_at` / `_PHASE_BOUNDS`**。均已核验正确。
- **不新增 spec delta**。本 change 不改变任何 Requirement 的语义 —— F4 是**代码向 spec 靠拢**，而非 spec 变更。故归档时用 `--skip-specs`。
