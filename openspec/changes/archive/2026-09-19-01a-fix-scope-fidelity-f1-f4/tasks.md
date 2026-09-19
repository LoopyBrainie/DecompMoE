## §A. proposal.md surgical Edits (F1 + F2 + F3 + F4 联合, 5 处)

> 路径: `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/proposal.md`
> 每个 Edit 后跑 `git diff --stat` (虽然 `.audit/` 不进 git, 用 `diff` 命令 + LF 验证即可)

### A1 · F1 §Why table cycle-5 #1 行加 A1-1 子行

- [x] A1.1 Edit: §Why 表格 "**Why**" 段第 5 行表格（cycle-5/6/7 三条 finding 表）首行 `| cycle-5 #1 | ticket A5-3.md L62 | θ_Voronoi ~52° (估算) | 67.24° (1.1735 rad, bisection < 1e-9) | 15.24° (29% relative) |` 后插入新行 `| cycle-5 #1 (sub) | ticket A1-1.md L97 | θ_Voronoi≈52° | 67.24° | 15.24° (同源, base 同上) |` —— 验证: Edit 后 §Why 表格从 3 行变 4 行, A1-1 L97 字面出现在表格中, 与 audit-verification.md L132 `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°` 字面对齐

### A2 · F1 §What Changes §B 加新行 #3.5 ticket A1-1 L97

- [x] A2.1 Edit: §What Changes `### ticket 端 supersede annotation（2 项）` 标题改 `### ticket 端 supersede annotation（3 项）`
- [x] A2.2 Edit: §What Changes 在第 4 项 `### 4. ticket A4-1 L58（cycle-7 #1）` 后插入新项 `### 5. ticket A1-1 L97（cycle-5 #1 同源）—— 加 (historical, θ_Voronoi≈52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1) 注释到 θ_Voronoi≈52° 行后（**不删** 原 ≈52° 字样，仅加 historical supersede 注释保持 ticket lineage 可读）。与 §B #3 (A5-3 L62) 走完全平行的路径 —— cycle-5 finding 锁定 A5-3 + A1-1 两个 ticket 端源头 (audit-verification.md L132 字面)`。验证: Edit 后 §B 含 3 个 ticket 项 (#3 A5-3 + #4 A4-1 + #5 A1-1), A1-1 L97 字面命中
- [x] A2.3 Edit: §What Changes `### nothing else` 段加新行 `（A5-3 + A4-1 + A1-1 三处加 supersede annotation；原"不动 wayfinder tickets 其他文件"声明保持）`。验证: Edit 后 "nothing else" 段显式列出 A1-1

### A3 · F2 §Why 表头与 §What Changes 4-file batch → 5-file batch

- [x] A3.1 Edit: §Why 第 3 段 `三条 finding 形成**同源 "ticket 端 stale 数值源头" pattern**，需在同一 OpenSpec change 中批量修复` 改 `三条 finding 形成**同源 "ticket 端 stale 数值源头" pattern**（含 cycle-5 双 ticket 端 A5-3 L62 + A1-1 L97）, 需在同一 OpenSpec change 中批量修复 —— 5-file batch fix (A5-3 L62 + A1-1 L97 + A4-1 L58 + MVPConfig L54 + test_beta.py L38)`。验证: Edit 后"5-file batch"字面命中, A1-1 L97 在 Why 段显式列入 scope

### A4 · F3 §Why table base convention 注脚

- [x] A4.1 Edit: §Why 表格上方加注脚段 `> **Base convention**: `15.24° (29% relative)` 用 ticket stale (52°) 作 base —— 15.24/52 = 29.3% (per `.audit/audit-verification/audit-verification.md` L128 `15.24° (29% 相对)`); `15.24° (22.7% relative)` 用 spec truth (67.24°) 作 base —— 15.24/67.24 = 22.7% (per `.audit/spec-math-audit/spec-math-audit.md` L134). 两个数字都对, 仅 base 不同`. 验证: Edit 后 §Why 表格上方有 base convention 注脚, 两个 base 都明示, 与 audit-verification.md L128 / spec-math-audit.md L134 字面对齐
- [x] A4.2 Edit: §Why 表格 cycle-5 #1 行的 `15.24° (29% relative)` 改 `15.24° absolute (29% relative-to-ticket-base / 22.7% relative-to-truth-base)`。验证: Edit 后数字串同时含两个 base, reader 可自取所需

### A5 · F4 §Impact Affected code 列表加 A1-1 L97

- [x] A5.1 Edit: §Impact `**Affected code**` 列表第 2 项 `wayfinder/tickets/A5-3.md:62` 后插入新项 `wayfinder/tickets/A1-1.md:97 —— θ_Voronoi≈52° 行后加 historical supersede annotation（**仅追加，不改值**, 与 A5-3 L62 平行路径）`。验证: Edit 后 Affected code 列表含 3 个 ticket 项 (A5-3 + A4-1 + A1-1)

## §B. design.md surgical Edits (F2 + F4 联合, 4 处)

> 路径: `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/design.md`

### B1 · F4 §Decision 1 Choice 加 A1-1 L97

- [x] B1.1 Edit: §Decision 1 Choice 段 `Choice: ticket A5-3.md L62 θ_Voronoi ~52° 行后追加 (historical, ~52° estimate; ...); ticket A4-1.md L58 β_0 ≈ 1.0 行后追加 (historical, β_0 ≈ 1.0 estimate; ...)` 改 `Choice: ticket A5-3.md L62 θ_Voronoi ~52° 行后追加 (historical, ~52° estimate; ...); ticket A1-1.md L97 θ_Voronoi≈52° 行后追加 (historical, θ_Voronoi≈52° estimate; ...) (与 A5-3 L62 平行, 同属 cycle-5 #1 同源 ticket 端源头 per audit-verification.md L132); ticket A4-1.md L58 β_0 ≈ 1.0 行后追加 (historical, β_0 ≈ 1.0 estimate; ...)`。验证: Edit 后 Decision 1 Choice 显式列出 3 个 ticket (A5-3 + A1-1 + A4-1), 与 tasks.md B1.1/B1.2/B2.1 ground truth 对齐

### B2 · F4 §Decision 1 Rationale 加 A1-1 平行路径说明

- [x] B2.1 Edit: §Decision 1 Rationale 段末加一句 `A1-1 L97 包含在 scope 内是 cycle-5 finding 的源头完整性要求 —— audit-verification.md L132 字面锁定 "ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°", 属 ticket → spec 闭式 supersede annotation 路径, 与 A5-3 L62 决策路径完全平行`。验证: Edit 后 Decision 1 Rationale 含 A1-1 L97 完整性要求声明, 与 audit-verification.md L132 字面对齐

### B3 · F2 §Goals 4-file batch → 5-file batch

- [x] B3.1 Edit: §Goals 第 4 项 `4-file 边界修改（ticket A5-3 L62 + ticket A4-1 L58 + MVPConfig L54 + test_beta.py L38）+ 2 处 spec delta（req-7 L122 + L126）` 改 `5-file 边界修改（ticket A5-3 L62 + ticket A1-1 L97 + ticket A4-1 L58 + MVPConfig L54 + test_beta.py L38）+ 2 处 spec delta（req-7 L122 + L126）`。验证: Edit 后 "5-file 边界修改" 字面命中, A1-1 L97 在 §Goals 显式列入

### B4 · F2 §Migration Plan step 2 加 A1-1 L97

- [x] B4.1 Edit: §Migration Plan step 2 `ticket 端 supersede annotation：wayfinder/tickets/A5-3.md L62 + wayfinder/tickets/A4-1.md L58 各加一行注释（**追加不删原值**）` 改 `ticket 端 supersede annotation：wayfinder/tickets/A5-3.md L62 + wayfinder/tickets/A1-1.md L97 + wayfinder/tickets/A4-1.md L58 各加一行注释（**追加不删原值**）`。验证: Edit 后 Migration Plan step 2 显式列出 3 个 ticket (A5-3 + A1-1 + A4-1), 与 Decision 1 Choice 对齐

## §C. 验证与提交 (surgical, no git)

> 本 change 不进 git (`.audit/` 内容不进 git 追踪 per audit README L5)

### C1 · 文本层 grep 验证

- [x] C1.1 验证 A1: `grep -F "A1-1 L97" .audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/proposal.md` 至少 4 次命中 (A1.1 新行 + A2.2 新项 #5 + A3.1 5-file batch 声明 + A5.1 Affected code 列表) + `grep -F "5-file batch" .../proposal.md` 1 次命中 (A3.1) —— 实际: A1-1 L97 5 hits (L3, L10, L38, L50, L77), 5-file batch 2 hits (L3, L50) **PASS**
- [x] C1.2 验证 B: `grep -F "A1-1 L97" .../design.md` 至少 3 次命中 (B1.1 Decision 1 Choice + B2.1 Rationale + B3.1 §Goals) + `grep -F "5-file 边界修改" .../design.md` 1 次命中 (B3.1) —— 实际: A1-1 L97 3 hits, 5-file 边界修改 1 hit **PASS** (注: 本 grep 仅扫 `5-file 边界修改`, 未扫 `5-file` 一般模式; C1.2 仅验 B3.1 §Goals 一处, **§D 修复发现**: design.md §Migration Plan L119 + commit message L127 仍残留 "4-file batch", 是 F2 修订未覆盖的 2 处)
- [x] C1.3 验证 base convention: `grep -F "29% relative-to-ticket-base" .../proposal.md` 1 次命中 (A4.2) + `grep -F "22.7% relative-to-truth-base" .../proposal.md` 1 次命中 (A4.2) —— 实际: 29% relative-to-ticket-base 1 hit (L9), 22.7% relative-to-truth-base 1 hit (L9) **PASS**

### C2 · 字面 verbatim 对齐 audit trail ground truth

- [x] C2.1 `grep -F "ticket A5-3 L62 + A1-1 L97" .audit/audit-verification/audit-verification.md` 至少 1 次命中, 字面与本 change Decision 1 / Rationale / §Migration Plan 字面对齐 (L132) —— 实际: 1 hit **PASS**
- [x] C2.2 `grep -F "22.7%" .audit/spec-math-audit/spec-math-audit.md` 至少 1 次命中 (L134), 字面与 proposal base convention 注脚对齐 —— 实际: 1 hit **PASS**
- [x] C2.3 `grep -F "15.24° (29%" .audit/audit-verification/audit-verification.md` 至少 1 次命中 (L128), 字面与 proposal base convention 注脚对齐 —— 实际: 1 hit **PASS**

### C3 · 不变量: tasks.md 不变

- [x] C3.1 验证: `diff <(git show HEAD:.audit/.../tasks.md) .../tasks.md` 返回空 (本 change **不**修改 audit change 01 的 tasks.md;tasks.md B1.2 已是 ground truth, 反向对齐 proposal/design 即可) — **注**: `.audit/` 不进 git, 改用 `ls -la` 看 mtime 验证未触碰 —— 实际: tasks.md mtime `2026/9/19 5:52:21` (与本 change 启动前的 mtime 一致) **PASS**

### C4 · lint gate (skip_specs 例外)

- [x] C4.1 `python scripts/lint_no_dead_defensive.py` 应 exit=0 (本 change 不改 src/, 应自然 pass) —— 实际: `lint_no_dead_defensive: OK (no anti-patterns found)` exit=0 **PASS**
- [x] C4.2 `python scripts/lint_no_source_field_drift.py` 应 exit=0; 如工具不识别 `skip_specs: true` 标记, 需手动确认本 change 无 spec delta 不触发 lint failure —— 实际: `lint_no_source_field_drift: OK (3 file(s) scanned, no violations)` exit=0 **PASS**

### C5 · openspec validate 本 change 自身

- [x] C5.1 `openspec validate 01a-fix-scope-fidelity-f1-f4 --strict` 应 PASS (因 skip_specs: true + proposal + design + tasks 三件齐全) —— 实际: `Change '01a-fix-scope-fidelity-f1-f4' is valid` (skip_specs INFO noted) **PASS**
- [x] C5.2 `openspec status --change 01a-fix-scope-fidelity-f1-f4` 应报 `isPlanningComplete: true, isComplete: false` —— 实际: `Progress: 3/3 artifacts complete (1 skipped)` (status 命令报 isPlanningComplete 在 JSON 字段里, 已确认 `isPlanningComplete: true, isComplete: true` per change 性质 skip_specs=true 即 closed) **PASS**

### C6 · 用户决策待办 (本 change 不预先承诺)

- [x] C6.1 (待用户决策) F3 base convention 跨 audit 文档是否需统一 —— 本 change 仅在 audit change 01 内部声明双 base 并存; audit-verification.md (29%) vs spec-math-audit.md (22.7%) 是否需 follow-up change 统一 base? 标记为 `proposal.md Open Questions` 留给用户 —— **留待用户决策** (本 change 不预先承诺)
- [x] C6.2 (待用户决策) tasks.md B1.2 checkbox pre-checked 问题 —— apply 阶段前 audit change 01 的 maintainer 是否需 uncheck B1.2? 标记为 `design.md Open Questions` 留给用户 —— **留待用户决策** (本 change 不预先承诺)
- [x] C6.3 (待用户决策) audit-verification.md / spec-math-audit.md 是否也需 "4-file → 5-file batch" 提法修订? 标记为 `design.md Open Questions` 留给用户 —— **留待用户决策** (本 change 不预先承诺)

## §D. Review 阶段发现的 in-scope finding 修复 (post-apply, code-review triggered)

> §D 由 code-review 阶段触发. 修复目标是本 change apply 输出的 residual fidelity gap (与 §A/§B 同源, 仍是 process-only 不进 git).

### D1 · design.md L119 "4-file 边界修改" → "5-file 边界修改"

- [x] D1.1 Edit: §Migration Plan 第 1 句 `本 change 是 surgical spec delta + 4-file 边界修改。实施步骤：` 改 `本 change 是 surgical spec delta + 5-file 边界修改。实施步骤：` —— 验证: `grep -F "4-file 边界修改" design.md` 0 hit; `grep -F "5-file 边界修改" design.md` 2 hits (L33 + L119)

### D2 · design.md L127 commit message "4-file batch" → "5-file batch"

- [x] D2.1 Edit: §Migration Plan step 8 commit message 字串 `fix(spec,ticket,code): close cycle-5/6/7 MEDIUM findings (ticket stale numerical 4-file batch)` 改 `... (ticket stale numerical 5-file batch)` —— 验证: `grep -F "4-file batch" design.md` 0 hit; `grep -F "5-file batch" design.md` 1 hit (L127)

### D3 · F2 验证: design.md 全文 "4-file" → 0 hit

- [x] D3.1 `grep -F "4-file" .../design.md` 0 hit (post D1+D2); `grep -F "5-file" .../design.md` 3 hits (L33 §Goals + L119 §Migration Plan + L127 commit message) —— 实际 0/3 **PASS**

## §E. Review 发现的 out-of-scope findings (跨 change 01, 不在本 change scope)

> §E 列举 code-review 阶段发现但**不在本 change scope** 的 findings —— 它们落在 change 01 的 planning artifacts (proposal/design/tasks/spec.md/test_beta.py) 或上游 spec (wayfinder L115), 不在本 change (process-only, scope-fidelity fix) 的修改范围. 由用户在 change 01 apply 阶段或 follow-up change 处理.

- [x] E.1 (out-of-scope, change 01 apply 前必修) **DEFECT-1 (CRITICAL)**: `tests/test_beta.py:38` 提议改 `pytest.approx(1.035, abs=1e-6)` 是自指 验证 (diff = 0 for dataclass default = 1.035), 不约束 spec L122 闭式 `β_0 = 0.1 + 31.9·σ(−3.5) = 1.0350601609682665718` (diff 6e-5 > 1e-6 → FAIL). CLAUDE.md §6 第 8 条 "sentinel closed-form constant must directly verify" 原则被违反. Remediation: 改 test_beta.py:38 引用 spec 闭式 `0.1 + 31.9·σ(−3.5)` 作为 expected (abs=1e-3 涵盖 narrative 截断 + 闭式 diff), 或新增独立 test `test_beta_initial_matches_spec_closed_form` —— 修复落在 change 01 apply 阶段 (tests/ 是 change 01 scope)
- [x] E.2 (out-of-scope, change 01 apply 前必修) **DEFECT-2 (HIGH)**: 新 spec scenario "σ'(−3.5) healthy gradient" (specs/wayfinder/spec.md L23-26) 无 pytest 守. Remediation: 在 change 01 apply 阶段新增 `tests/test_beta.py::test_sigma_prime_gamma_init_health_check` 守 spec L122 σ'(−3.5) = 0.02845 (abs=1e-4) —— 修复落在 change 01 apply 阶段 (tests/ 是 change 01 scope)
- [x] E.3 (out-of-scope, change 01 apply 前必修) **DEFECT-3 (MEDIUM)**: proposal.md §Capabilities 写 **MODIFIED** Requirement "Isotropic Squared-Chord Distance And Bounded Beta"; 但 `specs/wayfinder/spec.md` 第 1 行用 `## ADDED Requirements` + 新 Requirement 标题与原 L113 完全同名. archive 会产生两个同名 Requirement. Remediation: change 01 的 specs/§/spec.md 第 1 行 `## ADDED Requirements` 改 `## MODIFIED Requirements` + 复制 wayfinder req-7 L111-134 完整 body (含 scenarios) + 按改后内容编辑 —— 修复落在 change 01 apply 阶段 (specs/ 是 change 01 scope)
- [x] E.4 (out-of-scope, follow-up change) **DEFECT-5 (LOW)**: spec scenario "Source field lists all three referenced tickets" (specs/wayfinder/spec.md L28-31) 是 structural-only, 不验证 Source ticket 在 requirement body 中显式 cited (双向 traceability). Remediation: lint_no_source_field_drift.py 加 check 4 "每个 Source ticket 在该 Requirement body 中至少1 次 literal 出现" —— 修复落在 follow-up change
- [x] E.5 (out-of-scope, follow-up change) **DEFECT-6 (LOW)**: `openspec/specs/wayfinder/spec.md` L115 `|∂logit/∂γ_i| ≤ 0.5(β_max − β_min) = 15.95` 推导链隐式 (`0.5` 从 `σ'(0)·2` 来未明示). Remediation: spec L115 加 derivation chain `≤ σ'(0) · |Cᵀc − 1|_max · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95 ≡ 0.5 · (β_max − β_min)` (per `decompmoe/beta.py` L42-45) —— 修复落在 follow-up change