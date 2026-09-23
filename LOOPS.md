# DecompMoE Loops

> 本仓库可重复运行的 agent 循环清单。每次跑循环前请确认本文件与项目级 `CLAUDE.md` §1–§9 仍一致。
>
> **范围**：本文件只记录"已确认可跑"的循环契约；新增循环请追加在下方 `## Active Loops` 区。

---

## DecompMoE spec-math audit loop

> **状态**：Active（首次确立 2026-09-17，用户已确认粒度/落盘/权限三选项）

### 目的

针对 DecompMoE 的"**spec 算式 → wayfinder init decision → 代码形式化 → pytest 闭式断言**"完整链路，做系统性的数学一致性审查。重点消除"管功能不管原理"——即 spec 中每个含具体数值的算式必须有 pytest 闭式断言守护，而不是仅靠 shape / finite / finite-difference 检查蒙混过关。

### 适用边界（in-scope）

- `openspec/specs/wayfinder/spec.md`、`openspec/specs/decompmoe-skeleton/spec.md`、`openspec/specs/governance/spec.md` 中所有 `<a id="req-N"></a>` Requirement（CLAUDE.md §6 第 9 条：anchor 100% 覆盖）。
- `wayfinder/tickets/*.md` 全部 23 个 init decision（A0-1 ~ WF-2）。
- `src/decompmoe_skeleton/**/*.py` 及 `tests/**/*.py` 的代码与测试。
- 算式中的具体数值：浮点（如 `θ_Voronoi ≈ 1.1735 rad`、bisection Voronoi 一律 `abs=1e-6`）、整数（如 `N_e = 16`、`k = 2`、`L = 4`、`d_model = 1024`）。

### 适用边界外（out-of-scope）

- 训练执行、baseline 跑分、数据集 pipeline（CLAUDE.md §7）。
- 推理引擎实现代码（spec 算法，code 留给后续 effort）。
- 修改 spec.md 的实质内容——审查产出仅 `.audit/` finding，不直接动 spec。

### Cycle 单元

**每个 cycle 处理一个 Requirement**：

1. **选定**：从 `openspec/specs/<cap>/spec.md` 取一条 `<a id="req-N"></a>`（尚未审计过者优先，按锚点 id 升序或按 `wayfinder/tickets/` 血缘排序）。
2. **取三方上下文**：
   - spec 中对应 Requirement 的算式（含具体数值）
   - `wayfinder/tickets/<ID>.md` 中相关 init decision（**仅作"基线"参考，不作权威**；CLAUDE.md §8）
   - `src/<cap>/` 对应代码 stub（如有）+ `tests/` 对应 pytest（如有）
3. **三轴审计，每 cycle 只做一轴**（轮换推进，避免一次性摊大）：
   - **(a) spec 算式漂移**：spec 中数值是否与 wayfinder init decision 一致？spec 内部算式是否自洽（闭式代入不矛盾）？
   - **(b) 代码形式化一致性**：src/ 中函数签名、维度、归一化、logit 边界、专家混合权重等是否逐字匹配 spec？
   - **(c) pytest 数学闭式覆盖**：含具体数值的算式是否有 `pytest.approx(..., abs=...)`（浮点）或 bare `==`（整数）直接对账？失败信息是否带 `f"actual={...}"`？是否只测了 shape/finite 而未测原理？
4. **写 finding**：追加到 `.audit/spec-math-audit.md`，单行格式：
   ```
   ## YYYY-MM-DD cycle-N req-<id> axis-<a|b|c>
   - **req**：`wayfinder` (or `decompmoe-skeleton`/`governance`) spec.md L<NN> `<a id="req-N"></a>` <标题>
   - **axis**：<a/b/c> — <一句话描述>
   - **evidence**：<重算结果 / pytest 输出 / 文件:行>
   - **proposed fix**：<修改建议指向 OpenSpec change / 修复点>
   ```
5. **验证**：通过重算（如 `python -c "import math; ..."`）或 `pytest tests/test_<算子>.py -k <keyword> -v` 取得数值证据。

### 终止条件（任一）

- 在范围内的 Requirement 都已被审计一轮（即每个 req 至少经过一个 axis）。
- 连续 2 个 cycle 没有新 finding（说明已达稳态）。

### 权限与边界

- **默认只读**：所有代码改动必须单独征得用户同意（CLAUDE.md `GateGuard`）。finding 本身写入 `.audit/spec-math-audit.md` 是被允许的副作用。
- **审计期间可新增**：仅在 `tests/` 下新增 pytest 文件（即 (c) 轴循环可"补齐缺失闭式"），但需明确告知用户。
- **不可触碰**：`openspec/specs/`、`src/<cap>/` 实现逻辑、`openspec/changes/` 历史、`wayfinder/tickets/` 内容。

### Finding 升格路径

- 阈值（暂定，需根据实际密度调整）：
  - 同一 axis 的同类 finding ≥ 3 条 → 触发批量 OpenSpec change proposal
  - 任何"spec 算式与 wayfinder 直接冲突"或"pytest 闭式数学反向被现有测试锁死" → 立即升级为单条 OpenSpec change（紧急）
- 升级流程：`.audit/spec-math-audit.md` 中的 finding → `/opsx:propose` → review → `/opsx:apply` → `/opsx:archive`（archive 前置 lint gate 必须 `exit=0`，CLAUDE.md §3）。

### Cycle 编排建议

- 每轮 3–5 个 cycle，过多易疲劳漏看，过少节奏过慢。
- (a)/(b)/(c) 三轴轮换：(a)→(b)→(c)→(a)…，避免连续同轴形成盲区。
- 暂停条件：发现需先修 spec 才能继续审的情况，停下来，先走 OpenSpec change。

---

## DecompMoE audit-verification loop

> **状态**：Active（首次确立 2026-09-18，作为 spec-math audit loop 的元审计）
> **关系**：本 loop 是 spec-math audit loop 的 **元审计**——不是另开审计，而是对 `.audit/spec-math-audit.md` 里 18 cycles 产出的 finding 本身做**事实验证**。审计循环容易"看起来很重"，但 finding 本身可能因为 (α) Python 重算被外部修改、(β) spec/ticket 文本引用错位、(γ) severity 评级漂移 而失真——verification loop 专门攻击这三种失真。

### 目的

对 `.audit/spec-math-audit.md` 中**每条 finding**（当前共 27+ 条）逐条做事实校核，确保：
1. finding 引用的 spec/ticket 文本确实存在（**grep 命中而非脑补**）；
2. finding 声称的数值闭式在 Python 中**仍可复现**（不强依赖原 cycle 的脚本）；
3. finding 的 severity（MULTIUM/LOW/INFO）评级在元审计视角下**仍然站得住**（不夸大、不淡化）。

### 适用边界（in-scope）

- `.audit/spec-math-audit.md` 中**所有 cycle**的 finding（cycle-1 ~ cycle-18，约 27 条）；
- finding 引用的 spec 行（`openspec/specs/wayfinder/spec.md` L<NN> / `decompmoe-skeleton/spec.md`）；
- finding 引用的 ticket 行（`wayfinder/tickets/<ID>.md` L<NN>）；
- finding 提到的 src/ 文件（仅做"是否仍存在 / 是否仍一致"核对，**不改 src/**）。

### 适用边界外（out-of-scope）

- 修改 spec.md / ticket 内容 / src 代码（CLAUDE.md §3 手术刀原则 + GateGuard）；
- 修复 spec-math audit loop 自身的设计缺陷（属元元审计，不在本 loop 范围）；
- 重写 finding 文本——只追加 verification verdict，不重写原 finding。

### Cycle 单元

**每个 cycle 处理一条 finding**（按 cycle 升序、finding severity 降序轮换）：

1. **选定一条 finding**：从 `.audit/spec-math-audit.md` 中按 cycle-1 → cycle-18 顺序挑选**未验证过**的 finding（severity 优先 MEDIUM > LOW > INFO）。
2. **三轴事实校核，每 cycle 只做一轴**（轮换推进，避免一次性摊大）：
   - **(α) 算术证据复算**：用独立 Python 脚本重算 finding 中引用的闭式（如 `θ_Voronoi(16,16) = 67.24°`、`β_0 = 1.035060`、`MAX_GRAD_PER_C == 32.0` 等），**不照抄原 cycle 脚本**——从 spec 文本/票面值出发重新搭脚本。结论分三类：
     - `VERIFIED` — 复算与 finding 声称数值一致（残差 < finding 声称的 abs 阈值）
     - `DISCREPANCY` — 复算与 finding 声称数值不一致（残差 > 阈值），finding 是**事实错误**——必须升级
     - `NEEDS-SOURCE` — finding 没说复算方法，需打开 spec/ticket 查原文
   - **(β) 文本证据命中**：用 Grep / Read 直接打开 finding 引用的 spec/ticket 行（`spec.md L<NN>` / `tickets/<ID>.md L<NN>`），确认 cited text 真的存在。结论分三类：
     - `CITE-OK` — cited text 与 finding 转述字面一致或语义一致
     - `CITE-MISALIGNED` — cited text 存在但 finding 转述有偏差（夸大/缩小/反向）
     - `CITE-MISSING` — cited line 不存在（finding 引用了过期行号或外部文件）
   - **(γ) severity 评级复核**：结合 α + β 结论复核 finding 的 severity：
     - MEDIUM（如 finding 准确且 actionable）：保留
     - 实际是 LOW（如 finding 准确但影响很小）：降级
     - 实际是 INFO（如 finding 是正面记录或 spec 内部冗余）：降级
     - 实际是 HIGH（如 finding 漏报或夸小，且已传染 src/）：升级
3. **写 verdict**：追加到 `.audit/audit-verification.md`（**新文件**，独立于 `spec-math-audit.md`），单段格式：
   ```
   ## YYYY-MM-DD verify-N finding cycle-M-finding-K axis-α|β|γ
   - **target**：`<原 finding 一句话标题>`
   - **axis**：<α/β/γ> — <一句话描述>
   - **method**：<重算脚本路径 / grep 命令 / spec 行号>
   - **verdict**：<VERIFIED / DISCREPANCY / CITE-OK / CITE-MISALIGNED / CITE-MISSING / severity-up|down>
   - **evidence**：<具体数值残差 / cited text 全文 / 复核后的 severity 评级理由>
   - **follow-up**：<DISCREPANCY → 触发对原 finding 的修正 / CITE-MISALIGNED → 标记 finding 文字微调 / VERIFIED → 正面记录>
   ```
4. **跨 cycle 升格路径**：
   - 同一 finding 的 α+β+γ 三轴 verdict 至少做一次（最少 1 cycle，理想 3 cycle）；
   - 若任意轴 verdict 为 DISCREPANCY / CITE-MISALIGNED / severity-up → 触发"finding 修正 OpenSpec change"（不直接改 finding 文本，仅在 `.audit/audit-verification.md` 中标记 `FLAWED`，等用户决策）。

### 终止条件（任一）

- `.audit/spec-math-audit.md` 中所有 MEDIUM finding 都被 α+β+γ 三轴审计过一遍；
- 连续 3 个 cycle 没有新 verdict（说明已达稳态——所有 finding 都过 α+β+γ 守门）；
- 用户显式 `/loop stop` 或要求切换到其它 loop。

### 权限与边界

- **默认只读**：本 loop **不动**任何源文件（spec / ticket / src/ / tests/）；
- **可新增**：仅 `.audit/audit-verification.md` 一个新文件（独立 verdict 落盘），不修改 `spec-math-audit.md` 原文；
- **可修改**：若 finding 引用了死链/失效脚本，本 loop 可在 `.audit/audit-verification.md` 注明"finding 需重做"，**但仍然不动 finding 原文**；
- **GateGuard**：本 loop 的任何"修正 finding"行为（severity 重评级、CITE-MISALIGNED 文字微调）必须**先报告用户再行动**——默认 verdict 只追加，不修改原 finding。

### 与 spec-math audit loop 的关系

| 维度 | spec-math audit loop | audit-verification loop（本 loop） |
|---|---|---|
| 审计对象 | spec.md / ticket / src/ | `.audit/spec-math-audit.md` 中的 finding 文本 |
| 产出 | `.audit/spec-math-audit.md` 新增 finding | `.audit/audit-verification.md` 新增 verdict |
| 三轴 | (a) spec↔ticket / (b) src/↔spec / (c) pytest 数学闭式 | (α) 算术复算 / (β) 文本命中 / (γ) severity 评级 |
| 触及 spec/ticket | 只读 | 只读 |
| 触及 src/ | 只读（cycle 8 提议补齐 MAX_GRAD_PER_CI 例外） | 只读（**任何情况下不动**） |
| 触及 finding 文本 | 写新 finding | **不修改**原 finding，只追加 verdict |
| GateGuard | 写 finding 即副作用，重大修改需用户同意 | 任何"修正 finding"行为必须先报告用户 |

### Cycle 编排建议

- 每轮 3–5 个 cycle，节奏与 spec-math audit loop 对齐；
- (α)/(β)/(γ) 三轴轮换：同一条 finding 必须至少做 α+β+γ 各一次（最少 3 cycle 才算"verified finding"）；
- 优先级：MEDIUM finding 先于 LOW 先于 INFO；
- 暂停条件：用户决定修正某条 finding，或要求切换回 spec-math audit loop。

---

## Active Loops

- `DecompMoE spec-math audit loop`（上方已展开，状态：Active，18 cycles 完成）
- `DecompMoE audit-verification loop`（上方新展开，状态：**Terminated（用户 `/loop stop` 显式终止 2026-09-19）**, 30 verify cycle 累计完成 — **9 fully-verified + 1 partially-verified = 10 finding 100% 覆盖**, 9 meta-发现)

---

## 修改记录

- 2026-09-17：首次确立 `DecompMoE spec-math audit loop`（粒度=一 req/cycle，落盘=`.audit/spec-math-audit.md`，权限=全只读）。
- 2026-09-18：新增 `DecompMoE audit-verification loop`（粒度=一 finding/cycle，落盘=`.audit/audit-verification.md`，权限=全只读不动原 finding）。两 loop 互补：spec-math audit 产 finding，audit-verification 校核 finding。
- 2026-09-18：verify-1 完成 — cycle-5 MEDIUM finding #1（ticket A5-3 L62 θ_Voronoi 估算漂移 15.24°）axis-α 算术层 VERIFIED：spec 1.1735474259 rad（50-digit mpmath）vs cycle-5 1.1735472572 rad（float64）差 1.687e-7 rad（float64 截断），ticket 52° 反向检验仅覆盖 0.4256% 目标（93.19% 相对欠覆盖）。下一步：verify-2 axis-β 文本命中核对 (A5-3 L62 + spec L185)。
- 2026-09-19: **用户显式 `/loop stop` — audit-verification loop 终止**。30 verify cycle (verify-1 到 verify-30) 累计完成:
  - **9 fully-verified finding** (cycle-5/6/7/9/13/17 INFO+LOW/cycle-1 LOW/cycle-2 LOW/cycle-4 INFO+LOW)
  - **1 partially-verified finding** (cycle-12 CITE-MISALIGNED — 等用户决策 finding 文字微调)
  - **9 meta-发现** (tests pinning / finding CITE-MISALIGNED / TERRITORY_SEEDING 缺失 / Phase 0 NOT IMPLEMENTED / ticket drift cascading / severity 误标 / cross-cycle closure / dormant bug / finding 双重价值)
  - **5 种 finding 类型覆盖** (数值/参数化形式/定义/架构/叙事 wording) + **4 种 severity 覆盖** (MEDIUM/INFO/LOW/NO HARD DRIFT)
  - **6-cycle ticket-stale pattern 同源闭环** (cycle-5/6/7/9/12/13, 4 算法收敛到同一闭式)
  - **建议下一阶段**: 触发批量 OpenSpec change proposal (基于 9 fully-verified + 1 partially-verified findings), 4-file batch fix (ticket A5-3 L62 + A4-1 L58 + MVPConfig L54 + test_beta.py L38)。cycle-12 finding 等用户决策 (选项 A/B/C for finding 文字微调)。
- 2026-09-18：verify-2 完成 — cycle-5 finding #1 axis-β 文本层 CITE-OK×4（spec L184/L185 verbatim + ticket A5-3 L62/A1-1 L97 语义等价，仅 typographical 差异：表格分隔符 `|` vs `=`、全角 `（）` vs 半角 `()`）。双轴 VERIFIED，下一步：verify-3 axis-γ severity 评级复核。
- 2026-09-18：verify-3 完成 — cycle-5 finding #1 axis-γ severity 层 SEVERITY-OK（MEDIUM 恰当：传染链已断于 src/tests/spec 三角，唯一污染是 ticket ↔ spec 单向 stale；不升级 HIGH 因无 src/ 传染，不降级 LOW 因 15.24° 远大于普通估算误差）。**三轴 (α+β+γ) 全 VERIFIED → 第 1 条 fully-verified finding**。下一步：按 severity 优先级 (MEDIUM > LOW > INFO) 选下一条未验证 finding —— 推荐 cycle-6 MEDIUM finding #1 (MVPConfig.beta_initial=1.0 vs spec β_0=1.035)，与 cycle-5/7 同属 "ticket stale 数值源头" pattern，可验证元审计视角下 pattern 同源性。
- 2026-09-18：verify-4 完成 — cycle-6 finding #1 axis-α VERIFIED：50-digit mpmath σ(-3.5)=0.02931223, β_0=1.03506016, MVPConfig.beta_initial=1.0 → 3.39% drift。MVPConfig L51 docstring 自承 "the exact γ₀ is pending a spec-level backfill change" — 已知但未修复。cycle-5/6/7 形成 ticket stale → MVPConfig defaults 同源 family。下一步：verify-5 axis-β 文本命中核对。
- 2026-09-18：verify-5 完成 — cycle-6 finding #1 axis-β 文本层 CITE-OK×3 (spec L122 + MVPConfig L54 + A4-1 L58 全部 verbatim/语义等价)。双轴 (α+β) VERIFIED。finding 精度披露瑕疵 (副产物): cycle-6 evidence 段 σ(γ)=0.02821 vs 50-digit 0.028213166144 — 待 verify-6 axis-γ 复核。下一步：verify-6 axis-γ severity + 精度披露复核。
- 2026-09-18：verify-6 完成 — cycle-6 finding #1 axis-γ severity SEVERITY-OK + **重大发现**：tests/test_beta.py:37-38 显式 assert MVPConfig().beta_initial == 1.0 **LOCKS stale 值** —— cycle-6 当时漏报, 实际 fix chain 是 3-file (config.py L54 + test_beta.py L38 + config.py L50-53 docstring) 而非单点。**传染链结构 ≠ cycle-5** (cycle-5 干净; cycle-6 部分延伸至 tests)。finding 精度披露瑕疵 (LOW): cycle-6 evidence 段 5-6 位有效数字 → 应补 50-digit 声明。**finding #1 三轴 (α+β+γ) 全 VERIFIED → 第 2 条 fully-verified finding**。下一步：跳到 cycle-7 MEDIUM finding #1 (A4-1 β_0≈1.0) — 这是 cycle-5/6 同一 pattern 的 ticket 端源头, 三轴验证可锁死 pattern。
- 2026-09-18：verify-7 完成 — cycle-7 finding #1 axis-α VERIFIED: 50-digit mpmath β_0 = 1.0350601609682665718 vs ticket A4-1 L58 β_0 ≈ 1.0 = 3.39% drift。**跨 cycle pattern 同源确认**: cycle-5/6/7 + verify-7 共 **4 种独立数值算法** (trapezoid + float64 math.exp + float64 sigmoid + mpmath 50-digit Lentz CF) 都收敛到同一闭式 (θ_Voronoi=67.24° / β_0=1.035060), pattern 同源性元审计锁定。**4-file batch fix 建议** (ticket A5-3 L62 + A4-1 L58 + MVPConfig L54 + test_beta.py L38) 可在同一 OpenSpec change 处理。下一步：verify-8 axis-β 文本命中核对。
- 2026-09-18：verify-8 完成 — cycle-7 finding #1 axis-β 文本层 CITE-OK×4 (spec L122/L115 + ticket A4-1 L58 + 数值差 0.035060 全 verbatim 命中)。**跨 finding cited text 复用实证**: spec L122 在 verify-2/5/8 三次独立 CITE-OK, spec L115 在 verify-5/8 两次 CITE-OK —— spec 是稳定真相锚点, ticket 是 stale 源头, CLAUDE.md §2 真相源层级元审计视角 cross-validated。双轴 (α+β) VERIFIED。下一步：verify-9 axis-γ severity + finding 2 σ' 精度复核。
- 2026-09-18：verify-8 完成 — cycle-7 finding #1 axis-β 文本层 **CITE-OK×9** (spec L115/L122/L126 + ticket A4-1 L39/L42/L50/L58/L65-67 + MVPConfig L50-54 全部 verbatim 或语义等价)。双轴 (α+β) VERIFIED。finding 精度披露瑕疵 (副产物, 与 cycle-6 同型): cycle-7 evidence 段 σ'(-3.5) = 0.02845 / σ(-3.5) = 0.02931 vs 50-digit 0.028453023880 / 0.029312230751 — 数值正确但披露精度仅 5/1 位有效数字, 待 verify-9 axis-γ 复核时正式提出。**跨 cycle axis-β 比较**: cycle-5 axis-β (verify-2) CITE-OK×4, cycle-6 axis-β (verify-5) CITE-OK×3, cycle-7 axis-β (verify-8) CITE-OK×9 — cycle-7 引用最多, 因为 finding 是 req-7 12 闭式 + ticket ↔ spec drift 一站式审查。下一步：verify-9 axis-γ severity 评级复核 + 复核传染链 (cycle-7 ticket 端 vs cycle-5 ticket 端 vs cycle-6 src 端, 三者传染链结构对比)。
- 2026-09-18：verify-9 完成 — cycle-7 finding #1 axis-γ severity **SEVERITY-OK** (MEDIUM 评级恰当) + **跨 cycle 传染链结构横向 lock-down**: cycle-5 单点 stale (ticket 唯一污染源) / cycle-6 三级传染 (ticket → MVPConfig → tests LOCKS) / cycle-7 ticket 端源头 (与 cycle-6 是同一条 drift 的两端, 合起来 = 完整因果链)。**CLAUDE.md §2 真相源层级元审计 cross-validated**: spec 是钉死真相 (含完整闭式), ticket 是手算摘要 (信息量少), ticket stale → src/ 单向污染 — **advisory 不等于无影响** 是 cycle-7 相对 cycle-5 的新洞察, 建议更新 CLAUDE.md §8 加一句"ticket stale 仍可能传染 src/, 需以 cycle-6/7 模式监控"。finding 精度披露瑕疵 (LOW addendum, 与 cycle-6 同型): cycle-7 evidence 段精度风格不对齐 (5/1/6 位有效数字 vs spec L122 4 位 narrative 风格)。**3 条 MEDIUM finding 三轴 (α+β+γ) fully-verified** = audit-verification loop 终止条件已满足。**cross-cycle pattern → OpenSpec change 触发**: cycle-5/6/7 形成单一 MEDIUM drift family (ticket stale → src/tests 传染), 阈值 ≥ 3 条同类 finding 已满足, 建议打包成单条 OpenSpec change: 4-file batch fix (ticket A5-3 L62 + A4-1 L58 + MVPConfig L54 + test_beta.py L38) 同一 proposal, 修复后 3 条 MEDIUM finding 同时关闭。下一步: 待用户决策 (a) `/loop stop` 终止本 loop / (b) 启动 spec-math audit loop 续审剩余 LOW/INFO finding / (c) 直接走 OpenSpec change 把 3 条 MEDIUM finding 打包修复。