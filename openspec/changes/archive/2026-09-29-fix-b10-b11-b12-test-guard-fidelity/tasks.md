# Tasks — B10 / B11 / B12

## 0. 排期门（串行前置）

- [x] 0.1 `2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity` 已 archive（commit `7bf77af`）
- [x] 0.2 `2026-09-28-fix-a2-a3-a4-residual-precision-claims` 已 archive（commit `9743d75`）
- [x] 0.3 三个目标测试文件 + 三份主 spec 工作树干净
      （`src/decompmoe/safeguards.py` 曾显示 `M`，经 `git diff` 确认为**纯 CRLF/LF 归一化提示、内容与 HEAD 逐字节相同**，非未提交编辑）
- [x] 0.4 anchor 覆盖 36/36、23/23、4/4；两 lint `exit=0`；`openspec validate --specs` 3/3
- [x] 0.5 archive 后重测行号：req-13 anchor **L303** / 正文 **L307**；req-12 Scenario **L256**；governance versine THEN **L55**（archive 未位移 B12/B10 引用；`req-gov-2` 锚点由 L56 移至 L58，故 delta 改用**锚点定位**而非硬编码行号）

## 1. B12 — `tests/test_schedule.py`（纯 test 侧）

- [x] 1.1 docstring `L295` → `anchor L303, body L307`
- [x] 1.2 Phase 0 理由改写：「无 gradient channel ⇒ 冻结名集合真空为空」，并显式否定「everything frozen ⇒ 全集」的误读
- [x] 1.3 删除第二段失效类比（Phase 0 返回 `{"c_i"}` 同样不是 spec 答案），改为「返回**非空**集合才破坏契约」
- [x] 1.4 两处断言消息 `per spec req-13 L295` → `L307`
- [x] 1.5 **不动** `actual_0 == set()` / `actual_4 == set()` 断言本身（经核验正确）
- [x] 1.6 **Rev 2**：修正 Rev 1 自身引入的错误归属 —— 新 docstring 曾写 `wayfinder req-14`，实测 `"no gradient"` / `"no EMA"` 在 **L83 / req-6**、phase 表在 **L617 / req-27**，已按实测改写

## 2. B11 — `tests/test_sphere.py` + `governance` delta

- [x] 2.1 L408/L409 `pytest.approx(..., abs=1e-4)` → 精确 `round(v, 4) == literal`
- [x] 2.2 注释改写：引用 req-6 的 4dp-display 先例
- [x] 2.3 **不动** L402-405 恒等式断言与 L410-413 的 (0,1) 区间断言
- [x] 2.4 **Rev 2**：新增 Step 2c，把 spec THEN 中声明的偏差以 6 位有效数字 + `abs=1e-10` **直接数值对账**，并加 `dev < 5e-5` 严格界（spec 承重声明）；初版用 7 位数字配 `abs=1e-12` 立即变红（截断误差 `1.17e-12`），已按所述精度配匹配容差
- [x] 2.5 **Rev 2**：obligation 2 新增 **4-decimal-display exception**（解决 `round()` 与「NOT bare `==`」的同 Requirement 内冲突）
- [x] 2.6 **Rev 2**：obligation 3 新增 scope 声明（`abs=1e-6` 只管 angle literal；versine 非 angle claim）
- [x] 2.7 **Rev 2**：THEN 删除 17 位实现值与变异测量数字（无测试守护，违反 `CLAUDE.md` §6），改为只声明已对账的偏差
- [x] 2.8 **Rev 2**：`spec L236-L237` → `wayfinder/spec.md L236-L237`；Step 3 的 `spec L233` → `wayfinder/spec.md L235`（区分句实际在 L235）

## 3. B10 — `tests/test_safeguards.py` + `decompmoe-skeleton` delta

- [x] 3.1 删除 L142-148 两条恒真断言（`RATE_LIMIT` 被 L123 钉死后恒为真，且与 L149/L150 冗余）
- [x] 3.2 **保留** L123 `assert RATE_LIMIT == 1000`（直接钉 spec 常量的前置条件，失败消息质量高于行为断言；按 surgical 原则不顺手清理）
- [x] 3.3 新增 `test_should_resurrect_rate_limit_boundary`：`Δ=R−1`→空、`Δ=R`→非空、`Δ=R+1`→非空，三条消息均内嵌 `f"actual={...}"`（obligation 5）
- [x] 3.4 修 docstring 错误论断（「retune 到 200 会静默通过」实测为假 —— `300 < 200` 为 `False`，L143/L146/L123/L150 全部变红）
- [x] 3.5 `decompmoe-skeleton` req-12 delta：Scenario 补单调性推导链 + 逐对存在量词 + `R` 对齐格点反例（`design.md` Decision 1）
- [x] 3.6 **Rev 2**：撤回假的「窗口族划分 / 同块 `⟺ Δ<R`」论证，改用可证的逐对等价式 `∃t. t ≤ t₁ < t₂ < t+R ⟺ Δ<R`，并在 spec 内**显式记录窗口族非划分**（`[0,R) ∩ [1,R+1) = R−1` 元素）及 `R` 对齐块的反例（`t₁=R−1, t₂=R`）
- [x] 3.7 **Rev 2**：删除「every `Δ ≥ R` is emitted」过度断言，收窄为限流守卫语义，并声明 `safeguards.py:95-96` / `:100-101` 两条与限流无关的空返回不是 deferral
- [x] 3.8 **Rev 2**：`2R = 2000` 改为对全部调用方模型成立的表述（仓内无 `last_resurrection_step` 写入方）

## 4. change 制品

- [x] 4.1 `.openspec.yaml`（`schema: spec-driven` / `created: 2026-09-29`）
- [x] 4.2 `proposal.md`（含对 finding 原文三处错误数字的显式纠正）
- [x] 4.3 **Rev 3**：`design.md`（Decision 1 B10 推导 / 2 B11 数值 / 3 B12 归属 / 4 wayfinder 重述 / 5 phases 0-4 Scenario / 6 换行约定 / §7 留档 / §8 剩余 hand-off）
- [x] 4.4 两份 delta **LF、无 BOM**
- [x] 4.5 两份 delta 的 `**Source:**` 行均为**纯追加**（skeleton 575→778、governance 1333→1580 字符），既有 lineage 完整保留
- [x] 4.6 delta 逐行对账：**Rev 2 为 skeleton 3 行 / governance 4 行**（obligation 2 + obligation 3 + Source + THEN），**RECONCILIATION: PASS**
- [x] 4.7 **Rev 2**：delta 构造改用**锚点定位**而非硬编码行号（`req-gov-2` 锚点 archive 后由 L56 移至 L58）

## 5. 变异测试（证明守护非恒真）

- [x] 5.1 **B11 · 公式变异**：`1.0 - math.cos(θ)` → `math.sin(θ)` ⟹ `assert 0.9221 == 0.6131` 变红 ✅
- [x] 5.2 **B11 · 精度变异（决定性）**：`v(16,16)` 偏移 `+8.0e-5`（距 literal `9.784e-5`）⟹ 旧 `abs=1e-4` **接受**、`round(v,4)` **拒绝**，测试变红 ✅
      > 首次构造误用 `+9.9e-5`：叠加基准已有的 `1.784e-5` 后总距 `1.168e-4 > 1e-4`，旧守卫**也会**红，证明不了新旧差异。已改为先做数值自检再定扰动量。
- [x] 5.3 **B11 · 变异体还原**：`git diff -- tests/test_sphere.py` 仅含 2.3 的预期改动
- [x] 5.4 **B10 · 边界变异（核心交付证明）**：`src/decompmoe/safeguards.py:93` 的 `<` → `<=` ⟹ `Δ=R is the first NON-rate-limited step and MUST fire; R=1000, actual=set()` 变红 ✅
- [x] 5.5 **B10 · 变异体还原**：`git diff -- src/decompmoe/safeguards.py` 为空（内容与 HEAD 逐字节相同）

## 6. 常规门

- [x] 6.1 `lint_no_dead_defensive.py` `exit=0`
- [x] 6.2 `lint_no_source_field_drift.py` `exit=0`
- [x] 6.3 `openspec validate --specs` 3 passed / 0 failed
- [x] 6.4 `pytest` 全绿 —— **归档时复核已过时，见 §9.3：本 change 自身的 3 个测试文件 73 passed，但全套件被 peer 的未提交改动打红（1 failed）**
- [x] 6.5 anchor 覆盖 3 capability 全 100%
- [x] 6.6 delta ≡ 主 spec 逐行对账
- [x] 6.7 两份 delta 无 CRLF、无 BOM

## 7. 独立 review 轮（Rev 1 → Rev 2）

由 Python reviewer（`/code-review`，三轴：spec 数学 / 实现↔形式化 / TDD 原理约束）复核，推翻 Rev 1 共 **7 项**（2 CRITICAL），逐条留档见 `design.md` §7。处置如下：

- [x] 7.1 **CRITICAL-1** 半开窗口「划分 + 同块 `⟺ Δ<R`」为假 —— 独立复算证实 `|W₀∩W₁| = 999`、`R` 对齐下 `t₁=999,t₂=1000` 反例；已改为逐对存在量词并在 spec 内显式记录非划分
- [x] 7.2 **CRITICAL-2** 「every `Δ ≥ R` is emitted」被 `safeguards.py:95-96`/`:100-101` 违反；已收窄为守卫语义
- [x] 7.3 **HIGH-2** `round()` 与 obligation 2「NOT bare `==`」同 Requirement 内冲突；已在 obligation 2/3 加 4-decimal-display 显式豁免
- [x] 7.4 **HIGH-3** spec THEN 写入 17 位实现值却无任何测试守护（违反 `CLAUDE.md` §6）；已删除并改为已对账的偏差值 + Step 2c 断言
- [x] 7.5 **MEDIUM-1** B12 修复引入 `wayfinder req-14` 错误归属（实际 req-6 L83 / req-27 L617）；已修正
- [x] 7.6 **MEDIUM-2** `2R = 2000` 依赖仓内不存在的调用方契约；已改为对全部调用方模型成立
- [x] 7.7 **MEDIUM-3** `round()` 在「残差放宽到 1e-6」档会漏判（`test_voronoi_residual_below_1e_minus_9` 与 6dp 角度守护先红，套件整体不漏）；措辞已改为「第三道防线」
- [x] 7.8 **MEDIUM-5 / LOW-1** `test_sphere.py` 两处 spec 引用未指名文件 / 行号错；已修正为 `wayfinder/spec.md L236-L237` / `L235`
- [x] 7.9 **LOW-2** 保留的 `L123 assert RATE_LIMIT == 1000`：review 变异实测确认**非恒真**（常量 1000→200 变红），删除 L143/L146 安全；`test_named_constants_have_spec_values`（L665）亦钉同一常量。按 surgical 原则保留

### 7.11 review 确认成立的 Rev 1 结论

- [x] versine 全部数值 bit-identical：`0.6131178409388285` / `0.4770659929048763`，偏差 `1.784094e-5` / `3.400710e-5`，均 < `5e-5`
- [x] `+8.0e-5` 变异体：旧 `abs=1e-4` 接受 / 新 `round(v,4)` 拒绝
- [x] M1 变异使新测试变红（消息逐字吻合）
- [x] 实现全域扫描 `Δ ∈ [0,2003]`，延后集恰为 `{Δ : Δ<1000}`；`R=1000` / `consec=200` 与 spec 一致
- [x] **8/8 变异体全部被 `test_should_resurrect_rate_limit_boundary` 单独捕获**（含两方向 off-by-one、`<2R`、`<=0`、去守卫、永不超时、忽略 `last_resurrection_step`）—— 三点足以钉住 `<` vs `≤`，非空转
- [x] delta 逐行对账与换行卫生、Source 纯追加
- [x] `resurrect_expert` **不推进** `last_resurrection_step`；全仓无该变量写入方

## 8. Rev 3 — 关闭本 session 剩余 findings（HIGH-1 / MEDIUM-4）

用户指示「修复本 session 内所有 findings」，故扩范围至原先登记为 hand-off 的两项。

- [x] 8.1 **HIGH-1-a 边界二义** → 新增 `wayfinder` delta（req-13），声明窗口边缘**排他**（`Δ = R` 不延后），并指向 skeleton req-12 Scenario 为规范形式化
- [x] 8.2 **HIGH-1-b 主语语义与实现不符** → wayfinder Scenario 加入 **Scope correction**：原 "only one resurrection event executes" 描述的每窗口配额**未实现**（`safeguards.py:98-102` 返回全部合格 expert，无 one-per-window 裁剪）；限流实为**每次调用的延后闸门**。被 supersede 的读法明文留档于 Scenario 内 + Decision 4
- [x] 8.3 **MEDIUM-4** → `decompmoe-skeleton` req-13 插入 `#### Scenario: Phase-0 and Phase-4 freeze-name set is empty`（紧接 Phase boundaries，保持 phase 顺序），把正文句 "empty for phases 0/4" 提升为有 Scenario 承载的规范句
- [x] 8.4 **未凭空新增 Source 字段** —— skeleton req-13 原本就无 `**Source:**` 行（既存，lint 通过），change 血缘记在 delta 与 `design.md`
- [x] 8.5 对账扩展为双模式：替换型（skeleton req-12 / governance req-gov-1 / wayfinder req-13）走逐行 diff + Source 纯追加；**插入型**（skeleton req-13）走「移除插入段后必须逐行等于主 spec block」的证明式对账
- [x] 8.6 期望差异数更新：skeleton req-12 = 3、skeleton req-13 = 插入 4 行、governance = 4、wayfinder = 3 —— **RECONCILIATION: PASS**
- [x] 8.7 `openspec validate 2026-09-29-fix-b10-b11-b12-test-guard-fidelity` → **valid**
- [x] 8.8 `design.md` Decision 编号重排为 1 B10 / 2 B11 / 3 B12 / 4 wayfinder / 5 phases 0-4 / 6 换行约定，与三份 delta 的 `**Source:**` 引用对齐

## 9. 归档记录（`/openspec-archive-change`）

### 9.1 归档前的基座漂移拦截 —— 一次真实的 delta 基座失效

归档前复验发现 **governance req-gov-1 基座已漂移 10 行**：peer 的 `33f7cc9`（`fix(voronoi_angle): replace defective measurement layer with mean per-cell equivalent-cap radius`）改写了 obligation 5（`obligations 1, 2, and 3` → `obligations 1, 2, 3 and 7`）、新增 obligation 7（Monte-Carlo-derived statistical claims）与一个新 Scenario。本 change 的 delta 建在旧基座上，而归档是**整块覆盖** —— 直接执行会静默销毁 peer 已提交的内容（不报错、不告警、lint 与 validate 全绿）。

**处置**：按 skill 的「capability 不匹配则 report and stop」中止归档，征得用户确认（peer 已收工）后，**以当前主 spec 为基重�� governance delta**（retain peer 的 obligation 5 改写 + obligation 7 + 新 Scenario，再叠加本 change 的 4 处编辑）。另 3 个 Requirement 基座未漂移，无需重建。

- [x] 9.1.1 重建前确认 peer 静默 60 分钟、HEAD 未动、三份主 spec 相对 HEAD 干净
- [x] 9.1.2 重建后 6 个 peer 标记 + 4 个本 change 标记全部在 delta 中；差异行数回到预期 4
- [x] 9.1.3 另两个未归档 change 的 skeleton delta 改的是 **req-21**，与本 change 的 req-12/13 无重叠（先查重再归档，避免后归档者静默丢弃先归档者的编辑）

### 9.2 同步与归档

- [x] 9.2.1 归档前对三份主 spec 做 **SHA256 + anchor 基线快照**（`%TEMP%\dm_prearchive\`），因主 spec 相对 HEAD 干净，`git checkout -- <spec>` 是有效完整恢复路径
- [x] 9.2.2 `openspec instructions specs --change <name> --json` → **exit 0、JSON 有效、无 `rules`**（no-rules 情形）
- [x] 9.2.3 以**确定性 block 替换**完成 sync（未用工具的隐式合并），逐份**保留主 spec 自身换行风格**（三份现均为 CRLF；若按 LF 写回 skeleton 会产生整文件伪 diff）
- [x] 9.2.4 归档前门禁：两 lint `exit=0`、`openspec validate --specs` 3/3、change 自身 `openspec validate` → valid
- [x] 9.2.5 `Move-Item -LiteralPath` 移入 `openspec/changes/archive/2026-09-29-fix-b10-b11-b12-test-guard-fidelity/`（`git mv` 对未跟踪目录不可用）

### 9.3 归档后验证（anchor 计数是唯一可信证据）

- [x] 9.3.1 **anchor 覆盖 wayfinder 36/36、decompmoe-skeleton 23/23、governance 4/4 —— 无丢失、无重复**。本仓此前已有 3 次归档吞 anchor 前科，exit code 与 `specsUpdated` 字段均不作数；本次**首次零 anchor 损失**
- [x] 9.3.2 本 change 的 spec 内容在主 spec 中全部生效（7 个标记全中）
- [x] 9.3.3 peer 已提交内容**未被归档销毁**（4 个标记全中）
- [x] 9.3.4 相对归档前快照，**仅 4 个目标 block 变化**（`skeleton req-12`/`req-13`、`governance req-gov-1`、`wayfinder req-13`），其余全部逐字节相同
- [x] 9.3.5 归档后门禁：两 lint `exit=0`、`openspec validate --specs` 3/3

### 9.4 BLOCKED — 非本 change 引入，未处理

全套件 `pytest` 现为 **212 passed / 1 failed**：`tests/test_config.py::test_total_param_estimate` 断言 `total == 452_329_984`，实测 `452331008`（差 `1024`）。

**归因**：peer 的**未提交**改动 `src/decompmoe/config.py` —— `vocab_size: int = 32000` → `32001  # PROBE`（该 `# PROBE` 注释表明是调试残留）。本 change 从未触碰 `src/decompmoe/config.py` 或 `tests/test_config.py`，且本次 sync 只写入 3 个 spec 的 `.md`，不可能影响参数计数。

**未处理原因**：用户明确要求「在不干扰其他 session 工作结果的前提下操作」。该失败归 peer 自行处置。

本 change 自身覆盖范围复测：`tests/test_safeguards.py` + `tests/test_sphere.py` + `tests/test_schedule.py` = **73 passed**。

### 9.5 阻塞已解除（事后复核，2026-09-30）

§9.4 记录的 `tests/test_config.py::test_total_param_estimate` 失败**已不存在**。归因的调试残留 `src/decompmoe/config.py:59` 的 `32001  # PROBE` 已复原为 `32000`；该 PROBE 从未被提交（`config.py` 不在任何 commit 的改动清单中），系 peer 在工作树中自行撤销，故 §9.4 的归因与「未处理原因」在归档当时成立，事后已消解。

复测（`e50cc02` 状态下，工作树 `src/` 干净）：

- `python -m pytest -q` → **215 passed**（对比 §9.4 记录的 `212 passed / 1 failed`）
- `python scripts/lint_no_dead_defensive.py` → exit=0
- `python scripts/lint_no_source_field_drift.py` → exit=0
- `openspec validate --specs` → exit=0（3 passed）
- spec anchor 覆盖：wayfinder 36/36 · decompmoe-skeleton 23/23 · governance 4/4（唯一 anchor 数与 `### Requirement` 数逐 capability 相等）

§9.4 作为归档当时的实测记录**保留不改写**，本节仅解除其「未处理」状态。本 change 自身的 spec 与 test 改动自归档起未再变动。
