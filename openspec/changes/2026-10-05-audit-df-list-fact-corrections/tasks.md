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

- [ ] 2.1 断言 `git worktree list` 在册项，确认 13 棵待删树无一在册
- [ ] 2.2 以单次顶层可恢复删除移除 13 棵非 pin 仓库副本树
- [ ] 2.3 保留 `pin6593a06`（审计基线）、`_mut4_scripts`、`_ur_probe_plugin.py`、`_lensB`、`_scratch_adv01`（除 mut2）
- [ ] 2.4 校验：审计基线 `git status --porcelain` 仍为空；`git worktree list` 条目数不变

## 3. 分支与 worktree 卫生

- [ ] 3.1 移除 `worktree-quiet-forest-039d` 的 worktree 注册（已验证无实质未提交内容）
- [ ] 3.2 删除分支 `worktree/quiet-forest-039d`（须在 3.1 之后）
- [ ] 3.3 删除分支 `feat/auto-20260904-b6fca17d`（已合入 dev）
- [ ] 3.4 用 `-D` 删除两个孤儿分支 `worktree-agent-aaca167863d597599`、`worktree-agent-ae19e963fe5074bcf`，并在提交信息中记明「与 dev 无共同祖先，非遗漏合入」
- [ ] 3.5 校验 `git branch -a -vv` 与 `git worktree list` 一致；`git merge-base main dev` 仍退出非零

## 4. `.gitignore` 补模式

- [ ] 4.1 为根级 scratch 文件补 root-anchored 模式（`_tmp_*.py` / `_numdrift_*.py` / `_revcheck_*.py` / `_rvrev_*.py` / `_verify_*.py` / `_w02_*.py` / `_bk_*.bak` / `_r2_*.txt` / `.zed/`）
- [ ] 4.2 刻意不写无锚点的宽模式，避免将来误伤子目录中的同名正式文件
- [ ] 4.3 校验未跟踪文件归零，且无 `spec.md` 副本被卷入

## 5. 门禁与归档

- [ ] 5.1 `python scripts/run_gates.py --change 2026-10-05-audit-df-list-fact-corrections` → `exit 0`
- [ ] 5.2 `openspec validate 2026-10-05-audit-df-list-fact-corrections --type change --strict` 通过
- [ ] 5.3 anchor 计数与本 change 开始前一致（wayfinder 38 / governance 11 / decompmoe-skeleton 23）
- [ ] 5.4 归档本 change

> 勾选规则：每条任务的 `[x]` 必须在**该动作实际执行并校验通过之后**才写入，不预先勾选。
