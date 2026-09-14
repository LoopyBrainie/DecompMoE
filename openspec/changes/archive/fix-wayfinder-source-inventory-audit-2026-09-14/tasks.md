## 1. Re-verify audit findings (defensive re-run before archive)

> 本节任务在 archive 前必须由 reviewer 重跑一遍，确保 spec.md 与本 fact-check 一致（防止 archive 期间 spec.md 被他人改动但 fact-check 未更新）。

- [x] 1.1 Re-run lint script on spec.md and verify output `OK, 0 violations` — 命令：`python scripts/lint_no_source_field_drift.py openspec/specs/wayfinder/spec.md`（re-run 2026-09-14: `OK (1 file(s) scanned, no violations)`, exit=0 ✓）
- [x] 1.2 Re-run classification script and verify counts: `pure_ticket=17, mixed=15, pure_change=0, NONE=0, TOTAL=32` — 命令：见 design.md §「Re-runnable verification」步骤 2（re-run 2026-09-14: `pure_ticket: 17 / pure_change: 0 / mixed: 15 / NONE: 0 / TOTAL: 32` ✓ 完全匹配）
- [x] 1.3 Re-verify the 6 off-by line locations (L558→L557, L579→L577, L594→L591, L609→L605, L628→L623, L646→L639) by grep + manual inspection — 命令：`grep -n "^\*\*Source:\*\*" openspec/specs/wayfinder/spec.md` 应输出与 proposal.md「Inventory 行号偏差表」一致的 Source 行集合（re-run 2026-09-14: 32 Source 行集合与偏差表 6/6 完全匹配 ✓）
- [x] 1.4 Re-verify L577/L639 style drift (missing backticks + trailing period) — 命令：`sed -n '577p;639p' openspec/specs/wayfinder/spec.md` 应输出无反引号 `wayfinder/tickets/A6a-2.md` + 行尾多 `.`（re-run 2026-09-14: L577/L639 均检测出 `unwrapped-ticket` + `trailing-period` ✓）

## 2. Decision Record resolution (reviewer 必须显式勾选)

> proposal.md「Decision Record」决策点 — 仅 (a) 不破 archive 不可变约定，(b)/(c) 需在 archive 前同步修改 archive 资产。

- [x] 2.1 Reviewer selects Decision 1 option:
  - [x] (a) 不加，旧 `proposal.md` 保持原样（**本 design 推荐**） — reviewer 2026-09-14 显式决议 (a)
  - ( ) (b) 在 `openspec/changes/archive/fix-wayfinder-spec-source-field-drift/proposal.md` 顶部加 `<!-- CORRIGENDUM 2026-09-14: ... -->` 头注 — 未选
  - ( ) (c) 同 (b)，且同时在 archive 的 `design.md` 顶部加头注 — 未选
- [x] 2.2 If option (b) or (c) selected: 在本任务下方写明 corrigendum 头注完整文本（archiver 据此 commit），格式示例：— **N/A**（option (a) selected，condition false，无 corrigendum 需 commit）
  ```
  <!-- CORRIGENDUM 2026-09-14 (fix-wayfinder-source-inventory-audit-2026-09-14):
       原 inventory 7 处违规分类偏差事实更正，详见
       openspec/changes/archive/fix-wayfinder-source-inventory-audit-2026-09-14/proposal.md
       「Fact-check results (2026-09-12)」一节。0 lint violations, 2 style drift at L577/L639.
  -->
  ```

## 3. Archive gate verification

> per CLAUDE.md §3 archive 前置条件：`lint_no_dead_defensive.py` exit=0 + `lint_no_source_field_drift.py` exit=0；`openspec validate` OK。

- [x] 3.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0（re-run 2026-09-14: `OK (no anti-patterns found)`, exit=0 ✓）
- [x] 3.2 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0（覆盖所有 spec 文件，不仅 wayfinder）（re-run 2026-09-14: `OK (3 file(s) scanned, no violations)`, exit=0 ✓）
- [x] 3.3 Run `openspec validate fix-wayfinder-source-inventory-audit-2026-09-14 --strict` and verify OK（re-run 2026-09-14: `Change 'fix-wayfinder-source-inventory-audit-2026-09-14' is valid`, exit=0 ✓）
- [x] 3.4 If Decision 1 = (b) or (c): apply corrigendum head note to archive asset(s) and commit BEFORE archive command — **N/A**（option (a) selected，condition false，无 corrigendum 需 commit）
- [x] 3.5 Run `mv openspec/changes/fix-wayfinder-source-inventory-audit-2026-09-14/ openspec/changes/archive/fix-wayfinder-source-inventory-audit-2026-09-14/` (per archive skill step 5, target name as-is since 2026-09-14 already in name; skip_specs path — no main spec sync) — 2026-09-14 执行中
