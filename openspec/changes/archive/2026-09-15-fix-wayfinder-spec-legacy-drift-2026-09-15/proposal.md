## Why

`openspec/specs/wayfinder/spec.md` 在 3 个位置保留着与下游真相源（`openspec/specs/decompmoe-skeleton/spec.md`、`src/decompmoe/*.py`、`wayfinder/tickets/A6b-2.md`）不一致的 legacy wording：L64 的 `+ ε` 归一化公式、L158 的 "activations" 术语、L293 的 `WB` 悬空符号引用。本次 archive-only 修复让 wayfinder master spec 与 init decision / code / skeleton 三方一致，避免后续 lint/审计误报与 reader 对 capability 与实现是否一致的误判。

## What Changes

- **`wayfinder/spec.md` Req 5 (L64)**：四步提取 pipeline 步骤 (2) 与 (4) 的归一化公式 `z / (‖z‖ + ε)` → `z / max(‖z‖₂, ε)`。对齐 `src/decompmoe/sphere.py:50` 实际实现 `torch.clamp(norm, min=eps)`，对齐 skeleton "Spherical L2 Normalization" Req 已锁定的 `max(·, ε)` 形式（skeleton L309 明确标注 prior `+ ε` formula 的 `[1 − 2ε, 1]` interval bound 已 obsolete）。
- **`wayfinder/spec.md` Req 9 (L158)**：SwiGLU FFN active counting 术语修正 — `k · 3 · d_model · d_ffn activations per routed token` → `k · 3 · d_model · d_ffn active parameters per routed token`。术语对齐 Req 10 "alignment with Mixtral's active-parameter accounting"，对齐 skeleton L25/154/166 已统一使用 "parameter" 表述。
- **`wayfinder/spec.md` Req 15 (L293)**：为悬空引用的 advisory 符号 `WB` 加 inline glossary — `WB = 0.0476 = 软正交损失的自然 baseline`（定义与数值出自 `wayfinder/tickets/A6b-2.md` L52, 89-92），保留 `L_sep / WB` 表达。

所有修改均为 spec wording 修复（**非** requirement 删除/语义变更/数值变更），不影响代码层、不引入新 requirement、**不引入 breaking change**。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `wayfinder`：
  - **Req 5 (Spherical Normalized C Extraction)**：步骤 (2)(4) 归一化公式形式（`+ ε` → `max(·, ε)`），仅 wording 不变
  - **Req 9 (Standard SwiGLU FFN Expert)**：active 参数计数术语（`activations` → `active parameters`），仅术语
  - **Req 15 (Hybrid Three-Layer Phase Triggers)**：advisory 信号 `WB` 在主 spec 加 glossary，悬挂引用消除

## Impact

- **代码层**：无影响。`src/decompmoe/sphere.py`、`extraction.py`、`experts.py` 实现均已分别采用 `max(·, ε)` 归一化和 active-parameter 概念；本次 fix 仅把 spec wording 与现有实现对齐。
- **Skeleton spec**：本 change scope **仅** wayfinder master。`decompmoe-skeleton/spec.md` L266 同样存在 `L_sep/WB` 悬空引用（与 L293 同源），列为 explicit out-of-scope follow-up（不在本 change 内）。
- **Source 反链**：3 处现有 `**Source:**` 字段分别已指向 `A3-1.md`、`A5-1.md`、`A6b-2.md`，lint_no_source_field_drift 仍绿，本 change 不重写 Source 字段。
- **Lint**：archive 前需 `python scripts/lint_no_source_field_drift.py` 与 `python scripts/lint_no_dead_defensive.py` 双 gate `exit=0`（per CLAUDE.md §3 archive 前置条件）。
- **Out of scope**：
  - skeleton spec L266 同位置 dangling reference（用户未列入本次 fix）
  - wayfinder spec 中其他未列入本 change 的潜在 drift
  - 任何代码层、测试层、tickets 变更