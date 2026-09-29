# Design

## Decision 1 — 驳回 B5：spec 的两档分层是有意设计

**裁定**：**驳回**，不改测试、不改 spec。

**依据**：`openspec/specs/decompmoe-skeleton/spec.md` req-6 对 `canonical_voronoi_angle` 的契约**明文**写道：

> its 4-decimal prose display `≈ 1.1735 rad (≈ 67.24°)` is the canonical spec form frozen in `CLAUDE.md` §5 and MUST NOT be paired with the `abs=1e-6` tolerance, because the impl bisection output `1.1735482746999482` is `4.83e-5` away from that 4-decimal literal (`48×` the tolerance) — the 4-decimal display is instead guarded by exact `round(θ, 4) == 1.1735` and `round(math.degrees(θ), 2) == 67.24`

`governance/spec.md` obligation 3（`spec.md:17`）同样把两者显式分层：6dp bisection test literals（`1.173548` / `1.165848` / `1.020506`）由 `pytest.approx(..., abs=1e-6)` 守护并 pin 在 `test_voronoi_monotone_in_ne` / `test_voronoi_canonical_N_e_dependence`；4dp canonical spec literal 是**另一个物**，不承担精度职责。

**finding 成立的部分与不成立的部分**：

- 成立：`round(θ, 4) == 1.1735` 的接受窗口 `[1.17345, 1.17355)` 宽 `1e-4`，恰为同测试上方 `abs=1e-6` 的 **100×**；impl 输出 `1.1735482746999482` 与真根 `1.17354742591971747` 都 round 到 `1.1735`，故该断言**测不出** `8.4878e-7` 的 frame bias。
- 不成立：这正是**设计意图**。精度职责由 6dp `approx(abs=1e-6)` 承担，`round()` 只承担「4dp 显示档取整结果」这一独立物。删除 `round()` 会丢失对 spec 显示形式的守护；改用 `approx(1.1735, abs=...)` 则须为 `4.83e-5` 的偏移重新论证容差取值，且推翻 `b23f0e5` 的显式 task 决定。

**finding 自身的引用错误**（实施时勿照抄）：

- 「收紧 governance L98 到 `1e-6`」——错文件。`b23f0e5` 的 `abs=1e-4 → abs=1e-6` 改的是 `openspec/specs/decompmoe-skeleton/spec.md:98`；`git show b23f0e5^:openspec/specs/governance/spec.md` 显示 governance 在该 commit **之前**就已是 `1e-6`。
- 「同测试上方 6 行」——错。`approx(1.173548, abs=1e-6)` 在 `test_sphere.py:94` 的 `test_voronoi_monotone_in_ne`；`round()` 断言在 `:116-117` 的 `test_voronoi_canonical_mvp_value`，**不同函数、相隔 22 行**。

**记录目的**：防止下一轮 reviewer 以同一条「窗口宽 100×」论证重复提。本条应与 `CLAUDE.md` 中「条款式指控先核对 WHEN 作用域」的教训同族阅读。

---

## Decision 2 — B4 残余部分：`core = 33_554_432` 保持字面量

**裁定**：不参数化。

**依据**：`33_554_432` 是 `governance/spec.md` Scenario「Closed-form FLOPs totals use bare `==`」**点名的 spec 锚定整数闭式**。按 `a7` design.md Decision 4 已确立的**不对称规则**：

- 硬编码 **config 字段**（`H_kv`）= 真 bug → 必须改取 `cfg.H_kv`（`a7` 已做，本 change 不重复）。
- 硬编码 **spec 字面量**（`128` / `144` / `66_080` / `33_554_432`）= **钉值，禁止改写成推导式**。推导式按构造产出该值，spec 怎么改分解它都绿，把可失败的 pin 换成恒真式。

`d_model` 漂移的担忧由 `tests/test_config.py:27` `assert cfg.d_model == 1024` 覆盖——config 改值会在该处变红，不会静默。

---

## Decision 3 — `test_gating.py:59` 明确排除

**裁定**：保留 `torch.all(grad[is_neg_inf] == 0.0)` 裸 `==`，不迁移。

**依据**：`req-gov-1` obligation 2 的作用域是「**spec-anchored** closed-form float claims」。该断言是对 `-inf` logit 位置梯度恒零的**谓词检查**（对应 `local_softmax` 对 `neg_inf` 掩码位置的零梯度性质），不是任何 spec 闭式数值声明的实例。`test_gating.py:111-118 test_convex_combination_dtype_safe` 另有 dtype 守护。迁移它不会提升任何 spec↔测试的对账能力，只会制造噪音。

记录目的：finding 清单把它列入同类，实施时勿顺手改。

---

## Decision 4 — B9 根因追溯：偏移起点 `af91717`

`git log -S` 逐符号回溯，三条线索**全部收敛到同一 commit**：

```
$ git log --oneline -S 'test_voronoi_measurement_layer' -- tests/test_sphere.py
af91717 feat(sphere): canonical Voronoi via Beta inversion + measurement layer
$ git log --oneline -S 'math.pi / 2'  -- tests/test_sphere.py
af91717 （同上）
$ git log --oneline -S 'mean_chord'   -- src/decompmoe/sphere.py
af91717 （同上）
```

**第 1 环（根）—— `af91717` 的假收敛声明。** 该 commit 同时写入实现 `θ = arccos(1 − mean_pairwise_chord)`、秩-3 夹具、`π/2` 上界，并留下一句至今仍活在 `src/decompmoe/sphere.py:179-181` 的 docstring：

> For N_e equal-area Voronoi cells on `S^{d_c − 1}`, this converges to `canonical_voronoi_angle` as the routing distribution approaches the equal-area ideal.

**该声明已被证伪，不是「未证明」。** 决定性实测——crosspolytope 的 32 个顶点 `±e_i` 在 `S^15` 上构成一个**精确等面积**划分（32 个 facet 全等）：

```
crosspolytope(32 pts, EXACT equal-area) theta = 2.018736 rad (115.6651°)
canonical_voronoi_angle(32, 16)          = 1.091607 rad ( 62.5445°)
→ 偏差 0.9271295 rad，relative error 84.9%
```

即：**即使在数学上完美的等面积极限下，该统计量离 canonical 也有 85% 之远**。

**但「根因是平均口径」这一判断是错的 —— review 后修正。** `chord = √(2·versine)`，故正确反解是 `θ = arccos(1 − c²/2)`；实现写的是 `arccos(1 − c)`，把**弦长**喂进了要 **versine** 的槽位。这是一个独立的、更早的公式错误。实测（用正单纯形使所有成对等角、平均精确，从而只测反解）：

| 真值 | 正确反解 | 实现 | 反解误差 |
|---|---|---|---|
| 10.0000° | 10.0000° | 34.3416° | +24.3416 |
| 45.0000° | 45.0000° | 76.4300° | +31.4300 |
| 60.0000° | 60.0000° | 90.0000° | +30.0000 |
| 120.0000° | 120.0000° | 137.0586° | +17.0586 |
| 150.0000° | 150.0000° | 158.7253° | +8.7253 |

正确反解在每个采样角度都**精确复现真值**；实现输出被抬高 **+8.73°…+31.43°**。

在 crosspolytope 理想上分解两个缺陷的贡献：

```
实现输出                    115.6651°
仅修正反解（仍全对平均）      91.5415°
canonical_voronoi_angle(32,16)  62.5445°
→ 反解占 impl→canonical 差额的 45.4%，平均口径占其余
```

**因此：只修平均口径的接手者仍会偏约 29°。** 本 change 初版把 crosspolytope 数字登记为「现成证据」是**不完整的**，已按上表补全，并把反解缺陷单列为移交项 1。

**第 2 环（掩盖）—— 秩-3 夹具。** `tests/test_sphere.py:213-217` 只填 `v[0] / v[1] / v[2]`，其余 13 维恒 0，故夹具是 S² 嵌入 R¹⁶（实测有效秩 3/16），**不是 S¹⁵ 上的分布**。`:203` 的注释却写「Generate Fibonacci-sphere points on `S^{d_c − 1}`」。`af91717` 当时是**诚实的**（注释写「projects poorly into R^16, so we use a loose tolerance」）。

**第 3 环（固化）—— `b23f0e5`。** 经 `fix-review-findings-voronoi-precision-and-lineage` 的 task 2.2.3（状态 `[~]` DEVIATION）：Python reviewer 正确指出 L7 近空转、要求收紧到 `abs=1e-6`，apply 实测失败（`actual_delta_rad=8.154e-01`）。作者随后**删除了当时诚实的自认注释**，**替换为伪造的定理**（`tasks.md:103-104`：「这是**物理导出的**上界 —— 实现胞元距 canonical 半角不可能超过半球」）。该定理在 `openspec/specs/**` 中 **0 命中**，是 change 记录自创物；反例存在：15 点塌缩到一处 + 1 个对跖点，Δ=0.4508 < π/2 仍通过两条断言。

**本 change 的处置（T5）**：只切断第 1、3 环 —— 删除 `sphere.py` 的假收敛声明与伪反解描述、删除测试里的伪定理、如实描述夹具秩。**`π/2` 断言数值不动**，另加 crosspolytope 已知答案见证（`test_voronoi_angle_known_answer_crosspolytope`）钉住 `115.6651°` —— 此前 `π/2` 界容忍 0.815 rad 偏差，**对本函数的输出完全不敏感**，任何公式改动都不会让它变红。

**明确移交（proposal 移交项 1–3）**：`voronoi_angle` 的反解缺陷、平均口径缺陷、以及 `decompmoe-skeleton` req-6 的「realized half-angle」契约措辞。实施时 `skeleton-l98` 已归档、该 Requirement 已释放，但修正属**行为变更**，`CLAUDE.md` §6 禁止绕过 OpenSpec 直接改，须另开专项 change 并按 §6 末条给出推导。

---

## Decision 5 — T4：改锚 MCI 下界；**删除**无数学关联的经验 CV 块

> **本 Decision 在 review 后被推翻并重写。** 初版裁定「把经验块收紧为 spec 逐字 claim `>= lower_bound`」。该裁定是错的，理由见下。

**初版的问题**：初版认为 `cv_estimated > lower_bound - 1e-2` 比 spec 的 `CV ≥ 1/d_c` 更弱，收紧到逐字形式即「回归 spec」。但初版**没有检查 `cv_estimated` 到底在算什么**。它算的是

```
cv_estimated = sqrt( max_t  2(1 − T_t · ĉ) )      ĉ = 归一化的经验均值方向
```

即「到经验均值方向的**最大弦距**」，而 spec 的 `CV` 是**凸包半径**。对各向同性样本，`T_t·ĉ ~ N(0, ‖ĉ‖²)` 且 `‖ĉ‖² ≈ 1/d_c`，10⁴ 个样本的 max 约 `4σ ≈ 1.0` —— 这个量**与 `d_c` 几乎无关**，与 `1/d_c` **没有任何数学关联**。实测松弛 30.7×（1.9212 / 0.0625）。

**推翻理由**：把断言从 `> 1/d_c − 1e-2` 收紧到 `>= 1/d_c`，只是从一个**没有推导的**界里去掉松弛，得到一个**依然没有推导的**更紧的界。它让一个错误数字看起来更可信，而没有增加任何探测能力 —— 这正是 `CLAUDE.md` §6 末条禁止的 policy-first 收口。

**重写后的裁定**：

1. **删除**经验 CV 块。它守护的 spec claim（`CV ≥ 1/d_c`）在本仓**没有实现**，补守护需要先给几何推导 —— 登记为移交项 4。
2. **改锚到 `metrics.MCI` 的下界**。`MCI` 是本仓真正实现且可测的量，其 rank-1 下界恰为 `1/d_c`。断言形式为

   ```
   health_target (0.05) < mci_floor        # mci_floor = MCI(rank-1) = 0.0625
   ```

   「health target 不可达」是关于**下界**的陈述，故必须与下界比较。初版写的 `health_target < mci_empirical`（`0.05 < 0.9987`）是拿 health target 与**典型值**比 —— 即使 `MCI` 被地板抬到 0.06 它也照样绿，形同虚设。

3. **不重复断言 `MCI(rank-1) == 1/d_c`**：该断言已由 `test_mci_rank1_token_distribution` 与 `test_mci_uncentered_both_endpoints_attainable_principle` 覆盖，第三次复制不守任何新东西。

**验收**：把 `metrics.MCI` 改为恒返回 0 → `health_target < mci_floor` 变红（已实测）。

**保留的部分**：初版拒绝发明 `0.25` 这类新阈值的判断仍然成立 —— 未采用 `cv_estimated > 0.25`，理由是 0.25 不是 spec 里的任何值。重写后该块被整体删除，该问题自然消解。

---

## Decision 6 — T1：AST 路线保留，但降级为**结构普查**（review 后修正）

`governance/spec.md:45` clause (3) 明列三种 acceptable mechanism：`torch.profiler`、custom hooks、`inspect.getsource` / AST analysis。

**选 AST 的依据不变且成立**：profiler 路径 backend-dependent（CUDA kernel fusion 可致 2× 偏差），会让断言在不同后端取不同值，违背 `req-gov-1` 的钉值意图。AST 是源码级、与硬件无关，且 clause (3) 明列认可。

### 初版实现被 review 推翻

初版写了一个「MAC 计量器」：遍历 `extract_C` 源码，按算子类型乘以调用方给的 `H_kv·d_k·d_c` 因子，得出 `33_040` 与 spec 字面量对账。**它不测 MAC。** 复核证据（`uv run python` 实测）：

| 变异 | 计数器 | 真值 | 结果 |
|---|---|---|---|
| baseline | 33_040 | 33_040 | — |
| 删掉跨头 mean | **33_040** | 32_416 | **绿（漏）** |
| 删掉 bias 加 | **33_040** | 32_912 | **绿（漏）** |
| einsum 提取成 helper（0 MAC 变化） | **160** | 33_040 | **红（假失败）** |

根因：`_rank_of` 对任何投影算子**硬编码返回 4**、对 mean 硬编码 3，**从不恢复任何维度**；每个乘数都由调用方 `MVPConfig` 供给而非从源码读出。于是「MAC 数」= 测试自己选的常数 × 测试自己数的算子数 —— 实现怎么改它都可能同意。

`unaccounted_reduction` 桶同样不可用：它把跨头 mean 记作 `1 × d_c = 16` MAC，而真实代价是每通道 `H_kv` 次乘 + `H_kv−1` 次加，× `d_c` 通道 = **240 ops（≥128 MAC）**，低估 8–15×；且从未被任何断言读取。「报出来但不断言」是三个选项里最差的一个。

### 重写后的裁定

**AST 降级为结构普查**，只数算子集合，不算量级：

```
census == {"projection": 2, "bias_add": 1, "l2_normalize": 2, "reduction": 1}
```

**`33_040` 保持 spec 字面量钉值**，由裸 `==` 对账（clause (1)）。量级是闭式自己的职责，不是 AST 的职责。

**为什么这仍然满足 clause (3) 的意图**：clause (3) 禁止的是「用重述闭式的 helper 推导数量」（tautology）。结构普查读的是**真实源码**，对实现的算子集合敏感 —— 删 mean、删投影、删归一、加第三个投影、删 bias，五种变异全部变红（已实测）。它不再冒充量级测量。

**已知局限（诚实记录）**：遍历是词法地限于 `extract_C` 自身函数体。把投影提取成模块级 helper 是**语义保持**的重构，普查会（正确地、但无益地）报「无投影」。它是结构守护，不是重构容忍型守护。

**scaling 断言（`m2 == 2*m1` / `m4 - m3 == d_k_step_contrib`）保持不动**：它们守护闭式的结构性性质（各项对 `d_c` 线性、`d_k` 步长项独立），不是实现。两者职责不同。

---

## Decision 7 — T2 迁移的诚实标注

`test_beta.py:107` 的 `beta.BETA_MIN == 0.1` 迁移到 `approx(..., abs=...)` 是**形式合规**，**不是探测能力增强**。

- obligation 2（`spec.md:15`）逐字覆盖它（`0.1` 非二进制精确，属「carries floating-point rounding」）。
- 但裸 `==` 在此**比 `approx` 更严**：`approx(0.1, abs=1e-9)` 会放过 `0.1 + 1e-10` 的漂移，裸 `==` 不会。
- 迁移的**真实理由**是消除「同仓两套规则并存」——同一文件 `:219` 刚 `assert isinstance(beta.MAX_GRAD_PER_C, float)`，两行后就套用整数规则。

`design.md` 与 `tasks.md` 必须如实写明，不得包装成「探测能力增强」。

**优先级**：`test_safeguards.py:690-691` docstring 与 `:712-715` 注释中「`MAX_GRAD_PER_C = 32.0` 是 integer closed-form」的错误规则表述是本 task **最高优先**项 —— 它把错误规则写进注释供后人复制，其危害高于断言本身。同文件 `:693-711` 已对三个同为 `Final[float]` 的常量正确使用 `approx(abs=1e-12)`，文件自身即自相矛盾。

---

## Decision 8 — T3 的 req-16 delta 程序化构造

按仓库既有纪律（`CLAUDE.md` §3 + 历次 change 实践）：

1. `block(lines, "### Requirement: Prefill And Decode Share The Same Algorithm")` 从 header 行抽到下一个 `### Requirement:` / `<a id=` 之前。
2. delta 内**不写** `<a id="req-16"></a>` anchor（archive 的替换范围从 `### Requirement:` 起，anchor 在 block 之外不会丢；仓库既有 archived delta 也是此惯例）。
3. 每次定点替换**断言命中次数 == 1**，target 用短且无歧义的锚（`16 floats = 64 bytes`）。
4. `difflib.SequenceMatcher` 出 op 列表作**展示**（不按 opcode 类型判 FAIL——较长替换在字符级必然产生 `insert` opcode）。
5. **往返验证**须按 header 整体反向（同一 Requirement 承载多条 edit，逐条反向永远不等）。
6. **反引号配平检查**：往返验证无法捕获未闭合反引号（缺陷在「我的新文本」里，反向后逐字节等于原文）。
7. block 内**逐字包含一行既有失效 code span**（`...for `d_c = 16`);` — `;` + 反引号）。按 `CLAUDE.md` §3 surgical **原样保留、不代为修复**（a7 proposal 已把 wayfinder 的 8 行同类登记为 out-of-scope）。用「反向验证该行在主 spec 中逐字存在」证明其为既有问题。
