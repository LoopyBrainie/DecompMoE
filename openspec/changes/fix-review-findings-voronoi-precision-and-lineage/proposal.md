# fix-review-findings-voronoi-precision-and-lineage

## Why

Python reviewer Agent（session `mvs_ddda1e68ba524b79ae6b14e053bfa6b1`，2026-09-27）对 fix cycle `139e093..125d626` 做全面 `/code-review`，产出 3 HIGH / 4 MEDIUM / 7 LOW + 16 项"spec 数值声明无守护测试"清单。主 agent 已用 `git show HEAD:<path>` + 独立数值计算逐条复核，**3 个 HIGH 全部证实为真**。

核心问题：`θ_Voronoi` 闭式值的数学精度守护被 commit `3dd1104`（2026-09-25）删除后未恢复，导致 spec L236-237 的 4 个数值声明（`1.1735 rad` / `67.24°` / `0.6131` / `1.0205 rad` / `58.47°` / `0.4771`）**零守护**；替代物是 `X == X` 恒真断言。同时 governance spec 用来背书该精度的 `abs=1e-6` 强制条款（req-gov-1 §3）引用的 3 个测试字面量与 1 个测试函数名**在仓库中全部不存在**，条款空转。

这直接违反用户关注的核心约束："每个子 spec tdd 工作流产生的 pytest 必须对数学原理进行约束，不能只管功能不管原理"。

## Scope

**In scope（本次修复）**：

| Finding | 文件 | 修复 |
|---|---|---|
| **H1** | `wayfinder/spec.md:240` | 假等式：`1.1735482746999482 rad = 67.2393145636...°` → 实为 `67.23936319516639°`（错 4.863e-05°）。把"真数学根的度数"与"实现的弧度值"配成等式 |
| **H2** | `tests/test_sphere.py:215-220` | `X == X` 恒真断言 → 恢复 `3dd1104` 删除的 6 个闭式字面量守护（`1.173548` / `1.165848` / `1.020506` / `0.61312` / `0.47707`），用 `pytest.approx(..., abs=1e-6)` + `f"actual="` |
| **H2b** | `tests/test_sphere.py:100-112, 115-134, 188-191` | 补 `θ(16,16) ≈ 1.1735 rad` / `67.24°` / `θ(64,16) ≈ 1.0205 rad` / `58.47°` 守护；L188 的 `abs < π/2` 弱容差收紧到 `abs=1e-6` |
| **H3** | `governance/spec.md:17, 28, 52-53` | 修 3 处 phantom 引用（`1.173548`/`1.165848`/`1.020507` 字面量 + 不存在的 `test_voronoi_rad_precision_alignment`）；改写 Scenario 为实测状态 |
| **M1** | `governance/spec.md:15,17` + `CLAUDE.md:62` | 三方 `1.1735`/`1.1736` 漂移。governance 误引 req-11 "declares 1.1736 rad"，req-11 L236 实际是 `1.1735 rad` |
| **M2** | `wayfinder/tickets/WF-1.md:17,62` | `1/128` 未加 supersede 注解（`A6a-2.md:63` 已正确注解，同一 stale 数字漏了一处）→ 按 `CLAUDE.md` §8 protocol (a) 补 |
| **M3** | `wayfinder/spec.md:705-711` | req-31 声称 gate 发出 `x_out`，但 `src/` 中无 `x_out` 生产者（`gating.py:55-60` 说该方程在下游 `GeometricRouter.route()`，那不存在）→ Scenario 措辞改为如实描述"守护 gate primitives 组合"而非虚构生产者 |
| **M4** | `decompmoe-skeleton/spec.md:98` | `abs=1e-4` vs governance `abs=1e-6` 同类声明容差冲突（`2d0950b` 以 LOW-006 defer，HEAD 仍 live）→ 对齐 `abs=1e-6` |
| **L1** | `wayfinder/spec.md:150,156` + `tickets/A4-1.md:59` | 引用 "per L122" / "L122 narrative"，`β_0`/`σ'` 实际在 **L130** |
| **L2** | `wayfinder/spec.md:834,836` + `tickets/A8-2.md:70,74` | 引用 req-20 "L394-466" / "MCI row at L413"，实际 **L434-505** / **L453** |
| **L3** | `wayfinder/spec.md:578` | `γ_init ≈ −6.785` → 正确值 **−6.78355**（误差 1.5e-3） |
| **L4** | `tests/test_distance.py:25-26,87` | 缺 `f"actual={...}"`（governance req-gov-1 §5 强制） |
| **L5** | `tests/test_gating.py:42` | `Σp=1` 缺 `f"actual={...}"` |
| **L7** | `tests/test_sphere.py:188-191` | `abs(theta - canonical) < math.pi/2` 近空断言（配合 L183 的 `0 < theta < π` 几乎任何值都过）→ 收紧 |
| **G1** | `tests/test_schedule.py` | 补 `gamma_reset_for_phase4(16.0) ≈ −0.06454` 字面量守护（当前只重推公式，不钉 spec literal） |
| **G2** | `tests/test_config.py` 或新 `tests/test_flops.py` | 补 `FLOPs_Routing = 66_048` / `264_192 FLOPs/token` / `≈0.20%` 比率守护（spec L420 无任何测试守护） |
| **G3** | `wayfinder/spec.md:363` | `16 floats = 64 bytes` 无守护 → 补测试 |
| **G4** | `tests/test_beta.py` | 补反事实 `γ_init ≈ −6.784` / `σ' ≈ 1.13e-3` / `25× starvation` 守护（spec L578 无守护） |
| **G5** | `tests/test_schedule.py` | 补 `\|β_max(55_999) − β^eff(56_000)\| < 5e-4` 字面边界守护 |

**Out of scope**：

- `W_proj ≈ 64 KB` / `activations ≈ 4 KB` / `0.5%` decoder latency / `0 bytes HBM` —— reviewer 标 UNVERIFIABLE（本环境无 CUDA，`cudaGetDeviceCount()` 返回 `cudaErrorNotSupported`）。spec 中改为显式标注 GPU-only / 非 CPU 可验，避免 future audit 误报
- `L6` `tests/test_extraction.py:106,125,137` helper-tautology —— governance req-gov-1 L43 已显式 carve-out 为 pre-existing state，非本 change 引入
- `M3` 的实现侧（新增 `GeometricRouter.route()`）—— 新增下游模块超 scope；本次只修 Scenario 措辞使其不虚构生产者
- 任何 `src/` 行为变更（本次全部是 spec 措辞 + 测试守护 + ticket 注解，无实现改动）

## Impact

- **Affected files**：
  - `openspec/specs/wayfinder/spec.md`（H1 数值、M3 措辞、L1/L2 行号、L3 数值、G3 守护声明）
  - `openspec/specs/decompmoe-skeleton/spec.md`（M4 容差）
  - `openspec/specs/governance/spec.md`（H3 phantom 引用、M1 漂移）
  - `CLAUDE.md`（M1 `1.1736` → `1.1735`）
  - `tests/test_sphere.py`（H2 字面量恢复、H2b、L7）
  - `tests/test_distance.py`（L4）
  - `tests/test_gating.py`（L5）
  - `tests/test_schedule.py`（G1、G5）
  - `tests/test_beta.py`（G4）
  - `wayfinder/tickets/WF-1.md`（M2）
  - `wayfinder/tickets/A4-1.md`（L1）
  - `wayfinder/tickets/A8-2.md`（L2）
- **Lint**：两个 gate 必须保持 `exit=0`。M2 的 ticket 注解必须用 `(historical, ...; superseded by ...)` 模式以通过 `lint_no_source_field_drift.py`
- **Test**：199 tests 基线必须保持全绿；新增守护为 additive

## Capabilities

### Modified Capabilities

`wayfinder`（L-annotation + 数值修正）、`decompmoe-skeleton`（M4 容差）、`governance`（H3 + M1）

### `skip_specs` rationale

不适用 —— 本 change 确实修改 spec 内容（H1 数值、M3 措辞、M4 容差、L1/L2/L3 修正），但通过本 change 目录的 `specs/<capability>/spec.md` delta 应用。

## Source back-link（governance/req-gov-1 §3）

- **`CLAUDE.md`** §3 TDD convention + §6 第 8 条 hard rule（L4/L5 `f"actual="`、H2 数值对账）
- change `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` proposal.md（A2.1/A2.2 closure context）
- Python reviewer session `mvs_ddda1e68ba524b79ae6b14e053bfa6b1` report（findings 来源，2026-09-27）
