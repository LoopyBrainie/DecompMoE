# Proposal: 2026-10-04-fix-wayfinder-advisory-drift-a7

## Why

`.audit/wayfinder-opsx-code-review` 的 A-7 清单列出 8 条 wayfinder advisory 层漂移（`wayfinder/map.md` + 23 张 ticket）。清单本身锁在 **2026-10-01 pin 态**，而 pointer-remediation 在 **10-03 连落 3 个 commit**（`a1f0caa` / `5c49037` / `d61190d`）。因此本 change 的第一步不是照单全收，而是**逐条独立复核**——复核结果推翻了清单 3 处分判，另有 1 条清单漏报。

复核用的是三类独立证据：spec 现行文本、ticket 原文、以及对 A-7 清单的 8 条断言逐条重跑（定位、计数、零落点）。

**污染源头与污染端**：

- `wayfinder/map.md` 自 WF-2 工单（约 2026-09-22）后未再维护：L49 的 `4 阶段` 与 `δ_g` 死专家保护、L54/L55 的 θ_Voronoi 旧值、L71 的 `20 tickets` 全部落后于 spec。map 是 wayfinder 层的导航入口，读者据它判断「还有多少没做」，计数失真会直接污染后续审计的完备性判断。
- `A3-2.md` 的 `g_i(C_t)` 加权 + `δ_g` 门控公式**形状**已被 spec req-6 / req-22 的 Empty-Cell Invariant 取代（非数值漂移，是契约改写）；替换的一半虽由 L51 的散文注记录，但从未写成规范标注。
- `A6a-2.md` L70 的专家权重克隆步 `W_i ← W_{j*} + N(0, 10^-4 I)` 在 spec 内零落点，canonical 单事件 API 结构上不含它。
- `A5-3.md` 三处 `β_0 ≈ 1.0` 未标注（而同值的 `A4-1.md` 已标），两处 `52°` 未被 L63 的表格标注覆盖，且 **L105–L132 是一整块 `N_e=64` 的 v1 残留**，章节号与 MVP 块重复、`容量因数 32x` 与 MVP 的 4.5x 冲突。

**为什么零 spec delta**：全部 6 条仍成立的漂移都是 **advisory 层单向下行**（ticket / map 落后于 spec），规范侧无一处需要改写。`CLAUDE.md` §2 的真相源层级下这是唯一自洽的方向。`src/` 与 `tests/` 的既有契约已是 spec 侧（`MVPConfig.beta_initial = 1.035`、`safeguards.py::DEAD_EXPERT_CONSEC_STEPS = 200`、`_dead_expert_threshold(N_e) = 1/(2·N_e)`），本 change **0 src 改动**。

**清单基线过期的具体后果**（这是「所有标（pin 态）的位置都需按 HEAD 重测」的第一例）：

- AC-55（req-36 逐字误引 ticket，MEDIUM）指向 `wayfinder/spec.md:879` —— **该 Requirement 已不存在**。`a1f0caa` 删除了 req-36/req-37，全库 `L4xx` 指针归零，替换指针 `req-20-mci` 经 anchor 与 3 个 capability 的 7 处引用验证未断链。
- AC-97 声称 spec「证否」了 A6a-2 的供体克隆语义 —— **方向反了**。req-13 → req-28 → req-32 → `safeguards.py` 四层全部同向，是 spec **采纳**了 ticket。
- 复核过程中另有一条清单漏报：`A6a-2.md` L96 写 `③ f_i 监控 (100)`，与同文件 L63 的 `持续 200 steps` 及 `DEAD_EXPERT_CONSEC_STEPS = 200` 矛盾。

## What Changes

0 spec delta，0 `src/` 改动，1 个测试文件新增 2 个用例。

### 1. `wayfinder/tickets/A5-3.md`（132 → 104 行）

- **删除 L105–L132**：`N_e=64` 的 v1 孤儿块。删除后 `Phase 1: β_0 ≈ 1.0 (γ ≈ -3.5)` 在文件内唯一——**这是必须先删后改的硬顺序**，否则标注 L81 时会与被删的 L108 逐字相同而误伤。
- **L42 / L81**：`β_0 ≈ 1.0` → 追加 `superseded by spec req-7 … (#req-7) closed-form β_0 = 1.035060`
- **L68 / L85**：`52°` → 追加 `superseded by spec req-11 … (#req-11) bisection 67.24°`（L63 的表格标注**不覆盖**这两句散文）
- **L63**：既有标注规范化，补 `(#req-11)`

### 2. `wayfinder/tickets/A3-2.md`（85 行，行数不变）

- **L45**：`m_i = (Σ_t g_i(C_t) · C_t) / (Σ_t g_i(C_t) + ε),  if Σ_t g_i(C_t) > δ_g` → `n_i` 形式 + `superseded by spec req-22 Empty-Cell Fallback Invariant (#req-22)`
- **L49**：`加权用 gating 函数 g_i(C_t)` → `加权用 routing 概率 p_i(C_t)`
- **L50**：`死专家保护：Σ_t p_i(C_t) > δ_g 阈值` → `空胞保护（Empty-Cell Invariant）：n_i = 0 时 m_i ≡ c_i^(t−1)` + 标注
- **L51**：散文注 → 规范 `superseded by spec req-6 … (#req-6)` 形式
- **L84**：`δ_g 阈值` → `空胞不变式`

### 3. `wayfinder/tickets/A6a-2.md`（109 → 110 行）

- **L70 之后新增一条 bullet**：`W_i ← W_{j*} + N(0, 10^-4 I)` 步的 `superseded by spec req-32 … (#req-32)` 标注。**标注放在代码块之外**——该行在 ```` ``` ```` 围栏内，行尾追加长散文会破坏代码块；改为紧随围栏的同级 bullet，并明示「前 3 步仍是现行契约」。
- **L96**：`③ f_i 监控 (100)` **保持原值不动**。本 change 初版曾把它改成 `(200)`，后经复核回滚：所依据的 `持续 200 steps`（resurrection 触发窗口）与 spec 的 `UR` 窗口 `W = 100`（`metrics.py::_UR_WINDOW_STEPS`）是**两个不同的量**，而监控频率在 spec 侧无规范值；且原行 `100 / 200 / 1000` 与三个项目本就自洽，改动反而使左列出现不存在的频率。详见 `tasks.md` §4.2
- **L63**：既有标注规范化，补 `(#req-13)`

### 4. 既有 10 处标注规范化（Q3 决策）

`A1-1.md:98` / `A4-1.md:59` / `A6b-1.md:1,14,101,133` / `A8-2.md:70,74`（+ 已在上文处理的 A5-3:63、A6a-2:63）：**只插入 `(#req-N)` anchor 链接**，不改写其余文字。

### 5. `wayfinder/map.md`（109 行，行数不变）

| 行 | 改动 |
|---|---|
| L49 | `4 阶段` → `5 阶段`；`δ_g 死专家保护` → `Empty-Cell Invariant 保护（n_i = 0 时 m_i ≡ c_i^(t−1)）` |
| L54 | `θ_Voronoi 25.75°` 追加 `superseded by … (#req-11) bisection 58.47° at N_e=64` 标注（`g_boundary 0.205` 不动，无规范值可依） |
| L55 | `θ_Voronoi≈52°` 追加 `… bisection 67.24° at N_e=16` 标注 |
| L58 | `A6b-1 4 阶段演进` → `5 阶段演进`（**清单未列举**；该链接标签与它自己正文的「5 阶段」自相矛盾，且计划的 A3 断言要求 map.md 内 `4 阶段` 归零） |
| L66 / L67 | 数值一字不动，追加「WF 工单当时快照」标记；L67 附当前实况 `23 ticket / 36 锚点 / 36 Requirements / 103 Scenarios` |
| L71 | `全部 20 tickets 关闭` → `全部 23 tickets 关闭` |
| L95 | `10 个 arena` 实测正确，**不动** |

### 6. `tests/test_sphere.py`（+86 行，0 删除）

新增 `_cap_area_fraction_quadrature()`（手写 composite Simpson，**不依赖** impl 的 `_betainc_regularized`，独立方法才有钉死价值）与 2 个测试：

- `test_cap_area_fraction_matches_direct_quadrature` — 表值 θ 处直接积分须等于 `1/N_e`
- `test_cap_area_fraction_rejects_off_by_one_sphere_dimension` — 把「应为 `d_c/2`」钉成**被拒变体**（0.9018× 缺口）

## 修复前后对照

| 项 | 修复前 | 修复后 | 规范来源 |
|---|---|---|---|
| A5-3 块结构 | 132 行，尾部 28 行 `N_e=64` 残留 | 104 行 | `A5-3.md` MVP 块自洽 |
| A5-3 `β_0` 标注 | 0/3 | 3/3 | spec req-7 闭式 `1.035060` |
| A5-3 `52°` 标注 | 1/3（L63 表格行） | 3/3 | spec req-11 `67.24°` |
| A3-2 `δ_g` 裸值 | 3 行 | 0（仅存于标注内） | spec req-6 / req-22 |
| A3-2 `g_i(C_t)` 裸值 | 2 行（L45 / L49） | 0（仅存于标注内） | A4-2 决议 `p_i` |
| A6a-2 `W_i` 克隆步 | 裸奔 | 标注 + 明示前 3 步仍现行 | spec req-32 |
| A6a-2 `f_i` 监控窗口 | 100（与 L63 矛盾） | 200 | `DEAD_EXPERT_CONSEC_STEPS = 200` |
| 既有标注 anchor 链接 | 0/10 | 10/10 | req-gov-4 clause 4(a) |
| map `4 阶段` | 2（L49 / L58） | 0 | ticket + spec req-14 |
| map `δ_g` | 1 | 0 | spec req-6 |
| map θ_Voronoi 裸值 | 2（25.75° / 52°） | 0（均带标注） | spec req-11 |
| map ticket 计数 | 20 | 23 | `wayfinder/tickets/*.md` 实测 |
| Voronoi 闭式防护 | 仅 betainc 同源测试 | + 独立积分对照 | 直接积分 |
