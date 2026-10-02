# Tasks

- [x] 1.1 F1 HIGH — skeleton req-7 前置条件改到跨头均值。验证：构造 4 正 4 负的精确抵消（`proj_W_V[h,0,0]=1`、`proj_b=0`、前 4 头 `+1` / 后 4 头 `−1`），确认 per-head 范数全为 1.0（**旧条件满足**）而 `extract_C` 返回 `‖C_t‖₂ = 0.0`。**→ 完成，条件改为 `‖z̄_t^l‖₂ ≥ ε` 并把该反例写进 Scenario。**
- [x] 1.2 F2 HIGH — wayfinder req-32 补 `c_centroids`。验证：全 spec grep `resurrect_expert(` 共 4 处调用点，`:753/:778/:788` 已含该参数、`:774` 缺；补后 4/4 一致，且旧写法 `resurrect_expert(i=3, j_star=0, β_per_expert, cfg)` 在 6 项 stale-token 扫描中零残留。**→ 完成。**
- [x] 1.3 F3 MED — `UR` 的聚合口径进 spec。验证：req-20 新增 Scenario 写明窗口并集、单步闭式 `3/16`、以及「激活集恒定时两读法不可区分」。**→ 完成（此前只存在于测试 docstring）。**
- [x] 1.4 F4 MED — 推翻并更正初稿的假对立。验证：200 步 fixture 在并集与逐占比均值下**都**给 0.125（激活集窗口内恒定）；`0.0625` 追到 `wayfinder/tickets/A8-2.md:93`（per-expert `f̄_i^(100)` 的健康值）。**→ 完成：C4 `design.md` 追加「D5 更正」保留推翻过程，`proposal.md` 同步，台账 AC-41 的 `old`/`new`/`method` 同步更正（`verdict_new`/`status` 不动）。**
- [x] 1.5 F5 MED — `A8-2.md:38/93` 漂移注释。验证：按 `CLAUDE.md` §8 的 `(historical, …; superseded by spec req-20 …)` 形式注明 ticket 的 UR 是 per-expert 量、其 `< 1/32` 在现行 spec 下是弱得多的信号、且复活触发实际走 req-13 的 `f_i^avg`。**→ 完成。**
- [x] 1.6 F6 MED — `UR` 拒绝 `ndim ≥ 3`。验证：`(200, 5, 16)` 中行 0–149 只激活专家 3、行 150–199 只激活专家 11，旧实现返回 `tensor([0.1250]×5)`（`UR(b3[:150])` 应为 `0.0625`）⇒ 整批行被丢。新实现抛 `ValueError`；`(N_e,)` 与 `(T, N_e)` 仍接受；list 形式的 3-D 元素也在拼接后被拒。**→ 完成。**
- [x] 1.7 F7 MED — `governance` req-gov-1 假推导。验证：`approx(134_217_728, abs=0).tolerance == 0.0`、`3.0 + 1e-13 == approx(3.0, abs=0)` 为 `False`、`DEFAULT_RELATIVE_TOLERANCE == 1e-6`。**→ 完成：obligation 1 与 obligation 3 的推导换成版本无关的陈述，3 处 Scenario 的 `rel=1e-6 magnitude-scaling` 措辞一并更正；我自己的 test docstring 同步更正。规则本身（整数闭式用裸 `==`）不变。**
- [x] 1.8 F8 LOW — 数值断言的失败信息补 `actual=`。验证：`test_a3_contract_alignment.py` 的 `__all__` 去重断言、λ 调度差异断言、`UR([])` 断言，以及 `test_extraction_phase.py` 的坍缩与范数断言。**→ 完成。**
- [x] 1.9 F9 LOW-MED — AC-79 守卫换性质断言 + 补 Generator 设备。验证：源码确认原实现是 `torch.Generator().manual_seed(...)` 配 `randn(..., device=centroids.device)`——**只给 `randn` 加了 `device=`，Generator 仍在默认设备**。改为 `torch.Generator(device=centroids.device)`；守卫从 `"device=centroids.device" in src` 换成 AST 断言（`Generator`/`randn`/`rand` 每处必须带 `device=`，`.manual_seed` 排除）。**→ 完成。CUDA 行为半边 `skipif` 且写明理由：本机无 GPU 时该缺陷不可达。**
  > **自造缺陷**：第一版 AST 守卫把 `.manual_seed(...)` 也纳入规则，跑测试立刻报出 `torch.Generator(device=centroids.device).manual_seed(VORONOI_AREA_SEED)`「缺 device」——它是已绑定设备的 Generator 上的方法，正确代码被拒。规则收窄后通过。
- [x] 1.10 F10 LOW-MED — AC-17 的 characterization 常数补闭式护栏。验证：999 步循环内**逐步**断言 req-18 Invariant 2 的 `max|‖c_i‖₂ − 1| < 1e-6`（原测试完全没查这一条）与「任意两步无两质心重合」。**→ 完成。characterization 值 `1.421196 / -0.023137` 保留并标注为 change-detector；被删分支的 5999 步数字标注为不可复现散文。**
- [x] 1.11 测试强度 — dense mask 与 `n_i = 0`。验证：dense fixture 取 `n_i > 1` 使 `clamp_min(1.0)` 成为 no-op，并断言「除法承重」与「列和不等」；方阵 fixture（`T = N_e = 4`）断言列索引读法与行索引读法给出不同结果（矩形 mask 下换轴会抛形状错，只有方阵能藏住该 bug）。`n_i = 0` 测试断言空胞专家**完全不动**（req-18 Invariant 1）且有 token 的专家**确实动了**。**→ 完成。**
  > **自造缺陷 2**：第一版「转置 mask 对照」写的是恒等式（`mask.T @ X` 的第 e 行就是 `Σ_t mask[t,e]·X[t]`，与正确读法**完全相同**），断言立刻以 `max|diff| = 2.98e-08` 失败。改成方阵 + 行/列双读法才对。
  > **自造缺陷 3**：新 fixture 先按行和归一化，导致部分列和 `n_i < 1`，驱动的 `clamp_min(1.0)` 生效而与「纯除法」期望分叉（差 ~0.002）。改为 `torch.rand + 1.0` 并显式断言 `n_i > 1`，把 clamp 变成 no-op；该 clamp 行为本身记录在 design.md D6，**本轮不修**。
- [x] 1.12 delta 生成与回验。验证：5 个块全部从主 spec 抽取原文；每处替换**断言命中恰 1 次**；块级 `difflib` 逐行 diff = req-20 (+32 −3)、req-28 (+1 −1)、req-32 (+2 −2)、req-7 (+1 −1)、req-gov-1 (+3 −3)；6 项 stale-token 全过。**→ 完成。**
- [x] 1.13 门禁。验证：`pytest` **262 passed + 1 skipped**（255 + 新增 8 − 重写 1，skip 为无 GPU 的 CUDA 行为半边）✅；`lint_no_dead_defensive.py` exit=0 ✅；`lint_no_source_field_drift.py` exit=0 ✅；spec 形状 37/23/4 无重复 ✅；`check_ledger.py` 自测 T1–T7 exit=0 ✅；change `validate --strict` ✅。
- [x] 1.14 归档后回验。**→ 归档损坏比预期严重，改走确定性重放（补记）。**
  - 直接 `openspec archive` 的实际破坏：**3 个 anchor 被整行删除**（skeleton `req-8`、governance `req-gov-2`、wayfinder `req-35`）**+ 2 个 wayfinder anchor 被移到错误位置**（`req-28`、`req-32` 各出现两次）——后者比删除更危险，裸计数看不出结构损坏。另有 4 处空行插进了未改动块。
  - 处置：`git checkout -- openspec/specs/` 复位到 HEAD → 按区间**确定性重放** delta（每个目标 anchor 断言恰好出现 1 次；按**行**索引替换，不是字符切片）→ `openspec archive --skip-specs` 只搬 change 记录。
  - 重放后三道判据全过：① spec 形状 **37/23/4、无重复 id、三份均纯 LF**；② **没有任何 `<a id=...>` 行发生变动**；③ 全部改动**只落在** req-20/req-28/req-32（wayfinder）、req-7（skeleton）、req-gov-1（governance）三个目标块内。
  - **numstat 声明值作废**：1.12 声明的行数取自**过滤掉空行**的 diff，空行在该基下不可见，与真实 numstat（wayfinder +36/−8、skeleton +1/−2、governance +3/−4）对不上。改用上述内容级判据——「改动是否被限制在目标块内、anchor 是否完好」才是能判真伪的指标，行数不是。
  > **本任务自造的 3 个缺陷**（都是脚本/门禁本身的错，不是 spec 的）：① `spec_shape.py` 的 `f"{dup or 'none':6s}"` 在 `dup` **非空**时是 dict 格式化崩溃——它此前一直能跑，只因为从未真的出现过重复 id，等于「有重复时门禁自己先崩」；② 重放脚本第一版用 `text[:s]`（**字符**切片）配**行**号 `s`，把新块插进了文件首行中间；③ 修 ② 时把 `write_bytes` 误放到替换**之前**，于是校验全过而文件根本没变——numstat=0 才是发现它的信号。**三者的共同形态：门禁/脚本的「通过」不等于被测对象正确，必须让判据作用在产物上。**

