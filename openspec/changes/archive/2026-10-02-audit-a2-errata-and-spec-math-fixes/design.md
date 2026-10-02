# Design

## Context

See `proposal.md` — Why。本节只补充**约束勘误工作本身的**事实。

**审计基线与漂移**：

| 项 | 值 |
|---|---|
| 审计基线（pin） | `6593a06` |
| HEAD（本轮复核时） | `188b9fb` |
| 分支 | `dev`（线性，无 merge commit） |
| 工作树 vs HEAD（`openspec/specs` `src` `tests`） | `git diff --stat HEAD --` 输出为空，即**完全一致** |
| `openspec/specs` 在 pin..HEAD 间 | 3 份 spec 被改动 |

**本轮复核方法约束**：工作树存在并行 session 的未提交内容（2 个 change 目录处于半归档状态、`wayfinder/tickets/WF-1.md` 被改、约 40 个未跟踪 `_numdrift_*.py` / `_tmp_*.py` 临时脚本）。因此本 design 的每条勘误与每个坐标都以 **commit object**（`git show <rev>:<path>` / `git grep <pat> <rev> --`）为唯一依据，**不读工作树文件**。

**两项改变实施方式的环境事实**：

1. **`.audit/` 被 gitignore**（`.gitignore:37`；`git check-ignore` 命中，`git ls-files` 报 `did not match any file(s) known to git`）。`lists/opsx-changes.md` **从未被 git 跟踪** ⇒ 勘误节是**本地协调文档而非版本化交付物**。活跃 change 目录同样在归档前 untracked（与 A-1 change 一致；归档时才进 git）。
2. **A-1 change 已完成**：`openspec list` 报 Complete，`## Errata` 节已写入清单 L1476（文件 146_935 → 155_223 B）。本 change 的勘误节紧接其后追加，不会产生重复标题。

**deltas 由脚本生成，不由手抄**：`decompmoe-skeleton` req-6 的 body 是**单行 6_110 字符**，手抄必然引入字符级漂移。故 delta 由 `gen_a2_deltas.py` 以「读当前主 spec → 逐条确定性字符串替换（每条断言恰好命中 1 行）→ 写 delta」的方式生成，并由 `verify_a2_deltas.py` 做**块级 diff 回验**（把 delta 的每个 MODIFIED block 与主 spec 同名 block 逐行对比，报告全部改动行 + 扫描失效 token）。首轮生成即被该回验拦下 4 处「只替换了行内片段、原行尾部悬空」的缺陷，已修正后复跑通过。

## Goals / Non-Goals

**Goals:**

- 让 19 处错误在**两处**可查：清单的 `## Errata (A-2 桶)` 节，且**在本 design 内有完整副本**（因 `.audit/` 不在 git 内，清单一旦被清理，勘误必须仍能从已归档的 change 恢复）。
- 记录每条勘误的**证据类型**（`实测` / `实测（数值）`），使读者能判断该结论的强度。
- 一次性修掉 10 条仍可执行的缺陷，且**每个写进 spec 的数值算式都配测试**（CLAUDE.md §6 / `governance/spec.md` req-gov-1：整数闭式 bare `==`，浮点闭式 `pytest.approx(..., abs=...)`，失败信息带 `f"actual={...}"`）。
- 登记与未归档 change 的重叠面，作为施工前门禁。

**Non-Goals:**

- ❌ 不改写清单 A-2 正文的任何既有结论、严重性或 `裁决` / `基线` 字段。
- ❌ 不修 N1–N4 四条「清单外新发现」——只登记，留给后续 change。
- ❌ 不裁决未归档 change `fix-review-findings-voronoi-precision-and-lineage` 的状态（只登记为门禁）。
- ❌ 不改 `src/` 的任何**可执行语句**（本 change 的 `src/` 改动仅限 docstring）。
- ❌ 不动 `context/00`–`07` 归档上下文（它们是 review run 的原始记录，与本勘误不一致是**有意的**）。
- ❌ 不直接编辑 `openspec/specs/**`——只经 delta + `openspec archive` 落地。

## Decisions

### D1 — 追加勘误节，不改写正文

**选择**：在 `lists/opsx-changes.md` 末尾追加 `## Errata (A-2 桶)`，A-2 正文 L376–L551 一字不动。

**理由**：清单是一次**已完成 review run** 的历史记录。改写它会销毁错误本身（读者再也无法区分「当时认为的」与「后来发现的」），并把一次 review 的产物伪装成持续维护的活文档。A-1 change 的 D1 已就 A-1 桶定过同一先例，本 change 沿用以保证两份勘误的可比性。

**备选与否决理由**：
- *就地改写错误行号* → 否决。会销毁错误本身。
- *另建一份勘误文件* → 否决。清单是唯一待办入口，勘误放在别处必然漏读。
- *在 `context/` 里改* → 否决。`context/` 是原始上下文，改它等于伪造 review 记录。

### D2 — 勘误锚定 HEAD 行号，同时标注 pin 行号

**选择**：每条勘误同时给出 pin 态与 HEAD 态坐标，并显式写出所用 commit。

**理由**：清单的行号体系是 pin 态坐标台账，而施工发生在 HEAD。两者都给出，实施者既能理解原意、也能直接施工。

### D3 — 勘误与本 design 互为副本（因 `.audit/` 不在 git 内）

**选择**：D4 节的 19 条勘误**完整地**出现在本 design 内；清单的 `## Errata (A-2 桶)` 节是它的对外呈现，并在节首记录本 change 名与本文件路径。

**理由**：`.gitignore:37` 使整棵 `.audit/` 不受版本控制，「只增不减」规则**没有 git 历史兜底**——一次 `git checkout --`、清理脚本或换机就能静默清掉整份勘误。把内容冗余进**会随归档进 git** 的制品，是唯一的持久化手段。

**备选与否决理由**：
- *在清单里维护、design 只引用* → 否决。引用会随清单一起丢失。
- *把 `.audit/` 移出 gitignore 并提交* → 否决。超出本 change 范围（会改变评审归档的跟踪策略），留给独立决策。

### D4 — 19 条勘误对照表（权威副本；清单节与本表同源）

证据类型：`实测` = 由 `git show` / `git grep` 直接读出；`实测（数值）` = 本轮独立计算得出。

| # | 条目 | 清单声称 | 实测 | 证据类型 | 后果 |
|---|---|---|---|---|---|
| E1 | AC-04 | `skeleton:98` 声明 `G` 在 `d_c=16` 于 `(82.8°, 90.0°)` 凹，`STILL_REAL` | pin `skeleton:98` 逐字含该句与 `82.8`/`98.1`/`179.1`；HEAD 三个数字**零命中** | 实测 | **stale**，实体已被 `e50cc02` 修；`STILL_REAL` 不成立 |
| E2 | AC-05 | `tests/test_sphere.py:523` 钉 `81.3148/82.6036/83.7313` 为凸性边界 | pin `:523` 确为 `def test_voronoi_angle_convexity_boundary()`（**清单行号准确**）；HEAD 该函数已删，改为 `:551` `test_voronoi_angle_precondition_is_area_below_half`，三个数成为「retired artefact」反向护栏 | 实测 | **stale** |
| E3 | AC-15 | `sphere.py:260` 的凹凸性分区图错误 | pin 实为 **261-262**（清单行号偏 2）；HEAD `:267-277` 已是正确版，`:288-294` 另加反有限差分警告 | 实测 | **stale**；`基线: unchanged-since-pin` **标错**（`e50cc02` 改 `sphere.py` 110 行） |
| E4 | AC-64 | `sphere.py:276` 峰值 `+31.5868°` / `θ*=38.9420°` | pin 实为 **278**（清单行号偏 2）；HEAD `:303` 已改为 `+31.5863380965°` / `38.9424412690°` | 实测 | **stale** |
| E5 | AC-84 | 该条件在 spec 中只是「MAY 级散文」，非 MUST 条款 | HEAD `wayfinder:246` 实为 **MUST 级**：`MUST strictly satisfy θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16) ≈ 20.36°` | 实测 | **stale**：残缺成分不成立，整条应降级为已失效 |
| E6 | AC-52 | 位置 `wayfinder:382`；总额 `33_040 MACs = 66_080 FLOPs`；`~0.83%` | 382 是**空行**，内容在 **383**（pin = HEAD，零漂移）；第 (3) 步 cross-head mean `H_kv·d_c = 128 MACs` 从未计入。真值 **`33_168 MACs = 66_336 FLOPs`**、**`~1.22%`**。驳回项复核成立：`66_336/33_554_432 = 0.1977% ≤ 0.3%`，allowance 不反转 | 实测（数值） | 成立，**全数**；清单行号错 + 数字错 |
| E7 | AC-46 | 位置 `skeleton:455`；`59%` 的随机批次不满足 exact | 455 非目标行，pin **456** / HEAD **459**（+3）。实体成立（float64 下约半数行不满足，最坏 `6.6613e-16`）；但 **`59%` 不可复现**——实测 float64 `49.4%–51.4%`、float32 `54.6%–57.3%`（4 维 × 2 dtype × 100 批 × 256 行），59% 超出观测上界 | 实测（数值） | 成立；**`59%` 不可作可 pin 判据**（口径依赖维度/dtype/形状/种子） |
| E8 | AC-42 | `_betainc_regularized` 在 `x→1` 时相对误差 **76%** | 位置 `sphere.py:73` **pin = HEAD，零漂移**（A-2 中唯一精确锚点）。MVP 点 `8.2915e-07` / `6.633 ppm` 正确；但 `x→1⁻` 实测 abs 升至 `1.5736e-01 @ θ=89.999°`，**相对误差 15.74%**，非 76%（差 5×；其引的 `7.61e-2` 绝对值本身对） | 实测（数值） | 成立；**清单数字错 5×**；`基线` 标 `unchanged-since-pin` **标错** |
| E9 | AC-53 | 位置 `wayfinder:251` | HEAD **252**。真值：按清单排除 `W^O` 得 `452_329_984 − 4_194_304 = 448_135_680`，差 **`0.9273%`** | 实测（数值） | 成立 |
| E10 | AC-82 | 位置 `wayfinder:248`；prose `≈ 484 M` | HEAD **249**。真值 `485_097_984`（偏差 `0.2263%`）。**但该值不以字面量出现在 spec 中**，反事实值是读者自行加总的派生值 ⇒ 清单「同段钉死的精确闭式」措辞**略强于事实** | 实测（数值） | 成立，但须同时注明派生性质 |
| E11 | AC-85 | 位置 `wayfinder:435`；「Qwen/GMoE **不可能**有相同 FLOPs」 | 位置**零漂移**（`:435` WHEN / `:436` THEN）。措辞越界坐实；但「不可能」在本仓内**不可证**（Mixtral 项理论上可重参数化），该半句应标为**推断**而非仓库内事实 | 实测 | 成立（措辞层）；`origin_ids` 推理需降级 |
| E12 | AC-86 | 位置 `wayfinder:398`；`≈ 64 KB` 与 `≈ 4 KB` | 398 是**空行**，内容在 **399**（pin = HEAD）。`W_proj` = `(8·4096 + 8·16)·2 = 65_792 B = 64.25 KiB`；字面张量集合 `{z, ẑ, z̄, C}` 各 `256 B`，即便按 `H_kv·d_c` 拼接也只 `1_600 B`，**只有 `H_kv·d_k·4 B = 4_096 B` 恰为 4 KB** | 实测（数值） | 成立，**两项均需改**（给闭式 + 改正张量集合） |
| E13 | AC-87 | Requirement 标 `wayfinder req-20` | L414 属 **req-19**（anchor L411，「Six Baseline Set On 4070 MVP」）；**req-20 是 L442「Eight Geometric Quantification Metrics」**，与 6 个 baseline 无关。同一清单 AC-85 对同一区域标对了 ⇒ 清单内部自相矛盾 | 实测 | 成立；**Requirement 归错** |
| E14 | AC-28 | `skeleton:98` 的 `d_c=2` 未提及 | 错误分区图已由 `e50cc02` 修；但 `d_c=2` 退化**仍未声明**：`git grep -ni 'affine\|d_c = 2'` 在 skeleton spec 只命中 L164 的 antipodal-distance Scenario（与 `G''` 无关） | 实测 | **仅残留真成分**，由 F1 修复 |
| E15 | AC-16 | `sphere.py:197` 的 accuracy caveat 只声明了 `< 1e-6` 一侧 | pin **197 = HEAD 210**（A-1 change 的 E2 勘误指向同一坐标）。**pin 态全段扫 `accuracy\|caveat\|1e-9\|1e-12\|residual\|totalit` 零命中** ⇒ 所述 caveat 在 pin 态**根本不存在**，是 `e50cc02` 之后才加的；清单把它当 pin 态事实是错的。`基线: unchanged-since-pin` **标错** | 实测 | 清单前提错误；**仅残留真成分**（π/2 硬跳变未披露），由 F9 修复 |
| E16 | N1（清单外） | — | `wayfinder:383` 把 bias **单列** `H_kv·d_c = 128 MACs`，`skeleton:151` 却**折进**第 (i) 项 `H_kv·(2·d_k·d_c + d_c) = 32_896`。总额同（33_040）**归因口径不同**，违反同源 Source 镜像的逐字性要求；req-17↔req-19 交叉注记只对齐总额、未对齐归因 | 实测 | **清单外新发现**，只登记不修 |
| E17 | N2（清单外） | — | `skeleton:34` 自称「(Matches master `wayfinder` Req 11 verbatim)」，但 master `wayfinder:252` 为「(`MVPConfig` does not currently expose them as learnable parameters at MVP scale)」，镜像为「(not exposed as learnable parameters in `MVPConfig` at MVP scale)」——**非逐字** | 实测 | **清单外新发现**，只登记不修（本次 F4 顺带删除了这句失真的 verbatim 声明） |
| E18 | N3（清单外） | — | `d_c=2` 时 `G(θ) = θ/π`（max dev `2.77e-18`），`canonical_voronoi_angle(N,2) = π/2` 精确成立；`sphere.py:242` 只挡 `signature_dim < 2` ⇒ **`d_c=2` 可达**。严格凸退化为等式、Jensen 变恒等式 ⇒ 单向性界**失去推导前提** | 实测（数值） | **清单外新发现**。**与 E14 是同一事实的两个侧面，修复由 F1 一次完成，不重复计数** |
| E19 | N4（清单外） | — | `sphere.py:288-294` 用「the true `G''` there is `+0.21`…`+2.46`」的**区间散文**冒充闭式（真值 82° → `+2.6073`、88° → `+0.7366`），与 AC-64 属同类瑕疵 | 实测（数值） | **清单外新发现**，只登记不修 |

**E20（实施期新增，清单外）—— `d_c = 2` 是单面板 GL-8 求积唯一的「小 `x` 侧」失效点**

本条在**实施 F1 时**发现，不在原审计范围内，但对 F1 的可实施性是决定性的。

| 观测 | 值 |
|---|---|
| `_cap_area(θ, 2)` 对 `θ/π` 的相对偏差 | **`3.64%`–`6.41%`**（`θ ∈ (0°, 90°)`，最差在 89.9°） |
| `canonical_voronoi_angle(N_e, 2)` 对 `π/N_e` 的相对偏差 | 最差 **`5.39%`**（`N_e = 32`）；`N_e = 4/8/16` 分别为 `4.78%`/`5.24%`/`5.36%` |
| `N_e = 2` 看似准确 | `6.71e-9` —— **假象**：二分落在 `x >= 1.0` 早退平台 `π/2` 上，即 F9 披露的那处不连续，而非求积准确 |
| 根因 | `d_c = 2 ⇒ a = (d_c−1)/2 = ½`，GL 面板被积函数 `u^(a−1) = u^(−1/2)` 在**左端点平方根奇异**；`d_c ≥ 3 ⇒ a ≥ 1` 被积函数在 `u=0` 光滑 |

**决策**：F1 的 Scenario **不写**「实现满足 `G(θ) = θ/π`」——因为它不满足。Scenario 分三层：(a) 精确实数算术下的恒等式 `G(θ) = θ/π`、`G'' ≡ 0`、`θ = π/N_e`；(b) 单向性界在此退化为**非定理**；(c) 实现的实测偏差带（`3.64%`–`6.41%`、`5.39%`）与根因，并要求测试**钉偏差带而非闭式**。

**理由**：计划初稿的测试断言是 `_cap_area(0.37, 2) == pytest.approx(0.37/math.pi, abs=1e-12)`。实施前探测发现该断言**必然失败**（实测 abs 偏差 `5.896e-03`、rel `5.01%`），而 req-6 的数值纪律要求 spec 里的每个算式都能被 `pytest.approx` 对账——即**照初稿写会产出一个没有任何实现能满足的 Scenario**。这与 E19/N4、AC-42/F10 是同一类错误的镜像（单点最优冒充全域），只是发生在**小 `x` 侧**而非 `x→1` 侧。

**与 req-6 既有惯例一致**：该 Requirement 已经用「impl-internal frame」同时给出实现值与真值（如 `1.16e-14` vs `4.15e-7`），本次沿用同一处理方式，而非引入新框架。

**归属**：只**声明**不修复。修 `d_c = 2` 的求积精度需要给 GL 面板加细分，属 `src` 行为变更，超出本 change（`src` 改动仅限 docstring）的范围 → 记为 open question 6。

**根命题复核（6 条共用项的数学前提）**：对 `d_c=16`，`G''(θ) = (d_c−2)·sin^{d_c−3}θ·cosθ / B((d_c−1)/2, ½)`；因 `sinθ>0` 对 `θ∈(0,π)` 恒成立，`G''=0 ⟺ cosθ=0 ⟺ θ=π/2`，故 `π/2` 是光滑拐点而非分支端。mpmath 50 位：0.05° 网格全区间**仅 1 个**变号点；二分求根 `90.000000°`；`G''(82.6036°) = +2.4567878`、`G''(97.2°) = −2.4055898`。伪零点复算（复刻 GL-8 节点/权重 + `h=1e-5` 中心差分）：`81.314831° / 82.603619° / 83.731280°`，与清单逐位吻合，而三点的**真** `G''` 严格为正。⇒ **根命题为真**，但前提成立 ≠ 条目成立：5 条实体已修（E1–E5）。

### D5 — AC-52 的修复必须三处联动，且 allowance 换分母

**选择**：F3 作为一个不可拆分任务，同时改 `wayfinder req-17`（body）、`wayfinder req-19`（交叉对账注记**全文**）、`decompmoe-skeleton req-7`（MAC 闭式）。

**理由**：Req-17 的总额一旦从 `66_080` 改成 `66_336 FLOPs`，Req-19 的交叉对账注记**每一处引用都必须跟着动**——首轮生成只改了净差那句，块级回验立刻发现注记开头仍在引用 Req-17 的 `33_040 MACs = 66_080 FLOPs` 与 `+272 MACs = +544 FLOPs`。这正是计划里列为「最容易漏的一步」的地方。

**并且 allowance 的分母必须换**：改后净差从 `32`（`0.0484%` of `FLOPs_Routing`）变为 `288`（`0.436%` of `FLOPs_Routing`）。原句「roughly `0.05%` of `FLOPs_Routing`, well under the `0.3%` allowance」把两个分母混用，数值与口径**同时**失效。`0.3%` allowance 本身仍成立——它的分母是 active-core 切片：`66_336 / 33_554_432 ≈ 0.1977% ≤ 0.3%`。故拟改文明确写出「`0.436%` 是相对 `FLOPs_Routing` 的比值、**不是** allowance 的度量」。

**备选与否决理由**：
- *只改 Req-17* → 否决。spec 内部立刻自相矛盾（两个 Requirement 对同一数字给出不同值）。
- *把 0.3% allowance 放宽到 0.5%* → 否决。allowance 未经复算就被放宽属于用「改判据」掩盖「改数据」，而复算证明原判据成立。
- *保留 `≈ 0.83%` 并加脚注* → 否决。脚注不能替代正文数字；下游 grep `33_040` 会漏掉脚注。

### D6 — `W^O` 消歧：改口径而非改闭式

**选择**：把 `W^O` **移出**排除清单，并显式写出「排除它会得到 `448_135_680`（−0.9273%），那不是闭式」。

**理由**：清单原文在同一 Requirement 内让三件事不能同时为真——假设 3 把 `W^O` 绑为注意力输出投影、假设 4 的排除清单又排除 `W^O`、而同段的 `4·d_model²` 与闭式 `452_329_984` 都**必须**包含 `W^O`。实现与全部测试都站在闭式一侧，**孤立的是排除句**。因此改排除句，不改闭式。

**顺带**：F4 删除了 `skeleton:34` 那句失真的「(Matches master `wayfinder` Req 11 verbatim)」——它自称逐字却不逐字（E17）。这不是独立修复，而是 F4 重写该行时的直接后果。

### D7 — Dedup 登记：与 A-1 勘误及未归档 change 的重叠

| 重叠方 | 重叠内容 | 处置 |
|---|---|---|
| A-1 change 的 **E2** | AC-08 勘误 `sphere.py:197` → `canonical_voronoi_angle` HEAD `:210` | **与 E15 引用完全同一坐标**（pin 197 就是 `def canonical_voronoi_angle` 行）。勘误节须交叉引用 A-1 的 E2，避免读者看到两条「不同」勘误指向同一行而误判其中一条为误 |
| 未归档 `fix-review-findings-voronoi-precision-and-lineage` | tasks 全 `[x]` 但**无 `specs/` delta**；H2/H2b/L7 动 `tests/test_sphere.py` Voronoi 区域（与 AC-05 现在的 `:551` 重叠）；M4 动 `skeleton:98`（与 F1 同一 locus） | **只登记，不处置**。必须在动手改 `tests/test_sphere.py` 前裁决它处于「已 inline 应用未归档」还是「停滞」——否则可能重复施加同一处改动。裁决结论记入 `tasks.md` 门禁 |
| `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` | 半归档：`proposal.md`/`tasks.md` 已删除未提交，`specs/` 目录仍在 | **门禁**：其 archive 会改动 spec 基座。`4f3e752` 本会话内已改 `wayfinder/spec.md` 15 行，基座确在漂移 |

### D8 — 四个被修改的 skeleton Requirement 没有 `**Source:**` 行

**事实**：`decompmoe-skeleton` 的 `**Source:**` 行只出现在部分 Requirement 上（HEAD 位于 L255/L428/L503/L631，分属 **req-12 / req-18 / req-21** 及之后），本 change 修改的四个 skeleton Requirement（req-2 / req-6 / req-7 / req-19）**一个都没有**。`scripts/lint_no_source_field_drift.py` 只校验**已存在**的 `**Source:**` 行，因此当前 `exit=0` 并不代表每个 Requirement 都有反链。

**选择**：**不**为本 change 新增 skeleton 侧的 `**Source:**` 行。

**理由**：为它填反链需要确定该 Requirement 的 ticket 血缘。本 change 无法从证据确定 req-19（`spherical_l2_normalize`）的血缘归属，而 CLAUDE.md §3 明令「设计起源是 `CLAUDE.md` amendment 但 ticket lineage 不存在：MUST 迁到 `governance/`，不得在 `wayfinder/` 用 "(historical, …)" 硬贴」。**写一个可能错误的反链比留空更糟**——那正是这条 lint 存在的目的。

**wayfinder 侧照常追加**：req-11 / req-17 / req-18 / req-19 均有 `**Source:**` 行且首项为 `` `wayfinder/tickets/…` ``，本 change 的 Decision 引用**追加到行尾**，保持 ticket 为第一个 top-level item ⇒ lint 规则 4（primary-first）自动满足。

**记录为 open question**（见下）。

## Risks / Trade-offs

**[只改 Req-17 不改 Req-19 注记] → spec 内部自相矛盾，且 `0.436% > 0.3%` 会被误读成 allowance 被突破** → D5 把 F3 绑为不可拆分任务；delta 由脚本生成并做块级回验，首轮即拦下该缺陷；`tasks.md` 验收含「三处 `33_168 MACs = 66_336 FLOPs` 字面一致」。

**[archive 吞 anchor]** → `openspec archive` 是整块覆盖，会因 MODIFIED block 尾部边界判定**吞掉紧随其后那个 Requirement 的 anchor**（每个被改的恰好丢 1 个）。本 change MODIFIED **8 个** Requirement（skel 4 + wayfinder 4），全在高危位置。archive 后**必须**复算 anchor 覆盖（`grep -c 'a id="req-'` vs `grep -c '^### Requirement:'`，并逐个确认配对无孤儿）——`exit code` 与 `~ N modified` 计数**都不是证据**。若丢失：`git show <archive-prev>:<spec>` 覆盖回去 → 用确定性字符串替换重放定点编辑（每条断言 old 恰好出现 1 次）→ 复算 anchors/headings/dup → `git diff --numstat` 恰等于声明行数。**绝不重跑 archive。**

**[基座在他处漂移] → delta 与主 spec 脱节** → 两个半归档 change + 并行 session 都在动基座。archive 前以「delta ↔ 当前主 spec 的预期差异行数」为 tripwire 复核；对不上即 report-and-stop，**重建 delta**（生成脚本运行时读主 spec，重跑自动带上对方新内容），**绝不重跑 archive**。

**[手抄 6_110 字符单行] → 字符级漂移** → delta 一律由脚本从主 spec 生成 + 块级 diff 回验，人工不参与长行转写。

**[勘误被当作活文档整篇改写]** → 勘误节首行显式声明「正文结论一律不改写」并写明理由（归档记录的是当时那轮 review run）；本 design 的 D4 是第二份权威副本，即使清单被改写也能比对。

**[勘误因 `.audit/` 不在 git 内而丢失]** → D3：内容冗余进会随归档进 git 的本 design。

**[AC-46 的 59% 被当契约]** → E7 明写「不可作可 pin 判据」并给出实测区间；F2 改用 `4·eps_f64` 有界陈述，**不引用任何百分比**。

**[AC-84 的 9207 步被当事实]** → E5 与 open question 3 明写「仅在不计 Phase 0 时成立（计则 10_207）；`beta_effective()` 对 phase 0 直接 `raise`」——这是**规范本身的缺口**，不是本 change 能顺手补的。

**[F2 的 `4·eps_f64` 上界被误当成实测值]** → 该界是**解析上界**（4 个 ulp），实测最坏是 `6.6613e-16`（约 3 ulp）。spec 与测试分别标注「上界」与「实测最坏」，不得混用。

**[并行 session 提交覆盖] → 本 change 的产物被静默回退** → 提交只暂存本 change 的路径（`git diff --cached --name-only` 逐条核对），禁止 `git add .`；提交后用 `git show HEAD:<path>` 核对**效果**而非 commit 是否存在。

## Migration Plan

不适用（纯规格与文档变更，无部署 / 无数据迁移）。

**回滚策略**：删除 `lists/opsx-changes.md` 末尾的 `## Errata (A-2 桶)` 节、删除本 change 目录、以及 `git checkout` 三个被改文件（`src/decompmoe/sphere.py`、`tests/test_sphere.py`、对应 spec）即可。**唯一不可回滚的风险点是 `openspec archive`**：它整块覆盖主 spec，archive 后回滚必须走 G3 的「从 `<archive-prev>` 还原 + 重放」路径，不能重跑 archive。

## Open Questions

以下可安全延后，不影响本 change 的 spec、方案或任务拆分：

1. **`fix-review-findings-voronoi-precision-and-lineage` 处于何种状态？** tasks 全 `[x]` 但无 delta，可能是「spec 已被 inline 修改、未走 delta 流程」，也可能是「停滞」。**必须在动手改 `tests/test_sphere.py` 前裁决**——若为前者，本 change 与它重叠的部分可能已被部分解决，需要重新定位。

2. **本 change 修改的 4 个 skeleton Requirement 为何没有 `**Source:**` 行？** lint 只校验已存在的行，故 `exit=0` 掩盖了这个缺口（D8）。补反链需要确定 ticket 血缘，尤其 req-19；血缘不明时应按 CLAUDE.md §3 考虑迁到 `governance/`，而不是硬贴 `(historical, …)`。建议独立 change 处理。

3. **AC-84 的 Phase 0 β 语义** —— `beta_effective()` 对 `phase == 0` 直接 `raise ValueError`，spec 未给 Phase 0 的 β 公式。**这是规范本身的缺口**，建议单独开 change；本 change 只在勘误中记录「9207 仅在不计 Phase 0 时成立」。

4. **AC-46 若要写成可 pin 的百分比契约** —— 需先固定「维度 × dtype × 批次形状 × 种子」的口径并登记为模块常量。本 change 用 `4·eps_f64` 有界陈述规避该问题，故不阻塞。

5. **N1 / N4 的修复归属** —— 分别与 F3（bias 归因口径）、F9/F10（区间散文冒充闭式）同 locus，建议并入下一轮「spec + src 语义」change。N2 已被 F4 顺带消解（失真的 verbatim 声明已删除），但其**镜像逐字性**问题在 req-11 ↔ skeleton req-2 两侧仍需单独裁决。

6. **`d_c = 2` 的求积精度要不要修？**（E20 的处置面）`canonical_voronoi_angle(N_e, 2)` 偏离 `π/N_e` 达 `5.39%`。修它需要给 `_betainc_regularized` 的 GL 面板加细分或换求积器，属 `src` **行为**变更，超出本 change 范围（`src` 改动仅限 docstring）。本 change 只把它**声明**进 spec。是否修、怎么修（细分面板 / 换 `scipy.special.betainc` / 直接在 `d_c=2` 走解析闭式 `θ=π/N_e`）留给独立 change 裁决——注意最后一条选项会把 `d_c=2` 变成特例路径，与 `d_c≥3` 的统一实现不同，需评估是否值得。
