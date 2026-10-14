# Design

## Context

见 `proposal.md` — Why。本文件只记录实现路径所需的事实与取舍。

执行基线：`HEAD 3c64cdc`（`dev`，264 commits）。`uv run python scripts/run_gates.py` 当前 `GATE OK` exit 0（7 lint 全 PASS、anchor coverage **74 anchor(s) across 3 capabilit(ies)**、541 passed / 1 skipped）。

台账 `.audit/gradual-review-2026-10-07/lists/opsx-changes.md` 的 pin 为 `dde0e1d`，距 HEAD `+3` commits（全部为 `archive(...)`）。本轮逐条复核发现该 pin 下的 OPX-2 桶**有 1 条已被后续 commit 消解、2 条被自己的复核注记否定、仅 2 条仍成立**——若照单执行会付出修复不存在缺陷的纯负成本。相关实测事实：

- `FIX-001`（49 处 `allclose` 省略 `rtol`）**已消解**：`df4a1d2` 新增 `scripts/lint_no_implicit_relative_tolerance.py`，7 lint 中已有它。（不在本 change 范围，仅记录 pin 漂移。）
- `FIX-034` / `FIX-042` **判定不成立**，见 D-4。
- `FIX-006` / `FIX-007` **成立**，见 D-1 / D-3。

两条硬约束在实现中必须被尊重：

1. `decompmoe-skeleton` `#req-22` 按 `#req-23` 的明文规定**逐字镜像** `wayfinder` `#req-20` 的闭式行。故任何 SP 语义改动必须**成对**落两份 spec，不得只改一侧。
2. 归档须走 `req-gov-10` 的 anchor 四步协议（写账本 → 归档 → 比对 → 手术式补回 → 复测），且**禁止重跑 archive** 修复被吞的 anchor。

工作树现存 3 处未提交修改（`.gitignore`、`src/decompmoe/gating.py`、`wayfinder/tickets/WF-1.md`），经用户裁定**完全不动**：不触碰、不暂存、不落定。门禁输出的 `dirty_entries=3` 属既有基线，不作为本 change 的失败判据。

## Goals / Non-Goals

**Goals:**

- 让「全体皆死」与「合法活测量恰为 `0.0`」在输出层**位层面可区分**，且不引入新的哨兵常量。
- 为此前**完全无规范**的状态（全死聚合 `SP`）补上契约，并把 `NaN` 从 `SP ∈ [-1,1]` 的值域中显式 carve out，使 range 断言与哨兵契约不再互相拆台。
- 纠正 `wayfinder` `#req-30` 中三处「在定义域内恰好为真 / 只在闭包上成立却写成可达」的条文，并补上此前为零覆盖的 `c_i` 侧守护。
- 把台账的**可复现证伪命令**固化进本制品，使下一轮重扫能自行判否而无需重新推导。

**Non-Goals:**

- 不为 CG / `D_chord` / `R_H` / MCI 的退化分支定契约（台账 `FIX-025`，落 DIR-2 桶）。
- 不碰 `tests/` 层 DIR-1…DIR-5 共 32 条，不碰 `.audit/**`（DIR-5），不修 `req-gov-9` 悬空引用（FIX-041，OPX-1）。
- 不新增任何 lint。现有 7 个 lint 对本 change 的落点（`metrics.py` 的 return 值、两份 spec 的 prose）均无覆盖需求。（基线 `3c64cdc`）
- 不接线 `SP` 到 `src/` 的任何调用路径（`CLAUDE.md` §7 formalize-only；`gating_logits` 全仓仅存 `typing.Protocol` 存根，见 §9）。

## Decisions

### D-1 · 全死聚合 `SP` 返回 `NaN`，不引入新哨兵

**选择**：`NaN`（`torch.full((), float("nan"))` 或 `torch.tensor(float("nan"))`）。

**理由**：
- **语义方向**：全死是一个**可测状态**（路由器全死），不是契约违反。抛异常会把合法状态错误化。
- **歧义关闭最干净**：`torch.equal(NaN, 0.0)` 为 `False`，位层面不可区分性消失；而 `live is _ZERO` 这种对象身份区分随 `_ZERO` 一起退役，无需维护第二种判别机制。
- **spec 已认可**：`wayfinder #req-20` 的单死场景已把 `NaN` 列为 `e.g.` 候选项之一，编码方式与既有措辞同构。
- **返回类型不变**：`SP` 是 `src/` 无调用方的存根 API，改签名的破坏半径与收益不相称。

**已否决的替代**：
- `(b) 抛异常` — 把合法状态错误化，且需先决定 5 处测试调用点的预期。（基线 `3c64cdc`）
- `(c) 返回 `(值, dead)` 元组` — 可观测性最好，但为一个存根 API 付最大破坏半径。
- `(d) 保留 `_ZERO` 但让调用方检查身份` — `_ZERO` 不在 `__all__`，全仓 `is _ZERO` **零命中**，即「可分辨」没有任何调用者，是一个无人使用的机制。

**代价**：今日为零（`src/` 无调用方，`tests/` 5 处直接调用可显式 `torch.isnan` 断言）。契约声明层面，`SP` 的值域扩到含 `NaN`，已由 `#req-40` 显式 carve out。

### D-2 · 两条早退一并处置；`_ZERO` 窄读法保留

`src/decompmoe/metrics.py` 有 **5** 个 `return _ZERO`（`:21` 定义、`:103`、`:140`、`:153`、`:165`、`:228`），归属如下（实测）：

| 行 | 归属 | 本 change | <!-- （基线 `3c64cdc`） -->
|---|---|---|
| `:140` | `SP`，`C_t.numel() == 0`（**合法** `T = 0`，此时全部 `n_i = 0`，同属全死） | **改 `NaN`** |
| `:153` | `SP`，`not per_expert_means`（合法输入下**不可达**：`sys.settrace` 逐行追踪、穷举 `N_e ≤ 5` × `T ≤ 8×200` 组，命中 0 次；仅越界 assignment / `N_e = 0` / 形状不匹配可触发） | **改 `NaN`** |
| `:103` `:165` `:228` | CG / `D_chord` / `R_H` / MCI 的退化分支，即台账 `FIX-025` | **不动** |
| `:21` | `_ZERO` 常量定义本身 | **不动** |

**选择**：只改 `:140` 与 `:153`，`_ZERO` 常量及其余 3 处 return 原样保留。（基线 `3c64cdc`）

**理由**：(i) 其余 3 处属 `FIX-025`，落 **DIR-2** 桶，已被用户 Q1 的范围裁定（专注 OPX-2）排除；(ii) `CLAUDE.md` §3 要求每一处改动可直接追溯到用户请求——为 3 个未被要求的度量定契约属越界。（基线 `3c64cdc`）

**已否决的替代**：删掉 `_ZERO`、让 5 处一起语义化。广读法需同时为另外 3 个度量的退化分支定契约，等于把一个 OPX-2 change 扩成 OPX-2 + DIR-2。（基线 `3c64cdc`）

**台账归因更正**：台账把 `:152-153` 当作「全死」入口。实测该行在合法输入下不可达；**合法的全死路径是 `:139-140` 的 `T = 0`**。两处返回同一 `_ZERO` 对象，故「不可区分」的结论不变，但行号归因不精确。本 change 同时处置两处，故该更正不影响修复内容——但它意味着台账的 `location` 字段需按此理解。

### D-3 · `#req-30` 三处子缺陷的修法

`wayfinder/spec.md:778` 单行内三处，逐条修法见 `specs/wayfinder/spec.md` 的 MODIFIED 块。此处只记录取舍：

- **(a) 见证条件** → 陈述 `‖∂logit/∂C‖₂ = β·‖c‖₂` **与夹角无关**，`c ⟂ C` 只是一个见证。**依据**：实测 autograd 在 `0°–180°` 每个角度都成立该恒等式，所以「在最坏配置 `c ⟂ C` 处取到」把一个充分条件写成了必要条件。
- **(b) 派生式** → 改为 `∂logit/∂C = β · c`，并显式标注旧式 `β · c / ‖C‖` **仅在 `‖C‖ = 1` 上成立**。**依据**：`logit = β(C^T c − 1)` 对 `C` 线性，导数不含 `‖C‖`；实测 `‖C‖ = 2` 处 autograd 给 `32.0` 而旧式给 `16.0`。这是**潜伏型**缺陷——定义域内恒等，故测试永不失败，只能靠「故意离开定义域」暴露。
- **(c) 量词** → `MUST be attained` 改为上确界措辞。**依据**：`β = 0.1 + 31.9·σ(γ)` 对一切有限 `γ` 严格小于 32（float64 需 `γ ≳ 36.7368` 才饱和到 1.0）。
- **连带** `:783-784` 的 Scenario 以符号值 `β = β_max` 断言 `‖∂logit/∂C‖₂ == 32.0`，继承 (c) 的同一处错误；若只改 Requirement 不改 Scenario，两者互相拆台。故该 Scenario 一并改为极限措辞。
- **γ 侧逐字保留** `|∂logit/∂γ| ≤ 15.95` 与 `:787-788` Scenario。**依据**：ARC-009 复算正确（`γ = 0 → β = 16.05`，`31.9·0.25·(−2) = −15.95`）。把已正确内容卷进本 change 会放大回归面且无收益。

**已否决的替代**：只改 Requirement 保留 `c ⟂ C` 作见证并加「角度无关」附注。取舍点是 `MUST be attained` 是否可以只靠附注软化——不可以。`MUST` 是规范级量词，附注不改变其断言内容；`β_max` 在有限 `γ` 下不可达是事实，必须落在条文本身。

### D-4 · FIX-034 / FIX-042 判定不成立，零 spec delta，证伪证据附此

台账存目纪律要求**不回改条目正文**，故这两条已被证伪的陈述会长期留在正文。只写「不成立」不足以防复燃——必须附**下一轮可一键复现**的反向锚定命令。

**FIX-034 反证链**（台账原述「`A_i` 是带种子的 Monte-Carlo 估计……未在任何一份 spec 中说明」）：

```
git show HEAD:openspec/specs/wayfinder/spec.md       | grep -c seeded                # → 0
git show HEAD:openspec/specs/wayfinder/spec.md       | grep -c 20260929              # → 0
git show HEAD:openspec/specs/wayfinder/spec.md       | grep -c VORONOI_AREA_SAMPLES  # → 0
git show HEAD:openspec/specs/decompmoe-skeleton/spec.md | grep -c 20260929           # → 命中
```

`decompmoe-skeleton/spec.md:115`（req-6）逐字含：「`A_i` MUST be estimated by seeded Monte-Carlo over `VORONOI_AREA_SAMPLES` uniform probes on `S^{d_c − 1}`, each assigned to its `argmax` site, with the sample count and the seed fixed as module constants (`1_000_000` and `20260929`) so the returned value is deterministic」。且 `wayfinder:263` 同一句块已称 `A_i` 为「the Monte-Carlo estimator of the cell areas」。

残留缺口只有「wayfinder 未复述 seed / 样本数 / 确定性」一项，而 `skeleton:115` 明文声明 wayfinder req-11「is NOT a verbatim mirror of this paragraph」——散文不对称是**被设计允许的**，把对称性偏好当 MINOR 缺陷修，等于凭空制造一笔不存在的债务。

**FIX-042 反证链**（台账自述「本项本身不构成缺陷」）：

```
grep -n 'SOURCE_EXEMPTIONS' scripts/lint_no_source_field_drift.py     # → :475 定义, :498 收尾
sed -n '475,498p' scripts/lint_no_source_field_drift.py | grep -c '"'   # → 20 条
```

`SOURCE_EXEMPTIONS` 实测恰 20 条（19 × `decompmoe-skeleton` + 1 × `wayfinder`），该 lint 在门禁中 PASS，且已能对「已补字段 / Requirement 消失 / 指向无 spec 的 capability」报 stale——登记表**无法静默增生**（req-gov-11 机制完备）。20/70 是谱系完整性的**状态事实**，不是缺陷。

### D-5 · 执行前置规则：否定性主张必须经反向锚定复核

**规则**：台账条目中的否定性主张（「未在任何一份 spec 中说明 X」类）在执行前必须经**反向锚定复核**——不找「说明在哪」，而是对具体字面量在目标文件计数：`0` 即证伪「已说明」、非 `0` 即证伪「未说明」。复核结论**不入台账正文**（存目纪律），但必须挂在 change 的裁决记录里。

**依据**：本轮实测到的失效模式是系统性的——台账 `problem` 段成文**早于** `evidence` 段的发现，存目纪律禁止回改，于是「problem 说没有 / 本轮复核说有」在同一词条内长期并存，而执行纪律倾向于照单全收。`FIX-034` 台账自身的复核注记已写明「问题是否仍成立需另行判断」，把判断推给了读者；本 change 补完该判断。`FIX-034` / `FIX-042` 若照单执行，会去修两个不存在的缺陷。

与本仓既有裁决哲学一致：**台账条目是待裁决的数据，不是执行令。**

### D-6 · 打包为 1 个 OpenSpec change

`FIX-006` 与 `FIX-007` 合成一个 change，理由：两者都被 `wayfinder` 领衔（`#req-20` 与 `#req-30`），且都属「规范侧未规定 / 条文侧写错」的同一类失效。change 数量直接等于 `req-gov-10` anchor 四步协议的执行次数，而该协议**禁止重跑 archive**，每次执行都是不可低成本重来的高风险操作。`FIX-034` / `FIX-042` 的裁决（D-4）作为 `design.md` 内容随本 change 落地，不单独开 change、不产生 delta。

### D-7 · 采用 MODIFIED 承载全死语义，anchor 数维持 74

**选择**：把全死 `SP` 的 6 条新 Scenario **补进既有的 `#req-20` / `#req-22` 块**，不新建 Requirement。

**理由**：
- 全死聚合 `SP` 此前无规定，但它是既有 Requirement（八个几何量化指标 / 八指标与分类）内部的一个**未规定状态**，补 Scenario 即是最小且语义准确的承载方式；新建 Requirement 反而把它从所属定义中割裂出去。
- `#req-23` 对 `#req-22` ← `#req-20` 的**逐字镜像**义务要求两侧同步，补 Scenario 两侧同文即自然维持。
- **anchor 数不变（74）**。CLAUDE.md §6 把「每个 Requirement MUST 设独立 anchor，100% 覆盖」列为硬约束；新增 Requirement 会把计数推到 78，使归档前后的门禁输出基线发生位移。

**转写风险如何消除（而非接受）**：`#req-20` 跨度 112 行、`#req-22` 跨度 87 行，手抄必然引入漂移。故 delta 的**原有部分由脚本从主 spec 按顶层 anchor 边界机械提取**，只把新 Scenario 追加到块尾。实测校验：两个块的**非空行与主 spec 逐字节相等**（`req-20` 90 行、`req-22` 55 行，均 BYTE-IDENTICAL）。

> **规划更正记录**：本 change 初版 delta 曾用 ADDED Requirement 承载（`wayfinder` `req-39`/`req-40`、`decompmoe-skeleton` `req-24`/`req-25`），使 anchor 由 74 变为 78，**违背本 change 契约 M2 明写的「不新增任何 Requirement，故不新增 anchor」**，也与用户原话「补 Scenario 措辞镜像单死」相左。属计划错误，已在 apply 前就地更正为 MODIFIED。本条记录保留，以免下一轮重扫时重新捡起同一个错误方案。

`#req-30` 同为 MODIFIED：它只有 17 行，且它确属既有定义的**修改**（取等见证条件、导数派生式、量词三者均改写），不是新增行为。

**`#req-30` 的 MODIFIED 约束**：OpenSpec 的 MODIFIED 块会**整体替换**原块，`openspec validate` 拒绝丢弃既有 Scenario。因此两个原 Scenario 名（`gradient bound is tight at orthogonal unit vectors`、`gamma-gradient bound is tight at antipodal config`）**必须原名保留**。前者与「上确界」改写的表面冲突，通过新增一条 Scenario 消解：区分「在 `β` 闭区间**边界值** `β = β_max` 上求值 = 32.0」与「任何**有限 `γ` 可达**的 `β` 严格 `< 32.0`」。

## Risks / Trade-offs

- **[R1] 归档吞掉 anchor** → 归档前 `run_gates.py anchor-ledger --write`，归档后 `anchor-ledger --verify`；若比对失败，**只做手术式补回，禁止重跑 archive**（req-gov-10）。本 change **不新增也不删除任何 Requirement**，故 anchor 集合应为 74 → 74 的恒等映射；归档后须逐一确认 74 个 anchor 的 `(capability, anchor_id)` 集合与归档前完全相同，无丢失、无新增、无 id 冲突。
- **[R2] `NaN` 污染下游聚合** → 今日代价为零（`src/` 无 `SP` 调用方）。但值域已变，故 `#req-40` 显式规定 `NaN` MUST NOT 被 clamp / 代入 / 比较 / 参与聚合，不留解释空间。
- **[R3] `#req-30` 重写误伤已正确的 γ 侧** → delta 只触碰 `C` 侧两句；γ 侧 `|∂logit/∂γ| ≤ 15.95` 与 `:787-788` Scenario 在 MODIFIED 块中逐字保留，并由测试守护。
- **[R4] D-2 窄读法若与本意相左，diff 大小差一个量级** → 广读法（删 `_ZERO`）需为另 3 个度量的退化分支定契约，即 `FIX-025`（DIR-2），已被范围裁定排除。该取舍已在 `proposal.md` Impact 与本文件 D-2 双处明示。（基线 `3c64cdc`）
- **[R5] 假债复燃** → 台账正文按纪律不回改，下一轮重扫仍会撞上原句。D-4 的证伪命令 + D-5 的前置规则使下一轮能自行判否。
- **[R6] 工作树 3 处既有改动与本 change 的 spec 改动产生语义交叉** → 尤其 `WF-1.md` 删除 `req-gov-2` 管辖的 supersede 标注，而 `req-gov-2` 是 Source 反链的执行者。按裁定完全不动；`#req-20` / `#req-22` / `#req-30` 三块的 `**Source:**` 行在 delta 中**原样保留**（机械提取的产物），不依赖 `req-gov-2` 的标注完整性即可通过 lint。
- **[R7] `(c)` 的上确界改写可能被下游实现视为放宽** → 不放松任何数值界：`32` 仍是上确界，只是从「可达最大值」改为「有限 `γ` 下不可达、随 `γ → ∞` 逼近」。测试须同时钉住「每个有限 `γ` 下严格 `< 32.0`」与「`|∂logit/∂γ| ≤ 15.95` 仍可达」。
