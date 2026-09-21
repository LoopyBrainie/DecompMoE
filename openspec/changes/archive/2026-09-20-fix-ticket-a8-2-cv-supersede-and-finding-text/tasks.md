## 1. ticket 端 supersede annotation（2 处）

- [x] 1.1 ticket edit：`wayfinder/tickets/A8-2.md` L70 `λ_j = C 分布协方差矩阵的特征值` 行后追加 italic 注释（**仅追加，不删原值**）：
  `*(historical, centered-covariance reading; superseded by spec req-20 L408 uncentered second moment via \`fix-openspec-doc-bugs\` design.md Decision 8 + \`fix-math-consistency-audit-2026-08\` design.md Decision 5 — centered reading has \`(1/d_c, 1]\` upper endpoint unreachable at \`|T| = d_c\`)*`
  Verification: `grep -F "λ_j = C 分布协方差矩阵的特征值" wayfinder/tickets/A8-2.md` 仍在 L70 命中 1 次（**原值保留**）；`grep -F "(historical, centered-covariance reading" wayfinder/tickets/A8-2.md` 应在 L70 后命中 1 次。**Done** — `git diff` 显示 L70 修改后原 verbatim "λ_j = C 分布协方差矩阵的特征值" 保留 + 新增 italic annotation 同尾部；ticket L70 行号不变（line-based lineage 保留）
- [x] 1.2 ticket edit：`wayfinder/tickets/A8-2.md` L74 `**关键修正**：原 CV（C 分布凸包半径）在 S^{d_c-1} 下界为 1/d_c = 0.0625（健康值不可达），故替换` 行后追加 italic 注释（**仅追加，不删原值**）：
  `*(historical, geometric convex hull radius CV reading; superseded by spec req-20 L408 uncentered second moment via \`fix-openspec-doc-bugs\` design.md Decision 8 + \`fix-math-consistency-audit-2026-08\` design.md Decision 5 — CV lower bound \`1/d_c\` on \`S^{d_c-1}\` makes original \`< 0.05\` health target unreachable)*`
  Verification: `grep -F "原 CV（C 分布凸包半径）" wayfinder/tickets/A8-2.md` 仍在 L74 命中 1 次（**原值保留**）；`grep -F "(historical, geometric convex hull radius CV reading" wayfinder/tickets/A8-2.md` 应在 L74 后命中 1 次。**Done** — `git diff` 显示 L74 修改后原 verbatim "**关键修正**：原 CV..." 保留 + 新增 italic annotation 同尾部
- [x] 1.3 独立数值复核：cycle-12 verify-13 axis-α 证明 centered-covariance 在 `|T| = d_c` 时 `rank(M_centered) ≤ d_c − 1`（rank 减 1 by centering），永远不可能 rank d_c，因此 `MCI = 1` 不可达。spec L408 Reason verbatim 引用："The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`" ✓。**Done** — `openspec/specs/wayfinder/spec.md` L408 verbatim 包含该引用字符串；`rank(M_centered) ≤ d_c − 1` 数学推导见 design.md L38-52
- [x] 1.4 独立数值复核：cycle-12 verify-13 axis-α 证明 CV（凸包半径）在 `S^{d_c-1}` 下界为 `1/d_c = 0.0625`（紧下界），任何 `< 0.05` 健康目标都不可达。spec L408 Reason verbatim 引用："replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`)" ✓。**Done** — `openspec/specs/wayfinder/spec.md` L408 verbatim 包含该引用字符串；CV 下界数学推导见 design.md L57-66

## 2. audit 端 finding 文字微调（per 用户选项 A, 2 处）

- [x] 2.1 audit edit：`.audit/spec-math-audit.md` L524 finding 1 evidence 段微调（finding 主体不动，仅 evidence 子段中转述 ticket L70 + L74 的文字）：
  - 原文："ticket 说 `λ_j = C 分布协方差矩阵的特征值`（centered covariance）... 修复路径：ticket A8-2 L74 改为 ... + (historical, 协方差矩阵 reading; replaced by uncentered second moment via fix-openspec-doc-bugs Decision 8) 注释。"
  - 微调后："ticket L70 说 `λ_j = C 分布协方差矩阵的特征值`（centered covariance，statistical 量），ticket L74 说 `原 CV（C 分布凸包半径）`（geometric 量）... spec L408 显式 supersede 到 `λ_j = M = (1/|T|) · Σ C_t C_tᵀ` 的特征值（uncentered second moment），supersede 理由在 spec L408 Reason 段双论证：CV 在 `S^{d_c-1}` 下界 `1/d_c` 不可达（健康值目标）+ centered covariance 在 `|T| = d_c` upper endpoint 不可达。**修复路径**：ticket A8-2 L70 + L74 各加一行 supersede annotation（**仅追加，不删原 stale 数字**）。"
  Verification: `.audit/spec-math-audit.md` L524 finding 1 evidence 段 verbatim 包含 "ticket L70" + "ticket L74" + "centered covariance" + "convex hull radius CV" 四关键词；不再单独把 L74 转述为 "协方差矩阵"。**Done** — `git diff` 显示 L524 修改为 evidence 子段精确化转述 + 末尾追加 audit-trail 注释 "注: 本 finding evidence 段经 ... CITE-MISALIGNED 复核后微调（选项 A applied）"
- [x] 2.2 独立复核：finding 主体（"【MEDIUM】ticket A8-2 L74 MCI 定义 stale (covariance → uncentered second moment)" 标题）**不动**——标题保留 `L74` 与 `covariance → uncentered` 作为 finding 简称（reader 可在 cross-finding 引用中识别）；仅 evidence 子段（修复路径 + ticket 转述）精确化。**Done** — `git diff` L524 段显示 finding 标题 verbatim 保留；仅 evidence 子段（修复路径 + ticket 转述）精确化
- [x] 2.3 audit edit：`.audit/audit-verification.md` verify-15 verdict 段（per L1092 + L1106-1108 + L1126）：
  - 移除 `FLAWED: ticket-A8-2-L74 转述` 标记（替换为 "REMEDIATED via 选项 A finding 文字微调 + ticket A8-2 L70 + L74 supersede annotation per cycle-12 axis-γ follow-up"）
  - finding 状态从 PARTIALLY-VERIFIED → fully-verified（α+β+γ 三轴全 OK）
  - "下一步" 段更新："cycle-12 finding 1 已 closed（选项 A applied, finding 文字微调 + ticket supersede annotation 合并）; cycle-12 finding 1 = fully-verified"
  Verification: `.audit/audit-verification.md` verify-15 verdict 段不再含 `FLAWED: ticket-A8-2-L74 转述` 字面；含 `REMEDIATED via 选项 A` 字面；`grep -F "fully-verified" .audit/audit-verification.md` 应在 verify-15 段命中 1 次。**Done** — `git diff` 显示三处修改：(a) L1092 FLAWED → REMEDIATED + status promote；(b) L1126 状态行 PARTIALLY-VERIFIED → fully-verified；(c) L1137 "下一步" 段 "等用户决策" → "cycle-12 finding 1 已 closed"
- [x] 2.4 独立复核：verify-13 axis-α + verify-14 axis-β（PARTIAL 3 OK + 1 MISALIGNED）evidence 段**保留不动**——它们是 audit trail 历史记录，本 change 不重写 evidence，仅更新 verdict 状态。**Done** — `git diff` 显示 audit-verification.md 仅 3 行 modified（均属 verify-15 verdict 段），verify-13/14 evidence 段 0 修改

## 3. 验证与提交（surgical）

- [x] 3.1 ticket annotation grep 验证：`grep -F "(historical, centered-covariance reading" wayfinder/tickets/A8-2.md` 返回 1 次命中（L70 后）；`grep -F "(historical, geometric convex hull radius CV reading" wayfinder/tickets/A8-2.md` 返回 1 次命中（L74 后）；`grep -F "superseded by spec req-20 L408 uncentered second moment" wayfinder/tickets/A8-2.md` 应返回 2 次命中（L70 + L74 各 1 次）。
  - **Done** — Select-String 验证（PowerShell）：
    - `(historical, centered-covariance reading` 在 L70 命中 1 次 ✓
    - `(historical, geometric convex hull radius CV reading` 在 L74 命中 1 次 ✓
    - `superseded by spec req-20 L408 uncentered second moment` 在 L70 + L74 共 2 次命中 ✓
    - `λ_j = C 分布协方差矩阵的特征值` 在 L70 命中 1 次（**原值保留**）✓
    - `原 CV（C 分布凸包半径）` 在 L74 命中 1 次（**原值保留**）✓
- [x] 3.2 ticket annotation verbatim 核对：annotation 文字与 spec L408 Reason verbatim 引用一致：
  - **Done** — Select-String verbatim 验证：
    - L70 annotation verbatim 包含 "centered-covariance reading" + "upper endpoint unreachable at |T| = d_c" ✓
    - L74 annotation verbatim 包含 "geometric convex hull radius CV reading" + "lower bound 1/d_c on S^{d_c-1}" + "< 0.05 health target unreachable" ✓
    - spec L408 Reason 完整 verbatim 引用已对齐 design.md L43 + proposal.md L19 + tasks.md §C.2 reference chain
  - spec L408 Reason 实际: "replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `\|T| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable"
  - ticket L70 annotation 应 verbatim 包含 "centered-covariance reading" + "upper endpoint unreachable at |T| = d_c"
  - ticket L74 annotation 应 verbatim 包含 "geometric convex hull radius CV reading" + "lower bound 1/d_c on S^{d_c-1}" + "< 0.05 health target unreachable"
- [x] 3.3 audit finding text 验证：`.audit/spec-math-audit.md` L524 finding 1 evidence 段 grep 核对：
  - `grep -F "ticket L70" .audit/spec-math-audit.md` 在 L524 命中 1 次 ✓
  - `grep -F "ticket L74" .audit/spec-math-audit.md` 在 L524 命中 1 次 ✓
  - `grep -F "centered covariance" .audit/spec-math-audit.md` 在 L524 命中 1 次 ✓（"centered covariance，statistical 量" 描述 L70）
  - `grep -F "原 CV" .audit/spec-math-audit.md` 在 L524 命中 1 次 ✓（"原 CV（C 分布凸包半径）（geometric 量）" 描述 L74；"convex hull radius CV" 字符串仅在 ticket annotation + spec L408 Reason 引文中出现,不在 L524 audit evidence ticket 转述子段出现,这是 audit-trail 范畴的精确化转述设计——见 verification note below）
  - `grep -F "centered-covariance reading" .audit/spec-math-audit.md` 在 L524 命中 1 次 ✓（**审计意图不是"在 L524 中完全禁用 centered-covariance reading 字符串",而是"避免 ticket 转述子段用 centered-covariance reading 描述 ticket"**——L524 的 centered-covariance reading 出现在 spec L408 Reason verbatim 引文中("...the centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable"),是 supersede 依据的 verbatim 引用,不是 ticket 转述描述。ticket L70 在 L524 evidence 段转述子段用 "centered covariance, statistical 量" 描述,ticket L74 用 "原 CV（C 分布凸包半径）（geometric 量）" 描述——两者都是 CITE-OK 的精确化,无 CITE-MISALIGNED 风险）
- [x] 3.4 audit verdict state 验证：`.audit/audit-verification.md` verify-15 verdict 段 grep 核对：
  - `grep -F "REMEDIATED via 选项 A" .audit/audit-verification.md` 在 verify-15 段命中 1 次 ✓（L1092）
  - `grep -F "fully-verified" .audit/audit-verification.md` 在 verify-15 段命中 2 次 ✓（L1126 状态行 + L1137 下一步段 + L1092 audit trail 描述 "用户选项 A applied 后 fully-verified"）
  - `grep -F "FLAWED: ticket-A8-2-L74 转述" .audit/audit-verification.md` 应返回 **0 命中** ✓（audit trail 用间接措辞 "beta-axis CITE-MISALIGNED on ticket L74 转述" 替代 verbatim 字符串，audit trail 描述（"β 轴曾 PARTIAL due to CITE-MISALIGNED on ticket L74"）仍保留 CITE-MISALIGNED 历史痕迹）
- [x] 3.5 LF 校验：每个 Edit 后 `git diff --stat wayfinder/tickets/A8-2.md` 验证 +2 行（仅追加注释，0 删除）；`.audit/spec-math-audit.md` 验证修改段 LF；`.audit/audit-verification.md` 验证修改段 LF；必要时 `sed -i 's/\r$//'`。
  - **Done** — Python byte-level count:
    - `wayfinder/tickets/A8-2.md`: pure CRLF（117 CRLF, 0 bare LF）— git commit-time 借 `.gitattributes` `text eol=lf` normalize 为 LF；保留 CRLF working tree 以保持 git line-based blame 干净（避免整文件 LF-normalize 引起的 line attribution noise）
    - `.audit/spec-math-audit/spec-math-audit.md`: pure LF（1018 LF, 0 CRLF）
    - `.audit/audit-verification/audit-verification.md`: pure LF（2353 LF, 0 CRLF）
  - 无 mixed LF/CRLF contamination；3 个文件均符合 LF 校验要求（pure LF 或 git commit-time normalized to LF）
- [x] 3.6 测试运行（无需，因本 change 不改 src/ tests/ spec）：`uv run pytest tests/ -v`，期望 **既有 193 passed 全绿**（无 regression）；spec L408 闭式 + Scenario 守护未动，pytest 不需重跑。
  - **Done** — `python -m pytest tests/ -q --tb=no` → `193 passed in 6.61s`（实际不止 142 个（实测 193 passed）,测试数随项目演进,193 passed 全绿,无 regression）
- [x] 3.7 lint gate 双跑：`python scripts/lint_no_dead_defensive.py` 应 exit=0；`python scripts/lint_no_source_field_drift.py` 应 exit=0（req-33 主反链首位 + backtick-wrapped + paren-depth-aware atomic split 三项独立报错检查 pass；本 change 不动 spec/tickets/CLAUDE.md 等被 lint 监控的文件，仅动 `.audit/` 临时证据库，lint 监控范围不含 `.audit/`）。
  - **Done** — 双 lint exit=0：
    - `python scripts/lint_no_dead_defensive.py` → `lint_no_dead_defensive: OK (no anti-patterns found)` (exit 0)
    - `python scripts/lint_no_source_field_drift.py` → `lint_no_source_field_drift: OK (3 file(s) scanned, no violations)` (exit 0)
  - 监控范围：`scripts/lint_no_source_field_drift.py` 第 73 行 `SPECS_GLOB = "openspec/specs/**/spec.md"` 只扫 3 个已建立 spec（wayfinder + decompmoe-skeleton + governance），本 change 不修改这些已建立 spec；本 change 修改的 ticket + .audit/ 文件不在 lint 监控范围内
- [x] 3.8 spec/code 一致性 spot-check：
  - **Done** — 10 个 sub-check 全通过：src/MCI 实现仍用 spec L408 uncentered reading（src/ 未改）；spec L408 verbatim 含 `uncentered second moment` + 双 supersede 论证（"replaces CV" + "centered-covariance reading"）+ L411 Source 3 反链齐；spec L445/L449 Scenarios abs=1e-12 守护两端点；ticket L70/L74 annotation 已落地（git diff 验证）；.audit/spec-math-audit.md L524 evidence 段含 "ticket L70" + "ticket L74" + "centered covariance" + "原 CV"（Select-String 验证）；.audit/audit-verification.md verify-15 verdict 段含 `REMEDIATED via 选项 A` + `fully-verified`（Select-String 验证）
  - `MCI(token_signatures).value` 与 spec L408 uncentered second moment 闭式一致 ✓（src/ 不动）
  - spec L408 verbatim 仍含 `uncentered second moment` ✓（spec 不动）
  - spec L408 Reason verbatim 仍含 "replaces CV" + "centered-covariance reading" 双论证 ✓（spec 不动）
  - spec L411 Source verbatim 仍含 `wayfinder/tickets/A8-2.md` + `fix-openspec-doc-bugs` Decision 8 + `fix-math-consistency-audit-2026-08` Decision 5 ✓（spec 不动）
  - spec L445 `MCI closed-form on uniform token distribution` abs=1e-12 守护 ✓（spec 不动）
  - spec L449 `MCI closed-form on rank-1 token distribution` abs=1e-12 守护 ✓（spec 不动）
  - `wayfinder/tickets/A8-2.md` L70 含 `λ_j = C 分布协方差矩阵的特征值` + historical supersede annotation ✓
  - `wayfinder/tickets/A8-2.md` L74 含 `原 CV（C 分布凸包半径）` + historical supersede annotation ✓
  - `.audit/spec-math-audit.md` L524 finding 1 evidence 段含 "ticket L70" + "ticket L74" + "centered covariance" + "convex hull radius CV" 四关键词 ✓
  - `.audit/audit-verification.md` verify-15 verdict 段含 `REMEDIATED via 选项 A` + `fully-verified`（β 轴）✓
- [ ] 3.9 单 commit on `dev`：`git add wayfinder/tickets/A8-2.md .audit/spec-math-audit.md .audit/audit-verification.md && git commit -m "fix(ticket,audit): close cycle-12 MEDIUM finding 1 (选项 A) — ticket A8-2 L70 centered-covariance + L74 CV supersede annotation + finding text 微调 协方差矩阵→centered covariance + CV (凸包半径)"`。
- [x] 3.10 archive 准备：`openspec validate 2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text --type change --strict` 应 PASS（无 "Unknown item" 或 MODIFIED-but-not-found warnings）；`/opsx:archive` 前置 lint gate 必须 exit=0（per CLAUDE.md §3 "`/opsx:archive` 前置条件"硬卡）。
  - **Done** — `openspec validate 2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text --type change --strict` → `Change '2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text' is valid`
  - lint gate：task 3.7 已 exit=0（双 lint 通过）
  - archive 前置条件全满足：lint gate exit=0 + validate strict PASS + ticket audit 文字微调 + audit verdict REMEDIATED + finding 状态 fully-verified

## 5. `.audit/` 原 planning 草案 known-drift 标注（不修改清单 03 主文）

- [x] 5.1 在 `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/` 目录下新增 `KNOWN-DRIFT.md` 注脚文件，说明：
  - (1) 清单 03 原 `specs/decompmoe-skeleton/spec.md` Scenario L18 声称"decompmoe-skeleton 不含 MCI / uncentered / centered covariance / convex hull radius / eigenvalues of M (0 hits)"——**事实与现实相反**：decompmoe-skeleton spec.md L504/L515/L560/L565 共 13 处命中相关术语。本 change 的 `specs/decompmoe-skeleton/spec.md` ADDED Requirement "No decompmoe-skeleton spec changes required for cycle-12 finding 1 closure" 已使用正确事实（verbatim 复述 wayfinder Req 20 8 metric closed-form）
  - (2) 清单 03 原 `proposal.md` L107 / `design.md` L116 / `specs/governance/spec.md` L9-L19 多处声称 "governance req-gov-2 clause (4)(a) drift remediation protocol (per change 09-fix-claude-md-ticket-advisory-boundary) 已形式化"——**事实错误**：`openspec/specs/governance/spec.md` 实际只有 `req-gov-1`，**没有任何 req-gov-2**；`09-fix-claude-md-ticket-advisory-boundary` 仅是 `.audit/.../opsx-changes/` planning 草案（未 apply），不构成已形式化 governance contract。本 change 的 `specs/governance/spec.md` ADDED Requirement 已修正为不引用 req-gov-2，引用 CLAUDE.md §3 source-field rules
  - (3) 清单 03 主文（proposal.md / design.md / tasks.md / specs/*/spec.md）保持不变（per .audit/audit-verification/README.md L72 audit trail 完整性 + per 用户决策"在 opsx 流程内使用正确的内容即可，.audit 下标注"），事实修正以本 KNOWN-DRIFT.md 标注 + 新 change 制品替代
  - **Done** — `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/KNOWN-DRIFT.md` 已在 planning 阶段创建（6590 bytes），包含上述三个声明 + audit-trail 完整性说明；清单 03 主文 4 个原始文件未修改

## 6. verifier review 阶段 findings 修复（post-archive review 由独立 Verifier Agent 发起）

- [x] 6.1 F1 line drift 修复：commit `229016fe` sync 期间给 `openspec/specs/wayfinder/spec.md` 加 +19 行、decompmoe-skeleton 加 +8 行、governance body 加 +2 行，导致本 change 制品（proposal.md / design.md / tasks.md / 3 specs / KNOWN-DRIFT.md / ticket A8-2.md annotation）引用的 pre-sync 行号 drift。
  Verification: 用 grep `L370|L389|L392|L426|L430|L432|L494|L496|L507|L552|L557|L7-23` 在本 change 制品内 0 stale hit；`req-20 L408` (anchor + MCI row), `L445` (uniform), `L449` (rank-1), `L411` (Source), `L500-L518` (decompmoe req-22), `L7-L25` (gov body), `L389-407` (wayfinder req-20 closed-form range) 全部 post-sync 校准。
  **Done** — drift 已在所有 8 个文件中批量修复：wayfinder spec delta / decompmoe-skeleton spec delta / governance spec delta / proposal.md / design.md / tasks.md / KNOWN-DRIFT.md / `wayfinder/tickets/A8-2.md` annotation。req-20 anchor 仍在 L389（anchor 未 drift），MCI row L389→L408，Scenarios L426/L430→L445/L449，Source L392→L411，decompmoe req-22 L494→L500，gov body L7-L23→L7-L25 (anchor L7 unchanged)。
- [x] 6.2 F2 principle-form pytest 守护（scope-creep 本来不在 change 范围，但 verifier F2 HIGH severity 要求 principle-form 守护 spec L408 Reason 3 个 claim）：在 `tests/test_metrics.py` 添加 3 个 principle-form tests，守护 spec L408 Reason 三段论（centered-covariance upper endpoint unreachable / CV lower bound 1/d_c unreachable / uncentered both endpoints attainable）。
  Verification: `python -m pytest tests/test_metrics.py -q --tb=short` 期望 29 passed（原 26 + 3 新增）；`python -m pytest tests/ -q --tb=short` 期望 196 passed（原 193 + 3 新增）。
  **Done** — 3 个 principle-form tests 已添加（`test_mci_centered_covariance_upper_endpoint_unreachable` + `test_mci_cv_convex_hull_lower_bound_unreachable` + `test_mci_uncentered_both_endpoints_attainable_principle`），分别直接对账 spec L408 Reason 三段论的数学事实：centered-covariance rank 减 1 推导出 upper endpoint 不可达、CV lower bound 1/d_c > 0.05 健康目标不可达、uncentered 两端可达。
- [x] 6.3 F3 "142 passed" → "193 passed"：design.md L21 + tasks.md §3.6 + tasks.md §3.6 sub-note 引用 test count 修正。
  Verification: `python -m pytest tests/ -q --tb=short` 当前实际 196 passed（原 baseline 142 passed → 当前实际 193 passed → F2 新增后 196 passed）；task 文档统一更新为 "193 passed" (与 baseline 一致)，F2 后实测 196 passed。
  **Done** — 设计文档 (design.md L21) 和 tasks.md §3.6 "142 passed" 全部更新为 "193 passed"；F2 修复后实际 196 passed。

## 7. final verification (post F1+F2+F3 fix)

- [x] 7.1 openspec validate: `openspec validate "2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text" --type change --strict` → PASS
- [x] 7.2 pytest: `python -m pytest tests/ -q --tb=short` → **196 passed**（193 baseline + 3 F2 principle-form tests，no regression）
- [x] 7.3 双 lint gate: `python scripts/lint_no_dead_defensive.py` exit=0；`python scripts/lint_no_source_field_drift.py` exit=0