# Tasks

> 命名约定：每条 task 标注其 finding ID 与交付形态。所有断言改动必须满足 `governance/spec.md` req-gov-1 obligation 5（每条嵌入 `f"actual={...}"`）。

## 1. T5 / B9 — 删除已证伪的声明（先做，风险最低，无断言变更）

- [x] 1.1 `src/decompmoe/sphere.py:179-181` 删除 docstring 中的假收敛声明（"For N_e equal-area Voronoi cells on `S^{d_c − 1}`, this converges to `canonical_voronoi_angle` as the routing distribution approaches the equal-area ideal."），替换为如实描述：`θ = arccos(1 − mean_pairwise_chord)` 是**质心离散度统计量**，对**所有**成对取平均；而 `canonical_voronoi_angle` 由**最近邻**（Voronoi 胞元半径）决定，二者量纲不同，**不可互相逼近**。附 crosspolytope 实测证据（见 `design.md` Decision 4）。
- [x] 1.2 `tests/test_sphere.py:233-234` 删除伪造定理（"a physically meaningful bound is half the sphere: the realized Voronoi cell cannot exceed π/2 from the canonical half-angle on `S^{d_c−1}"）。该定理在 spec 中 0 命中且有反例（15 点塌缩 + 1 对跖点，Δ=0.4508 < π/2 仍通过）。
- [x] 1.3 `tests/test_sphere.py:203-205` 与 docstring `:196-199` 如实描述夹具：只填 `v[0] / v[1] / v[2]`，**有效秩 3/16**，是 S² 嵌入 R¹⁶，**不是 S¹⁵ 上的分布**。
- [x] 1.4 `tests/test_sphere.py:235` 的 `π/2` 断言**数值不变**；失败消息补溯源指针（指向 `sphere.py` docstring，说明该界对质心离散度统计量成立、而非对 Voronoi 半角）。
- [x] 1.5 验证 `grep 'converges to .canonical_voronoi_angle|cannot exceed|half the sphere'` 在 `src/` 与 `tests/` 均 0 命中。

## 2. T3 / B6 — footprint 测试改真实调用 + req-16 delta 钉死元素类型

- [x] 2.1 程序化构造 `specs/wayfinder/spec.md` 的 req-16 delta（`design.md` Decision 8 的八步纪律：block 抽取 / 不带 anchor / 命中次数断言 / op 列表仅展示 / 按 header 往返 / 反引号配平 / 既有失效 code span 原样保留 / 逐字存在性证明）。**实施前重跑归属检查**（`Get-ChildItem openspec/changes -Directory` + 对每个活跃 change `Select-String 'Prefill And Decode'`）。
- [x] 2.2 delta 内容：`16 floats = 64 bytes per layer per token for `d_c = 16`` → 显式钉定 float32；`**Source:**` 追加本 change 反链（backtick-wrapped，**第一个 top-level item 保持不变** —— `lint_no_source_field_drift.py` 硬卡）。**不引入任何新数值**。
- [x] 2.3 `tests/test_sphere.py::test_ct_decode_footprint_64_bytes` 改为真实调用 `extraction.extract_C(...)`，断言 `C.dtype == torch.float32` + `C.shape[-1] == cfg.d_c`；footprint 由**实测** `cfg.d_c * C.element_size()` 导出并 `== 64`。
- [x] 2.4 删除冗余的 `:189`（与 `:186` 是同一断言，`floats` 就是 `cfg.d_c`）。
- [x] 2.5 修正 docstring stale 反链：`Spec L363` → `Spec L369 (req-16)`（L363 是 req-15 的一条 phase-trigger THEN 行）。
- [x] 2.6 修正 docstring `:178` 的误引：「Integer closed form → bare `==`」—— 64 bytes 不是任何 spec 公式的整数闭式，是本地 `d_c * element_size()`。改为如实描述并按 T2 形态使用 `pytest.approx` 承载浮点侧。

## 3. T2 / B3 — 9 处 spec-anchored 浮点裸 `==` 迁移

- [x] 3.1 **最高优先**：`tests/test_safeguards.py:690-691` docstring 与 `:712-715` 注释中「`MAX_GRAD_PER_C = 32.0` 是 integer closed-form / 用 bare `==`」的错误规则表述 → 改为 float 闭式用 `approx`（同文件 `:693-711` 已有正确先例）。
- [x] 3.2 `tests/test_safeguards.py:716` `beta_mod.MAX_GRAD_PER_C == 32.0` → `pytest.approx(32.0, abs=1e-12)`。
- [x] 3.3 `tests/test_safeguards.py:854` `nan_ladder(0) == ("skip", 1.0, False)` → 逐分量 `approx`（同文件 `:91-95` docstring 自己已声明「MUST be checked via `pytest.approx` rather than bare tuple equality」）。
- [x] 3.4 `tests/test_beta.py:107` `beta.BETA_MIN == 0.1` → `pytest.approx(0.1, abs=1e-12)`。**迁移理由是消除同仓两套规则并存，不是探测能力增强**（`design.md` Decision 7）。
- [x] 3.5 `tests/test_beta.py:260` `beta.MAX_GRAD_PER_C == 32.0` → `pytest.approx(32.0, abs=1e-12)`（`:258` 刚 `assert isinstance(..., float)`）。
- [x] 3.6 `tests/test_schedule.py:94` / `:95` `lo == 1.0` / `hi == 32.0` → `approx`。
- [x] 3.7 `tests/test_schedule.py:113` `advisory["R_H"] == 0.99` → `approx`。
- [x] 3.8 `tests/test_schedule.py:126` `phase_beta_box(2) == (1.0, 4.0)` → 逐分量 `approx`。
- [x] 3.9 `tests/test_viz_protocols.py:29` `PCA3D.camera_angles == (25.0, 135.0)` → 逐分量 `approx`。
- [x] 3.10 **明确排除** `tests/test_gating.py:59` `torch.all(grad[is_neg_inf] == 0.0)`（`design.md` Decision 3）。禁止顺手改。
- [x] 3.11 **不得触碰** `tests/test_sphere.py:116/117/141/142` 的 4 条 `round(...) ==`（B5 已驳回，`design.md` Decision 1）。
- [x] 3.12 AST sweep 验收：float-literal 与 tuple-of-float 两类裸 `==` 站点均归零（除 3.10 与 3.11 的豁免）。

## 4. T1 / B1 — `test_complexity_budget` 补实现侧 MAC 实测

- [x] 4.1 在 `tests/test_extraction.py::test_complexity_budget` 内用 `inspect.getsource(extraction.extract_C)` + `ast.parse` 导出实现侧 MAC 数（`design.md` Decision 6：选 AST 不选 profiler，因 profiler backend-dependent）。
- [x] 4.2 断言 `ast_measured == 33_040`（**`33_040` 保持字面量钉值**，被断言方是 spec 字面量，AST 提供独立导出 —— 两者不一致才红）。
- [x] 4.3 改写 docstring `:86-97`：删除「does NOT measure MAC count via profiler/hooks」的自认降级，如实描述 AST 实测路径。
- [x] 4.4 `:125` / `:137` 的 scaling 断言**保持不变**（守护闭式结构性质，非实现）。
- [x] 4.5 变异验收：给 `extract_C` 加一次不改变归一化语义的 softmax 后，4.2 的对账必须**变红**。

## 5. T4 / B8 — metrics 恒真式接真实实现

> **review 后重写**（见 §8 F6 与 `design.md` Decision 5）：本节原 5.2–5.4 的形态在 review 中被判为「让错数字看起来像被验证」，已整体替换。当前形态以本节复选框内标注为准。

- [x] 5.1 引入真实 `metrics.MCI` 调用读出下界：`mci_floor = metrics.MCI(rank-1 tokens).item()`（实测 `0.0625` 恰为 `1/d_c`）——下界来自实现，不再是 `1.0/16` 自比。
- [x] 5.2 **（重写）** 断言 `health_target < mci_floor`（`0.05 < 0.0625`），即「health target 不可达」锚定在**实现输出的下界**上。原 `health_target < mci_empirical` 形态对比的是各向同性样本上的种子相关读数（实测 `0.9987`），即使 `MCI` 被地板到 0.06 仍会通过。
- [x] 5.3 **（重写，删除）** 原 5.4 的经验 CV 块已**整块删除**：`cv_estimated` 量的是到经验均值方向的最大弦距，对各向同性样本 ≈4σ ≈ 1.0，与 `d_c` 无数学关联，松弛 30.7× 通过。收紧到 spec 逐字 claim 只会让一个与 `1/d_c` 无关的数字更像被验证过。spec 自身的 `CV ≥ 1/d_c` 声明**仍未被守护**，已登记为移交项。
- [x] 5.4 **（重写，删除）** `MCI(rank-1) == 1/d_c` 的重复断言已删——`test_mci_rank1_token_distribution` 与 `test_mci_uncentered_both_endpoints_attainable_principle` 已覆盖，第三份不守护任何新东西。
- [x] 5.5 测试重命名为 `test_mci_health_target_unreachable_below_floor`（旧名 `test_mci_cv_convex_hull_lower_bound_unreachable` 描述的 CV 凸包已不存在）。保留 `manual_seed(0)` 与 `f"actual={...}"` 失败消息。
- [x] 5.6 变异验收：`metrics.MCI` 恒返回 0 时，5.2 必须变红。

## 6. amend — 移除 governance 的 B1 deferred acknowledgment

- [x] 6.1 **先复读** `openspec/changes/2026-09-28-fix-a2-a3-a4-residual-precision-claims/specs/governance/spec.md` 当前内容（该制品由另一并行 session 拥有，已被 apply 到主 spec 但未归档）。
- [x] 6.2 定点替换 Scenario 的括号句：删除 `(The current tests/test_extraction.py::test_complexity_budget MACs-claim part uses the helper-tautology form — this is tracked in proposal.md "Deferred Items" (B1, B2) and is permitted only as a pre-existing-state acknowledgment;` 前半段，**保留** `any NEW test verifying the same claim MUST satisfy clause (3).)` 的前瞻性要求。断言命中次数 == 1。
- [x] 6.3 在该 change 的 `design.md` / `tasks.md` 记录「B1 已闭环，来源 = 本 change task 4」，并说明 `skeleton-l98` 已归档。
- [x] 6.4 **禁止**本 change 自出第二份 `req-gov-1` 整块 delta（OpenSpec archive 按 Requirement 整块覆盖，两份未归档 delta 后归档者会静默丢弃先归档者）。

## 7. 验收

- [x] 7.1 `uv run pytest -q` 全绿，且 passed 数**不少于**基线 204（review 修复后为 **207 passed**：`+1` 来自 F8 的 crosspolytope 已知答案见证，F3 的 footprint 测试为重命名不增计数）。
- [x] 7.2 `python scripts/lint_no_dead_defensive.py` exit=0。
- [x] 7.3 `python scripts/lint_no_source_field_drift.py` exit=0（archive 前置条件）。
- [x] 7.4 逐 task 变异测试全部按预期变红（T1 4.5 / T3 2.x / T4 5.6 / T5 1.5）。
- [x] 7.5 req-16 delta 三层验证全过：命中次数断言 / 往返验证 / 结构与反引号配平检查。

> 7.5 因 F3 失效：`wayfinder` req-16 的 delta 已**撤回**（见 `proposal.md` §Withdrawn），本 change 转为 `skip_specs: true`。撤回后 `.openspec.yaml` / delta 目录一并清理，claim 不再存在，故无三层验证可言。

## 8. review 修复轮（F1–F11）

来源：Python reviewer（`/code-review`，四轴）报 4 HIGH / 6 MEDIUM / 5 LOW。用户裁定「修复本 session 内所有 findings」——即只修本 change 引入或留下的项；pre-existing 与其他 change 的项只登记为移交项（见 `proposal.md` §移交项，共 10 条）。

reviewer 结论经**逐条实测复现**后才采信；三条最重的高危全部成立（A3-1 变异实测失明、A3-2 低估 8–15×、A1-2 反解误差实测 `+8.73°…+31.43°`）。

- [x] **F1**（A3-1 / A3-2 / A4-6）`tests/test_extraction.py`：`_measure_extract_c_macs` → `_census_extract_C()`。删 `unaccounted_reduction`（实测低估 8–15×，且无任何断言消费它）。计数器只数**算子**（projection 2 / bias_add 1 / l2_normalize 2 / reduction 1），不算 MAC 量级——量级因子全由调用方提供，在测试里算等于自乘一个自己选的常数。`33_040` 保持 spec 字面量裸 `==`（`design.md` Decision 6）。
- [x] **F2**（A1-2）`src/decompmoe/sphere.py` **仅 docstring**：`voronoi_angle` 的双缺陷（反解 `arccos(1−c)` 应为 `arccos(1−c²/2)`；平均口径应为 `mean_i min_{j≠i} angle/2`）写进函数 docstring 与模块 docstring，并在 `design.md` Decision 4 补「根因是平均口径」这一判断被推翻的更正段。**不修行为**——行为变更需数学推导，移交专项 change。
- [x] **F3**（A1-3 / A3-7）**撤回** req-16 的 float32 钉（无 spec 依据 + 与 req-18 BF16 冲突）。删 `specs/wayfinder/spec.md` delta 与空目录，`.openspec.yaml` 设 `skip_specs: true`。`test_ct_decode_footprint_64_bytes` → `test_ct_decode_footprint_is_dtype_dependent`，改断言 dtype 透明性。
- [x] **F4**（A3-4）3 处「不 binary-exact」的**不实**陈述改写为如实披露：实测 `32.0 / 1.0 / 4.0 / 25.0 / 135.0` 全精确，仅 `0.1 / 0.99` 不精确；并写明 `approx` 略**削弱**于 `==`。
- [x] **F5**（A3-6）`tests/test_safeguards.py`：`nan_ladder(0)` 补 failure message；`:725` 消息改 `actual=` 形式。
- [x] **F6**（A3-3）见 §5 重写标注。
- [x] **F7**（A3-5）`advisory["R_H"]` 由 `pytest.approx` **回退**裸 `==`（dict 透传，非 spec-anchored，与既有豁免 `test_gating.py:59` 同理由），并登记 req-15 Layer 2 零实现。
- [x] **F8**（A3-8）新增 `test_voronoi_angle_known_answer_crosspolytope`：钉住 `115.6651°`（`abs=1e-4`）与到 canonical 的差 `53.1206°`，让 measurement layer 的缺陷有一个可复现的量化见证。
- [x] **F9**（A1-4）`src/decompmoe/sphere.py` 模块 docstring 残留段落同步。
- [x] **F10**（A4-3）撤回 `a2-a3-a4` 中两处**不实**宣称：其 delta 的原始 B1 acknowledgment（并行 session 曾还原一次）+ 主 spec 的「now derives its MACs count」——实为 operator census 钉算子集合，不是量级测量。
- [x] **F11**（A4-4）`proposal.md` 补 §Withdrawn（req-16 撤回理由，含 req-18 BF16 冲突实测）、§Capabilities 改「无」、移交项扩为 10 条（含 reviewer A3-9 挖出的 req-15 `WB=0.0476` / `>2.0` 零实现、req-18 `64KB` / `4KB` 无 pin、skeleton req-7 与 clause-(3) 的矛盾）。

## 9. review 轮终验

- [x] 9.1 `uv run pytest -q` → **207 passed**，exit=0。
- [x] 9.2 两个 lint 均 exit=0：`lint_no_dead_defensive` OK、`lint_no_source_field_drift` OK (3 files scanned)。
- [x] 9.3 `openspec validate <change> --strict` → `is valid`，exit=0（`skip_specs` 被接受，零 delta）。
- [x] 9.4 anchor 覆盖 3/3 全量：`wayfinder` 36/36、`decompmoe-skeleton` 23/23、`governance` 4/4。
- [x] 9.5 ruff：本 session 引入的 `tests/test_extraction.py:6:1 I001` 已修；剩余 5 项（RUF022 `sphere.py` `__all__`、I001/PLR0402 `test_safeguards.py`、I001 `test_sphere.py`）**全部为 HEAD 既有**，未越界清理。
- [x] 9.6 换行：本 change 全部制品 + 本 session 触碰的 7 个源文件均 **LF**（`CR=0`），CRLF 归零。
- [x] 9.7 变异复验（内存 monkeypatch，不落盘）**6/6**：3 个基线仍绿 + 3 个 mutant 全部被杀（census `+1 projection` / footprint `.float()` 强转 / `MCI=0`）。
