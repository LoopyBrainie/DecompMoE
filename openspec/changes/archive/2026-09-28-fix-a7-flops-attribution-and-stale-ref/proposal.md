# Proposal

## Why

审计 finding A7 报告 `wayfinder/spec.md` 的 FLOPs 推导「`144 = 9·d_c` 在 spec 中无任何推导，且两项都不随 config 缩放」。**该 finding 的三条断言经四源实测后两条为假**，但其落点附近确有两个真实缺陷，性质与 finding 描述完全不同：

1. **标签归属错**（非「缺推导」）。`144 MACs` 在 `wayfinder:375` 与 `:422` 被称作 "per-head L2-normalize" 单独一项。按 canonical 闭式 `openspec/specs/decompmoe-skeleton/spec.md:138`（Scenario「Per-token MAC closed form」）的逐项枚举：per-head L2-normalization 是 `H_kv · d_c`（= 128），final L2-normalization 是 `d_c`（= 16）。`144 = H_kv · d_c + d_c` 是**两个 L2 步骤合计**，四步 pipeline 的第 4 步被漏标。spec 中**不存在 "9"**，推导完整存在。

2. **spec 行号反链漂移**（finding 未提及）。`wayfinder:422` 的 cross-req note 写 `"Req 17 L311"`。当前 `req-17` anchor 在 **L371**、extract_C 账目在 **L375**；L311 是 Req 13 的 "Standard step ordering" 场景（`req-13` anchor 在 L303）—— 指向了完全不相干的 Requirement。`git show be9ef09:openspec/specs/wayfinder/spec.md` 实测该行号**创建时是正确的**（anchor L307 / 文本 L311），属 `34b37be` / `6f22278` / `7929770` 等后续 commit 造成的漂移，与 `b23f0e5` L2/L4 在别处清理过的 stale-line-ref 同族。

**全部算术正确，一个数值都不改。** 独立复算：`4·16·8·128 = 65_536`；`2·16·16 = 512`；`FLOPs_Routing = 66_048`；`×L=4 = 264_192`；`FLOPs_MoE,core = 33_554_432`；ratio = `0.0019683837890625`（≈ 0.20%，在 0.3% allowance 内）；net `(128+144)·2 − 512 = 32`。`tests/test_config.py` 已守护全部六项。缺陷是**零测试红的纯叙述错** —— 恰恰是测试与 lint 都抓不到、只能靠人工交叉校对发现的一类。

## What Changes

| # | 位置 | 变更 |
|---|---|---|
| 1 | `openspec/specs/wayfinder/spec.md:375`（Req 17 body） | `bias `+128` MACs and per-head L2-normalize `+144` MACs` → 逐项标注闭式：bias `H_kv·d_c = 128` MACs、per-head L2-normalize `H_kv·d_c = 128` MACs、final L2-normalize `d_c = 16` MACs（两个 L2 步骤合计 `+144` MACs） |
| 2 | `openspec/specs/wayfinder/spec.md:422`（Req 19 cross-req note） | `Req 17 L311` → ``Req 17 (anchored `<a id="req-17"></a>`)`` —— **行号整体移除**，改用 anchor 引用（最终决定；初版为「订正为当前行号 `L375`」，见 design.md Decision 2 的覆写记录） |
| 3 | 同上 | `+144 MACs per-head L2-normalize` → 标注为 per-head L2 + final L2 合计（对齐变更 1） |
| 4 | 同上 | `intentionally does **not** repackage the bias add or per-head L2-normalize` → 补 `or the final L2-normalize` |
| 5 | `:377`、`:424` | 两处 `**Source:**` 追加本 change design.md 反链（backtick-wrapped，第一个 top-level item 保持不变） |
| 6 | `tests/test_config.py:109`、`:127`、`:142` | 参数化：`H_kv` 由硬编码 `8` 改为 `cfg.H_kv`（三处）。**`macs_bias_l2 = 128 + 144` 保持字面量不变**，仅补注释记录 `144` 的归属出处（per-head L2 `H_kv·d_c = 128` + final L2 `d_c = 16`，per `decompmoe-skeleton:138`）。**不引入推导式断言** —— 理由见 design.md Decision 4 |

**无 BREAKING 变更。** 全部是 Requirement body 的归属标注修正 + 反链订正 + 测试取值来源参数化；**无任何数值声明改变**。

### Audit fact-check

| ID | 清单断言 | 实测（`git show HEAD:<path>` @ `53ca016` + 独立算术） | 判定 |
|---|---|---|---|
| **A7-1** | `H_kv·d_c = 128` 可导出 | `decompmoe-skeleton:138` 明确枚举 `(i) per-head K/V/bias projection: H_kv · (2·d_k·d_c + d_c)`，`+d_c` 即 bias → `H_kv·d_c = 8·16 = 128` | ✅ 成立 |
| **A7-2** | `144 = 9·d_c` 且「spec 中无任何推导」 | `decompmoe-skeleton:138` 同时枚举 `(ii) per-head L2: H_kv·d_c = 128` 与 `(iii) final L2: d_c = 16`，故 `144 = H_kv·d_c + d_c`。**spec 中不存在 "9"** | ❌ 断言为假 → 真实缺陷是**标签归属错**，非缺推导 |
| **A7-3** | 两项都不随 config 缩放 | 二者均为 `H_kv` / `d_c` 参数化闭式的 MVP 实例，与同句 `4·d_c·H_kv·d_k` 同一模式 | ❌ 断言为假 |
| **A7-4**（新增） | — | `wayfinder:422` 写 `"Req 17 L311"`，实为 Req 13 的 Standard step ordering；`be9ef09` 时正确，后续 commit 漂移 | ✅ 成立（清单未列） |

**清单位置 off-by-one**：finding 标 `wayfinder/spec.md:L421`，L421 是空行。实际内容在 **`:422`**（cross-req note）与 **`:375`**（Req 17 主体）。

**已排除的伪缺陷（不得写入制品）**：以 `<a id="req-` 粗 grep 会得出「wayfinder 37 anchors / `req-20` 重复」。实为 `wayfinder:834` 一处 **inline prose 引用**（backtick-wrapped 文本）被误计。按「整行即 anchor」重测：wayfinder 36 requirements / 36 anchors、skeleton 23/23、governance 4/4 = **100% 覆盖，无重复 id**，与 `b23f0e5` 报告的 36/23/4 一致。**本 change 不触碰 anchor。**

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `wayfinder`：
  - Requirement 17 "Stateless Per-Frame C Recomputation" — extract_C 成本账目中 `144 MACs` 的归属标注对齐 canonical 闭式（补 final L2-normalize 项）。
  - Requirement 19 "Six Baseline Set On 4070 MVP" — cross-req consistency note 的同款归属标注 + `Req 17 L311` stale 行号反链改为 anchor 引用（``Req 17 (anchored `<a id="req-17"></a>`)``，行号整体移除）。

（`decompmoe-skeleton` **不在**列表内 —— 其 `L126`（四步 pipeline 定义）与 `L138`（MAC 闭式）本身完全正确，仅作对齐参照。`governance` 不涉及。）

## Impact

### Affected files

| 文件 | 组 | 操作 |
|---|---|---|
| `openspec/specs/wayfinder/spec.md` L375 | A7-1 | 144 MAC 归属标注 |
| `openspec/specs/wayfinder/spec.md` L422 | A7-2/3/4 | 144 MAC 归属 + `Req 17 L311` stale 行号反链改为 anchor 引用（行号移除）+ 补 final L2 |
| `openspec/specs/wayfinder/spec.md` L377 / L424 | A7-5 | 两处 `**Source:**` 追加本 change 反链 |
| `tests/test_config.py` L109 | A7-6 | `H_kv` 改取 `cfg.H_kv`（`MVPConfig` 已暴露该字段） |
| `tests/test_config.py` L109 / L127 / L142 | A7-6 | 三处硬编码 `8` → `cfg.H_kv`；L143 `macs_bias_l2 = 128 + 144` 补归属出处注释（**字面量保留**） |
| `openspec/changes/2026-09-28-fix-a7-flops-attribution-and-stale-ref/` | — | create 4 类制品 + `.openspec.yaml` |

**无 `src/` 实现变更。** 全部改动为 spec 归属标注 + 反链订正 + 测试取值来源参数化（不新增/删除任何断言）。

### Out of scope

- ❌ 任何 `src/` 实现变更（含当前工作树标脏的 `src/decompmoe/safeguards.py` —— 经 `git diff --ignore-all-space` 实测为纯 CRLF→LF 噪声、无语义改动）
- ❌ **改动任何数值**（`65_536` / `33_040` / `66_080` / `66_048` / `264_192` / `32` / `0.001968` / `0.05%` / `0.3%` 全部冻结，见 design.md Decision 3）
- ❌ `decompmoe-skeleton/spec.md` 零改动（`L126` / `L138` 本身正确，仅作对齐参照）
- ❌ spec anchor 体系（实测 36/36、23/23、4/4 = 100%，无重复 id）
- ❌ 触碰 in-flight change `2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding`、`2026-09-28-fix-a2-a3-a4-residual-precision-claims`、`fix-review-findings-voronoi-precision-and-lineage`、`2026-09-26-followup-spec-wording-bugs-after-precision-disclosure`
- ❌ 其余 A2 / A3 / A4 / A5 四条 finding
- ❌ 回补既有 in-flight change 缺失的 `specs/` delta（既有不一致，另开 cycle）
- ✅ **改为 anchor 引用**（初版列为 out-of-scope，2026-09-29 用户在收尾阶段覆写）：`Req 17 L382` → ``Req 17 (anchored `<a id="req-17"></a>`)``，**行号整体移除**。推翻理由见 design.md Decision 2 —— 硬编码行号 16 小时内两次失效（`L375 → L381 → L382`），「订正为当前行号」被实测证明只推迟复发；且 `wayfinder:847` 已有 `anchored \`<a id="req-20"></a>\`` 先例，改用 anchor 属沿用既有风格而非引入新风格
- ❌ 新增 lint 规则（扫 `openspec/specs/**` 检测归属标注与闭式不符）—— 属治理条款级扩展，超出措辞修正 scope
- ❌ **wayfinder 既有游离反引号 typo**（构造本 delta 时顺带发现，非本 change 引入）：`;` + 反引号 造成的失效 code span，按 **CommonMark 语义**（反斜杠转义生效）共 **6 行** —— `openspec/specs/wayfinder/spec.md` L205 / L351 / L363 / L369 / L381 / L534（`decompmoe-skeleton` 与 `governance` 各 0 处）。典型如 L381 `` no per-token C state survives into the next step;` the next step recomputes from fresh ``。**同一文件另有两行在 lint 语义下也算破缺**（L823 / L826）—— 它们本身是「谈论反斜杠转义反引号」的散文，而 `scripts/lint_no_source_field_drift.py` 的 tokenizer 按其自身 docstring 不支持 `\``，故 `in_code_span` 状态会错乱；按 lint 语义计为 8 行。本 delta 的 Req 17 block **逐字沿用**了 L381 这行（往返验证已确认），按 `CLAUDE.md` §3 surgical 不代为修复，另开 cycle
- ❌ GPU-only 声明（`W_proj ≈ 64 KB` / `0 bytes HBM` 等，本环境无 CUDA）
- ❌ `dev → main` / `dev → release` 合并

### Source back-link

- **`wayfinder/tickets/A7-2.md`** —— Req 17 "Stateless Per-Frame C Recomputation" 的既有 `**Source:**` 反链（本 change 追加于其后）
- **`wayfinder/tickets/A8-1.md`** —— Req 19 "Six Baseline Set On 4070 MVP" 的既有 `**Source:**` 反链（本 change 追加于其后）
- `openspec/specs/decompmoe-skeleton/spec.md:138`（canonical MAC 闭式，本 change 的对齐基准）、`:126`（四步 pipeline，final L2-normalize 为第 4 步）
- **`CLAUDE.md`** §6 第 8 条（对账方式依数值类型二分：整数闭式 bare `==`）、§2 truth hierarchy（`wayfinder` spec 为第 1 级真相源）、§3（Source 反链 + lint gate + archive 前置条件）、§4（分支规范）
- commit `be9ef09`（cross-req note 的创建 commit —— 用于证明 `Req 17 L311` 创建时正确、属后续漂移）
- commit `b23f0e5`（stale-line-ref 清理先例 L2/L4；亦为本缺陷邻域的最近一次 fix cycle）
- change `fix-review-findings-voronoi-precision-and-lineage` `tasks.md` G2（`FLOPs_Routing` 守护的引入点）
- 本 change `design.md` Decision 1–4

### Risks / Trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| **误改数值** —— 诱惑是把 `144` "修正"成 `128` | High | design.md Decision 3 显式记录「数值全部正确、只改归属标注」；tasks.md 列出 must-not-change 值清单；apply 后以 `git diff` 逐值对账 |
| **并行 session 改动 working tree / 推进 HEAD** | High | 实测 `b23f0e5` → `53ca016`（13:00:43）已发生一次。apply 前后各跑 turn-start 三连；**只 `git add` 上表列出的 3 个精确路径** |
| **行号漂移** | ~~Medium~~ **已消解** | 初版缓解手段是「apply 阶段每处编辑前 `git show HEAD:<path>` 重新定位」—— 实测该手段**两次失效**（16 小时内 +6、+1）。最终改用 anchor 引用（design.md Decision 2），从源头移除对行号的依赖；本行保留以记录该缓解手段为何被判定不足 |
| **改了 2 处 `**Source:**` 字段** —— 反链 lint 可能报错 | Medium | `lint_no_source_field_drift.py` **必须实跑**，不得假定不受影响。追加内容以 `, change \`<name>\` design.md (Decision N — ...)` 形式接在既有 backtick-wrapped ticket 反链之后，保证「第一个 top-level item 是 backtick-wrapped ticket」不变 |
| **delta 手抄失真** —— `## MODIFIED Requirements` 需逐字复制主 spec 的 Requirement block | High | 必须脚本化构造（从主 spec 抽取 block → 定点替换并断言命中次数 → `difflib` 结构化 diff 确认只剩预期 op），禁止凭记忆复述 |
| **`tests/test_config.py` 的 MAC 字面量不得参数化** —— 把 `128 + 144` 改成 `cfg.H_kv·cfg.d_c + cfg.d_c` 会把可失败的 literal pin 换成按构造产不出 144 的恒真式 | High | design.md Decision 4 记录该权衡与替代方案；tasks.md 3.3 明令禁止 |
| 参数化 `H_kv` 后测试强度是否下降 | Low | 不降：`65_536` / `512` / `66_048` / `264_192` / `66_080` / `32` 六个 spec 字面量全部保留为 bare `==` 断言；`cfg.H_kv` 化后 `projection` 随 config 变化，若 spec 改 `H_kv` 则 `assert projection == 65_536` 反而更早变红 |
