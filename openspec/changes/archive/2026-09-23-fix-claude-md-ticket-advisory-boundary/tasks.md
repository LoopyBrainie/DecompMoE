# Tasks

## 1. CLAUDE.md §8 boundary clarification (surgical Edit, 1 处)

- [x] 1.1 Read `CLAUDE.md` §8 当前文字（实测：第 L89-91 行 verbatim "## 8. Wayfinder Arena Index" + "> **2026-08-21 裁决**：wayfinder 不再是必改制品..." + 空行 + "## 9. Key Data Flow..."）确认原裁决块完整。**保留原裁决不修改** ✓
- [x] 1.2 Edit `CLAUDE.md` §8 原裁决引用块**末尾**追加第 2 个引用块（commit `6087ea1` 已含）。引用块文字 verbatim 按 `specs/governance/spec.md` req-gov-4 4 条 obligations + 引用 audit-verification evidence（`commit adf41ef` 2026-09-19 cycle-5/6/7 关闭 + 剩余 cycle-9/12/13 family）。**不要**用 `replace_all`；**不要**修改原裁决文字；**不要**重排其他 § 段 ✓
- [x] 1.3 byte-level LF 检查（per agent memory "Edit tool on Windows can introduce CRLF in non-ASCII files"）：`$bytes = [System.IO.File]::ReadAllBytes('CLAUDE.md'); ($bytes | Where-Object { $_ -eq 13 }).Count` → 0 ✓
- [x] 1.4 独立数值复核：人工 trace 修订后 `CLAUDE.md` §8 完整文字，确认 (a) 原 2026-08-21 裁决引用块（L89-91 verbatim）保留 ✓；(b) 新引用块以 `> **2026-09-19 边界补充**` 开头 ✓；(c) 新引用块引用 audit-verification evidence (`commit adf41ef` + 剩余 cycle-9/12/13 family) ✓；(d) 新引用块不与原裁决语义冲突 ✓

## 2. governance/spec.md 新增 Requirement（spec-level 形式化, anchor req-gov-4）

- [x] 2.1 实测确认 `req-gov-4` 是 next-free anchor：`grep -nE '<a id="req-gov-[0-9]+"></a>' openspec/specs/governance/spec.md` 返回序列 `[1, 2, 3]`（实测 2026-09-23）；req-gov-4 为 next-free ✓
- [x] 2.2 Edit `openspec/specs/governance/spec.md` 末尾追加新 Requirement（commit `6087ea1` 已含）：第一行 `<a id="req-gov-4"></a>`；Requirement heading `### Requirement: Ticket Advisory Boundary — Stale Contamination Monitoring`；body 4 条 verbatim + 3 Scenarios；`Source:` 字段 verbatim `**Source:** \`CLAUDE.md\` §8 (cycle-7 audit-verification L581 meta-洞察 boundary clarification, amended by this change)` ✓
- [x] 2.3 byte-level LF 检查：`openspec/specs/governance/spec.md` ($bytes | Where-Object { $_ -eq 13 }).Count → 0 ✓
- [x] 2.4 spec anchor 100% 覆盖验证：anchor count = 4, Requirement count = 4（req-gov-1/2/3/4）✓

## 3. 验证与提交（surgical）

- [x] 3.1 lint gate（per `CLAUDE.md` §3 `/opsx:archive` 前置条件）：`python scripts/lint_no_dead_defensive.py` → exit 0（"OK (no anti-patterns found)"）；`python scripts/lint_no_source_field_drift.py` → exit 0（"OK (3 file(s) scanned, no violations)"） ✓
- [x] 3.2 跨 spec 一致性 spot-check：`grep -n "req-gov-4" openspec/specs/governance/spec.md` 返回 1 hit；`python -c "content = open('openspec/specs/governance/spec.md', encoding='utf-8').read(); assert 'req-gov-4' in content and 'Ticket Advisory Boundary' in content and 'CLAUDE.md' in content; print('OK')"` → exit 0 ✓
- [x] 3.3 元审计 evidence 链 cross-validation：`grep "adf41ef|cycle-9|cycle-12|cycle-13" CLAUDE.md` 返回 7 hit（边界文字引用 commit SHA + remaining family） ✓
- [x] 3.4 既有 test 全绿：`uv run pytest tests/ -q` → **199 passed, 1 warning in 7.01s**（warning 为 cudaGetDeviceCount，与本 change 无关） ✓
- [x] 3.5 不变性 spot-check：`git diff --stat src/` → 0 改动；`git diff --stat tests/` → 0 改动；`git diff --stat wayfinder/tickets/` → 0 改动；`git diff --stat openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md` → 0 改动；唯一预期改动 = `CLAUDE.md` (+2 lines: 1 new blockquote + 1 empty separator) + `openspec/specs/governance/spec.md` (+31 lines: req-gov-4 body) ✓
- [x] 3.6 单 commit on `dev`：`git add CLAUDE.md openspec/specs/governance/spec.md && git commit -m "process(claude): CLAUDE.md §8 boundary clarification (cycle-7 audit-verification meta-advisory)"` → commit `6087ea1` 已创建（2 files changed, 33 insertions(+))；commit message 含 type `process` / scope `claude` / subject 60 字内 verbatim / body 引用 cycle-7 audit-verification L581 evidence + `commit adf41ef` 2026-09-19 + 剩余 cycle-9/12/13 family / `Co-Authored-By` trailer ✓

Co-Authored-By: Claude Code <noreply@anthropic.com>