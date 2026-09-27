# Tasks: fix-review-findings-voronoi-precision-and-lineage

## 1. Spec 数值与措辞修正

### 1.1 H1 — `wayfinder/spec.md:240` 假单位换算
- [x] 1.1.1 `1.1735482746999482 rad = 67.2393145636...°` → `1.1735482746999482 rad = 67.23936319516639°`
- [x] 1.1.2 验证：`math.degrees(1.1735482746999482) == 67.23936319516639`

### 1.2 M3 — `wayfinder/spec.md:705-711` req-31 措辞
- [x] 1.2.1 Scenario 措辞改为如实描述：spec 守护的是 gate primitives（`topk_mask_with_neg_inf` + `local_softmax`）的组合恒等式，而非虚构的 `x_out` 生产者
- [x] 1.2.2 显式声明下游 `GeometricRouter.route()` 为未实现的 future scope

### 1.3 M4 — `decompmoe-skeleton/spec.md:98` 容差对齐
- [x] 1.3.1 `within abs=1e-4 rad` → `within abs=1e-6 rad`（对齐 governance req-gov-1 §3）

### 1.4 L1 / L2 / L3 — 行号引用与数值修正
- [x] 1.4.1 `wayfinder/spec.md:150` `per L122` → `per L130`
- [x] 1.4.2 `wayfinder/spec.md:156` `the L122 narrative` → `the L130 narrative`
- [x] 1.4.3 `tickets/A4-1.md:59` `req-7 L122` → `req-7 L130`
- [x] 1.4.4 `wayfinder/spec.md:834` `L394-466` → `L434-505`；`MCI row at L413` → `MCI row at L453`
- [x] 1.4.5 `wayfinder/spec.md:836` `Spec L413 verbatim` → `Spec L453 verbatim`
- [x] 1.4.6 `tickets/A8-2.md:70,74` 对应行号同步
- [x] 1.4.7 `wayfinder/spec.md:578` `γ_init ≈ −6.785` → `γ_init ≈ −6.7836`；`σ'(−6.785) ≈ 1.128e-3` → `σ'(−6.7836) ≈ 1.130e-3`
- [x] 1.4.8 验证：解 `0.1 + 31·σ(γ) = 1.0` 得 γ 与 σ′ 实际值

### 1.5 M1 — 三方 `1.1735`/`1.1736` 漂移
- [x] 1.5.1 `governance/spec.md:15` `1.1736 rad` → `1.1735 rad`
- [x] 1.5.2 `governance/spec.md:17` 移除 "declared in Requirement 11" 误引，改为准确引用 req-11 L236 的 `1.1735 rad`
- [x] 1.5.3 `CLAUDE.md:62` `1.1736 rad` → `1.1735 rad`

## 2. Test 数值守护恢复与加固

### 2.1 H2 — `tests/test_sphere.py` 字面量恢复
- [x] 2.1.1 `test_voronoi_monotone_in_ne` 补 `θ(16,16) == approx(1.173548, abs=1e-6)` + `θ(17,16) == approx(1.165848, abs=1e-6)`，各带 `f"actual="`
- [x] 2.1.2 `test_voronoi_canonical_N_e_dependence` 补 `θ(64,16) == approx(1.020506, abs=1e-6)` + `f"actual="`
- [x] 2.1.3 `test_versine_voronoi_closed_form` 删除 `X == X` 恒真断言，改为 `v(16,16) == approx(0.61312, abs=1e-4)` + `v(64,16) == approx(0.47707, abs=1e-4)` + `f"actual="`
- [x] 2.1.4 更新该测试 docstring：删除 "NOT self-referenced" 误导性说明

### 2.2 H2b / L7 — spec 4dp 显示形守护 + 弱容差收紧
- [x] 2.2.1 补 `round(θ(16,16), 4) == 1.1735` 与 `round(math.degrees(θ(16,16)), 2) == 67.24`
- [x] 2.2.2 补 `round(θ(64,16), 4) == 1.0205` 与 `round(math.degrees(θ(64,16)), 2) == 58.47`
- [~] 2.2.3 `test_voronoi_angle` L188 容差收紧 — **DEVIATION**（见文末 Deviation record）：原计划收紧到 `abs=1e-6` 实测失败

### 2.3 L4 / L5 — `f"actual="` 补全
- [x] 2.3.1 `tests/test_distance.py:25-26` min/max 断言补 `f"actual="`
- [x] 2.3.2 `tests/test_distance.py:87` 补 `f"actual="`
- [x] 2.3.3 `tests/test_gating.py:42` `Σp=1` 补 `f"actual="`

### 2.4 G1 / G5 — schedule 数值守护
- [x] 2.4.1 `tests/test_schedule.py` 补 `gamma_reset_for_phase4(16.0) == approx(-0.06454, abs=1e-4)` 字面量守护（当前仅重推 `math.log(15/16)`）
- [x] 2.4.2 补 `\|β_max(55_999) − β^eff(56_000)\| < 5e-4` 边界守护

### 2.5 G2 — FLOPs 声明守护
- [x] 2.5.1 补 `FLOPs_Routing = 66_048` 裸 `==` 守护（整数闭式）
- [x] 2.5.2 补 `264_192 FLOPs/token` 裸 `==` 守护（4 层 × 66_048）
- [x] 2.5.3 补比率 `≈ 0.001968 → ≈ 0.20%` 守护 + `0.3%` allowance 上界
- [x] 2.5.4 补净增 `+32 FLOPs = 544 − 512` 与 `≈0.05%` 守护

### 2.6 G3 / G4 — 其余无守护数值声明
- [x] 2.6.1 补 `16 floats = 64 bytes`（`d_c=16` × 4 bytes）守护
- [x] 2.6.2 `tests/test_beta.py` 补反事实 `γ_init ≈ −6.7836` / `σ' ≈ 1.130e-3` / `≈25× starvation` 守护

## 3. Ticket 注解

### 3.1 M2 — `WF-1.md` stale `1/128`
- [x] 3.1.1 L17 `Resurrection 阈值 1/128 over 200 steps` 加 `(historical, ...; superseded by spec req-13 L268 f_threshold = 1/(2·N_e) via fix-openspec-doc-bugs Decision 7)` 注解
- [x] 3.1.2 L62 `Resurrection < 1/128 for 200 steps` 同样加注解
- [x] 3.1.3 验证 `lint_no_source_field_drift.py` 仍 `exit=0`

## 4. Governance spec 修正

### 4.1 H3 — phantom 引用清理
- [x] 4.1.1 `governance/spec.md:17` 移除 `1.173548 rad` / `1.165848 rad` / `1.020507 rad` 的 "existing test literal" 断言（改为指向本 change 实际恢复的守护测试与字面量）
- [x] 4.1.2 移除 "An existing test literal at `1.173547` ... present at `tests/test_sphere.py:90`"（L90 是注释，非字面量）
- [x] 4.1.3 `governance/spec.md:28` Source 列表移除 `test_voronoi_rad_precision_alignment`（该函数在仓库中不存在，`2026-09-12-migrate-l678-source` tasks 7.2 已记录删除但引用未清）
- [x] 4.1.4 `governance/spec.md:52-53` Scenario 改写：`1.020507` → `1.020506`（该字面量已在 `2026-09-12` task 7.1 被修正）；移除 `test_voronoi_rad_precision_alignment` OUT-OF-SCOPE 引用

## 5. 验证

- [x] 5.1 `uv run pytest -q` — 199 tests 基线 + 新增守护全绿
- [x] 5.2 `python scripts/lint_no_source_field_drift.py` — `exit=0`
- [x] 5.3 `python scripts/lint_no_dead_defensive.py` — `exit=0`
- [x] 5.4 anchor coverage 仍 100%（wayfinder 36/36、skeleton 23/23、governance 4/4）
- [x] 5.5 独立数值复核 H1 修正后的等式成立

## Deviation record

### 2.2.3 — L7 容差收紧回退（如实记录）

Reviewer 建议把 `tests/test_sphere.py::test_voronoi_measurement_layer` 的
`abs(theta - canonical) < math.pi/2` 收紧。实际应用 `abs=1e-6` **失败**：

```
AssertionError: actual_delta_rad=8.154e-01
assert 0.8154104976083063 < 1e-06
```

根因：`voronoi_angle()` 是 **measurement layer**（从实际 centroid 张量算实现角）。
Fibonacci 夹具在 S² 上近似等面积，但投影到 R¹⁶ 后实现角是 **113.96°** 而非 canonical
**67.24°**（差 0.815 rad）。原代码注释已声明此点（"projects poorly into R^16, so we
use a loose tolerance"）。

实际应用的修改：保留 `π/2` 上界（这是**物理导出的**上界 —— 实现胞元距 canonical 半角
不可能超过半球），补全 `f"actual={...}"` 失败消息并加物理依据注释。

结论：reviewer 对 L7 的"near-vacuous"判定**只部分成立** —— 该上界偏松但不是任意值。
本项修复比原计划窄，如实记录。

### 其他 reviewer finding 的部分采纳

- **M3 实现侧**（新增 `GeometricRouter.route()`）未做 —— 新增下游模块超 scope。改为修正
  req-31 Scenario 措辞，使其如实声明"当前无 `x_out` 生产者，本 Scenario 守护的是
  primitives 组合恒等式"，不再虚构生产者。
- **GPU-only 声明**（`W_proj ≈ 64 KB` / `activations ≈ 4 KB` / `0.5%` decoder latency /
  `0 bytes HBM`）未加测试 —— 本环境无 CUDA（`cudaGetDeviceCount()` 返回
  `cudaErrorNotSupported`），reviewer 已标 UNVERIFIABLE。列为 future scope。
- **L6**（`tests/test_extraction.py` helper-tautology）未动 —— governance req-gov-1 L43
  已显式 carve-out 为 pre-existing state，非本 change 引入。
- [x] 5.6 单 commit on dev，HEAD 不在 merge commit
