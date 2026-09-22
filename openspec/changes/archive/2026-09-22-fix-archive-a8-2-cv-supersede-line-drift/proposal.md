# Proposal

## Why

2026-09-22 独立事实验证（audit-verification 阶段 2 follow-up review）发现已 archive 的 change `2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/`（新 change 03 制品）自身有 **5+ 处事实错误**——这些错误是 verifier F1/F2/F3 post-archive line drift 修复留下的二次 drift：spec 行号引用全错（`spec req-20 L389` → 实际 L394；`MCI row L408` → 实际 L413 是 SP_i 行不是 MCI 行；`Source L411` → 实际 L416；`Scenarios L445/L449` → 实际 L450/L454）+ governance `req-gov-2` 制品误称"未引入"实际 L51 已添加 + ticket A8-2 L70/L74 annotation 引用的 `spec req-20 L408` 本身是错的（L408 是 SP_i 行）。**真实 spec 行为不变**（`openspec/specs/` 不动），仅 archive 制品中的**事实陈述**（行号引用 + governance 元描述）需要修正。

本 change 是新 change 03 制品 post-archive fact correction：把 archive 制品中残留的 5+ 处事实错误修正完整，并新增 findings 段记录清单 03 主文（`.audit/.../03-fix-ticket-a8-2-cv-supersede-and-finding-text/`）事实验证发现的 4 处新错误（**不修改** .audit/ 主文，per `.audit/README.md` L3 .audit/ 不进 git 追踪 + audit trail 完整性原则）。

## What Changes

### 1. archive 制品行号引用 fact correction（surgical Edit，5 个文件）

**目标文件**: `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/` 下的 `proposal.md` + `design.md` + `tasks.md` + `specs/wayfinder/spec.md` + `specs/governance/spec.md` —— 修正所有引用 archive 制品历史 spec 行号的位置：

| archive 制品声称 | 当前真 spec 实际 |
|---|---|
| `spec req-20` anchor L389 | **L394** |
| MCI row L408 | **L413**（注：L408 实际是 SP_i 行） |
| MCI Reason L389-R407 范围 | **L394-466**（含 CG positive homogeneity L464） |
| Source L411 | **L416** |
| Scenarios uniform L445 / rank-1 L449 | **L450 / L454** |
| decompmoe-skeleton req-22 范围 L500-L518 | L500-L518 ✓ (未 drift) |
| gov body L7-L25 | L7-L23（body 长度 +2 → L9-L23，anchor L7 unchanged）|

### 2. ticket A8-2 L70/L74 annotation 引用 L408 错误 correction（surgical Edit，2 处）

**目标文件**: `wayfinder/tickets/A8-2.md` L70 + L74 当前 annotation 引用 "spec req-20 **L408**"——L408 实际是 SP_i 行（MCI 行在 L413）。

**修正**: L70 + L74 annotation 中的 `spec req-20 L408` → `spec req-20 L413`（保留其他 verbatim 文字不变）。

### 3. archive 制品 governance `req-gov-2` 元描述 fact correction（documenting-only）

**目标文件**: `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/specs/governance/spec.md` 与 `proposal.md` 中声称 "req-gov-2 would only be introduced by planned 09-fix-claude-md-ticket-advisory-boundary" —— **事实错误**：该 archive change 自身已在 `openspec/specs/governance/spec.md` L51 添加了 `req-gov-2` 锚点（documenting-only meta Requirement），且 `09-fix-claude-md-ticket-advisory-boundary` 至今仍是 planning 草案，未 archive。**本 archive 制品误称 req-gov-2 由 planned 09 引入——自我矛盾**。

**修正**: 把 archive 制品中的 governance 元描述统一为"req-gov-2 由本 archive change 引入（L51 documenting-only meta），与 planned change 09 无关"。

### 4. 新增 findings 段（documenting-only，不修改 .audit/ 主文）

**目标文件**: 新 change 制品（`openspec/changes/2026-09-22-fix-archive-a8-2-cv-supersede-line-drift/`）下新增 `findings.md`，记录清单 03 主文（`.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/`）事实验证发现的 4 处新错误：
- F1: 清单 03 spec 行号偏差 ~24 行（L389/L426/L432/L392 → L413/L450/L454/L416）
- F2: 清单 03 test 命名错引（`test_mci_closed_form_*` 不存在，实际是 `test_mci_uniform_token_distribution` 等）
- F3: 清单 03 测试数错误（声称 142 passed，实际 197 passed）
- F4: 清单 03 描述的"待微调"动作已 applied（spec-math-audit.md L524 实际已是微调后版本）

### 5. nothing else

per CLAUDE.md §3 surgical：
- **不动** `openspec/specs/`（真 spec 行为不变）—— archive 制品中的 fact corrections 是 audit-trail 范畴，不影响 spec-level 行为
- **不动** `src/decompmoe/`（生产代码未变）
- **不动** `tests/`（test 行为不变）
- **不动** 其他 archive 制品（除本 archive 制品的目标 4 个文件外）
- **不动** `.audit/` 主文 4 个文件（清单 03 主文保留作 audit-trail 历史记录，事实错误在 findings.md 中记录）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 — 本 change 是 archive 制品的 fact correction，不修改真 spec Requirements）

## Impact

- **Affected archive artifacts**（surgical 5 处）：`openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/` 下的 `proposal.md` + `design.md` + `tasks.md` + `specs/wayfinder/spec.md` + `specs/governance/spec.md` —— 仅替换行号引用 + governance 元描述
- **Affected ticket 1 处**：`wayfinder/tickets/A8-2.md` L70 + L74 annotation 中 `spec req-20 L408` → `spec req-20 L413`
- **Affected audit files**：无（清单 03 主文 4 处错误在新 change 制品的 `findings.md` 中记录，不修改 `.audit/` 主文）
- **Affected real specs / code / tests**：无
- **Affected APIs / dependencies**：无
- **Risk**：
  - **Risk A**：archive 制品修改被误读为"篡改历史 audit trail"。Mitigation：本次 fact correction 在新 change 制品的 findings.md + KNOWN-DRIFT-style 文档中显式记录"correction of archive 制品 line drift"作为正当理由；新 change 制品本身有完整 audit trail（proposal.md / design.md / tasks.md）
  - **Risk B**：ticket A8-2 annotation 改 "L408" → "L413" 引入新的不一致。Mitigation：L413 是当前真 spec 中 MCI 行的实际位置（已独立 grep 验证）；annotation 引用 spec-req 行号必须与真 spec 一致才能履行"supersede annotation 引导 reader 到 spec 真相源"的作用
  - **Risk C**：findings.md 引用清单 03 主文 4 处错误，与 `.audit/` 主文存在事实不一致。Mitigation：清单 03 主文是 audit-trail 历史记录，findings.md 是新 change 的 audit-trail 历史记录；两者都是 evidence 文档而非真相源，真相源是当前 `openspec/specs/`（行为不变）

## Source

本 change 由 2026-09-22 独立事实验证（cycle-12 finding 1 follow-up review）触发：
- archive 制品自身 5+ 处事实错误（line drift + governance 元描述 self-contradiction）
- 清单 03 主文 4 处新事实错误（行号偏差 ~24 行 + test 命名错引 + 测试数错误 + 已 applied 状态）
- ticket A8-2 annotation 引用 L408 错误（L408 ≠ MCI 行）

evidence 链：上一回合事实验证报告（含 grep / Select-String 独立核对结果）。