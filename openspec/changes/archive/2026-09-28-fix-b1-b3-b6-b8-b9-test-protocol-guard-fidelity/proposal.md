# Proposal

## Why

审计清单 B 组 9 项「Tests 违反 principle-form 协议」逐条经**实测核验**（`git show HEAD:<path>` + 独立数值复算 + 变异敏感性测试）后，判定结果分三类，本 change 只处理第三类：

1. **已在飞 change 覆盖 —— 不重复做**：B2（spec 侧 = `skeleton-l98`，测试侧 = `a2-a3-a4` A4）、B4 的 `H_kv` 部分（= `a7` Decision 4）、B7（= `a2-a3-a4` A3）。
2. **spec 主动授权的有意设计 —— 驳回**：B5（详见 `design.md` Decision 1）。
3. **未被认领且证据确认成立 —— 本 change 处理**：B1、B3、B6、B8、B9。

这 5 项的共同根因是同一类缺陷：**测试断言与它所守护的 spec 声明脱钩**。具体表现为三种形态——

- **B1**：断言用 test-local `macs()` lambda 重述闭式，**从不触碰被测实现**。实测把 `extract_C` 换成 `normalize(softmax(10·C))` 后，shape 断言、球面断言、3 条算术断言**全绿**。`governance/spec.md:45` Scenario clause (3) 已明文禁止该形态并列出三种合规机制。
- **B3**：9 处 spec-anchored 浮点闭式用裸 `==`，违反 `req-gov-1` obligation 2（`spec.md:15`）。其中 `tests/test_safeguards.py:712-715` 的**注释**与 `:690-691` 的 **docstring** 把「`MAX_GRAD_PER_C = 32.0` 是整数闭式」写死——但该常量是 `Final[float]`，错误规则被写进注释供后人复制。
- **B6**：`test_ct_decode_footprint_64_bytes` 从不调用 `extraction.extract_C`、从不检查输出 dtype，只读 `cfg.d_c` 做 `16 * 4 == 64`。实测 `extract_C` 是 dtype-transparent（fp16 输入 → 32 bytes），**全仓无任何测试 pin `C.dtype`**，而 `wayfinder/spec.md:369` 的 64-byte claim 本身也从未指明元素类型。
- **B8**：`test_mci_cv_convex_hull_lower_bound_unreachable` 的两条断言是常量比常量（`1.0/16` vs `0.0625`、`0.05` vs `1.0/16`），且该函数从不调用 `metrics.MCI` / `metrics.SP`。经验块实测松弛 **30.7×**（cv=1.921 vs 阈值 0.0525）——各向同性 randn、2-blob 双峰、准 1D 紧密云、R¹⁵ 正单纯形全部通过，仅完全塌缩才失败。
- **B9**：`test_voronoi_measurement_layer` 的注释断言了一个**不存在的定理**（"realized Voronoi cell cannot exceed π/2 from the canonical half-angle"），并删除了当时诚实的自认说明。溯源结果见 `design.md` Decision 4，根因在 `src/decompmoe/sphere.py` 的 docstring 假收敛声明。

## What Changes

| # | Task | 位置 | 变更 |
|---|---|---|---|
| 1 | **T1 / B1** | `tests/test_extraction.py::test_complexity_budget` | 新增基于 `inspect.getsource` + `ast.parse` 的**实现侧算子普查**：钉住闭式所核算的算子集合（2 次投影 / 1 次 bias 加 / 2 次球面归一 / 1 次跨头归约）。`33_040` 保持 spec 字面量钉值，由裸 `==` 对账。**不计算 MAC 数量**——每个量级因子都由调用方供给，在此计算等于自证（见 `design.md` Decision 6）。 |
| 2 | **T2 / B3** | 8 处（见 tasks.md） | 浮点裸 `==` → `pytest.approx(..., abs=...)`；修正 `test_safeguards.py` 中错误的「integer closed-form」规则表述。明确排除 `test_gating.py:59`（梯度恒零谓词）与 `test_schedule.py` 的 `advisory["R_H"]`（dict 透传）——两者都不是 spec-anchored 闭式 claim。 |
| 3 | **T3 / B6** | `tests/test_sphere.py::test_ct_decode_footprint_is_dtype_dependent` | 改为真实调用 `extraction.extract_C`，并断言 **dtype 透明性**（fp16/bf16 输入 → 32 bytes，fp32 → 64 bytes）。原 spec delta 已撤回，见下方「Withdrawn」。 |
| 4 | **T4 / B8** | `tests/test_metrics.py::test_mci_health_target_unreachable_below_floor` | 改锚到 `metrics.MCI` 的 rank-1 **下界**（`health_target < mci_floor`），删除与 spec 无数学关联的「经验 CV」块。 |
| 5 | **T5 / B9** | `src/decompmoe/sphere.py` docstring + `tests/test_sphere.py` | 删除已证伪的收敛声明与伪造定理；**新增反解缺陷的完整证据**（见 `design.md` Decision 4）；如实描述夹具有效秩 3/16；新增 crosspolytope 已知答案见证。`π/2` 断言数值**不变**。 |
| 6 | — | `openspec/changes/2026-09-28-fix-a2-a3-a4-residual-precision-claims/specs/governance/spec.md` | **amend**：把 Scenario 的 B1 deferred acknowledgment 换为对当前实现形态的**如实**陈述（`req-gov-1` 已有该 change 的整块 delta，另开第二份会被静默覆盖）。 |

**无 BREAKING 变更**：全部为测试断言形态修正 + 注释纠错。**不修改任何 spec 数值**。本 change 最终**不含任何 spec delta**（见 Withdrawn）。

## Withdrawn

**req-16 的 `float32` 元素类型钉定 —— 已撤回。** 本 change 最初对 `wayfinder/spec.md` req-16 出过一份 delta，把 `16 floats = 64 bytes` 钉为 `16 float32 = …, the element type being pinned to float32`。Review 指出该钉定**无任何 spec 依据**，且与 req-18 的 BF16 形态冲突：

- 全仓无任何 spec 语句规定 `C_t` 的计算 dtype；
- req-18（`wayfinder/spec.md:397`）把 `W_proj ≈ 64 KB in BF16` 写死（实测一致：`8·4112·2 B = 65_792 B`），且要求兼容 vLLM / TensorRT-LLM / FlashDecoding / TGI / SGLang——这些后端一律携带 BF16 KV cache，即 bf16 `K,V` → bf16 `C` → **32 bytes**，不是 64；
- `CLAUDE.md` §6 末条禁止在无数学推导的情况下收口语义选择，而此处不存在推导。

因此**撤回而非修补**：spec 恢复原状，change 转为纯测试侧（`.openspec.yaml` 设 `skip_specs: true`），元素类型的推导登记为移交项。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

**无。** 本 change 不修改任何 spec。`wayfinder` req-16 的编辑已撤回（见 Withdrawn）；`governance` 的 clause-(3) 陈述修正走 `a2-a3-a4` 已持有的 `req-gov-1` 整块 delta，不另开第二份；`wayfinder` req-11 / req-17 / req-19 / req-24 的 delta 分别归属 `a2-a3-a4` 与 `a7`；`decompmoe-skeleton` 不涉及（但存在一处**未登记的矛盾**，见移交项 7）。

## Impact

### Affected files

| 文件 | 变更类型 |
|---|---|
| `tests/test_extraction.py` | 测试断言 + docstring |
| `tests/test_beta.py` | 测试断言（2 处） |
| `tests/test_safeguards.py` | 测试断言（2 处）+ docstring + 注释 |
| `tests/test_schedule.py` | 测试断言（3 处迁移 + 1 处**回退** + docstring） |
| `tests/test_viz_protocols.py` | 测试断言（1 处）+ 新增 `import pytest` |
| `tests/test_sphere.py` | 测试断言（T3 footprint 重写、crosspolytope 见证）+ 注释（T5） |
| `tests/test_metrics.py` | 测试断言（T4） |
| `src/decompmoe/sphere.py` | **仅 docstring**，无行为变更 |
| `openspec/changes/2026-09-28-fix-a2-a3-a4-.../specs/governance/spec.md` | amend（他人 change 制品） |
| `openspec/specs/governance/spec.md` | 随上条 amend（该 change 已 apply 但未归档） |

### 移交项（不在本 change 范围）

1. **`voronoi_angle` 的反解缺陷（`decompmoe-skeleton` req-6 / req-7）**。函数计算 `arccos(1 − c)`，而 `chord = √(2·versine)` 的正确反解是 `arccos(1 − c²/2)` —— 把**弦长**喂进了要 **versine** 的槽位。实测反解误差 **+8.73°…+31.43°**（45° 附近峰值）；正确反解在每个采样角度都精确复现真值。修正属**行为变更**，`CLAUDE.md` §6 禁止绕过 OpenSpec 直接改，须另开专项 change，并按 §6 末条给出推导。
2. **`voronoi_angle` 的平均口径错误**。对**所有** `i<j` 成对取平均，而 Voronoi 胞元半角由**最近邻**决定。正确的形式化是最近邻内切半径 `θ = mean_i min_{j≠i} angle(c_i,c_j)/2`；实测 crosspolytope(32) 下为 `45.0000°`，仍不等于 canonical `62.5445°` —— 差额属 spec/实现语义错配。与 1 合并处理。
3. **spec 的 MAC 闭式漏计 step 3**。`decompmoe-skeleton` req-7「Per-token MAC closed form」只枚举 3 项，未列 `z_unit.mean(dim=1)`。按 spec 自己的「1 MAC = 1 multiply + 1 accumulate」约定，该归约至少 `H_kv·d_c = 128` MAC/真值 ≥ `33_168`，spec 字面量 `33_040` 低估约 **0.39%**。`wayfinder/spec.md:381` 却称之为 "full extract_C pipeline"。**latent risk HIGH**：一个按 FLOPs 预算立论的 Requirement 数值有误，且因测试与 spec 断言同一个闭式，无任何测试能发现。
4. **`CV ≥ 1/d_c` 无守护**。原「经验 CV」块算的是「到经验均值方向的最大弦距」，对各向同性样本约为 `4σ ≈ 1.0`，与 `d_c` 几乎无关，与 `1/d_c` **无数学关联**（实测松弛 30.7×）。已从测试中删除而非「收紧」。补守护需先给几何推导。
5. **req-15 Layer 2 完全未实现**。spec 声明 `WB = 0.0476` 与 `> 2.0` 严重聚类阈值；两者在 `src/` 与 `tests/` 中**零出现**（grep 实测）。`advisory_signals` 是纯透传 stub。
6. **req-18 residency 数值无守护**。`W_proj ≈ 64 KB in BF16`（实测 `8·4112·2 B = 65_792 B` ✓）与 `activations ≈ 4 KB` 均可算但未被 pin，`H_kv`/`d_k`/`d_c` 漂移会静默使其失效。
7. **`decompmoe-skeleton` req-7 与 `req-gov-1` clause (3) 公开矛盾且未登记**。前者结尾写「Tests MUST assert the closed form … **NOT a profiler-derived op count**」，后者**要求**实现侧实测并明列 AST。当前测试两者都做，故无一条被字面违反，但下一个读 req-7 的作者会读到一条禁令。
8. **req-16 元素类型未指定且与 req-18 冲突**（见 Withdrawn）。需要一次推导：Decode 是否保持累加 dtype、而 `W_proj` 常驻 BF16？
9. 秩-3 夹具升级为真 16 维等面积点集并重新推导紧界 —— 需先给数学推导，不得用 policy 论证替代。
10. `wayfinder` 既有的 8 行失效 code span（a7 proposal 已登记 out-of-scope）。
