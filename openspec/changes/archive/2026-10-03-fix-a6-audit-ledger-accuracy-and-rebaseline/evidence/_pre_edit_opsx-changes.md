# 清单 A：需走 OpenSpec change 的条目

> 审计基线：pinned commit `6593a06`。本文件所有 `file:line` 均为 **pin 态行号**。
> 源数据：`_work/classified.json` 的 `opsx-change`（102 条）与 `user-decision`（6 条）两个桶，共 108 条，本轮原样搬运，未重排 verdict、未重判严重性、未重算任何数学。
> 本轮性质：**纯整理**。不含任何新发现。
> 交叉核查来源：`_work/check-completeness.json`（完整性 / 分桶冲突 / 基线重算）、`_work/check-contamination.json`（方案污染扫描）。
> 审计材料：`_final_report_full.md`（§1 L11 / §2 L23 / §3 L76 / §4 L1255 / §5 L1379 / §6 L1412 / §7 L1511 / §8 L1537 / §9 L1565 / §10 L1606 / §11 L1647）、
> `_handoff_verdicts_all.json`（197 条 lens 裁决）、`_handoff_delta.json`（27 条 delta）、`_handoff_mutations.json`（8 组变异）、`_handoff_pin.json`（7 条 pin 基线）。

---

## 本文件的读法

这一层的条目意味着：**问题的处置对象是 `openspec/specs/**` 里的真相源本身，或者它的解法取决于真相源写什么。**
按 `CLAUDE.md` §2 的真相源优先级与 §3 的工作流约定，想改 DecompMoE 行为先改 spec、不直接动代码；
反过来，**当缺陷落在 spec 的措辞、契约、交叉引用、change 制品或门禁流程上时，改代码就改不对**——
代码只是把 spec 的错误语义固化了一遍。清单 A 就是这类条目的集合。

它分成 8 个主题（A-1 ~ A-8），归属判据是**问题落在哪一层**，不是难易：

- **A-1 数值守卫缺口：spec 声明了数学闭式或不变量，tests/ 无原理级断言** —— 落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。
- **A-2 spec / 文档层的数学陈述与条款措辞缺陷** —— 缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。
- **A-3 spec 与 src 实现之间的语义偏离** —— 实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。
- **A-4 交叉引用与行号指针失效** —— spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。
- **A-5 OpenSpec 制品格式、门禁与归档流程** —— 落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。
- **A-6 裁决口径、镜像分歧与先例争议** —— 落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。
- **A-7 wayfinder advisory 层（map.md / tickets）漂移** —— 按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。
- **A-8 需用户裁决（user-decision 桶）** —— 问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。

### 基线状态字段怎么读

每条的 `基线` 是**机械查表**的结果，来自 `_pin_drift.json`（`git diff 6593a06..188b9fb` 的 hunk 行区间），
只回答一个问题：**pin 之后这个文件的这一段行被动过没有。**

- `unchanged-since-pin` = 该行区间不在任何 hunk 内。
- `touched-since-pin` = 该行落在某个 hunk 内。

**它不回答「问题是否已修复」或「问题是否仍存在」。** 本文件 108 条中 10 条记 `touched-since-pin`、98 条记 `unchanged-since-pin`，
这只说明它们的位置在 pin 之后是否漂移，**不构成任何一条仍然成立的断言**。要判断现状必须回到 HEAD 重新定位。

两条口径提醒：

1. `_pin_drift.json` 的生成脚本未记录区间取的是 pin 侧还是 HEAD 侧坐标。classified.json 全表 193 条里 191 条在 pin 坐标下自洽，
   故以 pin 坐标为工作假设；若口径相反，个别条目的 touched/unchanged 判定会翻转。
2. 本文件对 108 条全部重算了一遍，**发现 1 条与记录不符（AC-27）**，已在该条下标注并以查表结果为准。

### 与清单 B 的边界

**user-decision 桶（UD-01 ~ UD-06）同时被清单 B（`lists/direct-fixes.md`）收录。**
上游 classified.json 把这 6 条归入 user-decision，而本轮两份清单的取数范围在这一桶上重叠。
本文件保留这 6 条（`§A-8`）是为不丢信息；**以哪一份为准由整理轮的组织者裁定**，本轮不替其决定。
另有两条例外关系需要登记：

- 清单 B 的 **DF-08**（main18：spec 浮点闭式 claim `~0.83%` 在 tests/ 全目录无 `pytest.approx` 对账，locus `openspec/specs/wayfinder/spec.md:382`）
  按 classified.json 自己写下的分桶规则应落本清单 A-2，却落在清单 B。同 locus 的 **AC-52**（W02）在本清单。
- 清单 B 的 **DF-09**（main13：`.gitignore:37` 对 wayfinder spec 重复副本的威胁）被报告 §10 Batch D-2 列进 opensx change 批次，
  但 classified 落 direct-fix；按该批次执行时该条会漏。
- **UD-04**（W44：CLAUDE.md 对 ticket 既声明非约束又要求维护）与本清单 A-7 的 7 条 map.md / ticket 漂移条目共享同一批 finding id，
  会被两份清单分别计数。

### 交叉核查角标的读法

正文里出现的方括号角标来自两份交叉核查结果，**不是新发现**，只是把上游已知问题挂到对应条目上：

- `[口径冲突]` —— 报告自身对同一 finding 给出互相矛盾的三处判断，裁定前该条去留待定。
- `[分桶存疑]` —— check-completeness 判定该条实际应落 archive-only（它们是「证据不足 / 复验驳回」声明，不是行动项）。
- `[基线存疑]` —— 记录的 `baseline_status` 与 `_pin_drift.json` 机械查表结果不符。
- `[溯源存疑]` / `[溯源缺口]` —— `origin_ids` 指向与内容不符，或报告 §3 的 finding id 未进入该条溯源。
- `[同实体未合并]` —— 两条指向同一实体的不同侧面，上游合并规则要求同实体 + 同 `location_file` 才合并，本轮未合并。
- `[规则越界]` —— 该条按上游自己的分桶规则应在本清单，却落到了清单 B。
- `[边界保留]` —— 交叉核查判为 borderline 但结论是保留。
- `[已净化]` —— 原 problem 含祈使句，已改写为纯问题分析（详见「交叉核查」第 2 条）。

### 关于「不含修复方案」

本文件只写：位置、问题是什么、为什么是问题（数学或逻辑依据）、证据出处、严重性、归属理由。
条目里出现的真值与真位置（例如「真 G'' 在 θ=82.6036° 处为 +2.4568，而 pin 实现中心差分给 +9.9920e-06」）是数学与逻辑依据，
用来证明原值错在哪，删掉读者就无法复核，故保留；它们不是修法提案。
上游 schema 层面已无 `suggested_fix` 字段可承载方案，三反引号代码块在 193 条上命中 0 次。

---

## 分类概览

| 主题 | 条目数 | CRITICAL | MAJOR | MEDIUM | MINOR |
|---|---|---|---|---|---|
| **A-1** 数值守卫缺口：spec 声明了数学闭式或不变量，tests/ 无原理级断言 | 24 | 3 | 9 | 6 | 6 |
| **A-2** spec / 文档层的数学陈述与条款措辞缺陷 | 15 | 2 | 3 | 4 | 6 |
| **A-3** spec 与 src 实现之间的语义偏离 | 15 | 0 | 4 | 5 | 6 |
| **A-4** 交叉引用与行号指针失效 | 15 | 0 | 1 | 2 | 12 |
| **A-5** OpenSpec 制品格式、门禁与归档流程 | 18 | 0 | 9 | 3 | 6 |
| **A-6** 裁决口径、镜像分歧与先例争议 | 7 | 1 | 4 | 2 | 0 |
| **A-7** wayfinder advisory 层（map.md / tickets）漂移 | 8 | 0 | 0 | 1 | 7 |
| **A-8** 需用户裁决（user-decision 桶） | 6 | 0 | 4 | 0 | 2 |
| **合计** | 108 | 6 | 34 | 23 | 45 |

- 裁决分布：STILL_REAL 88、PARTIALLY_REAL 15、MOVED 5
- 基线分布：`unchanged-since-pin` 98、`touched-since-pin` 10

---

## A-1 数值守卫缺口：spec 声明了数学闭式或不变量，tests/ 无原理级断言（24 条）

落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。修不修得动取决于 spec 侧是否把该闭式写成可验条款，因此属于 change 层而不是单纯的测试补强。

### AC-01 — distance.logit 零守卫：变异体死于 autograd 崩溃而非数学断言

- **源 id**：`C-001` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：CRITICAL
- **位置**：`src/decompmoe/distance.py:24`（pin 态）
- **Requirement**：wayfinder req-7 L123 / skeleton req-8 L148 / req-5 L91-92
- **溯源 id**（`origin_ids`）：`mutate:0`、`main62`、`C-010`、`rv:main62:math`、`rv:main62:impact`、`rv:grv:gap11:math`
- **问题**：协议把该目标记为 killed，但杀死它的规定变异体（torch.zeros_like）的信号来自 test_logit_grad_safe 抛出的 RuntimeError（element 0 of tensors does not require grad），即 autograd 图断裂，而不是任何数学断言。补跑的 4 个保持图连接的变异体（图保持零、纯符号翻转 -β(inner−1)、丢掉 β、β·sign）全部 212 passed，其中符号翻转把 spec 要求的 -32 变成 +32 并落在 [0,+2β] 仍全绿。根因是全套 212 个测试只调用该原语 2 次，src/ 下无任何模块调用它，tests/test_beta.py 的 test_logit_range 与三个梯度测试全部在测试体内内联重算 beta*(inner-1.0)，从不 import 被测原语。
- **证据**：_handoff_mutations.json mutate:0（mutantSurvived=false, killedBy=[test_distance.py::test_logit_grad_safe]）；报告 §5 表格第 0 行 + §5『mutate:0 必须单独点出』
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-02 — 变异守护覆盖率：8 个数学不变量仅 12.5%–37.5% 被数学断言约束

- **源 id**：`C-009` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：CRITICAL
- **位置**：`src/decompmoe`（pin 态 line=0，目录级/模块级定位，无有效行号）
- **Requirement**：governance req-gov-1 obligation 5 / CLAUDE.md §6 第 8 条
- **溯源 id**（`origin_ids`）：`C-001`、`C-002`、`C-003`、`C-005`、`C-009`
- **问题**：以本轮 8 个被攻击的 spec 数学不变量为分母，按『pytest 以数学断言（非词法 grep / 非 autograd 崩溃 / 非与实现自洽的伪影）约束该不变量语义』为口径：完整约束 1 个（12.5%），真断言但部分覆盖或单线 3 个（37.5%），零守卫或伪守卫 4 个（50%）。另三个独立证据同向：UR 零调用、MVPConfig 字段集零断言（注入 spec 禁止的 beta_max 字段后全绿）、d_c≠16 零覆盖。controlsUnusable=0，8 个 control 全部 212 passed，故存活不是 harness 故障造成的假象。
- **证据**：报告 §5『守护覆盖率判断』段
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-03 — logit 闭式与值域无原理级守卫，恒返回 0 变异体全绿

- **源 id**：`C-010` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：CRITICAL
- **位置**：`tests/test_beta.py:184`（pin 态）
- **Requirement**：wayfinder req-7 L123 / skeleton req-8 L148
- **溯源 id**（`origin_ids`）：`rv:main62:impact`、`rv:main62:math`、`rv:main62:source`
- **问题**：decompmoe.distance.logit 的闭式 logit = β·(Cᵀc − 1) 及其值域 ∈ [−2β, 0] 完全没有对实现的原理级守卫：一个恒返回 0 的变异体通过全部 213 个测试。test_logit_no_w_i 用 inspect.signature + getsource + ast.parse 三重提取函数体做硬检查，是全库最严的守卫之一，但它只检查结构不检查数值，CLAUDE.md §6 第 8 条在这条路径上被完全绕过。
- **证据**：_merged_verdicts main62（TEST-GUARD-01）；报告 §8 正面清单 + §5 mutate:0
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-07 — 球面归一化零数值守卫：分母加 detach 全绿

- **源 id**：`C-003` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/sphere.py:49`（pin 态）
- **Requirement**：skeleton req-7 L132-134（Scenario 点名 gradcheck）/ wayfinder req-6 L98-99
- **溯源 id**（`origin_ids`）：`mutate:2`、`main64`
- **问题**：把归一化分母加 .detach() 后全套 212 passed，协议记为 survived。独立 oracle 实测：原实现 gradcheck PASS，加 detach 后 FAIL；前向 C.norm() 两边逐位相同（1.4142135623730949），但 K/V/W_K/W_V/b 的解析梯度相对数值梯度错 32.04% / 40.40% / 28.59% / 33.93% / 24.72%。现有 test_full_differentiability 只断言梯度非 None、有限、范数 > 1e-12；test_no_surrogate_in_codebase 是对 extract_C 源码的 '.detach(' 不出现词法扫描，detach 在一层调用帧之外。spec 自己点名的 torch.autograd.gradcheck（skeleton req-7 L145-147，ATOL 1e-5）全仓 0 次调用。
- **证据**：_handoff_mutations.json mutate:2（mutantSurvived=true, killedBy=[]）；报告 §5 表格第 2 行
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-08 — canonical_voronoi_angle 偶然守卫：纯名字 grep

- **源 id**：`C-005` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/sphere.py:197`（pin 态）
- **Requirement**：skeleton req-6 L118-120（no hard-coded table values Scenario）
- **溯源 id**（`origin_ids`）：`mutate:4`、`main65`、`gap18`
- **问题**：全精度硬编码查表（6 个被测输入）+ 变量名 _T 变异体 212 passed；同一张表逐字节相同、只把变量改名 _VORONOI_MVP_TABLE 才 1 failed，即守卫的唯一信号是 assert '_VORONOI_MVP_TABLE' not in src 这条字面量扫描。return _cap_radius(1.0/num_experts, 16)（忽略 signature_dim）同样 212 passed，因为 instrumented 显示套件只出现 distinct d_c values: [16]、26 次调用、6 个 (N_e,d_c) 对。d_c != 16 零覆盖是变异目标层面的偶然守卫而非真实覆盖。
- **证据**：_handoff_mutations.json mutate:4（mutantSurvived=true, killedBy=[]）；报告 §4 环 6 证据 D + §5 表格第 4 行
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-09 — 不完全 Beta 积分真守卫但只覆盖 2/13 点且阻碍正确化

- **源 id**：`C-006` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/sphere.py:67`（pin 态）
- **Requirement**：skeleton req-6 / governance req-gov-1 obligation 4
- **溯源 id**（`origin_ids`）：`mutate:5`、`D3-06`、`C-062`
- **问题**：规定变异体（b=0.5→0.45）偏差 +1.3579e-2 rad，是契约的 13578 倍，7 个测试死，真实守卫。守卫在 +1.1818e-6 处绑定（+1.1813e-6 仍全绿），名义值 ~6e-10 rad 内；7 个 killer 中 4 个是自指的（用被测的 _betainc_regularized 自己去算 ½·I，对任何常数缩放按构造不可见），且负方向能活到 -9.96e-6（幅度大 8.4 倍）。覆盖只有 (16,16) 与 (64,16) 两点，13 点探针里 6 点越界无人在看。更关键的是正向精度改良变异体（用 t = 1-u² 消奇点，偏差从 9.7e-3 降到 1e-14，精度提高约 10^7 倍）触发唯一失败 test_voronoi_angle_convexity_boundary，即测试套件主动禁止实现变正确。
- **证据**：_handoff_mutations.json mutate:5（7 个 killedBy）；报告 §5 表格第 5 行 + §4 环 6 证据 B/C
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-10 — UR 闭式 W=100 窗口在 tests/ 下零调用零断言

- **源 id**：`C-011` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`tests/test_metrics.py:65`（pin 态）
- **Requirement**：wayfinder req-20 L453 / skeleton req-22 L522
- **溯源 id**（`origin_ids`）：`rv:main63:impact`、`rv:main63:math`、`rv:main63:source`、`rv:gap21:math`、`rv:gap21:source`
- **问题**：把 UR 改成恒返回 0.5 后 213 个测试全部通过。src 已实现该闭式，但整个 tests/ 目录零调用、零断言，属『src 有 / test 无』的半落地。与 C-002 是同一缺陷的 finding 侧与变异侧两个独立记录。
- **证据**：_merged_verdicts main63（TEST-GUARD-02）与 gap21（W1-COVER-UR-01）；报告 §9 逐项落地缺口表首行
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。
- **交叉核查**：**[同实体未合并]** 本条与 AC-33（W11）、AC-41（C-026）指向同一 UR 闭式缺口的三面，`location_file` 同为 `tests/test_metrics.py:65` / `src/decompmoe/metrics.py:73`；classified.json 的合并规则要求同实体 + 同 location_file，本轮未合并。报告 §3 的 main37 由这三条共同承载。

### AC-11 — extract_C 可微性只做功能检查，gradcheck 零调用

- **源 id**：`C-012` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`tests/test_extraction.py:283`（pin 态）
- **Requirement**：skeleton req-7 L132-134 / wayfinder req-6 L98-99
- **溯源 id**（`origin_ids`）：`rv:main64:impact`、`rv:main64:math`、`rv:main64:source`
- **问题**：D-path 不变量只有『梯度非 None、有限、非零』这类功能性检查。把归一化分母 .detach() 的代理梯度（surrogate gradient）实现通过全部 213 个测试，而 gradcheck 立刻抓到。spec Scenario 明确点名 torch.autograd.gradcheck，仓库内 0 次调用，等于 spec 的可验声明没有执行者。
- **证据**：_merged_verdicts main64（TEST-GUARD-03）；报告 §5 表格第 2 行
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-12 — 禁硬编码表 Scenario 只 grep 标识符名不 grep 数值

- **源 id**：`C-013` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`tests/test_sphere.py:61`（pin 态）
- **Requirement**：skeleton req-6 L118-120
- **溯源 id**（`origin_ids`）：`rv:main65:impact`、`rv:main65:math`、`rv:main65:source`、`rv:gap18:math`、`rv:gap18:source`
- **问题**：Scenario 规定用 0.9076 / 0.4494 / 0.380 / 0.0971 四个字面量 grep sphere.py，实际测试 grep 的是符号名 _VORONOI_MVP_TABLE，Scenario 规定的检查形式与执行者不一致。因此一个对 (4,16) 或 (16,8) 的硬编码查表快路径通过全部 213 个测试；变异实验进一步显示只要把硬编码表改名为 _T，212 passed。
- **证据**：_merged_verdicts main65（TEST-GUARD-04）与 gap18（W2-MATH-05）；报告 §4 环 6 证据 D
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-13 — MVPConfig 字段集契约零断言，加 beta_max 字段全绿

- **源 id**：`C-014` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`tests/test_config.py:24`（pin 态）
- **Requirement**：skeleton req-21 L499-502 + L485 / governance req-gov-4 L144
- **溯源 id**（`origin_ids`）：`rv:main66:impact`、`rv:main66:math`、`rv:main66:source`、`rv:gap23:math`、`rv:gap23:source`
- **问题**：Scenario『MVPConfig field set is exactly …』（11 个字段，且 beta_min / beta_max MUST NOT 是 MVPConfig 字段）完全没有守卫：tests/ 中零处使用 dataclasses.fields(MVPConfig)，实测加第 12 个 beta_max 字段后 213 个测试全绿。这是 spec 唯一一处可枚举断言的字段集合契约，也是 governance req-gov-4 污染通道 (i) 可验证性的落点。
- **证据**：_merged_verdicts main66（TEST-GUARD-05）与 gap23（W1-COVER-FIELDSET-03）；报告 §5『另外三个独立证据』
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-18 — 反射分支测试声称守护该分支却通过

- **源 id**：`C-063` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`tests/test_sphere.py:553`（pin 态）
- **Requirement**：skeleton req-6（theta > pi/2 反射分支）
- **溯源 id**（`origin_ids`）：`D1-06`、`D2-03`
- **问题**：这是唯一实际执行 theta > pi/2 缺陷带的测试，但它通过——_cap_area 在 theta=pi/2 处有真硬不连续（左极限与右极限在 d_c=8/16/32 分别相差 5.239884e-2 / 7.870852e-2 / 1.158112e-1，与 pin 逐位相同），该测试的断言形式对这一量级的跳变不敏感。
- **证据**：_handoff_delta.json D1-06 与 D2-03；报告 §4 环 8
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D1-05 由本条承载，id 未进 `origin_ids`。

### AC-33 — req-20/req-22 的 UR 闭式 src 有实现而 tests 零调用

- **源 id**：`W11` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/metrics.py:73`（pin 态）
- **Requirement**：wayfinder req-20 / decompmoe-skeleton req-22
- **溯源 id**（`origin_ids`）：`gap21`、`mutate:1`、`main63`、`gap3`
- **问题**：UR 指标在 wayfinder req-20 与 skeleton req-22 两份 spec 中都有含具体数值的闭式（(1/N_e)·Σ I[f_i > 0]，W = 100 窗口），src 已实现，但整个 tests/ 目录零调用、零断言。instrumented call count 显示它在 212 个测试中被调用 0 次，而其余 7 个指标有 1–23 次。7 个语义不同的变异体全绿，说明没有任何测试能发现 UR 的读法或窗口语义被改坏——这是 §5 测得的 12.5%–37.5% 数学不变量守护率的最尖锐一例。
- **证据**：报告 §1 code 段、§9 落地缺口表 UR 行（src ⚠️ / test ❌）；finding gap21 [W1-COVER-UR-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。
- **交叉核查**：**[同实体未合并]** 见 AC-10。

### AC-37 — _dead_expert_threshold 部分真守卫：参数化维度无守护

- **源 id**：`C-004` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/safeguards.py:34`（pin 态）
- **Requirement**：wayfinder Req 13 / skeleton req-18（1/(2·N_e) 闭式）
- **溯源 id**（`origin_ids`）：`mutate:3`
- **问题**：7 个测试跨两层杀掉规定变异体与 2 个深化变异体（MUT2 常量 0.03125、MUT5 严格不等号改 <=），协议记为 killed。但两项查表变异体 MUT3（N_e==16→1/32; N_e==64→1/128; else 0.0）与 MUT4（1.0/(2*round(sqrt(N_e))**2)）双双存活。MUT4 在两个采样点（N_e=16 与 64）数值精确，但 N_e=8 给 0.055556（spec 0.0625）、N_e=32 给 0.013889（spec 0.015625），直接驱动 should_resurrect 产生静默假阴性。实质是 1/(2·N_e) 的参数化依赖只被两条硬编码点断言守护。
- **证据**：_handoff_mutations.json mutate:3（7 个 killedBy）；报告 §5 表格第 3 行
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-38 — local_softmax 真守卫但单线且归属错位

- **源 id**：`C-008` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/gating.py:30`（pin 态）
- **Requirement**：skeleton req-9（只在非 -inf 项上取指数 + Σp_i=1）
- **溯源 id**（`origin_ids`）：`mutate:7`
- **问题**：两个均匀权重变异体都被杀，故真守卫。但 MUTANT-B（输出恒为 [0.5,0.5]、行和精确 1.0、requires_grad=True、梯度恒 0、autograd 完好）下 test_k_equals_two / test_neg_inf_sentinel_used / test_partition_of_unity / test_zero_grad_for_non_top_k / test_convex_combination_dtype_safe 全部通过，唯一失败是 test_forward_formula_strictness（属 Req 31）。即 Req 9 自己点名的两条条款被一个常数 0.5/0.5 完全满足；杀它的是另一个 Requirement 的数值检查，守卫归属错位且为单线。
- **证据**：_handoff_mutations.json mutate:7（killedBy=[test_gating.py::test_forward_formula_strictness]）；报告 §5 表格第 7 行
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-39 — STE 禁令 grep 作用域只覆盖 extraction.py 一个文件

- **源 id**：`C-016` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`tests/test_extraction.py:327`（pin 态）
- **Requirement**：skeleton req-15 L348
- **溯源 id**（`origin_ids`）：`rv:main68:source`、`rv:gap22:math`、`rv:gap22:source`
- **问题**：spec 声明的 grep 不变量作用域是整个 src/decompmoe/（全树不得出现 StraightThroughEstimator / straight_through），实现只扫 extraction.py 一个文件，其余 12 个模块无覆盖；实测把 STE 注入 gating.py 后 213 个测试全绿。spec 措辞与执行范围不一致。
- **证据**：_merged_verdicts main68（TEST-GUARD-07）与 gap22（W1-COVER-STE-02）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-40 — MC 测量层的采样数与种子常量值零断言，只引用符号名

- **源 id**：`C-020` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:98`（pin 态）
- **Requirement**：skeleton req-6 L98 / governance req-gov-1 obligation 7(b)
- **溯源 id**（`origin_ids`）：`rv:gap16:math`、`rv:gap16:source`
- **问题**：spec L98 硬性规定 Monte-Carlo 测量层的采样数 1_000_000 与随机种子 20260929 必须 fixed as module constants 以保证返回值确定，但两个数值在 tests/ 中零命中，测试只引用符号名 sphere.VORONOI_AREA_SEED / SAMPLES。若有人改掉任一常量，全部 MC 容差断言会静默换基准而无一失败；obligation 7(b) 要求 σ 从估计器自身结构推导，当前结构输入未被守护。
- **证据**：_merged_verdicts gap16（W2-MATH-03）
- **基线**：`touched-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-47 — equal_area_witness 测试用被测实现自身作为参考做校准

- **源 id**：`C-064` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`tests/test_sphere.py:419`（pin 态）
- **Requirement**：skeleton req-6 / governance req-gov-1 obligation 4
- **溯源 id**（`origin_ids`）：`D2-04`、`C-006`
- **问题**：test_voronoi_angle_equal_area_witness_equal_area_configurations 把参考值对到实现自身输出而非独立 oracle，因此与被测实现共享误差；7 个 _betainc_regularized killer 中有 4 个属此类（用被测的 _betainc_regularized 自己去算 ½·I），对任何常数缩放按构造不可见。
- **证据**：_handoff_delta.json D2-04；报告 §4 环 6 证据 C
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-48 — test_voronoi_angle_one_sided_gap 把单向性降格为方向检查

- **源 id**：`C-065` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`tests/test_sphere.py:490`（pin 态）
- **Requirement**：skeleton req-6（reflected branch）/ wayfinder req-11（commensurability）
- **溯源 id**（`origin_ids`）：`D2-07`
- **问题**：测试 docstring 自述把 one-sidedness『guarded here as a direction check rather than as [a bound]』，即只判方向不判幅度。而 Jensen 单向界当前被一个不存在的阈值 theta_conv(d_c) 当作前置条件门控，使得这个已经降格的守卫实际上一旦前置条件成立就能被满足——单向性在测试层没有任何幅度约束。
- **证据**：_handoff_delta.json D2-07；报告 §4 环 5
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D1-04（Jensen 前向界的前置条件用了不存在的角度阈值 `theta_conv`）由本条与 AC-04 / AC-29 共同承载，id 未进 `origin_ids`。

### AC-60 — 球面归一化的 eps 默认值无守卫，同名原语却已钉住

- **源 id**：`C-015` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`tests/test_sphere.py:703`（pin 态）
- **Requirement**：skeleton req-19 L438
- **溯源 id**（`origin_ids`）：`rv:main67:source`
- **问题**：spec req-19 明写『The default eps SHALL equal 1e-6』，但把 spherical_l2_normalize 的默认 eps 从 1e-6 改成 1e-4，213 个测试全部通过。同一仓里 extract_C 的同名 eps 默认值反而被钉住，说明是守卫不一致而非有意不设防。
- **证据**：_merged_verdicts main67（TEST-GUARD-06）
- **基线**：`touched-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-61 — 一批浮点闭式断言缺 actual= 内嵌值，含 5 个精确值

- **源 id**：`C-017` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`tests/test_schedule.py:176`（pin 态）
- **Requirement**：governance req-gov-1 obligation 5（L24）
- **溯源 id**（`origin_ids`）：`rv:main69:source`
- **问题**：违反 governance req-gov-1 obligation 5：一批『浮点闭式』断言没有在失败消息中内嵌实际值，其中包括 wayfinder req-33 Scenario 逐字点名的 5 个 phase_beta_max 精确值。测试已用 abs=1e-9 钉住这些值（见 C-007），缺 actual= 使失败输出无法自证偏差来源。
- **证据**：_merged_verdicts main69（TEST-GUARD-08）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-62 — req-gov-1 obligation 4 的 5 个 ppm / 残差数值全仓零对账

- **源 id**：`C-019` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/governance/spec.md:20`（pin 态）
- **Requirement**：governance req-gov-1 obligation 4
- **溯源 id**（`origin_ids`）：`rv:main27:source`、`rv:gap17:math`、`rv:gap17:source`
- **问题**：obligation 4 列出的 5 个具体数值（impl-internal 残差 1.16e-14、true 残差 4.15e-7、相对误差 6.63 ppm、θ 偏差 0.72 ppm / 0.0086 ppm）经 mpmath 50 位重算全部正确，但 tests/ 全目录无任何直接对账。这条 Requirement 本身就是『每个含具体数值的算式必须有直接对账』的定义者，其自身数值却无人守护。
- **证据**：_merged_verdicts main27（G-MATH-04）与 gap17（W2-MATH-04）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-77 — gamma_reset_for_phase4 定义域 (1,32) 无守卫

- **源 id**：`C-054` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/schedule.py:139`（pin 态）
- **Requirement**：wayfinder Req 26 L642 / Req 29 L687
- **溯源 id**（`origin_ids`）：`rv:gap7:math`、`rv:gap7:source`
- **问题**：gamma_reset_for_phase4 的定义域是 (1, 32)，但函数无任何守卫；β_p3 落在边界上就抛出语义误导的 math.log 域错误，而 β_p3 = 1.0 在 Phase 3 是可达的（Phase-1 全 5000 步固定 β = 1.0）。spec 把该闭式无条件表述为 γ 重置契约，未声明 β_p3 的有效域。
- **证据**：_merged_verdicts gap7（ADV-08）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-83 — req-11 参数量闭式的三个中间整数项无字面量守护

- **源 id**：`W05` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:251`（pin 态）
- **Requirement**：wayfinder req-11
- **溯源 id**（`origin_ids`）：`gap19`、`rv:gap19:math`、`rv:gap19:source`
- **问题**：req-11 的参数计数闭式中 P_emb = 32_768_000、P_attn/layer = 4_194_304、P_router = 131_584 三个整数项在 skeleton spec 中逐项列出，但 tests/ 只钉了 P_router/layer = 32_896 与两个总计。闭式的分解层完全无对账，MVPConfig 默认值漂移时三个中间项会静默改变而测试不红——这正是 CLAUDE.md §8 描述的 ticket/spec/默认配置三传染通道在测试层的对应缺口。
- **证据**：finding gap19 [W2-MATH-06]；报告 §9 落地矩阵「spec → test 塌陷」结论
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

### AC-91 — req-24 Scenario 的 γ/β 空间间隙中间量无测试守护

- **源 id**：`W19` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:609`（pin 态）
- **Requirement**：wayfinder req-24
- **溯源 id**（`origin_ids`）：`gap20`、`rv:gap20:math`、`rv:gap20:source`
- **问题**：req-24 Scenario 中的 γ-space 间隙 4.54e-5、β-space 残差 1.5899599e-6、斜率 0.0350220952386 等中间量无任何测试钉住。其中 β-space 残差是 spec 论证「必须用 γ-space 断言而非 β-space 断言」的唯一量化依据——这条设计决策的论据本身零守护，未来任何人改动 γ/β 映射都不会有测试变红。违反 CLAUDE.md §6 第 8 条。
- **证据**：finding gap20 [W2-MATH-07]
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。

---

## A-2 spec / 文档层的数学陈述与条款措辞缺陷（15 条）

缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。spec 是唯一真相源，这类条目只能经 OpenSpec change 修订，不能在代码层绕过。

### AC-04 — req-6 的凹性错误数值无测试钉住，紧邻测试反而把同类伪零点硬钉为真值

- **源 id**：`C-031` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：CRITICAL
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:98`（pin 态）
- **Requirement**：skeleton req-6 L98 / L116
- **溯源 id**（`origin_ids`）：`rv:gap14:math`、`rv:gap14:source`、`BASE-01`、`C-061`
- **问题**：spec L98 声明『G 在 d_c=16 时在 (82.8°, 90.0°) 上是凹的』是数学错误的（G''=0 在 (0,π) 内的唯一根恰为 90°，G 在整个 (0°,90°) 上严格凸），该错误数值 82.8/98.1/179.1 无任何测试钉住；而紧邻的 test_voronoi_angle_convexity_boundary 把同类伪零点 82.6036° 硬钉为真值。测试层的方向与 spec 层的错误一致，互相加固。
- **证据**：_merged_verdicts gap14（W2-MATH-01）与 BASE-01（_handoff_pin.json）
- **基线**：`touched-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D1-03（req-6 凸性三条断言两条为假）、D1-04（Jensen 前置条件用了不存在的 `theta_conv`）、D3-02（spec L98 凹性数值是伪影）三条的实体都在本条，但三个 id 均未进入本条 `origin_ids`。

### AC-05 — test_voronoi_angle_convexity_boundary 钉死求积伪影

- **源 id**：`C-061` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：CRITICAL
- **位置**：`tests/test_sphere.py:523`（pin 态）
- **Requirement**：skeleton req-6 L98 / CLAUDE.md §6 第 8 条
- **溯源 id**（`origin_ids`）：`BASE-02`、`D1-01`、`D2-01`、`C-031`、`C-032`、`C-061`、`C-006`、`rv:main18:source`、`rv:main48:math`
- **问题**：该测试在三组 (d_c, deg) 上以 abs=1e-3 钉 81.3148 / 82.6036 / 83.7313 作为 G 的凸性边界，并额外断言边界上方 1° 处 _cap_area_second_derivative < 0。三个数都是单面板 8 点 GL 求积的伪零点：真 G''=0 在 (0,π) 内的唯一根恰为 90°，在 d_c=16、θ=82.6036° 处真 G'' = +2.4568（凸），而 pin 实现中心差分给 +9.9920e-06。差 8.69 / 7.40 / 6.27 度，比容差大六个数量级，故不是容差问题。
- **证据**：_handoff_pin.json BASE-02；_handoff_delta.json D1-01 与 D2-01；报告 §4 环 6 证据 A + §3.0 CRITICAL
- **基线**：`touched-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D3-03（凸性边界测试钉死求积伪影）即本条，id 未进 `origin_ids`。

### AC-15 — sphere.py 凹凸性分区图错误，被中心差分测试钉死

- **源 id**：`C-032` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/sphere.py:260`（pin 态）
- **Requirement**：skeleton req-6 / governance req-gov-1 §5-§6
- **溯源 id**（`origin_ids`）：`rv:main48:impact`、`rv:main48:math`、`rv:main48:source`、`rv:gap14:math`、`rv:gap14:source`、`D3-04`、`D2-08`
- **问题**：voronoi_angle docstring 声明的 _cap_area 凹凸性分区图在数学上是错的：_cap_area 在整个 (0°,90°) 严格凸、在 (90°,180°) 严格凹，不存在 81.9°/82.8°/97.2° 任何拐点。tests/test_sphere.py::test_voronoi_angle_convexity_boundary 用一个被 GL-8 求积噪声支配的 h=1e-5 中心差分把这个假边界钉成了断言（还断言 83.6° 处 G''<0，而该处真值 +2.185）。src 文档与测试共同陈述了与 spec 真相源矛盾的数学事实。
- **证据**：_merged_verdicts main48（NUM-DRIFT-01）、gap14、delta D3-04、delta D2-08；报告 §4 环 6 证据 A
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D1-03（req-6 凸性三条断言两条为假）由本条与 AC-04 / AC-28 共同承载，id 未进 `origin_ids`。

### AC-16 — canonical_voronoi_angle 的精度免责声明挂在错误的界上

- **源 id**：`C-043` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/sphere.py:197`（pin 态）
- **Requirement**：skeleton req-6（abs=1e-6 契约）
- **溯源 id**（`origin_ids`）：`D3-05`
- **问题**：canonical_voronoi_angle 的 accuracy caveat 只声明了『spec 的 < 1e-6』这一侧，没有覆盖实际的偏差量级方向——真 G 与实现偏差在 π/2 邻域达到 1e-1 量级，免责声明挂在不被违约的一侧，使读者对总性（totality）缺口无感知。
- **证据**：_handoff_delta.json delta:D3 的 D3-05；报告 §4 环 3
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D1-05（`_cap_area` 在 π/2 的硬不连续）由本条承载，id 未进 `origin_ids`。

### AC-28 — 被推翻的先例：主控 COMMON 事实 #4 的口径需精确化

- **源 id**：`V-26` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:98`（pin 态）
- **Requirement**：skeleton req-6 / BASE-01
- **溯源 id**（`origin_ids`）：`rv:main48:math`、`rv:main18:source`、`rv:main18:math`
- **问题**：主控把「G 严格凸」作为 COMMON 事实交给下游，本轮五条 COMMON 事实无一被推翻，但 #4 的表述被要求精确化：`(0, π/2)` 上严格凸、`G''(π/2) = 0`、`(π/2, π)` 上严格凹、`π/2` 是光滑拐点而非分支端，且 `d_c = 2` 是 `G'' ≡ 0` 的仿射退化情形而 spec 从未提及。沿用未精确化的旧表述会把拐点当端点用，进一步污染下游推导。
- **证据**：报告 §11 第 15 条（COMMON 五条全部复算、无一被推翻，含 #4 的精确化）、§4 环 4（二分返回 90.0°，`G''(π/2) = -9.98e-51` 为 roundoff）；_handoff_pin.json BASE-01（d_c=8/16/32 的 G'' 扫描无负值点）
- **基线**：`touched-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D1-03 由本条与 AC-04 / AC-15 共同承载，id 未进 `origin_ids`。

### AC-42 — 不完全 Beta 积分 docstring 未披露 x→1 的误差跃变

- **源 id**：`C-034` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/sphere.py:73`（pin 态）
- **Requirement**：skeleton req-6 L116 / governance req-gov-1 obligation 4
- **溯源 id**（`origin_ids`）：`rv:main50:source`、`D3-06`、`C-034`
- **问题**：_betainc_regularized 的绝对误差在 x→1（θ→90°）时从 8.29e-7 爆到 7.61e-2（76% 相对误差），docstring 只披露了 MVP 点 8.29e-7 而未披露这一量级跃变。以单点最优值代表全域，正是 C-032 假边界的直接成因。
- **证据**：_merged_verdicts main50（NUM-DRIFT-03）；报告 §4 环 1
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-46 — spec 声称球面归一化输出 exact 等于 1，59% 不满足

- **源 id**：`C-060` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:455`（pin 态）
- **Requirement**：skeleton req-19 / governance req-gov-1 obligation 2
- **溯源 id**（`origin_ids`）：`rv:gap8:math`、`rv:gap8:source`
- **问题**：spec 声称 spherical_l2_normalize 的输出满足 pow(2).sum(-1) == 1.0 exactly，实测在 float64 下 59% 的随机批次都不满足（最坏偏差 6.66e-16）——这是无法满足的 exact 表述。spec 自身的 Scenario 与 tests/test_sphere.py 的守护形式（pytest.approx）不一致，测试用 approx 掩盖了 spec 的 exact 声明。
- **证据**：_merged_verdicts gap8（ADV-09）
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-52 — req-17 闭式漏算第 (3) 步 128 MACs

- **源 id**：`W02` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/wayfinder/spec.md:382`（pin 态）
- **Requirement**：wayfinder req-17 / decompmoe-skeleton req-7
- **溯源 id**（`origin_ids`）：`main42`、`gap24`、`rv:gap24:math`、`rv:gap24:source`
- **问题**：req-17 声称「完整 extract_C pipeline = 33_040 MACs = 66_080 FLOPs」，但该 Requirement 自己定义的四步管线第 (3) 步（cross-head mean with 1/H_kv factor）在每个 token 上做 H_kv·d_c = 128 MACs，从未被计入。独立重算的真值是 33_168 MACs = 66_336 FLOPs，spec 相对 projection-only 的增幅应为 +1.22% 而非 +0.83%，「full」一词因此是过度声称。同一闭式在 skeleton req-7 的 Scenario 中被复制为只枚举三项的形式，spec 与自身正文互斥。必须同时记录的是驳回：finding 声称这会让 req-19 的 0.3% allowance 结论反转并不成立——该 allowance 是对着 active-core 分母定义的，恢复第 (3) 步后仍在界内。该项的数值偏差在归档 change 中已以 latent risk HIGH 登记为 hand-off，且 2026-09-28 的 design Decision 3 明确选择了冻结字面量而非派生值，两者需一并处理。
- **证据**：报告 §6.2；finding main42 [W-MATH-01]、gap24 [W1-COVER-MAC-04]；归档 archive/2026-09-28-fix-a7-flops-attribution-and-stale-ref/design.md Decision 3
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-53 — req-11 的 W^O 排除清单与同段 4·d_model² 闭式互斥

- **源 id**：`W03` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/wayfinder/spec.md:251`（pin 态）
- **Requirement**：wayfinder req-11
- **溯源 id**（`origin_ids`）：`main17`
- **问题**：req-11 的假设 3 把 `W^O` 绑为注意力输出投影，假设 4 的排除清单又把 `W^O` 排除，而同段的 `4·d_model²` 项与闭式 452_329_984 都必须包含 `W^O`——三者在同一 Requirement 内不能同时为真。复算确认若真按清单排除，P_total 变成 448_135_680，与闭式相差 4_194_304 参数（0.93%）。实现与全部测试都站在闭式一侧，孤立的是排除句。同一句错误在 decompmoe-skeleton spec 中逐字复制。
- **证据**：报告 §1 wayfinder 段「Req 11」；§6.5 末条；finding main17 [FLOPs-PARAM-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-64 — voronoi_angle docstring 峰值位置与幅度均算错

- **源 id**：`C-033` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/sphere.py:276`（pin 态）
- **Requirement**：CLAUDE.md §6 第 8 条（写进代码的数学断言须可对账）
- **溯源 id**（`origin_ids`）：`rv:main57:source`、`rv:main49:source`
- **问题**：docstring 给出的『真实峰值 +31.5868°，位于 θ* = 38.9420°』两个数字都与它自己写出的解析式不符，实测为 31.586338° / 38.942441°。等价记录见 NUM-DRIFT-02：峰值位置 38.9420°→实为 38.9424°，幅度 +31.5868°→实为 +31.5863°。属以扫描近似值冒充闭式结果。
- **证据**：_merged_verdicts main57（CODE-FORM-02）与 main49（NUM-DRIFT-02）
- **基线**：`touched-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-82 — req-11 权重 tying 反事实的 prose 数值与同段闭式不符

- **源 id**：`W04` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:248`（pin 态）
- **Requirement**：wayfinder req-11
- **溯源 id**（`origin_ids`）：`main43`
- **问题**：req-11 讨论「不做权重 tying」的反事实时，prose 写总量「≈ 484 M」，而同段自己钉死的精确闭式给出的实际值是 485_097_984 ≈ 485.1 M，偏差 0.23%。同一段内一个 Requirement 同时持有精确闭式与错误的约数近似，两者不构成整数闭式意义上的对账，读者无法判断哪一个是权威值。
- **证据**：报告 §6.5「权重 tying 反事实 prose 数值错」条；finding main43 [W-MATH-02]
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-84 — θ_Voronoi > θ_{1/e} 成立条件只是散文非条款

- **源 id**：`W06` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:233`（pin 态）
- **Requirement**：wayfinder req-11
- **溯源 id**（`origin_ids`）：`gap13`
- **问题**：复算确认 θ_Voronoi > θ_{1/e} 只在 β > 1/(1−cos θ_V) ≈ 1.6310 时成立，而调度中有 9207/100000 步运行在该判据的反转区（Phase 1 全部 5000 步固定 β = 1.0，余量 −22.76°）。finding 断言 spec 完全没写条件是误报——同一 Requirement 正文 L245 就以 β = 16 为条件写了这条不等式，finding 只读了 L233 起的 Scenario。剩余的真实成分是：该条件在 spec 中以 MAY 级的散文形式存在而非 MUST 级条款，因此它不构成可被 lint/测试对账的契约。
- **证据**：报告 §6.5「几何自洽判据适用条件」条与 §2.2 NEVER_EXISTED 列表第 4 条；finding gap13 [ADV-14]（rv:gap13:math / rv:gap13:source）
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-85 — req-19 把 1:1 FLOPs 断言从两个条目过度外推到每个 MoE 条目

- **源 id**：`W08` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:435`（pin 态）
- **Requirement**：wayfinder req-19
- **溯源 id**（`origin_ids`）：`main19`
- **问题**：req-19 的 Scenario 把 1:1 断言从「DecompMoE vs Dense-4096」过度外推为「每个 MoE 条目」，但该 Requirement 自己枚举的 Qwen1.5-MoE-A2.7B（QLoRA）与 GMoE 条目不可能与 Dense 基线有相同的 per-token active FLOPs。措辞越界使 Scenario 描述的契约宽于其自身枚举的对象范围，读者会把它读成对外部参数化 baseline 的性能承诺。属措辞越界而非数值错误。
- **证据**：finding main19 [FLOPs-BASE-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-86 — req-19 两个 residency 数值无 pin 且算不出 4 KB

- **源 id**：`W09` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:398`（pin 态）
- **Requirement**：wayfinder req-19 / wayfinder req-18 / ticket A7-3
- **溯源 id**（`origin_ids`）：`main22`、`gap26`
- **问题**：req-19 声明的两个 residency 数值（W_proj ≈ 64 KB in BF16、activations ≈ 4 KB）虽可闭式算出，但 src 与 tests 中均无任何 pin；H_kv/d_k/d_c 静默漂移会让该 Requirement 的 L2 常驻承诺失效而无测试变红。复算发现字面列举的 z/ẑ/z̄/C 张量集合算不出 4 KB，而 H_kv·d_k·4 B = 4_096 B 恰为 4 KB——spec 声明的张量集合与声明的数值不匹配，属可消歧的措辞缺口。已在归档 change 登记为 hand-off 移交项 6。
- **证据**：报告 §6.5 与 §7「无 Decision 记录」第 5 条表；§9 落地缺口表 residency 行；finding main22 [LANDING-03]、gap26 [W1-COVER-RESIDENCY-06]
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

### AC-87 — req-20 六个 baseline 有 5 个零表示且无 deferral

- **源 id**：`W10` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:414`（pin 态）
- **Requirement**：wayfinder req-20 / ticket A8-1
- **溯源 id**（`origin_ids`）：`main23`、`rv:main23:source`
- **问题**：req-20 要求对 6 个 baseline 报告 1:1 active FLOPs，但 src 的 flops_per_token 只支持 MOE/DENSE 两种 arch，5 个 baseline 在 src 与 tests 中零表示。该 Requirement 也没有像 territory_seeding 那样的显式 deferral 标注，因此读者无法区分「有意不做」与「漏做」。按 CLAUDE.md §7 训练与评测属 out-of-scope，缺的是标注而非实现。
- **证据**：报告 §9 落地缺口表「6 个 baseline 的 1:1 FLOPs」行；finding main23 [LANDING-04]
- **基线**：`unchanged-since-pin`
- **归属理由**：缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。

---

## A-3 spec 与 src 实现之间的语义偏离（15 条）

实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。归属 change 层是因为处置方向取决于spec 侧的契约要不要保留，代码层的「直接对齐」可能是错的。

### AC-14 — 测试只跑 Phase 1–4，暴露不了 Phase 0 范数矛盾

- **源 id**：`C-027` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/safeguards.py`（pin 态 line=0，目录级/模块级定位，无有效行号）
- **Requirement**：wayfinder Req 23 / skeleton req-18（Phase 0 归一化责任）
- **溯源 id**（`origin_ids`）：`rv:gap6:math`、`rv:gap6:source`
- **问题**：两份 peer spec 对 Phase 0 的球面范数不变量互相矛盾：wayfinder Req 23 要求任何 Phase（含 0 K-Means）满足 max_i|‖c_i‖−1| < 1e-7，skeleton req-18 却把 Phase 0 的归一化责任划给调用方且 driver 为 no-op。现有测试只跑 Phase 1–4，该矛盾在测试层没有任何执行者。
- **证据**：_merged_verdicts gap6（ADV-07）
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-17 — CentroidDriver.step 的 mask=None 分支广播同一均值

- **源 id**：`C-049` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/extraction.py:127`（pin 态）
- **Requirement**：skeleton req-18（m_i MUST 是 per-expert masked mean）/ wayfinder Req 6 / Req 27
- **溯源 id**（`origin_ids`）：`rv:gap0:math`、`rv:gap0:source`
- **问题**：该分支使 16 个质心完全坍缩到同一点（territory collapse）：迭代后两两最大距离 1.7528 → 4.54e-01(step 100) → 3.26e-07(step 1000) → 2.52e-07(step 5999)，平均成对 cos → +1.000000；符合 spec 的 per-expert 对照组稳定在 1.75 / +0.067。原 finding 声称零测试覆盖是错的：test_phase_090_ema L33、test_phase_095_to_099_ema_coefficients L53、test_phase_transition_swaps_rule L85 以 atol=1e-5 精确钉住了这个退化闭式（它们靠省略参数进入该分支，agent 的 grep 找的是显式 None）。正确表述是：不是零守护，而是测试在守护一个 spec 不要求的退化行为——spec 签名里 mask 是必填位置参数，代码给了默认值，故修签名必须先动这三个测试。
- **证据**：_merged_verdicts gap0（ADV-01）；报告 §8 偏离表
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-32 — req-2 的 MUST 级标识符 territory_collapse 悬空

- **源 id**：`W01` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/specs/wayfinder/spec.md:24`（pin 态）
- **Requirement**：wayfinder req-2 (Formal Symbols And Code Naming)
- **溯源 id**（`origin_ids`）：`main20`、`main58`、`rv:main20:source`、`rv:main20:impact`、`rv:main58:source`
- **问题**：req-2 以 MUST 形式列出 7 个必须映射进 codebase 的代码标识符，其中 `territory_collapse` 在 src/ 与 tests/ 中均零命中，其余 6 项全部落地。它与同列表的 `territory_seeding` 处境不同——后者有专门的 deferred Requirement 承接，而本项既无实现、也无 deferral 标注，属 spec-only 悬空标识符，src + test 两层同时缺失。归档制品 2026-09-23-07 的 Open Question 正是在问这件事，至今无 Decision 闭环。
- **证据**：报告 §9 落地缺口表「territory_collapse 标识符」行；§1 wayfinder 段；finding main20 [LANDING-01]、main58 [CODE-FORM-03]
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-35 — req-23 Phase 0 范数 MUST 与 req-18 冲突

- **源 id**：`W18` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/specs/wayfinder/spec.md:575`（pin 态）
- **Requirement**：wayfinder req-23 vs decompmoe-skeleton req-18
- **溯源 id**（`origin_ids`）：`gap6`
- **问题**：wayfinder Req 23 的 WHEN 子句说球面范数不变量对「any Phase（含 0 K-Means）」成立，skeleton req-18 却把 Phase 0 的归一化责任划给调用方且 driver 为 no-op。实测同一非单位输入上 P0 与 P4 输出不同（8.83 vs 5.96e-08），证实两份 peer 真相源对同一 MUST 给出互斥约束。现有测试只跑 Phase 1–4，无法暴露该矛盾，因此它是一颗只在 Phase 0 被真正调用时才会引爆的雷。
- **证据**：报告 §6.5「Req 23 与 req-18 对 Phase 0 的球面范数不变量互相矛盾」条；finding gap6 [ADV-07]（rv:gap6:math / rv:gap6:source 判 MAJOR）
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-41 — UR 的 W=100 窗口与 R_H/S_load 滑窗语义未实现

- **源 id**：`C-026` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/metrics.py:73`（pin 态）
- **Requirement**：wayfinder req-20 L452-454（W = 100 量化主张）
- **溯源 id**（`origin_ids`）：`rv:gap3:math`、`rv:gap3:source`
- **问题**：UR 窗口语义完全未实现：任意长度历史都 reduce，200 步历史给 0.1875（spec 正确值 0.125），把 (B, N_e) 批量误当时间轴给 0.25（spec 0.0625）。R_H 与 S_load 声明的 sliding window 同样零实现。UR 另是唯一既无 spec 闭式 Scenario、又无任何数值测试的指标。
- **证据**：_merged_verdicts gap3（ADV-04）；报告 §9 逐项落地缺口表 UR 行
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。
- **交叉核查**：**[同实体未合并]** 见 AC-10。

### AC-43 — resurrect_expert 返回裸 ε 而非克隆后扰动，破坏球面归一不变量

- **源 id**：`C-050` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/safeguards.py:166`（pin 态）
- **Requirement**：wayfinder Req 13 L315 / Req 28 / Req 32
- **溯源 id**（`origin_ids`）：`rv:gap1:math`、`rv:gap1:source`、`gap1`
- **问题**：Dead Expert Splitting Resurrection 返回的是裸 ε ~ N(0, 0.05²I)（长度约 0.2），不是 spec 要求的『克隆 j* 后扰动』的 c_{j*}+ε；被复活的专家落在近似均匀随机方向上，与供体正交。math 镜实测 E[cos(c_perturbed, c_j*)] = 0（sd 0.25）vs spec 语义 0.981697 / E[angle] 10.7957°，8.34× 角差；返回向量长度还短 5.0787×，赋给 c_i 会先破坏 S^{d_c−1} 不变量。
- **证据**：_merged_verdicts gap1（ADV-02）；报告 §8 偏离表首行
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-44 — loss.py 硬编码 100K 边界与 total_steps API 静默错位

- **源 id**：`C-053` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/loss.py:31`（pin 态）
- **Requirement**：governance req-gov-3 obligation 1（dormant-bug 判据）/ skeleton req-13
- **溯源 id**（`origin_ids`）：`rv:gap5:math`、`rv:gap5:source`
- **问题**：λ(t) 与 β^eff 的调度在 loss.py / beta_effective 中硬编码 100K 边界，而 phase_id / phase_boundaries / phase_beta_max 接受 total_steps 参数，非 100K 运行时两者静默错位。非 100K 不是 spec 强制运行时（skeleton req-13 只在 WHEN total_steps == 100_000 下钉边界），故为 dormant。两条 violates 引用（§6 item 8、req-gov-3 obligation 1）均误引。
- **证据**：_merged_verdicts gap5（ADV-06）；报告 §8 偏离表第 4 行
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-45 — req-2 映射表中 territory_collapse 在 src 零出现

- **源 id**：`C-058` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/contracts.py:77`（pin 态）
- **Requirement**：wayfinder req-2（Formal Symbols And Code Naming，MUST 映射表 7 项）
- **溯源 id**（`origin_ids`）：`rv:main58:source`、`rv:main20:impact`、`rv:main20:math`、`rv:main20:source`
- **问题**：7 项 MUST 级代码标识符映射中，territory_collapse 在 src/ 中零出现（其余 6 项均落地），且不像同列表的 territory_seeding 那样有专门的 deferred Requirement 标注。与之对应，tests/ 中也零命中——属 spec-only 悬空标识符，缺 src + test 两层。
- **证据**：_merged_verdicts main58（CODE-FORM-03）与 main20（LANDING-01）；报告 §9 逐项落地缺口表
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-56 — req-15/16 Layer 2 的 WB 与阈值零实现

- **源 id**：`W31` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MEDIUM
- **位置**：`src/decompmoe/schedule.py:186`（pin 态）
- **Requirement**：wayfinder req-15 / req-16 Layer 2 / ticket A6b-2
- **溯源 id**（`origin_ids`）：`main21`、`gap25`、`rv:main21:impact`、`rv:main21:math`、`rv:main21:source`、`rv:gap25:math`、`rv:gap25:source`
- **问题**：spec req-15 Layer 2 声明的两个具体数值（WB = 0.0476 与 > 2.0 严重聚类阈值）在 src/ 与 tests/ 中零出现，advisory_signals 是纯透传 dict。两条 lens 的分歧在于：impact 镜认为本项数学来源未推导，贸然补 approx 断言会把未推导的数字钉成真值，因此降为 PARTIALLY_REAL；math 镜认为按 §7 表「有 Decision 记录」档（archive 2026-09-25 design.md:112 明写「本 change 不处理」+ archive 2026-09-28 移交项 5）已合规，仅需保持现状。两条都一致：spec 正文目前无任何 deferral 标注，是比完全无标注更诚实的缺口的反面。
- **证据**：报告 §7「有 Decision 记录」表第 4 行、§9 落地缺口表 WB 行；finding main21 [LANDING-02]、gap25 [W1-COVER-WB-05]（rv:gap25:math=UNVERIFIABLE）
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-73 — clip_global_grad_norm_ 的 else 分支不可达且会抛错

- **源 id**：`C-046` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/safeguards.py:57`（pin 态）
- **Requirement**：CLAUDE.md §2 Simplicity First（不为不可能场景写错误处理）
- **溯源 id**（`origin_ids`）：`rv:main59:source`
- **问题**：else pre_norm 分支不可达：clip_grad_norm_ 恒返回 0 维张量，故 pre_norm 恒为标量 0 且永不为 None；若该分支被触达，会因 float(多元素张量) 直接抛错。可从 torch 源码证明不可达，不只是观察。
- **证据**：_merged_verdicts main59（CODE-FORM-04）；报告 §8 偏离表
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-74 — _betainc_regularized 求积循环内两处守卫数学上不可达

- **源 id**：`C-047` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/sphere.py:117`（pin 态）
- **Requirement**：CLAUDE.md §2 Simplicity First
- **溯源 id**（`origin_ids`）：`rv:main60:source`
- **问题**：求积循环内的 if t <= 0.0: continue 与 math.log(t) if t > 0 else -math.inf 两处守卫在数学上不可达（GL 节点严格落在 (0,1) 开区间内）。判 PARTIALLY_REAL：分支确不可达，但 _betainc_regularized 本身在 x→1 处的真实缺陷（C-034）比这两处死守卫重要得多。
- **证据**：_merged_verdicts main60（CODE-FORM-05）；报告 §8 偏离表
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-75 — extract_C 的投影参数名与 skeleton req-7 声明签名漂移

- **源 id**：`C-048` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/extraction.py:36`（pin 态）
- **Requirement**：decompmoe-skeleton req-7 声明签名 proj_W_K, proj_W_V, proj_b
- **溯源 id**（`origin_ids`）：`rv:main61:source`
- **问题**：extract_C 的前三个投影参数名是 W_K, W_V, b，与 decompmoe-skeleton req-7 显式声明的签名 proj_W_K, proj_W_V, proj_b 漂移。按 spec 写法以关键字调用会 TypeError，即 spec 声明的签名不可执行。这是 8 个 spec 明文声明签名中至少 3 个不一致之一。
- **证据**：_merged_verdicts main61（CODE-FORM-06）；报告 §8 偏离表 + 签名层漂移统计
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-76 — resurrect_expert docstring 的实参描述与实现不符

- **源 id**：`C-051` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/safeguards.py:208`（pin 态）
- **Requirement**：wayfinder Req 32 L735（same-call-stack 契约）
- **溯源 id**（`origin_ids`）：`rv:gap12:math`、`rv:gap12:source`
- **问题**：resurrect_expert docstring 声称 c_perturbed 来自 resurrection_perturb_distribution(torch.empty(0), j_star, ...)，实际代码传的是 f_per_expert（= β_per_expert.detach()）。文档与实现不一致，而 Req 32 的 same-call-stack 契约正是以该 docstring 作为人类可读依据。
- **证据**：_merged_verdicts gap12（ADV-13）
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-78 — __all__ 只列 3 个 dunder 名字，spec 要求列出全部公开符号

- **源 id**：`C-056` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/__init__.py:21`（pin 态）
- **Requirement**：decompmoe-skeleton req-1 L12
- **溯源 id**（`origin_ids`）：`rv:gap10:math`、`rv:gap10:source`
- **问题**：decompmoe.__all__ 只列 3 个 dunder 名字，而 spec req-1 要求它列出『every public symbol introduced by this skeleton』（实测 76 个）；且 docstring 声称的『populated lazily by submodules』并未发生。
- **证据**：_merged_verdicts gap10（ADV-11）
- **基线**：`unchanged-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

### AC-79 — voronoi_angle 的 probe 强制建在 CPU 且多出 ValueError

- **源 id**：`C-059` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/sphere.py:288`（pin 态）
- **Requirement**：change 2026-09-30-fix-voronoi-angle-review-findings 授权编辑面
- **溯源 id**（`origin_ids`）：`D3-07`
- **问题**：torch.randn(..., generator=generator) 无 device= 参数，probe 矩阵是 1e6 × d_c 的 float32（d_c=16 时 64 MB）；同时新增的 d_c < 2 的 ValueError 也不在授权 change 枚举的 4 项 sphere.py 编辑里，更不在 spec 里。当前无生产调用者所以影响为零，属 change 授权外变更。
- **证据**：_handoff_delta.json delta:D3 的 D3-07；报告 §8 偏离表末行
- **基线**：`touched-since-pin`
- **归属理由**：实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。

---

## A-4 交叉引用与行号指针失效（15 条）

spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。真相源不可被指针反向定义，所以修的是引用关系与反链约束，不是被指向的那一行本身。

### AC-34 — req-36 整段以行号指针钉真相源而多数已漂移

- **源 id**：`W12` ｜ **主桶**：opsx-change ｜ **裁决**：MOVED ｜ **严重性**：MAJOR
- **位置**：`openspec/specs/wayfinder/spec.md:847`（pin 态）
- **Requirement**：wayfinder req-36 (Source Pointer Contract)
- **溯源 id**（`origin_ids`）：`main72`
- **问题**：req-36 整段以 25 处行号指针声明「真相源钉死契约」，但其中的 wayfinder L413 实际是空行——MCI 行在 L460、Source 在 L463、两个 MCI Scenario 在 L497/L501，req-20 实际跨 L441-L511。该 Requirement 自称是全库唯一的行号引用规范载体，自己却整段失效。漂移源单一：33f7cc9 给 wayfinder +1 / skeleton +13 / governance +8 行却没有重绑任何一处指针，偏移量可机械预测。仓库内已有一个被采纳过的结构性手法（archive 2026-09-28 Decision 2：Req 17 的引用已采用 anchor 形式），但没有推广到其余指针族。
- **证据**：报告 §6.4「spec 行号反链的系统性失效」与 §1 wayfinder 段；finding main72 [CROSS-SPEC-LINEPTR-01]（rv:main72:source 判 MOVED，rv:main72:impact / rv:main72:math 判 STILL_REAL）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-54 — 三处「Req 10」反链指向已被改写的 Requirement

- **源 id**：`W16` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/wayfinder/spec.md:183`（pin 态）
- **Requirement**：wayfinder req-2 / req-21 / decompmoe-skeleton req-2
- **溯源 id**（`origin_ids`）：`main71`
- **问题**：wayfinder spec 三处「Req 10」反链指向错位：req-10 现在是 Territory Seeding Deferred Contract，但三处引用的内容（Mixtral 记账保证、前向公式）实际在 req-21 No Shared Expert。属「Req N 形式引用指向已改写的 Requirement」类，与行号指针族是两种不同的引用失效模式——即使未来全部指针都采用 anchor 形式，这三处仍会错。skeleton L184 存在同款第三处。
- **证据**：报告 §2.2 E 类（ticket/map 漂移）与 §6.4 同族；finding main71 [CROSS-SPEC-BACKREF-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-59 — skeleton L242 引 wayfinder L249 实为 L315

- **源 id**：`W42` ｜ **主桶**：opsx-change ｜ **裁决**：MOVED ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:242`（pin 态）
- **Requirement**：wayfinder req-13 / req-32 (resurrection Source 行)
- **溯源 id**（`origin_ids`）：`main75`
- **问题**：skeleton L255（finding 报 242）引「wayfinder L249」定位一个 Source 行，但 L249 是 GQA 参数计数假设，真正的规范正文在 wayfinder L315。该指针与 W15（req-2 引 L211 实际应为 L249）、W26（resurrection 供体克隆语义）指向同一片 wayfinder 区域，三条缺陷的纠正目标互不相同，容易互相覆盖。
- **证据**：报告 §6.4 失效样例第 5 条；finding main75 [CROSS-SPEC-LINEPTR-04]（rv:main75:source 判 MOVED）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-63 — arctan(pi/sqrt(d_c)) 不变式的守护交接指向空处

- **源 id**：`C-023` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:367`（pin 态）
- **Requirement**：skeleton req-15 → req-16 的守护交接声明
- **溯源 id**（`origin_ids`）：`rv:gap15:math`、`rv:gap15:source`、`rv:main17:math`
- **问题**：spec L367 声称被移出 grep 层级的 arctan(pi/sqrt(d_c)) 不变式『已在 Centroid Driver Semantic Invariants (req-16) 中由对应命名 test 场景重新陈述并强制执行』，但 req-16 正文完全不含该不变式，tests/ 与 src/ 中 arctan / 38.146 / 3.58 全部零命中。这是一个指向空处的悬空守护：spec 的可验声明没有对账执行者。
- **证据**：_merged_verdicts gap15（W2-MATH-02）；报告 §9 逐项落地缺口表 arctan 行
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-65 — config.py 把 spec 权威行标为 L245，实为 API 句

- **源 id**：`C-035` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/config.py:95`（pin 态）
- **Requirement**：wayfinder req-11 / decompmoe-skeleton req-11
- **溯源 id**（`origin_ids`）：`rv:main51:source`
- **问题**：config.py 的参数闭式把 spec 权威行标为 req-11 L245，而实际 L245 是 canonical_voronoi_angle 的 API 句，闭式 totals 在 L253。src 文档的 spec 引用不可解析到正确权威行。
- **证据**：_merged_verdicts main51（NUM-DRIFT-04）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-66 — schedule.py 把三条 β^eff 公式的 spec 行号指错

- **源 id**：`C-036` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/schedule.py:147`（pin 态）
- **Requirement**：wayfinder Req 24 L587-589（真实位置）
- **溯源 id**（`origin_ids`）：`rv:main52:source`
- **问题**：schedule.py 与 test_schedule.py 把 per-phase β^eff 三条规范公式的 spec 行号标为 wayfinder L491-507 / line 495/496/497，实际落在 Req 20 的 SP / D_chord / MCI 三个无关 Scenario 上；正确位置是 Req 24 的 L587-589。src 注释的 spec 引用指向了不承载该条款的 Requirement。
- **证据**：_merged_verdicts main52（NUM-DRIFT-05）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-67 — test_safeguards.py 10 处 per L249 全部指错

- **源 id**：`C-037` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`tests/test_safeguards.py:772`（pin 态）
- **Requirement**：wayfinder L314（真实位置）
- **溯源 id**（`origin_ids`）：`rv:main53:source`
- **问题**：test_safeguards.py 中 10 处『per wayfinder L249』全部指错：L249 是 req-11 的 GQA 参数计数假设 2，五条 safeguard 的规范正文在 L314。测试断言的 spec 引用不可解析到承载该条款的 Requirement。
- **证据**：_merged_verdicts main53（NUM-DRIFT-06）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-68 — metrics.py 把 CG 指标的 spec 行号标错

- **源 id**：`C-038` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/metrics.py:166`（pin 态）
- **Requirement**：wayfinder Req 20 L461（真实位置）
- **溯源 id**（`origin_ids`）：`rv:main54:source`
- **问题**：metrics.py 与 test_metrics.py 把 CG 指标的 spec 行号标为 Req 20 L394，实测 L394 是 req-18 的 anchor 行；CG 表格行在 L461。src/测试文档的 spec 引用指向错误位置。
- **证据**：_merged_verdicts main54（NUM-DRIFT-07）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-69 — test_extraction.py 把 eps 默认值规范行号标错

- **源 id**：`C-039` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`tests/test_extraction.py:356`（pin 态）
- **Requirement**：decompmoe-skeleton L126（真实位置）
- **溯源 id**（`origin_ids`）：`rv:main55:source`
- **问题**：test_extraction.py 把 extract_C 的 eps=1e-6 默认值规范行号标为『spec req-7 L100』，实测 wayfinder L100 是 req-6 的空行；承载该签名的规范在 decompmoe-skeleton L126。
- **证据**：_merged_verdicts main55（NUM-DRIFT-08）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-70 — req-12 引用的 safeguards.py 行号漂移 52 行

- **源 id**：`C-040` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:240`（pin 态）
- **Requirement**：skeleton req-12（src/decompmoe/safeguards.py:211/:222）
- **溯源 id**（`origin_ids`）：`rv:main39:source`
- **问题**：Req 12 引用的 src/decompmoe/safeguards.py:211 与 :222 两处行号均已漂移 52 行；且未被任何 pending change 覆盖（pending B10-B12 delta 原样搬运了同样的过期行号）。属 spec 指向不存在的代码位置，同类缺陷已登记为 B13/B14/B16。
- **证据**：_merged_verdicts main39（S-MATH-04）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-71 — req-20 引用 beta.py:50 的行号与逐字引文皆错

- **源 id**：`C-041` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:458`（pin 态）
- **Requirement**：skeleton req-20（src/decompmoe/beta.py:50）
- **溯源 id**（`origin_ids`）：`rv:main40:source`
- **问题**：Req 20 引用 src/decompmoe/beta.py:50 并逐字引用源码 MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0——行号与源码字面量两处皆错（数值 15.5 本身正确）。spec 用逐字引文作为契约，但引文与源码不符。
- **证据**：_merged_verdicts main40（S-MATH-05）
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-72 — voronoi_angle docstring 把读者指向一个不存在的测试名

- **源 id**：`C-045` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/sphere.py:234`（pin 态）
- **Requirement**：skeleton req-6
- **溯源 id**（`origin_ids`）：`D2-06`
- **问题**：docstring 指示读者去看 test_voronoi_angle_equal_area_witness_crosspolytope 了解某项保证，但 tests/ 中实际的测试名是 test_voronoi_angle_equal_area_witness_equal_area_configurations。src 文档给出的可追溯入口不可解析。
- **证据**：_handoff_delta.json delta:D2 的 D2-06；报告 §5 表格第 4 行 killedBy 列表
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-88 — wayfinder spec 内部行号交叉引用系统性失效（聚合记录）

- **源 id**：`W13` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:847`（pin 态）
- **Requirement**：wayfinder req-2 / req-34 / req-36
- **溯源 id**（`origin_ids`）：`main44`、`main72`、`main74`、`main77`
- **问题**：本条是 wayfinder spec 内部行号引用族失效的聚合记录：req-36 引用的 L434-505 / L450 / L453 / L454 / L456 / L416 / L413、req-34 的 L831→L251、req-2 的 L24「req-11 L211」全部指向当前文件的错误行，其中 req-2 那条指向的内容与该主张完全无关（落在 req-10 Territory Seeding 块内）。判定为 MINOR 而非 MAJOR 是因为每一处单独看都是可定位的引用错误，实体主张本身未变；但作为一族，它们共同构成 §6.4 所说的「7 条独立 finding 指向同一个根因」。仓库已有 commit a036a15 校正过同类指针（B14: L122→L130、L115→L123），说明该失败模式已被识别过一次却未根治。
- **证据**：报告 §6.4 失效样例清单；finding main44 [W-MATH-03]
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-89 — req-34 的 live example 指针指向参数计数假设

- **源 id**：`W14` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:831`（pin 态）
- **Requirement**：wayfinder req-34
- **溯源 id**（`origin_ids`）：`main74`
- **问题**：req-34 把 A6a-2 historical-annotation 的「canonical live example」定位在 wayfinder L251，但该 Source 行实际在 L316，L251 是参数计数假设 4。这是指针目标语义完全不匹配的一类——不是 off-by-one，而是指到了另一个 Requirement 的另一类内容。已用 git show f033d2e3 证明该指针在 2026-09-15 撰写时是对的，属纯粹的撰写后漂移。
- **证据**：报告 §6.4 失效样例第 3 条；finding main74 [CROSS-SPEC-LINEPTR-03]
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

### AC-90 — req-2 引 req-11 L211 落在 req-10 块内

- **源 id**：`W15` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:24`（pin 态）
- **Requirement**：wayfinder req-2 → req-11
- **溯源 id**（`origin_ids`）：`main77`
- **问题**：req-2 引「req-11 L211」定位 GQA-degenerates 陈述，但 L211 落在 req-10 Territory Seeding 块内，该陈述实际在 wayfinder L249。指针落进相邻 Requirement 的正文块，使 req-2 的一条 MUST 条款失去可追溯依据。同时 §6.5 已记录 req-11 L249 本身还带着 W^O 排除句的互斥问题，两条缺陷叠加在同一目标行上。
- **证据**：报告 §6.4 失效样例第 5 条；finding main77 [CROSS-SPEC-LINEPTR-06]
- **基线**：`unchanged-since-pin`
- **归属理由**：spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。

---

## A-5 OpenSpec 制品格式、门禁与归档流程（18 条）

落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。这层的问题不体现为某个 Requirement 的数学对错，而体现为「真相源能不能被可靠地写下去和查出来」。

### AC-19 — archive 工具静默吞掉后继 Requirement 的 anchor

- **源 id**：`O-01` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/changes/archive/2026-09-29-fix-voronoi-angle-measurement-layer-semantics/tasks.md:64`（pin 态）
- **Requirement**：archive/2026-09-29-fix-voronoi-angle-measurement-layer-semantics
- **溯源 id**（`origin_ids`）：`delta:D4-01`
- **问题**：OpenSpec 1.13.2 的 archive 会把每一条 MODIFIED Requirement 之后那行 <a id="req-N"></a> 一并吞掉，因为它的 requirement block 解析器一直累积到下一个 Requirement 标题或二级标题为止，而仓库风格把 anchor 放在两个Requirement 标题之间。pin 态实测复现：anchor 覆盖从 36/23/4 掉到 35/22/3，丢的正是 wayfinder req-12、decompmoe-skeleton req-7、governance req-gov-2。这是第三次同型事故，delta 内容本身落地完全正确，损坏仅限 anchor，且事故记录里归档流程走的是 CLI 而非仓库自带的 delta 合并脚本。
- **证据**：_handoff_delta.json key=delta:D4 findings[D4-01]；报告 §3.0 D4-01；报告 §1 opsx 段
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-20 — CLAUDE.md §3 门禁清单对 anchor 事故全部返回 exit 0

- **源 id**：`O-02` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`CLAUDE.md:45`（pin 态）
- **Requirement**：CLAUDE.md §3 /opsx:archive 前置条件
- **溯源 id**（`origin_ids`）：`delta:D4-01`
- **问题**：§3 规定归档前置条件是两个 Python lint 加 validate --specs。这三项在 anchor 已被吞掉的 spec 树上实测全部 exit 0，也就是说门禁清单在结构上覆盖不到它声称要防的那类损坏。锚点 100% 覆盖在 §6 被写成硬约束，但归档这一步没有任何可执行形式去核对它。
- **证据**：_handoff_delta.json key=delta:D4 findings[D4-01] evidence 段（四道门全过）；报告 §1 opsx 段 (b)；报告 §10 Batch D-2
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-21 — 仓库无 CI 配置，scripts/ 即全部门禁面

- **源 id**：`O-04` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`scripts/`（pin 态 line=0，目录级/模块级定位，无有效行号）
- **Requirement**：N/A
- **溯源 id**（`origin_ids`）：`delta:D4-05`
- **问题**：pin 态树里没有 .github/ 也没有 .gitlab-ci.yml，除 openspec/changes/ 外唯一的 yml 是 openspec/config.yaml。两个 lint 与全部测试只在人工触发的会话里跑，没有任何提交或合并钩子强制它们。这解释了为什么上面两条门禁缺口可以连续跨多个会话存在而无人被拦下。
- **证据**：_handoff_delta.json key=delta:D4 findings[D4-05] evidence（ls -a 无 .github/）；报告 §10 Batch D-2
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-22 — range 内两个 100% 完成的 change 是非法 OpenSpec 制品

- **源 id**：`O-06` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/changes/2026-09-29-fix-b13-b16-src-docstring-and-line-ref-drift/.openspec.yaml:1`（pin 态）
- **Requirement**：2026-09-29-fix-b13-b16-src-docstring-and-line-ref-drift / 2026-09-29-fix-b15-test-loss-actual-embedding
- **溯源 id**（`origin_ids`）：`delta:D4-02`
- **问题**：这两个 change 既没有 specs/ delta 也没有 skip_specs 标记，openspec validate --strict 对它们 exit 1，报 'Change must have at least one delta'。二者 tasks 已 100% 勾选、代码已随 commit 落库，却因为制品不合法而永远无法走完归档。讽刺的是它们各自的 C.5 task 已明确判定「确认不需要 specs/ 目录」，即意图清楚、只是没落到 .openspec.yaml 上。作为对照，68 个已归档 change 全部满足两个前置条件之一，所以这是最新一批 change 创建实践的回归，不是历史遗留。
- **证据**：_handoff_delta.json key=delta:D4 findings[D4-02]；报告 §3.0 D4-02
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-23 — b10-b11-b12 change 全部完成但目录未跟踪、delta 未 sync

- **源 id**：`O-10` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/changes/2026-09-29-fix-b10-b11-b12-test-guard-fidelity/tasks.md:1`（pin 态）
- **Requirement**：B10 split
- **溯源 id**（`origin_ids`）：`rv:main3:impact`、`rv:main3:source`
- **问题**：该 change 的 37 个 task 全部勾选、openspec list 报 Complete，但整个目录 6 个文件在 pin 态全部未被 git 跟踪，两份 delta 也没有 sync 进主 spec——完成态只存在于工作树，一次清理即可全部丢失。主 spec 此刻仍保留被 delta 明确 supersede 的旧文本（versine 4dp 字面量那一条仍写 abs=1e-4），所以真相源与测试在这一点上暂时互相矛盾。tasks.md 自己声明的 RECONCILIATION: PASS 只证明 delta 与主 spec 基线可对账，不证明 delta 已 apply。
- **证据**：f_main/003.json（W-01）；_handoff_verdicts_all.json key=rv:main3:source（NEVER_EXISTED）/ rv:main3:impact（STILL_REAL, MAJOR）；报告 §2.2 第 1 类、§3 环 4
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。
- **交叉核查**：**[口径冲突]** 报告 §2.2 L56 判 main3 为 NEVER_EXISTED、§3.1 L318 判 STILL_REAL / MAJOR、§10 Batch D-2 L1641 明写「不入批」；本条采纳的是 §3.1 口径，三处裁定前该条的去留待定。

### AC-24 — Source 反链 lint 的必需要子串只硬编码到目录前缀

- **源 id**：`O-17` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`scripts/lint_no_source_field_drift.py:104`（pin 态）
- **Requirement**：CLAUDE.md §3 Source 反链 / wayfinder req-34
- **溯源 id**（`origin_ids`）：`rv:main25:source`、`rv:main25:math`、`rv:main25:impact`
- **问题**：§3 要求 wayfinder/ 与 decompmoe-skeleton/ 的 Requirement 必须含带 ticket 文件名的字面反链，但 lint 的必需要子串只到 wayfinder/tickets/ 这个目录前缀为止，三项结构性检查全部只对该前缀做子串判断。实测裸目录形式与不带 .md 后缀的 ticket id 形式都能三项全过，与规范形式不可区分——反链 lineage 不可追溯的情况可以合法通过门禁。读 req-34 可见责任面更宽：它正文写的是带文件名的 MUST，紧接着自己的执行细则第 1 条却降级为只要求含目录前缀，属 spec 内部自相矛盾。
- **证据**：f_main/025.json（G-MATH-02）；_handoff_verdicts_all.json key=rv:main25:source / :math / :impact；报告 §3 环 6、§10 Batch D-2
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-25 — 门禁运行期间工作树被并发写入，快照不可复现

- **源 id**：`O-19` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`tests/test_loss.py:1`（pin 态）
- **Requirement**：CLAUDE.md §3 archive 前置条件（门禁须针对确定快照）
- **溯源 id**（`origin_ids`）：`rv:main0:source`、`rv:main0:impact`、`rv:main0:math`
- **问题**：同一轮门禁的两次 git status 采样之间，tests/test_loss.py 从干净变为已修改（另三个测试文件在同一批次更早被改），两次 pytest 都返回全绿，但第二次的 pass 结果对应的文件内容已不是第一次采样时的那份。结果是门禁结论无法复现，而 §3 的归档前置条件恰恰要求 lint gate 针对确定的工作树快照判定 exit=0。并发的 bulk checkpoint commit 随后把这批在途写入落库，兑现了这个风险。
- **证据**：f_main/000.json（GATE-01）；_handoff_verdicts_all.json key=rv:main0:source（PARTIALLY_REAL）/ :impact（STILL_REAL, MAJOR）；报告 §3 环 4、§10 Batch D-2
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-31 — UNVERIFIABLE 与 severity 的自指缺陷：治理规则的零守卫

- **源 id**：`V-40` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/specs/governance/spec.md:13`（pin 态）
- **Requirement**：req-gov-1 obligation 1 / G-MATH-01 / main24
- **溯源 id**（`origin_ids`）：`rv:main24:math`、`rv:main24:source`
- **问题**：req-gov-1 用 `pytest.approx` 的有效容差公式作为「整数闭式必须用 bare `==`」的规范理由，但实测（项目自带 pytest 9.1.1）表明该理由的两个默认值写反（实为 rel 默认 1e-6、abs 默认 1e-12）、结论方向也反了（显式给 `abs` 时 `ApproxScalar.tolerance` 短路返回该 `abs`，容差精确为 0，与 bare `==` 等价）。自指问题是：该 Requirement §4 的四个含具体数值的算式全部为假，且全部无任何测试守护——治理「所有数值守卫」的规则本身零守卫，错误理由已 verbatim 传播到 CLAUDE.md:41、3 个测试文件注释与 6 份归档 delta。
- **证据**：报告 §6.1 整节（实测 `pytest.approx(452_329_984, abs=0.0).tolerance = 0.0`）；对照 §11 第 3 条「19 条 UNVERIFIABLE 是弃权不是证伪」——两者是同一治理体系的两处自指漏洞
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-36 — fix-review-findings change 的悬空 delta 声明

- **源 id**：`W33` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`openspec/changes/fix-review-findings-voronoi-precision-and-lineage/proposal.md:66`（pin 态）
- **Requirement**：change fix-review-findings-voronoi-precision-and-lineage
- **溯源 id**（`origin_ids`）：`main4`、`rv:main4:source`、`rv:main4:impact`
- **问题**：该 change 声称 3 个 Modified Capability（wayfinder / decompmoe-skeleton / governance）且「通过本 change 目录的 specs/<capability>/spec.md delta 应用」，但目录下根本不存在 specs/ 目录——悬空 delta 声明。其 spec 内容虽已直接落进主 spec，制品自述与其自身结构矛盾。openspec list 报该 change 处于待 archive 状态，错误自述会被原样固化进 archive。wayfinder 层的影响是：主 spec 的 wayfinder 改动失去可追溯的 delta 来源。注：git status 显示该 change 的 proposal.md / tasks.md 在当前工作树处于已删除未提交状态。
- **证据**：报告 §10 引用该 change 作为未归档项；finding main4 [W-02]（rv:main4:math 判 MAJOR）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-49 — §3 门禁清单不含 openspec validate <change> --strict

- **源 id**：`O-05` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`CLAUDE.md:45`（pin 态）
- **Requirement**：CLAUDE.md §3 门禁清单
- **溯源 id**（`origin_ids`）：`delta:D4-05`、`delta:D4-02`
- **问题**：§3 列出的归档前置条件里没有对 change 制品本身做严格校验的步骤。后果是下面 O-06 那类工具判为非法的 change 可以一路走到 100% 完成而没有任何一道门拦它；同一个门禁清单也解释不了为什么两次 anchor 事故全程绿灯。
- **证据**：_handoff_delta.json key=delta:D4 findings[D4-02]；报告 §1 opsx 段 (c)；报告 §10 Batch D-2
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-57 — change 的 task 勾选声称已完成但对应编辑从未落库

- **源 id**：`W40` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/changes/fix-review-findings-voronoi-precision-and-lineage/tasks.md:19`（pin 态）
- **Requirement**：change fix-review-findings-voronoi-precision-and-lineage / ticket A4-1
- **溯源 id**（`origin_ids`）：`D4-03`、`delta:D4-03`、`PROC-03`
- **问题**：Task 1.4.3 被勾选为 [x]，声称 tickets/A4-1.md:59 已从 L122 校正到 L130，但该编辑从未进入任何 commit。这是「change claims completion it never performed」——与 gap21（UR 的 tasks.md 勾选点名了一个 git 历史中不存在的 test 与 SHA）同族。两者都危险于「无记录」：无记录会被发现，假记录会被读成已交付。wayfinder 层的影响是 ticket A4-1 的 β_0 行号指针校正至今没做。
- **证据**：报告 §7「无 Decision 记录」第 8 条（gap21 / main63 同族）；finding delta:D4-03
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-58 — a036a15 只落了 B14 的 src 半边，spec 半边滞留

- **源 id**：`W41` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:496`（pin 态）
- **Requirement**：wayfinder req-7 (β_0 闭式 L130 / Sigmoid 闭式 L123)
- **溯源 id**（`origin_ids`）：`main76`、`D4-04`、`delta:D4-04`、`PROC-03`
- **问题**：commit a036a15 落了 B14 的 src 半边（config.py L122 → L130），spec 半边则坐在未归档的 fix-config-docstring-beta-line-drift change 里，尚未 sync 进主 spec。skeleton L496/L498/L521 引「wayfinder req-7 L122 / L115」——L122 是空行、L115 是 req-6 的 territory_seeding Scenario，而正确目标是 wayfinder L130（β_0 闭式）与 L123（Sigmoid 闭式）。这是本轮唯一一条被部分修好的指针族：src 侧已对、spec 侧未对，因此当前状态比 pin 态更不一致。
- **证据**：报告 §6.4 失效样例第 6 条；finding main76 [CROSS-SPEC-LINEPTR-05]、delta:D4-04
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 main41（skeleton req-21 三处过期 wayfinder 行号）即本条，id 未进 `origin_ids`。

### AC-80 — 仓库无任何 anchor 覆盖检查的门禁脚本

- **源 id**：`O-03` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`scripts/lint_no_dead_defensive.py:1`（pin 态）
- **Requirement**：CLAUDE.md §6 spec anchor 全覆盖硬约束
- **溯源 id**（`origin_ids`）：`delta:D4-05`
- **问题**：scripts/ 下两个 lint 都不检查 anchor，唯一的 anchor 逻辑在 delta 合并脚本里（它是应用器不是检查器）。事故记录里点名的检测器是一个从未被提交的临时脚本，git log 对它零命中。anchor 覆盖今天确实是 100%，但这条硬约束没有任何可执行形态，所以三次事故都只能靠人手发现、人手修复。
- **证据**：_handoff_delta.json key=delta:D4 findings[D4-05]；报告 §10 Batch D-2 门禁有效性
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-81 — Source 行匹配的行首锚定可被缩进或引用前缀绕过

- **源 id**：`O-18` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`scripts/lint_no_source_field_drift.py:75`（pin 态）
- **Requirement**：CLAUDE.md §3 Source 反链 / governance req-gov-1
- **溯源 id**（`origin_ids`）：`rv:main26:source`
- **问题**：lint 用行首锚定的正则识别 Source 行，凡该行带前导空白或 blockquote 前缀就整条跳过，三项结构性检查一项都不执行。实测同一段违规文本顶格写会被报 violation，加两个空格或加 > 前缀则报 0 violation。当前 live spec 树里 4 个 Source 行都是顶格，所以今天没有实际漏报，属覆盖面加固缺口。
- **证据**：f_main/026.json（G-MATH-03）；_handoff_verdicts_all.json key=rv:main26:source（STILL_REAL）；报告 §10 Batch D-2
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-92 — wayfinder 两个 anchor 被正文内联重复声明

- **源 id**：`W20` ｜ **主桶**：opsx-change ｜ **裁决**：MOVED ｜ **严重性**：MINOR
- **位置**：`openspec/specs/wayfinder/spec.md:429`（pin 态）
- **Requirement**：wayfinder req-17 / wayfinder req-20
- **溯源 id**（`origin_ids`）：`main70`
- **问题**：wayfinder spec 中 req-17 与 req-20 两个 anchor 被正文内联重复声明，decompmoe-skeleton 另有 2 处 req-22 变体，产生重复 HTML id。anchor 覆盖率本身 100% 合规，不违反 CLAUDE.md §6「spec anchor 不全」的判定标准——记录它是因为按 anchor grep 时会命中两处，而行号指针族（见 W12–W15）正是在向 anchor 引用迁移，重复 id 会在迁移后成为新的歧义源。定性为可接受的引用提及而非缺失 anchor。
- **证据**：finding main70 [CROSS-SPEC-ANCHOR-01]（rv:main70:source 判 MOVED）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-100 — fix-review-findings change 目录名无日期前缀

- **源 id**：`W34` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/changes/fix-review-findings-voronoi-precision-and-lineage/proposal.md:1`（pin 态）
- **Requirement**：change fix-review-findings-voronoi-precision-and-lineage
- **溯源 id**（`origin_ids`）：`main10`、`rv:main10:source`
- **问题**：该 change 目录名无 YYYY-MM-DD- 前缀，违反本仓 67 个归档目录中 64 个采用的命名惯例，并导致 openspec list 按名排序时它被排到最末、与另外 4 个日期前缀 change 的时间序脱节。proposal.md L5 记录 reviewer session 日期为 2026-09-27，说明日期信息存在只是没进目录名。属非阻断的惯例偏离。
- **证据**：finding main10 [W-08]（rv:main10:source 判 PARTIALLY_REAL）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-101 — followup change 的 task 勾选框账目漂移

- **源 id**：`W35` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/changes/2026-09-26-followup-spec-wording-bugs-after-precision-disclosure/tasks.md:33`（pin 态）
- **Requirement**：change 2026-09-26-followup-spec-wording-bugs-after-precision-disclosure
- **溯源 id**（`origin_ids`）：`main7`、`rv:main7:source`
- **问题**：该 change 有 13 个未勾选 task（openspec list 报 3/16），但这 13 项全部是「跑验证 / 提交」类动作，实质已由 commit 125d626 满足，属勾选框未回填的账目漂移。change 同时在工作树留下 2 个空的 specs/<capability>/ 目录，与其自身 proposal.md L53-57 的 skip_specs 声明矛盾。wayfinder 层的风险是：这条 change 承载的正是 spec 措辞类修正，账目漂移会让它被误判为未完成而长期滞留。
- **证据**：finding main7 [W-05]（rv:main7:source 判 PARTIALLY_REAL）；报告 §2.2 NEVER_EXISTED 第 3 条的关联背景
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

### AC-102 — b13-b16 change 24/24 完成且已落库但仍未 archive

- **源 id**：`W38` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`openspec/changes/2026-09-29-fix-b13-b16-src-docstring-and-line-ref-drift/tasks.md:1`（pin 态）
- **Requirement**：change 2026-09-29-fix-b13-b16-src-docstring-and-line-ref-drift
- **溯源 id**（`origin_ids`）：`main6`、`rv:main6:source`
- **问题**：该 change 24/24 task 全勾选、已随 commit f0b3aa2 落库、且正确声明不产生 spec delta，但仍处于未归档状态。属 OpenSpec 流程积压而非缺陷——但它正是 W12–W15 行号指针族修复的 src 侧载体（B13/B16 修 src docstring 与行号引用漂移），持续未归档会让「已修 src、未修 spec」的半边状态长期看起来像是完整交付。
- **证据**：finding main6 [W-04]（rv:main6:source 判 STILL_REAL）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。

---

## A-6 裁决口径、镜像分歧与先例争议（7 条）

落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。这些不进代码，但必须与结论一起搬运，否则下游会重犯同一类误判。它们被放在本清单是因为它们改变的是 change 的输入（哪些 finding 可信），而不是因为要改代码。

### AC-06 — 裁决时点漂移：e50cc02 已切断环4→环6，环1/环2 未修

- **源 id**：`V-34` ｜ **主桶**：opsx-change ｜ **裁决**：MOVED ｜ **严重性**：CRITICAL
- **位置**：`src/decompmoe/sphere.py:137`（pin 态）
- **Requirement**：skeleton req-6 / test_voronoi_angle_precondition_is_area_below_half
- **溯源 id**（`origin_ids`）：`rv:main48:math`、`rv:main18:source`
- **问题**：裁决基线是 pin 6593a06，但 HEAD 188b9fb 已多出 9 个 commit。报告在 HEAD 上复测：skeleton req-6 现在写「G is STRICTLY CONVEX on the whole of (0,π/2) … so G'' has NO interior zero」并附闭式，凸性边界测试已被 `test_voronoi_angle_precondition_is_area_below_half` 取代并把三个退役值转为反向回归钉——这是正确处置；但 `_betainc_regularized` 仍是单个 8 点 GL 面板零细分，`_cap_area` 的 π/2 跳变与 pin 逐位相同。结论是「不能因为凸性已修好就认为整条链已闭合」。本条的复测时点因此是 HEAD 而非 pin，其自身结论也不外推到 pin 态。
- **证据**：报告 §4 环 8（HEAD 上实测跳变 5.239884e-2 / 7.870852e-2 / 1.158112e-1，与 pin 逐位相同）；§10 Batch A「不在本批（已被 post-pin e50cc02 处理）」（测试文件行 519-525 落在 pin→HEAD 漂移区间内）
- **基线**：`touched-since-pin`
- **归属理由**：落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。
- **交叉核查**：**[已净化]** 原 problem 末句为祈使句（「所有 verdict 的时点必须随 pin 标注。」），check-contamination 判为 borderline 污染，此处已改写为纯时点陈述。

### AC-26 — main45：镜像分歧后合并为 STILL_REAL 的先例

- **源 id**：`V-15` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`tests/test_loss.py:166`（pin 态）
- **Requirement**：LIFECYCLE-01 / main45 / governance req-gov-1 obligation 5
- **溯源 id**（`origin_ids`）：`rv:main45:source`、`rv:main45:math`、`rv:main45:impact`
- **问题**：同一条 finding 的三个镜给出互斥结论：source 镜判 FIXED_BY_COMMIT（b272787 的 26 行编辑在最后一次采样后 3 分 05 秒被提交并在 pin 中存在，blob 哈希与 b272787:tests/test_loss.py 逐字节相同），impact 镜判 STILL_REAL（同一批并发写入后来以 e50cc02「checkpoint parallel session's in-flight work」落库，顺手把 b272787 的修复又回退掉，pin 态 `actual=` 计数为 0）。合并规则是判 STILL_REAL，理由是危害已经兑现——即「曾经修好过」不能抵消「现在又坏了」。这是本轮唯一被完整记录的镜像分歧合并先例。
- **证据**：报告 §2.2 第 2 条（逐字记录两镜分歧与合并理由）；rv:main45:source（blob 6ddbdef == b272787:tests/test_loss.py）、rv:main45:impact（「HEAD-at-that-moment was byte-identical to the pre-fix blob 8f50659」，引 governance/spec.md:24 obligation 5）、rv:main45:math（「INVERTED ON EVERY CHECKABLE POINT」但 fixingCommit 字段填 315065e）
- **基线**：`touched-since-pin`
- **归属理由**：落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。

### AC-27 — MOVED 的漂移源单一：33f7cc9 造成 +1/+13/+8

- **源 id**：`V-18` ｜ **主桶**：opsx-change ｜ **裁决**：MOVED ｜ **严重性**：MAJOR
- **位置**：`openspec/specs/decompmoe-skeleton/spec.md:122`（pin 态）
- **Requirement**：CROSS-SPEC-LINEPTR-01 / main72
- **溯源 id**（`origin_ids`）：`rv:main72:source`、`rv:main72:math`
- **问题**：本轮全部行号漂移的成因是单一 commit 33f7cc9：它给 skeleton 插入 13 行（锚点 L122 之后）、governance 净增 8 行、wayfinder 净增 1 行（锚点 L284），却没有重绑任何一处指针。因此偏移量可机械预测。凡引用这两份文件行号的 Requirement 与代码注释现在成族失效——这是「MOVED 可批量重绑」而非「逐条重定位」的结构性理由。
- **证据**：报告 §2.2 第 3 条、§6.4 第 1 条（7 条独立 finding 同一根因）；rv:main72:source（`git diff -U0 7bf77af 6593a06` 的 @@ 块：wayfinder @@ -283,0 +284 @@，skeleton +13，governance +8）、rv:main72:math
- **基线**：`touched-since-pin`
- **归属理由**：落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。
- **交叉核查**：**[基线存疑]** 本条 `baseline_status` 记 `touched-since-pin`，但 `openspec/specs/decompmoe-skeleton/spec.md:122` 不落在该文件任何 drift 区间内（该文件区间为 [98,98] [132,132] [255,255] [270,271] [326,329] [340,340] [499,499] [501,501] [524,524]）；机械查表应为 `unchanged-since-pin`。以查表结果为准。

### AC-29 — 诚实的边界：D3 未能证明 Jensen 单向界本身

- **源 id**：`V-27` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MAJOR
- **位置**：`_final_report_full.md:1367`（pin 态）
- **Requirement**：skeleton req-6 Jensen 前置条件 / D1-04 / D2-07
- **溯源 id**（`origin_ids`）：`rv:main18:math`、`rv:main48:math`
- **问题**：D3 明确记录其支撑线证明在 `μ=0.5, d_c=3` 处失败，因此只反驳 spec 给出的理由、不声称定理本身错误。报告采信「正确前置条件是面积条件」这一条（`G⁻¹` 在 `(0, ½)` 上凹 + 等面积 `A_i = 1/N_e < ½`），但明确不声称已独立证明该界对任意 `A_i < ½` 的 cell 组成立。本条的结论边界因此是：被证伪的是 spec 给出的理由陈述，不是 Jensen 单向界本身——两者是不同命题。
- **证据**：报告 §4 环 5 末段（「诚实边界」）、§11 第 4 条；D1-04 / D2-07 提供的 700+ 配置经验证据（N_e∈{2,3,4,8,16} × d_c∈{2,3,16,32}，唯二表观反例是 -4.0e-12 与 -2.1e-17 的二分噪声）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。
- **交叉核查**：**[溯源缺口]** 报告 §3 的 D1-04 由本条与 AC-04 / AC-48 共同承载，id 未进 `origin_ids`。

### AC-30 — gap0：结论成立但 finding 自身证据不可复用

- **源 id**：`V-28` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`src/decompmoe/schedule.py`（pin 态 line=0，目录级/模块级定位，无有效行号）
- **Requirement**：CentroidDriver.step(mask=None) / gap0
- **溯源 id**（`origin_ids`）：`rv:main20:math`
- **问题**：gap0 的 finding 自陈六行数值在其声明的设置下都无法复现；math 镜重算得到更严重的坍缩（step ~1000 完成而非 5000，Phase-1 结束时的坍缩比报告值严重约 850×），并推翻了 finding 的 α 序与 frozen-vs-fresh 节奏叙述。缺陷本身仍判成立，但支撑它的数值证据整体作废，需要用可复现代码重新立项。这是本轮唯一被点名的「结论保留、证据废弃」条目。
- **证据**：报告 §11 第 5 条；§8 表第 2 行（math 镜重算：质心最大距离 1.7528 → 4.54e-01 → 3.26e-07 → 2.52e-07，平均成对 cos → +1.000000）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。
- **交叉核查**：**[分桶存疑 + 溯源存疑]** 报告 §11 第 5 条是「结论保留、证据废弃」声明，check-completeness 判其应落 archive-only；另本条 `origin_ids` 记 `rv:main20:math`，而其内容是 gap0，真实键为 `rv:gap0:math` / `rv:gap0:source`（见 AC-17）。

### AC-50 — main42 的「结论反转」被驳回，定级由 MAJOR 降为 MEDIUM

- **源 id**：`V-29` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/wayfinder/spec.md:383`（pin 态）
- **Requirement**：wayfinder req-17 / skeleton req-7 / W-MATH-01 / main42
- **溯源 id**（`origin_ids`）：`rv:main18:source`、`rv:main17:source`
- **问题**：finding 声称 extract_C 漏算第 (3) 步 128 MACs 会让 req-19 的「0.3% allowance」结论反转。该推论被 impact 镜与 source 镜一致驳回：该 allowance 在 wayfinder L428 是对着 active-core 分母 33_554_432 定义的，恢复第 (3) 步后 66_336/33_554_432 = 0.1977%，与原值 0.1968% 一样在界内，finding 的 0.436% 用的是另一个分母。CLAUDE.md 明确禁止用「结论反转」这类别名关闭数学语义选择，因此这次驳回是硬约束而非可选裁量。
- **证据**：报告 §6.2 末段（「必须同时记录的驳回」）、§11 第 6 条（「若修复时按 finding 原文执行会得出错误的预算结论」）；真值 32_896+128+128+16 = 33_168 MACs = 66_336 FLOPs
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。
- **交叉核查**：**[分桶存疑 + 溯源存疑]** 报告 §11 第 6 条是「main42 的结论反转被明确驳回」，check-completeness 判其应落 archive-only；main42 的可执行部分已由 AC-52（W02）承载。本条 `origin_ids` 记 `rv:main18:source` / `rv:main17:source`，不含 `rv:main42:*`，指向与标题不符。

### AC-51 — main21/main22 的 violates 归因被三镜一致驳回

- **源 id**：`V-30` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MEDIUM
- **位置**：`tests/test_config.py:69`（pin 态）
- **Requirement**：CLAUDE.md §6 第 8 条 / main21 / main22 / gap25
- **溯源 id**（`origin_ids`）：`rv:grv:gap25:math`、`rv:main22:math`
- **问题**：两条 finding 都以「违反 CLAUDE.md §6 第 8 条」立论，复验认定归因错误：CLAUDE.md 规范的是断言形式而非隐式契约；`WB` 在仓库里根本没有闭式，`pytest.approx(0.0476)` 只能是常量对自身的同义反复；main22 的中心断言被 `test_config.py:69` 的 `router_per_layer == 32_896` bare `==` 直接推翻。残留缺陷在 spec 措辞层，不构成 CLAUDE.md 违规。
- **证据**：报告 §11 第 7 条、§8 表第 4 行（「两条 `violates` 引用都误引」）；rv:grv:gap25:math（`grep -rn 0.0476 src tests` 仅 tests/test_schedule.py:127 的一处 docstring，`src/` 0 命中）
- **基线**：`unchanged-since-pin`
- **归属理由**：落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。
- **交叉核查**：**[分桶存疑]** 报告 §11 第 7 条是「main21/main22 的 violates 归因被三镜一致驳回」，check-completeness 判其应落 archive-only。

---

## A-7 wayfinder advisory 层（map.md / tickets）漂移（8 条）

按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。故仍走 change（ticket 端标注 + spec 端对齐），而不走直接改代码。

### AC-55 — req-36 逐字引用 ticket A8-2 与 ticket 实际不符

- **源 id**：`W17` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MEDIUM
- **位置**：`openspec/specs/wayfinder/spec.md:879`（pin 态）
- **Requirement**：wayfinder req-36 / ticket A8-2
- **溯源 id**（`origin_ids`）：`main79`
- **问题**：req-36 逐字引用 ticket A8-2 的 annotation 为「spec req-20 L413」（5 处），ticket 实际写的是「spec req-20 L453」（2 处），而两者的真值都是 L460。spec 作为真相源却逐字误引其 lineage 制品，且 spec 与 ticket 两侧各自带错值。这条比单纯的行号漂移更严重：逐字引用意味着该字符串会被当作权威契约文本复制，grep 审计会命中一个不存在的原文。
- **证据**：报告 §6.4 失效样例第 8 条；finding main79 [CROSS-SPEC-TICKETQUOTE-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

### AC-93 — map.md 两条 A5-3 narrative 仍写旧 θ_Voronoi 值

- **源 id**：`W22` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`wayfinder/map.md:54`（pin 态）
- **Requirement**：wayfinder req-11 / ticket A5-3 / ticket A1-1
- **溯源 id**（`origin_ids`）：`main28`、`§7-no-decision-5`
- **问题**：map.md 的 A5-3 两条 narrative 仍写 θ_Voronoi 25.75°（N_e=64）与 ≈52°（N_e=16），与 spec req-11 的 58.47° / 67.24° 冲突。关键的不一致在于：同一批修复已在 ticket A5-3 L63 与 A1-1 L98 加上 (historical, …) 标注，map.md 端漏标。CLAUDE.md §8 的三步修复协议 (a) 只写了 ticket 端义务，map 侧没有对应条款，导致「同一漂移在同一批次里被修了一半」。
- **证据**：报告 §7「无 Decision 记录」第 5 条；finding main28 [DRIFT-MAP-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

### AC-94 — map.md 的 4 阶段生命周期措辞漏改且仍带已删除的 δ_g

- **源 id**：`W23` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`wayfinder/map.md:49`（pin 态）
- **Requirement**：ticket A3-2 / map.md 生命周期叙述
- **溯源 id**（`origin_ids`）：`main29`、`main33`、`§7-no-decision-4`
- **问题**：map.md 仍写「c_i 4 阶段生命周期」，而 ticket A3-2 的同一措辞已被 change 2026-09-22-fix-ticket-a5-2-cascading-correction 修为 5 阶段——该 change 修了 A3-2 + A5-2 两个 ticket 却漏掉 map.md 的同款措辞，属同一 change 内的漏改。map.md 同一行还带着「δ_g 死专家保护」，而 δ_g 在 openspec/ 内零落点。
- **证据**：报告 §7「无 Decision 记录」第 4 条；finding main29 [DRIFT-MAP-02]
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

### AC-95 — map.md 的三处计数全部落后于仓库实况

- **源 id**：`W24` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`wayfinder/map.md:71`（pin 态）
- **Requirement**：map.md 导航计数
- **溯源 id**（`origin_ids`）：`main30`、`§7-no-decision-6`
- **问题**：map.md 的三处计数全部落后：写 20 tickets（实 23）/ 21 锚点 21 Requirements（实 36/36）/ 34 Scenarios / 10 arena。anchor 覆盖本身 100% 合规，drift 仅在 map.md 的叙述性计数。它是 wayfinder 层的导航入口，读者据它判断「还有多少没做」，因此计数失真会直接影响后续审计的完备性判断——上一轮就发生过把「3 个未归档 change」当成前提而实为 5 个（见 main5）的情况。
- **证据**：报告 §7「无 Decision 记录」第 6 条；finding main30 [DRIFT-MAP-03]
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

### AC-96 — ticket A3-2 的 δ_g 门控被替换且无 Decision

- **源 id**：`W25` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`wayfinder/tickets/A3-2.md:45`（pin 态）
- **Requirement**：ticket A3-2 → wayfinder req-6 / req-22
- **溯源 id**（`origin_ids`）：`main33`、`§7-no-decision-1`
- **问题**：A3-2 的 δ_g 死专家门控与 g_i(C_t) 加权的 m_i 形式在 openspec/ 内零命中（grep -rn "δ_g" openspec/ = 0），spec req-6 L91 / req-22 L554 改用硬指示符 n_i = Σ_t I[r_{t,i} = max_j r_{t,j}]。ticket 端无 (historical, …) 标注，openspec 无任何 Decision 记录这次替换。这是「ticket 语义被无声替换」最干净的一例——不是数值漂移，是公式形状漂移，因此 CLAUDE.md §8 的三步协议按 (a) ticket 标注 / (b) 默认值同步 / (c) 测试迁移去套用时，(b)(c) 两步无处落地。
- **证据**：报告 §7「无 Decision 记录」第 1 条；finding main33 [DRIFT-A3-2-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

### AC-97 — ticket A6a-2 供体克隆语义无落点且无 Decision

- **源 id**：`W26` ｜ **主桶**：opsx-change ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`wayfinder/tickets/A6a-2.md:67`（pin 态）
- **Requirement**：ticket A6a-2 → wayfinder req-13 / req-28 / req-32
- **溯源 id**（`origin_ids`）：`main31`
- **问题**：A6a-2 声明的 resurrection 供体克隆语义 c_i ← Normalize(c_{j*} + ε)（继承最忙专家质心再微扰）在 openspec 内无任何 API 落点，而 spec req-13 的「clones j*」措辞被自家 req-28/32 的 canonical API 与已落地代码证否，且无 Decision 记录该删除。它同时是 CLAUDE.md §8 三传染通道中「reader-ticket-not-spec 复制」那一路的源头：任何照 ticket 实现的人会实现出一个 spec 明确不要求的归一化包装。
- **证据**：报告 §7「无 Decision 记录」第 2 条、§8 resurrection 行；finding main31 [DRIFT-A6A2-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

### AC-98 — ticket A6a-2 的专家权重克隆步在 openspec 内零落点

- **源 id**：`W27` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`wayfinder/tickets/A6a-2.md:70`（pin 态）
- **Requirement**：ticket A6a-2 → wayfinder req-13 / req-32
- **溯源 id**（`origin_ids`）：`main32`、`§7-no-decision-2`
- **问题**：A6a-2 resurrection 的第 4 步「专家权重克隆 W_i ← W_{j*} + N(0, 10^-4 I)」在整个 openspec/ 内零命中，spec 也从未记录该步被有意删除。ticket 端无 (historical, …) 标注，违反 governance req-gov-4 clause 4(a) 与 CLAUDE.md §8 三步协议的 (a) 步。复验者把定级降到 NONE 并部分驳回：req-32 的单事件 wrapper 契约在范围上已覆盖该步的删除，剩余成分只是标注缺失。
- **证据**：报告 §7「无 Decision 记录」第 2 条、§9 落地缺口表「专家权重克隆步」行；finding main32 [DRIFT-A6A2-02]（rv:main32:source 判 PARTIALLY_REAL / NONE）
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

### AC-99 — ticket A5-3 的 β_0 ≈ 1.0 标注只做了一半

- **源 id**：`W28` ｜ **主桶**：opsx-change ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`wayfinder/tickets/A5-3.md:42`（pin 态）
- **Requirement**：ticket A5-3 / ticket A4-1 → wayfinder req-7
- **溯源 id**（`origin_ids`）：`main34`、`§7-no-decision-7`
- **问题**：A5-3 三处 β_0 ≈ 1.0（L42 / L81 / L108）未加 (historical, …) 标注，而同值的 A4-1 L59 已加。同一漂移的 ticket 端标注只做了一半——正是 CLAUDE.md §8 描述的三传染通道形式：一个 ticket 加了标注，另一个没加，读者按 A5-3 读会拿到已被 spec req-7 闭式（β_0 = 1.035060）取代的旧值。
- **证据**：报告 §7「无 Decision 记录」第 7 条；finding main34 [DRIFT-A5-3-01]
- **基线**：`unchanged-since-pin`
- **归属理由**：按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，stale 值可沿三条通道传染到 `src/` 与 tests。

---

## A-8 需用户裁决（user-decision 桶）（6 条）

问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。任何自动处置都等于替用户做决定，故本清单只登记问题，不推进。

### UD-01 — main 与 dev 无共同祖先，dev → main --no-ff 当前不可执行

- **源 id**：`O-24` ｜ **主桶**：user-decision ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`CLAUDE.md:51`（pin 态）
- **Requirement**：CLAUDE.md §4 分支架构 / main 行
- **溯源 id**（`origin_ids`）：`rv:main11:source`、`rv:main11:impact`
- **问题**：main 的 root 是一个只含 2 个文件的 Initial commit，与 dev 无任何共同祖先，因此规范定义的「dev → main 存档」通道在当前拓扑下根本跑不通（需要规范未授权的 unrelated-histories 开关）。「dev 上未进 main 的提交数」实为 dev 的全部历史（174/174），这条指标因此失去意义。项目记忆记录用户此前已选择「仅 push dev」而非自动修复，属已登记的推迟项。
- **证据**：f_main/011.json（W1-GIT-01）；_handoff_verdicts_all.json key=rv:main11:source（STILL_REAL, MAJOR）/ :impact；报告 §10 Batch D-2 git 卫生
- **基线**：`unchanged-since-pin`
- **归属理由**：问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。

### UD-02 — release 分支与任何 tag 都不存在

- **源 id**：`O-25` ｜ **主桶**：user-decision ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MAJOR
- **位置**：`CLAUDE.md:52`（pin 态）
- **Requirement**：CLAUDE.md §4 分支架构 / release 行
- **溯源 id**（`origin_ids`）：`rv:main12:source`、`rv:main12:impact`
- **问题**：release 分支在本地与远端均不存在，仓库 tag 数为零，正式出埠口从未建立。这意味着「release 永远是 git tree 最前端」这条语义目前没有任何仓库状态与之对应，而 §4 的合并顺序约束与禁止清单都建立在该分支存在的前提上。
- **证据**：f_main/012.json（W1-GIT-02）；_handoff_verdicts_all.json key=rv:main12:source（PARTIALLY_REAL）/ :impact（STILL_REAL）；报告 §10 Batch D-2 git 卫生
- **基线**：`unchanged-since-pin`
- **归属理由**：问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。

### UD-03 — run d53 的 pin agent hand-back 触发了不可逆本地销毁告警

- **源 id**：`P05` ｜ **主桶**：user-decision ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`workflows/wf_fd517ac0-d53.json`（pin 态 line=0，目录级/模块级定位，无有效行号）
- **Requirement**：N/A
- **溯源 id**（`origin_ids`）：`rv:main45:source`、`rv:main45:impact`
- **问题**：run d53 的 journal log 里，pin agent 与 rv:main45:source / rv:main45:impact 三条 hand-back 都被 hook 判为 SECURITY WARNING [Irreversible Local Destruction]，理由是它们的 hand-back 指向父 workflow 去执行 git checkout -- tests/test_loss.py 与 git checkout -- src/decompmoe/config.py（会丢弃未提交改动）。这三条 agent 的输出因此带了一层『未经用户授权不得执行』的封条，其结论能否直接采纳成为悬而未决的问题。
- **证据**：workflows/wf_fd517ac0-d53.json logs 第 1 / 3 / 4 条（pin:baseline+delta-map、rv:main45:source、rv:main45:impact）
- **基线**：`unchanged-since-pin`
- **归属理由**：问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。

### UD-04 — CLAUDE.md 对 ticket 同时声明非约束与必须维护

- **源 id**：`W44` ｜ **主桶**：user-decision ｜ **裁决**：STILL_REAL ｜ **严重性**：MAJOR
- **位置**：`CLAUDE.md:51`（pin 态）
- **Requirement**：CLAUDE.md §2 / §8 / governance req-gov-4
- **溯源 id**（`origin_ids`）：`main28`、`main29`、`main30`、`main31`、`main33`、`main34`
- **问题**：CLAUDE.md §2 的真相源优先级把 wayfinder/map.md + 23 tickets 定为「参考性、非约束性」第 4 档，§8 的 2026-08-21 裁决同向；但 §8 的三步修复协议 (a) 又要求 ticket 端必须维护 `(historical, …)` 标注，并按 governance req-gov-4 把它形式化为硬义务。也就是说 ticket 同时被声明为「非约束」与「必须被维护」。本轮 8 类「无 Decision 记录」中至少 6 类落在 ticket/map 端，它们的共同根因就是这两条规则的张力：非约束制品的维护义务没有责任人、没有检查点、也没有 lint 覆盖。
- **证据**：报告 §7「无 Decision 记录（必须点名，共 8 类）」整节与 §1 wayfinder 段「累积了两年漂移的散文」定性
- **基线**：`unchanged-since-pin`
- **归属理由**：问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。

### UD-05 — beta_effective 对 γ 不可微，训练性论证依赖该通路

- **源 id**：`C-052` ｜ **主桶**：user-decision ｜ **裁决**：PARTIALLY_REAL ｜ **严重性**：MINOR
- **位置**：`src/decompmoe/schedule.py:171`（pin 态）
- **Requirement**：wayfinder Req 7 L123/L130 / Req 24 L586 / skeleton L471-473
- **溯源 id**（`origin_ids`）：`rv:gap2:math`、`rv:gap2:source`
- **问题**：beta_effective(gamma_p: float, …) 返回 requires_grad=False, grad_fn=None，叠加 Phase 2–3 对 β_max(t) 的硬 clamp，使 γ→loss 的梯度通路在 spec 所设计的 AdamW 训练下看似不存在。三路反驳使 math 镜降级为 PARTIALLY_REAL（Phase 3 cap 是严格递增 ramp、上界在 phase_end 排他约定下不可达故总会释放；γ_init≈−3.5 处 dβ/dγ=0.9077 存活；Phase-4 γ reset 重开通路 dβ_eff/dγ'=7.742），但『梯度通路在 Phase 1–3 不存在』的解读仍需 spec 侧澄清。
- **证据**：_merged_verdicts gap2（ADV-03）；报告 §8 偏离表第 3 行
- **基线**：`unchanged-since-pin`
- **归属理由**：问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。

### UD-06 — 312 行审计台账从未回流主干且与主干分叉

- **源 id**：`O-29` ｜ **主桶**：user-decision ｜ **裁决**：STILL_REAL ｜ **严重性**：MINOR
- **位置**：`REVIEW-LEDGER.md`（pin 态 line=0，目录级/模块级定位，无有效行号）
- **Requirement**：N/A
- **溯源 id**（`origin_ids`）：`rv:main16:source`
- **问题**：audit/sdd-review-2026-09-04 分支上的 REVIEW-LEDGER.md 从未进入 dev（dev 树中任何路径下都不存在该文件），该分支与 dev 已分叉，两份同名文件的差异量达 201 增 63 删。内容已推到远端未丢失，但属审计制品未回流，后续审计读不到这份台账。
- **证据**：f_main/016.json（W1-GIT-06）；_handoff_verdicts_all.json key=rv:main16:source（STILL_REAL）；报告 §10 Batch D-2 git 卫生
- **基线**：`unchanged-since-pin`
- **归属理由**：问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。

---

## 交叉核查

本节把 `check-completeness.json` 与 `check-contamination.json` 指向本桶的 issues 原样登记，不重判。

### 1. 分桶冲突（上游报告自身 / 上游规则不一致）

| # | 条目 | 冲突 | 状态 |
|---|---|---|---|
| 1 | AC-23（O-10，main3） | 报告 §2.2 L56 判 NEVER_EXISTED（该 change 目录在 pin 态不存在）、§3.1 L318 判 STILL_REAL / MAJOR、§10 Batch D-2 L1641 明写「不入批」。classified.json 采纳 §3.1。 | **待裁定**，未消解 |
| 2 | DF-08（main18，不在本桶） | 同一 locus `openspec/specs/wayfinder/spec.md:382`：AC-52（W02）在本桶，DF-08 落 direct-fix，违反 classified 自订规则「凡涉及 spec / governance spec / ticket annotation / change 制品 / archive 流程 / 门禁脚本的取 opsx-change」。 | **待改桶或登记为例外** |
| 3 | UD-04（W44） | 同一实体同时支撑 user-decision（UD-04）与 A-7 的 7 条 map.md / ticket 漂移条目，跨桶共享 6 个 finding id，会被两份清单分别计数。 | **待收窄 `origin_ids` 或登记双桶归属** |
| 4 | AC-10 / AC-33 / AC-41 | 同一 UR 闭式缺口被拆成三条；上游合并规则要求同实体 + 同 `location_file`，本轮未合并。 | **待合并或明确分列理由** |
| 5 | AC-27（V-18） | 记录的 `baseline_status=touched-since-pin` 与机械查表结果（`unchanged-since-pin`）不符。 | **本文件以查表为准** |

### 2. 方案污染处置（`check-contamination.json`）

上游 193 条中 1 条判污染、7 条判 borderline。落到本桶的只有 2 条 borderline，均为**对审计记录本身的祈使/处置措辞**，不针对被审缺陷：

- **AC-06**（V-34）原句「所有 verdict 的时点必须随 pin 标注。」——已改写为「本条的复测时点因此是 HEAD 而非 pin，其自身结论也不外推到 pin 态。」
- **AC-29**（V-27）原句「归档时把「spec 理由错」写成「Jensen 界错」是越界。」——已改写为「本条的结论边界因此是：被证伪的是 spec 给出的理由陈述，不是 Jensen 单向界本身——两者是不同命题。」

污染最重的一条（archive-only AO-31 / P20，带环境变量名的重跑补救）不在本桶。
另需注意边界：`check-contamination` 明确把「零断言 / 缺对账 / 零覆盖」判为问题陈述而非修法提案，把「真值与真位置」判为数学依据，
本文件两类都原样保留。

### 3. 分桶存疑（`check-completeness.json` §11 misplacement）

报告 §11 实际有 **15 条**编号项（不是任务文本说的 12 条）。其中 4 条被 classified 放进 opsx-change，但它们是
**「证据不足 / 复验驳回」的声明**而非可执行行动项，check-completeness 判其应落 archive-only：

| 条目 | 报告 §11 项 | 上游记的严重性 | 问题 |
|---|---|---|---|
| AC-29（V-27） | 第 4 条 | MAJOR | D3 未能证明 Jensen 单向界本身；可执行部分已由 AC-44 承载 |
| AC-30（V-28） | 第 5 条 | MAJOR | gap0 结论成立但 finding 自身证据不可复用；`origin_ids` 另指错（`rv:main20:math` 应为 `rv:gap0:*`） |
| AC-50（V-29） | 第 6 条 | MEDIUM | main42 的「结论反转」被明确驳回；`origin_ids` 另指错（不含 `rv:main42:*`） |
| AC-51（V-30） | 第 7 条 | MEDIUM | main21 / main22 的 violates 归因被三镜一致驳回 |

**这 4 条带 MAJOR / MEDIUM 定级留在本清单，有被当成行动项执行的风险。**本轮不删不迁，仅标注。

### 4. 溯源缺口（报告 §3 finding id 未进入 `origin_ids`）

7 条 §3 finding 的**实体在本桶内，但 id 未进 `origin_ids`**，导致按 id 查表会误判为「未覆盖」：

| 报告 §3 id | 承载条目 | 主题 |
|---|---|---|
| D1-03 | AC-04 / AC-15 / AC-28 | A-2 |
| D1-04 | AC-04 / AC-29 / AC-48 | A-2 / A-6 / A-1 |
| D1-05 | AC-16 / AC-18 | A-2 / A-1 |
| D3-02 | AC-04 | A-2 |
| D3-03 | AC-05 | A-2 |
| main37 | AC-10 / AC-33 / AC-41 | A-1 / A-1 / A-3 |
| main41 | AC-58 | A-5 |

### 5. 内容准确性标记（`check-completeness.json` content_accuracy_flags，落在本桶者）

- **AC-30**：`origin_ids` 记 `rv:main20:math`，内容是 gap0，真实键为 `rv:gap0:math` / `rv:gap0:source`（见 AC-17）。
- **AC-50**：`origin_ids` 记 `rv:main18:source` / `rv:main17:source`，标题说的是 main42，真实键为 `rv:main42:*`。
- 另 4 条 flag 落在其他桶（archive-only C-028、direct-fix V-36 / P19、报告自身），不在本文件范围。
- 报告自身另有一处计数笔误：§2.2 L60 写「其余 4 条」却列出 7 个 id（gap9 / gap11 / main14 / main35 / main2 / main5 / main8）。本轮不展开，仅记录。

---

## 本文件的盲区

### 盲区 1：9 条 §3 finding 在 classified.json 里完全没有实体（最严重）

`check-completeness.json` 报 105/123 覆盖，18 条无落点，其中 9 条是**实体完全不存在**，不是本文件漏搬：

| 报告 §3 id | 内容 | 最近的本桶条目 |
|---|---|---|
| **D1-02** | `_betainc_regularized` 用单个 8 点 Gauss–Legendre 面板、零细分；b=1/2 的平方根奇点使误差随 x=sin²θ→1 爆炸，MVP 工作点 67.24° 已越过 CF 对称性阈值 x*=0.85，89° 处相对误差 1.1e-1。报告 §4 环 1 判其为整条 Voronoi 数值主线的根因，§10 Batch A 列为首条。 | AC-09（C-006）同 locus `src/decompmoe/sphere.py:67`，但只谈守卫强度与 2/13 覆盖 |
| **D1-07** | governance req-gov-1 §4 把 impl-internal frame（单个 8 点 GL 面板、无细分 + 逐位二分输出 1.1735482746999482 / 1.0205068335735599）钉成规范；积分器一旦正确，该 frame 与配套免责文本同时作废。 | 无（AC-62 / C-019 是同一 Requirement 的 obligation 4 零对账，不同问题） |
| **D2-02 + gap4** | `voronoi_angle` 的 MC 容差 σ 建立在「各 cell 面积独立」这一可证伪的假设上；实际 cell 计数服从多项分布且 ΣA_i≡1，一阶 delta-method 方差相消。5σ=0.0355° 比实测 SE 大 10×（随机 16 站点）到 228×（crosspolytope）。 | AC-40（C-020）只谈采样数 / 种子常量零断言 |
| **D2-05** | skeleton req-6 与 governance req-gov-1 Scenario 声称的三个实测 gap「6.5e-5 deg / 1.0e-4 deg / 0.0 deg」有两个错，第三个对采样估计量在原理上不可能；真值约 6.456e-5 / 2.481e-5 / 2.261e-5 deg。 | 无 |
| **D3-01** | `canonical_voronoi_angle` 的反射分支被宣称为 totality 所必需且 `_cap_radius` 被 docstring 描述为 [0,1] 上的逆；实测 N_e=3 / d_c=16 下公开 API 返回 84.4738°，真值 83.4100°，误差为估计量 5σ 的 30 倍，[0.40,0.60] 的 2001 点采样中 1575 点不满足往返闭合。 | AC-16（只谈免责声明挂错侧）、AC-18（只谈测试不敏感），未覆盖公开 API 可达的超差输出本身 |
| **main36** | wayfinder Req 23 整条 Requirement 由行号断言构成，实指 skeleton req-22 而非 req-23；报告 §3.1 判 STILL_REAL / 校准 MEDIUM，§10 Batch D-1 明确列入。 | 无。`rv:main36:math` 只作为 AC-29（V-03 的 12 个弃权键之一）出现 |
| **main38** | skeleton Req 7 的 `‖C_t‖₂ = 1 for every token (within 1e-5)` 是无条件断言，与 Req 19 自己明文规定的 `0 < ‖z‖₂ < ε` 次单位范数区直接矛盾，且无测试走该分支。 | AC-46（C-060，同族但是 exact vs approx 表述的另一个问题） |
| **main73** | wayfinder req-23 对 skeleton 的交叉引用全部写成行号且 Requirement 号错（req-23 实为 req-22）。 | A-4 的 AC-70 / AC-71 / AC-90 是不同 Requirement 的行号漂移 |
| **main78** | governance req-gov-3 称 cycle-5 ticket 的 θ_Voronoi 52°→67.24° supersede 由「spec req-1 L184-L185」承载，但 wayfinder req-1 是 Naming And Alias Convention（L8-L18），L184 是空行、L185 落在 req-9 块内。 | 无 |

**这 9 条里 main36 / main38 / main73 / main78 是 §3 判仍成立、§10 已入批的 spec 缺陷，但 classified.json 里没有落点。**
D1-02 尤其关键：它是报告 §10 Batch A 的首条 finding，也是 A-1 / A-2 里 Voronoi 数值主线的根因，
却只能靠 AC-09 的「2/13 覆盖」侧面读到，实体本身没被登记。**本文件不补写**（本轮是纯整理，不做新发现），此处只点名。

### 盲区 2：AC-29 的结论边界

AC-29（V-27）在本清单里以 MAJOR 出现，但它承载的是**「D3 未能证明 Jensen 单向界本身」这一弃权声明**。
被证伪的是 spec 给出的理由陈述（用了不存在的 `theta_conv` 阈值），不是 Jensen 单向界。
Jensen 问题的可执行部分是 AC-48（`test_voronoi_angle_one_sided_gap` 把单向性降格为方向检查）与 AC-18（反射分支测试声称守护该分支却通过）。
读 AC-29 时不能读成「Jensen 界已证伪」。

### 盲区 3：AC-06 是 HEAD 时点结论

AC-06（V-34）自陈「裁决基线是 pin 6593a06，但 HEAD 188b9fb 已多出 9 个 commit」，其复测在 HEAD 上做。
它同时是 A-6 里唯一的 `MOVED` + CRITICAL 条目，描述 e50cc02 已切断环 4→环 6 而环 1 / 环 2 未修。
**这一条的坐标是 HEAD 的，不是 pin 的**——是 108 条里唯一打破本文件「file:line 一律 pin 态」通例的条目。

### 盲区 4：4 条 §11 声明留在本清单

AC-29 / AC-30 / AC-50 / AC-51 是「证据不足 / 复验驳回」声明，check-completeness 判其应落 archive-only（见「交叉核查」第 3 条）。
本轮按「不删不迁」原则保留并标注，但**执行本清单时这 4 条不应被当作待修复项**。

### 盲区 5：本文件未做的事

- **未重算任何数学。** 所有真值、误差量级、σ 倍数都原样取自上游，未复核。
- **未在 HEAD 上重新定位。** 所有 `file:line` 是 pin 态；`touched-since-pin` 的 10 条（AC-04 / AC-05 / AC-06 / AC-26 / AC-27 / AC-28 / AC-40 / AC-60 / AC-64 / AC-79） 位置已漂移，正文里的行内引用需回 pin 态读。
- **未核对报告内部一致性。** 只搬运了 `check-completeness` 已经点出的矛盾（main3 三处口径、§2.2 L60 计数笔误），没有自查报告其余部分。
- **未补 D1-02 / D2-02 / D3-01 等 9 条缺失实体。** 见盲区 1。
- **未处理与清单 B 的 6 条重叠**（UD-01 ~ UD-06）。见「本文件的读法 · 与清单 B 的边界」。
- **未处理变异副本残留（mut1 / mut4 / mut7）。** 上游拆成 6 条 direct-fix（DF-01 ~ DF-06），是同一实体，占 direct-fix 桶 9 条中的 6 条；其中 DF-01（P19）的 `origin_ids` 是空数组、DF-05（V-36）的 `origin_ids` 指向三个 test-guard finding 与内容无关。归 B 桶，不在本文件。
- **未处理 P05 / UD-03 的 `origin_ids` 跨桶引用。** 它含 `rv:main45`，而 main45（LIFECYCLE-01）在 A-6 的 AC-26 且被判 FIXED_BY_COMMIT 排除在批外。

### 盲区 6：本文件的权威边界

本清单是**既有结论的搬运**，不是审计结论。真相源优先级不变：
`openspec/specs/**/spec.md` > `openspec/changes/archive/` > `wayfinder/map.md` + 23 tickets（advisory）> 代码层。
条目里的 verdict_class 与 severity 是 pin 态的判断，**引用时必须连同 pin 标注一起搬运**。

---

## Errata

> **本节由 change `2026-10-01-audit-errata-a1-numeric-guard-list` 增补。**
> **清单正文结论一律不改写** —— 上方 A-1 桶 24 条的措辞、严重性、`裁决`、`基线` 字段全部保持原样。本节只更正**坐标**与**措辞/数字**，不新增、不推翻任何 verdict。

### 前提：坐标口径

本清单所有 `file:line` 均为 pinned commit `6593a06` 的行号（见 `README.md` 基线警告）。**pin 坐标在 pin 态成立是本清单的既定契约，不是缺陷**；下游变更前须按 `context/07-baseline-drift.md` 的漂移表重定位。因此本节只登记 **pin 态本身就错**的坐标，以及**无论在哪个 rev 都错**的措辞/数字。

审计基线 `6593a06` → 复核时 HEAD `188b9fb`（9 个 commit）。所有复核均锚定 commit object（`git show <rev>:<path>` / `git grep <pat> <rev> --`），未读工作树。

### 生效勘误（11 条）

| # | 条目 | 清单声称 | 实测 |
|---|---|---|---|
| E1 | AC-03 | 位置 `tests/test_beta.py:184` | 该行实为 `test_logit_range` 体内行 `logits = beta_val * (inner - 1.0)`。清单所称的 `test_logit_no_w_i` 在 **`tests/test_distance.py:53`**（pin = HEAD，该文件零漂移） |
| E3 | AC-01 | 位置 `src/decompmoe/distance.py:24` | `:24` 落在 `def squared_chord` 附近；真正 `return beta * (inner - 1.0)` 在 **`:33`**。该文件 pin→HEAD 零漂移，故这 9 行偏差是清单错、不是漂移 |
| E5 | AC-61 | wayfinder req-33 逐字点名 **5** 个 `phase_beta_max` 精确值 | 该 Scenario（`wayfinder/spec.md:665`，THEN 行 `:666`）逐字只点名 **4** 个：`(2,6_000)→1.0`、`(2,16_000)→2.5`、`(3,26_000)→4.0`、`(3,41_000)→10.0`。第 5 个 `3.99985`（`test_sphere.py:184`）来自**相邻** Scenario，不在点名范围内 |
| E6 | AC-77 | `β_p3 = 1.0` 在 Phase 3 **可达**（据「Phase-1 全 5000 步固定 β = 1.0」） | `phase_beta_box(3)` 返回 **`(4.0, 16.0)`**；其 docstring 明写 `(1.0, 32.0)` fallback 适用于「Phase 1 `β^eff = 1.0` fixed」——即 Phase-1 的 1.0 语义上不是 P3 退出值。`gamma_reset_for_phase4` 的全部调用点只传 `16.0` ⇒ **不可达**。**但 `β_p3` 域声明缺失本身仍成立，严重性应下调** |
| E7 | AC-10 / AC-33 | UR 在 `tests/` **零调用、零断言** | `metrics.UR(` 作为调用在 pin 与 HEAD 均 **0 次**（核心主张成立）；但裸 token `UR` 有 **4 处**：`test_metrics.py:65`（集合成员断言）、`:71`、`test_safeguards.py:458`（docstring）、`:466`（`torch.randn(100, cfg.N_e)  # per metrics.UR stacked history`，**模仿输入形状却不调用**）。准确表述为「无**数值**守卫」 |
| E8 | AC-10 / AC-33 | 其余 7 个指标调用计数「1–23 次」 | **三个口径都成立，不可混用**：①**AST 调用点** = `L_sep` 1 / `R_H` 2 / `S_load` 5 / `SP` 5 / `D_chord` 2 / `MCI` 6 / `CG` 17，区间 **1–17**；②**文本匹配行数**（`git grep -c`，**会命中 docstring 里的示例调用**）区间 2–16；③清单给的是 instrumented **运行期**计数（计参数化展开）= 1–23。**以 ①为准** |
| E9 | AC-40 | `1_000_000` 与 `20260929` 在 `tests/` **零命中** | `20260929` 确为 **0 命中**；`1_000_000` 有 **1 处**——`test_sphere.py:240`，位于 docstring 引用 `VORONOI_AREA_SAMPLES = 1_000_000`。另 `test_safeguards.py:94` 的 `0.10000001` 是子串误配。**断言体内命中数仍为 0**，故实质主张成立。**常量名是 `VORONOI_AREA_SAMPLES`**，清单写 `SAMPLES` |
| E10 | AC-18 | `_cap_area` 在 `θ=π/2` 处「左极限与右极限相差 `5.239884e-2` / `7.870852e-2` / `1.158112e-1`」 | 三个数是**单侧**跳变 `|G(π/2) − G(π/2−h)|`。真正的左右极限间距是 **2 倍**：`1.047977e-1` / `1.574170e-1` / `2.316223e-1`（d_c = 8 / 16 / 32，h=1e-7） |
| E11 | AC-91 | req-24 的三个 γ/β 中间量「无任何测试钉住」 | γ-space 间隙**有两条真断言**：`test_beta.py:154` `round(float(gamma_full), 4) == -6.7835`、`:164` `gamma_full == pytest.approx(-6.7835, abs=1e-4)`（后者带 `f"actual="`）。β-space 残差 `1.5899599e-6`（`:160`）与斜率 `0.0350220952386`（`:161`）确**均只在注释里** |
| E12 | AC-48 | 单向界被一个**不存在的阈值** `theta_conv` 门控 | `e50cc02` 已把该门控**整体删除**，Jensen 前置条件改为无阈值的 `∀i: A_i < 0.5`，由 `test_voronoi_angle_precondition_is_area_below_half`(`test_sphere.py:551`) 守。HEAD 的 `theta_conv` 仅剩 1 处命中（`test_sphere.py:580` 的 f-string 报错文案，说明其「已退役」）。**该具体指控不成立**；但「单向性只有方向约束、无幅度」仍成立 |

| E13 | AC-08 / AC-09 | 清单认为 6dp 字面量 `1.173548` / `1.165848` 已被有效守护 | **该字面量必须与「求积器是否已修」联读才有意义，但其本身是标准 red→green 判别式。** `governance` obligation 3 的 `abs=1e-6` **恰好 ≥ 新旧字面量之差**（两者相差 **恰为 `1.000e-06`**），故现字面量对修前 impl 与修后真值**都 PASS**（`2.747e-07` / `5.741e-07`）；但新字面量 `1.173547` 对修前 impl `1.1735482746999482` 为 **`1.275e-06` FAIL**、对修后真值 `1.1735474259197174` 为 `4.259e-07` PASS ⇒ **修前红、修后绿**。N_e=17 同构（`1.297e-06` FAIL / `6.216e-07` PASS）。⇒ **Change 2 只改字面量即产生可观察测试，无需动容差**；且 6dp 字面量对真值的固有截断误差上界为 `5e-07`，**任何 `< 1e-6` 的容差都会在真值上失败**，故 obligation 3 的 `abs=1e-6` 对 6dp 字面量是**必需**而非宽松，维持不变 |

### E10 的根因（清单未给出）

`sin²(π/2)` 在 float64 下**精确等于 1.0**，命中 `_betainc_regularized` 开头的 `if x >= 1.0: return 1.0` 早退 ⇒ `G(π/2) = 0.5`（精确）。而 `x = nextafter(1.0, 0)` 时同一函数返回 `0.8425829560490325`（单片 8 点 Gauss–Legendre 面板在 `x→1` 的平方根奇点上崩溃）⇒ `G` 掉到 `0.421291`。**1 个 ULP 的 x 变化造成 `d_c=16` 时 `7.87e-2` 的面积跳变。**

精确数学在此连续（跳幅随 h 线性趋零）⇒ **该不连续是实现伪影**，其根因是求积器在 `x→1` 的失效与 `x >= 1.0` 早退叠加，而非反射分支本身。

### 复现命令（全部只读，锚定 commit object）

```bash
# E1
git show 6593a06:tests/test_beta.py | sed -n '184p'
git grep -n 'def test_logit_no_w_i' 6593a06 -- tests/
# E3
git show 188b9fb:src/decompmoe/distance.py | sed -n '33p'
# E5
git grep -n 'Scenario.*phase_beta_max' 188b9fb -- openspec/specs/wayfinder/spec.md
# E6
git show 188b9fb:src/decompmoe/schedule.py | grep -A16 'def phase_beta_box'
# E7 / E8 / E9
git grep -n '\bUR\b' 188b9fb -- tests/
git grep -nE 'metrics\.UR\s*\(' 188b9fb -- tests/        # → 0
git grep -cE 'metrics\.(L_sep|R_H|S_load|SP|D_chord|MCI|CG)\s*\(' 188b9fb -- tests/
git grep -n '20260929' 188b9fb -- tests/                  # → 0
git grep -n '1_000_000' 188b9fb -- tests/
# E11 / E12
# E11 / E12
git show 188b9fb:tests/test_beta.py | sed -n '152,166p'
git grep -n 'theta_conv' 188b9fb -- src tests
# E10
python -c "import sys,math; sys.path.insert(0,'src'); from decompmoe.sphere import _cap_area as A; h=1e-7; [print('d_c=%d right=%.6e gap=%.6e'%(d,abs(A(math.pi/2,d)-A(math.pi/2-h,d)),2*abs(A(math.pi/2,d)-A(math.pi/2-h,d)))) for d in (8,16,32)]"
# E13
python -c "import sys; sys.path.insert(0,'src'); from decompmoe.sphere import canonical_voronoi_angle as c; i=c(16,16); t=1.1735474259197174; [print('N_e=16 lit=%.6f |lit-impl|=%.3e |lit-true|=%.3e'%(L,abs(L-i),abs(L-t))) for L in (1.173548,1.173547)]"
python -c "import sys; sys.path.insert(0,'src'); from decompmoe.sphere import canonical_voronoi_angle as c; i=c(17,16); t=1.1658476215516009; [print('N_e=17 lit=%.6f |lit-impl|=%.3e |lit-true|=%.3e'%(L,abs(L-i),abs(L-t))) for L in (1.165848,1.165847)]"
```

### 已撤回（2 条，不是错误）

| # | 条目 | 撤回理由 |
|---|---|---|
| E2 | AC-08 位置 `src/decompmoe/sphere.py:197` | `git show 6593a06:src/decompmoe/sphere.py` 的 `:197` **正是** `def canonical_voronoi_angle(...)`。清单 pin 定位正确；HEAD 在 `:210`（+13 行漂移） |
| E4 | AC-83 位置 `openspec/specs/wayfinder/spec.md:251`(pin) | pin `:251` **正是**含 `P_router/layer = … = 32_896` 与 `P_router = … = 131_584` 的 Router term 行（`:252` 才是空行）。清单 pin 定位正确；HEAD 在 `:252`（+1 行漂移） |

两条都只是漂移，而漂移已被 `README.md` 基线警告与 `context/07-baseline-drift.md` 覆盖，**不构成勘误**。

⇒ **「定位指错」类勘误实际只有 2 条（E1、E3）**，非 6 条。加入 review 阶段新发现的 E13，**生效勘误总数 11**。

### 与未归档 change 的重叠（施工前必须裁决）

`openspec/changes/fix-review-findings-voronoi-precision-and-lineage/` 的 `tasks.md` 全部标记 `[x]`，但该 change **没有 `specs/` delta 目录**（仅 `proposal.md` + `tasks.md`）。其范围与本桶重叠：

| 其条目 | 目标位置 | 对应本桶 |
|---|---|---|
| L4 | `tests/test_distance.py:25-26,87` 缺 `f"actual="` | AC-03 / AC-61 |
| L5 | `tests/test_gating.py:42` `Σp=1` 缺 `f"actual="` | AC-38 |
| H2 / H2b / L7 | `tests/test_sphere.py` Voronoi 字面量恢复与收紧 | AC-08 / AC-12 |
| M4 | `openspec/specs/decompmoe-skeleton/spec.md:98` `abs=1e-4` → `1e-6` | AC-40（同一行） |
| G1 / G5 | `tests/test_schedule.py` | AC-77 / AC-61 |

⚠️ **该 change 的状态尚未裁决**（是「spec 已被 inline 修改、未走 delta 流程」，还是「停滞」）。**开始任何修复 change 的施工前必须先裁决**，否则可能对同一处改动重复施加。

### 两条维护规则

1. **本节只增不减。** 后续若坐标再漂或出现新勘误，**追加**新条目，不得改写既有条目。
2. **本节不是权威副本。** `.audit/` 被 `.gitignore:37` 忽略，**不会进入版本控制**。权威副本是 `openspec/changes/2026-10-01-audit-errata-a1-numeric-guard-list/design.md` 的 D4 节（已跟踪），勘误的完整上下文、风险与验收见该 change 的 `tasks.md`。

## Errata (A-2 桶)

> 本节由 change `2026-10-02-audit-a2-errata-and-spec-math-fixes` 增补；**清单 A-2 正文结论、严重性、`裁决`、`基线` 字段一律不改写**，本节仅更正坐标、数字与 Requirement 归属。
> **本节只增不减**：后续若坐标再漂，**追加**新条目而非改写本节。
> **勘误的 HEAD 坐标以 `188b9fb` 为准**；pin 坐标与「错误本身」永久有效。
>
> 本节的**权威副本在** `openspec/changes/2026-10-02-audit-a2-errata-and-spec-math-fixes/design.md` 的 D4 节。
> 之所以冗余保存：`.audit/` 被 `.gitignore:37` 忽略（`git ls-files` 报 `did not match any file(s) known to git`），本清单**从未被 git 跟踪**，「只增不减」没有 git 历史兜底；design.md 会随归档进 git，故它是可恢复的副本。

**基线与漂移**：pin `6593a06`，HEAD `188b9fb`，`openspec/specs` 在两者之间 3 份全被改动。下列每条勘误均以 **commit object**（`git show <rev>:<path>` / `git grep <pat> <rev> --`）为依据，不读工作树。

**证据类型**：`实测` = 由 `git show` / `git grep` 直接读出；`实测（数值）` = 本轮独立复算（mpmath 50 位 / 整数闭式 / torch 实测），复算脚本 `$env:TEMP\a2_recompute.py` 报 `TOTAL MISMATCHES: 0`。

### 根命题复核

对 `d_c = 16`，`G''(θ) = (d_c−2)·sin^{d_c−3}θ·cosθ / B((d_c−1)/2, ½)`；`sinθ>0` 对 `θ∈(0,π)` 恒成立，故 `G''=0 ⟺ cosθ=0 ⟺ θ=π/2`。0.01° 网格全区间 `(0°,180°)` 扫描**仅 1 个**变号点（落在 90.01°，即真根 90.000° 所在网格格），`G''(π/2)` 为 `~1e-50` roundoff。`G''(82.6036°) = +2.4567878`（严格凸）、`G''(97.2°) = −2.4055898`（严格凹）。⇒ 根命题为真，是下列 6 条共用项的数学前提。**但前提成立 ≠ 条目成立**——其中 5 条实体已修（E1–E5）。

### E1–E19 勘误对照表

| # | 条目 | 清单声称 | 实测 | 证据类型 | 后果 |
|---|---|---|---|---|---|
| E1 | AC-04 | `skeleton:98` 声明 `G` 在 `d_c=16` 于 `(82.8°, 90.0°)` 凹，`STILL_REAL` | pin `skeleton:98` 逐字含该句及 `82.8`/`98.1`/`179.1`；HEAD 三个数字**零命中** | 实测 | **stale**，实体已被 `e50cc02` 修；`STILL_REAL` 不成立 |
| E2 | AC-05 | `tests/test_sphere.py:523` 钉 `81.3148/82.6036/83.7313` 为凸性边界 | pin `:523` 确为 `def test_voronoi_angle_convexity_boundary()`（**行号准确**）；HEAD 该函数已删，改为 `:551` `test_voronoi_angle_precondition_is_area_below_half`，三个数成为「retired artefact」反向护栏 | 实测 | **stale** |
| E3 | AC-15 | `sphere.py:260` 的凹凸性分区图错误 | pin 实为 **261-262**（清单行号偏 2）；HEAD `:267-277` 已是正确版，`:288-294` 另加反有限差分警告 | 实测 | **stale**；`基线: unchanged-since-pin` **标错**（`e50cc02` 改 `sphere.py` 110 行） |
| E4 | AC-64 | `sphere.py:276` 峰值 `+31.5868°` / `θ* = 38.9420°` | pin 实为 **278**（偏 2）；HEAD `:303` 已改为 `+31.5863380965°` / `38.9424412690°`。独立复算 `θ* = 2·arcsin(1/3) = 38.942441268981383°` | 实测（数值） | **stale** |
| E5 | AC-84 | 该条件在 spec 中只是「MAY 级散文」，非 MUST 条款 | HEAD `wayfinder:246` 实为 **MUST 级**：`MUST strictly satisfy θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16) ≈ 20.36°` | 实测 | **stale**：残缺成分不成立，整条降级为已失效 |
| E6 | AC-52 | 位置 `wayfinder:382`；总额 `33_040 MACs = 66_080 FLOPs`；`~0.83%` | 382 是**空行**，内容在 **383**（pin = HEAD，零漂移）。第 (3) 步 cross-head mean `H_kv·d_c = 128 MACs` 从未计入。复算真值 **`33_168 MACs = 66_336 FLOPs`**、**`~1.22%`**（`+1.220703%` vs proj）。`FLOPs_Routing = 66_048`，净差由 `32` 变 **`288 FLOPs**（`0.436%` of routing）。**驳回项复核成立**：`66_336 / 33_554_432 = 0.1977% ≤ 0.3%`，allowance 不反转 | 实测（数值） | 成立，**全数**；行号错 + 数字错 |
| E7 | AC-46 | 位置 `skeleton:455`；`59%` 的随机批次不满足 exact | 455 非目标行，pin **456** / HEAD **459**（+3）。实体成立（float64 约半数行不满足，实测最坏 **`6.661338e-16`**）。但 **`59%` 不可复现**：实测 float64 `49.4%–51.4%`、float32 `54.6%–57.3%`（4 维 × 2 dtype × 100 批 × 256 行），59% 超出观测上界 | 实测（数值） | 成立；**`59%` 不可作可 pin 判据**（口径依赖维度/dtype/形状/种子） |
| E8 | AC-42 | `_betainc_regularized` 在 `x→1` 时相对误差 **76%** | 位置 `sphere.py:73` **pin = HEAD，零漂移**（A-2 中唯一精确锚点）。MVP 点 `8.2915e-07` / `6.633 ppm` 正确；但 `x→1⁻` 实测 abs 升至 `1.5736e-01 @ θ=89.999°`，**相对误差 15.74%**，非 76%（差 5×；其引的 `7.61e-2` 绝对值本身对） | 实测（数值） | 成立；**清单数字错 5×**；`基线` 标 `unchanged-since-pin` **标错** |
| E9 | AC-53 | 位置 `wayfinder:251` | HEAD **252**。复算：按清单排除 `W^O` 得 `452_329_984 − 4_194_304 = 448_135_680`，差 **`0.927266%`** | 实测（数值） | 成立 |
| E10 | AC-82 | 位置 `wayfinder:248`；prose `≈ 484 M` | HEAD **249**。复算 `485_097_984`（`485.097984 M`，偏差 `0.2263%`）。**但该值不以字面量出现在 spec 中**，反事实值是读者自行加总的派生值 ⇒ 清单「同段钉死的精确闭式」措辞**略强于事实** | 实测（数值） | 成立，须同时注明派生性质 |
| E11 | AC-85 | 位置 `wayfinder:435`；「Qwen/GMoE **不可能**有相同 FLOPs」 | 位置**零漂移**（`:435` WHEN / `:436` THEN）。措辞越界坐实；但「不可能」在本仓内**不可证**（Mixtral 项理论上可重参数化），该半句应标为**推断** | 实测 | 成立（措辞层）；`origin_ids` 推理需降级 |
| E12 | AC-86 | 位置 `wayfinder:398`；`≈ 64 KB` 与 `≈ 4 KB` | 398 是**空行**，内容在 **399**（pin = HEAD）。复算 `W_proj = 32_896` 参数 → BF16 `65_792 B = 64.25 KiB`；字面张量集合 `{z, ẑ, z̄, C}` 各 `256 B`（`4·d_c·4`），即便按 3 个 per-head + 1 个 post-mean 拼接也只 **`1_600 B`**，**只有 `H_kv·d_k·4 B = 4_096 B = 4.00 KiB` 恰为 4 KB** | 实测（数值） | 成立，**两项均需改** |
| E13 | AC-87 | Requirement 标 `wayfinder req-20` | L414 属 **req-19**（anchor L411，「Six Baseline Set On 4070 MVP」）；**req-20 是 L442「Eight Geometric Quantification Metrics」**，与 6 个 baseline 无关。同一清单 AC-85 对同一区域标对了 ⇒ 清单内部自相矛盾 | 实测 | 成立；**Requirement 归错** |
| E14 | AC-28 | `skeleton:98` 的 `d_c=2` 未提及 | 错误分区图已由 `e50cc02` 修；但 `d_c=2` 退化**仍未声明**：`git grep -ni 'affine\|d_c = 2'` 在 skeleton spec 只命中 L164 的 antipodal-distance Scenario（与 `G''` 无关） | 实测 | **仅残留真成分**，由本 change 的 F1 修复 |
| E15 | AC-16 | `sphere.py:197` 的 accuracy caveat 只声明了 `< 1e-6` 一侧 | pin **197 = HEAD 210**（与 A-1 change 的 E2 勘误**同坐标**）。**pin 态全段扫 `accuracy\|caveat\|1e-9\|1e-12\|residual\|totalit` 零命中** ⇒ 所述 caveat 在 pin 态**根本不存在**，是 `e50cc02` 之后才加的；清单把它当 pin 态事实是错的。`基线` 标 `unchanged-since-pin` **标错** | 实测 | 清单前提错误；**仅残留真成分**（π/2 硬跳变未披露），由 F9 修复 |
| E16 | **N1（清单外新发现）** | — | `wayfinder:383` 把 bias **单列** `H_kv·d_c = 128 MACs`，`skeleton:151` 却**折进**第 (i) 项 `H_kv·(2·d_k·d_c + d_c) = 32_896`。总额同（33_040）**归因口径不同**，违反同源 Source 镜像的逐字性要求；req-17↔req-19 交叉注记只对齐总额、未对齐归因 | 实测 | 只登记不修 |
| E17 | **N2（清单外新发现）** | — | `skeleton:34` 自称「(Matches master `wayfinder` Req 11 verbatim)」，但 master `wayfinder:252` 为「(`MVPConfig` does not currently expose them as learnable parameters at MVP scale)」，镜像为「(not exposed as learnable parameters in `MVPConfig` at MVP scale)」——**非逐字** | 实测 | 只登记不修（本次 F4 顺带删除了这句失真的 verbatim 声明） |
| E18 | **N3（清单外新发现）** | — | `d_c=2` 时 `G(θ) = θ/π`，50 位 mpmath 下采样偏差 **0.000e+00**（解析恒等），`G(π/2) = 0.5`；`sphere.py:242` 只挡 `signature_dim < 2` ⇒ **`d_c=2` 可达**。`G(θ)=1/N_e` ⇒ `θ = π/N_e`，故 `N_e=2` 时 `θ=π/2`。严格凸退化为等式、Jensen 变恒等式 ⇒ 单向性界**失去推导前提** | 实测（数值） | 只登记不修。**与 E14 是同一事实的两个侧面，修复由 F1 一次完成，不重复计数** |
| E19 | **N4（清单外新发现）** | — | `sphere.py:288-294` 用「the true `G''` there is `+0.21`…`+2.46`」的**区间散文**冒充闭式。复算真值 82° → **`+2.6073072`**、88° → **`+0.7365965`**，与 AC-64 属同类瑕疵 | 实测（数值） | 只登记不修 |

### E20 追加勘误（实施期新增，清单外）—— `d_c = 2` 是单面板 GL-8 求积唯一的「小 `x` 侧」失效点

> 本条在实施 change `2026-10-02-audit-a2-errata-and-spec-math-fixes` 的 F1 时发现，不在原审计范围内，但对 F1 的可实施性是决定性的。按上文「只增不减」规则**追加**本条，不改写 E1–E19。

| 观测 | 值 |
|---|---|
| `_cap_area(θ, 2)` 对 `θ/π` 的相对偏差 | **`3.64%`–`6.41%`**（`θ ∈ (0°, 90°)`，最差在 89.9°） |
| `canonical_voronoi_angle(N_e, 2)` 对 `π/N_e` 的相对偏差 | 最差 **`5.39%`**（`N_e = 32`）；`N_e = 4/8/16` 分别为 `4.78%`/`5.24%`/`5.36%` |
| `N_e = 2` 看似准确（`6.71e-9`） | **假象**：二分落在 `x >= 1.0` 早退平台 `π/2` 上，即 E15/F9 披露的那处不连续，而非求积准确 |
| 根因 | `d_c = 2 ⇒ a = (d_c−1)/2 = ½`，GL 面板被积函数 `u^(a−1) = u^(−1/2)` 在**左端点平方根奇异**；`d_c ≥ 3 ⇒ a ≥ 1`，被积函数在 `u = 0` 光滑 |

**为什么重要**：精确实数算术下 `G(θ) = θ/π`（因 `I_x(½,½) = 2·arcsin(√x)/π` 且 `x = sin²θ`），但**本实现达不到**。任何「`d_c=2` 下实现满足 `G(θ)=θ/π`」的条款都无法被 `pytest.approx(..., abs=1e-12)` 对账——实测 abs 偏差 `5.896e-03`。这与 E19、AC-42 属同一类错误（单点最优冒充全域）的**镜像**：那次发生在 `x→1` 侧，这次发生在**小 `x` 侧**。

**处置**：只**声明**不修复。修它需给 `_betainc_regularized` 的 GL 面板加细分或换求积器，属 `src` 行为变更，超出该 change 范围。修复方案（细分面板 / 换 `scipy.special.betainc` / `d_c=2` 走解析特例）留待独立 change 裁决。

### 清单自身的 7 类错误（汇总）

1. **Requirement 归错 1 条**：E13（AC-87 标 req-20，实为 req-19），且与 AC-85 自相矛盾。
2. **行号错 5 条**：AC-52(382→383)、AC-86(398→399)、AC-46(455→456/459)、AC-15(260→261-262)、AC-64(276→278)。
3. **`基线` 标注错 4 条**：AC-15/16/42 标 `unchanged-since-pin`，但 `e50cc02` 改了 `sphere.py` 110 行；AC-46 标 `unchanged-since-pin` 但实际漂了 +3。
4. **数字自身算错 4 处**：AC-42「76%」→ 15.74%；AC-46「59%」→ 实测 49.4%–57.3%；AC-15「+2.185」→ 真值 +2.1862978；AC-84「9207 步」→ 仅在**不计 Phase 0** 时成立（计则 10_207；`beta_effective()` 对 phase 0 直接 `raise`，β 未定义）。
5. **已修未同步 5 条**：E1–E5（AC-04/05/15/64/84）仍标 `STILL_REAL`。
6. **裁决口径自相矛盾 1 条**：E5（AC-84 残缺成分称「MAY 级散文」，HEAD 已是 MUST 级）。
7. **溯源缺口字段 6/6 全部属实**，与 `context/00-provenance.md` 的 `covered_by` 映射逐一吻合；`origin_ids` 未发现凭空 id。

### Dedup 登记

| 重叠方 | 重叠内容 | 处置 |
|---|---|---|
| A-1 change `2026-10-01-audit-errata-a1-numeric-guard-list` 的 **E2** | AC-08 勘误 `sphere.py:197` → `canonical_voronoi_angle` HEAD `:210` | **与 E15（AC-16）引用完全同一坐标**（pin 197 就是 `def canonical_voronoi_angle` 行）。两条勘误指向同一行但结论不同（E2 说「行号指错」，E15 说「所述 caveat 在 pin 态不存在」），**不矛盾，是同一位置的两个不同事实** |
| 未归档 `fix-review-findings-voronoi-precision-and-lineage` | tasks 全 `[x]` 但**无 `specs/` delta**；H2/H2b/L7 动 `tests/test_sphere.py` Voronoi 区域（与 AC-05 现在的 `:551` 重叠）；M4 动 `skeleton:98`（与 E14/F1 同 locus） | **已裁决 = 「已 inline 应用未归档」**：G1/H2/H2b/G5/L5 的声称改动实测均在工作树生效。本 change 的 delta 由**当前**主 spec 生成、测试全为**新增**函数名，故无需重定位 |
| `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` | 半归档：`proposal.md`/`tasks.md` 已删除未提交，`specs/` 目录仍在 | **门禁**：其 archive 会改动 spec 基座。`4f3e752` 本会话内已改 `wayfinder/spec.md` 15 行，基座确在漂移 |
---

## Errata (A-4 段)

> 本节在实施 change `2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract`
> 时写入。按上文「只增不减」规则**只追加**，不改动 AC-34…AC-90 任一原条目。
>
> **测量基准**：全部坐标经 `evidence/derive_a4_errata.py` 从 git 重新派生，
> 对照 blob 为 pin `6593a06` 与 audit HEAD `188b9fb`；`基线` 字段一节的
> commit 计数测于 `850ed8a`。逐项可复算，不引用本清单的 `基线` 自述字段，
> 也不引用本 change 早前的复核结论。

### A4-E1 — AC-34 的行内坐标是 0-based，且其所称的「漂移」在该坐标上不成立

AC-34 正文称「wayfinder L413 实际是空行——MCI 行在 L460、Source 在 L463、两个
MCI Scenario 在 L497/L501」。在 pin `6593a06` 实测（1-based）：

| 清单所称 | 1-based 实测该行 | 1-based 实测下一行 |
|---|---|---|
| L413 是空行 | `### Requirement: Six Baseline Set On 4070 MVP` | `''`（空行） |
| MCI 行在 L460 | 表格中的 `D_chord` 指标行（相邻行） | 表格中的 `MCI` 行：`MCI = 1 / (d_c · Σ λ̃ⱼ²)` … |
| Source 在 L463 | `''`（空行） | `**Source:** \`wayfinder/tickets/A8-2.md\`…` |
| Scenario 在 L497 | `''`（空行） | `#### Scenario: MCI closed-form on uniform token distribution` |
| Scenario 在 L501 | `''`（空行） | `#### Scenario: MCI closed-form on rank-1 token distribution` |

**五个坐标全部恰好少 1**，且「L413 是空行」只在 0-based 读法下为真 ⇒ AC-34 的行内
坐标按 0-based 书写。**更关键**：pin `6593a06` 与 audit HEAD `188b9fb` 的
wayfinder spec 在上述每个坐标上**逐字相同**（两版均 894 行），即该区间**没有发生
任何漂移**。AC-34 对 req-36「多数已漂移」的裁决，有一部分证据是这个基准差，而不是漂移。

同一读法问题波及 AC-88（聚合记录，直接引用 req-36 的 L434-505 / L450 / L453 / L454 /
L456 / L416 / L413 坐标族）与 AC-59（「skeleton L242 引 wayfinder L249 实为 L315」），
二者应与 AC-34 一并按 0-based 复核后再采信。

### A4-E2 — `基线` 字段在文件级读法下 15/15 全错（不是部分错）

A-4 全部 15 条的 `基线` 一律写 `unchanged-since-pin`，整齐得反常。按「该文件自 pin
起是否被改动过」读法实测（`git log 6593a06..850ed8a -- <file>`）：

| 文件 | pin 后 commit 数 | 覆盖的 A-4 条目 |
|---|---|---|
| `openspec/specs/wayfinder/spec.md` | 8 | AC-34 / AC-88 / AC-89 / AC-90 |
| `openspec/specs/decompmoe-skeleton/spec.md` | 8 | AC-59 / AC-63 / AC-70 / AC-71 |
| `src/decompmoe/sphere.py` | 5 | AC-72 |
| `tests/test_safeguards.py` | 4 | AC-67 |
| `tests/test_extraction.py` | 4 | AC-69 |
| `src/decompmoe/metrics.py` | 3 | AC-68 |
| `src/decompmoe/schedule.py` | 2 | AC-66 |
| `src/decompmoe/config.py` | 1 | AC-65 |

**无一个文件自 pin 起零改动** ⇒ 15/15 的 `基线` 标注均不成立。

**该计数本身会漂，故必须记基准**：本 change 在 apply 起点（`1526b98`）实测为 **14/15**，
唯一例外是 `src/decompmoe/config.py`（当时 pin 后 0 commit）；本 change 的清扫提交
`a1f0caa` 随后改动了该文件，例外消失。**这正是本 Errata 记录的那一族缺陷**：一个不带
基准的计数，会在被测对象自身变化后静默改变真值。

### A4-E3 — AC-88 是 AC-34 / AC-89 / AC-90 的聚合记录，且重复对字段值比对不可见

AC-88 标题自称「（聚合记录）」，其 `origin_ids` 为 `main44`、`main72`、`main74`、
`main77` 四个；而这四个 id 分别就是 AC-90（`main77`）、AC-34（`main72`）、
AC-89（`main74`）与 AC-88 自身（`main44`）。

**因此 AC-34 + AC-89 + AC-90 的内容已被 AC-88 整体重述一遍**。任何按 `origin_ids`
**字段值**做去重的检查都发现不了：AC-88 把四个 id 塞进一个字段，字段值与那三条各自
的单 id 值不相等。只有把该字段拆成 id 列表再比对，重复才显形。

另：AC-34 与 AC-88 的 `位置` **完全相同**（均为 `openspec/specs/wayfinder/spec.md:847`
pin 态），`源 id` 却分别是 `W12` 与 `W13`，条目间无任何交叉引用。

### A4-E4 — AC-70 的 `位置` 指向空行；AC-59 / AC-70 不是重复项

pin `6593a06` 的 skeleton spec 实测：L240 = `''`（**空行**），L241 =
`#### Scenario: L_sep closed form`，L242 = 该 Scenario 的 `- **WHEN**` 子句。
故 AC-70 的 `位置` `skeleton:240` 指向空行，内容在 241 起。

**AC-59 与 AC-70 不是同一条**：AC-59 是 spec→spec 指针（skeleton 引 wayfinder
`L249`），AC-70 是 spec→code 指针（skeleton req-12 引 `safeguards.py:211/:222`），
目标不同，只是 `位置` 相隔 2 行。本 change 早前一轮复核曾把二者登记为重复项，
**该判断错误，此处更正**。

### A4-E5 — AC-63 的「零命中」属实，但清单把它归错了原因

AC-63 主张 `arctan(pi/sqrt(d_c))` 这一形式在 spec 中零命中。实测零命中为真
（`evidence/pointer_census.py` 的分类器自检以 `wayfinder L249` = 10 作阳性对照，
确认分类器未失效）。

但清单把「3.58」当作该不变量的组成部分之一。**`3.58` 与 arctan 无关**：它是
`sphere._betainc_regularized` 自身 docstring 在 `θ = 82.6036°` 处报告的求积误差
`3.58e-16`，与该 token 无关。因此「`3.58` 缺失」这条证据对 arctan 不成立，
零命中**只**证明该字面 token 不存在，不能证明其数学内容未被以其他写法引入。

清单所称偏离幅度亦只有 1/3 可复现：实测 `5.078e-01`（`N_e=16`）与 `5.001e-01`
（17）可复现，`1.53e-05` 不可复现（`N_e=64` 实测 `3.547e-01`）。

### A4-E6 — 本段的 4 条处置汇总

1. **基准错误 1 族**：AC-34 / AC-88 / AC-59 的行内坐标为 0-based（A4-E1）。
2. **`基线` 字段 15/15 错**，且该计数自身随被测对象漂移（A4-E2）。
3. **静默重复计数 1 处**：AC-88 聚合 AC-34/89/90，字段值比对不可见（A4-E3）。
4. **`位置` 指向空行 1 条**：AC-70（A4-E4）；AC-59/AC-70 非重复，本段更正了
   本 change 早前一轮复核的错误登记。

**AC-34 的处置变更**：其「req-36 整段行号指针失效」的**实体**经本 change 独立确认
成立（req-36 的 Scenario 标题本身含行号，无法以 MODIFIED 改写，已按
`## REMOVED Requirements` 移除并迁移其 4 条保障）；但其**证据中的坐标基准**须按
A4-E1 更正后重述，本 change 未据其坐标数字施工。


---

# Errata — A-5 段事实验证结果（2026-10-03，追加，不改原条目）

> 本节由 2026-10-03-a5-archive-gate-executability change 追加。原 AC-19…AC-102
> 条目**逐字未动**，本节只记录在 HEAD 940b27c 上的重新定位与实测裁决。
> ⚠️ .audit 被 .gitignore:37 忽略、tracked 文件数 0 ⇒ **本节永不会被提交**，
> 仅作本地记录，不得据此认为已交付。

## 1. 判定分布（自行重数，未引用任何上游汇总）

| 判定 | 条数 | AC id | 处置 |
|---|---|---|---|
| CONFIRMED | 11 | AC-19、21、24、36、49、57、80、81、92、100、101 | 7 条施工 / 4 条延后或只记录 |
| FIXED | 4 | AC-23、31、58、102 | 结案 |
| PARTIAL | 3 | AC-20、22、25 | AC-20/25 门禁族施工；AC-22 残留归「不接管」 |

合计 18，与条目数一致。**无整条 UNVERIFIABLE**，仅 3 个子主张不可复现（AC-19 的
瞬时态与 openspec 版本归属、AC-25 的两次采样时点窗口）。

## 2. 四条 FIXED 的证据

- **AC-31**（pytest.approx 容差公式自指）：pin L13 含 max(abs, rel·|expected|) 与
  「rel 默认 1e-12」的错误理由；HEAD 零命中，改为 version-independence 论证
  （2510ea5 + change 2026-10-02-corr-pytest-approx-abs-semantics）。
- **AC-23**：b10-b11-b12 change 已被 git 跟踪（git ls-files --error-unmatch 命中）
  并带 3 份 delta spec 归档（c0ec330）。清单标注的「口径冲突」在物理上已消解。
- **AC-58**：skeleton spec.md 三处指针全部已对准 
eq-7 L130 / 
eq-7 L123。
- **AC-102**：b13-b16 change 已由 315065e 归档。

## 3. 清单自身的失真（照抄会出事）

- **行号实际只漂移 3 条**（AC-92、AC-58，加 3 条路径整体迁入 rchive/），
  其余 12 条漂移为 0 —— 清单整体标称的漂移面比实际大得多。
- **「位置」瞄错 2 条**：AC-20 与 AC-49 同标 CLAUDE.md:45，真值 **:32**（-13）。
  CLAUDE.md pin→HEAD 未被修改，是撰写期定位错误，不是漂移。
- **行号基准混用**：全清单 1-based，**唯 AC-92 是 0-based**。
- **「基线」字段 6 条误导**：AC-19（机械比对对「工具行为缺陷」完全失灵）、
  AC-22/23/58/102（目录已迁 rchive/ 却仍写 unchanged）、AC-100（支撑计数过时）。
- **清单自身事实错误 2 处**：AC-20 称 §3 含 alidate --specs（**CLAUDE.md 从未
  包含**；它住在 .claude/commands/opsx/sync.md:150）；AC-58 称「wayfinder L122
  是空行」（pin 的 L122 是 req-7 正文）。

## 4. AC-81 的判定修正 —— 清单在这里是错的

清单称 > **Source:** 前缀行是**漏报**。实测：那一行是 
eq-19 内对 
eq-20
Source 字段的**逐字引用副本**（真字段在其后 12 行）。若按 AC-81 放宽
SOURCE_LINE_RE 接受 > 前缀，lint 会**立刻判该行违规并 exit 1**，把当前绿灯打红
—— 修一个不存在的漏洞，制造一个真实回归。**AC-81 已裁决延后**，SOURCE_LINE_RE
未被修改。

## 5. 归档当天实测复现的 AC-19（新增记录）

change 2026-10-03-a5-archive-gate-executability 归档时，**openspec archive 当场
吞掉了 <a id="req-gov-7"></a>**，而 
eq-gov-7 的 Requirement 正文**完整无损**。
已按 
eq-gov-9 手术式补回 anchor + 空行（未重跑 archive），governance 由 6 → 9
个 anchor，总数 65 → 68，openspec validate --specs --strict exit 0。

**同时暴露了本 change 自身的流程缺陷**：归档前写的账本**未声明预期新增 anchor**，
于是 lost 比对（基线有、现在没了）**按构造看不见**它 —— 该 id 既不在基线也不在树里。
只有 
ever_added 能抓。已修：nchor-ledger --write --change <name> 现在从该
change 自己的 ## ADDED Requirements delta 自动派生预期清单，并有
	ests/test_run_gates.py::test_verify_catches_an_anchor_the_archive_swallowed 钉死。

## 6. 不接管的条目

- **AC-36 / AC-101 / AC-22 残留**：2026-09-26-followup-… 与
  ix-review-findings-… 的 proposal.md/	asks.md 正被并行 session 处于
  「已删除未提交」状态（两者至今 openspec validate --strict exit 1
  "must have at least one delta"）。**不接管**，只记录。
- **AC-57**（wayfinder/tickets/A4-1.md:59 仍写 
eq-7 L122）：票据注解形式正被
  并行 change 的 
eq-gov-2 改写（L### → anchor 形式）接管，**延后**。
- **AC-100**（change 目录名无日期前缀）：落点是被排除的 ix-review-findings-…
  目录，**不碰**。附带：清单的支撑计数（67 中 64）已过时，HEAD 实测 archive 目录
  86 个 / 带日期前缀 83 个。

## 7. 清单未覆盖的相邻缺口（发现但不在本次范围）

openspec/specs/wayfinder/spec.md 有 **36 个 Requirement 但只有 35 个顶格
**Source:** 行** —— 
eq-34 本身没有 Source 字段。lint_no_source_field_drift.py
只校验**已存在**的 Source 行，**无法发现整条缺失**。属独立缺陷（与 AC-24 的
「子串过松」不同），本次只记录不改。
