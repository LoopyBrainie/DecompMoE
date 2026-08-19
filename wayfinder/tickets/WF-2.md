# WF-2: Polish OpenSpec Spec

- **Arena**: W (Wayfinder self-audit; not part of A0–A8)
- **Type**: grilling (audit-as-decision)
- **Status**: closed
- **Blocks**: —
- **Blocked by**: WF-1
- **File**: tickets/WF-2.md
- **Resolved**: 2026-08-18

## Question

由 `openspec/changes/polish-wayfinder-spec/` 引入的 polish change（4 项 polish 项 = 3 项 WF-1 warning + 1 项 21 ticket deep-check 发现的 A4-1 precision drift）是否完整执行？主 spec `openspec/specs/wayfinder/spec.md` 是否承载了所有 polish 的结果？

## Resolution

**PASS**：4 项 polish 项全部按 design.md 的 5 项 Decision 顺序执行；archive 后主 spec 验证通过。

### 执行清单

| Group | 内容 | 状态 |
|---|---|---|
| 0 | Archive gate precondition（specs/wayfinder/spec.md 不存在 + WF-1 Resolution 未改）| ✅ |
| 1 | spec.md 加 21 个锚点（`<a id="req-N">">`，N = 1..21） | ✅ |
| 7 | A4-1 γ 梯度上界 per-component 精度修正（32 → 15.95） | ✅ |
| 2 | design.md 1 处 Requirement 自然语言引用 → 相对锚点链接 | ✅ |
| 3 | tasks.md 2.4 拆分判定路径（spec 侧 / ticket 侧）+ 2.5/2.6 重编号 | ✅ |
| 4 | proposal.md Impact 段加 R/S 数行 | ✅ |
| 5 | `openspec validate` 双 change 通过 + 主 spec 验证 | ✅ |
| 6.1 | `openspec archive polish-wayfinder-spec --yes` | ✅ → `2026-08-18-polish-wayfinder-spec` |
| 6.2 | `openspec archive introduce-wayfinder-decompoe-spec --yes` | ✅ → `2026-08-18-introduce-wayfinder-decompoe-spec`（apply +21 Requirements） |

### 主 spec 落地验证

| 项 | 期望 | 实际 |
|---|---|---|
| 锚点 `<a id="req-N">` | 21 | **21** ✓ |
| `### Requirement:` | 21 | **21** ✓ |
| `#### Scenario:` | 34 | **34** ✓ |
| A4-1 γ 梯度上界 15.95 文本 | 1 | **1** ✓ |
| 旧 `all three gradient magnitudes` 文本 | 0 | **0** ✓ |
| 旧 `# Spec Delta` 标题 | 0 | **0** ✓（archive 转换） |

### 关键决策回溯

- **skip_specs: true** 在 polish change 中保持有效——A4-1 精度修正（32 → 15.95）属于 15.95 ⊂ 32 子集，行为契约未扩张，不构成 capability modification。
- **archive 顺序**：polish 先 archive（落入 change log），再 introduce archive（拿到 polished 版本落主 spec）。顺序反了会导致主 spec 拿到未 polished 的 anchor 与 A4-1 文本。
- **archive 副作用**：archive 流程吞掉了主 spec 的 `## ADDED Requirements` 段头与 `# Spec Delta — wayfinder` 标题，但保留 `## Purpose` 与 21 Requirements 的 anchor。已在 archive 后手动补回 `req-1` 锚点（archive 吞掉了 `<a id="req-1">` 因为它在第一个 Requirement 之前没有前导段头作为"截断锚点"）。

### 与 WF-1 的关系

WF-2 是 WF-1 的执行 follow-up：
- WF-1 发现 3 项 warning（proposal R/S 数 / design anchor / tasks 2.4 精度）
- 21 ticket deep-check 又发现 1 项 A4-1 precision drift
- WF-2 把这 4 项 polish 项合并到一个 polish change 中执行并 archive

### 后续

- 主 spec `openspec/specs/wayfinder/spec.md` 是 DecompMoE 设计的 OpenSpec 真相源
- 后续 code-level delta（例如 `add-decompoe-mvp-module`）将基于该 spec 启动新 proposal
- wayfinder 的 map.md 现在引用主 spec 作为 source of truth