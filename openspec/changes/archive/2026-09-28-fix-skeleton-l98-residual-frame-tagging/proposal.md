# Proposal

## Why

`decompmoe-skeleton` req-6 的 SHALL 句在同一行里做了**两个 `< 1e-9` 残差声明**：

```
The implementation MUST compute this value via bisection on the equation (residual `< 1e-9`), NOT via a hard-coded table.
```

```
... SHALL return `1.173548 rad` (within `abs=1e-6` rad per req-gov-1 §3, with the bisection residual `< 1e-9`); ...
```

两者都**没有指明参考系**。而 `openspec/specs/governance/spec.md` L19-22 的 obligation 4（req-gov-1 §4「Residual frame disambiguation」）明文要求：

> Spec MUST clarify which frame is used for "< 1e-9" claims. Either frame is acceptable as long as the frame is explicit — **avoid silent reference-frame shifting.**

这不是措辞洁癖。两个声明在 **impl-internal 参考系**下为真、在 **true closed-form 参考系**下为假，实测差距跨 3 个数量级：

| 参考系 | N_e=16, d_c=16 | N_e=64, d_c=16 | `< 1e-9` 成立? |
|---|---|---|---|
| impl-internal（`_betainc_regularized`） | `1.1643e-14` | `1.9429e-15` | ✅ 是 |
| true closed-form（mpmath 精确积分） | `4.1457e-7` | `1.4273e-9` | ❌ **否**（两者均不满足） |

即：**同一句话在两个参考系下真值相反**。读者若按字面把 `< 1e-9` 理解成「对数学意义上的正则化不完全 beta 成立」，那这句话在 MVP 点上就是**假的**；而 spec 全文没有给出任何机制把它读成 impl-internal。这正是 obligation 4 要防的「silent reference-frame shifting」。

同 Requirement 的 Scenario 侧（`:102`、`:106`）**已经**带了 `(impl-internal frame per this Requirement's body)` 的标注，Scenario 侧合规、**body 侧裸奔**——缺口精确地落在 L98 的两个从句上。

## What Changes

### In scope

| 项 | 位置 | 变更 |
|---|---|---|
| **C** | `openspec/specs/decompmoe-skeleton/spec.md:98` | 两个 `< 1e-9` 从句各补 frame 标注：显式点名 `impl-internal frame per ... req-gov-1 §4`，并给出两个参考系各自的实测残差与「true closed-form 不满足 `< 1e-9`」的否定结论 |

净效果：**1 行长散文单行的 2 处从句替换**（1 删 1 增）。**不引入任何新数字** —— `1.16e-14` / `4.15e-7` 已写在 `governance/spec.md:20,21`，`1.94e-15` / `1.43e-9` 已写在同 Requirement 的 Scenario L114/L115（见 `design.md` Decision 4）。

### Out of scope

- **`openspec/specs/governance/spec.md` 零改动**。obligation 4 本身完全正确——它就是本 change 引用的权威条款。缺陷在**引用方**，不在规则方（`CLAUDE.md` §3 surgical）。
- **`openspec/specs/wayfinder/spec.md` 零改动**。`wayfinder:233` 与 Scenario `:274-276` 存在**完全同族**的未标注 `< 1e-9`（true closed-form 下 `4.1457e-7`，同样为假），但该 capability 的 delta 已被 `2026-09-28-fix-a2-a3-a4-residual-precision-claims` 与 `2026-09-28-fix-a7-flops-attribution-and-stale-ref` **两份** active change 占用。叠第三份 full-block `MODIFIED` delta 会在 archive 时**静默互相覆盖**（后归档者整块丢弃先归档者的编辑，不报错、不告警、lint 与 validate 全绿）。详见 `design.md` Decision 2。
- **不触碰任何并行 session 的 change 目录**（`a2-a3-a4` / `a6` / `a7` / `2026-09-26-followup-…`，均 untracked）。
- **不新增测试或 lint 规则**。本 change 是纯散文标注修正，无新行为可钉；且 `tests/test_sphere.py` 已被 `a2-a3-a4` 占用（其 A4 需要新增角度域偏差上界测试），再动会产生竞争编辑。
- **不修 `a2-a3-a4` 陈旧 delta 导致的 A5 回退风险**。只**报告 + 留可重跑的审计任务**，不代改他人 session 的 change 目录。详见 `design.md` Decision 3。

## Capabilities

### New Capabilities

（无。本 change 不引入新 capability。）

### Modified Capabilities

- `decompmoe-skeleton`: Requirement **req-6（Voronoi Self-Consistency Threshold）** 的 body 措辞变更 —— 为 L98 的两个 `< 1e-9` 残差声明补上 `req-gov-1 §4` 要求的参考系标注。**Requirement 的规范性行为、阈值、容差绑定关系一律不变**；这是消除歧义的标注，不是改变要求。

（`governance` 与 `wayfinder` **不在** Modified 列表内 —— 见 Out of scope。）

## Impact

- **Affected files（apply 阶段总账）**：
  - `openspec/specs/decompmoe-skeleton/spec.md` — edit L98（req-6 body，2 处从句）**仅此一行**
  - `openspec/changes/2026-09-28-fix-skeleton-l98-residual-frame-tagging/` 下的 4 类制品（proposal / specs ×1 / design / tasks）+ `.openspec.yaml` — create
- **代码 / API / 依赖**：**零变更**。`src/`、`tests/`、`scripts/`、`CLAUDE.md` 一行不动。无新增依赖。`canonical_voronoi_angle` 与 `_betainc_regularized` 的输出逐位不变。
- **测试**：`uv run pytest -q` 基线 `204 passed` 必须保持——本 change **零新增/零修改测试**。
- **Lint gate**：`lint_no_dead_defensive.py` 与 `lint_no_source_field_drift.py` 必须保持 `exit=0`（`CLAUDE.md` §3 archive 前置条件）。本 change 不修改 lint 脚本；`req-6` 的 `**Source:**` 反链字段逐字保留（delta 为 full-block 替换，Source 行在 block 内，已由往返验证守护）。
- **Anchor coverage**：wayfinder 36/36、decompmoe-skeleton 23/23、governance 4/4 = 100%，必须不变（只改 body 措辞，不增删 Requirement）。
- **Git**：单 commit on `dev`（`CLAUDE.md` §4），HEAD 不落在 merge commit 上。

## Source back-link

- **`CLAUDE.md`** §2（spec 为最高真相源）、§3（surgical 修改 + archive 前置两个 lint `exit=0` + source 反链规则）、§4（单 commit on `dev`）、§5（`d_c = 16` 冻结、`θ_Voronoi(16,16) ≈ 67.24° (1.1735 rad)` 的 4dp 冻结形式）
- `openspec/specs/governance/spec.md` req-gov-1 **§4（L19-22，「Residual frame disambiguation」）** —— 本 change 引用的权威条款，其 "Spec MUST clarify which frame is used" 一句即是本 change 存在的理由
- `openspec/specs/decompmoe-skeleton/spec.md` req-6 Scenario **L102 / L106** —— 同 Requirement 内**已合规**的 frame 标注写法，本 change 使 body 与之对齐
- `openspec/specs/decompmoe-skeleton/spec.md` req-6 Scenario **L114 / L115** —— `1.94e-15` / `1.43e-9` 两个数字的既有出处（本 change 引用而非新造）
- commit `b23f0e5` —— 缺陷的 pre-existing 载体（两处从句在该 commit 即已存在，非本 change 引入）
- 归档 change `2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding`（commit `33deb9b` / `e5fec3a`）—— 本 change 是其同族缺陷清单中**唯一落在空闲 capability** 的残余项
