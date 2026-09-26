# Proposal: 2026-09-12-replace-literal-wayfinder-l249-with-anchor-ref

## Why

`openspec/specs/decompmoe-skeleton/spec.md` 在 4 行（合计 7 处）body 文字里以**字面行号**形式引用 `wayfinder L249`（即 wayfinder spec 第 249 行所在的 Requirement 13 "Numerical Safeguards" 主体），未走 `<a id="req-13"></a>` 稳定锚点。这 7 处覆盖了 NaN 升级阶梯（场景 L220 末段 1 处）和 `should_resurrect` 语义解释（场景 L244 首段 1 处、L248 第 2 段 1 处、L260 Notational pin 段 4 处）四个不同位置：

| 行号 | 所在 Scenario | 字面引用形态（共 7 处） |
|---|---|---|
| L220 | `NaN ladder default at consecutive_nan=0` | 1 处："matches wayfinder L249 strict-greater-than ladder tiers" |
| L244 | `should_resurrect semantic interpretation (per-step vs avg-window)` | 1 处："The wayfinder L249 wording `f_i^avg < 1/(2·N_e)`" |
| L248 | `should_resurrect semantic interpretation (per-step vs avg-window)` | 1 处："matching the wayfinder L249 wording's 'for 200 consecutive steps' temporal qualifier" |
| L260 (1) | `should_resurrect semantic interpretation (per-step vs avg-window)` | 1 处："**Notational pin on `f_i^avg`** (wayfinder L249)" |
| L260 (2) | 同上（Notational pin 段内） | 1 处："which the wayfinder L249 wording does not contain" |
| L260 (3) | 同上（Notational pin 段内） | 1 处："Cross-reference: wayfinder L249's `f_i^avg` notation is used identically..." |
| L260 (4) | 同上（Notational pin 段末） | 1 处："the same meaning in L249's `f_i^avg < 1/(2·N_e)` trigger"（注意：此处**无** "wayfinder" 前缀，但仍指 L249） |

wayfinder spec 当前在 L245 已铺设稳定锚点 `<a id="req-13"></a>`，且 Requirement 标题 `### Requirement: Numerical Safeguards`（L247）相对稳定。一旦未来 wayfinder spec 因其它 change（已 archive 的 `2026-09-12-add-should-resurrect-per-step-math-derivation`、`fix-spec-resurrection-math-direction-2026-09-12` 等）新增/删除/重排 L249 周围的行，这 7 处字面引用就会静默漂移到错误的行号，**比"未引用"更危险**——reader 会以为引用仍然指向 Req 13 Numerical Safeguards，但实际指向已变成 NaN ladder scenario 或 `fix-openspec-doc-bugs` Decision N 的某个旁注。本次 change 把 7 处字面引用统一替换为稳定锚点引用。

**触发背景**：本 change 是对独立事实复核（fix-spec-should-resurrect-signature-drift-2026-09-12 fact-check, 2026-09-12）的延伸动作。原 fact-check 揭示 archived change `2026-09-10-fix-safeguards-should-resurrect-signature-drift` 的 premise 是假命题（spec ↔ code 签名 byte-identical），但复核过程中顺手定位到上面 7 处字面行号引用——这是**真实存在**的脆弱性（独立于假命题部分），适合以独立 change 形式处理。

## What Changes

- **`openspec/specs/decompmoe-skeleton/spec.md`**（合计 7 处字面 `L249` → 稳定锚点 `Req 13` / `Numerical Safeguards` / `#req-13`）：
  - L220（Scenario `NaN ladder default at consecutive_nan=0` 末段）：把"this matches wayfinder L249 strict-greater-than ladder tiers"改为"this matches wayfinder Req 13 'Numerical Safeguards' strict-greater-than ladder tiers (anchor `#req-13`)".
  - L244（Scenario `should_resurrect semantic interpretation` 主体首段）：把"The wayfinder L249 wording `f_i^avg < 1/(2·N_e)`"改为"The wayfinder Req 13 wording `f_i^avg < 1/(2·N_e)`".
  - L248（同 Scenario 第 2 段）：把"matching the wayfinder L249 wording's 'for 200 consecutive steps' temporal qualifier"改为"matching the wayfinder Req 13 wording's 'for 200 consecutive steps' temporal qualifier".
  - L260 (1)（同 Scenario Notational pin 段首）：把"**Notational pin on `f_i^avg`** (wayfinder L249)"改为"**Notational pin on `f_i^avg`** (wayfinder Req 13)".
  - L260 (2)（同 Notational pin 段内）：把"which the wayfinder L249 wording does not contain"改为"which the wayfinder Req 13 wording does not contain".
  - L260 (3)（同 Notational pin 段内）：把"Cross-reference: wayfinder L249's `f_i^avg` notation is used identically..."改为"Cross-reference: wayfinder Req 13's `f_i^avg` notation is used identically...".
  - L260 (4)（同 Notational pin 段末）：把"the same meaning in L249's `f_i^avg < 1/(2·N_e)` trigger"中的"L249"同步改为"Req 13"（此处的 L249 没有 "wayfinder" 前缀，但仍指向同一位置）。
- 不改 wayfinder spec；不改 code；不改 test。
- **NOT BREAKING**：纯文字改写，无外部 API 变化，无测试断言变化。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `decompmoe-skeleton`：Requirement `Five Numerical Safeguard Helpers` 下两个 Scenario（`NaN ladder default at consecutive_nan=0`、`should_resurrect semantic interpretation (per-step vs avg-window)`）body 文字里 7 处字面 `L249` 引用（分布于 L220/L244/L248/L260 四行）全部替换为稳定锚点引用（wayfinder Req 13 'Numerical Safeguards' + `#req-13` 锚点）。无 Scenario 数量变化，无 Requirement 数量变化，无 `**Source:**` 字段变化（Source 已在 L206/L251 反链到 `wayfinder/tickets/A6a-2.md`，lint 已 exit=0）。

## Impact

- **Spec 影响**：`openspec/specs/decompmoe-skeleton/spec.md` 内 1 个 Requirement (`Five Numerical Safeguard Helpers`) 下 2 个 Scenario（`NaN ladder default at consecutive_nan=0`、`should_resurrect semantic interpretation (per-step vs avg-window)`）body 文字（共 7 处字面 `L249` 替换为稳定锚点 `Req 13`）。无结构性变更（无新增/删除 Requirement，无 Scenario 数量变化），属于**纯文本鲁棒性修正**。
- **Code 影响**：`src/decompmoe/` 下**无任何代码改动**。
- **Test 影响**：`tests/` 下**无任何测试改动**。本次修正不涉及代码引用或测试函数名。
- **CI 影响**：`/opsx:archive` 前置条件（`scripts/lint_no_dead_defensive.py`、`scripts/lint_no_source_field_drift.py`）须 `exit=0`。本次修正不涉及 `**Source:**` 字段（spec 已正确指 `wayfinder/tickets/A6a-2.md` + `change fix-openspec-doc-bugs design.md (Decision 7)`），lint 期望通过。`lint_no_dead_defensive.py` 仅 grep `*args`/`**kwargs` 等 dead defensive 模式，与本次纯 body-text 改写无关。
- **跨 spec 影响**：`openspec/specs/wayfinder/spec.md` 不修改；其 L245 锚点 `<a id="req-13"></a>` 与 L247 Requirement 标题 `Numerical Safeguards` 已是稳定锚点来源。
- **Source 反链检查**：spec L206 现有 Source 字段含 `wayfinder/tickets/A6a-2.md (initial A6a-2 design intent); change fix-openspec-doc-bugs design.md (Decision 7 — threshold parameterization 1/(2·N_e)); signature mirrors src/decompmoe/safeguards.py:71-80 at commit d3689a1.`。本次 change 不修改 Source 字段（delta spec 直接继承现有 Source 即可），符合 `scripts/lint_no_source_field_drift.py` 的 wayfinder/tickets/ 强制反链规则。
