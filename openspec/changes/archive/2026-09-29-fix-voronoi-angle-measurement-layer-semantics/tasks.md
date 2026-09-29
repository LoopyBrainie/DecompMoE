# tasks.md

> 勾选状态纪律：本文件落盘时，验收项一律按**已实测**的结果标记。`[x]` 只在该项对应命令实际跑过并通过后才写；未跑的一律 `[ ]`。本文档被后续 audit 与 reviewer 当作事实来源，假的 `[x]` 会作为「曾经声称已完成」的记录进入 git 历史。

## A. 制品

- [x] A.1 `openspec/changes/2026-09-29-fix-voronoi-angle-measurement-layer-semantics/.openspec.yaml`（`schema: spec-driven`，**无** `skip_specs`——本 change 有真实 spec delta）
- [x] A.2 `proposal.md` — Why（含缺陷实测表 + 「最近邻不是正解」的排除性实测）/ What changes / Out of scope / Impact / Capabilities / Source back-link
- [x] A.3 `design.md` — Decision 1 承载完整数学推导（Jensen 蕴含链 + 凸分支前提 + 逐胞腔反退化论证 + 统计误差预算 + 被取代反解误差的闭式订正），满足 `CLAUDE.md` §6 末条
- [x] A.4 `specs/decompmoe-skeleton/spec.md` delta（req-6 MODIFIED，契约句 + 2 新 Scenario；**不**新增 Source——该 Requirement 本就没有 Source 字段）
- [x] A.5 `specs/wayfinder/spec.md` delta（req-11 MODIFIED，契约句 + Source 追加 change 引用，主反链 `wayfinder/tickets/A5-3.md` 保持首位）
- [x] A.6 `specs/governance/spec.md` delta（req-gov-1 MODIFIED，obligation 7 + obligation 5 适用范围 + 1 新 Scenario）
- [x] A.7 `tasks.md`（本文件）

> A.4-A.6 的 MODIFIED 块由 `_tmp_make_deltas.py` 从**主 spec 原文机械提取**后仅替换目标从句生成，不手工转写 2602 字符的 Requirement 正文。

## B. 实现

- [x] B.1 抽出 `_cap_area(θ, d_c)`（含 `θ > π/2` 反射分支）与 `_cap_radius(area, d_c)`（`(0, π)` 二分反解）
- [x] B.2 `canonical_voronoi_angle` 改为委托 `_cap_radius(1/N_e, d_c)` — **实测零回归**：`(16,16)` 仍为 `1.1735482746999482`，6dp 差 `2.747e-7` / `8.336e-7`，`round(θ,4)==1.1735`、`round(deg(θ),2)==67.24`、`round(θ,4)==1.0205`、`round(deg(θ),2)==58.47` 全部保持，impl-internal residual 仍 `1.164e-14`
- [x] B.3 `voronoi_angle` 重写为 `θ̂ = (1/N_e)·Σ_i G⁻¹(A_i)`，签名不变；模块常量 `VORONOI_AREA_SAMPLES = 1_000_000` / `VORONOI_AREA_SEED = 20260929`
- [x] B.4 保留既有 `dim() != 2` / `N_e < 2` 两个 `ValueError` 分支（不属本次缺陷）；新增 `d_c < 2` 分支
- [x] B.5 删除 clamp 后永不可达的 `try/except`
- [x] B.6 docstring 三处订正：模块级语义与纯度声明、函数级 Jensen 推导 + 凸分支前提 + 峰值订正（`+31.5868° @ 38.9420°`，两端归零）
- [x] B.7 `__all__` 导出两个新常量

## C. 测试

- [x] C.1 `test_voronoi_measurement_layer` 重写为 `1.0°` 可通约性界（被取代统计量在此处偏离 `46.72°`，47 倍）
- [x] C.2 `test_voronoi_angle_known_answer_crosspolytope` 见证换值 `pytest.approx(62.5444, abs=1e-3)`，并新增两个被取代输出的回归守护
- [x] C.3 `test_voronoi_angle_equal_area_witness_equal_area_configurations`（新增）
- [x] C.4 `test_voronoi_angle_not_degenerate_mean_area_form`（新增）
- [x] C.5 `test_voronoi_angle_one_sided_gap`（新增，gap 756σ/319σ/70σ）
- [x] C.6 `test_voronoi_angle_convexity_boundary`（新增，钉 `θ_conv`）
- [x] C.7 `test_voronoi_angle_reflected_cap_branch_n_e_2`（新增，`A_i = 0.50039 > 0.5` 触发反射分支）
- [x] C.8 全部新断言内嵌 `f"actual={...}"`

## D. 验收

- [x] D.1 `uv run pytest tests/test_sphere.py -k voronoi` → **14 passed**
- [x] D.2 `uv run pytest` → **213 passed**（基线 `208 passed` + 5 个新增测试）
- [x] D.3 `canonical_voronoi_angle` 未回归（见 B.2）
- [x] D.4 crosspolytope 见证 `62.5444°`，`abs=1e-3` 通过；实测 gap `6.5e-5°`
- [x] D.5 反退化守护通过（分离 `26.85°` / `2.47°` vs 阈值 `1.0°`）
- [x] D.6 单侧性 3 构型通过
- [x] D.7 运行时 `voronoi_angle(crosspolytope)` `0.155 s` < `1.0 s`
- [x] D.8 `voronoi_angle` 在 `src/` 内仍零调用方（`sphere.py` 是叶模块）

## E. Gate（spec 应用后）

- [x] E.1 三份 delta 已应用到主 spec（`openspec archive` 报 `~ 3 modified`）
- [x] E.2 `python scripts/lint_no_dead_defensive.py` → `exit=0`
- [x] E.3 `python scripts/lint_no_source_field_drift.py` → `exit=0`
- [x] E.4 `openspec validate --specs` → 3 passed / 0 failed
- [x] E.5 **archive 前后 anchor 覆盖逐行计数** —— **抓到了 archive 吞 anchor**（见 F.3）

## F. Archive

- [x] F.1 archive 前三份主 spec 逐字节 SHA256 快照（skeleton `018FFE733985FB03`/23、wayfinder `7B2ABF5F84917854`/36、governance `A14492093FC5A9B4`/4）
- [x] F.2 `openspec archive <name> -y` → exit 0
- [x] F.3 **archive 后 anchor 复跑：23/36/4 → 22/35/3，三份各丢 1 个。已全部恢复（23/36/4）并复验通过。**
- [x] F.4 change 目录已由 `openspec archive` 移入 `archive/`（CLI 自身的 move 成功，无需 `git mv`）

## G. Archive 吞 anchor 事故记录（本仓第三次）

`openspec archive` 报 `exit=0` 与 `~ 3 modified`，而**以下四项全部通过**：

- `lint_no_dead_defensive` → `exit=0`
- `lint_no_source_field_drift` → `exit=0`
- `openspec validate --specs` → 3 passed / 0 failed
- `openspec validate <change> --strict` → valid

**但 anchor 覆盖从 23/36/4 掉到 22/35/3。** 丢失的三行：

| spec | 被吞的 anchor | 原位置 | 机制 |
|---|---|---|---|
| `decompmoe-skeleton` | `<a id="req-7"></a>` | HEAD L122 | MODIFIED 块（req-6）尾部边界吞掉**紧随其后的下一个 requirement 的 anchor** |
| `wayfinder` | `<a id="req-12"></a>` | HEAD L284 | 同上（req-11 之后） |
| `governance` | `<a id="req-gov-2"></a>` | HEAD L58 | 同上（req-gov-1 之后） |

**每个被修改的 Requirement 恰好丢 1 个，且丢的永远是下一个的 anchor，不是被改的那个。** 与前两次（`2026-09-28-fix-a7-flops-attribution-and-stale-ref` 丢 `req-18`/`req-20`、`2026-09-28-fix-skeleton-l98-residual-frame-tagging`）形态完全一致。

恢复方式：把三个 anchor 按各自真正所属的 Requirement 重新插到其 `### Requirement:` heading 之前，并补齐仓内规范的空行框架（`空行 / anchor / 空行 / heading`）。仅按 `^<a id="req-(?:gov-)?\d+"></a>$` 逐行计数是唯一能发现它的检查——**工具返回成功不等于产物正确**。

**既有问题，本 change 未修**：`wayfinder/spec.md` 的 `<a id="req-27"></a>` 之前缺一个空行（其上一行直接是 `- **AND** …`）。经 `git show HEAD` 核验，改动前后完全一致，属既有状态且与本次 MODIFIED 无关，按 `CLAUDE.md` §3「不修与本次请求无关的既有问题」留待专项 change。校验脚本 `_tmp_check_anchors.py` 把它降级为 WARN。

## H. 提交

- [x] H.1 commit `33f7cc9`（12 files, +955 / −133）
- [x] H.2 `tests/test_sphere.py` 与并行 session 共享：提交只含本 change 的 hunk，其未提交的 `test_versine_voronoi_closed_form` 编辑（change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` finding B11）留在工作树未提交
- [x] H.3 提交后校验基准切换到 commit object（`git show <sha>:<path>`），非工作树

## 计划偏差记录

- **P1**：计划为 `test_voronoi_measurement_layer` 规定 `assert theta <= canonical + 1e-9`。实测该夹具真实 gap `0.0399°` 超过估计器 `5σ = 0.0355°`，且符号翻转量级与真实 gap 相同，故任何 σ 量级阈值都无法在该夹具判定单侧性。处置：改为 `1.0°` 可通约性界，单侧性移交 C.5 的 3 个 70σ–756σ 构型。**这是对计划的实质修正，已在 proposal.md「实施中发现并修正的计划缺陷」记录。**
- **P2**：计划为 skeleton req-6 假定存在 `**Source:**` 行以追加 change 引用。实测该 Requirement 无 Source 字段（skeleton 23 个 Requirement 仅 4 个有 Source），`lint_no_source_field_drift.py` 只检查已存在的 Source 行。处置：不新增 Source，血缘记录在 Scenario 与 proposal.md。
- **P3**：计划预判 `_cap_radius` 委托可能扰动 6dp pin 并给出回退分支。实测零回归（Decision 4），回退未触发。
