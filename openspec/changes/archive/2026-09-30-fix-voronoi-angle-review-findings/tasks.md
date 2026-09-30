# Tasks — `2026-09-30-fix-voronoi-angle-review-findings`

> `[x]` 只在对应校验**实测通过**后写。门禁类任务在跑完前保持 `[ ]`。

## A. BLOCKER 1 — `θ_conv` 伪影

- [x] A.1 解析推导 `G''` 闭式并与 mpmath 50 位 FD 对账（12 位有效数字一致）→ 确认 `G'' > 0` 恒成立，`(0, π/2)` 无零点
- [x] A.2 三方对照（解析 / 真实 beta 的 FD / 仓库 8 点 GL 求积）定位三个 `θ_conv` 为求积符号翻转点
- [x] A.3 `sphere.py` docstring 凸性段重写：给出闭式、删分支表、前提降为 `∀i: A_i < 0.5`
- [x] A.4 docstring 增加「不要用 `_cap_area` 有限差分读曲率」警告
- [x] A.5 `decompmoe-skeleton` req-6 delta：凸性前提改为「`G` 严格凸 ⇒ `A_i < 0.5`」
- [x] A.6 `wayfinder` req-11 delta：指针措辞点名真实前提
- [x] A.7 `governance` 无关段落不涉及（A 只改前两份 + docstring）

## B. BLOCKER 2 — 同义反复测试

- [x] B.1 删除 `test_voronoi_angle_convexity_boundary`
- [x] B.2 删除 `_cap_area_second_derivative` / `_convexity_boundary`
- [x] B.3 新增 `_cap_area_d2_closed_form`（`math.gamma`，零新增依赖）
- [x] B.4 新增 `test_voronoi_angle_precondition_is_area_below_half`（三段断言，含已退役 `θ_conv` 上方的回归守护）
- [x] B.5 `tests/test_sphere.py` 全绿（23 passed）

## C. HIGH 3 + HIGH 4 — σ 推导

- [x] C.1 确认 `Σ_i n_i = M` 恒成立（`bincount` 单一 M 点集，每点唯一 owner）
- [x] C.2 推导一阶项恒消、二阶主导、`Var(Σε_i²) ≈ 2N_e(A(1−A)/M)²` ⇒ `1/M` 标度
- [x] C.3 闭式 `σ = 1.461e-5°`、`5σ = 7.31e-5°`
- [x] C.4 跨 seed 实测互证：8 seeds SD `1.353e-5°`（闭合形式到 ~8%）
- [x] C.5 `governance` obligation 7 正文：推导改写 + 「当独立会得 `0.0355°`，大 `486×`，MUST NOT be reintroduced」负面锚点
- [x] C.6 `governance` Scenario：`28×` → `13.7×`，cross-seed `8.6e-5°`(4 seeds) → `4.20e-5°`(8 seeds)
- [x] C.7 `governance` Scenario：单侧性 gap 倍数 `756/319/70σ` → `3.7e5/1.6e5/3.4e4×`
- [x] C.8 `decompmoe-skeleton` req-6 Scenario：同上 σ 倍数同步
- [x] C.9 `sphere.py` docstring 误差预算重写 + 记录被取代的 `0.0071°`
- [x] C.10 `_VORONOI_MC_5SIGMA_DEG` `0.0355` → `7.31e-5`，推导 docstring 重写
- [x] C.11 其余 3 个测试的 `5σ` 注释同步

## D. MEDIUM 5 / 6 / 7

- [x] D.1 MEDIUM 5：实测零面积胞腔（`areas = [250678, 249432, 249392, 250498, 0, 0, 0, 0]`）
- [x] D.2 MEDIUM 5：**授权而非抛错**（抛错会推翻 req-6 既有 one-sidedness Scenario）→ 写进 req-6 + docstring
- [x] D.3 MEDIUM 6：新增单位范数校验 `atol=1e-6`，`ValueError` 点名行号 + 修复建议
- [x] D.4 MEDIUM 6：req-6 delta 写入契约
- [x] D.5 MEDIUM 6：新增 `test_voronoi_angle_rejects_non_unit_centroids`
- [x] D.6 MEDIUM 7：probe 块 `.to(centroids.dtype)`，float32 数值路径不变
- [x] D.7 MEDIUM 7：req-6 delta 写入契约
- [x] D.8 MEDIUM 7：新增 `test_voronoi_angle_honours_centroid_dtype`（回归守护）
- [x] D.9 实测 `float32` / `float64` 输出逐位相同（`1.5707963267948966`）

## E. LOW 8 / 9 / 10 + 界收紧

- [x] E.1 LOW 8：docstring 峰值改 `+31.5863380965°` @ `38.9424412690°`（精确值经 mpmath 复算）
- [x] E.2 LOW 9：`test_voronoi_angle_reflected_cap_branch_n_e_2` 改 spy `_cap_radius`，断言 `A_i > 0.5` 且 `r > π/2`
- [x] E.3 LOW 9：删除无法区分分支的 `approx(90.0)` 断言
- [x] E.4 LOW 10：不改 archived 字节；在本 `design.md` 记 supersession 表
- [x] E.5 界收紧：`test_voronoi_measurement_layer` `1.0°` → `0.2°`（真实 gap `0.0399°`，5× 余量）
- [x] E.6 `governance` Scenario 的 commensurability 界 `1.0°` → `0.2°` 同步

## F. 门禁

- [x] F.1 `openspec validate <change> --strict` → `Change ... is valid`
- [x] F.2 `python scripts/lint_no_dead_defensive.py` → `exit=0`（archive 后复跑）
- [x] F.3 `python scripts/lint_no_source_field_drift.py` → `exit=0`（archive 后复跑）
- [x] F.4 `openspec archive` 后复跑 anchor 覆盖计数：**63 Requirement / 63 anchor / 0 缺锚**（archive 前基线相同）
- [x] F.5 全量 pytest：`214 passed`；唯一 failure 为 `tests/test_config.py::test_total_param_estimate`（`actual=452331008` vs `452_329_984`），源自并行 session 未提交的 `src/decompmoe/config.py` 改动，与本 change 无关
- [x] F.6 换行复核：三份 spec 与两个源文件 CR 字节数均为 `0`（`openspec archive` 曾写入 CRLF，已归一化回 LF）

## G. archive 后补救（吞锚 + 换行）

archive 复现了已知的 MODIFIED-block 边界缺陷：每个被改的 Requirement 恰丢 1 个 anchor，
且永远是紧随其后的那个。本次丢 `req-7` / `req-12` / `req-gov-2`（63 → 60）。已按
「空行 / anchor / 空行 / heading」恢复，并复跑计数确认 63/63、0 缺锚。

`openspec archive` 同时把三份 spec 写成 CRLF（HEAD 为 LF，CR 637/891/171）。已按字节归一化回 LF；
若不复核，`git diff` 仍可能显示为整文件重写而非真实增量。

## 记录

- 复算脚本（系统 temp，不入库）：`check_theta_conv.py`（BLOCKER 1 三方对照）、`fix_numbers.py`（σ / 峰值 / 运行时 / 零面积 / dtype）、`seed_spread.py`（crosspolytope 跨 8 seed 分布）。
- **σ 的三重互证**：闭式 `1.461e-5°`；`eye(16,16)` 跨 8 seed 实测 SD `1.353e-5°`；crosspolytope(32) 跨 8 seed 实测 SD `1.533e-5°`（吻合到 5%）。
- 数值路径变更范围：仅 MEDIUM 6 的新错误路径与 MEDIUM 7 的 dtype 回归修复；float32 前向逐位不变。

