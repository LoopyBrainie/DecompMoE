# Design

## Context

见 `proposal.md` — Why。此处只记塑造方案的当前状态与约束。

`governance` req-gov-1 的 7 条 obligation 全部是「某类 claim → 某种断言形式」的逐案映射（整数闭式→`==`；浮点闭式→`pytest.approx`；二分 Voronoi→`abs=1e-6`；Monte-Carlo→`5σ`）。块内 `allclose`/`rtol` 零次规范性出现（唯一 `torch.allclose` 命中在 obligation 3 的散文里，非规范性）。因此 48 处 `torch.allclose` 站点整体落在规则之外——这是 FIX-020 判定「枚举代替一般义务」的具体机制。

实测基线（HEAD `dde0e1d` 干净导出、torch 2.12.1+cu130 / pytest 9.1.1、monkeypatch 采集 48/48 站点）给出三套互不替代的度量：

| 度量 | 问的是 | 结果 |
|---|---|---|
| 当前是否真翻转 | 现在有无真实漂移被默认 `rtol` 放过 | **2/48**（`test_extraction.py:461`、`:540`，均 `atol=1e-12`） |
| 放行区间放大 `widen=(1e-5·\|other\|)/atol` | 阈值被放大多少倍 | min 0 / median **7.344** / p75 72.05 / max 8.115e6；`widen<1` **16/48**；`≥100×` 10/48；`≥1000×` 4/48 |
| 结构分类 | 构造上是否可能被翻转 / 恒等 | 25/48 可能、23/48 构造不可能；19/48 站点 `delta==0`（已逐位恒等）；唯一 `\|other\|==0` 站点 `test_extraction.py:566`（`rtol` 项恒为 0，结构免疫） |

漂移实测（float32，与子任务独立复现 bit-identical）：`:461` = `7.450580596923828e-09`（2⁻²⁷）、`:540` = `1.1920928955078125e-07`（2⁻²³）、`:636` = `0.0`。三处 `atol=1e-12` 中只有前两处翻转，`:636` 已恒等。

约束：`skeleton` req-16 `:409` 把 EMA near-zero invariant 的 verifier 归属给 `test_near_zero_candidate_fallback`（def `test_extraction.py:496`，含 `:540`）；`:461` 所在测试名归 `:405` 空胞 invariant。skeleton `:456`/`:473` 已逐字要求 P4 用 `torch.where(use_old, prev, normalize(...))` guard。工作树当前 8 项脏，脏树跑 `run_gates.py` 以 `GATE RESULT INVALID` exit 2。

## Goals / Non-Goals

**Goals:**
- 把 req-gov-1 的阈值规则从枚举一般化为三条可判定义务，覆盖默认相对项 / 无容差 / 负极性三个空白面。
- 消除 2 处当前失明（`:461`、`:540`），并让其余 46 处的风险从「靠默认 rtol 侥幸」变为「显式且可导出」。〔基线：`evidence/flip-baseline.md` @ `dde0e1d`〕
- 让 `skeleton` `:409` 的 verifier 归属在 `:540` 改动后仍然成立（名实相符），delta 保持单一 capability。

**Non-Goals:**
- 不修 FIX-041（`req-gov-9` 悬空）、FIX-042（Source 豁免比例）——各自独立 change。
- 不 blanket 改 48 处为 `rtol=0.0`：与实测分布不符（16 处 `widen<1`、1 处结构免疫、8 处负极性方向相反）。〔基线：`evidence/flip-baseline.md` @ `dde0e1d`〕
- 不修 `.audit/fix001-verification-report.md` §A.6 的内部不一致（`.audit` 非 spec 路径）。
- 不改 `skeleton` req-16 的 invariant 本身（`:461` 是让实现向已钉死的 invariant 对齐，不是改 invariant）。

## Decisions

### D1 — 以 ADDED Requirement 承载一般义务，不重写 req-gov-1

req-gov-1 的 7 条 obligation 是新一般义务的**特化实例**（obligation 3/7 正是「阈值可导出」的二分实例、Monte-Carlo 实例）。因此新增三条一般义务作为独立 `### Requirement:`，req-gov-1 文本不动。

- **替代方案**：把三条并入 req-gov-1 作为 obligation 8/9/10（MODIFIED）。否决：req-gov-1 块已极长（L7–L65，15 行谈容差），再堆三条使「一 Requirement 一行为」失效，且 archive 时 MODIFIED 需整块复制，diff 噪音大。ADDED 保持 req-gov-1 为可读的特化清单。
- 三条各自独立成 Requirement（而非一条含三行为），符合 spec delta「一 Requirement 一行为」的拆分约定。

### D2 — 义务 1/2/3 的内容与「不点名站点」

三条义务分别对应：默认相对项显式且可导出（Req A）、无容差禁止（Req B）、负极性容差显式（Req C）。三者均以**一般义务**措辞，不点名任何现有测试站点——站点处置只在本 design 与 `tasks.md` 出现。这样 archive 后的主 spec 不依赖当前 `tests/` 行号（避免 `Cross-Reference Anchor Contract` 意义上的漂移）。

### D2b — 相对项声明范围：全量 46 采纳，(b) baseline-grandfather 否决（2026-10-13 裁定）

Req A 是**一般义务**，因此必须裁定「既有 34 处「有 atol、无 rtol」的正向站点」是否一并补上显式 `rtol=0.0`。采纳 **(a) 全量 46**，否决 **(b) grandfather + 前向 baseline lint**：〔基线：`evidence/flip-baseline.md` @ `dde0e1d`〕

- **(a) 采纳的理由（按权重）**：
  1. **严重度逻辑不允许 grandfather 大头**：翻转测试只证明 2 处今天真失明，剩余站点是「今天碰巧安全」——而「碰巧安全」正是本 change 要消灭的；`widen ≥ 100×` 10/48、`widen < 1` 16/48 的 latent 窗口不应以 grandfather 形式永久保留（病灶占实例数约 70%）。〔基线：`evidence/flip-baseline.md` @ `dde0e1d`〕
  2. **(b) 会重蹈 FIX-020 的诊断**：「rtol MUST 显式——除已登记的 34 处」是一条带 34 项枚举例外的一般义务，正是 FIX-020 所修之病（枚举代替一般义务）的换皮复发，且制造「新写的被卡、旧的全放行」的不对称。〔基线：`evidence/flip-baseline.md` @ `dde0e1d`〕
  3. **机制强度**：无条件 lint 可在含缺陷的树上自证判别力（本树 HEAD 即其反例），符合 `Archive Gate Must Be Executable` 的「不能失败的检查不是检查」；baseline lint 只卡增量、且改动既有调用点任意一行即可「洗白」，并需随每次迁移维护注册表（`req-gov-11` 的 stale exemption 即报红条款是历史教训的产物）。
  4. **安全性是实测的**：非翻转站点实测 `delta ≤ atol`（见 `evidence/flip-baseline.md`），故 `rtol=0.0` 不使任何测试转红（apply 后全量 513 passed 实证）；且这些 atol 均按 spec 声明逐案选定、不携带相对分量，`rtol=0.0` 是把通过条件还原成被声称的那个，而非「收紧」。
- **(b) 被否决的记录**：留给 reviewer 复核分叉。它以 34 行 diff 换取一个永久注册表、一条更弱的门禁、Req A 字面在 70% 实例上不成立，且把 FIX-001 与 FIX-020「同一处条文一体两面」的关系在 delta 里重新拆开。〔基线：`evidence/flip-baseline.md` @ `dde0e1d`〕
- 证据链：`evidence/flip-baseline.md` 的 per-site 表（`delta ≤ atol` 实测）是 (a) 不转红的呈堂证供；apply 后的 flip 复测（`evidence/flip-post.md`）是 Req A 的验收证据。

### D3 — 负极性义务的物理依据（为何不能与正向合并）

8 处 `assert not torch.allclose` 的 delta 是**有意做大**的（要证两量不等），`widen` 在这些点上让相等带变宽、否定断言**更难**成立——与「失明」方向相反。最极端 `test_extraction_phase.py:107`：`\|other\|=45.99` ⇒ 放行带 `1e-5·45.99 = 4.6e-4`。故 blanket 加 `rtol=0.0` 会在 40 处收紧、在 8 处**放松**——不是统一变严。负极性义务是独立第三条，不并入义务 1。

### D4 — `:461`：修实现（conformance），保留声明，升级 `torch.equal`

drift 机理不是 EMA 语义错误，而是 float32 两步舍入叠加（`α·c+(1−α)·mean` 在 `mean==c` 时二进制下 `0.9`/`0.1` 非精确，加 `normalize()` 除法舍入），量级恰在 ulp 级。修法：EMA 分支 return 前加一行显式空胞直通 `out = torch.where((n_i == 0).unsqueeze(-1), centroids, out)`，与 skeleton `:456`/`:473` 已逐字要求的 `torch.where(use_old, prev, normalize(...))` guard 同构，只对 spec 已逐字钉死的分支生效。

- 这是 **conformance 修复**，不是绕过 spec 改行为：spec（skeleton `:405`/`:434`）已声明 `n_i=0 ⇒ c_i^(t+1)==c_i^(t)` element-wise、`‖Δ‖₂<10⁻¹²`，不符的是实现侧。符合 CLAUDE.md §2「spec 优先」方向，不触碰 §6 边界（§6 禁的是绕过 spec 改行为）。
- 修后 drift 严格为 0（passthrough 使空胞行成为逐位恒等），比较器升级为 `torch.equal`——`torch.equal` 表达「逐位相同」，与 `atol=1e-12` 声称的机器精度恒等语义匹配。
- **替代方案**：放宽声明为「2⁻²⁴ 内」。否决：spec 已钉死 element-wise 恒等，放宽声明等于让实现迁就缺陷，违背「spec 钉死的形式 → guard 跟随该形式」。

### D5 — `:540`：float64 重建构造（保住 `:409` 归属，delta 保持单一 capability）

问题：当前 `:540` 测试构造（`X=0`、one-hot mask ⇒ `mean=0` ⇒ `candidate=0.9c`）**根本没有触发** near-zero fallback（`‖u‖<1e-9`），却在 skeleton `:409` 被登记为该 invariant 的 verifier。即「名字测 A、构造测 B」。

float32 下抵消舍入下限 `≈5e-8` 高于阈值 `1e-9`，故 EMA near-zero 路径在 float32 下近似不可达（唯一真实可达退化路径是空胞，走 `mean=centroids`，已由 `:461` 覆盖）。实测四个构造：

| dtype | mean 取法 | `‖candidate‖` | 触发 fallback？ |
|---|---|---|---|
| float32 | 字面 `−9c` | `2.2e-07` | ✗ |
| float32 | `−α/(1−α)·c` | `3.3e-08` | ✗ |
| float64 | 字面 `−9c` | `1.5944e-16` | ✓（余量 ~6.3e6，实测） |
| float64 | `−α/(1−α)·c` | `1.3e-16` | ✓ |

修正：把 `:540` 测试构造升到 float64（仓内先例：`test_full_differentiability` 显式用 `dtype=torch.double`），使 fallback 以约 7 个数量级余量稳健触发，且 `torch.where(use_old, centroids, …)` 的 passthrough 使 fallback 行逐位保留 ⇒ `torch.equal` 为真。测试名不变、声称不缩水、`:409` 归属不失效——只是构造终于匹配名字。delta 因此保持 governance-only（不需第二个 capability）。

- **替代方案 (i)** governance-only + `:540` 重新定位（改断言为幸存行闭式、收回 fallback 声称）。否决：会让 skeleton `:409` 的 verifier 归属当场失效，留下一个 knowingly 悬空的 `Verified by` 归属——本仓文化里这是更大的恶（`req-gov-4` 把部分闭合判为未闭合；FIX-001 自身的三次严重度改判史即 follow-up 会迟到的直接证据）。
- **替代方案 (ii)** 增加 `decompmoe-skeleton` delta 修 `:409`。否决：`(iii)` 以更低成本达成同一完整性——修构造而非修 spec 使其迁就一个测不到东西的构造。
- 后果与诚实警告：float32 下该 EMA near-zero 分支近似死代码。这一事实连同推导（抵消下限 `≈5e-8` > 阈值 `1e-9`）写入测试注释与本 design，供未来实现者判断，不掩盖。

### D6 — 比较器选型与 `torch.equal` vs obligation 2 的裁定（交 reviewer）

- 真正逐位相等的站点（`:461` 修后、`:636`）：`torch.equal`。
- `:540` 健康行：float64-ulp 推导的 `pytest.approx(abs=...)` + `f"actual={...}"`（req-gov-1 obligation 5 要求）。
- `pytest.approx` **不用于张量迁移**：`pytest.approx(tensor, abs=a)` 落进 pytest 内部 `ApproxNumpy` 分支（依赖 `__array__`），返回裸 `bool`，会丢失 `f"actual={...}"` 失败信息，且不检查 dtype/shape——比 `allclose` 更弱。逐位语义用 `torch.equal`，闭式浮点用 `pytest.approx`，不混用。

**`torch.equal` 与 obligation 2 的关系（交 reviewer 裁决，不静默选择）**：本 design 的读法是**不冲突**——obligation 2 的 scoped 对象是「closed-form float claims」（某个浮点闭式的值近似等于某数，禁其用 bare `==`）；而 `c_i^(t+1)==c_i^(t)` 是 spec 钉死的**状态恒等式**，passthrough 使其成为逐位事实。req-gov-1 obligation 2 内嵌的 **4-decimal display exception** 是同类先例：spec 钉死一种 display/identity 形式时，guard 形式跟随该形式（`round(x,4)==literal` 精确匹配），而非套浮点闭式的 approx 义务。请 reviewer 依此先例裁定。

### D7 — 可选机械门禁与工作树前置

新增一条 `scripts/lint_*.py`，经 `run_gates.py` glob 自动发现（`Archive Gate Must Be Executable` 已规定 glob 发现取代枚举），机械卡住「新写的 `allclose` 未显式给出相对项」。**前置**：工作树当前 8 项脏，脏树跑门禁 `GATE RESULT INVALID` exit 2；archive 前必须落定工作树或明确 pin。lint 自测需在引入新 `allclose` 的 mutant 上 exit 非零、在干净树 exit 0。〔基线：工作树项数由 `git status --porcelain` 实测〕

### D8 — 顺序：flip 快照先于修复

flip 分析（决策 2）在 HEAD `dde0e1d` 干净导出上先跑，作为「当前失明」快照（已完成：`2/48`）。`:461` 加 passthrough 后 drift 解析可知（严格 0），`:540` 改 float64 构造后 fallback 行 drift 解析可知（`torch.equal` 逐位），故不必复测即可写入 task。`:461` 与 `:540` 是同一 impl+test 修复 commit 的两个伴生 task。

### D9 — reviewer 若否决 float64 构造则回退到 (ii)

若 reviewer 认为「验证 dtype 必须与 MVP 运行时 dtype（float32）一致」而否决 float64 构造，则改走替代方案 **(ii)**——本 change 追加 `decompmoe-skeleton` delta 修 `:409` 的 verifier 归属——而非 (i)（governance-only + `:409` 悬空 + 等 follow-up）。理由： knowingly 让 spec 的 `Verified by` 归属悬空是更大的恶。

## Risks / Trade-offs

- **float64 构造偏离 MVP 运行时 dtype（float32）** → reviewer 可能否决。缓解：D9 预先登记回退到 (ii)；float32 不可达推导随附，论证「用 float64 使阈值语义可判」是有意的可判定性选择而非偷懒。
- **`:461` 改实现触碰 `src/decompmoe/extraction.py`** → 需确认 passthrough 不影响其它分支。缓解：只对 `n_i==0` 的行生效，`:636`（P4，已恒等）与健康行走原有路径；apply 时以全量 `pytest` + flip 复测把关。
- **在脏工作树上取门禁结果** → `GATE RESULT INVALID` exit 2，「通过」与「不知道」不可混读。缓解：D7 要求 archive 前落定工作树。
- **`torch.equal` 判定存目争议** → 交 reviewer（D6），design 已备好类比论证，reviewer 成本低。
- **新增 lint 覆盖面不全 / 误报** → 已缓解：`_COMPARATORS` 扩至 Req A 一般措辞（`torch.testing.assert_close` / `np.allclose` / `torch.isclose` / `math.isclose`）+ 模块别名解析（`import torch as th`），自检 10 例使判别力可自证；干净树 exit 0 / HEAD exit 1。残留缺口：经普通变量间接引用的比较器（`fn = torch.allclose`）静态不可解析，已在 lint docstring 记录而非掩盖。

## 已记录但未修的语义变更（审计披露，spec 中立）

- **`src/decompmoe/extraction.py:182` 空胞行 `∂out_i/∂c_i` 变更**：passthrough 使空胞行 Jacobian 从 `normalize` 的值（实测 `[0.402, 0.116, 1.270]`）变为恒等 `[1,1,1]`。`req-18` 已声明 EMA 三阶段 gradient channel Frozen（phase 1 `{c_i, beta_i, W_K, W_V, b}`、phase 2 `{c_i, beta_i}`、phase 3 `{c_i}`），故 spec 层中立；但这是 `src/` 真实语义变化且仓内无 `CentroidDriver` 梯度路径测试，故显式记录于此。
- **`:164` 空胞 `mean` 选择在 passthrough 后对输出不再 load-bearing**（passthrough 在 `:182` 直接返回 `centroids`）。`req-18` 的 `m_i ≡ c_i^(t−1)` 仍为规范性，故该行保留，并由 `tests/test_extraction.py::test_empty_cell_mean_selection_is_structural` 以 AST 结构守护钉住（实测：去掉该行时全部输出断言仍绿，仅此守护转红）。
- **`10⁻¹²` 的对账采用「恒等式 + 常数」双守护**：`test_empty_cell_preserves_centroid` 与 `test_extraction_phase.py::test_empty_cell_falls_back_to_the_previous_centroid` 各有一条 `‖Δ‖₂ < 1e-12` 显式断言直接对账 req-17 的常数，同两处的 `torch.equal` 守恒等式（`Δ == 0`，严格更强）。二者不是二选一——`torch.equal` 不断言该数，若无并行断言则修改 spec 常数不会让任何测试变红（已实测：删 passthrough 时两处均转红）。

## Migration Plan

1. flip 快照（已完成，HEAD `dde0e1d` 干净导出）→ 作为 evidence 落盘。
2. 归档本 change（spec delta 并入 `governance` 主 spec，新增 req-gov-13/14/15 三个 anchor）。
3. apply：`:461` 实现直通 + `:540` float64 重建 + 负极性/无容差站点显式化（同一 impl+test commit）。
4. 可选 lint 接入（经 glob 发现）。
5. archive 前落定工作树，跑 `run_gates.py` 取得 exit 0。

无回滚需求：spec delta 为纯追加；tests/impl 改动由 `:461` passthrough 与 `:540` 构造驱动，均为局部可逆编辑（`:461` 删一行直通即回到当前行为）。

## Open Questions

- `torch.equal` 与 obligation 2 的裁定（D6）交 reviewer；若否决，触发 D9。该裁定不改变 spec delta 内容（三条义务均不含 `torch.equal`），只影响 impl/task 的比较器选型，故可安全延后到 review 而不在本 change 内解决。
