# Proposal

## Why

C3 关掉的是「代码偏离已定稿契约」的一类缺陷；本 change 处理的是**另一类：契约本身
不足，或代码用一条 spec 未禁止的捷径绕过了契约**。三条都改变数值输出或调用签名，
因此与 C3 分开交付，以便单独回滚。

1. **AC-43 复活返回的是裸 ε。** `resurrect_expert` 把
   `resurrection_perturb_distribution` 的输出原样当作「扰动后的质心」返回，即
   `ε ~ N(0, 0.05²·I)`。而 wayfinder req-28 要求扰动的是**克隆出的那个专家**。
   后果有两层，且互相独立：`E‖ε‖₂ ≈ 0.2`（`d_c=16, eps_std=0.05`）使返回值根本
   不在单位球面上，赋给 `c_i` 会**先于任何其它不变量**破坏 `S^{d_c-1}`；同时该向量
   与供体近似正交（`E[cos] = -0.000289`，`90.0177°`），复活被做成了一个与供体无关
   的随机方向。

2. **AC-76 docstring 与实参不符。** docstring 声称 `c_perturbed` 来自
   `resurrection_perturb_distribution(torch.empty(0), j_star, ...)`，实际传的是
   `f_per_expert`（= `β_per_expert.detach()`），且遗漏了 `dim` 已成必填。req-32 的
   same-call-stack 契约正是以该 docstring 作为人类可读依据。

3. **AC-17 `mask=None` 广播同一均值。** `CentroidDriver.step` 给 `mask` 写了默认值
   `None`，并在该分支用 `X.mean(dim=0)` 展开给全部质心——16 个质心因此完全坍缩到
   同一点（5999 步后平均成对 cos → `+1.000000`）。skeleton req-18 明写 `mask` 是
   必填位置参、且实现 MUST 拒绝缺失的 `mask` 而不是替代它。
   重判同时更正了原 finding 的一处错误表述：这不是「零测试覆盖」，而是**三个测试
   以 `atol=1e-5` 精确钉住了这个退化闭式**（它们靠省略参数进入该分支）。

4. **AC-41 `UR` 的 W=100 窗口未实现。** req-20 写死「over the most recent
   `W = 100` steps」，实现却对任意长度历史直接 reduce。200 步历史给出 0.1875，
   而窗口语义下应为 0.125。该指标在 src 与 tests 中零调用点，因此修正轴语义零成本。

## What Changes

- **spec（`wayfinder` req-32，MODIFIED）**：为 `resurrect_expert` 声明必填的按次调用
  参数 `c_centroids: Tensor`（形状 `(N_e, d_c)`），并把 Scenario 的 `c_perturbed`
  从「primitive 的裸 ε 输出」改为 `L2Normalize(c_centroids[j_star] + ε)`，附两条新
  断言（`‖c_perturbed‖₂ == 1.0` within `abs=1e-6`；`cos(c_perturbed, c_centroids[j_star]) > 0`）
  与一条新 Scenario（克隆源是 donor 行）。
- `safeguards.py`：按上述签名实现克隆-扰动；重写 docstring（结清 AC-76）。
- `extraction.py`：`mask` 改必填位置参；**删除** `mask is None` 的全批均值替代分支；
  显式 `mask=None` 以 `TypeError` 拒绝。
- `metrics.py`：`UR` 加 `_UR_WINDOW_STEPS = 100` 窗口切片与显式轴语义说明。
- 测试：`tests/test_a3_contract_alignment.py` 续写 13 条（AC-43/76/17/41）；
  `test_safeguards.py` 3 处调用点补 `c_centroids`；`test_extraction_phase.py` 与
  `test_extraction.py` 共 9 处调用点补 `mask`，其中 3 个退化期望值重写。

**不改动**：路由数学（`gating_logits` / top-k / local_softmax）、`R_H` 与 `S_load`
的签名（理由见 design.md D5）、任何 spec 之外的新增 Requirement。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder`：req-32（MODIFIED）——见 `specs/wayfinder/spec.md`。

## Impact

- **受影响模块**：`safeguards` / `extraction` / `metrics`。
- **数值输出变化**：`resurrect_expert` 的第一个返回值由「裸 ε」变为「球面上的
  donor 邻域点」，`CentroidDriver.step` 的省略-`mask` 路径消失。这两处都是把
  行为改回 spec 已声明的语义，不是新功能。
- **调用点全部在 tests 内**：两个被改签名的函数在 `src/` 中零生产调用点，故
  无生产代码需要同步修改。
- **AC-41 的一处口径裁决已记录**：req-20 对 `UR` 的跨步聚合**没有闭式 Scenario**，
  两种读法都与文本相容。本 change 采纳与 spec 自身英文注解一致的「窗口内取并集」，
  并把该裁决与其依据写进 design.md D5。**注意**：初稿曾以「台账的两个 spec 值来自两条
  不同规则」作为冲突证据，该论据经 R1 review 实测推翻（200 步 fixture 对两种读法
  给出同一个 0.125，不具区分力；0.0625 的真实出处是 `wayfinder/tickets/A8-2.md`
  的 per-expert 健康值，属范畴错误）。结论不变，证据已更正，见 design.md 的
  「D5 更正」。
- **共享工作树隔离**：`src/decompmoe/gating.py` 自 pin 起即为 modified-uncommitted
  （`baseline.json` 已登记），与本 change 无关，全程选择性暂存，**未**纳入。
