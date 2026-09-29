# Tasks — B13 + B16

> 行号基线：commit `7bf77af`。本文件不引用 spec 裸行号（B14 即为裸行号漂移的成因）。

## A · B13 — docstring 重写

- [x] A.1 核验 docstring 实际范围与断言句位置（实测 L112–136，断言句 L128–129），记录对原报告 `L129-130` 的纠正
- [x] A.2 核验实际守卫位于 `resurrect_expert`（非本 primitive），实测形态为 `f_per_expert.shape[-1] != cfg.N_e` → `raise ValueError`
- [x] A.3 核验同文件 `resurrect_expert` 内注释已直接否认 docstring（`vacuous self-check ... shape[-1] == shape[0]`）
- [x] A.4 `git show 0b2202e -- src/decompmoe/safeguards.py` 确认该 commit 同时引入修复与 stale docstring（根因）
- [x] A.5 核验权威记录在 `wayfinder` Req 32（英文，anchor `<a id="req-32">`），且中文字符串 `早期草稿` 全仓零命中
- [x] A.6 重写 docstring layer-2 契约段为 `cfg.N_e` 锚定，追加 vacuous 机理 + `0b2202e` 溯源
- [x] A.7 确认未删除任何原有诊断信息

## B · B16 — stale spec 行号

- [x] B.1 核验 `wayfinder` spec L644 实际内容（γ 参数化 Requirement 的 `Source:` 行，Phase 4 边界），与 resurrection 无关
- [x] B.2 核验 Req 28 anchor 与 Req 32 anchor 真实位置
- [x] B.3 将 `spec Req 28 / Req 32 L644` 改为 capability 路径 + anchor id + commit SHA 形式
- [x] B.4 确认 `resurrect_expert` 内其余注释未被改写

## C · 制品

- [x] C.1 `.openspec.yaml`（`schema: spec-driven` / `created: 2026-09-29`）
- [x] C.2 `proposal.md` —— 含对原报告四处事实纠正的表格
- [x] C.3 `design.md` —— 4 项 Decision
- [x] C.4 `tasks.md`（本文件）
- [x] C.5 确认**不创建** `specs/` 目录（无 spec delta）

## D · 验收

- [x] D.1 `git diff --numstat` 确认纯内容改动，无 EOL 混入（实测 21 插 / 10 删）
- [x] D.2 `git show HEAD:src/decompmoe/safeguards.py` 中 `shape[0]` 作为**现行契约**的表述归零（仅存于显式标注 superseded history 的段落）
- [x] D.3 `git grep -n "L644" -- src` 零命中
- [x] D.4 `uv run pytest` 全绿
- [x] D.5 `python scripts/lint_no_dead_defensive.py` exit 0
- [x] D.6 `python scripts/lint_no_source_field_drift.py` exit 0
- [x] D.7 anchor 覆盖回归确认 36 / 23 / 4（本 change 不触碰 spec）
- [x] D.8 提交后断言工作树 == commit object（证明 peer 未再触碰该文件）

## Out of scope

- `wayfinder/tickets/A4-1.md:59` 的 `L122` —— 属 B14 / deferred
- `src/decompmoe/config.py:50` 的 `L122` —— 属 change `fix-config-docstring-beta-line-drift`
- `tests/test_loss.py` 的 `actual=` 嵌入 —— 属 change `2026-09-29-fix-b15-test-loss-actual-embedding`
