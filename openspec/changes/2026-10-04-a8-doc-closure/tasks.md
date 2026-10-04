# Tasks

## 1. 台账实读与登记素材

- [x] 1.1 从 `git cat-file blob audit/sdd-review-2026-09-04:REVIEW-LEDGER.md` 取**字节流**口径的行数与 CR 计数（数 `0x0A`；**不得**用 PowerShell 文本路径的 `Get-Content`，它给出假低读数 310）。验证：raw LF 计数 = 312、raw CR = 0，且与 `git diff --numstat dev...audit -- REVIEW-LEDGER.md` 的 `312 0` 三口径对账一致。
- [x] 1.2 对 `LOOPS.md` 做同口径核验：确认它是 A-8 清单漏掉的同族资产，且其 dev→audit numstat 为 `63` 增 / `201` 删（**极性与清单记录的 `201 增 63 删` 相反**）。验证：`git diff --numstat dev audit/sdd-review-2026-09-04 -- LOOPS.md` 输出与记录一致。
- [x] 1.3 从上述两个 blob 中各提取一句 **≥8 字符的 verbatim 引文**，供 req-gov-6 的 prose-passage 引用格式使用。**禁止凭文件名或记忆编造引文**（`CLAUDE.md` §3：不在无真相源处造值）。验证：引文可在 `git cat-file blob` 的输出中逐字 grep 到。
- [x] 1.4 确认 `REVIEW-LEDGER.md` 在 `dev` 树中任何路径下均不存在（全量 `git ls-tree -r dev --name-only`，不做 scope-limited 收窄），且 audit 分支在远端可见（`git ls-remote` 返回该 ref 且 SHA 与本地一致）。验证：记录两条命令的实测输出。

## 2. `CLAUDE.md` §4 状态注记（UD-01 / UD-02）

- [x] 2.1 按**内容**定位（不按行号）`CLAUDE.md` 的 `## 4. Git Branch Architecture` 与其 `release` 行，在该行之后追加 design.md D2 给出的「当前状态（2026-10-04 实测）——本节通道未启用」段。措辞须：陈述 main 的真实形态、与 dev 无合并关系、release/tag 五路皆无；**不写任何提交计数**（并发工作树下该类数字会漂移，实测 `main..dev` = 229/229，清单的 174/174 已过期）。验证：`git diff CLAUDE.md` 的 diff 只落在 §4 内。
- [x] 2.2 确认该段**未**改写 §4 的三分支架构本身（`dev` / `main` / `release` 三条 bullet 与 L55 合并顺序一字未动）。验证：`git diff CLAUDE.md` 中不存在对这三行的修改行。
- [x] 2.3 复核新增段落**不含行号引用**（`lint_no_line_pointers.py` 检查 C1）。验证：`git diff CLAUDE.md | Select-String -Pattern 'CLAUDE\.md L\d|spec\.md L\d'` 无命中。

## 3. `CLAUDE.md` §8 引用 req-gov-4 clause (1)（UD-04）

- [x] 3.1 按内容定位 `## 8. Wayfinder Arena Index` 的 2026-08-21 裁决段，在段末追加 design.md D1 给出的引用段。**只能引 `req-gov-4` clause (1)**（advisory scope 收窄），**不得**引 clause 4(a) 作为标注义务依据（兄弟 change `fix-wayfinder-advisory-drift-a7` 的 D4 已裁定该义务依据是 `wayfinder` req-34）。验证：`git diff CLAUDE.md` 的 diff 只落在 §8 内，且新段中不出现 clause 4(a)。
- [x] 3.2 复核新增段满足 req-gov-6 的 prose-passage 引用形式：Requirement 号 + 标题 + ≥8 字符 verbatim 引文，**无行号**、**无 `#req-gov-4` 锚点字面量**（规避 C3）。验证：新段含 `req-gov-4`、Requirement 标题、以及 `this is the ONLY meaning of "advisory"` 这一 verbatim 串；`git diff CLAUDE.md | Select-String '#req-gov-4'` 无命中。
- [x] 3.3 确认 §8 的 2026-09-19 边界补充段（已含「advisory ≠ 无影响」）与 L24 的真相源第 4 档条目**一字未动**。验证：`git diff CLAUDE.md` 中不存在对这两处的修改行。

## 4. deferred-evidence 桶与台账登记（UD-03 / UD-06）

- [x] 4.1 建立 `deferred-evidence` 桶，逐条记录 **3 条**带 `[Irreversible Local Destruction]` 封条的 hand-back（`pin:baseline+delta-map` / `rv:main45:source` / `rv:main45:impact`），每条含：原结论、失效原因（`tests/test_loss.py` 当前 blob `e12ac751` 既非 revert 态 `7a88c637` 也非 fix 态 `6ddbdefb`，封条保护的工作树状态已从树上消失）、前置条件（新 HEAD 稳定后）、重跑范围（**仅该条 lens**，不重跑 `rv:main45` 整批）。验证：桶内恰 3 条，每条四字段齐全。
- [x] 4.2 在脚注记 `rv:main58:source`：因安全分类器限流**未产生任何输出**，既无告警也无放行，**不构成证据**、**不进重取证清单**；如需覆盖须重新提交分类。验证：脚注存在，且 `rv:main58:source` 未出现在 4.1 的桶内。
- [x] 4.3 登记台账位置与状态（`REVIEW-LEDGER.md` **与** `LOOPS.md` 各一条），含分支名 `audit/sdd-review-2026-09-04`、commit SHA、精确 numstat 与分叉计数（190/1），并显式纠正 A-8 清单的两处错（真实为 312 增 0 删；「两份同名文件」不成立）。引用采用 1.3 实读的 verbatim 引文。验证：两条登记齐全，且任一条都能让后续审计无需重新测量即可定位到源。
- [x] 4.4 若 `.audit/` 下的 A-8 报告在执行时不存在，则把 4.1/4.2/4.3 的内容整体落入本 change 的 `design.md`，**不新建**版本化的伪报告文件。验证：记录实际落点及判断依据。

## 5. 门禁与提交

- [ ] 5.1 先在主工作树采样 `git status --porcelain -uall`，确认本 change 目录未被并行 session 移动，且并行 session 对 `openspec/specs/decompmoe-skeleton/spec.md` / `src/decompmoe/gating.py` / `wayfinder/tickets/WF-1.md` 的改动**不在**本 change 的写入面（本 change 只写 `CLAUDE.md`）。验证：记录采样输出。
- [ ] 5.2 提交到 dev（**禁止 `git commit --amend`**——并行 session 共用同一 index；选择性暂存的校验必须与 `git commit` 紧邻执行）。验证：`git log --oneline -1` 显示本 change 的新 commit。
- [ ] 5.3 `git worktree add --detach <tmp> <my-commit>`，在该 worktree 内用主仓解释器跑 `python scripts/run_gates.py --change 2026-10-04-a8-doc-closure`（新 worktree 无 `.venv`；`run_gates.py` 从 `__file__` 推导 repo root）。判据是 **`exit 0`**；`exit 1` = 报红，`exit 2` = `GATE RESULT INVALID`（判定无效，结果不可引用）。**不要在主工作树重跑碰运气。** 验证：记录退出码与 finding 数。
- [ ] 5.4 `openspec validate 2026-10-04-a8-doc-closure --type change --strict` `exit 0`（本 change 声明 `skip_specs: true`，无 delta 是**预期**结果，不是缺陷）。验证：记录退出码。
- [ ] 5.5 `git worktree remove <tmp>`。验证：`git worktree list` 中该条目消失。

## 6. 远端默认展示分支

- [ ] 6.1 执行 `git remote set-head origin dev`（改的是远端默认展示分支指针，**不动任何 ref 拓扑**）。执行前先记录 `git symbolic-ref refs/remotes/origin/HEAD` 的当前值（应为 `refs/remotes/origin/main`）。验证：记录执行前后的两个值。
- [ ] 6.2 确认 `release` 分支与 tag 仍为零、`main` 与 `dev` 仍无共同祖先——本 change 只改展示指针，**不得**顺带创建分支或打 tag。验证：`git tag | Measure-Object` 计数为 0；`git merge-base main dev` 仍无输出。
- [ ] 6.3 报告 5.3/5.4/6.1 的实测结果，**在结果产出之后**才勾选对应条目。**禁止预先勾选**——已有前例：门禁判定作废（exit 2）后制品却已打勾。
