# Tasks

## 1. archive 制品 spec 行号引用 fact correction（5 个文件）

### 1.1 `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/specs/wayfinder/spec.md` 行号引用修正

- [x] 1.1.1 surgical Edit 替换 L5 "L389-459" → "L394-466"、"the `MCI` row at L408" → "the `MCI` row at L413"、"L408 Reason" → "L413 Reason"、"L411 Source" → "L416 Source"、"L445/L449" → "L450/L454"。Verification: `grep -F "L389-459" openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/specs/wayfinder/spec.md` 应返回 0 命中；`grep -F "L394-466" ...` 应返回 1 命中；`grep -F "the \`MCI\` row at L413" ...` 应返回 1 命中。

- [x] 1.1.2 surgical Edit 替换 L17 "L445 `MCI closed-form on uniform token distribution`" → "L450 ..."、L18 "L449 `MCI closed-form on rank-1 token distribution`" → "L454 ..."。Verification: `grep -n -F "L445 \`MCI closed-form on uniform token distribution\`" ...` 应返回 0 命中；`grep -n -F "L450 \`MCI closed-form on uniform token distribution\`" ...` 应返回 1 命中。

- [x] 1.1.3 surgical Edit 替换 L22-23 ticket 提及"L70 (`\`λ_j = C 分布协方差矩阵的特征值\`) — `-- spec req-20 L408 uncentered second moment ..."` → "spec req-20 L413 ..."。Verification: `grep -F "spec req-20 L408" openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/specs/wayfinder/spec.md` 应返回 0 命中；`grep -F "spec req-20 L413" ...` 应返回 2 命中（L70 + L74 各 1 次）。

- [x] 1.1.4 surgical Edit 替换 L37 + L42 ticket L70 + L74 annotation verbatim 引用 `spec req-20 L408` → `spec req-20 L413`。Verification: 同 1.1.3。

- [x] 1.1.5 surgical Edit 替换 L50 "spec L408 Reason (钉死真相) → ticket L70 + L74 (历史 lineage) → audit `.audit/spec-math-audit.md` L524 evidence段 (审计 trail)" 中 L408 → L413。Verification: `grep -F "spec L408 Reason (钉死真相)" ...` 应返回 0 命中；`grep -F "spec L413 Reason (钉死真相)" ...` 应返回 1 命中。

- [x] 1.1.6 LF 校验：`file openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/specs/wayfinder/spec.md` 应返回 LF；`git diff --stat .../specs/wayfinder/spec.md` 验证仅修改行被 touch、0 删除。

### 1.2 `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/specs/governance/spec.md` 行号引用 + governance 元描述修正

- [x] 1.2.1 surgical Edit 替换 L13 "The planned change `09-fix-claude-md-ticket-advisory-boundary` ... intended to introduce a future governance Requirement ... would be `req-gov-2` *if* and when `09-fix-claude-md-ticket-advisory-boundary` is actually proposed and archived. **This change is NOT contingent on that planned Requirement being live**" → "req-gov-2 由本 archive change 引入（L51 documenting-only meta Requirement per CLAUDE.md §3 source-field rules application），与 planned change 09 无关；planned change 09 是独立 future governance 增强（advisory scope vs operational impact distinction 等），未来若由 archive 引入则为 `req-gov-3`+"。Verification: `grep -F "would be \`req-gov-2\` \*if\* and when" openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/specs/governance/spec.md` 应返回 0 命中；`grep -F "req-gov-2 由本 archive change 引入" ...` 应返回 1 命中。

- [x] 1.2.2 surgical Edit 替换 L22 "the planned `09-fix-claude-md-ticket-advisory-boundary` ticket-advisory-boundary formalization is a separate future change" → "the planned `09-fix-claude-md-ticket-advisory-boundary` ticket-advisory-boundary formalization is a separate future change（注：本 archive change 已引入 req-gov-2 documenting-only meta，planned 09 引入后为 req-gov-3+）"。Verification: 同 1.2.1 的 "req-gov-2 由本 archive change 引入"。

- [x] 1.2.3 surgical Edit 替换 L24 "this ADDED Requirement does NOT introduce a `req-gov-2` anchor — `req-gov-2` would only be introduced by the planned `09-fix-claude-md-ticket-advisory-boundary`" → "this ADDED Requirement DOES introduce `req-gov-2` anchor at L51（documenting-only meta）；the planned `09-fix-claude-md-ticket-advisory-boundary` is a separate future change that may introduce additional governance Requirements as `req-gov-3`+ if/when archived"。Verification: `grep -F "would only be introduced by the planned" ...` 应返回 0 命中；`grep -F "DOES introduce \`req-gov-2\` anchor at L51" ...` 应返回 1 命中。

- [x] 1.2.4 LF 校验：`file .../specs/governance/spec.md` 应返回 LF；`git diff --stat .../specs/governance/spec.md` 验证仅修改行被 touch、0 删除。

### 1.3 `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/proposal.md` 行号引用 + governance 元描述修正

- [x] 1.3.1 surgical Edit 替换 L7 "spec L408 显式 supersede 到 `λ_j = M = (1/|T|) · Σ C_t C_tᵀ`" → "spec L413 显式 supersede ..."。Verification: `grep -n -F "spec L408 显式 supersede" .../proposal.md` 应返回 0 命中；`grep -n -F "spec L413 显式 supersede" .../proposal.md` 应返回 1 命中。

- [x] 1.3.2 surgical Edit 替换 L12 "spec L408 + L408 Reason + L411 Source" → "spec L413 + L413 Reason + L416 Source"。Verification: 同上 pattern。

- [x] 1.3.3 surgical Edit 替换 L19-22 "spec L408 (uncentered second moment reading)" + "spec L408 Reason" + "spec L411 Source" + "spec L407-459 共 12 Scenarios" → "spec L413 ..." + "spec L413 Reason" + "spec L416 Source" + "spec L394-466 共 12 Scenarios"。Verification: `grep -F "spec L407-459 共 12 Scenarios" .../proposal.md` 应返回 0 命中；`grep -F "spec L394-466 共 12 Scenarios" .../proposal.md` 应返回 1 命中。

- [x] 1.3.4 surgical Edit 替换 L33 "wayfinder spec req-20 L389" → "wayfinder spec req-20 L394"（anchor 行号）。Verification: `grep -F "wayfinder spec req-20 L389" .../proposal.md` 应返回 0 命中；`grep -F "wayfinder spec req-20 L394" .../proposal.md` 应返回 1 命中。

- [x] 1.3.5 surgical Edit 替换 L34 "spec L408 闭式 + L445/L449 Scenarios" → "spec L413 闭式 + L450/L454 Scenarios"。Verification: `grep -F "L445/L449 Scenarios" .../proposal.md` 应返回 0 命中；`grep -F "L450/L454 Scenarios" .../proposal.md` 应返回 1 命中。

- [x] 1.3.6 surgical Edit 替换 L40-41 ticket annotation 引用 L408 → L413（仅 spec-req 行号；保留其他 verbatim 文字不变）。Verification: `grep -n -F "superseded by spec req-20 L408" .../proposal.md` 应返回 0 命中；`grep -n -F "superseded by spec req-20 L413" .../proposal.md` 应返回 2 命中。

- [x] 1.3.7 surgical Edit 替换 L59 "spec L408 (uncentered second moment 闭式钉死真相源)" + "spec L408 Reason" + "spec L411 Source" + "spec L407-459 Scenarios (含 L445/L449 MCI closed-form)" → "spec L413 ..." + "spec L413 Reason" + "spec L416 Source" + "spec L394-466 Scenarios (含 L450/L454 MCI closed-form)"。Verification: 类似 1.3.3。

- [x] 1.3.8 surgical Edit 替换 L61 governance 元描述 "现有 req-gov-1 ... 由 planned change `09-fix-claude-md-ticket-advisory-boundary` (当前为 `.audit/.../opsx-changes/` planning 草案) 形式化" → "现有 req-gov-1 (L7-23) + req-gov-2 (L51 documenting-only meta per CLAUDE.md §3 source-field rules) 已在本 archive change 引入；planned change `09-fix-claude-md-ticket-advisory-boundary` 是独立 future governance 增强"。Verification: `grep -F "由 planned change \`09-fix-claude-md-ticket-advisory-boundary\`" .../proposal.md` 应返回 0 命中。

- [x] 1.3.9 surgical Edit 替换 L84-85 ticket annotation 引用 L408 → L413（proposal.md 影响段）。Verification: `grep -F "spec req-20 L408" .../proposal.md` 应返回 0 命中。

- [x] 1.3.10 surgical Edit 替换 L93 + L104 "spec L408 Reason" + "spec L411 Source" + "L408 + L408 Reason + L411 Source" → "spec L413 Reason" + "spec L416 Source" + "L413 + L413 Reason + L416 Source"。Verification: 同上。

- [x] 1.3.11 LF 校验：`file .../proposal.md` 应返回 LF；`git diff --stat .../proposal.md` 验证仅修改行被 touch、0 删除。

### 1.4 `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/design.md` 行号引用 + governance 元描述修正

- [x] 1.4.1 surgical Edit 替换所有 "spec L389" → "spec L394"、"spec L389-R407 范围" → "spec L394-466 范围"、"spec L408 Reason" → "spec L413 Reason"、"spec L408 uncentered" → "spec L413 uncentered"、"spec L408 闭式" → "spec L413 闭式"、"spec L411 Source" → "spec L416 Source"、"L445/L449 MCI closed-form" → "L450/L454 MCI closed-form"、"spec L389-R459" → "spec L394-466"。Verification: `grep -F "spec L389" .../design.md` 应返回 0 命中；`grep -F "spec L394" .../design.md` 应返回 1+ 命中。

- [x] 1.4.2 surgical Edit 替换 governance 元描述："planned `09-fix-claude-md-ticket-advisory-boundary` 已形式化 ticket annotation mode" → "planned `09-fix-claude-md-ticket-advisory-boundary` 是独立 future governance 增强；本 archive change 已在 `openspec/specs/governance/spec.md` L51 引入 req-gov-2 documenting-only meta"。Verification: `grep -F "已形式化 ticket annotation mode" .../design.md` 应返回 0 命中。

- [x] 1.4.3 LF 校验：`file .../design.md` 应返回 LF；`git diff --stat .../design.md` 验证仅修改行被 touch、0 删除。

### 1.5 `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/tasks.md` 行号引用修正

- [x] 1.5.1 surgical Edit 替换所有 "spec L408" → "spec L413"、"spec L408 Reason" → "spec L413 Reason"、"spec L411 Source" → "spec L416 Source"、"L445 `MCI closed-form on uniform token distribution`" → "L450 ..."、"L449 `MCI closed-form on rank-1 token distribution`" → "L454 ..."。Verification: `grep -F "spec L408" .../tasks.md` 应返回 0 命中；`grep -F "spec L413" .../tasks.md` 应返回 1+ 命中。

- [x] 1.5.2 LF 校验：`file .../tasks.md` 应返回 LF；`git diff --stat .../tasks.md` 验证仅修改行被 touch、0 删除。

## 2. ticket A8-2 L70 + L74 annotation spec-req 行号引用修正

- [x] 2.1 surgical Edit 替换 `wayfinder/tickets/A8-2.md` L70 末尾 annotation 中 `spec req-20 L408 uncentered second moment` → `spec req-20 L413 uncentered second moment`。Verification: `grep -n -F "spec req-20 L408" wayfinder/tickets/A8-2.md` 应返回 0 命中；`grep -n -F "spec req-20 L413" wayfinder/tickets/A8-2.md` 应返回 2 命中（L70 + L74）。

- [x] 2.2 surgical Edit 替换 `wayfinder/tickets/A8-2.md` L74 末尾 annotation 中 `spec req-20 L408 uncentered second moment` → `spec req-20 L413 uncentered second moment`。Verification: 同 2.1。

- [x] 2.3 LF 校验：`file wayfinder/tickets/A8-2.md` 应返回 LF；`git diff --stat wayfinder/tickets/A8-2.md` 验证 0 删除（仅 2 处字符串替换）；保留原 verbatim "λ_j = C 分布协方差矩阵的特征值" + "原 CV（C 分布凸包半径）" 不变。

## 3. 新 change 制品 findings.md 创建

- [x] 3.1 在新 change 制品目录下新增 `findings.md`（documenting-only），记录清单 03 主文事实验证发现的 4 处新事实错误（F1/F2/F3/F4）。Verification: `ls -la openspec/changes/2026-09-22-fix-archive-a8-2-cv-supersede-line-drift/findings.md` 应返回存在；文件含 4 个子段（每段独立 grep 验证关键词）。

- [x] 3.2 在 `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/KNOWN-DRIFT.md` 追加 "Drift 3" 子段，列出清单 03 主文事实验证发现的 4 处新事实错误（与新 change findings.md 同步）。Verification: `grep -F "## Drift 3" .audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/KNOWN-DRIFT.md` 应返回 1 命中。

## 4. 验证与提交

- [x] 4.1 行号引用全替换验证：跨 5 个 archive 制品文件 + ticket A8-2.md 一次性 grep 所有可能 stale 行号字符串（"L389" + "L407-459" + "L408" + "L411" + "L445" + "L449" + "L7-L25"），应全部返回 0 命中（除了 anchor L389→L394 已在 design.md / tasks.md 处理）。Verification: `grep -r -F "L389" openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/` 应仅返回已被 architecture 改为 audit trail 解释的行（如"原来 L389"），主 spec-req 引用全部修正。

- [x] 4.2 新增 anchor 一致性验证：`req-20` anchor 在 `openspec/specs/wayfinder/spec.md` L394 ✓（已 grep 验证）；新 change 制品引用"L394"与真 spec 一致 ✓；archive 制品修正后引用 L394 也一致 ✓。

- [x] 4.3 governance req-gov-2 元描述自洽性验证：archive 制品 governance spec delta 声称"req-gov-2 由本 archive change 引入（L51 documenting-only meta）"+"planned 09 是独立 future governance 增强"——两段描述自洽，无 self-contradiction。Verification: `grep -F "would only be introduced by the planned" openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/` 应返回 0 命中（所有 self-contradict 措辞已清）。

- [x] 4.4 测试运行（无需，因本 change 不改 src/ tests/ spec）：`uv run pytest tests/ -q --no-header`，期望 **197 passed** 全绿（无 regression；archive 制品 + ticket annotation 行号引用对账不进入 pytest 测试覆盖）。

- [x] 4.5 lint gate 双跑：`python scripts/lint_no_dead_defensive.py` 应 exit=0；`python scripts/lint_no_source_field_drift.py` 应 exit=0（本 change 不修改 `openspec/specs/` 真 spec，lint 监控范围不含 archive 制品与 ticket 文件）。

- [x] 4.6 spec/code 一致性 spot-check：
  - 真 spec `req-20` anchor L394 + MCI row L413 + Source L416 + Scenarios L450/L454 + Range `MCI ∈ [1/d_c, 1]` 不变 ✓（真 spec 行为不变）
  - governance req-gov-2 anchor L51 不变（archive change 03 已引入） ✓
  - `MCI(token_signatures)` 实现用 spec uncentered second moment 不变 ✓（src/decompmoe/metrics.py 不动）
  - `test_mci_uniform_token_distribution` + `test_mci_rank1_token_distribution` 仍用 spec 闭式 + abs=1e-12 守护 ✓（tests 不动）
  - archive 制品 5 个文件 + ticket A8-2 L70 + L74 annotation + 新 change findings.md + .audit/.../KNOWN-DRIFT.md 全部 line drift 修正完成 ✓

- [x] 4.7 单 commit on `dev`：`git add openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/ wayfinder/tickets/A8-2.md openspec/changes/2026-09-22-fix-archive-a8-2-cv-supersede-line-drift/findings.md .audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/KNOWN-DRIFT.md && git commit -m "fix(archive-a8-2): correct archive 2026-09-20 line drift (req-20 L389→L394, MCI L408→L413, Source L411→L416, Scenarios L445/L449→L450/L454) + governance req-gov-2 meta self-contradiction + ticket A8-2 L408→L413 + findings on list-03 main text drift (4 处新错误)"`。

- [x] 4.8 archive 准备：`openspec validate "2026-09-22-fix-archive-a8-2-cv-supersede-line-drift" --type change --strict` 应 PASS（无 "Unknown item" 或 MODIFIED-but-not-found warnings）；`/opsx:archive` 前置 lint gate 必须 exit=0。