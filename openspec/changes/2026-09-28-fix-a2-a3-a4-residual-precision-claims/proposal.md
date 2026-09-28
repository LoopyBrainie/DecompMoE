# Proposal

## Why

三条 spec 数值 claim 缺陷全部源自 in-flight change `fix-review-findings-voronoi-precision-and-lineage`（46/47 done，apply 于 commit `b23f0e5` 2026-09-27）的 apply 阶段残留，**同源**，故合并为一个 change 一次收口：

1. **A2 —— 规范性 bound 失效**（`governance/spec.md:52`）。Scenario 声称三个 6dp test literal "each within `3e-7` of actual bisection output"，但 `b23f0e5` 的 H3/task 4.1.4 把 `N_e=64` literal 由 `1.020507` 改为 `1.020506` 时**未同步该 bound**。旧 literal 实差 `1.664e-7`（真在 3e-7 内），新 literal 实差 `8.3357e-7`（**2.78×**）。规范性的 `abs=1e-6` 仍覆盖，故今日无测试变红 —— 但一个被写进 Requirement 的数值 bound 处于**事实错误**状态，违反 `CLAUDE.md` §6 第 8 条"每个含具体数值的算式必须有可验对账"。

2. **A3 —— Requirement 内数值错误 + 测试锁定 stale 值**（`wayfinder/spec.md:578` + `tests/test_beta.py:98`）。反事实 `γ_init ≈ −6.7836` 在自称 5-sig 精度下错误，正确值为 `−6.783545399795103364342`（5-sig 即 `−6.7835`）。根因是该 change 的 reviewer finding **L3 原文写的正确值就是 `−6.78355`**，但 task **1.4.7** 实施时对 `−6.783545…` 作了 half-up 取整写成 `−6.7836`，并在 task **2.6.2** 把同值钉进 `tests/test_beta.py` —— 构成 `CLAUDE.md` §8 所述 *"tests `assert == stale_value` LOCKS 传染"* 通道。**只改 spec 会留下反向传染，必须同批改测试。**

3. **A4 —— frame 披露粒度不一致**（`wayfinder/spec.md:235`）。该文件已披露 true-CF residual（`4.15e-7`）但**未显式列出 angle-domain bias**；`decompmoe-skeleton/spec.md:116` 已正确列出（`~8.49e-7 rad` / `~8.79e-9 rad`）。两文件**详略不一致，非矛盾**。

## What Changes

- **A3（唯一需改真数值者）**
  - `wayfinder/spec.md:578` req-24 body：`γ_init ≈ −6.7836` → `−6.7835`，`σ'(-6.7836) ≈ 1.130e-3` → `σ'(-6.7835) ≈ 1.130e-3`。
  - `wayfinder/spec.md:584` req-24 `**Source:**` 追加本 change 反链。
  - `tests/test_beta.py` L88 docstring / L98 `gamma_cf` / L100 注释同步 `−6.7835`。
  - `tests/test_beta.py` 新增守护：由 spec 另一条声明 `γ_init ≈ −3.5` 独立反解 `β_0`，再由 `β_0` 反解反事实 `γ`，断言 `round(float(γ_full), 4) == -6.7835` + `γ_full == approx(-6.7835, abs=1e-4)`。该 `round` 形态正是**能捕获本次 bug 类**的守护（写 `-6.7836` 即失败）。
- **A2（governance）**
  - `governance/spec.md:52`：`each within \`3e-7\`` → `each within \`1e-6\``，与同 Scenario THEN 子句的规范性 `abs=1e-6` 对齐。三个 literal 与实际输出列表**保持不变**。此编辑**不引入任何新数值声明**（`1e-6` 已在同句出现并已被 `test_voronoi_monotone_in_ne` / `test_voronoi_canonical_N_e_dependence` 守护），**无需新增测试**。
  - `governance/spec.md:26` `**Policy lineage**` 追加 bound 失效 provenance。
- **A4（wayfinder 披露对齐）**
  - `wayfinder/spec.md:235` req-11 frame-disclosure 段追加 angle bias `(N_e=16, d_c=16) ≈ 8.49e-7 rad` / `(N_e=64, d_c=16) ≈ 8.79e-9 rad`。
  - `tests/test_sphere.py` 新增**双侧有界守护** `0 < |θ_impl − θ_true_cf| < 1e-6`，两个 `(N_e, d_c)` 各一。

**无 BREAKING 变更**：全部是 Requirement body 的数值 claim 修正 + 披露对齐 + 新增 additive 守护。

### Audit fact-check（清单 line ref → 当前真实位置 → 判定 → 根因）

| ID | 清单 line ref | 当前真实位置（`git show HEAD:<path>` 实测） | 判定 | 根因 commit / task |
|---|---|---|---|---|
| **A2** | `governance/spec.md:52` | `openspec/specs/governance/spec.md:52`（line ref 准确） | ✅ 成立（`1.020506` 实差 `8.3357e-7` = `3e-7` 的 **2.78×**） | `b23f0e5` H3 / change task **4.1.4**（改 literal 未改 bound） |
| **A3** | `wayfinder/spec.md:578` | `openspec/specs/wayfinder/spec.md:578`（line ref 准确） | ✅ 成立（正确 `−6.783545399795103364342` → 5-sig `−6.7835`） | change task **1.4.7**（末位 half-up 取整）+ task **2.6.2**（测试锁定） |
| **A4** | `wayfinder/spec.md:240` | 核心缺陷已于 `b23f0e5` H1 修复（task **1.1.1**）；残余为 `wayfinder/spec.md:235` 披露粒度 | ⚠️ **部分成立 → 降 LOW** | 残余为既有披露粒度不一致（见下） |

**A4 降级理由（实测）**：`b23f0e5` H1 已把 `1.1735482746999482 rad = 67.2393145636...°` 修正为 `= 67.23936319516639°`（60-dps 实测 `67.239363195166395823`，吻合）并补 `math.degrees(...)` provenance。60-dps 二分实测显示，bias 虽为 `8.4878e-7 rad`，但**三档显示全部对 frame 不敏感**：

| 显示档 | 真实数学根 | impl 输出 | 一致 |
|---|---|---|---|
| rad 4dp | `1.1735` | `1.1735` | ✅ |
| deg 2dp (round) | `67.24` | `67.24` | ✅ |
| versine 4dp | `0.6131` | `0.6131` | ✅ |

故"把 8.49e-7 rad 数值误差编码进 Requirement"的定性不成立；真实残余仅为 wayfinder 缺 angle bias 显式披露。

## Capabilities

### New Capabilities

无。本 change 不引入新 capability。

### Modified Capabilities

- `wayfinder`：
  - Requirement 24 "Beta Parameterization Space vs Operational Domain" — 反事实 `γ_init` / `σ'` 数值修正（A3）。
  - Requirement 11 "4070 MVP Hyperparameter Set" — frame-disclosure 段追加 angle bias（A4）。
- `governance`：
  - Requirement "Test Guard Precision for Closed-form Numerical Claims"（`req-gov-1`）— Scenario 中失效的 `3e-7` bound 修正 + Policy lineage provenance（A2）。

### `skip_specs` rationale

**不适用** —— 本 change 确实修改 spec Requirement body（wayfinder req-24 / req-11、governance req-gov-1），故按 schema 产出 `specs/wayfinder/spec.md` 与 `specs/governance/spec.md` 两份 delta，不设 `skip_specs: true`。

> 注：in-flight change `fix-review-findings-voronoi-precision-and-lineage` 与 `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` 均修改了 spec body 却无 `specs/` delta 目录（既有不一致）。**本 change 不复制该不一致、也不代劳回补**（见 Out of scope）。

## Impact

### Affected files

| 文件 | 组 | 操作 |
|---|---|---|
| `openspec/specs/wayfinder/spec.md` L578 | A3 | `−6.7836` → `−6.7835`（`γ_init` 与 `σ'(-6.7836)` 两处） |
| `openspec/specs/wayfinder/spec.md` L584 | A3 | req-24 `**Source:**` 追加本 change 反链（backtick-wrapped，第一 top-level item） |
| `openspec/specs/wayfinder/spec.md` L235 | A4 | frame-disclosure 段追加 angle bias `8.49e-7 rad` / `8.79e-9 rad` |
| `openspec/specs/governance/spec.md` L52 | A2 | `3e-7` → `1e-6` |
| `openspec/specs/governance/spec.md` L26 | A2 | `**Policy lineage**` 追加 bound 失效 provenance |
| `tests/test_beta.py` L88 / L98 / L100 | A3 | docstring + `gamma_cf` + 注释同步 `−6.7835` |
| `tests/test_beta.py`（新增断言） | A3 | `β_0` 反解 + `round(γ_full, 4) == -6.7835` 守护 |
| `tests/test_sphere.py`（新增测试） | A4 | 双侧有界守护 `0 < bias < 1e-6`，(16,16) 与 (64,16) |

**无 `src/` 实现变更。** 全部改动为 spec 数值 claim 修正 + 披露对齐 + additive 测试守护。

### Out of scope

- ❌ 任何 `src/` 实现变更（含当前工作树他人未提交的 `src/decompmoe/safeguards.py`）
- ❌ archive 或修改 in-flight change `fix-review-findings-voronoi-precision-and-lineage`（46/47，含 `[~]` Deviation 2.2.3）
- ❌ 触碰 in-flight change `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure`（3/16，anchor coverage 主题，无关）
- ❌ 补 `wayfinder/spec.md:235` 已有的 `4.15e-7` / `1.43e-9` residual 字面量的缺失守护（既有缺口，另开 cycle，避免范围膨胀）
- ❌ 触碰 `decompmoe-skeleton/spec.md`（L116 已正确，仅作对齐参照）
- ❌ GPU-only 声明（`W_proj ≈ 64 KB` / `0 bytes HBM` 等，本环境无 CUDA，按上一轮先例列 future scope）
- ❌ `dev → main` / `dev → release` 合并
- ❌ 回补既有 in-flight change 的 `specs/` delta（既有不一致，另开 cycle）

### Source back-link

- **`CLAUDE.md`** §6 第 8 条（"对账方式依数值类型二分"硬规则 —— 驱动 A3 测试加固与 A2/A4 的可验性要求）、§3 TDD convention、§8 ticket-stale 三传染通道（A3 根因判定依据）
- **`wayfinder/tickets/A4-1.md`**、`wayfinder/tickets/A6b-1.md`（req-24 既有 Source 反链，本 change 追加于其后）
- change `fix-review-findings-voronoi-precision-and-lineage` `tasks.md` task **1.1.1**（A4 核心已修）、**4.1.4**（A2 根因）、**1.4.7** + **2.6.2**（A3 根因）
- 本 change `design.md` Decision 1–4

### Risks / Trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| **并行 session 改动 working tree**（`src/decompmoe/safeguards.py` 当前有非本 change 的未提交改动） | High | apply 前后各跑 turn-start 审计（`git log --all --oneline -10` + `git reflog --date=iso` + `git status --short`）；**只 `git add` 本 change 涉及的文件**，绝不 `git add .` / `-A` |
| **行号漂移**：line ref 可能随 spec 演化失效 | Medium | apply 阶段所有行号必须 `git show HEAD:<path>` 实测确认，不得沿用本 proposal 或 audit 清单的行号 |
| **A3 精度陷阱**：以 5-sig 字面量 `−6.7835` 反推 `β_0` 残差约 `1.9e-6`（`|dβ/dγ| ≈ 0.03497` × `5.454e-5`），若误用 `abs=1e-12` 等紧容差必红 | Medium | design.md Decision 3 记录推导；采用 `round(..., 4)` 形态，对 5-sig 字面量天然安全 |
| **有界守护退化为恒真**：若写成 `bias >= 0` | Medium | 强制双侧 `0 < bias < 1e-6`；apply 后用 `-k` 单跑该测试确认它会因实现变更而失败 |
| **in-flight change 被误 archive** | Medium | Out of scope 显式声明；archive 属独立 workflow |
| **既有 change 缺 `specs/` delta** | Low | 本 change 照 schema 创建 delta；是否回补列为待决 |
