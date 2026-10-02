# Design

## D1 — 为什么收窄 req-23 而不是反过来让 driver 在 Phase 0 归一化

两条可选路径：(a) 保留「含 Phase 0」并让 `CentroidDriver` 在 Phase 0 做归一化；
(b) 收窄 req-23 为 Phase 1–4，把 Phase 0 的范数前置条件归给调用方。

**选 (b)**，理由是职责边界而非便利性：Phase 0 是 Spherical K-Means 播种，
其数学前置条件是**输入点已在单位球上**——`territory_seeding` 的 deferred contract
已明写 `C_batch ∈ (S^{d_c−1})^T` 是「spherical K-Means mathematical precondition」，
而由「输入已在球面上」推出「输出质心在球面上」是 K-Means 本身的性质，不是 driver
该补偿的错误。选 (a) 会让 no-op driver 变成有副作用的 driver，并使 req-18 现有的
「caller's responsibility」表述自相矛盾。

代价是 Phase 0 失去了一条「谁来保证」的无歧义归属，因此**必须**在 skeleton req-18
侧把该义务升格为显式 MUST（配对 change）。两侧只改一条会留下新的不一致——这是本
change 与 skeleton 侧 change 必须成对落地的原因。

## D2 — `territory_collapse` 为何不设占位函数（与 `territory_seeding` 的有意分歧）

`territory_seeding` 的完整先例是：deferred Requirement + 薄占位函数
（`raise NotImplementedError` 带逐字 spec 指针）+ `__all__` 导出 + 场景测试。
本 change **只做 spec-only**，不设占位函数。

理由：`territory_seeding` 的数学语义是明确的（球面 K-Means，闭式已知），占位函数
只是在替一个已定义的签名占位。`territory_collapse` **没有任何闭式**——spec 未定义
「塌缩」的统计量：是 `max_{i≠j} c_i·c_j`？是 `Σ_i` 的条件数？还是 territory 体积
的退化？占位函数必须声明一个签名，而声明一个未推导的签名，正是本 change 要修的
那类缺陷（req-2 已因 `territory_collapse` 被声明为 MUST 而吃过一次亏）。

因此 req-38 显式写明「specification-only: no placeholder function is mandated,
because the MVP has no closed form for the collapse statistic and a placeholder would
assert a signature whose semantics are not derived」，并把激活路径写成
「先推导闭式 → 再更新本 Requirement → 另开 superseding change」。

**这是有意分歧，不是遗漏。** 记录在此以免下一轮误以为需要补齐占位函数。

## D3 — req-15 的 deferral note 指向已存在的记录而非新承诺

audit 说「spec 正文无 deferral 标注」，字面成立，但缺口比它描述的**窄**：移交
记录已存在于 `tests/test_schedule.py:133-137`（"registered as a hand-off in this
change's proposal"）与引入 Layer 2 的 change proposal。缺的只是 spec 正文一层。
因此本 change 的措辞是「so the spec body is no longer the only place lacking the
annotation」——**不新造一条承诺，只把已有承诺在 spec 里指出来**，避免
「重开一个已经决定过的问题」。

## D4 — 编辑方式：脚本生成 + 块级 diff 回验

req-2 的正文是**单行 1387 字符**。对这样的行做 substring 替换会产生「行尾悬空」
——原句前半已被替换、后半仍留着，而所有 grep 关键字依然命中，检查项全过但文本结构
已坏（这正是审计台账自身踩过的坑）。故本 change：

1. 先跑 **pre-flight**，5 个 needle 必须全部命中才允许写入（打错字也不能留下半改状态）；
2. 每处替换**断言恰好命中 1 行**，命中 0 行或 ≥2 行立即中止；
3. 写完做**块级 `difflib.unified_diff`** 而非 grep 回验；
4. 另跑**失效 token 扫描**，确认旧的 WHEN 子句已消失。

## D5 — 验证时抓到的自造缺陷：anchor 计数把行内散文当成 anchor

写完复核脚本后，它报「wayfinder: anchors=39, duplicates={req-17, req-20}」。第一
反应是 spec 被我改坏了。**用 `git show HEAD:` 对照后确认不是**：HEAD 本来就是
38 个 `<a id=` 命中，其中 L448 与 L866 是**反引号内的行内交叉引用**（"Req 17
(anchored `<a id="req-17"></a>`)"），是刻意的文档而非 anchor 声明。

`build_baseline.py` 统计的是 **standalone** anchor（整行就是 anchor），所以它报
36/36 且 `duplicate_anchor_ids: {}` 是对的；**坏掉的是我新写的复核脚本**——它用了
不过行首锚定的裸正则。修正为 `^\s*<a id="(req-\d+)"></a>\s*$` 后得 37 = 37、无重复、
覆盖 100%。

**教训**：这是「计数器报 0 / 报多的那个是计数器坏了」的镜像形态。零计数与**过计数**
同样危险：它会让人去修一个根本没坏的东西。判据不变——先用第二种检索方式独立确认
（此处是 `git show HEAD:` vs 工作树），再动被测对象。
