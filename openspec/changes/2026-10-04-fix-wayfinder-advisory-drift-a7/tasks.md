# Tasks: 2026-10-04-fix-wayfinder-advisory-drift-a7

doc-level change：0 spec delta、0 `src/` 改动。扫描范围声明：本 change 的验证 grep **覆盖 `wayfinder/` 全目录 + `openspec/specs/`**，不做 scope-limited 收窄（`2026-09-22-fix-ticket-a5-2-cascading-correction` 正是漏在 scope-limited 验证上，导致同款措辞在 `map.md` 残留至今，见 design.md AC-94 根因）。

---

## 1. `tests/test_sphere.py` — Voronoi 闭式防护（先于文档改动落地）

- [x] 1.1 新增 `_cap_area_fraction_quadrature(theta, signature_dim, *, exponent_offset=0, panels=4096)`：`S^(d-1)` 单极 cap 面积占比 `∫_0^θ sin^(d−2) / (2·∫_0^{π/2} sin^(d−2))`，手写 composite Simpson。**不复用** `sphere._betainc_regularized` / `mpmath.betainc`——同源方法无法证伪自己的参数化。`exponent_offset=1` 切换到 `sin^(d−1)`（`S^d`，大一个维度）作为被拒变体。
- [x] 1.2 新增 `test_cap_area_fraction_matches_direct_quadrature`：`(16,16)` → `pytest.approx(1/16, abs=1e-6)`；`(64,16)` → `pytest.approx(1/64, abs=1e-6)`。失败信息内嵌 `f"actual={share}"`。
- [x] 1.3 新增 `test_cap_area_fraction_rejects_off_by_one_sphere_dimension`：`exponent_offset=1` 在 `(16,16)` → `pytest.approx(0.0563632, abs=1e-6)` 且严格小于 `1/16`。
- [x] 1.4 验证：`uv run pytest tests/test_sphere.py -q -k "cap_area_fraction"` → **2 passed, 28 deselected**。全文件 `uv run pytest tests/test_sphere.py -q` → 见 §6。
- [x] 1.5 验证（characterization test，非 bug-fix）：两个用例断言的是**现状正确性**，首次运行即绿，红绿循环不适用。已在 design.md D3 记录证伪过程。
- [x] 1.6 换行符复核：`test_sphere.py` lf=1528 / crlf=0 / 无 BOM / 单尾换行；`git diff --stat` = **+86 / −0**（纯插入，无既有行改动）。

## 2. `wayfinder/tickets/A5-3.md`（132 → 104 行）— AC-99

- [x] 2.1 **先删 L105–L132**（`N_e=64` v1 孤儿块，28 行）。硬顺序：L81 与被删的 L108 逐字相同，先标注 L81 会造成 `replace_all` 误伤。删除后 `Phase 1: \`β_0 ≈ 1.0\` (γ ≈ -3.5)` 在文件内**唯一**（实测 count=1）。
- [x] 2.2 L42 `β_0 ≈ 1.0` → 追加 `superseded by spec req-7 … (#req-7) closed-form β_0 = 1.035060`
- [x] 2.3 L81 同款 β_0 标注
- [x] 2.4 L68 `20.36° < 52°` → 追加 `superseded by spec req-11 … (#req-11) bisection 67.24°`（L63 的表格标注**不覆盖**这句散文）
- [x] 2.5 L85 `（20.36° < 52°）` → 同款 52° 标注
- [x] 2.6 L63 既有标注规范化：`spec req-11 (4070 MVP Hyperparameter Set)` → `spec req-11 4070 MVP Hyperparameter Set (#req-11)`
- [x] 2.7 验证：`(Get-Content wayfinder/tickets/A5-3.md).Count` = **104**；lf=104 / crlf=0 / 无 BOM / 单尾换行。

## 3. `wayfinder/tickets/A3-2.md`（85 行不变）— AC-96

- [x] 3.1 L45 公式行改写为 `n_i` 形式 + `superseded by spec req-22 Empty-Cell Fallback Invariant (#req-22)` 标注
- [x] 3.2 L49 `加权用 gating 函数 g_i(C_t)` → `加权用 routing 概率 p_i(C_t)`
- [x] 3.3 L50 `死专家保护：Σ_t p_i(C_t) > δ_g 阈值` → `空胞保护（Empty-Cell Invariant）：n_i = |T_i| = 0 时 m_i ≡ c_i^(t−1)`，并补 δ_g 的历史标注（含「不做 `clamp_min(1e-9)` 归一化」的理由，与 spec req-6 的 MUST NOT 对齐）
- [x] 3.4 L51 散文注 → 规范 `superseded by spec req-6 … (#req-6) via change fix-openspec-doc-bugs design.md (Decision 2)` 形式
- [x] 3.5 L84 `δ_g 阈值` → `空胞不变式`
- [x] 3.6 验证：`δ_g` / `g_i` 在 `wayfinder/` 全目录的**裸值命中 = 0 行**（仅存于 `(historical, …)` 标注内部——规范形式要求逐字保留原值，故 A1 断言按「裸值为 0」而非「总命中为 0」判定）。lf=85 / crlf=0。

## 4. `wayfinder/tickets/A6a-2.md`（109 → 110 行）— AC-98 + 清单漏报项

- [x] 4.1 L70 专家权重克隆步加 `superseded by spec req-32 … (#req-32)` 标注。**标注置于代码块围栏之外的同级 bullet**（该行在 ```` ``` ```` 内，行尾追加长散文会破坏代码块渲染），并明示「前 3 步（供体克隆质心 + 协同衰减 β）仍是现行契约」。
- [x] 4.2 L96 `③ f_i 监控 (100)` → `(200)`。依据：同文件 L63 的 `持续 200 steps` + `wayfinder/spec.md`「Eight Geometric Quantification Metrics」内的 200-step history + `decompmoe-skeleton/spec.md` `consec = 200` + `src/decompmoe/safeguards.py:31 DEAD_EXPERT_CONSEC_STEPS = 200`。**清单未覆盖此条**，是本轮新发现的 ticket 内部自相矛盾。
- [x] 4.3 L63 既有标注规范化：`spec req-13 (Numerical Safeguards)` → `spec req-13 Numerical Safeguards (#req-13)`
- [x] 4.4 验证：lf=110 / crlf=0 / 无 BOM / 单尾换行；代码块围栏配对未破坏。

## 5. 既有 10 处标注规范化（补 `(#req-N)` anchor）

- [x] 5.1 `A1-1.md:98` → `(#req-11)`
- [x] 5.2 `A4-1.md:59` → `(#req-7)`
- [x] 5.3 `A6b-1.md:1`（**H1 标题行**）→ `(#req-14)`；逐字复核标题文字 `# A6b-1: 四阶段演进逻辑` 未变
- [x] 5.4 `A6b-1.md:14` → `(#req-14)`
- [x] 5.5 `A6b-1.md:101` → `(#req-11)`；**不补 provenance**（无可核实的 change Decision，见 §7）
- [x] 5.6 `A6b-1.md:133` → `(#req-7)` ×2 + `(#req-14)`；同上不补 provenance
- [x] 5.7 `A8-2.md:70` → `(#req-20-mci)`；`#req-20-mci` 是 `wayfinder/spec.md` 内的**块级 anchor**，已核实存在
- [x] 5.8 `A8-2.md:74` → `(#req-20-mci)`（`replace_all` 覆盖 2 处，实测 count=2）
- [x] 5.9 验证：`wayfinder/tickets/*.md` 内 `(#req-N)` 合计 **20**（10 处既有规范化 + 10 处本 change 新增）。分布：A1-1=1 / A3-2=3 / A4-1=1 / A5-3=5 / A6a-2=2 / A6b-1=6 / A8-2=2。

## 6. `wayfinder/map.md`（109 行不变）— AC-93/94/95

- [x] 6.1 L49 `c_i 4 阶段生命周期` → `5 阶段`；`δ_g 死专家保护` → `Empty-Cell Invariant 保护（n_i = 0 时 m_i ≡ c_i^(t−1)）`。α schedule `0.90→0.95→0.99` 与 spec 一致，**不动**
- [x] 6.2 L54 `θ_Voronoi 25.75°` → 追加 `superseded by spec req-11 … (#req-11) bisection 58.47° at N_e=64, d_c=16`。`g_boundary 0.205` **不动**（无 spec 规范值可依）
- [x] 6.3 L55 `θ_Voronoi≈52°` → 追加 `… bisection 67.24° at N_e=16, d_c=16`
- [x] 6.4 L58 `A6b-1 4 阶段演进` → `5 阶段演进`。**清单未列举**；该链接标签与它自己正文的「**5 阶段 1/5/20/30/44% 时长**」自相矛盾，且 A3 断言要求 map.md 内 `4 阶段` 归零
- [x] 6.5 L66 / L67 数值**一字不动**，追加「WF 工单当时快照」标记；L67 附当前实况 `23 ticket / 36 锚点 / 36 Requirements / 103 Scenarios`
- [x] 6.6 L71 `全部 20 tickets 关闭` → `全部 23 tickets 关闭`（`wayfinder/tickets/*.md` 实测 23 = 21 张 A* + WF-1 + WF-2）
- [x] 6.7 L95 `10 个 arena` 实测正确，**不动**
- [x] 6.8 验证：`4 阶段`=**0**、`20 tickets`=**0**、`δ_g`=**0**；`25.75` 与 `52°` 各 **1 行**（原值与其历史标注同行，裸值随标注消解）；`23 tickets`=1、`10 个 arena`=1。行数 109 不变，**CRLF 保持**（109 crlf；`.gitattributes` 的 `*.md text eol=lf` 保证提交后仍归一为 LF，diff 逐行）。

## 7. 门禁与提交

- [x] 7.1 `uv run python scripts/run_gates.py --change 2026-10-04-fix-wayfinder-advisory-drift-a7` → 见 §7 实测
- [x] 7.2 `uv run pytest tests/test_sphere.py -q` → 全绿
- [x] 7.3 `git diff openspec/specs/ src/` → **0 行**（本 change 不碰规范面与实现）
- [x] 7.4 换行符全量复核：8 个 md + 1 个 py，全部无 BOM、单尾换行；除 `map.md` 保持工作树 CRLF 外全部 LF（Edit 工具未引入 CRLF 污染）
- [x] 7.5 门禁期间零编辑：`run_gates.py` 前后各采样 `HEAD` 与工作树摘要，不一致即 `GATE RESULT INVALID` + exit 2（req-gov-8）。门禁前后均无并发编辑
- [x] 7.6 单 commit on `dev`：`git add <13 条显式路径>`（不用 `git add .`），**不使用 `--amend`**（共享 index）。**不暂存** `wayfinder/tickets/WF-1.md` 与 `src/decompmoe/gating.py`（并行 session 的脏项）
