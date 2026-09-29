# Design

## Context

See `proposal.md` — Why 与 `## Audit fact-check` 表（缺陷定位、四源实测、severity 论证）。

本 design 只补充实现前必须定下的技术选择。核心事实前置：`openspec/specs/decompmoe-skeleton/spec.md:138`（Scenario「Per-token MAC closed form」）是 extract_C MAC 成本的 **canonical 闭式**：

```
H_kv · (2 · d_k · d_c + d_c)  +  H_kv · d_c  +  d_c
         (i) projection        (ii) per-head   (iii) final
             incl. bias           L2-norm      L2-norm
```

MVP 实例化（`H_kv=8, d_k=128, d_c=16`）：`8·4112 + 8·16 + 16 = 32_896 + 128 + 16 = 33_040` MACs。

`wayfinder` 侧 Req 17 / Req 19 的账目与之同源，但把 (ii)(iii) 合并后的 `144` 标成了 (ii) 单独一项。约束：`decompmoe-skeleton` 本 change **零改动**（其 L126 / L138 本身正确，仅作对齐基准）。

## Goals / Non-Goals

**Goals:**

- 让 wayfinder 的 `144 MACs` 归属与 canonical 闭式逐项对应，读者可据 spec 自行复现 `128 + 16`。
- 订正指向错误 Requirement 的 stale 行号反链。
- 让测试保持对 spec 的**钉值探测能力**：`H_kv` 取自 `MVPConfig` 而非硬编码，且 `128 + 144` 继续以字面量形式与 spec 对账，使「144 的归属」若被 spec 改写能在测试侧暴露。
- 保证 delta 逐字保真（`## MODIFIED Requirements` 需复制整段 Requirement 文本）。

**Non-Goals:**

- 不改任何数值（见 Decision 3）。
- 不重构 `extract_C` pipeline 或任何 `src/` 实现。
- 不修 wayfinder 既有游离反引号 typo（9 行，见 proposal Out of scope）。
- 不设计「扫 spec 检测归属标注与闭式不符」的 lint（治理条款级扩展，另开 cycle）。

## Decisions

### Decision 1 — `144` 改标注为「两个 L2 步骤合计」，不改数值

**选择**：`144 MACs` 一律标注为 per-head L2-normalize `H_kv·d_c = 128` + final L2-normalize `d_c = 16` 的合计。

**依据**：`decompmoe-skeleton:138` 明确枚举三项，per-head L2 是 `H_kv·d_c`（= 128），final L2 是 `d_c`（= 16）。`144 = 128 + 16` 是 (ii)+(iii) 之和。四步 pipeline 的第 4 步（`decompmoe-skeleton:126`「final spherical projection」）在 wayfinder 账目中从未被提及。

**考虑过的替代方案**：

| 替代 | 为何不选 |
|---|---|
| 把 `144` 直接改成 `128`（视为数值错） | **`128 + 144 = 272` 是正确的非投影总量**（= bias 128 + per-head L2 128 + final L2 16）。改数会破坏 `(128+144)·2 − 2·N_e·d_c = 32` 的 net 差、66_080 总账、以及 `tests/test_config.py` 的三处断言。**这是本 change 最容易犯的错** |
| 删掉 `144` 只留 `+272` 总量 | 丢失分解信息，读者无法据 spec 复现 272 的构成；且与 `decompmoe-skeleton:138` 的三项枚举脱节 |
| 同时把 `128` 标注为「bias + per-head L2」 | `128` 确实同时等于 bias 子项与 per-head L2 子项（两者都是 `H_kv·d_c`），但把它们并成一项会让「bias」与「L2」两类操作混淆。保持三项独立更清晰 |

### Decision 2 — stale 反链改为 anchor 引用（初版曾选择「订正为当前行号」）

> **2026-09-29 用户覆写。** 本 Decision 初版选择「订正为当前行号」以对齐 `b23f0e5` 先例；用户在收尾 questionnaire 中明确推翻，改为 anchor 引用。下文**同时保留初版理由与推翻理由**，以免后人误以为初版从未被否决、或误以为推翻缺乏依据。

**初版选择**：`Req 17 L311` → `Req 17 L375`。依据是 `be9ef09` 创建该 note 时行号正确（anchor L307 / 文本 L311），属后续 commit 漂移；而 `b23f0e5` 对同族缺陷（L2 `stale L394-466 → L434-505`、L4 `stale L413 → L453`）全部使用「订正为当前行号」，未引入 anchor 引用。

**最终选择**：`Req 17 L382` → ``Req 17 (anchored `<a id="req-17"></a>`)``，**行号整体移除**（不是「行号 + anchor」并存）。

**推翻依据（实测，非推测）**：硬编码行号在 **16 小时内两次失效，两次都发生在同一行、同一缺陷类** ——

| 时点 | 账目行实际位置 | 事件 |
|---|---|---|
| 设计时 | `L375` | — |
| apply 阶段首次 | `L381` | 基座推进，**+6 行** |
| apply 阶段复验 | `L382` | peer's `9144f1b` 在账目行上方再插入 1 行，**+1 行** |

「订正为当前行号」因此被实测证明**只把复发推迟到下一次无关 commit，而不是修复复发**。初版把「与 `b23f0e5` 风格一致」置于「消除复发」之上，在已有两次反例的情况下这个权衡是错的。

**为何 anchor 是正确形式（而非新风格）**：spec 已有稳定 anchor 体系（实测 `36/36` 覆盖、无重复 id），且 wayfinder 内**已有 inline anchor 引用先例** —— `openspec/specs/wayfinder/spec.md:847` 的 `anchored \`<a id="req-20"></a>\``。故改用 anchor 是**沿用既有风格**，而非引入第二种风格 —— 这直接推翻了初版替代方案表里「会形成两种风格并存」的顾虑。anchor 与 Requirement 身份绑定，不随行号漂移。

**考虑过的替代方案**：

| 替代 | 为何不选 |
|---|---|
| 保留行号 + 追加 anchor（`Req 17 L382 (anchored ...)`） | 保留的恰恰是会漂移的那部分，读者仍会先看到那个会过期的数字。半修等于未修 |
| 删掉行号只写「Req 17」 | 丧失可导航性。anchor 引用**同时**给出可导航性与稳定性，是严格更优项 |
| 保留 `L311` 加注「(created at be9ef09)」 | 把漂移固化成正文的一部分，读者仍会被误导 |
| 订正为当前行号（**初版选择，已被推翻**） | 16 小时内两次失效，见上表 |

### Decision 3 — 冻结全部数值

**选择**：`65_536` / `33_040` / `66_080` / `66_048` / `264_192` / `32` / `0.001968` / `0.20%` / `0.05%` / `0.3%` / `~0.83%` / `128` / `144` / `272` 全部不动。

**依据**（独立复算 @ `53ca016`）：`4·16·8·128 = 65_536`；`2·16·16 = 512`；`66_536` 不出现（`65_536 + 512 = 66_048`）；`×4 = 264_192`；`8·1024² + 2·6·1024·2048 = 33_554_432`；ratio = `0.0019683837890625`；`(128+144)·2 − 512 = 32`。全部与 spec 声称一致，且 `tests/test_config.py` 的 G2 守护已覆盖前六项。

**为何这条要显式成文**：审计清单把 A7 报为「数值缺乏推导」，极易诱导实施者去「修数字」。而真实结论是数字全对、标签错。把冻结清单写进 design 与 tasks，是本 change 最主要的误改防线。

### Decision 4 — 只把 `H_kv` 参数化，MAC 字面量保持不推导

**选择**：`tests/test_config.py` 中三处硬编码的 `8`（`test_flops_routing_closed_form_66048` / `test_flops_routing_ratio_within_allowance` / `test_flops_routing_cross_req_net_delta_32`）改取 `cfg.H_kv`；`macs_bias_l2 = 128 + 144` **保持字面量不变**，仅补注释记录 `144` 的归属出处。

**依据（为何不把字面量改成推导式）**：

字面量 `128 + 144` 是**对 spec 的钉值**——若 spec 日后修正该分解（例如把 `144` 改为分别列 `128` 与 `16`、或改变 bias 归属），`assert extract_c_flops == 66_080` 会**变红**，把漂移暴露出来。改成 `macs_l2 = cfg.H_kv·cfg.d_c + cfg.d_c` 后，该式**按构造产出 144**，再拿它去 `assert ... == 144` 是自证：spec 怎么改分解它都绿。`CLAUDE.md` §6 第 8 条要求的是「断言直接对账 spec 声称的值」，而「先算出这个值再断言它等于自己」并未与任何东西对账。

换言之，本 change 的 D4 修正方向是**反的** —— 最初设想把字面量拆成 `macs_bias` / `macs_l2` 推导式并「新增字面量交叉对账」，实际效果是把一个可失败的 pin 换成不可失败的恒真式，**测试对 spec 漂移的探测能力下降**。已回退。

**`H_kv` 化为何安全且有益**：它不是 spec 字面量，而是 config 字段。`MVPConfig` 已声明 `H_kv: int = 8`（`src/decompmoe/config.py`），测试却硬编码 `8`，二者一旦不同步测试不会发现。改取 `cfg.H_kv` 后，`projection` 随 config 变化，而 `assert projection == 65_536` 仍是 spec 钉值 —— config 与 spec 两侧都被守住，强度不减反增。

**范围澄清（避免后续 reviewer 重复过度延伸）**：`governance/spec.md:40-43` 的 clause (3)（禁止 helper-tautology）位于 Scenario「Closed-form per-head extraction MACs use bare `==`」，其 WHEN 明确限定 **`33_040` MACs claim 且点名 `tests/test_extraction.py::test_complexity_budget`**。它**不管辖**本 change 触碰的 `test_config.py` FLOPs net-delta 断言。因此上述回退的依据是**设计质量**（钉值 vs 恒真），**不是** clause (3) 的合规要求 —— 引用 clause (3) 来论证本处改动会失实。

**考虑过的替代方案**：

| 替代 | 为何不选 |
|---|---|
| 把 `128 + 144` 拆为 `cfg.H_kv·cfg.d_c` 与 `cfg.H_kv·cfg.d_c + cfg.d_c` 两项并各自断言 | 即被否决的方案。探测 spec 漂移的能力由「可失败」退化为「恒真」 |
| 保持原样（连 `H_kv` 也不动） | 遗留 config 与测试脱钩：`MVPConfig.H_kv` 改成 7 时 `test_flops_routing_closed_form_66048` 仍绿。零成本的 `cfg.H_kv` 化没有理由不做 |
| 用 `torch.profiler` / AST 真实测量 `extract_C` 的 MAC 数以彻底关闭 B1/B2 | 这才是**真正**满足 clause (3) 的做法，但属 `test_extraction.py::test_complexity_budget` 的既有治理债（B1/B2），**超出本 change scope**。另开 cycle |
| 把 `144` 归属改成由 `decompmoe-skeleton` 导出的共享 fixture | 跨 capability 的 fixture 依赖，且本仓无此先例。为一处注释引入新依赖模式不成比例 |

### Decision 5 — `## MODIFIED Requirements` delta 必须程序化构造

**选择**：delta 由脚本构造 —— 从主 spec 抽取 Requirement block 原文 → 定点字符串替换并**断言每次命中次数 == 1** → **往返验证**（反向替换后必须与主 spec block 逐字节相等）→ **结构检查**（本 change authored 的行必须反引号配平、change 名必须 backtick-wrapped 且只出现一次）。禁止凭记忆复述。

**依据（本轮实证）**：Req 17 block 14 行、Req 19 block 29 行。手工复述这类长 Requirement 必然引入静默失真。本轮脚本化构造当场抓到两个问题：

1. **我自己写出的反引号未闭合** —— `Source` 反链写成 `` change `…-stale-ref design.md ``（缺收尾反引号），code span 未闭合。该错误**完美通过往返验证**（反向替换后确实等于原文），只有结构检查能抓到。已修正为 `` change `…-stale-ref` design.md ``。
2. **既有游离反引号** —— Req 17 的 "No C caching" 行（主 spec L381）含 `;\`` 失效 span，属既有问题，脚本判为「逐字沿用、非本 change 引入」并记入 proposal Out of scope，而非当作 delta 缺陷。

**为何往返验证要按 header 整体反向**：同一 header 承载多条 edit，逐条反向后再与原文比较**永远不可能相等**（其它 edit 尚未撤销）。必须按 header 一次性反向全部 edit。

**考虑过的替代方案**：

| 替代 | 为何不选 |
|---|---|
| 用 opcode 类型判定 diff 合法性 | 误报：较长的替换在字符级必然产生 `insert` opcode。本轮首次运行即因此误报 FAIL，而实际 5 处替换全部正确 |
| 只做往返验证，不要结构检查 | 抓不到反引号未闭合（见上）。两者互补，缺一不可 |
| 逐条 edit 独立往返 | 恒失败，见上 |
| 复用 propose 阶段产物 | 并行 session 会改主 spec，使 delta 的 verbatim 基座漂移（本轮实测 HEAD 在 plan 批准后 4 分钟内从 `b23f0e5` 推进到 `53ca016`）。构造脚本必须在 apply 阶段重跑并重新断言 |

## Risks / Trade-offs

- **[误改数值，把 `144` 改成 `128`]** → 最高风险。Decision 3 冻结清单 + tasks.md 的 must-not-change 对账；apply 后以 `git diff` 逐值核对。
- **[改了 2 处 `**Source:**` 字段，反链 lint 可能报错]** → `lint_no_source_field_drift.py` **必须实跑**。追加内容以 `, change \`<name>\` design.md (Decision N — ...)` 形式接在既有 backtick-wrapped ticket 反链**之后**，保证「第一个 top-level item 是 backtick-wrapped ticket」这一 lint 规则不变。
- **[行号漂移]** → 全部行号实测于 `53ca016`；apply 阶段每处编辑前 `git show HEAD:<path>` 重新定位。本轮已发生一次 HEAD 推进。
- **[并行 session 改动 working tree]** → turn-start 审计；只 `git add` 3 个精确路径，禁止 `git add .` / `-A`。
- **[anchor coverage 误判]** → 计数必须用「整行即 anchor」（`^<a id="req-[^"]+"></a>$`）。用 `<a id="req-` 粗 grep 会把 `wayfinder:834` 的 inline prose 引用误计为 anchor，产生假重复。实测基线 36/36、23/23、4/4，本 change 不触碰 anchor。
