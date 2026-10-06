# Tasks

## 1. 事实校正（已完成，随本 change 提交）

- [x] 1.1 在 HEAD 实测逐条复核 DF-01…DF-09，不继承清单的 `STILL_REAL` / `PARTIALLY_REAL` 裁决
- [x] 1.2 定位 DF-08 的 `~0.83%`：确认为 401 行的 prior 旧值，live 闭式 `66_336 FLOP / ~1.22%` 已有守护
- [x] 1.3 定位 DF-09 的 `_staged/`：确认不存在、从未入库、未跟踪文件中 `spec.md` 副本数为 0
- [x] 1.4 枚举审计根下全部非 pin 仓库副本树，取得真实对象数（13），而非清单的 3
- [x] 1.5 判定 6 棵带 `.git` 指针的树未在 `git worktree list` 注册，确认删除不经由 git 层
- [x] 1.6 判定 `worktree-quiet-forest-039d` 的 123 条 modified 为纯行尾差异（`--ignore-cr-at-eol` 下 diff 为空）
- [x] 1.7 核对 DF-05 的 `origin_ids` 错链与报告行号偏移
- [x] 1.8 把上述结果写入 `design.md`

## 2. 外部审计目录清理

- [x] 2.1 断言 `git worktree list` 在册项，确认 13 棵待删树无一在册（实测在册 3 项，命中 0/13）
- [x] 2.2 以单次顶层可恢复删除移除 13 棵非 pin 仓库副本树（实测 13/13 已移除，`rm` exit 0）
- [x] 2.3 保留 `pin6593a06`（审计基线）、`_mut4_scripts`、`_ur_probe_plugin.py`、`_lensB`、`_scratch_adv01`（除 mut2）（实测全部仍在）
- [x] 2.4 校验：审计基线 `git status --porcelain` 为空；`git worktree list` 在本阶段结束时条目数未变
- [ ] 2.5 `scratch/` 未清空（残留 4 个 audit 脚本 `nd05_*.py`），按计划的条件式守卫**不删除**，留作未决

## 3. 分支与 worktree 卫生

- [x] 3.1 移除 `worktree-quiet-forest-039d` 的 worktree 注册（删除前复验：`--ignore-cr-at-eol` diff 为空、无暂存、无未跟踪）
- [x] 3.2 删除分支 `worktree/quiet-forest-039d`（须在 3.1 之后；实测先 remove 后 `-d` 成功）
- [x] 3.3 删除分支 `feat/auto-20260904-b6fca17d`（已合入 dev）
- [x] 3.4 用 `-D` 删除两个孤儿分支 `worktree-agent-aaca167863d597599`、`worktree-agent-ae19e963fe5074bcf`（实测 `-d` 如预期以 "not fully merged" 拒绝，`-D` 成功；两者停在 `051f247`，与 dev 无共同祖先）
- [x] 3.5 校验 `git branch -a -vv` 与 `git worktree list` 一致（实测 3 类目标分支均已消失，worktree 降至 2 项）；`git merge-base main dev` 仍退出 1，既有状态未变

## 4. `.gitignore` 补模式

- [x] 4.1 为根级 scratch 文件补 root-anchored 模式（9 条模式，覆盖实测 45 个未跟踪 scratch 文件）
- [x] 4.2 刻意不写无锚点的宽模式；用 `git check-ignore` 对假设路径实测：根级 `_tmp_probe.py` 被忽略，`tests/` `src/` `docs/` 下的同名文件均可见
- [x] 4.3 校验未跟踪文件归零（仅剩本 change 自身 4 个文件），且 `spec.md` 副本 0 命中
- [x] 4.4 保留原文件的 LF 行尾：首次提交把整文件翻成 CRLF，已改回并 `--amend`，最终 diff 为纯 +14 行

## 5. 门禁

- [x] 5.1 `python scripts/run_gates.py --change 2026-10-05-audit-df-list-fact-corrections` → `exit 0`（5 lint + 2 validate + anchor 70 + pytest 483 passed/1 skipped，全 PASS，`GATE OK: all gates passed on a stable worktree`）
- [x] 5.2 `openspec validate 2026-10-05-audit-df-list-fact-corrections --type change --strict` 通过
- [x] 5.3 anchor 计数与本 change 开始前一致（门禁报 anchor coverage 70 anchor(s) across 3 capabilities；wayfinder 38 / governance 11 / decompmoe-skeleton 23）

> 勾选规则：每条任务的 `[x]` 必须在**该动作实际执行并校验通过之后**才写入，不预先勾选。
>
> 本文件不列「归档本 change」这类任务：归档发生在 tasks 全部完成之后，且归档后该文件即不可写回，写成 task 等于把 change 自己的归档设成它自己的前置条件，那一条永远勾不上。归档后需人工执行的步骤记在 `proposal.md` 的 Post-archive checklist，不进本文件。
