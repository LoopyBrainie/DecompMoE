# Design

## Context

见 `proposal.md` — Why。此处只记录塑形了方案的现状与约束。

`wayfinder` spec 的 requirement 顺序不是数值序：`req-24` 之后紧接 `req-27`、`req-26`、`req-33`、`req-28`、`req-29`。按内容定位时不能靠「下一个 `req-N` 就是边界」推断——本次 delta 的 `## MODIFIED Requirements` 整块取自 `### Requirement: Beta Parameterization Space vs Operational Domain` 至其最后一个 Scenario（`Counterfactual β_min = 1.0 forces a 5-significant-figure γ_init`），不含 `<a id="req-24"></a>` 锚点行（锚点由归档流程管理，delta 内重复会在 archive 时产生重锚）。

`src/decompmoe/schedule.py::beta_effective` 现有 6 条测试断言（`test_schedule.py` 4 条 + `test_a3_contract_alignment.py` 2 条）全部走**显式 γ 入参**，其中两条以 `γ = −5.0` 依赖下界饱和。`test_beta_effective_phase_2_3_cap_binding`（`test_schedule.py`）已用 `γ = 0.0` 断言 `β^eff == phase_beta_max`——即本 design 选定语义的 cap 绑定行为**已被钉住**，本 change 新增的只是「`γ = 0` 是 Phase-2 入口的实际值」这一排程契约。

## Goals / Non-Goals

**Goals:**

- 让 req-14 的 operational ramp 在 Phase 2/3 逐点 `≡ cap(t)`，且交付时刻**由规范确定**而非由 `lr`/weight-decay 决定。
- 把「γ 梯度通路在哪个相位存在」从隐含推断变成显式 Scenario，附可测的边界。
- 现有 0 条测试断言被破坏。

**Non-Goals（design 层边界，超出 proposal 范围的补充）:**

- 不引入训练循环或任何 optimizer 集成。交付物是**原语 + 契约**；仓库是 formalize-only 目的地。
- 不引入可微的 `beta_effective` 变体。若未来要 Phase 2/3 的 γ 学习信号，那是独立 change（见 Open Questions）。
- 不新增梯度上界常量。饱和区推导链写进 `beta.py` 注释即可。

## Decisions

### D1 — ramp 是 normative；γ 梯度通路自 Phase 4 起存在

req-14 的 ramp 与 req-24 的 `Clamp(β^param(γ), 1.0, cap(t))` 在数学上互斥：两条同时成立要求 `β^eff ≡ cap(t)`，而 `Clamp(x,·,cap) ≡ cap ⟺ x ≥ cap`，此点 `∂β^eff/∂γ = 0`。**必须选一条**。

选 ramp。理由：ramp 是 req-14 的**显式行为契约**（"operational β ramping `1.0 → 4.0` / `4.0 → 16.0`"），而 γ 梯度在任何 spec 中都**从未被声称过**——`wayfinder` 的 "Gradient Channel (AdamW)" 语义原文是 `governs c_i.requires_grad` 与 across-P AdamW registration，skeleton req-20 对 `beta_effective` 的可微性完全沉默。冻结集描述的是**参数组成员资格**，不是「该参数的损失梯度非零」；零梯度下 decoupled weight decay 照样更新参数组成员，两者不矛盾。

**被否决的替代方案**：(b) 改 spec 对齐「γ 可训」——需给出 γ 在 30 000 步内从 `−3.5` 爬到 `≥ logit(3.9/31.9) = −1.9709` 的训练动力学 derivation，本 design 无此依据，且按 `CLAUDE.md` §6 第 8 条属 policy-first。(c) 引入独立排程量 `β^op(t)` 让 cap 不再兼任 ramp——唯一真能同时满足两者的方案，但要改 req-24 的核心公式，改动面与本 change 的保守姿态不匹配。

**连带结果**：审计头条结论「Phase 1–3 无 γ 梯度通路」从误报转为显式语义——Phase 1 常数函数、Phase 2/3 上界饱和、Phase 4 无 clamp 故有通路。

### D2 — 契约由既有 `beta_effective` + 具名锚点承载；`beta_effective` 签名与函数体不动

**证据强制，非偏好**。`test_beta_effective_phase_2_3_use_inverse_temperature` 传 `γ = −5.0` 期望下界饱和得 `1.0`；`test_beta_effective_at_100k_is_unchanged` 传 `−5.0` 与 `0.0`。若让 `beta_effective` 在 Phase 2/3 忽略传入 γ 并改用 reset 值，这两条立刻变红，且需连带修改 `decompmoe-skeleton` req-20/req-33 的签名契约。

**被否决的替代方案 (a)**：在 `beta_effective` 内部把 Phase 2/3 的 γ 替换为 reset 值。代价 = 2 条既有断言变红 + 跨 capability 签名改动 + 语义变更与「显式 γ 入参」的可测试性冲突。

**被否决的替代方案 (b)**：新增 `beta_effective_operational(phase, step, total_steps)` 作为无 γ 的 operational 读取路径。**实现阶段经审查后撤销**，理由是它在 D1 语义下**零可计算内容**：Phase 2–3 饱和后 `β^eff ≡ phase_beta_max(phase, step)`，而 `phase_beta_max` 已存在且已是公开符号；该函数唯一语义是它在 Phase 2–3 上的别名。更糟的是它与 `beta_effective` 构成**永久命名漂移风险**——名字暗示「这才是真正的 operational β」，下一轮 audit 必问「这两个函数谁是真相」。点式相等这个不变量完全可以用既有符号钉成 Scenario，不需要第三个名字。

**实际落地**：只保留 `gamma_reset_for_phase2()` 一个新符号——与 `gamma_reset_for_phase4`（req-20 已公开，带闭式 + 精度钉定 Scenario）对称；「Phase-2 入口 γ MUST reset」是训练回路侧的义务，formalize-only 仓里需要一个**具名、可 grep、可单测的锚点**让该义务落地。ramp 的点式相等由 `beta_effective(gamma_reset_for_phase2(), phase, step)` 对 `phase_beta_max` 的 **bit-exact 断言**守护（见 D4）。

### D3 — reset 目标取 `γ = 0.0`，不是最小可行 γ

饱和条件是 `β^param(γ) ≥ phase_beta_max(3, 55_999) = 15.9996`，即 `γ ≥ logit(0.498420) ≈ −0.006318`。取**最小**可行值可把裕量压到 `3.4e-5`；取 `γ = 0.0` 得裕量 `5.04e-2`（**1483 倍**），且 `γ = 0` 恰是 decoupled weight decay 的不动点 —— Phase 3 β_i 解冻时 weight decay 作用在 `γ = 0` 上仍为 `0`，γ 自稳定，不需要额外 momentum reset。

该取值与仓库内既有模式 `gamma_reset_for_phase4(beta_p3)` 同构（后者返回 `math.log(beta_p3 - 1.0) - math.log(BETA_MAX - beta_p3)`）；`gamma_reset_for_phase2()` 无参、返回 `0.0`，形状对齐但更简。

### D4 — 梯度断言在测试内联组合原语，不新增生产 API

Phase 1–3 的梯度断言需要一条可微组合路径。`beta_effective` 是 float-only，无法承载；`decompmoe.beta` 的 `inverse_temperature` / `phase4_inverse_temperature` 已足够。测试内联组合 `Clamp(inverse_temperature(γ_t), 1.0, phase_beta_max(...))` 即可，**不引入新的生产符号**——契约属于 spec，不属于 API 表面。

**这条是防回归核心**：数值闭式（`∂β^eff/∂γ ≡ 0`）与存在性（`grad_fn is not None`）两者都过、而通路仍在 API 面断掉，正是 `beta_effective` 现有缺陷类。

### D5 — 三个梯度量必须在 Scenario 里显式区分

`7.75 = 31·σ'(0)`（`γ' = 0` 处的上界，`decompmoe/beta.py` 已导出并被 `tests/test_beta.py` 钉住）、`240/31 ≈ 7.7419355`（reset 点 `γ' = ln(15/16)` 处的斜率）、`0.9077 = 31.9·σ'(−3.5)`（`γ_init` 处的**参数域**量）。三者是不同量。审计清单曾把 reset 点斜率与上界混谈，而「Phase-4 重开通路」那条反驳在 API 面上根本不成立（Phase 4 分支同样走 `as_tensor(float)` → `.item()`）。Scenario 必须写明各自语义域，否则下轮审计会把它们互换。

> **本 design 初稿在此处犯过一次错并已修正**：初稿把 reset 点斜率写成 `240/961 ≈ 7.7419`。`240/961 = 0.2497` 是 `σ'(γ')` 本身；β 侧梯度还要乘 `31`，故为 `240/31`。这个错误恰好就是 D5 要防的那一类——把 σ′ 与 `dβ/dγ` 混为一谈。守护测试的断言值从一开始就用的是 `240/31`，所以测试是绿的，错的是文档。

### D6 — req-1 的三个公开面计数随新符号 bump（跨 capability）

`gamma_reset_for_phase2` 是新公开符号，必须进 `schedule.__all__` 与 `decompmoe.__all__`。这直接改动 `decompmoe-skeleton` req-1 的三个**规范性**计数（不是描述性统计——原文带 "SHALL expose a stable `__all__` listing every public symbol" + 去重规则 + "MUST NOT: summing … yields 76"）：

| | 前 | 后 |
|---|---|---|
| 去重 union | 75 | **76** |
| 未去重 per-module sum | 76 | **77** |
| 包级 `__all__` | 78 | **79** |

新符号无跨模块同名碰撞，去重规则叙述与「唯一碰撞是 `flops_per_token`」这句话**不变**。

**被否决的替代方案**：让新符号**不进任何 `__all__`**（保持 75/76/78）。这样 0 断言改动、change 也不跨 capability——但**新符号公开却不上 `__all__`，就是同时违反 req-1 的枚举义务与计数 guard**，等于把契约藏起来躲过 spec，正是这套治理要防的漂移模式。计数被钉成契约，正是为了强制「加公开符号 ⇒ 显式 bump」这个动作可见。

### D7 — 精度帧：float32 帧内 bit-exact，float64 帧偏移只作文档

`torch.as_tensor(<python float>)` 产生 **float32** 张量，而 `phase_beta_max` 是纯 Python float（**float64**）。所以「`β^eff` MUST equal `phase_beta_max` pointwise」在 float32 下**字面不成立**：`float32(15.9996) = 15.999600410461426` vs `float64 = 15.999600000000001`，差 `4.10e-7`。

**这是既有实现的潜伏缺陷，被本 change 的新探针第一次暴露**：`beta_effective` 一直返回 float32 舍入后的 cap，而既有测试的规范 cap 值（`1.0` / `2.5` / `4.0` / `10.0`）**全部能被 float32 精确表示**，所以从未触发。`15.9996` 是第一个不能的。

**裁决：在 float32 操作帧内用 bit-exact 断言（`torch.equal`，无容差、不会 flaky），float64 帧偏移降级为文档。** 仓内已有定型先例：`decompmoe-skeleton` req-19（`spherical_l2_normalize`）把标题里的 "equals 1.0" 降级为 DISPLAY FORM、改钉维度相关的可证界 + 实测包络，并明令 MUST NOT restate as bare `==`；`governance` req-gov-1 的双帧器具（spec-literal 帧 vs impl-internal 帧）同理。饱和分支返回的就是 `float32(cap)`，故 bit-exact 是**构造性**成立，不是靠调容差凑出来的。

**被否决的替代方案 (a) 把 operational 路径升 float64**：换来的「精确」只是下一层量子化（float64 在 16 处 ulp ≈ `3.6e-15`），而代价是实打实的——与 `beta_effective` / logit 热路径的 float32 计算惯例之间出现跨 dtype 边界，下游 `β·(Cᵀc − 1)` 面临提升风险，且「升到哪里为止」是任意的（logit 要不要也升？）。D2 砍掉 `beta_effective_operational` 之后，这条路更无触发器。

**被否决的替代方案 (c) 连 `beta_effective` 一起升 float64**：超出本 change 范围（无改动理由——D2 已砍掉别名，dtype 问题随别名一起消失）。若将来 logit 侧确有 float32 精度问题，另开 change。

**数值自洽核验**：`float32(16.05) ≈ 16.0499992 > float32(15.9996) ≈ 15.9995995`，饱和在 float32 帧内同样**严格**成立，bit-exact 断言因此安全。

## Risks / Trade-offs

- **[风险] `β^param` 与 `β^eff` 在 Phase 2/3 长期脱钩** —— `β^param ≡ 16.05` 而 `β^eff` 走 `1.0 → 15.9996`。这是 ramp 由 cap 交付的必然结果。→ 缓解：在 Scenario 1 的措辞里显式说明「ramp 由 schedule cap 交付，不由 `β^param` 的值交付」，避免下轮审计把它读成实现走偏。
- **[风险] `γ_init ≈ −3.5` 在操作域降为 vestigial** —— Phase 1 的 `β^eff = 1.0` 与 γ 无关，Phase 2 入口被 reset，`σ'(−3.5) ≈ 0.02845` 的冷启动梯度永不被使用。→ 缓解：既有的 "Parameterization floor preserves cold-start gradient" Scenario **不删**（`β_min = 0.1` 的反事实论证仍支撑参数化空间的选择），但 Scenario 2 明写 `0.9077` 是参数域量、不是操作域量。
- **[风险] Phase 2 的 ramp 起点从 `1.0` 变为 `cap(2, 6_000) = 1.0`（不变），但后续立刻贴 cap** —— `β^eff` 在 `step = 6_000` 仍为 `1.0`（`cap` 起点），与 req-14 的 `1.0 → 4.0` 起点一致，无回归。→ 缓解：新测试在 `6_000` / `13_000` / `25_999` 三点断言。
- **[风险] `decompmoe-skeleton/spec.md:492` 声明 `beta_effective` 签名 "exactly 3 positional args"，代码为 3 位置 + `total_steps` 默认参** —— 属**已登记的既有漂移**（AC-44 引入 `total_steps` 时留下）。本 change 不修。→ 缓解：登记为已知漂移；若并行 session 正在修该文件，不要同文件双写。
- **[权衡] 放弃 Phase 2/3 的 γ 学习信号** —— 换来了 ramp 的确定性交付。真正想要 γ 学习信号时，正确做法是引入 D1 中被否决的 (c)（独立排程量），而不是让 cap 兼职 ramp。

## Migration Plan

无迁移面。改动限于 `src/decompmoe/schedule.py`（新增 2 符号 + `__all__` + 一处 docstring）、`src/decompmoe/beta.py`（仅注释）、`tests/test_schedule.py`（新增 5 断言）、`tests/test_a3_contract_alignment.py`（一行注释数字）。回滚 = revert 单个 commit，`beta_effective` 的既有行为从未改变，故无兼容期。

## Open Questions

- **Phase 2/3 是否最终需要 γ 的学习信号？** 若需要，D1 的 (c)（引入独立排程量 `β^op(t)`，让 cap 专职做上界）是唯一同时满足 req-14 与梯度需求的方案，会改动 req-24 的核心公式，属独立 change。此问题**可以安全推迟**：它不改变本 change 的 spec、方案或任务分解。
- **`decompmoe-skeleton/spec.md:490/:492` 的 `beta_effective` 签名漂移由谁收口？** 可安全推迟到并行 session 或独立 change。
