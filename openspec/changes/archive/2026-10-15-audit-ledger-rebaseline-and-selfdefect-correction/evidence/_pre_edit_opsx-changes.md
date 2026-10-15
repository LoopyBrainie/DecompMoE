# opsx-change 桶：已定位问题清单（8 条）

> 本文件只收录 `bucket == opsx-change` 的条目。另有四桶 —— `conflict` / `archive-only` / `context` / `user-decision` —— 记录在同级的 `context/` 下，不在此文件。

**测量基线**：HEAD = `dde0e1d`（`git rev-list --count HEAD` = 261 commits）。本清单所有 evidence 均在该 commit 复算。
**性质**：这是**已定位问题的存目**，不是修复方案表。读者用它判断「哪里有问题」，怎么处理由人另行决定；因此全文不给出改法、目标值、优先级或处理顺序。
**输入**：`.audit/gradual-review-2026-10-07/_work3/c1/classified.json`（`items` 共 88 条；本桶 8 条）。**ledger 中 `FIX-033` 不在本桶**（HEAD 复验后归 `archive-only`）。

---

## 速览

| ref | 分类 | severity | location | 问题一句话 |
|---|---|---|---|---|
| **FIX-001** | **OPX-1** | CRITICAL | `tests/` 49 处 `torch.allclose(`（另 5 处记为无容差） | 49 处 `allclose` 全部省略 `rtol`，隐式默认 `rtol=1e-05` 参与判定 |
| **FIX-020** | **OPX-1** | MAJOR | `openspec/specs/governance/spec.md` req-gov-1（L7–L65） | 阈值推导规则被写成逐案枚举白名单而非一般义务，F-08/F-01 两类缺陷落在枚举之外 |
| **FIX-041** | **OPX-1** | MINOR | `openspec/specs/governance/spec.md` 编号序列 | `req-gov-9` 不存在，而 `openspec/changes/**` 有 20 处散文引用该编号 |
| **FIX-006** | **OPX-2** | MAJOR | `src/decompmoe/metrics.py:152-153` | 全体专家皆死时 SP 返回 `0.0`，与合法活测量 `SP = 0.0` 在输出层不可区分 |
| **FIX-007** | **OPX-2** | MAJOR | `openspec/specs/wayfinder/spec.md:778`（req-30 同节） | 一行内并含三处缺陷：取到点的见证条件、离球面的推导式、上确界措辞 |
| **FIX-034** | **OPX-2** | MINOR | `openspec/specs/wayfinder/spec.md:263`（req-11） | 不等式写的是估计量 `Â`，但 `A_i` 是带种子 MC 估计这一性质未与不等式同处 |
| **FIX-042** | **OPX-2** | MINOR | `openspec/specs/wayfinder/spec.md` req-34（@HEAD L853） | Source 字段豁免 20/70，集中在 `decompmoe-skeleton`（19）与 `wayfinder`（1） |
| **FIX-029** | **OPX-3** | MAJOR | 审计报告 F-08 所指测试（ledger 未给 `file:line`） | 该测试红绿由舍入残差**符号**决定：`d_c=16` 绿、`d_c=64` 红 |
| | | | | **本桶合计 8 条** |

排序：**按分类**，分类内再按 severity（CRITICAL → MAJOR → MINOR）、同级内按 ref。severity 是字段不是主键，见下节。

---

## 分类：本桶 8 条的分法

本清单**自成一册**：类号不与任何另一份清单共享，条目不跨文件对照。**分类**回答的是这一条属于哪一次 change；**不回答**怎么改、改成什么值、先做哪条 —— 改法、目标值、优先级、处理顺序仍全部不在本文件内。类内按 severity（CRITICAL → MAJOR → MINOR）、同级内按 ref 排序。

**severity 是字段，不是排序主键。** 它仍逐条记在速览表与每条的 `**severity**` 行内，但不再决定条目的归属与次序 —— 决定归属的是**分类**。

| 类 | 判据 | 成员 | 条数 |
|---|---|---|---|
| **OPX-1** | 该 change 的 delta 落在 `openspec/specs/governance/spec.md` | FIX-001 / FIX-020 / FIX-041 | **3** |
| **OPX-2** | 该 change 的 delta 落在 `openspec/specs/wayfinder/spec.md` 或 `openspec/specs/decompmoe-skeleton/spec.md` | FIX-006 / FIX-007 / FIX-034 / FIX-042 | **4** |
| **OPX-3** | 变更对象本身尚未定位到 `file:line`，无法判定 delta 落在哪一份 spec | FIX-029 | **1** |

| | | **本桶合计** | **8** |

### 不重不漏（本桶内，实测）

- **无重**：本桶 8 条 ref 两两互异；各类成员集合与速览表 `分类` 列逐类相等（3 + 4 + 1 = 8）。
- **无漏**：8 条 == `_work3/c1/classified.json` 中本桶的 8 条，集合完全相等（json-only 0 / list-only 0）。
- **口径**：每条在三处一致出现 —— 速览表 `分类` 列、所属小节的 `## 分类` 标题、条目的物理顺序；三者可逐条对照。

### 本节明确不覆盖的范围

`classified.json` 共 88 条，另 48 条在 `conflict`(22) / `archive-only`(12) / `context`(9) / `user-decision`(5) 四桶。这 48 条**不在本文件的 `## 附：` 之前，也不参与上面的归口计数**；它们的桶定义与分布记录在 `context/07-verdict-taxonomy.md` §1（实测：该文件记录的是四桶的**定义与条数**，48 条的逐条 ref 未在 `context/*.md` 中全量点名 —— 22 / 48 被点名，其余以桶级计数登记）。因此本节的「40 条不重不漏」是对**两份清单**的陈述，不是对 88 条的陈述。

---

## 分类 OPX-1 · 治理条文 delta（3 条）

### FIX-001 — CRITICAL

- **location**：`tests/` 下 48 处 `torch.allclose(` 调用点（含 `tests/test_extraction.py:461,540` 两处 `atol=1e-12`）；`tests/` 中 0 处传 `rtol=`；另 3 处完全不给容差：`tests/test_extraction.py:566`、`tests/test_extraction_phase.py:241`、`tests/test_gating.py:45`；对照 `src/decompmoe/sphere.py:514`（全仓唯一显式 `rtol=0.0`）
- **artifact**：`tests/**`；`openspec/specs/governance/spec.md` req-gov-1；`.audit/DecompMoE-逐级review.md:40,214-218`
- **problem**：48 处 `allclose` 全部省略 `rtol`。`torch.allclose` 的隐式默认 `rtol=1e-05` 使绝对允许量随被比较张量的量级线性放大，因此这 48 条比较的通过条件中含有一个从未被任何人选择过的相对项。
- **analysis**：危害性质是「默认值危害」，与 F-08 的「阈值推导危害」是两条不同规则；审计报告把二者并称为「恰好从同一条缝漏过」不成立（详见 FIX-020）。严重性取决于被保护的量与阈值之比：在 `tests/test_extraction.py:461,540`（`atol=1e-12`）上，实测漂移 `1.1920928955078125e-07` 恰好落在默认 `rtol` 的放行区间内，故该处默认 `rtol` 直接决定测试是否失明；在量级为 1 附近的量上影响可忽略。本项与 CFL-005 相互制约：报告「全仓」的表述因 `src/decompmoe/sphere.py:514` 而字面为假，但 `tests/` 侧的 48/0 计数独立成立。
- **consequence**：阈值相对量级越小、默认 `rtol` 的放行区间越宽，测试的判别力越弱；`atol=1e-12` 级的断言在默认 `rtol` 下的实际容差比其名义值宽约 8 个数量级。
- **evidence**（测于 `@dde0e1d`）：本轮复算 —— `git show HEAD:tests/*.py` → `allclose(` 计 **49**、含 `rtol` 计 **0**；`src/decompmoe/sphere.py:514` 逐字为 `torch.allclose(norms, torch.ones_like(norms), atol=1e-6, rtol=0.0)`。B5-gates §4 B-1 记录三次关闭史：2026-09-04 spec-math-audit 判为 gold-standard、2026-10-03 记为 F-9 MEDIUM、2026-10-07 记为 F-01 CRITICAL；`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md:2025-2027` 记录 owner 曾预先裁定修法并推迟，同时标注 F-9 阻塞归档前置条件。
>
> **D3 更正（2026-10-11）· 计数口径**：上文 evidence 行的「`allclose(` 计 **49**」是**文本 grep** 的结果，含 1 处**非调用点** —— `tests/test_extraction.py:510` 是散文行「through silently; the byte-exact \`torch.allclose(..., atol=1e-12)\`」。按 **AST 调用点**口径（`ast.Call` 且 `func` 渲染为 `torch.allclose` / `allclose`），`tests/` 实为 **48** 处；`rtol` 计数 **0** 不变。分布：`test_extraction_phase.py` 19、`test_extraction.py` 17、`test_gating.py` 3、`test_loss.py` 3、`test_sphere.py` 2、`test_experts.py` 2、`test_a3_contract_alignment.py` 1、`test_metrics.py` 1，合计 48。49 与 48 的差恰为 `:510` 一处，故「49」是**计数了提及而非计数了实体**。本条的 `location` / `problem` / `analysis` 三行已据此由 49 订正为 48。
>
> **D3 更正（2026-10-11）· 引用坐标**：上文原写 `lists/opsx-changes.md:2023-2027`，该写法使引用读作指向本文件自身，但本文件仅 **170 行**，不存在该区间；真实来源是**上一轮归档** `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md`。该文件 `:2023` 逐字为「change 处理——F-9 修好之前补 F-8 是无效功。」（属 F-8 段，非预裁决），预裁决正文起于 **`:2025`**（「**用户已预先裁决 F-9 的修法**：float64 守护「机器精度恒等」，float32 另设一个可达容差。」）并延至 `:2027`。故区间亦由 `2023-2027` 收窄为 **`2025-2027`**。
>
> **D3 更正（2026-10-11）· 「完全不给容差」由 5 订正为 3**：见下方「本轮复核」①；该复核自身也有一处偏差，已在其后更正。
- **severity**：CRITICAL
- **status**：ledger 无 `status` 字段（88 条中 82 条如此；5 条 UNVERIFIABLE、1 条 RESOLVED_AT_HEAD 均不在本桶）。
- **crossrefs**：CFL-005 / CFL-010 / FIX-020 / FIX-003 / FIX-029
- **source_ledger**：A3, A4, A5, B4, B5a, B5

> **本轮复核（记为存目差异，不改动上文 ledger 原文）**：
> ① `tests/test_extraction_phase.py:107` 实际给了容差 —— `atol=1e-6` 落在续行 L108（`assert not torch.allclose(` 起于 L107）。本轮逐处扫描得到的「完全不给容差」集合为 **4** 处（`test_extraction.py:566,598`、`test_extraction_phase.py:241`、`test_gating.py:45`），与上文所列 5 处相差该 `:107`。
> ② `tests/test_extraction.py:510` 不是调用点，是散文行（`through silently; the byte-exact \`torch.allclose(..., atol=1e-12)\``）；同组的真实 `atol=1e-12` 调用点是 `:461` 与 `:540`。
>
> **D3 更正（2026-10-11）· 复核 ① 本身仍有偏差，故真值为 3 而非 4**：复核 ① 把 `tests/test_extraction.py:598` 列入「完全不给容差」，但该调用点**给了**容差 —— `:598` 起 `assert torch.allclose(`，续行 `:599` `torch.linalg.norm(grad, dim=-1)`、`:600` `torch.full((N_e,), 0.05)`、`:601` `atol=1e-7,`，AST 读出 `keywords=['atol']`。故「完全不给容差」的真值集合为 **3** 处：`tests/test_extraction.py:566`、`tests/test_extraction_phase.py:241`、`tests/test_gating.py:45`。两处更正叠加以才对得上：ledger 原记 5 → 复核 ① 记 4 → D3 实测 **3**。

---

### FIX-020 — MAJOR

- **location**：`openspec/specs/governance/spec.md` req-gov-1（占 L7–L65 共 59 行，其中 15 行即 25.4% 谈 `rel`/`abs`/`approx`；义务 3 在 `tests/test_sphere.py:112,113,157` 被行使，义务 7 在 `:512,563` 被行使）；全治理 spec 中 `allclose` / `isclose` / `rtol` 出现 0 次；`openspec/specs/` 下 `rtol` 字面 0 次
- **artifact**：`openspec/specs/governance/spec.md` req-gov-1
- **problem**：req-gov-1 把「阈值须由该 dtype 的 eps 与量的尺度推导」这条规则写成了逐案枚举的白名单（义务 3 的二分、义务 7 的 Monte-Carlo 5σ），而非一般义务；其形式为枚举，故 F-08 那类阈值推导缺陷落在枚举之外，F-01 那类默认值缺陷同样不在其中。
- **analysis**：治理层的真实状态是「有该规则但未一般化」，而非审计报告所称的「零规则」—— 这比报告的诊断精确一个层级。5 个 lint 中无一触碰 `rtol` / `allclose` / `finfo` / dtype eps / 噪声底（见 CTX-002）。req-gov-1 中 `abs=0` 的惰性被测量并陈述了 4 次，且该测量的框架（pytest 9.1.1 上 `abs=0` 恰为 0）本身是有效的，这一点报告未质疑。本项最薄弱处是义务 7 的 σ 推导要求与断言表达式不同处：散文满足、断言未满足 —— `tests/test_sphere.py:547` 的 docstring 记录了「`abs=1e-3` 度是推导出的 `5σ = 7.31e-5` 度的 13.7 倍」，而 `:512` 与 `:563` 的断言表达式里写的仍是裸 `abs=1e-3`。
- **consequence**：`rtol` / `allclose` / `finfo` / dtype eps / 噪声底五类主题在 5 个 lint 中零覆盖，故 FIX-001 与 FIX-029 两类缺陷都没有机械门禁可依赖。
- **evidence**（测于 `@dde0e1d`，并经 git blob 复核）：req-gov-1 占 59 行，15 行谈容差（L13:8, L17:9, L30:6, L57:6, L37/42/52/61 各 4）；req-gov-1 内 `allclose`/`isclose`/`rtol` 计 0 次；跨 `openspec/specs/` 的 `allclose|isclose|atol` 5 次命中全部是英文单词 `disclosed` 里的子串 `isclose`，`rtol` 0 字面。义务 3 与 7 的行使位置见 `tests/test_sphere.py:112,113,157` 与 `:512,563`；义务 7 的引用记于 `:500`，散文推导记于 `:547`。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-001 / FIX-029 / FIX-033 / CTX-002
- **source_ledger**：A6, B3, B5

> **本轮复核**：governance spec 的 anchor 序列为 `:7 req-gov-1` → `:66 req-gov-2`，故 req-gov-1 块恰为 L7–L65（59 行），与上文一致。`tests/test_sphere.py` 抽查：`:112`/`:113`/`:157` 均为 `pytest.approx(..., abs=1e-6)`；`:512` 与 `:563` 均为裸 `abs=1e-3`；`:500` docstring 记 `5σ (req-gov-1 obligation 7)`；`:547` docstring 记 `13.7x the derived 5σ = 7.31e-5 deg`。全部与上文一致。

---

### FIX-041 — MINOR

- **location**：`openspec/specs/governance/spec.md` 的 Requirement 编号序列（req-gov-1…req-gov-8、req-gov-10、req-gov-11、req-gov-12）
- **artifact**：`openspec/specs/governance/spec.md`
- **problem**：`req-gov-9` 不存在，编号在 req-gov-8 与 req-gov-10 之间留下空档；`openspec/changes/**` 中有 20 处散文引用 `req-gov-9`（见 FIX-021）。
- **analysis**：空档本身可能是有意的（例如某条 Requirement 被撤回），但没有任何制品记录这一点，因此读者无法区分「编号保留」与「引用了从未定义的编号」。与 FIX-021 的耦合使后果具体化：20 处散文引向一个在本树无定义的 anchor id，且这些引用分散在已归档 change 的文本中。
- **consequence**：20 处散文引用悬空，指向一个在本树无定义的 anchor id；`#req-gov-9` 形式的锚点跳转无处可落。
- **evidence**（测于 `@dde0e1d`）：`openspec/specs/governance/spec.md` 共 11 个 Requirement（req-gov-1…8、10、11、12），无 `req-gov-9`；`openspec/changes/**` 散文普查得 `req-gov-9` × **20** 处引用，全部无活动锚点。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-021
- **source_ledger**：B2, B3

> **本轮复核**：governance spec 的 anchor 全序列为 `:7 req-gov-1`、`:66 req-gov-2`、`:100 req-gov-3`、`:160 req-gov-4`、`:191 req-gov-5`、`:241 req-gov-6`、`:335 req-gov-7`、`:369 req-gov-8`、`:408 req-gov-10`、`:494 req-gov-11`、`:544 req-gov-12` —— 共 11 个，`req-gov-9` 确认不存在，空档在 `:369` 与 `:408` 之间。与上文一致。

---


---

## 分类 OPX-2 · 数学条文 delta（4 条）

### FIX-006 — MAJOR

- **location**：`src/decompmoe/metrics.py:152-153`（全死时返回模块级哨兵 `_ZERO`）；`openspec/specs/wayfinder/spec.md:479`（req-20 SP_i 行的 `MUST NOT be reported as 0`）与 `:496-498`（Scenario「Dead-expert SP is undefined」，措辞为 `e.g. … or omitted` 的候选项）；`openspec/specs/decompmoe-skeleton/spec.md:573`（req-22 给出 `SP ∈ [−1,1]`）与 `:610-613`；`tests/test_metrics.py` 共 5 个 SP 测试（`:370,:382,:396,:412,:422`）
- **artifact**：`src/decompmoe/metrics.py`；`openspec/specs/wayfinder/spec.md`；`openspec/specs/decompmoe-skeleton/spec.md`；`tests/test_metrics.py`
- **problem**：全体专家皆死时 SP 返回 `0.0`，与一个合法的活测量 `SP = 0.0` 在位层面完全相同（`torch.equal` 为 `True`，两者 repr 同为 `'tensor(0.)'`）；唯一可区分点是对象身份 `live is _ZERO`，而那是哨兵的实现细节，任何日志、序列化或下游比较都区分不了。
- **analysis**：`MUST NOT` 确实存在于 spec，报告对内容的判定正确，但其引用形态有两处偏差：一是 `MUST NOT` 与同行的 `NaN` 候选措辞相隔 19 行而非同一行，且 `NaN` 出现在 `e.g.` 候选项而非强制位；二是 wayfinder req-20 未给 SP 的数值范围，`0.0` 落在 skeleton req-22 给出的 `[−1,1]` 内，故「0.0 违规」的路径并不直接成立。spec 侧另有一处空白：wayfinder/spec.md:496 的 Scenario 只规定单个死专家的行为，从未规定全体皆死时聚合 SP 的行为。测试侧未覆盖全死路径、`MUST NOT` 这条 Requirement 与 `C_t.numel()==0` 路径；`test_sp_range_containment` 结构上不可能抓到，因为 `0.0` 满足 `−1−1e-6 ≤ SP ≤ 1+1e-6`。诚实限定：20000 组随机活配置中落在 `|SP| ≤ 1e-8` 的有 0 组，故「不可区分」成立而「常见」不成立 —— 真实测量取到 `0.0` 需对抗式构造。
- **consequence**：「全死」与「活测量恰为 0」在输出层不可区分；spec 对全体皆死时聚合 SP 的行为无规定；测试对全死路径零覆盖。
- **evidence**（测于 `@dde0e1d`）：决定性构造 —— `d_c=2`，centroids `[[1,0],[0,1]]`，signatures `[[0.6,0.8],[−0.6,0.8],[0.8,0.6],[0.8,−0.6]]`，assignments `[0,0,1,1]`；两专家均存活（`‖T₀‖₁=‖T₁‖₁=2`），每 token 对齐度 `±0.6` 精确抵消（IEEE-754 保证 `0.6f + (−0.6f) == 0.0`），四个签名 `‖C_t‖` 精确为 `1.0`，`SP₀ = SP₁ = 0.0`。测试覆盖经全套插桩：5 次 SP 调用中全死 **0** 次。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：ARC-005
- **source_ledger**：A3, B3

> **本轮复核**：`metrics.py:152-153` 逐字为 `if not per_expert_means:` / `    return _ZERO`；`wayfinder/spec.md:479` 为 SP_i 表行，`:496-498` 为该 Scenario 三行（`#### Scenario: Dead-expert SP is undefined` / `- **WHEN** …` / `- **THEN** … NOT as \`0.0\``）；`decompmoe-skeleton/spec.md:573` 含 `SP ∈ [-1, 1]`，`:610-613` 为 SP range bound Scenario。全部与上文一致。

---

### FIX-007 — MAJOR

- **location**：`openspec/specs/wayfinder/spec.md:778`（req-30「Phase 2 β Box Equality」同节内）
- **artifact**：`openspec/specs/wayfinder/spec.md` req-30；`.audit/DecompMoE-逐级review.md:224`
- **problem**：该行同时含三个缺陷：(a) 断言界 `‖∂logit/∂C‖₂ = β‖c‖₂` 必须在 `c ⟂ C` 处取到，而该范数与夹角无关，正交只是充分见证而非必要条件；(b) 给出的推导式 `∂logit/∂C = β · c / ‖C‖` 在 `‖C‖ = 2` 处给出 16 而 autograd 给出 32，即离球面即错；(c) 在 sigmoid 参数化下 `0.1 + 31.9σ(γ)` 对一切有限 `γ` 严格小于 32，故 32 是上确界而非最大值，`MUST be attained` 的措辞依坐标系而定。
- **analysis**：三个子缺陷在同一行、同一 Requirement 内，(a) 与 (c) 是机理与量词描述，(b) 是写法缺陷。(b) 在定义域内（`‖C‖ = 1`）恒等因而不显形，只有在离开球面时暴露，故它是潜伏型而非显性错误。报告同样把「在正交处取到」当作机理陈述并沿用，构成 report 侧与 spec 侧的同源表述（见 CFL-006 的同类归属问题）。同一行还引用 Req 7 的第二条界 `|∂logit/∂γ| ≤ 15.95` —— 该界实测正确（见 ARC-009 所引），故本项不涉及 γ 侧。
- **consequence**：(b) 为潜伏型，缺陷仅在离开球面时显形；测试侧对 `c_i` 零覆盖（`tests/` 中 10 处 `autograd.grad` 调用无一以 `c_i` 或质心为求导变量），故这三处均无守护。
- **evidence**（测于 `@dde0e1d`）：autograd 对 `β ∈ {0.1,1,16.05,32} × d_c ∈ {2,3,16,64}` 复算，`‖∂logit/∂C‖₂ = β‖c‖₂ = β` 在 0°–180° 每个角度都成立；`‖C‖=2` 处 autograd 给 `32.0` 而公式给 `16.0`；`β=32` 时环境范数处处为 32，但 float64 中需 `γ ≳ 36.7368` 处 `σ` 饱和到 1.0 才取到。`tests/` 中 10 处 `autograd.grad` 调用无一以 `c_i` 或质心为求导变量，故 `c_i` 侧零覆盖。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CFL-006
- **source_ledger**：A2, B3

> **本轮复核**：`wayfinder/spec.md` 的 anchor 序列为 … `:774 <a id="req-30">` → `:792 <a id="req-31">`，故 L778 确在 req-30 块内；L778 逐字以 `The bound \`‖∂logit/∂C‖₂ ≤ β_max = 32\` in Req 7 MUST be attained (not merely bounded above) at the worst-case configuration: \`β = β_max = 32\`, \`‖C‖₂ = 1\`, \`‖c‖₂ = 1\`, \`c ⟂ C\`.` 起首。

---

### FIX-034 — MINOR

- **location**：`openspec/specs/wayfinder/spec.md:263`（req-11，`θ̂ ≤ G⁻¹((1/N_e)·Σ_i A_i) = G⁻¹(1/N_e) = canonical_voronoi_angle(N_e, d_c)`）；`openspec/specs/decompmoe-skeleton/spec.md:115`（req-6 同一不等式）、`:156`（`d_c=2` 时 Jensen 退化为等式的 caveat）
- **artifact**：`openspec/specs/wayfinder/spec.md` req-11；`openspec/specs/decompmoe-skeleton/spec.md` req-6
- **problem**：该不等式写的是估计量 `Â`，却未在任何一份 spec 中说明 `A_i` 是带种子的 Monte-Carlo 估计；因此它仅对真面积精确，对估计量只是一个关于偏差的陈述。
- **analysis**：严格性本身成立且已被双路建立：`(G⁻¹)″ = −G″/(G′)³` 在每个采样面积处为负，且凹性在 `G⁻¹(0) = 0` 处存活 —— `G′(θ) = sin^{d_c−2}θ/B → 0` 使 `G⁻¹` 在原点有垂直切线，但无穷左导数与凹性相容，局部展开 `G⁻¹(y) ~ ((d_c−1)·B·y)^{1/(d_c−1)}` 的指数 `1/(d_c−1) ≤ 1/2 < 1` 为凹幂律，故 Jensen 在闭区间 `[0,½]` 上两端均适用，含零面积胞。概率前提 `∀i: A_i < 0.5` 已写入并镜像于 `src/decompmoe/sphere.py:415` 与 `:440`，且推导全程无 cap-measure 步骤。`d_c = 2` 的退化 caveat 已在 skeleton spec 显式声明。故本项是欠规范而非错误：唯一缺口是估计量性质未与不等式同处。
- **consequence**：读者若不另行查阅 `A_i` 的来源，会把一条关于偏差的陈述读成关于真面积的等式；严格性链条本身不受影响。
- **evidence**（测于 `@dde0e1d`）：`d_c=16` 下 `(0.01, 1.00]` 上 `G″` 最小值 `2.127e-64 > 0`；`(G⁻¹)″` 在每个采样面积处为负；`y = 1e-12` 处 `G⁻¹` 实测 `1.854998e-01` vs 渐近 `1.846253e-01`；另一端 `y = ½` 处 `G⁻¹′ = B(7.5,½) = 0.658077758002940` 有限；`θ̂` 在 `wayfinder/` 下 0 出现，引入于 `wayfinder/spec.md:263` 与 `skeleton/spec.md:115`。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CTX-001
- **source_ledger**：A2, B3

> **本轮复核**：`wayfinder/spec.md:263` 为 `canonical_voronoi_angle(...) MUST return this closed-form value (computed via bisection ...` 起首的 API 行（其下即该不等式）；`skeleton/spec.md:115` 为同一 API 的 `SHALL provide` 行，`:156` 为 `- **AND** the one-sidedness bound ... is NOT a theorem in this degenerate case` 的 caveat 行。均与上文一致。
>
> **本轮复核（2026-10-12）· problem 段的记述与被引文本相反，且一处坐标偏差**：上文 problem 段称「`A_i` 是带种子的 Monte-Carlo 估计……**未在任何一份 spec 中说明**」，而被引的 `openspec/specs/decompmoe-skeleton/spec.md:115` 行内恰恰写明该说明：「`A_i` MUST be estimated by seeded Monte-Carlo over `VORONOI_AREA_SAMPLES` uniform probes on `S^{d_c − 1}`, each assigned to its `argmax` site, with the sample count and the seed fixed as module constants (`1_000_000` and `20260929`) so the returned value is deterministic.」原记「未在任何一份 spec 中说明」，现记「该说明就在上文所引的 skeleton spec 同一行内」；上文按存目原样保留该 problem 表述与 severity（问题是否仍成立需另行判断，本节只登记引用层的偏差）。另：上文 analysis 段称概率前提 `∀i: A_i < 0.5` 已镜像于 `src/decompmoe/sphere.py:415` 与 `:440`，实测 `:415` 为 `θ̂   = (1/N_e) · Σ_i G⁻¹(A_i)             where G = \`_cap_area\``、`:440` 为 `θ̂ = (1/N_e) Σ G⁻¹(A_i) ≤ G⁻¹((1/N_e) Σ A_i) = G⁻¹(1/N_e) = canonical` 这一 Jensen 推导行；字面前提 `∀i: A_i < 0.5` 在 **`:438`**，逐字为 `smaller than a hemisphere — \`∀i: A_i < 0.5\`. Then`。原记 `sphere.py:415` 与 `:440`，现记 `sphere.py:438`（前提行）与 `:440`（Jensen 推导行）；上文按存目原样保留 `:415`。

---

### FIX-042 — MINOR

- **location**：`openspec/specs/wayfinder/spec.md` req-34（@HEAD L853，缺顶格 `**Source:**` 字段）；`scripts/lint_no_source_field_drift.py:475-498`（`SOURCE_EXEMPTIONS` 登记表，规模 20 = skeleton 19 + wayfinder 1）；`openspec/specs/decompmoe-skeleton/spec.md`（23 个 Requirement 中仅 4 个有 Source 字段，19 个缺）
- **artifact**：`openspec/specs/wayfinder/spec.md`；`openspec/specs/decompmoe-skeleton/spec.md`；`scripts/lint_no_source_field_drift.py`
- **problem**：governance 11/11 有 Source 字段，wayfinder 35/36（req-34 缺），decompmoe-skeleton 4/23（19 个缺）；20 条 grandfathered 豁免集中在 skeleton（19）与 wayfinder（1）。
- **analysis**：本项本身不构成缺陷 —— 登记表的存在正是 req-gov-11 规定的机制，且该 lint 自身治理完备：已补字段、Requirement 消失、指向无 spec 的 capability 的条目均报 stale `SOURCE_EXEMPTIONS entry`，故登记表无法静默增生。记录本项是因为 20/70 的豁免比例是归档需要知道的当前状态：`decompmoe-skeleton` 的绝大多数 Requirement 没有可追溯的设计起源反链，因此该 capability 的谱系完整性低于另两份。
- **consequence**：三份 capability 的谱系完整性不均 —— `decompmoe-skeleton` 19/23 条 Requirement 无设计起源反链，读者无法从 spec 反查到 ticket。
- **evidence**（测于 `@dde0e1d`）：Source 字段计数 wayfinder 35/36（req-34 缺）、decompmoe-skeleton 4/23、governance 11/11；`SOURCE_EXEMPTIONS` 位于 `scripts/lint_no_source_field_drift.py:475-498`，规模 **20**（skeleton `req-1…11,13…17,19,20,22` 共 19 条 + wayfinder `req-34`）；`git show HEAD:scripts/lint_no_source_field_drift.py` 的 body 切片按 match 结束偏移实现。三个 Source lint 均 exit 0，独立印证计数。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-021
- **source_ledger**：B3

> **本轮复核**：`wayfinder/spec.md` 的 req-34 anchor 在 `:851 <a id="req-34"></a>`，标题在 `:853 ### Requirement: Source Field Format Invariant for OpenSpec Specs`，其正文（L855 起）通篇无顶格 `**Source:**` 字段 —— 与上文一致。`SOURCE_EXEMPTIONS` 定义确在 `scripts/lint_no_source_field_drift.py:475` 起、`:497` 收尾（`:498` 为 `)`），逐条数得 skeleton 19 条（`req-1…11,13…17,19,20,22`）+ wayfinder 1 条（`req-34`）= **20**，与上文一致。

## 分类 OPX-3 · 变更对象未定位（1 条）

### FIX-029 — MAJOR

- **location**：审计报告 F-08 所指的测试（同一构造在 `d_c=16` 上绿、在 `d_c=64` 上红：`eigvals[0]` 落在 `+1.1e-08` vs `−7.5e-09`）；该 `1e-10` 阈值在 `src/` 中无可执行字面量。
  > **ledger 未给出 `file:line`**，故此处按 artifact + 符号描述定位，未做行号引用。
- **artifact**：`.audit/DecompMoE-逐级review.md`（§4.3 F-08）
- **problem**：该测试的红/绿由舍入残差的符号决定，而非由数学决定：把同一个构造从 `d_c=16` 换到 `d_c=64`，`eigvals[0]` 的符号翻转，测试随之由绿转红。
- **analysis**：这是 F-08 的核心性质，也是它与 F-01（`rtol` 默认值）不能合并的原因：F-01 的阈值是无人选择的默认值，F-08 的阈值是被刻意写下、且低于 float32 噪声底、但未给出推导的那个值。共同根因是无义务把阈值从该 dtype 的 eps 与量的尺度推导出来，`rtol` 默认只是它的一个实例（见 FIX-020）。本项的 flakiness 无需复现偶然失败即可证明 —— 同一构造在不同 `d_c` 上给出相反结论，其决定因素是残差符号而非命题真伪。
- **consequence**：该测试的红绿不可解释（既不能读作命题为真，也不能读作命题为假），但不影响其他测试的判别力。`1e-10` 这一阈值只活在测试与散文里，`src/` 中零出现，与 FIX-023 中 `0.0476` 的情形同类。
- **evidence**（测于 `@dde0e1d`，F-08 强化复测）：同一构造 `d_c=16` 绿、`d_c=64` 红，`eigvals[0] = +1.1e-08` vs `−7.5e-09`。`1e-10` 字面量在 `src/` 中零出现。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-001 / FIX-020
- **source_ledger**：A5, A6

---


---
---

## 附：本文件的取数与自检
- **取数**：`_work3/c1/classified.json` → `items`（88 条）按 `bucket == 'opsx-change'` 过滤，得 **8 条**；`FIX-033` 不在其中（HEAD 复验后归 `archive-only`）。
- **severity 分布**：CRITICAL 1（FIX-001）、MAJOR 4（FIX-006 / FIX-007 / FIX-020 / FIX-029）、MINOR 3（FIX-034 / FIX-041 / FIX-042）。
- **status 分布**：8 条均无 `status` 字段（ledger 全局：NO_STATUS_FIELD 82 / UNVERIFIABLE 5 / RESOLVED_AT_HEAD 1，后 6 条均不属本桶）。
- **行号复核**：本轮对 8 条中的 file:line 引用逐条核对，除 `FIX-001` 记有 `:107` 一处偏差（见该条末「本轮复核」）外，其余均与 HEAD 快照一致；`FIX-029` 的 ledger 本身未给行号，已按 artifact + 符号描述。

---

## 附：本文件的措辞自检

> 本节与 `lists/direct-fixes.md` 的同名附录对称。两份清单此前**只有 direct-fixes 一侧有措辞自检**，opsx-changes 一侧没有 —— 于是「无方案泄漏」这一性质在本文件上从未被检验过，只是被默认。本节补上，使两份清单在该性质上具有可比的证据。

- **扫描范围**：**本文件正文**（头部注释 + 速览 + 分类节 + 8 条条目，即本附录之前全部 **18,933** 字符 / **212** 行）。**边界规则在此明示**：取至行首为 `## 附：` 的那一行的**行首**为止、不含该行 —— 与 `_work3/d3/leak_scan.py:4` 自述的 scope（"up to and excluding its own `## 附：` appendix"）及扫描器实际行为一致。不扫本附录自身 —— 附录按要求逐条列出模式名，模式名本身必然自命中。
>
> **本字符数写在附录内，故更新它不会使该数自我失效** —— 这正是附录被排除在扫描边界之外的用途。历史值：**19,575**（本附录上一段写下时的「归口分组」版，两小时后被「分类」重构取代）、**17,305**（归口一节加入前）、**17,317**（更早一版，取的边界规则不同，见本附录末条）、24,602（初记，对不上任何口径）。规则 A / B 之分与 12 字符成因的结论**均不因本次重构而改变** —— 那两个数是同一时刻同一文件上的差，与内容增删无关。
- **主模式集**（13 类，与 direct-fixes 同）：`should be` / `should change` / `fix by` / `replace with` / `add rtol` / `use NaN` / `建议` / `改为` / `修改为` / `修复` / `应当` / `推荐` / `patch`。

| 模式 | 正文命中 |
|---|---|
| `should be` / `should change` / `fix by` / `replace with` / `add rtol` / `use NaN` | 各 **0** |
| `建议` / `修改为` / `应当` / `推荐` / `patch` | 各 **0** |
| `改为` | **2** |
| `修复` | **1** |

- **逐处归类（3 处全部非泄漏）**：

| 位置 | 逐字 | 归类 |
|---|---|---|
| L6 | 「这是**已定位问题的存目**，不是修复方案表。……因此全文不给出改法、目标值、优先级或处理顺序。」 | 本文件的**性质声明**，逐字列举被排除的类别（「修复方案表」正是它声明自己不是的东西）。非处置建议。 |
| FIX-001 的 D3 更正注 | 「本条的 `location` / `problem` / `analysis` 三行已据此**由 49 改为 48**」 | 对**本归档自身计数**的更正。「改为」的对象是本文件此前的三行数字，不是 `src/` 或 `tests/` 的任何代码、测试或 spec。 |
| FIX-001 的 D3 更正注 | 「「完全不给容差」**由 5 改为 3**」 | 同上，对本归档自身计数（5 → 3）的更正。 |

- **相邻措辞扫描**（同 direct-fixes 的 11 类绕过模式）：`应当改为` / `建议改` / `应改` / `需改` / `改成` / `更正为` / `统一为` / `目标值` / `优先` / `先改` / `推荐使用` —— 命中 **2** 处，**同属 L6 那一行**（`目标值` 1、`优先` 1），均为上述性质声明的组成部分。

- **分类计数**：(a) 引用既有制品原文 **5** 处（机械判据：引文在某个受追踪制品中逐字出现即计入；其中「引用制品自身的**规范性祈使措辞**」子集为 **1** 处 —— FIX-001 的 `location` 逐字引 `src/decompmoe/sphere.py:514` 的 `torch.allclose(norms, torch.ones_like(norms), atol=1e-6, rtol=0.0)`，已对 `git show dde0e1d:src/decompmoe/sphere.py:514` 逐字核对一致；该引是本条全部证据的锚点，删之则证据不可复核）；(b) 本文件自身的处置建议 **0** 处。

- **结论**：(b) 类为 **0**，本文件在其正文范围内不含处置建议、不含替换值、不含优先级或处理顺序。(a) 类的 1 处为既有制品原文引用，按 direct-fixes 附录所用的同一判据（引文归属于被引制品、本文件只转述）归为非泄漏。

> **D5 复扫（2026-10-12）· 本附录两处数字已过时，(b) 仍为 0**：D5 轮对本文件正文（FIX-034 条）补入一处「本轮复核」注记后重跑同一判据（脚本 `_work3/d5/leak_scan.py`，即 D3 的 `leak_scan.py` 原样副本），正文实测 **174 行 / 17,305 字符**。13 主模式 + 11 绕过模式合计命中 **3** 处，**全部在 L6 那一行**（`修复` / `目标值` / `优先`），与上表逐行归类的第 (i) 条同源。
>
> 与本附录原记的差异有两处，均记在此处而不回改上表：原记 `改为` 正文命中 **2** 处（FIX-001 的两条 D3 更正注「由 49 改为 48」/「由 5 改为 3」），现记 **0** 处 —— 那两条注记在本附录写下之后已按 D3 的记法订正为「由 … **订正为** …」，故 `改为` 不再命中，原表两行归类随之失去对象；原记 (a) = **5** 处，现记 **7** 处（机械判据不变，即引文在某个受追踪制品中逐字出现即计入），增量来自 D5 新增注记中对 `openspec/specs/decompmoe-skeleton/spec.md:115` 的长段逐字引用。**(b) 类仍为 0** —— D5 未在本文件引入任何处置建议、替换值或优先级。
>
> **本附录字符数的成因（已查明，订正）**：原文此处记「三者互不相等、成因未查」。实测结论：**三个受口径约束的数字分属两套边界规则，另有一个对不上任何口径的数字。** 规则 **A** = 取至行首 `## 附：` 那一行的行首为止、不含该行（`_work3/d3/leak_scan.py:4` 自述的 scope，亦为扫描器实际执行者）；规则 **B** = 取至该标题行内 `自检` 二字之前为止。

> | 数字 | 出处 | 口径 | 成因 |
> |---|---|---|---|
> | **24,602** | 本附录原记 | —— | **对不上任何口径**：全文去掉所有空白仅 18,032 字符 |
> | 16,301 | D3 `verification.md` | A | D3 两处数字订正写入**前**的状态 |
> | **17,305** | D5 复扫 / 本次复跑 | A | 规则 A 下的当前实测，两次独立运行复现同值 |
> | ~~17,317~~ | 上一版本误标为「当前实测」 | B | 规则 B 下的当前实测；与上一行**同时测得**，差 12 字符 |

> **⚠ 上一版本所写「差 12 字符即 D5 在自测之后又补入的内容」经复测证伪。** 那 12 字符恰为附录标题自身的行内前缀：标题全行为 `## 附：本文件的取数与自检`，`自检` 位于行内偏移 **+12**。在当前文件上**同一时刻**同时测得 A = 17,305、B = 17,317 —— 两值之差**完全由边界规则决定，与有无内容增删无关**。真正的内容增量是 16,301 → 17,305 的 **+1,004** 字符（D3 的两处数字订正 + D5 的注记），且该两值**同属规则 A**，彼此可比。
>
> 连带订正：本附录「扫描范围」一行原记 24,602，上一版本订正为 17,317 —— 该值与扫描器实际边界及「不扫本附录自身」的自述相矛盾（17,317 会把附录标题行的前 12 字符算入正文）。现订正为 **17,305**。

---

> **⚠ 以下两段已被本段整体取代（2026-10-13 晚）· 「归口分组」已重构为「分类」**：本文件在数小时内先后存在两个版本的第二轴。第一版是跨两份清单**共享**的 `A`–`G` 归口组；第二版改为**本清单自成一册**的 `OPX-1`–`OPX-3` 分类。下文先记第一版，再记第二版（终态），以免「不静默订正」的纪律被绕过。
>
> **第一版（已被取代）· 归口分组**：正文新增「归口分组（第二轴：问题共性）」一节（速览表增列 `归口`），实测正文 **206 行 / 19,575 字符**（规则 A 边界）。PASS 1 原始命中 **4**（PRIMARY 1 / BYPASS 3），(a) = **7**，(b) = **0**。
>
> **第二版（终态）· 分类**：本清单改为**自成一册**的 `OPX-1` / `OPX-2` / `OPX-3` 三类，条目按类**重排**（分类为主键，severity 降为字段），速览表改为 `ref | 分类 | severity | location | 问题一句话` 五列。实测：
>
> | 项 | 值 |
> |---|---|
> | 正文规模（规则 A 边界） | **212 行 / 18,933 字符** |
> | 分类 | `OPX-1` 治理条文 delta **3** / `OPX-2` 数学条文 delta **4** / `OPX-3` 变更对象未定位 **1** = **8** |
> | PASS 1 原始命中（13 PRIMARY + 11 BYPASS） | **6**（PRIMARY **1** / BYPASS **5**） |
> | ├ PRIMARY 13 类命中 | **1** —— L6 `修复`（「不是**修复**方案表」，性质声明） |
> | └ BYPASS 11 类命中 | **5** —— L6 `目标值` / L6 `优先`（头部 L6 免责声明）+ **L31 `改成` / `目标值` / `优先`**（分类节的排除声明） |
> | PASS 2 (a) 逐字引用既有制品 | **7**（两版同值，未变） |
> | **(b) 本文件自身的处置建议** | **0** |
>
> **为什么 PASS 1 由 4 涨到 6 而 (b) 不变**：增量全在分类节首句「**不回答**：怎么改、改成什么值、先做哪条」这一句**排除声明**上 —— 它逐字列举了被排除的类别，因而自命中 `改成` / `目标值` / `优先` 三词。声明「本文件不做这些事」与「本文件做这些事」在这套模式表下不可区分，只能逐处人工裁定；裁定结果为**排除声明**，故 (b) 保持 **0**。这也说明 PASS 1 的计数**不能**单独作为泄漏指标，必须与裁定一同引用。
>
> **选词说明**：分类节一律用「分类 / 类 / 落点」，不用「建议」。理由不是「建议」一词本身有罪，而是**「分类」精确描述了该节做的事**（指派归属），而「建议」容易被读成提出处置 —— 措辞与实际行为一致，比事后辩解更可靠。
>
> **本附录上方 L225–238 的逐模式命中表与三处归类按留痕纪律不回改**，其与终态的差异记于此。第一版「归口」的分法（门禁工具失效 / 测试判别力 / 数学语义 / 引用完整性 / 审计制品自陈 / ticket 与 Source 治理）已被 `OPX-*` 取代，理由是它**跨两份清单共享命名空间**，导致读本文件的人必须打开另一份文件才能看全一类 —— 这与「两份清单不得混淆」相悖。

