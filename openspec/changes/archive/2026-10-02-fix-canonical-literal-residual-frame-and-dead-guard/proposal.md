# Proposal

## Why

`decompmoe-skeleton` req-6 与 `governance` req-gov-1 把一组**由有缺陷的求积器产生**的数值当成规范事实冻结，导致四个已独立复算确认的缺陷同时存在（F2 / F3b / F4 / F6，裁决见 `archive/2026-10-01-audit-errata-a1-numeric-guard-list/design.md` D4.4）：

- **F2（字面量冻结）**：16 位 canonical 值 `1.1735482746999482 rad` 被冻结在三处（`skeleton` req-6 正文与 Scenario bullet、`governance` obligation 4）。真值是 `1.173547425919717470035`，**第 7 位小数起分歧**。
- **F3b（自身作 oracle）**：`< 1e-9` 的残差声明由 `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` 钉住，而该测试用 `sphere._betainc_regularized`——**被检验函数本身**——度量。impl 内部残差 `1.16e-14`，真值 `4.15e-7`，差 `4.2e5` 倍。而 `governance` obligation 4 本就强制「MUST clarify which frame」⇒ **是测试违反治理，不是治理缺失**。
- **F4（量纲混用）**：面积分数残差 `4.15e-7` 被直接与**角度容差** `1e-6` 比较；N_e=64 的 `1.43e-9` 同样跨量纲。正确表述是 θ 偏差 `8.49e-7 rad < 1e-6 rad`，已占 **85% 预算**。
- **F6（死防御）**：`src/decompmoe/gating.py:36-40` 的 `torch.where(isinf(x) & (x<0), full_like(-inf), x)` 选中的正是已为 `-inf` 的项再赋 `-inf` ⇒ 纯 no-op。`scripts/lint_no_dead_defensive.py` 未捕获。

根因是同一个：`src/decompmoe/sphere.py::_betainc_regularized` 用**单个 8 点 Gauss–Legendre panel、不做细分**，在其 docstring 声明的适用域外失效。规范层把它的输出提升为 canonical，却从未声明「这个数只在那个失效域内成立」。

**为什么是现在**：这四项已由 `/code-review` 与本仓独立复核双向确认，且 Change 0（`2026-10-01-audit-errata-a1-numeric-guard-list`）已把勘误与 finding 台账固化归档——本 change 是台账 D4.4 中标为「Change 2」的那一批，现在具备施工的事实基线。

## What Changes

- **BREAKING（数值）**：修好 `src/decompmoe/sphere.py::_betainc_regularized`，使其达到其 docstring 已声明的意图（真求积精度）。**这是本 change 的根修复**——F2 无法在不修它的前提下诚实修复：把 6dp 字面量改成真值会让测试合法变红，而在求积器仍旧缺陷的情况下「钉住缺陷输出」等于把 bug 写进规范。
- 随之，`canonical_voronoi_angle` 的 6dp 字面量由 `1.173548` → `1.173547`、`1.165848` → `1.165847`（N_e=64 的 `1.020506` 与 `θ(32,16)` 的 `62.5444°` 不变）。
- **`abs=1e-6` 容差维持不变**。实测新字面量 `1.173547` 对未修 impl 为 `1.275e-06`（FAIL）、对修后真值为 `4.259e-07`（PASS），是标准 **red→green** 判别式，无需收紧。（6dp 字面量对真值的固有截断误差上界 `5e-07` 是 `1e-9` 的 426 倍，任何 `< 1e-6` 的容差都会失败。）
- **`governance` obligation 4 的处置改为 retire 而非 update**：求积器修好后 impl-internal 与 true 两帧重合（残差降到 ~1e-50），`1.16e-14` vs `4.15e-7` / `6.63 ppm` / `0.72 ppm` 这套双帧装置随之失去存在前提，`obligation 3` 的 `< 1e-9` 论证在**两帧下同时成立**。具体取舍见 `design.md` D2。
- `decompmoe-skeleton` req-6 正文与 Scenario bullet 中的 16 位字面量、两帧残差表述、以及与 `1e-6` 的跨量纲比较一并更正。
- 删除 `src/decompmoe/gating.py:36-40` 的死防御 no-op（同文件 `:41-43`、`:46-50` **不是** no-op，保留）。

**不做**：不改 `abs=1e-6`；不动 `CLAUDE.md` §5 的「球面几何自洽」表述（已另立范围）；不动 38 个伪守卫（属 Change 1）。

⚠️ **范围在 apply 期间扩大（用户裁决）**：`wayfinder` spec 原被排除，但实测发现 `req-11` 有两处数值（impl 二分输出 `1.1735482746999482 rad = 67.23936319516639°`，以及由它导出的 `4.83e-5` / `48×` 4 位小数间隙）**因本修复而变假**。该 Requirement 的**结论**（「4 位小数展示形式不得与 `abs=1e-6` 容差配对」）不依赖这两个数，保持不变；只换数值。范围由 2 个 capability 扩到 **3** 个。

## Capabilities

### New Capabilities

（none）

### Modified Capabilities

- `decompmoe-skeleton`: req-6（Voronoi Self-Consistency Threshold）。16 位 canonical 字面量改为求积器修复后的真值；`impl-internal` / `true closed-form` 双帧残差表述改为单帧；面积分数残差与角度容差的跨量纲比较改为同量纲陈述。
- `governance`: req-gov-1。obligation 3 保留 `abs=1e-6` 并更新其 `< 1e-9` 论证为两帧皆成立；obligation 4 的双帧 disambiguation 装置按 `design.md` D2 的结论 retire 或收窄。另含 `versine` 4dp 偏差 `1.70583e-5` / `3.40146e-5`（原 `1.78409e-5` / `3.40071e-5`；这两个偏差是 θ 的函数，故随修复移动，而 4dp 字面量 `round(v,4)` 与严格界 `5e-5` 不变）。
- `wayfinder`: req-11（4070 MVP Hyperparameter Set）。仅更新两处随 θ 改变的数值（`1.1735474259196821 rad = 67.23931456363941°`；4 位小数间隙 `4.74e-5` / `47×`），结论与两个 `round` 守卫（`round(θ,4)==1.1735`、`round(deg,2)==67.24`）不变。

F6 是**纯 no-op 删除**，`local_softmax` 的可观测行为不变，按 OpenSpec 规则**不产生 spec delta**，只改 `src/`。

## Impact

| 面 | 影响 |
|---|---|
| `src/decompmoe/sphere.py` | `_betainc_regularized` 换为可收敛的求积路径（细分或更高阶）。`_cap_area` 在 `θ=π/2` 的伪不连续随之消失（E10：单侧跳变 `7.870852e-02` 是 `x >= 1.0` 早退 + panel 失效叠加，精确数学连续） |
| `src/decompmoe/gating.py` | 删 `:36-40` 的 no-op（仅 3 行，无行为变化） |
| `openspec/specs/decompmoe-skeleton/spec.md` | req-6 整块改写（该 block 含 6680 字符单行正文，delta 必须整块携带） |
| `openspec/specs/governance/spec.md` | req-gov-1 整块改写 |
| `openspec/specs/wayfinder/spec.md` | req-11 整块改写（仅 2 处数值） |
| `tests/` | 6dp 字面量与残差断言更新；`test_voronoi_residual_below_1e_minus_9` 需改为对修复后实现仍成立且 frame 明确 |
| **并发风险** | `sphere.py`、两份 spec、四个测试文件（`test_sphere.py` 等）**当前含未提交的并发 session 改动**。本 change 的 apply 阶段与之正面重叠，**apply 前必须先裁决归属**（见 `design.md` D6） |
| 测试总数 | 当前 `227`；本 change 不新增/删除测试函数，只改断言与实现 |

**门禁**：`openspec archive` 已知会吞 `<a id="req-N"></a>` 锚点（见 `git log 4f3e752`）。归档前须抓取三份 spec 的 anchor 指纹，归档后复算，不一致时从 `git cat-file blob` 恢复且**绝不重跑 archive**。
