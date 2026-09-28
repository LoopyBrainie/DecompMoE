# Tasks

> **Apply 顺序说明**：`proposal.md` §Affected files 把主 spec 正文改动列在 apply 阶段；但本 change 同时携带 `specs/*/spec.md` delta，archive 阶段会再用 delta 同步主 spec。因此 4.x 有一道 **delta ≡ 主 spec 一致性门禁**，确保两个新 Scenario 不会被重复插入。
>
> 每组自带其所需的测试与文档改动；第 4 组只做跨组集成门禁。

> **提交归属事故（2026-09-28 17:38，事后记录）**：本 change 的 10 个文件中，**9 个被并行 session 的 commit `bdbc978`（"chore(opsx): archive 2026-09-28-fix-skeleton-l98-residual-frame-tagging"，提交于 17:38:05）一并带走** —— 原因是 git index 为共享状态，对方的 commit 提交了整个 index，把我已 `git add` 但尚未 commit 的文件卷入了。只有 `tasks.md` 落在归属正确的 commit `0fd5358`（17:38:24）。
>
> - **内容完整性已复核**：9 个文件全部正确进入工作树 —— A3（`wayfinder/spec.md` L590 Source 含 `−6.783545399795103364342`）、A2（`each within \`1e-6\``）、A4（`8.4878023e-7` ×2）、两个新测试函数均在位；`uv run pytest -q` → **206 passed**；两个 lint gate `exit=0`。**不存在内容丢失。**
> - **性质**：提交归属（audit trail）问题，不是内容正确性问题。
> - **§0.2 的教训**：只 `git add` 指定路径**不足以**隔离共享 index —— 只要文件进了 index，另一次 `git commit` 就会连带提交。真正隔离需要 `git commit -- <paths>`（仅提交指定路径）或独立 worktree。**后续并行场景应改用 `git commit -- <显式路径列表>`。**
> - 是否重写历史把 9 个文件从 `bdbc978` 拆出，属**用户决策**（并行 session 正在同一分支上提交，改写其 commit 有丢失对方工作的风险）—— 本 change 不擅自改写。

## 0. 阻塞前置 — 与并行 change `2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding` 的排序冲突

> **实测状态（2026-09-28 本 change propose 阶段发现）**：HEAD 仍为 `b23f0e5`（未变），但工作树已被**并行 session** 改动，且改动**与本 change 的 A4 目标区域重叠**：
>
> - `openspec/specs/wayfinder/spec.md` req-11 **Display precision note**（L240 / L241 两行）已被重写
> - `openspec/specs/decompmoe-skeleton/spec.md` req-6 同段落已被重写
> - 并行 change `openspec/changes/2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding/` 已存在（处理 A1 / A5，与本 change 的 A2 / A3 / A4 是不同条目）
>
> 本 change 的两份 delta 是从 **`b23f0e5`（HEAD）** 抽取原文后程序化构造的，因此**对 HEAD 逐字有效**；但若 apply 时从已被改过的工作树抽取，req-11 的 verbatim 基座就会漂移。本 change 的两条 A4 改动（definitional-layer 段追加 angle bias、display note 末行追加"两量不可混淆"声明）与并行 change 的重写落在同一 Requirement 的相邻段落。
>
> **apply 阶段（2026-09-28 15:29）实测复检 —— 阻塞成立，已暂停等待用户处理 A1/A5 的 archive**：
>
> - HEAD 已前移到 **`33deb9b`**（"fix(spec): rebind abs=1e-6 to the 6dp Voronoi literal; drop phantom §2 tolerance grant"）。A1/A5 的编辑已进主 spec 并 commit，但 change 仍为 **39/39 未 archive**，且仍持有 `wayfinder` req-11 与 `decompmoe-skeleton` req-6 的 delta。
> - **req-11 verbatim 基座已漂移**：结构化 diff 显示 req-11 比 propose 时多出一个 `[replace] src[9:11]` op，命中 Display precision note 的两条 bullet。**照现状 apply + archive 会静默回退 `33deb9b` 的 display-note rebinding。**
> - **archive 顺序硬约束**：OpenSpec archive 按 Requirement **整块覆盖**。本 change 与 A1/A5 各自持有一份 req-11 delta，两者都未 archive → **后 archive 者静默丢弃先 archive 者的全部 req-11 编辑**，不报错、不告警、lint 与 validate 全绿。必须先 archive A1/A5。
> - **未漂移、可立即 apply 的部分**：`governance` req-gov-1（3 replace + 1 insert）与 `wayfinder` req-24（2 replace + 1 insert）的 diff op 与 propose 时完全一致 → **A2、A3 无阻塞**；仅 A4 的 req-11 段被卡住。
> - **实施代码已变但 A4 数值结论仍成立**：`33deb9b` 改了 `src/decompmoe/sphere.py::_betainc_regularized`（移除 `n=60` 细分参数）。实测 `canonical_voronoi_angle(16, 16)` 仍返回 `1.17354827469994816`（**逐位未变**），偏差仍为 `8.4878e-7 rad` / `8.7898e-9 rad`，`0 < bias < 1e-6` 仍成立 → **A4 的 spec 数字与"有界守护"决策均无需更改**。该结论已按 design.md Decision 2 的意图验证（求积实现变了，守护不红）。

- [x] 0.1 **确认排序**：`2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding` 必须先 commit（必要时 archive），使 req-11 的 display precision note 段落稳定。**若该并行 change 先落地，本 change 的 req-11 delta 必须基于落地后的版本重新构造**（重跑 delta 构造脚本；断言命中数不为 1 时按新文本更新锚点，不得手工修补）。验证：`git show HEAD:openspec/specs/wayfinder/spec.md` 中 req-11 display note 段与本 change delta 的 verbatim 基座一致
- [x] 0.2 **不得把并行 session 的未提交改动混入本 change**：commit 时只 `git add` 本 change 涉及的文件；`src/decompmoe/safeguards.py`、`openspec/specs/decompmoe-skeleton/spec.md` 的既有未提交改动**不得**被本 change 的 commit 携带。验证：`git show --stat HEAD` 只列出本 change 制品与本 change 明确 apply 的 spec/tests 文件
- [x] 0.3 记录与并行 change 的语义边界，避免 archive 时重复插入：并行 change 处理**4-decimal 显示形与 tolerance 的绑定关系**（A1/A5），本 change 处理**angle-domain bias 披露**（A4）；两者可互补，但 req-11 display note 段落的最终措辞须由 0.1 确定的顺序裁决。验证：4.2 的 delta ≡ 主 spec 一致性检查通过

## 1. A3 — 反事实 `γ_init` 末位取整修正（spec + test 双点，MAJOR）

**背景**：上一轮 change 的 reviewer finding L3 给出的正确值是 `−6.78355`，task 1.4.7 实施时对 `−6.783545…` 作 half-up 取整写成 `−6.7836`，task 2.6.2 又把同值钉进 `tests/test_beta.py` → 构成 `CLAUDE.md` §8 "tests `assert == stale_value` LOCKS 传染"。**必须同批修 spec 与 test。**

- [x] 1.1 `openspec/specs/wayfinder/spec.md` req-24 body：`γ_init ≈ −6.7836` → `−6.7835`，`σ'(-6.7836)` → `σ'(-6.7835)`。**注意源文混用两种减号字形**：`γ_init ≈ −6.7836` 用 U+2212，`σ'(-6.7836)` 用 ASCII 连字符。验证：req-24 block 内 **`6.7836` 仅作为被否值出现**（`grep -n "6\.7836"` 的每一处命中都必须落在 1.2 新增 Scenario 的 "NOT `−6.7836`" 及其对照句中，不得出现在任何断言性正文里）—— 注：原判据写作「`grep -c` 返回 0」，被 1.2 自己引入的合法 `−6.7836` 引用作废，故改为上述「仅作被否值」判据
- [x] 1.2 `openspec/specs/wayfinder/spec.md` req-24 追加新 Scenario `Counterfactual β_min = 1.0 forces a 5-significant-figure γ_init`（WHEN/THEN/AND/AND 四条，与 `specs/wayfinder/spec.md` delta 逐字一致）。验证：`grep -c "5-significant-figure γ_init"` 返回 1
- [x] 1.3 `openspec/specs/wayfinder/spec.md` req-24 `**Source:**` 追加 `` change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` design.md (Decision 3 — …) ``，**保留 `wayfinder/tickets/A4-1.md` 为第一个 top-level item**。验证：`python scripts/lint_no_source_field_drift.py` `exit=0`
- [x] 1.4 `tests/test_beta.py::test_counterfactual_floor_1_gamma_starvation`：docstring、`gamma_cf = mpmath.mpf("-6.7836")`、行内注释三处同步 `−6.7835`。**初次 apply 只完成前两处**（docstring + `gamma_cf`），行内注释仍留 `σ'(−6.7836)` 与一个会随 spec 编辑漂移的行号引用（写作 `Spec L578`，而 req-24 body 实际在 L584）—— 属 §8 finding C-3，已补齐：改为引用 Requirement id `req-24`（行号在 spec 编辑下会漂移，Requirement id 不会）。验证：该测试两条既有断言仍通过（实测 `σ'(−6.7835) = 1.1297450077e-3`，距 `1.130e-3` 差 `3.10e-7 < abs=1e-6`；`ratio = 25.1854 ∈ [23.75, 25.00×1.05]`）
- [x] 1.5 `tests/test_beta.py` 新增守护：`mpmath.mp.dps ≥ 50` 下由 adopted-path 声明 `γ_init ≈ −3.5` 独立反解 `β_0 = 0.1 + 31.9·σ(−3.5)`，再由 `(β_0−1)/31` 反解 `logit` 得 `γ_full`；断言 `round(float(gamma_full), 4) == -6.7835` 与 `gamma_full == pytest.approx(-6.7835, abs=1e-4)`，各带 `f"actual={...}"`。**容差不得用 `1e-12` 量级** —— 5-sig 字面量 `−6.7835` 与精确根的 γ-空间间隙为 `4.5399795e-5`（`abs=1e-4` 给出 `2.2×` 余量），其 β-空间等价残差为 `1.5899599e-6`（`4.5399795e-5 × |dβ/dγ| = 4.5399795e-5 × 0.0350220952386`）。**（原记录写作「残差约 `1.9e-6`（`|dβ/dγ| ≈ 0.03497` × `5.454e-5`）」系把被否字面量 `−6.7836` 的量搬到了新字面量上：`-6.7836` 的 β-残差才是 `1.9120749e-6`、斜率 `0.0350186011251`、γ-间隙 `5.4600205e-5`；`−6.7835` 的三个数见上。见 §8 finding S-3）** 测试内须写明该守护是两条独立 spec 声明的交叉对账、**非** helper-tautology。验证：`uv run pytest tests/test_beta.py -v` 全绿
- [x] 1.6 **mutation sanity**：把 1.5 的期望临时改回 `-6.7836`，`round(gamma_full, 4) == -6.7836` 必须**失败**；确认后还原。验证：断言确实能捕获本次 bug 类

## 2. A4 — angle-domain bias 披露对齐 + 双侧有界守护

**背景**：A4 的核心（跨 frame 假等式）已在 `b23f0e5` H1 修掉；残余缺口仅 `wayfinder` 未显式列 angle bias、而 `decompmoe-skeleton` req-6 已列。60-dps 实测 bias `8.4878023e-7 rad` / `8.7898467e-9 rad`，且 4dp rad / 2dp deg / versine 4dp 三档显示对 frame 均不敏感。

- [x] 2.1 `openspec/specs/wayfinder/spec.md` req-11 definitional-layer 段：追加 angle-domain bias `≈ 8.49e-7 rad`（N_e=16）/ `≈ 8.79e-9 rad`（N_e=64）+ 50-digit 精确值 + 与 `decompmoe-skeleton` req-6 的同源声明。验证：`grep -c "8.4878023e-7"` 返回 1
- [x] 2.2 `openspec/specs/wayfinder/spec.md` req-11 display precision note 末行追加：angle-domain bias（impl-frame vs exact-root）与 prose-rounding gap 是**两个不可混淆的量**。验证：与 2.1 同处 req-11 block 内
- [x] 2.3 `openspec/specs/wayfinder/spec.md` req-11 `**Source:**` 追加本 change 反链（Decision 2），保留 `wayfinder/tickets/A5-3.md` 为第一 item。验证：`lint_no_source_field_drift.py` `exit=0`
- [x] 2.4 `openspec/specs/wayfinder/spec.md` req-11 追加新 Scenario `Impl bisection output lies within 1e-6 rad of the exact equation root`（与 delta 逐字一致）。验证：`grep -c "lies within 1e-6 rad of the exact equation root"` 返回 1
- [x] 2.5 `tests/test_sphere.py` 新增守护：对 `(N_e, d_c) ∈ {(16,16), (64,16)}`，用 50-digit mpmath 二分求 `½·I_{sin²θ}((d_c−1)/2, ½) = 1/N_e` 的精确根，断言 `0 < abs(theta_impl − theta_exact) < 1e-6`，带 `f"actual={...}"`。**下界必须是严格 `0 <`**，写成 `>= 0` 会使下界恒真、整条守护退化为只查上界。`test_sphere.py` 若未 import `mpmath` 则在本测试内局部 import。验证：`uv run pytest tests/test_sphere.py -v` 全绿
- [x] 2.6 **mutation sanity**：把上界临时收紧到 `1e-9`，测试必须**失败**（证明上界非空转）；另用 `grep` 确认源码写的是 `0 <` 而非 `>= 0`（下界只能靠 review 拦截，测试无法自证）；确认后还原

## 3. A2 — governance proximity bound realignment + obligation 6

**背景**：bound 失效根因是 `b23f0e5` H3 / task 4.1.4 把 literal `1.020507`（实差 `1.664e-7`）改为 `1.020506`（实差 `8.336e-7` = `2.78×`）却未同步 bound。规范性的 `abs=1e-6` 仍覆盖，故今日无测试变红 —— 性质是**过时 prose bound**，不是可验断裂。

- [x] 3.1 `openspec/specs/governance/spec.md` bisection Voronoi Scenario：`(each within \`3e-7\` of actual bisection output …)` → `\`1e-6\`` + 括注实测差值与 realignment 理由。三个 literal 与实际输出列表**保持不变**。验证：`grep -c "each within \`1e-6\`"` 返回 1
- [x] 3.2 `openspec/specs/governance/spec.md` req-gov-1 新增 **obligation 6**（改 literal 不得静默作废 proximity bound；bound 不得严于本 Scenario 自己的规范容差）。验证：obligation 编号 1–6 连续无重复
- [x] 3.3 `openspec/specs/governance/spec.md` `**Policy lineage**` 追加 bound 失效 provenance（`3e-7` → `1.020507` 实差 `1.664e-7` → task 4.1.4 改 `1.020506` 实差 `8.336e-7` → realign 到 `1e-6`）。验证：与 3.1 同文件
- [x] 3.4 `openspec/specs/governance/spec.md` `**Source:**` 追加本 change 反链（Decision 1），**保留 `CLAUDE.md` 为第一个 top-level item**。验证：`lint_no_source_field_drift.py` `exit=0`
- [x] 3.5 确认本组**不引入任何新的无守护数值声明**：obligation 6 与 Scenario 括注中的 `1e-6` 即本 Scenario 已有的规范性容差（已由 `test_voronoi_monotone_in_ne` / `test_voronoi_canonical_N_e_dependence` 守护），因此**无需新增测试**。验证：`grep -n "1e-6" openspec/specs/governance/spec.md` 中新增行的 `1e-6` 均与 obligation 3 / Scenario THEN 子句同值
- [x] 3.6 验证残留 `3e-7` 仅存在于 3 处**说明性**位置：obligation 6、Policy lineage provenance、Scenario 括注理由。验证：`grep -n "3e-7" openspec/specs/governance/spec.md` 返回 3 行且逐行可归入上述三类

## 4. 集成门禁（跨组检查）

- [x] 4.1 **delta 漂移防护**：重跑 delta 构造/断言脚本，确认所有定点替换的命中数仍为 1（任一不为 1 立即停止，不做手工修补）。验证：脚本 `exit=0`
- [x] 4.2 **delta ≡ 主 spec 一致性**：主 spec 应用 1.x / 2.x / 3.x 后，重跑结构化 diff，确认 delta block 与主 spec block 之间**只剩预期差异**（即 delta 描述的正是已应用内容），从而 archive 阶段不会重复插入两个新 Scenario。验证：diff 中无 `design.md design.md`、无时间戳漂移、无 Scenario 重复
- [x] 4.3 `python scripts/lint_no_source_field_drift.py` → `exit=0`；`python scripts/lint_no_dead_defensive.py` → `exit=0`
- [x] 4.4 anchor 覆盖率仍 100%：wayfinder 36/36、governance 4/4、decompmoe-skeleton 23/23（本 change 只改 Requirement body，不新增/删除 Requirement；Scenario 为 `####` 四级，不影响 anchor 计数）。**skeleton 的 22/23 缺口已于 `9017a94` 由并行 change `2026-09-28-fix-skeleton-l98-residual-frame-tagging` 归档闭合**，本 change 不 stage、不代修该文件。
- [x] 4.5 `uv run pytest -q` 全绿 —— **实测 206 passed**（HEAD `9017a94` 基线 204 + 本 change 新增 2 条守护）。**（原记录写「199 基线」系误记，reviewer 已指出；reviewer 给出的 204 亦为 HEAD 实测基线，本 change 自身新增 2 条，故正确总数为 206）**
- [x] 4.6 单 commit on `dev`；`git log -1 --pretty=%P` 只有一个 parent（HEAD 不在 merge commit）；`git show --stat HEAD` **不含** `src/decompmoe/safeguards.py`、`src/decompmoe/sphere.py` 及任何并行 change 目录（他人未提交改动不得被 stage —— **只 `git add` 本 change 涉及的文件，绝不 `git add .` / `-A`；且按 §0.2 教训，路径边界放在 `git commit -- <paths>` 而非 `git add`**）

## 5. 本 change 明确不做（Deferred / Out of scope）

- **B1 helper-tautology 闭环 —— 已由外部 change 承接（不再是本 change 的 deferred item）**：`governance` req-gov-1 Scenario 的括号句曾承认 `tests/test_extraction.py::test_complexity_budget` 使用 helper-tautology 形态。闭环由 `2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity` task 4 完成（AST 实测 + 与 `33_040` 裸 `==` 对账），本 change 的 `req-gov-1` 整块 delta 已同步更新该括号句（见 design.md Decision 6）。**理由**：本 change 已持有 `req-gov-1` 的整块 delta，另开第二份会被 archive 静默覆盖。clause (3) 的前瞻性要求原样保留。

- **β_0 精度补全（deferred，可丢弃）**：`wayfinder/spec.md` req-24 现有 `β_0 ≈ 1.035` 仅 3dp，而 `γ_init` 声明为 5-sig —— 前提精度低于结论精度。可追加 50-dps 推导披露（`β_0 = 1.0350601609682665718` 与 `γ = −6.783545399795103364342`）使 5-sig 结论有精确前提。**按已批准 plan §7.1 推迟**；A3 核心修复不受影响。若要做，应另开 change（会改 spec，按 `openspec instructions tasks` 的 Open Questions 规则不得在本 change 内塞入未决范围）。
- 不 archive、不修改、不推进 in-flight change `fix-review-findings-voronoi-precision-and-lineage`（46/47）与 `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure`（3/16）—— 仅在 Source 反链中引用前者。
- 不回补上述两个 in-flight change 缺失的 `specs/` delta（既有不一致，另开 cycle）。
- 不为 `wayfinder/spec.md` 既有 `4.15e-7` / `1.43e-9` residual 字面量补守护（既有缺口）。
- 不动 `decompmoe-skeleton/spec.md`（req-6 已正确，仅作对齐参照）。
- 不动任何 `src/`；不追 GPU-only 声明（`W_proj ≈ 64 KB` / `0 bytes HBM` 等，本环境无 CUDA）；不做 `dev → main` / `dev → release` 合并。

## 6. Code review record（2026-09-28，agent `agent-b1a39f2827bf` "Python reviewer"）

一次 `/code-review` 针对本 change 产出 4 类 finding。**每条都在动手前由本 agent 独立复算验证**，未按报告原话采信；reviewer 判定的**不可 archive** 状态已由下述修复解除。

### 6.1 已在本 change 内修复（4 条）

- [x] 6.1 **S-2 (MAJOR) — 本 change 自己引入的假机制描述。** `wayfinder` req-11 body 原写 `Gauss–Legendre 8-point / 60-segment` 的 `_betainc_regularized`，而 `src/decompmoe/sphere.py:64-65` 明写「A **single** 8-point Gauss–Legendre panel is applied on `[0, x]`; there is **no subdivision**」—— 且该句同时把 `decompmoe-skeleton` req-6 当对齐参照引用，而 req-6 讲的正是「单面板无细分」，构成**自相矛盾**。修复：wayfinder req-11 body 与 `governance` req-gov-1 obligation 4 的两处（`60 subintervals` / `60-segment`）统一改为 **`a single 8-point Gauss–Legendre panel on [0, x], no subdivision`**，与 `sphere.py` 源码及 skeleton req-6 L116 三方一致。**同时折入归档 change `2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding` §9.1 的另一半**：`governance` L21 的 `< 1 ppm` 原是**对函数自身相对误差**的假界（实测 `6.633 ppm`，超 `6.6×`）。现限定为 **θ 偏差**界（`0.72 ppm` @ `N_e=16`、`0.0086 ppm` @ `N_e=64`，均 < 1 ppm ✓），并显式写出函数自身相对误差 `6.63 ppm` —— 与 skeleton req-6 L116 措辞对齐。**归属确认**：§9.1 明确标注该处被本 change 争用（`governance` L26 + L52），条件是「apply only after that change is archived」，而该 change 现已于 `9017a94` 前的 commit 中归档，故本 change 承接。
- [x] 6.2 **S-3 (MINOR) — 把旧字面量的导数搬进了新字面量。** `wayfinder` req-24 新 Scenario 与 `tests/test_beta.py` 注释原写「`~1.9e-6` 残差 / `|dβ/dγ| ≈ 0.03497`」。实测：`1.9e-6` 是**被否字面量** `−6.7836` 的 β-残差（`1.9120749e-6`），不是新字面量 `−6.7835` 的（`1.5899599e-6`）；`0.03497` 两个字面量都不对（`−6.7835` 为 `0.0350220952386`）。修复：spec 与测试注释全部改用实测值，并**按 frame 拆开陈述** —— γ-空间间隙 `4.5399795e-5`（`abs=1e-4` 即 `2.2×` 余量，实测 `1e-4 / 4.5399795e-5 = 2.2026531`）与其 β-空间等价残差 `1.5899599e-6 = 4.5399795e-5 × 0.0350220952386`（线性化与精确值相对偏差 `2.3e-5`）。同时补上原先**根本没写**的 γ-空间间隙 —— 支撑 `abs=1e-4` 的正是它，不是 β-残差。
- [x] 6.3 **C-3 (MINOR) — task 1.4 只做 3 分之 2 却标 `[x]`。** `tests/test_beta.py` 三处同步里，docstring 与 `gamma_cf` 已改，行内注释仍留 `σ'(−6.7836)` 与一个**会随 spec 编辑漂移**的行号引用（原写 `Spec L578`，req-24 body 实际在 L584）。修复：注释改引 Requirement id `req-24`（行号会漂移，id 不会）。**连带修正 task 记录本身**：1.4 的 `[x]` 记录补上遗漏项，1.1 的验收判据「`grep -c "6\.7836"` 返回 0」被 1.2 自己引入的合法 `−6.7836` 被否值引用作废，改为「仅作被否值出现」。
- [x] 6.4 **P-1 (MAJOR) — 全量未提交。** 本 change 的全部内容在 review 时均处于未提交状态，archive 前必须落为 `dev` 上的单个 linear commit。修复：见 §7。

### 6.2 修复后门禁（全部实测，非引述）

| 门禁 | 结果 |
|---|---|
| `uv run pytest -q` | **206 passed** |
| `python scripts/lint_no_source_field_drift.py` | `exit=0` |
| `python scripts/lint_no_dead_defensive.py` | `exit=0` |
| anchor 覆盖 | wayfinder **36/36** · skeleton **23/23** · governance **4/4** |
| `openspec validate <change> --strict` | valid |
| `openspec validate --specs` | 3 passed / 0 failed |
| delta ≡ 主 spec | req-11 / req-24 / req-gov-1 三块逐块 **IDENTICAL** |
| delta 字节 | LF、无 BOM（`b"\r" not in raw`，全部制品 `ok`） |

**自审抓到的一处 delta 污染（已修，单独后续 commit）**：首次提交时 governance delta 是**从工作树**重建的，而工作树的 `req-gov-1` 里带着 b1-b3 在途的 `test_complexity_budget` 括号句改写；同一 hunk 在**主 spec 侧被我的选择性暂存排除**了。于是「提交的 delta」≠「提交的主 spec」。`openspec archive` 是**逐块原样插入** delta，届时会把 b1-b3 的 spec 编辑**借本 change 的手**静默写进主 spec —— 而 §4.2 的 delta≡主 spec 校验当时是拿工作树跑的，抓不到。修法：delta 改为从 **HEAD 的主 spec blob** 重建，并新增一条**以提交对象（`git show HEAD:…`）而非工作树**为输入的 archive 前置校验（`delta ≡ HEAD 主 spec` + delta 字节 LF/BOM）。**教训：凡是把「工作树」当基准的校验，在选择性暂存之后都不再等价于「将被提交的状态」；archive 类校验必须锚定 commit。**

**mutation sanity（本 change 两条新守护，均以独立脚本执行、不改动工作树，避免与并行 session 抢同一测试文件）**：

- A3 `round(float(gamma_full), 4)`：baseline `-6.7835` 成立 ✓；换成 `-6.7836` **不成立** ✓（捕获原始 bug 类）；`abs=1e-12` **不成立** ✓、`abs=1e-6` **不成立** ✓（证明 5-sig 字面量确实需要 slack，且 `1e-6` 这个 Voronoi 家族惯用容差**不足以**覆盖 γ-间隙）；`abs=1e-4` 成立 ✓。
- A3 **β-空间无法区分两个字面量**（新增的负向论证）：β-残差 `1.5899599e-6` vs `1.9120749e-6`，比值 `1.2025931` —— 任何 `abs ≥ 1.9120749e-6` 的 β-空间断言对两者都通过，故**判别断言必须在 γ-空间**（`round(γ_full, 4) == -6.7835`，`−6.7836` 差 `1e-4` 而失败）。此论证已写入 spec req-24 Scenario。
- A4 双侧界 `0 < bias < 1e-6`：`N_e=16` bias `8.487802307e-7`、`N_e=64` bias `8.789846688e-9`，两者均 `0 < bias < 1e-6` 为 **True** ✓；把上界收紧到 `1e-9` 后两者均为 **False** ✓（证明上界非空转）。

### 6.3 已上报但**不在**本 change 授权范围内（属其他并行 change，未代修）

用户授权范围是「本 session 内的 findings」。以下属 reviewer 报告但归属其他 change，**仅上报、不动手**：

- **C-8**：`tests/test_beta.py:111` / `:265` 的 `pytest.approx` 改写 → 属 `2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity` tasks 3.4/3.5。另 `ruff check tests/test_sphere.py` 当前因该 change 的 import 顺序失败。
- **C-5**：新测试只覆盖 MVP 点，硬编码表仍可逃逸；建议追加 MVP 外的 `(N_e, d_c)`。
- **S-5 / S-6 / S-7 / S-8 / S-9**：LOW/MINOR 措辞质量项。
- **C-6**（本 change 自有，但 reviewer 自评为「未决论辩而非疏漏」）：严格下界 `0 < bias` 在 double 下不可能失败（bias 由求积截断误差主导），docstring 声称的「排除巧合」保证无法兑现。MUT3 已证明合法精度改进仍通过，且它至少阻止后人简化成 `>= 0`。**决定：暂不动**，保留为已知未决论辩。

## 7. 提交

- [x] 7.1 按 §0.2 教训，路径边界放在 **commit** 而非 add：`git commit -F <msgfile> -- <显式路径列表>`；**不**用 `git add -A` / `git add .`。提交后用 `git merge-base --is-ancestor <sha> HEAD` 复查可达性 —— 并行 session 在本 session 期间多次移动 HEAD 并 `git reset`，`git log` 里看得到并不等于可达（§0.1 记录的 3 个 commit 即因此变 dangling）。
- [x] 7.2 `git show --stat HEAD` 文件数与预期清单逐项比对，确认未夹带 `src/decompmoe/safeguards.py`、`src/decompmoe/sphere.py`、`tests/test_{config,extraction,metrics,safeguards,schedule,viz_protocols}.py` 或任何其他 change 目录。
