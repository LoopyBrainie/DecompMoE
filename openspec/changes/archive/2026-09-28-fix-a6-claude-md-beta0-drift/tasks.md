# Tasks

## 1. Pre-flight

- [x] 1.1 Turn-start 审计：跑 `git log --all --oneline -10`、`git reflog --date=iso -10`、`git status --short`，确认 HEAD、分支（应为 `dev`）与工作树状态；确认 `src/decompmoe/safeguards.py` 的标脏仍为纯 CRLF→LF 噪声（`git diff --ignore-all-space --stat -- src/decompmoe/safeguards.py` 输出为空）—— 若出现语义改动则**停下报告**，不并入本 change
      - 实测 @ `e5fec3a`（`dev`）：HEAD 与本 change propose 时一致，无新 commit。`safeguards.py` 采用更强判据核验 —— `git hash-object` worktree blob `e0fce170…` == index blob `e0fce170…`，**逐字节一致**（R-23 建议的 blob 哈希法，比 `--ignore-all-space` 强：后者会掩盖 Python 缩进改动）。
      - 并行 session 已扩散至 `governance/spec.md` / `wayfinder/spec.md` / `decompmoe-skeleton/spec.md` + `tests/test_beta.py` / `tests/test_sphere.py`。**`CLAUDE.md` 未被触及**，本 change 的目标文件无冲突。task 3.2 的 pytest 基线若异常须归因到并行 session。

## 2. Edit

- [x] 2.1 `git show HEAD:CLAUDE.md` 实测第 61 行当前内容，确认仍为 `β ∈ [0.1, 32], γ_init ≈ -3.5（β_0 ≈ 1.0）`；若已非此内容则**停下报告行号漂移**，不得凭本 tasks 的行号盲改
      - 实测 @ `e5fec3a`：L61 = `β ∈ [0.1, 32], γ_init ≈ -3.5（β_0 ≈ 1.0）`，与 propose 阶段记录一致，工作区同值。`git grep -c 'β_0 ≈ 1.0）' HEAD` = 全仓仅 `CLAUDE.md` 1 处。**无行号漂移。**
- [x] 2.2 将 `（β_0 ≈ 1.0）` 精确替换为 `（β_0 ≈ 1.035）`（仅此一处，全仓唯一）；验证 `git diff CLAUDE.md` 显示**恰好 1 行变更、1 处删除 1 处插入**，且无其他 hunk
      - `git diff --numstat -- CLAUDE.md` → `1  1  CLAUDE.md`；hunk 数 = **1**；diff 内容恰为 `-…（β_0 ≈ 1.0）` / `+…（β_0 ≈ 1.035）`，§5 其余各行均以 context 行出现（未被改写）。

## 3. Verification

- [x] 3.1 复看 `git show HEAD:CLAUDE.md` 第 61 行确认为 `β ∈ [0.1, 32], γ_init ≈ -3.5（β_0 ≈ 1.035）`，并确认 §5 冻结块其余各行（`d_model` / `N_e` / `k` / `d_ffn` / `L` / `Total` / `Active` / `d_ffn_dense` / `θ_Voronoi` / `θ_{1/e}` / phase ratios / phase boundaries）**逐字未变**
      - 工作区 L61 = `β ∈ [0.1, 32], γ_init ≈ -3.5（β_0 ≈ 1.035）` ✓。L59 / L60 / L62 / L63 / L64 逐行 `-ceq`（区分大小写）比对 HEAD：**全部 identical=True**，含 `θ_Voronoi … 1.1735 rad`（`b23f0e5` 的修正值）与 `θ_{1/e} ≈ 20.36°`。
- [x] 3.2 跑 `uv run pytest -q` 验证基线 **204 passed** 不变（本 change 不触碰 `src/` 与 `tests/`，任何 red 都是并行 session 造成，须停下报告）
      - 实际 **`206 passed, 1 warning in 4.04s`，零失败**。计数 +2 归因：并行 session 在脏工作树的 `tests/test_beta.py`（+43 行）与 `tests/test_sphere.py`（+43 行）中新增了 2 个测试函数 —— `test_counterfactual_gamma_init_5sig_literal`（a2a3a4 的 A3 守护）与 `test_voronoi_impl_output_within_1e6_of_exact_root`（A4 守护）。`204 + 2 = 206`，`--collect-only` 复核一致。**A6 本身零 red**，无停机条件触发。
- [x] 3.3 跑 `python scripts/lint_no_dead_defensive.py` 与 `python scripts/lint_no_source_field_drift.py` 验证均 `exit=0`（本 change 不改任何 `**Source:**` 字段与 `src/`，预期不受影响，但按 `CLAUDE.md` §3 archive 前置条件仍须实跑）
      - `lint_no_dead_defensive: OK (no anti-patterns found)` → `exit=0`；`lint_no_source_field_drift: OK (3 file(s) scanned, no violations)` → `exit=0`。两者均通过。
- [x] 3.4 `git add CLAUDE.md`（**精确路径，禁止 `git add .` / `-A`**）后在 `dev` 上提交单 commit，commit message 引用本 change 名与 `β_0` 修正；验证 `git status --short` 中不再有 `CLAUDE.md` 条目，且 `safeguards.py` 与 untracked change 目录保持原状未被误提交
      - `git add CLAUDE.md` 后暂存区 `git diff --cached --name-only` = **仅 `CLAUDE.md`**（逐条 add，未用 `-A`）。提交 `8765806`（`dev`），`git show --stat` = **1 file changed, 1 insertion(+), 1 deletion(-)**。提交后 `git status --short -- CLAUDE.md` 为空。
      - 并行 session 的全部文件原样保留未被误提交：脏 spec（`decompmoe-skeleton` / `governance` / `wayfinder`）、`safeguards.py`、脏测试（`test_beta.py` / `test_sphere.py`）、6 个 `_*.py` / `_*.txt` 临时脚本、4 个 untracked change 目录。
      - **过程记录（偏离）**：首次提交尝试用多段 `git commit -m "..."` 在 PowerShell 下失败 —— PowerShell 把第 2 段起的参数当作 pathspec（`error: pathspec '...' did not match any file(s) known to git`）。**回读 `git log -1` 确认未产生 commit、暂存区完好**，无残留状态。改用 write 工具写 UTF-8 无 BOM message 文件 + `git commit -F <abs path>` 成功。此为 PowerShell 语法限制，非 change 缺陷。
