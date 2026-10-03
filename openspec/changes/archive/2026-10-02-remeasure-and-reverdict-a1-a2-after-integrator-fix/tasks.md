# Tasks

> 104 条台账条目的**机器可读主体**在 `evidence/ledger.json`（design.md D10）；本清单是执行顺序，`design.md` 承载决策与逐桶小结。
> 每组的最后一条是**本组自带的**一致性检查——不把检查堆到最后（design.md R1）。

## 0. 门禁（apply 开工前必须先完成）

- [x] 0.1 锚定两端坐标。记录审计 pin 态 commit（从 `.audit/**` 的溯源字段反查并用 `git show <pin>:<path>` 确认，不采信其行号字段），以及新态的 `git rev-parse HEAD` + 本 change 触及文件的 sha256 清单，落盘 `evidence/baseline.json`。~~**必须显式记录「求积器修复未提交、基准由工作树承载」**~~ **→ [2026-10-02 更正] 该要求的前提已被实测推翻**：求积器修复已提交在 HEAD，`sphere.py` / `test_sphere.py` / 3 份 spec 均在 HEAD；工作树承载项仅 `gating.py` / `WF-1.md`，不在测量链上。改按**内容级**三值判定（`IDENTICAL` / `CRLF_ONLY` / `CONTENT_DIFF`）落盘，并显式记录 CRLF 造成的字节级假阳性（**数量逐次变动，6 → 10 → 9，须与 `baseline.json` 的 `head` 字段一同引用，不得写死**；见 D4 二次更正）。验证：脚本重跑三次得到同一份 sha256 清单（`F4AA04A1…`，幂等 ✅）；`git show <pin>:<path>` 20/20 可取、无缺失 ✅；anchor **覆盖**契约复算通过（每条 Requirement 恰一个独立 anchor、无重复；绝对计数 37/23/4，wayfinder 由 36 增至 37 是 `1afac58` 合法新增 Requirement 所致，契约改为检查覆盖而非常量）✅；生成脚本内置跨方法断言（`git hash-object` / `git diff` 必须与内容级判定一致）全部通过 ✅。**实施期复锚**：HEAD 在本轮被并行 session 推进 `f6461d7` → `8ba7d6f` → `a97e3a7`（后者 4 个 commit 触及 `src/` 与 `openspec/specs/`），已重跑脚本重新锚定。
- [x] 0.2 冻结 oracle。沿用 change `2026-01` 的 `evidence/oracle.py`（dps=60，两条独立路线），复核其在 5 个 `(N_e, d_c)` 上 `spread == 0.00e+00`；把本 change 需重测的探针点追加进去并落盘 `evidence/oracle_recheck.json`。~~验证：退出码 0 且末行 verdict 为 PASS；先拿一条「已知存在」与一条「已知不存在」的样本验一遍匹配器再跑全量。~~ **→ 冻结 oracle 实际位于 `2026-10-02-fix-canonical-literal-…` 归档（task 原写的 `2026-01` 不存在），已在 json 中显式记录而非静默替换。5 个探针点两路线 `spread` 全为 `0`；3 参 `betainc` 陷阱作为反向对照保持分离（gap 0.46–1.68），确保「两路线互验」不是空转。impl↔oracle 偏差 1.65e-14 ~ 3.55e-14，全部 < 1e-12。matcher control 通过：AC-09 的科学计数法 `1.1813e-6`/`1.1818e-6`/`1.3579e-2` 命中、AC-74 命中、AC-44 不命中。冻结 oracle 原样重跑 `exit 0` + `ORACLE VERDICT: PASS`。退出码 0。**
>
> **本任务自身修正的两个自造缺陷**（均曾产生自信的错误结论）：① 签名靠猜 —— `canonical_voronoi_angle(n_e=, d_c=)` 报 TypeError，实为 `num_experts`/`signature_dim`，已改为 `inspect.signature` 取值；② 数值正则带否定前瞻 `(?![\w])`，**静默丢弃全部科学计数法**，使 AC-09 这条明写求积探针的 finding 计成未命中、求积相关数虚报为 17/95。修正后为 26/95、字面量 83→117。教训：零/低计数先做独立文本 grep 确认，且**不要用手写常量表当匹配基准**——应由运行真实代码导出。

- [x] 0.3 建台账骨架。落盘 `evidence/ledger.json`，schema 固定为：`{ac_id, bucket, title, in_source_as_heading, dependency: {depends, derivation, code_refs}, invalidation_kind: numeric|coordinate|provenance|none, remeasurement: {old, new, method}, verdict_old, verdict_new, verdict_evidence, status, provenance}`。~~95 条全部预置为 `status: PENDING`~~ **→ 落盘 104 条（95 源内 + 9 无实体），全部 `status: PENDING`、`dependency.depends: null`。** 验证按「集合 diff 而非计数」执行：① 两条独立提取路径（item 优先 / header 优先）对称差 = `0`；② `missing_from_ledger` / `extra_in_ledger` 双向为空；③ `X-` 与 `AC-` 命名空间无交叉；④ ac_id 唯一；⑤ 分桶 A-1=26 / A-2=17 / A-3=17 / A-4=18 / A-5=18 / A-7=8。`excluded_items` 登记 13 条（A-6=7、A-8=6，6 条 `UD-` 全落 A-8）。按 D3，审计的 `裁决` / `基线` 只转抄进 `provenance.audit_*_claim` 并附 `authority_note`。

- [x] 0.4 建结构检查器。实现 design.md D1 的三段推导齐全性检查与 D2 的「非依赖者必须有依据」检查，输出每条缺什么。~~验证：先在一条故意写坏的样本上确认检查器会红，再在 0.3 的空台账上确认它只报「全缺」而不误报其它。~~ **→ 落盘 `evidence/tools/check_ledger.py`，自测 7/7 PASS、`exit 0`。T1 故意写坏的 10 类样本全部被捕获且理由正确；T2 5 条夹具只标出那 1 条坏的（守「全报等于不报」）；T3 空台账 104 条全 OUTSTANDING、0 条结构性错误；T4 104 条填满后同时 clean 且 complete（否则该检查器永远不让人收工）；T5 转抄勘误的 verdict 被捕获而自行重导的不误报；T6 无盲区行的 `X-` id 与缺 locus 的 `X-` 条目被捕获；T7 104 / 95+9 分区是真不变量（少一条或重复一条都会破）。**
>
> **自测抓到的自造缺陷**：① 「`bool(空dict) and …`」把真空为真报成控制失败——已改为分支判定，并把「0 条错误」这个**更强**的事实单独陈述；② 更要紧的是**检查器本身的空洞化**：PENDING 且 `depends=None` 被当作合法，于是「N 条待做」与「N 条完成」输出完全一样，等于给了一条能带着全空台账收掉 change 的路。现已把 `problems`（结构性错误）、`outstanding`（未完成）、`denominator`（分母）**分三个通道**报告并分别 gate；③ T6 首次失败是**测试样本自身**没传 `registered_x`（默认空集使规则被跳过），规则本身正确——「无法失败的对照不是对照」。
>
> **分母常量收归一处**（风险 R-a）：`EXPECT_TOTAL=104` / `EXPECT_IN_SOURCE=95` / `EXPECT_UNREGISTERED=9` 只在 `check_ledger.py` 顶部定义，扩范围时不会漏改多处硬编码。

- [x] 0.5 勘误层与盲区层解析。清单除 108 条发现外还带 11 条生效勘误 / 2 条已撤回 / E1–E19+E20 / 6 条盲区，且**盲区 1 登记了 9 条 `classified.json` 中完全无实体的上游 finding**（其中 `D1-02` 即本次求积器缺陷的根因本体），全部落盘 `evidence/errata_index.json`。验证：脚本 `evidence/tools/build_errata_index.py` 自检 `exit 0`；`###` 标题 **135** = 108 `AC-`/`UD-` + 27 章节标题，分区闭合（108 + 6 + 21 = 135）；A-1 生效勘误 11 / 已撤回 2；A-2 E1–E19 共 19 + E20（**E20 是 1 条勘误用 5 行观测表表达，按行数计会把勘误总数从 20 虚增到 24**）；6 盲区；9 条无实体 finding 逐条带 `source_ref` 与「无 pin 坐标」说明。另记录勘误自称锚定 `188b9fb` ≠ 当前 HEAD `8ba7d6f`，其间 5 个 commit 改过 `openspec/specs/`，故勘误坐标与数值均已过期。

## 1. A-1 数值守卫缺口（24 + 2 = 26 条）

优先判定（线索，非结论，按 D1 逐条验）：`AC-08` `AC-09` `AC-48` `AC-62`。
条目：`AC-01 AC-02 AC-03 AC-07 AC-08 AC-09 AC-10 AC-11 AC-12 AC-13 AC-18 AC-33 AC-37 AC-38 AC-39 AC-40 AC-47 AC-48 AC-60 AC-61 AC-62 AC-77 AC-83 AC-91`。
本桶追加的无实体条目（D9）：`X-D1-02`（求积器根因本体）、`X-D2-02`（MC 容差 σ 建立在可证伪的独立性假设上）。

- [ ] 1.1 逐条写三段依赖性判定（① 依赖的量 → ② 计算链是否过求积路径 → ③ 链上哪一行），26 条全部完成。验证：0.4 的检查器对 A-1 报 0 缺项。
- [ ] 1.2 对 `depends: true` 的条目重测数值，填 `remeasurement.{old,new,method}`。验证：新值经 0.2 的 oracle 两路线互验；`old` 取自审计正文原文而非其 `裁决` 字段。
- [ ] 1.3 对 `depends: true` 的条目重判 verdict，按 D3 的五值分类法；`RESOLVED_BY_UPSTREAM` 必须附因果链，无因果链者降级为 `REMEASURED_SAME`。验证：抽查 3 条能沿 `verdict_evidence` 复现裁决过程。
- [ ] 1.4 **D8 边界**：本桶的 `verdict_evidence` 不得无独立锚点地引用勘误的修前字面量（`1.1735482746999482` / `1.0205068335735599`）或勘误编号（`E1`…`E13`）。A-1 勘误已对 `AC-08` / `AC-09` / `AC-10` / `AC-18` / `AC-33` / `AC-40` / `AC-48` / `AC-61` / `AC-77` / `AC-91` 给出裁决——**这些结论一律不得作为起点**。验证：T5 规则对本桶报 0 命中。
- [ ] 1.5 **D9 专项**：`X-D1-02` 的 D1 第③步须从零建立（它是根因本体，最可能被误当作「已在 95 条里覆盖过」而跳过）。验证：T6 规则对其报 0 命中，或显式 `PENDING` + 写明缺口。
- [ ] 1.6 A-1 组一致性检查。验证：26 条 `status` 均非 `PENDING`；`depends:false` 的条目 `derivation` 非空；条目数与 id 集合不变，且分母检查（T7）仍为 104 / 95+9。

## 2. A-2 spec / 文档层数学陈述（15 + 2 = 17 条）

优先判定：`AC-04` `AC-05` `AC-16` `AC-42` `AC-64` `AC-82`。
条目：`AC-04 AC-05 AC-15 AC-16 AC-28 AC-42 AC-46 AC-52 AC-53 AC-64 AC-82 AC-84 AC-85 AC-86 AC-87`。
本桶追加的无实体条目（D9）：`X-D1-07`（治理把 impl-internal frame 钉成规范）、`X-D2-05`（spec 声称的三个实测 gap 两个错、第三个原理上不可能）。

> **本桶已被既有勘误全覆盖**：A-2 勘误节的 E1–E19 + E20 **覆盖了本桶全部 15 条**。按 D8，这些结论**一条都不作为起点**——但它们划定了「该去看哪里」，且其自身锚定 `188b9fb`、测于求积器修复之前，故坐标与数值均需重取。

- [ ] 2.1 逐条三段依赖性判定，17 条完成。**注意本桶主体是 spec 文本而非数值**：`depends` 判据是「该陈述所引用的数值是否由求积路径产生」，而不是「文件是否是 spec」。验证：0.4 检查器对本桶报 0 缺项。
- [ ] 2.2 重测 + 重判，规则同 1.2 / 1.3。验证：新值与 Change 2 归档后的主 spec 实际文本一致（`git show` 而非工作树，见 0.1）。
- [ ] 2.3 **D8 边界**：本桶是转抄风险最高的一桶（勘误 100% 覆盖）。`verdict_evidence` 若引用 `1.1735482746999482` / `1.0205068335735599` / `81.3148` / `82.6036` / `83.7313` 或 `E1`…`E20`，必须同时含独立锚点（`git show <rev>:<path>` / `git grep <pat> <rev> --` / 本 change 自己的复算）。验证：T5 规则对本桶报 0 命中；抽查 2 条证据串能独立复现。
- [ ] 2.4 **已知需独立复核的反向注记**：勘误 E13 断言「任何 `< 1e-6` 的容差都会在 6dp 字面量的真值上失败」。该论断**已被证伪**——`pytest.approx(x, abs=T)` 的实际判据是 `max(T, rel·|x|)` 且 `rel` 默认 `1e-6` 不被 `abs` 关闭，故 `abs=1e-6` 的有效容差是 `1.1735e-6`，而截断误差 `4.259e-07 < 1.1735e-6` ⇒ 不会失败。**本桶不得以该论断为依据**。
- [ ] 2.5 A-2 组一致性检查。验证：同 1.6（17 条）。

## 3. A-3 spec ↔ src 语义偏离（15 + 2 = 17 条）

优先判定：`AC-74`（finding 正文即针对 `_betainc_regularized` 求积循环内的守卫，本次该循环已被重写）。
条目：`AC-14 AC-17 AC-32 AC-35 AC-41 AC-43 AC-44 AC-45 AC-56 AC-73 AC-74 AC-75 AC-76 AC-78 AC-79`。
本桶追加的无实体条目（D9）：`X-D3-01`（公开 API 超出 spec 声称的 totality / 逆映射声明）、`X-main38`（`‖C_t‖₂ = 1` 无条件断言与 Req 19 的次单位范数区自相矛盾）。

- [x] 3.1 逐条三段依赖性判定，17 条完成。**本桶的 `depends` 多数应为 false**（AC-43/44/45/56/73/75/76/78 涉及 loss / config / schedule / extraction / `__all__`，本次未改动）——但「未改动」必须由 0.1 的清单**证明**，不得由印象断言。验证：每条 `depends:false` 的 `derivation` 引用该文件的**内容级**判定（`IDENTICAL` / `CRLF_ONLY` / `CONTENT_DIFF`），**不得引用裸 sha256**——工作树以 CRLF 存储而 HEAD blob 为 LF，裸哈希对若干文件给出假阳性（数量是工作树快照，6 → 10 → 9，非固定值）。 **→ 17/17 完成，`depends:true` 仅 2 条（AC-74、X-D3-01），其余 15 条 `depends:false`。** 每条 `2_chain` 均含 `git log 6593a06..HEAD -- <path>` 的实测结果与内容级判定；`3_line` 给出 HEAD 实测行号。凡涉及 CRLF 文件（`loss.py` / `safeguards.py` / 三份 spec）一律引用内容级判定。**为使本任务可执行，先补齐了 0.1 的缺口**：`baseline.json` 原缺 `src/decompmoe/__init__.py` 与 `src/decompmoe/contracts.py`（AC-78 / AC-45 的「未改动」本无据可依），已在 `build_baseline.py` 的 `TRACKED` 补入这 2 个 + 4 个 A-3 证据测试文件（`test_safeguards` / `test_extraction_phase` / `test_schedule` / `test_contracts`），重跑两次得同一 sha256（幂等 ✅）。**补齐时发现计划未预见的漂移**：`tests/test_safeguards.py`（`e50cc02`）与 `tests/test_schedule.py`（`5a7e48d`、`e50cc02`）**自 pin 起被改过**，而其对应的 `src/safeguards.py` 与 `src/schedule.py` 一次未动——测试与源码的漂移向量不同向。检查器对 A-3 报 **0 `problems`**。
- [x] 3.2 对 `AC-74` 单独重判：旧 finding 描述的「两处数学上不可达的守卫」在新实现里**已不存在**（循环被重写），须判定为 `RESOLVED_BY_UPSTREAM` 并给出「旧守卫位置 → 新实现对应处理」的因果链；若新实现在别处引入了同类不可达守卫，则改判 `STILL_REAL` 并给出新位置。验证：因果链两侧的代码坐标均可用 `git show` 复核。 **→ 判 `RESOLVED_BY_UPSTREAM`。** 因果链：`git grep -n -E 'if t <= 0\.0:|math\.log\(t\) if t' 6593a06 -- src/decompmoe/sphere.py` 端点 2 命中（L117/L120），对 HEAD **0 命中**；删除者是 `e50cc02` + `f6461d7`（`git log 6593a06..HEAD -- src/decompmoe/sphere.py` 返回 2 个 commit，385 行变更 / 311 行插入），机制是 8 点面板 → 8/16 点自适应 + `t = sin²φ` 代换，端点奇异性被解析消去。**audit 的 `基线` 字段标 `unchanged-since-pin`，与该 git 结果直接矛盾——这是本桶唯一的硬错误。** 同类死守卫的**后继观察**已登记（不在 14 条内，本轮不修）：HEAD `sphere.py:218` 的 `if s <= 0.0 or c <= 0.0: return 0.0`，其注释自承「Only reachable at an endpoint, which the quadrature never samples」——**下一轮要清同类死分支，目标应是 L218 而非 L117**。
- [x] 3.3 其余条目重测 + 重判，规则同 1.2 / 1.3。验证：同 1.6（17 条）。 **→ 15 条完成（AC-74 见 3.2）。** `old` 全部取自 `.audit/` 清单正文原文，未取其 `裁决` 字段；`基线`/`裁决` 仅转抄进 `provenance.audit_*_claim`。**复算推翻的 audit 声明（已全部写入各条 `verdict_evidence`）**：(a) `基线` 字段 6/15 是文件级而非子句级（AC-32/35/56 涉 wayfinder spec 被动 4 commit、AC-75/78 涉 skeleton spec 被动 3 commit、AC-44 涉 `loss.py` 被 `969b17c` 改），**仅 AC-79 一条文件级准确**；(b) 行号失效集中在散文/注释/空行：AC-78 pin 21→真值 23（注释行）、AC-32 pin 24→真值 23（空行）、AC-75 pin 36→真值 35、AC-79 pin 288→真值 304（docstring，真实漂移 **+217** 而非其自记的 16）；(c) 数值复算不符：AC-78「76 个公开符号」实为 **75**（13 个子模块 `__all__` 逐个求和 76、去重并集 75，唯一冲突 `flops_per_token` 同时在 `config` 与 `metrics`——**「76」的来源已定位为求和未去重**）；AC-17 坍缩速率与 AC-35 的 `P0=8.83` 均为 harness 特定值，终态一致但中间量不可引用；(d) **AC-32 与 AC-45 是同一条**（`origin_ids` 同为 `main20`+`main58`、同一张 §9 缺口表行，仅按 lens 切分），**两条均未标重复**（对照 AC-41 显式写了「同实体未合并，见 AC-10」）——台账按 104 分母不合并 id，但已在两条 `verdict_evidence` 内互相标注，下游修复只做一次。
- [x] 3.4 **D9 专项**：`X-D3-01` / `X-main38` 无 pin 坐标可继承，D1 第③步必须从零建立。`X-D3-01` 的「2001 点往返闭合」测试需重新设计采样口径才能复现——若建立不出坐标，该条**长期 `PENDING` 并写明缺什么**，不得借勘误补齐。验证：T6 规则对这两条报 0 命中，或显式标注 `PENDING` 与缺口。 **→ 两条均从零建立坐标并判 `DONE`，T6 报 0 命中。** `X-D3-01`：`depends:true`（`canonical_voronoi_angle` 完全经由 `_betainc_regularized` 二分链，`sphere.py:275/293/321/401`）。audit 的两项测量**均不复现**——API 在 HEAD 返回 **83.527956°**（audit 记 84.4738°），且对模型方程 `½·I_{sin²θ}=1/N_e` 满足到 <1e-9（N_e=3/16/64 三点全中）；往返闭合 2001 点中仅 **1** 点超差（最差 2.264e-08），audit 记 1575 点 → 判 `RESOLVED_BY_UPSTREAM`（求积器重写前旧值）。`X-main38`：`depends:false`，坐标 `skeleton spec:149`（req-7 无条件 `‖C_t‖₂=1 within 1e-5`）与 `:471`（req-19 的 `0 < ‖z‖₂ < ε` 次单位区，anchor L456），文本矛盾复现 → `STILL_REAL`；audit 的「无测试走该分支」子项**未复算**，已在 `verdict_evidence` 标为未验证而非已证。
- [x] 3.5 A-3 组一致性检查。验证：同 1.6（17 条）。 **→ 17 条 `status` 均非 `PENDING`；分母检查（T7）仍为 104 / 95+9 ✅。** `check_ledger.py` 全量 `problems: 0`、`outstanding: 87`（A-1 26 + A-2 17 + A-4 18 + A-5 18 + A-7 8 = 87，**均不在本计划范围**），自测 T1–T7 `exit=0`。
  > **修工具时抓到的一个自造缺陷**：T3 原断言 `len(outstanding) == len(entries)`，那是**未开动台账时的巧合**而非它要守的不变量——A-3 判完 17 条后它必然失败，等于「change 一开始干活，控制就不可运行」。已改为守真正的不变量 `len(outstanding) == n_p3 and n_p3 > 0`（outstanding 精确跟踪 PENDING，且台账仍有活要干时才算过），在任何阶段都成立。**已做反向验证**：把 104 条全置 DONE 后 `n_p3=0`，该表达式为 `False` ⇒ 控制仍会红，**不是被改弱**。


## 4. A-4 交叉引用与行号指针失效（15 + 3 = 18 条）

条目：`AC-34 AC-54 AC-59 AC-63 AC-65 AC-66 AC-67 AC-68 AC-69 AC-70 AC-71 AC-72 AC-88 AC-89 AC-90`。
本桶追加的无实体条目（D9）：`X-main36`（wayfinder Req 23 整条由行号断言构成且实指 skeleton req-22）、`X-main73`（wayfinder req-23 跨 spec 交叉引用全写成行号且 Requirement 号错）、`X-main78`（治理条款的行号指针指向错误的 Requirement 块）。

> **归因更正**：原文把行号位移单一归因于「Change 2 重写三份 spec 的大块正文」。实测 pin→HEAD 之间有 **5 个** commit 改过 `openspec/specs/`（`e50cc02` / `315065e` / `4f3e752` / `188b9fb` / `f6461d7`），Change 2 只是最后一个。且漂移不限于指向 spec 的指针——清单「盲区 5」列出的 `touched-since-pin` 共 10 条，其中 **7 条在本 change 范围内且分属 A-1 / A-2 / A-3**：`AC-04` / `AC-05` / `AC-28` / `AC-40` / `AC-60` / `AC-64` / `AC-79`。

- [ ] 4.1 判定本桶的失效机制。按 design.md R5，本桶多为 `invalidation_kind: coordinate`（坐标位移）而非 `numeric`。逐条确认其指向的目标文件是否属于 pin→HEAD 期间被改动的那 5 个 commit 触及的文件，并据此定 `invalidation_kind`。验证：每条 `coordinate` 类都给出「指针声明的行号 → 该行在当前 HEAD 的实际内容 → 正确行号」。
- [ ] 4.2 重算行号指针。**范围不再限于指向 `openspec/specs/**` 的指针**——指向 `src/**` 的指针需先确认目标文件在期间是否被改动（`sphere.py` 已改，其余未改），未改的只做坐标复核不做重判。验证：抽查 3 条按台账给出的新行号能定位到正确文本；并对上述 7 条跨桶漂移项各给出一行结论（它们由 1.x / 2.x / 3.x 判定，本任务只做指针侧记录）。
- [ ] 4.3 重判 verdict。`coordinate` 类的 verdict 表达的是「指针是否已失效」，与数值类不同，不得混用同一套判据。验证：0.4 检查器对本桶报 0 缺项；18 条 `invalidation_kind` 全部非空。
- [ ] 4.4 **D9 专项**：`X-main36` / `X-main73` / `X-main78` 的指针目标须从零定位（清单只给了「最近的本桶条目」，没给行号）。验证：T6 规则对三条报 0 命中，或显式 `PENDING` + 写明缺口。
- [ ] 4.5 A-4 组一致性检查。验证：同 1.6（18 条）。

## 5. A-5 OpenSpec 制品格式、门禁与归档流程（18 条）

优先判定：`AC-19` `AC-20` `AC-80`（**其重判依据待 5.1 现场复现**，见下）。
条目：`AC-19 AC-20 AC-21 AC-22 AC-23 AC-24 AC-25 AC-31 AC-36 AC-49 AC-57 AC-58 AC-80 AC-81 AC-92 AC-100 AC-101 AC-102`。

> **D7 降级**：`design.md` 原把「archive 每份 spec 吞掉恰好 1 个 anchor、丢的是被改 Requirement 之后的那一个」写成既定事实，与本任务 5.1「必须独立复现而非转抄本轮记录」直接矛盾。现降级为**待验假设**：AC-19 / AC-20 / AC-80 在 5.1 复现完成前**一律不得判 `RESOLVED_BY_UPSTREAM`**。

- [ ] 5.1 现场复现归档事故，作为 AC-19 / AC-20 / AC-80 的重判依据。在 TEMP 副本里对一份最小 spec delta 跑 `openspec archive`，记录：是否吞 anchor、吞几个、丢的是不是「被改 Requirement 之后的那一个」、现有 lint 门禁是否对该事故有感。**已有观测是「每份恰好 1 个，且是被改块之后的那一个；两个 lint gate 均 exit 0」，但那是待验假设，必须在独立条件下复现而非转抄。** 验证：复现脚本的输出落盘 `evidence/archive_incident.json`，并与 AC-19 原描述逐句对照，标出原描述未涵盖的可核事实。
- [ ] 5.2 逐条三段依赖性判定，18 条完成。本桶以 `invalidation_kind: provenance`（溯源失效）为主——指向制品完成度、门禁覆盖、目录跟踪状态的条目，其失效来自**流程事件**而非数值。验证：每条 `provenance` 类都指名它依赖哪个流程事件。
- [x] 5.3 重判 verdict。其中「工作树有 **2 个** archive 目录从未提交」（`2026-10-01-audit-errata-a1-numeric-guard-list` 与 `2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard`——后者即本 change 要重判其成果的 Change 2）与「2 个 change 目录的 `proposal.md`/`tasks.md` 在工作树被删而 HEAD 仍追踪」这两条**当前仍成立**，须用 `git status --porcelain` 实测确认而非引用旧记录。~~4 个~~ **→ 已实测更正为 2 个**。验证：实测命令与输出落盘 `evidence/worktree_state.json`。 **→ [2026-10-02 复测] 归档前实测（`evidence/tools/measure_worktree_state.py` → `worktree_state.json`，HEAD `473072e`）：untracked archive 目录现在是 `1 个`而非 2 个——`2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard` 已入库，原计数随之失效；「2 个 change 目录的 `proposal.md`/`tasks.md` 在工作树被删而 HEAD 仍追踪」**仍成立**，实测 4 个文件分属 `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` 与 `fix-review-findings-voronoi-precision-and-lineage`，逐个 `tracked_at_head: true`。**复现脚本首轮报「0 个」是我的分类器坏了**：porcelain v1 是定宽 `XY <path>`，`" D path"` 以空格开头，用 `partition(" ")` 会切出空状态码；已改为 `line[:2]` / `line[3:]` 并加正则交叉校验（两法计数不等即 abort）。**
- [x] 5.4 **自指的缺陷**：本 change 的 `evidence/**` 与 Change 2 归档**当前同样 untracked**——正是 AC-23 / AC-100 的主题。按 D11，本桶在判定这两条时必须把「本 change 自身处于同一状态」写进 `verdict_evidence`，不能只判别人。验证：`evidence/tools/` 与 `evidence/*.json` 的 tracked 状态被实测并落盘。 **→ [2026-10-02] 起测时 `evidence/**` 44 文件已在 HEAD、工作树 49 个，差额即本轮新增产物；Change 2 归档目录已随 `b05c727` 入库（22 文件全 `A`、索引内 0 删除）。同一份 `worktree_state.json` 把「被测对象」与「本 change 自身」并排列出，使 5.4 的自指要求可被机器复核而非散文声明。**
- [ ] 5.5 A-5 组一致性检查。验证：同 1.6（18 条）；且 5.1 的复现结论被至少 3 条引用。

## 6. A-7 wayfinder advisory 层漂移（8 条）

优先判定：`AC-93`（`map.md` 仍写旧 `θ_Voronoi` 叙述）。
条目：`AC-55 AC-93 AC-94 AC-95 AC-96 AC-97 AC-98 AC-99`。本桶无无实体条目追加。

- [ ] 6.1 逐条三段依赖性判定，8 条完成。本桶是 CLAUDE.md §8 三角漂移监控义务的落点：`ticket ↔ spec ↔ src`。判定须回答「该 ticket/map 的陈述是否引用了本次改变的量」。验证：每条判定引用具体的 ticket 或 map 行。
- [ ] 6.2 对依赖者重判。注意 CLAUDE.md §8 的既有纪律：ticket 是 advisory non-binding，但**advisory ≠ 无影响**（经 MVPConfig 默认值 / tests 断言 / reader 复制三条传染通道）。本组须给出「该 stale ticket 当前是否已沿某条通道传染进 `src/` 或 `tests/`」的实测结论。验证：传染结论附 `grep` / `git show` 证据。
- [ ] 6.3 **D8 边界**：本桶的传染结论若引用勘误的票面数字（如 `1.035060` / `1.173547`），必须同时含独立锚点。验证：T5 规则对本桶报 0 命中。
- [ ] 6.4 A-7 组一致性检查。验证：同 1.6（8 条）。

## 7. 收口

- [x] 7.1 登记排除桶。为 A-6（7 条，裁决口径/镜像分歧/先例争议）与 A-8（6 条，`UD-01`..`UD-06`，需用户裁决）写明**排除理由**并落盘 `evidence/excluded.json`；同时记录 A-8 使用 `### UD-` 前缀而非 `### AC-`（本轮曾据此误报「台账缺 6 条」，实为扫描器正则缺陷，台账本身无缺口）。另须登记**盲区 3 / 盲区 4 的 7 条（`AC-06` / `AC-26` / `AC-27` / `AC-29` / `AC-30` / `AC-50` / `AC-51`）实测全在 A-6**，已被排除 ⇒ 对 104 条新范围无影响。验证：源文件分桶 `24+15+15+15+18+7+8+6 == 108` 仍成立（源文件未改）；**分账** = 95 源内 + 9 源外 + 13 排除 = **117 条经手**，其中台账 104。 **→ [2026-10-02] 落盘 `evidence/excluded.json`（生成器 `evidence/tools/build_excluded_index.py`）。条目清单从 `ledger.json :: excluded_items` **读取而非重打**，使登记不可能与它所描述的台账漂移；生成器带两道硬断言——A-6 必须 7 条 / A-8 必须 6 条，以及盲区 3/4 的 7 条**必须全在 A-6**（否则 7.1 的「对 104 条新范围无影响」这句话为假，脚本 abort 而非写出一个好看的报告）。分账实测 `95 + 9 + 13 = 117`，台账 104。**`UD-` 前缀的误报经过已一并登记**：曾因扫描器只匹配 `### AC-` 而报「台账缺 6 条」，台账本身无缺口——已改正的告警仍是证据，故留档。**
- [ ] 7.2 交叉一致性总检，改为**两条独立集合判据**（D9）。验证：(a) **判据一**——95 条源内 ac_id 与源文件实际 `### AC-`/`### UD-` 标题集合**逐字相等**（该断言不因扩容而放松为子集包含）；(b) **判据二**——9 条 `X-` 条目逐条出现在 `evidence/errata_index.json` 的无实体 finding 表中，且**均不出现在**源文件的 `###` 标题集合中；(c) 0.4 检查器全表 `problems` 报 0 且 `outstanding == 0`；(d) 每条 `verdict_new` 要么有 `verdict_evidence` 要么状态为 `PENDING`；(e) 台账中出现的每个数值都能在 `evidence/` 的某个 JSON 里找到出处；(f) 每个 `X-` 条目的 D1 第③步坐标可用 `git show` 复核；(g) 全部 104 条的 `verdict_evidence` 不含无独立锚点的勘误原文指纹（T5）；(h) 分母不变量 104 / 95+9 通过（T7），且 `X-` 与 `AC-` 命名空间不交叉。
- [x] 7.3 交付说明。在 `design.md` 末尾写明：本次**只判定不修复**；新发现的缺陷各需另开 change。**`fix-review-findings-voronoi-precision-and-lineage` 的状态已由 A-2 Errata 的 Dedup 登记裁决为「已 inline 应用未归档」**（其声称改动实测均在工作树生效）——本 change **不重新开启该裁决**，只**复核其在当前 HEAD 仍成立**并登记证据；同时实测记录其 `proposal.md` / `tasks.md` 的工作树/HEAD 状态。验证：该条目在台账中有独立小节，引用的是该裁决 + 本 change 的复核实测，不是「尚未裁决」的旧表述。 **→ [2026-10-02] `design.md` 新增「交付说明（tasks.md 7.3）」一节，五小节：①只判定不修复；②交付边界表（A-3 19 条已判定 / A-1 24 + A-2 17 + A-4 18 + A-5 18 + A-7 8 = 87 条未判定），并点明 `problems: 0` 与 `outstanding: 87` **同时为真且含义不同**——归档记录前者，后者由该节承担；③未归档 change 的独立复核；④派生的 α / β 两个新 change；⑤自指状态。复核走 `evidence/tools/recheck_lineage_adjudication.py` → `evidence/lineage_recheck.json`，**6/6 声称改动在 HEAD 全部命中**，结论「裁决在当前 HEAD 仍成立」。复核同时更正了三处坐标/内容：H2 字面量已由 `1.173548` 改为 `1.173547`（后续 change 刻意换成 canonical 截断值，正合 D1）、H2b 行号 `123/148` 而非 `117/142`、原裁决登记为残留的 L4 缺口**已被别的 change 闭合**（`tests/test_distance.py:88` 现有 `actual=`）⇒ 不继承「不处置」结论。**按 D8，该节不引用原裁决文本作依据，全部坐标在本 change 重新 grep。**
- [x] 7.4 归档门禁 + **入库义务**。**不修改 `.audit/**`**（design.md D6）；`openspec validate --strict` 通过；`evidence/tools/verify_toolchain.py` 全绿；归档后按本仓既有协议复算三份 spec 的 anchor（基线 wayfinder 36 / decompmoe-skeleton 23 / governance 4，100% 覆盖、0 重复），并预期 archive 仍会各吞 1 个 anchor —— 若发生，从 `git cat-file blob` 恢复且**绝不重跑 archive**。**新增（D11）**：`evidence/**` 与 Change 2 归档目录**必须入库**才算交付；提交前必须走**选择性暂存**并以 `git status --porcelain` 复核——`git add -A` 会静默删除 4 个 HEAD 追踪但工作树已失的文件（`2026-09-26-followup-…` 与 `fix-review-findings-…` 两个 change 的 `proposal.md` / `tasks.md`）。验证：两个 lint gate `exit=0`；anchor 复算与基线逐位相符；`git status --porcelain` 显示 4 个 ` D` 未被提交。 **→ [2026-10-02 归档时实测] ① 两个 lint gate `exit=0`（`lint_no_dead_defensive` / `lint_no_source_field_drift`）；② `openspec validate --strict` `exit=0`，输出明写 `skip_specs is set in .openspec.yaml: change declares no spec-level behavior changes, zero deltas accepted`；③ `verify_toolchain.py` 12/12 `exit=0`（CONTRACT 自检 11 声明 / 11 唯一）；④ `check_ledger.py` 自测 T1–T10 全 PASS，`problems: 0` / `outstanding: 87` / `scope ok=True`（95 期望、0 missing、0 unexpected、0 `X-` 在源内）/ 分母 104 = 95+9；⑤ **归档前后三份真相源 spec 的 sha256 逐位相同**（governance `A333F0A3…`、skeleton `10C20A5D…`、wayfinder `6A05178A…`）；⑥ anchor 复算 governance 4 / skeleton 23 / wayfinder 39（唯一 37，`req-17`/`req-20` 为散文交叉引用）——**归档后无一 anchor 被吞**。**D7 的「archive 每份 spec 恰好吞 1 个 anchor」假设对本 change 不成立**，原因是它 `skip_specs: true`、根本不带 delta；该假设只对**带 delta** 的 change 有意义，故 D7 的待验范围相应收窄（带 delta 的 change 仍需复现）。⑦ 4 个 ` D` 经 `worktree_state.json` 实测仍在工作树、`tracked_at_head: true`，选择性暂存后逐条复核未被提交。**故未触发「从 `git cat-file blob` 恢复」分支。

> **[2026-10-02 归档后 · D7 二次确认] 上述「archive 不碰真相源」的结论只对 `skip_specs` 的 change 成立；对**带 delta** 的 change，anchor 吞没每次都发生，已独立复现两次：**
>
> | 归档 | 被改 Requirement | 被吞的 anchor | 真相源变化 |
> |---|---|---|---|
> | α | `governance req-gov-1` | `req-gov-2` | 4 → 3 anchors |
> | α | `skeleton req-6` | `req-7` | 23 → 22 anchors |
> | β | `governance req-gov-1` | `req-gov-2` | 5 → 4 anchors |
> | Change 3（`skip_specs`） | — | — | 无，三份 sha256 逐位相同 |
>
> **规律已经清楚：吞掉的恒是被改 Requirement 之后那一个 anchor，且连带其后一行空行。** 三次都按本任务规定的手术式编辑恢复（补 anchor + 空行），**三次都没有重跑 archive**。
>
> 另有一类**计数上不可见**的损坏：`α` 新增的 `req-gov-5` 整块**没有携带 anchor**。`4 + 1 - 1 = 4` 与 `4 - 1 = 3` 在原始计数上都要靠逐条清单才能分辨，故 `evidence/tools/diff_anchor_inventory.py` 把 `lost`（基线有、现在没了）与 `never added`（ADDED 却从未带 anchor）分开报。
>
> **对本 change 的净结论**：D7 的假设从「待验」升级为**已确认的规律**，且适用范围收窄为「带 delta 的 change」。任何后续带 delta 的归档都必须走同一套流程：apply 前 `snapshot_truth_source.py` → apply 后 `diff_anchor_inventory.py` → 手术式补回 → 复测，且 `5.01e-52` 这类字面量的门禁**不能写成「必须为 0」**（`req-gov-5` 内部有两处刻意的反面示例），只能写成「承重位点为 0、示例位点豁免」。**
