# Proposal

## Why

`CLAUDE.md` §5「MVP Hyperparameters（frozen）」块的 `β_0 ≈ 1.0` 是全仓最后一处 stale 的 `β_0` 字面量。spec canonical 值是 `β_0 ≈ 1.035`（`openspec/specs/wayfinder/spec.md:130` / `:578` / `:589`，`openspec/specs/decompmoe-skeleton/spec.md:483`），`src/decompmoe/config.py:55` 与 `tests/test_beta.py:38` 也已同步为 1.035。独立复算：`σ(−3.5) = 0.02931223075135632`，`β_0 = 0.1 + 31.9·σ(−3.5) = 1.0350601609682666`，`1.0` 偏差 **−3.39%**。

根因是**两段历史叠加**（`git log -S 'β_0 ≈ 1.0）' -- CLAUDE.md` 实测）：

1. **引入** —— `0d87e32`（2026-08-19，`feat(skeleton): implement DecompMoE MVP skeleton + 85 TDD tests`）创建 `CLAUDE.md` 时即写入 `β_0 ≈ 1.0`。该值此后从未被任何 commit 改动。
2. **未同步** —— `b23f0e5`（2026-09-27）触碰了同一冻结块的**相邻 θ 行**（`1.1736 rad → 1.1735 rad`，其 MEDIUM finding M1）却未同步本行：`git show b23f0e5 -- CLAUDE.md` 显示该 commit 对 `CLAUDE.md` 的 diff 恰好只有一个 hunk、一行替换。

即 `b23f0e5` **不是引入者，是漏同步者**；本 change 的修复责任在 (2)，而 stale 值的年龄始于 (1)。

`CLAUDE.md` 由此内部自相矛盾：§8 明确宣称三条 ticket→spec 传染通道「传染链已断」并给出三步修复协议，而 §5 仍摆着被协议 (a) 修掉的原值。读者若以 §5 为准，会重新引入 §8 已判定为失效的 stale 数值。

## What Changes

- `CLAUDE.md` §5 冻结块单行替换：`（β_0 ≈ 1.0）` → `（β_0 ≈ 1.035）`。

**无 BREAKING 变更。** 纯叙述摘要对齐，无 Requirement 变更、无 `src/` 变更、无测试变更。

## Capabilities

### New Capabilities

无。本 change 不引入新 capability。

### Modified Capabilities

无。`CLAUDE.md` 不是 capability，**其 §5 冻结块不承载任何规范性 Requirement**（`β_0` 的规范性闭式在 `wayfinder` req-7 / req-24 与 `decompmoe-skeleton` req-13 内，均已正确）。据此本 change 的 `.openspec.yaml` 设 `skip_specs: true`，不产出 spec delta。

## Audit fact-check

| ID | 清单 line ref | 当前真实位置（`git show HEAD:<path>` 实测，HEAD = `53ca016`） | 判定 | 根因 commit |
|---|---|---|---|---|
| **A6** | `CLAUDE.md:61` | `CLAUDE.md:61`（line ref 准确；HEAD 与工作区一致，`git diff CLAUDE.md` 为空） | ✅ 成立（`1.0` vs canonical `1.035`，偏差 −3.39%） | 引入 `0d87e32`（2026-08-19）；`b23f0e5`（2026-09-27）触碰相邻 θ 行未同步本行 |

**措辞修正（清单表述需更正）**：清单称本条为「记录该污染修复的治理文档里的残留」。更准确的说法是：真实缺陷是 **`CLAUDE.md` 内部 §5 与 §8 的自相矛盾**。`CLAUDE.md` **是** `governance` capability 的**设计起源**（`openspec/specs/governance/spec.md:3` Purpose 明载 "design origin is a `CLAUDE.md` amendment"），但**不是其规范性载体** —— `req-gov-4` §2 的三条传染通道正文位于 `openspec/specs/governance/spec.md:142`，`CLAUDE.md:93`（§8）自己就把这 4 条 obligations 转引给了 `req-gov-4` 形式化。故「治理文档里的残留」这一措辞既不准确（§5 不是治理条款），也不完整（§8 才是）。

### Severity 降级：MAJOR → MEDIUM

清单原标 MAJOR。按 audit-verification 的 γ 轴（是否外溢）复核后判为 MEDIUM，理由：

1. §8 所述三条传染通道中，**通道 (i) `src/` 默认值抄 ticket 与通道 (ii) tests `assert ==` 锁定，均已在 `adf41ef` / `d239f57` / `f077be8` 闭合**，且 `src/decompmoe/config.py:55` 与 `tests/test_beta.py:38` 现均为 1.035。
2. `β_0 ≈ 1.0` 在 `CLAUDE.md` 是**叙述摘要**，不是闭式声明，无任何 Requirement 依赖它。
3. **没有任何 guard test 会因本缺陷变红**：`tests/test_beta.py::test_beta_param_init_default` 断言的是 `MVPConfig().beta_initial`（已为 1.035），与 `CLAUDE.md` 文本无耦合（全仓测试无一处读取 `CLAUDE.md` 字节，30 处 `CLAUDE.md` 命中全在 docstring / 注释 / 报错文案）。

**但须诚实标注一处不闭合**：`CLAUDE.md:61` 触及的是通道 **(iii) reader-ticket-not-spec 复制** —— 它正是一份读者可见的叙述摘要、承载着 `wayfinder/tickets/A4-1.md` 的 stale `β_0 ≈ 1.0`。而 `governance/spec.md:144`（`req-gov-4` §3）明文规定：「A "传染链已断" verdict ... does NOT exempt the project from this monitoring obligation — recurrence remains possible whenever a new contributor reads a ticket without consulting the corresponding spec.」

即：通道 (i)(ii) 确实闭合，通道 (iii) 仍开放，本缺陷正是 (iii) 的一个实例。这不改变 severity 判定（无 `src/` / `tests/` 外溢、无测试变红），但决定了它**不是「已彻底了结」而是「仍需按 §3 周期复核」**。

即：缺陷真实存在（3.39% 数值漂移 + 文件自相矛盾），但不构成 §8 意义上的「传染」。判 MEDIUM 而非 MAJOR。

## Impact

### Affected files

| 文件 | 行 | 操作 |
|---|---|---|
| `CLAUDE.md` | 61 | `（β_0 ≈ 1.0）` → `（β_0 ≈ 1.035）` |

**无 `src/` 变更。无 `tests/` 变更。** 本 change 是单行文档漂移修复。

### Out of scope

- ❌ 任何 `src/` 变更（含当前工作树标脏的 `src/decompmoe/safeguards.py` —— 经 `git diff --ignore-all-space` 实测为纯 CRLF→LF 噪声、无语义改动）
- ❌ 任何 `tests/` 变更（本缺陷无 guard test 可加，理由见 design.md Decision 3）
- ❌ `CLAUDE.md` §5 冻结块其余 MVP 字面量的普查（`Total ≈ 452M` / `Active ≈ 100M` / `θ_{1/e} ≈ 20.36°` / phase ratios / phase boundaries 均未独立复算）—— 另开 cycle，避免范围膨胀
- ❌ 触碰 in-flight change `2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding`（其 Out of scope 已显式排除 `CLAUDE.md`）、`2026-09-28-fix-a2-a3-a4-residual-precision-claims`、`fix-review-findings-voronoi-precision-and-lineage`、`2026-09-26-followup-spec-wording-bugs-after-precision-disclosure`
- ❌ 新增 `CLAUDE.md` ↔ spec 一致性 lint 脚本（见 design.md Decision 3）
- ❌ `dev → main` / `dev → release` 合并

### Source back-link

- **`CLAUDE.md`** §6 第 8 条（每个含具体数值的算式必须有可验对账 —— 本 change 的「为何不抄 ticket 值」依据）、§8（ticket 三传染通道 + 三步修复协议，本缺陷的判定依据）、§2 truth hierarchy
- commit `b23f0e5`（2026-09-27 18:58:09）— 部分应用 §5 块的引入 commit
- commit `adf41ef`（2026-09-19）— 通道 (i)(ii) 闭合
- `openspec/specs/governance/spec.md:142`（`req-gov-4` §2 三通道正文）+ `openspec/specs/wayfinder/spec.md:146`（4-sig-fig narrative precision 风格依据）
- 本 change `design.md` Decision 1–3

### Risks / Trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| **并行 session 改动 working tree** | High | apply 前后各跑 turn-start 审计（`git log --all --oneline -10` + `git reflog --date=iso` + `git status --short`）；**只 `git add CLAUDE.md`**，绝不 `git add .` / `-A`（已实测 `53ca016` 于 13:00:43 由并行 session 推进） |
| **行号漂移** | Medium | apply 阶段必须 `git show HEAD:CLAUDE.md` 重新定位，**不得**沿用本 proposal 的行号 |
| **本缺陷无自动化 gate 覆盖** | Medium | `scripts/lint_no_source_field_drift.py` 只读 `openspec/specs/**/spec.md`、不校验 `CLAUDE.md` 内容（实测）→ 同类漂移会再次逃逸。记为 future scope，见 design.md Decision 3 |
| 改用 1.0 → 1.035 后 `CLAUDE.md` 与 spec 的耦合加深 | Low | 反向考量：`CLAUDE.md` §5 是 frozen block，本就声明为 MVP 权威参数摘要；不耦合才是不一致 |
