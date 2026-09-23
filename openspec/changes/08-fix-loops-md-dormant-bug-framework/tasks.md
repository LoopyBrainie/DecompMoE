# Tasks

## 1. Pre-flight 实测确认（anchor + LOOPS.md 状态）

- [x] 1.1 实测 grep governance spec 当前 anchor 序列：`grep -nE '<a id="req-gov-[0-9]+"></a>' openspec/specs/governance/spec.md` 应返回 req-gov-1 (L7) + req-gov-2 (L51) 共 2 次命中；确认 `req-gov-3` 是下一个空槽（按 `agent memory "Spec anchor 编号必须基于实测 grep 而非'当前 N 个'的假设"` 原则，不得复用"现有 N 个 → 下一个是 N+1"假设）
- [x] 1.2 实测 LOOPS.md 当前 git 状态：`git status LOOPS.md` 应显示 `?? LOOPS.md`（untracked）；`git log --all --oneline -- LOOPS.md` 返回 1 命中（`f8e5b26 docs(audit): round 1 SDD math-conformance review ledger`——这是 2026-09-04 的 58 行版本，与当前 198 行内容不同；current 文件为后续本地修订，未重 commit）
- [x] 1.3 实测 LOOPS.md 当前行数：198 行（[System.IO.File]::ReadAllText + split `\n` 计数）；section 锚实测：L64-69 (Finding 升格路径)、L118-122 (axis-γ)、L178-198 (修改记录)；唯一既存 "dormant bug" 在 L186（9 meta-发现 清单），与本 change 新增条款无冲突

## 2. LOOPS.md 入库 commit（commit 1：chore）

- [x] 2.1 Edit：`git add LOOPS.md`，并验证 `git status LOOPS.md` 显示 `new file: LOOPS.md`（staged for commit）
- [x] 2.2 Commit：`git commit -m "chore(audit): import LOOPS.md to version control"` 并验证 `git show HEAD --stat` 只显示 LOOPS.md（1 file changed, 198 insertions(+)）；commit hash `dd8b9d79f66dce4372e207a7d39a72da5450954d`。注意 `git diff HEAD~1` 还显示 working tree 中既有 uncommitted modifications（`apply-checklist.md` + `openspec/changes/archive/2026-09-11-.../tasks.md`），属本 change 范围外预先存在修改，不影响本 commit
- [x] 2.3 实测 LOOPS.md LF 校验：`git show HEAD:LOOPS.md` 用 `-split \`r\`n` 与 `-split \`n` 都是 198 行 → 无 `\r` 字符（无 CRLF 污染）；全是 LF

## 3. governance spec delta（req-gov-3 ADDED Requirement）

- [x] 3.1 Edit `openspec/specs/governance/spec.md`：在最后一个 Requirement（req-gov-2）后追加 `<a id="req-gov-3"></a>` anchor + `### Requirement: Loop Severity Framework Gap Closure` heading + 5 项 obligations（dormant bug 升级触发器 + audit 自我校核 + verdict 嵌入 + LOOPS.md 反向引用 + LOOPS.md 入库前置约束）+ `**Source:**` 字段首项 backtick-wrapped `` `CLAUDE.md` `` 字面反链 + 2 个 Scenario（dormant bug + audit self-correction）
- [x] 3.2 实测 spec.md 包含 anchor：grep `<a id="req-gov-3">` `openspec/specs/governance/spec.md` 返回 1 次命中（L69）；grep `^### Requirement:` 返回 3 次命中（req-gov-1 L9 + req-gov-2 L53 + req-gov-3 L71 一一对应）；grep `^#### Scenario:` 返回 8 次命中（5 来自 req-gov-1 + 1 来自 req-gov-2 + 2 来自 req-gov-3 = 8；本 change 1 req 配 2 Scenario ✓）
- [x] 3.3 实测 Source 字段合规：3 个 `**Source:**` 行均首项为 backtick-wrapped `CLAUDE.md`（L23 req-gov-1 + L59 req-gov-2 + L102 req-gov-3）；符合 wayfinder req-34 governance-capability dispatch 规则

## 4. LOOPS.md surgical edit（4 处）

- [x] 4.1 Edit `LOOPS.md` L118-122（§DecompMoE audit-verification loop "Cycle 单元"段 axis-γ 子段）：在原 "MEDIUM/HIGH/LOW/INFO" 末尾**新增** dormant bug 升级条款 + 在子段开头新增 "Reading finding text first rule" 子段；引 governance/spec.md req-gov-3 作为 spec 单源真相
- [x] 4.2 Edit `LOOPS.md` L64-69（§DecompMoE spec-math audit loop "Finding 升格路径"段）：在原阈值描述中**新增** dormant bug 升级条款引用；引 governance/spec.md req-gov-3
- [x] 4.3 Edit `LOOPS.md` §"修改记录"末尾：追加 2026-09-23 条目（fix-loops-md-dormant-bug-framework 落地两条过程条款 + meta-06 + meta-08 闭环）
- [x] 4.4 实测 LOOPS.md 新增内容：`dormant bug` 4 命中（原 L188 + 新增 L70/L124/L201，≥ 3 ✓）；`Reading finding text first` 1 命中（L119 axis-γ 子段首句 ✓）；`Loop Severity Framework Gap Closure` 4 命中（L70/L119/L124/L201，≥ 2 ✓）
- [x] 4.5 实测 LOOPS.md LF 校验：split `\r\n` 返回 1（无 CRLF）；split `\n` 返回 201 行（198 + 3 处编辑净增：axis-γ 子段 +5 -1，Finding 升格路径 +1，修改记录 +1）；`git diff --stat LOOPS.md` 待 commit 5.x 后实测

## 5. lint gate 与验证（commit 2 前置）

- [x] 5.1 lint gate 跑：`python scripts/lint_no_source_field_drift.py` 应 PASS（governance spec 新增 Requirement 的 Source 字段首项 backtick-wrapped `CLAUDE.md`，合规；无 wayfinder Source 字段被污染）。**实际**：初跑 FAIL（L102 有 plain-text `CLAUDE.md` 违例 — parenthes 内未 backtick-wrapped）；已 fix（将 "parallel to CLAUDE.md" 改为 "parallel to \`CLAUDE.md\`"）；复跑 OK exit=0（3 file(s) scanned, no violations）
- [x] 5.2 lint gate 跑：`python scripts/lint_no_dead_defensive.py` 应 PASS（spec delta 是纯内容追加，无 defensive code pattern）。**实际**：OK exit=0（no anti-patterns found）
- [x] 5.3 governance spec anchor 100% 覆盖实测：`grep '<a id="req-gov-[0-9]+"></a>'` 返回 3 命中（req-gov-1 L7 + req-gov-2 L51 + req-gov-3 L69）；`grep '^### Requirement:'` 返回 3 命中（L9/L53/L71），与 anchors 一一对应

## 6. commit 2 + post-archive 独立复核

- [ ] 6.1 Edit 提交：`git add openspec/specs/governance/spec.md LOOPS.md && git commit -m "fix(governance+LOOPS): close meta-06 + meta-08 — dormant bug escalation clause + audit self-correction rule"`；验证 `git log -2 --stat` 显示两个 commit 信息正确（chore 入库 + fix spec delta + surgical edit）
- [ ] 6.2 post-archive 独立数值闭环复核：
  - dormant bug 升级触发器公式代入：cycle-13 finding 1 `latent_risk=HIGH × trigger_probability=HIGH` ⇒ HIGH dormant-bug（满足 either-dimension rule）；cycle-5 finding 1 `latent_risk=LOW × trigger_probability=LOW` ⇒ MEDIUM retained（no-op boundary）
  - audit self-correction 关键词代入：cycle-17 finding 1 finding-keyword "正面记录" ⇒ verdict-INFO；cycle-1 finding 1 finding-keyword "低危文字漂移" ⇒ verdict-LOW
  - 实测 grep 确认每条 retro-application 闭环（与 design.md Decision 1-2 的两种边界用例对齐）
- [ ] 6.3 archive 前置：`openspec validate 08-fix-loops-md-dormant-bug-framework --type change --strict` 应 PASS（governance spec delta 是 ADDED 而非 MODIFIED，符合 wayfinder req-34 governance-migration Scenario；spec.md 锚点齐全）
- [ ] 6.4 archive 执行：`openspec archive 08-fix-loops-md-dormant-bug-framework --yes` 应成功；archive 后 `git log --oneline -- openspec/changes/archive/08-fix-loops-md-dormant-bug-framework/` 应返回 commit 记录