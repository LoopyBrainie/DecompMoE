# Design — F4/F5/F6/F7 loss 接线与守护保真度

## Decision 1 — F4 取 `cfg.N_e`，张量宽度仅作 fallback

`N_e` 在 spec 闭合式 `L_lb = N_e · Σ_i f_i.detach() · P_i` 中是模型级常量。`MVPConfig.N_e` 是其权威来源；`f_per_expert.shape[-1]` 是对同一常量的观测。

```python
# `N_e` in the spec closed form is the model-wide constant, so it is read
# from cfg whenever the caller supplies one; the routing-tensor width is
# only the cfg-free fallback (they coincide under the `N_e` invariant).
N_e = cfg.N_e if cfg is not None else f_per_expert.shape[-1]
```

保持 `cfg` 为**可选关键字参数**（`*, cfg=None`）：`cfg` 缺失时行为与改动前逐位相同，不给既有调用点引入新义务。

不改 `compute_L_sep`：其 `N_e = G.shape[0]` 是**定义性**的 —— `C ∈ R^{N_e×d_c}` 的行数就是 `N_e`，不存在权威值与观测值的分歧。

## Decision 2 — F5 用「独立重推」打断自指，而非加 mock

F5 的本质是**恒等自指**：`L_sep` 与 `L_sep_raw` 同源、`L_total` 的各项与被测函数同源。打破自指有两条路：

| 方案 | 评价 |
|---|---|
| (a) mock / monkeypatch `compute_L_sep` | 只证明「被调用」，不证明「按 spec 算出正确值」 |
| **(b) 在测试内由 `c` 独立重推 spec 闭合式** | **采纳** |

(b) 让断言同时具备两层能力：既钉「接线发生」，也钉「结果符合 spec」。`test_sep_formula_non_degenerate` 已有同款重推先例（由 `c` 重算 `G` / `fro_sq` / `expected`），本 change 沿用其写法与 `abs=1e-9` 容差约定，保持风格一致。

三条断言各自的捕获目标：

```python
expected_sep_raw = float(((G * G).sum() - N_e) / (N_e * (N_e - 1)))   # 独立重推
assert parts.L_sep_raw ≈ expected_sep_raw                            # ① 接线 + 数值
assert parts.L_sep ≈ λ · expected_sep_raw                            # ② λ 接线
assert parts.L_total ≈ L_CE + L_lb + L_sep                            # ③ 三项组合
```

① 拦 `L_sep_raw = zeros`；② 拦 `L_sep` 不乘 λ 或乘错 λ；③ 拦 `L_total` 丢项。① 另含 `expected_sep_raw > 0` 的 setup 断言 —— 若随机种子偶然给出正交（退化）质心，测试会以「test setup is degenerate」明确报错而非静默通过一个 `≈0` 的平凡断言。

## Decision 3 — F4/F5 的守护必须经变异测试验收

新增测试若无变异测试，无法区分「守护生效」与「断言恒真」。本 change 对 `src/decompmoe/loss.py` 施加三个单点变异并确认各自被**预期的那个**测试拦下：

| 变异 | 捕获者 | 数量 |
|---|---|---|
| `L_sep_raw = compute_L_sep(c_centroids)` → `torch.zeros(())` | `test_sep_raw_wired_into_l_total` | 1 failed |
| `L_total_t = L_CE + L_lb + L_sep` → `L_CE + L_lb` | `test_sep_raw_wired_into_l_total` | 1 failed |
| `N_e = cfg.N_e if ... else ...` → `f_per_expert.shape[-1]` | `test_lb_N_e_comes_from_cfg_not_tensor_width` | 1 failed |

三个变异各自**恰好** 1 failed、10 passed，且失败者即预期测试 —— 证明新测试不是靠别的断言偶然转红。变异通过写回原始 bytes 还原并校验 `p.read_bytes() == orig`。

## Decision 4 — F7 删除范围

F7 表面是「`ref` 建后即删」，但删 `ref` 会让 `c` 成为未用变量。因此删除范围为 L169–L173 **整块**（`c` 的构造、`ref` 的计算、`assert ref > 0`、`del ref`），不留孤儿。docstring 尾句「(via L_sep = λ·L_sep_raw with a known L_sep_raw)」描述的是被删脚手架的用途，同步改写为「λ(t) is verified directly against the cosine closed form」。

## 归档

本 change **无 spec delta**，归档用 `--skip-specs`。因此不触发 archive 的 anchor 吞并风险（该风险仅作用于 MODIFIED Requirement 的 block 边界）。归档后仍复算三份主 spec 的 anchor 覆盖计数，作为例行核对。
