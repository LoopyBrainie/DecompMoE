# Tasks: 2026-09-26-followup-spec-wording-bugs-after-precision-disclosure

## 1. Audit closure documentation（active change scope）

本 change 不动 spec / src / tests，仅 audit-closure 留痕。

### Task 1.1 — Audit fact-check closure table

**Goal**: 把 A2.1 + A2.2 audit 清单 5 项的 closure 判定写入 tracked artifacts，使 future audit cycle 可 grep 立即定位 closure 证据。

**Source**: 本 change `proposal.md` §"Audit fact-check" 表

**Done when**:
- [x] proposal.md L## 表格列出 5 项 + 判定 + 引用 commit
- [x] tasks.md（本文件）显式列出 5 项 closure 判定
- [x] `openspec/specs/wayfinder/spec.md` 与 `openspec/specs/decompmoe-skeleton/spec.md` 实测 anchor 覆盖率 = 100%（guard at HEAD `042cacd`）

**Closure 判定表**：

| 清单 ID | 清单 line ref | Requirement 头当前位置 + anchor | Closure 引用 |
|---|---|---|---|
| A2.1.1 | L502 | L506 `<a id="req-35"></a>` | ❌ 误报（清单点错行） — `archive/.../proposal.md` L57 独立判定 |
| A2.1.2 | L524 | L530 `<a id="req-25"></a>` | ✅ commit `2d0950b` (2026-09-26 15:13:03) |
| A2.1.3 | L588 | L596 `<a id="req-27"></a>` | ✅ commit `2d0950b` |
| A2.1.4 | L627 | L637 `<a id="req-33"></a>` | ✅ commit `2d0950b`（req-33 slot resuscitated from archived `24118d6` orphan） |
| A2.2.1 | L293 | L303 `<a id="req-13"></a>` | ✅ commit `de96ba6` (2026-09-26 14:58:47) |

### Task 1.2 — 单 commit on dev

**Goal**: 在 dev 上做单 commit 把本 change 的 `proposal.md` + `tasks.md` 纳入 tracked artifacts；HEAD 不在 merge commit 上（per CLAUDE.md §4 + Memory lesson "offshore-git-workflow"）。

**Done when**:
- [ ] `git status` 显示 0 modified tracked files + 2 new untracked files（proposal.md + tasks.md）
- [ ] `git log -1` 显示本 turn commit；commit message 包含：
  - "audit closure for A2.1 + A2.2 (anchor coverage)" 标识
  - 引用 `archive/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293` (commit `ef45765`)
  - 引用本 plan 路径
- [ ] `git branch --show-current` = `dev`
- [ ] HEAD 不在 merge commit（per `git log -1 --pretty=%P` 无 second parent）

### Task 1.3 — 验收 guard

**Goal**: 在 commit 前 re-verify spec 覆盖率未漂移；若不一致立即停止。

**Done when**（commit 前必跑）：
- [ ] `git show HEAD:openspec/specs/wayfinder/spec.md | grep -c '^<a id='` = 36
- [ ] `git show HEAD:openspec/specs/decompmoe-skeleton/spec.md | grep -c '^<a id='` = 23
- [ ] `git show HEAD:openspec/specs/wayfinder/spec.md | grep -c '^### Requirement'` = 36
- [ ] `git show HEAD:openspec/specs/decompmoe-skeleton/spec.md | grep -c '^### Requirement'` = 23

## 2. Out of scope（per proposal.md §Scope）

- 不修改任何 spec body / src / tests
- 不修改任何 ticket / map.md / lint script
- 不触发任何 active change 的 apply / archive
- 不重写 `archive/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/` 任何文件
- 不做任何 `dev → main / dev → release` 合并

## 3. Verification checklist (post-commit)

- [ ] `python scripts/lint_no_source_field_drift.py` exit=0
- [ ] `python scripts/lint_no_dead_defensive.py` exit=0
- [ ] `git log --oneline -1` 显示本 turn commit on dev
- [ ] working tree clean (`git status --short` 空)
- [ ] HEAD 不在 merge commit（per `git log -1 --pretty=%P` 只有一个 parent）