## 1. Read ticket A6a-2 L61-66

- [x] 1.1 Read `wayfinder/tickets/A6a-2.md` L61-66，确认 ③ Dead Expert Splitting Resurrection 段 bullet 列表完整（**触发** / **目标** / **分裂动作** / **限流** / **设计哲学**），L63 实际 verbatim 为 `- **触发**：`f_i^avg < 1/128` 持续 200 steps`。验证：人工 trace L61-66 + `grep -n "^- \*\*触发\*\*" wayfinder/tickets/A6a-2.md` 返回 1 hit

## 2. Edit ticket A6a-2 L63 追加 italic annotation

- [x] 2.1 Edit `wayfinder/tickets/A6a-2.md` L63，仅在该 bullet 行**末尾追加** italic annotation。原 L63 行：
  ```markdown
  - **触发**：`f_i^avg < 1/128` 持续 200 steps
  ```
  修订后 L63 行：
  ```markdown
  - **触发**：`f_i^avg < 1/128` 持续 200 steps  *(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L245 `f_threshold = 1/(2·N_e)` via `fix-openspec-doc-bugs` design.md Decision 7)*
  ```
  验证：`grep -n "historical, threshold 1/128 at N_e=64" wayfinder/tickets/A6a-2.md` 返回 1 hit（L63 annotation）；`grep -n "f_i^avg < 1/128" wayfinder/tickets/A6a-2.md` 仍返回 1 hit（原触发描述 verbatim 保留）

- [x] 2.2 独立数值复核：人工 trace 修订后 L63 完整 bullet 行，确认（a）原触发描述 verbatim 保留；（b）annotation 以 `*(historical, ...` 开头 + `)*` 闭合；（c）引用 spec req-13 L245 + `f_threshold = 1/(2·N_e)` 参数化形式 + `fix-openspec-doc-bugs` change 名 + Decision 7；（d）markdown 渲染无歧义（外层 italic + 内嵌双 backtick-wrapped 公式 + change 名）

- [x] 2.3 LF/CRLF 校验（实际：项目约定是 LF via `.gitattributes` `*.md text eol=lf`，working tree CRLF 是 autocrlf=false 不转换结果；commit 时 Git 会强制 LF 转换）。验证：`git diff --stat wayfinder/tickets/A6a-2.md` = `1 insertion(+), 1 deletion(-)`（inline 行末追加，行数变化为 0）；working tree 字节 = 109 CRLF + 0 LF-only（Edit 未污染）；commit 时 `.gitattributes` 会强制 LF，与 HEAD blob (109 LF + 0 CRLF) 对齐

## 3. Cross-validation 与 grep 验证

- [x] 3.1 annotation 文字 grep 验证：`grep -n "historical, threshold 1/128 at N_e=64" wayfinder/tickets/A6a-2.md` → 1 hit；`grep -n "superseded by spec req-13 L245" wayfinder/tickets/A6a-2.md` → 1 hit；`grep -n "fix-openspec-doc-bugs" wayfinder/tickets/A6a-2.md` → 1 hit；`grep -n "Decision 7" wayfinder/tickets/A6a-2.md` → 1 hit

- [x] 3.2 spec/ticket/src 三角 cross-validation：`grep -n "Previously hardcoded to 1/128" src/decompmoe/safeguards.py` → 1 hit（L29 legacy 注释）；`grep -n "historical, threshold .1/128." openspec/specs/wayfinder/spec.md` → 1 hit（L247 Source，反引号包裹 `\`1/128\``）；三处一致引用 `(historical, 1/128)` supersede chain

## 4. 不变性验证（per CLAUDE.md §3 surgical）

- [x] 4.1 spec 不变性：`git diff --stat openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md openspec/specs/governance/spec.md` 期望全 **0** 改动（本 change 不动任何 spec）

- [x] 4.2 src/ 不变性：`git diff --stat src/` 期望全 **0** 改动（src/decompmoe/safeguards.py L34-36 + L29 已合规）

- [x] 4.3 tests/ 不变性：`git diff --stat tests/` 期望全 **0** 改动（既有 test 集合与本 finding 无关）

- [x] 4.4 其他 ticket 不变性：`git diff --stat wayfinder/tickets/` 期望仅 `A6a-2.md` 一处改动（其他 22 个 wayfinder tickets 不动）

- [x] 4.5 CLAUDE.md 不变性：`git diff --stat CLAUDE.md` 期望 **0** 改动（本 change 不引入 CLAUDE.md 修订；CLAUDE.md §8 边界补充属 change 09 范围）

## 5. Lint gate 与既有 test

- [x] 5.1 lint gate（per CLAUDE.md §3 `/opsx:archive` 前置条件）：`python scripts/lint_no_dead_defensive.py` → exit 0；`python scripts/lint_no_source_field_drift.py` → exit 0（本 change 不修改 src/ spec）

- [x] 5.2 既有 test 全绿：`uv run pytest tests/ -v` 期望全绿（本 change 不引入新 test）。如有 failure 立即暂停提交并调查根因

## 6. Commit 与 archive 准备

- [x] 6.1 单 commit on `dev`：`git add wayfinder/tickets/A6a-2.md && git commit -m "fix(ticket): A6a-2 L63 supersede annotation per cycle-9 audit-verification (1/128 → 1/(2·N_e))"`。commit message 含 Co-Authored-By trailer

- [x] 6.2 archive 准备（future, 不在本 change 完成范围）：archive 前须跑 `openspec validate 02-fix-ticket-a6a-2-f-threshold-supersede --type change --strict` 应 PASS；本 change 不要求立即 archive（待用户决策）

Co-Authored-By: Claude Code <noreply@anthropic.com>