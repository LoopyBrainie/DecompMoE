# Proposal

## Why

`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` 的 A-2 桶（15 条「spec / 文档层的数学陈述与条款措辞缺陷」）是后续 spec 修复 change 的待办输入，但独立复核（pin `6593a06` vs HEAD `188b9fb`，全部锚定 commit object 实测，未读工作树）发现清单自身有 **7 类错误**：1 条 Requirement 归错、5 条行号指向空行或差 1–3 行、4 条 `基线` 字段标错、4 处自带数字算错、5 条 `STILL_REAL` 已失效（实体早被 `e50cc02` 修掉）、1 条裁决口径与自身问题段自相矛盾。

若不先勘误，实施者会**按错误坐标施工**：AC-52 与 AC-86 的清单行号（382 / 398）都是空行，AC-87 被归到 req-20 而实为 req-19，且 5 条已修条目会被重复施加——而清单不会给出任何提示，这类错误只会在 review 时被当作「改了个不相关的地方」。

## What Changes

**Part 1 — 勘误（文档事实修正）**

- 在 `lists/opsx-changes.md` 的 A-1 勘误节之后追加 `## Errata (A-2 桶)`，登记 E1–E19：15 条 AC 的坐标/数字/Requirement 归属更正 + 5 条 stale 重判 + 4 条「清单外新发现」（标注为未收录缺陷，**只登记不修复**）。清单 A-2 正文 L376–L551 **逐字不改写**（A-1 change design.md D1 的既定先例：归档是一次已完成 review run 的历史记录，改写会销毁错误本身并伪造历史）。

**Part 2 — 修复（spec 数学缺陷）**

10 条仍可执行的缺陷，分两类落点：

- **spec delta（6 个 Requirement）**：`decompmoe-skeleton` req-6 / req-7 / req-19，`wayfinder` req-11 / req-17 / req-19
  - `d_c = 2` 仿射退化（`G(θ) = θ/π`、`G'' ≡ 0`）从未被 spec 声明，而 `signature_dim = 2` 是可达输入 → 严格凸退化为等式、Jensen 单向性界失去推导前提
  - `spherical_l2_normalize` 声称 `pow(2).sum(-1) == 1.0` **exactly**（float64 下约半数行不满足，最坏 `6.6613e-16`）→ 改为 `4·eps_f64` 有界陈述
  - Req-17 的 extract_C 闭式**漏算第 (3) 步 cross-head mean 的 128 MACs**：`33_040 → 33_168 MACs`，增幅 `~0.83% → ~1.22%`
  - Req-11 的 `W^O` 排除清单与同段 `4·d_model²` / `452_329_984` 闭式互斥（真按清单排除得 `448_135_680`，差 `0.9273%`）
  - Req-11 tying 反事实 prose `≈ 484 M` 与同段闭式（`485_097_984`）不符
  - Req-19 把 1:1 断言从两个条目过度外推到「每个 MoE 条目」；两个 residency 数值无 pin 且 `≈ 4 KB` 算不出；六个 baseline 有 5 个零表示且无 deferral 标注
- **src docstring（2 处，纯注释，不改可执行语句）**：`src/decompmoe/sphere.py` 的 `_betainc_regularized` 未披露 `x→1` 误差跃变（8.29e-07 → 1.5736e-01，相对误差 15.74%）；`canonical_voronoi_angle` 的 caveat 未披露 `θ = π/2` 处的硬不连续（跳幅 `7.870852e-2`，实现伪影）

**Part 3 — 数值守卫（CLAUDE.md §6 / req-gov-1 强制）**

每个写进 spec 的数值算式配套测试：整数闭式 bare `==`（禁止 `approx(abs=0)`），浮点闭式 `pytest.approx(..., abs=...)`，失败信息必带 `f"actual={...}"`。其中 Req-19 的 `H_kv` / `d_k` / `d_c` 漂移守卫与 `flops_per_token` arch 字面量守卫是**当前 src/tests 中完全缺失**的钉住。

**非破坏性**：无 API 变更、无行为变更、无参数移除。`src/` 改动仅限 docstring 文本。

## Capabilities

### New Capabilities

（none）

### Modified Capabilities

- `decompmoe-skeleton`: req-6 补 `d_c = 2` 仿射退化与 `G''` 闭式；req-7 的 per-token MAC 闭式补第 (iv) 项 cross-head mean（`33_040 → 33_168`）；req-19 把 `pow(2).sum(-1) == 1.0 exactly` 改为 `4·eps_f64` 有界陈述
- `wayfinder`: req-11 消除 `W^O` 排除清单与闭式的互斥 + tying 反事实给出闭式；req-17 补第 (3) 步 cross-head mean（`33_168 MACs = 66_336 FLOPs`，`~1.22%`）；req-19 收窄 1:1 断言范围、给 residency 数值补闭式与漂移守卫、给六个 baseline 补 deferral 标注，并**连带重写**其与 Req-17 的交叉对账注记（净差 `32 → 288 FLOPs`，allowance 分母改锚 active-core）

## Impact

| 文件 | 操作 |
|---|---|
| `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` | 末尾**追加** `## Errata (A-2 桶)`；正文 L376–L551 逐字不动 |
| `src/decompmoe/sphere.py` | 2 处 docstring（F9 `canonical_voronoi_angle` caveat、F10 `_betainc_regularized` 误差披露）——纯注释 |
| `tests/test_sphere.py` | 新增 F1 / F2 / F3 / F9 / F10 的数值钉住测试 |
| `tests/test_config.py`、`tests/test_metrics.py` | 新增 F4 / F5 / F7 的闭式钉住与 F8 的 arch 字面量守卫 |
| `openspec/specs/**` | **仅经 `openspec archive` 落地**，不直接编辑 |

**关键前置事实（影响本 change 的可行性）**

1. **`.audit/` 已被 gitignore**（`.gitignore:37`）。因此勘误节是**本地协调文档而非版本化交付物**——「只增不减」规则由约定而非 git 历史强制。本 change 的 `openspec/changes/<name>/` 同样在归档前处于 untracked（与 A-1 change 一致；归档时才进 git）。
2. **AC-52 的修复强制连带改 Req-19 的交叉对账注记**。把总额改成 `66_336 FLOPs` 后净差从 `32`（`0.0484%` of routing）变为 `288`（`0.4360%` of routing），原句「roughly 0.05% of `FLOPs_Routing`, well under the `0.3%` allowance」在**数值与分母口径两层同时失效**。`0.3%` allowance 本身仍成立（`66_336 / 33_554_432 = 0.19770%`），但口径必须从 `FLOPs_Routing` 改锚 active-core。**只改 Req-17 不改 Req-19 会让 spec 内部自相矛盾。**
3. **spec 基座正在漂移**。工作树中 `2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` 与 `fix-review-findings-voronoi-precision-and-lineage` 处于半归档状态（`proposal.md`/`tasks.md` 已删除未提交、`specs/` 目录仍在），且 `4f3e752` 本会话内已改 `wayfinder/spec.md` 15 行。构造 delta 后、archive 前必须以「预期差异行数」为 tripwire 复核。
4. **并行 session 共用工作树**（约 40 个未跟踪临时脚本、`wayfinder/tickets/WF-1.md` 被改）。提交只暂存本 change 的路径，禁止 `git add .`。
5. **archive 会吞 anchor**：每个被 MODIFIED 的 Requirement 恰好丢紧随其后那个 Requirement 的 `<a id="req-N">`。本 change MODIFIED 6 个 Requirement，全在高危位置，archive 后必须复算 anchor 覆盖。
6. **基线**：`pytest --collect-only` 217 tests 全绿；两个 lint gate 均 `exit=0`；清单为 LF-only（1473 LF / 0 CRLF）。
