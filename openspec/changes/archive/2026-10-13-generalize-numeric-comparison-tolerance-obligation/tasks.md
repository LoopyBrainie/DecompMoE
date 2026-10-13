# Tasks

> 范围：FIX-001 + FIX-020（governance req-gov-1 一般义务）。FIX-041 / FIX-042 不在本 change。全部 flip / drift 数字测自 HEAD `dde0e1d` 干净导出（torch 2.12.1+cu130 / pytest 9.1.1）。当前失明快照 = **2/48**（`test_extraction.py:461`、`:540`）。

## 1. 基线证据

- [x] 1.1 把 HEAD `dde0e1d` 干净导出的 48/48 站点 flip 采集结果落盘为本 change 的 evidence（per-site 表：site / atol / |other| / 放行宽度 `1e-5·|other|` / delta_max / FLIP；记录 HEAD sha 与导出方式，满足 req-gov-8「证据须可复算」）。验证：evidence 文件含 48 行、HEAD sha 与 flip 计数 2 可逐行复现。
- [x] 1.2 记录三套度量（当前真翻转 `2/48`、widen 分位数 median `7.344` / `widen<1` `16/48` / `≥100×` `10/48` / `≥1000×` `4/48`、结构分类 `25` 可能 / `23` 不可能 / `19` 已恒等 / `:566` 免疫）与三处 `atol=1e-12` 的 drift（`:461`=`7.450580596923828e-09`、`:540`=`1.1920928955078125e-07`、`:636`=`0.0`）。验证：数字与 design.md Context 表逐项一致。

## 2. 空胞不变式 conformance 修复（`:461`，D4）

- [x] 2.1 在 `src/decompmoe/extraction.py` 的 `CentroidDriver.step` 空胞分支加显式直通 `out = torch.where((n_i == 0).unsqueeze(-1), centroids, out)`，与 skeleton req-16 `:456`/`:473` 的 `torch.where(use_old, prev, normalize(...))` guard 同构。验证：空胞行输出 `== centroids` 逐位相等（`torch.equal` 为真），健康行行为不变。
- [x] 2.2 将 `tests/test_extraction.py:461` 的比较器由 `torch.allclose(..., atol=1e-12)` 升级为 `torch.equal(out[0], centroids[0])`，并把该测试的 `f"actual={...}"` 改为逐位相等的失败信息。验证：`:461` 测试通过且在 mutant（空胞行被扰动）下失败。

## 3. near-zero fallback 测试重建（`:540`，D5）

- [x] 3.1 把 `test_near_zero_candidate_fallback`（def `test_extraction.py:496`）的构造升到 float64（参考先例 `test_full_differentiability` 的 `dtype=torch.double`），使 `mean` 取 `−α/(1−α)·c` 或字面 `−9c`，使 `‖candidate‖ < 1e-9` 以约 7 个数量级余量真正触发 fallback。验证：fallback 行确实进入 `torch.where(use_old, …)` 分支（打桩或断点确认），而非走 EMA 直通。
- [x] 3.2 fallback 行改用 `torch.equal(out[i], centroids[i])`（passthrough 使其逐位保留），健康行走闭式 `normalize(α·c+(1−α)·mean)` + float64-ulp 推导的 `pytest.approx(abs=...)` + `f"actual={...}"`。验证：`:540` 测试通过；skeleton `:409` 的 `Verified by test_near_zero_candidate_fallback` 归属仍成立。
- [x] 3.3 在 `:540` 邻近注释写入 float32 不可达推导（抵消下限 `≈5e-8` > 阈值 `1e-9`，故用 float64 使阈值语义可判），附重算入口，满足 req-gov-5 数字来源三件套（值 / 决定方程 / 重算入口）。验证：注释含该推导且 reviewer 可据此复算。
- [x] 3.4 `:636`（P4，已 drift=`0.0`）比较器由 `torch.allclose(..., atol=1e-12)` 收紧为 `torch.equal`。验证：`:636` 测试通过。

## 4. 负极性站点显式化（8 处，D3）

- [x] 4.1 对 8 处 `assert not torch.allclose`（`test_a3_contract_alignment.py:386`；`test_extraction_phase.py:73/107/124/150/163/195/241`）逐处显式给出 `rtol=`，使负极性断言的真实界被声明。验证：8 处全部含显式 `rtol`；`test_extraction_phase.py:107`（原 `|other|=45.99`、放行带 `4.6e-4`）经测试通过且意图在注释中说明。

## 5. 无容差站点显式化（3 处，Req B）

- [x] 5.1 对 3 处完全不供给容差的站点（`test_extraction.py:566`、`test_extraction_phase.py:241`、`test_gating.py:45`）显式给出至少一个容差；注意 `:241` 同时属负极性（task 4.1），`:566` 运行时 `|other|==0`（结构免疫，给容差不改变判定）。验证：3 处均含显式 `atol`/`rtol`；相关测试通过。

## 6. 全量相对项显式声明（(a) 扩量，D2b）

- [x] 6.1 对剩余 34 处「有 atol、无 rtol」的正向站点逐处补 `rtol=0.0`（AST 定位 + 字节级插入，幂等）。验证：AST 复查 `tests/` 46 处 allclose 全部含显式 `rtol`、0 处无容差；全量 pytest 513 passed 无回归（(a) 安全主张：非翻转站点 `delta ≤ atol`，加 `rtol=0.0` 不转红）。

## 7. 机械门禁（D7）

- [x] 7.1 新增 `scripts/lint_*.py` 无条件卡住「`tests/` 内所有 `torch.allclose` MUST 携带显式 `rtol`；且至少给出一个容差（`atol`/`rtol` 其一）」，经 `run_gates.py` glob 自动发现；不引入豁免注册表。验证：干净树 exit 0；在 HEAD（48 处无 rtol）这一含缺陷树上 exit 非零（自证判别力）。

## 8. 集成复核

- [x] 8.1 在含上述改动的干净导出上重跑 flip 采集，确认「当前真翻转」为 `0/48`，且 `:461`/`:540`/`:636` 三处 `atol=1e-12` 组全部 `delta==0`（逐位恒等），落盘 `evidence/flip-post.md`。验证：新 flip 表 FLIP 计数为 0。
- [x] 8.2 全量 `pytest` 通过（无回归），并复核 8 处负极性与 3 处无容差站点在显式容差下仍表达原意图。验证：`pytest` exit 0。

## 9. 独立审计整改（2026-10-13）

- [x] 9.1 修正 `:540` docstring 的 float32「不可达」假命题：实测 5000 seed 触发率 12.16%（608/5000，其中 570 恰为 0），真因是 margin 随 seed 波动而非不可达；`~5e-8`/`2.2e-07`/`3.3e-08` 均改为实测值。验证：docstring 与 `design.md` D5 表数字一致且可复算。〔基线：torch 2.12.1+cu130 / pytest 9.1.1，seed 0–4999 × d_c=3〕
- [x] 9.2 补 spec 常数 `1e-9` 的双侧对账（新增 expert 3 判别行，candidate ~1e-8 ∈ (1e-9, 1e-3)）。验证：变异 `1e-9→1e-3` 与 `1e-9→1e-18` 均转红（修复前 `1e-9→1e-3` 全绿未检出）。
- [x] 9.3 纠正两处**放松**守卫的修复：`test_gating.py:45`（放松 100×）与 `test_extraction.py:566`（放松 10×）改 `torch.equal`。验证：两处实测 `delta=0.0`、`torch.equal` 为真。
- [x] 9.4 补回 4 处 `f"actual={...}"`（违反 req-gov-1 obligation 5 与本 change 自身验收标准）。验证：`:464`/`:565`/`:620`/`:692` 逐条带 `actual=`。
- [x] 9.5 补 `tests/test_lint_no_implicit_relative_tolerance.py`（仓内惯例：每个 lint 配一个测试）。验证：12 项 lint 测试全绿。
- [x] 9.6 把 lint 覆盖面扩至 Req A 一般措辞（`torch.testing.assert_close`/`np.allclose`/`torch.isclose`/`math.isclose` + 模块别名解析）。验证：自检 10 例全过；干净树 exit 0 / HEAD exit 1。
- [x] 9.7 解 `lint_no_baseline_counts` GATE BLOCKER（8 处计数缺 baseline）。验证：给计数行内联 `〔基线：evidence/flip-baseline.md @ dde0e1d〕`，lint exit 0。
- [x] 9.8 修正 `evidence/flip-post.md` 与 `proposal.md` 的 `pytest.approx(rtol=)` 硬错误（该 kwarg 不存在）。验证：改为 `torch.allclose(atol=..., rtol=0.0)`，与代码一致。
- [x] 9.9 钉住 req-17 的 `10⁻¹²` 常数：`:461` 与 `test_extraction_phase.py` 的空胞测试各增一条 `‖Δ‖₂ < 1e-12` 显式对账，与 `torch.equal` 恒等守护**并存**。验证：删 passthrough（M1）时两处均转红。
- [x] 9.10 修复 `#13` 死代码盲区：passthrough 使 `:164` 空胞 `mean` 选择对输出不再 load-bearing，新增 `test_empty_cell_mean_selection_is_structural`（AST 结构守护）钉住 req-18 的 `m_i ≡ c_i^(t-1)`。验证：变异 M9（删该行）由全绿转红。
- [x] 9.11 记录 `#12` autograd 语义变更（空胞行 Jacobian `[0.402,0.116,1.270]` → `[1,1,1]`），注明 req-18 EMA 三阶段 gradient channel Frozen 故 spec 中立。验证：design.md 已录。
- [x] 9.12 修复 `#9` 条文张力：新增 Req D「Tensor Closed Form Is Guarded By An Explicit Relative Term」，声明 `torch.allclose(atol=X, rtol=0.0)` 为张量闭式的等效形式（`pytest.approx` 的 `ApproxNumpy` 路径返回裸 bool、丢 `actual=`、不查 dtype/shape）。验证：`openspec validate --strict` valid。

## Workflow follow-up

- 落定工作树后跑 `run_gates.py --change generalize-numeric-comparison-tolerance-obligation`，取得 exit 0（脏树会 `GATE RESULT INVALID` exit 2）。
- 交 reviewer 裁定 `torch.equal` 与 req-gov-1 obligation 2 的关系（design.md D6，附 4-decimal display exception 类比）。若否决 float64 构造，触发 design.md D9 回退到替代方案 (ii)（追加 `decompmoe-skeleton` delta 修 `:409`），而非 (i)。
- 归档本 change（spec delta 并入 `governance` 主 spec，新增三个 anchor），并按「写账本 → 归档 → 比对 → 手术式补回 → 复测」执行（req-gov-10）。
