# Design

## Context

被审对象：已 archive 的 `2026-10-02-audit-a2-errata-and-spec-math-fixes`（下文称「第一轮」）。它把 A-2 审计桶的 15 条上报缺陷中的 10 条落成了 spec / test / docstring 修改。本 design 记录第二轮 —— **修第一轮自己引入的错误**，不是修 A-2 桶的新缺陷。

第一轮已证明有效的部分（review 复算全部确认，此处不重复论证）：8 个 MODIFIED block 的闭式全部算得对；`33_168 MACs = 66_336 FLOPs` 是正确的 extract_C 总额；`W^O` 消歧、residency 闭式 `65_792 B`、参数计数器 `448_135_680` / `485_097_984` 均正确；`src/decompmoe/sphere.py` 确为纯 docstring（compile + 抹除全部字符串常量的 code-object 比对，798/798 token 相同）。

第一轮的错误集中在**「把一个经验常数写成规范界」**这一类。

## Goals / Non-Goals

**Goals**
- 让每条规范性数值条款在其声明的定义域内**为真**。
- 让每个 spec 里的数值都能被一个测试按 `governance` req-gov-1 的形式直接对账。
- 修好审计链：Source 标签必须解析到被引 design.md 里**真实存在**的 decision。

**Non-Goals**
- 不改任何 `src/` 可执行代码（与第一轮同约束）。
- 不修 `d_c=2` 的求积精度、不修 `x→1` 的求积精度 —— 那些是「声明」而非「修复」，属独立 change。
- 不重开第一轮的 20 条勘误条目（`design.md` D4 表已锁定为权威副本）。

## Decisions

### D1 — governance req-gov-1 的 extraction MAC 字面量同步到四项闭式

req-gov-1 义务 1 与 L46–47 Scenario 仍写 `33_040 = macs(8, 128, 16) = H_kv·(2·d_k·d_c + d_c[bias] + d_c[L2-step2]) + d_c[L2-step4]`，并点名 `tests/test_extraction.py::test_complexity_budget`；第一轮已把该测试改为 `33_168`。

**决策**：义务 1、L46 WHEN、L47 正文中的字面量与分解式一并改为 `33_168 = macs(8,128,16) = H_kv·(2·d_k·d_c + d_c[bias]) + H_kv·d_c[L2-step2] + H_kv·d_c[cross-head mean, step 3] + d_c[L2-step4]`，并同步 `pytest.approx(33_040, abs=0)` 这个举例数字。

**为什么是 MUST**：req-gov-1 是 `CLAUDE.md` §2 层级里的 peer 真相源，且**它点名的正是第一轮改过的那个测试**。不改它，本仓就有两份 spec 对同一 MAC 总额给出不同值 —— 与第一轮要修的「跨 spec 不一致」是同一类缺陷，只是方向相反。

**Source 追加**：req-gov-1 的 `**Source:**` 行尾追加本 change 的 Decision D1 引用。这是本轮**唯一**新增的 Source 引用 —— 因为只有 governance 的规范性数字发生了变动，而「协议不知道数字变了」正是本轮要消灭的缺陷模式。

### D2 — `4·eps` 从普适界降级为 MVP 宽度的经验包络

**决策**：req-19 的 THEN 改为陈述**维度相关**的解析界
`|pow(2).sum(-1) − 1.0| ≤ γ_{d_c} := (d_c−1)·u / (1 − (d_c−1)·u) ≤ d_c·eps`，
并显式写明「**不存在维度无关的常数界**」，附实测证据（对 `4·eps` 的比值在 `d = 512/1024/4096/16384` 分别为 `1.00/1.12/1.75/3.00`×，float64）。`4·eps ≈ 8.88e-16` 保留，但**限定为冻结的 MVP 宽度 `d_c = 16` 的经验包络**，并加 `MUST NOT be generalised`。

**为什么不是「把量词收窄到 `d ≤ 512`」**：那样得到的是一条**经验**条款 —— 它成立与否取决于当前 kernel 实现，一旦有人重写归约实现就失效，而 spec 不会知道。`γ_{d−1}` 是**解析**界：任何逐项求和的实现都满足它，因此 spec 条款与实现解耦。同时保留 `4·eps` 作为 MVP 的紧致包络，是因为 MVP 是冻结的、那个数字确实紧。

**为什么这不只是措辞问题**：`4·eps` 作普适界是**假命题**。一个 MUST 级条款为假，比它不精确严重得多。

**测试必须跟着变**：第一轮的守卫扫 `{8,16,32,128}` —— 恰好是 `4·eps` 绰绰有余的区间，**结构上不可能**发现该失效。新守卫扫到 `d=4096` 并断言 `worst ≤ d·eps`，`4·eps` 只在 `d = d_c = 16` 断言。已实证：把断言换回旧的 `worst ≤ 4·eps`，`d=1024` 与 `d=4096` 立刻转红。

**顺带修**：(a) 同一句里 `(the max(‖z‖₂, ε) denominator equals ‖z‖₂ for ‖z‖₂ ≥ ε)` **逐字重复两次**，删一次；(b) 文本说守卫用 `pytest.approx(..., abs=1e-6)`，而实际断言 `≤ 4·eps`（`8.88e-16`）—— 差约 `10⁹` 倍，改为引用测试名与真实界；(c) Scenario 标题 `Output norm equals 1.0 for ‖z‖₂ ≥ ε` 与正文「MUST NOT be restated as a bare `==`」自相矛盾，改为 `Output norm is 1.0 up to a dimension-dependent rounding bound …`。

### D3 — residency 张量集按逐头 / 均值后分解

req-18 同一句给了两个总数（`1_024 B` 与 `1_600 B`）。

**决策**：`z, ẑ, z̄` 标注为**逐头**（`H_kv·d_c·4 = 512 B` each at MVP），`C` 标注为**均值后**（`d_c·4 = 64 B`），四个张量合计 `3·512 + 64 = 1_600 B`；后一个子句的「at most `1_600 B`」改为「exactly `1_600 B` at MVP」。

**为什么是这个分解**：`extract_C` 的 step-2 是 per-head L2（产出 `H_kv` 个 `d_c` 维向量），step-3 才是 cross-head mean（产出单个 `C`）。所以 `z, ẑ, z̄` 天生是 `H_kv` 份、`C` 只有一份。第一轮写的 `4·d_c·4 = 256 B` 把两者都当成了单份。

**这个错误为什么没被测试抓到**：`tests/test_config.py::test_routing_residency_closed_forms` **用的就是这个正确分解**（`per_head = H_kv*d_c*4 == 512`、`3*per_head + d_c*4 == 1_600`）—— 测试不看 spec 文本，所以 spec 写错它照样绿。教训：**测试钉住的是数学事实，不是 spec 文本的一致性**；两者要分别验。

### D4 — d_c=2 偏差带按开区间重测，并断言 `N_e` 单调性

第一轮写「`3.64%`–`6.41%` relative over `θ ∈ (0°, 90°)`」与「up to `5.39%` (at `N_e = 32`)」，两处都偏低。

**决策**：偏差带改为 `3.63%`–`6.52%`（开区间；最小 `3.6300% @ θ ≈ 81.337°`，最大 `6.5174% @ θ = 89.99999°`）；canonical 角偏差改为**随 `N_e` 单调递增**、给出 `4.780 / 5.238 / 5.359 / 5.389 / 5.397%`（`N_e = 4/8/16/32/64`）、上确界 `5.3994%`。

**第一轮为什么测偏了**：扫描止于 `89.9°`（那里是 `6.41%`），而声明的定义域是开区间 `(0°, 90°)`；`canonical` 只扫到 `N_e=32`，而偏差其实还在涨。**声明的定义域比测量的定义域大** —— 这是可核对的错，不是估计误差。

**为什么上界必须带单调性而不只是数字**：`N_e=32 → 5.3894%` 与 `N_e=64 → 5.3970%` 只差 `0.008` 个百分点，任何固定带宽都盖不住。断言**单调性**才是稳定的那部分：它对精度改进免疫，且能捕捉「上界被归给错误的 `N_e`」这类归属错误。

**顺带说明**：`θ = 90°` 处 `G = θ/π` 精确成立（`x = sin²θ` 命中 `x ≥ 1.0` 早退返回 `0.5`），所以开区间端点**不能**参与 min/max 统计 —— 第一轮的扫描若含 `90.0°` 会得到 min = 0，那是早退平台伪影不是真最小值。

### D5 — Source 的 Decision 标签按 design.md 实际编号校正

第一轮新增的四条 `**Source:**` 引用全部指错。被引的 `2026-10-02-audit-a2-errata-and-spec-math-fixes/design.md` 的决策清单是：D1 追加勘误节 / D2 锚定行号 / D3 勘误互为副本 / D4 19 条勘误对照表 / D5 AC-52 三处联动+allowance / D6 `W^O` 消歧 / D7 Dedup / D8 四个 skeleton Requirement 无 Source 行。

| Requirement | 第一轮写的 | 实际应是 |
|---|---|---|
| req-11 | D4（`W^O` 消歧） | **D6**；tying 反事实属 D4 表 **E10** 行 |
| req-17 | D3（MAC 总额修正） | **D5** |
| req-18 | D5（residency 闭式） | D5 是 FLOPs/allowance；residency 属 D4 表 **E12** 行 |
| req-19 | D5（1:1 收窄 / residency / deferral / 交叉对账） | D4 表 **E11** 行 + **E12** 行 + **D5** |

**决策**：按上表逐条改为真实编号 / 表行号。无法唯一对应到某个 D 的（如 residency），改引 D4 表的 E 行号而非硬套一个 D。

**为什么这条值得单列**：这个 change 的**全部目的**就是让审计可追溯，而它自己写的四条指针全部解析到错误的决策 —— 比没有指针更坏，因为读者会以为已经核对过。

### D6 — 落地用确定性重放 + `archive --skip-specs`，绕开 archive 吞 anchor

第一轮实测：`openspec archive` 的 block 替换区间**不是** anchor 边界规则。当 delta 只携带**非连续** requirement 子集时，它会吃掉主 spec 里紧随其后的 anchor —— 第一轮 8 个 block 丢了 5 个 anchor（wayfinder `req-12`/`req-20`，skeleton `req-3`/`req-8`/`req-20`），并注入 3 个外来 anchor 造成 3 个重复 id。全程 `exit 0`、`validate` 与两条 lint 全绿。

**决策**：本 change 的落地分两步 ——
1. **确定性重放**：按「`<a id="req-N"></a>` 起、至下一个 `<a id=` 前一行止；尾部空行视为分隔符并原样回填」做区间替换，**每个目标 anchor 强制恰好出现 1 次**，每条编辑的 `old_sub` 强制**在目标行内恰好命中 1 次**。
2. **`openspec archive <name> -y --skip-specs`**：只把 change 记录移入 `archive/`，不触发 spec 更新（spec 已由第 1 步落地）。

**为什么不「重跑 archive」**：那是第一轮 9.3 明令禁止的，且在已被污染的基座上重跑会叠加损坏。现在基座干净，但仍不必再冒这个风险 —— `--skip-specs` 让工具只做归档这件它能做对的事。

**验收判据**：重放后的 `git diff --numstat` 必须等于重放脚本按 block 计算出的 del+ins 之和（第一轮经验：两者精确相等即证明重放无遗漏无重复）。此外必须复算 anchor↔heading 配对、重复 id、孤儿 anchor —— 这三项都不是 `exit code` 或 `~ N modified` 能替代的。

### D7 — 派生列必须从 `cfg` 读，禁止硬编码 MVP 常量

`tests/test_extraction.py::test_complexity_budget` 里 `flops_routing = 4*16*8*128 + 2*16*16` 与 `active_core = 8*1024**2 + 2*6*1024*2048` 硬编码了 MVP 维度，而同一函数已持有 `cfg_hkv, cfg_dk, cfg_dc`。

**决策**：全部改从 `cfg` 派生，并补 `active_core == 33_554_432` 的闭式断言（对应 `wayfinder` req-19 的 `8·d_model² + k·6·d_model·d_ffn^Expert`）。

**一个诚实的边界**：`FLOPs_Routing` **没有** spec 闭式（req-19 只要求它「作为独立 line item 报告」），所以它的分解式是**测试自造的**。已在测试里显式标注这一点，避免后人误以为它有 spec 背书。同时 `2 * cfg.N_e * cfg_dc` 写成 `N_e` 而非 `d_c` —— MVP 下 `N_e = d_c = 16` 两者数值相同，原写法因此有歧义；按 gating similarity 的语义应读作 `N_e`。

## Risks / Trade-offs

1. **`d·eps` 比 `4·eps` 松约 `d/4` 倍（MVP 下 4 倍）。** 条款变弱了，但变得**为真**。收紧它需要改 kernel（`torch.linalg.norm` 的内部累加顺序），属行为变更，超出本 change。已把 `4·eps` 作为 MVP 的紧致包络单列，MVP 场景的实际约束力未降低。
2. **行号位移。** 本轮再改两份 spec，仓库内 `req-N L###` 裸行号引用会再次失效。第一轮已实测这类引用的失效半径是**全仓**（含 `src/` docstring 与其它测试文件），不限于本 change 触及的文件。需按 anchor 区间 `anchor_L ≤ ref_L < next_anchor_L` 复扫。
3. **req-6 偏差带随 kernel 改进而变宽/变窄。** 带宽 `0.036..0.0652` 是按「未来精度改进应表现为测试失败」而非「静默通过」选的（沿用第一轮决策）。若将来真去修 `d_c=2` 的求积，这条测试会红 —— 那是正确行为，届时应同步更新 spec 与带宽。
4. **不重跑 archive 意味着 spec 落地不经过工具校验。** 用 D6 的双重复核（numstat 对账 + anchor 复算）补偿。

## Migration Plan

1. 改测试（D2/D4/D7 对应），跑全量确认绿。
2. 脚本生成三份 delta（同一张编辑表，逐条断言唯一命中）。
3. `openspec validate --type change --strict`。
4. 确定性重放到三份主 spec → numstat 对账 → anchor 复算。
5. `openspec archive --skip-specs`。
6. 复跑两条 lint + `validate --specs --strict` + 全量 pytest。
7. 全仓扫 `req-N L###` 裸行号引用，按 anchor 区间校验。

## Open Questions

1. **`d·eps` 要不要换成实现相关的更紧界？** 若 `torch.linalg.norm` 的累加顺序在未来变化，`γ_{d−1}` 仍是上界但可能不紧。要不要额外钉一个「当前实现的最坏实测 vs `d·eps` 的比值 ≤ 某常数」作为回归护栏？本轮未加，因为它对 kernel 改动敏感。
2. **`FLOPs_Routing` 要不要给 spec 闭式？** 现在它是测试自造分解（见 D7）。若它要长期作为 line item 出现在报告里，应当在 `wayfinder` req-19 补一条闭式，否则每次实现改动都要靠测试来定义它。
3. **`archive` 吞 anchor 该不该上游报 issue？** 影响本仓后续**任何**只改部分 Requirement 的 change，且工具自身全绿。已在本 change 的 tasks 里登记。
