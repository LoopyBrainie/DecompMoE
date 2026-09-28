# Design

## Context

见 `proposal.md` — Why。此处只记录塑造实现方案的当前状态与约束。

- `openspec/specs/` 下三个 peer capability：`wayfinder`（36 Requirements）、`decompmoe-skeleton`（23）、`governance`（4）。反链 lint（`scripts/lint_no_source_field_drift.py`）按 capability 区分 Source 规则：`wayfinder/` 的 Requirement 必须以 `` `wayfinder/tickets/<ID>.md` `` 为主反链（且为第一个 top-level item），`governance/` 的必须以 `` `CLAUDE.md` `` 为主反链。
- `CLAUDE.md` §6 第 8 条要求 spec 中每个含具体数值的算式都有可验对账；`governance` `req-gov-1` 把这条展开为按数值类型二分的 5 条 obligation（本 change 追加第 6 条）。
- 上一轮 change `fix-review-findings-voronoi-precision-and-lineage` 的 apply（commit `b23f0e5`）同时留下了三处不同形态的残留：改 literal 未改 bound（governance）、reviewer 正确值在实施时取整取错末位并被测试锁定（wayfinder + tests）、以及修好跨 frame 配对后未补 angle-domain bias 披露（wayfinder vs skeleton 粒度不一）。
- delta 制品要求 MODIFIED Requirement **verbatim 完整重述**。手抄重述在本轮实测中产生了两类静默缺陷：时间戳 `22:02:52` 被误抄为 `22:52:52`；`σ'(-6.7836)` 的 ASCII 连字符被当成 U+2212。因此本 change 的 delta 采用**程序化构造**：从主 spec 提取 Requirement block 原文，在其上做定点替换，每个替换断言命中次数。

## Goals / Non-Goals

**Goals:**

- 让三条 finding 的数值 claim 全部达到"可验 + 正确"，且每条数值 claim 都有对应守护或不引入新的无守护数值。
- 把 A3 的 spec 与 test 两个污染点一次收口，不留"测试锁死 stale 值"的反向传染。
- 守护形态能承受未来的**精度改进**（更准的求积、更精确的字面量），而不是把当前误差固化为契约。
- 保持 delta 的逐字保真可机器验证。

**Non-Goals:**

- 不做任何 `src/` 行为变更；`_betainc_regularized` 的 Gauss–Legendre 实现本身不动。
- 不改 `canonical_voronoi_angle` 的收敛策略或容差。
- 不给 `wayfinder/spec.md` 中既有的 `4.15e-7` / `1.43e-9` residual 字面量补守护（既有缺口，另开 cycle）。
- 不回补前两个 in-flight change 缺失的 `specs/` delta。

## Decisions

### Decision 1 — A2 用 `1e-6` 单值 bound，而非逐 literal 差值

**选择**：把 Scenario 中 `each within \`3e-7\`` 改为 `each within \`1e-6\``，并在同处括注实测差值 `2.747e-7` / `2.974e-7` / `8.336e-7` 作为**非规范性说明**；同时新增 obligation 6，把"proximity bound 不得严于本 Scenario 自己的规范性容差"固化为条款。

**理由**：`3e-7` 的真实问题是"prose bound 比自己的 guard 更紧"。把 bound 拉到与同句规范性 `abs=1e-6` 同量级，条款本身就消除了这类不一致，不需要逐条核对每个 literal。

**备选与否决**：

- *逐 literal 差值作为规范性声明*（`2.747e-7` / `2.974e-7` / `8.336e-7`）—— 否决。按 §6 第 8 条，每个新数值声明都需要一条 `pytest.approx(..., abs=...)` 守护，会为纯说明性信息引入 3 条测试；而且 literal 一旦改动又需要再改 bound，重演本次缺陷。
- *直接删除该 parenthetical* —— 否决。规范性条款本就是 `abs=1e-6`，但删掉会丢失"为什么容差不能再紧"的可读信息，而 obligation 6 正是要把这条信息制度化。

### Decision 2 — A4 bias 用双侧有界守护，而非精确值守护

**选择**：`tests/test_sphere.py` 新增 `0 < |θ_impl − θ_exact| < 1e-6`，`(N_e=16,d_c=16)` 与 `(N_e=64,d_c=16)` 各一。

**理由**：spec 真正承诺的量是"`_betainc_regularized` 的系统误差 < 1 ppm，即角度域 bias < 1e-6 rad"。若写 `|bias| == approx(8.4878023e-7, abs=1e-9)`，等于把**当前求积的具体误差**固化成契约：将来有人改用更精确的求积（或直接调 mpmath），bias 趋近 0 时测试变红，而那恰恰是改进而非回归。

**备选与否决**：

- *精确守护 `8.4878023e-7`* —— 否决，如上；且 `CLAUDE.md` 的"数学约束"意图是钉住**原理**，不是钉住某个实现缺陷的当前数值。
- *只写 narrative 不加守护*（照抄 `decompmoe-skeleton` L116 现状）—— 否决。字面违反 §6 第 8 条；本 change 既然把该数值引入 `wayfinder`，就必须给它可验条款。
- *下界写成 `>= 0`* —— 否决。绝对值天然 `>= 0`，那会让下界恒真、整条守护退化为只检查上界。必须用严格 `0 <`，既断言"确有偏差"（排除实现恰好等于真根的巧合），又保留上界容差。

### Decision 3 — A3 的 spec 与 test 必须同批修

**选择**：`wayfinder/spec.md` 的 `γ_init` 改为 `−6.7835`，同时把 `tests/test_beta.py` 的 docstring、`gamma_cf` 字面量、注释一并改掉，并新增能捕获该 bug 类的守护。

**理由**：`CLAUDE.md` §8 的三传染通道之一就是"tests `assert == stale_value` LOCKS 传染"。上一轮 change 的 reviewer finding L3 给出的正确值是 `−6.78355`，task 1.4.7 实施时对 `−6.783545…` 作 half-up 取整写成 `−6.7836`，task 2.6.2 又把同值钉进测试。只修 spec 会让测试继续断言一个 spec 已不再声明的数。

**新守护的形态**（关键，有精度陷阱）：不能断言"5-sig 字面量精确复现 `β_0`"。以 `−6.7835` 反推 `β_0` 的残差约 `1.9e-6`（`|dβ/dγ| = 31·σ(1−σ) ≈ 0.03497` × 舍入差 `5.454e-5`），任何 `abs=1e-12` 量级的紧容差必红。正确形态是从另一条 spec 声明（`γ_init ≈ −3.5`）独立反解 `β_0`，再反解反事实 `γ`，然后断言

- `round(float(γ_full), 4) == -6.7835` —— 这一条才是真正能捕获 bug 类的守护：`round(-6.7835454, 4) == -6.7835`，而 half-up 写成 `-6.7836` 必然失败；
- `γ_full == pytest.approx(-6.7835, abs=1e-4)` —— 覆盖 5-sig 舍入差 `4.54e-5`。

**为何非 tautological**：`β_0` 由 adopted path 的 `γ_init ≈ −3.5` 声明反解，与被断言的反事实 `γ` 无共享表达式，构成两条独立 spec 声明的交叉对账；这正是 `governance` `req-gov-1` 场景中禁止的 "helper-tautology"（测试内 helper 重述被测公式）的反面。测试内须写明该理由。

### Decision 4 — A4 披露粒度以 `decompmoe-skeleton` 为对齐目标

**选择**：在 `wayfinder` req-11 的 definitional-layer 段补 angle-domain bias（`≈ 8.49e-7 rad` / `≈ 8.79e-9 rad` + 50-digit 精确值），并在 display precision note 末尾显式声明"angle-domain bias"与"prose-rounding gap"是两个**不可混淆**的量。

**理由**：`decompmoe-skeleton` req-6 "Bisection output + narrative precision disclosure" 已列出这两个值，`wayfinder` 只列了 residual。两者不矛盾但粒度不一，future audit reader 在 `wayfinder` 里看不到角度域偏差，会重复提出同一类 finding。补齐时同时写明两者是不同的量，避免"显示精度"与"实现偏差"被当成同一回事——这正是原 A4 误判的来源。

### Decision 5 — delta 用程序化构造（verbatim 保真的工程手段）

**选择**：本 change 的两份 delta 不手写重述，而是由脚本从 `openspec/specs/**` 提取 Requirement block 后做定点替换产出，每个替换断言命中次数；产出后再跑结构化 diff，确认只剩预期改动。

**理由**：本轮手抄重述实测产生了两处静默缺陷（时间戳 `22:02:52`→`22:52:52`；`σ'(-6.7836)` 的 ASCII 连字符被当成 U+2212）。两者都不会让 Markdown 渲染失败、也不会被肉眼在长 Requirement 里发现，只会在 archive 后悄悄污染主 spec。断言式替换把这类缺陷变成硬失败。

**备注**：源文同时使用 U+2212（`γ_init ≈ −6.7836`）与 ASCII 连字符（`σ'(-6.7836)`）两种减号字形，脚本必须分别锚定。

### Decision 6 — B1 deferred acknowledgment 由 `2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity` task 4 闭环

**背景**：`governance` req-gov-1 的 Scenario「Closed-form per-head extraction MACs use bare `==`」clause (3) 要求
MAC 计数必须来自实现侧实测（`torch.profiler` / hooks / AST），并以括号句承认 `tests/test_extraction.py::test_complexity_budget`
当时使用的是 helper-tautology 形态（记在 `proposal.md` "Deferred Items" (B1, B2)）。

**选择**：该 acknowledgment 由 change `2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity` task 4 闭环，
其 Scenario 括号句在本 delta 内一并更新为「已按 clause (3) 改为 AST 实测」。

**理由**：本 change 已对 `req-gov-1` 出**整块** MODIFIED delta，而 OpenSpec archive 是按 Requirement **整块覆盖**而非按行 patch。
若让 B1 的闭环另出一份 `req-gov-1` delta，两份未归档 delta 中**后归档者会静默丢弃先归档者的全部编辑**——不报错、不告警、
lint 与 `openspec validate` 全绿。折进本 change 是唯一零覆盖风险的路径。clause (3) 的前瞻性要求
（"any NEW test verifying the same claim MUST satisfy clause (3)"）**原样保留**。

**闭环内容**：T1 用 `inspect.getsource` + `ast.parse` 从 `extract_C` 源码恢复每个中间量的秩，按各算子实际消费的形状计费，
与 spec 字面量 `33_040` 裸 `==` 对账。选 AST 而非 profiler 的依据：本测试原 docstring 已记录 profiler 路径 backend-dependent
（CUDA kernel fusion 可致 2× 偏差），会破坏整数闭式的零容差意图。该计数器同时暴露了 spec 闭式枚举**未列出**跨头
`z_unit.mean(dim=1)` 归约（`d_c` 宽，`= 16` MAC/token）—— 见 `design.md` Decision 5 的风险段；补入需改
`decompmoe-skeleton` 闭式，不在本 change 范围。

**备注**：本 change apply 时 `2026-09-28-fix-skeleton-l98-residual-frame-tagging` 已归档（commit `d6c9350`），
`decompmoe-skeleton` anchor 覆盖恢复 23/23。

## Risks / Trade-offs

| Risk | Trade-off / Mitigation |
|---|---|
| **delta 与主 spec 漂移** —— apply 前主 spec 若被并行 session 修改，delta 的 verbatim 基础就变了 | apply 前重跑提取脚本的断言；任一替换命中数不为 1 即立即停止，不做"看着差不多"的手工修补 |
| **A4 有界守护的下界 `0 <` 可能被后人"简化"成 `>= 0`** | obligation 6 与 Decision 2 都写明理由；Scenario 的 `**AND**` 子句直接规定"必须是双侧界，不得对 pinned bias 值取等" |
| **A3 新守护依赖 `mpmath` 的 50-digit 求值**，若未来测试环境 `mpmath` 精度设置变化，守护可能漂移 | 守护断言的是**相对关系**（`β_0` 由 `σ(-3.5)` 反解、`γ` 再反解），不依赖任何硬编码的高精度常量；把 `mpmath.mp.dps` 显式设为 50 以上并写进测试 |
| **`governance` obligation 6 是新条款，可能被读作"以后所有 prose bound 都必须 = 规范容差"的过强约束** | 条款原文限定在"a Scenario carries a proximity bound numerically tighter than its own normative tolerance"这一具体失效形态，并显式允许"bound 满足即无需改动"的分支 (a) |
| **in-flight change `fix-review-findings-voronoi-precision-and-lineage` 46/47 未 archive**，本 change 与它存在时间重叠 | 本 change 只在 Source 反链中引用它，不修改、不 archive、不推进其 task；两者在 `.audit/` 与 archive 目录中各自留痕 |
