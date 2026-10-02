# Proposal

## Why

`Python-reviewer` 对 A-3 修复轮（`6593a06` 之后的 5 个 commit）做了一轮两阶段
review（先审 spec 的数学正确性，再审代码实现与数学形式化的一致性、以及 pytest
是否真的约束了原理而不只是功能），报出 13 条发现。本 change 修掉其中**全部落在本轮
scope 内**的条目。

两条 HIGH 都是**我上一轮自己引入或修补不完整**的：

1. **F1 — skeleton req-7 的前置条件不充分（C2 引入）。** 我当时写的是「每个
   per-head 投影 `z^{l,h}` 满足 `‖z^{l,h}‖₂ ≥ ε`」，但 `extract_C` 最后除的是
   **跨头均值** `z̄` 的范数。构造精确抵消（4 头 `+e₀`、4 头 `−e₀`）可得：所有
   per-head 范数恰为 1.0、前置条件满足，而 `‖z̄‖ = 0` ⇒ `extract_C` 返回
   `‖C_t‖₂ = 0.0`，Scenario 自己断言的 `= 1` 被违反。**充分条件必须落在均值上。**

2. **F2 — wayfinder req-32 有一处漏改的调用点（C4 引入）。** 同一 Scenario 族里
   `:753/:778/:788` 三处都补了 `c_centroids`，`:774` 没补，于是 spec 里留着一个
   既缺参数、又「关键字后跟位置参数」（`SyntaxError`）的调用写法。**这正是
   AC-75/AC-43「spec 声明的签名不可执行」那一类缺陷，而我上轮的结论是「已关闭」。**

一条 MEDIUM-HIGH 是我的**流程不一致**：F3 —— `UR` 的跨步聚合口径我裁决了、也实现
了，却只写进测试 docstring，没进 spec。对 AC-43/AC-17 我走 spec-first，对 AC-41
走了 code-first，违反 `CLAUDE.md` §2「想修改 DecompMoE 行为？先改 OpenSpec spec」。

一条 MEDIUM 推翻了我给用户的结论：F4 —— 我说「台账两个 spec 值来自两条不同规则」，
**实测不成立**：200 步 fixture 在两种读法下都给 0.125（不具区分力），且 0.0625 的
真实出处是 `wayfinder/tickets/A8-2.md:93` 的 **per-expert** 健康值，属范畴错误。
结论（并集读法）不变，证据已更正。

## What Changes

**spec（全部经脚本从主 spec 抽取整块生成，块级 diff 回验 + 6 项 stale-token 扫描）**

- `decompmoe-skeleton` req-7：前置条件从 per-head 范数改为**跨头均值**范数
  `‖z̄_t^l‖₂ ≥ ε`，并写明 4 正 4 负的反例。
- `wayfinder` req-32：`:774` 补 `c_centroids`；`E‖ε‖₂` 从 RMS 近似改为**精确闭式**
  `eps_std·√2·Γ((d+1)/2)/Γ(d/2) = 0.196901`（RMS `0.2` 高估 1.58%）。
- `wayfinder` req-20：`UR` 行写明窗口归约是**并集**；新增 2 条 Scenario（窗口/轴/闭式，
  无时间轴输入拒绝）；`R_H` 行补滑窗 deferral，`S_load` 行点明单步无窗口。
- `wayfinder` req-28：`target_idx` 的语义与 req-32 实际传入的 donor `j_star` 对齐。
- `governance` req-gov-1：**更正两处实测为假的容差推导**（obligation 1 的
  `abs=0` 机制、obligation 3 的 `max(1e-6, 1e-6·|expected|) = 1.17e-6`）。

**代码**

- `metrics.py`：`UR` 拒绝 `ndim ≥ 3`（`(B, N, N_e)` 无时间轴，切轴 0 会静默丢
  整批行）；返回值恒为标量。
- `sphere.py`：`torch.Generator()` → `torch.Generator(device=centroids.device)`。
  **这是 F9 的实质发现**：AC-79 只给 `randn` 加了 `device=`，Generator 本身仍在默认
  设备，torch 会拒绝用 CPU generator 向非 CPU 张量采样，**该修复在 CUDA host 上
  并没有真正闭合**。

**制品 / 台账**

- `wayfinder/tickets/A8-2.md:38/93` 按 `CLAUDE.md` §8 补
  `(historical, …; superseded by spec req-20 …)` 注释——ticket 的 UR 是 per-expert
  100 步均值，其 `< 1/32` 触发条件与 spec 的 UR 语义不是同一个量。
- C4 已归档的 `design.md` / `proposal.md` 更正 D5 的错误论据（保留结论、保留推翻过程）。
- `evidence/ledger.json` 的 AC-41 条目同步更正（`verdict_new` / `status` 不动）。

**测试**：补 8 条、改 4 条。含 F9 的 AST 属性守卫（替掉字符串匹配）、F10 的
req-18 Invariant 2 **逐步**闭式护栏、dense-mask 与 `n_i = 0` 空胞路径。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder`：req-20 / req-28 / req-32（MODIFIED）
- `decompmoe-skeleton`：req-7（MODIFIED）
- `governance`：req-gov-1（MODIFIED）

## Impact

- **受影响模块**：`metrics`、`sphere`。
- **`UR` 的拒绝面**：`ndim ≥ 3` 由「静默丢 batch 行」变为 `ValueError`。`UR` 在
  src 与 tests 中零调用点，无迁移成本。
- **`voronoi_angle` 的 Generator 设备**：在 CPU host 上**逐位不变**（默认设备就是
  CPU）；只在非 CPU host 上改变行为——而那个行为此前是**抛异常**。
- **三份 spec 的 EOL 不变**（wayfinder 纯 LF、skeleton / governance 纯 CRLF）。
- **不在本 change scope**：`.audit/**`（gitignored）、A-1/A-2/A-4/A-5/A-7 桶、
  `src/decompmoe/gating.py` 与 `wayfinder/tickets/WF-1.md`（并行 session 的在制品）、
  `n_i.clamp_min(1.0)` 在 `0 < n_i < 1` 时会静默改变结果这一**新发现的**行为
  （见 design.md D6，只记录不修）。
