# 修复 B.2 Tests 冗余/格式三项 finding（B10 / B11 / B12）

## Why

Python reviewer 批次 B.2 的三项 finding 全部经 Explore agent 逐条事实核验。三项中有**两项的 finding 原文数字不成立**，需在修复的同时纠正记录；另有两项是**零测试红的叙述缺陷**（测试不红、lint 不红、spec 也不红），只能靠交叉校对发现。

| Finding | 位置 | 报告 severity | 核验结论 | 真实 severity |
|---|---|---|---|---|
| **B10** | `tests/test_safeguards.py:143,146` | LOW | 成立，但冗余对象是测试自身 setup literal 而非「行为断言」；且漏报同函数 docstring 一处**错误论断** | LOW（+1 处 docstring 错误） |
| **B11** | versine guard（finding 标 `test_sphere.py:268`） | MEDIUM | **部分成立**：窗口算术、`0.6140` 反例、偏差值三项均错；但「2× 宽于 literal 自身精度」成立 | MEDIUM |
| **B12** | `tests/test_schedule.py:60` | LOW | 成立；**断言正确，错的是 docstring 理由** | LOW |

## What changes

### B12 — stale spec 行号 + docstring 理由反了（纯 test 侧）

`tests/test_schedule.py` 的 docstring 引用 `spec req-13 L295`，当前 anchor 在 **L303**、正文在 **L307**。

过期归因经 `git show de96ba6~1` / `git show de96ba6` 实测：anchor 是在**该 commit 内**从「无、heading 在 L293」变成「anchor L293、heading L295」的，而 docstring 也是该 commit 写的 —— **所以 `L295` 在作者当时准确**（指向 heading 行），此后 spec 增长才使其 stale。不是出生即错。

更严重的是 docstring 的**理由反了**：`Phase 0 = SEEDING freezes everything by K-Means definition` 若按字面理解会推出**全集**，与同一 docstring 断言的 `set()` 自相矛盾。真相是 `phase_step_frozen_names` 返回的是「要冻结的 gradient-channel 名字集」，而 Phase 0 **根本没有 gradient channel**（`wayfinder/spec.md:83` "no gradient, no EMA"；phase 表 `requires_grad=False`），因此冻结名集合**必为空集**。断言本身正确，只有解释错误。

docstring 第二段的类比论证（返回 `{"c_i"}` 会破坏契约）同样不成立 —— Phase 0 的 gradient channel 全是 `requires_grad=False`，`{"c_i"}` 也不是 spec 认可的答案。改为「真正会破坏契约的是返回**非空**集合」。

### B11 — 4dp versine literal 不该用 `abs=1e-4` 钉

`test_versine_voronoi_closed_form` 用 `pytest.approx(0.6131, abs=1e-4)` / `pytest.approx(0.4771, abs=1e-4)` 钉 spec 的 **4 位小数显示值**。`abs=1e-4` 是 4dp 半单位 `5e-5` 的 **2 倍**，会放行不 round 到 literal 的值。

**实测（Explore 全精度）**：

| pin | 实际值 | 偏差 | 旧 `abs=1e-4` 窗口 |
|---|---|---|---|
| `0.6131` | `0.61311784093882848` | `1.784094e-05` | `[0.6130, 0.6132]` |
| `0.4771` | `0.47706599290487628` | `3.400710e-05` | `[0.4770, 0.4772]` |

**finding 原文的三处数字不成立**（在此纠正，不写入 spec）：

1. 窗口 `[0.6120, 0.6141]` 宽度 9e-4，等于按 `abs=1e-3` 算的；真实宽度 2e-4。
2. **`0.6140` 不通过**（`|0.6140−0.6131| = 9e-4 > 1e-4`），headline 反例被推翻。窗口内有效反例是 `0.6131999`。
3. 偏差是 `1.784094e-05` 不是 `1.71e-5`；且 finding 建议的 `abs=5e-5` 在 `0.4771` 上只剩 **1.47x** 余量。

**修法（按 `decompmoe-skeleton` req-6 L98 已确立的先例）**：4 位小数 spec 显示值用**精确 `round(x, 4) == literal`** 守护，不用放宽的 `approx` 容差。req-6 对 `θ` 的 4dp 显示值（`round(θ, 4) == 1.1735` / `round(math.degrees(θ), 2) == 67.24`）正是同一规则。两处偏差均 < `5e-5`，故 `round` 是精确判定而非近似放行。

**为什么不用 `abs=5e-5`**：即使采用 finding 的建议，`0.4771` 的余量也仅 1.47x，仍然脆弱；而 `round()` 无容差、无任意性，且与仓内既有先例同构。

### B10 — 恒真断言 + Δ = RATE_LIMIT 边界无守护

**恒真部分**：`L143` / `L146` 是 `300-(300-2300) >= RATE_LIMIT` 与 `300-(300-300) < RATE_LIMIT` 的字面折叠，`RATE_LIMIT` 一旦被 `L123` 钉死即为恒真，且与 `L149` / `L150` 的行为断言冗余。删除。

**漏报部分**（finding 未提）：同函数 docstring 写「a retune to e.g. `200` would not break the inequality assertion and would pass silently」——**实测为假**。`RATE_LIMIT=200` 时 `300 < 200` 为 `False`，不等式断言本身就会红（L123、L150 同样红）。删除该错误论断。

**边界部分（本次的主要 spec 交付）**：实现是 `if current_step - last_resurrection_step < rate_limit_steps: return set()`（`src/decompmoe/safeguards.py:93`），即 `Δ ≥ R` 放行、`Δ < R` 延后。现有测试只覆盖 `Δ=2300`（放行）与 `Δ=300`（延后），**`Δ` 恰等于 `R=1000` 无任何测试**；spec 措辞 "within the same 1000-step window" 在边界处二义，未钉 `<` vs `≤`。

按 `CLAUDE.md` §6 末条，此项不以 policy+code-first 论证关闭，须给出推导链 + 反例（见 `design.md` Decision 1）。

## Out of scope

- 其余 13 项 reviewer finding（本 change 处理的 3 项为 B10 / B11 / B12）。
- 不改 `src/` 任何行为 —— B10 的 `<` 读法经推导与全域实测（`Δ ∈ [0,2003]`，延后集恰为 `{Δ : Δ<1000}`）均已正确。
- 不清理未跟踪临时产物（`_bk/`、`_patches/`、`_staged/`、`_tmp_*.py` 等）—— 本 workspace 批量删除通道不可用，交由用户处理。
- 不修 `openspec validate --changes` 的 4 个既存失败（`2026-09-26-followup-...`、`fix-review-findings-voronoi-precision-and-lineage`，以及并行 session 的 `b13-b16` 与 `b15`）；本 change 自身 `openspec validate 2026-09-29-fix-b10-b11-b12-test-guard-fidelity` → **valid**。

## Review round

本 change 经独立 Python reviewer（`/code-review`，三轴：spec 数学 / 实现↔形式化 / TDD 原理约束）复核，**推翻 Rev 1 的 7 项结论**（2 CRITICAL）；随后按用户指示关闭本 session 内的**全部** findings，Rev 2 遗留的 HIGH-1 / MEDIUM-4 亦已闭合（Rev 3）。逐条留档见 `design.md` §7。

**Rev 1 → Rev 2**：

- 半开窗口「划分 / 同块 `⟺ Δ<R`」论证**为假**（窗口族交集 999 元素，非划分；`R` 对齐下 `t₁=999, t₂=1000` 构成前向反例）—— 即 `CLAUDE.md` §6 末条所要求的推导链本身有假命题。
- 「every `Δ ≥ R` is emitted」**被实现直接违反**（`safeguards.py:95-96` / `:100-101` 两条与限流无关的空返回路径）。
- 纠正 `2R = 2000` 的调用方契约假设、versine 被「angle claim」carve-out 覆盖的错误成因分析、B12 修复自身引入的 `wayfinder req-14` 错误归属。
- 新增 obligation 2/3 的 4-decimal-display 显式豁免（原文存在同 Requirement 内部的 `round()` vs "NOT bare `==`" 冲突），并把 spec 数值声明改为逐值对账（原 Rev 1 把 17 位实现值写进 spec 却无任何测试守护，违反 `CLAUDE.md` §6）。

**Rev 2 → Rev 3**（本 session 全部 findings 闭合）：

- **HIGH-1 关闭**：新增 `wayfinder` delta（req-13）。钉死 `Δ = R` **不**延后（窗口边缘排他），并纠正主语语义 —— 原 "only one resurrection event executes" 描述的每窗口配额**并未实现**（`safeguards.py:98-102` 返回全部合格 expert，无 one-per-window 裁剪）；限流实为**每次调用的延后闸门**，被 supersede 的读法明文留档。
- **MEDIUM-4 关闭**：`decompmoe-skeleton` req-13 新增 `#### Scenario: Phase-0 and Phase-4 freeze-name set is empty`，把此前只存在于 Requirement 正文的 "empty for phases 0/4" 提升为有 Scenario 承载的规范句。
